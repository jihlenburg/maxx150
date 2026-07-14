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
    p = PRM.P
    assert abs(bb.XLength - 500.0) < 0.01 and abs(bb.YLength - 500.0) < 0.01
    zmin = -(p.GLUE_GAP + (p.BOT_KRAGEN_DEPTH if p.BOT_KRAGEN else 0.0))
    assert abs(bb.ZMin - zmin) < 1e-6     # Noppen bis -3 bzw. Unterkragen-Kante
    assert abs(bb.ZMax - top_z()) < 1e-6                 # Deckfläche bei 25

def test_oeffnung_bleibt_400():
    s = _frame()
    p = PRM.P
    # Prüfkörper in der Öffnung darf den Rahmen nicht schneiden. Die Öffnung
    # hat R5-Ecken (Spec), daher hat auch der Prüfkörper gerundete Ecken
    # (R5.5 > R5 bei 0.1 mm Wandabstand -> liegt vollständig im Freiraum).
    # Seit GEOM_REV 3 gilt der volle 400er-Freiraum nur OBERHALB der
    # Unterkragen-Übergangsfase (der Belluna-Kragen endet bei top_z-19,
    # weit darüber); darunter garantiert der zweite Prüfkörper das
    # Kragen-Innenmaß als durchgehenden Freiraum bis unter die Kragenkante.
    from FreeCAD import Vector
    from model import features as F
    z0 = (p.BOT_KRAGEN_TRANS + 0.7) if p.BOT_KRAGEN else -5.0
    probe = F.rounded_box(399.8, 399.8, 40, 5.5, Vector(-199.9, -199.9, z0))
    assert s.common(probe).Volume < 1e-6
    if p.BOT_KRAGEN:
        ki = p.CUTOUT_W - 2 * p.BOT_KRAGEN_CLEAR - 2 * p.BOT_KRAGEN_T - 0.2
        tief = F.rounded_box(ki, ki, 60, 3.5, Vector(-ki / 2, -ki / 2, -25))
        assert s.common(tief).Volume < 1e-6

def test_volumen_plausibel():
    # Band seit GEOM_REV 4 + Messkampagne: +Unterkragen (~174 cm³),
    # +Freistellungs-Entfall (~90 cm³), +CELL_L 43 (etwas mehr Stege)
    v = _frame().Volume
    assert 1.75e6 < v < 2.2e6, f"Volumen {v/1e6:.2f} l unplausibel"

def test_deckflaeche_vorhanden():
    """Ebene Belluna-Auflage bis zum Beginn der Entwässerungsfasen."""
    s = _frame()
    zt = top_z()
    top_area = sum(f.Area for f in s.Faces
                   if abs(f.CenterOfMass.z - zt) < 1e-4)
    p = PRM.P
    flat_l = (PRM.drainage_start(p, p.W_TOP_REAR)
              + PRM.drainage_start(p, p.W_TOP_FRONT))
    flat_w = (PRM.drainage_start(p, p.W_TOP_RIGHT)
              + PRM.drainage_start(p, p.W_TOP_LEFT))
    erwartet = flat_l * flat_w - p.CUTOUT_W ** 2
    assert erwartet * 0.98 < top_area < erwartet * 1.02, \
        f"plane Auflage {top_area:.0f} weicht von {erwartet:.0f} mm² ab"

def test_entwaesserungsfase_faellt_nach_aussen_und_bleibt_geschlossen():
    """47°-Fase statt Wasserablage; Stichproben zugleich als Boolean-Wächter."""
    import Part
    from FreeCAD import Vector
    s = _frame()
    p = PRM.P
    for x in (230.0, 238.0, 245.0, 249.0):
        radius = 0.2
        probe = Part.makeCylinder(radius, 80, Vector(x, 100, -30))
        common = s.common(probe)
        assert common.Volume > 0
        # ZMax liegt wegen des Probenradius am inneren Rand x-radius.
        erwartet = PRM.top_surface_z(p, x - radius, p.W_TOP_REAR)
        assert abs(common.BoundBox.ZMax - erwartet) < 0.03
    assert len(s.Shells) == 1 and s.Shells[0].isClosed()

def test_obere_belluna_schraubpfade_sind_vollmaterial():
    """ST4.2x25 darf an keiner der acht Positionen in eine Kammer laufen."""
    import math
    import Part
    from FreeCAD import Vector
    from model import features as F
    from model import frame as MF
    s = _frame()
    p = PRM.P
    r = 0.7
    length = 24.5
    voll = math.pi * r * r * length
    for k, offsets in enumerate(MF._plate_screw_offsets_by_chamber_side(p)):
        for offset in offsets:
            probe = Part.makeCylinder(r, length,
                                      Vector(p.CUTOUT_W / 2 + 0.25, offset, 15),
                                      Vector(1, 0, 0))
            material = s.common(F.rotz(probe, k)).Volume
            assert material > voll * 0.98, \
                f"Schraubpfad Seite {k}, Offset {offset} nicht massiv: {material:.1f}/{voll:.1f}"

def test_kammern_wirken():
    """Rippenkammern (Task 14) müssen substanziellen Materialanteil entfernen,
    aber die acht 25-mm-Schraubpfade als Vollmaterial stehen lassen.
    GEOM_REV 5 entfernt deshalb weniger Volumen als der alte, überall
    gekammerte Stand; 253 cm³ bleiben weiterhin substanziell."""
    import params as PRM
    from model.frame import build_frame
    v_solid = build_frame(PRM.Params(CHAMBERS=False, CORNER_CHAMBERS=False)).Volume
    v_cham = build_frame().Volume
    assert 2.2e5 < (v_solid - v_cham) < 4.5e5, f"Kammervolumen {v_solid - v_cham:.0f}"
