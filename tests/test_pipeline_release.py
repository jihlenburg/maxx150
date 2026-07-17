"""Pure Provenienzpruefungen des Release-Packagers."""
import hashlib

from pipeline.checks import toolchain_versions
from pipeline.release import (_dirty_paths, _release_status,
                              _report_provenance, _verify_reported_file)
from project_paths import tests_dir


def test_report_provenienz_wird_extrahiert():
    digest = "a" * 64
    text = (
        "Git-Commit: `1234567890abcdef` · GEOM_REV: `6`\n\n"
        "| Datei | SHA256 |\n|---|---|\n"
        f"| teil.step | `{digest}` |\n"
    )
    commit, files = _report_provenance(text)
    assert commit == "1234567890abcdef"
    assert files == {"teil.step": digest}


def test_toolchain_versionen_werden_erfasst():
    """Release-Manifest-Provenienz (Review-Punkt 'Werkzeugversionen'):
    stabile Schluessel; die FreeCAD-Version muss auf dieser Maschine real
    ermittelbar sein, die uebrigen duerfen defensiv auf 'nicht ermittelbar'
    fallen, aber nie fehlen oder leer sein."""
    versionen = toolchain_versions()
    assert set(versionen) == {"freecad", "blender", "openfoam", "chrome",
                              "pdfinfo"}
    assert "FreeCAD" in versionen["freecad"]
    assert all(isinstance(v, str) and v for v in versionen.values())


def test_dirty_paths_ignoriert_pipeline_und_nutzerdaten_pfade():
    """Der Release-Dirty-Guard darf weder die von der Pipeline selbst
    geschriebenen getrackten Pfade noch messwerte.json (Nutzerdaten, kein
    Build-Input) noch untracked Dateien als Blocker werten -- wohl aber jede
    andere getrackte Aenderung, auch als Rename."""
    porcelain = (
        " M pipeline/release.py\n"
        "?? notizen.md\n"
        " M messwerte.json\n"
        " M release/current/manifest.json\n"
        " M references/belluna/models/manifest.json\n"
        "R  altname.py -> model/neuname.py\n"
    )
    assert _dirty_paths(porcelain) == ["pipeline/release.py", "model/neuname.py"]
    assert _dirty_paths("") == []
    assert _dirty_paths(" M messwerte.json\n") == []


def test_release_status_wird_strikt_abgeleitet():
    """Die drei bekannten Gesamtergebnis-Varianten aus fem/report.py werden
    exakt abgebildet; fehlende oder umformulierte Banner duerfen NIE still zu
    RELEASED werden, sondern brechen ab."""
    assert _release_status("# Gesamtergebnis: **PASS**\n") == "RELEASED"
    assert _release_status(
        "# Gesamtergebnis: **PASS mit Vorbehalt** (offene Gates)\n"
    ) == "PROTOTYPE_ONLY"
    for text in ("# Gesamtergebnis: **FAIL**\n",
                 "# Gesamtergebnis: **PASS mit Vorbehalten**\n",
                 "Report ohne Banner\n"):
        try:
            _release_status(text)
        except RuntimeError:
            continue
        raise AssertionError(f"RuntimeError erwartet fuer {text!r}")


def test_report_hash_wird_gegen_datei_geprueft():
    path = tests_dir("pipeline_release") / "teil.stl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"stl")
    digest = hashlib.sha256(b"stl").hexdigest()
    _verify_reported_file(path, {path.name: digest})
