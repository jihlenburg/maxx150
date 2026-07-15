"""Ausführbare FreeCAD-Stufe für den digitalen Passungscheck."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analysis.fit_check import main  # noqa: E402


main()
