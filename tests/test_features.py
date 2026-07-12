import math

from model import features as F


def test_rounded_box_volumen():
    s = F.rounded_box(100, 60, 20, 10)
    v_erw = 100 * 60 * 20 - (4 - math.pi) * 10**2 * 20   # Eckenabzug
    assert s.isValid()
    assert abs(s.Volume - v_erw) < 1.0

def test_ring_volumen_und_zentrierung():
    s = F.ring(500, 500, 12, 400, 400, 5, 25)
    a_out = 500 * 500 - (4 - math.pi) * 12**2
    a_in = 400 * 400 - (4 - math.pi) * 5**2
    assert abs(s.Volume - (a_out - a_in) * 25) < 5.0
    bb = s.BoundBox
    assert abs(bb.XMin + 250) < 1e-6 and abs(bb.XMax - 250) < 1e-6
    assert abs(bb.ZMin) < 1e-9 and abs(bb.ZMax - 25) < 1e-9

def test_hex_prism():
    s = F.hex_prism(7.4, 3.5, (10, 20), 0)
    a_hex = 2 * math.sqrt(3) * (7.4 / 2) ** 2             # Fläche über Schlüsselweite
    assert abs(s.Volume - a_hex * 3.5) < 0.5
    assert abs(s.BoundBox.Center.x - 10) < 0.01

def test_rect_path_points():
    pts = F.rect_path_points(100, 100, 60)
    assert len(pts) >= 12                                  # Umfang 800 / 60 aufgerundet je Seite
    for x, y in pts:
        assert abs(abs(x) - 100) < 1e-6 or abs(abs(y) - 100) < 1e-6
