"""Erzeugt einen vollständigen OpenFOAM-simpleFoam-Referenzfall."""
from __future__ import annotations

from dataclasses import asdict
import json
import math
from pathlib import Path
import shutil
import subprocess

import params as PRM
from cfd.config import AERO, REFERENCE_CASE, CaseConfig, cfd_hash, selected_case
from project_paths import ROOT, cfd_dir


def _header(object_name: str, class_name: str = "dictionary") -> str:
    return f"""/* maxx150: generated, do not edit */
FoamFile
{{
    version 2.0;
    format ascii;
    class {class_name};
    object {object_name};
}}
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def _vector(values: tuple[float, float, float]) -> str:
    return "(" + " ".join(f"{value:.9g}" for value in values) + ")"


def _flow(case: CaseConfig) -> tuple[float, float, float]:
    yaw = math.radians(case.yaw_deg)
    return (case.speed_ms * math.cos(yaw), case.speed_ms * math.sin(yaw), 0.0)


def _wall_entries(kind: str, value: str) -> str:
    entries = []
    for patch in ("roof", "belluna", "adapter", "roofEdge"):
        entries.append(f"""
    {patch}
    {{
        type {kind};
        value uniform {value};
    }}""")
    return "".join(entries)


def _block_mesh_dict(case: CaseConfig) -> str:
    xmin, ymin, zmin = case.domain_min_m
    xmax, ymax, zmax = case.domain_max_m
    nx, ny, nz = case.base_cells
    return _header("blockMeshDict") + f"""
scale 1;
vertices
(
    ({xmin} {ymin} {zmin}) ({xmax} {ymin} {zmin})
    ({xmax} {ymax} {zmin}) ({xmin} {ymax} {zmin})
    ({xmin} {ymin} {zmax}) ({xmax} {ymin} {zmax})
    ({xmax} {ymax} {zmax}) ({xmin} {ymax} {zmax})
);
blocks
(
    hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1)
);
edges ();
boundary
(
    inlet {{ type patch; faces ((0 4 7 3)); }}
    outlet {{ type patch; faces ((1 2 6 5)); }}
    sideMinus {{ type symmetryPlane; faces ((0 1 5 4)); }}
    sidePlus {{ type symmetryPlane; faces ((3 7 6 2)); }}
    roof {{ type wall; faces ((0 3 2 1)); }}
    top {{ type symmetryPlane; faces ((4 5 6 7)); }}
);
mergePatchPairs ();
"""


def _snappy_dict(case: CaseConfig) -> str:
    fan_lo, fan_hi = case.fan_surface_level
    sec_lo, sec_hi = case.secondary_surface_level
    near_level = case.near_field_level
    return _header("snappyHexMeshDict") + f"""
castellatedMesh true;
snap true;
addLayers false;

geometry
{{
    belluna.stl {{ type triSurfaceMesh; name belluna; }}
    adapter.stl {{ type triSurfaceMesh; name adapter; }}
    roofEdge.stl {{ type triSurfaceMesh; name roofEdge; }}
    nearFan
    {{
        type searchableBox;
        min (-0.85 -0.65 0.0);
        max (1.05 0.65 0.45);
    }}
}}

castellatedMeshControls
{{
    maxLocalCells 1000000;
    maxGlobalCells 3000000;
    minRefinementCells 10;
    maxLoadUnbalance 0.10;
    nCellsBetweenLevels 3;
    features ();
    refinementSurfaces
    {{
        belluna
        {{
            level ({fan_lo} {fan_hi});
            patchInfo {{ type wall; }}
        }}
        adapter
        {{
            level ({sec_lo} {sec_hi});
            patchInfo {{ type wall; }}
        }}
        roofEdge
        {{
            level ({sec_lo} {sec_hi});
            patchInfo {{ type wall; }}
        }}
    }}
    resolveFeatureAngle 30;
    refinementRegions
    {{
        nearFan
        {{
            mode inside;
            levels ((1e15 {near_level}));
        }}
    }}
    locationInMesh (-1.5 0 0.75);
    allowFreeStandingZoneFaces true;
}}

snapControls
{{
    nSmoothPatch 5;
    tolerance 2.0;
    nSolveIter 50;
    nRelaxIter 8;
    nFeatureSnapIter 15;
    implicitFeatureSnap true;
    explicitFeatureSnap false;
    multiRegionFeatureSnap false;
}}

addLayersControls
{{
    relativeSizes true;
    layers {{}}
    expansionRatio 1.2;
    finalLayerThickness 0.3;
    minThickness 0.1;
    nGrow 0;
    featureAngle 60;
    nRelaxIter 3;
    nSmoothSurfaceNormals 1;
    nSmoothNormals 3;
    nSmoothThickness 10;
    maxFaceThicknessRatio 0.5;
    maxThicknessToMedialRatio 0.3;
    minMedialAxisAngle 90;
    nBufferCellsNoExtrude 0;
    nLayerIter 50;
}}

