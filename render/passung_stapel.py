"""Digitaler Passungstest: Belluna-Platten-Mock EINGESETZT in unseren
Adapterrahmen (Platte ruht auf der Deckflaeche, Kragen taucht in die
Oeffnung). Prueft Kollision, Radialspiel, Steg-Auflage und die
Schraubkorridore Platte->Innenwand. NICHT Teil der Druck-Pipeline.

Aufruf:  bin/fc render/passung_stapel.py
"""
import os
import sys

import FreeCAD as App
import Part

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.getcwd())

import params as PRM                                    # noqa: E402
from model import features as F                        # noqa: E402
from model.frame import build_frame, top_z             # noqa: E402

# --- Platten-Mock als Solids holen (ohne STL-Export) ---
os.environ["PLATTE_SKIP_EXPORT"] = "1"
ns = {}
src = open(os.path.join("render", "belluna_platte_mock.py")).read()
exec(compile(src, "belluna_platte_mock", "exec"), ns)

h = top_z()
platte = ns["body"].copy()
platte.translate(App.Vector(0, 0, h))                  # Auflage auf Deckflaeche

print("== Rahmen bauen (PRM.P, Hash", PRM.params_hash() + ") ==")
frame = build_frame(PRM.P)

# 1) Nominal-Kollision
kol = frame.common(platte)
print(f"KOLLISION nominal: {kol.Volume:.3f} mm^3", flush=True)
if kol.Volume > 1e-6:
    bb = kol.BoundBox
    print(f"  Zone: x {bb.XMin:.1f}..{bb.XMax:.1f}  y {bb.YMin:.1f}..{bb.YMax:.1f}"
          f"  z {bb.ZMin:.1f}..{bb.ZMax:.1f}")

# 2) Radialspiel: Platte seitlich versetzen, bis es klemmt
for dx in (0.5, 0.9, 1.1, 1.5):
    s = platte.copy()
    s.translate(App.Vector(dx, 0, 0))
    v = frame.common(s).Volume
    print(f"VERSATZ +x {dx:.1f} mm: Kollision {v:.2f} mm^3")

# 3) Steg-Auflage: duenne Pruefringe knapp unter der Deckflaeche -- liegt
#    unter jedem der drei Platten-Stege durchgehend Rahmenmaterial?
STEGE = ns["STEGE"]                                     # ((207,209),(215,217),(223,225)) halb


def _r(halb):
    return max(3.0, 18.0 - (225.0 - halb))


for name, (ri, ro) in zip(("innen", "mitte", "aussen"), STEGE):
    probe = F.ring(2 * ro, 2 * ro, _r(ro), 2 * ri, 2 * ri, _r(ri), 0.3)
    probe.translate(App.Vector(0, 0, h - 0.35))
    getragen = frame.common(probe).Volume
    print(f"AUFLAGE Steg {name} ({ri}..{ro}): {getragen:.0f} von "
          f"{probe.Volume:.0f} mm^3 unterfuettert")

# 4) Schraubkorridore Platte->Innenwand (F: Ø4, Mitte 10 unter Auflage):
#    Vollmaterial-Erwartung je Korridor = pi*r^2*INNER_WALL
p = PRM.P
z_s = h - 10.0
soll = 3.141592653589793 * 2.0 ** 2 * p.INNER_WALL
for off in (0.0, 140.0, 165.0):
    zyl = Part.makeCylinder(2.0, 14, App.Vector(off, p.CUTOUT_W / 2 - 2, z_s),
                            App.Vector(0, 1, 0))
    ist = frame.common(zyl).Volume
    marke = "OK" if ist > soll * 0.95 else "!! HOHLRAUM im Korridor (Vent?)"
    print(f"SCHRAUBKORRIDOR y-Seite, Offset {off:.0f}: {ist:.1f} / {soll:.1f} mm^3  {marke}")

print("PASSUNG-ENDE")
