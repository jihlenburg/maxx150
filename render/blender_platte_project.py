"""Projiziert die Mess-Ankerpunkte des Platten-Mocks in die Bildkoordinaten
der drei Render-Ansichten (gleiche Kameras wie render/blender_platte_mock.py)
-- KEIN Rendering, nur Geometrie. Ausgabe: out/belluna_platte/anno.json
mit {ansicht: {key: [u, v]}} in normierten Bildkoordinaten (0..1, v von unten).

Aufruf:  blender -b -P render/blender_platte_project.py
"""
import json
import os
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

OUT = os.path.join("out", "belluna_platte", "anno.json")

# Ankerpunkte (3D, Koordinaten des Mocks: z=0 Flansch-Unterseite).
# Stand: A6-verankerter Stapel (Kragen 173..176, Dichtung ..182, Steg ..184).
ANCHORS = {
    "oben": {
        "cam": (700, -700, 480), "tgt": (0, 0, 4),
        "punkte": {
            "a1ab":  (0, -225, 4),
            "band":  (60, -205, 4),
            "rib":   (0, -183, 12),
            "dicht": (0, -179, 9),
            "a3b":   (0, -174.5, 24),
            "clip":  (113, -171.8, 16),
            "open":  (0, -173, 6),
        },
    },
    "unten": {
        "cam": (660, -660, -450), "tgt": (0, 0, -4),
        "punkte": {
            "band_u": (-40, -221, 0),
            "a2a":    (40, -224, 0),
            "trog":   (0, -212, 1),
            "a4a":    (0, -197.5, -19),
            "floch":  (140, -197.5, -10),
            "gusset": (50, -190, -5),
            "a3ac":   (-60, -199, -12),
        },
    },
    "schnitt": {
        "cam": (620, -380, 260), "tgt": (-40, 0, 0),
        "punkte": {
            "flt":    (0, -220, 2),
            "trog2":  (0, -212, 1),
            "rib2":   (0, -183, 10),
            "dicht2": (0, -179, 7),
            "a3b2":   (0, -174.5, 20),
            "a4a2":   (0, -197.5, -17),
            "clip2":  (-113, -171.8, 16),
            "floch2": (-140, -197.5, -10),
        },
    },
}

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x = 1500
scene.render.resolution_y = 1125

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

result = {}
for view, spec in ANCHORS.items():
    cam.location = spec["cam"]
    target.location = spec["tgt"]
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    cam_eval = cam.evaluated_get(deps)
    result[view] = {}
    for key, p in spec["punkte"].items():
        uv = world_to_camera_view(scene, cam_eval, Vector(p))
        result[view][key] = [round(uv.x, 4), round(uv.y, 4)]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(result, f, indent=1)
print("ANNO-ENDE:", OUT)
sys.stdout.flush()
