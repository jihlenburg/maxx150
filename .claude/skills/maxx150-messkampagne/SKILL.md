---
name: maxx150-messkampagne
description: Messwerte/Messkampagne eintragen — Nutzer liefert gemessene Werte aus dem Messprotokoll (Messschieber/Zollstock am Fahrzeug oder an der Karosseriebefestigungsplatte) und diese sollen in params.py übernommen werden.
---

# maxx150-Messkampagne

Überträgt echte Messwerte aus dem Messprotokoll in `params.py` — ersetzt
Schätzwerte durch belastbare Zahlen. Reines Python3-Tool
(`scripts/messkampagne.py`), KEIN FreeCAD nötig für diesen Schritt.

## Protokollfelder → params-Feld (Formeln)

| Protokollfeld(er) | params-Feld | Formel |
|---|---|---|
| B1a + B1b | `EDGE_DIST` | Ausschnitt-Hinterkante → Dachkante |
| B2 | `EDGE_H` | 1:1 |
| B3 | `ROOF_T` | 1:1 |
| B4 | `HOOD_UNDERSIDE_H` | 1:1 |
| A1c / A1d / A1e / A1f | `W_TOP_FRONT`/`_REAR`/`_LEFT`/`_RIGHT` | 1:1 je Seite |
| A4a | `REC_GUSSET_D` | + 0.5 mm Reserve (Fertigungstoleranz) |
| A4b | `REC_GUSSET_W` | + 2.0 mm Reserve (Fertigungstoleranz) |

Weitere Protokollfelder (A2a-c, A3a-c, A5a, A5b) sind im Messprotokoll
vorgesehen, haben aber noch KEIN params-Feld/keine Formel — bleiben in
`messwerte.json` stehen (nullable), fließen aber nicht automatisch ein.
Vollständige Feldliste + Defaults: Session-Messprotokoll
(`messprotokoll.md`-Vorlage) bzw. `docs/superpowers/specs/2026-07-12-belluna-adapter-design.md` §8.

## Nutzung von scripts/messkampagne.py

1. Nutzer-Messwerte als JSON sammeln (Vorlage: `messwerte.beispiel.json` im
   Repo-Wurzelverzeichnis kopieren, Werte eintragen, unbekannte Felder auf
   `null` lassen).
2. Trockenlauf zuerst — zeigt die Diff-Tabelle, schreibt nichts:
   ```sh
   python3 scripts/messkampagne.py messwerte.json --dry-run
   ```
3. Nutzer die Diff-Tabelle (alt → neu) zur Bestätigung zeigen.
4. Echt patchen (Default-Ziel `./params.py`, Backup wird automatisch als
   `params.py.bak` angelegt):
   ```sh
   python3 scripts/messkampagne.py messwerte.json
   ```
   Für Tests/Isolation `--target <andere-datei>` verwenden (z. B. eine
   tmp-Kopie) — rührt dann das echte `params.py` NICHT an.

Das Skript patcht per Feldname-anchored Regex NUR den Zahlenwert nach `=`
(Kommentar/Einrückung bleiben erhalten) und lässt params-Felder ohne
zugehörigen (nicht-null) Messwert unangetastet auf ihrem Default stehen.

## Pflicht-Reihenfolge NACH dem Patchen

Niemals direkt drucken/exportieren! Erst verifizieren:

1. `bin/fc tests/run_tests.py` (voller Testlauf, ~10 min, als
   Hintergrundprozess — siehe Skill `maxx150-pipeline`) — muss grün sein.
   `PRM.validate(p)` kann bei extremen neuen Messwerten (z. B. sehr schmale
   `W_TOP`-Seite) direkt beim Laden/Bauen fehlschlagen — das ist beabsichtigt,
   nicht ignorieren.
2. `bin/fc run_all.py` (als Hintergrundprozess, Log + Poll) — neuer
   `params_hash`, neue Druckdateien + Report.
3. **Report prüfen**: `out/report_<neuer_hash>.md` öffnen. Insbesondere: wechselt
   der Haubenfreigang-Eintrag von `OFFEN` (Schätzwert-Vorbehalt) auf eine
   konkrete Zahl (PASS/FAIL)? Das ist der eigentliche Zweck der
   Messkampagne bei EDGE_DIST/EDGE_H (Messkampagne 7) — wenn er weiterhin
   `OFFEN` zeigt, wurden B1a/B1b bzw. B2 nicht mitgeliefert.
4. **Erst PLA-Probedruck, dann ASA-Serie.** Nach neuem, verifiziertem
   Parameterstand IMMER zuerst einen PLA-Probedruck (schnell, billig) auf
   Passung/Freigang prüfen, bevor in ASA (langsam, Tempern nötig) gedruckt
   wird — siehe Montagenotiz-Pflichtbedingungen (Skill `maxx150-pipeline`
   bzw. `fem/report.py`-Ausgabe).

## Nach erfolgreicher Übernahme

Das `.bak`-Backup (`params.py.bak`) nicht automatisch löschen — bleibt als
Rückfallebene liegen, bis der Nutzer den neuen Stand bestätigt hat.
