"""Konservative Lastpfadabschätzung für die komplette Dachbaugruppe.

Die Rechnung ersetzt keine Bauteilzulassung. Sie macht aber die bisher nur
qualitativ beschriebenen Grenzflächen explizit und verwendet bewusst
abgeminderte Bemessungswerte statt Hersteller-Kurzzeitwerte. Einheiten sind
mm, N, N/mm² (= MPa) und Nm.

Aufruf::

    python3 -m analysis.load_paths

Wenn die aktuelle CFD-Fallmatrix vorhanden ist, wird deren bereits mit 1,5
multiplizierter offener Lastfall automatisch als zusätzliche Sensitivität
eingelesen. Der 480-N-Windhüllfall bleibt unabhängig davon maßgebend.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from itertools import combinations
import json
import math
from pathlib import Path

import params as PRM
from fem import analytic as FEM_ANALYTIC
from project_paths import load_path_dir


SOURCES = {
    "sikaflex_522": {
        "url": "https://industry.sika.com/en/home/transportation/"
               "sealants/adhesive-sealants/sikaflex-522.html",
        "basis": (
            "1,8 MPa Zugfestigkeit, 400 % Bruchdehnung, -50 bis +90 °C; "
            "Originalsubstrat-Prüfung wird vom Hersteller gefordert"
        ),
    },
    "sika_elastic_bonding": {
        "url": "https://industry.sika.com/dms/getdocument.get/"
               "8ffff4cd-c90d-4d24-969d-ee4db9093cf3_global-industry/"
               "compendium-elasticbonding.pdf",
        "basis": (
            "Temperatur-, Dauer-, Ermüdungs- und Alterungsabminderung; "
            "Designsicherheitsfaktor typischerweise 1,5 bis 2,5 oder höher; "
            "50 % typische zulässige thermische Scherverformung"
        ),
    },
    "sika_stp_pretreatment": {
        "url": "https://industry.sika.com/dms/getdocument.get/"
               "776a779a-10a6-413c-b20b-c46467315e33/"
               "pre-treatment-chartforsilanterminatedpolymersstp-"
               "sikaflex-500ser.pdf",
        "basis": (
            "Version 8 (02/2026): ABS, 2K-PUR-Lack und GFK-Gelcoat; "
            "Tabelle ist nur Leitlinie und nennt ASA-GF nicht ausdrücklich"
        ),
    },
    "rk_1300": {
        "url": "https://media.weicon.de/fmds/307278/dld%3Ainline/"
               "DE_TDS_10560060_RK-1300.pdf",
        "basis": (
            "6 MPa Zugscherfestigkeit auf ABS, 16 MPa auf GFK, "
            "-50 bis +130 °C und Optimum bei 0,15 bis 0,25 mm Fuge"
        ),
    },
    "sikaforce_710_l35": {
        "url": "https://deu.sika.com/dms/getdocument.get/"
               "41466f3f-1639-4fc4-8298-5c9a0a2d34e1/"
               "sikaforce-710-l35.pdf",
        "basis": (
            "für Holz/GFK mit EPS/XPS-Sandwichkernen; 14 MPa Zug- und "
            "9 MPa Zugscherfestigkeit des Klebstoffs"
        ),
    },
    "xps_reference": {
        "url": "https://ursa.de/wp-content/uploads/2023/05/DB-xps.pdf",
        "basis": (
            "herstellerseitiger Vergleichswert TR 200: mindestens 0,20 MPa "
            "Zugfestigkeit senkrecht zur Plattenebene; nicht das X150-Material"
        ),
    },
    "carloflex": {
        "url": "../../../../references/datasheets/adhesives/"
               "carloflex-410-uv-source.md",
        "basis": (
            "Carlofon-TDS: >1,8 MPa Zugfestigkeit, >450 % Dehnung, "
            "-40 bis +90 °C; Belluna-Anwendungsempfehlung"
        ),
    },
}


@dataclass(frozen=True)
class Assumptions:
    """Projekt-Bemessungswerte mit eingerechneter Unsicherheit."""

    # Sikaflex-522 bzw. Carloflex 410 UV: nur 1,7 % bzw. 2,8 % der
    # publizierten 1,8-MPa-Zugfestigkeit als Größenskala. Der Schubwert ist
    # eine Projektannahme, weil die TDS keinen Grenzflächen-Schubwert nennen.
    # Diese
    # starke Reduktion deckt 85 °C nahe der 90-°C-Grenze, Dauer/Ermüdung,
    # Alterung, FDM-/GFK-Streuung und fehlende Originalsubstrat-Coupons ab.
    elastic_normal_allow_MPa: float = 0.030
    elastic_shear_allow_MPa: float = 0.050

    # 6 MPa auf ABS ist der niedrigste passende RK-1300-TDS-Wert. 0,5 MPa
    # entspricht Faktor 12 für ASA-Analogie, FDM, Alterung und Temperatur.
    rk1300_lap_shear_allow_MPa: float = 0.50

    # Nicht die 9/14 MPa des SikaForce-Klebstoffs ansetzen: 0,05 MPa ist nur
    # ein Viertel des herstellerseitigen XPS-Vergleichswerts TR 200. Zudem
    # wird nur EINE der beiden großen GFK/Holz-Flächen angerechnet.
    panel_bond_normal_allow_MPa: float = 0.050
    panel_bond_shear_allow_MPa: float = 0.050

    # ASA-Pfad: bestehender dauerabgeminderter Gewindeauszug nochmals halbiert
    # für Pilotloch-, FDM- und lokale Kerbunsicherheit.
    asa_thread_detail_factor: float = 0.50

    # Deckt ungleiche Schraubensteifigkeit, Toleranzen und nichtideale
    # Gruppenverteilung ab. Jede Schraubenrechnung wird damit vergrößert.
    screw_load_concentration: float = 1.50


DEFAULTS = Assumptions()


@dataclass(frozen=True)
class LoadCase:
    name: str
    description: str
    force_N: tuple[float, float, float]
    moment_top_Nm: tuple[float, float, float]
    moment_base_Nm: tuple[float, float, float]
    provenance: str


def _square_ring(inner_side_mm: float, width_mm: float) -> dict:
    outer = inner_side_mm + 2.0 * width_mm
    area = outer**2 - inner_side_mm**2
    inertia = (outer**4 - inner_side_mm**4) / 12.0
    return {
        "inner_side_mm": inner_side_mm,
        "outer_side_mm": outer,
        "width_mm": width_mm,
        "area_mm2": area,
        "second_moment_mm4": inertia,
        "section_modulus_mm3": inertia / (outer / 2.0),
    }


def _rounded_square_ring(inner_side_mm: float, width_mm: float,
                         inner_radius_mm: float) -> dict:
    """Exakter Ring einer quadratischen Kontur mit gerundeten Ecken.

    Fläche und Flächenträgheitsmoment entstehen als Differenz zweier
    abgerundeter Quadrate. Das vermeidet die leicht optimistische
    Quadratnäherung gerade bei den relativ kleinen Rillenradien.
    """
    outer_side = inner_side_mm + 2.0 * width_mm
    outer_radius = inner_radius_mm + width_mm

    def rounded_square(side: float, radius: float) -> tuple[float, float]:
        area = side * side - (4.0 - math.pi) * radius * radius
        square_i = side**4 / 12.0
        corner_center = side / 2.0 - radius
        corner_square_i = (
            radius * ((corner_center + radius) ** 3 - corner_center**3) / 3.0
        )
        quarter_circle_i = (
            math.pi * radius**4 / 16.0
            + 2.0 * corner_center * radius**3 / 3.0
            + corner_center**2 * math.pi * radius**2 / 4.0
        )
        inertia = square_i - 4.0 * (corner_square_i - quarter_circle_i)
        return area, inertia

    outer_area, outer_i = rounded_square(outer_side, outer_radius)
    inner_area, inner_i = rounded_square(inner_side_mm, inner_radius_mm)
    area = outer_area - inner_area
    inertia = outer_i - inner_i
    return {
        "inner_side_mm": inner_side_mm,
        "outer_side_mm": outer_side,
        "width_mm": width_mm,
        "inner_radius_mm": inner_radius_mm,
        "outer_radius_mm": outer_radius,
        "area_mm2": area,
        "second_moment_mm4": inertia,
        "section_modulus_mm3": inertia / (outer_side / 2.0),
    }


def _roof_double_bead(p: PRM.Params) -> dict:
    """Gemeinsame Querschnittswerte der zwei konzentrischen Dachraupen.

    Die acht Ventunterbrechungen werden als rechteckige Fehlstellen aus
    Fläche und Flächenträgheitsmoment der inneren Raupe abgezogen. Durch die
    vierfach rotationssymmetrische Anordnung gilt Ix = Iy.
    """
    rings = []
    area = 0.0
    inertia_x = 0.0
    inertia_y = 0.0
    outer_side = 0.0
    for off, width, _gap_length in PRM.groove_specs(p):
        ring = _rounded_square_ring(
            p.CUTOUT_W + 2.0 * off,
            width,
            p.CUTOUT_R + off,
        )
        rings.append(ring)
        area += ring["area_mm2"]
        inertia_x += ring["second_moment_mm4"]
        inertia_y += ring["second_moment_mm4"]
        outer_side = max(outer_side, ring["outer_side_mm"])

    inner_center_r = p.CUTOUT_W / 2.0 + p.GROOVE_OFF + p.GROOVE_W / 2.0
    patch_area = p.GROOVE_W * p.GROOVE_VENT_W
    removed_area = 0.0
    removed_ix = 0.0
    removed_iy = 0.0
    for side in range(4):
        radial_along_x = side % 2 == 0
        for tangent in p.GROOVE_VENT_OFFS:
            if side == 0:
                cx, cy = inner_center_r, tangent
            elif side == 1:
                cx, cy = -tangent, inner_center_r
            elif side == 2:
                cx, cy = -inner_center_r, -tangent
            else:
                cx, cy = tangent, -inner_center_r
            dim_x = p.GROOVE_W if radial_along_x else p.GROOVE_VENT_W
            dim_y = p.GROOVE_VENT_W if radial_along_x else p.GROOVE_W
            removed_area += patch_area
            removed_ix += patch_area * cy * cy + dim_x * dim_y**3 / 12.0
            removed_iy += patch_area * cx * cx + dim_y * dim_x**3 / 12.0

    area -= removed_area
    inertia = 0.5 * ((inertia_x - removed_ix) + (inertia_y - removed_iy))
    return {
        "type": "double_bead_with_inner_dry_side_vents",
        "beads": rings,
        "inner_vent_count": 4 * len(p.GROOVE_VENT_OFFS),
        "inner_vent_width_mm": p.GROOVE_VENT_W,
        "channel_width_mm": p.GROOVE_CHANNEL_W,
        "outer_side_mm": outer_side,
        "area_mm2": area,
        "second_moment_mm4": inertia,
        "section_modulus_mm3": inertia / (outer_side / 2.0),
    }


def _bond_check(load: LoadCase, moment_Nm: tuple[float, float, float],
                ring: dict, normal_allow: float, shear_allow: float) -> dict:
    fx, fy, fz = load.force_N
    mx, my, _ = moment_Nm
    area = ring["area_mm2"]
    edge = ring["outer_side_mm"] / 2.0
    inertia = ring["second_moment_mm4"]
    average_normal = fz / area
    bending_normal = ((abs(mx) + abs(my)) * 1000.0 * edge / inertia)
    max_tension = max(0.0, average_normal + bending_normal)
    shear = math.hypot(fx, fy) / area

    # Sika-Normalspannungshypothese in normierter Form. Dadurch dürfen für
    # Zug und Schub unterschiedliche konservative Bemessungswerte gelten.
    n = max_tension / normal_allow
    s = shear / shear_allow
    interaction = 0.5 * n + 0.5 * math.sqrt(n * n + 4.0 * s * s)
    return {
        "average_normal_MPa": average_normal,
        "bending_normal_MPa": bending_normal,
        "max_tension_MPa": max_tension,
        "average_shear_MPa": shear,
        "normal_allow_MPa": normal_allow,
        "shear_allow_MPa": shear_allow,
        "normalized_interaction": interaction,
        "PASS": interaction <= 1.0,
    }


def _plate_screw_positions(p: PRM.Params) -> tuple[tuple[float, float], ...]:
    radius = p.PLATE_KRAGEN_W / 2.0
    offset = min(abs(v) for v in p.PLATE_SCREW_OFFS)
    return (
        (-radius, -offset), (-radius, offset),
        (radius, -offset), (radius, offset),
        (-offset, -radius), (offset, -radius),
        (-offset, radius), (offset, radius),
    )


def _roof_screw_positions(p: PRM.Params) -> tuple[tuple[float, float], ...]:
    """Acht seitliche Unterkragen-Schrauben, nur als Bedarfswert."""
    radius = (p.CUTOUT_W - 2.0 * p.BOT_KRAGEN_CLEAR - p.BOT_KRAGEN_T) / 2.0
    offset = max(abs(v) for v in p.BOT_KRAGEN_HOLE_OFFS)
    return (
        (-radius, -offset), (-radius, offset),
        (radius, -offset), (radius, offset),
        (-offset, -radius), (offset, -radius),
        (-offset, radius), (offset, radius),
    )


def _screw_group_check(load: LoadCase, moment_Nm: tuple[float, float, float],
                       capacity_per_screw_N: float, p: PRM.Params,
                       a: Assumptions,
                       positions: tuple[tuple[float, float], ...] | None = None
                       ) -> dict:
    positions = positions or _plate_screw_positions(p)
    n_screws = len(positions)
    sx2 = sum(x * x for x, _ in positions)
    sy2 = sum(y * y for _, y in positions)
    sr2 = sum(x * x + y * y for x, y in positions)
    fx, fy, fz = load.force_N
    mx, my, mz = moment_Nm
    forces = []
    for x, y in positions:
        # Elastische Schraubengruppen-Näherung. Translation wird gleichmäßig,
        # Mx/My über vertikale Scherkräfte und Mz tangential verteilt.
        qx = fx / n_screws - mz * 1000.0 * y / sr2
        qy = fy / n_screws + mz * 1000.0 * x / sr2
        qz = (fz / n_screws + mx * 1000.0 * y / sy2
              - my * 1000.0 * x / sx2)
        forces.append(a.screw_load_concentration
                      * math.sqrt(qx * qx + qy * qy + qz * qz))
    maximum = max(forces)
    return {
        "count": n_screws,
        "load_concentration_factor": a.screw_load_concentration,
        "max_resultant_per_screw_N": maximum,
        "capacity_per_screw_N": capacity_per_screw_N,
        "utilization": maximum / capacity_per_screw_N,
        "PASS": maximum <= capacity_per_screw_N,
    }


def _screw_omission_sensitivity(
        load: LoadCase, moment_Nm: tuple[float, float, float],
        capacity_per_screw_N: float, p: PRM.Params,
        a: Assumptions) -> dict:
    """Zeigt die Reserve gegen fehlende Schrauben ohne sie freizugeben."""
    positions = _plate_screw_positions(p)
    result = {}
    for missing in (1, 2):
        utilizations = []
        for omitted in combinations(range(len(positions)), missing):
            retained = tuple(
                pos for index, pos in enumerate(positions)
                if index not in omitted
            )
            check = _screw_group_check(
                load, moment_Nm, capacity_per_screw_N, p, a, retained)
            utilizations.append(check["utilization"])
        result[f"{missing}_missing"] = {
            "remaining_count": len(positions) - missing,
            "best_utilization": min(utilizations),
            "worst_utilization": max(utilizations),
            "all_configurations_PASS": max(utilizations) <= 1.0,
        }
    return result


def _asa_screw_capacity(p: PRM.Params, a: Assumptions) -> dict:
    # Gleiche konservative Grundgleichung wie der bisherige Nachweis, aber
    # nicht mehr als scheinbar genauer Endwert ohne Detailfaktor ausgeben.
    sigma_long, _ = PRM.allowables(p)
    engagement = 12.0
    base = (math.pi * p.BOT_KRAGEN_SCREW_D * engagement
            * 0.5 * sigma_long)
    project = base * a.asa_thread_detail_factor
    return {
        "analytical_thread_reference_N": base,
        "detail_factor": a.asa_thread_detail_factor,
        "project_capacity_per_screw_N": project,
        "engagement_mm": engagement,
        "warning": (
            "Abgeminderte Geometrie-/Materialanalogie für ST4.2 in FDM-ASA-GF; "
            "keine Zulassung oder herstellergeprüfte Schraubverbindung"
        ),
    }


def _base_load_cases(p: PRM.Params) -> list[LoadCase]:
    wind = PRM.wind_force(p)
    top_z = p.H_RAISE - p.GLUE_GAP
    lateral = p.FAN_MASS * 9.81 * p.G_LAT
    uplift = p.FAN_MASS * 9.81 * p.G_VERT
    return [
        LoadCase(
            "wind_envelope_480N",
            "bestehende analytische 200-km/h-Hülle einschließlich SF=2",
            (wind, 0.0, 0.0),
            (0.0, wind * p.H_CG / 1000.0, 0.0),
            (0.0, wind * (p.H_CG + top_z) / 1000.0, 0.0),
            "params.wind_force; bleibt gegenüber CFD unverändert maßgebend",
        ),
        LoadCase(
            "road_uplift_lateral",
            "gleichzeitige +4-g-Abhebe- und 2-g-Querhülle auf 6,5 kg",
            (0.0, lateral, uplift),
            (-lateral * p.H_CG / 1000.0, 0.0, 0.0),
            (-lateral * (p.H_CG + top_z) / 1000.0, 0.0, 0.0),
            "konservative Kombination der vorhandenen LF2-Komponenten",
        ),
        LoadCase(
            "snow_compression",
            "Schnee-/Standlast, wirkt auf die Klebfugen überwiegend drückend",
            (0.0, 0.0, -p.SNOW_LOAD),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
            "params.SNOW_LOAD",
        ),
    ]


def _load_cfd_transfer() -> tuple[LoadCase | None, str | None]:
    try:
        from cfd.config import comparison_hash
        from project_paths import cfd_matrix_dir

        path = cfd_matrix_dir(comparison_hash()) / "comparison.json"
        if not path.exists():
            return None, None
        data = json.loads(path.read_text(encoding="utf-8"))
        transfer = data["structural_transfer_open_medium"]
        return LoadCase(
            "cfd_open_medium_x1p5",
            "offene Haube, mittleres Netz, Kräfte bereits mit Modellfaktor 1,5",
            tuple(transfer["force_N"]),
            tuple(transfer["free_moment_at_adapter_top_Nm"]),
            tuple(transfer["moment_about_adapter_base_Nm"]),
            f"{path} · Matrix {data['comparison_hash']}",
        ), str(path)
    except (ImportError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None, None


def assess(p: PRM.Params = PRM.P, a: Assumptions = DEFAULTS,
           include_cfd: bool = True) -> dict:
    top_elastic_ring = _square_ring(
        p.CUTOUT_W + 2.0 * p.PLATE_BOND_OFF, p.PLATE_BOND_W)
    roof_elastic_ring = _roof_double_bead(p)
    wood_ring = _square_ring(p.CUTOUT_W, p.ROOF_WOOD_FRAME_W)
    asa_capacity = _asa_screw_capacity(p, a)
    cases = _base_load_cases(p)
    cfd_path = None
    if include_cfd:
        cfd, cfd_path = _load_cfd_transfer()
        if cfd is not None:
            cases.append(cfd)

    case_results = {}
    for case in cases:
        top_bond = _bond_check(
            case, case.moment_top_Nm, top_elastic_ring,
            a.elastic_normal_allow_MPa, a.elastic_shear_allow_MPa)
        bottom_bond = _bond_check(
            case, case.moment_base_Nm, roof_elastic_ring,
            a.elastic_normal_allow_MPa, a.elastic_shear_allow_MPa)
        top_screws = _screw_group_check(
            case, case.moment_top_Nm,
            asa_capacity["project_capacity_per_screw_N"], p, a)
        roof_screw_demand = _screw_group_check(
            case, case.moment_base_Nm, 1.0, p, a,
            positions=_roof_screw_positions(p))
        panel_bond = _bond_check(
            case, case.moment_base_Nm, wood_ring,
            a.panel_bond_normal_allow_MPa,
            a.panel_bond_shear_allow_MPa)
        case_results[case.name] = {
            "description": case.description,
            "provenance": case.provenance,
            "force_N": list(case.force_N),
            "moment_top_Nm": list(case.moment_top_Nm),
            "moment_base_Nm": list(case.moment_base_Nm),
            "belluna_to_adapter": {
                "elastic_ring_bond_only": top_bond,
                "eight_side_screws_full_case": top_screws,
            },
            "adapter_to_roof": {
                "double_elastic_bead_primary": bottom_bond,
                "eight_roof_side_screws_secondary": {
                    "installed_count": 8,
                    "required_capacity_per_screw_N_for_full_case":
                        roof_screw_demand["max_resultant_per_screw_N"],
                    "capacity_credit_N": 0.0,
                    "qualification": (
                        "mechanische Rückfallebene; Holz/GFK, Pilotloch und "
                        "beiliegende ST4.2 nicht typgeprüft; nicht zum PASS addiert"
                    ),
                    "PASS": None,
                },
            },
            "wood_to_roof_sandwich": {
                "sikaforce_one_face_only": panel_bond,
            },
            # Oben trägt die vollständige Schraubengruppe. Unten muss die
            # Doppelraupe den vollständigen Lastfall allein tragen. Die acht
            # Holzschrauben sind nur unqualifizierte Rückfallebene.
            "serial_load_path_PASS": (
                top_screws["PASS"] and bottom_bond["PASS"]
                and panel_bond["PASS"]
            ),
        }

    lap_area = p.LAP_L * PRM.min_band(p)
    wind = PRM.wind_force(p)
    rk_tau = wind / lap_area
    lap_h = PRM.lap_height(p)
    bolts_per_joint = len(p.JOINT_BOLT_OFFS)
    group_bearing = ((wind / bolts_per_joint)
                     / (p.JOINT_BOLT_D * lap_h))
    one_remaining_bearing = wind / (p.JOINT_BOLT_D * lap_h)
    _, short_allow = PRM.allowables(p)
    segment = {
        "load_N": wind,
        "assumption": "volle 480-N-Horizontallast durch genau EINEN Stoß",
        "lap_area_mm2": lap_area,
        "rk1300_shear_MPa": rk_tau,
        "rk1300_allow_MPa": a.rk1300_lap_shear_allow_MPa,
        "rk1300_utilization": rk_tau / a.rk1300_lap_shear_allow_MPa,
        "rk1300_PASS": rk_tau <= a.rk1300_lap_shear_allow_MPa,
        "m5_count_per_joint": bolts_per_joint,
        "m5_group_bearing_MPa": group_bearing,
        "m5_one_remaining_bearing_MPa": one_remaining_bearing,
        "asa_short_allow_MPa": short_allow,
        "m5_group_bearing_utilization": group_bearing / short_allow,
        "m5_one_remaining_utilization": one_remaining_bearing / short_allow,
        "m5_single_bolt_full_case_PASS": one_remaining_bearing <= short_allow,
    }
    segment["PASS"] = (segment["rk1300_PASS"]
                       and segment["m5_single_bolt_full_case_PASS"])

    thermal_util = FEM_ANALYTIC.glue_shear_utilization(p)
    thermal = {
        "allowable_shear_movement_fraction": p.GLUE_SHEAR_CAP,
        "utilization": thermal_util,
        "PASS": thermal_util <= 1.0,
    }
    all_cases_pass = all(v["serial_load_path_PASS"]
                         for v in case_results.values())
    wind_case = cases[0]
    fastener_sensitivity = {
        "scope": (
            "480-N-Windhülle; elastisch neu verteilte Last nach Ausfall, "
            "ohne dynamische Ausfallfolgen"
        ),
        "top_group": _screw_omission_sensitivity(
            wind_case, wind_case.moment_top_Nm,
            asa_capacity["project_capacity_per_screw_N"], p, a),
        "design_requirement": (
            "Alle acht Belluna-Plattenschrauben montieren und intakt halten. "
            "Die acht unteren Schrauben montieren, aber ohne qualifizierte "
            "Holz-/Dachkapazität nicht zum Primärnachweis addieren."
        ),
    }
    status = ("PASS_ASSUMPTION_BASED" if all_cases_pass
              and segment["PASS"] and thermal["PASS"]
              else "FAIL_ASSUMPTION_BASED")
    return {
        "schema": 2,
        "status": status,
        "claim_limit": (
            "Konservative Plausibilisierung, keine Zulassung oder Garantie; "
            "Grenzflächen und beiliegende Schrauben sind nicht typgeprüft"
        ),
        "parameter_hash": PRM.params_hash(p),
        "assumptions": asdict(a),
        "sources": SOURCES,
        "geometry": {
            "top_elastic_ring": top_elastic_ring,
            "roof_elastic_ring": roof_elastic_ring,
            "wood_frame_one_face_only": wood_ring,
        },
        "capacities": {
            "asa_screw": asa_capacity,
        },
        "load_cases": case_results,
        "segment_joint": segment,
        "thermal_movement": thermal,
        "fastener_sensitivity": fastener_sensitivity,
        "model_limitations": [
            "Starrer Ring und linear-elastische Lastverteilung; lokale "
            "Peelspitzen und Gehäusenachgiebigkeit sind nicht aufgelöst.",
            "Die zwei unteren 10-mm-Elastikraupen sind der allein angerechnete "
            "Adapter-Dach-Primärpfad. Die acht seitlichen Schrauben sind eine "
            "physische, aber mangels Holz-/Dachprüfung unqualifizierte Reserve.",
            "Die acht oberen ST4.2x25 werden mit einem abgeminderten axialen "
            "Analogiewert auf den resultierenden Lastvektor geprüft.",
            "Der einzelne M5 je Segmentstoß wird mit der vollen 480-N-Hülle "
            "geprüft; expliziter Bolzenkontakt und Lochspiel sind nicht aufgelöst.",
            "Das reale X150-GFK/XPS-Sandwich ist nicht typgeprüft; deshalb "
            "werden nur eine Holz/GFK-Fläche und 0,050 MPa angerechnet.",
            "CFD, FEM und Lastpfadrechnung sind Modellplausibilisierungen, "
            "keine Bauteilprüfung oder Herstellerfreigabe.",
        ],
        "cfd_source": cfd_path,
        "system_PASS": status == "PASS_ASSUMPTION_BASED",
    }


def _pct(value: float) -> str:
    return f"{100.0 * value:.0f} %"


def to_markdown(result: dict) -> str:
    lines = [
        "# Abschätzung der Klebe-, Schraub- und Dachlastpfade",
        "",
        f"Parameterstand `{result['parameter_hash']}` · **{result['status']}**",
        "",
        "> Konservative Plausibilisierung, keine Bauteilzulassung. Die untere "
        "Doppelraupe trägt den Primärnachweis allein; acht seitliche "
        "Holzschrauben bleiben eine physische, aber unqualifizierte Reserve.",
        "",
        "## Ergebnisübersicht",
        "",
        "| Lastfall | obere Elastikfuge allein | 8 Schrauben oben | "
        "2×10-mm-Dachraupe allein | erforderliche Kapazität je Rückfallschraube | "
        "Holz–Dach, eine Fläche | serieller Pfad |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for name, case in result["load_cases"].items():
        top = case["belluna_to_adapter"]
        roof = case["adapter_to_roof"]["double_elastic_bead_primary"]
        fallback = case["adapter_to_roof"]["eight_roof_side_screws_secondary"]
        wood = case["wood_to_roof_sandwich"]["sikaforce_one_face_only"]
        lines.append(
            f"| `{name}` | "
            f"{_pct(top['elastic_ring_bond_only']['normalized_interaction'])} | "
            f"{_pct(top['eight_side_screws_full_case']['utilization'])} | "
            f"{_pct(roof['normalized_interaction'])} | "
            f"{fallback['required_capacity_per_screw_N_for_full_case']:.0f} N "
            "(nicht qualifiziert) | "
            f"{_pct(wood['normalized_interaction'])} | "
            f"{'PASS' if case['serial_load_path_PASS'] else 'FAIL'} |"
        )

    seg = result["segment_joint"]
    therm = result["thermal_movement"]
    top_fasteners = result["fastener_sensitivity"]["top_group"]
    asa = result["capacities"]["asa_screw"]
    top_ring = result["geometry"]["top_elastic_ring"]
    roof_ring = result["geometry"]["roof_elastic_ring"]
    lines += [
        "",
        "Die obere Belluna-Verbindung bleibt hybrid: Kleber und acht "
        "Seitenschrauben werden nicht addiert; die Schraubengruppe trägt den "
        "vollständigen Fall mit Lastkonzentrationsfaktor 1,5. Unten müssen die "
        "beiden 10-mm-Raupen den vollständigen Fall allein bestehen. Die acht "
        "Holzschrauben werden weder zur Klebung addiert noch als PASS gewertet.",
        "Der Schubgrenzwert 0,050 MPa ist kein TDS-Schubkennwert, sondern eine "
        "bewusst niedrige Projektannahme. Reale Grenzflächenhaftung und "
        "Alterung bleiben unbekannt.",
        "",
        "## Maßgebende Festwerte",
        "",
        f"- Obere Ringfuge: {top_ring['area_mm2']:.0f} mm²; 0,030 MPa "
        "normal / 0,050 MPa Schub, nicht allein maßgebend.",
        f"- Untere Doppelraupe: {roof_ring['area_mm2']:.0f} mm² wirksam, Innenmaß "
        f"{roof_ring['beads'][0]['inner_side_mm']:.0f} mm, Außenmaß "
        f"{roof_ring['outer_side_mm']:.0f} mm; vollständig über dem "
        f"30-mm-Holzrahmen, {roof_ring['inner_vent_count']} innere "
        "Trockenraum-Vents, 0,030/0,050 MPa.",
        f"- Obere ST4.2x25 in ASA-GF: {asa['project_capacity_per_screw_N']:.0f} N "
        "je Schraube nach Detailfaktor 0,5.",
        f"- Segmentstoß unter vollen 480 N: RK-1300 "
        f"{_pct(seg['rk1300_utilization'])}; {seg['m5_count_per_joint']} M5 "
        f"{_pct(seg['m5_group_bearing_utilization'])}, einzelner M5-Vollfall "
        f"{_pct(seg['m5_one_remaining_utilization'])}; "
        f"{'PASS' if seg['PASS'] else 'FAIL'}.",
        f"- Thermische Scherbewegung der 3-mm-Fuge: "
        f"{_pct(therm['utilization'])} des 50-%-Grenzwerts; "
        f"{'PASS' if therm['PASS'] else 'FAIL'}.",
        f"- Obere Schraubengruppe: eine fehlende Schraube ergibt "
        f"{_pct(top_fasteners['1_missing']['best_utilization'])} bis "
        f"{_pct(top_fasteners['1_missing']['worst_utilization'])}; zwei "
        "fehlende Schrauben bestehen nicht in jeder Anordnung. Alle acht "
        "Belluna-Plattenschrauben bleiben Pflicht.",
        "",
        "## Konstruktive Interpretation",
        "",
        "- Der Adapter bleibt bei 500 mm Außenmaß. Zwei getrennte 10-mm-Raupen "
        f"liefern trotz acht 5-mm-Ventunterbrechungen rund "
        f"{roof_ring['area_mm2']:.0f} mm² wirksame "
        "Klebefläche und liegen vollständig über dem Holzrahmen.",
        "- Die äußere Raupe bleibt als Wassersperre geschlossen. Nur die innere "
        "Raupe wird an acht Stellen zur trockenen Öffnungsseite unterbrochen, "
        "damit der 4-mm-Mittelkanal Feuchte nachführen kann.",
        "- Acht seitliche ST4.2x25 sichern den Unterkragen im Holzrahmen. Ohne "
        "typgeprüften Schraubgrund wird nur der je Lastfall erforderliche "
        "Kapazitätswert ausgewiesen; die Schrauben werden nicht angerechnet.",
        "- Ein M5 je Stoß trägt die volle 480-N-Hülle bereits allein. RK-1300 "
        "bildet einen davon getrennt geprüften Fügepfad.",
        "- Sikaflex-522 und Carloflex 410 UV werden weiterhin nur mit den "
        "stark abgeminderten 0,030/0,050-MPa-Werten angesetzt. Produkte "
        "innerhalb einer Baugruppe nicht mischen.",
        "",
        "## Oberflächenannahme für Sikaflex-522",
        "",
        "Die tragenden Klebezonen bleiben lackfrei. ASA-GF und Belluna-"
        "Kunststoff werden sehr fein angeschliffen, mit Sika Cleaner P "
        "gereinigt und als ABS-Analogie mit Sika Primer-507 vorbehandelt. "
        "GFK-Gelcoat wird sehr fein angeschliffen, gereinigt und mit Sika "
        "Aktivator-205 vorbehandelt. ASA-GF ist nicht ausdrücklich in der "
        "Sika-Tabelle genannt; die Rechnung ist daher keine Herstellerfreigabe.",
        "",
        "Carloflex bleibt erst nach prozesssicherer Festlegung seines im TDS "
        "nicht namentlich genannten Kunststoffprimers eine ausführbare "
        "Alternative.",
        "",
        "## Modellgrenzen",
        "",
    ]
    lines += [f"- {item}" for item in result["model_limitations"]]
    lines += [
        "",
        "## Primärquellen",
        "",
    ]
    for source in result["sources"].values():
        lines.append(f"- [{source['basis']}]({source['url']})")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--without-cfd", action="store_true",
        help="vorhandene CFD-Fallmatrix nicht als Sensitivität einlesen")
    args = parser.parse_args(argv)
    result = assess(include_cfd=not args.without_cfd)
    target = load_path_dir(result["parameter_hash"])
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "assessment.json"
    md_path = target / "assessment.md"
    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    md_path.write_text(to_markdown(result), encoding="utf-8")
    print(f"Lastpfadabschätzung: {md_path}")
    print(f"Ergebnis: {result['status']}")
    return 0 if result["system_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
