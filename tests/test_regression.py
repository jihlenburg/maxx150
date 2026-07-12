"""FEM-Regression: Referenz-Parameterstand -> erwartete Kennwerte ±15 %.
Fängt unbeabsichtigte Modell-/Vernetzungsänderungen. Grobnetz für Tempo."""
import params as PRM
from fem import loadcases as LC
from fem.run_fem import run_case
from model.frame import build_frame

REFERENZ = {
    # Grobnetz-Gegenprobe (MESH_MM_TEST=20) zum ersten verifizierten
    # run_all.py-Lauf, Parameterstand 9f91735a (2026-07-12):
    # LF1_wind 0.8933 MPa, LF3_klemmung 2.1136 MPa.
    # (Produktionsnetz 10 mm zum Vergleich: 0.85 bzw. 2.13 MPa.)
    "LF1_wind": 0.89,
    "LF3_klemmung": 2.11,
}


def test_fem_regression_grobnetz():
    s = build_frame()
    for name, ref in REFERENZ.items():
        r = run_case(s, LC.CASES[name], PRM.P, PRM.P.MESH_MM_TEST)
        assert abs(r["vm_max_MPa"] - ref) / ref < 0.15, \
            f"{name}: {r['vm_max_MPa']:.2f} weicht > 15 % von Referenz {ref} ab"
