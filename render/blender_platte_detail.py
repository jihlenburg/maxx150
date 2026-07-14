"""Einmal-Skript: Nahaufnahme des Schnittprofils des Platten-Mocks.
Aufruf: blender -b -P <dieses Skript> -- <stl_dir> <out_dir>"""
import math
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
STL_DIR, OUT_DIR = argv[0], argv[1]

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


def stl_import(path):
    before = set(bpy.data.objects)
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=path)
    else:
        bpy.ops.import_mesh.stl(filepath=path)
    return list(set(bpy.data.objects) - before)[0]


def mat(name, rgb, rough=0.45, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    return m


body = stl_import(os.path.join(STL_DIR, "platte_xcut.stl"))
body.data.materials.append(mat("kunststoff", (0.85, 0.85, 0.85)))
body.data.materials.append(mat("cut", (0.9, 0.35, 0.05), 0.6))
for poly in body.data.polygons:
    poly.use_smooth = False
    if abs(poly.center.x) < 0.05 and poly.normal.x > 0.9:
        poly.material_index = 1
clips = stl_import(os.path.join(STL_DIR, "clips_xcut.stl"))
clips.data.materials.append(mat("stahl", (0.72, 0.73, 0.75), 0.35, 0.9))
seal = stl_import(os.path.join(STL_DIR, "dichtring_xcut.stl"))
seal.data.materials.append(mat("gummi", (0.05, 0.05, 0.06), 0.85))
for o in (clips, seal):
    for poly in o.data.polygons:
        poly.use_smooth = False

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 5.5
sun.data.angle = math.radians(15)
sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(35))
scene.collection.objects.link(sun)
area = bpy.data.objects.new("Area", bpy.data.lights.new("Area", "AREA"))
area.data.energy = 60000
area.data.size = 400
area.location = (300, -500, 400)
area.rotation_euler = (math.radians(35), 0, math.radians(20))
scene.collection.objects.link(area)

target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.lens = 70
cam.data.clip_end = 10000
scene.collection.objects.link(cam)
scene.camera = cam
tc = cam.constraints.new("TRACK_TO")
tc.target = target
tc.track_axis = "TRACK_NEGATIVE_Z"
tc.up_axis = "UP_Y"

# Nahaufnahme auf das vordere Schnittprofil (y ~ -173..-225, z -20..24)
target.location = (0, -199, 2)
cam.location = (300, -270, 90)
scene.render.filepath = os.path.join(OUT_DIR, "p_schnitt_detail.png")
bpy.ops.render.render(write_still=True)
print("RENDER:", scene.render.filepath, flush=True)
print("RENDER-ENDE", flush=True)
