"""export/manifest.py::append_manifest (Finalreview I1, Task 16 Block 2)."""
import re
import subprocess

import params as PRM
from export.manifest import append_manifest
from project_paths import tests_dir

OUT = tests_dir("manifest")


def _fake_report_und_dateien():
    OUT.mkdir(parents=True, exist_ok=True)
    report = OUT / "report.md"
    report.write_text("# Verifikationsreport\n\n# Gesamtergebnis: **PASS**\n",
                      encoding="utf-8")
    f1 = OUT / "a.step"
    f1.write_text("fake-step-inhalt-a", encoding="utf-8")
    f2 = OUT / "b.stl"
    f2.write_text("fake-stl-inhalt-b", encoding="utf-8")
    return report, [f1, f2]


def test_manifest_sektion_hashes_und_commit():
    report, files = _fake_report_und_dateien()
    append_manifest(str(report), files, git_rev="deadbeef1234567")

    text = report.read_text(encoding="utf-8")
    assert "# Gesamtergebnis: **PASS**" in text          # ursprünglicher Report bleibt erhalten
    assert "## Datei-Manifest" in text
    assert "deadbeef1234567" in text
    assert f"GEOM_REV: `{PRM.P.GEOM_REV}`" in text
    assert "a.step" in text and "b.stl" in text

    hashes = re.findall(r"`([0-9a-f]{64})`", text)
    assert len(hashes) == 2, f"erwarte 2 SHA256-Hashes, gefunden: {hashes}"


def test_manifest_hash_stimmt_mit_inhalt_ueberein():
    import hashlib
    report, files = _fake_report_und_dateien()
    append_manifest(str(report), files, git_rev="cafef00d")

    text = report.read_text(encoding="utf-8")
    for f in files:
        erwartet = hashlib.sha256(f.read_bytes()).hexdigest()
        assert erwartet in text, f"SHA256 von {f.name} fehlt/stimmt nicht: {erwartet}"


def test_manifest_git_rev_wird_wortwoertlich_uebernommen():
    # append_manifest ruft git NICHT selbst auf (git_rev ist Pflichtparameter
    # vom Aufrufer, siehe pipeline/engineering.py) -- Beleg, dass der übergebene Wert
    # unverändert im Report landet (kein eigenes git rev-parse in manifest.py).
    report, files = _fake_report_und_dateien()
    echter_head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                 text=True, check=True).stdout.strip()
    fake_rev = "0" * 40
    assert fake_rev != echter_head
    append_manifest(str(report), files, git_rev=fake_rev)
    text = report.read_text(encoding="utf-8")
    assert fake_rev in text
    assert echter_head not in text
