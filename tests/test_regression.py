"""FEM-Regression: Referenz-Parameterstand -> erwartete Kennwerte ±15 %.
Fängt unbeabsichtigte Modell-/Vernetzungsänderungen. Grobnetz für Tempo."""
import params as PRM
from fem import loadcases as LC
from fem.run_fem import run_case
from model.frame import build_frame

REFERENZ = {
    # Grobnetz-Gegenprobe (MESH_MM_TEST=20). Historie:
    # - Parameterstand 9f91735a (2026-07-12): LF1 0.8933, LF3 2.1136 MPa
    #   (Produktionsnetz 10 mm: 0.85 bzw. 2.13 MPa).
    # - Parameterstand dfc6857f (2026-07-13, GEOM_REV 4 + Messkampagne):
    #   LF3 sinkt auf 1.43 MPa -- REC_GUSSET_D=0 macht die Deckplatte im
    #   früheren Freistellungsring voll tragend (5 statt 2 mm unter der
    #   Klemm-Lastfläche), LF1 bleibt im 15-%-Band. Bewusste Re-Baseline,
    #   keine unbeabsichtigte Modelländerung (Suite-Lauf out/suite_passung.log).
    # - GEOM_REV 5 / Standard-ASA (2026-07-14): Entwässerungsfase und lokal
    #   massive ST4.2-Schraubpfade ändern die Steifigkeitsverteilung bewusst.
    #   Re-Baseline aus separatem Grobnetzlauf: LF1 0.7305, LF3 1.3767 MPa;
    #   die unveränderte ±15-%-Toleranz fängt weitere Drift weiterhin ab.
    "LF1_wind": 0.74,
    "LF3_klemmung": 1.38,
}


def test_fem_regression_grobnetz():
    s = build_frame()
    for name, ref in REFERENZ.items():
        r = run_case(s, LC.CASES[name], PRM.P, PRM.P.MESH_MM_TEST)
        assert abs(r["vm_max_MPa"] - ref) / ref < 0.15, \
            f"{name}: {r['vm_max_MPa']:.2f} weicht > 15 % von Referenz {ref} ab"
