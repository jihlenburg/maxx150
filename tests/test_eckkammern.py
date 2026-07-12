"""Eckkammern (Task 17): optionale 90°-Rotationsfortsetzung der Seiten-
Kammerringe um die vier massiven Eckblöcke (Haupt-Schrumpfspannungs-
Reservoirs laut Herstellbarkeitsanalyse). Default AUS (CORNER_CHAMBERS=False)
-- der verifizierte Stand (GEOM_REV=2) ändert sich geometrisch NICHT; nur
params_hash ändert sich zwangsläufig durch die zwei neuen Parameterfelder
(siehe test_eckkammern_default_anker_unveraendert unten und Report)."""
import params as PRM
from model import dfm
from model.frame import build_frame
from model.segments import build_segments

P_ECK = PRM.Params(CORNER_CHAMBERS=True)


def _frame_eck():
    global _CACHED_FRAME_ECK
    try:
        return _CACHED_FRAME_ECK
    except NameError:
        _CACHED_FRAME_ECK = build_frame(P_ECK)
        return _CACHED_FRAME_ECK


def _frame_default():
    global _CACHED_FRAME_DEFAULT
    try:
        return _CACHED_FRAME_DEFAULT
    except NameError:
        _CACHED_FRAME_DEFAULT = build_frame(PRM.P)
        return _CACHED_FRAME_DEFAULT


def _segs_eck():
    global _CACHED_SEGS_ECK
    try:
        return _CACHED_SEGS_ECK
    except NameError:
        _CACHED_SEGS_ECK = build_segments(P_ECK)
        return _CACHED_SEGS_ECK


def test_eckkammern_frame_valide_und_wasserdicht():
    s = _frame_eck()
    assert s.isValid()
    assert len(s.Shells) == 1 and s.Shells[0].isClosed()


def test_eckkammern_volumendelta_plausibel():
    delta = _frame_default().Volume - _frame_eck().Volume
    assert 2.5e4 < delta < 7.0e4, f"Eckkammer-Volumendelta {delta:.0f} mm³ unplausibel"


def test_eckkammern_segmente_valide_ueberschneidungsfrei():
    segs = _segs_eck()
    assert len(segs) == 4
    for s in segs:
        assert s.isValid() and s.Volume > 1e5
    for i in range(4):
        for j in range(i + 1, 4):
            ov = segs[i].common(segs[j]).Volume
            assert ov < 1.0, f"Segmente {i}/{j} überschneiden sich: {ov:.3f} mm³"


def test_eckkammern_dfm_ueberhang():
    for i, s in enumerate(_segs_eck()):
        bad, allowed = dfm.overhang_area(s, P_ECK)
        assert bad <= allowed * 1.2 + 200, \
            f"Segment {i}: {bad:.0f} mm² Überhang (erlaubt ~{allowed:.0f})"


def test_eckkammern_ohne_chambers_wirft_valueerror():
    try:
        PRM.validate(PRM.Params(CORNER_CHAMBERS=True, CHAMBERS=False))
        assert False, "erwartete ValueError"
    except ValueError:
        pass


def test_eckkammern_default_anker_unveraendert():
    """Default (CORNER_CHAMBERS=False) muss geometrisch IDENTISCH zum
    verifizierten Stand (Ledger 21/22, Task 15) bleiben -- Volumen-Anker
    1736006.070242394 mm³ (Symmetrie-Anker aus todo.md), GEOM_REV bleibt 2.
    params_hash ändert sich zwangsläufig (zwei neue Felder), das ist
    dokumentiert kein Geometrie-Bruch: Volumengleichheit ist der Beleg."""
    v = _frame_default().Volume
    assert abs(v - 1736006.070242394) < 1.0, f"Default-Volumen driftete: {v}"
    h_default = PRM.params_hash(PRM.P)
    h_alt_feld = PRM.params_hash(PRM.Params(CORNER_ANGLE_MARGIN=25.0))
    assert h_default != h_alt_feld
