"""Gesamtpipeline: Modell -> FEM (Produktionsnetz) -> Analytik -> Export -> Report.
Aufruf: bin/fc run_all.py   — Exit-Code 0 nur bei Gesamt-PASS."""
import subprocess
import sys
import time

# freecadcmd flusht gepufferten Python-stdout bei Redirect (nohup/Pipe) nicht
# zuverlässig beim Prozessende -- ohne line_buffering fehlen ALLE print()-
# Zeilen inkl. Vorbehalts-Banner im Log (gleiche Ursache wie in
# tests/run_tests.py dokumentiert; beim ersten Pipeline-Lauf nachgewiesen).
sys.stdout.reconfigure(line_buffering=True)

import params as PRM
PRM.validate()
from export.export import export_all
from export.manifest import append_manifest
from fem.joint_check import run_joint_submodel
from fem.loadcases import CASES
from fem.report import write_report
from fem.run_fem import run_case
from model.dfm import overhang_area
from model.frame import build_frame
from model.segments import build_segments

t_start = time.time()
p = PRM.P
h = PRM.params_hash(p)
print(f"Parameterstand {h}: baue Rahmen …")
frame = build_frame(p)
print(f"  Rahmen gebaut ({time.time() - t_start:.1f} s)")

# Segmente EINMAL bauen (nicht mehr separat in export_all) -- Grundlage für
# das DFM-Gate UND für den späteren Export (Finalreview I2 + M4: Shape-
# Durchreichung spart ~20-30 s je Lauf, siehe export/export.py::export_all).
t0 = time.time()
segments = build_segments(p)
print(f"  Segmente gebaut ({time.time() - t0:.1f} s)")

print("DFM-Überhangs-Gate für 4 Rotationskopien des Universal-Segments …")
dfm_failed = []
for i, seg in enumerate(segments):
    bad, allowed = overhang_area(seg, p)
    limit = allowed * 1.2 + 200
    status = "PASS" if bad <= limit else "FAIL"
    print(f"  DFM Universal-Kopie {i}: {bad:.0f}/{limit:.0f} mm² Überhang -> {status}")
    if bad > limit:
        dfm_failed.append(i)
if dfm_failed:
    print(f"ABBRUCH: DFM-Überhangs-Gate FAIL für Segment(e) {dfm_failed} — kein Export.")
    sys.exit(1)

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
# write_report liefert (ok, vorbehalt) als strukturiertes Ergebnis (Ledger
# 42) -- kein "Vorbehalt"-String-Grep im Reporttext mehr für die Gate-
# Entscheidung. ok/vorbehalt kommen direkt aus der Verifikationslogik.
ok, vorbehalt = write_report(fem_results, joint, p, report_path)
print(f"Report: {report_path} -> {'PASS' if ok else 'FAIL'}")

if not ok:
    print("ABBRUCH: Verifikation FAIL — kein Export.")
    sys.exit(1)

# "PASS mit Vorbehalt" liefert ok=True -> weiter exportieren, aber der
# Hinweis darf im Konsolenoutput nicht untergehen (der Bediener könnte
# sonst ungeprüft in den Druck gehen). Details stehen im Report selbst.
if vorbehalt:
    print()
    print("!" * 78)
    print("! ACHTUNG: PASS MIT VORBEHALT — vor Druckfreigabe im Report prüfen!")
    print(f"! Report: {report_path}")
    print("!" * 78)
    print()

print("Export …")
t0 = time.time()
exported = export_all(p, "out", frame=frame, segments=segments)
for f in exported:
    print(f"  {f}")
print(f"  Export fertig ({time.time() - t0:.1f} s, frame/segments durchgereicht "
      f"-- eine Universal-Datei x4, kein erneutes build_frame/build_segments)")

try:
    git_rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                             text=True, check=True).stdout.strip()
except Exception as exc:
    git_rev = f"UNBEKANNT ({exc})"
append_manifest(report_path, exported, git_rev, p)
print(f"Manifest an {report_path} angehängt ({len(exported)} Dateien, Git {git_rev}).")

if vorbehalt:
    print(f"FERTIG: Artefakte erzeugt -- PASS MIT VORBEHALT, KEINE "
          f"Druckfreigabe (offene Messwerte/Probedruck, siehe Report). "
          f"(Gesamtlaufzeit {time.time() - t_start:.0f} s)")
else:
    print(f"FERTIG: Druckdateien sind verifiziert freigegeben. "
          f"(Gesamtlaufzeit {time.time() - t_start:.0f} s)")
sys.exit(0)
