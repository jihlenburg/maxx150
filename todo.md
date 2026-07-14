# Follow-up-Register (aus dem finalen Whole-Branch-Review, 2026-07-12)

Detail-Historie: `.superpowers/sdd/progress.md` (Ledger). Vor-Merge-Fixes laufen separat
(validate(p), M5-Kommentare, Normlänge) — dieses File sammelt NUR die Follow-ups.

## Messkampagne A (2026-07-13): offene Design-Entscheidungen VOR dem Patch

Messwerte liegen in `messwerte.json` (Gruppe A weitgehend komplett; B + A3a/A3c/A4b
offen). Zwei Befunde verhindern die blinde 1:1-Übernahme — beide per
Wegwerf-Kopie + `validate()` belegt (Chat 2026-07-13):

- [ ] **W_TOP-Entscheidung**: Plattenflansch real nur 26 mm je Seite (A1c–f,
      Platte 450×450 VOLL symmetrisch — nur der Lüfter kragt nach hinten aus).
      1:1-Übernahme (Adapter 452×452) scheitert dreifach an validate():
      Außenwand hinter Kammerring 2 = −16 mm, M5-Senkung erreicht Außenwand.
      EMPFEHLUNG: W_TOP=50 belassen (Adapter bleibt 500×500 wie FEM-verifiziert,
      Platte liegt mittig, ~24 mm Deckflächen-Rand frei — Klebetrog A2a/A2b
      landet sicher auf dem Deck). Alternative (Optik): W_TOP=45 → 490×490,
      erfordert FEM-Re-Run. User entscheidet.
- [ ] **REC_GUSSET-Entscheidung**: A4a = A3b = 20 mm — ABER Fotos zeigen:
      Kragen + Clips + (vermutlich) Gussets zeigen nach OBEN zum Lüfter-Sockel,
      nicht nach unten. Mapping A4a→REC_GUSSET_D (20,5) NICHT anwenden
      (validate-Beweis: Deckrest −15,5). Tischtest beim User angefragt
      (Trogseite unten, liegt die Flanschfläche satt auf?); wenn satt:
      REC_GUSSET_D=0 setzen (model/frame.py: verträgt der Freistellungs-Cut
      D=0? DFM-Brückenzone Gusset-Freistellung entfällt dann).
- [ ] **Befestigungskonzept BESTÄTIGT (Seitenfoto)**: Platte hat ZWEI Kragen —
      oben Clip-Kragen (Lüfter-Sockel, A3b/A5a/A5b), unten Einbaukragen
      (~20 mm tief = A4a) mit SEITLICHEN Befestigungslöchern → Spec-Konzept
      „seitliche Schrauben Einbaukragen→Adapter-Innenwand" gilt unverändert,
      fem/analytic.py::side_screw_pullout bleibt. Noch nötig: F1–F3 (Loch-
      Anzahl/Positionen, z-Lage unter Flansch, Ø) + A3a/A3c am UNTEREN Kragen;
      Abgleich z-Lage ↔ INNER_WALL (voll massiv, unkritisch erwartet).
      REC_GUSSET_D=0 umsetzen (Gussets tauchen mit ein; frame.py D=0 prüfen,
      DFM-Brückenzone Gusset-Freistellung entfällt). B4-Messhinweis: Platte
      auf zwei Leisten, Kragen frei, bis FLANSCH-UNTERSEITE messen.
- [ ] A2c ist INVERS (−2-mm-Trog mit 2 dünnen Stegen, Stege tragen nicht) —
      Skizze `docs/messkampagne/messskizze_A_platte.svg` korrigiert;
      Auswirkung: Kleberaupe Platte→Deck bekommt definierte ~2 mm Dicke über
      Trogtiefe. Kein params-Feld betroffen.
- [ ] **Kreuzcheck Mittelloch <-> Segmentstoss**: Lochbild unterer Kragen
      (gemessen): 2 Seiten mit 3 Löchern (Mitte + Paar), 2 mit 2. Das
      MITTELLOCH liegt an der Seitenmitte = genau am Segmentstoss, F2 final
      GEMESSEN: Lochmitte 10 unter der Auflage = 15 über Adapter-Boden;
      Schraube Ø4 spannt 12..17 mm über Boden, Lap-Teilungsebene liegt bei
      12,5 — nur ~0,5 mm Luft zur Fuge. Schraube in die Stossfuge wäre schlecht: AUFGELÖST
      2026-07-13 (F1 gemessen: Mitte+-140 bzw. +-165): Ausweich-Orientierung
      gibt es NICHT (alle 4 Seiten tragen einen Stoss in Seitenmitte).
      Empfehlung: die 2 Mittellöcher planmäßig UNGENUTZT lassen -> 8
      Schrauben (8 x 356 N Auszug >> Lastniveau); optional nach Epoxid-
      Aushärtung als Dübel-Bonus setzen (3-mm-Kernloch, kreuzt die verklebte
      Lap-Teilungsebene). Alle Aussenpaare (+-140/+-165) liegen frei von der
      +-40-Stosszone, Innenwand ist ohnehin umlaufend massiv. In die
      Montagenotiz übernehmen (beim nächsten Parameterlauf).
