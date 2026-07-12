"""FreeCAD-Einstiegspunkt fuer den Heatmap-Workflow: ruft
fem.heatmap.heatmap_all() mit den aktuellen Parametern auf. Straight-line-
Skript ohne CLI-Parsing (freecadcmd-argv ist unzuverlaessig, wie run_all.py).

Aufruf: bin/fc scripts/heatmap_run.py
Laufzeit: mehrere Minuten (4 Lastfaelle x Gmsh+CalculiX, Produktionsnetz)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fem.heatmap import heatmap_all

heatmap_all()
