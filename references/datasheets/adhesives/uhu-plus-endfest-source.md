# UHU plus endfest (90 min): Herstellerangaben, Quellenprotokoll

Ausgewählter Klebstoff der vier Segmentstöße. Er ersetzt WEICON RK-1300, das
im realen Fügeversuch am gedruckten ASA-GF nicht getragen hat (Nutzerbefund
2026-08-14). Ein handelsüblicher 2K-Epoxidklebstoff hat dort funktioniert.

- Hersteller: UHU GmbH & Co. KG, Bühl (Baden)
- Produkt: **UHU plus endfest**, Zweikomponenten-Epoxidharzklebstoff,
  Verarbeitungszeit 90 min
- Lieferform des Projekts: Doppelkammerspritze mit statischem Mischer
- Abgerufen: 2026-08-14

## Wichtiger Namenshinweis

Der frühere **UHU plus endfest 300** ist für den privaten Endverbrauch nicht
mehr die gleiche Rezeptur. UHU hat den Härter überarbeitet, damit das Produkt
ohne kindersicheren Verschluss verkauft werden darf, und es dabei in
**UHU plus endfest – 90 min** umbenannt. Die Verarbeitungseigenschaften sind
ähnlich, die erreichbare Endfestigkeit liegt jedoch niedriger (Aluminium rund
19–20 statt rund 30 N/mm²), und die Reaktion lässt sich nicht mehr durch
Wärmezufuhr verbessern. Für dieses Projekt gilt ausschließlich die aktuelle
90-min-Variante, ihre Kennwerte stehen unten. Restbestände mit der
Bezeichnung „300" nicht mit ihr vermischen.

## Für das Projekt relevante Herstellerangaben

- Lösemittelfreier 2K-Epoxidharzklebstoff, Mischungsverhältnis **1:1**
  (Volumen), Binder + Härter.
- Verarbeitungszeit (Topfzeit) **90 min**. Handfest nach **6 h**,
  endfest nach **24 h** bei Raumtemperatur.
- Temperaturbeständigkeit **−40 bis +100 °C**.
- Endfestigkeit auf Aluminium rund **19 N/mm²** Zugscherfestigkeit.
- Viskosität rund **35.000 mPa·s** (mittelviskos, standfest).
- UV-Beständigkeit sehr gut, Wasserbeständigkeit gut, nicht wasserlöslich.
- Nicht geeignet für Polyethylen, Polypropylen, PTFE, Polystyrol und
  Weich-PVC. Harte Thermoplaste wie ABS/ASA sind geeignete Untergründe.
- Handelsübliche Gebinde: Doppelkammerspritze 15 g, 24 ml/25 g und 33 g,
  jeweils auch mit statischem Mischer.

## Datengrenzen

- Das Merkblatt nennt **keine Glasübergangstemperatur**. Die
  Temperaturbeständigkeit −40 bis +100 °C ist die einzige belastbare
  Temperaturaussage und deckt `T_MAX = 85 °C` ab. Ein Festigkeitsabfall zum
  oberen Ende hin ist bei Epoxid dennoch zu erwarten. Die Lastpfadrechnung
  setzt deshalb nur 0,50 MPa an (Faktor rund 38 gegenüber dem Aluminiumwert).
- Es liegt **kein Herstellerwert für ASA-GF oder ABS** vor. Der Aluminiumwert
  ist nur Größenordnung, keine Substratfreigabe.
- Das unveränderte Hersteller-PDF liegt derzeit **nicht** im Repo: die
  Arbeitsumgebung dieser Änderung hatte keinen Dateizugriff auf den
  UHU-Server. Die Angaben stammen aus dem veröffentlichten technischen
  Merkblatt und den Produktdaten des Herstellers. Sobald das PDF vorliegt,
  gehört es unverändert mit SHA-256 in `catalog.json`. Dieses Protokoll bleibt
  bis dahin die Projektquelle.

## Warum dieses Produkt für Laienmontage

- **Doppelkammerspritze mit statischem Mischer**: 1:1 wird beim Auspressen
  automatisch dosiert und gemischt. Keine Waage, kein Anrühren, kein
  Mischfehler, der häufigste Laienfehler bei 2K-Systemen, entfällt.
- **90 min Topfzeit**: der Rahmen wird in drei Schritten gefügt (zwei
  Halbrahmen, dann der Schluss). RK-1300 ließ dafür nur wenige Minuten.
- **Kein Aktivator**, keine Ablüftzeit, keine zweite Chemikalie.
- **Spalttolerant und standfest**: rund 35.000 mPa·s laufen an den senkrechten
  und über Kopf liegenden Fügeflächen nicht ab. Die 0,25 mm `TOL_JOINT`
  liegen im gut verklebbaren Bereich. RK-1300 verlangte dagegen 0,15–0,25 mm
  und war ab 0,4 mm außerhalb seines Optimums.
- Überall im Baumarkt erhältlich.

Diese Datei ist ein Projekt-Quellenprotokoll, nicht das originale
Hersteller-PDF. Für Verarbeitung und Sicherheit gelten das aktuelle
Herstellermerkblatt und das aktuelle Sicherheitsdatenblatt.
