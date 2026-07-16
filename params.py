"""Zentrale Parameterdatei — einzige Quelle der Wahrheit.
Längen mm, Kräfte N, Spannungen MPa, Temperaturen °C.
Quellen: Belluna-Anleitung (22 S.), Challenger-Dachdiagramm (35 mm X-Modelle),
aktuelle Auslegung ``docs/design.md`` und Referenzen unter ``references/``.
Als Messpunkte markierte Defaults werden am realen Fahrzeug ersetzt."""
import hashlib
import math
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Params:
    # --- Meta: Geometrie-Revision. Erhöhen bei geometrie-wirksamen CODE-
    # Änderungen (z. B. neue Fillets/Radien), auch wenn kein Messwert
    # wechselt -- ändert params_hash, damit Druckfiles/Report eindeutig
    # bleiben (Task 15, Heatmap-Fix Noppenfuß-Radius) ---
    GEOM_REV: int = 6            # 6: rotationsidentisches Universal-Segment;
                                  # Dach- und Belluna-Schraubraster entkoppelt
    # --- Dachausschnitt / Fahrzeug ---
    CUTOUT_W: float = 400.0      # Sollmaß Ausschnitt (Anleitung; Messpunkt C1)
    CUTOUT_R: float = 5.0        # Eckenradius R5
    ROOF_T: float = 35.0         # Dachstärke X-Modelle (B3)
    EDGE_DIST: float = 250.0     # Ausschnitt-Hinterkante -> Dachkante (B1a+B1b)
    EDGE_H: float = 55.0         # Höhe Dachkante über Dachebene (B2)
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
    # --- Deckflächenbreiten je Seite (aus A1/A2 abgeleitete Designwahl) ---
    W_TOP_FRONT: float = 50.0
    W_TOP_REAR: float = 50.0
    W_TOP_LEFT: float = 50.0
    W_TOP_RIGHT: float = 50.0
    R_OUT: float = 12.0          # Außeneckenradius
    # --- Obere Plattenschnittstelle / Entwässerung ---
    PLATE_OUTER_W: float = 450.0     # Belluna-Flansch, A1a/A1b bestätigt
    PLATE_KRAGEN_W: float = 397.0    # A3a gemessen 2026-07-14
    PLATE_KRAGEN_MEASURED: bool = True
    TOP_DRAIN_RUN: float = 13.0      # max. Breite der äußeren Entwässerungsfase
    TOP_DRAIN_DEG: float = 47.0      # selbsttragend in Druckorientierung
    TOP_DRAIN_SUPPORT_MARGIN: float = 2.0  # ebene Auflage über Flanschrand hinaus
    # --- Freistellung Gussets oben innen (Messpunkt A4) ---
    REC_GUSSET_W: float = 18.0
    REC_GUSSET_D: float = 0.0    # GEMESSEN 2026-07-13 (A4 erledigt):
                                  # die Belluna-Gussets tauchen mit dem Unterkragen
                                  # in den Ausschnitt, NICHTS ragt über die
                                  # Auflageebene -> keine Deck-Freistellung.
                                  # 0 = Cut wird zum No-Op (Ring liegt über der
                                  # Deckfläche); der digitale Passungscheck
                                  # belegt die vollständige Stegauflage.
    # --- Unterseite: Kleberille + Noppen ---
    GROOVE_OFF: float = 15.0     # Rillenbeginn ab Öffnungskante
    GROOVE_W: float = 8.0
    GROOVE_D: float = 2.0
    NOPPLE_R: float = 4.0
    NOPPLE_SPACING: float = 60.0
    NOPPLE_FILLET: float = 1.5   # Kerbentschärfung am Zylinderansatz (Übergangskegel,
                                  # Heatmap 2026-07-12: alle LF-Hotspots am Noppenfuß)
    CHAMFER_OUT: float = 4.0     # Fase Außenkante unten (Elastikfugen-Kehle)
    # --- Segmentierung ---
    N_SEGMENTS: int = 4          # nur 4 unterstützt (Quadranten)
    LAP_L: float = 25.0          # Halbüberlappung am Stoß
    TOL_JOINT: float = 0.25      # Passungsluft je Fügefläche
    JOINT_BOLT_D: float = 5.5    # M5-Durchgang (M4 fiel bei 480 N Lochleibungs-Nachweis durch)
    JOINT_BOLT_OFF: float = 30.0 # strukturell zwischen Kleberille und Entwässerungsfase
    JOINT_CB_D: float = 10.0     # Zylindersenkung Kopf (DIN912 M5)
    JOINT_CB_T: float = 6.0
    JOINT_NUT_AF: float = 8.0    # Sechskant-Schlüsselweite Muttertasche (M5)
    JOINT_NUT_T: float = 4.0
    SEG_MAX_BBOX: float = 300.0  # zulässige Segment-Boundingbox (Druckservice)
    # --- Unterkragen (User-Entscheidung 2026-07-13): dupliziert den Belluna-
    # Einbaukragen nach UNTEN -- taucht in den Dachausschnitt und wird dort
    # SEITLICH verschraubt (Methode der Belluna-Anleitung; mechanische
    # Redundanz zum Kleber am Dach-Interface). Dieses Dachinterface ist seit
    # GEOM_REV 6 bewusst vom 3/2/3/2-Lochbild der Belluna-Platte entkoppelt:
    # acht umlaufend gleiche Löcher bei ±140 gehen in den nachgerüsteten
    # Holzrahmen. Die Belluna-Platte nutzt oben weiterhin ihre realen
    # ±140/±165-Positionen, dort aber universelle lokale Vollmaterialrippen.
    # So bleibt jedes der vier Druckteile rotationsidentisch. Die 16
    # beiliegenden ST4.2x25 bleiben vollständig zugeordnet: 8x
    # Platte->Adapter und 8x Adapter->Holz. KEIN Loch bei 0 (Segmentstoß).
    # Druckorientierung kopfüber -> Kragen zeigt im Druck nach oben,
    # 45°-Übergang (BOT_KRAGEN_TRANS) selbsttragend wie der Noppenkegel.
    BOT_KRAGEN: bool = True
    BOT_KRAGEN_T: float = 4.0        # Wandstärke
    BOT_KRAGEN_CLEAR: float = 1.0    # Belluna-Nennschnittstelle: ~398 in 400
    BOT_KRAGEN_DEPTH: float = 19.0   # Eintauchtiefe unter die Dachoberfläche (wie Belluna)
    BOT_KRAGEN_TRANS: float = 3.0    # 45°-Übergangsfase Öffnungswand -> Kragen
    BOT_KRAGEN_HOLE_D: float = 4.0   # Schraubenloch (Kernloch 3 im Dach vorbohren)
    BOT_KRAGEN_HOLE_Z: float = 10.0  # Lochmitte unter Dachoberfläche (wie Belluna)
    BOT_KRAGEN_SCREW_D: float = 4.2  # Belluna-Lieferumfang: ST 4.2x25
    BOT_KRAGEN_SCREW_L: float = 25.0
    BOT_KRAGEN_HOLE_OFFS: tuple = (-140.0, 140.0)  # identisch auf allen 4 Seiten
    # Obere Belluna-Platte: jede Segmenthälfte bietet BEIDE möglichen
    # Außenloch-Abstände. Nur das am realen Plattenloch liegende Paar wird
    # verschraubt; es entstehen keine ungenutzten offenen Löcher.
    PLATE_SCREW_OFFS: tuple = (-165.0, -140.0, 140.0, 165.0)
    PLATE_SCREW_Z_FROM_TOP: float = 10.0  # F2: Lochmitte unter Plattenauflage
    PLATE_SCREW_BOSS_HALF: float = 5.0    # 10-mm-Rippe um ST4.2-Schraubachse
    PLATE_SCREW_BOSS_L: float = 25.0      # radialer Vollmaterialpfad
    PLATE_KRAGEN_D: float = 19.0     # Belluna-Einbaukragen-Tiefe (A4a GEMESSEN
                                      # 2026-07-13): dessen Spitze endet bei
                                      # top_z - 19 -- Schnittstellen-Gate unten
    PLATE_KRAGEN_Z_CLEAR_MIN: float = 2.0  # axialer Mindestfreigang zur Übergangsfase
    ROOF_WOOD_FRAME_W: float = 30.0  # Mindestbreite des PU-verklebten Schraubgrunds
    ROOF_WOOD_FRAME_CONFIRMED: bool = False  # erst nach Einbau/Probeschraube True
    # --- Lüfter / Lasten (Spec §3/§6) ---
    FAN_MASS: float = 6.5        # kg (Maxxfan-Hüllkurve; Belluna 5.0)
    V_DESIGN_KMH: float = 200.0  # 160 Reise + Böenreserve
    CD_HOOD: float = 1.2
    A_HOOD: float = 0.108        # m² projiziert, Haube offen: MaxxFan Deluxe 0.408 x (0.236+0.028)
    SF_WIND: float = 2.0
    G_VERT: float = 4.0          # Schlechtweg vertikal
    G_LAT: float = 2.0           # Schlechtweg quer
    CLAMP_FORCE: float = 2400.0  # KONSERVATIVE HÜLLKURVE: real keine harte Klemmung
                                 # (nur Zierblende von unten, User 2026-07-12); deckt Montagefälle
    SNOW_LOAD: float = 200.0     # N auf Grundfläche
    T_MIN: float = -20.0
    T_MAX: float = 85.0
    # --- Material: Würth ASA GF15, Verkehrsschwarz ähnlich RAL 9017 ---
    # Art.-Nr. 4954641200, 1,75 mm, 750-g-Spule. Plan-of-Record 2026-07-15.
    # 15 % Glasfaser, daher geschlossener Bauraum und gehärtete Düse. Das
    # schwarze Druckteil wird vor dem Dacheinbau zwingend mit dem in der
    # Montageanleitung festgelegten weißen 2K-PUR-System RAL 9003 beschichtet.
    #
    # WICHTIGE DATENGRENZE: Würth weist ausdrücklich darauf hin, dass die
    # mechanischen Kennwerte an Halbzeug und nicht an FDM-Probekörpern ermittelt
    # wurden. E_BASE und SIGMA_BASE sind deshalb konservative Projektannahmen;
    # Da XY-/Z-Coupons aktuell nicht realistisch verfügbar sind, bleiben die
    # Abminderungen dauerhafte Projektannahmen und der Status PROTOTYPE_ONLY.
    MATERIAL_NAME: str = ("Würth ASA GF15, Verkehrsschwarz RAL 9017 ähnlich "
                          "(Art.-Nr. 4954641200)")
    E_BASE: float = 3000.0       # MPa, Annahme für gedrucktes XY; Halbzeug 3520
    SIGMA_BASE: float = 45.0     # MPa, Annahme für gedrucktes XY; nicht 91,2 Halbzeug
    NU: float = 0.35             # keine chargenspezifische Herstellerangabe
    RHO: float = 1100.0          # kg/m³, Würth-Datenblatt 1,1 g/cm³
    HDT_045: float = 99.0        # °C, HDT/B bei 0,45 MPa laut Würth-Datenblatt
    HDT_182: float | None = None # bei 1,82 MPa nicht angegeben; nicht erfinden
    CTE_ASA: float = 60e-6       # 1/K, konservative Projektannahme; Datenblattlücke
    CTE_ROOF: float = 25e-6      # 1/K (GFK)
    DERATE_TEMP: float = 0.5     # Abminderung trotz weißem Decklack und HDT/B 99 °C
    DERATE_Z: float = 0.5        # streng geschätzt, da Würth keine FDM-Z-Werte nennt
    DERATE_CREEP: float = 0.4
    INFILL_FACTOR: float = 1.0   # 100 % Infill (Kammern übernehmen die Gewichtsreduktion,
                                  # kein Slicer-Infill mehr nötig)

    # Verfügbare Rückfalloption PC/ABS (User-Datenblatt 2026-07-14), bewusst
    # KEIN aktives Preset: rho 1090 kg/m³, E 1900 MPa, Zug 41 MPa,
    # HDT 110/96 °C (0,45/1,82 MPa), Bruchdehnung 6 %. UV-/CTE-Eignung und
    # Haftung des festgelegten Kleb-/Lacksystems wären neu zu qualifizieren.
    # --- Rippenkammern (geschlossene Zellen; User-Entscheidung 2026-07-12) ---
    CHAMBERS: bool = True
    DECK_T: float = 5.0        # Deckplatte: Gusset-Freistellung 3 + 2 Rest
    BOTTOM_T: float = 4.0      # Bodenplatte: enthält Kleberille (Tiefe 2)
    INNER_WALL: float = 8.0    # Schraubgrund seitliche Verschraubung
    CHAMBER_W: float = 15.0    # radiale Kammerbreite (2 konzentrische Ringe)
    CHAMBER_RIB: float = 4.0   # Steg zwischen den Kammerringen
    CELL_L: float = 43.0       # Zellenteilung entlang der Seite. Vent-Kanäle,
                                # die einer Universal-Schraubrippe zu nahe
                                # kommen, werden innerhalb ihrer Zelle lokal
                                # zur Ecke verschoben (model/frame.py).
    CELL_RIB: float = 3.0      # Quersteg zwischen Zellen
    SOLID_CORNER: float = 45.0 # massiv ab Eck-Außenkante
    SOLID_JOINT_HALF: float = 40.0  # massiv um Seitenmitte (deckt Lap + M5)
    CHEVRON_DEG: float = 47.0  # Kammerboden-Zelt; >45° mit Reserve (DFM-Kante)
    VENT_D: float = 4.0        # Druckausgleichsbohrung je Zelle (FDM; SLS verworfen)
    VENT_Z: float = 17.0       # Bohrungshöhe (weit weg von Schraubzone)
    # --- Eckkammern (optional; Herstellbarkeit: entlastet die vier massiven
    # Eckblöcke, Haupt-Schrumpfspannungs-Reservoirs -- Task 17) ---
    CORNER_CHAMBERS: bool = True    # seit 2026-07-12 Default EIN (User-Entscheidung
                                     # Task 20; Verzugs-/Gewichtsnutzen, FEM-verifiziert
                                     # Task 17). GEOM_REV bleibt (Parameter-, keine
                                     # Code-Änderung -- params_hash ändert sich über
                                     # das Feld selbst).
    CORNER_ANGLE_MARGIN: float = 18.0  # Grad Randabstand des 90°-Sektors je Seite
    CORNER_GAP: float = 3.0    # Mindestluft zwischen Ecksektor-Keepout und Zellraster
                                # (Review-Critical Task 17: model/frame.py::_corner_keepout)
    # --- FEM-Steuerung ---
    MESH_MM: float = 10.0        # Produktionsnetz
    MESH_MM_TEST: float = 20.0   # Grobnetz für Tests
    DEFL_TOP_MAX: float = 0.5    # zulässige Deckflächenverformung (Dichtheit)


