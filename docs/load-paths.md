# Abschätzung der Klebe-, Schraub- und Dachlastpfade

Stand: 2026-07-16 · Parameterstand `78f560c8` · Status
`PASS_ASSUMPTION_BASED`

## Kurzurteil

Die Baugruppe ist unter den dokumentierten Annahmen plausibel tragfähig. Die
Schnittstellen werden bewusst unterschiedlich behandelt:

- Belluna-Platte → Adapter: acht seitliche ST4.2×25 tragen den vollständigen
  Lastfall; der obere 8-mm-Klebering wird nicht hinzuaddiert.
- Adapter → Dach: eine 25 mm breite, geschlossene Elastikfuge trägt den
  vollständigen Lastfall allein. Es gibt keine Verschraubung in den
  Holzrahmen und damit keine mechanische Rückfallebene.
- Holzrahmen → Dachsandwich: nur eine der beiden vollflächigen
  SikaForce-Verbindungen wird rechnerisch angesetzt.
- Segmentstöße: RK-1300 und zwei M5 je Stoß werden getrennt geprüft; selbst
  ein einzelner verbleibender M5 muss die volle 480-N-Hülle aufnehmen.

Der automatisch erzeugte Detailreport liegt unter
`build/analysis/load_paths/<parameter-hash>/assessment.{md,json}`.

## Lastfälle und Ergebnisse

| Lastfall | obere Fuge allein | 8 Schrauben oben | 25-mm-Dachfuge allein | Holz–Dach, eine Fläche | serieller Pfad |
|---|---:|---:|---:|---:|---|
| 480 N Windhülle | 157 % | 74 % | 58 % | 35 % | PASS |
| +4 g abhebend und 2 g quer | 98 % | 43 % | 34 % | 18 % | PASS |
| 200 N Schnee, drückend | 0 % | 21 % | 0 % | 0 % | PASS |

Die Werte sind Auslastungen, keine gemessenen Festigkeiten. Der obere
Bond-only-Wert über 100 % ist kein System-Fail, weil dort die vollständige
Schraubengruppe separat besteht. An der unteren Schnittstelle wäre ein Wert
über 100 % dagegen ein System-Fail.

Zusätzliche Nachweise:

- Segmentstoß, volle 480 N durch einen Stoß: RK-1300 55 %, zwei M5 gemeinsam
  31 %, ein verbleibender M5 62 %.
- Thermische Bewegung der 3-mm-Elastikfuge: 41 % des angesetzten
  50-%-Scherbewegungsgrenzwerts.
- Holzrahmen–Dach: nur eine 30-mm-GFK/Holz-Fläche wird angerechnet; XPS und
  zweite Fläche liefern keine rechnerische Reserve.
- Obere Schraubengruppe: Mit einer fehlenden Schraube 83–87 %; bei zwei
  fehlenden Schrauben bestehen nicht alle Anordnungen. Alle acht oberen
  Schrauben bleiben Montage- und Inspektionspflicht.

## Herleitung der Bemessungsannahmen

| Pfad | Hersteller-/Vergleichswert | verwendeter Projektwert | Abminderung |
|---|---:|---:|---|
| Sikaflex-522 / Carloflex normal | 1,8 MPa / >1,8 MPa Zugfestigkeit | 0,030 MPa | mindestens Faktor 60 |
| Sikaflex-522 / Carloflex Schub | kein TDS-Schubwert | 0,050 MPa Projektannahme | gegenüber Zugfestigkeit mindestens Faktor 36 |
| RK-1300 auf ASA-GF | 6 MPa auf ABS | 0,50 MPa | Faktor 12 |
| SikaForce/Sandwich | 9 MPa Schub, 14 MPa Zug; XPS-Vergleich TR 0,20 MPa | 0,050 MPa | durch unbekanntes Dachsandwich begrenzt |
| ST4.2×25 in ASA-GF | 356 N analytischer Gewindeauszug | 178 N je Schraube | zusätzlicher Detailfaktor 0,5 |

Die Elastikfugen-Abminderung deckt 85 °C nahe der veröffentlichten
90-°C-Grenze, Dauerlast, Ermüdung, Bewitterung und unbekannte reale
Grenzflächen ab. Der 0,050-MPa-Schubwert ist ausdrücklich kein aus einem TDS
abgeleiteter Kennwert, sondern eine niedrige Projektannahme.

## Warum die Geometrieänderung wirkt

