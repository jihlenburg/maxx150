#!/bin/sh
# Montageanleitung-Pipeline: FreeCAD baut die Szenen-STLs + Manifest, Blender
# rendert die 14 Schrittbilder, python3/Chrome erzeugt die PDF.
#
# Aufruf: scripts/montageanleitung.sh
#
# Marker-Zeilen im Log:
#   MONTAGE-STL-ENDE: <stl_dir>   (FreeCAD-Stufe fertig)
#   RENDER-ENDE                   (Blender-Stufe fertig)
#   PDF-ENDE: <pfad>              (PDF erzeugt)
#
# Voraussetzungen: bin/fc (FreeCAD), blender im PATH (oder BLENDER_BIN),
# Google Chrome (Headless-PDF). Alle Stufen sind idempotent -- Wiederholen
# überschreibt out/montage/* und out/montageanleitung_<hash>.pdf sauber.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BLENDER_BIN="${BLENDER_BIN:-$(command -v blender)}"
STL_DIR="$ROOT/out/montage/stl"
IMG_DIR="$ROOT/out/montage/img"

echo "== 1/3 FreeCAD: Szenen-STLs + Manifest (bin/fc montage/build_stls.py) =="
"$ROOT/bin/fc" "$ROOT/montage/build_stls.py"

echo "== 2/3 Blender: 14 Schrittbilder (montage/render_steps.py) =="
"$BLENDER_BIN" -b -P "$ROOT/montage/render_steps.py" -- "$STL_DIR" "$IMG_DIR"

echo "== 3/3 PDF: HTML + Chrome-Headless (montage/build_pdf.py) =="
python3 "$ROOT/montage/build_pdf.py"

echo "Fertig. STLs:   $STL_DIR"
echo "Fertig. Bilder: $IMG_DIR"
echo "Fertig. PDF:    $ROOT/out/ (montageanleitung_<hash>.pdf)"
