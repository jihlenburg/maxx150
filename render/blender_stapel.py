"""Blender-Seite der Baugruppen-Renderings (render/stapel_stl.py):
Iso-Gesamtansicht + X-Schnitt + Y-Schnitt. Konventionen wie
render/blender_views.py; Schnittflächen: Rahmen orange, Platte blau.

Aufruf:  blender -b -P render/blender_stapel.py -- <stl_dir> <out_dir>
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


def _mat(name, rgb, rough=0.45, metallic=0.0):
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


FARBEN = {"frame": ((0.85, 0.85, 0.85), 0.45, 0.0),
          "platte": ((0.62, 0.70, 0.82), 0.4, 0.0),
          "clips": ((0.72, 0.73, 0.75), 0.35, 0.9),
          "seal": ((0.05, 0.05, 0.06), 0.85, 0.0)}
CUT = {"frame": (0.9, 0.35, 0.05), "platte": (0.15, 0.45, 0.85)}


def _load(suffix, cut_axis=None):
    for name, (rgb, rough, met) in FARBEN.items():
        pfad = os.path.join(STL_DIR, f"{name}{suffix}.stl")
        if not os.path.exists(pfad):
            continue
        o = _stl_import(pfad)
        o.data.materials.append(_mat(name, rgb, rough, met))
        if cut_axis and name in CUT:
            o.data.materials.append(_mat(f"{name}_cut", CUT[name], 0.6))
            for poly in o.data.polygons:
                poly.use_smooth = False
                c = poly.center
                n = poly.normal
                wert = c.x if cut_axis == "x" else c.y
                nwert = n.x if cut_axis == "x" else n.y
                if abs(wert) < 0.05 and nwert > 0.9:
                    poly.material_index = 1
        else:
            for poly in o.data.polygons:
                poly.use_smooth = False


def _render(scene, name):
    scene.render.filepath = os.path.join(OUT_DIR, name)
    bpy.ops.render.render(write_still=True)
    print("RENDER:", name, flush=True)


# Iso-Gesamtansicht
scene = _new_scene()
_load("")
cam, target = _rig(scene)
cam.location = (820, -820, 560)
target.location = (0, 0, 12)
_render(scene, "stapel_iso.png")

# X-Schnitt (x>0 entfernt, Blick von +x)
scene = _new_scene()
_load("_xcut", "x")
cam, target = _rig(scene)
cam.location = (700, -420, 310)
target.location = (-60, 0, 10)
_render(scene, "stapel_schnitt_x.png")

# Y-Schnitt (y>0 entfernt, Blick von +y)
scene = _new_scene()
_load("_ycut", "y")
cam, target = _rig(scene)
cam.location = (-420, 700, 310)
target.location = (0, -60, 10)
_render(scene, "stapel_schnitt_y.png")

print("RENDER-ENDE", flush=True)
