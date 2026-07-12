"""Beweist die komplette FEM-Kette am gebündelten Cantilever-Beispiel,
bevor eigenes CAD existiert. Nutzt femexamples aus dem FreeCAD-Bundle."""
import tempfile

import FreeCAD

BUNDLE_BIN = "/Applications/FreeCAD.app/Contents/Resources/bin"


def _ensure_binary_paths():
    g = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/Gmsh")
    if not g.GetString("gmshBinaryPath"):
        g.SetString("gmshBinaryPath", BUNDLE_BIN + "/gmsh")
    c = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/Ccx")
    if not c.GetString("ccxBinaryPath"):
        c.SetString("ccxBinaryPath", BUNDLE_BIN + "/ccx")


def _proxy_module(obj):
    """Modulname der Proxy-Klasse eines Scripted Objects -- robuster als der
    (je nach FreeCAD-Version/Beispiel wechselnde) Objektname."""
    proxy = getattr(obj, "Proxy", None)
    return type(proxy).__module__ if proxy is not None else ""


def _find_gmsh_mesh(doc):
    """API-Drift #1: femexamples.manager.get_meshname() liefert 'Mesh',
    nicht 'FEMMeshGmsh' wie in älteren Foren-Beispielen. Erst gängige Namen
    probieren, sonst per Proxy-Modul suchen -- das unterscheidet Gmsh- von
    Netgen-Meshes, die sich denselben TypeId 'Fem::FemMeshShapeBaseObjectPython'
    teilen und daher per isDerivedFrom() allein nicht auseinanderzuhalten sind."""
    for name in ("FEMMeshGmsh", "Mesh", "MeshGmsh"):
        obj = doc.getObject(name)
        if obj is not None:
            return obj
    for o in doc.Objects:
        if _proxy_module(o) == "femobjects.mesh_gmsh":
            return o
    return None


def _find_ccx_solver(doc):
    """API-Drift #2: 'SolverCcxTools' ist der Proxy-Klassenname, das
    Cantilever-Beispiel vergibt aber 'CalculiXCcxTools' als Objektname.
    Beide Namen probieren, sonst per Proxy-Modul suchen."""
    for name in ("SolverCcxTools", "CalculiXCcxTools"):
        obj = doc.getObject(name)
        if obj is not None:
            return obj
    for o in doc.Objects:
        if _proxy_module(o) == "femobjects.solver_ccxtools":
            return o
    return None


def test_cantilever_durch_gmsh_und_ccx():
    from femexamples.ccx_cantilever_faceload import setup
    from femmesh.gmshtools import GmshTools
    from femtools import ccxtools

    _ensure_binary_paths()
    doc = setup()

    mesh = _find_gmsh_mesh(doc)
    assert mesh is not None, (
        "Beispiel liefert kein Gmsh-Mesh-Objekt. Vorhandene Objekte: "
        f"{[o.Name for o in doc.Objects]}"
    )
    err = GmshTools(mesh).create_mesh()
    assert not err, f"Gmsh-Fehler: {err}"

    analysis = doc.getObject("Analysis")
    assert analysis is not None, (
        f"kein Analysis-Objekt. Vorhandene Objekte: {[o.Name for o in doc.Objects]}"
    )
    solver = _find_ccx_solver(doc)
    assert solver is not None, (
        "kein CalculiX-ccxtools-Solver gefunden. Vorhandene Objekte: "
        f"{[o.Name for o in doc.Objects]}"
    )

    fea = ccxtools.FemToolsCcx(analysis, solver)
    fea.update_objects()
    fea.setup_working_dir(tempfile.mkdtemp(prefix="fc_smoke_"))
    fea.setup_ccx()
    msg = fea.check_prerequisites()
    assert not msg, f"Voraussetzungen fehlen: {msg}"
    fea.purge_results()
    fea.run()
    fea.load_results()

    results = [o for o in doc.Objects if o.isDerivedFrom("Fem::FemResultObject")]
    assert results, "kein Ergebnisobjekt geladen"
    vm_max = max(results[0].vonMises)
    assert vm_max > 0.0 and vm_max < 1e6, f"unplausibles vonMises-Maximum {vm_max}"
    FreeCAD.closeDocument(doc.Name)
