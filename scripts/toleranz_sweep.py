#!/usr/bin/env python3
"""Toleranz-Sweep der Messkampagnen-Parameter durch die analytischen Gates.

Beantwortet VOR der Messkampagne (Messpunkte A1/A4/B1-B4): Wie genau muss
jede Messung sein, damit die analytischen Gates robust bleiben -- und welche
Messung entscheidet ueberhaupt ein Gate? Geprueft werden je Parametersatz:

1. ``params.validate`` (geometrische Konsistenz),
2. Haubenfreigang ``fem.analytic.hood_clearance`` gegen ``CLEAR_MIN``
   (inkl. Regime-Analyse: erreicht die Haube die Dachkante ueberhaupt?),
3. Thermikfugen-Auslastung ``fem.analytic.glue_shear_utilization``,
4. Stossnachweis ``fem.analytic.joint_checks`` unter der 480-N-Huelle,
5. Lastpfadcheck ``analysis.load_paths.assess`` (``system_PASS``).

Reines Python3, kein FreeCAD. Der geometrische Belluna-Fit-Check (FreeCAD,
``pipeline fit``) ist ausdruecklich NICHT enthalten; er bleibt der Nachlauf
nach der echten Messwertuebernahme. Ausgabe: Markdown auf stdout, optional
``--json``. Der Sweep ist deterministisch (Eckenenumeration, kein Zufall).

Nutzung:
    python3 scripts/toleranz_sweep.py                  # OAT + Ecken + Regime
    python3 scripts/toleranz_sweep.py --tol EDGE_H=3.0 # Band ueberschreiben
    python3 scripts/toleranz_sweep.py --json sweep.json
"""
from __future__ import annotations

import argparse
import dataclasses
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import params as PRM                     # noqa: E402
from analysis import load_paths as LP   # noqa: E402
from fem import analytic as A            # noqa: E402


# Messkampagnen-Parameter -> (Default-Toleranz mm, Protokollfeld, Messmittel).
# Die Baender folgen dem realistischen Messmittel am Fahrzeug: Gliedermassstab/
# Winkel fuer die B-Aussenmasse, Messschieber fuer Demontage- und A4-Masse.
MESSFELDER: dict[str, tuple[float, str, str]] = {
    "EDGE_DIST": (3.0, "B1a+B1b", "Gliedermassstab, zwei Teilmessungen"),
    "EDGE_H": (2.0, "B2", "Gliedermassstab an der Dachkante"),
    "ROOF_T": (0.5, "B3", "Messschieber bei Demontage"),
    "HOOD_UNDERSIDE_H": (2.0, "B4", "schwer zugaenglich, Fuehlerlehre/Keil"),
    # W_TOP_* ist eine KONSTRUKTIVE Wahl, kein Protokollfeld: A1c-f messen
    # den Belluna-Plattenflansch (~26,5 mm) und werden bewusst nicht auf
    # W_TOP gemappt (scripts/apply_measurements.py). Im Sweep steht W_TOP
    # trotzdem, weil eine Nachparametrierung nach der Kampagne hier landet.
    "W_TOP_FRONT": (1.0, "(konstruktiv)", "Deckflaechenbreite, kein Messfeld"),
    "W_TOP_REAR": (1.0, "(konstruktiv)", "Deckflaechenbreite, kein Messfeld"),
    "W_TOP_LEFT": (1.0, "(konstruktiv)", "Deckflaechenbreite, kein Messfeld"),
    "W_TOP_RIGHT": (1.0, "(konstruktiv)", "Deckflaechenbreite, kein Messfeld"),
    "REC_GUSSET_D": (0.3, "A4a", "gemessen 2026-07-13, Messschieber"),
    "REC_GUSSET_W": (0.5, "A4b", "Messschieber"),
}

# Physikalische Untergrenzen, damit ein Toleranzband keine sinnlosen
# Parameter erzeugt (z. B. negative Gusset-Tiefe).
_FELD_MIN = {"REC_GUSSET_D": 0.0, "REC_GUSSET_W": 0.0}


