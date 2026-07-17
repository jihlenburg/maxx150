# Final-Fix-Report — Pre-Merge-Nachbesserung (Whole-Branch-Review)

Datum: 2026-07-12
Umfang: Fix 1 (Critical C1), Fix 2 (Ledger 13), Fix 3 (Ledger 14), Fix 4 (Ledger 35) — ein Commit.

## Fix 1 — `params.validate(p)` gegen stille Geometriebrecher

Neue Funktion `validate()` in `params.py`, verdrahtet als erste Zeile in
`model/frame.py::build_frame()` und direkt nach `import params as PRM` in
`run_all.py`.

### Nachrechnung der Default-Ungleichungen (P = Params())

| Prüfung | Rechnung | Schwelle | Ergebnis |
|---|---|---|---|
| Außenwand hinter Kammerring 2 | `w_min(50) - (INNER_WALL 8 + 2*CHAMBER_W 15 + CHAMBER_RIB 4)` = 50 − 42 = **8.0 mm** | ≥ 2.4 | OK |
| Deckplatten-Rest über Kammern | `DECK_T 5 - REC_GUSSET_D 3` = **2.0 mm** (exakter Grenzfall) | ≥ 2.0 (Prüfcode: `< 2.0` löst nicht aus) | OK, kein Fehlalarm |
| Chevron-Apex vs. Kammerdecke | `kammerdecke = (28-3)-5 = 20`; `apex = 4 + tan(47°)*15/2 ≈ 12.0428` | `apex ≤ kammerdecke-1.0 = 19` | OK (12.04 ≤ 19) |
| VENT_Z-Band | Band = `[apex+VENT_D/2+0.5, kammerdecke-VENT_D/2-0.5]` = `[14.54, 17.5]`; `VENT_Z=17` | innerhalb | OK |
| M5-Kopfsenkung vs. Außenwand | `JOINT_BOLT_OFF 35 + JOINT_CB_D/2 5 = 40` | ≤ `w_min-2.4 = 47.6` | OK |
| GLUE_GAP | 3.0 | ≥ 2.0 | OK |
| Noppenabstand | `NOPPLE_SPACING 60` | ≥ `3*NOPPLE_R = 12` | OK |

Ergebnis: **alle sieben Default-Ungleichungen bestehen ohne Schwellen-Anpassung.**
Der einzige Grenzfall ist der Deckplatten-Rest (exakt 2.0 mm bei den Defaults);
die Spezifikation `if deck_rest < 2.0` (strikt `<`, nicht `<=`) behandelt ihn
korrekt als bestanden — keine Änderung an Defaults oder Schwellen nötig, kein
Anpassungsbedarf gegenüber der Vorgabe.

### Test-Fänge (Messkampagnen-Brecher, alle lösen `ValueError`)

- `W_TOP_*=40` (statt 50) → Außenwand `40-42 = -2.0 < 2.4` → fängt.
- `REC_GUSSET_D=6.0` → Deckplatten-Rest `5-6 = -1.0 < 2.0` → fängt.
- `VENT_Z=24.0` → außerhalb Band `[14.54, 17.5]` → fängt.
- `GLUE_GAP=1.0` → `< 2.0` → fängt.

Neue Tests: `tests/test_params.py::test_validate_defaults_ok`,
`tests/test_params.py::test_validate_faengt_messkampagnen_brecher`.

## Fix 2 — `fem/analytic.py`

Kommentar in `joint_checks()` korrigiert: „Lochleibung der M4-Schraube im
ASA“ → „Lochleibung der M5-Schraube im ASA“ (der Code selbst nutzte bereits
`JOINT_BOLT_D` = 5.5 mm / M5-Durchgang; nur der Kommentar war veraltet, vgl.
`params.py` Zeile zu `JOINT_BOLT_D`: „M5-Durchgang (M4 fiel bei 480 N
Lochleibungs-Nachweis durch)“).

## Fix 3 — `tests/test_analytic.py`

Kommentar in `test_haubenfreigang_default_kein_ueberlapp()` korrigiert:
„Haube ragt 130 mm über den Ausschnitt“ → „Haube ragt 179 mm
(MaxxFan-Maßblatt) über den Ausschnitt“ — deckt sich mit
`params.HOOD_TIP_REACH = 179.0`.

## Fix 4 — `export/export.py`: DIN-912-Normlänge für M5

Inline-Formel `int(p.H_RAISE - p.GLUE_GAP + p.JOINT_NUT_T + 2)` ersetzt durch
Helper `_m5_bolt_length(p)`, der die rohe Klemmlänge (Klemmlänge + Muttertasche
+ Überstand) auf die nächste DIN-912-Normlänge aus
`(20, 25, 30, 35, 40, 45, 50)` aufrundet.

Default-Rechnung: `28 - 3 + 4 + 2 = 31` → aufgerundet auf **35**.

Beleg aus der generierten Montagenotiz (`out/test_export/montagenotiz_*.md`,
`rg -o "M5x[0-9]+"`):

```
M5x35
```

## Testausgaben

```
$ TEST_FILTER=params bin/fc tests/run_tests.py
...
7 bestanden, 0 fehlgeschlagen

$ TEST_FILTER=export timeout 570 bin/fc tests/run_tests.py
PASS test_export.test_export_erzeugt_alle_dateien
PASS test_export.test_montagenotiz_inhalt
PASS test_export.test_step_reimport_volumen
3 bestanden, 0 fehlgeschlagen

$ timeout 570 bin/fc tests/run_tests.py
...
45 bestanden, 0 fehlgeschlagen
```

## Grenzfall-Anmerkungen

- Deckplatten-Rest bei Defaults liegt exakt auf der Schwelle (2.0 mm); der
  strikte `<`-Vergleich in `validate()` verhindert einen Fehlalarm, wie in der
  Vorgabe gefordert. Keine Schwellen- oder Default-Änderung vorgenommen.
- Alle übrigen Ungleichungen liegen mit spürbarem Abstand innerhalb der
  Toleranz — keine weiteren Grenzfälle.
- `run_all.py` ruft `PRM.validate()` direkt nach `import params as PRM` auf,
  vor den übrigen (FreeCAD-lastigen) Modul-Importen — mit Default-Parametern
  ist das ein No-Op, wie von der Aufgabenstellung gefordert (kein
  Produktionslauf nötig, da Parameterstand unverändert).

## Verifizierte Dateien

- `/Users/jihlenburg/maxx150/params.py`
- `/Users/jihlenburg/maxx150/model/frame.py`
- `/Users/jihlenburg/maxx150/run_all.py`
- `/Users/jihlenburg/maxx150/fem/analytic.py`
- `/Users/jihlenburg/maxx150/tests/test_analytic.py`
- `/Users/jihlenburg/maxx150/tests/test_params.py`
- `/Users/jihlenburg/maxx150/export/export.py`
