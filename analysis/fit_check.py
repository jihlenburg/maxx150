"""Digitaler Passungscheck Belluna-Rekonstruktion ↔ Adapterrahmen.

Die Analyse prüft Nominalkollision, seitliches Montagespiel, Auflage der drei
Belluna-Unterseitenstege und die Belluna-Schraubkorridore. Ergebnis ist ein
maschinenlesbares JSON im einheitlichen Build-Baum.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(line_buffering=True)

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

import params as PRM  # noqa: E402
from model import features as F  # noqa: E402
from model.frame import build_frame, top_z  # noqa: E402
from project_paths import fit_dir  # noqa: E402
from reference_models import belluna as B  # noqa: E402


def _belluna_source_sha256() -> str:
    return hashlib.sha256(Path(B.__file__).read_bytes()).hexdigest()


def _git_revision() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def run_fit_check(p: PRM.Params = PRM.P, source_commit: str | None = None) -> dict:
    """Digitaler Passungscheck Adapterrahmen <-> Belluna-Rekonstruktion.

    Setzt die Belluna-Platte auf die Deckfläche (z = top_z) und misst vier
    Kriterien: Nominalkollision (Durchdringungsvolumen mm³, soll ~0), seitliches
    Montagespiel bei 0,5..2,0 mm Querversatz, Auflagegrad der drei Belluna-
    Unterseitenstege (common-Volumen / Probevolumen, >= 0,95) und die Ø4-
    Belluna-Schraubkorridore (freier Anteil >= 0,95). Rückgabe: maschinen-
    lesbares Ergebnis-Dict (Schema 2) inkl. Parameter-Hash, Quell-Provenienz
    und PASS = alle Checks erfüllt; ``source_commit`` wird unverändert
    übernommen."""
    PRM.validate(p)
    frame = build_frame(p)
    plate = B.PLATTE.copy()
    plate.translate(App.Vector(0, 0, top_z(p)))

    collision = frame.common(plate).Volume
    offsets = {}
    for dx in (0.5, 1.0, 1.5, 2.0):
        shifted = plate.copy()
        shifted.translate(App.Vector(dx, 0, 0))
        offsets[f"{dx:.1f}"] = round(frame.common(shifted).Volume, 6)

    support = {}
    h = top_z(p)
    for name, (ri, ro) in zip(("innen", "mitte", "aussen"), B.STEGE):
        def radius(half: float) -> float:
            """Eckradius (mm) der ringförmigen Auflage-Probe für die Steg-
            Halbbreite half: vom Belluna-Außenradius R_OUT_ANN linear nach innen
            reduziert, mindestens 3 mm, damit die Probe der gerundeten
            Stegkontur folgt."""
            return max(3.0, B.R_OUT_ANN - (B.FL_HALF - half))

        probe = F.ring(2 * ro, 2 * ro, radius(ro),
                       2 * ri, 2 * ri, radius(ri), 0.3)
        probe.translate(App.Vector(0, 0, h - 0.35))
        ratio = frame.common(probe).Volume / probe.Volume
        support[name] = round(ratio, 6)

    corridors = {}
    z_s = h - p.PLATE_SCREW_Z_FROM_TOP
    expected = math.pi * 2.0**2 * p.INNER_WALL
    for off in (0.0, *sorted(set(abs(x) for x in p.PLATE_SCREW_OFFS))):
        cylinder = Part.makeCylinder(
            2.0, 14, App.Vector(off, p.CUTOUT_W / 2 - 2, z_s), App.Vector(0, 1, 0)
        )
        corridors[f"{off:.0f}"] = round(frame.common(cylinder).Volume / expected, 6)

    nominal_clearance = (p.CUTOUT_W - 2 * B.KRAGEN_OUT) / 2
    checks = {
        "nominal_collision": collision <= 1e-6,
        "nominal_radial_clearance": nominal_clearance >= 1.0,
        "support": all(value >= 0.95 for value in support.values()),
        "screw_corridors": all(value >= 0.95 for value in corridors.values()),
    }
    return {
        "schema": 2,
        "parameter_hash": PRM.params_hash(p),
        "source_commit": source_commit,
        "belluna_model": "MEASURED_RECONSTRUCTION",
        "belluna_source_sha256": _belluna_source_sha256(),
        "nominal_collision_mm3": round(collision, 6),
        "nominal_radial_clearance_mm_per_side": round(nominal_clearance, 3),
        "offset_collision_mm3": offsets,
        "support_ratio": support,
        "screw_corridor_ratio": corridors,
        "checks": checks,
        "PASS": all(checks.values()),
    }


def main() -> None:
    """Rechnet den Passungscheck für PRM.P mit dem aktuellen Git-Commit,
    schreibt das Ergebnis nach ``fit_dir/<hash>/fit_summary.json``, gibt es auf
    stdout aus und beendet mit SystemExit(1), falls ein Check fehlschlägt."""
    result = run_fit_check(PRM.P, source_commit=_git_revision())
    target = fit_dir(result["parameter_hash"])
    target.mkdir(parents=True, exist_ok=True)
    path = target / "fit_summary.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    print(f"FIT-ENDE: {path}", flush=True)
    if not result["PASS"]:
        raise SystemExit(1)
