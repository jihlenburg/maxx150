"""Unit-Tests fuer fem.heatmap: NUR die FreeCAD-freien Helferfunktionen
(classify, cmap, write_ply) -- kein Gmsh/CalculiX-Lauf (Laufzeit!), daher
kein Suite-Aufruf von heatmap_all()/run_capture() hier. Dateiname enthaelt
'tools' (gemeinsamer Substring-Filter mit test_tools_measurements.py, siehe
tests/run_tests.py::TEST_FILTER)."""
import io

import params as PRM
from fem.heatmap import classify, cmap, write_ply
from model.frame import top_z


def test_classify_zonen():
    p = PRM.P
    r_in1 = p.CUTOUT_W / 2 + p.INNER_WALL          # 208 bei Defaults
    r_out1 = r_in1 + p.CHAMBER_W                   # 223
    r_in2 = r_out1 + p.CHAMBER_RIB                 # 227
    r_out_last = (r_in1 + p.CHAMBER_RING_COUNT * p.CHAMBER_W
                  + (p.CHAMBER_RING_COUNT - 1) * p.CHAMBER_RIB)
    z_deck = top_z(p) - p.DECK_T                   # 20

    assert classify((200.0, 0.0, -1.0), p) == "Noppenfuß (Fixierstelle — Lagerkonzentration)"
    assert classify((200.0, 0.0, 2.0), p) == "Bodenplatte/Kleberille"
    assert classify((0.0, 200.0, z_deck + 1.0), p) == "Deckplatte/Freistellung"
    assert classify((r_out_last + p.CHAMBER_RIB + 1, 0.0, 10.0), p) == "Außenwand"
    assert classify((r_in1, 0.0, 10.0), p) == "Innenwand (Schraubgrund)"
    assert classify((0.0, (r_out1 + r_in2) / 2, 10.0), p) == "Kammersteg Ring1/Ring2"
    # Zwischen Innenwand- und Kammersteg-Toleranzband: Sammelzone.
    mid = (r_in1 + p.CHAMBER_RIB + r_out1 - p.CHAMBER_RIB) / 2
    assert classify((mid, 0.0, 10.0), p) == "Kammerwand/-boden"


def test_classify_folgt_parametern():
    """Zonengrenzen aus p abgeleitet, nicht hart codiert: mit vergroessertem
    INNER_WALL wandert die Innenwand-Zone erkennbar mit."""
    p = PRM.Params(INNER_WALL=20.0)
    r_in1 = p.CUTOUT_W / 2 + p.INNER_WALL          # 220
    assert classify((r_in1, 0.0, 10.0), p) == "Innenwand (Schraubgrund)"
    assert classify((208.0, 0.0, 10.0), p) != "Innenwand (Schraubgrund)"


def test_cmap_randwerte():
    assert cmap(0.0) == (68, 1, 83)
    assert cmap(1.0) == (253, 231, 36)
    # Clamping ausserhalb [0, 1]:
    assert cmap(-5.0) == cmap(0.0)
    assert cmap(5.0) == cmap(1.0)
    assert cmap(0.5) == (32, 144, 140)


def test_write_ply_header_und_body():
    f = io.StringIO()
    vertices = [(0.0, 0.0, 0.0), (1.0, 2.0, 3.0), (4.0, 5.0, 6.0)]
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    facets = [(0, 1, 2)]
    write_ply(f, vertices, colors, facets)
    lines = f.getvalue().splitlines()

    assert lines[0] == "ply"
    assert lines[1] == "format ascii 1.0"
    assert lines[2] == "element vertex 3"
    assert lines[3] == "property float x"
    assert lines[4] == "property float y"
    assert lines[5] == "property float z"
    assert lines[6] == "property uchar red"
    assert lines[7] == "property uchar green"
    assert lines[8] == "property uchar blue"
    assert lines[9] == "element face 1"
    assert lines[10] == "property list uchar int vertex_indices"
    assert lines[11] == "end_header"
    assert lines[12] == "0.00 0.00 0.00 255 0 0"
    assert lines[13] == "1.00 2.00 3.00 0 255 0"
    assert lines[14] == "4.00 5.00 6.00 0 0 255"
    assert lines[15] == "3 0 1 2"
    assert len(lines) == 16
