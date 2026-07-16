# Abschätzung der Klebe-, Schraub- und Dachlastpfade

Stand: 2026-07-16 · Parameterstand `83aeba39` · Status
`PASS_ASSUMPTION_BASED`

## Kurzurteil

Die Baugruppe ist unter den dokumentierten Annahmen plausibel tragfähig,
aber ausdrücklich als **Hybridverbindung aus elastischer Klebung und acht
seitlichen Schrauben je Schnittstelle**. Eine reine Klebung wird für den
480-N-Windhüllfall nicht angesetzt. Die Rechnung addiert Kleber- und
Schraubentragfähigkeiten nicht: Die Schraubengruppe wird separat mit dem
kompletten Lastfall und zusätzlich 1,5-facher Lastkonzentration geprüft.

Der knappste geschätzte Lastpfad ist die nicht typidentifizierte beiliegende
ST4.2×25 im nachgerüsteten Holzrahmen, nicht der Klebstoff. Der automatisch
erzeugte Detailreport liegt unter
`build/analysis/load_paths/<parameter-hash>/assessment.{md,json}`.

## Lastfälle und Ergebnisse

| Lastfall | Elastikfuge oben allein | 8 Schrauben oben | Elastikfuge unten allein | 8 Schrauben unten | Holz–Dach, eine Fläche |
|---|---:|---:|---:|---:|---:|
| 480 N Windhülle | 157 % | 74 % | 174 % | 82 % | 35 % |
| +4 g abhebend und 2 g quer | 98 % | 43 % | 103 % | 47 % | 18 % |
| 200 N Schnee, drückend | 0 % | 21 % | 0 % | 21 % | 0 % |
| offene CFD-Haube, mittleres Netz ×1,5 | 71 % | 32 % | 69 % | 31 % | 12 % |

Die Werte sind Auslastungen, keine gemessenen Festigkeiten. Beim
Elastikfugen-Bond-only-Fall gehen direkte Kräfte und das Kippmoment über die
8-mm-Ringfuge. Die Schraubenspalten enthalten denselben vollständigen
Lastfall einschließlich Moment. Deshalb ist ein Bond-only-Wert über 100 %
kein System-Fail, solange die vollständige mechanische Kette intakt ist.

Zusätzliche Nachweise:

- Segmentstoß, volle 480 N durch einen Stoß: RK-1300 77 %, M5-Lochleibung
  62 %.
- Thermische Bewegung der 3-mm-Elastikfuge: 38 % des angesetzten
  50-%-Scherbewegungsgrenzwerts.
- Holzrahmen–Dach: nur eine der zwei 30-mm-GFK/Holz-Flächen wird angerechnet;
  die XPS-Außenkante und die zweite Fläche liefern keine rechnerische Reserve.
- Sensitivität der unteren Windlast-Schraubengruppe: Mit einer fehlenden
  Schraube steigt die Auslastung je nach Position auf 92–97 %. Bei zwei
  fehlenden Schrauben liegt selbst die günstigste Sechser-Konfiguration bei
  103 %. **Alle acht Schrauben je Schnittstelle sind daher Montage- und
  Inspektionspflicht; die Ein-Ausfall-Rechnung ist keine Freigabe für sieben.**

## Herleitung der Bemessungsannahmen

| Pfad | Hersteller-/Vergleichswert | verwendeter Projektwert | Abminderung |
|---|---:|---:|---|
| Sikaflex-522 / Carloflex normal | 1,8 MPa / >1,8 MPa Zugfestigkeit | 0,030 MPa | mindestens Faktor 60 |
| Sikaflex-522 / Carloflex Schub | kein TDS-Schubwert; 1,8 MPa Zugfestigkeit nur als Größenskala | 0,050 MPa Projektannahme | gegenüber Zugfestigkeit mindestens Faktor 36 |
| RK-1300 auf ASA-GF | 6 MPa auf ABS | 0,50 MPa | Faktor 12 |
| SikaForce/Sandwich | 9 MPa Schub, 14 MPa Zug; XPS-Vergleich TR 0,20 MPa | 0,050 MPa | durch unbekanntes Dachsandwich begrenzt |
| ST4.2×25 im Holz | ETA-Analogie 12 N/mm² bei ρk=350 kg/m³ | 174 N je Schraube | kmod 0,5 / γM 1,3 / zusätzlicher Analogiefaktor 0,5 |
| ST4.2×25 in ASA-GF | 356 N analytischer Gewindeauszug | 178 N je Schraube | zusätzlicher Detailfaktor 0,5 |

Die Elastikfugen-Abminderung ist absichtlich sehr groß: 85 °C liegen nur 5 K
unter der veröffentlichten 90-°C-Dauergrenze; zusätzlich sind Dauerlast,
Ermüdung, Bewitterung und reale Grenzflächen unbekannt. Sika selbst fordert
für elastische Klebungen Temperatur-, Dauer-, Ermüdungs- und
Alterungsfaktoren sowie typischerweise einen Designsicherheitsfaktor von
1,5–2,5 oder höher. Das verwendete Modell folgt diesem Prinzip, behauptet
aber keine von Sika freigegebenen Produktfaktoren.

Der 0,050-MPa-Schubwert ist insbesondere **kein aus dem TDS abgeleiteter
Schubkennwert**. Er ist eine bewusst niedrige Projektannahme; reale Haftung,
Alterung und Schubfestigkeit der konkreten Grenzflächen bleiben unbekannt.

## Festgelegter Oberflächenpfad

Die tragenden Klebezonen bleiben bei der weißen Lackierung maskiert. Für
Sikaflex-522 gilt folgende reproduzierbare Annahme:

