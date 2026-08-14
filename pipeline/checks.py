"""Maschinenlesbare Abnahmekriterien fuer erzeugte Dokumentationsartefakte."""
from __future__ import annotations

import json
import re
import shutil
import struct
import subprocess
from pathlib import Path

import os

import params as PRM
from project_paths import CHROME, ROOT


EXPECTED_MANUAL_IMAGES = (
    "01_titel_explosion.png",
    "02_teile_uebersicht.png",
    "03_fuegeflaechen.png",
    "04_kleber_auftrag.png",
    "05_m5_montage.png",
    "06_m5_mutter.png",
    "07_rahmen_komplett.png",
    "08_maskierung_lack.png",
    "09_dach_holzrahmen.png",
    "10_aufsetzen.png",
    "11_hybrid_dachinterface.png",
    "12_kleberaupe.png",
    "13_aussenkehle.png",
    "14_platte_schrauben.png",
    "15_fertig.png",
)
MANUAL_IMAGE_SIZE = (1500, 1125)
MANUAL_PAGE_COUNT = 12


def png_dimensions(path: Path) -> tuple[int, int]:
    """Liest Breite und Hoehe direkt aus dem PNG-IHDR, ohne Pillow."""
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Kein gueltiges PNG: {path}")
    return struct.unpack(">II", header[16:24])


def parse_pdfinfo_pages(output: str) -> int:
    """Zieht die Seitenzahl aus einer ``pdfinfo``-Ausgabe (Zeile ``Pages: N``);
    wirft, wenn keine vorkommt."""
    match = re.search(r"^Pages:\s+(\d+)\s*$", output, re.MULTILINE)
    if not match:
        raise ValueError("pdfinfo-Ausgabe enthaelt keine Seitenzahl")
    return int(match.group(1))


def pdf_page_count(path: Path) -> int:
    """Seitenzahl eines PDF via ``pdfinfo`` (Poppler muss im PATH liegen)."""
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        raise RuntimeError("pdfinfo fehlt; Poppler installieren")
    result = subprocess.run(
        [pdfinfo, str(path)], check=True, capture_output=True, text=True
    )
    return parse_pdfinfo_pages(result.stdout)


def _version_line(cmd: list[str], pattern: str | None = None,
                  timeout: float = 30.0) -> str:
    """Erste Ausgabezeile eines Versionskommandos, defensiv erfasst; bei jedem
    Fehler (fehlendes Binary, Exit-Code != 0, Timeout, kein Treffer)
    ``"nicht ermittelbar"`` -- die Versionserfassung darf einen Release nie
    verhindern, aber auch nie Fehlertext als Version ausgeben. Mit ``pattern``
    zaehlt die erste Regex-Fundstelle in stdout+stderr (ein Treffer ist selbst
    der Beleg, z. B. im openfoam-Hilfetext); ohne ``pattern`` die erste Zeile
    von stdout, ersatzweise stderr (pdfinfo schreibt seine Version dorthin)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=timeout)
        if pattern:
            match = re.search(pattern, result.stdout + result.stderr)
            return match.group(0) if match else "nicht ermittelbar"
        if result.returncode != 0:
            return "nicht ermittelbar"
        output = result.stdout.strip() or result.stderr.strip()
        return output.splitlines()[0].strip() if output else "nicht ermittelbar"
    except Exception:
        return "nicht ermittelbar"


def toolchain_versions() -> dict[str, str]:
    """Best-effort-Erfassung der extern beteiligten Werkzeugversionen fuer
    das Release-Manifest (Provenienz: mit WELCHEM Stack wurde der Stand
    erzeugt?). Schluessel sind stabil; Werte sind Versionszeilen oder
    ``"nicht ermittelbar"`` (Erfassung blockiert nie)."""
    blender = os.environ.get("BLENDER_BIN") or shutil.which("blender")
    openfoam = shutil.which("openfoam")
    pdfinfo = shutil.which("pdfinfo")
    return {
        "freecad": _version_line([str(ROOT / "bin" / "fc"), "--version"]),
        "blender": _version_line([blender, "--version"]) if blender
        else "nicht ermittelbar",
        "openfoam": _version_line([openfoam, "-help"], pattern=r"v\d{4}")
        if openfoam else "nicht ermittelbar",
        "chrome": _version_line([str(CHROME), "--version"]),
        "pdfinfo": _version_line([pdfinfo, "-v"]) if pdfinfo
        else "nicht ermittelbar",
    }


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
