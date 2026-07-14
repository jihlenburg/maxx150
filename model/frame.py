"""Adapterrahmen (vor Segmentierung) mit Rippenkammern statt Slicer-Infill."""
import math

import Part
from FreeCAD import Vector

import params as PRM
from model import features as F


def top_z(p: PRM.Params = PRM.P) -> float:
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
    """Belluna-Seitenlöcher in Kammerreihenfolge REAR, RIGHT, FRONT, LEFT.

    ``BOT_KRAGEN_HOLE_OFFS_BY_SIDE`` ist in der Werkzeug-Rotationsreihenfolge
    RIGHT, FRONT, LEFT, REAR abgelegt. Ober- und Unterinterface verwenden
    bewusst dieselben acht äußeren Belluna-Positionen.
    """
    right, front, left, rear = p.BOT_KRAGEN_HOLE_OFFS_BY_SIDE
    return rear, right, front, left


def _without_plate_screw_cells(centers, offsets, p: PRM.Params):
    """Entfernt Kammerzellen, die den radialen ST4.2-Schraubpfad kreuzen."""
    keep = p.CELL_L / 2 + p.PLATE_SCREW_KEEP_HALF
    return [center for center in centers
            if all(abs(center - offset) > keep for offset in offsets)]


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
    screw_offsets = _plate_screw_offsets_by_chamber_side(p)
    for k, (plus_w, minus_w) in enumerate(_side_neighbor_bounds(p)):
        centers = (_chamber_cell_centers(p, plus_w)
                   + [-c for c in _chamber_cell_centers(p, minus_w)])
        total += len(_without_plate_screw_cells(centers, screw_offsets[k], p))
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
    """Radiale Grenzen der beiden konzentrischen Kammerringe, gemessen von
    der globalen Mittelachse (identisch für alle 4 geraden Seiten UND
    Grundlage der Eckkammer-Radien, siehe _corner_chamber_cuts)."""
    r_in1 = p.CUTOUT_W / 2 + p.INNER_WALL
    r_out1 = r_in1 + p.CHAMBER_W
    r_in2 = r_out1 + p.CHAMBER_RIB
    r_out2 = r_in2 + p.CHAMBER_W
    return r_in1, r_out1, r_in2, r_out2


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
    (r_in1..r_out2) - off vom Eckzentrum entfernt (Defaults: 13/28/32/47,
    siehe Brief).

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
    r_in1, r_out1, r_in2, r_out2 = _ring_radii(p)
    apex_z = p.BOTTOM_T + math.tan(math.radians(p.CHEVRON_DEG)) * (p.CHAMBER_W / 2)
    margin = p.CORNER_ANGLE_MARGIN
    sweep = 90 - 2 * margin
    if sweep <= 0:
        raise RuntimeError("frame: CORNER_ANGLE_MARGIN >= 45 lässt keinen Eck-Sektor übrig "
                           "(PRM.validate sollte das vorher abfangen)")

    # Die Entwässerungsfasen schneiden an den Ecksektor-Rändern tiefer als
    # auf den geraden Ringprofilen. Eine einheitlich abgesenkte Eckkammerdecke
    # hält dort konservativ mindestens DECK_T Material geschlossen.
    corner_axis_max = off + (r_out2 - off) * math.cos(math.radians(margin))
    corner_drop = max(
        max(0.0, corner_axis_max - PRM.drainage_start(p, side_w))
        * math.tan(math.radians(p.TOP_DRAIN_DEG))
        for side_w in PRM.side_top_widths(p)
    )
    corner_z_top = top_z(p) - p.DECK_T - corner_drop

    tools = []
    cr_out1 = r_out1 - off
    for r_in, r_out in ((r_in1 - off, cr_out1), (r_in2 - off, r_out2 - off)):
        face = _chamber_profile_face(r_in, r_out, apex_z, 0.0, p,
                                     z_top_override=corner_z_top)
        face.rotate(Vector(0, 0, 0), Vector(0, 0, 1), margin)
        solid = face.revolve(Vector(0, 0, 0), Vector(0, 0, 1), sweep)
        solid.translate(Vector(off, off, 0))
        for k in range(4):
            tools.append(F.rotz(solid, k))

    # Vents entlang der 45°-Diagonale (kanonische (+,+)-Ecke, dann F.rotz):
    diag = Vector(math.cos(math.radians(45)), math.sin(math.radians(45)), 0)
    for r0, length in ((p.CUTOUT_R - 1, p.INNER_WALL + 2),
                       (cr_out1 - 1, p.CHAMBER_RIB + 2)):
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
    r_in1, r_out1, r_in2, r_out2 = _ring_radii(p)
    apex_z = p.BOTTOM_T + math.tan(math.radians(p.CHEVRON_DEG)) * (p.CHAMBER_W / 2)
    neighbor_bounds = _side_neighbor_bounds(p)
    side_widths = PRM.side_top_widths(p)
    screw_offsets = _plate_screw_offsets_by_chamber_side(p)

    tools = []
    for k in range(4):
        plus_w, minus_w = neighbor_bounds[k]
        plus_half = _chamber_cell_centers(p, plus_w)
        minus_half = _chamber_cell_centers(p, minus_w)
        centers = _without_plate_screw_cells(
            plus_half + [-c for c in minus_half], screw_offsets[k], p)
        for uc in centers:
            y0 = uc - p.CELL_L / 2
            for r_in, r_out in ((r_in1, r_out1), (r_in2, r_out2)):
                cav = _chamber_cavity(r_in, r_out, apex_z, y0, p.CELL_L, p,
                                      side_widths[k])
                tools.append(F.rotz(cav, k))
            # Vent 1: Innenfläche (Öffnungskante) -> Kammerring 1 (durch INNER_WALL)
            v1 = Part.makeCylinder(p.VENT_D / 2, p.INNER_WALL + 2,
                                   Vector(p.CUTOUT_W / 2 - 1, uc, p.VENT_Z),
                                   Vector(1, 0, 0))
            # Vent 2: Kammerring 1 -> Kammerring 2 (durch den Steg CHAMBER_RIB)
            v2 = Part.makeCylinder(p.VENT_D / 2, p.CHAMBER_RIB + 2,
                                   Vector(r_out1 - 1, uc, p.VENT_Z),
                                   Vector(1, 0, 0))
            tools.append(F.rotz(v1, k))
            tools.append(F.rotz(v2, k))
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


