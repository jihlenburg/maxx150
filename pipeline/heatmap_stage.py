"""FreeCAD-Einstiegspunkt für den Heatmap-Workflow.

Wird von ``python3 -m pipeline heatmap`` aufgerufen. Das Skript bleibt ohne
CLI-Parsing, weil die Argumentweitergabe von freecadcmd unzuverlässig ist.

Direktaufruf: bin/fc pipeline/heatmap_stage.py
Laufzeit: mehrere Minuten (4 Lastfaelle x Gmsh+CalculiX, Produktionsnetz)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fem.heatmap import heatmap_all

heatmap_all()