- [ ] Noch zu messen: B1a/B1b/B2 (Freigang-Gate!), B3, B4, A3a, A3c,
      F2 (Loch-z) + F3 (Loch-Ø), Flanschdicke. Erledigt 2026-07-13
      nachmittags: A4b entfällt (Gussets innen), A6=346, A7=40, A8=6, A9=3,
      A10=2x8, Unterseiten-Kanalprofil 8/2/6/2/6/2, Gussets 4/Seite
      (G1=1 breit, G2=100 Teilung -> +-50/+-150) + Eck-Gussets,
      Lochbild F1a: Mitte+-140 (2 Seiten) / F1b: +-165 (2 Seiten).

## Externes Review 2026-07-14 — Adjudikation

SOFORT GEFIXT (Commit folgt):
- [x] messkampagne.py schlug W_TOP=26 / REC_GUSSET_D=19.5 vor (validate-
      Brecher; Mappings waren durch Design-Entscheidungen überholt) ->
      Mappings entfernt, explizite "BEWUSST NICHT uebernommen"-Meldung,
      NEUER Wächtertest mit der ECHTEN messwerte.json + validate().
- [x] run_all-Schlusszeile log "verifiziert freigegeben" auch bei
      PASS MIT VORBEHALT -> konditional ("KEINE Druckfreigabe").
- [x] manifest.py nahm GEOM_REV aus globalem PRM.P statt dem manifestierten
      Parameterobjekt -> p-Parameter durchgereicht.
- [x] FEM-Tempdirs (mkdtemp) wurden nie geloescht -> shutil.rmtree im
      finally (run_fem + heatmap), Altbestand gepurgt.
- [x] Spec-Drift Segment-Bbox (<=250 vs. Ist 277/Gate 300) -> Spec korrigiert.
- [x] Montagenotiz: Substrat-VORBEHALT fuer die 12 Dachschrauben (GFK/XPS/
      Holz in 10 mm Tiefe ungeprueft -> Probeschraube bei Demontage;
      bis dahin Lagesicherung, nicht tragende Redundanz).

BERECHTIGT, GROESSER — Roadmap (User entscheidet Priorität):
- [ ] Release-Zustaende statt PASS/Vorbehalt-Binarität: MODEL_PASS /
      PROTOTYPE_ONLY / BLOCKED / RELEASED; Export-Benennung daran koppeln.
      Heute blockt der Vorbehalt nur den Freigang, nicht Materialannahmen/
      fehlende physische Qualifikation.
- [ ] Provenienz je kritischem Eingang (Wert, Quelle, Status gemessen/
      Datenblatt/Schaetzung, Datum) statt nur ANNAHME-Kommentaren; Gate auf
      Provenienz. Läuft auf ein params-Metadaten-Schema hinaus.
- [ ] Physische Qualifikation VOR "verifiziert": Stoss-Coupon, XY+Z-Zugstaebe
      aus dem echten Druckprozess, Klebe-Coupons (GFK+ASA-GF, echte
      Vorbereitung), 1 Segment Verzugs-/Masskontrolle, Trocken-Fit,
      Thermozyklus+Fluttest. (Deckt sich mit geplantem PLA-Fit + Messkampagne,
      geht aber darüber hinaus.)
- [ ] FEM-Ausbau: Netz-Konvergenz 20/10/5, nachgiebige Noppen-Bettung
      (elastische Lager statt starr — deckt sich mit Alt-Punkt), Stoss-
      Submodell mit echter Lap-Geometrie+Bolzen, Kraeftegleichgewichts-Report.
- [ ] README/Statusseite (aktueller Hash, Release-Zustand, Reports),
      Run-Verzeichnisse unveraenderlich (Staging + Versionen der Tools).
