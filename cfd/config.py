"""Von den Konstruktionsparametern getrennte CFD-Konfiguration.

Die CFD-Geometrie ist eine Rekonstruktion aus den maßstäblichen Ansichten auf
Seite 10 der Belluna-Einbauanleitung. Ihr Hash ändert den freigegebenen
Konstruktionsstand nicht; CFD-Ergebnisse erhalten einen eigenen, vollständigen
Provenienz-Hash.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

import params as PRM


MODEL_REV = 1


@dataclass(frozen=True)
class AeroGeometry:
    hood_length_mm: float = 593.0
    hood_width_mm: float = 420.0
    mounting_plate_mm: float = 450.0
    closed_height_mm: float = 127.0
    open_height_mm: float = 182.0
    lid_thickness_mm: float = 4.0
    roof_edge_depth_mm: float = 120.0
    roof_edge_span_mm: float = 2600.0


@dataclass(frozen=True)
class CaseConfig:
    name: str = "closed_front_coarse"
    state: str = "closed"
    speed_ms: float = 200.0 / 3.6
    yaw_deg: float = 0.0
    air_density_kg_m3: float = 1.2
    kinematic_viscosity_m2_s: float = 1.5e-5
    turbulence_intensity: float = 0.05
    turbulence_length_m: float = 0.10
    iterations: int = 500
    model_factor: float = 1.5
    domain_min_m: tuple[float, float, float] = (-2.0, -1.5, 0.0)
    domain_max_m: tuple[float, float, float] = (3.0, 1.5, 1.5)
    base_cells: tuple[int, int, int] = (50, 30, 15)
    fan_surface_level: tuple[int, int] = (3, 4)
    secondary_surface_level: tuple[int, int] = (2, 3)


AERO = AeroGeometry()
REFERENCE_CASE = CaseConfig()


def manual_path() -> Path:
    return (Path(__file__).resolve().parent.parent / "references" / "belluna" /
            "manuals" / "belluna-super-fan-installation.pdf")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cfd_hash(case: CaseConfig = REFERENCE_CASE,
             p: PRM.Params = PRM.P) -> str:
    """Hash über Aerogeometrie, Fall und alle verwendeten Dachparameter."""
    payload = {
        "model_rev": MODEL_REV,
        "aero": asdict(AERO),
        "case": asdict(case),
        "installation": {
            "adapter_raise_mm": p.H_RAISE,
            "adapter_outer_mm": PRM.outer_dims(p),
            "cutout_mm": p.CUTOUT_W,
            "edge_distance_mm": p.EDGE_DIST,
            "edge_height_mm": p.EDGE_H,
        },
        "manual_sha256": _sha256(manual_path()),
        "model_source_sha256": _sha256(
            Path(__file__).resolve().parent.parent /
            "reference_models" / "belluna_aero.py"),
        "case_generator_sha256": _sha256(
            Path(__file__).resolve().parent / "generate_case.py"),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()[:8]
