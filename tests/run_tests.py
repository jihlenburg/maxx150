"""Minimaler Testrunner für freecadcmd (kein pytest im FreeCAD-Python).
Aufruf:  bin/fc tests/run_tests.py          — alle Tests
         TEST_FILTER=params bin/fc tests/run_tests.py — nur Dateien mit 'params'."""
import importlib.util
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main():
    """Lädt alle ``tests/test_*.py`` (optional via TEST_FILTER auf Dateinamen
    eingegrenzt), ruft jede ``test_*``-Funktion auf, zählt PASS/FAIL und
    beendet mit Exit-Code 1, sobald mindestens ein Test fehlschlägt."""
    flt = os.environ.get("TEST_FILTER", "")
    passed, failed = 0, 0
    for tf in sorted((ROOT / "tests").glob("test_*.py")):
        if flt and flt not in tf.name:
            continue
        spec = importlib.util.spec_from_file_location(tf.stem, tf)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception:
            print(f"LADEFEHLER {tf.name}")
            traceback.print_exc()
            sys.stdout.flush()
            failed += 1
            continue
        for name in sorted(dir(mod)):
            if name.startswith("test_") and callable(getattr(mod, name)):
                try:
                    getattr(mod, name)()
                    print(f"PASS {tf.stem}.{name}")
                    passed += 1
                except Exception:
                    print(f"FAIL {tf.stem}.{name}")
                    traceback.print_exc()
                    failed += 1
                sys.stdout.flush()
    print(f"\n{passed} bestanden, {failed} fehlgeschlagen")
    # freecadcmd flusht den gepufferten Python-stdout beim regulären
    # Prozessende nicht zuverlässig (sys.exit() allein verschluckt bei
    # nicht-interaktivem stdout, z. B. Pipe/Datei-Redirect, die letzten
    # print()-Zeilen inkl. dieser Zusammenfassung). Explizit flushen.
    sys.stdout.flush()
    sys.exit(1 if failed else 0)


main()
