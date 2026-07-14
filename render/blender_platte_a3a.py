"""Technischer Blender-Render zur eindeutigen Markierung von A3a.

Gezeigt wird die Unterseite der Belluna-Karosseriebefestigungsplatte. A3a ist
das Außenmaß des UNTEREN Einbaukragens, jeweils Außenkante zu Außenkante in X
und Y. Der Mock verwendet 398 mm nur als bisherige Annahme; die reale Platte
muss in beiden Richtungen gemessen werden.

Aufruf:
  blender -b -P render/blender_platte_a3a.py -- <stl_dir> <ausgabe.png>
"""
import math
import os
import sys

import bpy
from mathutils import Vector


argv = sys.argv[sys.argv.index("--") + 1:]
STL_DIR = argv[0]
OUT = argv[1]
os.makedirs(os.path.dirname(OUT), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1800
scene.render.resolution_y = 1800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False

world = bpy.data.worlds.new("A3a World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.025, 0.032, 0.045, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.32
scene.world = world


def material(name, color, roughness=0.45, metallic=0.0, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    emission_input = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
    if emission_input is not None:
        emission_input.default_value = (*color, 1)
    strength_input = bsdf.inputs.get("Emission Strength")
    if strength_input is not None:
        strength_input.default_value = emission
    return mat


MAT_BODY = material("Platte", (0.68, 0.72, 0.78), roughness=0.38)
MAT_COLLAR = material("A3a: unterer Einbaukragen", (1.0, 0.23, 0.035),
                      roughness=0.3, emission=0.12)
MAT_DIM = material("A3a Maß", (1.0, 0.09, 0.025), roughness=0.3, emission=0.5)
MAT_REF = material("400-mm-Referenz", (0.04, 0.58, 1.0), roughness=0.3, emission=0.5)
MAT_TEXT = material("Text", (0.94, 0.97, 1.0), roughness=0.45, emission=0.25)
MAT_WARN = material("Warnung", (1.0, 0.68, 0.04), roughness=0.35, emission=0.35)


def stl_import(path):
    before = set(bpy.data.objects)
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=path)
    else:
        bpy.ops.import_mesh.stl(filepath=path)
    return list(set(bpy.data.objects) - before)[0]


body = stl_import(os.path.join(STL_DIR, "platte.stl"))
body.name = "Belluna Karosseriebefestigungsplatte – Unterseite"
body.data.materials.append(MAT_BODY)
body.data.materials.append(MAT_COLLAR)

# Nur der UNTERE Kragen wird orange. Im ungedrehten Mock liegt er unter z=0
# und sein Außenradius bei 199 mm; Flansch, Gussets und oberer Clip-Kragen
# bleiben grau. Danach wird die ganze Platte für den Unterseitenblick gedreht.
for polygon in body.data.polygons:
    center = polygon.center
    radial = max(abs(center.x), abs(center.y))
    polygon.use_smooth = False
    if center.z < 0.6 and 194.0 <= radial <= 200.2:
        polygon.material_index = 1

body.rotation_euler[0] = math.pi


def line(name, p1, p2, radius, mat):
    p1 = Vector(p1)
    p2 = Vector(p2)
    direction = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=radius,
        depth=direction.length,
        location=(p1 + p2) / 2,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(direction.normalized())
    obj.data.materials.append(mat)
    return obj


def triangle(name, points, mat, z=25.2):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata([(x, y, z) for x, y in points], [], [(0, 1, 2)])
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    return obj


def text(name, value, location, size, mat, rotation=0.0, align="CENTER"):
    curve = bpy.data.curves.new(name + " Curve", "FONT")
    curve.body = value
    curve.align_x = align
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = 0.18
    curve.bevel_depth = 0.035
    curve.materials.append(mat)
    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    obj.rotation_euler[2] = rotation
    scene.collection.objects.link(obj)
    return obj


Z_REF = 24.1
Z_DIM = 25.2
COLLAR_HALF_ASSUMED = 199.0
CUTOUT_HALF = 200.0

# 400-mm-Dachausschnitt als Referenz. Beim 398-mm-Mock liegt die Linie nur
# 1 mm außerhalb des Kragens – genau deshalb ist die reale A3a-Messung nötig.
for idx, (a, b) in enumerate((
    ((-CUTOUT_HALF, -CUTOUT_HALF, Z_REF), (CUTOUT_HALF, -CUTOUT_HALF, Z_REF)),
    ((CUTOUT_HALF, -CUTOUT_HALF, Z_REF), (CUTOUT_HALF, CUTOUT_HALF, Z_REF)),
    ((CUTOUT_HALF, CUTOUT_HALF, Z_REF), (-CUTOUT_HALF, CUTOUT_HALF, Z_REF)),
    ((-CUTOUT_HALF, CUTOUT_HALF, Z_REF), (-CUTOUT_HALF, -CUTOUT_HALF, Z_REF)),
)):
    line(f"400-mm-Referenz {idx}", a, b, 0.7, MAT_REF)

# A3a-X: Außenkante zu Außenkante des unteren Kragens.
y_dim = -218.0
line("A3a-X Maßlinie", (-187, y_dim, Z_DIM), (187, y_dim, Z_DIM), 1.25, MAT_DIM)
line("A3a-X Hilfslinie links",
     (-COLLAR_HALF_ASSUMED, -196, Z_DIM), (-COLLAR_HALF_ASSUMED, -228, Z_DIM),
     0.75, MAT_DIM)
line("A3a-X Hilfslinie rechts",
     (COLLAR_HALF_ASSUMED, -196, Z_DIM), (COLLAR_HALF_ASSUMED, -228, Z_DIM),
     0.75, MAT_DIM)
triangle("A3a-X Pfeil links", [(-199, y_dim), (-187, y_dim + 5), (-187, y_dim - 5)], MAT_DIM)
triangle("A3a-X Pfeil rechts", [(199, y_dim), (187, y_dim + 5), (187, y_dim - 5)], MAT_DIM)

# A3a-Y: separat messen; Spritzguss und Einbau können in X/Y abweichen.
x_dim = 218.0
line("A3a-Y Maßlinie", (x_dim, -187, Z_DIM), (x_dim, 187, Z_DIM), 1.25, MAT_DIM)
line("A3a-Y Hilfslinie unten",
     (196, -COLLAR_HALF_ASSUMED, Z_DIM), (228, -COLLAR_HALF_ASSUMED, Z_DIM),
     0.75, MAT_DIM)
line("A3a-Y Hilfslinie oben",
     (196, COLLAR_HALF_ASSUMED, Z_DIM), (228, COLLAR_HALF_ASSUMED, Z_DIM),
     0.75, MAT_DIM)
triangle("A3a-Y Pfeil unten", [(x_dim, -199), (x_dim - 5, -187), (x_dim + 5, -187)], MAT_DIM)
triangle("A3a-Y Pfeil oben", [(x_dim, 199), (x_dim - 5, 187), (x_dim + 5, 187)], MAT_DIM)

text("Titel", "A3a – AUSSENMASS DES UNTEREN EINBAUKRAGENS",
     (0, 278, 26), 13.2, MAT_TEXT)
text("Untertitel", "In beiden Richtungen außen–außen messen",
     (0, 254, 26), 9.0, MAT_TEXT)
text("A3a-X", "A3a-X: HIER MESSEN", (0, -247, 26), 10.3, MAT_DIM)
text("A3a-Y", "A3a-Y: HIER MESSEN", (247, 0, 26), 10.3, MAT_DIM,
     rotation=math.pi / 2)
text("Kragenhinweis", "ORANGE = UNTERER KRAGEN\n(nicht der obere Clip-Kragen)",
     (0, 32, 26), 12.0, MAT_TEXT)
text("Referenzhinweis", "BLAU = 400 mm DACHAUSSCHNITT",
     (0, -42, 26), 8.0, MAT_REF)
text("Warnhinweis", "Mock: 398 mm NUR ANNAHME – reale Platte messen!",
     (0, -72, 26), 9.0, MAT_WARN)

# Beleuchtung und orthografische technische Draufsicht auf die umgedrehte
# Unterseite. Leichte Schatten erhalten die Kragenhöhe, ohne die Maßlinien zu
# verdunkeln.
area = bpy.data.objects.new("Softbox", bpy.data.lights.new("Softbox", "AREA"))
area.data.energy = 1450
area.data.shape = "DISK"
area.data.size = 520
area.location = (-160, -180, 520)
scene.collection.objects.link(area)

fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", "AREA"))
fill.data.energy = 700
fill.data.size = 400
fill.location = (280, 240, 360)
scene.collection.objects.link(fill)

cam_data = bpy.data.cameras.new("A3a Kamera")
camera = bpy.data.objects.new("A3a Kamera", cam_data)
scene.collection.objects.link(camera)
camera.location = (0, 0, 800)
camera.rotation_euler = (0, 0, 0)
camera.rotation_euler[0] = 0
camera.data.type = "ORTHO"
camera.data.ortho_scale = 610
camera.data.lens = 60
# Die Blender-Kamera blickt lokal entlang -Z; ohne Rotation schaut sie von
# oben korrekt auf den Ursprung.
scene.camera = camera

scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("A3A-RENDER:", OUT, flush=True)
