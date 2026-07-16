# Generator der illustrierten Montageanleitung

Reproduzierbarer Generator für eine gedruckte, bebilderte **Montageanleitung**
des Belluna-Adapterrahmens. Drei Stufen, wie im übrigen Repo strikt getrennt
(FreeCAD baut Geometrie, Blender rendert, python3/Chrome setzt das PDF):

```
params.py ──► build_stls.py (FreeCAD) ──► build/documentation/<hash>/stl + manifest
                                                   │
                            render_steps.py (Blender) ──► img/*.png
                                                   │
                              build_pdf.py (Chrome) ──► montageanleitung_<hash>.pdf
```

## Aufruf

Komplette Pipeline über den Orchestrator:

```sh
python3 -m pipeline manual
```

Das ist die Regel. Für Iterationen einzelne Stufen:

```sh
bin/fc montage/build_stls.py

blender -b -P montage/render_steps.py -- build/documentation/<hash>/stl build/documentation/<hash>/img
# jedes Bild zusätzlich: ~/Downloads/Belluna-Render-Zwischenstand/
ONLY_IMG=04,09 blender -b -P montage/render_steps.py -- build/documentation/<hash>/stl build/documentation/<hash>/img

python3 montage/build_pdf.py --manifest build/documentation/<hash>/manifest.json
python3 montage/build_pdf.py --manifest build/documentation/<hash>/manifest.json --no-pdf
```

Alle Stufen sind **idempotent** — erneuter Aufruf überschreibt sauber.

Ein vollständiger Lauf kann mehrere Minuten dauern. Für automatisierte Läufe
sollte die CLI mit dauerhaftem Log betrieben werden; ein abgebrochener Blender-
Prozess erzeugt bewusst kein scheinbar vollständiges PDF.

## Dateien

| Datei | Stufe | Zweck |
|-------|-------|-------|
| `build_stls.py` | FreeCAD (`bin/fc`) | Baut Segmente, vermessene Belluna-Rekonstruktion und Dach-Sandwich; schreibt `build/documentation/<hash>/stl/` + Manifest. |
| `render_steps.py` | Blender | Rendert die 14 Schrittbilder nach `build/documentation/<hash>/img/`. Liest nur das Manifest. |
| `build_pdf.py` | python3 | HTML aus `STEPS`-Datenstruktur + Chrome-Headless-PDF. Liest **nur** das Manifest. |
| `docs/assembly-manual.md` | — | Dieses Dokument. |

## Single Source of Truth: das Manifest

`build/documentation/<hash>/manifest.json` ist die einzige Schnittstelle zwischen den Stufen.
`build_stls.py` zieht **alle** Werte zur Laufzeit aus `params.py` bzw. den
`export`-Helpern (`_m5_bolt_length`, `PRM.select_shaft`,
`PRM.groove_centerline_len`, `PRM.bot_kragen_hole_count` …) und legt sie ab:

- `params_hash`, `geom_rev`, `erzeugt` (Datum);
- `geometrie` — abgeleitete Maße für die Blender-Polygon-Filter (Deckhöhe
  `top_z`, Lap-Ebene, Kleberführungen, Padabmessungen, Maskierzone, Holzrahmen);
- `marker` — Markerachsen als Endpunktpaare: `m5` (4×), `dach_screws` (8×)
  und `plate_screws` (16 mögliche Positionen), jeweils exakt aus den
  `params`-Positionen und dem
  gleichen 90°-Rotationsschema wie `model/segments.py`/`model/frame.py`;
- `explosion` — Explosions-Offsets;
- `text` — Textwerte für die Anleitung (M5-Länge, Klebstoff-ml, Wellenlänge,
  Schraubenzahlen/-durchmesser, Materialname, HDT/T_MAX …).

