#!/usr/bin/env python3
"""Messwertübernahme: überträgt das Messprotokoll in ``params.py``.
Reines Python3, KEIN FreeCAD-Import -- laeuft unter jedem python3 und ist
darum ohne bin/fc suite-testbar (tests/test_tools_measurements.py).

Protokollfelder (siehe messwerte.beispiel.json, nullable -- nur gemessene
Felder fliessen in die Uebertragung ein, Rest bleibt auf dem params.py-
Default stehen): B1a, B1b, B2, B3, B4, A1c-f, A2a-c, A3a-c, A4a, A4b, A5a, A5b.

Formeln (Protokoll -> params-Feld):
  EDGE_DIST          = B1a + B1b
  EDGE_H             = B2
  ROOF_T             = B3
  HOOD_UNDERSIDE_H   = B4

BEWUSST KEINE automatische Uebernahme (Design-Entscheidungen 2026-07-13,
Begruendung in messwerte.json/_notizen -- Review-Fix: die frueheren
1:1-Mappings haetten validate()-Brecher vorgeschlagen):
  A1c-f (Plattenflansch 26) -> W_TOP_* bleibt 50: die Deckflaeche ist
    bewusst BREITER als der Plattenflansch (Kammerstruktur braucht >=44),
    die Platte liegt mittig auf.
  A4a/A4b (Gussets) -> REC_GUSSET_* bleibt 0/18: die Gussets tauchen mit
    dem Unterkragen in den Ausschnitt, es gibt nichts freizustellen
  (Passungstest ``python3 -m pipeline fit``).

Aufruf:
  python3 scripts/apply_measurements.py messwerte.json [--target params.py] [--dry-run]

--target zeigt auf die zu patchende params-Datei (Default ./params.py). Vor
dem Schreiben wird IMMER ein Backup <target>.bak angelegt (ueberschreibt ein
vorhandenes Backup). --dry-run zeigt nur die Diff-Tabelle, schreibt nichts.

Danach PFLICHT: ``python3 -m pipeline test`` und
``python3 -m pipeline engineering``. Erst danach ist der neue Parameterstand
rechnerisch verifiziert; physische Freigabegates bleiben davon getrennt."""
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
)

# Protokollfelder, die frueher gemappt wurden, seit den Design-Entscheidungen
# vom 2026-07-13 aber BEWUSST NICHT mehr automatisch einfliessen (siehe
# Moduldocstring + messwerte.json/_notizen). Werden sie geliefert, gibt main()
# eine explizite Meldung aus, statt validate()-Brecher vorzuschlagen.
NICHT_UEBERNOMMEN = {
    "A1c": "W_TOP_FRONT bleibt 50 (Deckflaeche bewusst breiter als Plattenflansch)",
    "A1d": "W_TOP_REAR bleibt 50 (dito)",
    "A1e": "W_TOP_LEFT bleibt 50 (dito)",
    "A1f": "W_TOP_RIGHT bleibt 50 (dito)",
    "A4a": "REC_GUSSET_D bleibt 0 (Gussets tauchen in den Ausschnitt)",
    "A4b": "REC_GUSSET_W unveraendert (Freistellung entfaellt)",
}


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
    ap = argparse.ArgumentParser(description="Messwertübernahme: Messprotokoll -> params.py")
    ap.add_argument("messwerte", help="Pfad zur messwerte.json (Vorlage: messwerte.beispiel.json)")
    ap.add_argument("--target", default="./params.py",
                    help="zu patchende params-Datei (Default ./params.py)")
    ap.add_argument("--dry-run", action="store_true",
                    help="nur Diff-Tabelle anzeigen, nichts schreiben")
    args = ap.parse_args(argv)

    messwerte_path = Path(args.messwerte)
    messwerte = json.loads(messwerte_path.read_text(encoding="utf-8"))
    mapping = compute_mapping(messwerte)

    bewusst = [f"  {proto}={messwerte[proto]}: {grund}"
               for proto, grund in NICHT_UEBERNOMMEN.items()
               if messwerte.get(proto) is not None]
    if bewusst:
        print("BEWUSST NICHT uebernommen (Design-Entscheidungen 2026-07-13, "
              "siehe messwerte.json/_notizen):")
        print("\n".join(bewusst))
        print()

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
    print("\nDanach PFLICHT: python3 -m pipeline test && "
          "python3 -m pipeline engineering")
    return 0


if __name__ == "__main__":
    sys.exit(main())