P = Params()

# Vierkantwellen laut Anleitung: (Länge, Wandstärke min, max)
SHAFT_TABLE = ((120.0, 27.0, 47.0), (140.0, 48.0, 67.0), (160.0, 68.0, 80.0))

# Luftdichte (kg/m^3, 15 °C/1013 hPa) -- Modul-Konstante statt Magic Number
# in wind_force (Finalreview-Minor Task 1).
RHO_AIR = 1.2


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


def side_top_widths(p: Params = P) -> tuple:
    """Radiale Deckbreiten in der Rotationsreihenfolge REAR, RIGHT, FRONT, LEFT."""
    return (p.W_TOP_REAR, p.W_TOP_RIGHT, p.W_TOP_FRONT, p.W_TOP_LEFT)


def drainage_start(p: Params, side_width: float) -> float:
    """Radialkoordinate, ab der die äußere Entwässerungsfase beginnt.

    Der ebene Bereich trägt den Belluna-Flansch und die M5-Kopfsenkung. Nur
    die danach verbleibende, frei bewitterte Außenkante wird abgeschrägt.
    """
    outer = p.CUTOUT_W / 2 + side_width
    plate_keepout = p.PLATE_OUTER_W / 2 + p.TOP_DRAIN_SUPPORT_MARGIN
    bolt_keepout = (p.CUTOUT_W / 2 + p.JOINT_BOLT_OFF
                    + p.JOINT_CB_D / 2 + p.TOP_DRAIN_SUPPORT_MARGIN)
    return max(outer - p.TOP_DRAIN_RUN, plate_keepout, bolt_keepout)


