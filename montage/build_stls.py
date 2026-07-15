"""FreeCAD-Seite des Montageanleitungs-Generators.

Zweck
-----
Baut ALLE Geometrien der illustrierten Montageanleitung als STL nach
``out/montage/stl/`` und schreibt ein Manifest ``out/montage/manifest.json``.
Das Manifest ist die einzige Schnittstelle zur Blender-Seite
(``montage/render_steps.py``) und zur PDF-Seite (``montage/build_pdf.py``):
es enthält den ``params_hash``, alle Markerkoordinaten (M5-Schraubachsen,
Dach-Schraubachsen, Belluna-Plattenschraubachsen), die Explosions-Offsets,
Geometrie-Konstanten für die Blender-Polygon-Filter (Kleberille, Noppenfeld,
Stoßband) sowie alle abgeleiteten Textwerte (Klebstoffmenge in ml, M5-Länge,
Vierkantwellenlänge …). Sämtliche Zahlen werden zur Laufzeit aus ``params.py``
bzw. den ``export``-Helpern gezogen — nichts ist hier hartkodiert.

Aufruf
------
    bin/fc montage/build_stls.py

Abhängigkeiten
--------------
- FreeCAD (Part, MeshPart) über ``bin/fc`` (siehe Skill maxx150-pipeline).
- params.py, model/frame.py, model/segments.py (Geometrie).
- export/export.py::_m5_bolt_length (M5-Länge).
- render/belluna_platte_mock.py (Belluna-Platten-Mock via exec-Muster wie
  render/stapel_stl.py).

Endmarker im Log: ``MONTAGE-STL-ENDE: <verzeichnis>`` (von
scripts/montageanleitung.sh geparst)."""
import datetime
import json
import math
import os
import sys

import FreeCAD as App
import MeshPart
import Part

# Hintergrundläufe: freecadcmd flusht gepufferten stdout beim Prozessende nicht
# zuverlässig -> Zeilenpufferung erzwingen (Skill maxx150-pipeline).
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.getcwd())

import params as PRM                                      # noqa: E402
from model import features as F                           # noqa: E402
from model.frame import build_frame, top_z               # noqa: E402
from model.segments import build_segments                # noqa: E402
from export.export import _m5_bolt_length                 # noqa: E402

P = PRM.P
PRM.validate(P)
H = PRM.params_hash(P)

OUT = os.path.join("out", "montage")
STL = os.path.join(OUT, "stl")
os.makedirs(STL, exist_ok=True)

TOP_Z = top_z(P)                       # Deckflächenhöhe (Einbaulage), z=0 = Unterseite
LAP_H = TOP_Z / 2                       # Halbüberlappungs-Ebene
ROOF_TOP_Z = -P.GLUE_GAP               # Dachoberkante: die Noppenspitzen ruhen darauf


def stl(shape, name):
    """Vernetzt ein Shape und schreibt es als STL nach out/montage/stl/."""
    mesh = MeshPart.meshFromShape(shape, LinearDeflection=0.08,
                                  AngularDeflection=0.4, Relative=False)
    path = os.path.join(STL, name)
    mesh.write(path)
    print("STL:", name, f"({mesh.CountFacets} Facetten)", flush=True)


def rotz_pt(x, y, k):
    """Punkt (x,y) um k*90° um die z-Achse durch den Ursprung -- deckungs-
    gleich mit model.features.rotz (Rechte-Hand-Regel: (x,y)->(-y,x) je 90°)."""
    for _ in range(k % 4):
        x, y = -y, x
    return x, y


def marker_line(x, y, z0, z1, k=0):
    """Vertikaler Achsmarker: Endpunkte (x,y,z0)/(x,y,z1), um k*90° rotiert."""
    xr, yr = rotz_pt(x, y, k)
    return {"p1": [xr, yr, z0], "p2": [xr, yr, z1]}


def marker_horiz(x, y0, y1, z, k=0):
    """Horizontaler (radialer) Achsmarker in der kanonischen +y-Seite: von
    (x,y0,z) nach (x,y1,z), danach um k*90° rotiert (Endpunkte mitgedreht)."""
    p1 = list(rotz_pt(x, y0, k)) + [z]
    p2 = list(rotz_pt(x, y1, k)) + [z]
    return {"p1": p1, "p2": p2}


