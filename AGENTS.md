# maxx150 – Arbeitsregeln

Diese Datei ist die einzige Agenten-Anweisung des Repos; `CLAUDE.md` ist ein
Symlink hierauf (ein Inhalt für alle Agenten-Werkzeuge, kein Drift).

Antworte, dokumentiere und committe auf Deutsch. `README.md` und
`docs/README.md` sind die Einstiegspunkte; historische Dateien unter
`docs/archive/` sind nicht normativ.

## Kanonische Befehle

```sh
python3 -m pipeline doctor
python3 -m pipeline test
python3 -m pipeline engineering
python3 -m pipeline connections
python3 -m pipeline fit
python3 -m pipeline cfd
python3 -m pipeline render
python3 -m pipeline heatmap
python3 -m pipeline manual
python3 -m pipeline references
python3 -m pipeline release
python3 -m pipeline all
```

Direkte Unterstufen nur zur Diagnose verwenden. Alle generierten Artefakte
gehören in `build/<stufe>/<hash>/`; `release/current/` wird ausschließlich
durch die Release-Stufe geschrieben.

## Geometrie und Parameter

- `params.py` ist die einzige Parameterquelle.
- Jede geometriewirksame Codeänderung erhöht `Params.GEOM_REV`.
- Hersteller-CAD und Projekt-Rekonstruktion niemals verwechseln. Das
  Belluna-Modell unter `reference_models/` ist eine vermessene Rekonstruktion.
- `PROTOTYPE_ONLY` ist keine Produktionsfreigabe; offene Gates stehen in
  `docs/verification.md`.

## FreeCAD-Fallstricke

- Immer `bin/fc`, nie einen fest codierten freecadcmd-Pfad verwenden.
- Skriptpfade relativ zum Repo übergeben; absolute Pfade werden von FreeCAD
  1.1.1 auf macOS teilweise still ignoriert.
- `freecadcmd -c` und argv sind unzuverlässig; Stufen über Skriptdateien und
  Umgebungsvariablen steuern.
- stdout explizit puffern/flushen.
- `FemMesh.Nodes` nur einmal lesen; `SecondOrderLinear=True` beibehalten.

## Git

Fremde oder lokale Änderungen nicht pauschal stagen. Insbesondere
`messwerte.json` kann uncommittete Nutzerdaten enthalten. Gezielte Dateilisten
verwenden und vor jedem Commit `git diff --cached` prüfen.
