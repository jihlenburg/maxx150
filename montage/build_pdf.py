"""PDF-Seite des Montageanleitungs-Generators (reines python3, KEIN FreeCAD).

Zweck
-----
Erzeugt aus einer gut dokumentierten ``STEPS``-Datenstruktur und den Werten aus
``out/montage/manifest.json`` zunächst ``out/montage/montageanleitung_<hash>.html``
und druckt diese via Chrome-Headless zu ``out/montageanleitung_<hash>.pdf``.

Alle variablen Zahlen (M5-Länge, Klebstoffmenge, Wellenlänge, Schraubenanzahl …)
stammen aus dem Manifest -- als Fixtext gekennzeichnete Angaben (Tempern
80 °C/4 h, Aktivator beidseitig, RAL 9003 …) sind bewusst wörtlich.

Aufruf
------
    python3 montage/build_pdf.py [--manifest <pfad>] [--no-pdf]

Abhängigkeiten
--------------
- Google Chrome (Headless-PDF-Druck).
- out/montage/manifest.json + out/montage/img/*.png (aus build_stls/render_steps).

Endmarker im Log: ``PDF-ENDE: <pfad>``.
"""
import argparse
import datetime
import html
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_MONTAGE = os.path.join(ROOT, "out", "montage")
OUT = os.path.join(ROOT, "out")
IMG_REL = "img"                         # relativ zur HTML-Datei in out/montage/
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def de(x):
    """Zahl mit deutschem Dezimalkomma formatieren (ganzzahlig ohne Nachkomma)."""
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    return str(x).replace(".", ",")


