"""Von-Mises-Heatmaps aller Lastfaelle: FEM -> Knotenspannungen -> Mapping auf
die Oberflaechen-Tessellation -> PLY mit Vertexfarben (Viridis) + Hotspot-
Liste (fem.heatmap.heatmap_all(), Task 15: Session-Erkenntnis "alle LF-
Hotspots sitzen am Noppenfuss" ging aus genau diesem Workflow hervor).

Reine Helferfunktionen (cmap, classify, write_ply, hotspots, voxel_index,
build_lookup, nearest_vm) sind FreeCAD-frei nutzbar/testbar (siehe
tests/test_tools_heatmap.py); run_capture()/heatmap_all() brauchen die
FreeCAD/Gmsh/CalculiX-Toolchain (wie fem.run_fem) und laufen nur unter
bin/fc. run_capture() ist bewusst KEIN Aufruf von fem.run_fem.run_case():
run_case liefert nur aggregierte PASS/FAIL-Kennzahlen, hier werden die
rohen Knotenspannungen+-koordinaten gebraucht -- Aufbau/Ablauf ist
identisch zu run_case, Helfer (_direction_ref, _ensure_binary_paths) werden
von dort importiert statt dupliziert."""
import json
import shutil
import tempfile
from pathlib import Path

import FreeCAD
import MeshPart
import ObjectsFem
from femmesh.gmshtools import GmshTools
from femtools import ccxtools

import params as PRM
from fem import loadcases as LC
from fem.material import fem_material_dict
from fem.run_fem import _direction_ref, _ensure_binary_paths
from model.frame import build_frame, top_z
from project_paths import heatmap_dir

VIRIDIS = [(0.267, 0.005, 0.329), (0.229, 0.322, 0.545), (0.128, 0.567, 0.551),
          (0.369, 0.788, 0.383), (0.993, 0.906, 0.144)]


def cmap(t: float):
    """Viridis-Interpolation, t in [0, 1] (wird geclampt) -> (r, g, b) 0..255."""
    t = max(0.0, min(1.0, t))
    x = t * (len(VIRIDIS) - 1)
    i = min(int(x), len(VIRIDIS) - 2)
    f = x - i
    a, b = VIRIDIS[i], VIRIDIS[i + 1]
    return tuple(int(255 * (a[k] + f * (b[k] - a[k]))) for k in range(3))


def classify(pt, p: PRM.Params = PRM.P) -> str:
    """Ordnet einen Oberflaechenpunkt (x, y, z) einer Bauteilzone zu, fuer die
    lesbare Hotspot-Beschriftung im Report. Zonengrenzen sind aus den
    Kammer-/Deckgeometrie-Parametern abgeleitet (model.frame._chamber_cuts/
    build_frame), NICHT hart codiert -- aendern sich mit, wenn INNER_WALL/
    CHAMBER_W/CHAMBER_RIB/DECK_T/BOTTOM_T/H_RAISE/GLUE_GAP angepasst werden.
    Toleranzfenster um die radialen Kammerring-Grenzen = CHAMBER_RIB (der
    Steg selbst ist die charakteristische Laenge dieser Uebergangszone):
    bei Default-Parametern reproduziert das exakt die frueher hart codierten
    Baender 204/212, 219/231, 246 (Session-Heatmap 2026-07-12)."""
    x, y, z = pt
    r = max(abs(x), abs(y))
    z_top = top_z(p)
    z_deck = z_top - p.DECK_T                          # Unterkante Deckplatte/Kammerdecke
    r_in1 = p.CUTOUT_W / 2 + p.INNER_WALL               # Innenwand->Kammerring 1
    r_out1 = r_in1 + p.CHAMBER_W                        # Kammerring 1->Steg
    r_in2 = r_out1 + p.CHAMBER_RIB                      # Steg->Kammerring 2
    r_out2 = r_in2 + p.CHAMBER_W                        # Kammerring 2->Aussenwand
    tol = p.CHAMBER_RIB

    if z < -0.5:
        return "Noppenfuß (Fixierstelle — Lagerkonzentration)"
    if z < p.BOTTOM_T + 0.5:
        return "Bodenplatte/Kleberille"
    if z > z_deck + 0.5:
        return "Deckplatte/Freistellung"
    if r > r_out2 + tol:
        return "Außenwand"
    if r_in1 - tol < r < r_in1 + tol:
        return "Innenwand (Schraubgrund)"
    if r_out1 - tol < r < r_in2 + tol:
        return "Kammersteg Ring1/Ring2"
    return "Kammerwand/-boden"


