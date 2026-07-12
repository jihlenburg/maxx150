import params as PRM
from model.frame import build_frame, top_z


def _frame():
    global _CACHED
    try:
        return _CACHED
    except NameError:
        _CACHED = build_frame()
        return _CACHED

def test_valide_und_wasserdicht():
    s = _frame()
    assert s.isValid()
    assert len(s.Shells) == 1 and s.Shells[0].isClosed()

def test_hauptmasse():
    s = _frame()
    bb = s.BoundBox
    assert abs(bb.XLength - 500.0) < 0.01 and abs(bb.YLength - 500.0) < 0.01
    assert abs(bb.ZMin + PRM.P.GLUE_GAP) < 1e-6          # Noppen bis -3
    assert abs(bb.ZMax - top_z()) < 1e-6                 # Deckfläche bei 25

def test_oeffnung_bleibt_400():
    s = _frame()
    # Prüfkörper in der Öffnung darf den Rahmen nicht schneiden. Die Öffnung
    # hat R5-Ecken (Spec), daher hat auch der Prüfkörper gerundete Ecken
    # (R5.5 > R5 bei 0.1 mm Wandabstand -> liegt vollständig im Freiraum):
    from FreeCAD import Vector
    from model import features as F
    probe = F.rounded_box(399.8, 399.8, 40, 5.5, Vector(-199.9, -199.9, -5))
    assert s.common(probe).Volume < 1e-6

def test_volumen_plausibel():
    v = _frame().Volume
    assert 1.55e6 < v < 1.95e6, f"Volumen {v/1e6:.2f} l unplausibel"

def test_deckflaeche_vorhanden():
    s = _frame()
    zt = top_z()
    top_area = sum(f.Area for f in s.Faces
                   if abs(f.CenterOfMass.z - zt) < 1e-4)
    assert top_area > 60000, "zu wenig plane Klebefläche oben"

def test_kammern_wirken():
    """Rippenkammern (Task 14) müssen substanziellen Materialanteil entfernen,
    aber nicht die Festigkeitsstruktur sprengen (Bandbreite laut Brief)."""
    import params as PRM
    from model.frame import build_frame
    v_solid = build_frame(PRM.Params(CHAMBERS=False)).Volume
    v_cham = build_frame().Volume
    assert 2.5e5 < (v_solid - v_cham) < 5.0e5, f"Kammervolumen {v_solid - v_cham:.0f}"
