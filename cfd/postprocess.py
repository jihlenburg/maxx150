"""Maschinenlesbare Auswertung der OpenFOAM-Kräfte und Netzkennwerte."""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
from statistics import fmean, pstdev

import params as PRM
from cfd.config import REFERENCE_CASE, CaseConfig


FLOAT = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def parse_vector_line(line: str) -> dict | None:
    """Liest das v2606-Format: Zeit, total, pressure, viscous."""
    if not line.strip() or line.lstrip().startswith("#"):
        return None
    numbers = [float(value) for value in FLOAT.findall(line)]
    if len(numbers) < 10:
        return None
    return {
        "time": numbers[0],
        "total": numbers[1:4],
        "pressure": numbers[4:7],
        "viscous": numbers[7:10],
    }


def read_vectors(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parsed = parse_vector_line(line)
        if parsed is not None:
            rows.append(parsed)
    if not rows:
        raise RuntimeError(f"Keine auswertbaren Vektoren in {path}")
    return rows


def read_forces(force_path: Path, moment_path: Path) -> list[dict]:
    forces = read_vectors(force_path)
    moments = read_vectors(moment_path)
    moment_by_time = {row["time"]: row for row in moments}
    rows = []
    for force in forces:
        moment = moment_by_time.get(force["time"])
        if moment is not None:
            rows.append({
                "time": force["time"],
                "force_N": force["total"],
                "moment_Nm": moment["total"],
            })
    if not rows:
        raise RuntimeError("Kraft- und Momentzeitreihen haben keine gemeinsamen Zeiten")
    return rows


def _mean_vector(rows: list[dict], key: str) -> list[float]:
    return [fmean(row[key][axis] for row in rows) for axis in range(3)]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _mesh_metrics(log_path: Path) -> dict:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    patterns = {
        "cells": r"^\s*cells:\s+(\d+)",
        "max_aspect_ratio": r"Max aspect ratio\s*=\s*([0-9.eE+-]+)",
        "max_non_orthogonality_deg": r"Max:\s*([0-9.eE+-]+)\s+average",
        "max_skewness": r"Max skewness\s*=\s*([0-9.eE+-]+)",
        "concave_cells": r"Concave cells .*number of cells:\s*(\d+)",
    }
    out = {}
    for name, pattern in patterns.items():
        matches = re.findall(pattern, text, flags=re.MULTILINE)
        if matches:
            value = matches[-1]
            out[name] = (int(value) if name in {"cells", "concave_cells"}
                         else float(value))
    if out.get("cells") and out.get("concave_cells") is not None:
        out["concave_cell_fraction"] = out["concave_cells"] / out["cells"]
    out["check_mesh_passed"] = "Mesh OK" in text
    return out


def summarize(case_dir: Path, case: CaseConfig = REFERENCE_CASE) -> dict:
    force_files = sorted(
        (case_dir / "postProcessing" / "forcesBelluna").glob("*/force.dat")
    )
    moment_files = sorted(
        (case_dir / "postProcessing" / "forcesBelluna").glob("*/moment.dat")
    )
    if not force_files or not moment_files:
        raise RuntimeError("forcesBelluna/force.dat oder moment.dat fehlt")
    rows = read_forces(force_files[-1], moment_files[-1])
    window_count = min(50, max(5, len(rows) // 5))
    window = rows[-window_count:]
    force = _mean_vector(window, "force_N")
    moment = _mean_vector(window, "moment_Nm")
    yaw = math.radians(case.yaw_deg)
    drag_dir = [math.cos(yaw), math.sin(yaw), 0.0]
    side_dir = [-math.sin(yaw), math.cos(yaw), 0.0]
    drags = [_dot(row["force_N"], drag_dir) for row in window]
    drag = fmean(drags)
    side = _dot(force, side_dir)
    lift = force[2]
    drag_cov = pstdev(drags) / max(abs(drag), 1e-12)
    result = {
        "schema": 1,
        "status": "PRELIMINARY_CFD",
        "structural_use": "INFORMATIONAL_ONLY",
        "case": case.name,
        "samples": len(rows),
        "averaging_window": window_count,
        "force_mean_N": force,
        "moment_mean_Nm": moment,
        "drag_mean_N": drag,
        "side_mean_N": side,
        "lift_mean_N": lift,
        "drag_cov": drag_cov,
        "force_magnitude_N": math.sqrt(sum(value * value for value in force)),
        "existing_wind_envelope_N": PRM.wind_force(PRM.P),
        "model_factor": case.model_factor,
        "structural_drag_envelope_N": max(
            PRM.wind_force(PRM.P), abs(drag) * case.model_factor),
        "mesh": _mesh_metrics(case_dir / "log.checkMesh"),
        "limitations": [
            "Belluna aerodynamic envelope reconstructed from manual page 10",
            ("steady RANS case without prism-layer mesh; local refinement "
             f"level {case.near_field_level}, fan surface levels "
             f"{case.fan_surface_level}"),
            "no vehicle-body upstream boundary-layer calibration",
            "not yet mesh-converged or experimentally correlated",
        ],
    }
    output = case_dir / "result.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report = case_dir / "report.md"
    report.write_text(
        "\n".join((
            "# Vorläufiger CFD-Referenzfall",
            "",
            f"Fall: `{case.name}` · Status: **PRELIMINARY_CFD**",
            "",
            f"- Mittlere Kraft [N]: `{force}`",
            f"- Mittleres Moment [Nm]: `{moment}`",
            f"- Widerstand: **{drag:.1f} N**",
            f"- Seitenkraft: **{side:.1f} N**",
            f"- Auftrieb (+z): **{lift:.1f} N**",
            f"- Variationskoeffizient Widerstand: **{drag_cov:.3f}**",
            f"- Netz: `{result['mesh']}`",
            "",
            "Das Ergebnis ist informationshalber. Es ersetzt die bestehende "
            "480-N-Hülllast nicht und ist weder netzkonvergiert noch "
            "experimentell korreliert.",
            "",
        )),
        encoding="utf-8",
    )
    return result
