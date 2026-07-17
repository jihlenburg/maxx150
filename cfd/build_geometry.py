"""Exportiert die Belluna-CFD-Hüllgeometrien als STEP und Meter-STL."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(line_buffering=True)

import MeshPart  # noqa: E402

from cfd.config import cfd_hash, manual_path, selected_case  # noqa: E402
from export.export import _normalize_step_header  # noqa: E402
from project_paths import cfd_dir  # noqa: E402
from reference_models.belluna_aero import metadata, shapes  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_stl_m(shape, path: Path) -> None:
    """ASCII-STL in Metern; FreeCAD-Modell und STEP bleiben in Millimetern."""
    mesh = MeshPart.meshFromShape(shape, LinearDeflection=0.8,
                                  AngularDeflection=0.25, Relative=False)
    points, facets = mesh.Topology
    with path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(f"solid {path.stem}\n")
        for a, b, c in facets:
            p0, p1, p2 = points[a], points[b], points[c]
            normal = (p1 - p0).cross(p2 - p0)
            length = normal.Length
            if length:
                normal.multiply(1.0 / length)
            stream.write(
                f"  facet normal {normal.x:.9g} {normal.y:.9g} {normal.z:.9g}\n"
                "    outer loop\n"
            )
            for point in (p0, p1, p2):
                stream.write(
                    f"      vertex {point.x * 0.001:.9g} "
                    f"{point.y * 0.001:.9g} {point.z * 0.001:.9g}\n"
                )
            stream.write("    endloop\n  endfacet\n")
        stream.write(f"endsolid {path.stem}\n")


def main() -> None:
    """Exportiert die drei CFD-Hüllgeometrien (Belluna, Adapter, Dachkante) als
    mm-STEP und Meter-STL in den CFD-Geometrie-Build-Baum und schreibt ein
    Provenienz-Manifest (Quell-Commit, Anleitungs-SHA256, Datei-Hashes). Läuft
    unter freecadcmd."""
    case = selected_case()
    digest = cfd_hash(case)
    target = cfd_dir(digest) / "geometry"
    target.mkdir(parents=True, exist_ok=True)
    files = []
    for name, shape in shapes().items():
        if not shape.isValid():
            raise RuntimeError(f"Ungültige CFD-Hüllgeometrie: {name}")
        step = target / f"{name}.step"
        stl = target / f"{name}.stl"
        shape.exportStep(str(step))
        _normalize_step_header(step)
        _write_stl_m(shape, stl)
        files.extend((step, stl))
        print(f"CFD-Geometrie: {step.name}, {stl.name}", flush=True)

    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest = {
        "schema": 1,
        "cfd_hash": digest,
        "case": case.name,
        "source_commit": source_commit,
        "manual_sha256": _sha256(manual_path()),
        "provenance": metadata(),
        "units": {"step": "mm", "stl": "m"},
        "files": {
            path.name: {"sha256": _sha256(path), "bytes": path.stat().st_size}
            for path in files
        },
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"CFD-GEOMETRIE-ENDE: {target}", flush=True)


# freecadcmd führt Skripte nicht zuverlässig mit __name__ == "__main__" aus.
main()
