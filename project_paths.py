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


def engineering_dir(parameter_hash: str) -> Path:
    return BUILD_ROOT / "engineering" / parameter_hash


def render_dir(parameter_hash: str) -> Path:
    return BUILD_ROOT / "render" / parameter_hash


def heatmap_dir(parameter_hash: str) -> Path:
    return BUILD_ROOT / "analysis" / "heatmap" / parameter_hash


def fit_dir(parameter_hash: str) -> Path:
    return BUILD_ROOT / "analysis" / "fit" / parameter_hash


def cfd_dir(cfd_hash: str) -> Path:
    return BUILD_ROOT / "analysis" / "cfd" / cfd_hash


def cfd_matrix_dir(matrix_hash: str) -> Path:
    return BUILD_ROOT / "analysis" / "cfd" / "matrix" / matrix_hash


def manual_dir(parameter_hash: str) -> Path:
    return BUILD_ROOT / "documentation" / parameter_hash


def tests_dir(name: str = "") -> Path:
    base = BUILD_ROOT / "tests"
    return base / name if name else base


def current_release_dir() -> Path:
    return RELEASE_ROOT / "current"
