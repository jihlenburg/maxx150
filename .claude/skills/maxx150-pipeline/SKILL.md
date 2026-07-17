---
name: maxx150-pipeline
description: Arbeit an Konstruktion, FEM, Parametern, Tests, Artefakten oder Releases des maxx150-Belluna-Adapters.
---

# maxx150-Pipeline

Vor Änderungen `README.md`, `docs/pipeline.md` und bei Freigabefragen
`docs/verification.md` lesen.

## Einstieg

Alle normalen Abläufe über `python3 -m pipeline <stage>` ausführen. Verfügbare
Stufen: `doctor`, `test`, `engineering`, `connections`, `fit`, `cfd`,
`render`, `heatmap`, `manual`, `references`, `release`, `all`.

## Invarianten

- `params.py` ist die einzige Parameterquelle; Hash umfasst alle Parameter.
- Geometriewirksamer Code erfordert eine Erhöhung von `GEOM_REV`.
- `build/` ist temporär und hash-segregiert.
- `release/current/` darf nur die Release-Stufe schreiben.
- `PROTOTYPE_ONLY` niemals als Produktionsfreigabe formulieren.
- Belluna-STEP/STL sind vermessene Rekonstruktionen, kein Hersteller-CAD.

## FreeCAD

`bin/fc` verwenden. Skriptpfade relativ zum Repo übergeben. FreeCAD-argv nicht
für fachliche Parameter verwenden; Umgebungsvariablen oder Manifestdateien
nutzen. stdout explizit flushen. `FemMesh.Nodes` nur einmal lesen und
`SecondOrderLinear=True` nicht entfernen.

Fehlermeldungs-Falle: `Exception while processing file: <skript> [<text>]`
heißt, `<text>` ist die Exception AUS dem laufenden Skript — ein
`[File does not exist]` zeigt fast immer auf einen falschen Dateipfad IM
Skript, nicht auf ein fehlendes Skript (Fehldiagnose 2026-07-16 kostete eine
komplette Debugging-Schleife samt Watcher-Verdacht; erst der Minimaltest
`print("DA")` isolierte die Ursache).

## Konventionen als Wächter

Jede Konvention, die dauerhaft halten soll, bekommt einen Test statt eines
Doku-Appells (Vorbilder: Doku-Hash-Wächter in `tests/test_documentation.py`,
Provenienz-Pin des Belluna-Quellcodes, Referenzkatalog-Vollständigkeit).
Regeln ohne Wächter gelten als unverbindlich.

## Tests und Git

Gezielt: `TEST_FILTER=<dateiname> bin/fc tests/run_tests.py`; vollständig:
`python3 -m pipeline test`. Nutzeränderungen nicht pauschal stagen. Vor Commit
`git diff --cached --check` und danach den relevanten Pipeline-Gate ausführen.
