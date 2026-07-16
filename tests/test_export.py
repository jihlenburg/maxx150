import Mesh
import Part

import params as PRM
from export.export import export_all
from project_paths import tests_dir


OUT = tests_dir("export")


def _export():
    """Cachiere export_all, da es mehrere Minuten dauert."""
    global _CACHED
    try:
        return _CACHED
    except NameError:
        _CACHED = export_all(PRM.P, str(OUT))
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
    s.read(str(OUT / f"universal_segment_x4_{h}.step"))
    assert s.Volume > 1e5


def test_step_header_ist_reproduzierbar_normalisiert():
    _export()
    h = PRM.params_hash()
    text = (OUT / f"universal_segment_x4_{h}.step").read_text(encoding="utf-8")
    assert "1970-01-01T00:00:00" in text


def test_stl_liegt_druckorientiert_auf_z_null():
    _export()
    h = PRM.params_hash()
    mesh = Mesh.Mesh(str(OUT / f"universal_segment_x4_{h}.stl"))
    bb = mesh.BoundBox
    assert abs(bb.ZMin) < 1e-6
    assert 46.9 < bb.ZLength < 47.1
    assert max(bb.XLength, bb.YLength) <= PRM.P.SEG_MAX_BBOX

def test_montagenotiz_inhalt():
    _export()                          # Reihenfolge-unabhaengig (Ledger-Triage)
    h = PRM.params_hash()
    text = (OUT / f"montagenotiz_{h}.md").read_text(encoding="utf-8")
    for muss in ("140", "165", "Carloflex 410 UV", "Deckfläche nach unten", "Tempern",
                 "4 Perimeter", "100 % Infill", "Dichtheit", "RK-1300",
                 "PFLICHT gegen Verzug", "temperierter Bauraum", "Brim",
                 "PFLICHT", "ISO-20653", "M5x", "Würth ASA GF15",
                 "Mipa PUR HS", "SikaForce-710 L35", "Sikaflex-522", "RAL 9003",
                 "Primer-507", "Aktivator-205", "PASS_ASSUMPTION_BASED",
                 "ST 4.2×25", "8 Belluna-Schrauben", "Acht seitliche",
                 "1× M5x", "HDT", "Kammer",
                 "Universal-Segment", "4x identisch", "nicht spiegeln",
                 "16", "Abstandspads", "3.6 mm wirksame Raupenhöhe",
                 "äußere Schutzkehle", "7×7 mm", "Sika Tooling Agent N",
                 "nicht", "Tragpfad"):
        assert muss in text, f"'{muss}' fehlt in Montagenotiz"
