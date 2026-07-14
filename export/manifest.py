"""Datei-Manifest an den Verifikationsreport anhängen (Finalreview I1):
SHA256 je Exportdatei + Git-Commit + GEOM_REV. Macht die Artefakte eines
Reports nachvollziehbar zuordenbar, auch wenn ein späterer Lauf mit
UNVERÄNDERTEM Parameterstand (identischer params_hash) dieselben Dateinamen
in out/ überschreibt -- der Report bleibt der Beleg, WELCHER konkrete
Dateiinhalt zu diesem Lauf gehörte."""
import hashlib
from pathlib import Path

import params as PRM

_CHUNK = 1 << 20   # 1 MiB


def _sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def append_manifest(report_path: str, files, git_rev: str,
                    p: PRM.Params = PRM.P) -> None:
    """Hängt eine '## Datei-Manifest'-Sektion an den bestehenden Report unter
    report_path an: je Datei in `files` (Path oder str) Dateiname + SHA256,
    dazu `git_rev` (vom Aufrufer ermittelt, z. B. `git rev-parse HEAD` in
    run_all.py -- manifest.py selbst braucht dafür keine Subprocess-
    Abhängigkeit) und GEOM_REV des TATSÄCHLICH manifestierten
    Parameterobjekts p (Review-Fix 2026-07-14: vorher global PRM.P --
    bei Varianten-Läufen wäre der falsche Stand dokumentiert worden)."""
    rows = "\n".join(f"| {Path(f).name} | `{_sha256(f)}` |" for f in files)
    section = (
        "\n\n## Datei-Manifest\n\n"
        f"Git-Commit: `{git_rev}` · GEOM_REV: `{p.GEOM_REV}`\n\n"
        "| Datei | SHA256 |\n"
        "|---|---|\n"
        f"{rows}\n"
    )
    out = Path(report_path)
    out.write_text(out.read_text(encoding="utf-8") + section, encoding="utf-8")
