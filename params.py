"""Zentrale Parameterdatei — einzige Quelle der Wahrheit.
Längen mm, Kräfte N, Spannungen MPa, Temperaturen °C.
Quellen: Belluna-Anleitung (22 S.), Challenger-Dachdiagramm (35 mm X-Modelle),
Spec docs/superpowers/specs/2026-07-12-belluna-adapter-design.md.
Mit 'Messkampagne N' markierte Defaults sind Schätzwerte, die der User
per Messschieber ersetzt (Spec §8)."""
import hashlib
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Params:
    # --- Dachausschnitt / Fahrzeug ---
    CUTOUT_W: float = 400.0      # Sollmaß Ausschnitt (Anleitung, Messkampagne 6)
    CUTOUT_R: float = 5.0        # Eckenradius R5
    ROOF_T: float = 35.0         # Dachstärke X-Modelle (Messkampagne 8)
    EDGE_DIST: float = 250.0     # Ausschnitt-Hinterkante -> Dachkante (Messkampagne 7)
    EDGE_H: float = 55.0         # Höhe Dachkante über Dachebene (Messkampagne 7)
    # --- Haubengeometrie für Freigang-Check (Messkampagne 7) ---
    HOOD_TIP_REACH: float = 130.0   # horizontaler Haubenüberstand über Ausschnitt-Hinterkante
    HOOD_UNDERSIDE_H: float = 30.0  # Haubenunterkante am Überstand über Plattensitz
    CLEAR_MIN: float = 5.0          # geforderter Freigang
    H_CG: float = 160.0             # Angriffshöhe Windlast über Deckfläche
    # --- Erhöhung / Klebefuge ---
    H_RAISE: float = 28.0        # Zielerhöhung inkl. Klebespalt
    GLUE_GAP: float = 3.0        # Elastikfuge unten = Noppenhöhe (Thermik!)
    GLUE_SHEAR_CAP: float = 0.5  # zulässige Schubverzerrung der Fuge (50 %, Sika-Klasse)
    T_CURE: float = 20.0         # Verklebetemperatur
    # --- Deckflächenbreiten je Seite (Messkampagne 1/2) ---
    W_TOP_FRONT: float = 50.0
    W_TOP_REAR: float = 50.0
    W_TOP_LEFT: float = 50.0
    W_TOP_RIGHT: float = 50.0
    R_OUT: float = 12.0          # Außeneckenradius
    # --- Freistellung Gussets oben innen (Messkampagne 4) ---
    REC_GUSSET_W: float = 18.0
    REC_GUSSET_D: float = 3.0
    # --- Unterseite: Kleberille + Noppen ---
    GROOVE_OFF: float = 15.0     # Rillenbeginn ab Öffnungskante
    GROOVE_W: float = 8.0
    GROOVE_D: float = 2.0
    NOPPLE_R: float = 4.0
    NOPPLE_SPACING: float = 60.0
    CHAMFER_OUT: float = 4.0     # Fase Außenkante unten (Sika-Kehle)
    # --- Segmentierung ---
    N_SEGMENTS: int = 4          # nur 4 unterstützt (Quadranten)
    LAP_L: float = 25.0          # Halbüberlappung am Stoß
    TOL_JOINT: float = 0.25      # Passungsluft je Fügefläche
    JOINT_BOLT_D: float = 4.5    # M4-Durchgang
    JOINT_BOLT_OFF: float = 35.0 # Bolzenlage ab Öffnungskante (kollidiert nicht mit Rille)
    JOINT_CB_D: float = 8.5     # Zylindersenkung Kopf (DIN912 M4)
    JOINT_CB_T: float = 4.5
    JOINT_NUT_AF: float = 7.4    # Sechskant-Schlüsselweite Muttertasche
    JOINT_NUT_T: float = 3.5
    SEG_MAX_BBOX: float = 300.0  # zulässige Segment-Boundingbox (Druckservice)
    # --- Lüfter / Lasten (Spec §3/§6) ---
    FAN_MASS: float = 6.5        # kg (Maxxfan-Hüllkurve; Belluna 5.0)
    V_DESIGN_KMH: float = 200.0  # 160 Reise + Böenreserve
    CD_HOOD: float = 1.2
    A_HOOD: float = 0.10         # m² projiziert, Haube offen
    SF_WIND: float = 2.0
    G_VERT: float = 4.0          # Schlechtweg vertikal
    G_LAT: float = 2.0           # Schlechtweg quer
    CLAMP_FORCE: float = 2400.0  # 4 x 600 N aus 0,7 Nm (Anleitung), konservativ
    SNOW_LOAD: float = 200.0     # N auf Grundfläche
    T_MIN: float = -20.0
    T_MAX: float = 85.0
    # --- Material ASA (23 °C Basiswerte) + Abminderung (Spec §6) ---
    E_BASE: float = 2000.0
    SIGMA_BASE: float = 40.0
    NU: float = 0.35
    RHO: float = 1070.0          # kg/m^3
    CTE_ASA: float = 90e-6       # 1/K
    CTE_ROOF: float = 25e-6      # 1/K (GFK)
    DERATE_TEMP: float = 0.35    # bei 85 °C
    DERATE_Z: float = 0.6        # FDM-Schichthaftung
    DERATE_CREEP: float = 0.4    # Dauerlast
    INFILL_FACTOR: float = 0.5   # Homogenisierung >=4 Perimeter + 40 % Gyroid
    # --- FEM-Steuerung ---
    MESH_MM: float = 10.0        # Produktionsnetz
    MESH_MM_TEST: float = 20.0   # Grobnetz für Tests
    DEFL_TOP_MAX: float = 0.5    # zulässige Deckflächenverformung (Dichtheit)


P = Params()

# Vierkantwellen laut Anleitung: (Länge, Wandstärke min, max)
SHAFT_TABLE = ((120.0, 27.0, 47.0), (140.0, 48.0, 67.0), (160.0, 68.0, 80.0))


def effective_wall(p: Params = P) -> float:
    """Einbauwandstärke aus Lüftersicht: Dach + Adapter (inkl. Klebefuge)."""
    return p.ROOF_T + p.H_RAISE


def select_shaft(p: Params = P) -> float:
    t = effective_wall(p)
    for length, lo, hi in SHAFT_TABLE:
        if lo <= t <= hi:
            return length
    raise ValueError(f"Effektive Wandstärke {t} mm außerhalb 27-80 mm")


def outer_dims(p: Params = P):
    """(Länge in x = Fahrtrichtung, Breite in y)."""
    return (p.CUTOUT_W + p.W_TOP_FRONT + p.W_TOP_REAR,
            p.CUTOUT_W + p.W_TOP_LEFT + p.W_TOP_RIGHT)


def wind_force(p: Params = P) -> float:
    """Horizontale Auslegungswindlast inkl. Sicherheitsfaktor (N)."""
    v = p.V_DESIGN_KMH / 3.6
    q = 0.5 * 1.2 * v * v            # Staudruck, rho_Luft 1.2 kg/m^3
    return q * p.A_HOOD * p.CD_HOOD * p.SF_WIND


def allowables(p: Params = P):
    """(dauerhaft, kurzzeitig) zulässige von-Mises-Spannung in MPa."""
    kurz = p.SIGMA_BASE * p.DERATE_TEMP * p.DERATE_Z
    return kurz * p.DERATE_CREEP, kurz


def params_hash(p: Params = P) -> str:
    """8-Zeichen-Hash über alle Parameter (verknüpft Report <-> Druckdateien)."""
    blob = repr(sorted(asdict(p).items())).encode()
    return hashlib.sha256(blob).hexdigest()[:8]