def top_surface_z(p: Params, radius: float, side_width: float) -> float:
    """Sollhöhe der ebenen bzw. nach außen fallenden Deckfläche."""
    start = drainage_start(p, side_width)
    drop = max(0.0, radius - start) * math.tan(math.radians(p.TOP_DRAIN_DEG))
    return (p.H_RAISE - p.GLUE_GAP) - drop


def bot_kragen_hole_count(p: Params = P) -> int:
    """Gesamtzahl der seitlichen Dachschrauben."""
    return 4 * len(p.BOT_KRAGEN_HOLE_OFFS)


def min_band(p: Params = P) -> float:
    """Schmalste Deckflächenbreite über alle vier Seiten (M1/Ledger 23/30/33:
    konsolidierter Ersatz für die früher mehrfach kopierte
    min(W_TOP_FRONT, W_TOP_REAR, W_TOP_LEFT, W_TOP_RIGHT) -- konservative
    Bandbreite für Stoß-/Überlappungsnachweise, die absichtlich NICHT die
    seitenspezifische Breite ausnutzen: die volle Stoßlast wird konservativ
    durch die schmalste Seite angesetzt). NICHT verwenden für die
    DFM-Brückenflächen-Formel (model/dfm.py::_allowed_bridge_area) -- die
    nutzt seit Ledger 21/22 bewusst die Summe aller vier W_TOP statt eines
    globalen Minimums (seitenspezifische Zellraster, siehe dortiger
    Docstring); ein min_band(p) dort wäre eine Regression."""
    return min(p.W_TOP_FRONT, p.W_TOP_REAR, p.W_TOP_LEFT, p.W_TOP_RIGHT)


