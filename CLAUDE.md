# maxx150 — Belluna-Adapterrahmen (Challenger X150)

Parametrisches FreeCAD-Modell + FEM-Verifikation + Export für einen
4-teiligen, gedruckten Adapterrahmen (MaxxFan-Lüfter auf Belluna-Dachausschnitt).

Antworte auf Deutsch. Code/Kommentare/Commits ebenfalls Deutsch.

## Verzeichnisüberblick

- `params.py` — einzige Parameterquelle (`P`, `params_hash()`, `validate()`).
- `model/` — Geometrie (`frame.py`, `segments.py`, `features.py`, `dfm.py`).
- `fem/` — FEM (`loadcases.py`, `run_fem.py`, `heatmap.py`, `analytic.py`,
  `material.py`, `report.py`, `joint_check.py`).
- `export/` — Druck-/Archivdateien + Montagenotiz.
- `render/` — Render-STLs (FreeCAD-Seite) + Blender-Renderskripte.
- `scripts/` — Orchestrierung (`render.sh`, `heatmap.sh`, `messkampagne.py`).
- `tests/` + `run_tests.py` — Testsuite (minimaler freecadcmd-Runner).
- `run_all.py` — Gesamtpipeline (Modell→FEM→Analytik→Export→Report).
- `out/` — generierte Artefakte, gitignored.

## Kernkommandos

```sh
bin/fc tests/run_tests.py                     # volle Suite (~10 min, Hintergrund!)
TEST_FILTER=params bin/fc tests/run_tests.py   # nur Dateien mit 'params' im Namen
nohup bin/fc run_all.py > out/run_all.log 2>&1 &  # Pipeline, IMMER Hintergrund + Log + Poll
scripts/render.sh out/render out/render iso_oben   # Rendering (eine Ansicht = Smoke-Test)
scripts/heatmap.sh                             # FEM-Heatmap je Lastfall (mehrere Minuten!)
python3 scripts/messkampagne.py messwerte.json --dry-run   # Messwerte → params.py
```

Details/Fallstricke: Skills `maxx150-pipeline`, `maxx150-render`,
`maxx150-messkampagne` (`.claude/skills/`). Historie/Entscheidungen:
`docs/superpowers/`, `.superpowers/sdd/progress.md`. Offene Punkte: `todo.md`.

## FreeCAD-Fallstricke (Kurzform, Details im Skill maxx150-pipeline)

- `freecadcmd -c` kann kein Multiline; Skript-argv unzuverlässig → Env-Vars.
- stdout braucht `line_buffering`/explizites `flush()` bei Hintergrundläufen.
- `FemMesh.Nodes` ist O(n) je Zugriff — einmal heben, nie in Schleifen lesen.
- `mesh.Shape`/`mesh.Part` per `try/except` (FreeCAD-API-Version).
- `SecondOrderLinear=True` Pflicht (sonst ccx-Fehler 201 an Kleinradien).
- `ConstraintForce.Direction` braucht eine LinkSub-Kantenreferenz.
- `sys.executable` ist unter freecadcmd freecadcmd selbst, nicht `python3`.

## Regel

Jede geometrie-wirksame Code-Änderung (neue Fillets/Radien, geänderte
Booleans, …) ⇒ `Params.GEOM_REV` in `params.py` erhöhen — ändert `params_hash`,
hält Druckdateien/Reports eindeutig einer Geometrie zugeordnet.
