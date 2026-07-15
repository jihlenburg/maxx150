"""Schnelle Tests fuer die Artefakt-Abnahmekriterien der zentralen Pipeline."""
import struct

from pipeline.checks import parse_pdfinfo_pages, png_dimensions


def test_pdfinfo_seitenzahl_wird_strikt_gelesen():
    assert parse_pdfinfo_pages("Title: Test\nPages:           10\nEncrypted: no\n") == 10


def test_png_dimensionen_werden_ohne_bildbibliothek_gelesen():
    from project_paths import tests_dir

    path = tests_dir("pipeline_checks") / "header.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR"
        + struct.pack(">II", 1500, 1125)
    )
    assert png_dimensions(path) == (1500, 1125)
