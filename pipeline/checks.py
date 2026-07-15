"""Maschinenlesbare Abnahmekriterien fuer erzeugte Dokumentationsartefakte."""
from __future__ import annotations

import json
import re
import shutil
import struct
import subprocess
from pathlib import Path

import params as PRM


EXPECTED_MANUAL_IMAGES = (
    "01_titel_explosion.png",
    "02_teile_uebersicht.png",
    "03_fuegeflaechen.png",
    "04_kleber_aktivator.png",
    "05_m5_montage.png",
    "06_m5_mutter.png",
    "07_rahmen_komplett.png",
    "08_maskierung_lack.png",
    "09_dach_holzrahmen.png",
    "10_aufsetzen.png",
    "11_dachschrauben.png",
    "12_kleberaupe.png",
    "13_platte_schrauben.png",
    "14_fertig.png",
)
MANUAL_IMAGE_SIZE = (1500, 1125)
MANUAL_PAGE_COUNT = 10


def png_dimensions(path: Path) -> tuple[int, int]:
    """Liest Breite und Hoehe direkt aus dem PNG-IHDR, ohne Pillow."""
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Kein gueltiges PNG: {path}")
    return struct.unpack(">II", header[16:24])


def parse_pdfinfo_pages(output: str) -> int:
    match = re.search(r"^Pages:\s+(\d+)\s*$", output, re.MULTILINE)
    if not match:
        raise ValueError("pdfinfo-Ausgabe enthaelt keine Seitenzahl")
    return int(match.group(1))


def pdf_page_count(path: Path) -> int:
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        raise RuntimeError("pdfinfo fehlt; Poppler installieren")
    result = subprocess.run(
        [pdfinfo, str(path)], check=True, capture_output=True, text=True
    )
    return parse_pdfinfo_pages(result.stdout)


def validate_manual(target: Path) -> None:
    """Verhindert still unvollstaendige oder umgebrochene Montage-PDFs."""
    h = PRM.params_hash(PRM.P)
    manifest_path = target / "manifest.json"
    html_path = target / f"montageanleitung_{h}.html"
    pdf_path = target / f"montageanleitung_{h}.pdf"
    required = (manifest_path, html_path, pdf_path)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Montageartefakte fehlen: " + ", ".join(missing))

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("params_hash") != h:
        raise ValueError(
            f"Montagemanifest hat Hash {manifest.get('params_hash')!r}, erwartet {h!r}"
        )

    img_dir = target / "img"
    missing_images = [name for name in EXPECTED_MANUAL_IMAGES if not (img_dir / name).is_file()]
    if missing_images:
        raise FileNotFoundError("Montagebilder fehlen: " + ", ".join(missing_images))
    sizes = {name: png_dimensions(img_dir / name) for name in EXPECTED_MANUAL_IMAGES}
    wrong_sizes = {name: size for name, size in sizes.items() if size != MANUAL_IMAGE_SIZE}
    if wrong_sizes:
        raise ValueError(f"Unerwartete Bildgroessen: {wrong_sizes}")

    pages = pdf_page_count(pdf_path)
    if pages != MANUAL_PAGE_COUNT:
        raise ValueError(
            f"Montage-PDF hat {pages} Seiten, erwartet {MANUAL_PAGE_COUNT}; "
            "Druck-CSS oder Inhalt pruefen"
        )
    print(
        f"MONTAGE-CHECK: {len(EXPECTED_MANUAL_IMAGES)} Bilder "
        f"{MANUAL_IMAGE_SIZE[0]}x{MANUAL_IMAGE_SIZE[1]}, {pages} A4-Seiten, Hash {h}",
        flush=True,
    )
