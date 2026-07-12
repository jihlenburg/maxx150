import params as PRM
from model.segments import build_segments
from model import dfm


def test_stuetzenfrei_in_druckorientierung():
    for i, s in enumerate(build_segments()):
        bad, allowed = dfm.overhang_area(s, PRM.P)
        assert bad <= allowed * 1.2 + 200, \
            f"Segment {i}: {bad:.0f} mm² Überhang (erlaubt ~{allowed:.0f})"


def test_facet_area_fallback():
    # Stub ohne .Area-Attribut: rechtwinkliges Dreieck (3-4-5), Fläche 6
    class F:
        Points = ((0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (0.0, 4.0, 0.0))
    from model.dfm import _facet_area
    assert abs(_facet_area(F(), F.Points) - 6.0) < 1e-9
