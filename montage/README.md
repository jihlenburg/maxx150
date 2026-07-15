# montage/ — Illustrierte Montageanleitung (PDF)

Reproduzierbarer Generator für eine gedruckte, bebilderte **Montageanleitung**
des Belluna-Adapterrahmens. Drei Stufen, wie im übrigen Repo strikt getrennt
(FreeCAD baut Geometrie, Blender rendert, python3/Chrome setzt das PDF):

```
params.py ──► build_stls.py (bin/fc) ──► out/montage/stl/*.stl + manifest.json
                                             │
                        render_steps.py (blender) ──► out/montage/img/*.png
                                             │
                          build_pdf.py (python3) ──► out/montageanleitung_<hash>.pdf
```

## Aufruf

Komplette Pipeline über den Orchestrator:

```sh
scripts/montageanleitung.sh
```

Das ist die Regel. Für Iterationen einzelne Stufen:

```sh
bin/fc montage/build_stls.py                 # STLs + Manifest neu
MONTAGE_SKIP_SEGS=1 bin/fc montage/build_stls.py   # nur Dach/Platte neu (Segmente behalten)

blender -b -P montage/render_steps.py -- out/montage/stl out/montage/img
# jedes Bild zusätzlich: ~/Downloads/Belluna-Render-Zwischenstand/
ONLY_IMG=04,09 blender -b -P montage/render_steps.py -- out/montage/stl out/montage/img  # nur Bild 04+09

python3 montage/build_pdf.py                 # HTML + PDF
python3 montage/build_pdf.py --no-pdf         # nur HTML (kein Chrome)
```

Alle Stufen sind **idempotent** — erneuter Aufruf überschreibt sauber.

> **Lange Läufe im Hintergrund.** `build_stls.py` baut die vier Segmente
> (mehrere Minuten), der Vollrender der 14 Bilder dauert 10–20 min. Wie im
> Skill `maxx150-pipeline` beschrieben als Hintergrundprozess mit Log + Poll
> starten (`nohup … > log 2>&1 &`), **nicht** im Vordergrund mit kurzem Timeout
> — ein getimeouteter Vordergrund-Poll killt sonst die Prozessgruppe inkl.
> Blender. Launch und Poll deshalb in **getrennten** Kommandos.

## Dateien

| Datei | Stufe | Zweck |
|-------|-------|-------|
| `build_stls.py` | FreeCAD (`bin/fc`) | Baut Segmente, Belluna-Platte/Clips/Dichtring (Mock), Dach-Sandwich (Dach + Holzrahmen + XPS-Kern) inkl. Halbschnitte; schreibt `out/montage/stl/*.stl` + `out/montage/manifest.json`. |
| `render_steps.py` | Blender | Rendert die 14 Schrittbilder nach `out/montage/img/`. Liest **nur** das Manifest. |
| `build_pdf.py` | python3 | HTML aus `STEPS`-Datenstruktur + Chrome-Headless-PDF. Liest **nur** das Manifest. |
| `README.md` | — | Dieses Dokument. |

Orchestrator: `../scripts/montageanleitung.sh`.

## Single Source of Truth: das Manifest

`out/montage/manifest.json` ist die einzige Schnittstelle zwischen den Stufen.
`build_stls.py` zieht **alle** Werte zur Laufzeit aus `params.py` bzw. den
`export`-Helpern (`_m5_bolt_length`, `PRM.select_shaft`,
`PRM.groove_centerline_len`, `PRM.bot_kragen_hole_count` …) und legt sie ab:

- `params_hash`, `geom_rev`, `erzeugt` (Datum);
- `geometrie` — abgeleitete Maße für die Blender-Polygon-Filter (Deckhöhe
  `top_z`, Lap-Ebene, Kleberille, Noppenradien, Maskierzone, Holzrahmen);