# ---------------------------------------------------------------------------
# Inhaltsmodell
# ---------------------------------------------------------------------------
def build_model(mf):
    """Baut das komplette Inhaltsmodell (Titel, Materialtabelle, Schritte)
    aus den Manifest-Textwerten. Trennt Inhalt (hier) von Layout (render_html)."""
    t = mf["text"]
    h = mf["params_hash"]
    datum = mf["erzeugt"]

    material = [
        ("4×", f"Druckteil-Segment (universal, rotationsidentisch) aus "
               f"{t['material_name']}, je ca. {de(t['seg_mass_g'])} g. Schwarz "
               f"ist nur die Rohteilfarbe; RAL 9003 ist vor Einbau Pflicht."),
        ("4× 750 g", "Würth ASA GF15, Verkehrsschwarz RAL 9017 ähnlich, "
                     "1,75 mm, Art.-Nr. 4954641200. Vier Spulen derselben Charge "
                     "decken vier Segmente, Coupons und Fehldruckreserve."),
        ("4×", f"Zylinderkopfschraube M5×{de(t['m5_length'])} DIN 912 "
               f"(Durchgang Ø{de(t['m5_through_d'])}) + 4× Sechskantmutter M5 "
               f"(SW {de(t['nut_af'])})"),
        ("1× 60 g", "WEICON RK-1300 Set, Art.-Nr. 10000118, inklusive "
                    "RK-Aktivator. Strukturklebstoff für die vier Segmentstöße; "
                    "Aktivator auf den rauen FDM-Flächen beidseitig."),
        ("1× 310 ml", "Carloflex 410 UV weiß (Carlofon), elastische 1K-PU-Dicht- "
                      "und Klebemasse. Für untere Kleberille, Außenkehle, "
                      "Belluna-Ringklebenut und Schraubabdichtung."),
        (de(t["dach_screw_count"]) + "×",
         f"Belluna-Schraube ST {de(t['dach_screw_st_d'])}×"
         f"{de(t['dach_screw_st_l'])} aus dem Lieferumfang, "
         f"Adapter-Unterkragen→Holzrahmen; 3-mm-Kernloch vorbohren"),
        ("8×", f"Belluna-Schraube ST {de(t['dach_screw_st_d'])}×"
               f"{de(t['dach_screw_st_l'])} aus dem Lieferumfang, "
               f"Belluna-Platte→Adapter-Innenwand; 3-mm-Kernloch vorbohren"),
        ("1", f"Wasserfestes Holz für den Ausschnittsrahmen (Breite ≥ "
              f"{de(t['wood_frame_w'])} mm, Höhe = realer Dachkern)"),
        ("1 Gebinde", "KLEIBERIT 501.0 1K-PUR-Leim, D4 nach DIN EN 204, "
                      "zum vollflächigen Einsetzen des Holzrahmens in Holz/XPS."),
        ("1× 400 ml", "Mipa 1K-Plastic-Grundierfiller-Spray, hellgrau, "
                      "Art.-Nr. 213390000. Füllender Kunststoff-Haftgrund; "
                      "die Eignung auf ASA-GF wird am Coupon bestätigt."),
        ("1 System", "Mipa PUR HS 2K-PUR-Acryl-Fahrzeuglack, RAL 9003 "
                     "Signalweiß glänzend + Mipa 2K-MS-Härter MS 25, "
                     "Mischung 2:1 nach Volumen. Weiße Beschichtung ist Pflicht."),
        ("div.", f"Mipa Kunststoffreiniger antistatisch, Schleifpapier K240, "
                 f"MP Softpad Superfine, Drehmomentschlüssel "
                 f"({de(t['torque_nm'])} Nm), Vierkantwelle {de(t['shaft_mm'])} mm"),
    ]

    steps = [
        dict(nr=1, titel="Druckteile vorbereiten",
             bild=("03_fuegeflaechen.png",
                   "Bild 3: Fügeflächen einer Lappe (grün) – Überlappungs"
                   "schulter und Stirn."),
             absaetze=[
                 "Vier identische Segmente aus Würth ASA GF15 Verkehrsschwarz "
                 "(Art.-Nr. 4954641200) drucken: Deckfläche nach unten, "
                 "gehärtete Düse, geschlossener temperierter Bauraum, "
                 "4 Perimeter und 100 % Infill. Vor der Serie ein Segment auf "
                 "Ebenheit und Öffnungsmaß prüfen.",
                 "Kein pauschales Tempern: Würth nennt für diesen Artikel keinen "
                 "allgemeinen Temperprozess. Mechanische Werte des Herstellers "
                 "stammen aus Halbzeug; XY- und Z-Coupons des realen Druckprozesses "
                 "bleiben Teil der Freigabe.",
                 "Die vier Halbüberlappungs-Fügeflächen (grün im Bild: Ober- "
                 "und Unterseite der Lappe sowie die Stirn) mit Schleifpapier K240 "
                 "aufrauen und gemäß WEICON-Datenblatt reinigen und trocknen.",
             ],
             warn=[("warn", "Keine ungeprüften Lösemittel verwenden. Aceton "
                            "greift ASA an; Kleb- und Lackflächen außerdem strikt "
                            "silikon-, fett- und staubfrei halten.")]),
        dict(nr=2, titel="Stöße verkleben und verschrauben",
             bild=("04_kleber_aktivator.png",
                   "Bild 4: Zwei Segmente am Stoß 60 mm auseinandergezogen – "
                   "blau = Aktivatorschritt auf beiden Flächen; grün = "
                   "anschließender RK-1300-Auftrag auf einer Fläche."),
             bilder2=[("05_m5_montage.png",
                       "Bild 5: M5-Achse durch die Kopfsenkung (von oben)."),
                      ("06_m5_mutter.png",
                       "Bild 6: Muttertasche mit M5-Achse (von unten)."),
                      ("07_rahmen_komplett.png",
                       "Bild 7: Gefügter Rahmen, alle vier M5-Positionen.")],
             absaetze=[
                 "WEICON RK-Aktivator auf BEIDE rauen/porösen FDM-Fügeflächen "
                 "auftragen und mindestens 5 min ablüften. Anschließend RK-1300 "
                 "auf eine Fügefläche geben. Im Bild kennzeichnet Blau den "
                 "Aktivatorschritt, Grün den danach aufgetragenen Klebstoff.",
                 f"Segmente fügen und SOFORT je Stoß eine M5×{de(t['m5_length'])} "
                 f"(DIN 912) mit Mutter einsetzen und mit {de(t['torque_nm'])} Nm "
                 f"anziehen. Die konstruktive Spaltbreite darf die 0,4-mm-Grenze "
                 f"des RK-1300 nicht überschreiten.",
                 "Reihenfolge: erst 2+2 Segmente zu zwei Halbrahmen fügen, dann "
                 "die beiden Halbrahmen. Anschließend 24 h aushärten lassen.",
                 "Nach dem Anziehen die vier M5-Kopftaschen bündig mit RK-1300 "
                 "versiegeln (offene Taschen wären Wasserreservoirs oben).",
             ],
             warn=[("warn", "RK-1300 ist für ABS und GFK geprüft, ASA-GF aber "
                            "nicht ausdrücklich gelistet. Vor der Baugruppe einen "
                            "repräsentativen Stoßcoupon mit identischer Düse, "
                            "Charge und Oberflächenvorbereitung zerstörend prüfen.")]),
        dict(nr=3, titel="Weiße Schutzlackierung (Pflicht)",
             bild=("08_maskierung_lack.png",
                   "Bild 8: Unterseite – Kleberille und Noppenfeld (gelb) beim "
                   "Lackieren abkleben."),
             absaetze=[
                 "Der Plan-of-Record ist schwarzes ASA-GF; die weiße Lackierung "
                 "ist deshalb immer erforderlich. Nach dem Fügen die Baugruppe "
                 "für 60 min bei 60 °C ausgasen lassen, wie es Mipa für die "
                 "Kunststoffvorbereitung fordert, und vollständig abkühlen lassen.",
                 "Alle späteren Klebezonen abkleben: untere Kleberille und "
                 "Noppenfeld sowie die obere Auflage der Belluna-Platte. Mit "
                 "Mipa Kunststoffreiniger antistatisch reinigen, MP Softpad "
                 "Superfine schleifen, nachreinigen, trocknen und Benetzungsprobe "
                 "durchführen.",
                 "Mipa 1K-Plastic-Grundierfiller-Spray (Art.-Nr. 213390000) in "
                 "2–3 dünnen Spritzgängen auftragen: 15–40 µm, 2–3 min "
                 "Zwischenablüftung, nach 15–20 min überlackierbar.",
                 "Mipa PUR HS in RAL 9003 Signalweiß glänzend mit Mipa "
                 "2K-MS-Härter MS 25 im Volumenverhältnis 2:1 mischen. "
                 "1–2 Spritzgänge auf 50–60 µm, 5–8 min dazwischen; bei 20 °C "
                 "nach 12–24 h montagefest. Danach Maskierung abziehen.",
             ],
             warn=[("warn", "ASA-GF steht nicht in der Mipa-Primerliste. Vorher "
                            "am Originaldruck einen Lackcoupon komplett aufbauen "
                            "und Gitterschnitt/Abreißversuch durchführen. 2K-PUR "
                            "nur im Lackierfachbetrieb mit geeigneter Absaugung "
                            "und Schutzmaßnahmen verarbeiten."),
                   ("hinweis", "Warum dieses System: Der füllende Kunststoffprimer "
                               "ist für ABS, PC/ABS und GFK sowie 2K-Decklacke "
                               "ausgewiesen. PUR HS ist ein wetter- und "
                               "vergilbungsfester Nutzfahrzeuglack; RAL 9003 "
                               "reduziert die solare Aufheizung und ist Teil der "
                               "thermischen Auslegung.")]),
        dict(nr=4, titel="Dach vorbereiten",
             bild=("09_dach_holzrahmen.png",
                   "Bild 9: Dachquerschnitt – XPS-Kern ausräumen, Holzrahmen "
                   "(holzfarben) vollflächig einsetzen."),
             absaetze=[
                 "Mini-Heki demontieren, das komplette Altbett restlos entfernen "
                 "und mit Isopropanol reinigen.",
                 f"Ausschnitt messen (Soll {de(t['cutout_w'])}×{de(t['cutout_w'])}).",
                 f"Rund um den Ausschnitt den XPS-Randstreifen ausräumen und einen "
                 f"wasserfesten Holzrahmen (Höhe = real gemessener Dachkern, "
                 f"Breite ≥ {de(t['wood_frame_w'])} mm) mit KLEIBERIT 501.0 "
                 f"1K-PUR-Leim vollflächig einsetzen. Mindestens 60 min pressen "
                 f"und 2–3 h nachbinden lassen. Austretenden PUR-Schaum entfernen. "
                 f"Der Rahmen ist Schraubgrund UND Kompressionsschutz.",
             ],
             warn=[("hinweis", "Warum KLEIBERIT 501.0: Das Produkt ist D4 nach "
                               "DIN EN 204, hochwärmebeständig und für Holz, "
                               "Hartschäume sowie feuchtebelastete Anwendungen "
                               "ausgewiesen. Die offene Zeit von etwa 20–25 min "
                               "erlaubt das saubere Einsetzen des kompletten Rahmens."),
                   ("warn", f"Der Unterkragen ({de(t['kragen_outer_w'])} mm) "
                            f"braucht rundum ≥ {de(t['bot_kragen_clear'])} mm Luft "
                            f"im Ausschnitt. Real gemessen passt die 397er-Platte – "
                            f"vor dem Setzen den echten Ausschnitt kontrollieren.")]),
        dict(nr=5, titel="Rahmen setzen und verschrauben",
             bild=("12_kleberaupe.png",
                   "Bild 12: Kleberaupe kommt in die grün markierte Rille der "
                   "Unterseite."),
             bilder2=[("10_aufsetzen.png",
                       "Bild 10: Rahmen mit Unterkragen über dem Ausschnitt."),
                      ("11_dachschrauben.png",
                       "Bild 11: ST4,2×25-Schrauben (rot) durch den Kragen in den "
                       "Holzrahmen.")],
             absaetze=[
                 f"Carloflex 410 UV weiß aus der 310-ml-Kartusche als geschlossene "
                 f"Raupe (ca. {de(t['bead_ml'])} ml) in die untere Kleberille "
                 f"legen (Bild 12).",
                 "Rahmen mit dem Unterkragen in den Ausschnitt einsetzen (Bild 10) "
                 "und lagerichtig ausrichten.",
                 f"Je Seite zwei ST {de(t['dach_screw_st_d'])}×"
                 f"{de(t['dach_screw_st_l'])} aus dem Belluna-Lieferumfang durch die "
                 f"Kragenlöcher ({de(t['dach_screw_count'])} gesamt) in den "
                 f"Holzrahmen setzen – 3-mm-Kernloch vorbohren (Bild 11). Das "
                 f"fixiert den Rahmen lagerichtig, während der Kleber härtet.",
                 "Außen umlaufend mit Carloflex eine geschlossene Kehlnaht ziehen; "
                 "Schraubdurchtritte ebenfalls abdichten.",
             ],
             warn=[("hinweis", "Warum Carloflex 410 UV: Belluna empfiehlt genau "
                               "dieses Produkt für den Super Fan. Die elastische, "
                               "UV-beständige 1K-PU-Masse verbindet GFK und "
                               "Adapter, dichtet gleichzeitig und kann die "
                               "thermische Relativbewegung aufnehmen. Deshalb "
                               "wird keine generische Sika-Alternative gemischt."),
                   ("warn", f"Die Noppen definieren die {de(t['glue_gap'])} mm "
                            f"Fugendicke – den Kleber NICHT auspressen "
                            f"(Thermik-Elastikfuge).")]),
        dict(nr=6, titel="Belluna-Platte montieren",
             bild=("13_platte_schrauben.png",
                   "Bild 13: Belluna-Platte mit silbernen Metallclips; "
                   "ST4,2-Schrauben (rot) seitlich durch den Platten-Kragen "
                   "in die Adapter-Innenwand."),
             absaetze=[
                 "Carloflex 410 UV weiß in die Klebekanäle der Plattenunterseite "
                 "auftragen "
                 "und die Platte mittig aufsetzen (der Kragen taucht in die "
                 "Öffnung).",
                 f"Die ST {de(t['plate_screw_d'])}×{de(t['plate_screw_l'])} seitlich "
                 f"durch den Platten-Kragen in die Adapter-Innenwand setzen "
                 f"(3-mm-Kernloch vorbohren, Bild 13). Jede Seite bietet universelle "
                 f"Vollmaterialrippen für beide Belluna-Varianten (±140 und "
                 f"±165 mm).",
             ],
             warn=[("warn", "Vor der Serienmontage Haftcoupons zerstörend prüfen: "
                            "Carloflex auf rohem ASA-GF, auf ausgehärtetem "
                            "Mipa-Decklack und auf dem realen X150-GFK-Dach. "
                            "Nur vollständig kohäsive bzw. substratseitig "
                            "tragfähige Bruchbilder freigeben."),
                   ("hinweis", "Die zwei Mittellöcher der 3-Loch-Seiten liegen "
                               "auf den Segmentstößen – erst nach Aushärtung "
                               "des Stoßklebers setzen oder weglassen; die 8 "
                               "Außenschrauben genügen.")]),
        dict(nr=7, titel="Lüfter einsetzen",
             bild=("14_fertig.png",
                   "Bild 14: Fertige Baugruppe – Adapter, Platte und Dichtring."),
             absaetze=[
                 f"Vierkantwelle {de(t['shaft_mm'])} mm einsetzen "
                 f"(effektive Wandstärke {de(t['effective_wall_mm'])} mm = Dach "
                 f"{de(t['roof_t'])} mm + Erhöhung {de(t['h_raise'])} mm).",
                 "Lüfter-Sockel in die Clips einsetzen, Feder-/Sicherungselemente "
                 "montieren.",
                 "Nach der ersten Hitzeperiode alle Verschraubungen nachziehen "
                 "(Relaxation). Beim Nachziehen Lackkanten nicht beschädigen.",
             ],
             warn=[]),
        dict(nr=8, titel="Dichtheitsprüfung und Wartung",
             bild=None,
             absaetze=[
                 "Erst drucklos fluten (Gießkanne, 10 min, Innenkontrolle).",
                 "Hochdruck nur aus ISO-20653-9K-Abstand auf den Sockelbereich "
                 "richten – NIE direkt auf die Lüfterhaube (Belluna ist IPX4).",
                 "Jährlich die Nähte und den Lackzustand sichtprüfen. Die "
                 "Lackprüfung ist beim schwarzen Rohteil immer "
                 "Pflicht; Beschädigungen bis auf ASA-GF fachgerecht ausbessern.",
             ],
             warn=[]),
    ]

    return dict(hash=h, datum=datum, geom_rev=mf["geom_rev"], material=material,
                steps=steps, text=t)


