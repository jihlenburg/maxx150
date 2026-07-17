---
name: maxx150-measurements
description: Reale Belluna- oder Fahrzeugmesswerte prüfen und kontrolliert in params.py übernehmen.
---

# maxx150-Messwertübernahme

Messprotokoll: `docs/measurements/`; aktuelle Daten: `messwerte.json`.

Zuerst immer ein Trockenlauf:

```sh
python3 scripts/apply_measurements.py messwerte.json --dry-run
```

Die automatische Zuordnung umfasst `B1a+B1b → EDGE_DIST`, `B2 → EDGE_H`,
`B3 → ROOF_T` und `B4 → HOOD_UNDERSIDE_H`. Konstruktive Entscheidungen wie
Deckflächenbreite oder Gusset-Freistellung werden nicht automatisch verändert.

## Fremdteile vermessen (Belluna-Muster)

Beim Digitalisieren eines physischen Fremdteils NICHT nur Zahlen sammeln,
sondern den Verifikationskreis schließen (Lehre Messkampagne 2026-07-13:
die Platten-Topologie wurde ohne diesen Kreis dreimal falsch interpretiert —
Kragenrichtung, Trogprofil, Doppelkragen):

1. Messwerte sofort als parametrisches Mock modellieren
   (`reference_models/`), jede Annahme mit `_ANN`-Suffix markieren.
2. Dem Nutzer annotierte Renderings liefern: gemessene Werte GRÜN,
   Annahmen ORANGE, Marker in der 3D-Szene an der Messstelle — der Nutzer
   korrigiert am Bild, nicht an Zahlenkolonnen.
3. Maßketten an EINEM präzisen Maß verankern und als Kontrollsumme
   schließen (Beispiel: Öffnung + Wand + Dichtung + Steg = Auflagebreite);
   Widersprüche sind Messrauschen-Indikatoren, keine Rundungsmasse.
4. Zum Abschluss den digitalen Passungstest gegen das eigene Bauteil
   rechnen (`python3 -m pipeline fit`) — er findet Interferenzen, die
   Einzelmaße nicht zeigen (z. B. Freistellungen, Schraub-/Vent-Kollisionen).

Nach einer bestätigten Übernahme zwingend:

```sh
python3 -m pipeline test
python3 -m pipeline engineering
python3 -m pipeline fit
python3 -m pipeline release
```

Den neuen Report und Release-Status prüfen. Ein rechnerisches PASS schließt
physische Coupons und Einbauprüfungen nicht automatisch.
