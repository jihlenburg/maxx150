"""Monolithischer Adapterrahmen (vor Segmentierung)."""
import Part
from FreeCAD import Vector

import params as PRM
from model import features as F


def top_z(p: PRM.Params = PRM.P) -> float:
    return p.H_RAISE - p.GLUE_GAP


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
