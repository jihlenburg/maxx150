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
4. **Fertigung:** Druckservice, druckerunabhängig; Segment-Boundingbox konservativ ≤ 250 mm
   Kantenlänge; stützenfrei druckbar.
5. **Material & Prozess (§3.5):** **Würth ASA GF15 (Art. 4954641201, Signalweiß RAL 9003,
   Datenblatt Stand 05.03.2026)** im **FDM/FFF**-Verfahren als Default (User-Entscheidung
   Task 21, 2026-07-13). Löst den bisherigen Bambu-ASA-CF-Default (Task 19/20) ab —
   Begründung: ECHTES glasfaserverstärktes Compound (15 % GF, statt Carbonfaser) und
   Beschaffungsargument. **ACHTUNG Datenlage** (Kern-Vorbehalt, DA-3-relevant): das
   Würth-Blatt deklariert EXPLIZIT Halbzeug-Werte (Spritzguss-Probekörper), NICHT
   gedruckte FDM-Probekörper — anders als Bambus TDS V1.0, das echte gedruckte XY+Z-Werte
   lieferte. Halbzeug-Kennwerte: Zug 91,2 MPa, Bruchdehnung 8 %, E(100 %) 3520 MPa,
   Biegemodul 3500 MPa (alle ASTM), Kerbschlag 88 J/m, Vicat 101 °C, HDT/B(0,45 MPa) 99 °C,
   Dichte 1,1 g/cm³, Schrumpf 0,3 %, Düse 250–270 °C, max. Durchsatz 12 mm³/s, geschlossener
   Bauraum + gehärtete Düse empfohlen (GF abrasiv). Druckwerte `E_BASE`/`SIGMA_BASE`
   sind deshalb dokumentierte ANNAHMEN mit eigener Vorbehalts-Kette (params.py-Kommentar,
   analog `CTE_ASA` seit Task 19) — NICHT die Halbzeug-Zugfestigkeit 91,2 MPa: `E_BASE`
   3000 MPa (Abschlag ggü. Halbzeug-E 3520/Biegemodul 3500, da gedruckte FDM-Teile wegen
   Schichthaftung/Porosität i. d. R. unter dem Spritzguss-Wert liegen), `SIGMA_BASE`
   45 MPa (geschätzt aus gedruckten GF-ASA-Analoga, z. B. Phaetus ASA-GF10 TDS: 40–46 MPa
   XY gedruckt — NICHT aus dem unrealistisch hohen Halbzeugwert). Diese DA-3-Bewertung ist
   damit gegenüber Bambu ASA-CF (Task 19) formal SCHWÄCHER belegt (Halbzeug- statt
   Druckwerte); die Materialwahl trägt das Argument über Faserart (GF statt CF, geringeres
   Kriechen/UV-Alterungsrisiko) und Beschaffung, nicht über bessere Kennwert-Evidenz.
   Signalweiß RAL 9003 ist zusätzlich ein konstruktives Argument: geringere
   Solaraufheizung als schwarzes CF-Filament, senkt die reale Bauteiltemperatur unter
   der 85-°C-Auslegungsgrenze. Hauptgrund für FDM/FFF unverändert: direkte
   Klebefähigkeit mit MS-Polymer/Epoxid ohne Primer — tragend für das klebebasierte
   Befestigungs- und Dichtkonzept. Pulververfahren (SLS/MJF-PA12) weiterhin verworfen:
   Verklebung nur mit Primer/Plasma zuverlässig, Wasseraufnahme, stärkeres Kriechen.
   Eskalationsstufe bei FEM-Engpass unverändert: ASA-GF (höherer Faseranteil) oder
   PC-Blend (§6). Die Kammer-Vents (Ø4) dienen dem Druckausgleich der geschlossenen
   Zellen (−20…+85 °C ≈ 35 % Innendruckhub), nicht der Entpulverung.
   **Presets (params.py-Kommentar, kein Code-Pfad):** Bambu ASA-CF (TDS V1.0, seit
   Task 21 NRND — vorheriger Default Task 19/20, TDS-Zahlen bleiben gültig/belegt),
   Fiberon ASA-CF08 (8 % CF, KEIN TDS im Haus), CR3D FibCR20 (20 %-CF-FDM-Filament,
   grobe Marktklassenwerte, unbelegt), Extrudr DuraPro ASA GF (GF-verstärkt, KEIN
   TDS im Haus) und Standard-ASA (Projekt-Ur-Default, Task 1–18, belegt) bleiben als
   Vergleichszeilen dokumentiert — vor einem Umstieg auf eine unbelegte Alternative
   erst Datenblatt beschaffen (DA-3-Bruch/Gate-Muting-Gefahr).
   **Offene Punkte:** (1) `E_BASE`/`SIGMA_BASE` sind Druckwert-ANNAHMEN aus der
   Halbzeug-Lücke (s. o.) — ein gedrucktes TDS (XY+Z) würde sie durch Messwerte
   ersetzen. (2) `CTE_ASA` = 60e-6 1/K bleibt unverändert eine konservative Obergrenze
   (das Würth-Blatt nennt ebenfalls keinen CTE-Wert) — Herstelleranfrage folgt
   (todo.md); ein belegter, niedrigerer Wert senkt die aktuelle Fugenauslastung
   (~21 %) weiter. (3) `DERATE_Z` = 0,5 ist GESCHÄTZT (keine Z-Probekörper), strenger
   als Bambus gemessene 0,8.
