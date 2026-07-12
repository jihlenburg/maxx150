# Logbook (repo-lokale Arbeitsnotizen)

Ergänzt `todo.md` (Follow-up-Register) um eine chronologische Kurzfassung der
Session-Arbeit. Ausführliche Nachweise/Istwerte je Task: `.superpowers/sdd/task-*-report.md`.

## 2026-07-12 — Task 15: Geometrie-Korrektur + parametrische Robustheit

Quelle: `.superpowers/sdd/task-15-brief.md` (Finalreview I3 + Heatmap-Analyse +
User-Auftrag „alles vor der Messkampagne Mögliche"). Ausgangsstand: 7524cda,
45/45 Tests grün, params_hash `9f91735a`.

- Baseline vor Änderung erfasst (Suite 45/45, params_hash `9f91735a`,
  chamber_slot_count=24, dfm_allowed=36788.23, lap_step=4950.0,
  frame_volume=1733843.08 mm³, top_area=60234.49 mm²).
- params.py: `GEOM_REV=2` (Meta, erhöht bei geometrie-wirksamen Code-Änderungen
  ohne Messwert), `NOPPLE_FILLET=1.5` (Kerbentschärfung Noppenfuß, Heatmap
  2026-07-12). validate(p): `NOPPLE_FILLET>=0`,
  `NOPPLE_SPACING >= 3*NOPPLE_R + 2*NOPPLE_FILLET`.
- model/frame.py: Übergangskegel (45°-Flanke, Part.makeCone) am Noppenfuß,
  fused mit dem Zylinder. `_chamber_cell_centers(p, side_w)` seitenspezifisch
  statt global `min(W_TOP)` (Ledger 21/22). k<->Seite-Kanonik aus dem Code
  hergeleitet UND empirisch an der Geometrie verifiziert (Skript-Probe,
  nicht nur Formel-Lesen): k=0 REAR, k=1 RIGHT, k=2 FRONT, k=3 LEFT.
  `chamber_slot_count` jetzt Summe je Seite statt `4*2*n`.
- model/dfm.py: `lap_step = (LAP_L-TOL_JOINT) * Summe(W_TOP)` statt
  `4*(LAP_L-TOL_JOINT)*min(W_TOP)` — bei symmetrischen Defaults exakt
  identisch (4*49.75... eher 4*24.75*50 == 24.75*200 == 4950).
- Symmetrie-Anker bei Defaults NACH der Änderung geprüft (Skript-Probe):
  chamber_slot_count 24 (unverändert), dfm_allowed 36788.23334770628
  (bit-identisch), lap_step 4950.0, top_area 60234.48682836788
  (bit-identisch), chamber_volume_delta 391726.316... (identisch bis auf
  Float-Rauschen). Einzige Abweichung: frame_volume +2163 mm³
  (Noppenkegel-Zusatzvolumen, wie im Brief erwartet). params_hash neu:
  `88bacca5`.
- Neue/geänderte Tests: tests/test_params.py::test_params_frozen (Ledger 3),
  tests/test_frame.py::test_deckflaeche_vorhanden (Ledger 10, Formel statt
  60000 hart), tests/test_analytic.py::test_seitenschrauben_auszug
  (Sollwert-Assertion 266.0 N, Ledger 15), tests/test_segments.py Guard-
  Kommentar (Symmetrie-Voraussetzung), tests/test_asymmetrie.py (neu, 3
  Tests: Frame valide, Segmente valide+überschneidungsfrei+BBox, DFM-Gate) —
  P_ASYM = W_TOP(FRONT 46/REAR 60/LEFT 48/RIGHT 55).
- 1. voller Suite-Lauf: 48/49 bestanden -- 1 Fund: test_loadcases.
  test_face_selektoren (nopple_faces sammelte durch den neuen
  Übergangskegel eine zusätzliche, fälschlich mitselektierte
  Zylinder-Restfläche je Noppe ein, reiner CoM-Toleranzfilter ohne
  Ebenheits-/Normalencheck). Fix: fem/loadcases.py::nopple_faces jetzt wie
  top_faces() exakt auf Part.Plane + Normale gefiltert; ungenutzte
  _planar_faces() entfernt. Reduziert Regressionsrisiko (selektiert wieder
  exakt dieselben Flächen wie vor Task 15).
- 2. voller Suite-Lauf (final): 49/49 bestanden (out/run_tests_t15_v2.log).
- Produktionslauf `bin/fc run_all.py` (Hintergrund, out/run_all_t15.log):
  129 s (alt 128 s), params_hash 88bacca5, alle LF + Stoß PASS. LF1 0.79
  (alt 0.85, −7 %), LF2 0.43 (alt 0.44), LF3 2.24/3.36 (alt 2.13/3.36,
  +5 %, weiterhin engster Fall aber unkritisch), LF4 0.19 (alt 0.18),
  Stoß 3.37 (unverändert). Kein Delta > 15 % -> test_regression.py-
  Referenzwerte unverändert gelassen. PASS mit Vorbehalt (Haubenfreigang,
  unverändert vorbestehend, nicht Task-15-Scope).
- todo.md abgehakt: I3, Ledger 10, Ledger 21/22, Noppenfuß-Radius-Punkt,
  Ledger 3/15 (im Kleinkram-Eintrag vermerkt).
- Vollständiger Nachweis: `.superpowers/sdd/task-15-report.md`.

## 2026-07-12 — Task 15 Nachbesserung: Review-Critical Achsen-Fehlbezug (Stand 24f6fe1)

Befund (Final-Review nach Task 15): `_chamber_cell_centers` nutzte für die
u-Bandlänge (Zellposition entlang einer Seite) die EIGENE W_TOP der Seite
statt der beiden SENKRECHTEN Nachbarseiten, die die Bandlänge physisch
begrenzen. Bei symmetrischen Defaults unsichtbar (eigene W_TOP == Nachbar-
W_TOP), bei Asymmetrie (z. B. W_TOP_REAR=90, Rest 50) erodiert das
SOLID_CORNER bzw. erzeugt Phantom-Slots jenseits des Rahmenrandes.

- Kanonik verifiziert (Rotations-Mapping `(x,y)->(-y,x)` je 90°-Schritt,
  hergeleitet UND per Skript-Probe an echter Geometrie bestätigt, siehe
  `model/frame.py::_side_neighbor_bounds`-Docstring): k=0 REAR (+u←RIGHT,
  -u←LEFT), k=1 RIGHT (+u←FRONT, -u←REAR), k=2 FRONT (+u←LEFT, -u←RIGHT),
  k=3 LEFT (+u←REAR, -u←FRONT).
- `model/frame.py`: `_chamber_cell_centers(p, limit_w)` unverändert in der
  Formel, aber `limit_w` jetzt explizit als Nachbargrenze dokumentiert;
  neue `_side_neighbor_bounds(p)` kapselt die Kanonik; `_chamber_cuts`/
  `chamber_slot_count` bauen +u-/-u-Hälfte jetzt UNABHÄNGIG mit ihrer
  jeweiligen Nachbargrenze (vorher: `[-c for c in half]` derselben Liste).
- Symmetrie-Anker bei Defaults bitidentisch zu 24f6fe1: chamber_slot_count
  24, dfm._allowed_bridge_area 36788.23334770628, frame.Volume
  1736006.070242394, params_hash unverändert 88bacca5 (nur Code geändert,
  keine Parameterwerte).
- Neue Tests `tests/test_asymmetrie.py` (P_CORNER = W_TOP_REAR=90, Rest
  Default): REAR-Band bleibt ≤ 205 (Nachbargrenze LEFT/RIGHT=50, nicht
  REARs eigene 90); chamber_slot_count konsistent zu `len(_chamber_cuts)/4`;
  geometrische Eck-Probe (Prüfquader, common==Quadervolumen).
- Entdeckung bei der Eck-Probe: der im Befund vorgeschlagene Prüfquader
  (x/y 210..240) liegt legitim im Reichweitenbereich der reziprok
  mitwachsenden RIGHT-Seite (RIGHTs -u-Grenze ist laut derselben Kanonik
  W_TOP_REAR) — RIGHT wird durch REAR=90 physisch länger und bekommt dort
  KORREKT eine zusätzliche Zelle, keine Erosion. Skript-Beweis: an dieser
  Box weicht common-Volumen um 6626 mm³ vom Quadervolumen ab, OBWOHL die
  Formel exakt der Review-Vorgabe (Punkt 1) entspricht. Test verwendet
  stattdessen einen per Skript verifizierten, isolierten Prüfquader
  (x 210..240, y 193..199, z 6..18): trennt REARs eigenen (vormals
  fehlerhaften) Beitrag von RIGHTs legitimer reziproker Zelle. Beleg: unter
  der alten (eigene-W_TOP-)Formel wäre dieselbe Box um 1463.5 mm³ hohl
  gewesen (Regressionsnachweis), unter der neuen Formel exakt massiv (diff
  0.0000 mm³).
- Tests: `TEST_FILTER=asymmetrie` 6/6 grün (3 alt + 3 neu). Volle Suite
  56/56 grün, 0 fehlgeschlagen (davon 4 aus unbeteiligten, ungetrackten
  Testdateien eines parallelen Arbeitsstands im selben Repo — eigener
  Tracked-Beitrag 49 Basis + 3 neu = 52).
- Commit: gemäß CLAUDE.md-Vorgabe ("nie automatisch committen, erst nach
  Freigabe") NICHT automatisch erstellt — Änderungen liegen bereit
  (`model/frame.py`, `tests/test_asymmetrie.py`), Commit-Message im Report
  hinterlegt.
- Vollständiger Nachweis: `.superpowers/sdd/task-15-report.md`
  (Abschnitt „Review-Nachbesserung: Achsen-Fehlbezug").

## 2026-07-12 — Task 17: Eckkammern (parametrisierbar, Default AUS)

Quelle: `.superpowers/sdd/task-17-brief.md` (Herstellbarkeits-Paket,
todo.md). Ausgangsstand: d348e91, 60/60 Tests grün.

- params.py: `CORNER_CHAMBERS: bool = False` (Default AUS, verifizierter
  Stand bleibt geometrisch unverändert), `CORNER_ANGLE_MARGIN: float = 18.0`
  (Grad Randabstand des 90°-Sektors je Seite). validate(p): neuer Block
  `if p.CORNER_CHAMBERS` — (a) CHAMBERS-Voraussetzung, (b)
  0<CORNER_ANGLE_MARGIN<45, (c) Kollisions-Ungleichung Ecksektor <-> gerade
  Zellbänder (`sektor_extreme = off + r_out2_rel*sin(radians(margin))` muss
  >= größter vorkommender `band_end + 3mm` sein; bei Defaults 209.524 >= 208,
  PASS).
- model/frame.py: `_ring_radii(p)` als DRY-Helfer aus `_chamber_cuts`
  extrahiert (auch von der neuen Funktion genutzt). Neue
  `_corner_chamber_cuts(p)`: kanonisches Pentagon-Profil (identisch
  `_chamber_profile_face`) in der Ebene y=0 gebaut, um CORNER_ANGLE_MARGIN
  vorrotiert, `Part.Face.revolve(Ursprung, (0,0,1), 90-2*margin)` -> Solid,
  danach auf das Eckzentrum (CUTOUT_W/2-CUTOUT_R, dito) verschoben, dann per
  `_rot(shape,k)` (Rotation um den GLOBALEN Ursprung) auf alle 4 Ecken
  verteilt — KEINE Spiegelung nötig (kanonischer Sektor liegt symmetrisch
  zur 45°-Diagonale). Je Ecke 2 Diagonal-Vents (analog den Seiten-Vents).
  `_chamber_cuts` hängt die Eckkammer-Werkzeuge an dieselbe tools-Liste an
  (ein gemeinsamer cut()+removeSplitter() in build_frame, wie im Brief
  gefordert).
- model/dfm.py: `_allowed_bridge_area` Zone 6 (8 Eck-Vents, Formel wie
  Brief, Faktor 2 zusätzlich wegen diagonaler statt achsparalleler Kanäle,
  nur wenn CORNER_CHAMBERS) — dokumentiert, warum die Chevron-Sektorböden
  selbst keinen eigenen Term brauchen (>45° in jeder Radialebene, wie
  Zone 5).
- Geometrie-Beleg (Skript-Probe, siehe Report): Default-Volumen unverändert
  1736006.070242394 mm³ (Symmetrie-Anker aus Task-15-Ledger, bitidentisch).
  EIN-Variante (P_ECK = CORNER_CHAMBERS=True): Volumen 1694758.49 mm³,
  Delta 41247.58 mm³ (Band 2.5e4..7e4 laut Brief). Restwand an der
  45°-Diagonale zur Außenkontur: 25.81 mm (Brief-Schätzung „≈26mm"
  bestätigt). params_hash(P)=`eccafbc1` (ändert sich zwangsläufig durch die
  2 neuen Felder, GEOM_REV bleibt 2), params_hash(P_ECK)=`177d6901`.
- Neue Tests `tests/test_eckkammern.py` (6): Frame valide+1 Shell, Volumen-
  delta-Band, Segmente valide+überschneidungsfrei, DFM-Gate, validate()
  wirft ValueError ohne CHAMBERS, Default-Anker (Volumen + Hash-Diff-Nach-
  weis). Alle 6 grün; volle Suite 66/66 grün, 0 fehlgeschlagen.
- Rendering-Beleg: Wegwerf-Skripte (render/make_views_stl.py kann
  params.P nicht per Parameter überschreiben) bauen P_ECK, schneiden bei
  z=14 horizontal (wie render/make_views_stl.py::ZCUT) und rendern eine
  Top-Down-Orthoansicht: `out/render/task17_eck/v_schnitt_horizontal.png`
  — zeigt alle 4 Eck-Sektoren (Ring 1 + Ring 2, mit sichtbarem
  Margin-Abstand zu den geraden Zellbändern) klar von den geraden
  Kammerzellen abgesetzt.
- Vollständiger Nachweis: `.superpowers/sdd/task-17-report.md`.

## 2026-07-12 — Task 17 Review-Critical-Fix: falscher Referenzradius in validate()

Ausgangsstand: `80c6fbb`, 66/66 grün. Befund: die `validate()`-Kollisions-
ungleichung verglich den Sektor-Außenradius (`r_out2`) mit der Zellband-
grenze — der kritische Punkt liegt aber am Innenradius `r_in1` (entlang
des margin-Strahls `y(x)=off+tan(margin)*(x-off)` wächst `y` monoton mit
`x`). Vor jeder Code-Änderung per Skript reproduziert:
`Params(CORNER_CHAMBERS=True, CELL_L=53.0)` — `validate()` PASS,
`build_frame().isValid()` `True` (1 Shell), aber reale Überschneidung
letzte-Ring1-Zelle/Ecksektor = **516.2968692898736 mm³** (Boolean-Probe).

- model/frame.py: neue Funktion `_corner_keepout(p)` (`off +
  tan(radians(CORNER_ANGLE_MARGIN))*(r_in1-off) - CORNER_GAP`, Defaults
  196.223956 mm). `_chamber_cell_centers` wendet sie als **Filter NACH**
  der bestehenden Zentrierung an. Wichtig: ein direktes `band_end =
  min(band_end, corner_keepout)` VOR der Margin-Berechnung wurde erst
  probiert und dann verworfen, weil es bei Defaults ALLE Zellzentren
  verschoben hätte (letzte Zelle 193→188.6 mm, numerisch nachgerechnet) —
  das hätte den unveränderlichen Default-Volumen-Anker gebrochen, obwohl
  das natürliche Raster den Keepout ohnehin schon einhält.
- params.py: neuer Parameter `CORNER_GAP: float = 3.0`. `validate()`:
  die widerlegte `sektor_extreme`-Ungleichung entfernt, ersetzt durch
  Kohärenzprüfung `corner_keepout > SOLID_JOINT_HALF` + `CORNER_GAP >=
  1.0`.
- Docstrings korrigiert (`model/frame.py::_corner_chamber_cuts` §
  „Kollisionsfreiheit", `params.py::validate`): r_in1 statt r_out2,
  Herleitung y(x) monoton in x. Klarstellung zum alten Minor-Fund („Brief
  widerspricht Zahlenbeispiel", Report §10): der Fehlbezug betraf sowohl
  Richtung als auch Referenzradius.
- 2 neue Tests `tests/test_eckkammern.py` (jetzt 8 statt 6):
  Regressionsprobe (`CELL_L=53`: gefiltertes Raster `[66.5,122.5]` statt
  `[66.5,122.5,178.5]`, Summen-Overlap aller Zell- vs. Sektor-Kavitäten
  < 1e-6 mm³, `build_frame` weiter valide) + exakter P_ECK-Volumen-/Delta-
  /Keepout-Anker.
- Anker bitidentisch: `build_frame(PRM.P).Volume`=1736006.070242394 mm³,
  `build_frame(P_ECK).Volume`=1694758.489540970 mm³, Delta=41247.580701424
  mm³ — alle Diffs 0.0. `params_hash` ändert sich zwangsläufig durch das
  neue Feld: `P`=`da0d8553` (vorher `eccafbc1`), `P_ECK`=`d1eee427`
  (vorher `177d6901`).
- Volle Suite: `timeout 700 bin/fc tests/run_tests.py` → **68 bestanden,
  0 fehlgeschlagen**.
- Vollständiger Nachweis: `.superpowers/sdd/task-17-report.md` §11.

## 2026-07-12 — Task 16: Gate-Härtung + Konsolidierung (Abschluss Vor-Messkampagnen-Paket)

Ausgangsstand: `ff14e9a`, 68/68 grün, `params_hash` `da0d8553`. Quelle:
`.superpowers/sdd/task-16-brief.md` (7 Blöcke, Reihenfolge 6→4→1→2→3→5→7).
Reine Härtung/Refaktorierung + 2 neue Features (Manifest, DFM-Gate) — keine
Params-Feldänderung, Hash bleibt zwangsläufig unverändert.

- Block 6 (Kleinkram): `FREECAD_BUNDLE`-Env-Override in `bin/fc` +
  `fem/run_fem.py`; `scripts/{render,heatmap}.sh` → `set -euo pipefail` +
  `BLENDER_BIN=${BLENDER_BIN:-$(command -v blender)}`; `encoding="utf-8"`
  in report/export/messkampagne; `params.RHO_AIR=1.2` statt Magic Number;
  `test_toolchain.py` try/finally um `closeDocument`; `fem/analytic.py`
  ungenutztes `sig_lang` entfernt; `test_export.py` alle 3 Tests
  Reihenfolge-unabhängig.
- Block 4: `fem/run_fem.py::run_case` wirft `RuntimeError` statt
  `IndexError` bei leerer Ergebnisliste (inkl. ccx-Arbeitsverzeichnis) und
  prüft `fea.run()` explizit (`rc is not True` — reale FreeCAD-1.1.1-API
  liefert Bool, nicht den im Brief unterstellten Fehlstring, im Quellcode
  von `femtools/ccxtools.py` verifiziert). Neues Feld
  `defl_top_is_fallback` (True im Submodell ohne echte Deckflächen-Knoten);
  `fem/report.py` druckt „(Fallback)" dahinter.
- Block 1 (Ledger 42 + M7): `write_report(...) -> tuple[bool, bool]`
  (ok, vorbehalt) statt Text-Matching; `run_all.py` gated direkt darauf,
  kein Grep im Reporttext mehr; leeres `fem_results` → `ValueError`.
  `tests/test_report.py`: 5 Tests (3 umgestellt + 2 neu).
- Block 2 (Finalreview I1): neu `export/manifest.py::append_manifest`
  hängt SHA256-Manifest + Git-Commit + GEOM_REV an den Report;
  `run_all.py` ruft es nach `export_all` mit `git rev-parse HEAD` auf.
  `tests/test_manifest.py` (3 neu).
- Block 3 (Finalreview I2 + M4): `export/export.py::export_all(p, out_dir,
  frame=None, segments=None)` — rückwärtskompatibel. `run_all.py` baut
  `frame`+`segments` je einmal, DFM-Gate je Segment (`overhang_area` gegen
  `allowed*1.2+200`) VOR den FEM-Läufen (fail-fast) und VOR dem Export
  (Exit 1 bei Verletzung), reicht beide Shapes an `export_all` durch.
- Block 5 (heikelster Block, M1/Ledger 23/30/33): `params.py` neu
  `min_band`/`lap_height`/`groove_centerline_len`; Verbraucher
  `fem/analytic.py` (joint_checks, glue_load_shear), `fem/joint_check.py`,
  `export/export.py` umgestellt; `validate()` nutzt `min_band` selbst.
  `model/dfm.py` BEWUSST NICHT angefasst (Brief listet es, aber die dortige
  Summenformel ist der Ledger-21/22-Fix aus Task 15 — ein `min_band` dort
  wäre eine Regression, dokumentiert statt blind befolgt).
  `model/features.py::rotz(shape, k)` ersetzt die identischen `_rot()`-
  Kopien in `frame.py`/`segments.py` (Wrapper entfernt, `test_eckkammern.py`
  mitgezogen). `test_toolchain.py` importiert `_ensure_binary_paths` jetzt
  aus `fem.run_fem`. Anker bitidentisch geprüft: `frame.Volume`
  1736006.070242394, `dfm_allowed` 36788.23334770628, τ 0.384, Lochleibung
  6.98, `wind_force` 480.0 — alle 0 Diff.
- Block 7 (Task-17-Re-Review Minor 2): 2 neue Tests in
  `test_eckkammern.py` — explizite Werkzeugzahl-Konsistenz
  `len(_chamber_cuts) == 4*chamber_slot_count + 16` bei
  `CORNER_CHAMBERS=True, CELL_L=53` + Gegenprobe ohne Eckkammern.
- Volle Suite ZWEIMAL grün: **75 bestanden, 0 fehlgeschlagen** (68 + 7 neu:
  3 Manifest, 2 Report, 2 Eckkammern). Zweiter Lauf nach einer kosmetischen
  Manifest-Formatkorrektur, identisches Ergebnis.
- Produktionslauf `bin/fc run_all.py` (Hintergrund+Poll): DFM-Gate-Zeilen
  im Log (alle 4 Segmente PASS, 8909/44346 mm² Überhang), Manifest im
  Report (14 Dateien, 64-hex-SHA256 je Datei, Git-Commit, GEOM_REV=2),
  FEM-Istwerte 0.81/0.43/2.25/0.19/3.37 MPa (≤0.02 MPa Netz-Rauschen vs.
  Task-15-Referenz 0.79/0.43/2.24/0.19/3.37) — PASS mit Vorbehalt wie
  erwartet. Hash bleibt `da0d8553` (Brief-Erwartung „eccafbc1" war bereits
  vor Task 16 überholt, siehe task-17-report.md Zeile 373f. — nicht
  Task-16-Ursache). Laufzeit Gesamtpipeline 127 s (alt 129 s, verrauscht
  durch FEM-Nichtdeterminismus) — isolierte `export_all`-Messung zeigt den
  echten M4-Effekt sauber: 3.86 s (Neubau) → 0.43 s (durchgereicht),
  **~3.4 s gespart** — deutlich weniger als die im Brief geschätzten
  „20-30 s", ehrlich als Diskrepanz dokumentiert statt schöngerechnet.
- Vollständiger Nachweis: `.superpowers/sdd/task-16-report.md`.

## 2026-07-12 — Task 19: Materialwechsel Default → Bambu ASA-CF

Quelle: `.superpowers/sdd/task-19-brief.md` (User-Entscheidung, TDS V1.0 liegt
vor). Ausgangsstand: `32e0a6c`, 75/75 grün, params_hash `da0d8553`.

- params.py Materialkarte (geometriefrei, nur Materialfelder): E_BASE 4200
  (Zug-E XY; Z 2290), SIGMA_BASE 34 (XY; Z 30), RHO 1020, CTE_ASA 60e-6
  (konservative OBERGRENZE — TDS nennt keinen CTE; bewusst NICHT die
  optimistischeren ~40e-6, Gate-Muting-Lehre), DERATE_TEMP 0.5 (85 °C vs.
  HDT 102/Vicat 108), DERATE_Z 0.8 (GEMESSEN Z/XY=0.88, konservativ
  gerundet), DERATE_CREEP 0.4 unverändert (keine CF-Kriechdaten). NU 0.35
  unverändert. Preset-Vergleichstabelle (Standard-ASA, CR3D FibCR20) NUR
  als Kommentar. GEOM_REV bleibt 2 (keine Geometrieänderung).
- Abgeleitete Zahlen nachgerechnet (alle Brief-Werte bestätigt, nur
  Rundungsartefakte dokumentiert): allowables lang/kurz 5.44/13.60;
  Fugenauslastung u=0.208542 (~21 %, Brief 0.2086 = Zwischenrundung);
  side_screw_pullout 430.6747 N (Brief 430.6); τ_zul 6.80,
  Lochleibung_zul 13.60. M5 bleibt (M4 ginge rechnerisch wieder:
  Lochleibung mit M4-Durchgang 4.5 mm = 480/(4.5·12.5) = 8.53 MPa — vorher
  über 8.40 zulässig [durchgefallen], jetzt klar unter 13.60 — aber KEINE
  Geometrieänderung in diesem Task).
- Tests (Erwartungswerte geändert, KEINE Toleranz-Aufweichung):
  test_zulaessigkeiten 5.44/13.60 (±0.01), test_fugenauslastung
  0.15<u<0.30 (mit Rechnung im Kommentar), test_seitenschrauben_auszug
  430.6±5, test_materialkarte "4200.0 MPa" (im Brief nicht gelistet, aber
  zwingend: fem/material.py liest E_BASE), test_export +"ASA-CF"/"250"/
  "Kammer". RED je Block vor Anpassung nachgewiesen (alte Erwartungen
  scheitern an neuen params; Suite-Lauf 1: 74/75 mit exakt dem erwarteten
  einen FAIL vor dem test_materialkarte-Fix).
- Montagenotiz: Bambu ASA-CF (TDS V1.0), Düse 250–280 °C, Bett 80–100 °C
  texturiertes PEI, Kammer 45–60 °C, Trocknung 8 h/80 °C VOR Druck,
  Tempern 80–90 °C/6–12 h (statt 80 °C/4 h), Verzugs-Pflichtblock auf
  CF-Formulierung („dimensional stability", Maßnahmen bleiben PFLICHT),
  Brücken-Hinweis: Stoßstufen-Brücke ~25 mm < 40 mm TDS-Maximum.
- Spec §3.5 (Bambu ASA-CF Default + Datenblatt + DA-3-Begründung + Presets
  + CTE-Vorbehalt), §4 Thermik (60e-6 → ~1,84 mm statt 3,4 mm), §6
  Materialkette (34/4200, 0.5·0.8·0.4 → 5.44/13.60, DERATE_Z gemessen).
  todo.md: neuer offener Punkt CTE-Herstellerwert anfragen.
- Volle Suite: **75 bestanden, 0 fehlgeschlagen** (Lauf 2, nach
  test_materialkarte-Fix). Geometrie-Anker unverändert grün
  (test_eckkammern_default_anker_unveraendert: Volumen 1736006.070242394).
- Produktionslauf `bin/fc run_all.py` (Hintergrund+Poll): params_hash neu
  **`5f063cc3`** (vorher da0d8553). DFM 4x PASS (8909/44346 mm²). FEM:
  LF1 0.80/13.60 (5.9 %), LF2 0.41/13.60 (3.0 %), LF3 2.27/5.44 (41.7 %,
  Brief-Erwartung ~41 % getroffen; vM-Istwert 2.27 vs. 2.25 Task 16 =
  Netz-Rauschen), LF4 0.19/13.60 (1.4 %), Stoß 3.40/13.60 (25.0 %).
  Fugenauslastung 21 % (vorher 39 %). „PASS mit Vorbehalt" (Freigang
  OFFEN, Messkampagne 7) unverändert korrekt, !-Banner im Log, Manifest
  14 Dateien + Git-Rev + GEOM_REV=2, FERTIG nach 127 s.
- Vollständiger Nachweis: `.superpowers/sdd/task-19-report.md`.

## 2026-07-12 — Task 20: Eckkammern als Default aktivieren (Stand 3be4b64)

- params.py: `CORNER_CHAMBERS: bool = True` (User-Entscheidung 2026-07-12;
  Verzugs-/Gewichtsnutzen, FEM-verifiziert Task 17). GEOM_REV bleibt 2 —
  reine Parameter-, keine Code-Änderung; params_hash wechselt über das
  Feld selbst: Default neu **5ba1ea4b**, die AUS-Variante
  (`Params(CORNER_CHAMBERS=False)`) hasht exakt auf den alten Stand
  **5f063cc3** (Beweis der Rückführbarkeit).
- RED nachgewiesen (Suite-Lauf 1 nach Flip, 70/75): exakt die im Brief
  erwarteten 5 Fälle — test_kammern_wirken (ValueError CHAMBERS=False ohne
  CORNER_CHAMBERS=False), 3× test_eckkammern (Anker/Delta gedreht),
  test_asym_chamber_slot_count (P_CORNER erbt die 16 fixen Eck-Werkzeuge).
- Tests angepasst (KEINE Toleranz-Aufweichung, jede Band-Änderung
  nachgerechnet und im Testkommentar dokumentiert):
  - test_kammern_wirken: Solid-Referenz `Params(CHAMBERS=False,
    CORNER_CHAMBERS=False)`; Band (3.0e5, 5.5e5) statt (2.5e5, 5.0e5) —
    Rechnung: v_solid 2127732.386711353, v_default 1694758.489540970,
    Delta 432973.897170383 = 391726.316 (Seitenkammern) + 41247.581
    (Eckkammern); Bandbreite unverändert 2.5e5.
  - test_eckkammern.py: Semantik gedreht — Default-Anker jetzt EIN
    (1694758.489540970), NEU test_eckkammern_ausschalt_anker
    (1736006.070242394, alter Default bleibt beweisbar); P_ECK-Caches
    durch PRM.P/P_AUS ersetzt (kein Doppel-Bauen äquivalenter Frames);
    test_eckkammern_p_eck_volumen_exakt_unveraendert →
    test_eckkammern_delta_und_keepout_exakt (Delta 41247.580701424 exakt,
    corner_keepout 196.223956).
  - test_asymmetrie.py: Werkzeugbilanz len(tools) == 4*slots + 16
    (16 fixe Eck-Werkzeuge: 8 Sektor-Kavitäten + 8 Diagonal-Vents,
    unabhängig von CELL_L/W_TOP; Istfall P_CORNER 112 = 4*24 + 16).
    Übrige Asym-Tests halten formelbasiert unverändert (RED-Beleg).
- Volle Suite: **76 bestanden, 0 fehlgeschlagen** (75 Bestand + 1 neuer
  Ausschalt-Anker-Test).
- Produktionslauf `bin/fc run_all.py` (Hintergrund+Poll): Hash
  **5ba1ea4b**. DFM 4× PASS (8972 bzw. 8959/44828 mm² — Zone 6 aktiv,
  Allowance +482 durch die 8 Eck-Vents). FEM: LF1 0.78/13.60 (5.7 %),
  LF2 0.42/13.60 (3.1 %), LF3 2.29/5.44 (42.1 %, vorher 2.27 = minimal
  höher, Eckmaterial fehlt — Brief-Erwartung getroffen), LF4 0.19/13.60
  (1.4 %), Stoß 3.40/13.60 (25.0 %). „PASS mit Vorbehalt" (Freigang
  OFFEN, Messkampagne 7) unverändert, !-Banner im Log, Manifest 14
  Dateien + Git-Rev + GEOM_REV=2, FERTIG nach 146 s.
- Kosten-STL: `out/adapterrahmen_segment_5ba1ea4b.stl` (Kopie seg0);
  Segmentgewicht 430.7 g (V=422235.2 mm³ × RHO 1020) — vorher ~441 g,
  ~10.5 g je Segment gespart.
- Doku: Spec §4 Innenleben (Eckkammern seit 2026-07-12 Default EIN),
  todo.md Eckkammern-Punkt als aktiviert markiert.
- Vollständiger Nachweis: `.superpowers/sdd/task-20-report.md`.
