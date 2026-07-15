"""Exportiert die vermessene Belluna-Rekonstruktion als Referenzdateien."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(line_buffering=True)

import MeshPart  # noqa: E402
import Part  # noqa: E402

from export.export import _normalize_step_header  # noqa: E402
from project_paths import REFERENCES_ROOT  # noqa: E402
from reference_models.belluna import metadata, shapes  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def _write_stl(shape, path: Path) -> None:
    mesh = MeshPart.meshFromShape(shape, LinearDeflection=0.05,
                                  AngularDeflection=0.35, Relative=False)
    mesh.write(str(path))


def main() -> None:
    target = REFERENCES_ROOT / "belluna" / "models"
    target.mkdir(parents=True, exist_ok=True)
    components = shapes()
    components["belluna_baugruppe"] = Part.makeCompound(list(components.values()))

    files = []
    for name, shape in components.items():
        step = target / f"{name}.step"
        stl = target / f"{name}.stl"
        shape.exportStep(str(step))
        _normalize_step_header(step)
        _write_stl(shape, stl)
        files.extend((step, stl))
        print(f"Referenz: {step.name}, {stl.name}", flush=True)

    manifest = {
        "schema": 2,
        "description": "Vermessene Rekonstruktion; kein Belluna-Hersteller-CAD",
        "source": "reference_models/belluna.py",
        "source_sha256": _sha256(ROOT / "reference_models" / "belluna.py"),
        "provenance": metadata(),
        "files": {path.name: {"sha256": _sha256(path), "bytes": path.stat().st_size}
                  for path in files},
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"REFERENZEN-ENDE: {target}", flush=True)


# freecadcmd setzt ``__name__`` beim Skriptimport nicht zuverlässig auf
# ``__main__``; ausführbare FreeCAD-Stufen werden deshalb bewusst direkt
# aufgerufen (gleiche Konvention wie tests/run_tests.py).
main()