meshQualityControls
{{
    #includeEtc "caseDicts/mesh/generation/meshQualityDict.cfg"
}}
mergeTolerance 1e-6;
"""


def _initial_fields(case: CaseConfig) -> dict[str, str]:
    velocity = _flow(case)
    u = _vector(velocity)
    intensity_velocity = case.speed_ms * case.turbulence_intensity
    k_value = 1.5 * intensity_velocity**2
    omega = (math.sqrt(k_value) /
             (0.09**0.25 * case.turbulence_length_m))
    symmetry = """
    sideMinus { type symmetryPlane; }
    sidePlus { type symmetryPlane; }
    top { type symmetryPlane; }
"""
    fields = {}
    fields["U"] = _header("U", "volVectorField") + f"""
dimensions [0 1 -1 0 0 0 0];
internalField uniform {u};
boundaryField
{{
    inlet {{ type fixedValue; value uniform {u}; }}
    outlet
    {{
        type inletOutlet;
        inletValue uniform {u};
        value uniform {u};
    }}
    {_wall_entries("noSlip", "(0 0 0)")}
    {symmetry}
}}
"""
    fields["p"] = _header("p", "volScalarField") + f"""
dimensions [0 2 -2 0 0 0 0];
internalField uniform 0;
boundaryField
{{
    inlet {{ type zeroGradient; }}
    outlet {{ type fixedValue; value uniform 0; }}
    roof {{ type zeroGradient; }}
    belluna {{ type zeroGradient; }}
    adapter {{ type zeroGradient; }}
    roofEdge {{ type zeroGradient; }}
    {symmetry}
}}
"""
    for name, dimensions, initial, wall_type in (
        ("k", "[0 2 -2 0 0 0 0]", k_value, "kqRWallFunction"),
        ("omega", "[0 0 -1 0 0 0 0]", omega, "omegaWallFunction"),
    ):
        fields[name] = _header(name, "volScalarField") + f"""
dimensions {dimensions};
internalField uniform {initial:.9g};
boundaryField
{{
    inlet {{ type fixedValue; value uniform {initial:.9g}; }}
    outlet
    {{
        type inletOutlet;
        inletValue uniform {initial:.9g};
        value uniform {initial:.9g};
    }}
    {_wall_entries(wall_type, f"{initial:.9g}")}
    {symmetry}
}}
"""
    fields["nut"] = _header("nut", "volScalarField") + f"""
dimensions [0 2 -1 0 0 0 0];
internalField uniform 0;
boundaryField
{{
    inlet {{ type calculated; value uniform 0; }}
    outlet {{ type calculated; value uniform 0; }}
    {_wall_entries("nutkWallFunction", "0")}
    sideMinus {{ type symmetryPlane; }}
    sidePlus {{ type symmetryPlane; }}
    top {{ type symmetryPlane; }}
}}
"""
    return fields


def _control_dict(case: CaseConfig) -> str:
    flow = _flow(case)
    drag = tuple(value / case.speed_ms for value in flow)
    return _header("controlDict") + f"""
application simpleFoam;
startFrom startTime;
startTime 0;
stopAt endTime;
endTime {case.iterations};
deltaT 1;
writeControl timeStep;
writeInterval {case.iterations};
purgeWrite 1;
writeFormat binary;
writePrecision 8;
writeCompression off;
timeFormat general;
timePrecision 6;
runTimeModifiable true;

