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
    # Vollständig verklebter Rahmen: 500 mm statt Drucksegment-Länge.
    # ASA-GF-CTE-Annahme 60e-6: delta=(60-25)e-6*500*65=1.1375 mm;
    # je Ende /2, durch 3-mm-Fuge und 50-%-Grenze => 37.9167 %.
    assert abs(u - 0.3791666667) < 1e-8


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
    # Kreisflächenreferenz 356 N, zusätzlicher FDM-/Detailfaktor 0,5.
    assert abs(r["F_ref_N"] - 356.26) < 1.0
    assert abs(r["F_zul_N"] - 178.13) < 1.0
    assert r["PASS"]
