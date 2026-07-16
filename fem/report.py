"""Verifikationsreport (Markdown): FEM-Ergebnisse + analytische Nachweise +
Parameterstand. PASS/FAIL-Logik für das Pipeline-Gate (Spec §6/§7)."""
from pathlib import Path

import params as PRM
from fem import analytic as A


def write_report(fem_results: dict, joint_result: dict,
                 p: PRM.Params, out_path: str) -> tuple[bool, bool]:
    """Schreibt den Verifikationsreport nach out_path und liefert (ok,
    vorbehalt) (Ledger 42: strukturierte Rückgabe statt "Vorbehalt"-Text-
    Matching im Reporttext durch Konsumenten wie pipeline/engineering.py). M7: leeres
    fem_results (kein Lastfall) ist ein Aufrufer-Fehler, kein stiller
    Report -- wirft ValueError statt eine leere/irreführende Lastfall-
    Tabelle zu schreiben."""
    if not fem_results:
        raise ValueError("write_report: fem_results ist leer -- kein Lastfall zur Verifikation")
    lines = ["# Verifikationsreport Belluna-Adapterrahmen", ""]
    lines.append(f"Parameterstand: `{PRM.params_hash(p)}` · "
                 f"H_RAISE {p.H_RAISE} mm · Wandstärke effektiv "
                 f"{PRM.effective_wall(p)} mm · **Vierkantwelle "
                 f"{PRM.select_shaft(p):.0f} mm**")
    hdt_text = (f"HDT(1,82 MPa) {p.HDT_182:.0f} °C" if p.HDT_182 is not None
                else f"HDT/B(0,45 MPa) {p.HDT_045:.0f} °C; 1,82-MPa-Wert fehlt")
    lines.append(f"Material: **{p.MATERIAL_NAME}** · E {p.E_BASE:.0f} MPa · "
                 f"ρ {p.RHO:.0f} kg/m³ · {hdt_text}")
    lines.append("")
    ok = True

    lines.append("## FEM-Lastfälle")
    lines.append("| Lastfall | max vM [MPa] | zulässig | Deckfl.-Verf. [mm] | Status |")
    lines.append("|---|---|---|---|---|")
    for name, r in sorted(fem_results.items()):
        ok &= r["PASS"]
        # defl_top_is_fallback (fem/run_fem.py, M3/Ledger 32): fehlen echte
        # Deckflächen-Knoten (Submodell-Fall), weicht defl_top auf defl_max
        # aus -- im Report als "(Fallback)" kenntlich machen statt einen
        # unechten Deckflächenwert stillschweigend als solchen auszugeben.
        fallback = " (Fallback)" if r.get("defl_top_is_fallback", False) else ""
        lines.append(f"| {name} | {r['vm_max_MPa']:.2f} | {r['allowable_MPa']:.2f} "
                     f"| {r['defl_top_mm']:.3f}{fallback} (≤ {p.DEFL_TOP_MAX}) "
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
        # (EDGE_DIST/EDGE_H, Messpunkte B1/B2) und darf kein stilles PASS sein.
        vorbehalt = True
        lines.append(f"- Haubenfreigang über Dachkante: **OFFEN** — kein Überlapp "
                     f"laut Schätzwerten (EDGE_DIST={p.EDGE_DIST:.0f}, "
                     f"EDGE_H={p.EDGE_H:.0f}); vor Druckfreigabe messen "
                     f"(Messpunkte B1/B2)")
    else:
        clr_ok = clr >= p.CLEAR_MIN
        ok &= clr_ok
        lines.append(f"- Haubenfreigang über Dachkante: {clr:.1f} mm "
                     f"(≥ {p.CLEAR_MIN} mm) → {'PASS' if clr_ok else 'FAIL'}")
    u = A.glue_shear_utilization(p)
    u_ok = u < 1.0
    ok &= u_ok
    lines.append(f"- Elastikfugen-Auslastung (Thermik, LF5; vollständig gefügter "
                 f"{max(PRM.outer_dims(p)):.0f}-mm-Rahmen): {u*100:.0f} % "
                 f"→ {'PASS' if u_ok else 'FAIL'}")
    if p.HDT_182 is None:
        lines.append(f"- Materialtemperatur: T_MAX {p.T_MAX:.0f} °C; Würth nennt nur "
                     f"HDT/B(0,45 MPa) {p.HDT_045:.0f} °C, keinen 1,82-MPa-Wert. "
                     f"Weißer RAL-9003-Decklack ist Pflicht; Temperatur-Abminderung "
                     f"{p.DERATE_TEMP:.2f} angewendet")
    else:
        temp_margin = p.HDT_182 - p.T_MAX
        lines.append(f"- Materialtemperatur: T_MAX {p.T_MAX:.0f} °C, "
                     f"HDT(1,82 MPa) {p.HDT_182:.0f} °C, Marge {temp_margin:.0f} K; "
                     f"Temperatur-Abminderung {p.DERATE_TEMP:.2f} angewendet")
    j = A.joint_checks(p, PRM.wind_force(p))
    ok &= j["PASS"]
    lines.append(f"- Stoß analytisch: τ {j['tau_MPa']:.2f}/{j['tau_zul_MPa']:.2f} MPa, "
                 f"2×M5 je {j['lochleibung_MPa']:.2f} MPa, "
                 f"ein M5 im Restfall {j['lochleibung_ein_rest_MPa']:.2f}/"
                 f"{j['lochleibung_zul_MPa']:.2f} MPa "
                 f"→ {'PASS' if j['PASS'] else 'FAIL'}")
    g = A.glue_load_shear(p, PRM.wind_force(p))
    ok &= g["PASS"]
    lines.append(f"- Klebfugen-Schub aus Last: {g['tau_MPa']:.3f} ≤ "
                 f"{g['tau_zul_MPa']} N/mm² → {'PASS' if g['PASS'] else 'FAIL'}")
    sc = A.side_screw_pullout(p)
    ok &= sc["PASS"]
    lines.append(f"- Seitenschrauben-Auszug: {sc['F_zul_N']:.0f} N zulässig ≥ "
                 f"{sc['F_erf_N']:.0f} N erforderlich → {'PASS' if sc['PASS'] else 'FAIL'}")
    lines.append("- Fertigungslogik: 1 rotationsidentisches Universal-Segment ×4; "
                 "Belluna-Vollmaterialrippen ±140/±165 auf jeder Seite, "
                 "zwei M5 je Segmentstoß, geschlossener Unterkragen")
    plate_clear = (p.CUTOUT_W - p.PLATE_KRAGEN_W) / 2
    if not p.PLATE_KRAGEN_MEASURED:
        vorbehalt = True
    plate_status = "gemessen" if p.PLATE_KRAGEN_MEASURED else "angenommen"
    lines.append(f"- Belluna-Kragenpassung: nominal {plate_clear:.1f} mm Radialluft "
                 f"mit **{plate_status}em** A3a={p.PLATE_KRAGEN_W:.0f} mm"
                 + ("; A3a vor Druck messen" if not p.PLATE_KRAGEN_MEASURED else ""))
    if not p.ROOF_WOOD_FRAME_CONFIRMED:
        vorbehalt = True
    lines.append(f"- Dachinterface: {p.GROOVE_W:.0f}-mm-Elastikfuge vollständig "
                 f"über nachzurüstendem Holzrahmen ≥{p.ROOF_WOOD_FRAME_W:.0f} mm; "
                 f"keine Holzverschraubung. X150-Dach ist {p.ROOF_T:.0f} mm "
                 f"stark; Holzrahmen-Status "
                 f"{'bestätigt' if p.ROOF_WOOD_FRAME_CONFIRMED else 'vor Montage offen'}")

    lines.append("")
    if not ok:
        lines.append("# Gesamtergebnis: **FAIL**")
    elif vorbehalt:
        lines.append("# Gesamtergebnis: **PASS mit Vorbehalt** "
                     "(offene Mess-/Einbauvoraussetzungen vor Druck und Montage prüfen)")
    else:
        lines.append("# Gesamtergebnis: **PASS**")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return bool(ok), vorbehalt