6. **Befestigung:** Adapter ↔ Dach verklebt (Carloflex/Sika, Elastikfuge); Platte ↔ Adapter
   verklebt (Ringklebenut); zusätzlich seitliche Verschraubung Kragen → Adapter-Innenwand
   (Adapter übernimmt die Holzrahmen-Rolle der Anleitung). Keine Verschraubung von oben.
   **Reale Einbausituation (User 2026-07-12): KEINE harte Klemmkette durchs Sandwich** —
   Lüfter geklebt + Kragen formschlüssig im Schacht, von unten nur die Zierblende.
   LF3 bleibt als bewusst konservative Hüllkurve (Montage-Grenzfälle); die mechanische
   Redundanz trägt allein die seitliche Verschraubung + Formschluss.
7. **Dichtheit:** definierte Elastikkleber-Schichtdicke 2–3 mm (Thermodehnung), Sika-Kehlnaht außen.

## 4. Bauteilgeometrie

**Grundform:** rechteckige Plinthe, Höhe `H_RAISE` = 28 mm, Innenöffnung 400×400 mm mit R5-Ecken.

**Querschnitt (umlaufend):**
- **Deckfläche:** plane Klebefläche unter der Ringklebenut-Zone der Platte. Breite je Seite
  einzeln parametrisierbar (`W_TOP_FRONT/REAR/LEFT/RIGHT`, Startwert 50 mm), da der
  Plattenflansch asymmetrisch ist. Innen liegender Bereich mit parametrischer **Freistellung**
  (Tiefe `REC_GUSSET`) für die Dreiecks-Gussets der Plattenunterseite.
- **Innenwand:** 10–12 mm massiv als Schraubgrund für die seitliche Verschraubung aus dem
  Einbaukragen (Kernlochbohrung vor Ort nach realer Schraubposition).
- **Außenwand:** geschlossen, unten gefast für die Sika-Kehlnaht zum Dach.
- **Innenleben:** geschlossene Rippenkammern (zwei konzentrische Kammerringe je Seite,
  Zellenraster parametrisch, Wände/Platten voll dicht gedruckt). Kammerböden als 45°-Chevron
  (stützenfrei in Druckorientierung), Ø4-Entpulverungsbohrungen je Zelle zur Innenseite
  (für MJF/SLS; hinter dem Lüfterkragen verdeckt). Stoß- und Schraubzonen bleiben
  massiv. Eckkammern (90°-Rotationsfortsetzung der Kammerringe um die vier Eckblöcke,
  Task 17) sind seit 2026-07-12 Default EIN (`CORNER_CHAMBERS = True`, Task 20;
  Verzugs-/Gewichtsnutzen, FEM-verifiziert — abschaltbar, die AUS-Variante bleibt
  volumen-anker-geprüft reproduzierbar). Damit ist die Festigkeit geometrie-definiert
  (druckprofil-unabhängig); die FEM rechnet auf der echten Kammergeometrie mit vollem
  E-Modul (INFILL_FACTOR = 1,0). [Entscheidung mit User 2026-07-12, ersetzt
  Slicer-Infill-Ansatz]
- **Unterseite:** Klebespalt-Noppen (2,5 mm) für definierte Elastikfugen-Dicke + umlaufende
  Kleberille für die Carloflex-Raupe.

