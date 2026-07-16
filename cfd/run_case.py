"""Vernetzt, rechnet und protokolliert den generierten OpenFOAM-Fall."""
from __future__ import annotations

from pathlib import Path
import shlex
import shutil
import subprocess

from cfd.config import REFERENCE_CASE, cfd_hash
from cfd.postprocess import summarize
from project_paths import cfd_dir


def _run(case_dir: Path, command: list[str], log_name: str) -> None:
    wrapper = shutil.which("openfoam")
    if not wrapper:
        raise RuntimeError("OpenFOAM-Wrapper fehlt im PATH")
    shell_command = shlex.join(command)
    print(f"$ openfoam -c {shell_command}", flush=True)
    log = case_dir / log_name
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(
            [wrapper, "-c", shell_command], cwd=case_dir,
            text=True, stdout=stream, stderr=subprocess.STDOUT,
        )
    output = log.read_text(encoding="utf-8", errors="replace")
    tail = "\n".join(output.splitlines()[-12:])
    if tail:
        print(tail, flush=True)
    if result.returncode:
        raise RuntimeError(
            f"OpenFOAM-Befehl fehlgeschlagen ({result.returncode}): "
            f"{shell_command}; siehe {log}"
        )


def run_reference_case() -> dict:
    case = REFERENCE_CASE
    target = cfd_dir(cfd_hash(case)) / "cases" / case.name
    if not (target / "case_manifest.json").exists():
        raise RuntimeError("CFD-Fall fehlt; zuerst cfd.generate_case ausführen")
    for surface in ("belluna.stl", "adapter.stl", "roofEdge.stl"):
        _run(target, ["surfaceCheck", f"constant/triSurface/{surface}"],
             f"log.surfaceCheck.{surface}")
    _run(target, ["blockMesh"], "log.blockMesh")
    _run(target, ["snappyHexMesh", "-overwrite"], "log.snappyHexMesh")
    _run(target, ["checkMesh", "-allTopology", "-allGeometry"],
         "log.checkMesh")
    _run(target, ["potentialFoam", "-writePhi"], "log.potentialFoam")
    _run(target, ["simpleFoam"], "log.simpleFoam")
    result = summarize(target, case)
    print(f"CFD-ERGEBNIS: {target / 'result.json'}", flush=True)
    return result


if __name__ == "__main__":
    run_reference_case()
