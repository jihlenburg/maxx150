"""Gesamtpipeline: Modell -> FEM (Produktionsnetz) -> Analytik -> Export -> Report.
Aufruf: bin/fc run_all.py   — Exit-Code 0 nur bei Gesamt-PASS."""
import sys
import time
from pathlib import Path

# freecadcmd flusht gepufferten Python-stdout bei Redirect (nohup/Pipe) nicht
# zuverlässig beim Prozessende -- ohne line_buffering fehlen ALLE print()-
# Zeilen inkl. Vorbehalts-Banner im Log (gleiche Ursache wie in
# tests/run_tests.py dokumentiert; beim ersten Pipeline-Lauf nachgewiesen).
sys.stdout.reconfigure(line_buffering=True)

import params as PRM
from export.export import export_all
from fem.joint_check import run_joint_submodel
from fem.loadcases import CASES
from fem.report import write_report
from fem.run_fem import run_case
from model.frame import build_frame

t_start = time.time()
p = PRM.P
h = PRM.params_hash(p)
print(f"Parameterstand {h}: baue Rahmen …")
frame = build_frame(p)
print(f"  Rahmen gebaut ({time.time() - t_start:.1f} s)")

print("FEM-Lastfälle (Produktionsnetz) …")
# Explizite Schleife statt run_all_cases(): Laufzeit je Lastfall messen
# (Betriebsdaten für Netz-/Modelländerungen; Controller-Auftrag Task 13).
fem_results = {}
for name, case in CASES.items():
    t0 = time.time()
    fem_results[name] = run_case(frame, case, p, p.MESH_MM)
    r = fem_results[name]
    print(f"  {name}: vM {r['vm_max_MPa']:.2f}/{r['allowable_MPa']:.2f} MPa "
          f"-> {'PASS' if r['PASS'] else 'FAIL'}  ({time.time() - t0:.1f} s)")

print("Stoß-Submodell …")
t0 = time.time()
joint = run_joint_submodel(p)
print(f"  Stoß: vM {joint['vm_max_MPa']:.2f}/{joint['allowable_MPa']:.2f} MPa "
      f"-> {'PASS' if joint['PASS'] else 'FAIL'}  ({time.time() - t0:.1f} s)")

report_path = f"out/report_{h}.md"
ok = write_report(fem_results, joint, p, report_path)
print(f"Report: {report_path} -> {'PASS' if ok else 'FAIL'}")

if not ok:
    print("ABBRUCH: Verifikation FAIL — kein Export.")
    sys.exit(1)

# "PASS mit Vorbehalt" liefert ok=True -> weiter exportieren, aber die
# Vorbehaltszeile darf im Konsolenoutput nicht untergehen (der Bediener
# könnte sonst ungeprüft in den Druck gehen).
report_text = Path(report_path).read_text()
if "Vorbehalt" in report_text:
    vorbehalt_lines = [ln for ln in report_text.splitlines()
                       if "Vorbehalt" in ln or "OFFEN" in ln]
    print()
    print("!" * 78)
    print("! ACHTUNG: PASS MIT VORBEHALT — vor Druckfreigabe prüfen!")
    for ln in vorbehalt_lines:
        print(f"! {ln}")
    print("!" * 78)
    print()

print("Export …")
for f in export_all(p, "out"):
    print(f"  {f}")
print(f"FERTIG: Druckdateien sind verifiziert freigegeben. "
      f"(Gesamtlaufzeit {time.time() - t_start:.0f} s)")
sys.exit(0)
