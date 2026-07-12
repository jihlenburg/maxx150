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
