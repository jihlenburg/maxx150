"""Suite-Test für scripts/apply_measurements.py: reines Python3 per subprocess
(kein FreeCAD-Import noetig), arbeitet NUR auf einer tmp-Kopie von params.py
-- das echte params.py wird NIE angefasst. Dateiname enthaelt 'tools'
(gemeinsamer Substring-Filter mit test_tools_heatmap.py, siehe
tests/run_tests.py::TEST_FILTER)."""
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "apply_measurements.py"
BEISPIEL = ROOT / "messwerte.beispiel.json"


def _run(*args):
    # ACHTUNG: sys.executable ist unter freecadcmd (bin/fc, wie diese Test-
    # Suite laeuft) freecadcmd selbst, nicht python3 -- und freecadcmd-argv
    # ist unzuverlaessig (Skill maxx150-pipeline). Deshalb explizit "python3"
    # (reines Python3-Skript, kein FreeCAD-Import, siehe Moduldocstring).
    return subprocess.run(["python3", str(SCRIPT), *args],
                          capture_output=True, text=True, cwd=str(ROOT))


def _tmp_params() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="measurements_test_"))
    target = tmp / "params.py"
    shutil.copy2(ROOT / "params.py", target)
    return target


def _feld_wert(text: str, feld: str) -> float:
    m = re.search(rf"{feld}\s*:\s*\w+\s*=\s*([0-9eE+\-.]+)", text)
    assert m, f"{feld} nicht in params-Text gefunden"
    return float(m.group(1))


def test_beispiel_json_patcht_erwartete_felder():
    target = _tmp_params()
    r = _run(str(BEISPIEL), "--target", str(target))
    assert r.returncode == 0, r.stdout + r.stderr

    messwerte = json.loads(BEISPIEL.read_text())
    text = target.read_text()

    assert abs(_feld_wert(text, "EDGE_DIST") - (messwerte["B1a"] + messwerte["B1b"])) < 1e-6
    assert abs(_feld_wert(text, "EDGE_H") - messwerte["B2"]) < 1e-6
    assert abs(_feld_wert(text, "ROOF_T") - messwerte["B3"]) < 1e-6
    assert abs(_feld_wert(text, "HOOD_UNDERSIDE_H") - messwerte["B4"]) < 1e-6

    # Design-Entscheidungen 2026-07-13 (Review-Fix): A1c-f und A4a/A4b werden
    # BEWUSST NICHT mehr gemappt -- W_TOP_*/REC_GUSSET_* muessen auf ihren
    # params.py-Defaults stehen bleiben, der Lauf meldet das explizit.
    original = (ROOT / "params.py").read_text()
    for feld in ("W_TOP_FRONT", "W_TOP_REAR", "W_TOP_LEFT", "W_TOP_RIGHT",
                 "REC_GUSSET_D", "REC_GUSSET_W"):
        assert _feld_wert(text, feld) == _feld_wert(original, feld), feld
    assert "BEWUSST NICHT uebernommen" in r.stdout

    # Felder OHNE Formel/Messwert (A2/A3/A5, hier null) bleiben unveraendert:
    assert _feld_wert(text, "CUTOUT_W") == _feld_wert(original, "CUTOUT_W")

    backup = target.with_name(target.name + ".bak")
    assert backup.exists()
    assert backup.read_text() == (ROOT / "params.py").read_text()


def test_dry_run_schreibt_nichts():
    target = _tmp_params()
    original = target.read_text()
    r = _run(str(BEISPIEL), "--target", str(target), "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "nichts geschrieben" in r.stdout
    assert target.read_text() == original
    assert not target.with_name(target.name + ".bak").exists()


def test_diff_tabelle_im_stdout():
    target = _tmp_params()
    r = _run(str(BEISPIEL), "--target", str(target))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "EDGE_DIST" in r.stdout
    assert "alt" in r.stdout and "neu" in r.stdout
    assert "pipeline test" in r.stdout and "pipeline engineering" in r.stdout


def test_echte_messwerte_json_ergibt_validen_parameterstand():
    """Review-Fix 2026-07-14: die ECHTE messwerte.json (nicht nur das
    Beispiel) muss durch den Importer laufen und einen validate()-sauberen
    Parameterstand ergeben. Vorher schlug der Importer W_TOP=26 und
    REC_GUSSET_D=19.5 vor -- beides dokumentierte validate()-Brecher
    (Design-Entscheidungen in messwerte.json/_notizen)."""
    echt = ROOT / "messwerte.json"
    target = _tmp_params()
    r = _run(str(echt), "--target", str(target))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "BEWUSST NICHT uebernommen" in r.stdout

    text = target.read_text()
    original = (ROOT / "params.py").read_text()
    for feld in ("W_TOP_FRONT", "W_TOP_REAR", "W_TOP_LEFT", "W_TOP_RIGHT",
                 "REC_GUSSET_D"):
        assert _feld_wert(text, feld) == _feld_wert(original, feld), feld

    # gepatchte Kopie importieren und validate() ausfuehren (python3-Subprozess,
    # params.py ist reines Python)
    check = subprocess.run(
        ["python3", "-c",
         "import importlib.util,sys;"
         f"spec=importlib.util.spec_from_file_location('pp', r'{target}');"
         "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
         "m.validate();print('VALIDATE-OK', m.params_hash())"],
        capture_output=True, text=True)
    assert check.returncode == 0, check.stdout + check.stderr
    assert "VALIDATE-OK" in check.stdout


def test_echtes_params_py_bleibt_unberuehrt():
    """Sicherstellen, dass NUR die --target-Kopie gepatcht wird."""
    real_before = (ROOT / "params.py").read_text()
    target = _tmp_params()
    r = _run(str(BEISPIEL), "--target", str(target))
    assert r.returncode == 0, r.stdout + r.stderr
    assert (ROOT / "params.py").read_text() == real_before
    assert not (ROOT / "params.py.bak").exists()
