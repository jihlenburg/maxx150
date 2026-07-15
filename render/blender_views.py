"""Blender-Seite des Render-Workflows: rendert die Standardansichten aus den
STLs, die ``render/make_views_stl.py`` nach ``build/render/<hash>/`` legt.
Kamera-/Licht-/Materialeinstellungen aus der verifizierten Session-Vorlage
(render_v3.py / render_v3_schnitt.py) uebernommen.

Aufruf:  blender -b -P render/blender_views.py -- <stl_dir> <out_dir> [ansichten]
  stl_dir    Verzeichnis mit frame.stl, seg{0..3}.stl, frame_xcut.stl
             (Ausgabe von render/make_views_stl.py)
  out_dir    Zielverzeichnis fuer die PNGs (wird angelegt)
  ansichten  optionale Komma-Liste aus {iso_oben, iso_unten, explosion,
             einzelteil, schnitt}; Default: alle fuenf. Fuer einen schnellen
             Smoke-Test genuegt eine einzelne Ansicht, z. B. iso_oben.

Die Schnittebene fuer die orange Markierung der Schnittflaeche (Ansicht
"schnitt") kommt -- wie auf der FreeCAD-Seite -- aus der Umgebungsvariable
RENDER_XCUT (Default 120, siehe render/make_views_stl.py und Skill
maxx150-pipeline)."""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
STL_DIR = argv[0]
OUT_DIR = argv[1] if len(argv) > 1 else STL_DIR
VIEWS = set(argv[2].split(",")) if len(argv) > 2 else {
    "iso_oben", "iso_unten", "explosion", "einzelteil", "schnitt"}
XCUT = float(os.environ.get("RENDER_XCUT", "120"))

os.makedirs(OUT_DIR, exist_ok=True)

TINTS = [(0.85, 0.85, 0.85), (0.38, 0.48, 0.62), (0.85, 0.85, 0.85), (0.38, 0.48, 0.62)]


def _new_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 96
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 1125
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.19, 0.21, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    scene.world = world
    return scene


def _stl_import(path):
    before = set(bpy.data.objects)
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=path)
    else:
        bpy.ops.import_mesh.stl(filepath=path)
    return list(set(bpy.data.objects) - before)[0]


def _make_mat(name, rgb, rough=0.45):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


def _rig(scene, sun_energy=5.5, area_energy=120000):
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = sun_energy
    sun.data.angle = math.radians(15)
    sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(35))
    scene.collection.objects.link(sun)
    area = bpy.data.objects.new("Area", bpy.data.lights.new("Area", "AREA"))
    area.data.energy = area_energy
    area.data.size = 800
    area.location = (-500, -700, 900)
    area.rotation_euler = (math.radians(35), 0, math.radians(-30))
    scene.collection.objects.link(area)

    target = bpy.data.objects.new("Target", None)
    scene.collection.objects.link(target)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = 60
    cam.data.clip_end = 10000
    scene.collection.objects.link(cam)
    scene.camera = cam
    tc = cam.constraints.new("TRACK_TO")
    tc.target = target
    tc.track_axis = "TRACK_NEGATIVE_Z"
    tc.up_axis = "UP_Y"
    return cam, target


def _render(scene, path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDER:", path, flush=True)


def _load_assembly():
    segs = []
    for k in range(4):
        o = _stl_import(os.path.join(STL_DIR, f"seg{k}.stl"))
        o.name = f"seg{k}"
        o.data.materials.append(_make_mat(f"asa{k}", TINTS[k]))
        for poly in o.data.polygons:
            poly.use_smooth = False
        segs.append(o)
    return segs


def view_iso(tag, cam_loc, target_loc):
    scene = _new_scene()
    _load_assembly()
    cam, target = _rig(scene)
    cam.location = cam_loc
    target.location = target_loc
    _render(scene, os.path.join(OUT_DIR, f"v_{tag}.png"))


def view_explosion():
    scene = _new_scene()
    segs = _load_assembly()
    cam, target = _rig(scene)
    for o in segs:
        c = sum((Vector(v) for v in o.bound_box), Vector()) / 8.0
        c = o.matrix_world @ c
        d = Vector((c.x, c.y, 0))
        if d.length > 1:
            o.location += d.normalized() * 70
    cam.location = (900, -900, 620)
    target.location = (0, 0, 8)
    _render(scene, os.path.join(OUT_DIR, "v_explosion.png"))


def view_einzelteil():
    scene = _new_scene()
    segs = _load_assembly()
    cam, target = _rig(scene)
    for o in segs:
        o.location = (0, 0, 0)
        o.hide_render = True
    segs[0].hide_render = False
    cam.data.lens = 70
    cam.location = (520, 60, 330)
    target.location = (150, 150, 10)
    _render(scene, os.path.join(OUT_DIR, "v_einzelteil.png"))


def view_schnitt():
    scene = _new_scene()
    o = _stl_import(os.path.join(STL_DIR, "frame_xcut.stl"))
    o.data.materials.append(_make_mat("asa", (0.85, 0.85, 0.85)))
    o.data.materials.append(_make_mat("cut", (0.9, 0.35, 0.05), 0.6))
    for poly in o.data.polygons:
        poly.use_smooth = False
        if abs(poly.center.x - XCUT) < 0.05 and poly.normal.x > 0.9:
            poly.material_index = 1
    cam, target = _rig(scene)
    target.location = (XCUT / 2, 0, 8)
    cam.location = (700, -420, 310)
    _render(scene, os.path.join(OUT_DIR, "v_schnitt.png"))


if "iso_oben" in VIEWS:
    view_iso("iso_oben", (820, -820, 560), (0, 0, 8))
if "iso_unten" in VIEWS:
    view_iso("iso_unten", (780, -780, -520), (0, 0, 0))
if "explosion" in VIEWS:
    view_explosion()
if "einzelteil" in VIEWS:
    view_einzelteil()
if "schnitt" in VIEWS:
    view_schnitt()

print("RENDER-ENDE", flush=True)