# ---------------------------------------------------------------------------
# HTML/CSS
# ---------------------------------------------------------------------------
CSS = """
:root { --ink:#1a1d21; --muted:#5b6570; --line:#c8ccd2; --accent:#1f4e8c; }
* { box-sizing: border-box; }
@page { size: A4; margin: 14mm; }
html, body { margin:0; padding:0; }
body {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--ink); font-size: 10.7pt; line-height: 1.5;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
h1 { font-size: 22pt; line-height:1.15; margin:0 0 4mm; }
h2 { font-size: 13.5pt; margin:0 0 3mm; color: var(--accent);
     border-bottom: 2px solid var(--accent); padding-bottom: 1.5mm; }
p { margin: 0 0 2.4mm; }
img { max-width: 100%; height: auto; display:block; border:1px solid var(--line);
      border-radius: 3px; }
figure { margin: 0 0 3mm; }
figcaption { font-size: 8.6pt; color: var(--muted); margin-top: 1mm; }

/* Titelseite */
.titel { min-height: 247mm; display:flex; flex-direction:column; page-break-after: always; }
.titel .kicker { color: var(--accent); font-weight:600; letter-spacing:.5px;
                 text-transform:uppercase; font-size:9.5pt; }
.titel figure { margin-top: 4mm; }
.titel .meta { margin-top: auto; font-size: 10pt; color: var(--muted); }
.titel .meta b { color: var(--ink); }

/* Vorbehalts-Banner (rot umrandet) */
.banner { border:2.2px solid #c02626; background:#fbeaea; color:#7a1414;
          border-radius:6px; padding:4mm 5mm; margin:6mm 0 0; font-size:10.2pt; }
.banner .tag { font-weight:700; text-transform:uppercase; letter-spacing:.4px;
               color:#c02626; display:block; margin-bottom:1.2mm; }

/* Schritte */
.schritt { page-break-inside: avoid; margin: 0 0 7mm; padding-top: 2mm; }
.schritt-kopf { display:flex; align-items:center; gap:3.5mm; margin-bottom:3mm; }
.nr { flex:0 0 auto; width:10mm; height:10mm; border-radius:50%;
      background:var(--accent); color:#fff; font-weight:700; font-size:13pt;
      display:flex; align-items:center; justify-content:center; }
.schritt-kopf h2 { border:0; margin:0; padding:0; }
.grid2 { display:grid; grid-template-columns: 1fr 1fr; gap:3mm; margin-top:2mm; }

/* Material-Tabelle */
table { width:100%; border-collapse:collapse; margin: 0 0 3mm; }
th, td { text-align:left; vertical-align:top; padding:1.8mm 2.4mm;
         border-bottom:1px solid var(--line); font-size:10pt; }
th { background:#eef1f5; font-size:9pt; text-transform:uppercase;
     letter-spacing:.3px; color:var(--muted); }
tr { page-break-inside: avoid; }
td.menge { white-space:nowrap; font-weight:600; width:22mm; }

/* Hinweis-/Warnboxen */
.box { border-radius:5px; padding:2.6mm 3.4mm; margin:2.5mm 0 0; font-size:9.8pt; }
.box.warn { background:#fdf4d6; border:1.4px solid #e2b53a; }
.box.hinweis { background:#eaf1fb; border:1.4px solid #9dbbe6; }
.box .tag { font-weight:700; text-transform:uppercase; font-size:8.6pt;
            letter-spacing:.4px; margin-right:1.5mm; }
.box.warn .tag { color:#9a6d05; }
.box.hinweis .tag { color:#2a548f; }
ul { margin:0 0 2.4mm; padding-left:5mm; }

.section { page-break-inside: avoid; margin-bottom: 6mm; }

/* Laufende Fusszeile auf jeder gedruckten Seite */
.fuss { position: fixed; left:0; right:0; bottom:0; height:7mm;
        font-size:7.6pt; color:var(--muted);
        display:flex; justify-content:space-between; align-items:center;
        border-top:0.6px solid var(--line); background:#fff; padding:0 1mm; }
"""


