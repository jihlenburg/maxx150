"""Design-for-Manufacturing-Prüfung: Überhänge in Druckorientierung.
Druckorientierung FDM: Deckfläche auf dem Bett (Teil kopfüber). Facetten,
deren Normale steiler als 45° nach unten zeigt und die nicht auf dem Bett
liegen, brauchen Stützen — außer in bewusst zugelassenen Brückenzonen."""
import math

import MeshPart
from FreeCAD import Matrix

import params as PRM
from model.frame import top_z

COS45 = math.cos(math.radians(45))


def _allowed_bridge_area(p):
    """Bewusst zugelassene Brücken (in Druckorientierung nach unten offen):
    Gusset-Freistellungsring + 4 Kopfsenkungen ringförmig + 4 Muttertaschen-Decken."""
    rec_ring = ((p.CUTOUT_W + 2 * p.REC_GUSSET_W) ** 2 - p.CUTOUT_W ** 2)
    cb = 4 * math.pi * (p.JOINT_CB_D / 2) ** 2
    nut = 4 * 2 * math.sqrt(3) * (p.JOINT_NUT_AF / 2) ** 2
    return rec_ring + cb + nut


def _facet_points(facet):
    return facet.Points


def _facet_area(facet, pts):
    if hasattr(facet, "Area"):
        return facet.Area
    # Fallback: Fläche aus den drei Eckpunkten per Kreuzprodukt (0.5*|AB x AC|)
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = pts
    abx, aby, abz = bx - ax, by - ay, bz - az
    acx, acy, acz = cx - ax, cy - ay, cz - az
    cx_ = aby * acz - abz * acy
    cy_ = abz * acx - abx * acz
    cz_ = abx * acy - aby * acx
    return 0.5 * math.sqrt(cx_ * cx_ + cy_ * cy_ + cz_ * cz_)


def overhang_area(shape, p: PRM.Params = PRM.P):
    flipped = shape.copy()
    flipped = flipped.transformGeometry(Matrix(1, 0, 0, 0,
                                               0, -1, 0, 0,
                                               0, 0, -1, 0))  # 180° um x
    zmin = flipped.BoundBox.ZMin
    mesh = MeshPart.meshFromShape(flipped, LinearDeflection=0.3,
                                  AngularDeflection=0.5, Relative=False)
    bad = 0.0
    for facet in mesh.Facets:
        n = facet.Normal
        pts = _facet_points(facet)
        z = min(pt.z for pt in pts) if hasattr(pts[0], "z") \
            else min(pt[2] for pt in pts)
        on_bed = z < zmin + 0.3
        if n.z < -COS45 and not on_bed:
            bad += _facet_area(facet, pts)
    return bad, _allowed_bridge_area(p)