def write_ply(f, vertices, colors, facets):
    """Schreibt ein ASCII-PLY mit Vertexfarben auf ein file-like Objekt f
    (Produktion: offene Datei; Test: io.StringIO). vertices: Liste von
    (x, y, z)-Tupeln; colors: Liste von (r, g, b)-Tupeln (0..255); facets:
    Liste von (a, b, c)-Tupeln (0-basierte Vertex-Indizes, Dreiecke)."""
    f.write("ply\nformat ascii 1.0\n")
    f.write(f"element vertex {len(vertices)}\n")
    f.write("property float x\nproperty float y\nproperty float z\n")
    f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
    f.write(f"element face {len(facets)}\n")
    f.write("property list uchar int vertex_indices\nend_header\n")
    for (x, y, z), (r, g, b) in zip(vertices, colors):
        f.write(f"{x:.2f} {y:.2f} {z:.2f} {r} {g} {b}\n")
    for a, b_, c in facets:
        f.write(f"3 {a} {b_} {c}\n")


def voxel_index(pt, size=12.0):
    return (int(pt[0] // size), int(pt[1] // size), int(pt[2] // size))


def build_lookup(vm, coords):
    grid = {}
    for n, c in coords.items():
        if n in vm:
            grid.setdefault(voxel_index(c), []).append((c, vm[n]))
    return grid


def nearest_vm(grid, pt, size=12.0):
    ix, iy, iz = voxel_index(pt, size)
    best, best_d = 0.0, 1e18
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for c, v in grid.get((ix + dx, iy + dy, iz + dz), ()):
                    d = (c[0] - pt[0])**2 + (c[1] - pt[1])**2 + (c[2] - pt[2])**2
                    if d < best_d:
                        best_d, best = d, v
    return best


def hotspots(vm, coords, p: PRM.Params = PRM.P, k=6, min_dist=25.0):
    """Die k hoechsten, raeumlich getrennten (min_dist) Knoten je Lastfall,
    mit Bauteilzone. Reihenfolge: hoechste Spannung zuerst."""
    ranked = sorted(vm.items(), key=lambda kv: -kv[1])
    out = []
    for n, v in ranked:
        c = coords[n]
        if all((c[0] - o[1][0])**2 + (c[1] - o[1][1])**2 + (c[2] - o[1][2])**2 > min_dist**2
               for o in out):
            out.append((v, c, classify(c, p)))
            if len(out) >= k:
                break
    return out


def run_capture(shape, case, p: PRM.Params, mesh_mm: float):
    """Wie fem.run_fem.run_case, liefert aber die rohen Knotenspannungen +
    -koordinaten statt der aggregierten PASS/FAIL-Kennzahlen -- Grundlage
    fuer die Oberflaechen-Heatmap."""
    _ensure_binary_paths()
    doc = FreeCAD.newDocument("hm_" + case.name)
    try:
        geo = doc.addObject("Part::Feature", "Frame")
        geo.Shape = shape
        ana = ObjectsFem.makeAnalysis(doc, "Analysis")
        sol = ObjectsFem.makeSolverCalculiXCcxTools(doc, "Solver")
        sol.AnalysisType = "static"
        sol.GeometricalNonlinearity = "linear"
        ana.addObject(sol)

        mat = ObjectsFem.makeMaterialSolid(doc, "ASA")
        m = dict(mat.Material)
        m.update(fem_material_dict(p))
        mat.Material = m
        ana.addObject(mat)

        fix = ObjectsFem.makeConstraintFixed(doc, "Fix")
        fix.References = [(geo, case.fixed_faces(shape, p))]
        ana.addObject(fix)

        for i, (faces, vec, mag) in enumerate(case.loads(shape, p)):
            fo = ObjectsFem.makeConstraintForce(doc, f"Load{i}")
            fo.References = [(geo, faces)]
            fo.Force = f"{mag} N"
            fo.Direction = _direction_ref(doc, vec, f"Dir{i}")
            fo.Reversed = False
            ana.addObject(fo)

        mesh = ObjectsFem.makeMeshGmsh(doc, "Mesh")
        try:
            mesh.Shape = geo
        except Exception:
            mesh.Part = geo
        mesh.CharacteristicLengthMax = f"{mesh_mm} mm"
        mesh.ElementOrder = "2nd"
        mesh.SecondOrderLinear = True         # Pflicht -- sonst ccx-Fehler 201, siehe fem/run_fem.py
        ana.addObject(mesh)
        err = GmshTools(mesh).create_mesh()
        if err:
            raise RuntimeError(f"Gmsh: {err}")

        fea = ccxtools.FemToolsCcx(ana, sol)
        fea.update_objects()
        workdir = tempfile.mkdtemp(prefix=f"hm_{case.name}_")
        fea.setup_working_dir(workdir)
        fea.setup_ccx()
        msg = fea.check_prerequisites()
        if msg:
            raise RuntimeError(f"FEM-Voraussetzungen: {msg}")
        fea.purge_results()
        fea.run()
        fea.load_results()

        res = [o for o in doc.Objects if o.isDerivedFrom("Fem::FemResultObject")][0]
        nodes_prop = doc.getObject("Mesh").FemMesh.Nodes  # einmal heben, O(n)-Property!
        vm_by_node = {n: v for n, v in zip(res.NodeNumbers, res.vonMises)}
        coords = {n: (vec.x, vec.y, vec.z) for n, vec in nodes_prop.items()}
        return vm_by_node, coords
    finally:
        FreeCAD.closeDocument(doc.Name)
        if 'workdir' in dir():
            shutil.rmtree(workdir, ignore_errors=True)


def heatmap_all(p: PRM.Params = PRM.P, mesh_mm: float = None,
                out_dir: str | Path | None = None) -> dict:
    """Fuehrt alle Lastfaelle aus fem.loadcases.CASES aus, schreibt je Fall
    ein PLY (Oberflaechennetz, Vertexfarben auf das Fall-Maximum normiert)
    und eine gemeinsame heat_summary.json (vm_max + Hotspots je Fall) nach
    out_dir. mesh_mm=None -> p.MESH_MM (Produktionsnetz; Laufzeit mehrere
    Minuten -- KEIN Suite-Test, siehe tests/test_tools_heatmap.py)."""
    PRM.validate(p)
    mesh_mm = mesh_mm or p.MESH_MM
    out = Path(out_dir) if out_dir is not None else heatmap_dir(PRM.params_hash(p))
    out.mkdir(parents=True, exist_ok=True)

    frame = build_frame(p)
    surf = MeshPart.meshFromShape(frame, LinearDeflection=0.4, AngularDeflection=0.5,
                                  Relative=False)
    pts, facets = surf.Topology
    verts = [(pt.x, pt.y, pt.z) for pt in pts]
    print(f"Oberflächennetz: {len(verts)} Punkte, {len(facets)} Facetten", flush=True)

    summary = {}
    for name, case in LC.CASES.items():
        print(f"--- {name} ---", flush=True)
        vm_by_node, coords = run_capture(frame, case, p, mesh_mm)
        grid = build_lookup(vm_by_node, coords)
        vmax = max(vm_by_node.values())
        colors = [cmap(nearest_vm(grid, xyz) / vmax) for xyz in verts]

        ply_path = out / f"heat_{name}.ply"
        with open(ply_path, "w") as f:
            write_ply(f, verts, colors, facets)

        hs = hotspots(vm_by_node, coords, p)
        summary[name] = {
            "vm_max": vmax,
            "hotspots": [{"vm": round(v, 3), "xyz": [round(q, 1) for q in c], "zone": z}
                        for v, c, z in hs],
        }
        print(f"{name}: vm_max={vmax:.3f} -> {ply_path}", flush=True)

    summary_path = out / "heat_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print(f"HEATMAP-ENDE: {summary_path}", flush=True)
    return summary
