"""Geometrische Invarianten der ausdrücklich groben CFD-Rekonstruktion."""
import params as PRM
from cfd.config import AERO
from reference_models.belluna_aero import metadata, shapes


def test_cfd_huellmodelle_sind_valide_und_masshaltig():
    model = shapes()
    assert set(model) == {"belluna_closed", "belluna_open", "adapter", "roof_edge"}
    assert all(shape.isValid() for shape in model.values())

    closed = model["belluna_closed"].BoundBox
    opened = model["belluna_open"].BoundBox
    assert 590.0 < closed.XLength < 600.0
    assert abs(closed.YLength - AERO.mounting_plate_mm) < 0.1
    assert abs(closed.ZMax - (PRM.P.H_RAISE + AERO.closed_height_mm)) < 0.1
    assert abs(opened.ZMax - (PRM.P.H_RAISE + AERO.open_height_mm)) < 0.1


def test_cfd_provenienz_behauptet_keine_herstellergeometrie():
    data = metadata()
    assert data["classification"] == "AERODYNAMIC_ENVELOPE_RECONSTRUCTION"
    assert data["manufacturer_cad"] is False
    assert data["documented_mm"]["hood_length"] == 593.0