- [ ] heatmap.run_capture dupliziert run_case-Setup ohne dessen
      Fehlerpruefungen -> konsolidieren; passung_stapel als Gate-Test
      einbinden; N_SEGMENTS!=4-Pseudoparameter entfernen oder implementieren.

ZURUECKGEWIESEN / RELATIVIERT:
- "identische Segmente vs. Asymmetrie widerspruechlich": Asymmetrie ist
  dokumentierte Parameter-OPTION (Messkampagnen-Vorsorge, tests/
  test_asymmetrie.py); Default ist symmetrisch-identisch. Kein Defekt.
- "kein Report fuer dfc6857f": korrekt, aber Artefakt-, kein Code-Problem —
  Lauf nachgeholt (out/report_dfc6857f.md).

## Unterkragen (GEOM_REV 3, 2026-07-13)

- [x] Unterkragen implementiert (params BOT_KRAGEN_*, frame._bot_kragen_tools,
      Segmente-Lappen bis Kragenkante, DFM-Zone 7, Montagenotiz, 6 Tests grün,
      validate()-Gates). 12 Löcher = 3 je Seite bei -140/+60/+140 (identische
      Segmente; User-Entscheidung statt exakt 10 wie Anleitung).
- [ ] Volle Suite + run_all nach B-Messwerten (ein Lauf für alles); FEM-Report
      neu (Hash wechselt durch GEOM_REV 3 + BOT_KRAGEN-Felder).
- [ ] fem/analytic: Auszugs-/Lochleibungs-Nachweis der 12 Dachschrauben
      ergänzen (analog side_screw_pullout; nicht blockierend -- Schrauben sind
      Redundanz ZUM Kleber, nicht alleinige Befestigung).

