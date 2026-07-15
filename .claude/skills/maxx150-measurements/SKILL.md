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

Nach einer bestätigten Übernahme zwingend:

```sh
python3 -m pipeline test
python3 -m pipeline engineering
python3 -m pipeline fit
python3 -m pipeline release
```

Den neuen Report und Release-Status prüfen. Ein rechnerisches PASS schließt
physische Coupons und Einbauprüfungen nicht automatisch.
