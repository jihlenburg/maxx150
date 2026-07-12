import params as PRM
from model.frame import build_frame
from fem import loadcases as LC
from fem.material import fem_material_dict


def _frame():
    global _CACHED
    try:
        return _CACHED
    except NameError:
        _CACHED = build_frame()
        return _CACHED


def test_materialkarte():
    m = fem_material_dict(PRM.P)
    # 2000 * INFILL 1.0 — Kammern, kein Slicer-Infill
    assert m["YoungsModulus"] == "2000.0 MPa"
    assert m["PoissonRatio"] == "0.35"


def test_face_selektoren():
    s = _frame()
    top = LC.top_faces(s, PRM.P)
    nop = LC.nopple_faces(s, PRM.P)
    assert len(top) >= 1 and len(nop) >= 20
    front = LC.top_half_faces(s, PRM.P, -1)
    rear = LC.top_half_faces(s, PRM.P, +1)
    assert front and rear and not set(front) & set(rear)


def test_lastfaelle_vollstaendig_und_bezahlt():
    s = _frame()
    assert set(LC.CASES) == {"LF1_wind", "LF2_schlechtweg", "LF3_klemmung", "LF4_schnee"}
    for c in LC.CASES.values():
        assert c.fixed_faces(s, PRM.P)
        loads = c.loads(s, PRM.P)
        assert loads and all(m > 0 for _, _, m in loads)
        assert c.allowable(PRM.P) > 0


def test_lf1_zahlen():
    s = _frame()
    loads = LC.CASES["LF1_wind"].loads(s, PRM.P)
    mags = sorted(m for _, _, m in loads)
    assert abs(sum(mags) - (PRM.wind_force() + 2 * LC.couple_force(s, PRM.P))) < 2.0


def test_lf2_zahlen():
    f_vert = PRM.P.FAN_MASS * 9.81 * PRM.P.G_VERT
    assert abs(f_vert - 255.1) < 0.5
