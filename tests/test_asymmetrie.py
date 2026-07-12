"""Asymmetrie-Smoke-Test (Finalreview I3, Ledger 21/22): W_TOP je Seite
unterschiedlich. Deckt die seitenspezifischen Kopplungen ab, die bei den
symmetrischen Defaults (alle W_TOP=50) unentdeckt blieben (z. B. eine
Seitenvertauschung in der k<->Seite-Kanonik in model/frame.py::_chamber_cuts
waere bei Symmetrie unsichtbar). min(46,48,55,60)=46 >= Kammergrenze 44.4
(INNER_WALL 8 + 2*CHAMBER_W 15 + CHAMBER_RIB 4 + 2.4), validate() akzeptiert
also diesen Parametersatz."""
import params as PRM
from model import dfm
from model.frame import build_frame
from model.segments import build_segments

P_ASYM = PRM.Params(W_TOP_FRONT=46.0, W_TOP_REAR=60.0,
                    W_TOP_LEFT=48.0, W_TOP_RIGHT=55.0)


def _frame():
    global _CACHED_FRAME
    try:
        return _CACHED_FRAME
    except NameError:
        _CACHED_FRAME = build_frame(P_ASYM)
        return _CACHED_FRAME


def _segs():
    global _CACHED_SEGS
    try:
        return _CACHED_SEGS
    except NameError:
        _CACHED_SEGS = build_segments(P_ASYM)
        return _CACHED_SEGS


def test_asym_frame_valide_und_wasserdicht():
    s = _frame()
    assert s.isValid()
    assert len(s.Shells) == 1 and s.Shells[0].isClosed()


def test_asym_segmente_valide_ueberschneidungsfrei_bbox():
    segs = _segs()
    assert len(segs) == 4
    for s in segs:
        assert s.isValid() and s.Volume > 1e5
        bb = s.BoundBox
        assert max(bb.XLength, bb.YLength) <= PRM.P.SEG_MAX_BBOX, \
            f"Segment {bb.XLength:.0f}x{bb.YLength:.0f} zu groß"
    for i in range(4):
        for j in range(i + 1, 4):
            ov = segs[i].common(segs[j]).Volume
            assert ov < 1.0, f"Segmente {i}/{j} überschneiden sich: {ov:.2f} mm³"


def test_asym_dfm_ueberhang():
    for i, s in enumerate(_segs()):
        bad, allowed = dfm.overhang_area(s, P_ASYM)
        assert bad <= allowed * 1.2 + 200, \
            f"Segment {i}: {bad:.0f} mm² Überhang (erlaubt ~{allowed:.0f})"
