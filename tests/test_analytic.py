import params as PRM
from fem import analytic as A


def test_haubenfreigang_default_kein_ueberlapp():
    # Default: Haube ragt 130 mm über den Ausschnitt, Kante erst bei 250 mm
    assert A.hood_clearance() == float("inf")


def test_haubenfreigang_mit_ueberlapp():
    p = PRM.Params(HOOD_TIP_REACH=300.0)        # ragt über die Kante
    c = A.hood_clearance(p)
    # 28 + 30 - 55 = 3 mm Freigang
    assert abs(c - 3.0) < 1e-9


def test_fugenauslastung():
    u = A.glue_shear_utilization()
    # Segmentlänge ~275 mm, dT = 85-20 = 65 K, dAlpha 65e-6:
    # delta = 65e-6*275*65 = 1.162 mm; je Ende 0.581; gamma = 0.194; /0.5 = 0.39
    assert 0.30 < u < 0.50


def test_stossnachweis_traegt_windlast():
    r = A.joint_checks(PRM.P, PRM.wind_force())
    assert r["tau_MPa"] < r["tau_zul_MPa"]
    assert r["lochleibung_MPa"] < r["lochleibung_zul_MPa"]
    assert r["PASS"]


def test_klebfugen_schub_aus_last():
    r = A.glue_load_shear(PRM.P, PRM.wind_force())
    # Rillenfläche ~14e3 mm² -> 480 N ergeben ~0.034 MPa, weit unter 0.05
    assert r["tau_MPa"] < 0.05
    assert r["PASS"]


def test_seitenschrauben_auszug():
    r = A.side_screw_pullout(PRM.P)
    assert r["F_zul_N"] > 150.0            # je Schraube, dauerfest
    assert r["PASS"]