def lap_height(p: Params = P) -> float:
    """Höhe der halben Stoß-Überlappung (= halbe Körperhöhe bis zur
    Deckfläche, (H_RAISE-GLUE_GAP)/2 bzw. äquivalent model.frame.top_z(p)/2
    -- M1/Ledger 23/30/33: konsolidiert die früher an mehreren Stellen
    wiederholte Formel in fem/analytic.py und fem/joint_check.py)."""
    return (p.H_RAISE - p.GLUE_GAP) / 2


def groove_centerline_len(p: Params = P) -> float:
    """Umfangslänge der unteren Kleberille (4 Seiten, konservativ mit der
    AUSSENkante der Rille statt der echten Mittellinie gerechnet -- M1/
    Ledger 23/30/33: konsolidiert die früher doppelt kopierte Formel in
    fem/analytic.py::glue_load_shear und export/export.py::_montagenotiz)."""
    return 4 * (p.CUTOUT_W + 2 * p.GROOVE_OFF + p.GROOVE_W)


def wind_force(p: Params = P) -> float:
    """Horizontale Auslegungswindlast inkl. Sicherheitsfaktor (N)."""
    v = p.V_DESIGN_KMH / 3.6
    q = 0.5 * RHO_AIR * v * v        # Staudruck
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
    w_min = min_band(p)                # M1/Ledger 23/30/33: eigener Helper statt Inline-min()
    plate_clear = (p.CUTOUT_W - p.PLATE_KRAGEN_W) / 2
    if plate_clear < 0.5:
        source = "gemessen" if p.PLATE_KRAGEN_MEASURED else "angenommen"
        fehler.append(f"Belluna-Kragen hat oben nur {plate_clear:.1f} mm Radialluft (< 0.5): "
                      f"PLATE_KRAGEN_W ist {source}; Schnittstelle korrigieren")
    if p.CUTOUT_W >= p.PLATE_OUTER_W:
        fehler.append("Obere Rahmenöffnung erreicht den Belluna-Flansch: keine Auflagefläche")
    if not (45.0 <= p.TOP_DRAIN_DEG <= 70.0):
        fehler.append(f"TOP_DRAIN_DEG={p.TOP_DRAIN_DEG} außerhalb 45..70°: "
                      f"Druck-Selbsttragfähigkeit bzw. Entwässerung nicht gesichert")
    for side_w in side_top_widths(p):
        outer = p.CUTOUT_W / 2 + side_w
        start = drainage_start(p, side_w)
        if start >= outer - 2.0:
            fehler.append(f"Entwässerungsfase nur {outer - start:.1f} mm breit (< 2.0): "
                          f"W_TOP={side_w} oder Keepouts prüfen")
        if top_surface_z(p, outer, side_w) <= p.CHAMFER_OUT + 2.0:
            fehler.append(f"Entwässerungsfase endet bei z={top_surface_z(p, outer, side_w):.1f} mm "
                          f"zu nah an Boden/Außenfase")
    if p.CHAMBERS:
        aussenwand = w_min - (p.INNER_WALL + 2 * p.CHAMBER_W + p.CHAMBER_RIB)
        if aussenwand < 2.4:
            fehler.append(f"Außenwand hinter Kammerring 2 nur {aussenwand:.1f} mm (< 2.4): "
                          f"W_TOP erhöhen oder CHAMBER_W/INNER_WALL senken")
        deck_rest = p.DECK_T - p.REC_GUSSET_D
        if deck_rest < 2.0:
            fehler.append(f"Deckplatten-Rest über Kammern nur {deck_rest:.1f} mm (< 2.0): "
                          f"DECK_T an REC_GUSSET_D anpassen (Messpunkt A4)")
        kammerdecke = (p.H_RAISE - p.GLUE_GAP) - p.DECK_T
        apex = p.BOTTOM_T + math.tan(math.radians(p.CHEVRON_DEG)) * p.CHAMBER_W / 2
        if apex > kammerdecke - 1.0:
            fehler.append(f"Chevron-Apex {apex:.1f} mm erreicht Kammerdecke {kammerdecke:.1f} mm")
        r_out2 = (p.CUTOUT_W / 2 + p.INNER_WALL + 2 * p.CHAMBER_W
                  + p.CHAMBER_RIB)
        for side_w in side_top_widths(p):
            geneigte_decke = top_surface_z(p, r_out2, side_w) - p.DECK_T
            if apex > geneigte_decke - 1.0:
                fehler.append(f"Chevron-Apex {apex:.1f} mm erreicht geneigte Kammerdecke "
                              f"{geneigte_decke:.1f} mm bei W_TOP={side_w}")
        if p.CORNER_CHAMBERS:
            off = p.CUTOUT_W / 2 - p.CUTOUT_R
            corner_axis = off + (r_out2 - off) * math.cos(
                math.radians(p.CORNER_ANGLE_MARGIN))
            corner_drop = max(
                max(0.0, corner_axis - drainage_start(p, side_w))
                * math.tan(math.radians(p.TOP_DRAIN_DEG))
                for side_w in side_top_widths(p))
            corner_ceiling = kammerdecke - corner_drop
            if apex > corner_ceiling - 1.0:
                fehler.append(f"Chevron-Apex {apex:.1f} mm erreicht abgesenkte "
                              f"Eckkammerdecke {corner_ceiling:.1f} mm")
        if not (apex + p.VENT_D / 2 + 0.5 <= p.VENT_Z <= kammerdecke - p.VENT_D / 2 - 0.5):
            fehler.append(f"VENT_Z={p.VENT_Z} außerhalb des Kammer-z-Bands "
                          f"({apex + p.VENT_D/2 + 0.5:.1f}..{kammerdecke - p.VENT_D/2 - 0.5:.1f})")
    if p.JOINT_BOLT_OFF + p.JOINT_CB_D / 2 > w_min - 2.4:
        fehler.append("M5-Kopfsenkung erreicht die Außenwand: JOINT_BOLT_OFF/W_TOP prüfen")
    joint_r = p.CUTOUT_W / 2 + p.JOINT_BOLT_OFF
    groove_outer = p.CUTOUT_W / 2 + p.GROOVE_OFF + p.GROOVE_W
    if joint_r - p.JOINT_CB_D / 2 < groove_outer + 1.0:
        fehler.append("M5-Kopfsenkung erreicht die Kleberille: JOINT_BOLT_OFF erhöhen")
    for side_w in side_top_widths(p):
        if joint_r + p.JOINT_CB_D / 2 > drainage_start(p, side_w):
            fehler.append("M5-Kopfsenkung erreicht die Entwässerungsfase: "
                          "JOINT_BOLT_OFF/Drainage-Keepout prüfen")
    if p.GLUE_GAP < 2.0:
        fehler.append("GLUE_GAP < 2 mm: Thermik-Elastikfuge und Noppen-Fixierflächen brauchen >= 2")
    if p.NOPPLE_FILLET < 0:
        fehler.append("NOPPLE_FILLET < 0: Übergangskegel-Höhe unzulässig negativ")
    if p.NOPPLE_SPACING < 3 * p.NOPPLE_R + 2 * p.NOPPLE_FILLET:
        fehler.append("NOPPLE_SPACING < 3*NOPPLE_R + 2*NOPPLE_FILLET: "
                       "Noppen (inkl. Übergangskegel-Fuß) überlappen")
    if p.CORNER_CHAMBERS:
        if not p.CHAMBERS:
            fehler.append("Eckkammern setzen CHAMBERS voraus (CORNER_CHAMBERS ohne CHAMBERS)")
        elif not (0 < p.CORNER_ANGLE_MARGIN < 45):
            fehler.append(f"CORNER_ANGLE_MARGIN={p.CORNER_ANGLE_MARGIN} außerhalb (0, 45): "
                          f"Sektorwinkel (90 - 2*Margin) muss positiv bleiben")
        elif p.CORNER_GAP < 1.0:
            fehler.append(f"CORNER_GAP={p.CORNER_GAP} < 1.0 mm: zu wenig Luft zwischen "
                          f"Ecksektor-Keepout und Zellraster")
        else:
            # Eckkammern (Task 17, Review-Critical-Fix): Kollisionsfreiheit
            # Ecksektor <-> gerade Zellbänder wird NICHT mehr hier per
            # Ungleichung geprüft, sondern model/frame.py::_chamber_cell_centers
            # klemmt die Bandgrenze selbst gegen die Keepout-Grenze
            # (model/frame.py::_corner_keepout) -- das Zellraster kann sich
            # dadurch physisch gar nicht mehr bis in den Ecksektor hinein
            # erstrecken (auch nicht bei kleinem CELL_L, siehe dortiger
            # Docstring für die vollständige Herleitung). FRÜHERE Fassung hier
            # verglich fälschlich den ÄUSSERSTEN Ring-2-Punkt (r_out2) des
            # Sektors mit der Bandgrenze -- das ist der UNKRITISCHE Punkt:
            # entlang des margin-Strahls y(x) = off + tan(margin)*(x-off)
            # wächst y monoton mit x, der kritischste (kleinste y bei im
            # Zellband liegendem x) Punkt liegt am INNENRADIUS r_in1, nicht
            # bei r_out2. Die alte Ungleichung validierte damit einen zu
            # optimistischen (nicht existierenden) Sicherheitsabstand und ließ
            # reale Kollisionen durch (empirisch belegt: CELL_L=53 überschnitt
            # den Ecksektor um 516.3 mm³, obwohl validate() PASS meldete).
            # Verbleibende Prüfung hier: reine Kohärenz -- die Keepout-Grenze
            # muss überhaupt noch Platz für mindestens eine Zelle lassen
            # (sonst produziert der Klemm-Mechanismus in _chamber_cell_centers
            # stillschweigend 0 Zellen auf der betroffenen Halbseite, was zwar
            # geometrisch sicher, aber vermutlich nicht die Absicht ist).
            off = p.CUTOUT_W / 2 - p.CUTOUT_R
            r_in1 = p.CUTOUT_W / 2 + p.INNER_WALL
            corner_keepout = (off + math.tan(math.radians(p.CORNER_ANGLE_MARGIN)) * (r_in1 - off)
                              - p.CORNER_GAP)
            if corner_keepout <= p.SOLID_JOINT_HALF:
                fehler.append(
                    f"Eckkammer-Keepout {corner_keepout:.2f} mm liegt nicht über "
                    f"SOLID_JOINT_HALF {p.SOLID_JOINT_HALF}: kein Platz für irgendeine Zelle "
                    f"im Band (CORNER_ANGLE_MARGIN erhöhen oder CORNER_GAP senken)")
    # Obere Belluna-Schnittstelle ist geometrisch unabhängig vom optionalen
    # Unterkragen und muss deshalb auch bei BOT_KRAGEN=False validiert werden.
    plate_offsets = p.PLATE_SCREW_OFFS
    if len(plate_offsets) != 4 or len(set(plate_offsets)) != 4:
        fehler.append("PLATE_SCREW_OFFS braucht vier verschiedene universelle Positionen")
    else:
        if any(-offset not in plate_offsets for offset in plate_offsets):
            fehler.append("PLATE_SCREW_OFFS muss vorzeichen-symmetrisch sein")
        if min(abs(o) for o in plate_offsets) < p.SOLID_JOINT_HALF + p.PLATE_SCREW_BOSS_HALF:
            fehler.append("Belluna-Schraubrippe erreicht die massive Segmentstoßzone")
        if (max(abs(o) for o in plate_offsets) + p.PLATE_SCREW_BOSS_HALF
                > p.CUTOUT_W / 2 - p.CUTOUT_R):
            fehler.append("Belluna-Schraubrippe erreicht den Eckradius")
    if p.PLATE_SCREW_BOSS_HALF < p.BOT_KRAGEN_SCREW_D / 2 + 2.0:
        fehler.append("PLATE_SCREW_BOSS_HALF lässt <2 mm Material neben ST4.2")
    boss_min_l = p.INNER_WALL + p.CHAMBER_W
    boss_max_l = boss_min_l + p.CHAMBER_RIB
    if not (boss_min_l <= p.PLATE_SCREW_BOSS_L <= boss_max_l):
        fehler.append(f"PLATE_SCREW_BOSS_L={p.PLATE_SCREW_BOSS_L} muss im "
                      f"Zwischensteg {boss_min_l:.1f}..{boss_max_l:.1f} mm enden")
    screw_z = (p.H_RAISE - p.GLUE_GAP) - p.PLATE_SCREW_Z_FROM_TOP
    if screw_z - p.PLATE_SCREW_BOSS_HALF < p.BOTTOM_T + 1.0:
        fehler.append("Belluna-Schraubrippe reicht zu nah an Kammerboden/Bodenplatte")

    if p.BOT_KRAGEN:
        if p.BOT_KRAGEN_CLEAR < 0.5:
            fehler.append(f"BOT_KRAGEN_CLEAR={p.BOT_KRAGEN_CLEAR} < 0.5 mm Radialluft: "
                          f"Kragen klemmt im Dachausschnitt (Druck-/Ausschnitt-Toleranzen)")
        if p.ROOF_WOOD_FRAME_W < 30.0:
            fehler.append(f"ROOF_WOOD_FRAME_W={p.ROOF_WOOD_FRAME_W} < 30 mm: "
                          f"Schraubgrund/Kompressionsrahmen zu schmal")
        if p.BOT_KRAGEN_DEPTH > p.ROOF_T - 2.0:
            fehler.append(f"BOT_KRAGEN_DEPTH={p.BOT_KRAGEN_DEPTH} taucht tiefer als "
                          f"Dachstärke-2 ({p.ROOF_T - 2.0:.1f}): Kragen stößt innen durch")
        if p.BOT_KRAGEN_HOLE_Z + p.BOT_KRAGEN_HOLE_D / 2 + 1.0 > p.BOT_KRAGEN_DEPTH:
            fehler.append(f"Kragenloch (z={p.BOT_KRAGEN_HOLE_Z}, Ø{p.BOT_KRAGEN_HOLE_D}) "
                          f"unterschreitet den Kragenrand (Tiefe {p.BOT_KRAGEN_DEPTH})")
        offsets = p.BOT_KRAGEN_HOLE_OFFS
        if len(offsets) != 2 or len(set(offsets)) != 2:
            fehler.append("BOT_KRAGEN_HOLE_OFFS braucht genau zwei verschiedene Offsets")
        else:
            if abs(sum(offsets)) > 1e-6:
                fehler.append("BOT_KRAGEN_HOLE_OFFS muss als symmetrisches ±Paar "
                              "rotationsidentische Segmente ergeben")
            if bot_kragen_hole_count(p) != 8:
                fehler.append("Unterkragen braucht genau 8 Löcher: zweite Hälfte der 16 "
                              "beiliegenden Belluna-ST4.2x25")
            if min(abs(o) for o in offsets) < p.LAP_L + 10.0:
                fehler.append(f"Kragenloch zu nah an der Seitenmitte "
                              f"(min |Offset| < LAP_L+10 = {p.LAP_L + 10.0:.0f})")
            if (max(abs(o) for o in offsets) + p.BOT_KRAGEN_HOLE_D / 2 + 2.0
                    > p.CUTOUT_W / 2 - p.CUTOUT_R - p.BOT_KRAGEN_T):
                fehler.append("Kragenloch läuft in den Eckradius")
        if p.BOT_KRAGEN_SCREW_L > p.ROOF_WOOD_FRAME_W:
            fehler.append(f"ST4.2x{p.BOT_KRAGEN_SCREW_L:.0f} länger als Holzrahmenbreite "
                          f"{p.ROOF_WOOD_FRAME_W:.0f} mm")
        # Schnittstelle Belluna-Kragen: dessen Spitze (top_z - PLATE_KRAGEN_D)
        # muss OBERHALB der Übergangsfase bleiben (Fasenoberkante = TRANS+0.5,
        # siehe frame._bot_kragen_tools), sonst setzt die Platte auf der
        # Fase auf statt auf der Deckfläche (seit GEOM_REV 4; Mindestluft in 5)
        frei = (p.H_RAISE - p.GLUE_GAP) - p.PLATE_KRAGEN_D
        z_clear = frei - (p.BOT_KRAGEN_TRANS + 0.5)
        if z_clear < p.PLATE_KRAGEN_Z_CLEAR_MIN:
            fehler.append(f"Axialluft Belluna-Kragenspitze↔Übergangsfase nur "
                          f"{z_clear:.1f} mm (< {p.PLATE_KRAGEN_Z_CLEAR_MIN:.1f}): "
                          f"BOT_KRAGEN_TRANS senken oder H_RAISE erhöhen")
    if fehler:
        raise ValueError("Parameter-Validierung fehlgeschlagen:\n- " + "\n- ".join(fehler))
