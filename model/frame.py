"""Adapterrahmen (vor Segmentierung) mit Rippenkammern statt Slicer-Infill."""
import math

import Part
from FreeCAD import Vector

import params as PRM
from model import features as F


def top_z(p: PRM.Params = PRM.P) -> float:
    """Oberkante der Deckfläche (mm) über der Dachebene z=0: Zielerhöhung
    H_RAISE minus dem freien Klebespalt GLUE_GAP (der als Pads/Kleberaupe
    ausgeführte Spalt zählt nicht zur festen Adapterhöhe). Bezugsgröße für
    fast alle z-Koordinaten des Modells (Deckfläche, Kammerdecke, Stoßhöhe)."""
    return p.H_RAISE - p.GLUE_GAP


def _corner_keepout(p: PRM.Params) -> float:
    """Bandkoordinate (u, gemessen wie in _chamber_cell_centers), ab der das
    Zellraster wegen des Eck-Sektors (Task 17, CORNER_CHAMBERS) keinen Platz
    mehr hat -- Review-Critical-Fix: der frühere validate()-Check verglich
    fälschlich den ÄUSSERSTEN Sektorpunkt (r_out2) mit der Bandgrenze. Das
    ist der UNKRITISCHE Punkt.

    Herleitung: der Ecksektor ist ein echter Kreissektor um das Eckzentrum
    (off, off) mit off = CUTOUT_W/2 - CUTOUT_R (siehe _corner_chamber_cuts).
    Für Punkte auf seinem margin-Rand (Polarwinkel = CORNER_ANGLE_MARGIN
    relativ zum Eckzentrum, der dem geraden Zellband am nächsten liegende
    Sektorrand) gilt in globalen (X,Y)-Koordinaten -- die für die kanonische
    REAR-Seite (k=0) IDENTISCH mit den Kammer-Koordinaten (r, u) sind --:
        X = off + r'*cos(margin),  Y = off + r'*sin(margin)
    mit r' = radialer Abstand vom Eckzentrum. Eliminiert man r', folgt
        Y(X) = off + tan(margin) * (X - off)
    d. h. Y WÄCHST MONOTON MIT X. Der kritische (kleinste Y bei einem X im
    Zellband liegenden) Punkt liegt deshalb am kleinsten relevanten X, das
    ist der INNENRADIUS von Ring 1 (r_in1 = CUTOUT_W/2 + INNER_WALL) -- NICHT
    am Außenradius r_out2 (die alte, widerlegte Annahme). Ring 2 liegt bei
    noch größerem X (r_in2 > r_in1) und damit noch größerem Y -- eine
    einzige Klemme auf Basis von r_in1 deckt also BEIDE Ringe ab.

    corner_keepout = off + tan(margin)*(r_in1 - off) - CORNER_GAP
    (Defaults: 195 + 13*tan(18°) - 3 = 196.22 mm) ist die größte Bandkoor-
    dinate (Zellreichweite = Zentrum + CELL_L/2), bis zu der das gerade
    Zellraster überhaupt reichen darf.

    WICHTIG (empirisch verifiziert, siehe _chamber_cell_centers): dieser Wert
    wird als POST-HOC-FILTER auf die bereits fertig zentrierten Zellen
    angewendet, NICHT als Ersatz für band_end in der Zentrierungsformel --
    ein direktes band_end = min(band_end, corner_keepout) VOR der
    Margin-Berechnung würde bei Defaults die Zentrierung neu verteilen und
    ALLE Zellzentren verschieben (getestet: letzte Zelle wandert von
    Reichweite 193 auf 188.6, siehe Diff-Skript im Fix-Report) -- das würde
    den unveränderlichen Default-Volumen-Anker brechen, obwohl das
    natürliche (unveränderte) Default-Raster den Keepout ohnehin schon
    einhält (193 < 196.22). Ein Filter NACH der Zentrierung dagegen lässt
    Defaults exakt unverändert (kein Zentrum verletzt den Keepout, nichts
    wird gefiltert) und entfernt bei kleinerem CELL_L (Regressionsfund:
    CELL_L=53 überschnitt den Sektor vorher um 516.3 mm³, siehe Fix-Report)
    gezielt nur die tatsächlich kollidierenden äußersten Zellen.

    Nur relevant, wenn p.CORNER_CHAMBERS -- sonst existiert kein Sektor und
    der Aufrufer wendet den Filter gar nicht erst an."""
    off = p.CUTOUT_W / 2 - p.CUTOUT_R
    r_in1 = p.CUTOUT_W / 2 + p.INNER_WALL
    return off + math.tan(math.radians(p.CORNER_ANGLE_MARGIN)) * (r_in1 - off) - p.CORNER_GAP


