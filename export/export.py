"""Export der Druck-/Archivdateien + auto-generierte Montagenotiz (Spec §7)."""
import re
from pathlib import Path

import MeshPart
from FreeCAD import Vector

import params as PRM
from model.frame import build_frame
from model.segments import build_segments


def _write_mesh(shape, path: Path):
    mesh = MeshPart.meshFromShape(shape, LinearDeflection=0.05,
                                  AngularDeflection=0.35, Relative=False)
    mesh.write(str(path))


def _normalize_step_header(path: Path) -> None:
    """Entfernt den laufabhängigen FreeCAD-Zeitstempel aus dem STEP-Header.

    OpenCascade schreibt bei identischer Geometrie sonst bei jedem Lauf andere
    Bytes. Der neutrale Zeitstempel macht SHA-256-Manifeste reproduzierbar,
    ohne Geometrie- oder Produktdaten zu verändern.
    """
    text = path.read_text(encoding="utf-8")
    normalized, count = re.subn(
        r"(FILE_NAME\('[^']*',)'[^']*'", r"\1'1970-01-01T00:00:00'", text, count=1
    )
    if count != 1:
        raise ValueError(f"STEP-Header in {path} nicht erkannt")
    # OpenCascade setzt in einigen Context-Zeilen bedeutungslose Leerzeichen
    # vor dem Zeilenende. Sie sind nicht semantisch, stoeren aber Patch-Checks
    # und bytegenaue Reproduzierbarkeit zwischen Exporterversionen.
    keep_final_newline = normalized.endswith("\n")
    normalized = "\n".join(line.rstrip() for line in normalized.splitlines())
    if keep_final_newline:
        normalized += "\n"
    path.write_text(normalized, encoding="utf-8")


def _print_oriented(shape):
    """Kopie fuer STL/3MF mit der Deckflaeche auf Z=0.

    STEP bleibt in Einbaulage. Die Mesh-Exporte werden dagegen bereits so
    ausgerichtet, wie die Montagenotiz den FDM-Druck verlangt: 180 Grad um X,
    danach auf das Druckbett verschoben. Das Original-Shape bleibt unveraendert.
    """
    printable = shape.copy()
    printable.rotate(Vector(0, 0, 0), Vector(1, 0, 0), 180)
    printable.translate(Vector(0, 0, -printable.BoundBox.ZMin))
    return printable


DIN912_M5_LENGTHS = (20, 25, 30, 35, 40, 45, 50)


def _m5_bolt_length(p: PRM.Params) -> int:
    """M5-Länge: Klemmlänge + Muttertasche + Überstand, aufgerundet auf die
    nächste DIN-912-Normlänge."""
    raw = p.H_RAISE - p.GLUE_GAP + p.JOINT_NUT_T + 2
    for length in DIN912_M5_LENGTHS:
        if length >= raw:
            return length
    raise ValueError(f"M5-Länge {raw:.1f} mm übersteigt die Normlängen-Tabelle "
                     f"(max {DIN912_M5_LENGTHS[-1]})")


