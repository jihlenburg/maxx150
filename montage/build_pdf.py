"""PDF-Seite des Montageanleitungs-Generators (reines python3, KEIN FreeCAD).

Zweck
-----
Erzeugt aus dem Manifest zunächst HTML und druckt es via Chrome-Headless als
PDF. Standardziel ist ``build/documentation/<hash>/``.

Alle variablen Zahlen (M5-Länge, Klebstoffmenge, Wellenlänge, Schraubenanzahl …)
stammen aus dem Manifest -- als Fixtext gekennzeichnete Angaben (Tempern
80 °C/4 h, Aktivator beidseitig, RAL 9003 …) sind bewusst wörtlich.

Aufruf
------
    python3 montage/build_pdf.py [--manifest <pfad>] [--no-pdf]

Abhängigkeiten
--------------
- Google Chrome (Headless-PDF-Druck).
- Manifest + ``img/*.png`` aus den vorigen Dokumentationsstufen.

Endmarker im Log: ``PDF-ENDE: <pfad>``.
"""
import argparse
import html
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import params as PRM  # noqa: E402
from project_paths import manual_dir  # noqa: E402

OUT_MONTAGE = str(manual_dir(PRM.params_hash(PRM.P)))
IMG_REL = "img"
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

    material_parts = [
        ("4×", "Universal-Segment",
         f"Vier identische, fertig gedruckt angelieferte Bauteile; je ca. "
         f"{de(t['seg_mass_g'])} g. Vor der Montage auf Vollständigkeit, "
         "Ebenheit und Transportschäden prüfen."),
        (de(t["m5_count"]) + "×", "Stoßverschraubung",
         f"M5×{de(t['m5_length'])} DIN 912 + Sechskantmutter M5, SW "
         f"{de(t['nut_af'])}; Durchgang Ø{de(t['m5_through_d'])} mm."),
        ("8×", "Belluna-Platte → Adapter",
         f"Belluna ST {de(t['dach_screw_st_d'])}×{de(t['dach_screw_st_l'])} "
         "aus dem Lieferumfang; Kernloch 3 mm."),
        (de(t["dach_screw_count"]) + "×", "Adapter → Holzrahmen",
         f"Belluna ST {de(t['dach_screw_st_d'])}×{de(t['dach_screw_st_l'])} "
         "aus dem Lieferumfang; seitlich durch den Unterkragen, Kernloch 3 mm."),
        ("1 Satz", "Holzrahmen",
         f"Trockenes Nadelvollholz, ρk ≥ 350 kg/m³, Breite ≥ "
         f"{de(t['wood_frame_w'])} mm, Höhe = real gemessener Dachkern; "
         "Faser längs zu jeder Rahmenseite."),
        ("Werkzeug", "Vorbereitung und Montage",
         f"K240, MP Softpad Superfine, 3-mm-Bohrer, Drehmomentschlüssel "
         f"({de(t['torque_nm'])} Nm), Vierkantwelle {de(t['shaft_mm'])} mm."),
    ]

    material_system = [
        dict(rolle="Segmentstöße", menge="1× 60 g",
             produkt="WEICON RK-1300 Set · Art.-Nr. 10000118",
             warum="MMA-Strukturklebstoff für Hartkunststoffe und Fahrzeugbau; "
                   "hohe Schlag-, Schäl- und Scherfestigkeit. Sein "
                   "Festigkeitsoptimum bei 0,15–0,25 mm passt zur Fügepassung."),
        dict(rolle="Dach + Belluna", menge="2× 300 ml",
             produkt="Sikaflex-522 weiß (Standard)",
             warum="UV-/witterungsbeständiger STP-Dichtklebstoff mit "
                   "veröffentlichten Kennwerten. Rechnerisch stark auf 0,030 "
                   "MPa normal und 0,050 MPa Schub abgemindert. Zwei 10-mm-"
                   "Raupen tragen den vollständigen Lastfall ohne Anrechnung "
                   "der acht seitlichen Rückfallschrauben. Carloflex "
                   "410 UV weiß ist mit denselben Projektwerten eine "
                   "Belluna-konforme Alternative, sobald der passende "
                   "Kunststoffprimer prozesssicher festgelegt ist."),
        dict(rolle="522-Vorbehandlung", menge="je 1 Gebinde",
             produkt="Sika Cleaner P · Primer-507 · Aktivator-205",
             warum="Cleaner P + Primer-507 auf den lackfreien Kunststoff-"
                   "Klebeflächen als konservative Vorbehandlung; Cleaner P + Aktivator-205 "
                   "auf angeschliffenem GFK-Gelcoat."),
        dict(rolle="Holzrahmen", menge="1× 1,2 kg A+B",
             produkt="SikaForce-710 L35 + SikaForce-010",
             warum="2K-PUR-Paneelklebstoff, ausdrücklich für Holz/GFK mit "
                   "XPS-Kernen. Härtet auch in der geschlossenen Dachfuge "
                   "kontrolliert aus; professioneller Misch-/Pressprozess."),
        dict(rolle="Lack-Haftgrund", menge="1× 400 ml",
             produkt="Mipa 1K-Plastic-Grundierfiller-Spray · 213390000",
             warum="Füllender Haftvermittler für u. a. ABS, PC/ABS und GFK, "
                   "mit 2K-Decklacken überlackierbar."),
        dict(rolle="Weißer Decklack", menge="1 System",
             produkt="Mipa PUR HS RAL 9003 + 2K-MS-Härter MS 25",
             warum="2:1 Volumen. Wetter- und vergilbungsfester "
                   "Nutzfahrzeuglack; Weiß begrenzt die Solaraufheizung."),
    ]

    steps = [
        dict(nr=1, titel="Gelieferte Teile vorbereiten",
             bild=("03_fuegeflaechen.png",
                   "Bild 3: Fügeflächen einer Lappe (grün) – Überlappungs"
                   "schulter und Stirn."),
             absaetze=[
                 "Die vier fertig gedruckt gelieferten Segmente auspacken und "
                 "auf Vollständigkeit, Ebenheit, Maßhaltigkeit, Risse und "
                 "Transportschäden prüfen. Beschädigte Teile nicht montieren.",
                 "Die vier Halbüberlappungs-Fügeflächen (grün im Bild: Ober- "
                 "und Unterseite der Lappe sowie die Stirn) mit Schleifpapier K240 "
                 "aufrauen und gemäß WEICON-Datenblatt reinigen und trocknen.",
             ],
             warn=[("warn", "Keine ungeprüften Lösemittel verwenden. Kleb- und "
                            "Lackflächen strikt silikon-, fett- und staubfrei "
                            "halten.")]),
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
                       f"Bild 7: Gefügter Rahmen, alle {de(t['m5_count'])} M5-Positionen.")],
             absaetze=[
                 "WEICON RK-Aktivator auf BEIDE rauen Fügeflächen "
                 "auftragen und mindestens 5 min ablüften. Anschließend RK-1300 "
                 "auf eine Fügefläche geben. Im Bild kennzeichnet Blau den "
                 "Aktivatorschritt, Grün den danach aufgetragenen Klebstoff.",
                 f"Segmente fügen und SOFORT je Stoß {de(t['m5_per_joint'])}× M5×{de(t['m5_length'])} "
                 f"(DIN 912) mit Muttern einsetzen und mit {de(t['torque_nm'])} Nm "
                 f"anziehen. Die konstruktive Spaltbreite darf die 0,4-mm-Grenze "
                 f"des RK-1300 nicht überschreiten.",
                 "Reihenfolge: erst 2+2 Segmente zu zwei Halbrahmen fügen, dann "
                 "die beiden Halbrahmen. Anschließend 24 h aushärten lassen.",
                 f"Nach dem Anziehen die {de(t['m5_count'])} M5-Kopftaschen bündig mit RK-1300 "
                 "versiegeln (offene Taschen wären Wasserreservoirs oben).",
             ],
             warn=[("warn", "RK-1300 ist für Referenzkunststoffe dokumentiert, "
                            "den gelieferten Druckteilwerkstoff aber nicht ausdrücklich. Die Lastpfadrechnung setzt "
                            "deshalb nur 0,50 statt 6 MPa auf ABS an und prüft "
                            "zusätzlich den vollständigen 480-N-Pfad über M5.")]),
        dict(nr=3, titel="Weiße Schutzlackierung (Pflicht)",
             bild=("08_maskierung_lack.png",
                   "Bild 8: Unterseite – Doppelraupe, Mittelkanal und Abstandspads (gelb) beim "
                   "Lackieren abkleben."),
             absaetze=[
                 "Die Segmente werden mit schwarzer Rohteiloberfläche geliefert; "
                 "die weiße Lackierung ist deshalb immer erforderlich. Nach dem Fügen die Baugruppe "
                 "für 60 min bei 60 °C ausgasen lassen, wie es Mipa für die "
                 "Kunststoffvorbereitung fordert, und vollständig abkühlen lassen.",
                 "Alle späteren Klebe- und Belüftungszonen abkleben: beide "
                 "Kleberführungen, Mittelkanal, Abstandspads sowie die obere Auflage der Belluna-Platte. Mit "
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
             warn=[("warn", "Der Werkstoff der gelieferten Segmente steht nicht "
                            "ausdrücklich in der Mipa-Primerliste. Der Lack ist "
                            "deshalb kein struktureller Lastpfad und muss jährlich "
                            "kontrolliert und bei Schäden sofort ausgebessert "
                            "werden. 2K-PUR nur im Lackierfachbetrieb mit "
                            "geeigneter Absaugung und Schutzmaßnahmen verarbeiten."),
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
                 "und mit Isopropanol reinigen. Ausschnitt messen (Soll "
                 f"{de(t['cutout_w'])}×{de(t['cutout_w'])}).",
                 f"Rund um den Ausschnitt den XPS-Randstreifen ausräumen. Einen "
                 f"Holzrahmen aus trockenem Nadelvollholz (ρk ≥ 350 kg/m³) "
                 f"vorbereiten: Höhe = real gemessener Dachkern, Breite ≥ "
                 f"{de(t['wood_frame_w'])} mm, Faser längs zur jeweiligen "
                 f"Rahmenseite. Klebeflächen "
                 f"an GFK, XPS und Holz sauber, trocken, fett- und staubfrei halten.",
                 "SikaForce-710 L35 (Komponente A vorher aufrühren) mit "
                 "SikaForce-010 (Komponente B) homogen mischen: 100:25 nach "
                 "Volumen bzw. 100:19 nach Gewicht. Bei 23 °C beträgt die "
                 "Topfzeit 35 min; vor Ablauf der halben Topfzeit auftragen und "
                 "den Holzrahmen hohlraumfrei einsetzen.",
                 "Mit ebenen Zulagen pressen und bei 23 °C mindestens 125 min "
                 "nicht entlasten. Den konkreten Pressdruck am realen Dachaufbau "
                 "ermitteln; er muss unter der Druckfestigkeit des XPS-Kerns "
                 "bleiben. Der Rahmen ist vollflächig verklebter Lastverteiler "
                 "und Kompressionsschutz.",
             ],
             warn=[("hinweis", "Warum SikaForce-710 L35: Sika spezifiziert genau "
                               "die vorhandene Werkstoffkette Holz/GFK mit "
                               "expandiertem oder extrudiertem Polystyrol. Das "
                               "reaktive 2K-System ist nicht auf Luftfeuchtigkeit "
                               "in der geschlossenen Sandwichfuge angewiesen."),
                   ("warn", "Nur SikaForce-710 L35 mit SikaForce-010 durch "
                            "erfahrene Anwender gemäß Sicherheitsdatenblatt "
                            "verarbeiten. Gleichmäßig und hohlraumarm auftragen; "
                            "der Pressdruck muss unter der Kern-Druckfestigkeit bleiben. "
                            f"Der {de(t['kragen_outer_w'])}-mm-Unterkragen braucht "
                            f"rundum ≥ {de(t['bot_kragen_clear'])} mm Luft; den "
                            "echten Ausschnitt vor dem Setzen kontrollieren.")]),
        dict(nr=5, titel="Adapter kleben, setzen und sichern",
             bild=("12_kleberaupe.png",
                   "Bild 12: Zwei grüne Kleberführungen; die äußere bleibt geschlossen, "
                   "die innere besitzt acht geformte Belüftungsbrücken."),
             bilder2=[("10_aufsetzen.png",
                       "Bild 10: Rahmen mit Unterkragen über dem Ausschnitt."),
                      ("11_hybrid_dachinterface.png",
                       "Bild 11: Acht seitliche Rückfallschrauben (rot) gehen "
                       "geschützt durch den Unterkragen in den Holzrahmen.")],
             absaetze=[
                 "Die lackfreie Kunststoff-Klebezone sehr fein anschleifen, mit "
                 "Sika Cleaner P reinigen und Sika Primer-507 als konservative "
                 "ABS-Analogie gemäß aktuellem Produktdatenblatt auftragen. "
                 "Das angeschliffene GFK-Gelcoat mit Cleaner P reinigen und "
                 "Sika Aktivator-205 gemäß aktuellem Produktdatenblatt auftragen.",
                 f"Sikaflex-522 weiß nominal ca. {de(t['bead_ml'])} ml in die "
                 f"beiden {de(t['groove_w'])}-mm-Kleberführungen legen (Bild 12). "
                 "Die äußere Raupe muss wasserdicht und ohne Unterbrechung geschlossen sein. "
                 f"Die innere Raupe an den {de(t['groove_vent_count'])} geformten "
                 "Brücken sauber unterbrechen; den Mittelkanal nicht überfüllen.",
                 "Rahmen mit dem Unterkragen in den Ausschnitt einsetzen (Bild 10) "
                 "und lagerichtig ausrichten. Gleichmäßig nur so weit anpressen, "
                 f"bis die {de(t['spacer_pad_count'])} Abstandspads den vorgesehenen "
                 f"{de(t['glue_gap'])}-mm-Dachabstand definieren. In den "
                 f"{de(t['groove_d'])}-mm-Führungen beträgt die wirksame "
                 f"Raupenhöhe damit {de(t['bondline_thickness'])} mm; anschließend mit einer ebenen, nicht "
                 "beschädigenden Montagehilfe gegen Verschieben sichern. Keine "
                 "Zwingen, Spanngurte oder vertikale Verschraubung verwenden; "
                 "die Pads sind Anschläge, keine Klemmpunkte.",
                 f"Je Seite zwei ST {de(t['dach_screw_st_d'])}×{de(t['dach_screw_st_l'])} "
                 f"durch die Kragenlöcher in den Holzrahmen setzen – insgesamt "
                 f"{de(t['dach_screw_count'])}, Kernloch 3 mm, "
                 f"Drehmoment {de(t['torque_nm'])} Nm (Bild 11). Die Schrauben "
                 "sichern mechanisch, werden aber rechnerisch nicht zur Klebung addiert. "
                 "Schraubdurchtritte nach dem Anziehen mit Sikaflex-522 abdichten. "
                 "Bis zur vollständigen Durchhärtung gemäß aktuellem "
                 "Sikaflex-522-Produktdatenblatt weder weiter montieren noch "
                 "fahren oder belasten; Temperatur, Luftfeuchte und die zwei "
                 "Raupen bei der Wartezeit berücksichtigen.",
                 "Außen umlaufend mit demselben gewählten Produkt eine geschlossene "
                 "Kehlnaht ziehen.",
             ],
             warn=[("hinweis", "Warum 522 als Standard: Carloflex 410 UV ist "
                               "mit >1,8 MPa Zugfestigkeit und >450 % Dehnung "
                               "rechnerisch eine gleichwertig abgeminderte, "
                               "Belluna-konforme Alternative. Sika dokumentiert "
                               "den Vorbehandlungsweg jedoch namentlich; das "
                               "Carloflex-TDS nennt den Kunststoffprimer nicht. "
                               "Je Baugruppe nur ein vollständiges System "
                               "verwenden."),
                   ("warn", f"Die {de(t['spacer_pad_count'])} Abstandspads mit "
                            f"{de(t['spacer_pad_radial'])} × {de(t['spacer_pad_tangential'])} mm Kontaktmaß definieren "
                            f"{de(t['glue_gap'])} mm "
                            f"Dachabstand und {de(t['bondline_thickness'])} mm Raupenhöhe – den Kleber NICHT auspressen "
                            f"(Thermik-Elastikfuge). Äußere Dichtungsraupe, "
                            f"Mittelkanal und innere Ventöffnungen vor dem "
                            f"Aushärten visuell vollständig kontrollieren. "
                            "Die unteren Schrauben sind eine physische "
                            "Rückfallebene, aber ohne typgeprüften Holz-/Dachpfad "
                            "kein angerechneter Tragfähigkeitsnachweis.")]),
        dict(nr=6, titel="Belluna-Platte montieren",
             bild=("13_platte_schrauben.png",
                   "Bild 13: Belluna-Platte mit silbernen Metallclips; "
                   "ST4,2-Schrauben (rot) seitlich durch den Platten-Kragen "
                   "in die Adapter-Innenwand."),
             absaetze=[
                 "Die lackfreien Klebezonen an Adapter und Belluna-Platte sehr "
                 "fein anschleifen, mit Sika Cleaner P reinigen und mit Sika "
                 "Primer-507 als ABS-Analogie gemäß aktuellem Datenblatt "
                 "vorbehandeln. Sikaflex-522 in die Klebekanäle der "
                 "Plattenunterseite auftragen "
                 "und die Platte mittig aufsetzen (der Kragen taucht in die "
                 "Öffnung).",
                 f"Die ST {de(t['plate_screw_d'])}×{de(t['plate_screw_l'])} seitlich "
                 f"durch den Platten-Kragen in die Adapter-Innenwand setzen "
                 f"(3-mm-Kernloch vorbohren, Bild 13). Jede Seite bietet universelle "
                 f"Vollmaterialrippen für beide Belluna-Varianten (±140 und "
                 f"±165 mm).",
             ],
             warn=[("warn", "Der gelieferte Druckteilwerkstoff ist in der Sika-Tabelle nicht "
                             "ausdrücklich genannt. Deshalb gelten die Klebwerte in der "
                             "Lastpfadrechnung mit bis zu Faktor 60 abgemindert "
                             "und das Ergebnis bleibt PASS_ASSUMPTION_BASED, "
                             "nicht herstellerfreigegeben."),
                   ("hinweis", "Nur die acht äußeren Belluna-Positionen "
                               "verwenden. Die zwei Mittellöcher der "
                               "3-Loch-Seiten liegen auf Segmentstößen und "
                               "bleiben frei.")]),
        dict(nr=7, titel="Lüfter einsetzen",
             bild=("14_fertig.png",
                   "Bild 14: Fertige Baugruppe – Adapter, Platte und Dichtring."),
             absaetze=[
                 f"Vierkantwelle {de(t['shaft_mm'])} mm einsetzen "
                 f"(effektive Wandstärke {de(t['effective_wall_mm'])} mm = Dach "
                 f"{de(t['roof_t'])} mm + Erhöhung {de(t['h_raise'])} mm).",
                 "Lüfter-Sockel in die Clips einsetzen und Feder-/Sicherungselemente "
                 "gemäß Belluna-Einbauanleitung montieren.",
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
                 "Lackprüfung ist beim schwarzen Grundkörper immer "
                 "Pflicht; Beschädigungen bis auf den Kunststoff fachgerecht ausbessern.",
             ],
             warn=[]),
    ]

    return dict(hash=h, datum=datum, geom_rev=mf["geom_rev"],
                material_parts=material_parts, material_system=material_system,
                steps=steps, text=t)


