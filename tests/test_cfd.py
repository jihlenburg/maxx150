"""Pure-Python-Tests für Fallgenerator, Provenienz und v2606-Auswertung."""
from dataclasses import replace
from pathlib import Path
import tempfile

import params as PRM
from cfd.config import (
    AERO,
    CASE_ORDER,
    OPEN_COARSE,
    OPEN_MEDIUM,
    REFERENCE_CASE,
    cfd_hash,
    comparison_hash,
    manual_path,
    selected_case,
)
from cfd.generate_case import (
    _block_mesh_dict,
    _control_dict,
    _initial_fields,
    _snappy_dict,
)
from cfd.postprocess import parse_vector_line, summarize


def test_aerohuelle_kommt_aus_dokumentierten_massen():
    assert AERO.hood_length_mm == 593.0
    assert AERO.hood_width_mm == 420.0
    assert AERO.closed_height_mm == 127.0
    assert AERO.open_height_mm == 182.0
    assert manual_path().exists()


def test_cfd_hash_reagiert_auf_fallparameter_aber_nicht_zufaellig():
    digest = cfd_hash()
    assert len(digest) == 8
    assert digest == cfd_hash()
    assert digest != cfd_hash(replace(REFERENCE_CASE, yaw_deg=30.0))
    assert len(comparison_hash()) == 8


def test_fallmatrix_trennt_zustand_und_netzniveau():
    assert CASE_ORDER == (
        "closed_front_coarse",
        "open_front_coarse",
        "open_front_medium",
    )
    assert OPEN_COARSE.state == OPEN_MEDIUM.state == "open"
    assert OPEN_MEDIUM.near_field_level > OPEN_COARSE.near_field_level
    assert OPEN_MEDIUM.fan_surface_level[1] > OPEN_COARSE.fan_surface_level[1]
    assert selected_case("open_front_medium") is OPEN_MEDIUM


def test_openfoam_dicts_enthalten_ausdrueckliche_modellgrenzen():
    block = _block_mesh_dict(REFERENCE_CASE)
    snappy = _snappy_dict(REFERENCE_CASE)
    fields = _initial_fields(REFERENCE_CASE)
    control = _control_dict(REFERENCE_CASE)
    assert "symmetryPlane" in block
    assert "locationInMesh" in snappy
    assert "belluna.stl" in snappy
    assert "kOmegaSST" not in snappy
    assert "55.5555556" in fields["U"]
    assert "forcesBelluna" in control
    assert f"Aref {PRM.P.A_HOOD}" in control
    assert "levels ((1e15 2));" in snappy
    assert "levels ((1e15 3));" in _snappy_dict(OPEN_MEDIUM)


def test_v2606_vektorzeile():
    row = parse_vector_line(
        "500 17.2 -0.03 164.0 15.5 -0.03 163.8 1.7 0.0 0.2"
    )
    assert row == {
        "time": 500.0,
        "total": [17.2, -0.03, 164.0],
        "pressure": [15.5, -0.03, 163.8],
        "viscous": [1.7, 0.0, 0.2],
    }
    assert parse_vector_line("# header") is None


def test_summary_darf_480_nicht_kleinrechnen():
    with tempfile.TemporaryDirectory() as directory:
        case = Path(directory)
        force_dir = case / "postProcessing" / "forcesBelluna" / "0"
        force_dir.mkdir(parents=True)
        header = "# Time total pressure viscous\n"
        force_rows = [
            f"{i} 20 0 100 18 0 99 2 0 1" for i in range(5, 105, 5)
        ]
        moment_rows = [
            f"{i} 0 5 0 0 4.8 0 0 0.2 0" for i in range(5, 105, 5)
        ]
        (force_dir / "force.dat").write_text(
            header + "\n".join(force_rows) + "\n", encoding="utf-8")
        (force_dir / "moment.dat").write_text(
            header + "\n".join(moment_rows) + "\n", encoding="utf-8")
        adapter_dir = case / "postProcessing" / "forcesAdapter" / "0"
        adapter_dir.mkdir(parents=True)
        zero_rows = [f"{i} 0 0 0 0 0 0 0 0 0" for i in range(5, 105, 5)]
        (adapter_dir / "force.dat").write_text(
            header + "\n".join(zero_rows) + "\n", encoding="utf-8")
        (adapter_dir / "moment.dat").write_text(
            header + "\n".join(zero_rows) + "\n", encoding="utf-8")
        (case / "log.checkMesh").write_text(
            "    cells: 1000\nMax aspect ratio = 4 OK.\n"
            "Mesh non-orthogonality Max: 40 average: 5\n"
            "Max skewness = 2 OK.\nMesh OK.\n",
            encoding="utf-8",
        )
        result = summarize(case)
        assert result["drag_mean_N"] == 20.0
        assert abs(result["moment_mean_Nm"][1] - 5.56) < 1e-12
        assert result["force_scope"] == "BELLUNA_PLUS_ADAPTER"
        assert result["structural_drag_envelope_N"] == PRM.wind_force()
        assert result["structural_use"] == "INFORMATIONAL_ONLY"