def _montagenotiz(p: PRM.Params, h: str) -> str:
    L, W = PRM.outer_dims(p)
    bead_ml = PRM.groove_adhesive_volume_ml(p)
    return f"""# Montagenotiz Adapterrahmen (Parameterstand {h})

## Druck (1 Universal-Segment, **4x identisch drucken**)
- Material: **{p.MATERIAL_NAME}**, 1,75 mm, 750-g-Spule. Schwarz ist nur die
  Rohteilfarbe; vor dem Dacheinbau ist RAL 9003 Signalweiß zwingend.
- Datenlage: Würths mechanische Werte stammen aus Halbzeug, nicht aus
  FDM-Probekörpern. E={p.E_BASE:.0f} MPa und Zug={p.SIGMA_BASE:.0f} MPa sind
  konservative Projektannahmen. Da XY-/Z-Coupons aktuell nicht realistisch
  verfügbar sind, werden diese Werte nicht hochgestuft; Status PROTOTYPE_ONLY.
- Würth-Profil: Düse **250–270 °C**, max. **12 mm³/s**, geschlossener
  temperierter Bauraum und **gehärtete Düse** (15 % GF, abrasiv). Bett und
  Trocknung nach dem der Charge beiliegenden Datenblatt kalibrieren.
- Würth nennt nur HDT/B(0,45 MPa) **{p.HDT_045:.0f} °C**, keinen
  1,82-MPa-Wert. T_MAX **{p.T_MAX:.0f} °C** bleibt mit Abminderung angesetzt;
  der weiße Decklack ist Teil der Thermikauslegung.
- Orientierung: **Deckfläche nach unten**; Layerhöhe 0,20 mm als Startwert,
  mindestens **4 Perimeter**, **100 % Infill**, keine Supports in Kammern oder
  Schraubkanälen. Alle vier Teile aus `universal_segment_x4`, nur um Z drehen,
  **nicht spiegeln oder umdrehen**.
- **PFLICHT gegen Verzug**: geschlossener Bauraum, **Brim ≥ 10 mm**, keine
  Zugluft, im geschlossenen Bauraum abkühlen. Erst ein Segment drucken und
  Ebenheit/Öffnungsmaß prüfen. Kein pauschales Tempern: Würth nennt für diesen
  Artikel keinen allgemeinen Temperprozess.
## Fügen — WEICON RK-1300
- Rohes ASA-GF K240 anschleifen. **WEICON RK-1300, 60-g-Set,
  Art.-Nr. 10000118** verwenden. Wegen der rauen/porösen FDM-Flächen den
  Aktivator beidseitig auftragen, mindestens 5 min ablüften, RK-1300 auf eine
  Seite geben, fügen und je Stoß mit **{len(p.JOINT_BOLT_OFFS)}× M5x{_m5_bolt_length(p)} DIN 912 +
  Muttern** bei 0,8 Nm sichern. Endfestigkeit nach 24 h.
- Alle {PRM.joint_bolt_count(p)} M5-Kopftaschen bündig mit RK-1300 versiegeln. RK-1300 wurde gewählt,
  weil WEICON den MMA-Strukturklebstoff für Hartkunststoffe/Fahrzeugbau sowie
  hohe Schlag-, Schäl- und Scherfestigkeit spezifiziert. ASA-GF ist nicht
  einzeln gelistet; die Rechnung setzt deshalb nur 0,50 statt 6 MPa an und
  prüft den vollständigen 480-N-Pfad zusätzlich über M5.

## Weiße Schutzlackierung — Pflicht
- Nach dem Fügen spätere Klebezonen roh lassen und abkleben: beide unteren
  Kleberführungen samt Mittelkanal/Abstandspads und obere Belluna-Auflage. Lack ist
  kein Klebgrund.
- Haftgrund: **Mipa 1K-Plastic-Grundierfiller-Spray**, hellgrau, 400 ml,
  Art.-Nr. **213390000**. Mipa-Untergrundvorbereitung befolgen; 2–3 dünne
  Spritzgänge, 15–40 µm, nach 15–20 min überlackierbar.
- Decklack: **Mipa PUR HS 2K-PUR-Acryl-Fahrzeuglack, RAL 9003 Signalweiß,
  glänzend**, mit **Mipa 2K-MS-Härter MS 25**, **2:1 nach Volumen**.
  1–2 Spritzgänge, 50–60 µm, 5–8 min Zwischenablüftung; bei 20 °C nach
  12–24 h montagefest. Verarbeitung im Lackierfachbetrieb/Spritzkabine.
- Wahlgrund: Der füllende Primer ist für u. a. ABS, PC/ABS und GFK sowie
  2K-Decklacke ausgewiesen; der PUR-HS-Decklack für Nutzfahrzeuge ist wetter-
  und vergilbungsfest sowie chemisch/mechanisch beständig. ASA-GF fehlt in der
  Primerliste. Der Lack ist deshalb kein struktureller Lastpfad; jährlich
  kontrollieren und Schäden sofort fachgerecht ausbessern.

## Dach-Sandwich und Dichtheit
- Mini-Heki und Altbett entfernen. Den XPS-Randstreifen ausräumen und einen
  Rahmen aus trockenem Nadelvollholz (ρk ≥ 350 kg/m³, Höhe Kern, Breite ≥
  30 mm, Faser längs zu jeder Rahmenseite) mit
  **SikaForce-710 L35 + SikaForce-010** vollflächig einsetzen. A:B = 100:25
  nach Volumen bzw. 100:19 nach Gewicht; A vorher aufrühren, homogen mischen,
  bei 23 °C vor der halben Topfzeit auftragen und mindestens 125 min mit
  ebenen Zulagen pressen. Den Pressdruck gleichmäßig und unter der
  Druckfestigkeit des Kerns halten. Wahlgrund: Sika
  spezifiziert genau Holz/GFK mit EPS/XPS für Sandwichpaneele; das 2K-System
  härtet auch in der geschlossenen Dachfuge kontrolliert aus. Nur durch
  erfahrene Anwender gemäß aktuellem Sicherheitsdatenblatt verarbeiten.
- Der Unterkragen
  ({p.CUTOUT_W - 2 * p.BOT_KRAGEN_CLEAR:.0f} mm) zentriert im Soll-Ausschnitt
  {p.CUTOUT_W:.0f}×{p.CUTOUT_W:.0f} mm. Acht seitliche ST4.2×25 gehen durch
  seine vorgefertigten Löcher in den Holzrahmen. Sie sind eine nicht
  angerechnete mechanische Rückfallebene; Primärpfad bleibt die Klebung. Der
  Holzrahmen ist vollflächig verklebter Lastverteiler und Kompressionsschutz.
- Dicht-/Klebstoff: **Sikaflex-522 weiß, 2× 300 ml**: ca.
  **{bead_ml:.0f} ml** nominal in die beiden {p.GROOVE_W:.0f} mm breiten
  unteren Kleberführungen, ca. **{PRM.weather_fillet_volume_ml(p):.0f} ml**
  für die äußere Schutzkehle sowie zusätzlich die obere Belluna-Fuge;
  {PRM.spacer_pad_count(p)}
  Abstandspads halten {p.GLUE_GAP} mm Dachabstand. Zusammen mit der {p.GROOVE_D:.1f}-mm-
  Führung entstehen {PRM.groove_bondline_thickness(p):.1f} mm wirksame Raupenhöhe.
  Die Pads haben {p.SPACER_PAD_RADIAL:.1f}×{p.SPACER_PAD_TANGENTIAL:.1f} mm Kontaktmaß.
  Keine Zwingen, Spanngurte oder vertikale Klemmverschraubung: nur bis zum
  ersten gleichmäßigen Padkontakt anpressen und gegen Verschieben sichern.
  Danach auch die Belluna-Ringklebenut mit 522 füllen. Strukturelle
  Klebezonen bleiben lackfrei. ASA-GF/Belluna-Kunststoff sehr fein schleifen,
  mit **Sika Cleaner P** reinigen und **Sika Primer-507** als ABS-Analogie
  einsetzen; GFK-Gelcoat sehr fein schleifen, Cleaner P und **Sika
  Aktivator-205**. Jeweils aktuelle Produktdatenblätter beachten.
  **Carloflex 410 UV weiß** ist eine Belluna-konforme Alternative. Das
  Hersteller-TDS nennt >1,8 MPa Zugfestigkeit und >450 % Dehnung; deshalb
  gelten dieselben stark abgeminderten Projektgrenzwerte von 0,030 MPa normal
  und 0,050 MPa Schub. Das TDS benennt den erforderlichen Kunststoffprimer
  jedoch nicht: je Baugruppe nur ein vollständig spezifiziertes System
  verwenden, Produkte nicht mischen. Die untere Doppelraupe ist der allein
  angerechnete Adapter-Dach-Primärpfad: äußere Raupe wasserdicht geschlossen herstellen;
  die definierten Unterbrechungen der inneren Raupe und den Mittelkanal nicht
  mit Dichtstoff verschließen. Bis zur vollständigen Durchhärtung gemäß
  aktuellem Produktdatenblatt bewegungsfrei halten und nicht belasten.
- Erst **nach vollständiger Durchhärtung** der beiden tragenden Dachraupen die
  zugängliche Außenkehle schließen. GFK-Gelcoat und vollständig ausgehärtete
  Mipa-2K-PUR-Lackflanke jeweils etwa {PRM.weather_fillet_leg(p):.0f} mm breit
  nach aktueller Sika-STP-Vorbehandlungstabelle vorbereiten. Sikaflex-522 zu
  einer lückenlosen konkaven Kehle von ungefähr
  {PRM.weather_fillet_leg(p):.0f}×{PRM.weather_fillet_leg(p):.0f} mm formen und
  innerhalb der Hautbildungszeit ausschließlich mit **Sika Tooling Agent N**
  glätten. Keine Spülmittel-, Alkohol- oder Lösemittellösung. Diese erneuerbare
  Wetter-/Kontrollfuge bleibt sichtbar und zugänglich, wird **nicht** als
  Tragpfad angerechnet und ist jährlich sowie nach Beschädigung zu prüfen.
- Jede Adapterseite besitzt Vollmaterialrippen ±140/±165. Von den zehn
  Belluna-Seitenlöchern nur die **acht äußeren** mit den übrigen 8
  ST4.2×25 setzen; Mittellöcher an den Segmentstößen frei lassen. Die vier
  PT4.0×12 Lüfter→Platte mit Belluna-Drehmoment 0,7 Nm. Damit werden die
  **8 Belluna-Schrauben ST 4.2×25** an der Platte verwendet; die acht
  übrigen beiliegenden Schrauben sichern den Adapter seitlich im Holzrahmen.
- Zerstörende Originalsubstrat-Coupons stehen aktuell nicht zur Verfügung.
  `analysis/load_paths.py` ersetzt sie für den Prototypenentscheid durch stark
  abgeminderte Grenzflächenwerte, vollständige Schraubenlasten mit Faktor 1,5
  und nur eine angerechnete Holz/GFK-Fläche (`PASS_ASSUMPTION_BASED`, keine
  Herstellerfreigabe). Die äußere Raupe geschlossen führen; die innere an
  den acht geformten Trockenraum-Vents unterbrechen. Nach Einbau drucklos fluten
  (Gießkanne, 10 min); Hochdruck nur aus ISO-20653-9K-Abstand, nie direkt auf
  die IPX4-Lüfterhaube. Die äußere Schutzkehle, die untere Klebefuge, Nähte und
  Lack jährlich prüfen.

## Lüftereinbau
- Effektive Wandstärke: {PRM.effective_wall(p):.0f} mm →
  **Vierkantwelle {PRM.select_shaft(p):.0f} mm** einsetzen.
- Außenmaß Adapter: {L:.0f} x {W:.0f} mm, Höhe {p.H_RAISE:.0f} mm inkl. Fuge.
"""


