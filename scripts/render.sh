#!/bin/sh
# Render-Workflow: FreeCAD baut die Render-STLs, Blender rendert die Ansichten.
# Aufruf: scripts/render.sh [out_dir] [ansichten]
#   out_dir     Zielverzeichnis fuer die PNGs (Default: out/render/<hash>,
#               dasselbe Verzeichnis wie die STLs)
#   ansichten   optionale Komma-Liste an render/blender_views.py durchgereicht
#               (Default: alle fuenf Standardansichten)
#
# Schnittebenen ueber Umgebungsvariablen VOR dem Aufruf setzen (siehe
# render/make_views_stl.py, Skill maxx150-pipeline):
#   RENDER_ZCUT=14 RENDER_XCUT=120 scripts/render.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$(mktemp)"

echo "== FreeCAD: Render-STLs (bin/fc render/make_views_stl.py) =="
"$ROOT/bin/fc" "$ROOT/render/make_views_stl.py" | tee "$LOG"

STL_DIR="$(sed -n 's/^RENDER-STL-ENDE: //p' "$LOG" | tail -1)"
if [ -z "$STL_DIR" ]; then
    echo "FEHLER: Render-STL-Verzeichnis nicht im FreeCAD-Log gefunden." >&2
    exit 1
fi

OUT_DIR="${1:-$STL_DIR}"
VIEWS="${2:-}"

echo "== Blender: Ansichten aus $STL_DIR nach $OUT_DIR =="
if [ -n "$VIEWS" ]; then
    /opt/homebrew/bin/blender -b -P "$ROOT/render/blender_views.py" -- "$STL_DIR" "$OUT_DIR" "$VIEWS"
else
    /opt/homebrew/bin/blender -b -P "$ROOT/render/blender_views.py" -- "$STL_DIR" "$OUT_DIR"
fi

echo "Fertig. STLs: $STL_DIR"
echo "Fertig. Ansichten: $OUT_DIR"
