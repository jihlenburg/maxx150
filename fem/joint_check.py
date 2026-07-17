"""FEM-Submodell des Halbüberlappungsstoßes: die untere Lappe (LAP_L lang,
Bandbreite breit, halbe Körperhöhe dick) als Kragarm, eingespannt am Übergang
zum Segmentkern, belastet mit der vollen horizontalen Stoßlast (konservativ:
real teilen sich 4 Stöße + Verklebung die Last)."""
import Part
from FreeCAD import Vector

import params as PRM
from fem.loadcases import Case
from fem.run_fem import run_case


def _lap_shape(p):
    band = PRM.min_band(p)
    lap_h = PRM.lap_height(p)          # == top_z(p)/2, M1/Ledger 23/30/33
    return Part.makeBox(p.LAP_L, band, lap_h)


def run_joint_submodel(p: PRM.Params = PRM.P, f_inplane: float = None,
                       mesh_mm: float = 4.0) -> dict:
    """Rechnet das Kragarm-Submodell des Halbüberlappungsstoßes (siehe
    Moduldocstring): spannt die Lappe an ihrer x=0-Stirnfläche (Übergang zum
    Segmentkern) ein, leitet die in-plane-Last f (Default: Windlast) als Schub
    auf die Kontakt-Oberseite ein und gibt das FEM-Ergebnisdict von
    ``run_case`` zurück. mesh_mm steuert die Netzfeinheit (Default 4 mm, feiner
    als das Produktionsnetz)."""
    f = f_inplane if f_inplane is not None else PRM.wind_force(p)
    lap = _lap_shape(p)

    def _fixed(shape, _p):
        # Einspannfläche: x=0-Stirnseite (Übergang zum Segmentkern)
        return tuple(f"Face{i+1}" for i, fa in enumerate(shape.Faces)
                     if abs(fa.CenterOfMass.x) < 1e-6)

    def _loads(shape, _p):
        # Schub auf der Oberseite der Lappe (Kontaktfläche zum Partner)
        top = tuple(f"Face{i+1}" for i, fa in enumerate(shape.Faces)
                    if abs(fa.CenterOfMass.z - PRM.lap_height(_p)) < 1e-6)
        return [(top, Vector(1, 0, 0), f)]

    case = Case("Stoss", "kurz", _fixed, _loads)
    return run_case(lap, case, p, mesh_mm)