def _img(src, cap):
    return (f'<figure><img src="{IMG_REL}/{src}" alt="{html.escape(cap)}">'
            f'<figcaption>{html.escape(cap)}</figcaption></figure>')


def _boxes(warn):
    out = []
    for kind, txt in warn:
        tag = "Warnung" if kind == "warn" else "Hinweis"
        out.append(f'<div class="box {kind}"><span class="tag">{tag}:</span>'
                   f'{html.escape(txt)}</div>')
    return "".join(out)


def render_html(m):
    h = m["hash"]
    datum = m["datum"]
    fuss = (f'Parameterstand {h} &nbsp;&bull;&nbsp; generiert am {datum} '
            f'&nbsp;&bull;&nbsp; VORABVERSION')

    # Titelseite
    titel = f"""
<section class="titel">
  <div class="kicker">Montageanleitung</div>
  <h1>Adapterrahmen Belluna-Dachlüfter<br>Challenger X150</h1>
  {_img("01_titel_explosion.png", "Bild 1: Explosionsansicht der Baugruppe – vier Segmente, Belluna-Platte, Dichtring und Clips.")}
  <div class="banner">
     <span class="tag">Vorabversion</span>
     Druck- und Montagefreigabe erst nach Kontrolle des realen Haubenfreigangs
     und einem PLA-Passform-Probedruck. Stand: PASS mit Vorbehalt.
  </div>
  <div class="meta">
     Parameterstand <b>{h}</b> (GEOM_REV {m['geom_rev']}) &nbsp;&bull;&nbsp;
     Erzeugungsdatum <b>{datum}</b>
  </div>
</section>
"""

    # Material & Werkzeug
    rows = "".join(f'<tr><td class="menge">{html.escape(mng)}</td>'
                   f'<td>{html.escape(txt)}</td></tr>'
                   for mng, txt in m["material"])
    material = f"""
<section class="section">
  <h2>Material und Werkzeug</h2>
  {_img("02_teile_uebersicht.png", "Bild 2: Einzelteile – Druckteil-Segment, Belluna-Platte mit Metallclips und Dichtring (Referenz).")}
  <table>
    <thead><tr><th>Menge</th><th>Position</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</section>
"""

    # Schritte
    schritte = []
    for s in m["steps"]:
        absaetze = "".join(f"<p>{html.escape(a)}</p>" for a in s["absaetze"])
        bild = _img(*s["bild"]) if s.get("bild") else ""
        extra = ""
        if s.get("bilder2"):
            extra = ('<div class="grid2">'
                     + "".join(_img(src, cap) for src, cap in s["bilder2"])
                     + "</div>")
        schritte.append(f"""
<section class="schritt">
  <div class="schritt-kopf"><div class="nr">{s['nr']}</div>
    <h2>{html.escape(s['titel'])}</h2></div>
  {bild}
  {absaetze}
  {_boxes(s['warn'])}
  {extra}
</section>
""")

    body = titel + material + "".join(schritte)
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<title>Montageanleitung Adapterrahmen {h}</title>
<style>{CSS}</style></head>
<body>
{body}
<div class="fuss"><span>{fuss}</span><span>Belluna-Adapterrahmen &middot; Challenger X150</span></div>
</body></html>
"""


# ---------------------------------------------------------------------------
# Chrome-PDF
# ---------------------------------------------------------------------------
def print_pdf(html_path, pdf_path):
    if not os.path.exists(CHROME):
        print(f"WARNUNG: Chrome nicht gefunden ({CHROME}) -- nur HTML erzeugt.",
              flush=True)
        return False
    cmd = [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
           "--virtual-time-budget=10000",
           f"--print-to-pdf={pdf_path}", f"file://{html_path}"]
    print("Chrome:", " ".join(cmd), flush=True)
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Chrome-STDERR:", res.stderr[-2000:], flush=True)
    return os.path.exists(pdf_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(OUT_MONTAGE, "manifest.json"))
    ap.add_argument("--no-pdf", action="store_true", help="nur HTML erzeugen")
    args = ap.parse_args()

    with open(args.manifest, encoding="utf-8") as fh:
        mf = json.load(fh)

    m = build_model(mf)
    html_doc = render_html(m)

    os.makedirs(OUT_MONTAGE, exist_ok=True)
    html_path = os.path.join(OUT_MONTAGE, f"montageanleitung_{m['hash']}.html")
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html_doc)
    print("HTML:", html_path, flush=True)

    pdf_path = os.path.join(OUT, f"montageanleitung_{m['hash']}.pdf")
    if args.no_pdf:
        print("PDF übersprungen (--no-pdf).", flush=True)
        return
    if print_pdf(html_path, pdf_path):
        print("PDF-ENDE:", pdf_path, flush=True)
    else:
        print("FEHLER: PDF wurde nicht erzeugt.", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
