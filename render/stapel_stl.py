"""Baugruppen-STLs: Belluna-Platten-Mock EINGESETZT in unseren Adapter
(gleiche Aufstellung wie render/passung_stapel.py), je Bauteil voll,
X-Halbschnitt (x>0 entfernt) und Y-Halbschnitt (y>0 entfernt).

Aufruf:  bin/fc render/stapel_stl.py
Ausgabe: out/stapel/{frame,platte,clips,seal}[_xcut|_ycut].stl
"""
import os
import sys

import FreeCAD as App
import MeshPart
import Part

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.getcwd())

import params as PRM                                    # noqa: E402
from model.frame import build_frame, top_z             # noqa: E402

OUT = os.path.join("out", "stapel")
os.makedirs(OUT, exist_ok=True)

os.environ["PLATTE_SKIP_EXPORT"] = "1"
ns = {}
src = open(os.path.join("render", "belluna_platte_mock.py")).read()
exec(compile(src, "belluna_platte_mock", "exec"), ns)

h = top_z()
teile = {}
for name, solid in (("platte", ns["body"]), ("clips", ns["clips_comp"]),
                    ("seal", ns["dichtring"])):
    s = solid.copy()
    s.translate(App.Vector(0, 0, h))
    teile[name] = s

print("== Rahmen bauen (Hash", PRM.params_hash() + ") ==")
teile["frame"] = build_frame(PRM.P)

halb_x = Part.makeBox(600, 1200, 400, App.Vector(0, -600, -150))
halb_y = Part.makeBox(1200, 600, 400, App.Vector(-600, 0, -150))


def stl(shape, name):
    mesh = MeshPart.meshFromShape(shape, LinearDeflection=0.08,
                                  AngularDeflection=0.4, Relative=False)
    mesh.write(os.path.join(OUT, name))
    print("STL:", name)


for name, solid in teile.items():
    stl(solid, f"{name}.stl")
    stl(solid.cut(halb_x), f"{name}_xcut.stl")
    stl(solid.cut(halb_y), f"{name}_ycut.stl")

print("STAPEL-STL-ENDE:", OUT)
