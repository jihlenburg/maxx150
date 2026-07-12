"""FEM-Submodell des Halbüberlappungsstoßes: die untere Lappe (LAP_L lang,
Bandbreite breit, halbe Körperhöhe dick) als Kragarm, eingespannt am Übergang
zum Segmentkern, belastet mit der vollen horizontalen Stoßlast (konservativ:
real teilen sich 4 Stöße + Verklebung die Last)."""
import Part
from FreeCAD import Vector

import params as PRM
from fem.loadcases import Case
from fem.run_fem import run_case
from model.frame import top_z


def _lap_shape(p):
    band = min(p.W_TOP_FRONT, p.W_TOP_REAR, p.W_TOP_LEFT, p.W_TOP_RIGHT)
    lap_h = top_z(p) / 2
    return Part.makeBox(p.LAP_L, band, lap_h)


def run_joint_submodel(p: PRM.Params = PRM.P, f_inplane: float = None,
                       mesh_mm: float = 4.0) -> dict:
    f = f_inplane if f_inplane is not None else PRM.wind_force(p)
    lap = _lap_shape(p)

    def _fixed(shape, _p):
        # Einspannfläche: x=0-Stirnseite (Übergang zum Segmentkern)
        return tuple(f"Face{i+1}" for i, fa in enumerate(shape.Faces)
                     if abs(fa.CenterOfMass.x) < 1e-6)

    def _loads(shape, _p):
        # Schub auf der Oberseite der Lappe (Kontaktfläche zum Partner)
        top = tuple(f"Face{i+1}" for i, fa in enumerate(shape.Faces)
                    if abs(fa.CenterOfMass.z - top_z(_p) / 2) < 1e-6)
        return [(top, Vector(1, 0, 0), f)]

    case = Case("Stoss", "kurz", _fixed, _loads)
    return run_case(lap, case, p, mesh_mm)
