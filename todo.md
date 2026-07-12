# Follow-up-Register (aus dem finalen Whole-Branch-Review, 2026-07-12)

Detail-Historie: `.superpowers/sdd/progress.md` (Ledger). Vor-Merge-Fixes laufen separat
(validate(p), M5-Kommentare, Normlänge) — dieses File sammelt NUR die Follow-ups.

## Pflichtpaket VOR dem Messkampagnen-Re-Run
- [ ] I3: Asymmetrie-Smoke-Test (W_TOP je Seite verschieden, innerhalb validate(p)):
      Segmente valide, Union-Invariante, DFM grün; test_identische_segmente auf
      Symmetrie bedingen; Kammerraster-min()-Kopplung prüfen (Ledger 17/28/29, T6/T8)
- [ ] I2: DFM-Überhang-Scan je Segment ins run_all-Gate (oder Freigabetext relativieren)
- [ ] I1: Datei-Manifest (SHA256) nach Export an Report anhängen + git-Hash aufnehmen
- [ ] Ledger 10: test_deckflaeche-Schwelle aus Parametern berechnen statt 60000 hart
- [ ] Ledger 21/22: min(W_TOP)-Kopplungen in dfm/frame seitenspezifisch machen

## Herstellbarkeits-Paket (User-Anforderung 2026-07-12: Verzugsfreiheit sicherstellen)
- [ ] Montagenotiz: ASA-Pflichtbedingungen (geschlossener Bauraum >=45 °C, Bett 100-110 °C,
      PEI+Brim 10 mm, Draft-Shield, Abkühlen im Bauraum, Tempern) — SOFORT nach Fix-Agent
- [ ] Eckkammern: Kammerstruktur um die Ecken ziehen, massiv nur ~30 mm um M5/Laps
      (eliminiert die 4 größten Schrumpfspannungs-Blöcke je Segment; Rework wie Task 14)
- [ ] DFM-Warp-Metrik: größten zusammenhängenden Massivquerschnitt je Segment berechnen
      und in Montagenotiz/Report ausweisen (Schwelle diskutieren)
- [ ] ASA-GF als Herstellbarkeits-Empfehlung dokumentieren (Verzug + CTE, Spec §3.5)

## Allgemeine Follow-ups (Priorität nach Bedarf)
- [ ] M1/Ledger 23/30/33: Formel-/Helfer-Duplikate konsolidieren (lap_height, min_band,
      groove_centerline_len, _rot -> features.py, _ensure_binary_paths -> fem)
- [ ] M2: INFILL_FACTOR-Semantik klären (toter Knopf seit Kammern; Montagenotiz koppeln)
- [ ] M3/Ledger 5: run_fem-Diagnose (leeres Ergebnis, fea.run()-Rückgabe)
- [ ] M4: Frame-Shape von run_all an export_all durchreichen (~20-30 s je Lauf)
- [ ] M5/Ledger 40: FREECAD_BUNDLE-Env-Override statt harter /Applications-Pfade; encoding="utf-8"
- [ ] M7: write_report-Guard gegen leeres fem_results
- [ ] Ledger 42: write_report -> (ok, vorbehalt) statt Text-Matching im Banner
- [ ] Ledger 2/3/4/6/9/12/15/32/34/36/37: Kleinkram laut Ledger-Triage
- [ ] Optionaler Abmagerungs-Sweep (Wandstärken runter mit FEM-Gate; LF3/Klemmung ist
      der Treiber mit 63 % Auslastung) — User-Entscheid nach Messkampagne
