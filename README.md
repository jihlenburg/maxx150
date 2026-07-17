# Belluna-Super-Fan-Adapter für den Challenger X150

Parametrisches FreeCAD-Modell eines 28-mm-Adapterrahmens für den Belluna Super
Fan im vorhandenen 400×400-mm-Dachausschnitt. Das Bauteil besteht aus vier
rotationsidentischen L-Segmenten und wird als ein Universalteil mit Stückzahl
vier bereitgestellt.

## Projektstatus

**Aktueller Parameterstand:** `8eb8b79f` · **GEOM_REV:** `10`
**Freigabestatus:** `PROTOTYPE_ONLY`

Geometrie-, DFM-, FEM-, analytische, Lastpfad- und digitale Passungsnachweise
sind Teil der Pipeline. Eine Produktionsfreigabe besteht trotzdem noch nicht:
Nicht verfügbare Werkstoff-/Haftversuche sind durch stark abgeminderte,
quellenbasierte Annahmen ersetzt (`PASS_ASSUMPTION_BASED`); endgültiger
Dachausschnitt, Doppelraupe und Holzrahmen bleiben beim Einbau zu
kontrollieren. Die acht seitlichen Dachrahmenschrauben sind eine physische,
aber mangels typgeprüftem Schraubgrund rechnerisch nicht angerechnete Reserve.
Die Dateien unter
[`release/current`](release/current/) sind daher ein nachvollziehbarer
Release Candidate, keine stillschweigende Serienfreigabe.

## Ein Einstiegspunkt

```sh
python3 -m pipeline doctor       # Werkzeugkette prüfen
python3 -m pipeline test         # komplette Testsuite
python3 -m pipeline engineering  # Konstruktion + DFM + FEM + Report + Export
python3 -m pipeline connections  # Klebe-, Schraub- und Dachsandwich-Lastpfade
python3 -m pipeline fit          # Belluna-Rekonstruktion gegen Adapter prüfen
python3 -m pipeline cfd          # aerodynamisches Hüllmodell + OpenFOAM
python3 -m pipeline render       # technische Konstruktionsansichten
python3 -m pipeline heatmap      # FEM-Heatmaps
python3 -m pipeline manual       # Montagebilder + PDF
python3 -m pipeline references   # Belluna-Referenzmodelle neu exportieren
python3 -m pipeline release      # verifizierten Stand paketieren
python3 -m pipeline all          # alle Stufen in Gate-Reihenfolge
```

Alle temporären Ergebnisse landen unter `build/<stufe>/<parameter-hash>/`.
Nur geordnete Herstellerreferenzen und der explizit paketierte Release
Candidate werden versioniert.

## Struktur

| Pfad | Verantwortung |
|---|---|
| `params.py` | einzige Quelle für Geometrie-, Last- und Materialparameter |
| `model/` | B-Rep-Rahmen, Segmentierung und DFM-Geometrie |
| `fem/` | Lastfälle, Materialmodell, CalculiX und analytische Nachweise |
| `analysis/` | Belluna-Passung sowie Klebe-, Schraub- und Sandwich-Lastpfade |
| `cfd/` | Belluna-Aerohüllmodell, OpenFOAM-Fall und Kräfteauswertung |
| `export/` | STEP/STL/3MF und technische Montagenotiz |
| `render/` | technische Blender-Ansichten und Heatmaps |
| `montage/` | Generator der illustrierten Montageanleitung |
| `pipeline/` | zentrale Orchestrierung und Release-Paketierung |
| `reference_models/` | parametrische Rekonstruktionen externer Schnittstellen |
| `references/` | Datenblätter, Belluna-Unterlagen und Referenzmodelle |
| `release/current/` | aktueller, manifestierter STL-/STEP-Stand |
| `docs/` | aktuelle Doku; historische Arbeitspläne nur unter `docs/archive/` |
| `tests/` | Suite inklusive Geometrie-, FEM-, Referenz- und Doku-Wächtern |
| `scripts/` | Bedienhelfer (Messwertübernahme nach `params.py`) |
| `bin/` | `fc`-Wrapper für headless FreeCAD |
| `project_paths.py` | zentrale Build-/Artefaktpfade für alle Stufen |
| `messwerte.json` | reale Messwerte (Eingabe für `scripts/apply_measurements.py`; kann uncommittete Nutzerdaten enthalten) |
| `messwerte.beispiel.json` | dokumentierte Feldvorlage des Messprotokolls |

### Ordnungsprinzipien

Die Struktur folgt vier Schichten — **Eingaben → Verwandlung → Wissen →
Ergebnisse** — mit fünf Regeln:

1. **Eine Quelle, ein Hash.** Alles beginnt bei `params.py`; der achtstellige
   Parameter-Hash steckt im Namen jedes Artefakts. Ein Artefakt ohne
   zugehörigen Report gilt als nicht nachvollziehbar.
2. **Code fließt in eine Richtung.** `model` baut Geometrie, `fem`/`analysis`/
   `cfd` beweisen sie, `export`/`render`/`montage` erzeugen Artefakte,
   `pipeline` orchestriert das als Gate-Kette. Kein Modul greift rückwärts.
3. **Versioniert wird Wissen, nicht Rechenergebnis.** `references/` und
   `docs/` sind nicht regenerierbar und daher getrackt; `build/` ist
   hash-segregierte Wegwerfware. Einzige Ausnahme: `release/current/` — genau
   ein eingefrorener Stand, geschrieben ausschließlich von der Release-Stufe.
4. **Fremdes bleibt als Fremdes markiert.** Belluna-Modelle sind vermessene
   Rekonstruktionen; ihr Manifest pinnt sogar den SHA-256 der Quelldatei.
5. **Doku kann nicht veralten.** `tests/test_documentation.py` erzwingt
   intakte Links, aktuelle Einstiegspunkte und den aktuellen Parameterstand
   in README und Projektstatus.

Einsortierregel für neue Dateien: „Ist es Eingabe, Code, Wissen oder
Ergebnis?" beantwortet fast immer allein, wohin sie gehört.

## Offene Punkte und Historie

- Offene Arbeitspunkte: [`docs/project-status.md`](docs/project-status.md)
  (testgesichert aktuell; `TODO.md` in der Wurzel ist ein Symlink darauf).
- Projekthistorie: [`docs/archive/logbook.md`](docs/archive/logbook.md)
  sowie die SDD-Ledger unter `docs/archive/` (nicht normativ; `LOGBOOK.md`
  in der Wurzel ist ein Symlink darauf).

## Dokumentation

- [Dokumentationsindex](docs/README.md)
- [Aktuelles Design](docs/design.md)
- [Pipeline und Artefakte](docs/pipeline.md)
- [Nachweise und Freigabestatus](docs/verification.md)
- [Klebe-, Schraub- und Dachlastpfade](docs/load-paths.md)
- [CFD-Modell und Windlasten](docs/cfd.md)
- [Generator der Montageanleitung](docs/assembly-manual.md)
- [Referenz- und Datenblattkatalog](references/README.md)

## Grundregel

Jede geometriewirksame Änderung erhöht `Params.GEOM_REV`. Jede Änderung an
Parametern verändert den achtstelligen Parameter-Hash. Kein Fertigungsfile
gilt ohne zugehörigen Report und SHA-256-Manifest als nachvollziehbar.