## Pflichtpaket VOR dem Messkampagnen-Re-Run
- [ ] Würth/OEM nach gedruckten Kennwerten (XY+Z) und CTE fragen — würde
      Annahmen durch Messwerte ersetzen (senkt Fugenauslastung von 21 % weiter
      UND ersetzt die Druckwert-Annahmen `E_BASE`/`SIGMA_BASE`) — Task 21:
      Würth ASA GF15 (Art. 4954641201) Datenblatt liefert nur HALBZEUG-Werte
      (Spritzguss-Probekörper, Zug 91,2/E 3520/3500 MPa) — `E_BASE=3000.0`/
      `SIGMA_BASE=45.0` sind DOKUMENTIERTE ANNAHMEN für die gedruckten
      XY-Werte (abgeleitet aus GF-ASA-Analoga, s. params.py-Kommentar), keine
      Messwerte. `DERATE_Z=0.5` ist ebenfalls GESCHÄTZT (kein Z-Probekörper
      im Blatt, strenger als Bambus gemessene 0,8). `CTE_ASA=60e-6` bleibt
      unverändert seit Task 19 eine konservative Obergrenze (auch das
      Würth-Blatt nennt keinen CTE-Wert). Ein belegter, niedrigerer CTE-Wert
      senkt `fem.analytic.glue_shear_utilization` unter die aktuellen ~21 %
      weiter (Spec §3.5 „Offene Punkte").
- [x] I3: Asymmetrie-Smoke-Test (W_TOP je Seite verschieden, innerhalb validate(p)):
      Segmente valide, Union-Invariante, DFM grün; test_identische_segmente auf
      Symmetrie bedingen; Kammerraster-min()-Kopplung geprüft (Ledger 17/28/29, T6/T8)
      — Task 15: tests/test_asymmetrie.py, P_ASYM (46/60/48/55), Guard-Kommentar in
      tests/test_segments.py.
- [x] I2: DFM-Überhang-Scan je Segment ins run_all-Gate (oder Freigabetext relativieren)
      — Task 16: run_all.py baut frame+segments EINMAL, prüft je Segment
      dfm.overhang_area gegen allowed*1.2+200 VOR dem Export (Exit 1 + Meldung bei
      Verletzung); export_all(p, out_dir, frame=None, segments=None) nimmt beide
      optional entgegen (rückwärtskompatibel) statt sie intern neu zu bauen (M4,
      spart ~20-30 s/Lauf). Freigabetext „verifiziert freigegeben" stimmt jetzt.
- [x] I1: Datei-Manifest (SHA256) nach Export an Report anhängen + git-Hash aufnehmen
      — Task 16: neu export/manifest.py::append_manifest(report_path, files, git_rev)
      hängt „## Datei-Manifest" (SHA256 je Exportdatei, Git-Commit, GEOM_REV) an den
      Report an; run_all.py ruft es NACH export_all mit `git rev-parse HEAD` auf.
      tests/test_manifest.py (3 Tests).
- [x] Ledger 10: test_deckflaeche-Schwelle aus Parametern berechnen statt 60000 hart
      — Task 15: tests/test_frame.py::test_deckflaeche_vorhanden, Formel wie
      Task-4-Review ((L*W - Öffnung - Freistellungsring)*0.9).
- [x] Ledger 21/22: min(W_TOP)-Kopplungen in dfm/frame seitenspezifisch machen
      — Task 15: model/frame.py::_chamber_cell_centers(p, side_w) + k<->Seite-Kanonik
      hergeleitet und dokumentiert (k=0 REAR, k=1 RIGHT, k=2 FRONT, k=3 LEFT);
      model/dfm.py::lap_step = (LAP_L-TOL_JOINT)*Summe(W_TOP). Symmetrie-Anchor
      bestätigt: chamber_slot_count/DFM-allowed bei Defaults bitidentisch zu vorher.
- [x] Review-Critical (Achsen-Fehlbezug) auf obigem Ledger-21/22-Fix: die erste
      Fassung nahm für die u-Bandlänge fälschlich die EIGENE W_TOP der Seite statt
      der beiden SENKRECHTEN Nachbarseiten (physische Bandgrenze) — bei Asymmetrie
      (z. B. W_TOP_REAR=90, Rest 50) erodierte das SOLID_CORNER bzw. hätte
      Phantom-Slots erzeugt. Fix (Task-15-Nachbesserung): model/frame.py::
      _side_neighbor_bounds(p) kapselt die Kanonik (k=0 REAR: +u←W_TOP_RIGHT/
      -u←W_TOP_LEFT; k=1 RIGHT: +u←W_TOP_FRONT/-u←W_TOP_REAR; k=2 FRONT:
      +u←W_TOP_LEFT/-u←W_TOP_RIGHT; k=3 LEFT: +u←W_TOP_REAR/-u←W_TOP_FRONT),
      hergeleitet UND per Skript-Probe an echter Geometrie verifiziert (Rotations-
      Mapping (x,y)->(-y,x) je k). _chamber_cuts/chamber_slot_count bauen +u-/-u-
      Hälfte jetzt unabhängig mit ihrer jeweiligen Nachbargrenze (keine pauschale
      Spiegelung derselben Liste mehr). Symmetrie-Anker bei Defaults bitidentisch
      (slots=24, dfm_allowed=36788.23334770628, frame.Volume=1736006.070242394).
      Neue Tests: tests/test_asymmetrie.py (3 neu: REAR-Band-Nachbargrenze,
      Slot-Count-Konsistenz, geometrische Eck-Probe). Dabei entdeckt: der ERSTE
      Entwurf des Eck-Prüfquaders im Review-Befund (x/y 210..240) liegt legitim
      im Reichweitenbereich der reziprok mitwachsenden RIGHT/LEFT-Seite (RIGHTs
      -u-Grenze ist laut derselben Kanonik W_TOP_REAR) — keine Erosion, sondern
      beabsichtigte Konsequenz derselben Formel (Skript-Beweis: 6626 mm³
      Differenz trotz korrekter Formel). Test nutzt stattdessen einen isolierten,
      per Skript verifizierten Prüfquader (y 193..199), der REARs eigenen Fehler
      von RIGHTs legitimer reziproker Zelle trennt (alte Formel dort nachweislich
      1463.5 mm³ hohl, neue Formel exakt massiv). Details: .superpowers/sdd/
      task-15-report.md (Abschnitt „Review-Nachbesserung").

## Herstellbarkeits-Paket (User-Anforderung 2026-07-12: Verzugsfreiheit sicherstellen)
- [x] Montagenotiz: Verzugs-Pflichtbedingungen — erledigt (15bd068), Task 19 auf
      Bambu-ASA-CF-Profil (Bett 80-100 °C, Kammer 45-60 °C), seit Task 21 auf
      Würth-ASA-GF15-Profil aktualisiert (Düse 250-270 °C gehärtet, Bett
      100-110 °C, geschlossener Bauraum PFLICHT, Schrumpf 0,3 % lt. Blatt)
- [x] Eckkammern: Kammerstruktur um die Ecken ziehen, massiv nur ~30 mm um M5/Laps
      (eliminiert die 4 größten Schrumpfspannungs-Blöcke je Segment; Rework wie Task 14)
      — VOLLSTÄNDIG ERLEDIGT/AKTIVIERT: seit Task 20 (User-Entscheidung 2026-07-12)
      Default EIN (CORNER_CHAMBERS=True; neuer Default-Anker 1694758.489540970 mm³,
      AUS-Variante bleibt anker-geprüft 1736006.070242394 mm³; GEOM_REV bleibt 2,
      params_hash wechselt über das Feld selbst — Details .superpowers/sdd/
      task-20-report.md).
      — Task 17: params.py::CORNER_CHAMBERS (Default AUS)/CORNER_ANGLE_MARGIN=18°;
      model/frame.py::_corner_chamber_cuts (90°-Rotationssektor je Ecke, Ring1 r13-28/
      Ring2 r32-47 relativ zum Eckzentrum (CUTOUT_W/2-CUTOUT_R, dito), Part.Face.revolve
      um den Ursprung + _rot auf alle 4 Ecken, 2 Diagonal-Vents je Ecke); DFM Zone 6
      (model/dfm.py, 8 Eck-Vents); PRM.validate() prüft CORNER_CHAMBERS->CHAMBERS-
      Voraussetzung + Winkelmargin-Kollisionsungleichung (sektor_extreme >= band_end+3,
      bei Defaults 209.5 >= 208, PASS). Volumendelta EIN-Variante 41247.6 mm³, Restwand
      an der Diagonale 25.8 mm. Default (CORNER_CHAMBERS=False) geometrisch unverändert
      (Volumen-Anker 1736006.070242394 mm³ bitidentisch), params_hash ändert sich
      zwangsläufig durch die 2 neuen Felder (eccafbc1 statt vorher). 66/66 Tests grün.
      Details: .superpowers/sdd/task-17-report.md.
- [x] Review-Critical-Fix auf obigem Task-17-Eintrag: validate() verglich fälschlich
      den UNKRITISCHEN Sektor-Außenradius (r_out2) statt des kritischen Innenradius
      (r_in1, entlang des margin-Strahls y(x)=off+tan(margin)*(x-off) wächst y
      monoton mit x) -- empirisch belegt: CORNER_CHAMBERS=True+CELL_L=53 überschnitt
      real um 516.3 mm³, obwohl validate() PASS meldete und isValid() True blieb
      (Boolean-Cut mit überlappenden Werkzeugen bleibt topologisch gültig). Fix:
      model/frame.py::_corner_keepout(p) + Filter (NACH der Zentrierung, NICHT als
      band_end-Ersatz VOR ihr -- sonst hätte sich bei Defaults die ganze Zentrierung
      verschoben und den Volumen-Anker gebrochen) in _chamber_cell_centers; neuer
      Parameter CORNER_GAP=3.0; validate() prüft nur noch Kohärenz (Platz für
      mind. 1 Zelle). Anker bitidentisch (P 1736006.07, P_ECK 1694758.49, Delta
      41247.58 mm³), corner_keepout(P_ECK)=196.22 mm. 2 neue Regressionstests
      (68/68 Tests grün). Details: .superpowers/sdd/task-17-report.md §11.
- [x] Task-17-Re-Review Minor 2 (Werkzeugzahl-Konsistenztest fehlte): Task 16 —
      tests/test_eckkammern.py::test_eckkammern_werkzeugzahl_konsistent_zu_slot_count_
      cell_l_53 prüft len(_chamber_cuts) == 4*chamber_slot_count + 16 (fixe
      Eck-Werkzeuge) explizit bei CORNER_CHAMBERS=True+CELL_L=53 (Reviewer-
      Regressionsrezept); Gegenprobe test_eckkammern_werkzeugzahl_konsistent_ohne_
      eckkammern für CORNER_CHAMBERS=False (Eck-Term muss 0 sein).
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
- [x] Heatmap-Workflow (fem_heatmap.py + render_heat.py, Session-Scratchpad) als
      fem/heatmap.py in die Pipeline übernehmen (PLY je LF + Hotspot-JSON im Report)
      — Task 18: fem/heatmap.py (heatmap_all/classify/cmap/write_ply/hotspots),
      scripts/heatmap_run.py + scripts/heatmap.sh, render/blender_heatmap.py,
      tests/test_tools_heatmap.py.

## Allgemeine Follow-ups (Priorität nach Bedarf)
- [x] M1/Ledger 23/30/33: Formel-/Helfer-Duplikate konsolidieren (lap_height, min_band,
      groove_centerline_len, _rot -> features.py, _ensure_binary_paths -> fem)
      — Task 16: params.py::min_band/lap_height/groove_centerline_len (+ validate()
      nutzt min_band selbst); Verbraucher fem/analytic.py (joint_checks,
      glue_load_shear), fem/joint_check.py, export/export.py umgestellt.
      model/features.py::rotz(shape, k) ersetzt die identischen lokalen _rot()-Kopien
      in model/frame.py UND model/segments.py (Wrapper entfernt, tests/
      test_eckkammern.py auf F.rotz umgestellt). tests/test_toolchain.py importiert
      _ensure_binary_paths jetzt aus fem.run_fem. BEWUSST NICHT angefasst:
      model/dfm.py::_allowed_bridge_area nutzt seit Ledger 21/22 bewusst die SUMME
      aller vier W_TOP statt eines globalen Minimums (seitenspezifische Zellraster)
      — ein min_band(p) dort wäre eine Regression, siehe Docstring von
      params.min_band. Anker bitidentisch: frame.Volume 1736006.070242394,
      dfm_allowed 36788.23334770628, tau 0.384, Lochleibung 6.98, wind_force 480.0.
- [ ] M2: INFILL_FACTOR-Semantik klären (toter Knopf seit Kammern; Montagenotiz koppeln)
- [x] M3/Ledger 5/32: run_fem-Diagnose (leeres Ergebnis, fea.run()-Rückgabe) — Task 16:
      fem/run_fem.py::run_case wirft RuntimeError statt IndexError bei leerer
      Ergebnisliste (inkl. ccx-Arbeitsverzeichnis-Hinweis) und prüft fea.run() explizit
      (RuntimeError bei rc != True). Rückgabe-dict zusätzlich "defl_top_is_fallback"
      (True im Submodell-Fall ohne echte Deckflächen-Knoten, Ledger 32); fem/report.py
      druckt „(Fallback)" dahinter.
- [x] M4: Frame-Shape von run_all an export_all durchreichen (~20-30 s je Lauf) —
      Task 16, zusammen mit I2 (siehe oben): export_all(p, out_dir, frame=None,
      segments=None) baut nur, was nicht übergeben wurde.
- [x] M5/Ledger 40: FREECAD_BUNDLE-Env-Override statt harter /Applications-Pfade; encoding="utf-8"
      — Task 16: bin/fc + fem/run_fem.py::BUNDLE_BIN lesen
      os.environ.get("FREECAD_BUNDLE", ...); scripts/render.sh + heatmap.sh:
      set -euo pipefail + BLENDER_BIN=${BLENDER_BIN:-$(command -v blender)};
      encoding="utf-8" in fem/report.py, export/export.py, export/manifest.py,
      scripts/messkampagne.py (run_all.py braucht nach Ledger 42 keinen eigenen
      read_text/write_text mehr).
- [x] M7: write_report-Guard gegen leeres fem_results — Task 16: ValueError
      ("kein Lastfall zur Verifikation") statt eines stillen/leeren Reports.
- [x] Ledger 42: write_report -> (ok, vorbehalt) statt Text-Matching im Banner —
      Task 16: fem/report.py::write_report liefert tuple[bool, bool]; run_all.py
      gated direkt darauf (kein "Vorbehalt"-Grep im Reporttext mehr für die
      Gate-Entscheidung); tests/test_report.py komplett umgestellt (5 Tests: alle
      drei Fälle + M7-ValueError + Fallback-Annotation).
- [ ] Ledger 2/4/6/9/12/32/34/36/37: Kleinkram laut Ledger-Triage — TEILWEISE erledigt
      (Ledger 3 [Immutability-Test] und Ledger 15 [Auszug-Sollwert-Test] durch Task 15
      erledigt: tests/test_params.py::test_params_frozen,
      tests/test_analytic.py::test_seitenschrauben_auszug Sollwert-Assertion;
      Ledger 2/4/12/37 [FREECAD_BUNDLE/encoding] und 32 [defl_top-Fallback] durch
      Task 16 erledigt, siehe M5/M3-Einträge oben. NOCH OFFEN: Ledger 6/9/34/36 —
      in Task-16-Brief nicht referenziert, keine eindeutige Zuordnung ohne
      Rücksprache mit dem ursprünglichen Ledger-Text gefunden.)
- [ ] Optionaler Abmagerungs-Sweep (Wandstärken runter mit FEM-Gate). LF3 ist zwar mit
      63 % der rechnerisch engste Fall, aber eine bewusste Hüllkurve — real gibt es keine
      harte Klemmung (nur Zierblende unten, User 2026-07-12) → mehr Spielraum als es aussieht
