"""Pure Provenienzpruefungen des Release-Packagers."""
import hashlib

from pipeline.release import _report_provenance, _verify_reported_file
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


def test_report_hash_wird_gegen_datei_geprueft():
    path = tests_dir("pipeline_release") / "teil.stl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"stl")
    digest = hashlib.sha256(b"stl").hexdigest()
    _verify_reported_file(path, {path.name: digest})