- `marker` — Markerachsen als Endpunktpaare: `m5` (4×), `dach_screws` (8×),
  `plate_screws` (16×), jeweils exakt aus den `params`-Positionen und dem
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
| Druckteil | Würth ASA GF15, Verkehrsschwarz ähnlich RAL 9017, 1,75 mm, Art.-Nr. 4954641200 | 15 % GF, UV-/Witterungseignung, hohe Steifigkeit und geringerer Verzug; mechanische Werte sind jedoch nur Halbzeugwerte, daher bleiben Druckcoupons Pflicht. |
| Segmentstöße | WEICON RK-1300, 60-g-Set inkl. Aktivator, Art.-Nr. 10000118 | MMA-Strukturklebstoff für Hartkunststoffe/Fahrzeugbau; höchste Zugscherfestigkeit bei 0,15–0,25 mm und bis 130 °C spezifiziert. ASA-GF wird über Originaldruck-Coupon qualifiziert. |
| Dach- und Belluna-Dichtung | Carloflex 410 UV weiß, 310 ml; exakt benannte Alternative: Sikaflex-522 weiß, 300 ml | Carloflex bleibt Bellunas Referenzweg. 522 ist ein aktueller UV-/witterungsbeständiger STP-Dichtstoff für Kunststoffe und 2K-Lacke; nur nach Haftcoupon, innerhalb einer Baugruppe nicht mischen. |
| Holzrahmen | SikaForce-710 L35 + SikaForce-010, 1,2-kg-A+B-Set | 2K-PUR-System ausdrücklich für Holz/GFK mit EPS/XPS-Sandwichkernen; kontrollierte Härtung in der geschlossenen Dachfuge. Erfordert exaktes Mischen, Coupon und definierten Pressprozess. |
| Lack-Haftgrund | Mipa 1K-Plastic-Grundierfiller-Spray, Art.-Nr. 213390000 | Füllender Haftvermittler für u. a. ABS, PC/ABS und GFK, mit 2K-Decklack überlackierbar. ASA-GF ist nicht ausdrücklich gelistet: Coupon ist Pflicht. |
| Weißer Decklack | Mipa PUR HS 2K-PUR-Acryl-Fahrzeuglack RAL 9003 Signalweiß glänzend + Mipa 2K-MS-Härter MS 25, 2:1 Volumen | Wetter- und vergilbungsfester Nutzfahrzeuglack mit hoher chemischer/mechanischer Beständigkeit; Weiß reduziert die solare Aufheizung des schwarzen Rohlings. |

