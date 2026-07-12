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


def _chamber_cell_centers(p: PRM.Params):
    """u-Positionen (entlang einer Seite, Ursprung = Seitenmitte/Stoß) der
    Kammerzellen EINER Seitenhälfte (u > 0). Zellenraster CELL_L/CELL_RIB,
    zentriert im Band zwischen SOLID_JOINT_HALF und SOLID_CORNER (gemessen
    ab der -- konservativ über die schmalste Deckflächenbreite angenäherten --
    Außenkante). Identisches Raster für beide Kammerringe (dieselbe
    Seitenparameter-Herleitung), damit Ring 1 und Ring 2 dieselbe Zellenzahl
    erhalten (siehe Brief: sonst Vent-Fehlanbindung -> zusätzliche Shell)."""
    band_ref = min(p.W_TOP_FRONT, p.W_TOP_REAR, p.W_TOP_LEFT, p.W_TOP_RIGHT)
    side_half = p.CUTOUT_W / 2 + band_ref
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


def chamber_cell_count(p: PRM.Params = PRM.P) -> int:
    """Gesamtzahl der Kammerzellen über alle 4 Seiten (je Zelle: ein Kammerpaar
    Ring 1 + Ring 2 plus 2 Vent-Kanäle). Für die DFM-Vent-Allowance."""
    if not p.CHAMBERS:
        return 0
    half = _chamber_cell_centers(p)
    return 4 * 2 * len(half)          # 4 Seiten * (Band rechts + Band links vom Stoß)


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
    90 Grad rotiert für die 3 übrigen Seiten). Cut-Werkzeuge, kein Fuse."""
    if not p.CHAMBERS:
        return []
    r_in1 = p.CUTOUT_W / 2 + p.INNER_WALL
    r_out1 = r_in1 + p.CHAMBER_W
    r_in2 = r_out1 + p.CHAMBER_RIB
    r_out2 = r_in2 + p.CHAMBER_W
    apex_z = p.BOTTOM_T + math.tan(math.radians(p.CHEVRON_DEG)) * (p.CHAMBER_W / 2)
    half = _chamber_cell_centers(p)
    centers = half + [-c for c in half]

    tools = []
    for k in range(4):
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

    # Klebespalt-Noppen (definierte Elastikfugen-Dicke)
    nops = [Part.makeCylinder(p.NOPPLE_R, p.GLUE_GAP, Vector(x, y, -p.GLUE_GAP))
            for x, y in _nopple_positions(p)]
    body = body.fuse(nops)
    body = body.removeSplitter()
    if not body.isValid():
        raise RuntimeError("frame: Boolesche Operationen ergaben ungültigen Körper")
    return body
