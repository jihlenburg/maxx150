# Pipeline und Artefakte

## Datenfluss

```text
params.py
   ├─ model/ ── DFM ── FEM + Analytik ── export/ ── build/engineering/<hash>/
   ├─ reference_models/ + model/ ── Passung ─────── build/analysis/fit/<hash>/
   ├─ fem/ ── Spannungsfelder ── Blender ───────── build/analysis/heatmap/<hash>/
   ├─ model/ ── Blender ────────────────────────── build/render/<hash>/
   └─ model/ + Belluna + Dach ── Blender ── PDF ─ build/documentation/<hash>/
                                                        │
                               explizite Paketierung ───┴─ release/current/
```

## Kanonische Stufen

| Stufe | Inhalt | Gate/Ergebnis |
|---|---|---|
| `doctor` | FreeCAD, Blender, Chrome, pdfinfo und Pfade | bricht bei fehlendem Werkzeug ab |
| `test` | Geometrie-, FEM-, Export-, Referenz- und Toolchaintests | alle Tests müssen bestehen |
| `engineering` | Rahmen, Segmente, DFM, vier globale Lastfälle, Stoßmodell, Analytik, Export | Report darf nicht `FAIL` sein |
| `fit` | Belluna-Rekonstruktion gegen Adapter | Kollision, Radialspiel, Auflage, Schraubpfade |
| `render` | Standardansichten und Schnitte | PNG + Render-STL |
| `heatmap` | Knotenspannungen und Hotspots aller Lastfälle | PLY, JSON und PNG |
| `manual` | 14 Montageszenen, HTML und PDF | 14 PNGs in 1500×1125, aktueller Hash und exakt 10 A4-Seiten |
| `references` | Belluna-Rekonstruktion als STEP/STL | separates Provenienz-/Dateimanifest |
| `release` | geprüfte Universaldatei + Report + Fit-Summary nach `release/current` | aktueller Quellcommit, Report-SHA256 und Fit-PASS |

`python3 -m pipeline all` führt die Stufen in dieser Reihenfolge aus. Die
Heatmap berechnet die Lastfälle bewusst erneut, weil sie rohe Knotenspannungen
benötigt; der Engineering-Report verwendet aggregierte Ergebnisgrößen.
Die Release-Stufe akzeptiert keine Engineering-Dateien aus einem älteren
Commit und verifiziert STEP/STL erneut gegen das Dateimanifest im Report.

## Verzeichnisvertrag

Generierter Inhalt wird nie anhand eines „neuesten“ Dateinamens gesucht,
sondern stets über den Parameter-Hash:

```text
build/
├── engineering/<hash>/
├── analysis/fit/<hash>/
├── analysis/heatmap/<hash>/
├── render/<hash>/
├── documentation/<hash>/
└── tests/
```

`MAXX150_BUILD_ROOT` kann für CI oder isolierte Versuche gesetzt werden. Der
alte lokale Ordner `out/` ist nur noch eine ignorierte historische Ablage und
wird von keiner aktuellen Pipeline-Stufe gelesen.

## Werkzeugversionen

Der aktuell geprüfte lokale Stack ist FreeCAD 1.1.1, Blender 5.1 und Google
Chrome Headless. `bin/fc` akzeptiert über `FREECAD_BUNDLE` eine alternative
FreeCAD-App. `BLENDER_BIN` überschreibt den Blender-Pfad.

## Messwertübernahme

Messwerte werden bewusst nicht automatisch während eines Builds angewendet:

```sh
python3 scripts/apply_measurements.py messwerte.json --dry-run
```

Eine tatsächliche Übernahme verändert `params.py` und erfordert anschließend
mindestens `pipeline test`, `pipeline engineering`, `pipeline fit` und eine
neue Release-Paketierung.
