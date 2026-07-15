"""Konsistenzpruefungen fuer die aktuelle, normative Dokumentation."""
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CURRENT_DOCS = [
    ROOT / "README.md",
    ROOT / "CLAUDE.md",
    ROOT / "references" / "README.md",
    *sorted((ROOT / "docs").glob("*.md")),
    *sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md")),
]
LINK = re.compile(r"!?\[[^]]*\]\(([^)]+)\)")
FORBIDDEN = (
    "run_all.py",
    "scripts/render.sh",
    "scripts/heatmap.sh",
    "scripts/montageanleitung.sh",
    "out/montage",
)


def _relative_links(path):
    for raw in LINK.findall(path.read_text(encoding="utf-8")):
        target = raw.strip().strip("<>").split("#", 1)[0]
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        yield target


def test_aktuelle_dokumentation_hat_keine_toten_relativlinks():
    broken = []
    for document in CURRENT_DOCS:
        for target in _relative_links(document):
            if not (document.parent / target).resolve().exists():
                broken.append(f"{document.relative_to(ROOT)} -> {target}")
    assert not broken, "Tote Dokumentationslinks: " + ", ".join(broken)


def test_aktuelle_dokumentation_nennt_keine_alten_einstiegspunkte():
    hits = []
    for document in CURRENT_DOCS:
        text = document.read_text(encoding="utf-8")
        for obsolete in FORBIDDEN:
            if obsolete in text:
                hits.append(f"{document.relative_to(ROOT)}: {obsolete}")
    assert not hits, "Veraltete Einstiegspunkte: " + ", ".join(hits)
