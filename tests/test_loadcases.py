import params as PRM
from model.frame import build_frame, top_z
from fem import loadcases as LC
from fem.material import fem_material_dict


def _frame():
    global _CACHED
    try:
        return _CACHED
    except NameError:
        _CACHED = build_frame()
        return _CACHED


def _face_by_name(shape, name):
    """Face-Name ('FaceN', 1-basiert) -> das zugehörige Part.Face-Objekt,
    wie von den loadcases-Selektoren erzeugt (f"Face{i+1}" für Index i)."""
    idx = int(name[len("Face"):]) - 1
    return shape.Faces[idx]


def test_materialkarte():
    m = fem_material_dict(PRM.P)
    # Task 21 (Würth ASA GF15, Druckwert-ANNAHME): 3000 * INFILL 1.0 — Kammern,
    # kein Slicer-Infill; NU unveraendert (keine Herstellerangabe)
    assert m["YoungsModulus"] == "3000.0 MPa"
    assert m["PoissonRatio"] == "0.35"


def test_face_selektoren():
    s = _frame()
    top = LC.top_faces(s, PRM.P)
    nop = LC.nopple_faces(s, PRM.P)

    # top_faces: exakt eine zusammenhängende Deckfläche bei top_z, keine
    # Kammerdecken/Vents/Freistellungen mehr eingesammelt.
    tz = top_z(PRM.P)
    for name in top:
        assert abs(_face_by_name(s, name).CenterOfMass.z - tz) < 1e-3
    top_area = sum(_face_by_name(s, name).Area for name in top)
    assert 55e3 < top_area < 70e3

    # nopple_faces: alle exakt bei z = -GLUE_GAP.
    assert len(nop) >= 20
    for name in nop:
        assert abs(_face_by_name(s, name).CenterOfMass.z - (-PRM.P.GLUE_GAP)) < 1e-3

    # outer_wall_faces: Front/Heck beidseitig belegt, disjunkt, auf den
    # jeweiligen Außenwand-x-Ebenen (|x| = CUTOUT_W/2 + W_TOP_* = 250).
    front = LC.outer_wall_faces(s, PRM.P, -1)
    rear = LC.outer_wall_faces(s, PRM.P, +1)
    assert front and rear and not set(front) & set(rear)
    for name in front + rear:
        assert abs(abs(_face_by_name(s, name).CenterOfMass.x) - 250.0) < 0.5


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
    # couple_force = wind_force * (H_CG + top_z) / L = 480 * 185 / 500 = 177.6 N
    cf = LC.couple_force(s, PRM.P)
    assert abs(cf - 177.6) < 0.5

    loads = LC.CASES["LF1_wind"].loads(s, PRM.P)
    mags = sorted(m for _, _, m in loads)
    # Erwartungswert unabhängig hingeschrieben (nicht aus demselben Aufruf
    # abgeleitet): 480.0 (Wind) + 2 * 177.6 (Kräftepaar) = 835.2 N.
    assert abs(sum(mags) - 835.2) < 0.1


def test_lf2_zahlen():
    f_vert = PRM.P.FAN_MASS * 9.81 * PRM.P.G_VERT
    assert abs(f_vert - 255.1) < 0.5
