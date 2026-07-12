"""Integrationstest: kompletter Gmsh+CalculiX-Lauf für einen Lastfall
(Grobnetz, schnellster Lastfall LF4 als Rauchtest der gesamten Kette)."""
import params as PRM
from model.frame import build_frame
from fem import loadcases as LC
from fem.run_fem import run_case


def test_lf4_schnee_grobnetz():
    """Schnellster Lastfall als Integrationstest (Grobnetz)."""
    s = build_frame()
    r = run_case(s, LC.CASES["LF4_schnee"], PRM.P, PRM.P.MESH_MM_TEST)
    assert r["vm_max_MPa"] > 0.001
    assert r["vm_max_MPa"] < 5.0, f"200 N Schnee erzeugen {r['vm_max_MPa']} MPa?!"
    assert r["defl_max_mm"] < 0.2
    assert r["PASS"] is True
    # Voller Rahmen hat echte Deckflächen-Knoten -> kein Fallback (M3/Ledger 32)
    assert r["defl_top_is_fallback"] is False
