---
name: maxx150-pipeline
description: Arbeit an diesem Repo (maxx150, Belluna-Adapterrahmen) — Bauen, Testen, FEM-Läufe, Parameter/Hash/GEOM_REV, Commit-Politik. Immer laden, bevor Code in model/, fem/, params.py, run_all.py oder tests/ geändert oder eine Suite/run_all/FEM ausgeführt wird.
---

# maxx150-Pipeline

FreeCAD-Projekt (Belluna-Adapterrahmen, Challenger X150). Alle Wege führen über
`freecadcmd` — es gibt kein pytest im FreeCAD-Python, kein System-`python3` mit
FreeCAD-Modulen.

## bin/fc-Wrapper

`bin/fc <script.py> [args]` ist `exec /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd "$@"`.
Nutze IMMER `bin/fc`, nie den nackten `freecadcmd`-Pfad.

**Fallstricke:**
- `freecadcmd -c "..."` kann **kein Multiline** — nur einzeilige Kommandos.
  Für alles Mehrzeilige ein Skript-File schreiben und `bin/fc datei.py` aufrufen.
- **argv nach dem Skriptpfad ist unzuverlässig** (freecadcmd reicht es nicht
  robust durch). Steuerung über **Umgebungsvariablen**, nicht CLI-Flags (siehe
  `render/make_views_stl.py`: `RENDER_ZCUT`/`RENDER_XCUT`). `scripts/*.py`
  (reines Python3, z. B. `scripts/messkampagne.py`) sind davon NICHT betroffen
  — die laufen unter echtem `python3`, dort funktioniert argparse normal.
  ACHTUNG: `sys.executable` ist unter freecadcmd **freecadcmd selbst**, nicht
  `python3` — wer aus einem bin/fc-Kontext einen echten Python3-Subprozess
  braucht (z. B. Tests für reine Python3-Skripte), muss explizit `"python3"`
  aufrufen, nie `sys.executable`.
- **stdout braucht line_buffering + Flush.** Bei Hintergrund-/Redirect-Läufen
  (nohup, Pipe, Datei) flusht freecadcmd gepufferten stdout beim Prozessende
  NICHT zuverlässig — sonst fehlen die letzten `print()`-Zeilen (inkl.
  Zusammenfassung/Vorbehalts-Banner) im Log. Fix:
  `sys.stdout.reconfigure(line_buffering=True)` am Skriptanfang (siehe
  `run_all.py`) bzw. explizites `sys.stdout.flush()` nach jeder wichtigen Zeile
  (siehe `tests/run_tests.py`).
- `FemMesh.Nodes` ist eine **O(n)-Property** — jeder Zugriff baut das komplette
  Knoten-Dict neu auf (~85k Einträge beim Grobnetz). Einmal in eine lokale
  Variable heben, NIE in einer Schleife wiederholt zugreifen (sonst O(n²),
  >570 s statt Millisekunden — Root-Cause aus Task 9).
- `mesh.Shape = geo` (FreeCAD 1.x) vs. `mesh.Part = geo` (ältere API) — immer
  mit `try/except` beides abdecken (siehe `fem/run_fem.py`, `fem/heatmap.py`).
- `SecondOrderLinear = True` ist **Pflicht** bei quadratischen Tetraedern: ohne
  das erzeugt Gmsh an kleinradiigen Details (Noppen R4, Vent-Bohrungen Ø4,
  Außenfase 4 mm) umgeschlagene Elemente ("nonpositive jacobian"), CCX bricht
  mit Fehler 201 ab.
- `ConstraintForce.Direction` braucht eine **LinkSub-Kantenreferenz**, kein
  Vector direkt — dafür baut `fem/run_fem.py::_direction_ref()` eine kurze
  Hilfslinie als `Part::Feature` und referenziert deren `Edge1`. Wiederverwenden
  statt duplizieren (siehe `fem/heatmap.py`, importiert `_direction_ref` +
  `_ensure_binary_paths` aus `fem.run_fem`).

## Tests: TEST_FILTER-Konvention

`bin/fc tests/run_tests.py` läuft alle `tests/test_*.py`, sammelt jede
`test_*`-Funktion, druckt `PASS`/`FAIL` je Funktion + Summenzeile
`N bestanden, M fehlgeschlagen`, Exit-Code 1 bei Fehlern.

`TEST_FILTER=<substring> bin/fc tests/run_tests.py` filtert **auf den
Dateinamen** (nicht Funktionsnamen!) — nur Dateien, deren Name den Substring
enthält, laufen. Mehrere neue Testdateien mit einem gemeinsamen Namensteil
(z. B. `test_tools_*.py`) lassen sich so gemeinsam gezielt ausführen:
`TEST_FILTER=tools bin/fc tests/run_tests.py`.

