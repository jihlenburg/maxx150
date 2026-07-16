import params as PRM
from fem import analytic as A


def test_haubenfreigang_default_kein_ueberlapp():
    # Default: Haube ragt 179 mm (MaxxFan-Maßblatt) über den Ausschnitt, Kante erst bei 250 mm
    assert A.hood_clearance() == float("inf")


def test_haubenfreigang_mit_ueberlapp():
    p = PRM.Params(HOOD_TIP_REACH=300.0)        # ragt über die Kante
    c = A.hood_clearance(p)
    # 28 + 30 - 55 = 3 mm Freigang
    assert abs(c - 3.0) < 1e-9


def test_fugenauslastung():
    u = A.glue_shear_utilization()
    # Vollständig verklebter Hybridrahmen: 500 mm.
    # delta=(60-25)e-6*500*65=1.1375 mm; je Ende /2,
    # durch 3-mm-Fuge und 50-%-Grenze => 37,9167 %.
    assert abs(u - 0.37916666666666665) < 1e-8


def test_stossnachweis_traegt_windlast():
    r = A.joint_checks(PRM.P, PRM.wind_force())
    assert r["tau_MPa"] < r["tau_zul_MPa"]
    assert r["m5_count_per_joint"] == 1
    assert r["lochleibung_MPa"] == r["lochleibung_ein_rest_MPa"]
    assert r["lochleibung_ein_rest_MPa"] < r["lochleibung_zul_MPa"]
    assert r["PASS"]


def test_klebfugen_schub_aus_last():
    r = A.glue_load_shear(PRM.P, PRM.wind_force())
    # Zwei abgerundete 10-mm-Raupen minus acht innere 5-mm-Vents:
    # 33.313,27 mm² (exakte R5-Parallelkurven, keine Quadratnäherung).
    assert abs(r["tau_MPa"] - 480 / 33313.27412287184) < 1e-12
    assert r["PASS"]


def test_seitenschrauben_auszug():
    r = A.side_screw_pullout(PRM.P)
    assert r["F_zul_N"] > 150.0            # je Schraube, dauerfest
    # Kreisflächenreferenz 356 N, zusätzlicher FDM-/Detailfaktor 0,5.
    assert abs(r["F_ref_N"] - 356.26) < 1.0
    assert abs(r["F_zul_N"] - 178.13) < 1.0
    assert r["PASS"]
