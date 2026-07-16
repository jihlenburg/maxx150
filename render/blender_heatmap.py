"""Blender-Seite des Heatmap-Workflows: importiert die PLY-Dateien (Vertex-
farben, Viridis) aus fem.heatmap.heatmap_all() und rendert je Lastfall zwei
Ansichten (oben/unten -- die Hotspots sitzen laut Task-15-Analyse an den
Abstandspads unten). Emission-Material aus Vertexfarben (render_heat.py-
Vorlage).

Aufruf:  blender -b -P render/blender_heatmap.py -- <ply_dir> <out_dir>
  ply_dir  Verzeichnis mit heat_<Lastfall>.ply (+ optional heat_summary.json
           fuer die vM-Max-Beschriftung), Ausgabe von fem.heatmap.heatmap_all()
  out_dir  Zielverzeichnis fuer die PNGs (Default: ply_dir)

Die Lastfaelle werden aus den vorhandenen heat_*.ply-Dateien ermittelt (kein
hartcodiertes LF1..LF4 -- funktioniert mit jeder fem.loadcases.CASES-Belegung)."""
import glob
import json
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
PLY_DIR = argv[0]
OUT_DIR = argv[1] if len(argv) > 1 else PLY_DIR
os.makedirs(OUT_DIR, exist_ok=True)

summary = {}
summary_path = os.path.join(PLY_DIR, "heat_summary.json")
if os.path.exists(summary_path):
    with open(summary_path) as f:
        summary = json.load(f)

CASES = sorted(os.path.splitext(os.path.basename(p))[0][len("heat_"):]
              for p in glob.glob(os.path.join(PLY_DIR, "heat_*.ply")))
if not CASES:
    raise SystemExit(f"Keine heat_*.ply in {PLY_DIR} gefunden -- "
                     f"fem.heatmap.heatmap_all() vorher laufen lassen.")


def _new_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1050
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.10, 0.10, 0.12, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    scene.world = world
    return scene


def _heat_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    emis = nt.nodes.new("ShaderNodeEmission")
    emis.inputs["Strength"].default_value = 1.0
    outn = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(attr.outputs["Color"], emis.inputs["Color"])
    nt.links.new(emis.outputs["Emission"], outn.inputs["Surface"])
    return m


scene = _new_scene()
target = bpy.data.objects.new("T", None)
target.location = (0, 0, 5)
scene.collection.objects.link(target)
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C"))
cam.data.lens = 55
cam.data.clip_end = 10000
scene.collection.objects.link(cam)
scene.camera = cam
tc = cam.constraints.new("TRACK_TO")
tc.target = target
tc.track_axis = "TRACK_NEGATIVE_Z"
tc.up_axis = "UP_Y"

for name in CASES:
    before = set(bpy.data.objects)
    path = os.path.join(PLY_DIR, f"heat_{name}.ply")
    if hasattr(bpy.ops.wm, "ply_import"):
        bpy.ops.wm.ply_import(filepath=path)
    else:
        bpy.ops.import_mesh.ply(filepath=path)
    o = list(set(bpy.data.objects) - before)[0]
    o.name = name
    o.data.materials.append(_heat_mat("hm_" + name))
    for poly in o.data.polygons:
        poly.use_smooth = False
    vmax = summary.get(name, {}).get("vm_max")
    label = f" (vM_max {vmax:.2f} MPa)" if vmax is not None else ""
    # zwei Ansichten je Fall: oben-iso und unten-iso (Hotspots sitzen unten!)
    for tag, loc, tz in (("oben", (760, -760, 520), 5), ("unten", (720, -720, -480), 0)):
        for other in bpy.data.objects:
            if other.type == "MESH":
                other.hide_render = other.name != name
        cam.location = loc
        target.location = (0, 0, tz)
        scene.render.filepath = os.path.join(OUT_DIR, f"hm_{name}_{tag}.png")
        bpy.ops.render.render(write_still=True)
        print(f"RENDER: {name} {tag}{label}", flush=True)

print("RENDER-ENDE", flush=True)
