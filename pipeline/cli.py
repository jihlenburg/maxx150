"""Einziger öffentlicher Einstiegspunkt für Konstruktion und Nachweise.

Aufruf: ``python3 -m pipeline <stufe>``. Die fachlichen Stufen bleiben in
FreeCAD, Blender und normalem Python getrennt; diese CLI vereinheitlicht nur
Aufruf, Pfade, Fehlerbehandlung und Reihenfolge.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import params as PRM
from pipeline.checks import validate_manual
from project_paths import BUILD_ROOT, ROOT, heatmap_dir, manual_dir, render_dir


CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["MAXX150_BUILD_ROOT"] = str(BUILD_ROOT)
    return env


def _run(cmd: list[str], *, label: str,
         extra_env: dict[str, str] | None = None) -> None:
    print(f"\n== {label} ==", flush=True)
    print("$", " ".join(cmd), flush=True)
    env = _env()
    if extra_env:
        env.update(extra_env)
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)


def _freecad(script: str, label: str,
             extra_env: dict[str, str] | None = None) -> None:
    # freecadcmd 1.1.1 akzeptiert den Repo-relativen Skriptpfad zuverlässig;
    # ein absoluter Skriptpfad wird auf macOS dagegen teils still ignoriert.
    _run([str(ROOT / "bin" / "fc"), script], label=label,
         extra_env=extra_env)


def _blender(script: str, *args: Path | str, label: str) -> None:
    blender = os.environ.get("BLENDER_BIN") or shutil.which("blender")
    if not blender:
        raise RuntimeError("Blender fehlt; BLENDER_BIN setzen oder blender im PATH installieren")
    _run([blender, "-b", "-P", str(ROOT / script), "--", *map(str, args)], label=label)


def stage_doctor() -> None:
    blender = os.environ.get("BLENDER_BIN") or shutil.which("blender")
    required = {
        "FreeCAD": ROOT / "bin" / "fc",
        "Blender": Path(blender) if blender else None,
        "Chrome": CHROME,
        "pdfinfo": Path(shutil.which("pdfinfo")) if shutil.which("pdfinfo") else None,
        "OpenFOAM": (Path(shutil.which("openfoam"))
                     if shutil.which("openfoam") else None),
    }
    missing = []
    print(f"Projekt: {ROOT}")
    print(f"Build:   {BUILD_ROOT}")
    print(f"Stand:   {PRM.params_hash(PRM.P)} (GEOM_REV {PRM.P.GEOM_REV})")
    for name, path in required.items():
        ok = path is not None and path.exists()
        print(f"{name:8} {'OK' if ok else 'FEHLT'}  {path}")
        if not ok:
            missing.append(name)
    if missing:
        raise RuntimeError("Fehlende Werkzeuge: " + ", ".join(missing))


def stage_test() -> None:
    _freecad("tests/run_tests.py", "Tests und Toolchain-Smokes")


def stage_engineering() -> None:
    _freecad("pipeline/engineering.py", "Konstruktion, DFM, FEM, Analytik und Export")
    stage_connections()


def stage_connections() -> None:
    _run([sys.executable, "-m", "analysis.load_paths"],
         label="Klebe-, Schraub- und Dachlastpfade")


def stage_render() -> None:
    h = PRM.params_hash(PRM.P)
    target = render_dir(h)
    _freecad("render/make_views_stl.py", "Rendergeometrien")
    views = os.environ.get("MAXX150_RENDER_VIEWS", "")
    args = [target, target]
    if views:
        args.append(views)
    _blender("render/blender_views.py", *args, label="Konstruktionsrenderings")


def stage_heatmap() -> None:
    h = PRM.params_hash(PRM.P)
    target = heatmap_dir(h)
    _freecad("pipeline/heatmap_stage.py", "FEM-Heatmaps")
    _blender("render/blender_heatmap.py", target, target, label="Heatmap-Renderings")


def stage_fit() -> None:
    _freecad("pipeline/fit_stage.py", "Digitaler Belluna-Passungscheck")


def stage_cfd() -> None:
    from cfd.config import CASE_ORDER

    for case_name in CASE_ORDER:
        case_env = {"MAXX150_CFD_CASE": case_name}
        _freecad(
            "cfd/build_geometry.py",
            f"Belluna-CFD-Hüllgeometrien · {case_name}",
            extra_env=case_env,
        )
        _run(
            [sys.executable, "-m", "cfd.generate_case"],
            label=f"OpenFOAM-Fall erzeugen · {case_name}",
            extra_env=case_env,
        )
        _run(
            [sys.executable, "-m", "cfd.run_case"],
            label=f"OpenFOAM rechnen · {case_name}",
            extra_env=case_env,
        )
    _run([sys.executable, "-m", "cfd.compare"],
         label="CFD-Fallmatrix und Netzsensitivität")
    _freecad("fem/cfd_load_check.py",
             "Nicht freigabewirksamer CFD→CalculiX-Strukturcheck")
    stage_connections()


def stage_manual() -> None:
    h = PRM.params_hash(PRM.P)
    target = manual_dir(h)
    stl_dir = target / "stl"
    img_dir = target / "img"
    _freecad("montage/build_stls.py", "Montagegeometrien und Manifest")
    _blender("montage/render_steps.py", stl_dir, img_dir, label="Montagerenderings")
    _run([sys.executable, str(ROOT / "montage" / "build_pdf.py"),
          "--manifest", str(target / "manifest.json")], label="Montage-PDF")
    validate_manual(target)


def stage_references() -> None:
    _freecad("reference_models/export_belluna.py", "Belluna-Referenzmodelle")


def stage_release() -> None:
    _run([sys.executable, "-m", "pipeline.release"], label="Release Candidate paketieren")


STAGES = {
    "doctor": stage_doctor,
    "test": stage_test,
    "engineering": stage_engineering,
    "connections": stage_connections,
    "render": stage_render,
    "fit": stage_fit,
    "cfd": stage_cfd,
    "heatmap": stage_heatmap,
    "manual": stage_manual,
    "references": stage_references,
    "release": stage_release,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="maxx150-Projektpipeline")
    parser.add_argument("stage", choices=[*STAGES, "all"],
                        help="auszuführende Pipeline-Stufe")
    args = parser.parse_args(argv)

    PRM.validate(PRM.P)
    if args.stage == "all":
        for name in ("doctor", "test", "engineering", "fit", "cfd", "render",
                     "heatmap", "manual", "references", "release"):
            STAGES[name]()
    else:
        STAGES[args.stage]()
    return 0
