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
    # --- Meta: Geometrie-Revision. Erhöhen bei geometrie-wirksamen CODE-
    # Änderungen (z. B. neue Fillets/Radien), auch wenn kein Messwert
    # wechselt -- ändert params_hash, damit Druckfiles/Report eindeutig
    # bleiben (Task 15, Heatmap-Fix Noppenfuß-Radius) ---
    GEOM_REV: int = 2
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
    NOPPLE_FILLET: float = 1.5   # Kerbentschärfung am Zylinderansatz (Übergangskegel,
                                  # Heatmap 2026-07-12: alle LF-Hotspots am Noppenfuß)
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
    CLAMP_FORCE: float = 2400.0  # KONSERVATIVE HÜLLKURVE: real keine harte Klemmung
                                 # (nur Zierblende von unten, User 2026-07-12); deckt Montagefälle
    SNOW_LOAD: float = 200.0     # N auf Grundfläche
    T_MIN: float = -20.0
    T_MAX: float = 85.0
    # --- Material Bambu ASA-CF (TDS V1.0, GEDRUCKTE Probekörper XY+Z; Task 19,
    # Spec §3.5) + Abminderung (Spec §6) ---
    E_BASE: float = 4200.0       # Zug-E XY; Z: 2290 (FEM isotrop-homogen, Verformungen unkritisch)
    SIGMA_BASE: float = 34.0     # Zugfestigkeit XY (Z: 30 -> Z/XY=0.88 gemessen)
    NU: float = 0.35             # unverändert (keine Herstellerangabe)
    RHO: float = 1020.0          # kg/m^3
    CTE_ASA: float = 60e-6       # 1/K; DATENBLATT-LÜCKE: konservative OBERGRENZE für
                                  # CF-ASA (in-flow typ. 30-45e-6, quer höher). BEWUSST
                                  # nicht die optimistischeren ~40e-6 (Gate-Muting-Lehre!);
                                  # Herstellerwert anfragen -> senkt Fugenauslastung
                                  # weiter (todo.md).
    CTE_ROOF: float = 25e-6      # 1/K (GFK)
    DERATE_TEMP: float = 0.5     # 85 °C Bauteil vs. HDT 102/Vicat 108 (TDS)
    DERATE_Z: float = 0.8        # GEMESSEN Z/XY=0.88 (30/34 MPa), konservativ gerundet
    DERATE_CREEP: float = 0.4    # keine CF-Kriechdaten -> unverändert konservativ
    INFILL_FACTOR: float = 1.0   # 100 % Infill (Kammern übernehmen die Gewichtsreduktion,
                                  # kein Slicer-Infill mehr nötig)

    # Preset-Vergleich (NUR Kommentar, kein totes Dict -- Spec §3.5). Aktueller
    # Default ist Bambu ASA-CF (TDS V1.0, gedruckte XY+Z-Probekörper -- einzige
    # der drei Spalten mit echtem Datenblatt für DIESES Bauteil, Task 19).
    # Standard-ASA = vorheriger Projekt-Default (Task 1-18, ebenfalls belegt).
    # CR3D FibCR20 = grobe Marktklassen-Richtwerte für 20%-CF-verstärktes FDM-
    # Filament OHNE eigenes TDS im Haus -- vor einem Umstieg erst Datenblatt
    # beschaffen (sonst DA-3-Bruch/Gate-Muting-Gefahr, siehe CTE_ASA oben):
    #
    #   Feld              Bambu ASA-CF*  Standard-ASA   CR3D FibCR20 (unbelegt)
    #   E_BASE     [MPa]    4200           2000           ~3500-4000
    #   SIGMA_BASE [MPa]      34             40             ~30-35
    #   RHO      [kg/m^3]   1020           1070           ~1150-1200
    #   CTE_ASA    [1/K]   60e-6          90e-6          ~30-40e-6 (offen)
    #   DERATE_TEMP           0.5            0.35           n/a (HDT unbekannt)
    #   DERATE_Z              0.8            0.6            n/a (keine Z-Probekörper)
    #   * aktueller Default (Task 19)
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
    if fehler:
        raise ValueError("Parameter-Validierung fehlgeschlagen:\n- " + "\n- ".join(fehler))
