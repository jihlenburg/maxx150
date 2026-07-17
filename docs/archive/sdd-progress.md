# SDD Progress Ledger — Belluna-Adapter-Pipeline
Plan: docs/superpowers/plans/2026-07-12-belluna-adapter-pipeline.md
Branch: main (User-Freigabe), Commits lokal pauschal freigegeben, NIEMALS push.

BASE Task 1: b7ca595
Task 1: complete (b7ca595..370dddd, review clean). Minors fürs Finalreview: run_tests.py ohne __main__-Guard (plan-mandated); Luftdichte 1.2 als Magic Number in wind_force; kein Immutability-Test für Params.
BASE Task 2: 370dddd
PENDING nach Task 2: Parameter-Amendment aus MaxxFan-Deluxe-Maßblatt (User-Upload): A_HOOD 0.10->0.108, HOOD_TIP_REACH 130->179, Windlast 444.4->488.9 N (test_windlast + Plan-Global-Constraints + Spec §6 LF1 anpassen). Zeichnungsdaten: 586 lang, 408 breit, 132 zu, 236 offen, Überstand offen 179 (123 bis Knick).
Task 2: complete (370dddd..0f23773, review clean, Reviewer bestätigte echten ccx-Lauf). Minors fürs Finalreview: closeDocument ohne try/finally im Toolchain-Test; fea.run()-Rückgabewert ungeprüft.
Amendment-Commit danach: MaxxFan-Maßblatt (A_HOOD 0.108, TIP_REACH 179, Wind 480 N) — Ledger-PENDING erledigt.
BASE Task 3: b47d4a8
Task 3: complete (b47d4a8..d601e67, Fix-Loop: Off-by-One rect_path_points [plan-geerbt] + Testlücke behoben, Re-Review Approved). Minors fürs Finalreview: mutable default origin in rounded_box; Docstrings rounded_box/_vertical_edges fehlen; isValid nur in einem Test; kein spacing-Guard.
BASE Task 4: d601e67
Task 4: complete (d601e67..4524460 + Plan-Sync, review Approved). Planfehler behoben: scharfer Öffnungs-Prüfkörper vs. R5-Fillets (jetzt R5.5-Probe), XLen->XLength (auch Task-6-Plantext vorab gefixt). Minors fürs Finalreview: test_deckflaeche-Schwelle 60000 nur 0.4% unter Istwert (fragil bei Parameteränderung).
BASE Task 5: siehe git log (Plan-Sync-Commit)
M5-Amendment-Commit 9c26a25 (JOINT_BOLT_D 5.5, CB 10.0/5.0, NUT 8.0/4.0) — Lochleibung mit 480 N sonst FAIL.
BASE Task 5: 9c26a25
Task 5: complete (9c26a25..f5c4e93, review Approved, Istwerte bestätigt: u=0.387, tau=0.384, Lochleibung=6.98, Auszug=266N). Minors fürs Finalreview: import math in Funktion; sig_lang ungenutzt in joint_checks; M4-Kommentar veraltet (ist M5); 130mm-Kommentar veraltet (ist 179); Auszugstest prüft nur Schwelle nicht Sollwert.
BASE Task 6: f5c4e93
Task 6: complete (f5c4e93..b9c2228, review Approved; Implementer fixte 2 Plan-Geometriebugs: lap_cut-Toleranz, Achsen-Noppen-Split; Reviewer verifizierte beide numerisch). Minors fürs Finalreview: kein isValid-Guard nach Bolzen-Cuts in build_segments; Asymmetrie-Behauptung im Docstring ungetestet; kein Kollisionstest Bolzen/Rille.
Doku-Amendment: Dichtheitskonzept in Spec §4 + Montagenotiz (Commit siehe git log).
BASE Task 7: b9c2228+Doku-Commit (git log)
Task 7: complete (c1d41ec..5d0ffa3, Fix-Loop: 4. Brückenzone Stoßstufe dokumentiert+eingerechnet [35581.86], _facet_area getestet, Import bereinigt; Re-Review Approved). Minors fürs Finalreview: Begriff Brücke vs Kragarm in dfm-Docstring; LinearDeflection-Kommentar; band=min(W_TOP) global konservativ.
BASE Task 14 (Rippenkammern): 87d8b71
Task 14: complete (87d8b71..79dadf3, review Approved; Volumenbilanz exakt reproduziert, 48 Kammern/24 Slots). WICHTIG für Task 8: INFILL_FACTOR/E_BASE erst dort verdrahten+prüfen (Reviewer-Befund: aktuell Leerlauf). Rename-Fix chamber_cell_count->chamber_slot_count folgt. Minors fürs Finalreview: side_half min() global; _rot dupliziert (frame/segments); Zwischen-Guards nur nach Kammern; DFM-Vent-Formel konservativ; kein Guard in _chamber_profile_face.
Rename-Fix committet; volle Suite 29/29 (Laufzeit jetzt einige Minuten wegen Kammer-Booleans).
BASE Task 8: siehe git log (Rename-Commit)
Task 8: complete (68a9e77..e25db91, Fix-Loop: Critical Face-Selektor-Kontamination + couple-Magic-Number behoben, Re-Review Approved mit Live-Reproduktion). Minors fürs Finalreview: LF1-Moment ~12-15% konservativ doppelt angesetzt; Testlücke Asymmetrie W_TOP (Vertauschung unentdeckbar bei symmetrischen Defaults); build_frame min()-Kammerraster blockiert asymmetrische Livetests.
BASE Task 9: e25db91
Task 9: implementiert (183e1c9), Review läuft. Erste FEM-Istwerte LF4 Grobnetz: vm 0.177 MPa (2% von 8.4), defl 0.87 µm, 85k Knoten, 17.7 s. Root-Cause-Fixes des Implementers: SecondOrderLinear=True (Jacobian an Kleinradien), FemMesh.Nodes-Hebung (O(n²)-Property-Falle — erklärt früheren Hänger).
Task 9: complete (e25db91..183e1c9, review Approved, Plausibilität bestätigt). AUFTRAG an Task 13: am 10-mm-Produktionsnetz prüfen ob SecondOrderLinear=True noch nötig (Reviewer-Important). Minors fürs Finalreview: _ensure_binary_paths dupliziert (toolchain-Test/run_fem); Magic 0.5 z-Toleranz defl_top.
BASE Task 10: 183e1c9
Task 10: complete (183e1c9..0e488bd, review Approved; Reviewer korrigierte Handrechnungs-Hebelarm auf lap_h/2, FEM 3.37-3.40 MPa plausibel). Minors fürs Finalreview: defl_top-Fallback semantisch irreführend im Submodell; Face-Filter-Duplikat.
BASE Task 11: siehe git log (Plan-Task-11-Commit)
Task 11: complete (9016d2a..a44ad4b, review Approved). Minor fürs Finalreview: PASS-Berechnungs-Asymmetrie in analytic.py-API (2 Checks ohne PASS-Feld).
BASE Task 12: a44ad4b
Task 12: complete (a44ad4b..6b87954, review Approved). Minors fürs Finalreview: M5x31 auf Normlänge runden; Teststrings PFLICHT/ISO-20653/Kernloch/M5 ungeprüft; Testreihenfolge-Abhängigkeit export; GLUE_GAP-Format; list[Path]-Annotation; encoding utf-8.
BASE Task 13: 6b87954
Task 13: complete (6b87954..9f5bd47, review Approved). Produktionslauf: LF1 0.85, LF2 0.44, LF3 2.13/3.36 (engster Fall, Dauerlast), LF4 0.18, Stoß 3.37; 128 s; PASS mit Vorbehalt (Freigang). Minors fürs Finalreview: Netz-Nichtdeterminismus vs. Netzkonvergenz im Wording vermischt; Banner-Erkennung textbasiert; Grobnetz-Referenzlog nicht archiviert.
ALLE 14 TASKS COMPLETE. Finales Whole-Branch-Review folgt.
Final-Review-Fixes complete (dc9364d: validate-Gate + M5-Kommentare + Normlänge M5x35). Doku b252c12/f7b0504. Herstellbarkeits-Pflichtblock in Montagenotiz (dieser Commit), Ledger-36-Strings erledigt. Suite 45/45.
BASE Task 15: 7524cda (Vor-Messkampagnen-Paket, User-Auftrag)
Task 15: complete (7524cda..138e82e inkl. Critical-Fix Achsen-Fehlbezug [aus Controller-Brief geerbt!], Re-Review Approved mit unabhängiger Skript-Verifikation). Hash neu 88bacca5, LF-Werte: 0.79/0.43/2.24/0.19, Stoß 3.37. Bonus-Fix: nopple_faces Planaritätscheck (latenter Bug durch Kegel aufgedeckt). Minors fürs nächste Review: Herleitungs-Redundanz 6-fach; P_ASYM ohne _side_neighbor_bounds-Unit-Check; logbook.md-Doku-Ungenauigkeit.
Task 18: complete (138e82e..d348e91, review Approved). 16 Artefakte: render/-Paket, fem/heatmap.py, scripts/messkampagne.py+JSON, 3 Skills, CLAUDE.md. Minors: run_capture-Duplikat (M1-Familie); pipefail fehlt in scripts/*.sh; blender-Pfad hart; _SIMPLE-Kommentar.
BASE Task 17: d348e91
Task 17: complete (d348e91..ff14e9a inkl. Critical-Fix Referenzradius/Keepout, Re-Review Approved, Anker live Δ0). Eckkammern CORNER_CHAMBERS default False, Delta EIN 41247.58 mm³. Minors: Report §2.3/§3 (gitignored) veraltet ohne Verweis; Konsistenztest slot_count für CORNER_CHAMBERS+CELL_L-Filter fehlt → Task 16.
BASE Task 16: ff14e9a
Task 16: complete (ff14e9a..32e0a6c, review Approved; 4 begründete Abweichungen bestätigt, Anker bitidentisch). Minors: manifest liest GEOM_REV von PRM.P statt p; doppeltes load_results (vorbestehend). VOR-MESSKAMPAGNEN-PAKET KOMPLETT: Tasks 15-18 + Fixes, 75/75 Tests, Hash da0d8553.
Task 19: complete (32e0a6c..2fb2a3d + Doku-Drift-Fix, review Approved; Zahlenkette unabhängig bestätigt). Material-Default = Bambu ASA-CF, Hash 5f063cc3, Auslastungen LF1 5.9/LF2 3.0/LF3 41.7/LF4 1.4/Stoß 25.0 %, Fuge 21 %. Offen: CTE-Herstelleranfrage (todo).
Task 20: complete (3be4b64..b3123da, review Approved, alle Zahlen unabhängig verifiziert). Eckkammern Default EIN, Hash 5ba1ea4b, LF3 42.1 %, Segment 430.7 g. AUS-Variante beweisbar == 5f063cc3. Minors: 4·slots+16 dreifach dupliziert; DFM-Seg-Asymmetrie (8972 vs 8959) unkommentiert (Mesh-Rauschen).
OFFEN: Materialfrage Bambu-NRND (User entscheidet: Bambu-Restbestand / Fiberon ASA-CF08 / Extrudr ASA-GF+Coupons).
Task 21: complete (b3123da..26dec46, review Approved). Material-Default = Würth ASA GF15 weiß RAL 9003, Hash 12ffab2a, Annahmenkette dokumentiert (E 3000/σ 45 ANNAHME, Z 0.5 GESCHÄTZT, CTE 60e-6 Obergrenze), zulässig 4.50/11.25, LF3 50.0 %, Segment 464.5 g (4x750g-Spulen). Geometrie SHA256-identisch zu 5ba1ea4b. Offen: Würth/OEM-Anfrage gedruckte Kennwerte XY+Z+CTE (todo).
