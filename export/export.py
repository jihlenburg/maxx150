"""Export der Druck-/Archivdateien + auto-generierte Montagenotiz (Spec §7)."""
from pathlib import Path

import MeshPart

import params as PRM
from model.frame import build_frame
from model.segments import build_segments


def _write_mesh(shape, path: Path):
    mesh = MeshPart.meshFromShape(shape, LinearDeflection=0.05,
                                  AngularDeflection=0.35, Relative=False)
    mesh.write(str(path))


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

## Druck (je 4x Segment, identisch)
- Material: **Würth ASA GF15** (Art. 4954641201), **Signalweiß RAL 9003** —
  weiß = geringere Solaraufheizung (die Thermik-Auslegung setzt ein HELLES
  Bauteil voraus!). Orientierung: **Deckfläche nach unten** (Schichten
  parallel zum Dach; bei MJF/SLS beliebig). Brücken in Gusset-Freistellung/
  Muttertaschen sind beabsichtigt und unkritisch.
- Druckparameter (Würth-Datenblatt Art. 4954641201): Düse **250–270 °C**,
  GEHÄRTETE Düse PFLICHT (Glasfaser abrasiv), max. Durchsatz **12 mm³/s**
  (Druckzeit entsprechend einplanen). Bett **100–110 °C** auf texturiertem
  PEI, Haftmittel empfohlen. Filament **VOR dem Druck trocknen**:
  Trockenbox/**80 °C, 4–6 h** (hygroskopisches Compound).
- Mindestens **4 Perimeter**, **100 % Infill** (die geschlossenen Rippenkammern
  übernehmen die Gewichtsreduktion; volle Dichte = definierte Festigkeit +
  Porenschluss), 0,4er Düse.
- **PFLICHT gegen Verzug**: Datenblatt nennt **0,3 % Schrumpf** — die
  Glasfaser senkt den Verzug spürbar, ersetzt aber NICHT die Sorgfaltspflicht
  bei diesem 275-mm-Teil mit massiven Eck-/Stoßzonen: geschlossener,
  beheizter Bauraum (Kammer) PFLICHT, **Brim ≥ 10 mm**, Draft-Shield, nach
  Druckende im geschlossenen Bauraum abkühlen lassen. Beim Druckservice
  ausdrücklich „GF-erfahren, gehärtete Düse, geschlossene Maschine"
  anfordern — KEIN offener Drucker.
- Nach dem Druck **Tempern** (80 °C, 4 h; ANNAHME analog Standard-ASA-Profil
  — das Würth-Blatt macht keine Temper-Angabe, Vicat 101 °C/HDT-B 99 °C
  liegen über dieser Temperatur) für Maßstabilität bei Dachhitze.
- **Spulenlogistik**: **4× 750-g-Spule** (Nettobedarf 4 Segmente ≈ 1,86 kg
  bei RHO {p.RHO:.0f} kg/m³ + Fehldruck-Reserve).

## Fügen
- 4 Stöße: Halbüberlappung, je 1x M5x{_m5_bolt_length(p)}
  Zylinderkopf (DIN 912) + Mutter in der Tasche, Fügeflächen VOLLFLÄCHIG mit
  2K-Epoxid benetzen, verschrauben (0,8 Nm). Die Epoxid-Fügung ist Teil des
  Dichtheitskonzepts (Spec §4) — nicht weglassen.

## Dichtheit
- Beide Kleber-Ringe (untere Rille, Belluna-Ringklebenut) laufen GESCHLOSSEN über
  alle vier Stöße — nicht an Stößen absetzen.
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
  **12 Schrauben Ø{p.BOT_KRAGEN_HOLE_D:.0f} (3 je Seite)** durch die
  Kragenlöcher seitlich in den Ausschnittsrand (3-mm-Kernloch vorbohren) —
  Methode der Belluna-Anleitung; fixiert den Rahmen lagerichtig, während
  der Kleber aushärtet. **EINBAUSCHRITT Holzrahmen** (User-
  Entscheid 2026-07-14; Bestand: Mini-Heki nur geklebt, KEIN Holz im
  35-mm-XPS-Kern): Nach der Demontage rund um den 400×400-Ausschnitt den
  XPS-Randstreifen ausräumen und einen wasserfest verleimten Holzrahmen
  (Höhe = Kernstärke, Breite ≥ 30 mm) mit PU-Leim einsetzen — übliche
  Praxis; er ist Schraubgrund UND Kompressionsschutz des Sandwichs. Die
  12 Ø4-Schrauben greifen dann durch die GFK-Haut ins Holz (Kernloch 3)
  und sind damit tragende Redundanz zum Kleber. Vor dem Einsetzen den
  realen Ausschnitt messen (C1a, Soll 400×400) — der Unterkragen (398)
  braucht rundum Luft; Schnittkanten des XPS vor dem Verkleben versiegeln.
- Carloflex/Sika-252-Raupe in die untere Kleberille: ca. **{bead_ml:.0f} ml**
  (+ Kehlnaht außen). Noppen definieren {p.GLUE_GAP} mm Fugendicke — NICHT auspressen.
- Karosseriebefestigungsplatte mit Carloflex in der Ringklebenut auf die
  Deckfläche kleben; seitliche Schrauben aus dem Einbaukragen in die
  Adapter-Innenwand (Kernloch 3 mm vorbohren).

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
        for ext in (".stl", ".3mf"):
            mp = out / f"seg{k}_{h}{ext}"
            _write_mesh(seg, mp)
            files.append(mp)

    note = out / f"montagenotiz_{h}.md"
    note.write_text(_montagenotiz(p, h), encoding="utf-8")
    files.append(note)
    return files
