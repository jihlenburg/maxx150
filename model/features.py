"""Wiederverwendbare Geometrie-Bausteine (reines Part-API, kein Dokument nötig)."""
import math

import Part
from FreeCAD import Vector


def _vertical_edges(solid, tol=1e-7):
    out = []
    for e in solid.Edges:
        vs = e.Vertexes
        if (len(vs) == 2 and abs(vs[0].X - vs[1].X) < tol
                and abs(vs[0].Y - vs[1].Y) < tol):
            out.append(e)
    return out


def rounded_box(length, width, height, radius, origin=Vector(0, 0, 0)):
    """Quader (length x width x height) ab origin (untere Ecke), mit an allen
    vier senkrechten Kanten auf radius verrundeten Ecken. radius=0 lässt den
    scharfkantigen Quader unverändert; z läuft von origin.z bis origin.z+height."""
    box = Part.makeBox(length, width, height, origin)
    if radius > 0:
        box = box.makeFillet(radius, _vertical_edges(box))
    return box


def rotz(shape, k):
    """Rotiert eine Kopie von shape um k*90 Grad um die z-Achse durch den
    Ursprung (Seiten-/Quadranten-/Ecken-Trick: dieselbe Konstruktion wird
    für alle vier Seiten/Ecken wiederverwendet). Konsolidierter Ersatz für
    die vormals identischen lokalen _rot()-Kopien in model/frame.py und
    model/segments.py (M1/Ledger 23/30/33)."""
    s = shape.copy()
    s.rotate(Vector(0, 0, 0), Vector(0, 0, 1), 90 * k)
    return s


def ring(outer_l, outer_w, r_out, inner_l, inner_w, r_in, h):
    """Rechteckring, zentriert um (0,0), z von 0 bis h."""
    outer = rounded_box(outer_l, outer_w, h, r_out,
                        Vector(-outer_l / 2, -outer_w / 2, 0))
    inner = rounded_box(inner_l, inner_w, h + 2, r_in,
                        Vector(-inner_l / 2, -inner_w / 2, -1))
    return outer.cut(inner)


def hex_prism(af, h, center_xy, z0):
    """Sechskantprisma (Muttertasche); af = Schlüsselweite."""
    r = af / 2 / math.cos(math.pi / 6)      # Umkreisradius
    cx, cy = center_xy
    pts = [Vector(cx + r * math.cos(a), cy + r * math.sin(a), z0)
           for a in [math.pi / 6 + i * math.pi / 3 for i in range(6)]]
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire).extrude(Vector(0, 0, h))


def rect_path_points(half_x, half_y, spacing):
    """Punkte auf dem Umfang eines Rechtecks (±half_x, ±half_y), von den Ecken
    um spacing/3 zurückgezogen, Abstand <= spacing."""
    pts = []

    def line(p0, p1):
        """Verteilt gleichmäßig Punkte auf die Strecke p0->p1 (Abstand <=
        spacing, mindestens 2 Punkte) und hängt sie an pts an."""
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        length = math.hypot(dx, dy)
        n = max(2, math.ceil(length / spacing) + 1)
        for i in range(n):
            t = i / (n - 1)
            pts.append((p0[0] + t * dx, p0[1] + t * dy))

    m = spacing / 3
    line((-half_x + m, -half_y), (half_x - m, -half_y))
    line((-half_x + m, half_y), (half_x - m, half_y))
    line((-half_x, -half_y + m), (-half_x, half_y - m))
    line((half_x, -half_y + m), (half_x, half_y - m))
    return pts
