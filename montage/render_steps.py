"""Blender-Seite des Montageanleitungs-Generators.

Zweck
-----
Rendert die 15 illustrierten Schrittbilder nach
``build/documentation/<hash>/img/``. Alle Geometrien kommen als STL aus
``montage/build_stls.py`` (FreeCAD-Seite); alle Koordinaten (Markerachsen,
Explosions-Offsets, Filtergrenzen) werden aus dem benachbarten Manifest
gelesen -- nichts ist hier hartkodiert.

Konventionen
------------
- Cycles, 96 Samples, Denoising, 1500x1125.
- Kräftiger technischer Studiohintergrund (sRGB ca. 60/149/195). Sichtbarer Hintergrund und
  Weltbeleuchtung sind getrennt: Der Hintergrund bleibt freundlich hell,
  während schwaches Fülllicht, gerichtetes Licht und feine Konturlinien die
  Form weißer Bauteile lesbar halten.
- Alle vier identischen ASA-Segmente weiß; die Belluna-Platte deutlich beige.
  Clips silber-metallisch, Dichtring fast schwarz.
- MARKIERUNGEN direkt in Blender:
  * emissive Signalrot-Zylinder (1.0,0.08,0.05, Emission Strength 2.0) für
    Schraubachsen,
  * FLÄCHEN-Hervorhebung über zweites Material + Polygon-Filter nach Position:
    Klebeflächen Grün (0.1,0.8,0.2), Maskierzonen Gelb (1.0,0.8,0.1).

Aufruf
------
    blender -b -P montage/render_steps.py -- <stl_dir> <out_dir>

Endmarker im Log: ``RENDER-ENDE``.
Jedes fertige Bild wird zusätzlich nach
``~/Downloads/Belluna-Render-Zwischenstand/`` kopiert.
"""
import json
import math
import os
import shutil
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
STL_DIR = argv[0]
OUT_DIR = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(STL_DIR), "img")
REVIEW_DIR = os.environ.get(
    "MONTAGE_REVIEW_DIR",
    os.path.expanduser("~/Downloads/Belluna-Render-Zwischenstand"),
)
MANIFEST = os.path.join(os.path.dirname(STL_DIR.rstrip("/")), "manifest.json")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(REVIEW_DIR, exist_ok=True)

with open(MANIFEST, encoding="utf-8") as fh:
    MF = json.load(fh)
G = MF["geometrie"]
MK = MF["marker"]
EX = MF["explosion"]

TOP_Z = G["top_z"]
LAP_H = G["lap_h"]
LAP_L = G["lap_l"]
CUT_HALF = G["cutout_half"]
ADAPTER_EDGE_COLLECTION = "Adapterkontur"

# --- Farbwelt -------------------------------------------------------------
COL_ASA = (1.00, 1.00, 1.00)
SEG_TINT = [COL_ASA] * 4
COL_PLATTE = (0.66, 0.46, 0.25)
COL_CLIPS = (0.52, 0.57, 0.66)
COL_SEAL = (0.05, 0.05, 0.06)
COL_DACH = (0.52, 0.54, 0.57)
COL_XPS = (0.36, 0.48, 0.62)
COL_HOLZ = (0.48, 0.25, 0.07)
COL_RED = (1.00, 0.02, 0.01)
COL_GREEN = (0.015, 0.90, 0.035)
COL_YELLOW = (1.00, 0.72, 0.01)


def _stl_path(name):
    return os.path.join(STL_DIR, name)


