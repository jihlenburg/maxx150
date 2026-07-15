# Design: 3D-gedruckter Adapterrahmen — Belluna Super Fan im Mini-Heki-Ausschnitt (Challenger X150 / Chausson X550)

Stand: 2026-07-12 · Status: Entwurf zur User-Review

## 1. Ziel und Kontext

Der Belluna Super Fan Dachventilator soll den vorhandenen Mini-Heki im 400×400-mm-Dachausschnitt
eines Challenger X150 (baugleich Chausson X550) ersetzen. Das Dach dieser Fahrzeuge hat eine
umlaufende hohe Kante am Heck; die Lüfterhaube (Grundriss 593 mm lang, Überstand nach hinten)
würde beim Öffnen/Schließen mit dieser Kante kollidieren. Ein Adapterrahmen („Plinthe") hebt die
Lüfterbasis um **28 mm** an. Vorbild ist ein im X150-Forum dokumentierter, handgefertigter
Holzsockel; hier entsteht stattdessen ein **algorithmisch erzeugtes, 3D-gedrucktes, per FEM
verifiziertes** Bauteil.

Erzeugung und Verifikation laufen vollständig skriptiert (Python) über headless FreeCAD
(`/Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd`) mit Netgen-Vernetzung und
CalculiX-Solver aus dem FreeCAD-Bundle. Kein GUI-Schritt ist Teil des Workflows.

## 2. Feste Eingangsdaten

### Aus der Belluna-Einbauanleitung (liegt vor, 22 S.)
| Größe | Wert |
|---|---|
| Lochgröße (Dachausschnitt) | 400 × 400 mm, Eckenradius R5 |
| Zulässige Einbauwandstärke | 27–80 mm |
| Vierkantwellen (mitgeliefert) | 120 mm ↔ 27–47 mm · 140 mm ↔ 48–67 mm · 160 mm ↔ 68–80 mm |
| Karosseriebefestigungsplatte | 593 × 420/450 mm, asymmetrischer Flansch (Überstand heckseitig) |
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

### Befunde aus Fotos der Karosseriebefestigungsplatte (Gerät liegt vor)
- Flanschoberseite plan, Schraublöcher verstöpselt; schwarze Dichtung umlaufend am Kragenfuß (Dichtebene Platte↔Lüftereinheit).
- Unterseite: Klebe-/Kontaktzone ist der **äußere Flanschbereich mit konzentrischen Ringrippen**
  (Ringklebenut); innen um den Einbaukragen **Dreiecks-Gussets**, die ggf. unter die
  Kontaktebene ragen → Adapter-Deckfläche braucht dort eine Freistellung (Maß zu messen).
- Einbaukragen mit Federstahl-Klipsen (Schraubaufnahmen der Lüfterbefestigung).

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
   Kantenlänge (`SEG_MAX_BBOX`; Ist ~277 mm — die ursprünglich konservativen 250 mm
   wurden mit der Bauraum-Klärung angehoben, Bambu H2D 350 mm verfügbar; Drift-Fix
   2026-07-14); stützenfrei druckbar.
5. **Material & Prozess (§3.5):** **Würth ASA GF15 Verkehrsschwarz ähnlich
   RAL 9017, 1,75 mm, Art.-Nr. 4954641200** aus lokaler FDM-Fertigung
   (Plan-of-Record 2026-07-15). 15 % Glasfaser; gehärtete Düse und geschlossener,
   temperierter Bauraum sind Projektpflicht. Drucklage ist Deckfläche nach unten;
   47°-Kammerdächer, 47°-Entwässerungsfase und Ø4-Querkanäle sind supportfrei.
   Brim ≥10 mm und langsames Abkühlen bleiben Pflicht. Würth nennt Dichte
   1,1 g/cm³ und HDT/B 99 °C bei 0,45 MPa, aber keinen HDT-Wert bei 1,82 MPa.
   Die publizierten mechanischen Werte stammen ausdrücklich aus Halbzeug, nicht
   aus FDM-Probekörpern. Deshalb bleiben E=3000 MPa, Zug=45 MPa, CTE=60e-6 1/K
   und Z-Faktor 0,5 konservative Projektannahmen bis zu XY-/Z-Coupons aus dem
   realen Druckprozess. Pauschales Tempern ist nicht freigegeben.
   Der schwarze Rohling wird vor dem Dacheinbau zwingend weiß beschichtet:
   Mipa 1K-Plastic-Grundierfiller-Spray (Art.-Nr. 213390000) plus Mipa PUR HS
   2K-PUR-Acryl-Fahrzeuglack RAL 9003 Signalweiß glänzend und Mipa 2K-MS-Härter
   MS 25 (2:1 Volumen). Weiß ist Teil der Thermikauslegung; Primerhaftung auf
   ASA-GF wird per Originaldruck-Coupon qualifiziert.
6. **Befestigung:** Adapter ↔ Dach und Platte ↔ Adapter mit **Carloflex 410 UV
   weiß** verklebt/abgedichtet (Elastikfuge bzw. Ringklebenut). Zusätzlich werden
   die 16 beiliegenden Belluna-ST4.2×25
   auf zwei entkoppelte Interfaces verteilt: 8 äußere Belluna-Seitenlöcher
   Platte→lokale Universalrippen (jede Seite hält ±140 und ±165 vor, ohne
   offene Vorratslöcher) und 8 umlaufend gleiche ±140-Löcher
   Unterkragen→nachgerüsteter Holzrahmen im XPS. Der Holzrahmen wird mit
   **KLEIBERIT 501.0 1K-PUR-Leim** (D4) vollflächig eingesetzt.
   Die zwei Belluna-Mittellöcher an den Segmentstößen bleiben frei. Keine Verschraubung
   von oben durch eine Dichtfläche.
   **Reale Einbausituation (User 2026-07-12): KEINE harte Klemmkette durchs Sandwich** —
   Lüfter geklebt + Kragen formschlüssig im Schacht, von unten nur die Zierblende.
   LF3 bleibt als bewusst konservative Hüllkurve (Montage-Grenzfälle); die mechanische
   Redundanz trägt allein die seitliche Verschraubung + Formschluss.
7. **Dichtheit:** definierte Carloflex-Schichtdicke 3 mm (Thermodehnung),
   Carloflex-Kehlnaht außen und abgedichtete Schraubdurchtritte.

## 4. Bauteilgeometrie

**Grundform:** rechteckige Plinthe, Höhe `H_RAISE` = 28 mm, Innenöffnung 400×400 mm mit R5-Ecken.

**Querschnitt (umlaufend):**
- **Deckfläche:** plane Klebefläche unter der Ringklebenut-Zone der Platte; außerhalb
  des 450-mm-Flansches geht sie in eine 47°-Entwässerungsfase über. Breite je Seite
  einzeln parametrisierbar (`W_TOP_FRONT/REAR/LEFT/RIGHT`, Startwert 50 mm), da der
  Plattenflansch asymmetrisch ist. Innen liegender Bereich mit parametrischer **Freistellung**
  (Tiefe `REC_GUSSET`) für die Dreiecks-Gussets der Plattenunterseite.
- **Innenwand:** 8 mm umlaufend; jede Seite besitzt an ±140 und ±165 mm
  lokale 10-mm-Vollmaterialrippen über den ganzen 25-mm-Schraubpfad. Acht
  der sechzehn möglichen Pfade werden durch die realen Belluna-Löcher genutzt.
  Die Rippen sind oben an die Deckplatte angebunden und laufen unten mit 45°
  aus; dadurch bleiben die 43-mm-Kammerzellen weitgehend erhalten und der
  Druck bleibt supportfrei. Kollidierende Ventkanäle werden innerhalb ihrer
  Zelle aus der Rippe verschoben.
- **Außenwand:** geschlossen, unten gefast für die Carloflex-Kehlnaht zum Dach.
- **Innenleben:** geschlossene Rippenkammern (zwei konzentrische Kammerringe je Seite,
  Zellenraster parametrisch, Wände/Platten voll dicht gedruckt). Kammerböden als 47°-Chevron
  (stützenfrei in Druckorientierung), horizontale Ø4-Druckausgleichsbohrungen je Zelle
  zur Innenseite. Stoß- und Schraubzonen bleiben
  massiv. Eckkammern (90°-Rotationsfortsetzung der Kammerringe um die vier Eckblöcke,
  Task 17) sind seit 2026-07-12 Default EIN (`CORNER_CHAMBERS = True`, Task 20;
  Verzugs-/Gewichtsnutzen, FEM-verifiziert — abschaltbar, die AUS-Variante bleibt
  volumen-anker-geprüft reproduzierbar). Damit ist die Festigkeit geometrie-definiert
  (druckprofil-unabhängig); die FEM rechnet auf der echten Kammergeometrie mit vollem
  E-Modul (INFILL_FACTOR = 1,0). [Entscheidung mit User 2026-07-12, ersetzt
  Slicer-Infill-Ansatz]
- **Unterseite:** Klebespalt-Noppen (3 mm) für definierte Elastikfugen-Dicke + umlaufende
  Kleberille für die Carloflex-Raupe.

**Segmentierung:** Standard **ein rotationsidentisches L-Ecksegment, 4× drucken**,
Stöße in den Seitenmitten (Spannungsmaxima liegen an den Ecken). Stoßverbindung: Halbüberlappung
(Toleranz `TOL_JOINT` = 0,25 mm, nach Probedruck justierbar) + 1 Durchsteckschraube M5 je Stoß
(M4 fiel beim Lochleibungs-Nachweis mit 480 N durch) + Klebefläche. Die vier
Kopien werden nur um Z gedreht, nie gespiegelt; ein starker Geometrietest
prüft die Rotationsidentität über die symmetrische Differenz.

**Thermik konstruktiv:** ASA-GF α = 60 µm/(m·K), konservative
Datenblatt-Lückenannahme, vs. GFK ≈25. Der mit RK-1300 und M5 vollständig
gefügte Rahmen wird thermisch als **500-mm-Baugruppe**, nicht als entkoppeltes
Drucksegment gerechnet. Von 20 °C Klebetemperatur bis 85 °C entstehen 1,14 mm
Differenzdehnung über die Kante; symmetrisch je Ende ergibt dies rund 38 %
Auslastung der 3-mm-Elastikfuge.
Aufnahme ausschließlich durch die elastische Klebschicht
(Carloflex 410 UV, elastisches 1K-PU) — deshalb sind die Klebespalt-Noppen und
das Verbot starrer Verklebung Pflicht, keine Option.

**Dichtheitskonzept (Mehrteiligkeit):** Dichtheit kommt von durchgehenden Elastomer-Ebenen,
nicht vom Druckteil — die Segmentstöße werden von diesen Ebenen überbrückt. Barrierenkette:
(1) Carloflex-Kehlnaht außen, umlaufend geschlossen über alle Stöße; (2) Carloflex-Ring in der
unteren Kleberille, geschlossen über die Stöße; (3) Ringklebenut der Belluna-Platte auf der
Deckfläche, ebenfalls geschlossen; (4) Stöße selbst: Halbüberlappungs-Labyrinth + vollflächige
WEICON-RK-1300-Verklebung der Fügeflächen (M5 = Verpressung/Redundanz, nicht Dichtung).
FDM-Mikroporosität: ≥4 Perimeter als dichte Haut; der festgelegte Mipa-Primer +
RAL-9003-2K-PUR-Decklack ist PFLICHT (Solarreflexion, Porenschluss, Wetterschutz).
Validierung praktisch (Flutungstest, dann Hochdruck aus
ISO-20653-9K-Abstand am verbauten Sockel); eine normative IP6K9K-Zertifizierung wäre
Prüfstandssache. Systemgrenze: der Belluna selbst ist nur IPX4 — Ziel ist die dichte
Dachdurchdringung, nicht ein dichter Lüfter.

## 5. Software-Architektur

```
maxx150/
├── params.py            # EINE Quelle der Wahrheit: Maße, Material, Lasten,
│                        #   Segmentierung, Toleranzen — kommentiert
├── model/
│   ├── frame.py         # Gesamtrahmen als B-Rep (FreeCAD Part-API)
│   ├── segments.py      # 4 Rotationskopien des Universalteils, Verzahnung
│   └── features.py      # Kleberille, Noppen, Rippen, Fasen, Schraubkanäle
├── fem/
│   ├── material.py      # ASA-Kennwerte + Abminderungskette
│   ├── loadcases.py     # LF1–LF5 (Kräfte, Randbedingungen) als Code
│   ├── run_fem.py       # Netgen-Mesh → CalculiX → Ergebnisextraktion
│   └── report.py        # Markdown-Report, PASS/FAIL je Kriterium
├── export/export.py     # STEP gesamt + eine Universaldatei x4 (STEP/STL/3MF),
│                        #   Fertigungs-/Montagenotiz (auto-generiert)
├── out/                 # Artefakte (gitignored)
├── run_all.py           # Pipeline: Modell → FEM → Export → Report
├── tests/               # Invarianten & Regression (headless)
└── docs/superpowers/specs/
```

**Datenfluss:** `params.py` → `frame.py` (ein wasserdichtes Solid) → (a) `segments.py` →
`export.py`; (b) `fem/`. Der Report verknüpft Parameterstand ↔ FEM-Ergebnis ↔ Datei-Hashes:
kein Druckfile ohne zugehörige Verifikation.

**FEM-Modellstrategie:** Globalnachweis am **ungeteilten** Rahmen (obere Steifigkeitsschranke),
Detailnachweis am Stoß-Submodell mit den Schnittkräften aus dem Globalmodell (untere Schranke).
Kein Vollkontaktmodell aller vier Segmente in CalculiX.

**Fehlerbehandlung:** Jeder Schritt validiert sein Ergebnis (Solid `isValid()` + geschlossene
Shell, Mindestwandstärke, Mesh-Qualität, CalculiX-Konvergenz) und bricht mit klarer Meldung ab,
statt fehlerhafte Artefakte zu exportieren.

## 6. FEM-Verifikation

**Lastfälle:**
| # | Lastfall | Ansatz |
|---|---|---|
| LF1 | Fahrtwind | 200 km/h → q ≈ 1,85 kPa; Haube offen (zulässig lt. Anleitung), Worst Case MaxxFan Deluxe: A = 0,408 m × (0,236 + 0,028) m ≈ 0,108 m² (Maßblatt), cd ≈ 1,2 → ~240 N horizontal, ×2 Sicherheit = **480 N** am Hebelarm der Haubenhöhe (Kippmoment auf Deckfläche) |
| LF2 | Schlechtweg | quasistatisch ±4 g vert. / ±2 g quer auf 6,5 kg → ±255 N / ±130 N |
| LF3 | Klemmung/Montage | Vorspannung Innenrahmen-Verschraubung (aus 0,7 Nm Anzugsmoment lt. Anleitung ≈ 400–600 N je Schraube, konservativ 600 N × 4) + Anzug der Seitenschrauben; Schraubenauszug/Flächenpressung Innenwand. **Konservative Hüllkurve: real keine harte Klemmung (s. §3.6)** |
| LF4 | Schnee/Stand | 0,75 kN/m² auf Grundfläche (~200 N) |
| LF5 | Thermik | ΔT −20…+85 °C, CTE-Differenz ASA↔GFK; Nachweis Elastikfuge (analytisch) + Verformungscheck (FEM) |

**Materialabminderung Würth ASA GF15:** Projektbasis 45 MPa / E 3000 MPa;
keine Behauptung gedruckter Herstellerwerte, da Würth nur Halbzeugdaten nennt.
Faktoren: Temperatur 0,5 · Z-Schichthaftung 0,5 (geschätzt, bis Coupon-Test) ·
Kriechen 0,4. → zulässig **4,50 MPa dauerhaft**, **11,25 MPa kurzzeitig**.
Drucklage so, dass
Hauptspannungen in der XY-Ebene liegen (Z sieht überwiegend Druck).

**Bestehenskriterien (Pipeline-Gate, automatisch):**
1. σ_vMises ≤ zulässig je Lastfall (Sicherheiten enthalten)
2. Verformung der Deckfläche < 0,5 mm (Dichtheit der Klebefuge)
3. Klebfugen-Schub ≤ 0,1 N/mm² dauerhaft (über Reaktionskräfte)
4. Flächenpressung/Auszug an der Innenwand ≤ zulässig
5. Optionale Eskalation bei FAIL: Rippen/Wände verstärken (Parameter) oder Material ASA-GF/PC.

## 7. Export, Fertigung, Tests

**Export:** STEP gesamt + genau eine Universal-Segmentdatei (`universal_segment_x4`)
als STEP, STL und 3MF; Dateinamen mit Parameter-Hash.
Auto-generierte Fertigungs-/Montagenotiz: Druckorientierung (liegend auf Deckfläche),
≥4 Perimeter, 100 % Infill (Kammern tragen die Gewichtsreduktion), kein
pauschales Tempern, Schraubenliste, exakte Kleb-/Dicht-/Lackprodukte und Carloflex-Bedarf (aus
Raupenlänge/-querschnitt berechnet), berechnete Wellenwahl (140 mm bei 35+28).

**DFM als Code-Invarianten:** Überhänge ≤ 45° (stützenfrei), Mindestwand 2,4 mm, Rippen 1,6 mm,
Nut-Feder-Toleranz parametrisch.

**Tests (headless in FreeCADCmd):**
1. Geometrie-Invarianten: wasserdicht/valide, Öffnung exakt 400×400, Höhe = `H_RAISE`, BBox-Bereich
2. Passung: Feder < Nut um exakt `TOL_JOINT`; boolesche Vereinigung der Segmente ≡ Rahmen − Fugenvolumen
3. DFM-Checks: Überhangwinkel-Scan, Wandstärken-Stichproben
4. FEM-Regression: Referenzparametersatz → erwartete max. Spannung/Verformung ±Toleranz
5. Smoke-Test: `run_all.py` leer → Report fehlerfrei

**Freigabe-Workflow:** Pipeline-Lauf → FEM-Report PASS → Sichtkontrolle in FreeCAD-GUI →
erst dann gelten Druckdateien als freigegeben.

## 8. Messkampagne (offene Parameter, vom User mit Messschieber am Gerät/Fahrzeug)

An der Karosseriebefestigungsplatte:
1. Flansch-Außenmaße und Flanschbreiten aller vier Seiten (Asymmetrie!)
2. Lage und Breite der Ringklebenut-Rippen (Abstand von Flansch-Außenkante), Rippenhöhe
3. Kragen-Außenmaß, Kragenhöhe, Kragenwandstärke
4. Überstand der Dreiecks-Gussets unter die Flansch-Kontaktebene (→ `REC_GUSSET`)
5. Positionen der Klipse/Schraublöcher am Kragen (seitliche Verschraubung)

Am Fahrzeug:
6. Realmaß Dachausschnitt (Soll 400×400) + Eckenradius nach Mini-Heki-Demontage
7. Abstand Ausschnitt-Hinterkante → hohe Dachkante und deren Höhe (**Verifikation der 28 mm**:
   geometrischer Haubenfreigang wird aus diesen Werten im Modell nachgerechnet)
8. Reale Dachstärke am Ausschnitt (Soll 35 mm)
9. Zustand der Klebefläche nach Demontage (Restbett, Unebenheit)

Bis zur Messung arbeitet die Pipeline mit dokumentierten Schätz-Defaults in `params.py`;
jede Messung ersetzt einen Default.

## 9. Entscheidungen (Log)

| Entscheidung | Wahl | Alternativen (verworfen) |
|---|---|---|
| Pipeline | A: vollparametrisch, headless FreeCAD + CalculiX | B: GUI+Spreadsheet (nicht reproduzierbar) · C: CadQuery-Stack (Werkzeugvorgabe FreeCAD) |
| Material | **Würth ASA GF15 Verkehrsschwarz, Art.-Nr. 4954641200 + Pflichtlackierung Mipa RAL 9003** | weißes Filament ist nicht verfügbar · PC/ABS erfordert neue UV-/CTE-/Klebe-/Lackqualifikation |
| Befestigung | Kleben + seitliche Schrauben | nur Kleben (keine Redundanz) · Klemmen (Kriechen der Klemmstelle) |
| Segmentierung | 1 rotationsidentisches L-Ecksegment ×4, Stoß in Seitenmitte | vier seitenspezifische Dateien (Logistik/Verwechslung) · Monolith (kein Bauraum) · 8 Teile (mehr Fugen) |
| Erhöhung | 28 mm (Forum-Vorbild), als Parameter | — wird per Messkampagne Punkt 7 verifiziert |
| Welle | 140 mm (aus 35+28 berechnet) | — Pipeline rechnet bei Parameteränderung neu |
| Dach-Befestigung | Belluna-konform seitlich: 8× ST4.2×25 Platte→Universalrippen ±140/±165 + 8× ST4.2×25 Adapter-Unterkragen im eigenen ±140-Raster→nachgerüsteter Holzrahmen; genau die 16 beiliegenden Schrauben, plus Kleber | Kopplung beider Lochraster (zwei Segmenttypen) · von oben durch Dichtfläche (Belluna rät ab) · 12 Schrauben |

## 10. Risiken und Gegenmaßnahmen

| Risiko | Gegenmaßnahme |
|---|---|
| Kriechen unter Dauerklemmung bei Hitze | Dauerlast-Zulässigkeit 4,50 MPa; Klemmpfad läuft primär über Dach+Adapter-Druckflächen; FEM LF3 |
| Schichthaftung (Z) versagt | Drucklage: Lasten in XY; Knockdown 0,5 bis Coupon-Test; kein pauschales Tempern |
| Thermodehnung reißt Klebfuge | 3-mm-Carloflex-Elastikfuge erzwungen (Noppen), LF5 |
| Druckservice-Toleranzen an den Stößen | `TOL_JOINT` parametrisch, Probedruck eines Stoßpaars vor Vollbestellung (Montagenotiz) |
| 28 mm reichen nicht (Haube streift) | Messkampagne Punkt 7 + geometrischer Freigang-Check im Modell vor Export |
| Schwarzer Rohling heizt sich solar auf / Lack löst sich | RAL-9003-Pflichtlackierung mit festgelegtem Mipa-System; Gitterschnitt-/Abreißcoupon auf Originaldruck; jährliche Lackkontrolle |
| Klebstoff haftet nicht auf realem Compound/Dach | RK-1300- und Carloflex-Coupons auf rohem ASA-GF, Mipa-Lack und realem X150-GFK vor Serienmontage |
| Zyklische Ermüdung (Thermozyklen x Vibration) nicht im FEM-Kollektiv | Dokumentiertes Restrisiko (quasistatische LF + konservative Faktoren decken es nur indirekt); Gegenmaßnahme: jährliche Sichtprüfung der Nähte, Flutungstest nach 1. Saison [DA-Review] |
| Klemmkraft-Relaxation ASA bei 85 °C | Entschärft: real keine harte Klemmkette (§3.6) — Restrisiko nur seitliche Schrauben; Feder-/Sicherungselemente + Nachziehen bleiben empfohlen [DA-Review, aktualisiert] |
| Freigang-Gate läuft auf Schätzwerten (EDGE_DIST/EDGE_H) und meldet inf | Report kennzeichnet Freigang als OFFEN bis Messkampagne 7; Druckfreigabe erst nach Messung + PLA-Passform-Probedruck [DA-Review] |

## 11. Erfolgskriterien

1. `run_all.py` läuft fehlerfrei durch: Modell → FEM (alle LF PASS) → Export → Report.
2. Alle Tests grün, inkl. Segmente-≡-Monolith und DFM-Checks.
3. Druckdateien: 1 Universal-Segment ×4, rotationsidentisch, stützenfrei,
   Boundingbox ≤ 300 mm.
4. Physisch: Segmente fügen sich passgenau, Lüfter mit 140er-Welle montierbar, Haube öffnet
   kollisionsfrei über der Dachkante, dicht nach Regenfahrt.
