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
    for k in range(4):
        assert f"seg{k}_{h}.step" in names
        assert f"seg{k}_{h}.stl" in names
        assert f"seg{k}_{h}.3mf" in names
    assert f"montagenotiz_{h}.md" in names

def test_step_reimport_volumen():
    _export()                          # Reihenfolge-unabhaengig (Ledger-Triage)
    h = PRM.params_hash()
    s = Part.Shape()
    s.read(f"out/test_export/seg0_{h}.step")
    assert s.Volume > 1e5


def test_stl_liegt_druckorientiert_auf_z_null():
    _export()
    h = PRM.params_hash()
    for k in range(4):
        mesh = Mesh.Mesh(f"out/test_export/seg{k}_{h}.stl")
        bb = mesh.BoundBox
        assert abs(bb.ZMin) < 1e-6
        assert 46.9 < bb.ZLength < 47.1
        assert max(bb.XLength, bb.YLength) <= PRM.P.SEG_MAX_BBOX

def test_montagenotiz_inhalt():
    _export()                          # Reihenfolge-unabhaengig (Ledger-Triage)
    h = PRM.params_hash()
    text = Path(f"out/test_export/montagenotiz_{h}.md").read_text(encoding="utf-8")
    for muss in ("140", "165", "Carloflex", "Deckfläche nach unten", "Tempern",
                 "4 Perimeter", "100 % Infill", "Dichtheit", "2K-Epoxid",
                 "PFLICHT gegen Verzug", "beheizter Bauraum", "Brim",
                 "PFLICHT", "ISO-20653", "M5x", "Standard-ASA",
                 "ST 4.2×25", "16 Belluna-Schrauben", "HDT", "Kammer"):
        assert muss in text, f"'{muss}' fehlt in Montagenotiz"
