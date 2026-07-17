"""Suite-Test für scripts/toleranz_sweep.py: reines Python3 per subprocess
(kein FreeCAD-Import noetig, gleiche Konvention wie test_tools_measurements).
Bewusst NUR strukturelle Zusicherungen und aus params.py abgeleitete Formeln
-- die konkreten Kipp-Befunde aendern sich mit der echten Messkampagne und
duerfen die Suite dann nicht brechen."""
import json
import subprocess
import tempfile
from pathlib import Path

import params as PRM

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "toleranz_sweep.py"


def _run(*args):
    # sys.executable ist unter freecadcmd (bin/fc) freecadcmd selbst --
    # deshalb explizit "python3" (siehe test_tools_measurements.py).
    return subprocess.run(["python3", str(SCRIPT), *args],
                          capture_output=True, text=True, cwd=str(ROOT))


def test_sweep_laeuft_und_meldet_alle_abschnitte():
    result = _run()
    assert result.returncode in (0, 1), result.stderr
    for marker in ("Toleranz-Sweep", "Regime-Analyse", "One-at-a-time",
                   "Eckensweep"):
        assert marker in result.stdout, f"{marker!r} fehlt:\n{result.stdout}"


def test_sweep_json_ist_vollstaendig_und_konsistent():
    with tempfile.TemporaryDirectory(prefix="toleranz_test_") as tmp:
        ziel = Path(tmp) / "sweep.json"
        result = _run("--json", str(ziel))
        assert result.returncode in (0, 1), result.stderr
        daten = json.loads(ziel.read_text(encoding="utf-8"))

    assert daten["parameter_hash"] == PRM.params_hash()
    felder = daten["toleranzen_mm"]
    assert daten["ecken"]["ecken_gesamt"] == 2 ** len(felder)
    assert (daten["ecken"]["ecken_validate_fail"]
            + daten["ecken"]["ecken_gate_fail"]
            == daten["ecken"]["ecken_fail"])
    # Nominalparameter muessen alle analytischen Gates bestehen -- sonst
    # waere der committete Parameterstand selbst nicht baubar.
    assert daten["oat"]["nominal"]["all_gates_PASS"] is True
    # Die gemeldete Maximalauslastung muss die freigabewirksamen Nachweise
    # unabhaengig nachgerechnet abdecken (Audit 2026-07-17: eine
    # schluesselnamensbasierte Suche uebersah rk1300_utilization und
    # normalized_interaction und untertrieb 77 % als 74 %).
    from analysis import load_paths as LP
    from fem import analytic as A
    r = LP.assess(include_cfd=False)
    erwartet = [A.glue_shear_utilization(PRM.P),
                r["segment_joint"]["rk1300_utilization"],
                r["segment_joint"]["m5_one_remaining_utilization"]]
    for fall in r["load_cases"].values():
        erwartet += [
            fall["belluna_to_adapter"]["eight_side_screws_full_case"]
            ["utilization"],
            fall["adapter_to_roof"]["double_elastic_bead_primary"]
            ["normalized_interaction"],
            fall["wood_to_roof_sandwich"]["sikaforce_one_face_only"]
            ["normalized_interaction"]]
    assert abs(daten["oat"]["nominal"]["max_utilization"]
               - max(erwartet)) < 0.001
    # Regime-Formeln direkt gegen params.py (robust gegen Wertaenderungen).
    p = PRM.P
    regime = daten["regime"]
    assert regime["edge_dist_regimegrenze_mm"] == p.HOOD_TIP_REACH
    assert regime["ueberlapp_edge_h_max_mm"] == round(
        p.H_RAISE + p.HOOD_UNDERSIDE_H - p.CLEAR_MIN, 1)
    erwartet = "OFFEN" if p.HOOD_TIP_REACH < p.EDGE_DIST else "UEBERLAPP"
    assert regime["regime_nominal"] == erwartet


def test_sweep_lehnt_unbekanntes_messfeld_ab():
    result = _run("--tol", "GIBT_ES_NICHT=1.0")
    assert result.returncode == 2
    assert "unbekanntes Messfeld" in result.stderr