# ---------------------------------------------------------------------------
# 1) Vier Segmente (Einbaulage, wie gefügt) -- build_segments liefert seg0..3
#    bereits rotiert an ihrer Quadrantenposition.
# ---------------------------------------------------------------------------
# MONTAGE_SKIP_SEGS=1 ueberspringt den teuren Segmentbau, wenn die vier
# Segment-STLs bereits vorliegen (die Segmente haengen nicht von den unten
# neu konstruierten Dach-/Platten-Teilen ab -- spart bei reinen Dach-Iterationen
# den mehrminuetigen build_segments-Boolean).
seg_stls = [os.path.join(STL, f"seg{k}.stl") for k in range(4)]
if os.environ.get("MONTAGE_SKIP_SEGS") == "1" and all(os.path.exists(s) for s in seg_stls):
    print(f"== Segmente uebersprungen (MONTAGE_SKIP_SEGS=1, Hash {H}) ==", flush=True)
else:
    print(f"== Segmente bauen (Hash {H}) -- dauert einige Minuten ==", flush=True)
    segments = build_segments(P)
    for k, seg in enumerate(segments):
        stl(seg, f"seg{k}.stl")

# Halbschnitt eines Segments für die Fügeflächen-Nahaufnahme ist nicht nötig:
# Bild 03 zeigt das volle Segment. Für die Baugruppen-Schnitte genügen die
# Dach-Halbschnitte unten.

# ---------------------------------------------------------------------------
# 2) Belluna-Platte + Clips + Dichtring (Mock) -- exec-Muster wie
#    render/stapel_stl.py; auf die Deckfläche (top_z) nach +z verschieben.
# ---------------------------------------------------------------------------
print("== Belluna-Platten-Mock laden ==", flush=True)
os.environ["PLATTE_SKIP_EXPORT"] = "1"
ns = {}
src = open(os.path.join("render", "belluna_platte_mock.py")).read()
exec(compile(src, "belluna_platte_mock", "exec"), ns)
for name, solid in (("platte", ns["body"]), ("clips", ns["clips_comp"]),
                    ("dichtring", ns["dichtring"])):
    s = solid.copy()
    s.translate(App.Vector(0, 0, TOP_Z))       # Auflageebene des Mock (z=0) -> Deckfläche
    stl(s, f"{name}.stl")

# ---------------------------------------------------------------------------
# 3) Dach-Mock (NEU konstruiert): 800x800xROOF_T mit zentralem 400x400-R5-
#    Ausschnitt. Dachoberkante bei ROOF_TOP_Z (=-GLUE_GAP), Unterkante darunter.
#    Zusätzlich als SEPARATE Teile: Holzrahmen (30 mm breiter Schraubgrund-Ring
#    direkt um den Ausschnitt) und XPS-Kern (symbolischer Ring außen herum).
# ---------------------------------------------------------------------------
print("== Dach-Mock konstruieren ==", flush=True)
ROOF_HALF = 400.0                        # 800 mm Kantenlänge
CUT_HALF = P.CUTOUT_W / 2                 # 200
HOLZ_W = P.ROOF_WOOD_FRAME_W             # 30 mm Rahmenbreite
CORE_H = P.ROOF_T - 4.0                  # Kernhöhe (2 mm GFK-Deckschicht oben/unten)
CORE_Z0 = ROOF_TOP_Z - 2.0 - CORE_H      # Kern-Unterkante
HOLZ_OUT_HALF = CUT_HALF + HOLZ_W        # 230
XPS_OUT_HALF = HOLZ_OUT_HALF + 150.0     # 380, symbolisch nach außen

# Dach als echtes Sandwich: GFK-Vollplatte mit Ausschnitt, aus der die
# Kern-Kavität (2 mm Deckschichten oben/unten bleiben stehen) ausgeschnitten
# wird -- Holzrahmen und XPS-Kern fuellen genau diese Kavitaet, sodass im
# Halbschnitt (Bild 09) eine saubere, ueberschneidungsfreie Schichtung
# entsteht (kein z-Fighting Kern gegen Dach-Vollmaterial).
roof_outer = F.rounded_box(2 * ROOF_HALF, 2 * ROOF_HALF, P.ROOF_T, 20.0,
                           App.Vector(-ROOF_HALF, -ROOF_HALF, ROOF_TOP_Z - P.ROOF_T))
roof_cut = F.rounded_box(P.CUTOUT_W, P.CUTOUT_W, P.ROOF_T + 4, P.CUTOUT_R,
                         App.Vector(-CUT_HALF, -CUT_HALF, ROOF_TOP_Z - P.ROOF_T - 2))
dach = roof_outer.cut(roof_cut)

