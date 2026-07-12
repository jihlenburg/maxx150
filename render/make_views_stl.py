"""FreeCAD-Seite des Render-Workflows: baut die Render-STLs (voller Rahmen,
4 Segmente, Horizontal-/Vertikalschnitt) fuer den aktuellen Parameterstand.

Nutzt die bereits exportierten STEP-Dateien in out/ (frame_<hash>.step,
seg{0..3}_<hash>.step, aus export.export_all), falls vorhanden -- sonst wird
frisch aus params.P gebaut (dauert je nach Segmentanzahl einige Minuten).

Aufruf:  bin/fc render/make_views_stl.py
Schnittebenen als Umgebungsvariablen (freecadcmd-argv ist unzuverlaessig,
siehe Skill maxx150-pipeline):
  RENDER_ZCUT  Horizontalschnitt-Hoehe z (Default 14 -- Kammern offen sichtbar,
               Apex 12.04 < 14 < Deckflaeche 20 bei Default-Parametern)
  RENDER_XCUT  Vertikalschnitt-Ebene x (Default 120 -- schneidet die
               y-parallelen Baender im Profil)

Ausgabe: out/render/<hash>/frame.stl, seg{0..3}.stl, frame_zcut.stl,
frame_xcut.stl. Druckt zum Schluss "RENDER-STL-ENDE: <out_dir>" (wird von
scripts/render.sh geparst)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import MeshPart
import Part
from FreeCAD import Vector

import params as PRM
from model.frame import build_frame
from model.segments import build_segments

ZCUT = float(os.environ.get("RENDER_ZCUT", "14"))
XCUT = float(os.environ.get("RENDER_XCUT", "120"))


def _write_stl(shape, path: Path):
    mesh = MeshPart.meshFromShape(shape, LinearDeflection=0.1, AngularDeflection=0.3,
                                  Relative=False)
    mesh.write(str(path))
    print(f"  {path.name}: {mesh.CountFacets} Facetten", flush=True)


def _load_or_build_frame(p, h, out_dir):
    step = out_dir / f"frame_{h}.step"
    if step.exists():
        shape = Part.Shape()
        shape.read(str(step))
        print(f"Rahmen: geladen aus {step.name}", flush=True)
        return shape
    print("Rahmen: kein passendes STEP gefunden -- baue aus params.P ...", flush=True)
    return build_frame(p)


def _load_or_build_segments(p, h, out_dir):
    steps = [out_dir / f"seg{k}_{h}.step" for k in range(p.N_SEGMENTS)]
    if all(s.exists() for s in steps):
        segs = []
        for s in steps:
            shape = Part.Shape()
            shape.read(str(s))
            segs.append(shape)
        print("Segmente: geladen aus STEP", flush=True)
        return segs
    print("Segmente: kein vollstaendiger STEP-Satz -- baue aus params.P ...", flush=True)
    return build_segments(p)


def main():
    p = PRM.P
    PRM.validate(p)
    h = PRM.params_hash(p)
    out_dir = ROOT / "out"
    render_dir = out_dir / "render" / h
    render_dir.mkdir(parents=True, exist_ok=True)

    print(f"Parameterstand {h}: Render-STLs nach {render_dir}", flush=True)

    frame = _load_or_build_frame(p, h, out_dir)
    _write_stl(frame, render_dir / "frame.stl")

    for k, seg in enumerate(_load_or_build_segments(p, h, out_dir)):
        _write_stl(seg, render_dir / f"seg{k}.stl")

    print(f"Horizontalschnitt z={ZCUT} ...", flush=True)
    zcut = frame.cut(Part.makeBox(2000, 2000, 100, Vector(-1000, -1000, ZCUT)))
    _write_stl(zcut, render_dir / "frame_zcut.stl")

    print(f"Vertikalschnitt x={XCUT} ...", flush=True)
    xcut = frame.cut(Part.makeBox(1000, 2000, 100, Vector(XCUT, -1000, -50)))
    _write_stl(xcut, render_dir / "frame_xcut.stl")

    print(f"RENDER-STL-ENDE: {render_dir}", flush=True)


main()