def export_all(p: PRM.Params = PRM.P, out_dir: str = "out",
               frame=None, segments=None) -> list:
    """frame/segments optional vorgefertigt übergeben (Finalreview I2/M4):
    baut nur, was NICHT übergeben wurde -- die Engineering-Stufe hat frame/segments für
    FEM/DFM-Gate ohnehin schon gebaut und reicht sie durch (spart ~20-30 s
    je Produktionslauf, keine doppelten build_frame/build_segments-Booleans
    mehr). Ohne Argumente bleibt der Aufruf kompatibel; exportiert wird
    bewusst nur das eine Universal-Segment mit Stückzahl x4."""
    PRM.validate(p)
    if len(set(PRM.side_top_widths(p))) != 1:
        raise ValueError("Universal-Segment-Export setzt vier gleiche W_TOP-Breiten voraus")
    h = PRM.params_hash(p)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = []

    if frame is None:
        frame = build_frame(p)
    fp = out / f"frame_{h}.step"
    frame.exportStep(str(fp))
    _normalize_step_header(fp)
    files.append(fp)

    if segments is None:
        segments = build_segments(p)
    if len(segments) != 4:
        raise ValueError(f"Universal-Export erwartet 4 Montagekopien, bekam {len(segments)}")
    # Alle vier Shapes sind Rotationskopien desselben physischen Teils. Nur
    # die kanonische Datei exportieren; Stückzahl steht im Namen.
    segment = segments[0]
    stem = f"universal_segment_x4_{h}"
    sp = out / f"{stem}.step"
    segment.exportStep(str(sp))
    _normalize_step_header(sp)
    files.append(sp)
    printable = _print_oriented(segment)
    for ext in (".stl", ".3mf"):
        mp = out / f"{stem}{ext}"
        _write_mesh(printable, mp)
        files.append(mp)

    note = out / f"montagenotiz_{h}.md"
    note.write_text(_montagenotiz(p, h), encoding="utf-8")
    files.append(note)
    return files
