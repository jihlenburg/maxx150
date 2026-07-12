"""Analytische Nachweise, die keine FEM brauchen (Spec §6 LF5, Stoß, Freigang)."""
import params as PRM


def hood_clearance(p: PRM.Params = PRM.P) -> float:
    """Vertikaler Freigang Haubenunterkante über der Dachkante (mm).
    inf, wenn die Haube die Kante horizontal gar nicht erreicht."""
    if p.HOOD_TIP_REACH < p.EDGE_DIST:
        return float("inf")
    return p.H_RAISE + p.HOOD_UNDERSIDE_H - p.EDGE_H


def _segment_length(p: PRM.Params) -> float:
    L, W = PRM.outer_dims(p)
    return max(L, W) / 2 + p.LAP_L        # längster Schenkel eines L-Segments


def glue_shear_utilization(p: PRM.Params = PRM.P) -> float:
    """Auslastung der unteren Elastikfuge durch CTE-Differenz ASA<->GFK.
    Bezugslänge ist das SEGMENT (Segmentierung entkoppelt die Gesamtlänge!)."""
    dT = max(p.T_MAX - p.T_CURE, p.T_CURE - p.T_MIN)
    delta = (p.CTE_ASA - p.CTE_ROOF) * _segment_length(p) * dT   # mm gesamt
    gamma = (delta / 2) / p.GLUE_GAP                             # Schubverzerrung je Ende
    return gamma / p.GLUE_SHEAR_CAP


def glue_load_shear(p: PRM.Params, f_inplane: float) -> dict:
    """Spec-Kriterium 3: lastinduzierter Schub in der unteren Klebfuge
    <= 0.1 N/mm² dauerhaft. Tragend nur die Rillenraupe (konservativ)."""
    groove_len = PRM.groove_centerline_len(p)
    a_bond = groove_len * p.GROOVE_W
    tau = f_inplane / a_bond
    return {"tau_MPa": tau, "tau_zul_MPa": 0.1, "PASS": tau <= 0.1}


def side_screw_pullout(p: PRM.Params) -> dict:
    """Spec-Kriterium 4: Auszugstragfähigkeit einer Seitenschraube (ST4.2)
    in der Adapter-Innenwand. Gewindeeingriff = Bandbreite, konservativ nur
    12 mm angesetzt; Scherfestigkeit = 0.5 * Dauerzulässigkeit."""
    d, l_e = 4.2, 12.0
    import math
    sig_lang, _ = PRM.allowables(p)
    f_zul = math.pi * d * l_e * 0.5 * sig_lang
    f_erf = 100.0        # Anpresssicherung der Platte, real winzig
    return {"F_zul_N": f_zul, "F_erf_N": f_erf, "PASS": f_zul >= f_erf}


def joint_checks(p: PRM.Params, f_inplane: float) -> dict:
    """Konservativer Stoßnachweis: die volle horizontale Last geht durch
    EINEN Stoß (real verteilt sie sich auf vier)."""
    lap_h = PRM.lap_height(p)
    band = PRM.min_band(p)
    a_lap = p.LAP_L * band                       # Scherfläche der Überlappung
    tau = f_inplane / a_lap
    _, sig_kurz = PRM.allowables(p)               # sig_lang (dauerhaft) ungenutzt hier
    tau_zul = 0.5 * sig_kurz                     # Schub ~ 0.5 * sigma (v. Mises)
    # Lochleibung der M5-Schraube im ASA (Kurzzeitfall):
    lochleibung = f_inplane / (p.JOINT_BOLT_D * lap_h)
    lochleibung_zul = sig_kurz
    return {
        "tau_MPa": tau, "tau_zul_MPa": tau_zul,
        "lochleibung_MPa": lochleibung, "lochleibung_zul_MPa": lochleibung_zul,
        "PASS": tau < tau_zul and lochleibung < lochleibung_zul,
    }
