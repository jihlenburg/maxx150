"""Export der Druck-/Archivdateien + auto-generierte Montagenotiz (Spec §7)."""
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
    groove_len = PRM.groove_centerline_len(p)      # M1/Ledger 23/30/33
    bead_ml = groove_len * p.GROOVE_W * (p.GLUE_GAP + p.GROOVE_D) / 1000.0
    return f"""# Montagenotiz Adapterrahmen (Parameterstand {h})

## Druck (1 Universal-Segment, **4x identisch drucken**)
- Material: **{p.MATERIAL_NAME}**, 1,75 mm, 750-g-Spule. Schwarz ist nur die
  Rohteilfarbe; vor dem Dacheinbau ist RAL 9003 Signalweiß zwingend.
- Datenlage: Würths mechanische Werte stammen aus Halbzeug, nicht aus
  FDM-Probekörpern. E={p.E_BASE:.0f} MPa und Zug={p.SIGMA_BASE:.0f} MPa sind
  konservative Projektannahmen; XY-/Z-Coupons aus Maschine, Düse und Charge
  bleiben Freigabebedingung.
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
- **Spulenlogistik**: **4× 750-g-Spule derselben Charge** (Nettobedarf ca.
  1,86 kg bei RHO {p.RHO:.0f} kg/m³ plus Coupon-/Fehldruckreserve).

## Fügen — WEICON RK-1300
- Rohes ASA-GF K240 anschleifen. **WEICON RK-1300, 60-g-Set,
  Art.-Nr. 10000118** verwenden. Wegen der rauen/porösen FDM-Flächen den
  Aktivator beidseitig auftragen, mindestens 5 min ablüften, RK-1300 auf eine
  Seite geben, fügen und je Stoß mit M5x{_m5_bolt_length(p)} DIN 912 + Mutter
  bei 0,8 Nm sichern. Endfestigkeit nach 24 h.
- Die M5-Kopftaschen bündig mit RK-1300 versiegeln. RK-1300 wurde gewählt,
  weil WEICON den MMA-Strukturklebstoff für Hartkunststoffe/Fahrzeugbau sowie
  hohe Schlag-, Schäl- und Scherfestigkeit spezifiziert. ASA-GF ist nicht
  einzeln gelistet: Stoßcoupon am Originaldruck ist Pflicht.

## Weiße Schutzlackierung — Pflicht
- Nach dem Fügen spätere Klebezonen roh lassen und abkleben: untere
  Kleberille/Noppenfeld und obere Belluna-Auflage. Lack ist kein Klebgrund.
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
  Primerliste: Gitterschnitt-/Abreißcoupon am Originaldruck ist Pflicht.

## Dach-Sandwich und Dichtheit
- Mini-Heki und Altbett entfernen. Den XPS-Randstreifen ausräumen und einen
  wasserfesten Holzrahmen (Höhe Kern, Breite ≥ 30 mm) mit
  **KLEIBERIT 501.0 1K-PUR-Leim** vollflächig einsetzen, mindestens 60 min
  pressen/fixieren. Wahlgrund: D4 nach DIN EN 204, Holz und Hartschäume,
  hohe Wärme- und Feuchtebeständigkeit. Der Rahmen ist Schraubgrund und
  Kompressionsschutz.
- Der Unterkragen ({p.CUTOUT_W - 2 * p.BOT_KRAGEN_CLEAR:.0f} mm) zentriert im
  Soll-Ausschnitt {p.CUTOUT_W:.0f}×{p.CUTOUT_W:.0f} mm. **8 beiliegende
  ST {p.BOT_KRAGEN_SCREW_D:.1f}×{p.BOT_KRAGEN_SCREW_L:.0f}** bei ±140 mm
  seitlich ins Holz, nie von oben durch die Dichtfläche.
- Dicht-/Klebstoff ausschließlich **Carloflex 410 UV weiß, 310 ml**: ca.
  **{bead_ml:.0f} ml** in die untere Kleberille plus Außenkehle; Noppen halten
  {p.GLUE_GAP} mm Fugendicke. Danach auch die Belluna-Ringklebenut mit
  Carloflex füllen. Wahlgrund: Belluna empfiehlt genau dieses dauerelastische,
  UV-beständige 1K-PU-Produkt für den Super Fan; es klebt und dichtet zugleich.
  Keine generische Sika-Alternative in die Prozesskette mischen.
- Jede Adapterseite besitzt Vollmaterialrippen ±140/±165. Von den zehn
  Belluna-Seitenlöchern nur die **acht äußeren** mit den übrigen 8
  ST4.2×25 setzen; Mittellöcher an den Segmentstößen frei lassen. Die vier
  PT4.0×12 Lüfter→Platte mit Belluna-Drehmoment 0,7 Nm. Damit sind die
  **16 Belluna-Schrauben ST 4.2×25** eindeutig auf 8× Dach und 8× Platte verteilt.
- Vor Serienmontage Haftcoupons prüfen: RK-1300 auf rohem ASA-GF; Carloflex
  auf rohem ASA-GF, ausgehärtetem Mipa-Lack und realem X150-GFK-Dach.
  Beide Kleberringe geschlossen führen. Nach Einbau drucklos fluten
  (Gießkanne, 10 min); Hochdruck nur aus ISO-20653-9K-Abstand, nie direkt auf
  die IPX4-Lüfterhaube. Nähte und Lack jährlich prüfen.

## Lüftereinbau
- Effektive Wandstärke: {PRM.effective_wall(p):.0f} mm →
  **Vierkantwelle {PRM.select_shaft(p):.0f} mm** einsetzen.
- Außenmaß Adapter: {L:.0f} x {W:.0f} mm, Höhe {p.H_RAISE:.0f} mm inkl. Fuge.
"""


def export_all(p: PRM.Params = PRM.P, out_dir: str = "out",
               frame=None, segments=None) -> list:
    """frame/segments optional vorgefertigt übergeben (Finalreview I2/M4):
    baut nur, was NICHT übergeben wurde -- run_all.py hat frame/segments für
    FEM/DFM-Gate ohnehin schon gebaut und reicht sie durch (spart ~20-30 s
    je Produktionslauf, keine doppelten build_frame/build_segments-Booleans
    mehr). Ohne Argumente bleibt der Aufruf kompatibel; GEOM_REV 6 exportiert
    jedoch bewusst nur noch das eine Universal-Segment mit Stückzahl x4."""
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
    files.append(fp)

    if segments is None:
        segments = build_segments(p)
    if len(segments) != 4:
        raise ValueError(f"Universal-Export erwartet 4 Montagekopien, bekam {len(segments)}")
    # GEOM_REV 6: alle vier Shapes sind Rotationskopien desselben physischen
    # Teils. Nur die kanonische Datei exportieren; Stückzahl steht im Namen.
    segment = segments[0]
    stem = f"universal_segment_x4_{h}"
    sp = out / f"{stem}.step"
    segment.exportStep(str(sp))
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
