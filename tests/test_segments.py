import params as PRM
from model.frame import build_frame
from model.segments import build_segments


def _segs():
    global _CACHED
    try:
        return _CACHED
    except NameError:
        _CACHED = build_segments()
        return _CACHED

def test_vier_valide_segmente():
    segs = _segs()
    assert len(segs) == 4
    for s in segs:
        assert s.isValid() and s.Volume > 1e5

def test_bbox_druckservice():
    for s in _segs():
        bb = s.BoundBox
        assert max(bb.XLength, bb.YLength) <= PRM.P.SEG_MAX_BBOX, \
            f"Segment {bb.XLength:.0f}x{bb.YLength:.0f} zu groß"

def test_identische_segmente_bei_symmetrie():
    # Voraussetzung: SYMMETRISCHE W_TOP-Defaults (PRM.P). Bei asymmetrischen
    # W_TOP-Breiten sind unterschiedliche Segmentvolumina korrekt und
    # ERWARTET (siehe tests/test_asymmetrie.py, das diesen Test bewusst
    # NICHT wiederholt -- Finalreview I3).
    vols = sorted(s.Volume for s in _segs())
    assert (vols[-1] - vols[0]) / vols[-1] < 0.002   # W_TOP alle gleich -> identisch

def test_union_ergibt_rahmen_minus_fugenluft():
    segs = _segs()
    u = segs[0]
    for s in segs[1:]:
        u = u.fuse(s)
    u = u.removeSplitter()
    frame_v = build_frame().Volume
    # Bolzenbohrungen+Senkungen+Taschen und Toleranzspalte fehlen in der Union:
    diff = frame_v - u.Volume
    assert 0 < diff < 25000, f"Differenz {diff:.0f} mm³ unplausibel"

def test_keine_ueberschneidung_der_segmente():
    segs = _segs()
    for i in range(4):
        for j in range(i + 1, 4):
            ov = segs[i].common(segs[j]).Volume
            assert ov < 1.0, f"Segmente {i}/{j} überschneiden sich: {ov:.1f} mm³"
