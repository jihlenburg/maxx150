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
5. **Material:** ASA weiß (UV-stabil, Tg ≈ 100 °C, geringe solare Aufheizung). Eskalationsstufe
   bei FEM-Engpass: ASA-GF oder PC-Blend (Modell materialagnostisch).
6. **Befestigung:** Adapter ↔ Dach verklebt (Carloflex/Sika, Elastikfuge); Platte ↔ Adapter
   verklebt (Ringklebenut); zusätzlich seitliche Verschraubung Kragen → Adapter-Innenwand
   (Adapter übernimmt die Holzrahmen-Rolle der Anleitung). Keine Verschraubung von oben.
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
- **Innenleben:** Rippenstruktur (Rippen 1,6 mm, Raster parametrisch) statt Vollmaterial.
- **Unterseite:** Klebespalt-Noppen (2,5 mm) für definierte Elastikfugen-Dicke + umlaufende
  Kleberille für die Carloflex-Raupe.

**Segmentierung:** Standard **4 identische L-Ecksegmente** (Rotationssymmetrie → eine Druckdatei),
Stöße in den Seitenmitten (Spannungsmaxima liegen an den Ecken). Stoßverbindung: vertikale
Nut-Feder-Verzahnung (Toleranz `TOL_JOINT` = 0,25 mm, nach Probedruck justierbar) + 2 Schraubdome
je Stoß (M4 oder Blechschraube) + Klebefläche. Segmentanzahl parametrisch (2/4/8).

**Thermik konstruktiv:** ASA α ≈ 90 µm/(m·K) vs. GFK ≈ 25 → auf 500 mm Kante bei ΔT 105 K
(−20…+85 °C) ~3,4 mm Differenzdehnung. Aufnahme ausschließlich durch die elastische Klebschicht
(Bewegungsaufnahme MS-Polymer ≥ 20 % bei 2–3 mm Fuge) — deshalb sind die Klebespalt-Noppen und
das Verbot starrer Verklebung Pflicht, keine Option.

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
| LF1 | Fahrtwind | 200 km/h → q ≈ 1,9 kPa; Haube offen (zulässig lt. Anleitung): A ≈ 0,1 m², cd ≈ 1,2 → ~230 N horizontal, ×2 Sicherheit = **460 N** am Hebelarm der Haubenhöhe (Kippmoment auf Deckfläche) |
| LF2 | Schlechtweg | quasistatisch ±4 g vert. / ±2 g quer auf 6,5 kg → ±255 N / ±130 N |
| LF3 | Klemmung/Montage | Vorspannung Innenrahmen-Verschraubung (aus 0,7 Nm Anzugsmoment lt. Anleitung ≈ 400–600 N je Schraube, konservativ 600 N × 4) + Anzug der Seitenschrauben; Schraubenauszug/Flächenpressung Innenwand |
| LF4 | Schnee/Stand | 0,75 kN/m² auf Grundfläche (~200 N) |
| LF5 | Thermik | ΔT −20…+85 °C, CTE-Differenz ASA↔GFK; Nachweis Elastikfuge (analytisch) + Verformungscheck (FEM) |

**Materialabminderung ASA (Kern des Nachweises):** Basis 40 MPa / E ≈ 2000 MPa (23 °C).
Faktoren: Temperatur 85 °C ≈ 0,35 · Z-Schichthaftung ≈ 0,6 · Kriechen (Dauerlast) ≈ 0,4.
→ zulässig ≈ **5 MPa dauerhaft**, ≈ **10 MPa kurzzeitig** (Böe, Schlagloch). Drucklage so, dass
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
≥4 Perimeter, ~40 % Gyroid, Tempern-Empfehlung, Schraubenliste, Carloflex-Bedarf (aus
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
| Material | ASA weiß | PETG (Tg zu nah an 85 °C) · PA12 (Kriechen, UV) · PC (Kosten; bleibt Eskalationsstufe) |
| Befestigung | Kleben + seitliche Schrauben | nur Kleben (keine Redundanz) · Klemmen (Kriechen der Klemmstelle) |
| Segmentierung | 4 identische L-Ecksegmente, Stoß in Seitenmitte | Monolith (kein Bauraum) · 8 Teile (mehr Fugen; bleibt Parameter-Option) |
| Erhöhung | 28 mm (Forum-Vorbild), als Parameter | — wird per Messkampagne Punkt 7 verifiziert |
| Welle | 140 mm (aus 35+28 berechnet) | — Pipeline rechnet bei Parameteränderung neu |

## 10. Risiken und Gegenmaßnahmen

| Risiko | Gegenmaßnahme |
|---|---|
| Kriechen ASA unter Dauerklemmung bei Hitze | Dauerlast-Zulässigkeit 5 MPa; Klemmpfad läuft primär über Dach+Adapter-Druckflächen (Druck, nicht Zug); FEM LF3 |
| Schichthaftung (Z) versagt | Drucklage: Lasten in XY; Knockdown 0,6 im Nachweis; Tempern empfohlen |
| Thermodehnung reißt Klebfuge | 2–3 mm Elastikfuge erzwungen (Noppen), MS-Polymer ≥ 20 % Bewegungsaufnahme, LF5 |
| Druckservice-Toleranzen an den Stößen | `TOL_JOINT` parametrisch, Probedruck eines Stoßpaars vor Vollbestellung (Montagenotiz) |
| 28 mm reichen nicht (Haube streift) | Messkampagne Punkt 7 + geometrischer Freigang-Check im Modell vor Export |
| UV-Versprödung | ASA (UV-stabilisiert), weiß; optional Lack |

## 11. Erfolgskriterien

1. `run_all.py` läuft fehlerfrei durch: Modell → FEM (alle LF PASS) → Export → Report.
2. Alle Tests grün, inkl. Segmente-≡-Monolith und DFM-Checks.
3. Druckdateien: 4 identische Segmente, stützenfrei, Boundingbox ≤ 250 mm.
4. Physisch: Segmente fügen sich passgenau, Lüfter mit 140er-Welle montierbar, Haube öffnet
   kollisionsfrei über der Dachkante, dicht nach Regenfahrt.
