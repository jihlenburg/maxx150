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
