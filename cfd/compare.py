"""Vergleicht die CFD-Fallmatrix und erzeugt die Lastübergabe-Metadaten."""
from __future__ import annotations

import json
import math
from pathlib import Path

import params as PRM
from cfd.config import (
    CASES,
    CASE_ORDER,
    COMPARISON_SCHEMA_REV,
    OPEN_MEDIUM,
    cfd_hash,
    comparison_hash,
)
from project_paths import cfd_dir, cfd_matrix_dir


def result_path(case_name: str) -> Path:
    case = CASES[case_name]
    return cfd_dir(cfd_hash(case)) / "cases" / case.name / "result.json"


def _relative_change(coarse: float, medium: float) -> float:
    return abs(medium - coarse) / max(abs(medium), 1e-12)


def _vector_changes(coarse: list[float], medium: list[float]) -> list[float]:
    return [_relative_change(a, b) for a, b in zip(coarse, medium)]


def compare() -> dict:
    results = {}
    for name in CASE_ORDER:
        path = result_path(name)
        if not path.exists():
            raise RuntimeError(f"CFD-Ergebnis fehlt: {path}")
        results[name] = json.loads(path.read_text(encoding="utf-8"))

    coarse = results["open_front_coarse"]
    medium = results[OPEN_MEDIUM.name]
    factor = OPEN_MEDIUM.model_factor
    force = [value * factor for value in medium["force_mean_N"]]
    moment_at_base = [value * factor for value in medium["moment_mean_Nm"]]
    horizontal = math.hypot(force[0], force[1])
    resultant = math.sqrt(sum(value * value for value in force))
    top_z_mm = PRM.P.H_RAISE - PRM.P.GLUE_GAP
    top_z_m = top_z_mm * 0.001
    # Äquivalente Last auf der Adapter-Deckfläche: M_frei = M_Basis - r×F.
    moment_at_top = [
        moment_at_base[0] + top_z_m * force[1],
        moment_at_base[1] - top_z_m * force[0],
        moment_at_base[2],
    ]
    existing_pitch = PRM.wind_force(PRM.P) * (PRM.P.H_CG + top_z_mm) * 0.001
    existing_vertical_road = PRM.P.FAN_MASS * 9.81 * PRM.P.G_VERT

    data = {
        "schema": COMPARISON_SCHEMA_REV,
        "status": "PRELIMINARY_CFD_MATRIX",
        "structural_use": "INFORMATIONAL_NON_GATING",
        "comparison_hash": comparison_hash(),
        "case_hashes": {name: cfd_hash(CASES[name]) for name in CASE_ORDER},
        "cases": results,
        "open_mesh_sensitivity": {
            "force_component_relative_change": _vector_changes(
                coarse["force_mean_N"], medium["force_mean_N"]),
            "moment_component_relative_change": _vector_changes(
                coarse["moment_mean_Nm"], medium["moment_mean_Nm"]),
            "drag_relative_change": _relative_change(
                coarse["drag_mean_N"], medium["drag_mean_N"]),
            "lift_relative_change": _relative_change(
                coarse["lift_mean_N"], medium["lift_mean_N"]),
            "cell_ratio_medium_to_coarse": (
                medium["mesh"]["cells"] / coarse["mesh"]["cells"]),
            "interpretation": (
                "Zwei Netze zeigen nur Sensitivität; für einen formalen "
                "Konvergenznachweis fehlt mindestens ein Feinnetz."
            ),
        },
        "structural_transfer_open_medium": {
            "model_factor": factor,
            "force_N": force,
            "moment_about_adapter_base_Nm": moment_at_base,
            "free_moment_at_adapter_top_Nm": moment_at_top,
            "load_application_z_m": top_z_m,
            "horizontal_resultant_N": horizontal,
            "force_resultant_N": resultant,
            "comparison_envelopes": {
                "existing_horizontal_N": PRM.wind_force(PRM.P),
                "existing_pitch_Nm": existing_pitch,
                "existing_vertical_road_N": existing_vertical_road,
            },
            "utilization_of_existing_envelopes": {
                "horizontal": horizontal / PRM.wind_force(PRM.P),
                "pitch_y": abs(moment_at_base[1]) / existing_pitch,
                "vertical_vs_road_magnitude": abs(force[2]) / existing_vertical_road,
            },
        },
        "limitations": [
            "Belluna-Hülle aus Einbauanleitung rekonstruiert, kein Hersteller-CAD",
            "stationäres RANS ohne Prismenschichten und Fahrzeug-Grenzschicht",
            "nur Frontalanströmung bei 200 km/h",
            "offener Zustand bislang nur auf Grob- und Mittelnetz",
            "keine experimentelle Korrelation",
        ],
    }

    target = cfd_matrix_dir(comparison_hash())
    target.mkdir(parents=True, exist_ok=True)
    output = target / "comparison.json"
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    c = data["open_mesh_sensitivity"]
    t = data["structural_transfer_open_medium"]
    lines = [
        "# Vorläufige CFD-Fallmatrix",
        "",
        f"Matrix `{data['comparison_hash']}` · Status **{data['status']}**",
        "",
        "## Kräfte ohne Modellfaktor",
        "",
        "| Fall | Zellen | Fx [N] | Fy [N] | Fz [N] | My [Nm] |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in CASE_ORDER:
        item = results[name]
        f = item["force_mean_N"]
        m = item["moment_mean_Nm"]
        lines.append(
            f"| `{name}` | {item['mesh']['cells']:,} | {f[0]:.2f} | "
            f"{f[1]:.2f} | {f[2]:.2f} | {m[1]:.3f} |".replace(",", ".")
        )
    lines.extend((
        "",
        "## Offenes Grob- gegen Mittelnetz",
        "",
        f"- Zellfaktor: **{c['cell_ratio_medium_to_coarse']:.2f}×**",
        f"- Änderung Widerstand: **{c['drag_relative_change']:.1%}**",
        f"- Änderung Auftrieb: **{c['lift_relative_change']:.1%}**",
        f"- Komponentenänderung Kraft: `{c['force_component_relative_change']}`",
        f"- Komponentenänderung Moment: `{c['moment_component_relative_change']}`",
        "",
        "Das ist eine Netzsensitivität, kein formaler Konvergenznachweis.",
        "",
        "## Nicht freigabewirksame Lastübergabe",
        "",
        f"Mittelnetz × {t['model_factor']:.2f}: Kraft `{t['force_N']}` N, "
        f"Moment um Adapterbasis `{t['moment_about_adapter_base_Nm']}` Nm.",
        f"Äquivalentes freies Moment an der Deckfläche: "
        f"`{t['free_moment_at_adapter_top_Nm']}` Nm.",
        "",
        "Die anschließende CalculiX-Prüfung ist informationshalber und "
        "ändert die bestehenden Freigabelastfälle nicht.",
        "",
    ))
    (target / "comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"CFD-VERGLEICH: {output}", flush=True)
    return data


if __name__ == "__main__":
    compare()