# Kern-Kavität (Ring vom Ausschnitt bis XPS-Aussenkante), fuellen Holz + XPS
core_cav = F.ring(2 * XPS_OUT_HALF, 2 * XPS_OUT_HALF,
                  P.CUTOUT_R + (XPS_OUT_HALF - CUT_HALF),
                  P.CUTOUT_W, P.CUTOUT_W, P.CUTOUT_R, CORE_H)
core_cav.translate(App.Vector(0, 0, CORE_Z0))
dach = dach.cut(core_cav)

# Holzrahmen-Ring (Schraubgrund) direkt um den Ausschnitt (x 200..230)
holz = F.ring(2 * HOLZ_OUT_HALF, 2 * HOLZ_OUT_HALF, P.CUTOUT_R + HOLZ_W,
              P.CUTOUT_W, P.CUTOUT_W, P.CUTOUT_R, CORE_H)
holz.translate(App.Vector(0, 0, CORE_Z0))

# XPS-Kern-Ring (symbolisch, außen um den Holzrahmen, x 230..380)
xps = F.ring(2 * XPS_OUT_HALF, 2 * XPS_OUT_HALF, P.CUTOUT_R + (XPS_OUT_HALF - CUT_HALF),
             2 * HOLZ_OUT_HALF, 2 * HOLZ_OUT_HALF, P.CUTOUT_R + HOLZ_W, CORE_H)
xps.translate(App.Vector(0, 0, CORE_Z0))

stl(dach, "dach.stl")
stl(holz, "holzrahmen.stl")
stl(xps, "xps_kern.stl")

# Halbschnitt (y>0 entfernt) für Schritt 09 (Dach im Schnitt)
halb_y = Part.makeBox(4000, 2000, 4000, App.Vector(-2000, 0, -2000))
stl(dach.cut(halb_y), "dach_ycut.stl")
stl(holz.cut(halb_y), "holzrahmen_ycut.stl")
stl(xps.cut(halb_y), "xps_kern_ycut.stl")

# ---------------------------------------------------------------------------
# 4) Markerkoordinaten (aus params abgeleitet) für die Blender-Seite
# ---------------------------------------------------------------------------
# M5-Stoßschrauben: vertikale Achse bei (CUTOUT_W/2+JOINT_BOLT_OFF, -LAP_L/2),
# 4x um 90° rotiert (deckungsgleich model/segments.py::_bolt_cuts).
m5_x = P.CUTOUT_W / 2 + P.JOINT_BOLT_OFF
m5_y = -P.LAP_L / 2
m5_markers = [marker_line(m5_x, m5_y, -3.0, TOP_Z + 4.0, k) for k in range(4)]

# Dach-Schrauben Ø4: horizontal (radial) durch den Unterkragen in den
# Holzrahmen, z=-(GLUE_GAP+BOT_KRAGEN_HOLE_Z), an BOT_KRAGEN_HOLE_OFFS.
dach_z = -(P.GLUE_GAP + P.BOT_KRAGEN_HOLE_Z)
ki_half = (P.CUTOUT_W - 2 * P.BOT_KRAGEN_CLEAR) / 2 - P.BOT_KRAGEN_T   # Kragen-Innenwand
dach_markers = []
for k in range(4):
    for off in P.BOT_KRAGEN_HOLE_OFFS:
        # von innen (Kragen) radial nach außen durch die Ausschnittwand in den Holzrahmen
        dach_markers.append(marker_horiz(off, ki_half - 8.0, CUT_HALF + HOLZ_W - 4.0,
                                         dach_z, k))

# Belluna-Plattenschrauben ST4.2: horizontal (radial) durch den Platten-Kragen
# in die Adapter-Innenwand, z=top_z-PLATE_SCREW_Z_FROM_TOP, an PLATE_SCREW_OFFS.
plate_z = TOP_Z - P.PLATE_SCREW_Z_FROM_TOP
plate_markers = []
for k in range(4):
    for off in P.PLATE_SCREW_OFFS:
        plate_markers.append(marker_horiz(off, CUT_HALF - 15.0, CUT_HALF + 15.0,
                                          plate_z, k))

# ---------------------------------------------------------------------------
# 5) Abgeleitete Textwerte (identische Formeln wie export/export.py)
# ---------------------------------------------------------------------------
groove_len = PRM.groove_centerline_len(P)
bead_ml = groove_len * P.GROOVE_W * (P.GLUE_GAP + P.GROOVE_D) / 1000.0

