#!/usr/bin/env python3
"""Messkampagne: ueberträgt das Messprotokoll (messwerte.json) in params.py.
Reines Python3, KEIN FreeCAD-Import -- laeuft unter jedem python3 und ist
darum ohne bin/fc suite-testbar (tests/test_tools_messkampagne.py).

Protokollfelder (siehe messwerte.beispiel.json, nullable -- nur gemessene
Felder fliessen in die Uebertragung ein, Rest bleibt auf dem params.py-
Default stehen): B1a, B1b, B2, B3, B4, A1c-f, A2a-c, A3a-c, A4a, A4b, A5a, A5b.

Formeln (Protokoll -> params-Feld):
  EDGE_DIST          = B1a + B1b
  EDGE_H             = B2
  ROOF_T             = B3
  HOOD_UNDERSIDE_H   = B4
  W_TOP_FRONT/REAR/LEFT/RIGHT = A1c/A1d/A1e/A1f
  REC_GUSSET_D       = A4a + 0.5   (Reserve: Fertigungstoleranz Gusset-Ueberstand)
  REC_GUSSET_W       = A4b + 2.0   (Reserve: Fertigungstoleranz Gusset-Reichweite)

Aufruf:
  python3 scripts/messkampagne.py messwerte.json [--target params.py] [--dry-run]

--target zeigt auf die zu patchende params-Datei (Default ./params.py). Vor
dem Schreiben wird IMMER ein Backup <target>.bak angelegt (ueberschreibt ein
vorhandenes Backup). --dry-run zeigt nur die Diff-Tabelle, schreibt nichts.

Danach PFLICHT: bin/fc tests/run_tests.py && bin/fc run_all.py (als
Hintergrundprozess, siehe Skill maxx150-pipeline) -- erst danach ist der neue
Parameterstand verifiziert und druckfreigegeben."""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

# params-Feld -> (Protokollfeld(er), Formel). Reihenfolge = Anzeige-Reihenfolge
# der Diff-Tabelle.
_SIMPLE = (
    ("EDGE_H", "B2"),
    ("ROOF_T", "B3"),
    ("HOOD_UNDERSIDE_H", "B4"),
    ("W_TOP_FRONT", "A1c"),
    ("W_TOP_REAR", "A1d"),
    ("W_TOP_LEFT", "A1e"),
    ("W_TOP_RIGHT", "A1f"),
)


def compute_mapping(messwerte: dict) -> dict:
    """messwerte (Protokollfelder, nullable) -> {params-Feldname: neuer Wert}.
    Formeln siehe Moduldocstring. Felder mit fehlenden/nullen Rohwerten
    werden ausgelassen (bleiben auf ihrem params.py-Default)."""
    out = {}

    b1a, b1b = messwerte.get("B1a"), messwerte.get("B1b")
    if b1a is not None and b1b is not None:
        out["EDGE_DIST"] = b1a + b1b

    for feld, proto in _SIMPLE:
        if messwerte.get(proto) is not None:
            out[feld] = messwerte[proto]

    if messwerte.get("A4a") is not None:
        out["REC_GUSSET_D"] = messwerte["A4a"] + 0.5
    if messwerte.get("A4b") is not None:
        out["REC_GUSSET_W"] = messwerte["A4b"] + 2.0

    return out


def _fmt(v: float) -> str:
    """Formatiert einen Zahlenwert wie die vorhandenen params.py-Literale
    (mindestens eine Nachkommastelle, keine unnoetigen Nullen)."""
    v = round(float(v), 4)
    s = f"{v:.4f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    return s


def patch_params_text(text: str, mapping: dict):
    """Ersetzt je params-Feld NUR den Zahlenwert nach '=' (Feldname-
    anchored Regex), Kommentar/Einrueckung bleiben unangetastet. Liefert
    (neuer_text, changes) mit changes = [(feld, alt_str, neu_str), ...] in
    der Reihenfolge, in der die Felder in der Datei auftauchen."""
    changes = []
    # split/join statt splitlines(keepends=True): (.*)$ matcht kein
    # abschliessendes "\n" -- mit keepends wuerde jede gepatchte Zeile ihren
    # Zeilenumbruch verlieren und mit der naechsten verschmelzen.
    lines = text.split("\n")
    remaining = dict(mapping)
    for i, line in enumerate(lines):
        if not remaining:
            break
        for feld in list(remaining):
            m = re.match(rf"^(\s*{feld}\s*:\s*\w+\s*=\s*)([0-9eE+\-.]+)(.*)$", line)
            if m:
                neu_str = _fmt(remaining.pop(feld))
                changes.append((feld, m.group(2), neu_str))
                lines[i] = f"{m.group(1)}{neu_str}{m.group(3)}"
                break
    return "\n".join(lines), changes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Messkampagne: Messprotokoll -> params.py")
    ap.add_argument("messwerte", help="Pfad zur messwerte.json (Vorlage: messwerte.beispiel.json)")
    ap.add_argument("--target", default="./params.py",
                    help="zu patchende params-Datei (Default ./params.py)")
    ap.add_argument("--dry-run", action="store_true",
                    help="nur Diff-Tabelle anzeigen, nichts schreiben")
    args = ap.parse_args(argv)

    messwerte_path = Path(args.messwerte)
    messwerte = json.loads(messwerte_path.read_text(encoding="utf-8"))
    mapping = compute_mapping(messwerte)
    if not mapping:
        print("Keine verwertbaren Messwerte in", messwerte_path, "-- nichts zu tun.")
        return 0

    target = Path(args.target)
    if not target.exists():
        print(f"FEHLER: Zieldatei {target} existiert nicht.", file=sys.stderr)
        return 1
    text = target.read_text(encoding="utf-8")
    new_text, changes = patch_params_text(text, mapping)

    if not changes:
        print(f"WARNUNG: keine der {len(mapping)} berechneten Felder in {target} gefunden "
             f"-- nichts geaendert.")
        return 1

    print(f"{'Feld':<20}{'alt':>12}{'neu':>12}")
    for feld, alt, neu in changes:
        print(f"{feld:<20}{alt:>12}{neu:>12}")

    fehlend = sorted(set(mapping) - {c[0] for c in changes})
    if fehlend:
        print(f"\nWARNUNG: nicht in {target} gefunden (ignoriert): {', '.join(fehlend)}")

    if args.dry_run:
        print("\n--dry-run: nichts geschrieben.")
        return 0

    backup = target.with_name(target.name + ".bak")
    shutil.copy2(target, backup)
    target.write_text(new_text, encoding="utf-8")
    print(f"\nBackup: {backup}")
    print(f"Geschrieben: {target}")
    print("\nDanach PFLICHT: bin/fc tests/run_tests.py && bin/fc run_all.py (Hintergrund!)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
