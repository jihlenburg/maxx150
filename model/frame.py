"""Adapterrahmen (vor Segmentierung) mit Rippenkammern statt Slicer-Infill."""
import math

import Part
from FreeCAD import Vector

import params as PRM
from model import features as F


def top_z(p: PRM.Params = PRM.P) -> float:
    return p.H_RAISE - p.GLUE_GAP


def _rot(shape, k):
    """Rotiert ein Werkzeug um k*90 Grad um die z-Achse (Seiten-/Quadrantentrick,
    analog model/segments.py)."""
    s = shape.copy()
    s.rotate(Vector(0, 0, 0), Vector(0, 0, 1), 90 * k)
    return s


def _chamber_cell_centers(p: PRM.Params, limit_w: float):
    """u-Positionen (entlang einer Seite, Ursprung = Seitenmitte/Stoß) der
    Kammerzellen EINER Seiten-HALBSEITE (u > 0, also nur +u ODER nur -u,
    je nachdem welche Nachbargrenze der Aufrufer übergibt -- siehe
    _side_neighbor_bounds). Zellenraster CELL_L/CELL_RIB, zentriert im Band
    zwischen SOLID_JOINT_HALF und SOLID_CORNER.

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
    identischer chamber_slot_count (Regressionsanker)."""
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
    for plus_w, minus_w in _side_neighbor_bounds(p):
        total += len(_chamber_cell_centers(p, plus_w))
        total += len(_chamber_cell_centers(p, minus_w))
    return total


def _chamber_profile_face(r_in, r_out, apex_z, y0, p):
    """Kammerquerschnitt als (r,z)-Polygon in der Ebene y=y0: flache Decke
    (z = top_z - DECK_T), senkrechte Wände bei r_in/r_out, Boden als Zelt
    (Chevron-Apex mittig bei apex_z)."""
    z_top = top_z(p) - p.DECK_T
    z_bot = p.BOTTOM_T
    r_mid = (r_in + r_out) / 2
    pts = [Vector(r_in, y0, z_bot), Vector(r_in, y0, z_top),
           Vector(r_out, y0, z_top), Vector(r_out, y0, z_bot),
           Vector(r_mid, y0, apex_z)]
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire)


def _chamber_cavity(r_in, r_out, apex_z, y0, length, p):
    face = _chamber_profile_face(r_in, r_out, apex_z, y0, p)
    return face.extrude(Vector(0, length, 0))


def _chamber_cuts(p: PRM.Params):
    """Alle Kammer-Hohlräume + Vent-Bohrungen (kanonische +x-Seite, dann je
    90 Grad rotiert für die 3 übrigen Seiten). Cut-Werkzeuge, kein Fuse.

    Kanonik k<->Seite (hergeleitet aus build_frame, NICHT angenommen):
    x0 = -(CUTOUT_W/2 + W_TOP_FRONT), x0+L = CUTOUT_W/2 + W_TOP_REAR ->
    die -x-Bandbreite ist W_TOP_FRONT, die +x-Bandbreite ist W_TOP_REAR:
    +x-Seite = REAR. _rot() dreht um +90*k Grad um +z (Part.Shape.rotate,
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
    asymmetrischen W_TOP unterschiedlich groß sein können."""
    if not p.CHAMBERS:
        return []
    r_in1 = p.CUTOUT_W / 2 + p.INNER_WALL
    r_out1 = r_in1 + p.CHAMBER_W
    r_in2 = r_out1 + p.CHAMBER_RIB
    r_out2 = r_in2 + p.CHAMBER_W
    apex_z = p.BOTTOM_T + math.tan(math.radians(p.CHEVRON_DEG)) * (p.CHAMBER_W / 2)
    neighbor_bounds = _side_neighbor_bounds(p)

    tools = []
    for k in range(4):
        plus_w, minus_w = neighbor_bounds[k]
        plus_half = _chamber_cell_centers(p, plus_w)
        minus_half = _chamber_cell_centers(p, minus_w)
        centers = plus_half + [-c for c in minus_half]
        for uc in centers:
            y0 = uc - p.CELL_L / 2
            for r_in, r_out in ((r_in1, r_out1), (r_in2, r_out2)):
                cav = _chamber_cavity(r_in, r_out, apex_z, y0, p.CELL_L, p)
                tools.append(_rot(cav, k))
            # Vent 1: Innenfläche (Öffnungskante) -> Kammerring 1 (durch INNER_WALL)
            v1 = Part.makeCylinder(p.VENT_D / 2, p.INNER_WALL + 2,
                                   Vector(p.CUTOUT_W / 2 - 1, uc, p.VENT_Z),
                                   Vector(1, 0, 0))
            # Vent 2: Kammerring 1 -> Kammerring 2 (durch den Steg CHAMBER_RIB)
            v2 = Part.makeCylinder(p.VENT_D / 2, p.CHAMBER_RIB + 2,
                                   Vector(r_out1 - 1, uc, p.VENT_Z),
                                   Vector(1, 0, 0))
            tools.append(_rot(v1, k))
            tools.append(_rot(v2, k))
    return tools


def _nopple_positions(p):
    """Zwei Noppenringe: innen (zwischen Öffnung und Rille) und außen
    (zwischen Rille und Außenkante)."""
    inner_r = p.CUTOUT_W / 2 + p.GROOVE_OFF / 2                       # ~207.5
    outer_r = p.CUTOUT_W / 2 + p.GROOVE_OFF + p.GROOVE_W + 12         # ~235
    pts = F.rect_path_points(inner_r, inner_r, p.NOPPLE_SPACING)
    pts += F.rect_path_points(outer_r, outer_r, p.NOPPLE_SPACING)
    return pts


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

    # Kleberille unten
    g_in = p.CUTOUT_W + 2 * p.GROOVE_OFF
    groove = F.ring(g_in + 2 * p.GROOVE_W, g_in + 2 * p.GROOVE_W,
                    p.CUTOUT_R + p.GROOVE_OFF + p.GROOVE_W,
                    g_in, g_in, p.CUTOUT_R + p.GROOVE_OFF,
                    p.GROOVE_D + 1)
    groove.translate(Vector(0, 0, -1))
    body = body.cut(groove)

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
