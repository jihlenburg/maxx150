# Design: 3D-gedruckter Adapterrahmen — Belluna Super Fan im Mini-Heki-Ausschnitt (Challenger X150 / Chausson X550)

Stand: 2026-07-16 · Parameterstand `8eb8b79f` · Status `PROTOTYPE_ONLY`

## 1. Ziel und Kontext

Der Belluna Super Fan Dachventilator soll den vorhandenen Mini-Heki im 400×400-mm-Dachausschnitt
eines Challenger X150 (baugleich Chausson X550) ersetzen. Das Dach dieser Fahrzeuge hat eine
umlaufende hohe Kante am Heck; die Lüfterhaube (Grundriss 593 mm lang, Überstand nach hinten)
würde beim Öffnen/Schließen mit dieser Kante kollidieren. Ein Adapterrahmen („Plinthe") hebt die
Lüfterbasis um **28 mm** an. Vorbild ist ein im X150-Forum dokumentierter, handgefertigter
Holzsockel; hier entsteht stattdessen ein **algorithmisch erzeugtes, 3D-gedrucktes, per FEM
verifiziertes** Bauteil.

Erzeugung und Verifikation laufen vollständig skriptiert über headless FreeCAD
mit Gmsh-Vernetzung und CalculiX-Solver aus dem FreeCAD-Bundle. Kein GUI-Schritt
ist Teil des reproduzierbaren Workflows.

## 2. Feste Eingangsdaten

### Aus der Belluna-Einbauanleitung (liegt vor, 22 S.)
| Größe | Wert |
|---|---|
| Lochgröße (Dachausschnitt) | 400 × 400 mm, Eckenradius R5 |
| Zulässige Einbauwandstärke | 27–80 mm |
| Vierkantwellen (mitgeliefert) | 120 mm ↔ 27–47 mm · 140 mm ↔ 48–67 mm · 160 mm ↔ 68–80 mm |
| Karosseriebefestigungsplatte | 593 × 420/450 mm, asymmetrischer Flansch (Überstand heckseitig) — Achtung, eigene Vermessung weicht ab: Flansch 450 × 450 voll symmetrisch, Kragen 397 (`reference_models/belluna.py`); 593 × 420 entspricht der Haube |
| Innenrahmen Lüfter | 445 × 445 mm |
| Haubenhöhe über Dach | 127 mm (zu) / 182 mm (offen) |
| Unterbau unter Dach | 31–47 mm |
| Befestigung laut Hersteller | Verklebung der Platte mit Carloflex (Ringklebenut); Verschraubung von oben nicht empfohlen (Wassereintritt); mechanische Option: seitliche Verschraubung in Holzrahmen |
| Schrauben | ST4.2×25 (Platte↔Karosserie, oben, nicht empfohlen) · ST3.9×40 (Lüfter↔Karosserie) · PT4.0×12 (Zwischen-↔Innenrahmen) |
| Masse Belluna | 5,0 kg |

### Fahrzeug (Challenger X150)
| Größe | Wert / Quelle |
|---|---|
| Dachstärke X-Modelle | **35 mm** (Hersteller-Diagramm: GFK-Außenhaut, XPS-Kern, Holzlage innen) |
| Dach am Ausschnitt | plan (Fotobefund), Mini-Heki in Dichtmittelbett verklebt |
| Reisegeschwindigkeit | bis 160 km/h |

### MaxxFan Deluxe (Hüllkurven-Lüfter für die Auslegung, Maßblatt liegt vor)
| Größe | Wert |
|---|---|
| Haube L × B | 586 × 408 mm |
| Höhe geschlossen / offen | 132 / 236 mm |
| Hecküberstand offen ab Dachausschnitt | 179 mm (123 mm bis Haubenknick) |
| Masse | 6,5 kg (Belluna: 5,0 kg) |

### Vermessene Belluna-Karosseriebefestigungsplatte
- Flanschoberseite plan, Schraublöcher verstöpselt; schwarze Dichtung umlaufend am Kragenfuß (Dichtebene Platte↔Lüftereinheit).
- Unterseite: Klebe-/Kontaktzone ist der **äußere Flanschbereich mit konzentrischen Ringrippen**
  (Ringklebenut); die Dreiecks-Gussets tauchen in den Ausschnitt und benötigen
  keine Deckflächenfreistellung.
- Unterer Einbaukragen: 397 mm außen, 1,5 mm Wand, 19 mm tief. Daraus folgen
  nominal 1,5 mm Radialluft je Seite in der 400-mm-Öffnung.
- Oben acht Federstahlclips als Schraubaufnahmen; schwarzer Dichtring 6 mm breit.
- Die versionierten STEP-/STL-Dateien unter `references/belluna/models/` sind
  eine Projekt-Rekonstruktion und ausdrücklich kein Hersteller-CAD.

### Abgeleitete Kerngröße
Effektive Einbauwandstärke = 35 mm Dach + 28 mm Adapter = **63 mm → 140er-Vierkantwelle**
(Bereich 48–67 mm, 4 mm Reserve zur Obergrenze). Die Pipeline berechnet die Wellenwahl aus den
Parametern und schreibt sie in die Montagenotiz.

## 3. Anforderungen

1. **Funktion:** Lüfterbasis um 28 mm anheben (`H_RAISE`, Parameter); Innenöffnung 400×400 mm
   fluchtend zum Dachausschnitt; Einbaukragen des Lüfters wird durchgesteckt wie durch ein 63-mm-Dach.
2. **Festigkeit:** Auslegungsanströmung 200 km/h (= 160 km/h Reise + Böen-/Gegenwindreserve),
   Schlechtweg ±4 g vertikal / ±2 g quer auf 6,5 kg Auslegungsmasse (Maxxfan-Hüllkurve; Belluna 5,0 kg).
3. **Temperatur:** Bauteiltemperatur −20 … **+85 °C** dauerhaft formstabil und tragfähig.
4. **Fertigung:** Druckservice, druckerunabhängig; Segment-Boundingbox ≤ 300 mm
   Kantenlänge (`SEG_MAX_BBOX` = 300 mm; Bambu H2D 350 mm verfügbar);
   stützenfrei druckbar. Das reale Segmentmaß ist ein automatisches DFM-Gate.
5. **Material & Prozess (§3.5):** **Würth ASA GF15 Verkehrsschwarz ähnlich
   RAL 9017, 1,75 mm, Art.-Nr. 4954641200** aus lokaler FDM-Fertigung
   (Plan-of-Record 2026-07-15). 15 % Glasfaser; gehärtete Düse und geschlossener,
   temperierter Bauraum sind Projektpflicht. Drucklage ist Deckfläche nach unten;
   47°-Kammerdächer, 47°-Entwässerungsfase und Ø4-Querkanäle sind supportfrei
   (47° zählen ab Horizontale = 43° Überhang aus der Senkrechten, konform zur
   45°-DFM-Grenze in §7).
   Brim ≥10 mm und langsames Abkühlen bleiben Pflicht. Würth nennt Dichte
   1,1 g/cm³ und HDT/B 99 °C bei 0,45 MPa, aber keinen HDT-Wert bei 1,82 MPa.
   Die publizierten mechanischen Werte stammen ausdrücklich aus Halbzeug, nicht
   aus FDM-Probekörpern. Deshalb bleiben E=3000 MPa, Zug=45 MPa, CTE=60e-6 1/K
   und Z-Faktor 0,5 konservative Projektannahmen. Da typgeprüfte XY-/Z-Coupons
   aktuell nicht realistisch verfügbar sind, werden diese Faktoren nicht
   hochgestuft; das Ergebnis bleibt `PASS_ASSUMPTION_BASED` (den Status
   `PROTOTYPE_ONLY` halten die offenen physischen Gates, s.
   `docs/verification.md`). Pauschales Tempern ist nicht freigegeben.
   Der schwarze Rohling wird vor dem Dacheinbau zwingend weiß beschichtet:
   Mipa 1K-Plastic-Grundierfiller-Spray (Art.-Nr. 213390000) plus Mipa PUR HS
   2K-PUR-Acryl-Fahrzeuglack RAL 9003 Signalweiß glänzend und Mipa 2K-MS-Härter
   MS 25 (2:1 Volumen). Weiß ist Teil der Thermikauslegung. ASA-GF steht nicht
   in der Primerliste; der Lack ist deshalb kein struktureller Lastpfad und
   wird jährlich kontrolliert.
6. **Befestigung:** Adapter ↔ Dach und Platte ↔ Adapter werden mit
   **Sikaflex-522 weiß** verklebt und abgedichtet (Elastikfuge bzw.
   Ringklebenut). **Carloflex 410 UV weiß** ist eine Belluna-konforme
   Alternative. Sein TDS nennt >1,8 MPa Zugfestigkeit, >450 % Dehnung und
   −40 bis +90 °C; die Lastpfadrechnung setzt daher für beide Produkte
   dieselben stark abgeminderten Grenzwerte von 0,030 MPa normal und
   0,050 MPa Schub an. 522 bleibt Standard, weil Sika den
   Vorbehandlungsprozess namentlich dokumentiert; das Carloflex-TDS nennt
   seinen Kunststoffprimer nicht. Je Baugruppe nur eines der beiden Systeme
   vollständig verwenden und nicht mischen. Die
   strukturellen Klebezonen bleiben lackfrei: ASA-GF/Belluna-Kunststoff sehr
   fein anschleifen, Sika Cleaner P und als ABS-Analogie Sika Primer-507;
   GFK-Gelcoat sehr fein anschleifen, Sika Cleaner P und Sika Aktivator-205
   gemäß jeweils aktuellem Produktdatenblatt. Acht Belluna-ST4.2×25 verbinden
   die äußeren Belluna-Seitenlöcher mit den lokalen Universalrippen; jede
   Seite hält ±140 und ±165 vor, ohne offene Vorratslöcher. Der Adapter wird
   zusätzlich mit acht seitlichen ST4.2×25 durch den Unterkragen im Holzrahmen
   gesichert. Diese Schrauben sind eine physische Rückfallebene; wegen der
   unbekannten Holz-, GFK- und Gewindetragfähigkeit werden sie rechnerisch
   nicht angerechnet. Der Primärnachweis wird allein von zwei getrennten,
   jeweils 10 mm breiten Sikaflex-Raupen geführt. Die äußere Raupe bleibt
   geschlossen und wasserdicht. Die innere besitzt acht 5-mm-Unterbrechungen
   zur trockenen Öffnungsseite, damit der dazwischenliegende 4-mm-Kanal
   Feuchte zur Durchhärtung nachführen kann. Die wirksame Fläche beträgt
   33.313 mm² bei 406 mm Innen- und 454 mm Außenmaß und liegt vollständig
   über dem nachgerüsteten 30-mm-Holzrahmen im XPS. Der Holzrahmen wird mit
   **SikaForce-710 L35 + SikaForce-010** (2K-PUR, 100:25 Volumen bzw.
   100:19 Gewicht) vollflächig eingesetzt. Das System ist ausdrücklich für
   Holz/GFK mit EPS/XPS-Sandwichkernen spezifiziert; Auftragsmenge und
   Pressprozess müssen gleichmäßig, hohlraumarm und unterhalb der
   Druckfestigkeit des Dachkerns bleiben. Er ist vollflächig verklebter
   Lastverteiler und Kompressionsschutz. Seine Schraubtragfähigkeit wird ohne
   Bauteilprüfung dennoch nicht als rechnerischer Lastpfad angesetzt. Verwendet werden
   trockene Nadelvollholz-Leisten mit ρk ≥ 350 kg/m³ und Faser längs zur
   jeweiligen Rahmenseite.
   Die zwei Belluna-Mittellöcher an den Segmentstößen bleiben frei. Keine Verschraubung
   von oben durch eine Dichtfläche.
   **Reale Einbausituation (User 2026-07-12): KEINE harte Klemmkette durchs Sandwich** —
   Lüfter geklebt + Kragen formschlüssig im Schacht, von unten nur die Zierblende.
   LF3 bleibt als bewusst konservative Hüllkurve (Montage-Grenzfälle). Die
   untere Doppelraupe trägt den Primärfall allein; die acht Seitenschrauben
   bleiben davon getrennte, unqualifizierte Reserve.
7. **Dichtheit:** 16 schmale Abstandspads definieren 3 mm Dachabstand; die
   0,6-mm-Applikationsführungen ergeben darin 3,6 mm wirksame Raupenhöhe.
   Geschlossene äußere Raupe und Kehlnaht bilden die Wassersperre. Die
   seitlichen Schrauben werden ausschließlich von der trockenen Öffnungsseite
   gesetzt und abgedichtet; sie durchdringen weder Dachaußenhaut noch äußere
   Wassersperre.

## 4. Bauteilgeometrie

**Grundform:** rechteckige Plinthe, Höhe `H_RAISE` = 28 mm, Innenöffnung 400×400 mm mit R5-Ecken.

**Querschnitt (umlaufend):**
- **Deckfläche:** plane Klebefläche unter der Ringklebenut-Zone der Platte; außerhalb
  des 450-mm-Flansches geht sie in eine 47°-Entwässerungsfase über. Breite je Seite
  einzeln parametrisierbar (`W_TOP_FRONT/REAR/LEFT/RIGHT`, Stand 50 mm), da der
  Plattenflansch asymmetrisch ist. Innen liegender Bereich mit parametrischer **Freistellung**
  (Tiefe `REC_GUSSET`) für die Dreiecks-Gussets der Plattenunterseite.
- **Innenwand:** 8 mm umlaufend; jede Seite besitzt an ±140 und ±165 mm
  lokale 10-mm-Vollmaterialrippen über den ganzen 25-mm-Schraubpfad. Acht
  der sechzehn möglichen Pfade werden durch die realen Belluna-Löcher genutzt.
  Die Rippen sind oben an die Deckplatte angebunden und laufen unten mit 45°
  aus; dadurch bleiben die 43-mm-Kammerzellen weitgehend erhalten und der
  Druck bleibt supportfrei. Kollidierende Ventkanäle werden innerhalb ihrer
  Zelle aus der Rippe verschoben.
- **Außenwand:** geschlossen, unten gefast für die Elastikfugen-Kehlnaht zum Dach.
- **Innenleben:** geschlossene Rippenkammern (zwei konzentrische Kammerringe je Seite,
  Zellenraster parametrisch, Wände/Platten voll dicht gedruckt). Kammerböden (in
§3.5 aus der anderen Bezugslage „Kammerdächer" genannt) als 47°-Chevron
  (stützenfrei in Druckorientierung), horizontale Ø4-Druckausgleichsbohrungen je Zelle
  zur Innenseite. Stoß- und Schraubzonen bleiben
  massiv. Die zwei 17-mm-Ringe füllen das kompakte 50-mm-Band, ohne es als
  28-mm-Massivquerschnitt zu drucken; die Außenwand bleibt 3 mm.
  Eckkammern (90°-Rotationsfortsetzung der Kammerringe um die vier Eckblöcke,
  Task 17) sind seit 2026-07-12 Default EIN (`CORNER_CHAMBERS = True`, Task 20;
  Verzugs-/Gewichtsnutzen, FEM-verifiziert — abschaltbar, die AUS-Variante bleibt
  volumen-anker-geprüft reproduzierbar). Damit ist die Festigkeit geometrie-definiert
  (druckprofil-unabhängig); die FEM rechnet auf der echten Kammergeometrie mit vollem
  E-Modul (INFILL_FACTOR = 1,0). [Entscheidung mit User 2026-07-12, ersetzt
  Slicer-Infill-Ansatz]
- **Unterseite:** 16 längliche Abstandspads (2,5×20×3 mm), jeweils innen und
  außen nahe den acht unteren Schraubachsen. Sie liegen vollständig in den
  trockenen 3-mm-Randstreifen über dem Holzrahmen und greifen nicht in die
  Klebefläche ein. Zwei umlaufende, nur 0,6 mm tiefe und 10 mm breite
  Applikationsführungen liegen ebenfalls vollständig über dem 30-mm-Holzrahmen.
  Die äußere Führung ist geschlossen; die innere besitzt acht modellierte
  5-mm-Brücken, welche den 4-mm-Mittelkanal zur trockenen Öffnungsseite
  entlüften. Gegenüber den früheren 68 Ø8-mm-Rundnoppen sinken harte
  Kontaktfläche und lokale Montagepressung deutlich.

**Segmentierung:** Standard **ein rotationsidentisches L-Ecksegment, 4× drucken**,
Stöße in den Seitenmitten (Spannungsmaxima liegen an den Ecken). Stoßverbindung: Halbüberlappung
(Toleranz `TOL_JOINT` = 0,25 mm, nach Probedruck justierbar) + eine
Durchsteckschraube M5 je Stoß + Klebefläche. Unter der vollständigen
konservativen 480-N-Stoßhülle liegt der einzelne M5 bei 62 %
Lochleibungsauslastung. Die Epoxidklebung wird getrennt mit 77 % nachgewiesen.
Die vier
Kopien werden nur um Z gedreht, nie gespiegelt; ein starker Geometrietest
prüft die Rotationsidentität über die symmetrische Differenz.

**Thermik konstruktiv:** ASA-GF α = 60 µm/(m·K), konservative
Datenblatt-Lückenannahme, vs. GFK ≈25. Der mit Epoxid und M5 vollständig
gefügte Rahmen wird thermisch als **500-mm-Baugruppe**, nicht als entkoppeltes
Drucksegment gerechnet. Von 20 °C Klebetemperatur bis 85 °C entstehen 1,14 mm
Differenzdehnung über die Kante; symmetrisch je Ende (0,57 mm) ergibt dies
rund 38 % des zulässigen Scherbewegungsgrenzwerts (50 % der konservativ mit
3 mm angesetzten Fugenhöhe = 1,5 mm); die reale Raupenhöhe in den
0,6-mm-Führungen beträgt 3,6 mm.
Die Lastaufnahme erfolgt ausschließlich durch die elastische Klebschicht.
Die Pads sind Montageanschläge, kein dauerhafter rechnerischer Lastpfad.

**Dichtheitskonzept (Mehrteiligkeit):** Dichtheit kommt von durchgehenden Elastomer-Ebenen,
nicht vom Druckteil — die Segmentstöße werden von diesen Ebenen überbrückt. Barrierenkette:
(1) erst nach vollständiger Durchhärtung der tragenden Dachraupen aufgebrachte,
zugängliche Sikaflex-522-Schutzkehle außen, umlaufend geschlossen über alle
Stöße; sie ist erneuerbare Wetter-/Kontrollfuge und erhält keine
Tragfähigkeitsgutschrift; (2) äußere
untere Raupe, geschlossen über die Stöße; die innere Raupe ergänzt Tragfläche,
bleibt aber an acht Trockenraum-Vents offen; (3) Ringklebenut der Belluna-Platte auf der
Deckfläche, ebenfalls geschlossen; (4) Stöße selbst: Halbüberlappungs-Labyrinth + vollflächige
2K-Epoxidverklebung der Fügeflächen (M5 = Verpressung/Redundanz, nicht Dichtung).

**Klebstoffwechsel 2026-08-14:** WEICON RK-1300 ist abgelöst. Der MMA-Klebstoff
war rechnerisch passend, hat am realen gedruckten ASA-GF aber nicht getragen.
Ausgewählt ist jetzt **UHU plus endfest**, ein 2K-Epoxid mit 90 min Topfzeit,
−40 bis +100 °C und 1:1-Doppelkammerspritze. Es ist ohne Aktivator, Waage und
Zeitdruck zu verarbeiten und deshalb für die Laienmontage geeignet. Der
Bemessungswert bleibt bewusst 0,50 MPa, obwohl er nun aus rund 19 MPa auf
Aluminium statt aus 6 MPa auf ABS abgeleitet wird: der Wechsel soll die
Nachweiskette nicht rechnerisch entlasten. Der WEICON Epoxyd-Minutenkleber
bleibt trotzdem verworfen, sein TDS nennt nur 2,7 % Bruchdehnung und Tg 44,7 °C
(46,1 °C nach Tempern), also deutlich unter `T_MAX = 85 °C`. Dieselbe Grenze
schließt alle schnellen 5-Minuten-Epoxide aus. Die 0,25 mm `TOL_JOINT` bleiben
unverändert, denn sie liegen im gut verklebbaren Bereich des Epoxids. Damit ist
keine Geometrieänderung verbunden und `GEOM_REV` bleibt stehen.
FDM-Mikroporosität: ≥4 Perimeter als dichte Haut; der festgelegte Mipa-Primer +
RAL-9003-2K-PUR-Decklack ist PFLICHT (Solarreflexion, Porenschluss, Wetterschutz).
Validierung praktisch (Flutungstest, dann Hochdruck aus
ISO-20653-9K-Abstand am verbauten Sockel); eine normative IP6K9K-Zertifizierung wäre
Prüfstandssache. Systemgrenze: der Belluna selbst ist nur IPX4 — Ziel ist die dichte
Dachdurchdringung, nicht ein dichter Lüfter.

## 5. Software-Architektur

```
maxx150/
├── params.py             # einzige Parameterquelle
├── model/                # B-Rep, Segmente und DFM
├── fem/                  # Lastfälle, Solver, Analytik und Report
├── analysis/             # digitale Passungsanalyse
├── export/               # STEP/STL/3MF und technische Notiz
├── render/               # technische Ansichten und Heatmaps
├── montage/              # Generator der Montageanleitung
├── pipeline/             # zentrale CLI und Release-Paketierung
├── reference_models/     # vermessene externe Schnittstellen
├── references/           # Datenblätter, Anleitungen und Referenz-CAD
├── build/                # generiert, hash-segregiert, gitignored
├── release/current/      # manifestierter Fertigungsstand
└── tests/                # Invarianten und Regressionen
```

**Datenfluss:** `params.py` → `frame.py` (ein wasserdichtes Solid) → (a) `segments.py` →
`export.py`; (b) `fem/`. Der Report verknüpft Parameterstand ↔ FEM-Ergebnis ↔ Datei-Hashes:
kein Druckfile ohne zugehörige Verifikation.

**FEM-Modellstrategie:** Globalnachweis am **ungeteilten** Rahmen (obere Steifigkeitsschranke),
Detailnachweis am Stoß-Submodell mit den Schnittkräften aus dem Globalmodell (untere Schranke).
Kein Vollkontaktmodell aller vier Segmente in CalculiX. Die globale Lagerung
liegt seit GEOM_REV 9 verteilt auf den Böden beider Kleberführungen. Sie
idealisiert Dach und ausgehärteten Klebstoff weiterhin starr, fixiert aber
nicht mehr die 16 Montagepads und vermeidet damit die früheren künstlichen
Punktspannungen an 68 Rundnoppen.

**Fehlerbehandlung:** Jeder Schritt validiert sein Ergebnis (Solid `isValid()` + geschlossene
Shell, Mindestwandstärke, Mesh-Qualität, CalculiX-Konvergenz) und bricht mit klarer Meldung ab,
statt fehlerhafte Artefakte zu exportieren.

## 6. FEM-Verifikation

**Lastfälle:**
| # | Lastfall | Ansatz |
|---|---|---|
| LF1 | Fahrtwind | 200 km/h → q ≈ 1,85 kPa; Haube offen (zulässig lt. Anleitung), Worst Case MaxxFan Deluxe: A = 0,408 m × (0,236 + 0,028) m ≈ 0,108 m² (Maßblatt), cd ≈ 1,2 → ~240 N horizontal, ×2 Sicherheit = **480 N** am Hebelarm der Haubenhöhe (Kippmoment auf Deckfläche) |
| LF2 | Schlechtweg | quasistatisch ±4 g vert. / ±2 g quer auf 6,5 kg → ±255 N / ±128 N |
| LF3 | Klemmung/Montage | Vorspannung Innenrahmen-Verschraubung (aus 0,7 Nm Anzugsmoment lt. Anleitung ≈ 400–600 N je Schraube, konservativ 600 N × 4) + Anzug der Seitenschrauben; Schraubenauszug/Flächenpressung Innenwand. **Konservative Hüllkurve: real keine harte Klemmung (s. §3.6)** |
| LF4 | Schnee/Stand | 0,75 kN/m² auf 0,25 m² Grundfläche = 187,5 N, konservativ 200 N angesetzt |
| LF5 | Thermik | Einsatzbereich −20…+85 °C; bemessungsrelevant ΔT 65 K ab 20 °C Klebetemperatur, CTE-Differenz ASA↔GFK; Nachweis Elastikfuge (analytisch, `fem/analytic.py`) |

**Materialabminderung Würth ASA GF15:** Projektbasis 45 MPa / E 3000 MPa;
keine Behauptung gedruckter Herstellerwerte, da Würth nur Halbzeugdaten nennt.
Faktoren: Temperatur 0,5 · Z-Schichthaftung 0,5 (konservative Annahme) ·
Kriechen 0,4. → zulässig **4,50 MPa dauerhaft**, **11,25 MPa kurzzeitig**.
Drucklage so, dass
Hauptspannungen in der XY-Ebene liegen (Z sieht überwiegend Druck).

**Bestehenskriterien (Pipeline-Gate, automatisch):**
1. σ_vMises ≤ zulässig je Lastfall (Sicherheiten enthalten)
2. Verformung der Deckfläche < 0,5 mm (Dichtheit der Klebefuge)
3. Elastische Klebfuge: 0,030 MPa normal / 0,050 MPa Schub als stark
   abgeminderte Projektwerte; Schraubengruppen separat mit vollständigem
   Lastfall und 1,5-facher Lastkonzentration
4. Flächenpressung/Auszug an der Innenwand ≤ zulässig
5. Optionale Eskalation bei FAIL: Rippen/Wände verstärken (Parameter) oder Material ASA-GF/PC.

## 7. Export, Fertigung, Tests

**Export:** STEP gesamt + genau eine Universal-Segmentdatei (`universal_segment_x4`)
als STEP, STL und 3MF; Dateinamen mit Parameter-Hash.
Auto-generierte Fertigungs-/Montagenotiz: Druckorientierung (liegend auf Deckfläche),
≥4 Perimeter, 100 % Infill (Kammern tragen die Gewichtsreduktion), kein
pauschales Tempern, Schraubenliste, exakte Kleb-/Dicht-/Lackprodukte und Dichtklebstoff-Bedarf (aus
Raupenlänge/-querschnitt berechnet), berechnete Wellenwahl (140 mm bei 35+28).

**DFM als Code-Invarianten:** Überhänge ≤ 45° aus der Senkrechten (stützenfrei;
die 47°-Chevronflächen zählen ab Horizontale = 43° Überhang und sind konform), Mindestwand 2,4 mm, Rippen 1,6 mm,
Nut-Feder-Toleranz parametrisch.

**Tests (headless in FreeCADCmd):**
1. Geometrie-Invarianten: wasserdicht/valide, Öffnung exakt 400×400, Höhe = `H_RAISE`, BBox-Bereich
2. Passung: Feder < Nut um exakt `TOL_JOINT`; boolesche Vereinigung der Segmente ≡ Rahmen − Fugenvolumen
3. DFM-Checks: Überhangwinkel-Scan, Wandstärken-Stichproben
4. FEM-Regression: Referenzparametersatz → erwartete max. Spannung/Verformung ±Toleranz
5. Toolchain-Smokes für Gmsh/CalculiX, Export und Referenzkatalog
6. Digitaler Belluna-Passungscheck: Kollision, Radialspiel, Auflage und Schraubpfade

**Freigabe-Workflow:** `pipeline test` → `pipeline engineering`
(einschließlich `pipeline connections`) → `pipeline fit`
→ reale Einbaukontrollen → `pipeline release`. Die nicht verfügbaren
Werkstoffversuche werden nicht als geschlossen behauptet; ihre Unsicherheit
bleibt über die Abminderungen und `PROTOTYPE_ONLY` sichtbar.

## 8. Offene reale Eingaben

Die Belluna-Plattenschnittstelle ist vermessen und in der Referenzrekonstruktion
dokumentiert. Am Fahrzeug bleiben offen:

1. Realmaß Dachausschnitt (Soll 400×400) + Eckenradius nach Mini-Heki-Demontage.
2. Abstand Ausschnitt-Hinterkante → hohe Dachkante und deren Höhe (**Verifikation der 28 mm**:
   geometrischer Haubenfreigang wird aus diesen Werten im Modell nachgerechnet)
3. Kontrollmessung der Dachstärke am Ausschnitt (Planstand 35 mm).
4. Zustand der Klebefläche und des XPS nach Demontage.
5. Abmessungen und Pressprozess des nachgerüsteten Holzrahmens.

Bis zur Messung bleiben die betreffenden Werte in `params.py` als dokumentierte
Defaults und erzwingen den Status `PROTOTYPE_ONLY`.

## 9. Entscheidungen (Log)

| Entscheidung | Wahl | Alternativen (verworfen) |
|---|---|---|
| Pipeline | A: vollparametrisch, headless FreeCAD + CalculiX | B: GUI+Spreadsheet (nicht reproduzierbar) · C: CadQuery-Stack (Werkzeugvorgabe FreeCAD) |
| Material | **Würth ASA GF15 Verkehrsschwarz, Art.-Nr. 4954641200 + Pflichtlackierung Mipa RAL 9003** | weißes Filament ist nicht verfügbar · PC/ABS erfordert neue UV-/CTE-/Klebe-/Lackqualifikation |
| Befestigung | oben Kleben + 8 seitliche Schrauben; unten 2×10-mm-Doppelraupe plus 8 unbewertete Seitenschrauben | ursprüngliche 8-mm-Einzelraupe (rechnerisch unzureichend) · 25-mm-Bond-only-Verbreiterung (größer/schwerer) · Klemmen (Kriechen der Klemmstelle) |
| Segmentierung | 1 rotationsidentisches L-Ecksegment ×4, Stoß in Seitenmitte | vier seitenspezifische Dateien (Logistik/Verwechslung) · Monolith (kein Bauraum) · 8 Teile (mehr Fugen) |
| Erhöhung | 28 mm (Forum-Vorbild), als Parameter | am realen Haubenfreigang zu verifizieren |
| Welle | 140 mm (aus 35+28 berechnet) | — Pipeline rechnet bei Parameteränderung neu |
| Dach-Befestigung | Zwei 10-mm-Sikaflex-522-Raupen mit 406/454-mm-Hüllmaß vollständig über dem vollflächig eingeklebten Holzrahmen; 16 schmale 2,5×20×3-mm-Abstandspads außerhalb der Klebeflächen, 0,6-mm-Applikationsführungen (drei 0,2-mm-Layer) und 3,6-mm-Raupenhöhe; äußere Raupe geschlossen, innerer Mittelkanal gezielt zur trockenen Seite belüftet; erst nach Primärhärtung eine zugängliche, nichttragende 7×7-mm-Schutzkehle außen; acht seitliche, abgedichtete ST4.2×25 als nicht angerechnete Reserve | 68 Ø8-mm-Rundnoppen mit 5-mm-Raupenhöhe und Punktlasten · ursprüngliche 8-mm-Fuge (unzureichend) · 25-mm-Bond-only-Verbreiterung je Seite (550-mm-Außenmaß und höheres Teilegewicht) · Schrauben durch nasse Dachfläche |

## 10. Risiken und Gegenmaßnahmen

| Risiko | Gegenmaßnahme |
|---|---|
| Kriechen unter Dauerklemmung bei Hitze | Dauerlast-Zulässigkeit 4,50 MPa; LF3-Hüllkurvenannahme: ein etwaiger Klemmpfad läuft über Dach+Adapter-Druckflächen (real keine harte Klemmkette, s. §3.6); FEM LF3 |
| Schichthaftung (Z) versagt | Drucklage: Lasten in XY; permanenter Knockdown 0,5; kein pauschales Tempern |
| Thermodehnung reißt Klebfuge | 16 Pads erzwingen 3 mm Dachabstand; in den flachen Führungen entstehen 3,6 mm Raupenhöhe. LF5 rechnet konservativ weiter mit 3 mm und erreicht 38 % des thermischen Scherbewegungsgrenzwerts. |
| Druckservice-Toleranzen an den Stößen | `TOL_JOINT` parametrisch, Probedruck eines Stoßpaars vor Vollbestellung (Montagenotiz) |
| 28 mm reichen nicht (Haube streift) | reale Fahrzeugmaße + geometrischer Freigang-Check vor Produktionsfreigabe |
| Schwarzer Rohling heizt sich solar auf / Lack löst sich | RAL-9003-Pflichtlackierung mit festgelegtem Mipa-System; Lack trägt keine Struktur; jährliche Kontrolle und sofortige Ausbesserung |
| Reale Grenzfläche schwächer als Datenblatt | `analysis/load_paths.py`: Sikaflex bis Faktor 60, Segmentstoß-Epoxid Faktor 38 und Sandwich auf 0,05 MPa abgemindert; Ergebnis bleibt `PASS_ASSUMPTION_BASED`, nicht zugelassen |
| Zyklische Ermüdung (Thermozyklen x Vibration) nicht im FEM-Kollektiv | Dokumentiertes Restrisiko (quasistatische LF + konservative Faktoren decken es nur indirekt); Gegenmaßnahme: jährliche Sichtprüfung der Nähte, Flutungstest nach 1. Saison [DA-Review] |
| Klemmkraft-Relaxation ASA bei 85 °C | Entschärft: real keine harte Klemmkette (§3.6) — Restrisiko nur seitliche Schrauben; Feder-/Sicherungselemente + Nachziehen bleiben empfohlen [DA-Review, aktualisiert] |
| Freigang-Gate läuft auf Defaults (`EDGE_DIST/EDGE_H`) | Report und Release bleiben `PROTOTYPE_ONLY`, bis reale Fahrzeugmaße vorliegen |

## 11. Erfolgskriterien

1. `python3 -m pipeline engineering` läuft fehlerfrei durch: Modell → DFM → FEM → Export → Report.
2. Alle Tests grün, inkl. Segmente-≡-Monolith und DFM-Checks.
3. Druckdateien: 1 Universal-Segment ×4, rotationsidentisch, stützenfrei,
   Boundingbox ≤ 300 mm.
4. Physisch: Segmente fügen sich passgenau, Lüfter mit 140er-Welle montierbar, Haube öffnet
   kollisionsfrei über der Dachkante, dicht nach Regenfahrt.
