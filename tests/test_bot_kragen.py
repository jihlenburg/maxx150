"""Unterkragen: Geometrie-, Schraubbild-, Validate- und DFM-Wächter."""
import Part
from FreeCAD import Vector

import params as PRM
from model import features as F
from model.dfm import overhang_area
from model.frame import build_frame


def _frame():
    """Cachiere den Default-Rahmen (Produktions-Booleans, ~30 s)."""
    global _CACHED
    try:
        return _CACHED
    except NameError:
        _CACHED = build_frame(PRM.P)
        return _CACHED


def test_kragen_tiefe_und_bbox():
    p = PRM.P
    bb = _frame().BoundBox
    soll = -(p.GLUE_GAP + p.BOT_KRAGEN_DEPTH)
    assert abs(bb.ZMin - soll) < 1e-6, f"ZMin {bb.ZMin} != {soll}"


def test_kragen_passt_in_den_ausschnitt():
    """Unterhalb der Dachoberfläche darf NICHTS breiter als der Ausschnitt
    minus Radialluft sein (sonst kollidiert der Kragen beim Einsetzen)."""
    p = PRM.P
    # Box endet 0.1 UNTER der Dachoberfläche (-GLUE_GAP): die Noppen reichen
    # exakt bis -GLUE_GAP und spannen ~478 mm -- sie gehören nicht zum Kragen
    unten = Part.makeBox(1000, 1000, p.BOT_KRAGEN_DEPTH + 0.9,
                         Vector(-500, -500, -(p.GLUE_GAP + p.BOT_KRAGEN_DEPTH + 1)))
    teil = _frame().common(unten)
    grenze = p.CUTOUT_W - 2 * p.BOT_KRAGEN_CLEAR + 0.01
    assert teil.BoundBox.XLength <= grenze
    assert teil.BoundBox.YLength <= grenze


def test_kragen_ist_geschlossen_und_hat_keine_dachschraubenloecher():
    """Der Zentrierkragen bleibt an den früheren Lochpositionen geschlossen."""
    p = PRM.P
    ki = p.CUTOUT_W - 2 * p.BOT_KRAGEN_CLEAR - 2 * p.BOT_KRAGEN_T
    z = -(p.GLUE_GAP + p.BOT_KRAGEN_HOLE_Z)
    frame = _frame()
    for k in range(4):
        for off in (-140.0, 140.0):
            sonde = Part.makeCylinder(p.BOT_KRAGEN_HOLE_D / 2 - 0.5,
                                      p.BOT_KRAGEN_T + 2,
                                      Vector(off, ki / 2 - 1, z), Vector(0, 1, 0))
            material = frame.common(F.rotz(sonde, k))
            assert material.Volume > 1.0, \
                f"Kragen an Seite {k}, Offset {off} unerwartet offen"
    assert p.BOT_KRAGEN_HOLE_OFFS == ()
    assert PRM.bot_kragen_hole_count(p) == 0


def test_ohne_kragen_flach_und_anderer_hash():
    p = PRM.Params(BOT_KRAGEN=False)
    bb = build_frame(p).BoundBox
    assert abs(bb.ZMin - (-p.GLUE_GAP)) < 1e-6
    assert PRM.params_hash(p) != PRM.params_hash()


def test_validate_faengt_kragen_brecher():
    for kaputt in (PRM.Params(BOT_KRAGEN_HOLE_OFFS=(-140.0, 140.0)),
                   PRM.Params(BOT_KRAGEN_DEPTH=34.0),
                   PRM.Params(BOT_KRAGEN_HOLE_Z=17.0),
                   PRM.Params(BOT_KRAGEN_CLEAR=0.2)):
        try:
            PRM.validate(kaputt)
            assert False, "erwartete ValueError"
        except ValueError:
            pass


def test_unterkragen_ohne_dachschrauben_bleibt_unabhaengig_von_belluna():
    p = PRM.P
    assert p.BOT_KRAGEN_HOLE_OFFS == ()
    assert p.PLATE_SCREW_OFFS == (-165.0, -140.0, 140.0, 165.0)
    assert PRM.bot_kragen_hole_count(p) == 0


def test_kragen_volumendelta_plausibel():
    """Default gegen die BOT_KRAGEN=False-Variante mit sonst identischen
    Parametern: das Delta ist NUR der Unterkragen (Ring ~398x4x21 +
    Übergangsring, ohne Löcher). Bewusst kein Vergleich gegen die
    Eckkammern-Anker mehr -- die pinnen seit der Messwertübernahme alte
    CELL_L/REC_GUSSET-Werte."""
    ohne = build_frame(PRM.Params(BOT_KRAGEN=False))
    delta = _frame().Volume - ohne.Volume
    assert 1.2e5 < delta < 2.2e5, f"Kragen-Volumendelta {delta:.0f} mm³ unplausibel"


def test_dfm_gate_mit_kragen():
    """Gleiches Gate wie die Engineering-Stufe: Überhang <= erlaubt*1.2 + 200."""
    bad, allowed = overhang_area(_frame())
    assert bad <= allowed * 1.2 + 200, f"DFM: {bad:.0f} > {allowed * 1.2 + 200:.0f}"