def evaluate(p: PRM.Params) -> dict:
    """Alle analytischen Gates fuer einen Parametersatz.

    ``validate_ok`` False beendet die Bewertung frueh (die uebrigen Gates
    waeren auf inkonsistenter Geometrie bedeutungslos). ``hood_clearance``
    ist ``None`` im OFFEN-Regime (Haube erreicht die Dachkante nicht;
    ``hood_PASS`` dann ebenfalls ``None``, kein stilles PASS)."""
    try:
        PRM.validate(p)
    except Exception as exc:  # validate wirft ValueError mit Klartext
        return {"validate_ok": False, "validate_error": str(exc),
                "all_gates_PASS": False}
    clr = A.hood_clearance(p)
    hood_open = clr == float("inf")
    hood_pass = None if hood_open else clr >= p.CLEAR_MIN
    glue_util = A.glue_shear_utilization(p)
    joint = A.joint_checks(p, PRM.wind_force(p))
    paths = LP.assess(p, include_cfd=False)
    gates = [hood_pass is not False, glue_util < 1.0, joint["PASS"],
             paths["system_PASS"]]
    return {
        "validate_ok": True,
        "hood_clearance_mm": None if hood_open else round(clr, 2),
        "hood_PASS": hood_pass,
        "glue_utilization": round(glue_util, 4),
        "glue_PASS": glue_util < 1.0,
        "joint_PASS": joint["PASS"],
        "load_paths_PASS": paths["system_PASS"],
        "max_utilization": round(_max_utilization(paths, glue_util), 4),
        "all_gates_PASS": all(gates),
    }


def _max_utilization(paths: dict, glue_util: float) -> float:
    """Groesste Auslastung der FREIGABEWIRKSAMEN Nachweise.

    Spiegelt exakt die system_PASS-Komposition von ``assess`` (je Lastfall
    ``serial_load_path_PASS`` = Schraubgruppe + Doppelraupe + Sandwich, dazu
    Segmentstoss und Thermik). Informative Alternativnachweise wie
    ``elastic_ring_bond_only`` zaehlen bewusst NICHT (Audit 2026-07-17: eine
    schluesselnamensbasierte Suche hatte 77 % als 74 % untertrieben). Wirft
    bei Schema-Aenderung von ``assess`` einen KeyError statt still 0."""
    werte = [glue_util]
    for fall in paths["load_cases"].values():
        werte.append(
            fall["belluna_to_adapter"]["eight_side_screws_full_case"]
            ["utilization"])
        werte.append(
            fall["adapter_to_roof"]["double_elastic_bead_primary"]
            ["normalized_interaction"])
        werte.append(
            fall["wood_to_roof_sandwich"]["sikaforce_one_face_only"]
            ["normalized_interaction"])
    werte.append(paths["segment_joint"]["segment_bond_utilization"])
    werte.append(paths["segment_joint"]["m5_one_remaining_utilization"])
    return max(float(w) for w in werte)


def _variante(feld: str, wert: float) -> PRM.Params:
    wert = max(wert, _FELD_MIN.get(feld, float("-inf")))
    return dataclasses.replace(PRM.P, **{feld: wert})


def oat_sweep(tols: dict[str, float]) -> dict:
    """One-at-a-time: jedes Messfeld einzeln an beide Bandgrenzen."""
    nominal = evaluate(PRM.P)
    ergebnis = {"nominal": nominal, "felder": {}}
    for feld, tol in tols.items():
        basis = getattr(PRM.P, feld)
        zeile = {}
        for richtung, wert in (("minus", basis - tol), ("plus", basis + tol)):
            e = evaluate(_variante(feld, wert))
            zeile[richtung] = e
            zeile[f"{richtung}_kippt"] = (
                e["all_gates_PASS"] != nominal["all_gates_PASS"])
        ergebnis["felder"][feld] = zeile
    return ergebnis


