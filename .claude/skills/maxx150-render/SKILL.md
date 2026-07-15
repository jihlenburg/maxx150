---
name: maxx150-render
description: Renderings, Schnittansichten, Montagebilder oder FEM-Heatmaps des maxx150-Adapters erzeugen.
---

# maxx150-Render

Standardansichten mit `python3 -m pipeline render`, Heatmaps mit
`python3 -m pipeline heatmap`, Montagebilder und PDF mit
`python3 -m pipeline manual` erzeugen.

Ausgaben liegen immer hash-segregiert:

- `build/render/<hash>/`
- `build/analysis/heatmap/<hash>/`
- `build/documentation/<hash>/`

`MAXX150_RENDER_VIEWS` begrenzt Standardansichten; `RENDER_ZCUT` und
`RENDER_XCUT` setzen Schnittebenen. Montage-Einzelbilder lassen sich mit
`ONLY_IMG=04,09` beschränken. Zwischenbilder werden zusätzlich nach
`~/Downloads/Belluna-Render-Zwischenstand/` kopiert.

FreeCAD erzeugt Geometrie/PLY, Blender rendert. Diese Trennung und die
Manifest-Schnittstellen nicht umgehen.
