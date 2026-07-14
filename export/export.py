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

## Druck (4 beschriftete Segmente; Lochlayout seitenspezifisch)
- Material: **{p.MATERIAL_NAME}, weiß/hell** — keine GF-/CF-Füllung
  vorausgesetzt. Hell = geringere Solaraufheizung; die Thermik-Auslegung setzt
  das voraus. Düsen-/Bett-/Trocknungswerte nach Datenblatt der tatsächlich
  gewählten Filamentcharge, zunächst mit Herstellerprofil kalibrieren.
- Temperaturvorbehalt: HDT bei 1,82 MPa = **{p.HDT_182:.0f} °C**, angesetzte
  maximale Bauteiltemperatur = **{p.T_MAX:.0f} °C**. Diese knappe 1-K-Marge
  ist in den zulässigen Spannungen stark abgemindert; ein schwarzes Teil oder
  ein unkalibrierter Hochtemperatur-Einbau ist damit nicht abgedeckt.
- Orientierung: **Deckfläche nach unten**; damit liegen die Hauptlasten in XY
  und alle 47°-Flächen sind supportfrei. Keine Supports in Kammern oder
  Schraubkanälen zulassen. Layerhöhe 0,20 mm als Ausgangspunkt, 0,4-mm-Düse.
- Mindestens **4 Perimeter**, **100 % Infill** (die geschlossenen Rippenkammern
  übernehmen die Gewichtsreduktion; volle Dichte = definierte Festigkeit +
  Porenschluss), 0,4er Düse.
- **PFLICHT gegen Verzug**: geschlossener, möglichst beheizter Bauraum,
  **Brim ≥ 10 mm**, keine Zugluft, Teil nach Druckende langsam im geschlossenen
  Bauraum abkühlen lassen. Erst ein Segment drucken und Ebenheit/Öffnungsmaß
  prüfen; Slicer-Kompensation erst aus diesem realen ASA-Druck ableiten.
- Kein pauschales Tempern: bei Standard-ASA kann es die 275-mm-Segmente ohne
  Lehre nachträglich verziehen. Nur mit Materialdatenblatt und Fixierlehre.
- **Spulenlogistik**: **3× 1-kg-Spule derselben Charge/Farbe** (Nettobedarf
  wird aus RHO {p.RHO:.0f} kg/m³ berechnet; dritte Spule ist Fehldruckreserve).

## Fügen
- 4 Stöße: Halbüberlappung, je 1x M5x{_m5_bolt_length(p)}
  Zylinderkopf (DIN 912) + Mutter in der Tasche, Fügeflächen VOLLFLÄCHIG mit
  2K-Epoxid benetzen, verschrauben (0,8 Nm). Die Epoxid-Fügung ist Teil des
  Dichtheitskonzepts (Spec §4) — nicht weglassen.
- Nach dem Anziehen die vier M5-Kopftaschen bündig mit 2K-Epoxid versiegeln;
  offene Taschen wären Wasserreservoirs auf der bewitterten Oberseite.

## Dichtheit
- Beide Kleber-Ringe (untere Rille, Belluna-Ringklebenut) laufen GESCHLOSSEN über
  alle vier Stöße — nicht an Stößen absetzen.
- Die äußere 47°-Fase ist der Ablauf der frei bewitterten Adapterkante; beim
  Versiegeln nicht mit einer Dichtstoffraupe oder Beschichtungskante aufstauen.
- PFLICHT: Außenflächen mit 2K-PU oder Epoxid versiegeln (Porenschluss + UV).
- Lüfter-Verschraubung mit Feder-/Sicherungselementen montieren; nach der ersten
  Hitzeperiode nachziehen; Nähte jährlich sichtprüfen (Relaxation/Zyklik).
- Wassertest nach Einbau: erst drucklos fluten (Gießkanne, 10 min, Innenkontrolle),
  dann Hochdruck nur aus ISO-20653-9K-Abstand auf den Sockelbereich — nie direkt
  auf die Lüfterhaube (Belluna ist IPX4).

## Verkleben auf dem Dach
- Untergrund: Mini-Heki-Altbett vollständig entfernen, mit Isopropanol reinigen.
- Der **Unterkragen** taucht in den Dachausschnitt ({p.BOT_KRAGEN_CLEAR} mm
  Radialluft je Seite) und zentriert den Rahmen. Nach dem Ausrichten:
  **8 der beiliegenden ST {p.BOT_KRAGEN_SCREW_D:.1f}×{p.BOT_KRAGEN_SCREW_L:.0f}**
  durch die zwei Kragenlöcher je Seite seitlich in den Ausschnittsrand —
  dieselbe optionale Holzrahmen-Methode wie Belluna, nicht von oben durch die
  Dichtfläche schrauben. Vorbohrdurchmesser am realen Holz per Probeschraube
  festlegen. **EINBAUSCHRITT Holzrahmen** (User-
  Entscheid 2026-07-14; Bestand: Mini-Heki nur geklebt, KEIN Holz im
  35-mm-XPS-Kern): Nach der Demontage rund um den 400×400-Ausschnitt den
  XPS-Randstreifen ausräumen und einen wasserfest verleimten Holzrahmen
  (Höhe = Kernstärke, Breite ≥ 30 mm) mit PU-Leim einsetzen — übliche
  Praxis; er ist Schraubgrund UND Kompressionsschutz des Sandwichs. Die
  8 ST4.2-Schrauben greifen dann durch den gedruckten Kragen ins Holz und
  sind damit tragende Redundanz zum Kleber. Vor dem Einsetzen den
  realen Ausschnitt messen (C1a, Soll 400×400) — der Unterkragen
  ({p.CUTOUT_W - 2 * p.BOT_KRAGEN_CLEAR:.0f} mm)
  braucht rundum Luft; Schnittkanten des XPS vor dem Verkleben versiegeln.
- Carloflex/Sika-252-Raupe in die untere Kleberille: ca. **{bead_ml:.0f} ml**
  (+ Kehlnaht außen). Noppen definieren {p.GLUE_GAP} mm Fugendicke — NICHT auspressen.
- Karosseriebefestigungsplatte mit Carloflex in der Ringklebenut auf die
  Deckfläche kleben. Von den zehn gemessenen seitlichen Belluna-Löchern nur
  die **acht äußeren** (je ±140 mm auf FRONT/REAR, je ±165 mm auf LEFT/RIGHT)
  mit den übrigen 8 beiliegenden ST4.2×25 in die dafür massiv gehaltenen
  Adapterzonen schrauben; die zwei Mittellöcher an den Segmentstößen bleiben
  frei. Damit werden insgesamt exakt die 16 Belluna-Schrauben verwendet.
- Die vier PT4.0×12 für Lüfter-Hauptelement→Karosseriebefestigungsplatte und
  das Belluna-Anzugsmoment 0,7 Nm bleiben gegenüber der Anleitung unverändert.

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
    mehr). Rückwärtskompatibel: ohne Argumente identisches Verhalten wie
    zuvor (bestehende Aufrufer/Tests unverändert grün)."""
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
    for k, seg in enumerate(segments):
        sp = out / f"seg{k}_{h}.step"
        seg.exportStep(str(sp))
        files.append(sp)
        printable = _print_oriented(seg)
        for ext in (".stl", ".3mf"):
            mp = out / f"seg{k}_{h}{ext}"
            _write_mesh(printable, mp)
            files.append(mp)

    note = out / f"montagenotiz_{h}.md"
    note.write_text(_montagenotiz(p, h), encoding="utf-8")
    files.append(note)
    return files