**Segmentierung:** Standard **4 identische L-Ecksegmente** (Rotationssymmetrie → eine Druckdatei),
Stöße in den Seitenmitten (Spannungsmaxima liegen an den Ecken). Stoßverbindung: Halbüberlappung
(Toleranz `TOL_JOINT` = 0,25 mm, nach Probedruck justierbar) + 1 Durchsteckschraube M5 je Stoß
(M4 fiel beim Lochleibungs-Nachweis mit 480 N durch) + Klebefläche. Segmentanzahl parametrisch.

**Thermik konstruktiv:** Würth ASA GF15 α ≈ 60 µm/(m·K), konservative Obergrenze, s. §3.5 —
Datenblatt-Lücke, `CTE_ASA` unverändert seit Task 19 (Bambu ASA-CF hatte denselben Wert
angesetzt) — vs. GFK ≈ 25 → auf 500 mm Kante bei ΔT 105 K (−20…+85 °C) ~1,84 mm
Differenzdehnung (unverändert ggü. Task 19/20, da `CTE_ASA` nicht angetastet wurde).
Aufnahme ausschließlich durch die elastische Klebschicht
(Bewegungsaufnahme MS-Polymer ≥ 20 % bei 2–3 mm Fuge) — deshalb sind die Klebespalt-Noppen und
das Verbot starrer Verklebung Pflicht, keine Option.

