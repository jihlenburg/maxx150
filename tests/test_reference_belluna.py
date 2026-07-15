import hashlib
import json
from pathlib import Path

import params as PRM

from analysis.fit_check import run_fit_check
from reference_models import belluna as B


ROOT = Path(__file__).resolve().parent.parent


def test_belluna_rekonstruktion_hat_explizite_provenienz():
    meta = B.metadata()
    assert meta["classification"] == "MEASURED_RECONSTRUCTION"
    assert meta["manufacturer_cad"] is False
    assert meta["measured_mm"]["lower_collar_outer"] == 397.0
    assert meta["measured_mm"]["lower_collar_wall"] == 1.5
    assert "outer_corner_radius" in meta["assumed_mm"]


def test_belluna_referenzteile_sind_valide():
    parts = B.shapes()
    assert set(parts) == {"belluna_platte", "belluna_metallclips", "belluna_dichtring"}
    assert all(shape.isValid() and not shape.isNull() for shape in parts.values())


def test_digitaler_passungscheck_default():
    result = run_fit_check(PRM.P)
    assert result["PASS"], result
    assert result["nominal_collision_mm3"] <= 1e-6
    assert result["nominal_radial_clearance_mm_per_side"] == 1.5
    assert result["belluna_source_sha256"] == hashlib.sha256(
        Path(B.__file__).read_bytes()
    ).hexdigest()


def test_belluna_dateimanifest_stimmt():
    model_dir = ROOT / "references" / "belluna" / "models"
    manifest = json.loads((model_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["provenance"]["manufacturer_cad"] is False
    assert manifest["source_sha256"] == hashlib.sha256(
        (ROOT / manifest["source"]).read_bytes()
    ).hexdigest()
    for name, entry in manifest["files"].items():
        path = model_dir / name
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
