import params as PRM
from model.segments import build_segments
from model import dfm


def test_stuetzenfrei_in_druckorientierung():
    for i, s in enumerate(build_segments()):
        bad, allowed = dfm.overhang_area(s, PRM.P)
        assert bad <= allowed * 1.2 + 200, \
            f"Segment {i}: {bad:.0f} mm² Überhang (erlaubt ~{allowed:.0f})"
