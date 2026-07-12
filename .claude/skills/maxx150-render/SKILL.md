---
name: maxx150-render
description: Rendern/Visualisieren des Adapterrahmens (Ansichten, Explosion, Schnittbild, Heatmap-PNGs). Trigger — Nutzer bittet um "rendern", "Schnittbild", "Explosion", "Ansicht/Rendering zeigen" oder "Heatmap"/"Spannungsbild".
---

# maxx150-Render

Zwei getrennte Seiten pro Workflow: **FreeCAD baut die Geometrie-STLs/PLYs**,
**Blender rendert die PNGs**. Orchestrierung über `scripts/*.sh`. Voraussetzung:
`maxx150-pipeline`-Konventionen (bin/fc, argv-Fallstricke) gelten hier genauso.

## Standard-Rendering: scripts/render.sh

```sh
scripts/render.sh                       # alle 5 Ansichten, Standardpfade
scripts/render.sh out/mein_ordner        # eigenes Zielverzeichnis
scripts/render.sh out/mein_ordner iso_oben   # nur EINE Ansicht (Smoke-Test)
RENDER_ZCUT=10 RENDER_XCUT=150 scripts/render.sh   # andere Schnittebenen
```

Ablauf: `bin/fc render/make_views_stl.py` baut/lädt Rahmen + 4 Segmente +
Horizontal-/Vertikalschnitt als STL nach `out/render/<params_hash>/`
(lädt vorhandene `out/frame_<hash>.step`/`seg{k}_<hash>.step`, sonst frischer
Bau aus `params.P` — dauert dann Minuten). Danach
`blender -b -P render/blender_views.py -- <stl_dir> <out_dir> [ansichten]`.

**Ansichtsnamen** (Dateien `v_<name>.png`):
- `iso_oben` — Rahmen montiert, Isoansicht von oben.
- `iso_unten` — Isoansicht von unten (Noppen, Rille, Fase, Muttertaschen).
- `explosion` — 4 Segmente radial auseinandergezogen.
- `einzelteil` — Nahaufnahme Segment 0 (Lap-Enden, M5-Senkung, Vents).
- `schnitt` — Vertikalschnitt bei `RENDER_XCUT` (Default 120), Schnittfläche
  orange markiert.

**Kamerakonventionen**: Cycles, 96 Samples (Heatmap: 64), 1500x1125 px,
dunkler neutraler Hintergrund (kein Studio-Weiß). Segmente alternierend hell/
bläulich getönt (`seg0`/`seg2` hell, `seg1`/`seg3` bläulich) — macht die
Stoßfugen in der Isoansicht sichtbar. Kamera trackt per `TRACK_TO`-Constraint
auf ein leeres `Target`-Objekt statt fester Rotation.

## Heatmap-Rendering: scripts/heatmap.sh

```sh
scripts/heatmap.sh
```

Ablauf: `bin/fc scripts/heatmap_run.py` → `fem.heatmap.heatmap_all()` — führt
**alle 4 Lastfälle mit Produktionsnetz** (Gmsh+CalculiX) aus, schreibt
`out/heatmap/heat_<Lastfall>.ply` (Viridis-Vertexfarben, auf das
Fall-Maximum normiert) + `out/heatmap/heat_summary.json`
(`vm_max` + bis zu 6 Hotspots je Fall mit Bauteilzone). **Laufzeit: mehrere
Minuten** — als Hintergrundprozess starten (siehe `maxx150-pipeline`), nicht
im Vordergrund warten. Danach
`blender -b -P render/blender_heatmap.py -- <ply_dir> <out_dir>` — pro
Lastfall zwei PNGs `hm_<Lastfall>_oben.png` / `hm_<Lastfall>_unten.png`
(Hotspots sitzen laut Task-15-Analyse typischerweise UNTEN, an den
Noppenfüßen — beide Ansichten immer rendern, nicht nur oben).

Für einen schnellen Funktionstest (keine 10-minütige Vollpipeline) direkt
`fem.heatmap.heatmap_all(mesh_mm=PRM.P.MESH_MM_TEST, out_dir=...)` mit nur
einem Lastfall aufrufen (`fem.loadcases.CASES` temporär auf einen Eintrag
reduzieren) statt `scripts/heatmap.sh`.

## Wohin die Ausgaben gehen

- Render-STLs: `out/render/<params_hash>/{frame,seg0..3,frame_zcut,frame_xcut}.stl`
- Render-PNGs: dasselbe Verzeichnis (Default) oder das an `scripts/render.sh`
  übergebene `out_dir`.
- Heatmap-PLY/JSON: `out/heatmap/` (Default von `heatmap_all()`).
- Heatmap-PNGs: dasselbe Verzeichnis (Default) oder das zweite Argument von
  `render/blender_heatmap.py`.

## Ergebnis an den Nutzer zurückspielen

PNGs liegen unter `out/` (gitignored, nicht Teil des Commits) — dem Nutzer
NIE nur den Dateipfad nennen, sondern das Bild aktiv mit dem Read-Tool laden
(zeigt es inline im Gespräch an), sonst sieht er das Ergebnis nicht. Bei
mehreren Ansichten in einer Antwort: kurze Beschriftung je Bild (welche
Ansicht, welcher Lastfall/welche Schnittebene).