def _chamber_cell_centers(p: PRM.Params, limit_w: float):
    """u-Positionen (entlang einer Seite, Ursprung = Seitenmitte/Stoß) der
    Kammerzellen EINER Seiten-HALBSEITE (u > 0, also nur +u ODER nur -u,
    je nachdem welche Nachbargrenze der Aufrufer übergibt -- siehe
    _side_neighbor_bounds). Zellenraster CELL_L/CELL_RIB, zentriert im Band
    zwischen SOLID_JOINT_HALF und SOLID_CORNER (bzw. der Eck-Keepout-Grenze,
    siehe unten).

    limit_w ist NICHT die W_TOP-Breite dieser Seite selbst, sondern die
    W_TOP-Breite der SENKRECHTEN Nachbarseite, die an diesem Ende physisch
    die Bandlänge begrenzt (side_half = CUTOUT_W/2 + limit_w): eine Seite
    läuft entlang ihrer eigenen W_TOP-Richtung nicht weiter, als der Nachbar
    an der Ecke reicht -- die eigene W_TOP-Breite bestimmt nur die radiale
    Kammertiefe (r_in..r_out, fest, siehe _chamber_cuts), nicht die
    Bandlänge (Review-Fund nach Ledger 21/22: die vorige 'seitenspezifische'
    Fassung nahm faelschlich die EIGENE W_TOP als Bandgrenze -- bei
    asymmetrischen Messwerten erodierte das SOLID_CORNER bzw. erzeugte
    Phantom-Slots jenseits des tatsaechlichen Rahmenrandes, siehe
    tests/test_asymmetrie.py). Bei symmetrischen Defaults (alle W_TOP=50)
    ist limit_w für jede Halbseite ohnehin 50 -> identisches Raster,
    identischer chamber_slot_count (Regressionsanker).

    Eck-Keepout-Filter (Task 17, Review-Critical-Fix): wenn CORNER_CHAMBERS
    aktiv ist, wird NACH der (unveränderten) Zentrierung jede Zelle verworfen,
    deren Reichweite (Zentrum + CELL_L/2) über _corner_keepout(p) hinausreicht
    -- der Ecksektor reicht sonst (insbesondere bei kleinem CELL_L, das den
    Zellraster-Rand näher an die physische Bandgrenze band_end schiebt) in
    den Sektor hinein, siehe _corner_keepout-Docstring für die vollständige
    Herleitung samt Regressionsbeleg UND die Begründung, warum ein Filter
    NACH statt eine Ersetzung VOR der Zentrierung nötig ist (Erhalt des
    Default-Rasters). Bei Defaults bleibt der Filter wirkungslos:
    corner_keepout=196.22 > tatsächliche Reichweite der letzten Zelle = 193
    (siehe test_eckkammern_delta_und_keepout_exakt) -- deshalb identisches
    Raster, identisches Default-Volumen."""
    side_half = p.CUTOUT_W / 2 + limit_w
    band_start = p.SOLID_JOINT_HALF
    band_end = side_half - p.SOLID_CORNER
    band_len = band_end - band_start
    step = p.CELL_L + p.CELL_RIB
    n = max(0, int((band_len + p.CELL_RIB) // step))
    used = n * p.CELL_L + max(0, n - 1) * p.CELL_RIB
    margin = (band_len - used) / 2
    centers = []
    for i in range(n):
        u0 = band_start + margin + i * step
        centers.append(u0 + p.CELL_L / 2)
    if p.CORNER_CHAMBERS:
        keepout = _corner_keepout(p)
        centers = [c for c in centers if c + p.CELL_L / 2 <= keepout]
    return centers


def _side_neighbor_bounds(p: PRM.Params):
    """Für jede Seite k (Kanonik k=0 REAR, k=1 RIGHT, k=2 FRONT, k=3 LEFT --
    siehe _chamber_cuts-Docstring) die (Nachbar-Grenze für +u, Nachbar-
    Grenze für -u), d. h. die W_TOP-Breiten der BEIDEN SENKRECHTEN
    Nachbarseiten, die die Bandlänge dieser Seite an ihren beiden Enden
    begrenzen (siehe _chamber_cell_centers).

    Herleitung aus dem Rotations-Mapping (Part.Shape.rotate um +z,
    Rechte-Hand-Regel: (x,y) -> (-y,x) je 90°-Schritt, also nach k
    Anwendungen (x,y) -> [(x,y), (-y,x), (-x,-y), (y,-x)][k]):

    Die kanonische (k=0, unrotierte) Kammerzelle liegt bei radialem r>0
    (feste Kammertiefe, X-Achse) und Bandkoordinate u (Y-Achse, das ist die
    Variable, deren Vorzeichen +u/-u hier bestimmt wird; siehe
    _chamber_profile_face/_chamber_cavity: Profil in x=r, Extrusion entlang
    +y ab y0=u-CELL_L/2). Ein Punkt (r,u) der kanonischen Zelle liegt nach
    k Rotationsschritten bei globalem (X,Y):
      k=0: (X,Y) = ( r,  u)   ->  u wächst  => +Y global
      k=1: (X,Y) = (-u,  r)   ->  u wächst  => -X global
      k=2: (X,Y) = (-r, -u)   ->  u wächst  => -Y global
      k=3: (X,Y) = ( u, -r)   ->  u wächst  => +X global

    Aus build_frame (siehe _chamber_cuts-Docstring) ist bekannt:
      +X-Rand = CUTOUT_W/2 + W_TOP_REAR    (REAR-Außenkante)
      -X-Rand = -(CUTOUT_W/2 + W_TOP_FRONT) (FRONT-Außenkante)
      +Y-Rand = CUTOUT_W/2 + W_TOP_RIGHT   (RIGHT-Außenkante)
      -Y-Rand = -(CUTOUT_W/2 + W_TOP_LEFT)  (LEFT-Außenkante)

    +u (u>0, die von _chamber_cell_centers direkt gelieferte Halbseite) und
    -u (gespiegelt, u<0) je k zeigen also auf folgende Außenkanten und damit
    folgende Nachbar-W_TOP-Breiten:
      k=0 REAR:  +u -> +Y-Rand -> W_TOP_RIGHT | -u -> -Y-Rand -> W_TOP_LEFT
      k=1 RIGHT: +u -> -X-Rand -> W_TOP_FRONT | -u -> +X-Rand -> W_TOP_REAR
      k=2 FRONT: +u -> -Y-Rand -> W_TOP_LEFT  | -u -> +Y-Rand -> W_TOP_RIGHT
      k=3 LEFT:  +u -> +X-Rand -> W_TOP_REAR  | -u -> -X-Rand -> W_TOP_FRONT

    Deckt sich exakt mit der Review-Vorgabe (Task-15-Nachbesserung,
    Achsen-Fehlbezug). Rückgabe: Tuple aus 4 (plus_w, minus_w)-Paaren,
    Index = k."""
    return (
        (p.W_TOP_RIGHT, p.W_TOP_LEFT),   # k=0 REAR
        (p.W_TOP_FRONT, p.W_TOP_REAR),   # k=1 RIGHT
        (p.W_TOP_LEFT, p.W_TOP_RIGHT),   # k=2 FRONT
        (p.W_TOP_REAR, p.W_TOP_FRONT),   # k=3 LEFT
    )


def _plate_screw_offsets_by_chamber_side(p: PRM.Params):
    """Universelle Belluna-Vollzonen je Seite, Reihenfolge REAR/RIGHT/FRONT/LEFT.

    Jede Seite unterstützt beide am Original vorkommenden Außenlochpaare
    ±140/±165. Die Platte nutzt davon nur ihr reales Paar. Weil die vier
    Tupel absichtlich gleich sind, bleibt der Rahmen 90°-rotationssymmetrisch.
    """
    return (p.PLATE_SCREW_OFFS,) * 4


def _vent_u_clear_of_plate_boss(uc, p: PRM.Params):
    """Verschiebt einen Vent-Kanal innerhalb seiner Zelle aus Schraubrippen.

    Die regulären ±168,5-mm-Zellzentren liegen nahe den universellen
    ±165-mm-Rippen. Der Vent-Kanal wandert dort nur so weit zur Ecke, dass
    zwischen Ø4-Vent und Rippe 1 mm Luft bleibt. Die Kavität selbst bleibt
    unverändert; damit entstehen weder eine grobe 43-mm-Vollzone noch ein
    geschlossener Hohlraum durch ein nachträglich versiegeltes Vent.
    """
    clearance = p.PLATE_SCREW_BOSS_HALF + p.VENT_D / 2 + 1.0
    nearest = min(p.PLATE_SCREW_OFFS, key=lambda offset: abs(uc - offset))
    distance = abs(uc - nearest)
    if distance >= clearance:
        return uc
    direction = 1.0 if uc >= 0 else -1.0
    shift = clearance - distance
    shifted = uc + direction * shift
    max_shift = p.CELL_L / 2 - p.VENT_D / 2 - 1.0
    if abs(shifted - uc) > max_shift:
        raise ValueError("Vent kann innerhalb der Kammerzelle nicht aus der "
                         "Belluna-Schraubrippe verschoben werden")
    return shifted


def chamber_slot_count(p: PRM.Params = PRM.P) -> int:
    """Anzahl der Kammer-SLOTS (u-Positionen) über ALLE 4 Seiten, SUMME je
    Seite (Ledger 21/22: nicht mehr 4x2xn, weil jede Seite jetzt ihr eigenes
    Zellenraster hat -- eine schmale Seite kann weniger Slots liefern als
    eine breite). +u- und -u-Halbseite werden UNABHÄNGIG mit ihrer jeweils
    eigenen Nachbargrenze gezählt (Review-Fix: keine pauschale Verdopplung
    mehr, da beide Hälften bei Asymmetrie unterschiedlich groß sein können).
    Ein Slot enthält ZWEI Einzelkammern (Ring 1 + Ring 2) und 2 Vent-Kanäle
    -- Einzelkammern gesamt = 2 x Slots. Für die DFM-Vent-Allowance."""
    if not p.CHAMBERS:
        return 0
    total = 0
    for k, (plus_w, minus_w) in enumerate(_side_neighbor_bounds(p)):
        centers = (_chamber_cell_centers(p, plus_w)
                   + [-c for c in _chamber_cell_centers(p, minus_w)])
        total += len(centers)
    return total


def _chamber_profile_face(r_in, r_out, apex_z, y0, p, side_width=None,
                          z_top_override=None):
    """Kammerquerschnitt als (r,z)-Polygon in der Ebene y=y0.

    Gerade Außenkammern folgen mit ihrer Decke der Entwässerungsfase, damit
    darüber überall ``DECK_T`` Material stehen bleibt. Eckkammern können eine
    konservativ abgesenkte, ebene Decke über ``z_top_override`` erhalten.
    """
    if z_top_override is not None:
        z_top_in = z_top_out = z_top_override
    elif side_width is not None:
        z_top_in = PRM.top_surface_z(p, r_in, side_width) - p.DECK_T
        z_top_out = PRM.top_surface_z(p, r_out, side_width) - p.DECK_T
    else:
        z_top_in = z_top_out = top_z(p) - p.DECK_T
    z_bot = p.BOTTOM_T
    r_mid = (r_in + r_out) / 2
    pts = [Vector(r_in, y0, z_bot), Vector(r_in, y0, z_top_in),
           Vector(r_out, y0, z_top_out), Vector(r_out, y0, z_bot),
           Vector(r_mid, y0, apex_z)]
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire)


def _chamber_cavity(r_in, r_out, apex_z, y0, length, p, side_width=None):
    face = _chamber_profile_face(r_in, r_out, apex_z, y0, p, side_width)
    return face.extrude(Vector(0, length, 0))


def _ring_radii(p: PRM.Params):
    """Kompatibilitäts-Helper für die Grenzen der ersten beiden Ringe."""
    bands = _ring_bands(p)
    return (*bands[0], *bands[1])


def _ring_bands(p: PRM.Params):
    """Radiale (innen, außen)-Grenzen aller konzentrischen Kammerringe.

    Die Anzahl ist parametrisch: GEOM_REV 9 nutzt im kompakten 50-mm-Band
    wieder zwei Ringe. So bleibt der Querschnitt leicht und verzugsarm, ohne
    die massive Segmentstoßzone mit dem einzelnen M5 anzutasten.
    """
    start = p.CUTOUT_W / 2 + p.INNER_WALL
    bands = []
    for _ in range(p.CHAMBER_RING_COUNT):
        end = start + p.CHAMBER_W
        bands.append((start, end))
        start = end + p.CHAMBER_RIB
    return tuple(bands)


def _corner_chamber_cuts(p: PRM.Params):
    """Eckkammern (Task 17, optional CORNER_CHAMBERS): 90°-Rotationsfort-
    setzung der Seiten-Kammerringe um die vier massiven Eckblöcke.

    Eckzentrum (kanonisch die (+,+)-Ecke, x>0/y>0): (off, off) mit
    off = CUTOUT_W/2 - CUTOUT_R -- Mittelpunkt des R{CUTOUT_R}-Eckradius der
    Öffnung. Herleitung der Ring-Radien relativ zu diesem Zentrum: die
    radial versetzte Kontur eines gerundeten Rechtecks (Eckradius R, Zentrum
    C) ist bei Offset d WIEDER ein gerundetes Rechteck mit Eckradius R+d und
    UNVERÄNDERTEM Zentrum C (Standardeigenschaft von Parallelkurven an
    Kreisbögen -- der Bogenmittelpunkt bleibt beim Offsetten fix). Die
    Kammerring-Innen-/Außenradien der geraden Seiten (_ring_radii, gemessen
    von der globalen Mittelachse) sind exakt Offsets der Öffnungskante
    (r=CUTOUT_W/2, Eckradius CUTOUT_R) -- am Eck liegen sie deshalb bei
    (r_in1..r_out2) - off vom Eckzentrum entfernt.

    Profil: IDENTISCHES (r,z)-Pentagon wie _chamber_profile_face (gleiche
    Decke/Boden/Chevron-Apex), gebaut in der lokalen Ebene y=0 (enthält die
    z-Achse durch den Ursprung, Winkel 0). Vor dem Revolve um
    CORNER_ANGLE_MARGIN Grad um (0,0,1) vorrotiert, dann um
    (90 - 2*CORNER_ANGLE_MARGIN) Grad weiter um dieselbe Achse (0,0,1) DURCH
    DEN URSPRUNG revolvt (Part.Face.revolve) -- der kanonische Sektor deckt
    damit die Winkel [margin, 90-margin] ab, symmetrisch zur 45°-Diagonale.
    Erst NACH dem Revolve auf das Eckzentrum (off, off) verschieben: ein
    Revolve um eine Achse durch den Ursprung hängt nur von (r, Winkel, z) ab,
    nicht von der absoluten Lage -- Verschieben nach dem Revolve ist
    äquivalent zu (und einfacher als) das Profil vorher zu verschieben und
    um eine Achse durch das Eckzentrum zu revolven.

    Die 4 Ecken entstehen NICHT durch vier separate Konstruktionen, sondern
    durch F.rotz(shape, k) (Rotation um den GLOBALEN URSPRUNG, Rechte-Hand-
    Regel (x,y) -> (-y,x) je 90°-Schritt, exakt wie in _chamber_cuts): das
    bildet den bei (off, off) liegenden, zur Diagonale symmetrischen Sektor
    SAMT Orientierung korrekt auf die anderen 3 Ecken ab
    ((off,off) -> (-off,off) -> (-off,-off) -> (off,-off)) -- KEINE
    Spiegelung nötig, weil der kanonische Sektor bereits symmetrisch zur
    Diagonale liegt (Winkelbereich [margin, 90-margin] ist spiegelsymmetrisch
    um 45°) und eine reine Rotation um den Ursprung Position UND Orientierung
    gemeinsam korrekt mitdreht.

    Kollisionsfreiheit Ecke <-> gerade Zellen (Review-Critical-Fix, Task 17):
    FRÜHERE (WIDERLEGTE) Fassung dieses Docstrings behauptete, der
    kritischste (der geraden Bandgrenze am nächsten liegende) Kavitätspunkt
    des Ecksektors sei der ÄUSSERSTE Ringpunkt r=r_out2_rel=47 beim
    Randwinkel margin -- das ist FALSCH: entlang des margin-Strahls
    y(x) = off + tan(margin)*(x-off) (x, y global, siehe _corner_keepout)
    WÄCHST y monoton mit x, der kritische (kleinste y bei im Zellband
    liegendem x) Punkt liegt deshalb am INNENRADIUS r_in1 (Ring 1), nicht am
    Außenradius. Die alte Ungleichung (sektor_extreme=209.5 >= band_end+3=208)
    verglich damit den UNKRITISCHEN Punkt und validierte einen nicht
    existierenden Sicherheitsabstand -- empirisch widerlegt: bei CELL_L=53
    (Defaults sonst unverändert) überschnitt die reale, per _chamber_cell_
    centers platzierte letzte Ring-1-Zelle den Ecksektor um 516.3 mm³,
    obwohl PRM.validate() PASS meldete (isValid() blieb sogar True, siehe
    Fix-Report -- ein Boolean-Cut mit überlappenden Werkzeugen bleibt
    topologisch gültig, entfernt aber zu viel Material).

    Fix: _chamber_cell_centers filtert das Zellraster selbst gegen
    _corner_keepout(p) (siehe dortiger Docstring für die vollständige
    Herleitung des korrekten, r_in1-basierten kritischen Punkts) -- das
    Raster kann sich damit unabhängig von CELL_L nicht mehr in den
    Ecksektor hinein erstrecken. PRM.validate() prüft nur noch eine
    Kohärenzbedingung (corner_keepout > SOLID_JOINT_HALF, d. h. überhaupt
    Platz für mindestens eine Zelle) statt der widerlegten geometrischen
    Ungleichung. Restwand zur Außenkontur an der 45°-Diagonale bleibt bei
    Defaults massiv genug (siehe Report, Skript-Probe: ~26 mm).

    Vents je Ecke (2 Stück, entlang derselben 45°-Diagonale wie oben, damit
    z=VENT_Z-Bohrungen exakt durch die dünnste Wandrichtung laufen):
    (a) vom Öffnungs-Eckradius (r=CUTOUT_R-1, 1 mm im Material der
        Öffnungsrundung) durch INNER_WALL in Ring 1 (Länge INNER_WALL+2,
        analog Vent 1 der geraden Zellen);
    (b) vom Ring-1-Außenrand (r=r_out1_rel-1) durch den Steg CHAMBER_RIB in
        Ring 2 (Länge CHAMBER_RIB+2, analog Vent 2 der geraden Zellen).
    Damit hängen auch die Eckkammern an der Außenluft -- der bestehende
    "genau 1 geschlossene Shell"-Test erzwingt die Anbindung automatisch
    mit."""
    if not p.CORNER_CHAMBERS:
        return []
    off = p.CUTOUT_W / 2 - p.CUTOUT_R
    bands = _ring_bands(p)
    r_in1, r_out1 = bands[0]
    r_out_last = bands[-1][1]
    apex_z = p.BOTTOM_T + math.tan(math.radians(p.CHEVRON_DEG)) * (p.CHAMBER_W / 2)
    margin = p.CORNER_ANGLE_MARGIN
    sweep = 90 - 2 * margin
    if sweep <= 0:
        raise RuntimeError("frame: CORNER_ANGLE_MARGIN >= 45 lässt keinen Eck-Sektor übrig "
                           "(PRM.validate sollte das vorher abfangen)")

    # Die Entwässerungsfasen schneiden an den Ecksektor-Rändern tiefer als
    # auf den geraden Ringprofilen. Eine einheitlich abgesenkte Eckkammerdecke
    # hält dort konservativ mindestens DECK_T Material geschlossen.
    corner_axis_max = off + (r_out_last - off) * math.cos(math.radians(margin))
    corner_drop = max(
        max(0.0, corner_axis_max - PRM.drainage_start(p, side_w))
        * math.tan(math.radians(p.TOP_DRAIN_DEG))
        for side_w in PRM.side_top_widths(p)
    )
    corner_z_top = top_z(p) - p.DECK_T - corner_drop

    tools = []
    for r_in_abs, r_out_abs in bands:
        r_in, r_out = r_in_abs - off, r_out_abs - off
        face = _chamber_profile_face(r_in, r_out, apex_z, 0.0, p,
                                     z_top_override=corner_z_top)
        face.rotate(Vector(0, 0, 0), Vector(0, 0, 1), margin)
        solid = face.revolve(Vector(0, 0, 0), Vector(0, 0, 1), sweep)
        solid.translate(Vector(off, off, 0))
        for k in range(4):
            tools.append(F.rotz(solid, k))

    # Vents entlang der 45°-Diagonale (kanonische (+,+)-Ecke, dann F.rotz):
    diag = Vector(math.cos(math.radians(45)), math.sin(math.radians(45)), 0)
    vent_starts = [(p.CUTOUT_R - 1, p.INNER_WALL + 2)]
    vent_starts += [
        (r_out - off - 1, p.CHAMBER_RIB + 2)
        for _, r_out in bands[:-1]
    ]
    for r0, length in vent_starts:
        base = Vector(off + r0 * diag.x, off + r0 * diag.y, p.VENT_Z)
        vent = Part.makeCylinder(p.VENT_D / 2, length, base, diag)
        for k in range(4):
            tools.append(F.rotz(vent, k))
    return tools


def _chamber_cuts(p: PRM.Params):
    """Alle Kammer-Hohlräume + Vent-Bohrungen (kanonische +x-Seite, dann je
    90 Grad rotiert für die 3 übrigen Seiten). Cut-Werkzeuge, kein Fuse.

    Kanonik k<->Seite (hergeleitet aus build_frame, NICHT angenommen):
    x0 = -(CUTOUT_W/2 + W_TOP_FRONT), x0+L = CUTOUT_W/2 + W_TOP_REAR ->
    die -x-Bandbreite ist W_TOP_FRONT, die +x-Bandbreite ist W_TOP_REAR:
    +x-Seite = REAR. F.rotz() dreht um +90*k Grad um +z (Part.Shape.rotate,
    Rechte-Hand-Regel): +x -> +y bei k=1. y0 = -(CUTOUT_W/2 + W_TOP_LEFT),
    y0+W = CUTOUT_W/2 + W_TOP_RIGHT -> die +y-Bandbreite ist W_TOP_RIGHT:
    +y-Seite = RIGHT. Also:
      k=0 (0°):   +x  = REAR   (W_TOP_REAR)
      k=1 (90°):  +y  = RIGHT  (W_TOP_RIGHT)
      k=2 (180°): -x  = FRONT  (W_TOP_FRONT)
      k=3 (270°): -y  = LEFT   (W_TOP_LEFT)
    Die radiale Kammertiefe (r_in1..r_out2) ist bewusst NICHT seitenspezifisch
    (feste Größen aus INNER_WALL/CHAMBER_W/CHAMBER_RIB) und hängt NICHT von
    W_TOP ab. Die Zellenzahl/-länge ENTLANG einer Seite (u-Richtung) wird
    dagegen physisch von den beiden SENKRECHTEN NACHBARSEITEN begrenzt, nicht
    von der eigenen W_TOP-Breite (Review-Fund nach Ledger 21/22, siehe
    _chamber_cell_centers/_side_neighbor_bounds für die vollständige
    Herleitung samt Rotations-Nachweis). +u-Hälfte und -u-Hälfte werden daher
    UNABHÄNGIG mit ihrer jeweiligen Nachbargrenze berechnet -- KEINE
    pauschale Spiegelung derselben Liste mehr, da beide Hälften bei
    asymmetrischen W_TOP unterschiedlich groß sein können.

    Hängt zusätzlich (nur wenn p.CORNER_CHAMBERS) die Eckkammer-Werkzeuge
    aus _corner_chamber_cuts an dieselbe Liste an (Task 17) -- build_frame
    cuttet damit Seiten- UND Eckkammern in EINEM Boolean-Aufruf, VOR dem
    gemeinsamen removeSplitter()."""
    if not p.CHAMBERS:
        return []
    bands = _ring_bands(p)
    apex_z = p.BOTTOM_T + math.tan(math.radians(p.CHEVRON_DEG)) * (p.CHAMBER_W / 2)
    neighbor_bounds = _side_neighbor_bounds(p)
    side_widths = PRM.side_top_widths(p)
    tools = []
    for k in range(4):
        plus_w, minus_w = neighbor_bounds[k]
        plus_half = _chamber_cell_centers(p, plus_w)
        minus_half = _chamber_cell_centers(p, minus_w)
        centers = plus_half + [-c for c in minus_half]
        for uc in centers:
            y0 = uc - p.CELL_L / 2
            for r_in, r_out in bands:
                cav = _chamber_cavity(r_in, r_out, apex_z, y0, p.CELL_L, p,
                                      side_widths[k])
                tools.append(F.rotz(cav, k))
            # Vent 1: Innenfläche -> Ring 1; weitere Vents durch jeden
            # Zwischensteg bis in den jeweils nächsten Ring.
            vent_u = _vent_u_clear_of_plate_boss(uc, p)
            vents = [Part.makeCylinder(
                p.VENT_D / 2, p.INNER_WALL + 2,
                Vector(p.CUTOUT_W / 2 - 1, vent_u, p.VENT_Z),
                Vector(1, 0, 0))]
            vents += [Part.makeCylinder(
                p.VENT_D / 2, p.CHAMBER_RIB + 2,
                Vector(r_out - 1, vent_u, p.VENT_Z), Vector(1, 0, 0))
                for _, r_out in bands[:-1]]
            tools.extend(F.rotz(vent, k) for vent in vents)
    tools += _corner_chamber_cuts(p)
    return tools


def _drainage_cuts(p: PRM.Params):
    """Druckbare, nach außen fallende Deckfasen auf allen vier Seiten.

    Die kanonische Fase liegt an +x (REAR) und wird wie Kammern/Segmente um
    90° rotiert. 47° sind in der vorgesehenen Druckorientierung selbsttragend;
    die Belluna-Auflage und die M5-Kopfsenkungen bleiben vollständig eben.
    """
    big = 2000.0
    h = top_z(p)
    slope = math.tan(math.radians(p.TOP_DRAIN_DEG))
    tools = []
    for k, side_w in enumerate(PRM.side_top_widths(p)):
        outer = p.CUTOUT_W / 2 + side_w
        start = PRM.drainage_start(p, side_w)
        x_end = outer + 2.0
        z_end = h - (x_end - start) * slope
        y0 = -big / 2
        pts = [Vector(start, y0, h),
               Vector(start, y0, h + 2.0),
               Vector(x_end, y0, h + 2.0),
               Vector(x_end, y0, z_end)]
        face = Part.Face(Part.makePolygon(pts + [pts[0]]))
        tools.append(F.rotz(face.extrude(Vector(0, big, 0)), k))
    return tools


def _plate_screw_bosses(p: PRM.Params):
    """Lokale, FDM-gerechte Vollmaterialpfade für Belluna ST4.2x25.

    Kanonisch beginnt jede Rippe an der +x-Öffnungswand und endet nach
    PLATE_SCREW_BOSS_L im massiven Steg zwischen Kammerring 1 und 2. Der
    Querschnitt in (u,z) ist oben mit der Deckfläche verbunden und läuft
    unter der Schraubachse als 45°-Spitze aus: in Druckorientierung
    (Deckfläche auf dem Bett) wächst er ohne Support aus der Deckplatte.
    Beide Belluna-Varianten ±140/±165 sind auf jeder Seite vorhanden, aber
    ohne vorgefertigte Löcher; gebohrt wird nur durch das reale Plattenloch.
    """
    h = top_z(p)
    zc = h - p.PLATE_SCREW_Z_FROM_TOP
    half = p.PLATE_SCREW_BOSS_HALF
    x0 = p.CUTOUT_W / 2
    bosses = []
    for offset in p.PLATE_SCREW_OFFS:
        points = [Vector(x0, offset - half, h),
                  Vector(x0, offset + half, h),
                  Vector(x0, offset + half, zc),
                  Vector(x0, offset, zc - half),
                  Vector(x0, offset - half, zc)]
        face = Part.Face(Part.makePolygon(points + [points[0]]))
        boss = face.extrude(Vector(p.PLATE_SCREW_BOSS_L, 0, 0))
        for k in range(4):
            bosses.append(F.rotz(boss, k))
    return bosses


def _spacer_pads(p):
    """16 schmale Abstandspads vollständig über dem Holzrahmen.

    Je unterer Dachschraubachse sitzt ein Pad im trockenen inneren und eines
    im trockenen äußeren Randstreifen der Doppelraupe. Die längliche Form
    verteilt den Montagedruck, ohne Klebebänder oder Mittelkanal zu
    unterbrechen. Vier Rotationskopien halten die Universalteil-Logik ein.
    """
    pads = []
    for radial_off in PRM.spacer_pad_radial_centers(p):
        x = p.CUTOUT_W / 2 + radial_off
        for tangential_off in p.SPACER_PAD_OFFS:
            pad = F.rounded_box(
                p.SPACER_PAD_RADIAL,
                p.SPACER_PAD_TANGENTIAL,
                p.GLUE_GAP,
                p.SPACER_PAD_RADIUS,
                Vector(
                    x - p.SPACER_PAD_RADIAL / 2,
                    tangential_off - p.SPACER_PAD_TANGENTIAL / 2,
                    -p.GLUE_GAP,
                ),
            )
            for k in range(4):
                pads.append(F.rotz(pad, k))
    return pads


def _groove_cut_tools(p):
    """Zwei flache Kleberführungen mit belüfteter innerer Raupe.

    Die äußere Rille bleibt geometrisch geschlossen. Aus dem Cutter der
    inneren Rille werden je Seite zwei 5-mm-Brücken herausgenommen. Dort
    bleibt die Bodenfläche stehen, unterbricht die innere Kleberaupe und
    verbindet den 4-mm-Mittelkanal mit der trockenen Öffnungsseite.
    """
    specs = PRM.groove_specs(p)
    grooves = []
    for index, (off, width, _gap_length) in enumerate(specs):
        g_in = p.CUTOUT_W + 2 * off
        groove = F.ring(
            g_in + 2 * width, g_in + 2 * width,
            p.CUTOUT_R + off + width,
            g_in, g_in, p.CUTOUT_R + off,
            p.GROOVE_D + 1,
        )
        groove.translate(Vector(0, 0, -1))
        if index == 0:
            bridges = []
            x0 = p.CUTOUT_W / 2 + off - 1.0
            for k in range(4):
                for vent_off in p.GROOVE_VENT_OFFS:
                    bridge = Part.makeBox(
                        width + 2.0,
                        p.GROOVE_VENT_W,
                        p.GROOVE_D + 2.0,
                        Vector(x0, vent_off - p.GROOVE_VENT_W / 2, -1.0),
                    )
                    bridges.append(F.rotz(bridge, k))
            groove = groove.cut(Part.makeCompound(bridges))
        grooves.append(groove)
    return grooves


def _bot_kragen_tools(p):
    """Unterkragen: dupliziert den Belluna-Einbaukragen nach unten.

    Er taucht BOT_KRAGEN_DEPTH tief in den Dachausschnitt und zentriert den
    Rahmen. Im Hybridstand enthält er acht parametrische Seitenlöcher für die
    unqualifizierte Rückfallsicherung in den Holzrahmen. Rückgabe
    ``(fuse_teile, loch_cutter)``.

    Aufbau: Der Kragen (außen CUTOUT_W-2*CLEAR) liegt radial INNERHALB der
    Öffnungswand und hätte allein keinen Materialkontakt. Ein Übergangsring
    bettet ihn deshalb 2 mm radial in Bodenplatte/Innenwand ein (dort ist
    der Körper massiv); seine innere Oberkante bekommt eine 45°-Fase
    (BOT_KRAGEN_TRANS), damit die Übergangsfläche in Druckorientierung
    (kopfüber) selbsttragend ist.
    Die lichte Öffnung verengt sich dadurch unterhalb z~TRANS von CUTOUT_W
    auf das Kragen-Innenmaß; der Belluna-Kragen von oben endet bei
    z = top_z-19 und bleibt davon unberührt (>=4 mm Luft)."""
    ko = p.CUTOUT_W - 2 * p.BOT_KRAGEN_CLEAR           # außen, passt in den Ausschnitt
    ki = ko - 2 * p.BOT_KRAGEN_T                       # innen
    r_out = max(1.0, p.CUTOUT_R - p.BOT_KRAGEN_CLEAR)  # Ecke bleibt in der R5-Ecke
    r_in = max(0.5, r_out - 1.0)
    # Fasenoberkante bewusst niedrig (TRANS+0.5): die
    # Belluna-Kragenspitze taucht bis top_z - PLATE_KRAGEN_D (= z 6 bei
    # Defaults) in die Öffnung -- validate() sichert den Freigang
    trans_h = p.BOT_KRAGEN_TRANS + 0.5

    trans = F.ring(p.CUTOUT_W + 4, p.CUTOUT_W + 4, p.CUTOUT_R + 2,
                   ki, ki, r_in, trans_h)
    innen_oben = [e for e in trans.Edges
                  if abs(e.CenterOfMass.z - trans_h) < 1e-6
                  and max(abs(e.CenterOfMass.x), abs(e.CenterOfMass.y)) < ki / 2 + 1]
    trans = trans.makeChamfer(p.BOT_KRAGEN_TRANS, innen_oben)

    kragen = F.ring(ko, ko, r_out, ki, ki, r_in,
                    p.GLUE_GAP + p.BOT_KRAGEN_DEPTH + 2.0)
    kragen.translate(Vector(0, 0, -(p.GLUE_GAP + p.BOT_KRAGEN_DEPTH)))

    cutters = []
    z_loch = -(p.GLUE_GAP + p.BOT_KRAGEN_HOLE_Z)
    for k in range(4):
        for off in p.BOT_KRAGEN_HOLE_OFFS:
            zyl = Part.makeCylinder(p.BOT_KRAGEN_HOLE_D / 2, p.BOT_KRAGEN_T + 4,
                                    Vector(off, ki / 2 - 2, z_loch), Vector(0, 1, 0))
            cutters.append(F.rotz(zyl, k))
    return [trans, kragen], cutters


def build_frame(p: PRM.Params = PRM.P) -> Part.Shape:
    """Baut den kompletten Adapter-Monolithen (vor der Segmentierung) und gibt
    ihn als ``Part.Shape`` zurück. Koordinaten: z=0 = Dachoberfläche/Bettebene,
    +x = Fahrtrichtung (REAR), Ursprung in der Ausschnittmitte.

    Baureihenfolge (jeder boolesche Block schließt mit ``removeSplitter()`` und
    einer ``isValid()``-Wächterprüfung ab, damit ein defekter Zwischenkörper
    sofort abbricht statt still ein Fehlartefakt zu exportieren):
      1. ``validate(p)`` -- Parameter-Gate (bricht bei Inkonsistenz ab);
      2. Außenquader minus Ausschnitt -> Grundkörper;
      3. Gusset-Freistellungsring oben innen (No-Op bei REC_GUSSET_D=0);
      4. Kammer-Cuts (geschlossene Rippenzellen + Vent-Bohrungen, ersetzen den
         Slicer-Infill; inkl. Eckkammern falls CORNER_CHAMBERS);
      5. universelle Belluna-Schraubrippen (Fuse NACH den Kammern, damit die
         Kavitäten bis auf die lokalen Vollmaterialpfade erhalten bleiben);
      6. Entwässerungsfasen der bewitterten Außenablage;
      7. zwei untere Kleberführungen (Doppelraupe);
      8. optionaler Unterkragen (Fuse + Seitenlöcher, VOR der Außenfase);
      9. Außenfase unten (Elastikfugen-Kehle) an den z=0-Kanten nahe der
         Außenkontur;
     10. 16 Abstandspads über dem Holzrahmen."""
    PRM.validate(p)
    L, W = PRM.outer_dims(p)
    h = top_z(p)
    x0 = -(p.CUTOUT_W / 2 + p.W_TOP_FRONT)
    y0 = -(p.CUTOUT_W / 2 + p.W_TOP_LEFT)

    outer = F.rounded_box(L, W, h, p.R_OUT, Vector(x0, y0, 0))
    inner = F.rounded_box(p.CUTOUT_W, p.CUTOUT_W, h + 2, p.CUTOUT_R,
                          Vector(-p.CUTOUT_W / 2, -p.CUTOUT_W / 2, -1))
    body = outer.cut(inner)

    # Freistellung für die Gussets der Karosseriebefestigungsplatte (oben, innen)
    rec = F.ring(p.CUTOUT_W + 2 * p.REC_GUSSET_W, p.CUTOUT_W + 2 * p.REC_GUSSET_W,
                 p.CUTOUT_R + p.REC_GUSSET_W,
                 p.CUTOUT_W, p.CUTOUT_W, p.CUTOUT_R,
                 p.REC_GUSSET_D + 1)
    rec.translate(Vector(0, 0, h - p.REC_GUSSET_D))
    body = body.cut(rec)

    # Rippenkammern (geschlossene Zellen; ersetzen den Slicer-Infill --
    # Festigkeit ist jetzt geometrie-definiert, siehe Task 14)
    chamber_tools = _chamber_cuts(p)
    if chamber_tools:
        body = body.cut(chamber_tools)
        body = body.removeSplitter()
        if not body.isValid():
            raise RuntimeError("frame: Kammer-Cuts ergaben ungültigen Körper")

    # Universelle Belluna-Schraubrippen erst NACH den Kammer-Cuts einsetzen:
    # so bleiben die Kavitäten bis auf die lokalen 10-mm-Pfade erhalten.
    # Die Vent-Kanäle wurden oben nötigenfalls innerhalb ihrer Zelle versetzt,
    # damit keine Rippe den einzigen Druckausgleich einer Zelle verschließt.
    body = body.fuse(_plate_screw_bosses(p))
    body = body.removeSplitter()
    if not body.isValid():
        raise RuntimeError("frame: Belluna-Schraubrippen ergaben ungültigen Körper")

    # Bewitterte 25-mm-Außenablage der 450er Belluna-Platte entwässern.
    body = body.cut(Part.makeCompound(_drainage_cuts(p)))
    body = body.removeSplitter()
    if not body.isValid():
        raise RuntimeError("frame: Entwässerungsfasen ergaben ungültigen Körper")

    # Zwei Kleberführungen unten: äußere Raupe geschlossen, innere Raupe mit
    # definierten Trockenraum-Vents zum 4-mm-Mittelkanal.
    body = body.cut(Part.makeCompound(_groove_cut_tools(p)))

    # Unterkragen: VOR der Außenfase fusen/bohren -- der
    # Fasen-Kantenfilter unten greift nur nahe der Außenkontur und bleibt
    # vom innenliegenden Kragen unberührt
    if p.BOT_KRAGEN:
        kragen_teile, kragen_loecher = _bot_kragen_tools(p)
        body = body.fuse(kragen_teile)
        body = body.cut(Part.makeCompound(kragen_loecher))
        body = body.removeSplitter()
        if not body.isValid():
            raise RuntimeError("frame: Unterkragen-Booleans ergaben ungültigen Körper")

    # Außenfase unten (Elastikfugen-Kehlnaht): alle z=0-Kanten nahe der Außenkontur
    def _on_outer(e):
        c = e.CenterOfMass
        near_x = min(abs(c.x - x0), abs(c.x - (x0 + L))) < p.R_OUT + 1
        near_y = min(abs(c.y - y0), abs(c.y - (y0 + W))) < p.R_OUT + 1
        return abs(c.z) < 1e-6 and (near_x or near_y)
    fase_edges = [e for e in body.Edges if _on_outer(e)]
    if fase_edges:
        body = body.makeChamfer(p.CHAMFER_OUT, fase_edges)

    # 16 schmale 3-mm-Abstandspads statt 68 harter Rundnoppen. Die Pads
    # definieren nur den Montagespalt; der FEM-Lastpfad wird über die
    # verteilten Böden der beiden Kleberführungen gelagert.
    body = body.fuse(_spacer_pads(p))
    body = body.removeSplitter()
    if not body.isValid():
        raise RuntimeError("frame: Boolesche Operationen ergaben ungültigen Körper")
    return body
