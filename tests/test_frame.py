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
    """Schwelle aus Parametern statt hart 60000 (Ledger 10, Task-4-Review:
    60000 lag nur 0.4 % unter dem Istwert -- fragil bei Parameteränderung).
    Formel: Außenfläche (L*W, unrund) minus Öffnungsfläche minus
    Freistellungsring (Gusset-Freistellung, in dfm._allowed_bridge_area
    identisch als rec_ring berechnet), konservativ mit 0.9 multipliziert
    (deckt Eckenrundungen/Rille/Fase/Kammer-Randeinflüsse ab)."""
    s = _frame()
    zt = top_z()
    top_area = sum(f.Area for f in s.Faces
                   if abs(f.CenterOfMass.z - zt) < 1e-4)
    p = PRM.P
    L, W = PRM.outer_dims(p)
    oeffnungsflaeche = p.CUTOUT_W ** 2
    freistellungsring = (p.CUTOUT_W + 2 * p.REC_GUSSET_W) ** 2 - p.CUTOUT_W ** 2
    schwelle = (L * W - oeffnungsflaeche - freistellungsring) * 0.9
    assert top_area > schwelle, \
        f"zu wenig plane Klebefläche oben ({top_area:.0f} <= {schwelle:.0f})"

def test_kammern_wirken():
    """Rippenkammern (Task 14) müssen substanziellen Materialanteil entfernen,
    aber nicht die Festigkeitsstruktur sprengen (Bandbreite laut Brief).

    Task 20 (Eckkammern Default EIN): die Solid-Referenz braucht jetzt
    explizit CORNER_CHAMBERS=False (CHAMBERS=False allein wirft seit dem
    Flip ValueError -- Eckkammern setzen CHAMBERS voraus). Das Delta enthält
    zusätzlich die Eckkammern. Rechnung (bin/fc-Probe, Task-20-Report):
      v_solid   = 2127732.386711353 mm³ (ohne jede Kammer, unverändert)
      v_default = 1694758.489540970 mm³ (EIN-Anker aus Task 17)
      Delta     =  432973.897170383 mm³
                = altes Seitenkammer-Delta 391726.316 + Eckkammern 41247.581
    Band (3.0e5, 5.5e5) statt (2.5e5, 5.0e5): identische Bandbreite 2.5e5,
    nur um das Eckkammer-Delta nach oben verschoben -- KEINE Aufweichung."""
    import params as PRM
    from model.frame import build_frame
    v_solid = build_frame(PRM.Params(CHAMBERS=False, CORNER_CHAMBERS=False)).Volume
    v_cham = build_frame().Volume
    assert 3.0e5 < (v_solid - v_cham) < 5.5e5, f"Kammervolumen {v_solid - v_cham:.0f}"
