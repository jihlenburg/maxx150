# Follow-up-Register (aus dem finalen Whole-Branch-Review, 2026-07-12)

Detail-Historie: `.superpowers/sdd/progress.md` (Ledger). Vor-Merge-Fixes laufen separat
(validate(p), M5-Kommentare, Normlänge) — dieses File sammelt NUR die Follow-ups.

## Pflichtpaket VOR dem Messkampagnen-Re-Run
- [x] I3: Asymmetrie-Smoke-Test (W_TOP je Seite verschieden, innerhalb validate(p)):
      Segmente valide, Union-Invariante, DFM grün; test_identische_segmente auf
      Symmetrie bedingen; Kammerraster-min()-Kopplung geprüft (Ledger 17/28/29, T6/T8)
      — Task 15: tests/test_asymmetrie.py, P_ASYM (46/60/48/55), Guard-Kommentar in
      tests/test_segments.py.
- [ ] I2: DFM-Überhang-Scan je Segment ins run_all-Gate (oder Freigabetext relativieren)
- [ ] I1: Datei-Manifest (SHA256) nach Export an Report anhängen + git-Hash aufnehmen
- [x] Ledger 10: test_deckflaeche-Schwelle aus Parametern berechnen statt 60000 hart
      — Task 15: tests/test_frame.py::test_deckflaeche_vorhanden, Formel wie
      Task-4-Review ((L*W - Öffnung - Freistellungsring)*0.9).
- [x] Ledger 21/22: min(W_TOP)-Kopplungen in dfm/frame seitenspezifisch machen
      — Task 15: model/frame.py::_chamber_cell_centers(p, side_w) + k<->Seite-Kanonik
      hergeleitet und dokumentiert (k=0 REAR, k=1 RIGHT, k=2 FRONT, k=3 LEFT);
      model/dfm.py::lap_step = (LAP_L-TOL_JOINT)*Summe(W_TOP). Symmetrie-Anchor
      bestätigt: chamber_slot_count/DFM-allowed bei Defaults bitidentisch zu vorher.

## Herstellbarkeits-Paket (User-Anforderung 2026-07-12: Verzugsfreiheit sicherstellen)
- [ ] Montagenotiz: ASA-Pflichtbedingungen (geschlossener Bauraum >=45 °C, Bett 100-110 °C,
      PEI+Brim 10 mm, Draft-Shield, Abkühlen im Bauraum, Tempern) — SOFORT nach Fix-Agent
- [ ] Eckkammern: Kammerstruktur um die Ecken ziehen, massiv nur ~30 mm um M5/Laps
      (eliminiert die 4 größten Schrumpfspannungs-Blöcke je Segment; Rework wie Task 14)
- [ ] DFM-Warp-Metrik: größten zusammenhängenden Massivquerschnitt je Segment berechnen
      und in Montagenotiz/Report ausweisen (Schwelle diskutieren)
- [ ] ASA-GF als Herstellbarkeits-Empfehlung dokumentieren (Verzug + CTE, Spec §3.5)

## Erkenntnisse aus der Heatmap-Analyse (2026-07-12, alle 4 LF auf 10-mm-Netz)
- [x] Noppenfuß-Radius/Fase (r1-2) am Zylinderansatz: ALLE Top-Hotspots aller Lastfälle
      sitzen an den Noppenfüßen des äußeren Rings (r~238, z~-0.8) — billigster Hebel
      gegen die einzige echte Kerbzone des Bauteils — Task 15: NOPPLE_FILLET=1.5,
      Übergangskegel 45° am Fuß (model/frame.py::build_frame), GEOM_REV=2.
- [ ] Elastische Bettung statt starrer Noppen-Fixierung in der FEM (Federelemente/
      weiche Zwischenschicht ~E_Sika): realistischere Lagerung würde die Konzentration
      an den Noppenfüßen deutlich senken (aktuell konservatives Artefakt)
- [ ] Heatmap-Workflow (fem_heatmap.py + render_heat.py, Session-Scratchpad) als
      fem/heatmap.py in die Pipeline übernehmen (PLY je LF + Hotspot-JSON im Report)

## Allgemeine Follow-ups (Priorität nach Bedarf)
- [ ] M1/Ledger 23/30/33: Formel-/Helfer-Duplikate konsolidieren (lap_height, min_band,
      groove_centerline_len, _rot -> features.py, _ensure_binary_paths -> fem)
- [ ] M2: INFILL_FACTOR-Semantik klären (toter Knopf seit Kammern; Montagenotiz koppeln)
- [ ] M3/Ledger 5: run_fem-Diagnose (leeres Ergebnis, fea.run()-Rückgabe)
- [ ] M4: Frame-Shape von run_all an export_all durchreichen (~20-30 s je Lauf)
- [ ] M5/Ledger 40: FREECAD_BUNDLE-Env-Override statt harter /Applications-Pfade; encoding="utf-8"
- [ ] M7: write_report-Guard gegen leeres fem_results
- [ ] Ledger 42: write_report -> (ok, vorbehalt) statt Text-Matching im Banner
- [ ] Ledger 2/4/6/9/12/32/34/36/37: Kleinkram laut Ledger-Triage
      (Ledger 3 [Immutability-Test] und Ledger 15 [Auszug-Sollwert-Test] durch Task 15
      erledigt: tests/test_params.py::test_params_frozen,
      tests/test_analytic.py::test_seitenschrauben_auszug Sollwert-Assertion)
- [ ] Optionaler Abmagerungs-Sweep (Wandstärken runter mit FEM-Gate). LF3 ist zwar mit
      63 % der rechnerisch engste Fall, aber eine bewusste Hüllkurve — real gibt es keine
      harte Klemmung (nur Zierblende unten, User 2026-07-12) → mehr Spielraum als es aussieht
