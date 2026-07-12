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
    # --- Haubengeometrie für Freigang-Check (MaxxFan-Deluxe-Maßblatt) ---
    HOOD_TIP_REACH: float = 179.0   # Haubenüberstand über Ausschnitt-Hinterkante, offen (Maßblatt)
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
    JOINT_BOLT_D: float = 5.5    # M5-Durchgang (M4 fiel bei 480 N Lochleibungs-Nachweis durch)
    JOINT_BOLT_OFF: float = 35.0 # Bolzenlage ab Öffnungskante (kollidiert nicht mit Rille)
    JOINT_CB_D: float = 10.0     # Zylindersenkung Kopf (DIN912 M5)
    JOINT_CB_T: float = 5.0
    JOINT_NUT_AF: float = 8.0    # Sechskant-Schlüsselweite Muttertasche (M5)
    JOINT_NUT_T: float = 4.0
    SEG_MAX_BBOX: float = 300.0  # zulässige Segment-Boundingbox (Druckservice)
    # --- Lüfter / Lasten (Spec §3/§6) ---
    FAN_MASS: float = 6.5        # kg (Maxxfan-Hüllkurve; Belluna 5.0)
    V_DESIGN_KMH: float = 200.0  # 160 Reise + Böenreserve
    CD_HOOD: float = 1.2
    A_HOOD: float = 0.108        # m² projiziert, Haube offen: MaxxFan Deluxe 0.408 x (0.236+0.028)
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
    INFILL_FACTOR: float = 1.0   # 100 % Infill (Kammern übernehmen die Gewichtsreduktion,
                                  # kein Slicer-Infill mehr nötig)
    # --- Rippenkammern (geschlossene Zellen; User-Entscheidung 2026-07-12) ---
    CHAMBERS: bool = True
    DECK_T: float = 5.0        # Deckplatte: Gusset-Freistellung 3 + 2 Rest
    BOTTOM_T: float = 4.0      # Bodenplatte: enthält Kleberille (Tiefe 2)
    INNER_WALL: float = 8.0    # Schraubgrund seitliche Verschraubung
    CHAMBER_W: float = 15.0    # radiale Kammerbreite (2 konzentrische Ringe)
    CHAMBER_RIB: float = 4.0   # Steg zwischen den Kammerringen
    CELL_L: float = 45.0       # Zellenteilung entlang der Seite
    CELL_RIB: float = 3.0      # Quersteg zwischen Zellen
    SOLID_CORNER: float = 45.0 # massiv ab Eck-Außenkante
    SOLID_JOINT_HALF: float = 40.0  # massiv um Seitenmitte (deckt Lap + M5)
    CHEVRON_DEG: float = 47.0  # Kammerboden-Zelt; >45° mit Reserve (DFM-Kante)
    VENT_D: float = 4.0        # Druckausgleichsbohrung je Zelle (FDM; SLS verworfen)
    VENT_Z: float = 17.0       # Bohrungshöhe (weit weg von Schraubzone)
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


def validate(p: Params = P) -> None:
    """Konsistenz-Ungleichungen (Spec §5: abbrechen statt defekte Artefakte).
    Empirisch belegte Brecher aus dem Final-Review: W_TOP<42 öffnet Kammerring 2
    zur Außenwand, REC_GUSSET_D>DECK_T-2 durchstößt die Kammerdecke."""
    import math
    fehler = []
    w_min = min(p.W_TOP_FRONT, p.W_TOP_REAR, p.W_TOP_LEFT, p.W_TOP_RIGHT)
    if p.CHAMBERS:
        aussenwand = w_min - (p.INNER_WALL + 2 * p.CHAMBER_W + p.CHAMBER_RIB)
        if aussenwand < 2.4:
            fehler.append(f"Außenwand hinter Kammerring 2 nur {aussenwand:.1f} mm (< 2.4): "
                          f"W_TOP erhöhen oder CHAMBER_W/INNER_WALL senken")
        deck_rest = p.DECK_T - p.REC_GUSSET_D
        if deck_rest < 2.0:
            fehler.append(f"Deckplatten-Rest über Kammern nur {deck_rest:.1f} mm (< 2.0): "
                          f"DECK_T an REC_GUSSET_D anpassen (Messkampagne 4!)")
        kammerdecke = (p.H_RAISE - p.GLUE_GAP) - p.DECK_T
        apex = p.BOTTOM_T + math.tan(math.radians(p.CHEVRON_DEG)) * p.CHAMBER_W / 2
        if apex > kammerdecke - 1.0:
            fehler.append(f"Chevron-Apex {apex:.1f} mm erreicht Kammerdecke {kammerdecke:.1f} mm")
        if not (apex + p.VENT_D / 2 + 0.5 <= p.VENT_Z <= kammerdecke - p.VENT_D / 2 - 0.5):
            fehler.append(f"VENT_Z={p.VENT_Z} außerhalb des Kammer-z-Bands "
                          f"({apex + p.VENT_D/2 + 0.5:.1f}..{kammerdecke - p.VENT_D/2 - 0.5:.1f})")
    if p.JOINT_BOLT_OFF + p.JOINT_CB_D / 2 > w_min - 2.4:
        fehler.append("M5-Kopfsenkung erreicht die Außenwand: JOINT_BOLT_OFF/W_TOP prüfen")
    if p.GLUE_GAP < 2.0:
        fehler.append("GLUE_GAP < 2 mm: Thermik-Elastikfuge und Noppen-Fixierflächen brauchen >= 2")
    if p.NOPPLE_SPACING < 3 * p.NOPPLE_R:
        fehler.append("NOPPLE_SPACING < 3*NOPPLE_R: Noppen überlappen")
    if fehler:
        raise ValueError("Parameter-Validierung fehlgeschlagen:\n- " + "\n- ".join(fehler))
