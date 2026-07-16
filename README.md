# Belluna-Super-Fan-Adapter für den Challenger X150

Parametrisches FreeCAD-Modell eines 28-mm-Adapterrahmens für den Belluna Super
Fan im vorhandenen 400×400-mm-Dachausschnitt. Das Bauteil besteht aus vier
rotationsidentischen L-Segmenten und wird als ein Universalteil mit Stückzahl
vier bereitgestellt.

## Projektstatus

**Aktueller Parameterstand:** `83aeba39` · **GEOM_REV:** `6`
**Freigabestatus:** `PROTOTYPE_ONLY`

Geometrie-, DFM-, FEM-, analytische, Lastpfad- und digitale Passungsnachweise
sind Teil der Pipeline. Eine Produktionsfreigabe besteht trotzdem noch nicht:
Nicht verfügbare Werkstoff-/Haftversuche sind durch stark abgeminderte,
quellenbasierte Annahmen ersetzt (`PASS_ASSUMPTION_BASED`); endgültiger
Dachausschnitt, Schraubeneinbindung und Holzrahmen bleiben beim Einbau zu
kontrollieren. Die Dateien unter
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
