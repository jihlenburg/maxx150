"""Paketiert den verifizierten Engineering-Export nach ``release/current``."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import params as PRM
from pipeline.checks import toolchain_versions
from project_paths import ROOT, current_release_dir, engineering_dir, fit_dir


_REPORT_COMMIT = re.compile(r"Git-Commit: `([0-9a-f]{7,40})`")
_REPORT_FILE = re.compile(r"^\| ([^|]+) \| `([0-9a-f]{64})` \|$", re.MULTILINE)
_REPORT_RESULT = re.compile(r"^# Gesamtergebnis: \*\*([^*]+)\*\*", re.MULTILINE)


def _release_status(report_text: str) -> str:
    """Leitet den Release-Status strikt aus der Gesamtergebnis-Zeile des
    Verifikationsreports ab. ``fem/report.py`` kennt genau drei Varianten
    (PASS, PASS mit Vorbehalt, FAIL); jede fehlende oder unbekannte
    Formulierung bricht ab, statt still RELEASED zu melden."""
    match = _REPORT_RESULT.search(report_text)
    if not match:
        raise RuntimeError("Verifikationsreport enthaelt keine Gesamtergebnis-Zeile")
    result = match.group(1).strip()
    if result == "PASS":
        return "RELEASED"
    if result == "PASS mit Vorbehalt":
        return "PROTOTYPE_ONLY"
    if result == "FAIL":
        raise RuntimeError("FEM-/Analytikreport ist FAIL; Release wird nicht erzeugt")
    raise RuntimeError(
        f"Unbekanntes Gesamtergebnis {result!r}; Release-Status nicht ableitbar"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_revision() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], check=True,
                          capture_output=True, text=True, cwd=ROOT).stdout.strip()


# Getrackte Pfade, deren uncommittete Aenderungen einen Release NICHT blockieren:
# release/current/ und references/belluna/models/ schreibt die Pipeline selbst
# (sonst blockierte jeder erfolgreiche Release- bzw. references-Lauf den
# naechsten), messwerte.json traegt Nutzer-Messdaten, die kein Build liest
# (Uebernahme nur explizit via scripts/apply_measurements.py).
_DIRTY_EXEMPT = ("release/current/", "references/belluna/models/", "messwerte.json")


def _dirty_paths(porcelain: str) -> list[str]:
    """Filtert eine ``git status --porcelain``-Ausgabe auf die Pfade, die einen
    Release wirklich verbieten: getrackte, uncommittete Aenderungen ausserhalb
    von ``_DIRTY_EXEMPT``. Untracked Eintraege (``??``) zaehlen nicht -- sie
    beeinflussen den Inhalt des getrackten Quellstands nicht."""
    dirty = []
    for line in porcelain.splitlines():
        if not line.strip() or line.startswith("??"):
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:  # Rename: neuer Pfad zaehlt
            path = path.split(" -> ", 1)[1].strip().strip('"')
        if not path.startswith(_DIRTY_EXEMPT):
            dirty.append(path)
    return dirty


def _git_dirty() -> list[str]:
    """Getrackte, uncommittete Aenderungen, die den Release-Stand verfaelschen
    wuerden (siehe ``_dirty_paths``). Ein Release aus schmutzigem Baum wuerde
    einen source_commit behaupten, dem der Code nicht entspricht."""
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        check=True, capture_output=True, text=True, cwd=ROOT,
    ).stdout
    return _dirty_paths(status)


def _git_commit_time(revision: str) -> str:
    return subprocess.run(
        ["git", "show", "-s", "--format=%cI", revision], check=True,
        capture_output=True, text=True, cwd=ROOT,
    ).stdout.strip()


def _report_provenance(report_text: str) -> tuple[str, dict[str, str]]:
    commit = _REPORT_COMMIT.search(report_text)
    if not commit:
        raise ValueError("Verifikationsreport enthaelt keinen Quellcommit")
    files = {name.strip(): digest for name, digest in _REPORT_FILE.findall(report_text)}
    if not files:
        raise ValueError("Verifikationsreport enthaelt kein Dateimanifest")
    return commit.group(1), files


def _verify_reported_file(path: Path, reported: dict[str, str]) -> None:
    expected = reported.get(path.name)
    if expected is None:
        raise ValueError(f"{path.name} fehlt im Dateimanifest des Reports")
    actual = _sha256(path)
    if actual != expected:
        raise ValueError(
            f"SHA256 von {path.name} stimmt nicht mit dem Verifikationsreport ueberein"
        )


def main() -> int:
    """Paketiert den verifizierten Engineering-Stand nach ``release/current``.

    Prueft, dass Report, STEP, STL und Passungscheck existieren, der Report
    aus dem aktuellen HEAD-Commit stammt und der Arbeitsbaum keine getrackten
    uncommitteten Aenderungen traegt (Ausnahmen: ``_DIRTY_EXEMPT``),
    verifiziert die im Report gelisteten SHA256 der Druckdateien sowie den
    Passungscheck, kopiert die Freigabedateien um und schreibt Manifest und
    README. Status strikt aus der Gesamtergebnis-Zeile (``_release_status``).
    Rueckgabe: Exit-Code 0."""
    p = PRM.P
    PRM.validate(p)
    h = PRM.params_hash(p)
    source = engineering_dir(h)
    report = source / f"report_{h}.md"
    step = source / f"universal_segment_x4_{h}.step"
    stl = source / f"universal_segment_x4_{h}.stl"
    fit = fit_dir(h) / "fit_summary.json"
    required = (report, step, stl, fit)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Engineering-Stufe fehlt: " + ", ".join(missing))

    report_text = report.read_text(encoding="utf-8")
    status = _release_status(report_text)

    dirty = _git_dirty()
    if dirty:
        shown = ", ".join(dirty[:5]) + (", ..." if len(dirty) > 5 else "")
        raise RuntimeError(
            f"Arbeitsbaum enthaelt uncommittete Aenderungen ({shown}); Release "
            "nur aus einem committeten Stand (sonst luegt source_commit im Manifest)"
        )
    head = _git_revision()
    report_commit, reported_files = _report_provenance(report_text)
    if report_commit != head:
        raise RuntimeError(
            f"Engineering-Artefakte stammen aus Commit {report_commit}, HEAD ist {head}; "
            "Engineering-Stufe nach dem Commit erneut ausfuehren"
        )
    _verify_reported_file(step, reported_files)
    _verify_reported_file(stl, reported_files)

    fit_data = json.loads(fit.read_text(encoding="utf-8"))
    belluna_source = ROOT / "reference_models" / "belluna.py"
    if (
        fit_data.get("parameter_hash") != h
        or fit_data.get("source_commit") != report_commit
        or fit_data.get("belluna_source_sha256") != _sha256(belluna_source)
        or fit_data.get("PASS") is not True
    ):
        raise RuntimeError("Digitaler Belluna-Passungscheck fehlt oder ist nicht PASS")

    target = current_release_dir()
    target.mkdir(parents=True, exist_ok=True)
    for old in target.iterdir():
        if old.is_file():
            old.unlink()

    names = {
        step: f"Belluna_Adapter_Universal_x4_{h}.step",
        stl: f"Belluna_Adapter_Universal_x4_PRINT_{h}.stl",
        report: f"verification_report_{h}.md",
        fit: f"fit_summary_{h}.json",
    }
    copied = []
    for src, name in names.items():
        dst = target / name
        shutil.copy2(src, dst)
        copied.append(dst)

    manifest = {
        "schema": 3,
        "status": status,
        "parameter_hash": h,
        "geom_rev": p.GEOM_REV,
        "source_commit": report_commit,
        "source_commit_time": _git_commit_time(report_commit),
        "toolchain": toolchain_versions(),
        "part": "Universal-L-Ecksegment",
        "quantity": 4,
        "step_orientation": "Einbaulage",
        "stl_orientation": "Drucklage, Deckfläche auf Z=0",
        "files": {path.name: {"sha256": _sha256(path), "bytes": path.stat().st_size}
                  for path in copied},
        "open_gates": (["reale Einbaukontrollen; Werkstoffpfade nur "
                         "PASS_ASSUMPTION_BASED laut docs/load-paths.md"]
                       if status == "PROTOTYPE_ONLY" else []),
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (target / "README.md").write_text(
        f"# Aktueller Adapterstand\n\n"
        f"Parameterstand `{h}` · GEOM_REV `{p.GEOM_REV}` · Status `{status}`\n\n"
        f"- `Belluna_Adapter_Universal_x4_{h}.step`: ein Universalsegment in Einbaulage.\n"
        f"- `Belluna_Adapter_Universal_x4_PRINT_{h}.stl`: dasselbe Segment in Drucklage.\n"
        f"- Stückzahl: **4**, nur um Z drehen, nicht spiegeln.\n"
        f"- `verification_report_{h}.md`: zugehöriger rechnerischer Nachweis.\n"
        f"- `fit_summary_{h}.json`: digitaler Passungscheck gegen die Belluna-Rekonstruktion.\n"
        f"- `manifest.json`: Prüfsummen, Quellcommit, Werkzeugversionen und offene Gates.\n\n"
        f"`PROTOTYPE_ONLY` ist keine Produktionsfreigabe. Reale Einbaukontrollen "
        f"und die Erkenntnisgrenze der annahmenbasierten Werkstoffpfade stehen "
        f"in `docs/verification.md` und `docs/load-paths.md`.\n",
        encoding="utf-8",
    )
    print(f"RELEASE-ENDE: {target} ({status}, Parameterstand {h})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
