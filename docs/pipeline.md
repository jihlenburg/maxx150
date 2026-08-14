# Pipeline und Artefakte

## Datenfluss

```text
params.py
   ├─ model/ ── DFM ── FEM + Analytik ── export/ ── build/engineering/<hash>/
   ├─ reference_models/ + model/ ── Passung ─────── build/analysis/fit/<hash>/
   ├─ Lasten + Verbindungsannahmen ─────────────── build/analysis/load_paths/<hash>/
   ├─ Belluna-Anleitung + Dach ── OpenFOAM ──────── build/analysis/cfd/<cfd-hash>/
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
| `engineering` | Rahmen, Segmente, DFM, vier globale Lastfälle, Stoßmodell, Analytik, Export; ruft danach `connections` auf | Reports dürfen nicht `FAIL` sein |
| `connections` | obere Acht-Schrauben-Gruppe, 2×10-mm-Dachraupe, acht nicht angerechnete untere Seitenschrauben, 2K-Epoxid/ein M5 je Stoß und Holzrahmen–Dachsandwich | `PASS_ASSUMPTION_BASED`; JSON + Markdown |
| `fit` | Belluna-Rekonstruktion gegen Adapter | Kollision, Radialspiel, Auflage, Schraubpfade |
| `cfd` | Aerohüllmodell, `snappyHexMesh`, stationäres RANS und Kräfteauswertung | vorläufige Kräfte/Momente; derzeit kein Release-Gate |
| `render` | Standardansichten und Schnitte | PNG + Render-STL |
| `heatmap` | Knotenspannungen und Hotspots aller Lastfälle | PLY, JSON und PNG |
| `manual` | 15 Montageszenen, HTML und PDF | 15 PNGs in 1500×1125, aktueller Hash und exakt 12 A4-Seiten |
| `references` | Belluna-Rekonstruktion als STEP/STL | separates Provenienz-/Dateimanifest |
| `release` | geprüfte Universaldatei + Report + Fit-Summary nach `release/current` | aktueller Quellcommit, Report-SHA256 und Fit-PASS |

`python3 -m pipeline all` führt die Stufen in dieser Reihenfolge aus;
`connections` läuft dabei nicht als eigene Stufe, sondern wird von
`engineering` und `cfd` mit aufgerufen. Die
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
├── analysis/load_paths/<hash>/
├── analysis/cfd/<cfd-hash>/
├── analysis/heatmap/<hash>/
├── render/<hash>/
├── documentation/<hash>/
└── tests/
```

`MAXX150_BUILD_ROOT` kann für CI oder isolierte Versuche gesetzt werden. Der
frühere Ausgabeordner `out/` aus der Zeit vor der Konsolidierung wurde bei der
Repo-Aufräumung entfernt; der `.gitignore`-Eintrag bleibt als Schutz bestehen,
keine aktuelle Pipeline-Stufe liest oder schreibt ihn.

## Werkzeugversionen

Der aktuell geprüfte lokale Stack ist FreeCAD 1.1.1, Blender 5.1, OpenFOAM
v2606 und Google Chrome Headless. `bin/fc` akzeptiert über `FREECAD_BUNDLE`
eine alternative FreeCAD-App. `BLENDER_BIN` überschreibt den Blender-Pfad.
Die CFD-Stufe verwendet den `openfoam`-Wrapper aus `PATH`.

Die Release-Stufe erfasst die tatsächlich vorgefundenen Versionen
maschinenlesbar im `toolchain`-Block von `release/current/manifest.json`
(Manifest-Schema 3) und verweigert die Paketierung, wenn getrackte
Quelldateien uncommittete Änderungen tragen — sonst würde `source_commit`
einen Stand behaupten, dem der Code nicht entspricht. Nicht als Blocker
zählen untracked Dateien sowie die Pfade, die die Pipeline selbst schreibt
(`release/current/`, `references/belluna/models/`), und `messwerte.json`
(Nutzer-Messdaten, die kein Build liest).

## Messwertübernahme

Messwerte werden bewusst nicht automatisch während eines Builds angewendet:

```sh
python3 scripts/apply_measurements.py messwerte.json --dry-run
```

Eine tatsächliche Übernahme verändert `params.py` und erfordert anschließend
mindestens `pipeline test`, `pipeline engineering`, `pipeline fit` und eine
neue Release-Paketierung.