def corner_sweep(tols: dict[str, float]) -> dict:
    """Alle 2^n Eckenkombinationen der Toleranzbaender (deterministisch)."""
    felder = list(tols)
    fails = []
    worst = {"max_utilization": -1.0, "ecke": None}
    total = 0
    for vorzeichen in itertools.product((-1.0, 1.0), repeat=len(felder)):
        total += 1
        werte = {f: getattr(PRM.P, f) + s * tols[f]
                 for f, s in zip(felder, vorzeichen)}
        werte = {f: max(w, _FELD_MIN.get(f, float("-inf")))
                 for f, w in werte.items()}
        e = evaluate(dataclasses.replace(PRM.P, **werte))
        if not e["all_gates_PASS"]:
            fails.append({"ecke": werte, **e})
        if (e["validate_ok"]
                and e.get("max_utilization", -1.0) > worst["max_utilization"]):
            worst = {"max_utilization": e.get("max_utilization", -1.0),
                     "ecke": werte, "ergebnis": e}
    validate_fails = sum(1 for f in fails if not f["validate_ok"])
    return {"ecken_gesamt": total, "ecken_fail": len(fails),
            "ecken_validate_fail": validate_fails,
            "ecken_gate_fail": len(fails) - validate_fails,
            "fails": fails[:10], "knappste_ecke": worst}


def regime_analyse() -> dict:
    """Beantwortet die Kernfrage der B-Messungen: In welchem Regime landet
    das Freigang-Gate, und wie genau muessen B2/B4 dann sein?

    Regime OFFEN: ``HOOD_TIP_REACH < EDGE_DIST`` -- die Haube erreicht die
    Dachkante nicht, das Gate bleibt bewusst OFFEN (kein stilles PASS).
    Regime UEBERLAPP: das Gate wird scharf; zulaessig ist
    ``EDGE_H <= H_RAISE + HOOD_UNDERSIDE_H - CLEAR_MIN``."""
    p = PRM.P
    grenz_edge_dist = p.HOOD_TIP_REACH
    edge_h_max = p.H_RAISE + p.HOOD_UNDERSIDE_H - p.CLEAR_MIN
    clr_ueberlapp = p.H_RAISE + p.HOOD_UNDERSIDE_H - p.EDGE_H
    return {
        "regime_nominal": ("OFFEN" if p.HOOD_TIP_REACH < p.EDGE_DIST
                           else "UEBERLAPP"),
        "edge_dist_nominal_mm": p.EDGE_DIST,
        "edge_dist_regimegrenze_mm": grenz_edge_dist,
        "edge_dist_abstand_zur_grenze_mm": round(p.EDGE_DIST - grenz_edge_dist, 1),
        "ueberlapp_edge_h_max_mm": round(edge_h_max, 1),
        "edge_h_nominal_mm": p.EDGE_H,
        "ueberlapp_freigang_bei_nominalwerten_mm": round(clr_ueberlapp, 1),
        "ueberlapp_nominal_PASS": clr_ueberlapp >= p.CLEAR_MIN,
    }


def _kurzbefund(e: dict) -> str:
    """Einzeiler je Bandgrenze: OK, VALIDATE-Klippe (Geometrie wird
    inkonsistent -> Design muesste nachparametriert werden) oder das
    verletzte Gate."""
    if e["all_gates_PASS"]:
        return "OK"
    if not e["validate_ok"]:
        grund = e["validate_error"].splitlines()[-1].lstrip("- ").split(":")[0]
        return f"VALIDATE: {grund}"
    verletzt = [name for name, schluessel in (
        ("Freigang", "hood_PASS"), ("Thermik", "glue_PASS"),
        ("Stoss", "joint_PASS"), ("Lastpfad", "load_paths_PASS"),
    ) if e.get(schluessel) is False]
    return "FAIL: " + ", ".join(verletzt)