def _new_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 96
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 1125
    scene.render.film_transparent = False
    # Technische Produktgrafik: Standard bewahrt definierte RGB-Werte. AgX
    # rollt helle Flächen filmisch ab und machte weißes ASA sichtbar grau.
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    # Technische Illustrationskontur: weißes ASA bleibt auf dem hellen
    # Hintergrund lesbar, ohne künstlich grau oder blau eingefärbt zu werden.
    scene.render.use_freestyle = True
    scene.render.line_thickness = 0.7
    freestyle = bpy.context.view_layer.freestyle_settings
    lineset = freestyle.linesets[0]
    lineset.select_silhouette = True
    lineset.select_border = True
    lineset.select_crease = True
    lineset.select_external_contour = True
    lineset.select_by_collection = True
    edge_collection = bpy.data.collections.new(ADAPTER_EDGE_COLLECTION)
    scene.collection.children.link(edge_collection)
    lineset.collection = edge_collection
    lineset.collection_negation = "INCLUSIVE"
    linestyle = lineset.linestyle
    if linestyle is None:  # Blender 5.x legt keinen Standardstil mehr an.
        linestyle = bpy.data.linestyles.new("Technische Kontur")
        lineset.linestyle = linestyle
    linestyle.color = (0.10, 0.11, 0.12)
    linestyle.alpha = 0.50
    linestyle.thickness = 0.8

    # Ein einzelner Background-Shader koppelt Hintergrundhelligkeit und
    # Umgebungslicht. Über Is Camera Ray sieht die Kamera ein helles Blaugrau,
    # während die Geometrie nur ein schwaches neutrales Fülllicht erhält.
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputWorld")
    fill = nodes.new("ShaderNodeBackground")
    fill.inputs[0].default_value = (0.66, 0.69, 0.73, 1)
    fill.inputs[1].default_value = 0.54
    backdrop = nodes.new("ShaderNodeBackground")
    # Gemessen aus 01_titel_explosion_better.png: ca. sRGB 60/149/195.
    # Unter Standard sind dies die folgenden linearen RGB-Werte.
    backdrop.inputs[0].default_value = (0.045, 0.300, 0.546, 1)
    backdrop.inputs[1].default_value = 1.0
    light_path = nodes.new("ShaderNodeLightPath")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(light_path.outputs["Is Camera Ray"], mix.inputs[0])
    links.new(fill.outputs[0], mix.inputs[1])
    links.new(backdrop.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs[0])
    scene.world = world
    return scene


