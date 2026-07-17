# Projektstatus

Stand: 17.07.2026 · GEOM_REV 10 · Parameterstand `8eb8b79f`

## Abgeschlossen

- Vier rotationsidentische Universal-L-Segmente statt vier Varianten.
- 28-mm-Erhöhung, 400-mm-Öffnung und supportfreie Kammergeometrie.
- Kompakter 500×500-mm-Hybridrahmen mit zwei getrennten 10-mm-Dachraupen
  vollständig über dem 30-mm-Holzrahmen: äußere Raupe geschlossen,
  4-mm-Mittelkanal und acht definierte Entlüftungen an der inneren Raupe.
- 16 längliche Abstandspads mit 2,5×20 mm Kontaktmaß statt 68 Rundnoppen.
  3 mm Dachabstand plus
  0,6-mm-Applikationsführung ergeben 3,6 mm wirksame Raupenhöhe und etwa
  120 ml Nennvolumen; kein Pad greift in die Klebefläche ein.
- Zwei 17-mm-Kammerringe statt eines massiven Außenbands; Universalteil rund
  530 g und 275×250×47 mm im theoretischen CAD-Modell.
- Acht Belluna-Plattenschrauben oben. Unten acht seitliche ST4.2×25 in den
  Holzrahmen als physische, mangels typgeprüftem Schraubgrund nicht
  angerechnete Rückfallebene; die Doppelraupe besteht den Primärnachweis allein.
- Ein M5 je Segmentstoß; sowohl dieser einzelne Bolzen als auch RK-1300
  bestehen die vollständige konservative 480-N-Stoßhülle getrennt.
- Digital vermessene Belluna-Rekonstruktion mit 397-mm-Unterkragen und
  1,5-mm-Wand; Metallclips und Dichtring als getrennte Referenzteile.
- DFM-, FEM-, analytische, Passungs-, Export- und Referenztests.
- Quellenbasierte Lastpfadabschätzung für Klebungen, obere Schraubengruppe,
  Segmentstöße und das Dachsandwich (`PASS_ASSUMPTION_BASED`).
- Definiertes Kleb-/Dicht-/Lacksystem und reproduzierbarer Montagegenerator.
- Einheitliche Pipeline und geordneter Build-/Release-/Referenzaufbau.
- Reproduzierbarer erster OpenFOAM-Grobfall für die geschlossene Belluna-
  Aerohülle bei 200 km/h; noch kein Freigabe-Gate.
- Deterministischer Toleranz-Sweep der Messkampagnen-Parameter durch alle
  analytischen Gates (`scripts/toleranz_sweep.py`). Kernbefunde: `W_TOP` hat
  beim aktuellen Parameterstand nach unten null Toleranz (50,0 mm liegt exakt
  auf der 2-mm-Mindestbreite der Entwässerungsfase — Messwerte darunter
  erfordern Nachparametrierung); die Lastpfad-Gates behalten im gesamten
  Messtoleranzband ≥ 26 % Reserve; im Überlapp-Regime des Haubenfreigangs
  wäre `EDGE_H` ≤ 53 mm gefordert (Schätzwert 55 mm) — B1 entscheidet das
  Regime, B2/B4 dann das Gate.

## Offen vor Produktionsfreigabe

- Reale Fahrzeugmaße `B1a`, `B1b` und `B2` für das Haubenfreigang-Gate.
- Reales Ausschnittmaß und Zustand des Dachkerns bei Heki-Demontage.
- Ausführung und Dokumentation des wasserfesten Holzrahmens.
- Vollständiger Trocken-Fit und Dichtheitstest am Fahrzeug.

## Technische Weiterentwicklung, nicht Freigabeblocker

- FEM-Netzkonvergenz 20/10/5 mm automatisieren.
- Nachgiebige Klebstoff-/GFK-Federbettung statt der derzeit starren,
  flächigen FEM-Lagerung untersuchen.
- Stoßmodell um expliziten Bolzenkontakt und zyklische Lasten erweitern.
- Werkstoff-, Haft- und Sandwichcoupons nur dann nachholen, wenn später reale
  Originalsubstrate und ein sinnvoller Prüfaufbau verfügbar werden; bis dahin
  bleiben sie dokumentierte Modellunsicherheit, kein kurzfristiges Gate.
- CFD-Netzkonvergenz sowie offene Haube, Schräg- und Seitenwind ergänzen.
- Zusammenhängenden Massivquerschnitt als quantitative Warp-Metrik ergänzen.
- Günstige Validierungen ohne Gate-Charakter umsetzen (PLA-Lasttest mit
  Messuhr, Z-Zugstäbe, Dachtemperatur-Logging, Demontage-Haftprobe auf dem
  ausgebauten Dachausschnitt) — Plan und Akzeptanzkriterien in
  [`verification.md`](verification.md).

Historische Tasks, verworfene Materialien und frühere Parameterstände stehen
im [`archive/logbook.md`](archive/logbook.md) und sind nicht mehr normativ.