**Keine hartkodierten Geometriemaße** in Bild-/Textlogik. Produktbezogene
Prozesswerte (beispielsweise RK-Ablüftzeit, Lackschichtdicke und RAL 9003)
stehen bewusst als Fixtext in `build_pdf.py::build_model`, weil sie aus den
jeweiligen Produktdatenblättern und nicht aus `params.py` stammen.

## Festgelegtes Materialsystem

Die folgende Tabelle ist interne Fertigungs- und Entwicklungsdokumentation.
Die erzeugte Montageanleitung beginnt dagegen bewusst mit vier fertig
gedruckt gelieferten Segmenten: Druckmaterial, Spulenlogistik, Charge und
Druckparameter werden dort nicht genannt und dürfen nicht wieder in die
Materialliste oder die Montageschritte aufgenommen werden.

| Funktion | Exaktes Produkt | Warum dieses Produkt |
|----------|-----------------|----------------------|
| Druckteil | Würth ASA GF15, Verkehrsschwarz ähnlich RAL 9017, 1,75 mm, Art.-Nr. 4954641200 | 15 % GF, UV-/Witterungseignung, hohe Steifigkeit und geringerer Verzug; mechanische Werte sind jedoch nur Halbzeugwerte, daher bleiben permanente FDM-Abminderungen und `PROTOTYPE_ONLY`. |
| Segmentstöße | WEICON RK-1300, 60-g-Set inkl. Aktivator, Art.-Nr. 10000118 | MMA-Strukturklebstoff für Hartkunststoffe/Fahrzeugbau; höchste Zugscherfestigkeit bei 0,15–0,25 mm und bis 130 °C spezifiziert. Für ASA-GF wird rechnerisch nur 0,50 statt 6 MPa auf ABS angesetzt. |
| Dach- und Belluna-Dichtung | Sikaflex-522 weiß, 2× 300 ml (Standard); Carloflex 410 UV weiß als Belluna-konforme Alternative | Beide TDS nennen mindestens 1,8 MPa Zugfestigkeit und hohe Dehnung; die Lastpfadrechnung setzt für beide nur 0,030 MPa normal und 0,050 MPa Schub an. Zwei 10-mm-Raupen tragen den unteren Primärnachweis allein; die äußere bleibt geschlossen, die innere belüftet den Mittelkanal an acht definierten Stellen. Acht Seitenschrauben bleiben eine rechnerisch nicht angerechnete Reserve. 522 bleibt Standard, weil Sika den Vorbehandlungsweg namentlich dokumentiert. Carloflex erst einsetzen, wenn der passende Kunststoffprimer prozesssicher festgelegt ist; Produkte innerhalb einer Baugruppe nicht mischen. |
| Vorbehandlung der 522-Klebezonen | Sika Cleaner P, Sika Primer-507, Sika Aktivator-205 | Lackfreie ASA-GF-/Belluna-Kunststoffflächen: Cleaner P + Primer-507 als ABS-Analogie. GFK-Gelcoat: Cleaner P + Aktivator-205. Aktuelle Sika-TDS und Ablüftzeiten beachten. |
| Holzrahmen | SikaForce-710 L35 + SikaForce-010, 1,2-kg-A+B-Set | 2K-PUR-System ausdrücklich für Holz/GFK mit EPS/XPS-Sandwichkernen; kontrollierte Härtung in der geschlossenen Dachfuge. Rechnerisch nur 0,05 MPa und eine GFK/Holz-Fläche angesetzt. |
| Lack-Haftgrund | Mipa 1K-Plastic-Grundierfiller-Spray, Art.-Nr. 213390000 | Füllender Haftvermittler für u. a. ABS, PC/ABS und GFK, mit 2K-Decklack überlackierbar. ASA-GF ist nicht ausdrücklich gelistet; der Lack bleibt nichttragend und wird jährlich kontrolliert. |
| Weißer Decklack | Mipa PUR HS 2K-PUR-Acryl-Fahrzeuglack RAL 9003 Signalweiß glänzend + Mipa 2K-MS-Härter MS 25, 2:1 Volumen | Wetter- und vergilbungsfester Nutzfahrzeuglack mit hoher chemischer/mechanischer Beständigkeit; Weiß reduziert die solare Aufheizung des schwarzen Rohlings. |

