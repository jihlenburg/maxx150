"""FreeCAD-Seite des Render-Workflows: baut die Render-STLs (voller Rahmen,
4 Segmente, Horizontal-/Vertikalschnitt) für den aktuellen Parameterstand.
Nutzt STEP-Dateien aus der Engineering-Stufe, falls vorhanden; andernfalls
wird frisch aus ``params.P`` gebaut.

Aufruf:  bin/fc render/make_views_stl.py
Schnittebenen als Umgebungsvariablen (freecadcmd-argv ist unzuverlaessig,
siehe Skill maxx150-pipeline):
  RENDER_ZCUT  Horizontalschnitt-Hoehe z (Default 14 -- Kammern offen sichtbar,
               Apex 12.04 < 14 < Deckflaeche 20 bei Default-Parametern)
  RENDER_XCUT  Vertikalschnitt-Ebene x (Default 120 -- schneidet die
               y-parallelen Baender im Profil)

Ausgabe: ``build/render/<hash>/``. Druckt zum Schluss
``RENDER-STL-ENDE: <verzeichnis>``."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import MeshPart  # noqa: E402
import Part  # noqa: E402
from FreeCAD import Vector  # noqa: E402

import params as PRM  # noqa: E402
from model.frame import build_frame  # noqa: E402
from model.segments import build_segments  # noqa: E402
from project_paths import engineering_dir, render_dir  # noqa: E402

ZCUT = float(os.environ.get("RENDER_ZCUT", "14"))
XCUT = float(os.environ.get("RENDER_XCUT", "120"))


def _write_stl(shape, path: Path):
    mesh = MeshPart.meshFromShape(shape, LinearDeflection=0.1, AngularDeflection=0.3,
                                  Relative=False)
    mesh.write(str(path))
    print(f"  {path.name}: {mesh.CountFacets} Facetten", flush=True)


def _load_or_build_frame(p, h):
    step = engineering_dir(h) / f"frame_{h}.step"
    if step.exists():
        shape = Part.Shape()
        shape.read(str(step))
        print(f"Rahmen: geladen aus {step.name}", flush=True)
        return shape
    print("Rahmen: kein passendes STEP gefunden -- baue aus params.P ...", flush=True)
    return build_frame(p)


def _load_or_build_segments(p, h):
    # Der kanonische Engineering-Export enthält bewusst nur das Universalteil
    # x4. Für Ansichten werden die vier positionierten Montagekopien benötigt.
    print("Segmente: baue vier positionierte Kopien aus params.P ...", flush=True)
    return build_segments(p)


def main():
    """Baut alle Render-STLs fuer den aktuellen Parameterstand: vollen Rahmen
    (aus Engineering-STEP oder frisch aus params.P), vier positionierte
    Segmente sowie Horizontalschnitt (z=ZCUT) und Vertikalschnitt (x=XCUT),
    nach ``build/render/<hash>/``. Laeuft unter freecadcmd."""
    p = PRM.P
    PRM.validate(p)
    h = PRM.params_hash(p)
    target = render_dir(h)
    target.mkdir(parents=True, exist_ok=True)

    print(f"Parameterstand {h}: Render-STLs nach {target}", flush=True)

    frame = _load_or_build_frame(p, h)
    _write_stl(frame, target / "frame.stl")

    for k, seg in enumerate(_load_or_build_segments(p, h)):
        _write_stl(seg, target / f"seg{k}.stl")

    print(f"Horizontalschnitt z={ZCUT} ...", flush=True)
    zcut = frame.cut(Part.makeBox(2000, 2000, 100, Vector(-1000, -1000, ZCUT)))
    _write_stl(zcut, target / "frame_zcut.stl")

    print(f"Vertikalschnitt x={XCUT} ...", flush=True)
    xcut = frame.cut(Part.makeBox(1000, 2000, 100, Vector(XCUT, -1000, -50)))
    _write_stl(xcut, target / "frame_xcut.stl")

    print(f"RENDER-STL-ENDE: {target}", flush=True)


main()
