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
    # Task 19 (Bambu ASA-CF, CTE_ASA 60e-6 statt 90e-6): Segmentlänge 275 mm,
    # dT = max(85-20, 20-(-20)) = 65 K, dAlpha = (60-25)e-6 = 35e-6:
    # delta = 35e-6*275*65 = 0.625625 mm; je Ende 0.3128125; gamma = 0.104271;
    # /GLUE_SHEAR_CAP(0.5) = 0.208542 (~21 %) -- Brief rundete gamma vor dem
    # Halbieren (0.1043*2=0.2086), exakt/unrundend ergibt sich 0.208542;
    # Differenz nur Rundungsartefakt, ändert nichts am Intervall.
    assert 0.15 < u < 0.30


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
    # Sollwert statt nur Schwelle (Ledger 15, Task-5-Review). Task 19 (Bambu
    # ASA-CF): pi*4.2*12*0.5*5.44 = 430.6747 (Brief rundete auf 430.6).
    assert abs(r["F_zul_N"] - 430.6) < 5.0
    assert r["PASS"]