# ---------------------------------------------------------------------------
# HTML/CSS
# ---------------------------------------------------------------------------
CSS = """
:root {
  --ink:#15212b; --muted:#5b6872; --quiet:#eef3f6; --line:#cbd5dc;
  --blue:#006aa6; --blue-dark:#004e7c; --blue-soft:#e8f2f8;
  --amber:#e6a400; --amber-soft:#fff5d8; --red:#bd2d2d; --red-soft:#fdecec;
}
* { box-sizing:border-box; }
@page { size:A4; margin:12.5mm 14mm 13mm; }
html, body { margin:0; padding:0; }
body {
  font-family:"Avenir Next", "Noto Sans", Arial, sans-serif;
  color:var(--ink); font-size:9.25pt; line-height:1.42;
  -webkit-print-color-adjust:exact; print-color-adjust:exact;
  font-variant-numeric:tabular-nums;
}
h1, h2, h3, p { margin-top:0; }
h1 { font-size:27pt; line-height:1.04; letter-spacing:-.55px; margin-bottom:4mm; }
h2 { font-size:18pt; line-height:1.12; letter-spacing:-.2px; margin:0; color:var(--ink); }
h3 { font-size:10.5pt; line-height:1.25; margin:0 0 1mm; }
p { margin-bottom:2.2mm; }
img { display:block; max-width:100%; height:auto; }
figure { margin:0; }
figcaption { color:var(--muted); font-size:7.5pt; line-height:1.3; margin-top:1.2mm; }
.page { break-after:page; page-break-after:always; min-height:258mm; }
.eyebrow { color:var(--blue); font-size:8pt; font-weight:700; letter-spacing:1px;
           text-transform:uppercase; }
.lead { color:var(--muted); font-size:10.2pt; line-height:1.45; max-width:145mm; }
.page-head { border-top:2.2mm solid var(--blue); padding-top:3.5mm; margin-bottom:4mm; }
.page-head .eyebrow { display:block; margin-bottom:1.2mm; }

/* Titelseite: Identifikation, Bild, Freigabestatus. */
.titel { min-height:258mm; display:flex; flex-direction:column;
         break-after:page; page-break-after:always; }
.titel .kicker { color:var(--blue); font-weight:700; letter-spacing:1.2px;
                 text-transform:uppercase; font-size:8pt; margin-bottom:2mm; }
.titel .subtitle { color:var(--muted); font-size:11pt; margin-bottom:5mm; }
.titel figure img { width:100%; height:125mm; object-fit:cover; border-radius:2mm; }
.titel .banner { margin-top:5mm; }
.titel .meta { margin-top:auto; display:grid; grid-template-columns:1fr 1fr 1fr;
               border-top:1px solid var(--line); padding-top:3mm; color:var(--muted);
               font-size:8pt; gap:4mm; }
.titel .meta b { color:var(--ink); display:block; font-size:9.5pt; margin-top:.6mm; }

.banner { border-left:2mm solid var(--red); background:var(--red-soft);
          color:#6f1b1b; border-radius:1mm; padding:3.4mm 4mm; font-size:9.2pt; }
.banner .tag { color:var(--red); display:block; font-size:7.6pt; font-weight:800;
               letter-spacing:.9px; text-transform:uppercase; margin-bottom:.8mm; }

/* Materialseiten. */
.material-hero { display:grid; grid-template-columns:1.35fr .65fr; gap:5mm;
                 align-items:stretch; margin-bottom:4mm; }
.material-hero figure img { width:100%; height:78mm; object-fit:cover; border-radius:1.5mm; }
.spec-strip { background:var(--blue-soft); border-radius:1.5mm; padding:4mm;
              display:flex; flex-direction:column; justify-content:space-between; }
.spec { border-bottom:1px solid #bad2e1; padding-bottom:3mm; }
.spec:last-child { border:0; padding-bottom:0; }
.spec strong { display:block; color:var(--blue-dark); font-size:15pt; line-height:1.1; }
.spec span { color:var(--muted); font-size:7.7pt; }
.parts-table { width:100%; border-collapse:collapse; }
.parts-table th { background:var(--ink); color:#fff; text-align:left; padding:2mm 2.5mm;
                  font-size:7.3pt; text-transform:uppercase; letter-spacing:.6px; }
.parts-table td { border-bottom:1px solid var(--line); padding:2.2mm 2.5mm;
                  vertical-align:top; font-size:8.4pt; }
.parts-table .qty { width:22mm; color:var(--blue-dark); font-weight:700; white-space:nowrap; }
.parts-table .item { width:49mm; font-weight:700; }
.process-line { display:grid; grid-template-columns:repeat(4, 1fr); gap:2mm;
                margin:1mm 0 4mm; }
.process-line div { background:var(--blue); color:#fff; border-radius:1mm; padding:2.6mm;
                    text-align:center; font-size:7.8pt; font-weight:700; position:relative; }
.process-line div:not(:last-child)::after { content:"›"; position:absolute; right:-2.1mm;
                    top:1.2mm; z-index:2; color:var(--blue-dark); font-size:15pt; }
.material-cards { display:grid; grid-template-columns:1fr 1fr; gap:3mm; }
.material-card { border:1px solid var(--line); border-radius:1.5mm; padding:3mm;
                 break-inside:avoid; min-height:44mm; }
.material-card .role { color:var(--blue); font-size:7.2pt; font-weight:800;
                       letter-spacing:.65px; text-transform:uppercase; }
.material-card .amount { float:right; color:var(--muted); font-size:7.4pt; }
.material-card .product { font-size:10.2pt; font-weight:700; line-height:1.23;
                          margin:1.2mm 0 1.5mm; }
.material-card .why { color:var(--muted); font-size:8.2pt; line-height:1.38; }
.material-card:last-child { grid-column:1 / -1; min-height:34mm; }
.qualification { margin-top:3mm; }

/* Arbeitsschritte: eine abgeschlossene Orientierungseinheit pro Seite. */
.step-page { break-before:page; page-break-before:always; break-after:page;
             page-break-after:always; min-height:258mm; break-inside:avoid; }
.step-page.step-7 { break-after:auto; page-break-after:auto; min-height:0; }
.step-page.step-8 { break-before:auto; page-break-before:auto; min-height:0;
                    break-after:auto; page-break-after:auto;
                    margin-top:6mm; padding-top:5mm; border-top:1px solid var(--line); }
.step-head { display:grid; grid-template-columns:12mm 1fr auto; gap:3mm;
             align-items:center; border-top:2.2mm solid var(--blue);
             padding-top:3.5mm; margin-bottom:4mm; }
.step-no { width:10mm; height:10mm; border-radius:50%; background:var(--blue);
           color:#fff; display:flex; align-items:center; justify-content:center;
           font-size:12pt; font-weight:700; }
.step-kicker { color:var(--muted); font-size:7.4pt; font-weight:700;
               letter-spacing:.6px; text-transform:uppercase; }
.step-layout { display:grid; grid-template-columns:1.12fr .88fr; gap:5mm;
               align-items:start; }
.step-hero img { width:100%; max-height:102mm; aspect-ratio:4/3; object-fit:cover;
                 border-radius:1.5mm; }
.actions { list-style:none; margin:0; padding:0; counter-reset:action; }
.actions li { counter-increment:action; position:relative; padding:0 0 3mm 8mm;
              margin:0 0 3mm; border-bottom:1px solid var(--line); }
.actions li:last-child { border-bottom:0; margin-bottom:0; }
.actions li::before { content:counter(action); position:absolute; left:0; top:.2mm;
                      width:5.5mm; height:5.5mm; border-radius:50%;
                      background:var(--quiet); color:var(--blue-dark); font-size:7pt;
                      font-weight:800; display:flex; align-items:center; justify-content:center; }
.callouts { display:grid; grid-template-columns:1fr; gap:2.5mm; margin-top:4mm; }
.callouts.two { grid-template-columns:1fr 1fr; }
.box { border-left:1.4mm solid; border-radius:1mm; padding:2.6mm 3mm;
       font-size:8.2pt; line-height:1.4; break-inside:avoid; }
.box.warn { border-color:var(--amber); background:var(--amber-soft); }
.box.hinweis { border-color:var(--blue); background:var(--blue-soft); }
.box .tag { display:block; font-size:7pt; font-weight:800; letter-spacing:.7px;
            text-transform:uppercase; margin-bottom:.8mm; }
.box.warn .tag { color:#8a6200; }
.box.hinweis .tag { color:var(--blue-dark); }
.thumb-grid { display:grid; gap:3mm; margin-top:4mm; }
.thumb-grid.count-2 { grid-template-columns:repeat(2, 1fr); }
.thumb-grid.count-3 { grid-template-columns:repeat(3, 1fr); }
.thumb-grid img { width:100%; height:51mm; object-fit:cover; border-radius:1.2mm; }
.step-2 .thumb-grid img { height:43mm; }
.step-7 .step-hero img { max-height:79mm; }
.step-8 .step-layout { display:block; }
.step-8 .actions { display:grid; grid-template-columns:repeat(3, 1fr); gap:3mm; }
.step-8 .actions li { border:0; background:var(--quiet); border-radius:1mm;
                      padding:3mm 3mm 3mm 9mm; margin:0; min-height:25mm; }
.step-8 .actions li::before { left:2.5mm; top:3mm; background:#fff; }

/* Laufende Fußzeile. */
.fuss { position:fixed; left:0; right:0; bottom:0; height:6mm;
        border-top:.5px solid var(--line); background:#fff; color:var(--muted);
        display:flex; justify-content:space-between; align-items:center;
        font-size:6.7pt; padding-top:1mm; }
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
  <p class="subtitle">Vier identische, fertig gelieferte Segmente · 28 mm Erhöhung · weiße Schutzlackierung</p>
  {_img("01_titel_explosion.png", "Bild 1: Explosionsansicht der Baugruppe – vier Segmente, Belluna-Platte, Dichtring und Clips.")}
  <div class="banner">
     <span class="tag">Vorabversion</span>
     Montagefreigabe erst nach Kontrolle des realen Haubenfreigangs und der
     Passform am Fahrzeug. Stand: PASS mit Vorbehalt.
  </div>
  <div class="meta">
     <span>Parameterstand<b>{h}</b></span>
     <span>Geometrie<b>GEOM_REV {m['geom_rev']}</b></span>
     <span>Erzeugt<b>{datum}</b></span>
  </div>
</section>
"""

    # Vorbereitung 1/2: Bauteile und Hardware
    rows = "".join(
        f'<tr><td class="qty">{html.escape(mng)}</td>'
        f'<td class="item">{html.escape(item)}</td>'
        f'<td>{html.escape(detail)}</td></tr>'
        for mng, item, detail in m["material_parts"])
    material_parts = f"""
<section class="page material-parts">
  <header class="page-head">
    <span class="eyebrow">Vorbereitung · 1 von 2</span>
    <h2>Bauteile und Befestigung</h2>
    <p class="lead">Vier fertig gedruckt gelieferte Universal-Segmente. Die Montage beginnt mit der Wareneingangsprüfung; je acht Belluna-Schrauben verbinden Originalplatte und Holzrahmen mit dem Adapter. Die unteren Schrauben bleiben rechnerisch unberücksichtigte Reserve.</p>
  </header>
  <div class="material-hero">
    {_img("02_teile_uebersicht.png", "Bild 2: Universal-Segment und Belluna-Originalplatte mit Metallclips und Dichtring.")}
    <div class="spec-strip">
      <div class="spec"><strong>4×</strong><span>identisches Universal-Segment</span></div>
      <div class="spec"><strong>28 mm</strong><span>Erhöhung einschließlich Klebespalt</span></div>
      <div class="spec"><strong>8×</strong><span>ST4,2×25 Platte → Adapter</span></div>
    </div>
  </div>
  <table class="parts-table">
    <thead><tr><th>Menge</th><th>Position</th><th>Festlegung</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</section>
"""

    # Vorbereitung 2/2: chemische Prozesskette mit Auswahlgrund
    cards = "".join(
        '<article class="material-card">'
        f'<span class="amount">{html.escape(x["menge"])}</span>'
        f'<div class="role">{html.escape(x["rolle"])}</div>'
        f'<div class="product">{html.escape(x["produkt"])}</div>'
        f'<div class="why">{html.escape(x["warum"])}</div>'
        '</article>' for x in m["material_system"])
    material_system = f"""
<section class="page material-system">
  <header class="page-head">
    <span class="eyebrow">Vorbereitung · 2 von 2</span>
    <h2>Kleb-, Dicht- und Lacksystem</h2>
    <p class="lead">Jede Chemie hat genau eine Aufgabe. Produkte werden nicht durch generische Alternativen ersetzt oder untereinander gemischt.</p>
  </header>
  <div class="process-line">
    <div>Segmente fügen</div><div>Weiß lackieren</div>
    <div>Holzrahmen setzen</div><div>Dach abdichten</div>
  </div>
  <div class="material-cards">{cards}</div>
  <div class="box warn qualification"><span class="tag">Rechenbasis und Restrisiko</span>
    Zerstörende Originalsubstrat-Coupons stehen derzeit nicht zur Verfügung. Deshalb rechnet das Projekt mit stark abgeminderten Grenzflächenwerten: oben trägt die vollständige Acht-Schrauben-Gruppe, unten die Doppelraupe allein; die acht Holzschrauben werden nicht angerechnet. Für den Holzrahmen zählt nur eine Holz/GFK-Fläche. Ergebnis: PASS_ASSUMPTION_BASED, keine Herstellerfreigabe.
  </div>
</section>
"""

    # Schritte
    schritte = []
    for s in m["steps"]:
        absaetze = ("<ol class=\"actions\">"
                    + "".join(f"<li>{html.escape(a)}</li>" for a in s["absaetze"])
                    + "</ol>")
        bild = f'<div class="step-hero">{_img(*s["bild"])}</div>' if s.get("bild") else ""
        extra = ""
        if s.get("bilder2"):
            count = len(s["bilder2"])
            extra = (f'<div class="thumb-grid count-{count}">'
                     + "".join(_img(src, cap) for src, cap in s["bilder2"])
                     + "</div>")
        callouts = ""
        if s["warn"]:
            extra_class = " two" if len(s["warn"]) == 2 else ""
            callouts = f'<div class="callouts{extra_class}">{_boxes(s["warn"])}</div>'
        schritte.append(f"""
<section class="step-page step-{s['nr']}">
  <header class="step-head">
    <div class="step-no">{s['nr']}</div>
    <h2>{html.escape(s['titel'])}</h2>
    <span class="step-kicker">Montage</span>
  </header>
  <div class="step-layout">
    {bild}
    <div class="step-copy">{absaetze}</div>
  </div>
  {callouts}
  {extra}
</section>
""")

    body = titel + material_parts + material_system + "".join(schritte)
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<title>Montageanleitung Adapterrahmen {h}</title>
<style>{CSS}</style></head>
<body>
{body}
<div class="fuss"><span>{fuss}</span><span>Belluna-Adapterrahmen &nbsp;·&nbsp; Challenger X150</span></div>
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

    out_montage = os.path.dirname(os.path.abspath(args.manifest))
    with open(args.manifest, encoding="utf-8") as fh:
        mf = json.load(fh)

    m = build_model(mf)
    html_doc = render_html(m)

    os.makedirs(out_montage, exist_ok=True)
    html_path = os.path.join(out_montage, f"montageanleitung_{m['hash']}.html")
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html_doc)
    print("HTML:", html_path, flush=True)

    pdf_path = os.path.join(out_montage, f"montageanleitung_{m['hash']}.pdf")
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
