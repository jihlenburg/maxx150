"""Blender-Seite fuer den Platten-Mock (render/belluna_platte_mock.py) --
NICHT Teil der Druck-Pipeline. Konventionen wie render/blender_views.py
(Cycles, 96 Samples, dunkler Hintergrund, TRACK_TO-Kamera, orange
Schnittflaechen bei x=0).

Aufruf:  blender -b -P render/blender_platte_mock.py -- <stl_dir> <out_dir>
Ansichten: p_iso_oben.png (Clip-Kragen), p_iso_unten.png (Trog/Kragen/
Gussets), p_schnitt.png (Halbschnitt x=0, Schnittflaechen orange).
"""
import math
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
STL_DIR = argv[0]
OUT_DIR = argv[1] if len(argv) > 1 else STL_DIR
os.makedirs(OUT_DIR, exist_ok=True)


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


def _make_mat(name, rgb, rough=0.45, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    return m


def _rig(scene):
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 5.5
    sun.data.angle = math.radians(15)
    sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(35))
    scene.collection.objects.link(sun)
    area = bpy.data.objects.new("Area", bpy.data.lights.new("Area", "AREA"))
    area.data.energy = 120000
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


def _load(cut=False):
    suffix = "_xcut" if cut else ""
    body = _stl_import(os.path.join(STL_DIR, f"platte{suffix}.stl"))
    body.data.materials.append(_make_mat("kunststoff", (0.85, 0.85, 0.85)))
    clips = _stl_import(os.path.join(STL_DIR, f"clips{suffix}.stl"))
    clips.data.materials.append(_make_mat("stahl", (0.72, 0.73, 0.75), 0.35, 0.9))
    teile = [body, clips]
    seal_path = os.path.join(STL_DIR, f"dichtring{suffix}.stl")
    if os.path.exists(seal_path):
        seal = _stl_import(seal_path)
        seal.data.materials.append(_make_mat("gummi", (0.05, 0.05, 0.06), 0.85))
        teile.append(seal)
    for o in teile:
        for poly in o.data.polygons:
            poly.use_smooth = False
    return body, clips


def view_iso(tag, cam_loc, target_loc):
    scene = _new_scene()
    _load()
    cam, target = _rig(scene)
    cam.location = cam_loc
    target.location = target_loc
    _render(scene, os.path.join(OUT_DIR, f"p_{tag}.png"))


def view_schnitt():
    scene = _new_scene()
    body, clips = _load(cut=True)
    cut_mat = _make_mat("cut", (0.9, 0.35, 0.05), 0.6)
    body.data.materials.append(cut_mat)
    for poly in body.data.polygons:
        if abs(poly.center.x) < 0.05 and poly.normal.x > 0.9:
            poly.material_index = 1
    cam, target = _rig(scene)
    target.location = (-40, 0, 0)
    cam.location = (620, -380, 260)
    _render(scene, os.path.join(OUT_DIR, "p_schnitt.png"))


view_iso("iso_oben", (700, -700, 480), (0, 0, 4))
view_iso("iso_unten", (660, -660, -450), (0, 0, -4))
view_schnitt()
print("RENDER-ENDE", flush=True)
