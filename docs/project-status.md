# Projektstatus

Stand: 15.07.2026 · GEOM_REV 6 · Parameterstand `83aeba39`

## Abgeschlossen

- Vier rotationsidentische Universal-L-Segmente statt vier Varianten.
- 28-mm-Erhöhung, 400-mm-Öffnung und supportfreie Kammergeometrie.
- Getrennte Schraubinterfaces: 8× Belluna-Platte → Adapter und 8× Adapter → Holz.
- Digital vermessene Belluna-Rekonstruktion mit 397-mm-Unterkragen und
  1,5-mm-Wand; Metallclips und Dichtring als getrennte Referenzteile.
- DFM-, FEM-, analytische, Passungs-, Export- und Referenztests.
- Definiertes Kleb-/Dicht-/Lacksystem und reproduzierbarer Montagegenerator.
- Einheitliche Pipeline und geordneter Build-/Release-/Referenzaufbau.
- Reproduzierbarer erster OpenFOAM-Grobfall für die geschlossene Belluna-
  Aerohülle bei 200 km/h; noch kein Freigabe-Gate.

## Offen vor Produktionsfreigabe

- Reale Fahrzeugmaße `B1a`, `B1b` und `B2` für das Haubenfreigang-Gate.
- Reales Ausschnittmaß und Zustand des Dachkerns bei Heki-Demontage.
- Ausführung und Dokumentation des wasserfesten Holzrahmens.
- Material-, Klebe-, Lack- und Sandwichcoupons gemäß `verification.md`.
- Vollständiger Trocken-Fit und Dichtheitstest am Fahrzeug.

## Technische Weiterentwicklung, nicht Freigabeblocker

- FEM-Netzkonvergenz 20/10/5 mm automatisieren.
- Elastische Noppenbettung statt starrer Lagerung untersuchen.
- Stoßmodell um expliziten Bolzenkontakt und zyklische Lasten erweitern.
- CFD-Netzkonvergenz sowie offene Haube, Schräg- und Seitenwind ergänzen.
- Zusammenhängenden Massivquerschnitt als quantitative Warp-Metrik ergänzen.

Historische Tasks, verworfene Materialien und frühere Parameterstände stehen
im [`archive/logbook.md`](archive/logbook.md) und sind nicht mehr normativ.