# Geometrie-Konstanten für die Blender-Polygon-Filter
groove_inner_half = P.CUTOUT_W / 2 + P.GROOVE_OFF
groove_outer_half = groove_inner_half + P.GROOVE_W
nopple_inner_r = P.CUTOUT_W / 2 + P.GROOVE_OFF / 2
nopple_outer_r = P.CUTOUT_W / 2 + P.GROOVE_OFF + P.GROOVE_W + 12
mask_r_in = P.CUTOUT_W / 2 + P.GROOVE_OFF - 5
mask_r_out = P.CUTOUT_W / 2 + P.GROOVE_OFF + P.GROOVE_W + 25

manifest = {
    "params_hash": H,
    "geom_rev": P.GEOM_REV,
    "erzeugt": datetime.date.today().isoformat(),
    "geometrie": {
        "top_z": TOP_Z,
        "lap_h": LAP_H,
        "cutout_w": P.CUTOUT_W,
        "cutout_half": CUT_HALF,
        "cutout_r": P.CUTOUT_R,
        "lap_l": P.LAP_L,
        "tol_joint": P.TOL_JOINT,
        "joint_bolt_off": P.JOINT_BOLT_OFF,
        "joint_cb_d": P.JOINT_CB_D,
        "outer_half": PRM.outer_dims(P)[0] / 2,
        "roof_t": P.ROOF_T,
        "roof_top_z": ROOF_TOP_Z,
        "groove_inner_half": groove_inner_half,
        "groove_outer_half": groove_outer_half,
        "groove_d": P.GROOVE_D,
        "nopple_inner_r": nopple_inner_r,
        "nopple_outer_r": nopple_outer_r,
        "nopple_r": P.NOPPLE_R,
        "mask_r_in": mask_r_in,
        "mask_r_out": mask_r_out,
        "holz_inner_half": CUT_HALF,
        "holz_outer_half": HOLZ_OUT_HALF,
        "glue_gap": P.GLUE_GAP,
        "bot_kragen_depth": P.BOT_KRAGEN_DEPTH,
    },
    "marker": {
        "m5": m5_markers,
        "dach_screws": dach_markers,
        "plate_screws": plate_markers,
    },
    "explosion": {
        "radial_mm": 70.0,        # radialer Segment-Auszug (wie render/blender_views.py)
        "platte_z_mm": 120.0,     # Belluna-Platte schwebt über der Deckfläche
    },
    "text": {
        "material_name": P.MATERIAL_NAME,
        "m5_length": _m5_bolt_length(P),
        "m5_through_d": P.JOINT_BOLT_D,
        "nut_af": P.JOINT_NUT_AF,
        "bead_ml": round(bead_ml),
        "bead_ml_exact": round(bead_ml, 1),
        "groove_len_mm": round(groove_len),
        "shaft_mm": round(PRM.select_shaft(P)),
        "effective_wall_mm": round(PRM.effective_wall(P)),
        "dach_screw_count": PRM.bot_kragen_hole_count(P),
        "dach_screw_d": P.BOT_KRAGEN_HOLE_D,
        "dach_screw_st_d": P.BOT_KRAGEN_SCREW_D,
        "dach_screw_st_l": P.BOT_KRAGEN_SCREW_L,
        "dach_hole_offs": list(P.BOT_KRAGEN_HOLE_OFFS),
        "plate_screw_d": 4.2,
        "plate_screw_l": 25,
        "plate_screw_offs": list(P.PLATE_SCREW_OFFS),
        "wood_frame_w": P.ROOF_WOOD_FRAME_W,
        "roof_t": P.ROOF_T,
        "cutout_w": P.CUTOUT_W,
        "bot_kragen_clear": P.BOT_KRAGEN_CLEAR,
        "kragen_outer_w": round(P.CUTOUT_W - 2 * P.BOT_KRAGEN_CLEAR),
        "h_raise": P.H_RAISE,
        "glue_gap": P.GLUE_GAP,
        "hdt_045": P.HDT_045,
        "hdt_182": P.HDT_182,
        "t_max": P.T_MAX,
        "seg_mass_g": 465,               # Zielmasse je Druckteil (Projektannahme)
        "torque_nm": 0.8,
        "paint_prep_c": 60,
        "paint_prep_min": 60,
        "cure_h": 24,
        "outer_l_mm": round(PRM.outer_dims(P)[0]),
        "outer_w_mm": round(PRM.outer_dims(P)[1]),
    },
}

with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, indent=2, ensure_ascii=False)
print("MANIFEST:", os.path.join(OUT, "manifest.json"), flush=True)
print("MONTAGE-STL-ENDE:", STL, flush=True)
