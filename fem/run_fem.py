"""Skriptierter CalculiX-Lauf für einen Lastfall (Muster aus Task-2-Smoke,
tests/test_toolchain.py: Binärpfade, Gmsh+ccxtools-Sequenz)."""
import os
import tempfile

import FreeCAD
import ObjectsFem
import Part
from FreeCAD import Vector
from femmesh.gmshtools import GmshTools
from femtools import ccxtools

import params as PRM
from fem.material import fem_material_dict
from model.frame import top_z

# FREECAD_BUNDLE ueberschreibt den Bundle-Wurzelpfad (Default: Standard-
# macOS-Installation) -- M5/Ledger 2/4/12/37, Task 16.
BUNDLE_BIN = os.environ.get("FREECAD_BUNDLE", "/Applications/FreeCAD.app") + \
    "/Contents/Resources/bin"


def _ensure_binary_paths():
    g = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/Gmsh")
    if not g.GetString("gmshBinaryPath"):
        g.SetString("gmshBinaryPath", BUNDLE_BIN + "/gmsh")
    c = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/Ccx")
    if not c.GetString("ccxBinaryPath"):
        c.SetString("ccxBinaryPath", BUNDLE_BIN + "/ccx")


def _direction_ref(doc, vec, name):
    """ConstraintForce braucht eine Kantenreferenz (LinkSub) als Richtung --
    baut dazu eine kurze Hilfslinie als Part::Feature."""
    line = Part.makeLine(Vector(0, 0, 0), Vector(vec).multiply(10.0))
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = line
    return (obj, ("Edge1",))


def run_case(shape, case, p: PRM.Params = PRM.P, mesh_mm: float = None) -> dict:
    """Führt einen Gmsh+CalculiX-Lauf für einen einzelnen Lastfall aus und
    liefert vm_max_MPa/defl_max_mm/defl_top_mm/allowable_MPa/PASS."""
    _ensure_binary_paths()
    mesh_mm = mesh_mm or p.MESH_MM
    doc = FreeCAD.newDocument("fem_" + case.name)
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
            mesh.Shape = geo          # FreeCAD 1.x
        except Exception:
            mesh.Part = geo           # Fallback ältere API
        mesh.CharacteristicLengthMax = f"{mesh_mm} mm"
        mesh.ElementOrder = "2nd"
        # Gerade Kanten statt echter Geometriekrümmung an den Zwischenknoten:
        # ohne das erzeugt Gmsh an kleinradiigen Details (Noppen R4, Vent-
        # Bohrungen Ø4, Außenfase 4 mm) im Verhältnis zur Elementgröße
        # umgeschlagene ("nonpositive jacobian") quadratische Tetraeder ->
        # CCX bricht mit Fehler 201 ab. SecondOrderLinear=True behebt das
        # (Root-Cause-Diagnose Task 9); Genauigkeitsverlust vernachlässigbar
        # gegenüber Bauteilabmessungen (>100 mm).
        mesh.SecondOrderLinear = True
        ana.addObject(mesh)
        err = GmshTools(mesh).create_mesh()
        if err:
            raise RuntimeError(f"Gmsh: {err}")

        fea = ccxtools.FemToolsCcx(ana, sol)
        fea.update_objects()
        fea.setup_working_dir(tempfile.mkdtemp(prefix=f"fc_{case.name}_"))
        fea.setup_ccx()
        msg = fea.check_prerequisites()
        if msg:
            raise RuntimeError(f"FEM-Voraussetzungen: {msg}")
        fea.purge_results()
        # femtools.ccxtools.FemToolsCcx.run() liefert True bei Erfolg, False
        # bei jedem Fehlerpfad (fehlende Voraussetzungen, .inp-Schreibfehler,
        # ccx-Binary nicht gefunden, ccx-Exitcode != 0 -- siehe
        # femtools/ccxtools.py::run() im FreeCAD-Bundle). Ohne diesen Check
        # lief die Pipeline bei einem stillen ccx-Fehlschlag einfach weiter
        # und stolperte erst weiter unten über einen IndexError auf der
        # (dann leeren) Ergebnisliste -- M3/Ledger 5/32, Diagnose-Härtung.
        rc = fea.run()
        if rc is not True:
            raise RuntimeError(
                f"CalculiX-Lauf ({case.name}) schlug fehl (fea.run() lieferte "
                f"{rc!r} statt True) -- ccx-Arbeitsverzeichnis: {fea.working_dir}"
            )
        fea.load_results()

        results = [o for o in doc.Objects if o.isDerivedFrom("Fem::FemResultObject")]
        if not results:
            raise RuntimeError(
                f"run_case ({case.name}): kein FEM-Ergebnisobjekt geladen trotz "
                f"fea.run()==True -- ccx-Arbeitsverzeichnis: {fea.working_dir}"
            )
        res = results[0]
        vm_max = max(res.vonMises)
        defl = [v.Length for v in res.DisplacementVectors]
        defl_max = max(defl)
        # Verformung der Deckflächen-Knoten (Dichtheitskriterium):
        try:
            fem_mesh = res.Mesh.FemMesh
        except Exception:
            fem_mesh = doc.getObject("Mesh").FemMesh
        # FemMesh.Nodes ist eine C++-Property, die bei JEDEM Zugriff das
        # komplette Knoten-Dict (~85k Vector-Einträge beim Grobnetz) neu
        # aufbaut -> einmal herausziehen, sonst O(n^2)-Falle (>570 s CPU
        # statt Millisekunden; Root-Cause-Diagnose Task 9).
        nodes = fem_mesh.Nodes
        zt = top_z(p)
        top_defl = [v.Length for v, n in zip(res.DisplacementVectors,
                                             res.NodeNumbers)
                    if abs(nodes[n].z - zt) < 0.5]
        # Submodell-Fall (z. B. fem/joint_check.py: die Lappen-Geometrie hat
        # gar keine Fläche bei top_z(p) des GESAMTrahmens) findet keine
        # Deckflächen-Knoten -- defl_top faellt dann auf defl_max zurueck,
        # was semantisch etwas anderes ist (Maximalverformung irgendwo im
        # Bauteil, nicht die Dichtheits-relevante Deckflaechenverformung).
        # Flag macht diesen Fallback fuer Report-Konsumenten sichtbar statt
        # ihn stillschweigend als echten Deckflaechenwert auszugeben (M3,
        # Ledger 32: "defl_top-Fallback semantisch irreführend im Submodell").
        defl_top_is_fallback = not top_defl
        defl_top = max(top_defl) if top_defl else defl_max
        allow = case.allowable(p)
        return {
            "vm_max_MPa": vm_max,
            "defl_max_mm": defl_max,
            "defl_top_mm": defl_top,
            "defl_top_is_fallback": defl_top_is_fallback,
            "allowable_MPa": allow,
            "PASS": vm_max <= allow and defl_top <= p.DEFL_TOP_MAX,
        }
    finally:
        FreeCAD.closeDocument(doc.Name)


def run_all_cases(shape, p: PRM.Params = PRM.P, mesh_mm: float = None) -> dict:
    from fem.loadcases import CASES
    return {name: run_case(shape, c, p, mesh_mm) for name, c in CASES.items()}