Primärquellen, unveränderte lokale Datenblätter und nachvollziehbare
Quellenprotokolle sind im
[`references`-Katalog](../references/README.md) mit Quelle und SHA-256 geordnet.

Bewusst nicht gewählt: WEICON Epoxyd-Minutenkleber für die Segmentstöße.
Trotz hoher nomineller Festigkeit und Temperaturbeständigkeit nennt das TDS
nur 2,7 % Bruchdehnung und einen Glasübergang von 44,7 °C (46,1 °C nach
Tempern). Das liegt deutlich unter `T_MAX = 85 °C`; RK-1300 passt außerdem
mit seinem 0,15–0,25-mm-Festigkeitsoptimum direkt zur konstruierten Passung.

## Bildliste (`build/documentation/<hash>/img/`)

| Datei | Inhalt | Markierung |
|-------|--------|-----------|
| 01 titel_explosion | Explosion 4 Segmente + Platte/Dichtring/Clips | — |
| 02 teile_uebersicht | Universalteil + Belluna-Platte; Dichtring bereits eingelegt | — |
| 03 fuegeflaechen | Lappenende, Fügeflächen | **grün** (Schulter + Stirn) |
| 04 kleber_aktivator | Zwei Segmente am Stoß getrennt | **blau** (Aktivator auf beiden Flächen) / **grün** (danach RK-1300 einseitig) |
| 05 m5_montage | Stoß von oben | 1× roter M5-Achsmarker (Senkung) |
| 06 m5_mutter | Stoß von unten | 1× roter M5-Achsmarker (Muttertasche) |
| 07 rahmen_komplett | Gefügter Rahmen | 4× dezent rote M5-Marker |
| 08 maskierung_lack | moderate 20°-Unteransicht | **gelb** (gleichmäßige Doppelraupe, Mittelkanal und 16 Pad-Auflageflächen) |
| 09 dach_holzrahmen | Dach-Halbschnitt | Holzrahmen eindeutig holzfarben, ohne Bauteil-fremden Marker |
| 10 aufsetzen | Rahmen über Dach, Kragen sichtbar | — |
| 11 hybrid_dachinterface | Eingesetzter Rahmen mit transparentem Dach und Holzrahmen | 8× rote Achsen der seitlichen, nicht angerechneten Rückfallschrauben |
| 12 kleberaupe | Unterseite | **grün** (zwei flache Führungsböden; acht Unterbrechungen der inneren Raupe sichtbar) |
| 13 platte_schrauben | Rahmen+Platte (halbtransparent) | 16 mögliche rote ST4,2-Achsmarker; 8 werden gesetzt |
| 14 fertig | Kompletter Stapel | — |

## Texte/Bilder ergänzen oder ändern

- **Text**: `build_pdf.py::build_model()` — `material` (Tabelle) und `steps`
  (Liste von `dict(nr, titel, bild, bilder2, absaetze, warn)`). `warn`-Einträge
  sind `("warn"|"hinweis", "Text")`. Variable Werte über `t["…"]` aus dem
  Manifest ziehen (nicht hartkodieren); `de(x)` formatiert mit Dezimalkomma.
- **Layout/Druck-CSS**: `build_pdf.py::CSS` — A4 mit 14-mm-Seitenrand,
  humanistische Avenir-Next-Typografie, Blau als Leitsystem, Gelb nur für
  Warnungen und Rot nur für echte Freigabesperren. Die elf Seiten sind als
  stabile Orientierungseinheiten mit festen Seitenumbrüchen gebaut. Damit
  entstehen keine verwaisten Bilder, Tabellenfortsetzungen oder
  Hinweisboxen.
