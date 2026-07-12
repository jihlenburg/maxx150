#!/bin/sh
# Heatmap-Workflow: FEM je Lastfall (bin/fc) -> PLY (Viridis) -> Blender-
# Rendering hintereinander. Aufruf: scripts/heatmap.sh
#
# ACHTUNG Laufzeit: 4 Lastfaelle x Gmsh+CalculiX auf dem Produktionsnetz --
# mehrere Minuten. Fuer einen Smoke-Test lieber direkt
# fem.heatmap.heatmap_all(mesh_mm=<grob>) mit Grobnetz aufrufen.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$(mktemp)"

echo "== FreeCAD + CalculiX: Heatmap je Lastfall (bin/fc scripts/heatmap_run.py) =="
"$ROOT/bin/fc" "$ROOT/scripts/heatmap_run.py" | tee "$LOG"

SUMMARY="$(sed -n 's/^HEATMAP-ENDE: //p' "$LOG" | tail -1)"
if [ -z "$SUMMARY" ]; then
    echo "FEHLER: Heatmap-Zusammenfassung nicht im FreeCAD-Log gefunden." >&2
    exit 1
fi
OUT_DIR="$(dirname "$SUMMARY")"

echo "== Blender: Heatmap-Renderings aus $OUT_DIR =="
/opt/homebrew/bin/blender -b -P "$ROOT/render/blender_heatmap.py" -- "$OUT_DIR" "$OUT_DIR"

echo "Fertig. Renderings: $OUT_DIR"