**Dichtheitskonzept (Mehrteiligkeit):** Dichtheit kommt von durchgehenden Elastomer-Ebenen,
nicht vom Druckteil — die Segmentstöße werden von diesen Ebenen überbrückt. Barrierenkette:
(1) Sika-Kehlnaht außen, umlaufend geschlossen über alle Stöße; (2) Carloflex-Ring in der
unteren Kleberille, geschlossen über die Stöße; (3) Ringklebenut der Belluna-Platte auf der
Deckfläche, ebenfalls geschlossen; (4) Stöße selbst: Halbüberlappungs-Labyrinth + vollflächige
2K-Epoxid-Verklebung der Fügeflächen (M5 = Verpressung der Klebung, nicht Dichtung).
FDM-Mikroporosität: ≥4 Perimeter als dichte Haut; 2K-PU/Epoxid-Versiegelung der
Außenflächen ist PFLICHT (Porenschluss + UV; DA-Review 2026-07-12). Validierung praktisch (Flutungstest, dann Hochdruck aus
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
│   ├── segments.py      # Zerlegung in N Segmente, Verzahnung, Schraubdome
│   └── features.py      # Kleberille, Noppen, Rippen, Fasen, Schraubkanäle
├── fem/
│   ├── material.py      # ASA-Kennwerte + Abminderungskette
│   ├── loadcases.py     # LF1–LF5 (Kräfte, Randbedingungen) als Code
│   ├── run_fem.py       # Netgen-Mesh → CalculiX → Ergebnisextraktion
│   └── report.py        # Markdown-Report, PASS/FAIL je Kriterium
├── export/export.py     # STEP gesamt+Segmente, STL/3MF je Segment,
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

**Materialabminderung Würth ASA GF15 (Kern des Nachweises, Task 21):** Basis 45 MPa / E ≈ 3000 MPa
(beide Druckwert-ANNAHMEN aus der Halbzeug-Datenlücke, s. §3.5 — NICHT der Halbzeug-Zugwert
91,2 MPa/E 3520). Faktoren: Temperatur 85 °C vs. Vicat 101/HDT-B(0,45 MPa) 99 °C ≈ 0,5 ·
Z-Schichthaftung ≈ 0,5 (GESCHÄTZT — keine Z-Probekörper im Datenblatt, strenger als Bambus
gemessene 0,8) · Kriechen (Dauerlast, keine Kriechdaten) ≈ 0,4 (unverändert konservativ).
→ zulässig **4,50 MPa dauerhaft**, **11,25 MPa kurzzeitig** (Böe, Schlagloch; exakte Kettenwerte,
von Plan/Code so verwendet; vorher Task 19/20 Bambu ASA-CF: 5,44/13,60 MPa). Drucklage so, dass
Hauptspannungen in der XY-Ebene liegen (Z sieht überwiegend Druck).

**Bestehenskriterien (Pipeline-Gate, automatisch):**
1. σ_vMises ≤ zulässig je Lastfall (Sicherheiten enthalten)
2. Verformung der Deckfläche < 0,5 mm (Dichtheit der Klebefuge)
3. Klebfugen-Schub ≤ 0,1 N/mm² dauerhaft (über Reaktionskräfte)
4. Flächenpressung/Auszug an der Innenwand ≤ zulässig
5. Optionale Eskalation bei FAIL: Rippen/Wände verstärken (Parameter) oder Material ASA-GF/PC.

## 7. Export, Fertigung, Tests

**Export:** STEP (gesamt + je Segment), STL + 3MF je Segment; Dateinamen mit Parameter-Hash.
Auto-generierte Fertigungs-/Montagenotiz: Druckorientierung (liegend auf Deckfläche),
≥4 Perimeter, 100 % Infill (Kammern tragen die Gewichtsreduktion), Tempern-Empfehlung, Schraubenliste, Carloflex-Bedarf (aus
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
| Material | ASA weiß → Task 19/20: Bambu ASA-CF (gedruckte XY+Z-Daten) → seit Task 21: **Würth ASA GF15** (echtes GF, Signalweiß RAL 9003; Halbzeug-Datenlage, Druckwerte ANNAHME) | Bambu ASA-CF (seit Task 21 NRND) · PETG (Tg) · PA12 (Kriechen/UV) · Fiberon ASA-CF08/CR3D FibCR20/Extrudr DuraPro ASA GF (kein TDS im Haus) · PC |
| Befestigung | Kleben + seitliche Schrauben | nur Kleben (keine Redundanz) · Klemmen (Kriechen der Klemmstelle) |
| Segmentierung | 4 identische L-Ecksegmente, Stoß in Seitenmitte | Monolith (kein Bauraum) · 8 Teile (mehr Fugen; bleibt Parameter-Option) |
| Erhöhung | 28 mm (Forum-Vorbild), als Parameter | — wird per Messkampagne Punkt 7 verifiziert |
| Welle | 140 mm (aus 35+28 berechnet) | — Pipeline rechnet bei Parameteränderung neu |

## 10. Risiken und Gegenmaßnahmen

| Risiko | Gegenmaßnahme |
|---|---|
| Kriechen unter Dauerklemmung bei Hitze | Dauerlast-Zulässigkeit 4,50 MPa (Würth ASA GF15, Task 21); Klemmpfad läuft primär über Dach+Adapter-Druckflächen (Druck, nicht Zug); FEM LF3 |
| Schichthaftung (Z) versagt | Drucklage: Lasten in XY; Knockdown 0,5 (GESCHÄTZT — kein Z-Datenpunkt im Würth-Blatt, strenger als Bambus gemessene 0,8); Tempern Pflicht lt. Montagenotiz |
| Thermodehnung reißt Klebfuge | 2–3 mm Elastikfuge erzwungen (Noppen), MS-Polymer ≥ 20 % Bewegungsaufnahme, LF5 |
| Druckservice-Toleranzen an den Stößen | `TOL_JOINT` parametrisch, Probedruck eines Stoßpaars vor Vollbestellung (Montagenotiz) |
| 28 mm reichen nicht (Haube streift) | Messkampagne Punkt 7 + geometrischer Freigang-Check im Modell vor Export |
| UV-Versprödung | ASA-Basis (Werkstoffklasse materialklassisch UV-beständig; Würth-Blatt macht dazu keine eigene Aussage); Versiegelung Pflicht (s. §3) |
| Zyklische Ermüdung (Thermozyklen x Vibration) nicht im FEM-Kollektiv | Dokumentiertes Restrisiko (quasistatische LF + konservative Faktoren decken es nur indirekt); Gegenmaßnahme: jährliche Sichtprüfung der Nähte, Flutungstest nach 1. Saison [DA-Review] |
| Klemmkraft-Relaxation ASA bei 85 °C | Entschärft: real keine harte Klemmkette (§3.6) — Restrisiko nur seitliche Schrauben; Feder-/Sicherungselemente + Nachziehen bleiben empfohlen [DA-Review, aktualisiert] |
| Freigang-Gate läuft auf Schätzwerten (EDGE_DIST/EDGE_H) und meldet inf | Report kennzeichnet Freigang als OFFEN bis Messkampagne 7; Druckfreigabe erst nach Messung + PLA-Passform-Probedruck [DA-Review] |

## 11. Erfolgskriterien

1. `run_all.py` läuft fehlerfrei durch: Modell → FEM (alle LF PASS) → Export → Report.
2. Alle Tests grün, inkl. Segmente-≡-Monolith und DFM-Checks.
3. Druckdateien: 4 identische Segmente, stützenfrei, Boundingbox ≤ 250 mm.
4. Physisch: Segmente fügen sich passgenau, Lüfter mit 140er-Welle montierbar, Haube öffnet
   kollisionsfrei über der Dachkante, dicht nach Regenfahrt.