def _markdown(oat: dict, ecken: dict, regime: dict,
              tols: dict[str, float]) -> str:
    n = oat["nominal"]
    lines = [
        "# Toleranz-Sweep der Messkampagnen-Parameter",
        "",
        f"Parameterstand `{PRM.params_hash()}` · deterministische "
        f"Eckenenumeration · analytische Gates ohne FreeCAD-Fit-Check",
        "",
        "## Nominal",
        "",
        f"- Alle analytischen Gates: "
        f"{'PASS' if n['all_gates_PASS'] else 'FAIL'}",
        "- Haubenfreigang: "
        + ("OFFEN (Schaetzwert-Regime, Haube erreicht Dachkante nicht)"
           if n["hood_clearance_mm"] is None
           else f"{n['hood_clearance_mm']} mm"),
        f"- Thermikfugen-Auslastung: {n['glue_utilization'] * 100:.0f} %",
        f"- Knappste freigabewirksame Grenzflaeche: "
        f"{n['max_utilization'] * 100:.0f} % Auslastung",
        "",
        "## Regime-Analyse Haubenfreigang (B1/B2/B4)",
        "",
        f"- Regime bei Schaetzwerten: **{regime['regime_nominal']}** "
        f"(EDGE_DIST {regime['edge_dist_nominal_mm']:.0f} mm vs. "
        f"Regimegrenze {regime['edge_dist_regimegrenze_mm']:.0f} mm; "
        f"Abstand {regime['edge_dist_abstand_zur_grenze_mm']:.0f} mm)",
        f"- Faellt B1 in das UEBERLAPP-Regime, gilt: EDGE_H <= "
        f"**{regime['ueberlapp_edge_h_max_mm']:.0f} mm** "
        f"(H_RAISE + HOOD_UNDERSIDE_H - CLEAR_MIN)",
        f"- Mit den heutigen Schaetzwerten waere der Ueberlapp-Freigang "
        f"{regime['ueberlapp_freigang_bei_nominalwerten_mm']:.0f} mm -> "
        f"{'PASS' if regime['ueberlapp_nominal_PASS'] else 'FAIL'}: "
        "B1 entscheidet das Regime, B2/B4 entscheiden dann das Gate.",
        "",
        "## One-at-a-time (je Feld an beide Bandgrenzen)",
        "",
        "| Feld | Protokoll | Band ±mm | −Band | +Band |",
        "|---|---|---|---|---|",
    ]
    for feld, tol in tols.items():
        zeile = oat["felder"][feld]
        _, protokoll, _ = MESSFELDER[feld]
        lines.append(f"| {feld} | {protokoll} | {tol} | "
                     f"{_kurzbefund(zeile['minus'])} | "
                     f"{_kurzbefund(zeile['plus'])} |")
    w = ecken["knappste_ecke"]
    lines += [
        "",
        "## Eckensweep (alle Kombinationen)",
        "",
        f"- {ecken['ecken_gesamt']} Ecken geprueft, "
        f"{ecken['ecken_fail']} nicht bestanden: "
        f"{ecken['ecken_validate_fail']} an der Parameter-Validierung "
        f"(Geometrie muesste nachparametriert werden), "
        f"{ecken['ecken_gate_fail']} an einem Last-/Freigang-Gate.",
        f"- Hoechste freigabewirksame Auslastung unter den geometrisch "
        f"gueltigen Ecken: {w['max_utilization'] * 100:.0f} %.",
    ]
    if ecken["ecken_fail"]:
        lines.append("- Erste Fail-Ecken (max. 10) stehen im JSON-Export "
                     "(--json).")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """CLI-Einstieg: OAT-, Ecken- und Regime-Analyse rechnen, Markdown auf
    stdout, optional JSON-Export. Rueckgabe 0, wenn alle Ecken PASS bleiben,
    sonst 1 (nutzbar als Vorab-Gate vor einer Messwertuebernahme)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tol", action="append", default=[],
                        metavar="FELD=MM",
                        help="Toleranzband eines Feldes ueberschreiben")
    parser.add_argument("--json", type=Path, default=None,
                        help="zusaetzlich vollstaendiges JSON schreiben")
    args = parser.parse_args(argv)

    tols = {feld: tol for feld, (tol, _, _) in MESSFELDER.items()}
    for eintrag in args.tol:
        feld, _, wert = eintrag.partition("=")
        if feld not in tols:
            parser.error(f"unbekanntes Messfeld {feld!r}; bekannt: "
                         + ", ".join(tols))
        tols[feld] = float(wert)

    oat = oat_sweep(tols)
    ecken = corner_sweep(tols)
    regime = regime_analyse()
    sys.stdout.write(_markdown(oat, ecken, regime, tols))
    if args.json:
        args.json.write_text(json.dumps(
            {"parameter_hash": PRM.params_hash(), "toleranzen_mm": tols,
             "oat": oat, "ecken": ecken, "regime": regime},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nJSON: {args.json}")
    return 0 if ecken["ecken_fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