functions
{{
    forcesBelluna
    {{
        type forces;
        libs (forces);
        patches (belluna);
        rho rhoInf;
        rhoInf {case.air_density_kg_m3};
        CofR (0 0 {PRM.P.H_RAISE * 0.001});
        writeControl timeStep;
        writeInterval 5;
        log yes;
    }}
    forcesAdapter
    {{
        type forces;
        libs (forces);
        patches (adapter);
        rho rhoInf;
        rhoInf {case.air_density_kg_m3};
        CofR (0 0 0);
        writeControl timeStep;
        writeInterval 5;
        log yes;
    }}
    forceCoeffsBelluna
    {{
        type forceCoeffs;
        libs (forces);
        patches (belluna);
        rho rhoInf;
        rhoInf {case.air_density_kg_m3};
        CofR (0 0 {PRM.P.H_RAISE * 0.001});
        liftDir (0 0 1);
        dragDir {_vector(drag)};
        pitchAxis (0 1 0);
        magUInf {case.speed_ms};
        lRef {AERO.hood_length_mm * 0.001};
        Aref {PRM.P.A_HOOD};
        writeControl timeStep;
        writeInterval 5;
        log yes;
    }}
}}
"""


FV_SCHEMES = _header("fvSchemes") + """
ddtSchemes { default steadyState; }
gradSchemes
{
    default Gauss linear;
    grad(U) cellLimited Gauss linear 1;
}
divSchemes
{
    default none;
    div(phi,U) bounded Gauss linearUpwindV grad(U);
    turbulence bounded Gauss upwind;
    div(phi,k) $turbulence;
    div(phi,omega) $turbulence;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
wallDist { method meshWave; }
"""


FV_SOLUTION = _header("fvSolution") + r"""
solvers
{
    p
    {
        solver GAMG;
        smoother GaussSeidel;
        tolerance 1e-7;
        relTol 0.05;
    }
    Phi { $p; }
    U
    {
        solver smoothSolver;
        smoother GaussSeidel;
        tolerance 1e-8;
        relTol 0.1;
        nSweeps 1;
    }
    "(k|omega)"
    {
        solver smoothSolver;
        smoother GaussSeidel;
        tolerance 1e-8;
        relTol 0.1;
        nSweeps 1;
    }
}
SIMPLE
{
    nNonOrthogonalCorrectors 1;
    consistent yes;
    residualControl
    {
        p 1e-4;
        U 1e-5;
        "(k|omega)" 1e-5;
    }
}
potentialFlow { nNonOrthogonalCorrectors 10; }
relaxationFactors
{
    fields { p 0.3; }
    equations { U 0.7; k 0.7; omega 0.7; }
}
cache { grad(U); }
"""


def generate_case(case: CaseConfig = REFERENCE_CASE) -> Path:
    """Legt einen vollständigen OpenFOAM-Fallordner (0/, constant/, system/) an.

    Kopiert die zustandsabhängigen STL-Hüllen (belluna_<state>, adapter,
    roof_edge) aus dem CFD-Geometrie-Build-Baum, schreibt block-/snappy-/
    control-Dicts, Transport-/Turbulenz-Properties und Feldrandwerte sowie ein
    Provenienz-Manifest (Geometrie- und Fall-Commit). Erwartet vorher gebaute
    CFD-Geometrie; Rückgabe: Pfad des Fallordners."""
    digest = cfd_hash(case)
    root = cfd_dir(digest)
    geometry = root / "geometry"
    manifest_path = geometry / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(
            "CFD-Geometrie fehlt; zuerst ./bin/fc cfd/build_geometry.py ausführen"
        )
    target = root / "cases" / case.name
    if target.exists():
        shutil.rmtree(target)
    tri = target / "constant" / "triSurface"
    tri.mkdir(parents=True)
    state_source = geometry / f"belluna_{case.state}.stl"
    if not state_source.exists():
        raise RuntimeError(f"Unbekannter Haubenzustand: {case.state}")
    shutil.copy2(state_source, tri / "belluna.stl")
    shutil.copy2(geometry / "adapter.stl", tri / "adapter.stl")
    shutil.copy2(geometry / "roof_edge.stl", tri / "roofEdge.stl")

    _write(target / "system" / "blockMeshDict", _block_mesh_dict(case))
    _write(target / "system" / "snappyHexMeshDict", _snappy_dict(case))
    _write(target / "system" / "controlDict", _control_dict(case))
    _write(target / "system" / "fvSchemes", FV_SCHEMES)
    _write(target / "system" / "fvSolution", FV_SOLUTION)
    _write(target / "constant" / "transportProperties",
           _header("transportProperties") + f"""
transportModel Newtonian;
nu {case.kinematic_viscosity_m2_s};
""")
    _write(target / "constant" / "turbulenceProperties",
           _header("turbulenceProperties") + """
simulationType RAS;
RAS
{
    RASModel kOmegaSST;
    turbulence on;
    printCoeffs on;
}
""")
    for name, content in _initial_fields(case).items():
        _write(target / "0" / name, content)

    geometry_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    case_manifest = {
        "schema": 1,
        "cfd_hash": digest,
        "case": asdict(case),
        "geometry_manifest": str(manifest_path.relative_to(ROOT)),
        "geometry_source_commit": geometry_manifest["source_commit"],
        "case_source_commit": source_commit,
        "structural_use": "INFORMATIONAL_ONLY",
        "existing_wind_envelope_N": PRM.wind_force(PRM.P),
    }
    _write(target / "case_manifest.json",
           json.dumps(case_manifest, ensure_ascii=False, indent=2))
    print(f"CFD-FALL-ENDE: {target}", flush=True)
    return target


def main() -> None:
    """Generiert den per Umgebung gewählten CFD-Fall (``selected_case``)."""
    generate_case(selected_case())


if __name__ == "__main__":
    main()