1. ASA-GF und die unbekannte Belluna-Kunststofffläche sehr fein anschleifen,
   mit **Sika Cleaner P** reinigen und – als konservative ABS-Analogie –
   **Sika Primer-507** gemäß aktuellem Produktdatenblatt auftragen.
2. X150-GFK-Gelcoat sehr fein anschleifen, mit **Sika Cleaner P** reinigen
   und **Sika Aktivator-205** gemäß aktuellem Produktdatenblatt auftragen.
3. Sikaflex-522 weiß in der konstruktiv erzwungenen 3-mm-Fuge beziehungsweise
   in den Ringklebenuten einsetzen; die Raupen nicht auspressen.

Die aktuelle Sika-Vorbehandlungstabelle nennt ABS, GFK-Gelcoat und
2K-PUR-Lack, aber nicht ASA-GF. Primer-507 ist daher eine begründete Analogie,
keine Herstellerfreigabe. Die starke Abminderung bildet diese Unsicherheit ab.
Das inzwischen vorliegende Carloflex-TDS nennt >1,8 MPa Zugfestigkeit,
>450 % Dehnung und −40 bis +90 °C. Carloflex liegt damit in derselben
Rechenklasse wie 522 und darf mit denselben 0,030/0,050-MPa-Projektwerten
angesetzt werden. Es nennt GFK, Hart-PVC, Holz und Glas, aber nicht ASA-GF,
und bezeichnet seinen Kunststoffprimer nicht exakt. Deshalb bleibt 522 mit
der namentlich dokumentierten Sika-Vorbehandlung der reproduzierbarere
Standardweg. Carloflex ist eine technisch plausible, Belluna-konforme
Alternative; innerhalb einer Baugruppe werden die Produkte nicht gemischt.

Die Schraubenanalogie gilt nur für trockene Nadelvollholz-Rahmenleisten mit
charakteristischer Dichte mindestens 350 kg/m³, Faser längs zur jeweiligen
Rahmenseite und mindestens 18 mm wirksamer Gewindeeinbindung. Bei Sperrholz,
unbekannter Faserrichtung, geringer Dichte oder Fehlstellen ist der
174-N-Projektwert nicht belegt und die Rechnung neu zu bewerten.

## Erkenntnisgrenzen des Modells

- Starrer Ring und linear-elastische Schraubenverteilung; lokale Peelspitzen,
  Gehäusenachgiebigkeit und dynamische Ausfallfolgen werden nicht aufgelöst.
- Der stark abgeminderte axiale Schrauben-Analogiewert wird auf den gesamten
  Axial-/Querlastvektor angewendet. Für die beiliegende Belluna-ST4.2×25 liegt
  keine identifizierte Holzschraubenzulassung vor.
- Acht gleichmäßig tragende Schrauben, ungerissenes trockenes Vollholz und
  ausreichende Rand-/Schraubenabstände werden vorausgesetzt.
- Das reale X150-GFK/XPS-Sandwich ist nicht typgeprüft. Nur eine Holz/GFK-
  Fläche und 0,050 MPa werden angerechnet; das ist eine konservative
  Plausibilisierung, keine Werkstoffidentifikation.
- CFD, FEM und Lastpfadrechnung ersetzen keine Bauteilprüfung oder
  Herstellerfreigabe.

## Reproduzierbarkeit

```sh
python3 -m pipeline connections
```

Die Stufe läuft außerdem nach `pipeline engineering` und nach `pipeline cfd`.
Der 480-N-Windhüllfall bleibt auch dann bestehen, wenn die CFD-Kräfte kleiner
ausfallen.

## Primärquellen

- [Sikaflex-522: 1,8 MPa, 400 %, −50 bis +90 °C und Originalsubstrat-Hinweis](https://industry.sika.com/en/home/transportation/sealants/adhesive-sealants/sikaflex-522.html)
- [Sika Compendium Elastic Bonding: Reduktions- und Sicherheitsfaktoren, Kombinationsgleichung und thermische Bewegung](https://industry.sika.com/dms/getdocument.get/8ffff4cd-c90d-4d24-969d-ee4db9093cf3_global-industry/compendium-elasticbonding.pdf)
- [Sika STP-Vorbehandlungstabelle, Version 8 (02/2026)](https://industry.sika.com/dms/getdocument.get/776a779a-10a6-413c-b20b-c46467315e33/pre-treatment-chartforsilanterminatedpolymersstp-sikaflex-500ser.pdf)
- [WEICON RK-1300: Zugscherwerte und Temperaturbereich](https://media.weicon.de/fmds/307278/dld%3Ainline/DE_TDS_10560060_RK-1300.pdf)
- [SikaForce-710 L35: Holz/GFK/XPS und 9/14-MPa-Kennwerte](https://deu.sika.com/dms/getdocument.get/41466f3f-1639-4fc4-8298-5c9a0a2d34e1/sikaforce-710-l35.pdf)
- [URSA-XPS-Vergleich: TR 200](https://ursa.de/wp-content/uploads/2023/05/DB-xps.pdf)
- [Würth ETA-11/0190: Holzschrauben-Ausziehparameter und Mindesteinbindung](https://www.wuerth.de/web/media/downloads/assy/ETA_110190_Wuerth_Holzschrauben_EN_23-7-2018_-elektronische_Kopie_Z50406.18~1.pdf)
- [Carloflex 410 UV: Quellenprotokoll des bereitgestellten Carlofon-TDS](../references/datasheets/adhesives/carloflex-410-uv-source.md)
- [Belluna Carloflex-Anwendungsempfehlung](https://belluna.eu/shop/carloflex/)
