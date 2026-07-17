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


def test_readme_und_status_tragen_den_aktuellen_parameterstand():
    """Repo-Aufraeumung 2026-07-16: README und Projektstatus nennen den
    Parameterstand prominent -- dieser Waechter erzwingt, dass beide bei
    jeder Parameteraenderung nachgezogen werden (Hash UND GEOM_REV),
    statt still zu veralten."""
    import sys
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import params as PRM
    hash_ist = PRM.params_hash()
    rev_ist = f"GEOM_REV:** `{PRM.P.GEOM_REV}`"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    status = (ROOT / "docs" / "project-status.md").read_text(encoding="utf-8")
    assert hash_ist in readme, f"README.md: Parameterstand {hash_ist} fehlt"
    assert rev_ist in readme, f"README.md: GEOM_REV {PRM.P.GEOM_REV} fehlt"
    assert hash_ist in status, f"project-status.md: Parameterstand {hash_ist} fehlt"
    assert f"GEOM_REV {PRM.P.GEOM_REV}" in status, \
        f"project-status.md: GEOM_REV {PRM.P.GEOM_REV} fehlt"


def test_aktuelle_dokumentation_nennt_keine_alten_einstiegspunkte():
    hits = []
    for document in CURRENT_DOCS:
        text = document.read_text(encoding="utf-8")
        for obsolete in FORBIDDEN:
            if obsolete in text:
                hits.append(f"{document.relative_to(ROOT)}: {obsolete}")
    assert not hits, "Veraltete Einstiegspunkte: " + ", ".join(hits)