def _nopple_positions(p):
    """Zwei Noppenringe: innen (zwischen Öffnung und Rille) und außen
    (zwischen Rille und Außenkante)."""
    inner_r = p.CUTOUT_W / 2 + p.GROOVE_OFF / 2                       # ~207.5
    outer_r = p.CUTOUT_W / 2 + p.GROOVE_OFF + p.GROOVE_W + 12         # ~235
    pts = F.rect_path_points(inner_r, inner_r, p.NOPPLE_SPACING)
    pts += F.rect_path_points(outer_r, outer_r, p.NOPPLE_SPACING)
    return pts


def _bot_kragen_tools(p):
    """Unterkragen: dupliziert den Belluna-Einbaukragen nach
    unten -- taucht BOT_KRAGEN_DEPTH tief in den Dachausschnitt und trägt
    2 seitliche Schraubenlöcher je Seite (8 gesamt, die äußeren Positionen
    des gemessenen Belluna-Lochbilds). Rückgabe (fuse_teile, loch_cutter).

    Aufbau: Der Kragen (außen CUTOUT_W-2*CLEAR) liegt radial INNERHALB der
    Öffnungswand und hätte allein keinen Materialkontakt. Ein Übergangsring
    bettet ihn deshalb 2 mm radial in Bodenplatte/Innenwand ein (dort ist
    der Körper massiv); seine innere Oberkante bekommt eine 45°-Fase
    (BOT_KRAGEN_TRANS), damit die Übergangsfläche in Druckorientierung
    (kopfüber) selbsttragend ist -- gleiches Prinzip wie der Noppenkegel.
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
    for k, offsets in enumerate(p.BOT_KRAGEN_HOLE_OFFS_BY_SIDE):
        for off in offsets:
            zyl = Part.makeCylinder(p.BOT_KRAGEN_HOLE_D / 2, p.BOT_KRAGEN_T + 4,
                                    Vector(off, ki / 2 - 2, z_loch), Vector(0, 1, 0))
            cutters.append(F.rotz(zyl, k))
    return [trans, kragen], cutters


def build_frame(p: PRM.Params = PRM.P) -> Part.Shape:
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

    # Bewitterte 25-mm-Außenablage der 450er Belluna-Platte entwässern.
    body = body.cut(Part.makeCompound(_drainage_cuts(p)))
    body = body.removeSplitter()
    if not body.isValid():
        raise RuntimeError("frame: Entwässerungsfasen ergaben ungültigen Körper")

    # Kleberille unten
    g_in = p.CUTOUT_W + 2 * p.GROOVE_OFF
    groove = F.ring(g_in + 2 * p.GROOVE_W, g_in + 2 * p.GROOVE_W,
                    p.CUTOUT_R + p.GROOVE_OFF + p.GROOVE_W,
                    g_in, g_in, p.CUTOUT_R + p.GROOVE_OFF,
                    p.GROOVE_D + 1)
    groove.translate(Vector(0, 0, -1))
    body = body.cut(groove)

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

    # Außenfase unten (Sika-Kehlnaht): alle z=0-Kanten nahe der Außenkontur
    def _on_outer(e):
        c = e.CenterOfMass
        near_x = min(abs(c.x - x0), abs(c.x - (x0 + L))) < p.R_OUT + 1
        near_y = min(abs(c.y - y0), abs(c.y - (y0 + W))) < p.R_OUT + 1
        return abs(c.z) < 1e-6 and (near_x or near_y)
    fase_edges = [e for e in body.Edges if _on_outer(e)]
    if fase_edges:
        body = body.makeChamfer(p.CHAMFER_OUT, fase_edges)

    # Klebespalt-Noppen (definierte Elastikfugen-Dicke) + Übergangskegel am
    # Fuß (Heatmap 2026-07-12: ALLE LF-Hotspots sitzen am Noppenfuß des
    # äußeren Rings, r~238, z~-0.8 -- billigster Hebel gegen die einzige
    # echte Kerbzone). Der Kegel füllt z in [-NOPPLE_FILLET, 0]: radius
    # NOPPLE_R bei z=-NOPPLE_FILLET (deckungsgleich mit dem Zylinder, der
    # dort ohnehin schon Material hat -- reiner Fuse-Zusatz nach außen) bis
    # radius NOPPLE_R+NOPPLE_FILLET bei z=0 (Übergang in die Bodenfläche) --
    # weitet sich zum Körper. Kegelflanke NOPPLE_FILLET/NOPPLE_FILLET = 45°
    # -> in Druckorientierung (kopfüber) selbsttragend, DFM unverändert.
    # ACHTUNG (Task 15, live gefunden über test_loadcases.test_face_selektoren):
    # der Kegel teilt die vormals durchgehende Zylindermantelfläche bei
    # z=-NOPPLE_FILLET in zwei Flächen. fem/loadcases.py::nopple_faces nahm
    # bislang JEDE Fläche mit CenterOfMass nahe z=-GLUE_GAP (reiner
    # Toleranzfilter, tol=1.0) -- die neue, kürzere untere Zylinder-Restfläche
    # (CoM jetzt näher an -GLUE_GAP als die alte volle Mantelfläche) wäre
    # damit fälschlich als Noppen-Stirnfläche in die FEM-Randbedingung
    # gerutscht. Fix dort: Plane+Normalen-Filter (wie top_faces) statt
    # reiner CoM-Toleranz -- selektiert wieder exakt dieselben Stirnflächen
    # wie vor dem Kegel.
    nops = []
    for x, y in _nopple_positions(p):
        nops.append(Part.makeCylinder(p.NOPPLE_R, p.GLUE_GAP, Vector(x, y, -p.GLUE_GAP)))
        if p.NOPPLE_FILLET > 0:
            nops.append(Part.makeCone(p.NOPPLE_R + p.NOPPLE_FILLET, p.NOPPLE_R,
                                      p.NOPPLE_FILLET, Vector(x, y, 0),
                                      Vector(0, 0, -1)))
    body = body.fuse(nops)
    body = body.removeSplitter()
    if not body.isValid():
        raise RuntimeError("frame: Boolesche Operationen ergaben ungültigen Körper")
    return body
