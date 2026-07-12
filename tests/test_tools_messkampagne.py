"""Suite-Test fuer scripts/messkampagne.py: reines Python3 per subprocess
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
SCRIPT = ROOT / "scripts" / "messkampagne.py"
BEISPIEL = ROOT / "messwerte.beispiel.json"


def _run(*args):
    # ACHTUNG: sys.executable ist unter freecadcmd (bin/fc, wie diese Test-
    # Suite laeuft) freecadcmd selbst, nicht python3 -- und freecadcmd-argv
    # ist unzuverlaessig (Skill maxx150-pipeline). Deshalb explizit "python3"
    # (reines Python3-Skript, kein FreeCAD-Import, siehe Moduldocstring).
    return subprocess.run(["python3", str(SCRIPT), *args],
                          capture_output=True, text=True, cwd=str(ROOT))


def _tmp_params() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="messkampagne_test_"))
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
    assert abs(_feld_wert(text, "W_TOP_FRONT") - messwerte["A1c"]) < 1e-6
    assert abs(_feld_wert(text, "W_TOP_REAR") - messwerte["A1d"]) < 1e-6
    assert abs(_feld_wert(text, "W_TOP_LEFT") - messwerte["A1e"]) < 1e-6
    assert abs(_feld_wert(text, "W_TOP_RIGHT") - messwerte["A1f"]) < 1e-6
    # dokumentierte Reserven:
    assert abs(_feld_wert(text, "REC_GUSSET_D") - (messwerte["A4a"] + 0.5)) < 1e-6
    assert abs(_feld_wert(text, "REC_GUSSET_W") - (messwerte["A4b"] + 2.0)) < 1e-6

    # Felder OHNE Formel/Messwert (A2/A3/A5, hier null) bleiben unveraendert:
    original = (ROOT / "params.py").read_text()
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
    assert "run_tests.py" in r.stdout and "run_all.py" in r.stdout


def test_echtes_params_py_bleibt_unberuehrt():
    """Sicherstellen, dass NUR die --target-Kopie gepatcht wird."""
    real_before = (ROOT / "params.py").read_text()
    target = _tmp_params()
    r = _run(str(BEISPIEL), "--target", str(target))
    assert r.returncode == 0, r.stdout + r.stderr
    assert (ROOT / "params.py").read_text() == real_before
    assert not (ROOT / "params.py.bak").exists()
