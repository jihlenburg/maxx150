"""Analytische Nachweise, die keine FEM brauchen (Spec §6 LF5, Stoß, Freigang)."""
import params as PRM


def hood_clearance(p: PRM.Params = PRM.P) -> float:
    """Vertikaler Freigang Haubenunterkante über der Dachkante (mm).
    inf, wenn die Haube die Kante horizontal gar nicht erreicht."""
    if p.HOOD_TIP_REACH < p.EDGE_DIST:
        return float("inf")
    return p.H_RAISE + p.HOOD_UNDERSIDE_H - p.EDGE_H


def _assembly_length(p: PRM.Params) -> float:
    L, W = PRM.outer_dims(p)
    return max(L, W)


def glue_shear_utilization(p: PRM.Params = PRM.P) -> float:
    """Auslastung der unteren Elastikfuge durch CTE-Differenz ASA<->GFK.
    Bezugslänge ist der vollständig epoxidverklebte und verschraubte Rahmen:
    Die Drucksegmentierung stellt nach dem Fügen keine thermische Entkopplung
    dar. Symmetrische Dehnung wird weiterhin je Rahmenende mit delta/2
    angesetzt."""
    dT = max(p.T_MAX - p.T_CURE, p.T_CURE - p.T_MIN)
    delta = (p.CTE_ASA - p.CTE_ROOF) * _assembly_length(p) * dT  # mm gesamt
    gamma = (delta / 2) / p.GLUE_GAP                             # Schubverzerrung je Ende
    return gamma / p.GLUE_SHEAR_CAP


def glue_load_shear(p: PRM.Params, f_inplane: float) -> dict:
    """Spec-Kriterium 3: lastinduzierter Schub in der unteren Klebfuge
    <= 0.05 N/mm². Tragend nur die Rillenraupe (konservativ); der Wert ist
    die stark abgeminderte Elastikfugen-Annahme aus docs/load-paths.md."""
    a_bond = PRM.groove_bond_area(p)
    tau = f_inplane / a_bond
    return {"tau_MPa": tau, "tau_zul_MPa": 0.05, "PASS": tau <= 0.05}


def side_screw_pullout(p: PRM.Params) -> dict:
    """Auszug einer Belluna-ST4.2x25 in der oberen Adapter-Innenwand.

    Jede Seite besitzt lokale Vollmaterialrippen für beide Belluna-Paare
    ±140/±165; acht der sechzehn möglichen Pfade werden real benutzt. Vom
    nominellen 25-mm-Schraubpfad werden trotzdem nur 12 mm Gewindeeingriff
    angesetzt; Scherfestigkeit = 0.5*Dauerzulässigkeit.
    """
    d, l_e = p.BOT_KRAGEN_SCREW_D, 12.0
    import math
    sig_lang, _ = PRM.allowables(p)
    f_ref = math.pi * d * l_e * 0.5 * sig_lang
    # Zusätzlicher Detailfaktor für FDM-Gewinde, Pilotloch und lokale Kerbe.
    # Die unverminderte Kreisfläche bleibt als Referenz explizit sichtbar.
    f_zul = 0.5 * f_ref
    f_erf = 100.0        # Anpresssicherung der Platte, real winzig
    return {"F_ref_N": f_ref, "detail_factor": 0.5,
            "F_zul_N": f_zul, "F_erf_N": f_erf, "PASS": f_zul >= f_erf}


def joint_checks(p: PRM.Params, f_inplane: float) -> dict:
    """Konservativer Stoßnachweis: die volle horizontale Last geht durch
    EINEN Stoß (real verteilt sie sich auf vier)."""
    lap_h = PRM.lap_height(p)
    band = PRM.min_band(p)
    a_lap = p.LAP_L * band                       # Scherfläche der Überlappung
    tau = f_inplane / a_lap
    _, sig_kurz = PRM.allowables(p)               # sig_lang (dauerhaft) ungenutzt hier
    tau_zul = 0.5 * sig_kurz                     # Schub ~ 0.5 * sigma (v. Mises)
    # Ein oder zwei M5 je Stoß. In jedem Fall muss ein einzelner Bolzen den
    # vollen Fall allein tragen können; bei zwei Bolzen ist das der Restfall.
    bolt_count = len(p.JOINT_BOLT_OFFS)
    lochleibung = (f_inplane / bolt_count) / (p.JOINT_BOLT_D * lap_h)
    lochleibung_ein_rest = f_inplane / (p.JOINT_BOLT_D * lap_h)
    lochleibung_zul = sig_kurz
    return {
        "tau_MPa": tau, "tau_zul_MPa": tau_zul,
        "m5_count_per_joint": bolt_count,
        "lochleibung_MPa": lochleibung,
        "lochleibung_ein_rest_MPa": lochleibung_ein_rest,
        "lochleibung_zul_MPa": lochleibung_zul,
        "PASS": (tau < tau_zul
                 and lochleibung_ein_rest < lochleibung_zul),
    }
