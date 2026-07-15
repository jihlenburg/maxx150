from pathlib import Path

import Mesh
import Part

import params as PRM
from export.export import export_all


def _export():
    """Cachiere export_all, da es mehrere Minuten dauert."""
    global _CACHED
    try:
        return _CACHED
    except NameError:
        _CACHED = export_all(PRM.P, "out/test_export")
        return _CACHED


def test_export_erzeugt_alle_dateien():
    files = _export()
    names = {f.name for f in files}
    h = PRM.params_hash()
    assert f"frame_{h}.step" in names
    for ext in ("step", "stl", "3mf"):
        assert f"universal_segment_x4_{h}.{ext}" in names
    assert not any(name.startswith("seg") for name in names)
    assert f"montagenotiz_{h}.md" in names

def test_step_reimport_volumen():
    _export()                          # Reihenfolge-unabhaengig (Ledger-Triage)
    h = PRM.params_hash()
    s = Part.Shape()
    s.read(f"out/test_export/universal_segment_x4_{h}.step")
    assert s.Volume > 1e5


def test_stl_liegt_druckorientiert_auf_z_null():
    _export()
    h = PRM.params_hash()
    mesh = Mesh.Mesh(f"out/test_export/universal_segment_x4_{h}.stl")
    bb = mesh.BoundBox
    assert abs(bb.ZMin) < 1e-6
    assert 46.9 < bb.ZLength < 47.1
    assert max(bb.XLength, bb.YLength) <= PRM.P.SEG_MAX_BBOX

def test_montagenotiz_inhalt():
    _export()                          # Reihenfolge-unabhaengig (Ledger-Triage)
    h = PRM.params_hash()
    text = Path(f"out/test_export/montagenotiz_{h}.md").read_text(encoding="utf-8")
    for muss in ("140", "165", "Carloflex 410 UV", "Deckfläche nach unten", "Tempern",
                 "4 Perimeter", "100 % Infill", "Dichtheit", "RK-1300",
                 "PFLICHT gegen Verzug", "temperierter Bauraum", "Brim",
                 "PFLICHT", "ISO-20653", "M5x", "Würth ASA GF15",
                 "Mipa PUR HS", "KLEIBERIT 501.0", "RAL 9003",
                 "ST 4.2×25", "16 Belluna-Schrauben", "HDT", "Kammer",
                 "Universal-Segment", "4x identisch", "nicht spiegeln"):
        assert muss in text, f"'{muss}' fehlt in Montagenotiz"