- **Automatische Abnahme**: `pipeline.checks.validate_manual()` verlangt nach
  jedem `manual`-Lauf genau 14 Bilder in 1500×1125 px, den aktuellen
  Parameterhash und genau elf PDF-Seiten. Ein unbeabsichtigter Umbruch ist
  damit ein Pipeline-Fehler statt einer stillen Layoutänderung.
- **Neues Bild**: Geometrie/STL in `build_stls.py`, ggf. Marker/Filtergrößen
  ins Manifest; Renderfunktion `imgNN_*` in `render_steps.py` (Kamera, Material,
  `highlight(obj, farbe, praedikat)`, `marker(p1, p2, radius)`); Bildreferenz
  in den passenden `steps`-Eintrag.

## Konventionen (Blender)

- Cycles, 96 Samples, Denoising, 1500×1125.
- **Kräftiger technischer Studiohintergrund** (sRGB ca. 60/149/195, aus dem
  freigegebenen Referenzbild gemessen); sichtbarer Hintergrund und
  Weltbeleuchtung sind über den Camera-Ray getrennt. Dadurch bleibt der
  Hintergrund ruhig, ohne die Formschatten der hellen Bauteile aufzuhellen.
  Der `Standard`-View-Transform bewahrt die definierten RGB-Werte; AgX wird
  bewusst nicht verwendet, weil dessen Highlight-Rolloff weißes ASA grau und
  Signalfarben pastellig erscheinen ließ. Dunkelgraue technische Konturlinien
  mit 50 % Deckkraft sichern die Lesbarkeit ausschließlich am weißen Adapter.
- Alle vier identischen ASA-GF-Segmente erscheinen didaktisch im finalen
  lackierten RAL-9003-Zustand klar weiß; der reale Rohling ist schwarz. Die
  Belluna-Originalplatte ist deutlich beige. Clips silber-metallisch und in allen Belluna-relevanten Bildern
  sichtbar, Dichtring fast schwarz. Dach mittelgrau, Holzrahmen
  holzfarben, XPS blau-grau.
- Marker: emissive Signalrot-Zylinder (Emission Strength 2.0). Flächen-
  Hervorhebung: zweites emissives Material (grün/blau/gelb) per Polygon-Filter
  nach Position direkt in `montage/render_steps.py`.

## Fallstricke

- **`freecadcmd`**: Multiline nur per Skriptdatei, argv unzuverlässig;
  stdout wird mit `reconfigure(line_buffering=True)` explizit gepuffert.
- **Segment-Basisfarbe vs. Hervorhebung**: In Bild 04 werden beide Segmente
  mit derselben weißen ASA-Basisfarbe geladen; Grün und Blau bezeichnen damit
  ausschließlich RK-1300- bzw. Aktivatorflächen.
- **Halbschnitt-Beleuchtung**: Die Schnittfläche eines `y>0`-Schnitts zeigt
  nach +y — Kamera **und** Zusatzlicht auf die +y-Seite, sonst bleibt der
  Schnitt unbeleuchtet (Bild 09).
- **Dach als echtes Sandwich**: Die Kern-Kavität wird aus dem Dach-Vollmaterial
  ausgeschnitten und von Holzrahmen + XPS gefüllt (kein z-Fighting im Schnitt).
- **Zwei nach oben/unten zeigende Fügeflächen** (Bild 04) sind nur gemeinsam
  sichtbar, wenn die obere Stoßhälfte angehoben und die Kamera **zwischen** den
  Schulterhöhen (nahezu horizontaler Blick) positioniert wird.
- **Chrome**: absolute `file://`-Pfade, `--no-pdf-header-footer`,
  `--virtual-time-budget=10000` gegen fehlende Bilder.

## Vorbehalt

Die Titelseite trägt bewusst das rote Banner **VORABVERSION**. Der aktuelle
Status bleibt `PROTOTYPE_ONLY`, bis die in `verification.md` aufgeführten
physischen Nachweise und Fahrzeugmaße geschlossen sind.