Primärquellen: [Würth ASA GF15](https://eshop.wuerth.de/ASA-GF15-filament-PRNTMATL-ASAGF15-TRAFFBLCK-D175-075KG/4954641200.sku/en/US/EUR/),
[WEICON RK-1300 TDS](https://media.weicon.de/fmds/307278/dld%3Ainline/DE_TDS_10560060_RK-1300.pdf),
[WEICON Epoxyd-Minutenkleber TDS](https://media.weicon.de/fmds/307275/dld%3Ainline/DE_TDS_10550024_Epoxyd-Minutenkleber.pdf),
[Belluna Carloflex 410 UV](https://belluna.eu/shop/carloflex/),
[Belluna Super-Fan-Anleitung](https://belluna.eu/wp-content/uploads/2024/05/Anleitung-Super-Fan.pdf),
[Sikaflex-522 TDS](https://deu.sika.com/content/dam/dms/deaddconst01/p/sikaflex-522.pdf),
[SikaForce-710 L35 TDS](https://deu.sika.com/dms/getdocument.get/41466f3f-1639-4fc4-8298-5c9a0a2d34e1/sikaforce-710-l35.pdf),
[Mipa Plastic-Grundierfiller TDS](https://www.mipa-paints.com/fileadmin/product/de/pi/spray/Mipa_1K-Plastic-Grundierfiller-Spray_DE.pdf) und
[Mipa PUR HS TDS](https://www.mipa-paints.com/fileadmin/product/de/pi/lm/Mipa_PUR_HS_2K-PUR-Acryl-Fahrzeuglack_DE.pdf).

Bewusst nicht gewählt: WEICON Epoxyd-Minutenkleber für die Segmentstöße.
Trotz hoher nomineller Festigkeit und Temperaturbeständigkeit nennt das TDS
nur 2,7 % Bruchdehnung und einen Glasübergang von 44,7 °C (46,1 °C nach
Tempern). Das liegt deutlich unter `T_MAX = 85 °C`; RK-1300 passt außerdem
mit seinem 0,15–0,25-mm-Festigkeitsoptimum direkt zur konstruierten Passung.

## Bildliste (`out/montage/img/`)

| Datei | Inhalt | Markierung |
|-------|--------|-----------|
| 01 titel_explosion | Explosion 4 Segmente + Platte/Dichtring/Clips | — |
| 02 teile_uebersicht | Universalteil + Belluna-Platte; Dichtring bereits eingelegt | — |
| 03 fuegeflaechen | Lappenende, Fügeflächen | **grün** (Schulter + Stirn) |
| 04 kleber_aktivator | Zwei Segmente am Stoß getrennt | **blau** (Aktivator auf beiden Flächen) / **grün** (danach RK-1300 einseitig) |
| 05 m5_montage | Stoß von oben | roter M5-Achsmarker (Senkung) |
| 06 m5_mutter | Stoß von unten | roter M5-Achsmarker (Muttertasche) |
| 07 rahmen_komplett | Gefügter Rahmen | 4× dezent rote M5-Marker |
| 08 maskierung_lack | moderate 20°-Unteransicht | **gelb** (gleichmäßige Kleberille + Noppen-Auflageflächen) |
| 09 dach_holzrahmen | Dach-Halbschnitt | Holzrahmen eindeutig holzfarben, ohne Bauteil-fremden Marker |
| 10 aufsetzen | Rahmen über Dach, Kragen sichtbar | — |
| 11 dachschrauben | Rahmen auf Dach (halbtransparent) | 8× rote Ø4-Achsmarker |
| 12 kleberaupe | Unterseite | **grün** (nur Kleberille) |
| 13 platte_schrauben | Rahmen+Platte (halbtransparent) | 16× rote ST4,2-Achsmarker |
| 14 fertig | Kompletter Stapel | — |

## Texte/Bilder ergänzen oder ändern

- **Text**: `build_pdf.py::build_model()` — `material` (Tabelle) und `steps`
  (Liste von `dict(nr, titel, bild, bilder2, absaetze, warn)`). `warn`-Einträge
  sind `("warn"|"hinweis", "Text")`. Variable Werte über `t["…"]` aus dem
  Manifest ziehen (nicht hartkodieren); `de(x)` formatiert mit Dezimalkomma.
- **Layout/Druck-CSS**: `build_pdf.py::CSS` — A4 mit 14-mm-Seitenrand,
  humanistische Avenir-Next-Typografie, Blau als Leitsystem, Gelb nur für
  Warnungen und Rot nur für echte Freigabesperren. Die zehn Seiten sind als
  stabile Orientierungseinheiten gebaut: Titel, zwei Vorbereitungsseiten,
  Schritte 1–6 jeweils vollständig auf einer Seite sowie Schritt 7+8 als
  gemeinsame Abschlussseite. Damit entstehen keine verwaisten Bilder,
  Tabellenfortsetzungen oder Hinweisboxen mehr.
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
  nach Position (Muster `render/blender_stapel.py` / `render/blender_platte_a3a.py`).

## Fallstricke

- **`freecadcmd`**: Multiline nur per Skriptdatei, argv unzuverlässig →
  Steuerung über Env-Vars (`MONTAGE_SKIP_SEGS`); stdout mit
  `reconfigure(line_buffering=True)`. Siehe Skill `maxx150-pipeline`.
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

Die Titelseite trägt bewusst das rote Banner **VORABVERSION** — Druck-/
Montagefreigabe erst nach Kontrolle des realen Haubenfreigangs und einem
PLA-Passform-Probedruck (Stand: PASS mit Vorbehalt).
