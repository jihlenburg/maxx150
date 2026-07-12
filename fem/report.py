"""Verifikationsreport (Markdown): FEM-Ergebnisse + analytische Nachweise +
Parameterstand. PASS/FAIL-Logik für das Pipeline-Gate (Spec §6/§7)."""
from pathlib import Path

import params as PRM
from fem import analytic as A


def write_report(fem_results: dict, joint_result: dict,
                 p: PRM.Params, out_path: str) -> bool:
    lines = ["# Verifikationsreport Belluna-Adapterrahmen", ""]
    lines.append(f"Parameterstand: `{PRM.params_hash(p)}` · "
                 f"H_RAISE {p.H_RAISE} mm · Wandstärke effektiv "
                 f"{PRM.effective_wall(p)} mm · **Vierkantwelle "
                 f"{PRM.select_shaft(p):.0f} mm**")
    lines.append("")
    ok = True

    lines.append("## FEM-Lastfälle")
    lines.append("| Lastfall | max vM [MPa] | zulässig | Deckfl.-Verf. [mm] | Status |")
    lines.append("|---|---|---|---|---|")
    for name, r in sorted(fem_results.items()):
        ok &= r["PASS"]
        lines.append(f"| {name} | {r['vm_max_MPa']:.2f} | {r['allowable_MPa']:.2f} "
                     f"| {r['defl_top_mm']:.3f} (≤ {p.DEFL_TOP_MAX}) "
                     f"| {'PASS' if r['PASS'] else 'FAIL'} |")

    lines.append("")
    lines.append("## Stoß-Submodell")
    ok &= joint_result["PASS"]
    lines.append(f"max vM {joint_result['vm_max_MPa']:.2f} MPa ≤ "
                 f"{joint_result['allowable_MPa']:.2f} MPa → "
                 f"{'PASS' if joint_result['PASS'] else 'FAIL'}")

    lines.append("")
    lines.append("## Analytische Nachweise")
    clr = A.hood_clearance(p)
    vorbehalt = False
    if clr == float("inf"):
        # DA-Review 2026-07-12: inf entsteht nur aus SCHÄTZWERTEN
        # (EDGE_DIST/EDGE_H, Messkampagne 7) und darf kein stilles PASS sein.
        vorbehalt = True
        lines.append(f"- Haubenfreigang über Dachkante: **OFFEN** — kein Überlapp "
                     f"laut Schätzwerten (EDGE_DIST={p.EDGE_DIST:.0f}, "
                     f"EDGE_H={p.EDGE_H:.0f}); vor Druckfreigabe messen "
                     f"(Messkampagne 7)")
    else:
        clr_ok = clr >= p.CLEAR_MIN
        ok &= clr_ok
        lines.append(f"- Haubenfreigang über Dachkante: {clr:.1f} mm "
                     f"(≥ {p.CLEAR_MIN} mm) → {'PASS' if clr_ok else 'FAIL'}")
    u = A.glue_shear_utilization(p)
    u_ok = u < 1.0
    ok &= u_ok
    lines.append(f"- Elastikfugen-Auslastung (Thermik, LF5): {u*100:.0f} % "
                 f"→ {'PASS' if u_ok else 'FAIL'}")
    j = A.joint_checks(p, PRM.wind_force(p))
    ok &= j["PASS"]
    lines.append(f"- Stoß analytisch: τ {j['tau_MPa']:.2f}/{j['tau_zul_MPa']:.2f} MPa, "
                 f"Lochleibung {j['lochleibung_MPa']:.2f}/{j['lochleibung_zul_MPa']:.2f} MPa "
                 f"→ {'PASS' if j['PASS'] else 'FAIL'}")
    g = A.glue_load_shear(p, PRM.wind_force(p))
    ok &= g["PASS"]
    lines.append(f"- Klebfugen-Schub aus Last: {g['tau_MPa']:.3f} ≤ "
                 f"{g['tau_zul_MPa']} N/mm² → {'PASS' if g['PASS'] else 'FAIL'}")
    sc = A.side_screw_pullout(p)
    ok &= sc["PASS"]
    lines.append(f"- Seitenschrauben-Auszug: {sc['F_zul_N']:.0f} N zulässig ≥ "
                 f"{sc['F_erf_N']:.0f} N erforderlich → {'PASS' if sc['PASS'] else 'FAIL'}")

    lines.append("")
    if not ok:
        lines.append("# Gesamtergebnis: **FAIL**")
    elif vorbehalt:
        lines.append("# Gesamtergebnis: **PASS mit Vorbehalt** "
                     "(Haubenfreigang ungemessen — Messkampagne 7 vor Druck!)")
    else:
        lines.append("# Gesamtergebnis: **PASS**")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))
    return bool(ok)
