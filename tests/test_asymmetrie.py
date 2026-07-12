"""Asymmetrie-Smoke-Test (Finalreview I3, Ledger 21/22): W_TOP je Seite
unterschiedlich. Deckt die seitenspezifischen Kopplungen ab, die bei den
symmetrischen Defaults (alle W_TOP=50) unentdeckt blieben (z. B. eine
Seitenvertauschung in der k<->Seite-Kanonik in model/frame.py::_chamber_cuts
waere bei Symmetrie unsichtbar). min(46,48,55,60)=46 >= Kammergrenze 44.4
(INNER_WALL 8 + 2*CHAMBER_W 15 + CHAMBER_RIB 4 + 2.4), validate() akzeptiert
also diesen Parametersatz."""
import Part
from FreeCAD import Vector

import params as PRM
from model import dfm
from model import frame
from model.frame import build_frame
from model.segments import build_segments

P_ASYM = PRM.Params(W_TOP_FRONT=46.0, W_TOP_REAR=60.0,
                    W_TOP_LEFT=48.0, W_TOP_RIGHT=55.0)

# Achsen-Fehlbezug-Nachbesserung (Review-Critical nach Ledger 21/22): nur
# EINE Seite (REAR) stark vergrößert, Rest Default (50) -- deckt exakt den
# im Befund genannten Fall auf (frühere "seitenspezifische" Fassung nahm
# fälschlich die EIGENE W_TOP_REAR als u-Bandgrenze statt der SENKRECHTEN
# Nachbarn W_TOP_LEFT/W_TOP_RIGHT).
P_CORNER = PRM.Params(W_TOP_REAR=90.0)


def _corner_frame():
    global _CACHED_CORNER_FRAME
    try:
        return _CACHED_CORNER_FRAME
    except NameError:
        _CACHED_CORNER_FRAME = build_frame(P_CORNER)
        return _CACHED_CORNER_FRAME


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


def test_asym_rear_band_durch_senkrechte_nachbarn_begrenzt():
    """Review-Fix (Achsen-Fehlbezug): REAR (k=0) muss die u-Bandlänge aus den
    SENKRECHTEN Nachbarn W_TOP_RIGHT (+u) / W_TOP_LEFT (-u) beziehen, NICHT
    aus der eigenen (hier stark vergrößerten) W_TOP_REAR=90 -- sonst
    Phantom-Slots/SOLID_CORNER-Erosion (Review-Befund). Bei P_CORNER sind
    LEFT/RIGHT unverändert 50 -> die Grenze bleibt (CUTOUT_W/2+50)-
    SOLID_CORNER = 205, unabhängig von REARs eigenem Wert."""
    plus_w, minus_w = frame._side_neighbor_bounds(P_CORNER)[0]  # k=0 REAR
    assert plus_w == P_CORNER.W_TOP_RIGHT == 50.0
    assert minus_w == P_CORNER.W_TOP_LEFT == 50.0
    limit = (P_CORNER.CUTOUT_W / 2 + 50.0) - P_CORNER.SOLID_CORNER
    assert limit == 205.0
    for half in (frame._chamber_cell_centers(P_CORNER, plus_w),
                 frame._chamber_cell_centers(P_CORNER, minus_w)):
        assert half, "REAR-Halbseite unerwartet leer"
        for c in half:
            reach = c + P_CORNER.CELL_L / 2
            assert reach <= limit, \
                f"REAR-Zelle reicht bis {reach:.1f} > {limit} (Nachbargrenze verletzt)"


def test_asym_chamber_slot_count_konsistent_zu_werkzeugzahl():
    """chamber_slot_count muss zur tatsächlich erzeugten Werkzeuganzahl aus
    _chamber_cuts passen: je Slot 2 Kammer-Cuts (Ring 1 + Ring 2) + 2
    Vent-Bohrungen = 4 Werkzeuge je Slot."""
    tools = frame._chamber_cuts(P_CORNER)
    assert len(tools) % 4 == 0
    assert frame.chamber_slot_count(P_CORNER) == len(tools) // 4


def test_asym_ecke_bleibt_massiv_bei_w_top_rear_90():
    """Geometrische Gegenprobe zur Unit-Probe oben (Ecke REAR/RIGHT bleibt
    massiv). Box bewusst NICHT bei x/y 210..240 (erster Entwurf des
    Befund-Prüfquaders): dort erstreckt sich unter der korrekt reparierten
    Nachbar-Kanonik (siehe frame._side_neighbor_bounds-Docstring)
    RECHTMÄSSIG die RECIPROKE RIGHT-Seite hinein -- RIGHTs -u-Grenze ist
    laut derselben Review-Vorgabe (Punkt 1) W_TOP_REAR, RIGHT wird durch
    REAR=90 also PHYSISCH LÄNGER und bekommt dort korrekt eine zusätzliche
    Zelle (keine Erosion, sondern beabsichtigte Konsequenz exakt derselben
    Formel). Skript-Probe (siehe Report): an x/y 210..240 weicht das
    common-Volumen um 6626 mm³ vom Quadervolumen ab, OBWOHL die Formel
    exakt der Review-Vorgabe entspricht -- der Befund-Prüfquader prüft dort
    also RIGHTs legitime Ausdehnung, nicht REARs Fehler.
    Stattdessen: Box direkt über REARs eigenem (jetzt korrektem) Bandende
    bei y=193 (170.5+CELL_L/2, siehe test oben) bis y=199, UNTERHALB von
    RIGHTs Bandbeginn bei y=CUTOUT_W/2+INNER_WALL=208 -- isoliert damit
    REARs eigenen (möglichen) Fehler von RIGHTs legitimer reziproker Zelle.
    Skript-Probe: unter der ALTEN (eigene-W_TOP-)Formel wäre dieselbe Box um
    1463.5 mm³ hohl (Regressionsnachweis); unter der neuen Formel exakt
    massiv (diff 0.0000)."""
    body = _corner_frame()
    box = Part.makeBox(30, 6, 12, Vector(210, 193, 6))
    common = body.common(box)
    diff = box.Volume - common.Volume
    assert abs(diff) <= 1.0, \
        f"Eckzone nicht massiv: box={box.Volume:.1f} common={common.Volume:.1f} diff={diff:.1f}"