Suite-Laufzeit **~10 Minuten** (voller Bestand inkl. FEM-Integrationstests) —
niemals mit kurzem Foreground-Timeout laufen lassen, siehe unten.

## run_all.py: IMMER als Hintergrundprozess

`bin/fc run_all.py` läuft je nach Parameterstand 1–3 Minuten (Produktionsnetz,
4 Lastfälle + Stoß-Submodell + Export). Genau wie die Suite: **nie im
Vordergrund mit kurzem Timeout starten** — als Hintergrundprozess mit Log +
Poll:

```sh
nohup bin/fc run_all.py > out/run_all.log 2>&1 &
echo $! > out/run_all.pid
# danach pollen (Prozess noch da? Log wachsen? "FERTIG"/Exit-Code im Log?)
```

Gleiches Muster für `bin/fc tests/run_tests.py` bei langen Läufen. Fertig ist
der Lauf, wenn `out/run_all.log` mit `FERTIG: ...` oder `ABBRUCH: ...` endet
(exit 0 bzw. 1).

## Gate-Semantik: PASS / Vorbehalt / FAIL

`fem/report.py::write_report()` liefert `ok: bool` (Gesamt-Gate) und schreibt
drei mögliche Banner in den Report:
- **PASS** — alle Nachweise grün, sofort druckfreigegeben.
- **PASS mit Vorbehalt** — `ok=True`, aber mindestens ein Nachweis beruht auf
  einer Schätzung, aktuell: Haubenfreigang ohne echten Messwert (EDGE_DIST/
  EDGE_H, Messkampagne 7) → Report zeigt `OFFEN` statt einer Zahl. Export läuft
  trotzdem, `run_all.py` druckt zusätzlich ein `!`-Banner in der Konsole, damit
  das nicht im Log untergeht.
- **FAIL** — `ok=False`, `run_all.py` bricht VOR dem Export ab (kein Export bei
  fehlgeschlagener Verifikation).

`PRM.validate(p)` (params.py) wirft `ValueError` bei geometrisch inkonsistenten
Parametern (z. B. `W_TOP` zu klein) — läuft VOR jedem `build_frame()`, bricht
sofort ab statt defekte Artefakte zu erzeugen.

## GEOM_REV-Konvention

`Params.GEOM_REV` (int) in params.py erhöhen bei **jeder geometrie-wirksamen
CODE-Änderung** (neue Fillets/Radien, geänderte Booleans etc.) — auch wenn
kein einzelner Messwert/Parameter sich ändert. Grund: `params_hash()` hasht
alle Felder inkl. `GEOM_REV`, damit bekommt jede geometrisch andere Version
zwangsläufig einen neuen Hash (siehe Hash↔Artefakt-Logik unten) und
Druckfiles/Reports bleiben eindeutig einer Geometrie zugeordnet.

## Hash ↔ Artefakt-Logik

`params_hash(p)` (params.py) ist ein 8-Zeichen-SHA256-Präfix über ALLE
Parameterfelder (inkl. `GEOM_REV`). Jeder Export/Report/Render-Lauf hängt
diesen Hash an seine Dateinamen: `out/frame_<hash>.step`,
`out/seg{0..3}_<hash>.{step,stl,3mf}`, `out/report_<hash>.md`,
`out/montagenotiz_<hash>.md`, `out/render/<hash>/*.stl`,
`out/heatmap/heat_*.ply` (Heatmap selbst ist NICHT hash-präfigiert, da
`out_dir` das schon trägt, wenn gewünscht). Praktische Konsequenz: **vor dem
Bauen/Rendern erst `PRM.params_hash()` bilden und prüfen, ob passende
Artefakte schon in `out/` liegen** (spart Minuten) — siehe
`render/make_views_stl.py::_load_or_build_frame/_load_or_build_segments`.

## Commit-Politik

Lokale Commits sind ok (auf `main`, ohne Rückfrage bei explizitem
Nutzerauftrag). **NIE `git push`** ohne ausdrückliche Freigabe des Nutzers.
Gezielt `git add <dateien>` — nie `-A`/`-u` (Gefahr, fremde/parallele
Baustellen versehentlich mitzucommitten).

## Weitere Skills

- `maxx150-render` — Rendern (Ansichten, Explosion, Schnittbild, Heatmap-PNGs).
- `maxx150-messkampagne` — Messwerte aus dem Protokoll in `params.py` eintragen.
