"""Zentrale Pfade und Artefaktkonventionen des Projekts.

Quellcode schreibt ausschließlich nach ``build/``. Dauerhaft versionierte
Referenzen liegen unter ``references/``; freizugebende Fertigungsdateien unter
``release/current/``. ``MAXX150_BUILD_ROOT`` erlaubt isolierte CI-/Testläufe.
"""
from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BUILD_ROOT = Path(os.environ.get("MAXX150_BUILD_ROOT", ROOT / "build")).resolve()
REFERENCES_ROOT = ROOT / "references"
RELEASE_ROOT = ROOT / "release"
# Chrome-Headless fuer die PDF-Erzeugung. Doctor-Stufe und Werkzeugversions-
# Erfassung teilen sich diese Definition; montage/build_pdf.py haelt fuer den
# Skript-Direktstart eine eigene Kopie desselben Pfads -- bei Aenderungen
# BEIDE Stellen anpassen.
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def engineering_dir(parameter_hash: str) -> Path:
    """Build-Ordner der Konstruktions-/Fertigungsartefakte zum Parameter-Hash."""
    return BUILD_ROOT / "engineering" / parameter_hash


def render_dir(parameter_hash: str) -> Path:
    """Build-Ordner der Konstruktionsrenderings zum Parameter-Hash."""
    return BUILD_ROOT / "render" / parameter_hash


def heatmap_dir(parameter_hash: str) -> Path:
    """Build-Ordner der FEM-Heatmaps zum Parameter-Hash."""
    return BUILD_ROOT / "analysis" / "heatmap" / parameter_hash


def fit_dir(parameter_hash: str) -> Path:
    """Build-Ordner des digitalen Belluna-Passungschecks zum Parameter-Hash."""
    return BUILD_ROOT / "analysis" / "fit" / parameter_hash


def cfd_dir(cfd_hash: str) -> Path:
    """Build-Ordner eines einzelnen CFD-Falls (Geometrie + Fall) zum CFD-Hash."""
    return BUILD_ROOT / "analysis" / "cfd" / cfd_hash


def cfd_matrix_dir(matrix_hash: str) -> Path:
    """Build-Ordner der ausgewerteten CFD-Fallmatrix zum Matrix-Hash."""
    return BUILD_ROOT / "analysis" / "cfd" / "matrix" / matrix_hash


def load_path_dir(parameter_hash: str) -> Path:
    """Build-Ordner der Lastpfadabschätzung zum Parameter-Hash."""
    return BUILD_ROOT / "analysis" / "load_paths" / parameter_hash


def manual_dir(parameter_hash: str) -> Path:
    """Build-Ordner der Montage-/Dokumentationsdateien zum Parameter-Hash."""
    return BUILD_ROOT / "documentation" / parameter_hash


def tests_dir(name: str = "") -> Path:
    """Build-Ordner für Testartefakte (optionaler Unterordner name)."""
    base = BUILD_ROOT / "tests"
    return base / name if name else base


def current_release_dir() -> Path:
    """Verzeichnis der aktuell freigegebenen Fertigungsdateien (release/current)."""
    return RELEASE_ROOT / "current"
