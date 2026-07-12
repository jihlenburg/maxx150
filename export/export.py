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
    groove_len = 4 * (p.CUTOUT_W + 2 * p.GROOVE_OFF + p.GROOVE_W)
    bead_ml = groove_len * p.GROOVE_W * (p.GLUE_GAP + p.GROOVE_D) / 1000.0
    return f"""# Montagenotiz Adapterrahmen (Parameterstand {h})

## Druck (je 4x Segment, identisch)
- Material: ASA weiß; Orientierung: **Deckfläche nach unten** (Schichten parallel
  zum Dach; bei MJF/SLS beliebig). Brücken in Gusset-Freistellung/Muttertaschen sind
  beabsichtigt und unkritisch.
- Mindestens **4 Perimeter**, **100 % Infill** (die geschlossenen Rippenkammern
  übernehmen die Gewichtsreduktion; volle Dichte = definierte Festigkeit +
  Porenschluss), 0,4er Düse.
- **PFLICHT gegen Verzug** (ASA, 275-mm-Teil mit massiven Eck-/Stoßzonen):
  geschlossener, beheizter Bauraum (≥ 45 °C Kammer), Bett 100–110 °C auf
  texturiertem PEI, **Brim ≥ 10 mm**, Draft-Shield, nach Druckende im
  geschlossenen Bauraum abkühlen lassen. Beim Druckservice ausdrücklich
  „ASA-erfahren, geschlossene Maschine" anfordern — KEIN offener Drucker.
- Nach dem Druck **Tempern** (ASA: 80 °C, 4 h) für Maßstabilität bei Dachhitze.

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


def export_all(p: PRM.Params = PRM.P, out_dir: str = "out") -> list:
    h = PRM.params_hash(p)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = []

    frame = build_frame(p)
    fp = out / f"frame_{h}.step"
    frame.exportStep(str(fp))
    files.append(fp)

    for k, seg in enumerate(build_segments(p)):
        sp = out / f"seg{k}_{h}.step"
        seg.exportStep(str(sp))
        files.append(sp)
        for ext in (".stl", ".3mf"):
            mp = out / f"seg{k}_{h}{ext}"
            _write_mesh(seg, mp)
            files.append(mp)

    note = out / f"montagenotiz_{h}.md"
    note.write_text(_montagenotiz(p, h))
    files.append(note)
    return files