def _mat(name, rgb, rough=0.5, metallic=0.0, emission=0.0, alpha=1.0):
    """Principled-BSDF-Material mit optionaler Emission (Druck-Marker/Flächen).

    Emission über 'Emission Color' + 'Emission Strength'; robust gegen die
    unterschiedlichen Socket-Namen unterstützter Blender-Versionen."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    if emission > 0:
        emi = b.inputs.get("Emission Color") or b.inputs.get("Emission")
        if emi is not None:
            emi.default_value = (*rgb, 1)
        stg = b.inputs.get("Emission Strength")
        if stg is not None:
            stg.default_value = emission
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    return m


def _stl_import(path):
    before = set(bpy.data.objects)
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=path)
    else:
        bpy.ops.import_mesh.stl(filepath=path)
    return list(set(bpy.data.objects) - before)[0]


def _flat(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = False


def load_part(name, mat):
    """Importiert eine einzelne STL (name.stl) als flach gerendertes Objekt mit
    dem Material mat."""
    o = _stl_import(_stl_path(f"{name}.stl"))
    o.name = name
    o.data.materials.append(mat)
    _flat(o)
    return o


def load_seg(k, alpha=1.0, tint=None):
    """Importiert Segment k (seg{k}.stl), färbt es (tint oder SEG_TINT[k],
    optional transparent über alpha) und hängt es in die Freestyle-
    Kantencollection ein."""
    o = _stl_import(_stl_path(f"seg{k}.stl"))
    o.name = f"seg{k}"
    rgb = tint if tint is not None else SEG_TINT[k]
    o.data.materials.append(_mat(f"asa{k}", rgb, rough=0.5, alpha=alpha))
    bpy.data.collections[ADAPTER_EDGE_COLLECTION].objects.link(o)
    _flat(o)
    return o


def load_segments(alpha=1.0):
    """Importiert alle vier Segmente (optional transparent über alpha) als
    Liste."""
    return [load_seg(k, alpha=alpha) for k in range(4)]


def highlight(obj, rgb, predicate, emission=0.80):
    """Zweites (emissives) Material anhängen und per Polygon-Filter zuweisen."""
    idx = len(obj.data.materials)
    obj.data.materials.append(_mat(f"hl_{obj.name}_{idx}", rgb, rough=0.35,
                                   emission=emission))
    n = 0
    for poly in obj.data.polygons:
        if predicate(poly.center, poly.normal):
            poly.material_index = idx
            n += 1
    print(f"  Hervorhebung {obj.name}: {n} Polygone", flush=True)
    return n


def marker(p1, p2, radius=3.0, rgb=COL_RED, emission=1.8):
    """Emissiver Zylinder zwischen zwei Punkten (Schraubachs-Marker)."""
    p1 = Vector(p1)
    p2 = Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=radius,
                                        depth=max(d.length, 0.1),
                                        location=(p1 + p2) / 2)
    o = bpy.context.object
    o.rotation_mode = "QUATERNION"
    if d.length > 1e-6:
        o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    o.data.materials.append(_mat("marker", rgb, rough=0.3, emission=emission))
    return o


def rounded_square_bead(name, half, corner_r, z, diameter, rgb=COL_GREEN):
    """Geschlossener Rundquadrat-Marker für die äußere Schutzkehle.

    Der runde Querschnitt ist eine gut lesbare Render-Abstraktion der real
    konkav abgezogenen Kehlnaht; Maße und Sollquerschnitt stehen im PDF.
    """
    points = []
    center = half - corner_r
    for cx, cy, a0 in ((center, center, 0), (-center, center, 90),
                       (-center, -center, 180), (center, -center, 270)):
        for i in range(9):
            a = math.radians(a0 + 90.0 * i / 8.0)
            points.append((cx + corner_r * math.cos(a),
                           cy + corner_r * math.sin(a), z))
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = diameter / 2.0
    curve.bevel_resolution = 4
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, xyz in zip(spline.points, points):
        point.co = (*xyz, 1.0)
    spline.use_cyclic_u = True
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(_mat(name + "_mat", rgb, rough=0.30, emission=1.1))
    return obj


def _rig(scene, sun=3.0, area=45000, key=(-500, -700, 900)):
    s = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    s.data.energy = sun
    s.data.angle = math.radians(18)
    s.rotation_euler = (math.radians(48), math.radians(14), math.radians(35))
    scene.collection.objects.link(s)
    a = bpy.data.objects.new("Area", bpy.data.lights.new("Area", "AREA"))
    a.data.energy = area * 1.90
    a.data.size = 900
    a.location = key
    a.rotation_euler = (math.radians(32), 0, math.radians(-28))
    scene.collection.objects.link(a)
    target = bpy.data.objects.new("Target", None)
    scene.collection.objects.link(target)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = 60
    cam.data.clip_end = 20000
    scene.collection.objects.link(cam)
    scene.camera = cam
    tc = cam.constraints.new("TRACK_TO")
    tc.target = target
    tc.track_axis = "TRACK_NEGATIVE_Z"
    tc.up_axis = "UP_Y"
    return cam, target


def _cam(cam, target, cam_loc, tgt_loc, lens=60):
    cam.location = cam_loc
    cam.data.lens = lens
    target.location = tgt_loc


def _render(scene, name):
    scene.render.filepath = os.path.join(OUT_DIR, name)
    edge_collection = bpy.data.collections.get(ADAPTER_EDGE_COLLECTION)
    if edge_collection is None or len(edge_collection.objects) == 0:
        scene.render.use_freestyle = False
    bpy.ops.render.render(write_still=True)
    review_path = os.path.join(REVIEW_DIR, name)
    shutil.copy2(scene.render.filepath, review_path)
    print("RENDER:", name, flush=True)
    print("ZWISCHENSTAND:", review_path, flush=True)


# ==========================================================================
# Filter-Prädikate (Weltkoordinaten = Modellkoordinaten; STL-Import identisch)
# ==========================================================================
def _rad(c):
    return max(abs(c.x), abs(c.y))


def lapA_faces(c, n):
    """Fügeflächen der unteren Lappe am Stoß A (kanonisches +x-Band, nahe y=0)
    von seg0: horizontale Überlappungsschulter bei z=lap_h (+z) + Stirn bei
    y=-(LAP_L) (-y-Normal)."""
    in_band = c.x >= CUT_HALF - 6 and -(LAP_L + 3) <= c.y <= 3
    shelf = in_band and abs(c.z - LAP_H) < 1.0 and abs(n.z) > 0.55
    stirn = (n.y < -0.5 and c.x >= CUT_HALF - 6
             and c.y <= -(LAP_L - 4) and 0.5 < c.z < LAP_H + 0.4)
    return shelf or stirn


def stossB_faces(c, n):
    """Fügeflächen von seg0 am Stoß B (kanonisches +y-Band, nahe x=0):
    Überlappungsschulter bei z=lap_h + Stirnschulter bei x=LAP_L."""
    in_band = c.y >= CUT_HALF - 6 and -3 <= c.x <= LAP_L + 3
    shelf = in_band and abs(c.z - LAP_H) < 1.0 and abs(n.z) > 0.55
    stirn = (abs(n.x) > 0.5 and c.y >= CUT_HALF - 6
             and abs(c.x - LAP_L) < 3 and 0.5 < c.z < LAP_H + 0.4)
    return shelf or stirn


def mask_faces(c, n):
    """Maskierzone (Bild 08): Kleberführung + Abstandspad-Auflageflächen.

    Der zusätzliche Normalenfilter ist wichtig: Nur tatsächlich nach unten
    gerichtete Kontaktflächen werden markiert. Ohne ihn färbte der reine
    Schwerpunktfilter auch senkrechte Rillen-/Kragenwände und erzeugte in der
    Perspektive eine optisch ungleichmäßige, ausgefranste Gelbfläche.
    """
    r = _rad(c)
    downward = n.z < -0.55
    ring = (downward and G["mask_r_in"] <= r <= G["mask_r_out"]
            and c.z < 2.6)
    pads = (downward and c.z < 0.0
            and any(abs(r - pad_r) <= G["spacer_pad_radial"]
                    for pad_r in G["spacer_pad_radii"]))
    return ring or pads


def groove_faces(c, n):
    """Nur die Böden der zwei Kleberführungen (Bild 12).

    Die Einschränkung auf nach unten gerichtete Flächen nahe der Rillentiefe
    lässt die ungeschnittenen Entlüftungsbrücken der inneren Raupe sichtbar.
    Ein reiner Radialfilter würde auch deren Unterseite grün färben und damit
    fälschlich eine geschlossene innere Raupe zeigen.
    """
    r = _rad(c)
    in_bead = any(lo - 1.5 <= r <= hi + 1.5 for lo, hi in G["groove_ranges"])
    return (in_bead and abs(c.z - G["groove_d"]) < 0.2
            and n.z < -0.55)


# ==========================================================================
# Bilder
# ==========================================================================
def img01_titel_explosion():
    """Bild 01 (Titel): Explosionsansicht der vier Segmente mit aufgesetzter
    Belluna-Platte, Clips und Dichtring."""
    scene = _new_scene()
    segs = load_segments()
    for o in segs:
        c = sum((Vector(v) for v in o.bound_box), Vector()) / 8.0
        c = o.matrix_world @ c
        d = Vector((c.x, c.y, 0))
        if d.length > 1:
            o.location += d.normalized() * EX["radial_mm"]
    platte = load_part("platte", _mat("platte", COL_PLATTE, rough=0.5))
    clips = load_part("clips", _mat("clips", COL_CLIPS, rough=0.3, metallic=0.9))
    seal = load_part("dichtring", _mat("seal", COL_SEAL, rough=0.8))
    for o in (platte, clips, seal):
        o.location = (0, 0, EX["platte_z_mm"])
    cam, target = _rig(scene)
    _cam(cam, target, (980, -980, 720), (0, 0, 70))
    _render(scene, "01_titel_explosion.png")


def img02_teile_uebersicht():
    """Bild 02: Teileübersicht -- ein Segment neben Belluna-Platte, Clips und
    Dichtring im Lieferzustand."""
    scene = _new_scene()
    seg = load_seg(0)
    seg.location = (-330, -120, 0)
    platte = load_part("platte", _mat("platte", COL_PLATTE, rough=0.5))
    platte.location = (230, 0, 0)
    clips = load_part("clips", _mat("clips", COL_CLIPS, rough=0.28, metallic=0.92))
    clips.location = (230, 0, 0)
    seal = load_part("dichtring", _mat("seal", COL_SEAL, rough=0.8))
    # Lieferzustand: Die schwarze Runddichtung sitzt bereits in ihrer Tasche
    # zwischen Clip-Kragen und Haltesteg der Belluna-Originalplatte.
    seal.location = (230, 0, 0)
    cam, target = _rig(scene, area=90000)
    _cam(cam, target, (250, -1050, 640), (10, 0, 10), lens=52)
    _render(scene, "02_teile_uebersicht.png")


def img03_fuegeflaechen():
    """Bild 03: Fügeflächen der unteren Lappe (Stoß A) an Segment 0, grün
    hervorgehoben."""
    scene = _new_scene()
    seg = load_seg(0)
    highlight(seg, COL_GREEN, lapA_faces, emission=1.0)
    cam, target = _rig(scene, area=90000)
    _cam(cam, target, (360, -230, 210), (222, -12, 8), lens=85)
    _render(scene, "03_fuegeflaechen.png")


def img04_kleber_auftrag():
    """Bild 04: Klebstoffauftrag -- die beiden Überlappungsschultern des
    +y-Band-Stoßes (Stoß B), beide grün markiert. Das 2K-Epoxid kommt auf
    BEIDE Fügeflächen; einen Aktivatorschritt gibt es nicht mehr."""
    # Beide Fuegeflaechen (Ueberlappungsschulter) des geteilten +y-Band-Stosses
    # liegen bei x in [0, LAP_L], z=lap_h: seg0 haelt die obere (Schulter nach
    # -z), seg1 die untere Lappe (Schulter nach +z). Zwei nach oben/unten
    # zeigende Flaechen sind nur sichtbar, wenn die obere Haelfte (seg0)
    # angehoben und die Kamera ZWISCHEN beiden Schulterhoehen positioniert wird.
    scene = _new_scene()
    # Einheitlich weiße Basis für beide; nur die markierten Flächen tragen das
    # semantische Grün.
    neutral = COL_ASA
    seg0 = load_seg(0, tint=neutral)
    seg1 = load_seg(1, tint=neutral)
    highlight(seg0, COL_GREEN, stossB_faces, emission=1.2)
    highlight(seg1, COL_GREEN, stossB_faces, emission=1.2)
    seg0.location = (0, 0, 50)          # obere Stoßhälfte kompakt angehoben
    seg1.location = (0, 0, 0)
    # Kamera zwischen beiden Schulterhöhen und weiter zurück: beide markierten
    # Fügeflächen bleiben sichtbar, der frühere große Leerraum verschwindet.
    cam, target = _rig(scene, area=60000, key=(-220, -260, 650))
    _cam(cam, target, (80, -70, 31), (12, 214, 31), lens=55)
    _render(scene, "04_kleber_auftrag.png")


def img05_m5_montage():
    """Bild 05: M5-Verschraubung des Stoßes von oben, zwei Schraubachsen als
    Marker."""
    scene = _new_scene()
    load_segments()
    for m in MK["m5"][:2]:
        marker(m["p1"], m["p2"], radius=3.0)
    cam, target = _rig(scene)
    _cam(cam, target, (430, -140, 250), (228, -12, 12), lens=80)
    _render(scene, "05_m5_montage.png")


def img06_m5_mutter():
    """Bild 06: dieselbe M5-Verbindung von unten (Muttertaschen), Schraubachsen
    als Marker."""
    scene = _new_scene()
    load_segments()
    for m in MK["m5"][:2]:
        marker(m["p1"], m["p2"], radius=3.0)
    cam, target = _rig(scene, key=(-500, -700, -900))
    _cam(cam, target, (430, -140, -230), (228, -12, 8), lens=80)
    _render(scene, "06_m5_mutter.png")


def img07_rahmen_komplett():
    """Bild 07: kompletter verschraubter Rahmen mit allen M5-Stoßmarkern."""
    scene = _new_scene()
    load_segments()
    for m in MK["m5"]:
        marker(m["p1"], m["p2"], radius=2.6)
    cam, target = _rig(scene)
    _cam(cam, target, (860, -860, 600), (0, 0, 10))
    _render(scene, "07_rahmen_komplett.png")


def img08_maskierung_lack():
    """Bild 08: Lackmaskierung -- Kleberführungs- und Abstandspad-Auflageflächen
    gelb markiert (Schrägansicht von unten)."""
    scene = _new_scene()
    segs = load_segments()
    for o in segs:
        highlight(o, COL_YELLOW, mask_faces, emission=1.0)
    cam, target = _rig(scene, key=(-500, -700, -900))
    # Moderate 20°-Schrägansicht von unten: mehr räumliche Information als
    # die frühere Orthogonalansicht, aber deutlich weniger seitlich als die
    # alte Perspektive, in der der Unterkragen zwei Maskierseiten verdeckte.
    _cam(cam, target, (300, -300, -1200), (0, 0, -3), lens=52)
    _render(scene, "08_maskierung_lack.png")


def img09_dach_holzrahmen():
    """Bild 09: Halbschnitt des Dachaufbaus (Deckhaut, XPS-Kern, Holzrahmen) an
    der Schnittebene y=0."""
    # Halbschnitt (y>0 entfernt): Schnittflaeche bei y=0 zeigt nach +y -> Kamera
    # und Zusatzlicht auf die +y-Seite, sonst bleibt der Schnitt unbeleuchtet.
    scene = _new_scene()
    load_part("dach_ycut", _mat("dach", COL_DACH, rough=0.7))
    load_part("xps_kern_ycut", _mat("xps", COL_XPS, rough=0.9))
    load_part("holzrahmen_ycut", _mat("holz", COL_HOLZ, rough=0.55, emission=0.55))
    hz = G["roof_top_z"] - G["roof_t"] / 2       # Kern-Mittelhoehe
    cam, target = _rig(scene, area=95000, key=(240, 620, 430))
    _cam(cam, target, (330, 355, 28), (243, 4, hz), lens=64)
    _render(scene, "09_dach_holzrahmen.png")


def img10_aufsetzen():
    """Bild 10: Rahmen 60 mm über dem Dach schwebend vor dem Aufsetzen, der nach
    unten tauchende Unterkragen bleibt sichtbar."""
    # Rahmen schwebt 60 mm ueber dem Dach; Blick schraeg unten-vorne (Kamera
    # unter der angehobenen Rahmenunterseite, aber ueber der Dachoberkante),
    # damit der nach unten tauchende Unterkragen sichtbar bleibt.
    scene = _new_scene()
    segs = load_segments()
    for o in segs:
        o.location = (0, 0, 60)
    load_part("dach", _mat("dach", COL_DACH, rough=0.7))
    load_part("holzrahmen", _mat("holz", COL_HOLZ, rough=0.6))
    load_part("xps_kern", _mat("xps", COL_XPS, rough=0.9))
    cam, target = _rig(scene, area=95000, key=(-150, -620, 130))
    _cam(cam, target, (380, -600, 16), (0, -70, 52), lens=50)
    _render(scene, "10_aufsetzen.png")


def img11_hybrid_dachinterface():
    """Bild 11: transparenter Adapter über dem Dach, alle acht radialen
    Dachschraubachsen als Marker (Hybrid-Dachschnittstelle)."""
    scene = _new_scene()
    # Transparenter Adapter als technische Durchsicht: So bleiben alle acht
    # radialen Schraubachsen erkennbar, auch wenn sie geometrisch im Kragen
    # beziehungsweise im Holzrahmen liegen.
    load_segments(alpha=0.58)
    load_part("dach", _mat("dach", COL_DACH, rough=0.7, alpha=0.18))
    load_part("holzrahmen", _mat("holz", COL_HOLZ, rough=0.6, alpha=0.72,
                                  emission=0.35))
    load_part("xps_kern", _mat("xps", COL_XPS, rough=0.9, alpha=0.22))
    for m in MK["dach_screws"]:
        p1, p2 = Vector(m["p1"]), Vector(m["p2"])
        axis = (p2 - p1).normalized()
        marker(p1 - axis * 10.0, p2 + axis * 5.0, radius=3.3)
    cam, target = _rig(scene)
    _cam(cam, target, (740, -740, 360), (0, 0, -12), lens=58)
    _render(scene, "11_hybrid_dachinterface.png")


def img12_kleberaupe():
    """Bild 12: Böden der zwei unteren Kleberführungen grün markiert
    (Unteransicht)."""
    scene = _new_scene()
    segs = load_segments()
    for o in segs:
        highlight(o, COL_GREEN, groove_faces, emission=1.0)
    cam, target = _rig(scene, key=(-500, -700, -900))
    _cam(cam, target, (760, -760, -560), (0, 0, 0))
    _render(scene, "12_kleberaupe.png")


def img13_aussenkehle():
    """Bild 13: äußere Sikaflex-Schutzkehle als grüner Rundquadrat-Marker in der
    Außenfase über dem Dachspalt."""
    scene = _new_scene()
    load_segments()
    load_part("dach", _mat("dach", COL_DACH, rough=0.72))
    leg = G["weather_fillet_leg"]
    # Marker liegt in der konstruierten 4-mm-Außenfase und überbrückt den
    # 3-mm-Dachspalt. Grün bedeutet wie in Bild 12: Sikaflex-Arbeitsschritt.
    rounded_square_bead(
        "Aussenkehle",
        G["outer_half"] + 0.4,
        G["outer_r"] + 0.4,
        G["roof_top_z"] + leg * 0.42,
        leg,
    )
    cam, target = _rig(scene, area=95000, key=(-300, -650, 520))
    _cam(cam, target, (710, -710, 205), (0, 0, -1), lens=61)
    _render(scene, "13_aussenkehle.png")


def img14_platte_schrauben():
    """Bild 14: transparente Belluna-Platte mit acht Plattenschraubachsen als
    Marker, Clips deckend silbern."""
    scene = _new_scene()
    load_segments()
    load_part("platte", _mat("platte", COL_PLATTE, rough=0.5, alpha=0.30))
    # Die Metallclips gehören zur Belluna-Platte und bleiben trotz der für
    # die Schraubachsen transparenten Platte deckend silber sichtbar.
    load_part("clips", _mat("clips", COL_CLIPS, rough=0.28, metallic=0.92))
    for m in MK["plate_screws"]:
        marker(m["p1"], m["p2"], radius=3.0)
    cam, target = _rig(scene)
    _cam(cam, target, (760, -760, 540), (0, 0, 16), lens=60)
    _render(scene, "14_platte_schrauben.png")


def img15_fertig():
    """Bild 15: fertige Baugruppe mit deckender Belluna-Platte, Clips und
    Dichtring."""
    scene = _new_scene()
    load_segments()
    load_part("platte", _mat("platte", COL_PLATTE, rough=0.5))
    load_part("clips", _mat("clips", COL_CLIPS, rough=0.3, metallic=0.9))
    load_part("dichtring", _mat("dichtring", COL_SEAL, rough=0.8))
    cam, target = _rig(scene)
    _cam(cam, target, (880, -880, 640), (0, 0, 20))
    _render(scene, "15_fertig.png")


ALL = [img01_titel_explosion, img02_teile_uebersicht, img03_fuegeflaechen,
       img04_kleber_auftrag, img05_m5_montage, img06_m5_mutter,
       img07_rahmen_komplett, img08_maskierung_lack, img09_dach_holzrahmen,
       img10_aufsetzen, img11_hybrid_dachinterface, img12_kleberaupe,
       img13_aussenkehle, img14_platte_schrauben, img15_fertig]

# Optionaler Filter über Env ONLY_IMG (Komma-Liste von Nummern) für gezieltes
# Nachrendern einzelner Bilder während der Sichtprüfung.
only = os.environ.get("ONLY_IMG", "").strip()
sel = set(only.split(",")) if only else None
for fn in ALL:
    num = fn.__name__[3:5]
    if sel is None or num in sel:
        fn()

print("RENDER-ENDE", flush=True)