Ein lediglich nach außen verbreiterter 8-mm-Ring hätte die Windhüll-Auslastung
nur von rund 174 % auf rund 148 % gesenkt. Entscheidend ist, dass die untere
Fuge jetzt von 8 auf 25 mm wächst und mit Innenmaß 410 mm und Außenmaß 460 mm
vollständig über dem 30-mm-Holzrahmen liegt. Ihre Fläche steigt dadurch auf
43.500 mm². Der Adapter wächst außen auf 540×540 mm; die zusätzliche Breite
schafft außerdem Platz für zwei M5 je Stoß.

Der geschlossene Unterkragen dient nur der Zentrierung. Der Holzrahmen bleibt
trotz entfallener Schrauben zwingend: Er verteilt die Dachfugenlast in beide
GFK-Häute und schützt den XPS-Kern gegen lokale Pressung.

## Festgelegter Oberflächenpfad

Die tragenden Klebezonen bleiben bei der weißen Lackierung maskiert.

1. ASA-GF und Belluna-Kunststoff sehr fein anschleifen, mit **Sika Cleaner P**
   reinigen und als ABS-Analogie **Sika Primer-507** nach aktuellem
   Produktdatenblatt auftragen.
2. X150-GFK-Gelcoat sehr fein anschleifen, mit **Sika Cleaner P** reinigen und
   **Sika Aktivator-205** nach aktuellem Produktdatenblatt auftragen.
3. Sikaflex-522 weiß in der konstruktiv erzwungenen 3-mm-Fuge einsetzen, nicht
   auspressen und die 25-mm-Dachfuge rundum hohlraumfrei schließen.
4. Bis zur vollständigen Durchhärtung nach aktuellem Produktdatenblatt
   bewegungsfrei halten und weder fahren noch belasten. Die breite
   feuchtigkeitshärtende Fuge bei der Wartezeit berücksichtigen.

ASA-GF ist in der Sika-Vorbehandlungstabelle nicht ausdrücklich genannt.
Primer-507 bleibt daher eine begründete Analogie, keine Herstellerfreigabe.
Carloflex 410 UV ist eine technisch plausible Belluna-Alternative, solange
sein Kunststoffprimer prozesssicher festgelegt wird. Produkte innerhalb einer
Baugruppe nicht mischen.

## Erkenntnisgrenzen

- Starrer Ring und linear-elastische Lastverteilung; lokale Peelspitzen,
  Gehäusenachgiebigkeit und dynamische Ablösung werden nicht aufgelöst.
- Die untere 25-mm-Fuge ist der einzige Adapter-Dach-Lastpfad. Fehlstellen,
  Randablösung oder mangelhafte Vorbehandlung haben keine Rückfallebene.
- Zwei M5 werden gleichmäßig belastet angenommen; Lochspiel und expliziter
  Bolzenkontakt sind nicht aufgelöst.
- Das reale X150-GFK/XPS-Sandwich ist nicht typgeprüft.
- CFD, FEM und Lastpfadrechnung ersetzen keine Bauteilprüfung oder
  Herstellerfreigabe.

## Reproduzierbarkeit

```sh
python3 -m pipeline connections
```

Der 480-N-Windhüllfall bleibt auch dann bestehen, wenn CFD-Kräfte kleiner
ausfallen.

## Primärquellen

- [Sikaflex-522](https://industry.sika.com/en/home/transportation/sealants/adhesive-sealants/sikaflex-522.html)
- [Sika Compendium Elastic Bonding](https://industry.sika.com/dms/getdocument.get/8ffff4cd-c90d-4d24-969d-ee4db9093cf3_global-industry/compendium-elasticbonding.pdf)
- [Sika STP-Vorbehandlungstabelle, Version 8 (02/2026)](https://industry.sika.com/dms/getdocument.get/776a779a-10a6-413c-b20b-c46467315e33/pre-treatment-chartforsilanterminatedpolymersstp-sikaflex-500ser.pdf)
- [WEICON RK-1300](https://media.weicon.de/fmds/307278/dld%3Ainline/DE_TDS_10560060_RK-1300.pdf)
- [SikaForce-710 L35](https://deu.sika.com/dms/getdocument.get/41466f3f-1639-4fc4-8298-5c9a0a2d34e1/sikaforce-710-l35.pdf)
- [URSA-XPS-Vergleich TR 200](https://ursa.de/wp-content/uploads/2023/05/DB-xps.pdf)
- [Carloflex-Quellenprotokoll](../references/datasheets/adhesives/carloflex-410-uv-source.md)
