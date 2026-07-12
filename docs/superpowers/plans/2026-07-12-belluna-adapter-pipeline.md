# Belluna-Adapterrahmen: Parametrische FreeCAD+FEM-Pipeline — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vollständig skriptierte Pipeline, die den 28-mm-Adapterrahmen für den Belluna Super Fan
parametrisch erzeugt, per CalculiX-FEM verifiziert und als Drucksegmente (STEP/STL/3MF) samt
Montagenotiz exportiert.

**Architecture:** Headless FreeCAD (`freecadcmd`) führt reine Python-Module aus: `params.py` →
`model/` (B-Rep-Geometrie) → `fem/` (Gmsh-Mesh, CalculiX, Analytik) → `export/` (Druckdateien,
Report). Eigener minimaler Testrunner (kein pytest im FreeCAD-Python). Spec:
`docs/superpowers/specs/2026-07-12-belluna-adapter-design.md`.

**Tech Stack:** FreeCAD 1.1.1 (Part, ObjectsFem, femmesh.gmshtools, femtools.ccxtools, MeshPart),
gebündeltes `ccx` und `gmsh`, Python 3.11 (FreeCAD-intern).

## Global Constraints

- FreeCAD headless: `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd` (verifiziert: Version 1.1.1; `ccx` und `gmsh` im Bundle unter `Contents/Resources/bin/`; **kein** Netgen-Python-Modul → Vernetzung ausschließlich Gmsh).
- Alle Ausführungen über den Wrapper `bin/fc` (Task 1). Tests: `bin/fc tests/run_tests.py`; Einzelfilter über Umgebungsvariable `TEST_FILTER=<substring>`.
- Einheiten: mm, N, MPa, °C. Koordinaten: Öffnung zentriert um (0,0); +x = Fahrtrichtung hinten (heckseitig); z=0 = Unterkante des Rahmenkörpers; Klebenoppen ragen bis z=−`GLUE_GAP`; Deckfläche bei z=`H_RAISE`−`GLUE_GAP`.
- Kennzahlen aus der Spec (müssen in Tests exakt so herauskommen): effektive Wandstärke 35+28=63 mm → 140er-Welle; Windlast 200 km/h → **480 N** (A_HOOD 0,108 m² aus MaxxFan-Deluxe-Maßblatt, mit SF 2; Amendment nach Task 2); Zulässigkeiten ASA bei 85 °C: 3,36 MPa dauerhaft / 8,4 MPa kurzzeitig (Kette 40 × 0,35 × 0,6 [× 0,4]).
- Keine externen Python-Pakete (kein pip, kein pytest) — nur FreeCAD-Bundle-Module + Stdlib.
- **Git: NIEMALS automatisch committen.** Globale User-Regel, überschreibt jede Skill-Vorgabe. Jeder Task endet mit „Checkpoint": Ergebnis melden, Commit-Freigabe des Users abwarten (Vorschlag für Commit-Message angeben).
- `out/` ist gitignored (generierte Artefakte).
- Zwischen `AskUserQuestion`-tauglichen Entscheidungen und Defaults: Defaults aus `params.py` verwenden, niemals blockieren — Messkampagnen-Werte ersetzt der User später selbst.

---

### Task 1: Projektgerüst, Parameter, Testrunner

**Files:**
- Create: `bin/fc`, `.gitignore`, `params.py`, `tests/run_tests.py`, `tests/test_params.py`

**Interfaces:**
- Produces: `params.Params` (frozen dataclass), Modul-Konstante `params.P`, Funktionen
  `effective_wall(p) -> float`, `select_shaft(p) -> float`, `outer_dims(p) -> (float, float)`,
  `wind_force(p) -> float`, `allowables(p) -> (float, float)`, `params_hash(p) -> str`.
  Alle späteren Tasks importieren `params` als `import params as PRM`.

- [ ] **Step 1: Wrapper + gitignore anlegen**

`bin/fc`:
```sh
#!/bin/sh
exec /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd "$@"
```

`.gitignore`:
```
out/
__pycache__/
*.FCStd1
```

Dann: `chmod +x bin/fc`

- [ ] **Step 2: Failing Test schreiben**

`tests/run_tests.py`:
```python
"""Minimaler Testrunner für freecadcmd (kein pytest im FreeCAD-Python).
Aufruf:  bin/fc tests/run_tests.py          — alle Tests
         TEST_FILTER=params bin/fc tests/run_tests.py — nur Dateien mit 'params'."""
import importlib.util
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main():
    flt = os.environ.get("TEST_FILTER", "")
    passed, failed = 0, 0
    for tf in sorted((ROOT / "tests").glob("test_*.py")):
        if flt and flt not in tf.name:
            continue
        spec = importlib.util.spec_from_file_location(tf.stem, tf)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception:
            print(f"LADEFEHLER {tf.name}")
            traceback.print_exc()
            failed += 1
            continue
        for name in sorted(dir(mod)):
            if name.startswith("test_") and callable(getattr(mod, name)):
                try:
                    getattr(mod, name)()
                    print(f"PASS {tf.stem}.{name}")
                    passed += 1
                except Exception:
                    print(f"FAIL {tf.stem}.{name}")
                    traceback.print_exc()
                    failed += 1
    print(f"\n{passed} bestanden, {failed} fehlgeschlagen")
    sys.exit(1 if failed else 0)


main()
```

`tests/test_params.py`:
```python
import params as PRM


def test_effective_wall_und_wellenwahl():
    assert PRM.effective_wall() == 63.0          # 35 Dach + 28 Adapter
    assert PRM.select_shaft() == 140.0           # Bereich 48-67 mm

def test_wellenwahl_grenzen():
    p = PRM.Params(ROOF_T=19.0)                  # 19+28=47 -> 120er (Obergrenze)
    assert PRM.select_shaft(p) == 120.0
    p = PRM.Params(ROOF_T=55.0)                  # 55+28=83 -> außerhalb
    try:
        PRM.select_shaft(p)
        assert False, "erwartete ValueError"
    except ValueError:
        pass

def test_windlast():
    assert abs(PRM.wind_force() - 444.4) < 1.0   # 200 km/h, cd 1.2, A 0.1, SF 2

def test_zulaessigkeiten():
    lang, kurz = PRM.allowables()
    assert abs(lang - 3.36) < 0.01               # 40*0.35*0.6*0.4
    assert abs(kurz - 8.40) < 0.01               # 40*0.35*0.6

def test_aussenmasse_und_hash():
    L, W = PRM.outer_dims()
    assert L == 500.0 and W == 500.0
    h1 = PRM.params_hash()
    h2 = PRM.params_hash(PRM.Params(H_RAISE=30.0))
    assert len(h1) == 8 and h1 != h2
```

- [ ] **Step 3: Test laufen lassen — muss fehlschlagen**

Run: `bin/fc tests/run_tests.py`
Expected: `LADEFEHLER test_params.py` (ModuleNotFoundError: params), Exit-Code 1.

- [ ] **Step 4: params.py implementieren**

`params.py`:
```python
"""Zentrale Parameterdatei — einzige Quelle der Wahrheit.
Längen mm, Kräfte N, Spannungen MPa, Temperaturen °C.
Quellen: Belluna-Anleitung (22 S.), Challenger-Dachdiagramm (35 mm X-Modelle),
Spec docs/superpowers/specs/2026-07-12-belluna-adapter-design.md.
Mit 'Messkampagne N' markierte Defaults sind Schätzwerte, die der User
per Messschieber ersetzt (Spec §8)."""
import hashlib
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Params:
    # --- Dachausschnitt / Fahrzeug ---
    CUTOUT_W: float = 400.0      # Sollmaß Ausschnitt (Anleitung, Messkampagne 6)
    CUTOUT_R: float = 5.0        # Eckenradius R5
    ROOF_T: float = 35.0         # Dachstärke X-Modelle (Messkampagne 8)
    EDGE_DIST: float = 250.0     # Ausschnitt-Hinterkante -> Dachkante (Messkampagne 7)
    EDGE_H: float = 55.0         # Höhe Dachkante über Dachebene (Messkampagne 7)
    # --- Haubengeometrie für Freigang-Check (Messkampagne 7) ---
    HOOD_TIP_REACH: float = 130.0   # horizontaler Haubenüberstand über Ausschnitt-Hinterkante
    HOOD_UNDERSIDE_H: float = 30.0  # Haubenunterkante am Überstand über Plattensitz
    CLEAR_MIN: float = 5.0          # geforderter Freigang
    H_CG: float = 160.0             # Angriffshöhe Windlast über Deckfläche
    # --- Erhöhung / Klebefuge ---
    H_RAISE: float = 28.0        # Zielerhöhung inkl. Klebespalt
    GLUE_GAP: float = 3.0        # Elastikfuge unten = Noppenhöhe (Thermik!)
    GLUE_SHEAR_CAP: float = 0.5  # zulässige Schubverzerrung der Fuge (50 %, Sika-Klasse)
    T_CURE: float = 20.0         # Verklebetemperatur
    # --- Deckflächenbreiten je Seite (Messkampagne 1/2) ---
    W_TOP_FRONT: float = 50.0
    W_TOP_REAR: float = 50.0
    W_TOP_LEFT: float = 50.0
    W_TOP_RIGHT: float = 50.0
    R_OUT: float = 12.0          # Außeneckenradius
    # --- Freistellung Gussets oben innen (Messkampagne 4) ---
    REC_GUSSET_W: float = 18.0
    REC_GUSSET_D: float = 3.0
    # --- Unterseite: Kleberille + Noppen ---
    GROOVE_OFF: float = 15.0     # Rillenbeginn ab Öffnungskante
    GROOVE_W: float = 8.0
    GROOVE_D: float = 2.0
    NOPPLE_R: float = 4.0
    NOPPLE_SPACING: float = 60.0
    CHAMFER_OUT: float = 4.0     # Fase Außenkante unten (Sika-Kehle)
    # --- Segmentierung ---
    N_SEGMENTS: int = 4          # nur 4 unterstützt (Quadranten)
    LAP_L: float = 25.0          # Halbüberlappung am Stoß
    TOL_JOINT: float = 0.25      # Passungsluft je Fügefläche
    JOINT_BOLT_D: float = 4.5    # M4-Durchgang
    JOINT_BOLT_OFF: float = 35.0 # Bolzenlage ab Öffnungskante (kollidiert nicht mit Rille)
    JOINT_CB_D: float = 8.5     # Zylindersenkung Kopf (DIN912 M4)
    JOINT_CB_T: float = 4.5
    JOINT_NUT_AF: float = 7.4    # Sechskant-Schlüsselweite Muttertasche
    JOINT_NUT_T: float = 3.5
    SEG_MAX_BBOX: float = 300.0  # zulässige Segment-Boundingbox (Druckservice)
    # --- Lüfter / Lasten (Spec §3/§6) ---
    FAN_MASS: float = 6.5        # kg (Maxxfan-Hüllkurve; Belluna 5.0)
    V_DESIGN_KMH: float = 200.0  # 160 Reise + Böenreserve
    CD_HOOD: float = 1.2
    A_HOOD: float = 0.10         # m² projiziert, Haube offen
    SF_WIND: float = 2.0
    G_VERT: float = 4.0          # Schlechtweg vertikal
    G_LAT: float = 2.0           # Schlechtweg quer
    CLAMP_FORCE: float = 2400.0  # 4 x 600 N aus 0,7 Nm (Anleitung), konservativ
    SNOW_LOAD: float = 200.0     # N auf Grundfläche
    T_MIN: float = -20.0
    T_MAX: float = 85.0
    # --- Material ASA (23 °C Basiswerte) + Abminderung (Spec §6) ---
    E_BASE: float = 2000.0
    SIGMA_BASE: float = 40.0
    NU: float = 0.35
    RHO: float = 1070.0          # kg/m^3
    CTE_ASA: float = 90e-6       # 1/K
    CTE_ROOF: float = 25e-6      # 1/K (GFK)
    DERATE_TEMP: float = 0.35    # bei 85 °C
    DERATE_Z: float = 0.6        # FDM-Schichthaftung
    DERATE_CREEP: float = 0.4    # Dauerlast
    INFILL_FACTOR: float = 0.5   # Homogenisierung >=4 Perimeter + 40 % Gyroid
    # --- FEM-Steuerung ---
    MESH_MM: float = 10.0        # Produktionsnetz
    MESH_MM_TEST: float = 20.0   # Grobnetz für Tests
    DEFL_TOP_MAX: float = 0.5    # zulässige Deckflächenverformung (Dichtheit)


P = Params()

# Vierkantwellen laut Anleitung: (Länge, Wandstärke min, max)
SHAFT_TABLE = ((120.0, 27.0, 47.0), (140.0, 48.0, 67.0), (160.0, 68.0, 80.0))


def effective_wall(p: Params = P) -> float:
    """Einbauwandstärke aus Lüftersicht: Dach + Adapter (inkl. Klebefuge)."""
    return p.ROOF_T + p.H_RAISE


def select_shaft(p: Params = P) -> float:
    t = effective_wall(p)
    for length, lo, hi in SHAFT_TABLE:
        if lo <= t <= hi:
            return length
    raise ValueError(f"Effektive Wandstärke {t} mm außerhalb 27-80 mm")


def outer_dims(p: Params = P):
    """(Länge in x = Fahrtrichtung, Breite in y)."""
    return (p.CUTOUT_W + p.W_TOP_FRONT + p.W_TOP_REAR,
            p.CUTOUT_W + p.W_TOP_LEFT + p.W_TOP_RIGHT)


def wind_force(p: Params = P) -> float:
    """Horizontale Auslegungswindlast inkl. Sicherheitsfaktor (N)."""
    v = p.V_DESIGN_KMH / 3.6
    q = 0.5 * 1.2 * v * v            # Staudruck, rho_Luft 1.2 kg/m^3
    return q * p.A_HOOD * p.CD_HOOD * p.SF_WIND


def allowables(p: Params = P):
    """(dauerhaft, kurzzeitig) zulässige von-Mises-Spannung in MPa."""
    kurz = p.SIGMA_BASE * p.DERATE_TEMP * p.DERATE_Z
    return kurz * p.DERATE_CREEP, kurz


def params_hash(p: Params = P) -> str:
    """8-Zeichen-Hash über alle Parameter (verknüpft Report <-> Druckdateien)."""
    blob = repr(sorted(asdict(p).items())).encode()
    return hashlib.sha256(blob).hexdigest()[:8]
```

- [ ] **Step 5: Tests laufen lassen — müssen bestehen**

Run: `bin/fc tests/run_tests.py`
Expected: `5 bestanden, 0 fehlgeschlagen`, Exit-Code 0.

- [ ] **Step 6: Checkpoint** — Ergebnis melden, User um Commit-Freigabe fragen.
Vorschlag: `feat: Projektgerüst mit params.py und Testrunner`

---

### Task 2: FEM-Toolchain-Smoke (Gmsh + CalculiX headless)

**Files:**
- Create: `tests/test_toolchain.py`

**Interfaces:**
- Produces: Gewissheit, dass Gmsh-Mesh + ccx-Lauf + Ergebnislesen headless funktionieren.
  Das hier etablierte Muster (Binärpfade setzen, `GmshTools`, `ccxtools.FemToolsCcx`,
  Result-Objekt) wird in Task 8/9 wiederverwendet.

- [ ] **Step 1: Failing Test schreiben**

`tests/test_toolchain.py`:
```python
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


def test_cantilever_durch_gmsh_und_ccx():
    from femexamples.ccx_cantilever_faceload import setup
    from femmesh.gmshtools import GmshTools
    from femtools import ccxtools

    _ensure_binary_paths()
    doc = setup()
    mesh = doc.getObject("FEMMeshGmsh")
    assert mesh is not None, "Beispiel liefert kein Gmsh-Mesh-Objekt"
    err = GmshTools(mesh).create_mesh()
    assert not err, f"Gmsh-Fehler: {err}"

    analysis = doc.getObject("Analysis")
    solver = doc.getObject("SolverCcxTools") or doc.getObject("CalculiXCcxTools")
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
```

- [ ] **Step 2: Test laufen lassen**

Run: `TEST_FILTER=toolchain bin/fc tests/run_tests.py`
Expected: PASS in < 2 min. Falls FAIL wegen Objektnamen (`SolverCcxTools` vs. andere):
Objektliste mit `print([o.Name for o in doc.Objects])` prüfen und Namen anpassen —
das ist der Zweck dieses Tasks: API-Drift HIER auffangen, nicht in Task 9.

- [ ] **Step 3: Checkpoint** — melden (inkl. gemessener Laufzeit), Commit-Freigabe erfragen.
Vorschlag: `test: FEM-Toolchain-Smoke (Gmsh+CalculiX headless)`

---

### Task 3: Geometrie-Helfer `model/features.py`

**Files:**
- Create: `model/__init__.py` (leer), `model/features.py`, `tests/test_features.py`

**Interfaces:**
- Produces: `rounded_box(l, w, h, r, origin=Vector(0,0,0)) -> Part.Shape`,
  `ring(outer_l, outer_w, r_out, inner_l, inner_w, r_in, h) -> Part.Shape` (zentriert um 0,0, z ab 0),
  `hex_prism(af, h, center_xy, z0) -> Part.Shape` (af = Schlüsselweite),
  `rect_path_points(half_x, half_y, spacing) -> list[(x, y)]` (Punkte auf Rechteckumfang).
  Konsumiert von `frame.py` und `segments.py`.

- [ ] **Step 1: Failing Test schreiben**

`tests/test_features.py`:
```python
import math

from model import features as F


def test_rounded_box_volumen():
    s = F.rounded_box(100, 60, 20, 10)
    v_erw = 100 * 60 * 20 - (4 - math.pi) * 10**2 * 20   # Eckenabzug
    assert s.isValid()
    assert abs(s.Volume - v_erw) < 1.0

def test_ring_volumen_und_zentrierung():
    s = F.ring(500, 500, 12, 400, 400, 5, 25)
    a_out = 500 * 500 - (4 - math.pi) * 12**2
    a_in = 400 * 400 - (4 - math.pi) * 5**2
    assert abs(s.Volume - (a_out - a_in) * 25) < 5.0
    bb = s.BoundBox
    assert abs(bb.XMin + 250) < 1e-6 and abs(bb.XMax - 250) < 1e-6
    assert abs(bb.ZMin) < 1e-9 and abs(bb.ZMax - 25) < 1e-9

def test_hex_prism():
    s = F.hex_prism(7.4, 3.5, (10, 20), 0)
    a_hex = 2 * math.sqrt(3) * (7.4 / 2) ** 2             # Fläche über Schlüsselweite
    assert abs(s.Volume - a_hex * 3.5) < 0.5
    assert abs(s.BoundBox.Center.x - 10) < 0.01

def test_rect_path_points():
    pts = F.rect_path_points(100, 100, 60)
    assert len(pts) >= 12                                  # Umfang 800 / 60 aufgerundet je Seite
    for x, y in pts:
        assert abs(abs(x) - 100) < 1e-6 or abs(abs(y) - 100) < 1e-6
```

- [ ] **Step 2: Run — Expected FAIL** (`ModuleNotFoundError: model`):
`TEST_FILTER=features bin/fc tests/run_tests.py`

- [ ] **Step 3: Implementieren**

`model/features.py`:
```python
"""Wiederverwendbare Geometrie-Bausteine (reines Part-API, kein Dokument nötig)."""
import math

import Part
from FreeCAD import Vector


def _vertical_edges(solid, tol=1e-7):
    out = []
    for e in solid.Edges:
        vs = e.Vertexes
        if (len(vs) == 2 and abs(vs[0].X - vs[1].X) < tol
                and abs(vs[0].Y - vs[1].Y) < tol):
            out.append(e)
    return out


def rounded_box(l, w, h, r, origin=Vector(0, 0, 0)):
    box = Part.makeBox(l, w, h, origin)
    if r > 0:
        box = box.makeFillet(r, _vertical_edges(box))
    return box


def ring(outer_l, outer_w, r_out, inner_l, inner_w, r_in, h):
    """Rechteckring, zentriert um (0,0), z von 0 bis h."""
    outer = rounded_box(outer_l, outer_w, h, r_out,
                        Vector(-outer_l / 2, -outer_w / 2, 0))
    inner = rounded_box(inner_l, inner_w, h + 2, r_in,
                        Vector(-inner_l / 2, -inner_w / 2, -1))
    return outer.cut(inner)


def hex_prism(af, h, center_xy, z0):
    """Sechskantprisma (Muttertasche); af = Schlüsselweite."""
    r = af / 2 / math.cos(math.pi / 6)      # Umkreisradius
    cx, cy = center_xy
    pts = [Vector(cx + r * math.cos(a), cy + r * math.sin(a), z0)
           for a in [math.pi / 6 + i * math.pi / 3 for i in range(6)]]
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire).extrude(Vector(0, 0, h))


def rect_path_points(half_x, half_y, spacing):
    """Punkte auf dem Umfang eines Rechtecks (±half_x, ±half_y), von den Ecken
    um spacing/3 zurückgezogen, Abstand <= spacing."""
    pts = []

    def line(p0, p1):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        length = math.hypot(dx, dy)
        n = max(2, math.ceil(length / spacing) + 1)   # ceil: sonst Abstand > spacing
        for i in range(n):
            t = i / (n - 1)
            pts.append((p0[0] + t * dx, p0[1] + t * dy))

    m = spacing / 3
    line((-half_x + m, -half_y), (half_x - m, -half_y))
    line((-half_x + m, half_y), (half_x - m, half_y))
    line((-half_x, -half_y + m), (-half_x, half_y - m))
    line((half_x, -half_y + m), (half_x, half_y - m))
    return pts
```

`model/__init__.py`: leere Datei.

- [ ] **Step 4: Run — Expected PASS**: `TEST_FILTER=features bin/fc tests/run_tests.py`
→ `4 bestanden, 0 fehlgeschlagen`

- [ ] **Step 5: Checkpoint** — Commit-Freigabe erfragen.
Vorschlag: `feat: Geometrie-Helfer (rounded_box, ring, hex_prism, rect_path_points)`

---

### Task 4: Monolith-Rahmen `model/frame.py`

**Files:**
- Create: `model/frame.py`, `tests/test_frame.py`

**Interfaces:**
- Consumes: `params`, `model.features`
- Produces: `build_frame(p=PRM.P) -> Part.Shape` — wasserdichter Volumenkörper:
  Ring 500×500/400×400, Körper z 0..25, Noppen z −3..0, Gusset-Freistellung oben innen,
  Kleberille unten, Außenfase unten. Konsumiert von `segments.py`, `fem/`, `export/`.
  Außerdem `top_z(p) -> float` (= `H_RAISE - GLUE_GAP`).

- [ ] **Step 1: Failing Test schreiben**

`tests/test_frame.py`:
```python
import params as PRM
from model.frame import build_frame, top_z


def _frame():
    global _CACHED
    try:
        return _CACHED
    except NameError:
        _CACHED = build_frame()
        return _CACHED

def test_valide_und_wasserdicht():
    s = _frame()
    assert s.isValid()
    assert len(s.Shells) == 1 and s.Shells[0].isClosed()

def test_hauptmasse():
    s = _frame()
    bb = s.BoundBox
    assert abs(bb.XLength - 500.0) < 0.01 and abs(bb.YLength - 500.0) < 0.01
    assert abs(bb.ZMin + PRM.P.GLUE_GAP) < 1e-6          # Noppen bis -3
    assert abs(bb.ZMax - top_z()) < 1e-6                 # Deckfläche bei 25

def test_oeffnung_bleibt_400():
    s = _frame()
    # Prüfkörper in der Öffnung darf den Rahmen nicht schneiden. Die Öffnung
    # hat R5-Ecken, daher gerundeter Prüfkörper (R5.5 > R5 bei 0.1 mm Inset):
    from FreeCAD import Vector
    from model import features as F
    probe = F.rounded_box(399.8, 399.8, 40, 5.5, Vector(-199.9, -199.9, -5))
    assert s.common(probe).Volume < 1e-6

def test_volumen_plausibel():
    v = _frame().Volume
    assert 1.9e6 < v < 2.4e6, f"Volumen {v/1e6:.2f} l unplausibel"

def test_deckflaeche_vorhanden():
    s = _frame()
    zt = top_z()
    top_area = sum(f.Area for f in s.Faces
                   if abs(f.CenterOfMass.z - zt) < 1e-4)
    assert top_area > 60000, "zu wenig plane Klebefläche oben"
```

- [ ] **Step 2: Run — Expected FAIL**: `TEST_FILTER=frame bin/fc tests/run_tests.py`
(ModuleNotFoundError: model.frame)

- [ ] **Step 3: Implementieren**

`model/frame.py`:
```python
"""Monolithischer Adapterrahmen (vor Segmentierung)."""
import Part
from FreeCAD import Vector

import params as PRM
from model import features as F


def top_z(p: PRM.Params = PRM.P) -> float:
    return p.H_RAISE - p.GLUE_GAP


def _nopple_positions(p):
    """Zwei Noppenringe: innen (zwischen Öffnung und Rille) und außen
    (zwischen Rille und Außenkante)."""
    inner_r = p.CUTOUT_W / 2 + p.GROOVE_OFF / 2                       # ~207.5
    outer_r = p.CUTOUT_W / 2 + p.GROOVE_OFF + p.GROOVE_W + 12         # ~235
    pts = F.rect_path_points(inner_r, inner_r, p.NOPPLE_SPACING)
    pts += F.rect_path_points(outer_r, outer_r, p.NOPPLE_SPACING)
    return pts


def build_frame(p: PRM.Params = PRM.P) -> Part.Shape:
    L, W = PRM.outer_dims(p)
    h = top_z(p)
    x0 = -(p.CUTOUT_W / 2 + p.W_TOP_FRONT)
    y0 = -(p.CUTOUT_W / 2 + p.W_TOP_LEFT)

    outer = F.rounded_box(L, W, h, p.R_OUT, Vector(x0, y0, 0))
    inner = F.rounded_box(p.CUTOUT_W, p.CUTOUT_W, h + 2, p.CUTOUT_R,
                          Vector(-p.CUTOUT_W / 2, -p.CUTOUT_W / 2, -1))
    body = outer.cut(inner)

    # Freistellung für die Gussets der Karosseriebefestigungsplatte (oben, innen)
    rec = F.ring(p.CUTOUT_W + 2 * p.REC_GUSSET_W, p.CUTOUT_W + 2 * p.REC_GUSSET_W,
                 p.CUTOUT_R + p.REC_GUSSET_W,
                 p.CUTOUT_W, p.CUTOUT_W, p.CUTOUT_R,
                 p.REC_GUSSET_D + 1)
    rec.translate(Vector(0, 0, h - p.REC_GUSSET_D))
    body = body.cut(rec)

    # Kleberille unten
    g_in = p.CUTOUT_W + 2 * p.GROOVE_OFF
    groove = F.ring(g_in + 2 * p.GROOVE_W, g_in + 2 * p.GROOVE_W,
                    p.CUTOUT_R + p.GROOVE_OFF + p.GROOVE_W,
                    g_in, g_in, p.CUTOUT_R + p.GROOVE_OFF,
                    p.GROOVE_D + 1)
    groove.translate(Vector(0, 0, -1))
    body = body.cut(groove)

    # Außenfase unten (Sika-Kehlnaht): alle z=0-Kanten nahe der Außenkontur
    def _on_outer(e):
        c = e.CenterOfMass
        near_x = min(abs(c.x - x0), abs(c.x - (x0 + L))) < p.R_OUT + 1
        near_y = min(abs(c.y - y0), abs(c.y - (y0 + W))) < p.R_OUT + 1
        return abs(c.z) < 1e-6 and (near_x or near_y)
    fase_edges = [e for e in body.Edges if _on_outer(e)]
    if fase_edges:
        body = body.makeChamfer(p.CHAMFER_OUT, fase_edges)

    # Klebespalt-Noppen (definierte Elastikfugen-Dicke)
    nops = [Part.makeCylinder(p.NOPPLE_R, p.GLUE_GAP, Vector(x, y, -p.GLUE_GAP))
            for x, y in _nopple_positions(p)]
    body = body.fuse(nops)
    body = body.removeSplitter()
    if not body.isValid():
        raise RuntimeError("frame: Boolesche Operationen ergaben ungültigen Körper")
    return body
```

- [ ] **Step 4: Run — Expected PASS**: `TEST_FILTER=frame bin/fc tests/run_tests.py`
→ `5 bestanden, 0 fehlgeschlagen` (Laufzeit < 60 s)

- [ ] **Step 5: Sichtprüfung erzeugen** (kein Test, einmalige Kontrolle):

`bin/fc` mit Inline-Skript ist unzuverlässig — Mini-Skript `out/` nutzen:
```python
# scratch: preview.py (nicht committen, nach Nutzung löschen)
import Part
from model.frame import build_frame
import pathlib
pathlib.Path("out").mkdir(exist_ok=True)
build_frame().exportStep("out/frame_preview.step")
print("out/frame_preview.step geschrieben")
```
Run: `bin/fc preview.py` — dann STEP in FreeCAD-GUI öffnen und Deckfläche,
Rille, Noppen, Fase visuell prüfen. `preview.py` danach löschen.

- [ ] **Step 6: Checkpoint** — Screenshot/Befund melden, Commit-Freigabe erfragen.
Vorschlag: `feat: Monolith-Adapterrahmen (build_frame)`

---

### Task 5: Analytik `fem/analytic.py` (Haubenfreigang, Thermik, Stoß, Welle)

**Files:**
- Create: `fem/__init__.py` (leer), `fem/analytic.py`, `tests/test_analytic.py`

**Interfaces:**
- Consumes: `params`
- Produces: `hood_clearance(p) -> float` (mm Freigang; `float('inf')` wenn kein
  horizontaler Überlapp), `glue_shear_utilization(p) -> float` (0..1, Auslastung der
  Elastikfuge durch Thermik), `glue_load_shear(p, f_inplane) -> dict` (lastinduzierter
  Klebfugen-Schub, Spec-Kriterium 3), `side_screw_pullout(p) -> dict` (Auszug der
  Seitenschrauben aus der Adapter-Innenwand, Spec-Kriterium 4),
  `joint_checks(p, f_inplane) -> dict` (Schub/Lochleibung am Stoß),
  alle konsumiert von `fem/report.py`.

- [ ] **Step 1: Failing Test schreiben**

`tests/test_analytic.py`:
```python
import params as PRM
from fem import analytic as A


def test_haubenfreigang_default_kein_ueberlapp():
    # Default: Haube ragt 130 mm über den Ausschnitt, Kante erst bei 250 mm
    assert A.hood_clearance() == float("inf")

def test_haubenfreigang_mit_ueberlapp():
    p = PRM.Params(HOOD_TIP_REACH=300.0)        # ragt über die Kante
    c = A.hood_clearance(p)
    # 28 + 30 - 55 = 3 mm Freigang
    assert abs(c - 3.0) < 1e-9

def test_fugenauslastung():
    u = A.glue_shear_utilization()
    # Segmentlänge ~275 mm, dT = 85-20 = 65 K, dAlpha 65e-6:
    # delta = 65e-6*275*65 = 1.162 mm; je Ende 0.581; gamma = 0.194; /0.5 = 0.39
    assert 0.30 < u < 0.50

def test_stossnachweis_traegt_windlast():
    r = A.joint_checks(PRM.P, PRM.wind_force())
    assert r["tau_MPa"] < r["tau_zul_MPa"]
    assert r["lochleibung_MPa"] < r["lochleibung_zul_MPa"]
    assert r["PASS"]

def test_klebfugen_schub_aus_last():
    r = A.glue_load_shear(PRM.P, PRM.wind_force())
    # Rillenfläche ~14e3 mm² -> 444 N ergeben ~0.03 MPa, weit unter 0.1
    assert r["tau_MPa"] < 0.05
    assert r["PASS"]

def test_seitenschrauben_auszug():
    r = A.side_screw_pullout(PRM.P)
    assert r["F_zul_N"] > 150.0            # je Schraube, dauerfest
    assert r["PASS"]
```

- [ ] **Step 2: Run — Expected FAIL**: `TEST_FILTER=analytic bin/fc tests/run_tests.py`

- [ ] **Step 3: Implementieren**

`fem/analytic.py`:
```python
"""Analytische Nachweise, die keine FEM brauchen (Spec §6 LF5, Stoß, Freigang)."""
import params as PRM


def hood_clearance(p: PRM.Params = PRM.P) -> float:
    """Vertikaler Freigang Haubenunterkante über der Dachkante (mm).
    inf, wenn die Haube die Kante horizontal gar nicht erreicht."""
    if p.HOOD_TIP_REACH < p.EDGE_DIST:
        return float("inf")
    return p.H_RAISE + p.HOOD_UNDERSIDE_H - p.EDGE_H


def _segment_length(p: PRM.Params) -> float:
    L, W = PRM.outer_dims(p)
    return max(L, W) / 2 + p.LAP_L        # längster Schenkel eines L-Segments


def glue_shear_utilization(p: PRM.Params = PRM.P) -> float:
    """Auslastung der unteren Elastikfuge durch CTE-Differenz ASA<->GFK.
    Bezugslänge ist das SEGMENT (Segmentierung entkoppelt die Gesamtlänge!)."""
    dT = max(p.T_MAX - p.T_CURE, p.T_CURE - p.T_MIN)
    delta = (p.CTE_ASA - p.CTE_ROOF) * _segment_length(p) * dT   # mm gesamt
    gamma = (delta / 2) / p.GLUE_GAP                             # Schubverzerrung je Ende
    return gamma / p.GLUE_SHEAR_CAP


def glue_load_shear(p: PRM.Params, f_inplane: float) -> dict:
    """Spec-Kriterium 3: lastinduzierter Schub in der unteren Klebfuge
    <= 0.1 N/mm² dauerhaft. Tragend nur die Rillenraupe (konservativ)."""
    groove_len = 4 * (p.CUTOUT_W + 2 * p.GROOVE_OFF + p.GROOVE_W)
    a_bond = groove_len * p.GROOVE_W
    tau = f_inplane / a_bond
    return {"tau_MPa": tau, "tau_zul_MPa": 0.1, "PASS": tau <= 0.1}


def side_screw_pullout(p: PRM.Params) -> dict:
    """Spec-Kriterium 4: Auszugstragfähigkeit einer Seitenschraube (ST4.2)
    in der Adapter-Innenwand. Gewindeeingriff = Bandbreite, konservativ nur
    12 mm angesetzt; Scherfestigkeit = 0.5 * Dauerzulässigkeit."""
    d, l_e = 4.2, 12.0
    import math
    sig_lang, _ = PRM.allowables(p)
    f_zul = math.pi * d * l_e * 0.5 * sig_lang
    f_erf = 100.0        # Anpresssicherung der Platte, real winzig
    return {"F_zul_N": f_zul, "F_erf_N": f_erf, "PASS": f_zul >= f_erf}


def joint_checks(p: PRM.Params, f_inplane: float) -> dict:
    """Konservativer Stoßnachweis: die volle horizontale Last geht durch
    EINEN Stoß (real verteilt sie sich auf vier)."""
    lap_h = (p.H_RAISE - p.GLUE_GAP) / 2
    band = min(p.W_TOP_FRONT, p.W_TOP_REAR, p.W_TOP_LEFT, p.W_TOP_RIGHT)
    a_lap = p.LAP_L * band                       # Scherfläche der Überlappung
    tau = f_inplane / a_lap
    sig_lang, sig_kurz = PRM.allowables(p)
    tau_zul = 0.5 * sig_kurz                     # Schub ~ 0.5 * sigma (v. Mises)
    # Lochleibung der M4-Schraube im ASA (Kurzzeitfall):
    lochleibung = f_inplane / (p.JOINT_BOLT_D * lap_h)
    lochleibung_zul = sig_kurz
    return {
        "tau_MPa": tau, "tau_zul_MPa": tau_zul,
        "lochleibung_MPa": lochleibung, "lochleibung_zul_MPa": lochleibung_zul,
        "PASS": tau < tau_zul and lochleibung < lochleibung_zul,
    }
```

`fem/__init__.py`: leere Datei.

- [ ] **Step 4: Run — Expected PASS**: `TEST_FILTER=analytic bin/fc tests/run_tests.py`
→ `4 bestanden, 0 fehlgeschlagen`

- [ ] **Step 5: Checkpoint** — Commit-Freigabe erfragen.
Vorschlag: `feat: analytische Nachweise (Freigang, Thermikfuge, Stoß)`

---

### Task 6: Segmentierung `model/segments.py`

**Files:**
- Create: `model/segments.py`, `tests/test_segments.py`

**Interfaces:**
- Consumes: `build_frame`, `params`, `features.hex_prism`
- Produces: `build_segments(p=PRM.P) -> list[Part.Shape]` — 4 L-Segmente **in
  Einbaulage** (für Union-Test und Export; identisch bei symmetrischen Breiten).
  Halbüberlappungsstoß in den Seitenmitten, 1 M4-Bolzen je Stoß (Senkung oben,
  Muttertasche unten), Passungsluft `TOL_JOINT` je Fügefläche.

- [ ] **Step 1: Failing Test schreiben**

`tests/test_segments.py`:
```python
import params as PRM
from model.frame import build_frame
from model.segments import build_segments


def _segs():
    global _CACHED
    try:
        return _CACHED
    except NameError:
        _CACHED = build_segments()
        return _CACHED

def test_vier_valide_segmente():
    segs = _segs()
    assert len(segs) == 4
    for s in segs:
        assert s.isValid() and s.Volume > 1e5

def test_bbox_druckservice():
    for s in _segs():
        bb = s.BoundBox
        assert max(bb.XLength, bb.YLength) <= PRM.P.SEG_MAX_BBOX, \
            f"Segment {bb.XLength:.0f}x{bb.YLength:.0f} zu groß"

def test_identische_segmente_bei_symmetrie():
    vols = sorted(s.Volume for s in _segs())
    assert (vols[-1] - vols[0]) / vols[-1] < 0.002   # W_TOP alle gleich -> identisch

def test_union_ergibt_rahmen_minus_fugenluft():
    segs = _segs()
    u = segs[0]
    for s in segs[1:]:
        u = u.fuse(s)
    u = u.removeSplitter()
    frame_v = build_frame().Volume
    # Bolzenbohrungen+Senkungen+Taschen und Toleranzspalte fehlen in der Union:
    diff = frame_v - u.Volume
    assert 0 < diff < 25000, f"Differenz {diff:.0f} mm³ unplausibel"

def test_keine_ueberschneidung_der_segmente():
    segs = _segs()
    for i in range(4):
        for j in range(i + 1, 4):
            ov = segs[i].common(segs[j]).Volume
            assert ov < 1.0, f"Segmente {i}/{j} überschneiden sich: {ov:.1f} mm³"
```

- [ ] **Step 2: Run — Expected FAIL**: `TEST_FILTER=segments bin/fc tests/run_tests.py`

- [ ] **Step 3: Implementieren**

`model/segments.py`:
```python
"""Zerlegung des Monolithen in 4 L-Ecksegmente mit Halbüberlappungsstoß.

Kanonik (vor Rotation, für Quadrant x>=0, y>=0):
- Stoß A liegt auf y=0 im +x-Band (Segment ERHÄLT dort die untere Lappe,
  die um LAP_L in den Nachbarquadranten y<0 ragt).
- Stoß B liegt auf x=0 im +y-Band (Segment GIBT dort die untere Hälfte
  bis LAP_L an den Nachbarn ab, behält die obere).
Alle Werkzeuge werden je Segment um k*90° rotiert; Booleans laufen gegen den
unrotierten Rahmen, daher funktionieren auch asymmetrische W_TOP-Breiten."""
import Part
from FreeCAD import Vector

import params as PRM
from model import features as F
from model.frame import build_frame, top_z

BIG = 2000.0


def _rot(shape, k):
    s = shape.copy()
    s.rotate(Vector(0, 0, 0), Vector(0, 0, 1), 90 * k)
    return s


def _bolt_cuts(p):
    """Bohrung + Kopfsenkung (oben) + Muttertasche (unten) für alle 4 Stöße.
    Wird VOR der Zerlegung vom Rahmen abgezogen -> beide Stoßpartner erhalten
    automatisch deckungsgleiche Halbfeatures."""
    h = top_z(p)
    cuts = []
    for k in range(4):
        x = p.CUTOUT_W / 2 + p.JOINT_BOLT_OFF     # im Band, frei von Rille/Freistellung
        y = -p.LAP_L / 2                           # mitten in der Überlappung
        bolt = Part.makeCylinder(p.JOINT_BOLT_D / 2, h + 2, Vector(x, y, -1))
        cb = Part.makeCylinder(p.JOINT_CB_D / 2, p.JOINT_CB_T + 1,
                               Vector(x, y, h - p.JOINT_CB_T))
        nut = F.hex_prism(p.JOINT_NUT_AF, p.JOINT_NUT_T + 1, (x, y), -1)
        for c in (bolt, cb, nut):
            cuts.append(_rot(c, k))
    return cuts


def _one_segment(frame, p, k):
    """Segment für Quadrant k (0: +x/+y, dann gegen den Uhrzeigersinn)."""
    h = top_z(p)
    lap_h = h / 2
    t = p.TOL_JOINT
    # Kernquadrant x>=0, y>=0:
    core = Part.makeBox(BIG, BIG, BIG, Vector(0, 0, -BIG / 2))
    # Lappe (untere Hälfte), ragt am Stoß A um LAP_L-t nach y<0, im +x-Band:
    lap_add = Part.makeBox(BIG, p.LAP_L - t, lap_h - t,
                           Vector(p.CUTOUT_W / 2 - 5, -(p.LAP_L - t), 0))
    # Abgabe am Stoß B: untere Hälfte bis LAP_L im +y-Band entfernen:
    lap_cut = Part.makeBox(p.LAP_L, BIG, lap_h,
                           Vector(0, p.CUTOUT_W / 2 - 5, -0.5))
    seg = frame.common(_rot(core, k))
    seg = seg.fuse(frame.common(_rot(lap_add, k)))
    seg = seg.cut(_rot(lap_cut, k))
    seg = seg.removeSplitter()
    if not seg.isValid():
        raise RuntimeError(f"Segment {k}: ungültiger Körper")
    return seg


def build_segments(p: PRM.Params = PRM.P):
    if p.N_SEGMENTS != 4:
        raise ValueError("nur N_SEGMENTS=4 (Quadranten) unterstützt")
    frame = build_frame(p)
    for c in _bolt_cuts(p):
        frame = frame.cut(c)
    frame = frame.removeSplitter()
    return [_one_segment(frame, p, k) for k in range(4)]
```

- [ ] **Step 4: Run — Expected PASS**: `TEST_FILTER=segments bin/fc tests/run_tests.py`
→ `5 bestanden, 0 fehlgeschlagen` (Laufzeit einige Minuten — Booleans sind teuer).
Hinweis: Schlägt `test_union_ergibt_rahmen_minus_fugenluft` mit zu GROSSER Differenz
fehl, zuerst `lap_cut`-z-Start (−0.5, schneidet auch Noppenansatz im Band? Noppen
liegen nicht im Stoßband — prüfen) und die Fase kontrollieren, bevor Toleranzen
verändert werden.

- [ ] **Step 5: Checkpoint** — Commit-Freigabe erfragen.
Vorschlag: `feat: Segmentierung in 4 L-Segmente mit Halbüberlappungsstoß`

---

### Task 7: DFM-Prüfung `model/dfm.py`

**Files:**
- Create: `model/dfm.py`, `tests/test_dfm.py`

**Interfaces:**
- Consumes: Segmente aus `build_segments`
- Produces: `overhang_area(shape, p) -> (offending_mm2, allowed_mm2)` — Überhangfläche
  in Druckorientierung (Deckfläche nach unten, Teil um x um 180° gedreht),
  abzüglich bekannter, bewusst zugelassener Brückenzonen (Gusset-Freistellung,
  Muttertaschen, Senkungen). Konsumiert von `tests` und `export` (Montagenotiz).

- [ ] **Step 1: Failing Test schreiben**

`tests/test_dfm.py`:
```python
import params as PRM
from model.segments import build_segments
from model import dfm


def test_stuetzenfrei_in_druckorientierung():
    for i, s in enumerate(build_segments()):
        bad, allowed = dfm.overhang_area(s, PRM.P)
        assert bad <= allowed * 1.2 + 200, \
            f"Segment {i}: {bad:.0f} mm² Überhang (erlaubt ~{allowed:.0f})"
```

- [ ] **Step 2: Run — Expected FAIL**: `TEST_FILTER=dfm bin/fc tests/run_tests.py`

- [ ] **Step 3: Implementieren**

`model/dfm.py`:
```python
"""Design-for-Manufacturing-Prüfung: Überhänge in Druckorientierung.
Druckorientierung FDM: Deckfläche auf dem Bett (Teil kopfüber). Facetten,
deren Normale steiler als 45° nach unten zeigt und die nicht auf dem Bett
liegen, brauchen Stützen — außer in bewusst zugelassenen Brückenzonen."""
import math

import MeshPart
from FreeCAD import Matrix

import params as PRM
from model.frame import top_z

COS45 = math.cos(math.radians(45))


def _allowed_bridge_area(p):
    """Bewusst zugelassene Brücken (in Druckorientierung nach unten offen):
    Gusset-Freistellungsring + 4 Kopfsenkungen ringförmig + 4 Muttertaschen-Decken."""
    rec_ring = ((p.CUTOUT_W + 2 * p.REC_GUSSET_W) ** 2 - p.CUTOUT_W ** 2)
    cb = 4 * math.pi * (p.JOINT_CB_D / 2) ** 2
    nut = 4 * 2 * math.sqrt(3) * (p.JOINT_NUT_AF / 2) ** 2
    return rec_ring + cb + nut


def overhang_area(shape, p: PRM.Params = PRM.P):
    flipped = shape.copy()
    flipped = flipped.transformGeometry(Matrix(1, 0, 0, 0,
                                               0, -1, 0, 0,
                                               0, 0, -1, 0))  # 180° um x
    zmin = flipped.BoundBox.ZMin
    mesh = MeshPart.meshFromShape(flipped, LinearDeflection=0.3,
                                  AngularDeflection=0.5, Relative=False)
    bad = 0.0
    for facet in mesh.Facets:
        n = facet.Normal
        z = min(pt.z for pt in facet.Points) if hasattr(facet.Points[0], "z") \
            else min(pt[2] for pt in facet.Points)
        on_bed = z < zmin + 0.3
        if n.z < -COS45 and not on_bed:
            bad += facet.Area
    return bad, _allowed_bridge_area(p)
```

- [ ] **Step 4: Run — Expected PASS**: `TEST_FILTER=dfm bin/fc tests/run_tests.py`
Hinweis bei FAIL: `facet.Points`-Zugriff je nach FC-Version Tupel — der Code
behandelt beide Varianten; bei anderem Attributnamen `dir(facet)` ausgeben.

- [ ] **Step 5: Checkpoint** — Commit-Freigabe erfragen.
Vorschlag: `feat: DFM-Überhangprüfung in Druckorientierung`

---

### Task 8: FEM-Material und Lastfälle `fem/material.py`, `fem/loadcases.py`

**Files:**
- Create: `fem/material.py`, `fem/loadcases.py`, `tests/test_loadcases.py`

**Interfaces:**
- Consumes: `params`, Rahmen-Shape
- Produces:
  - `material.fem_material_dict(p) -> dict` (FreeCAD-Materialkarte, homogenisiert)
  - `loadcases.CASES: dict[str, Case]` mit `Case(name, kind)`;
    `Case.fixed_faces(shape, p) -> tuple[str,...]`,
    `Case.loads(shape, p) -> list[(face_names, direction_vector, magnitude_N)]`,
    `Case.allowable(p) -> float` (MPa, je nach kind lang/kurz)
  - Face-Selektoren: `top_faces`, `nopple_faces`, `top_half_faces(sign)`
  Konsumiert von `fem/run_fem.py`.

- [ ] **Step 1: Failing Test schreiben**

`tests/test_loadcases.py`:
```python
import params as PRM
from model.frame import build_frame
from fem import loadcases as LC
from fem.material import fem_material_dict


def test_materialkarte():
    m = fem_material_dict(PRM.P)
    assert m["YoungsModulus"] == "1000.0 MPa"       # 2000 * INFILL 0.5
    assert m["PoissonRatio"] == "0.35"

def test_face_selektoren():
    s = build_frame()
    top = LC.top_faces(s, PRM.P)
    nop = LC.nopple_faces(s, PRM.P)
    assert len(top) >= 1 and len(nop) >= 20
    front = LC.top_half_faces(s, PRM.P, -1)
    rear = LC.top_half_faces(s, PRM.P, +1)
    assert front and rear and not set(front) & set(rear)

def test_lastfaelle_vollstaendig_und_bezahlt():
    s = build_frame()
    assert set(LC.CASES) == {"LF1_wind", "LF2_schlechtweg", "LF3_klemmung", "LF4_schnee"}
    for c in LC.CASES.values():
        assert c.fixed_faces(s, PRM.P)
        loads = c.loads(s, PRM.P)
        assert loads and all(m > 0 for _, _, m in loads)
        assert c.allowable(PRM.P) > 0

def test_lf1_zahlen():
    s = build_frame()
    loads = LC.CASES["LF1_wind"].loads(s, PRM.P)
    mags = sorted(m for _, _, m in loads)
    assert abs(sum(mags) - (444.4 + 2 * LC.couple_force(s, PRM.P))) < 2.0

def test_lf2_zahlen():
    f_vert = PRM.P.FAN_MASS * 9.81 * PRM.P.G_VERT
    assert abs(f_vert - 255.1) < 0.5
```

- [ ] **Step 2: Run — Expected FAIL**: `TEST_FILTER=loadcases bin/fc tests/run_tests.py`

- [ ] **Step 3: Implementieren**

`fem/material.py`:
```python
"""Homogenisierte ASA-Materialkarte für CalculiX (Spec §6).
Steifigkeit mit INFILL_FACTOR abgemindert (Perimeter + 40 % Gyroid);
Festigkeitsbewertung erfolgt NICHT hier, sondern gegen params.allowables()."""
import params as PRM


def fem_material_dict(p: PRM.Params = PRM.P) -> dict:
    return {
        "Name": "ASA-homogenisiert",
        "YoungsModulus": f"{p.E_BASE * p.INFILL_FACTOR} MPa",
        "PoissonRatio": str(p.NU),
        "Density": f"{p.RHO} kg/m^3",
    }
```

`fem/loadcases.py`:
```python
"""Lastfälle LF1-LF4 als Code (Spec §6). LF5 (Thermik) ist analytisch in
fem/analytic.py. Kräfte werden als (face_names, richtung, betrag_N) geliefert;
ConstraintForce verteilt den Betrag über die referenzierten Flächen."""
from dataclasses import dataclass
from typing import Callable

from FreeCAD import Vector

import params as PRM
from model.frame import top_z


def _planar_faces(shape, z_target, tol=1e-4):
    out = []
    for i, f in enumerate(shape.Faces):
        if abs(f.CenterOfMass.z - z_target) < tol:
            out.append((i, f))
    return out


def top_faces(shape, p):
    return tuple(f"Face{i+1}" for i, _ in _planar_faces(shape, top_z(p)))


def nopple_faces(shape, p):
    return tuple(f"Face{i+1}" for i, _ in _planar_faces(shape, -p.GLUE_GAP))


def top_half_faces(shape, p, sign):
    """Deckflächen-Anteile mit CenterOfMass.x in Richtung sign (+1 = heck)."""
    return tuple(f"Face{i+1}" for i, f in _planar_faces(shape, top_z(p))
                 if sign * f.CenterOfMass.x > 1.0)


def couple_force(shape, p) -> float:
    """Kräftepaar-Betrag, das das Wind-Kippmoment über die Deckflächen-Hälften
    abbildet. Hebelarm aus den realen Flächenschwerpunkten."""
    faces = _planar_faces(shape, top_z(p))
    front = [(f.Area, f.CenterOfMass.x) for _, f in faces if f.CenterOfMass.x < -1]
    rear = [(f.Area, f.CenterOfMass.x) for _, f in faces if f.CenterOfMass.x > 1]
    def _centroid(items):
        a = sum(a for a, _ in items)
        return sum(a_i * x for a_i, x in items) / a
    lever_mm = _centroid(rear) - _centroid(front)
    m_nmm = PRM.wind_force(p) * (p.H_CG + top_z(p))
    return m_nmm / lever_mm


@dataclass(frozen=True)
class Case:
    name: str
    kind: str                      # "kurz" oder "lang"
    fixed: Callable
    load_fn: Callable

    def fixed_faces(self, shape, p):
        return self.fixed(shape, p)

    def loads(self, shape, p):
        return self.load_fn(shape, p)

    def allowable(self, p) -> float:
        lang, kurz = PRM.allowables(p)
        return lang if self.kind == "lang" else kurz


def _lf1(shape, p):
    fc = couple_force(shape, p)
    return [
        (top_faces(shape, p), Vector(1, 0, 0), PRM.wind_force(p)),
        (top_half_faces(shape, p, +1), Vector(0, 0, 1), fc),
        (top_half_faces(shape, p, -1), Vector(0, 0, -1), fc),
    ]

def _lf2(shape, p):
    return [
        (top_faces(shape, p), Vector(0, 0, -1), p.FAN_MASS * 9.81 * p.G_VERT),
        (top_faces(shape, p), Vector(0, 1, 0), p.FAN_MASS * 9.81 * p.G_LAT),
    ]

def _lf3(shape, p):
    return [(top_faces(shape, p), Vector(0, 0, -1), p.CLAMP_FORCE)]

def _lf4(shape, p):
    return [(top_faces(shape, p), Vector(0, 0, -1), p.SNOW_LOAD)]


CASES = {
    "LF1_wind": Case("LF1_wind", "kurz", nopple_faces, _lf1),
    "LF2_schlechtweg": Case("LF2_schlechtweg", "kurz", nopple_faces, _lf2),
    "LF3_klemmung": Case("LF3_klemmung", "lang", nopple_faces, _lf3),
    "LF4_schnee": Case("LF4_schnee", "kurz", nopple_faces, _lf4),
}
```
Hinweis: `Case.fixed` bekommt die Funktion `nopple_faces` direkt — Fixierung an den
Noppenspitzen ist konservativ (Punktlager statt elastischer Klebefuge).

- [ ] **Step 4: Run — Expected PASS**: `TEST_FILTER=loadcases bin/fc tests/run_tests.py`
→ `5 bestanden, 0 fehlgeschlagen`

- [ ] **Step 5: Checkpoint** — Commit-Freigabe erfragen.
Vorschlag: `feat: FEM-Materialkarte und Lastfälle LF1-LF4`

---

### Task 9: FEM-Läufe `fem/run_fem.py`

**Files:**
- Create: `fem/run_fem.py`, `tests/test_run_fem.py`

**Interfaces:**
- Consumes: `build_frame`, `fem.material`, `fem.loadcases`, Muster aus Task 2
- Produces: `run_case(shape, case, p, mesh_mm) -> dict` mit Schlüsseln
  `vm_max_MPa`, `defl_max_mm`, `defl_top_mm`, `allowable_MPa`, `PASS`;
  `run_all_cases(shape, p, mesh_mm) -> dict[str, dict]`. Konsumiert von `report.py`
  und `run_all.py`.

- [ ] **Step 1: Failing Test schreiben**

`tests/test_run_fem.py`:
```python
import params as PRM
from model.frame import build_frame
from fem import loadcases as LC
from fem.run_fem import run_case


def test_lf4_schnee_grobnetz():
    """Schnellster Lastfall als Integrationstest (Grobnetz)."""
    s = build_frame()
    r = run_case(s, LC.CASES["LF4_schnee"], PRM.P, PRM.P.MESH_MM_TEST)
    assert r["vm_max_MPa"] > 0.001
    assert r["vm_max_MPa"] < 5.0, f"200 N Schnee erzeugen {r['vm_max_MPa']} MPa?!"
    assert r["defl_max_mm"] < 0.2
    assert r["PASS"] is True
```

- [ ] **Step 2: Run — Expected FAIL**: `TEST_FILTER=run_fem bin/fc tests/run_tests.py`

- [ ] **Step 3: Implementieren**

`fem/run_fem.py`:
```python
"""Skriptierter CalculiX-Lauf für einen Lastfall (Muster aus Task-2-Smoke)."""
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

BUNDLE_BIN = "/Applications/FreeCAD.app/Contents/Resources/bin"


def _ensure_binary_paths():
    g = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/Gmsh")
    if not g.GetString("gmshBinaryPath"):
        g.SetString("gmshBinaryPath", BUNDLE_BIN + "/gmsh")
    c = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/Ccx")
    if not c.GetString("ccxBinaryPath"):
        c.SetString("ccxBinaryPath", BUNDLE_BIN + "/ccx")


def _direction_ref(doc, vec, name):
    """ConstraintForce braucht eine Kantenreferenz als Richtung."""
    line = Part.makeLine(Vector(0, 0, 0), Vector(vec).multiply(10.0))
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = line
    return (obj, ("Edge1",))


def run_case(shape, case, p: PRM.Params = PRM.P, mesh_mm: float = None) -> dict:
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
        fea.run()
        fea.load_results()

        res = [o for o in doc.Objects if o.isDerivedFrom("Fem::FemResultObject")][0]
        vm_max = max(res.vonMises)
        defl = [v.Length for v in res.DisplacementVectors]
        defl_max = max(defl)
        # Verformung der Deckflächen-Knoten (Dichtheitskriterium):
        zt = top_z(p)
        top_defl = [v.Length for v, n in zip(res.DisplacementVectors,
                                             res.NodeNumbers)
                    if abs(res.Mesh.FemMesh.Nodes[n].z - zt) < 0.5]
        defl_top = max(top_defl) if top_defl else defl_max
        allow = case.allowable(p)
        return {
            "vm_max_MPa": vm_max,
            "defl_max_mm": defl_max,
            "defl_top_mm": defl_top,
            "allowable_MPa": allow,
            "PASS": vm_max <= allow and defl_top <= p.DEFL_TOP_MAX,
        }
    finally:
        FreeCAD.closeDocument(doc.Name)


def run_all_cases(shape, p: PRM.Params = PRM.P, mesh_mm: float = None) -> dict:
    from fem.loadcases import CASES
    return {name: run_case(shape, c, p, mesh_mm) for name, c in CASES.items()}
```

- [ ] **Step 4: Run — Expected PASS**: `TEST_FILTER=run_fem bin/fc tests/run_tests.py`
(Grobnetz, Laufzeit einstellig Minuten). Häufigste Fehlerquellen und Reihenfolge
der Diagnose: (1) `mesh.Shape/Part`-Property, (2) `ConstraintForce.Direction`-
Zuweisung (LinkSub-Format `(obj, ("Edge1",))`), (3) `res.Mesh.FemMesh.Nodes`-Zugriff
(alternativ über `doc.getObject("Mesh").FemMesh.Nodes`).

- [ ] **Step 5: Checkpoint** — Commit-Freigabe erfragen.
Vorschlag: `feat: skriptierter CalculiX-Lauf je Lastfall`

---

### Task 10: Stoß-Submodell `fem/joint_check.py`

**Files:**
- Create: `fem/joint_check.py`, `tests/test_joint.py`

**Interfaces:**
- Consumes: `run_case`-Muster (eigenständiges Mini-Modell), `params`, `analytic.joint_checks`
- Produces: `run_joint_submodel(p, f_inplane, mesh_mm=4.0) -> dict`
  (`vm_max_MPa`, `allowable_MPa`, `PASS`) — untere Lappe als Kragarm unter der
  konservativen Voll-Stoßlast. Konsumiert von `report.py`.

- [ ] **Step 1: Failing Test schreiben**

`tests/test_joint.py`:
```python
import params as PRM
from fem.joint_check import run_joint_submodel


def test_stoss_submodell():
    r = run_joint_submodel(PRM.P, PRM.wind_force())
    assert r["vm_max_MPa"] > 0.01
    assert r["PASS"], f"Stoß versagt: {r['vm_max_MPa']:.2f} > {r['allowable_MPa']:.2f} MPa"
```

- [ ] **Step 2: Run — Expected FAIL**: `TEST_FILTER=joint bin/fc tests/run_tests.py`

- [ ] **Step 3: Implementieren**

`fem/joint_check.py`:
```python
"""FEM-Submodell des Halbüberlappungsstoßes: die untere Lappe (LAP_L lang,
Bandbreite breit, halbe Körperhöhe dick) als Kragarm, eingespannt am Übergang
zum Segmentkern, belastet mit der vollen horizontalen Stoßlast (konservativ:
real teilen sich 4 Stöße + Verklebung die Last)."""
import Part
from FreeCAD import Vector

import params as PRM
from fem.loadcases import Case
from fem.run_fem import run_case
from model.frame import top_z


def _lap_shape(p):
    band = min(p.W_TOP_FRONT, p.W_TOP_REAR, p.W_TOP_LEFT, p.W_TOP_RIGHT)
    lap_h = top_z(p) / 2
    return Part.makeBox(p.LAP_L, band, lap_h)


def run_joint_submodel(p: PRM.Params = PRM.P, f_inplane: float = None,
                       mesh_mm: float = 4.0) -> dict:
    f = f_inplane if f_inplane is not None else PRM.wind_force(p)
    lap = _lap_shape(p)

    def _fixed(shape, _p):
        # Einspannfläche: x=0-Stirnseite (Übergang zum Segmentkern)
        return tuple(f"Face{i+1}" for i, fa in enumerate(shape.Faces)
                     if abs(fa.CenterOfMass.x) < 1e-6)

    def _loads(shape, _p):
        # Schub auf der Oberseite der Lappe (Kontaktfläche zum Partner)
        top = tuple(f"Face{i+1}" for i, fa in enumerate(shape.Faces)
                    if abs(fa.CenterOfMass.z - top_z(_p) / 2) < 1e-6)
        return [(top, Vector(1, 0, 0), f)]

    case = Case("Stoss", "kurz", _fixed, _loads)
    return run_case(lap, case, p, mesh_mm)
```

- [ ] **Step 4: Run — Expected PASS**: `TEST_FILTER=joint bin/fc tests/run_tests.py`

- [ ] **Step 5: Checkpoint** — Commit-Freigabe erfragen.
Vorschlag: `feat: FEM-Submodell des Segmentstoßes`

---

### Task 11: Report `fem/report.py`

**Files:**
- Create: `fem/report.py`, `tests/test_report.py`

**Interfaces:**
- Consumes: `params_hash`, `analytic`, Ergebnisse aus `run_all_cases` und
  `run_joint_submodel` (als dicts übergeben — Report rechnet selbst NICHT)
- Produces: `write_report(fem_results, joint_result, p, out_path) -> bool`
  (True = alle Kriterien PASS; schreibt Markdown). Konsumiert von `run_all.py`.

- [ ] **Step 1: Failing Test schreiben**

`tests/test_report.py`:
```python
from pathlib import Path

import params as PRM
from fem.report import write_report

FAKE_OK = {"vm_max_MPa": 1.0, "defl_max_mm": 0.1, "defl_top_mm": 0.05,
           "allowable_MPa": 8.4, "PASS": True}
FAKE_BAD = dict(FAKE_OK, vm_max_MPa=99.0, PASS=False)


def test_report_pass(tmp="out/test_report_ok.md"):
    ok = write_report({"LF1_wind": FAKE_OK}, FAKE_OK, PRM.P, tmp)
    assert ok is True
    text = Path(tmp).read_text()
    assert "PASS" in text and PRM.params_hash() in text
    assert "140" in text                      # Wellenwahl im Report

def test_report_fail(tmp="out/test_report_bad.md"):
    ok = write_report({"LF1_wind": FAKE_BAD}, FAKE_OK, PRM.P, tmp)
    assert ok is False
    assert "FAIL" in Path(tmp).read_text()
```

- [ ] **Step 2: Run — Expected FAIL**: `TEST_FILTER=report bin/fc tests/run_tests.py`

- [ ] **Step 3: Implementieren**

`fem/report.py`:
```python
"""Verifikationsreport (Markdown): FEM-Ergebnisse + analytische Nachweise +
Parameterstand. PASS/FAIL-Logik für das Pipeline-Gate (Spec §6/§7)."""
from pathlib import Path

import params as PRM
from fem import analytic as A


def write_report(fem_results: dict, joint_result: dict,
                 p: PRM.Params, out_path: str) -> bool:
    lines = ["# Verifikationsreport Belluna-Adapterrahmen", ""]
    lines.append(f"Parameterstand: `{PRM.params_hash(p)}` · "
                 f"H_RAISE {p.H_RAISE} mm · Wandstärke effektiv "
                 f"{PRM.effective_wall(p)} mm · **Vierkantwelle "
                 f"{PRM.select_shaft(p):.0f} mm**")
    lines.append("")
    ok = True

    lines.append("## FEM-Lastfälle")
    lines.append("| Lastfall | max vM [MPa] | zulässig | Deckfl.-Verf. [mm] | Status |")
    lines.append("|---|---|---|---|---|")
    for name, r in sorted(fem_results.items()):
        ok &= r["PASS"]
        lines.append(f"| {name} | {r['vm_max_MPa']:.2f} | {r['allowable_MPa']:.2f} "
                     f"| {r['defl_top_mm']:.3f} (≤ {p.DEFL_TOP_MAX}) "
                     f"| {'PASS' if r['PASS'] else 'FAIL'} |")

    lines.append("")
    lines.append("## Stoß-Submodell")
    ok &= joint_result["PASS"]
    lines.append(f"max vM {joint_result['vm_max_MPa']:.2f} MPa ≤ "
                 f"{joint_result['allowable_MPa']:.2f} MPa → "
                 f"{'PASS' if joint_result['PASS'] else 'FAIL'}")

    lines.append("")
    lines.append("## Analytische Nachweise")
    clr = A.hood_clearance(p)
    clr_ok = clr >= p.CLEAR_MIN
    ok &= clr_ok
    clr_txt = "kein horizontaler Überlapp" if clr == float("inf") else f"{clr:.1f} mm"
    lines.append(f"- Haubenfreigang über Dachkante: {clr_txt} "
                 f"(≥ {p.CLEAR_MIN} mm) → {'PASS' if clr_ok else 'FAIL'}")
    u = A.glue_shear_utilization(p)
    u_ok = u < 1.0
    ok &= u_ok
    lines.append(f"- Elastikfugen-Auslastung (Thermik, LF5): {u*100:.0f} % "
                 f"→ {'PASS' if u_ok else 'FAIL'}")
    j = A.joint_checks(p, PRM.wind_force(p))
    ok &= j["PASS"]
    lines.append(f"- Stoß analytisch: τ {j['tau_MPa']:.2f}/{j['tau_zul_MPa']:.2f} MPa, "
                 f"Lochleibung {j['lochleibung_MPa']:.2f}/{j['lochleibung_zul_MPa']:.2f} MPa "
                 f"→ {'PASS' if j['PASS'] else 'FAIL'}")
    g = A.glue_load_shear(p, PRM.wind_force(p))
    ok &= g["PASS"]
    lines.append(f"- Klebfugen-Schub aus Last: {g['tau_MPa']:.3f} ≤ "
                 f"{g['tau_zul_MPa']} N/mm² → {'PASS' if g['PASS'] else 'FAIL'}")
    sc = A.side_screw_pullout(p)
    ok &= sc["PASS"]
    lines.append(f"- Seitenschrauben-Auszug: {sc['F_zul_N']:.0f} N zulässig ≥ "
                 f"{sc['F_erf_N']:.0f} N erforderlich → {'PASS' if sc['PASS'] else 'FAIL'}")

    lines.append("")
    lines.append(f"# Gesamtergebnis: {'**PASS**' if ok else '**FAIL**'}")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))
    return bool(ok)
```

- [ ] **Step 4: Run — Expected PASS**: `TEST_FILTER=report bin/fc tests/run_tests.py`

- [ ] **Step 5: Checkpoint** — Commit-Freigabe erfragen.
Vorschlag: `feat: Verifikationsreport mit PASS/FAIL-Gate`

---

### Task 12: Export `export/export.py`

**Files:**
- Create: `export/__init__.py` (leer), `export/export.py`, `tests/test_export.py`

**Interfaces:**
- Consumes: `build_frame`, `build_segments`, `params_hash`, `select_shaft`
- Produces: `export_all(p, out_dir) -> list[Path]` — schreibt
  `frame_<hash>.step`, `seg<k>_<hash>.step/.stl/.3mf` (k=0..3) und
  `montagenotiz_<hash>.md`. Konsumiert von `run_all.py`.

- [ ] **Step 1: Failing Test schreiben**

`tests/test_export.py`:
```python
from pathlib import Path

import Part

import params as PRM
from export.export import export_all


def test_export_erzeugt_alle_dateien():
    files = export_all(PRM.P, "out/test_export")
    names = {f.name for f in files}
    h = PRM.params_hash()
    assert f"frame_{h}.step" in names
    for k in range(4):
        assert f"seg{k}_{h}.step" in names
        assert f"seg{k}_{h}.stl" in names
        assert f"seg{k}_{h}.3mf" in names
    assert f"montagenotiz_{h}.md" in names

def test_step_reimport_volumen():
    h = PRM.params_hash()
    s = Part.Shape()
    s.read(f"out/test_export/seg0_{h}.step")
    assert s.Volume > 1e5

def test_montagenotiz_inhalt():
    h = PRM.params_hash()
    text = Path(f"out/test_export/montagenotiz_{h}.md").read_text()
    for muss in ("140", "Carloflex", "Deckfläche nach unten", "Tempern",
                 "4 Perimeter", "100 % Infill", "Dichtheit", "2K-Epoxid"):
        assert muss in text, f"'{muss}' fehlt in Montagenotiz"
```

- [ ] **Step 2: Run — Expected FAIL**: `TEST_FILTER=export bin/fc tests/run_tests.py`

- [ ] **Step 3: Implementieren**

`export/export.py`:
```python
"""Export der Druck-/Archivdateien + auto-generierte Montagenotiz (Spec §7)."""
from pathlib import Path

import MeshPart

import params as PRM
from model.frame import build_frame
from model.segments import build_segments


def _write_mesh(shape, path: Path):
    mesh = MeshPart.meshFromShape(shape, LinearDeflection=0.05,
                                  AngularDeflection=0.35, Relative=False)
    mesh.write(str(path))


def _montagenotiz(p: PRM.Params, h: str) -> str:
    L, W = PRM.outer_dims(p)
    groove_len = 4 * (p.CUTOUT_W + 2 * p.GROOVE_OFF + p.GROOVE_W)
    bead_ml = groove_len * p.GROOVE_W * (p.GLUE_GAP + p.GROOVE_D) / 1000.0
    return f"""# Montagenotiz Adapterrahmen (Parameterstand {h})

## Druck (je 4x Segment, identisch)
- Material: ASA weiß; Orientierung: **Deckfläche nach unten** (Schichten parallel
  zum Dach; bei MJF/SLS beliebig). Brücken in Gusset-Freistellung/Muttertaschen sind
  beabsichtigt und unkritisch.
- Mindestens **4 Perimeter**, **100 % Infill** (die geschlossenen Rippenkammern
  übernehmen die Gewichtsreduktion; volle Dichte = definierte Festigkeit +
  Porenschluss), 0,4er Düse.
- Nach dem Druck **Tempern** (ASA: 80 °C, 4 h) für Maßstabilität bei Dachhitze.

## Fügen
- 4 Stöße: Halbüberlappung, je 1x M5x{int(p.H_RAISE - p.GLUE_GAP + p.JOINT_NUT_T + 2)}
  Zylinderkopf (DIN 912) + Mutter in der Tasche, Fügeflächen VOLLFLÄCHIG mit
  2K-Epoxid benetzen, verschrauben (0,8 Nm). Die Epoxid-Fügung ist Teil des
  Dichtheitskonzepts (Spec §4) — nicht weglassen.

## Dichtheit
- Beide Kleber-Ringe (untere Rille, Belluna-Ringklebenut) laufen GESCHLOSSEN über
  alle vier Stöße — nicht an Stößen absetzen.
- PFLICHT: Außenflächen mit 2K-PU oder Epoxid versiegeln (Porenschluss + UV).
- Lüfter-Verschraubung mit Feder-/Sicherungselementen montieren; nach der ersten
  Hitzeperiode nachziehen; Nähte jährlich sichtprüfen (Relaxation/Zyklik).
- Wassertest nach Einbau: erst drucklos fluten (Gießkanne, 10 min, Innenkontrolle),
  dann Hochdruck nur aus ISO-20653-9K-Abstand auf den Sockelbereich — nie direkt
  auf die Lüfterhaube (Belluna ist IPX4).

## Verkleben auf dem Dach
- Untergrund: Mini-Heki-Altbett vollständig entfernen, mit Isopropanol reinigen.
- Carloflex/Sika-252-Raupe in die untere Kleberille: ca. **{bead_ml:.0f} ml**
  (+ Kehlnaht außen). Noppen definieren {p.GLUE_GAP} mm Fugendicke — NICHT auspressen.
- Karosseriebefestigungsplatte mit Carloflex in der Ringklebenut auf die
  Deckfläche kleben; seitliche Schrauben aus dem Einbaukragen in die
  Adapter-Innenwand (Kernloch 3 mm vorbohren).

## Lüftereinbau
- Effektive Wandstärke: {PRM.effective_wall(p):.0f} mm →
  **Vierkantwelle {PRM.select_shaft(p):.0f} mm** einsetzen.
- Außenmaß Adapter: {L:.0f} x {W:.0f} mm, Höhe {p.H_RAISE:.0f} mm inkl. Fuge.
"""


def export_all(p: PRM.Params = PRM.P, out_dir: str = "out") -> list:
    h = PRM.params_hash(p)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = []

    frame = build_frame(p)
    fp = out / f"frame_{h}.step"
    frame.exportStep(str(fp))
    files.append(fp)

    for k, seg in enumerate(build_segments(p)):
        sp = out / f"seg{k}_{h}.step"
        seg.exportStep(str(sp))
        files.append(sp)
        for ext in (".stl", ".3mf"):
            mp = out / f"seg{k}_{h}{ext}"
            _write_mesh(seg, mp)
            files.append(mp)

    note = out / f"montagenotiz_{h}.md"
    note.write_text(_montagenotiz(p, h))
    files.append(note)
    return files
```

`export/__init__.py`: leere Datei.

- [ ] **Step 4: Run — Expected PASS**: `TEST_FILTER=export bin/fc tests/run_tests.py`
Hinweis: schlägt `.3mf` fehl, prüfen ob `Mesh.write` das Format kennt
(`import Mesh; print(Mesh.…)`) — Fallback: 3MF weglassen und nur STL+STEP liefern
(dann Test und Spec §7 anpassen, User informieren).

- [ ] **Step 5: Checkpoint** — Commit-Freigabe erfragen.
Vorschlag: `feat: Export von STEP/STL/3MF und Montagenotiz`

---

### Task 13: Pipeline `run_all.py` + FEM-Regression

**Files:**
- Create: `run_all.py`, `tests/test_regression.py`

**Interfaces:**
- Consumes: alles Vorherige
- Produces: `run_all.py` (Exit 0 nur bei Gesamt-PASS; schreibt `out/report_<hash>.md`
  und alle Exportdateien mit Produktionsnetz `MESH_MM`), Regressionstest mit
  Referenzwerten (beim ersten echten Lauf eingesetzt).

- [ ] **Step 1: run_all.py schreiben**

`run_all.py`:
```python
"""Gesamtpipeline: Modell -> FEM (Produktionsnetz) -> Analytik -> Export -> Report.
Aufruf: bin/fc run_all.py   — Exit-Code 0 nur bei Gesamt-PASS."""
import sys

import params as PRM
from export.export import export_all
from fem.joint_check import run_joint_submodel
from fem.report import write_report
from fem.run_fem import run_all_cases
from model.frame import build_frame

p = PRM.P
h = PRM.params_hash(p)
print(f"Parameterstand {h}: baue Rahmen …")
frame = build_frame(p)

print("FEM-Lastfälle (Produktionsnetz) …")
fem_results = run_all_cases(frame, p, p.MESH_MM)
for name, r in fem_results.items():
    print(f"  {name}: vM {r['vm_max_MPa']:.2f}/{r['allowable_MPa']:.2f} MPa "
          f"-> {'PASS' if r['PASS'] else 'FAIL'}")

print("Stoß-Submodell …")
joint = run_joint_submodel(p)

ok = write_report(fem_results, joint, p, f"out/report_{h}.md")
print(f"Report: out/report_{h}.md -> {'PASS' if ok else 'FAIL'}")

if not ok:
    print("ABBRUCH: Verifikation FAIL — kein Export.")
    sys.exit(1)

print("Export …")
for f in export_all(p, "out"):
    print(f"  {f}")
print("FERTIG: Druckdateien sind verifiziert freigegeben.")
sys.exit(0)
```

- [ ] **Step 2: Vollen Lauf ausführen**

Run: `bin/fc run_all.py`
Expected: alle Lastfälle PASS, Report + 14 Dateien in `out/`. Laufzeit 10–30 min
(Produktionsnetz). Die vM-Werte aus der Ausgabe notieren.

- [ ] **Step 3: Regressionstest mit den ECHTEN Werten aus Step 2 anlegen**

`tests/test_regression.py` (WERTE_HIER durch die notierten Zahlen ersetzen —
das ist beabsichtigt und kein Platzhalter-Verstoß: Referenzwerte existieren
erst nach dem ersten verifizierten Lauf):
```python
"""FEM-Regression: Referenz-Parameterstand -> erwartete Kennwerte ±15 %.
Fängt unbeabsichtigte Modell-/Vernetzungsänderungen. Grobnetz für Tempo."""
import params as PRM
from fem import loadcases as LC
from fem.run_fem import run_case
from model.frame import build_frame

REFERENZ = {
    # beim ersten run_all.py-Lauf gemessen (Grobnetz-Gegenprobe!):
    "LF1_wind": WERTE_HIER,        # z.B. 1.85
    "LF3_klemmung": WERTE_HIER,    # z.B. 0.92
}


def test_fem_regression_grobnetz():
    s = build_frame()
    for name, ref in REFERENZ.items():
        r = run_case(s, LC.CASES[name], PRM.P, PRM.P.MESH_MM_TEST)
        assert abs(r["vm_max_MPa"] - ref) / ref < 0.15, \
            f"{name}: {r['vm_max_MPa']:.2f} weicht > 15 % von Referenz {ref} ab"
```
Wichtig: Die Referenzwerte mit einem **Grobnetz-Lauf** bestimmen (gleiches Netz
wie der Test), nicht mit den Produktionsnetz-Werten aus Step 2.

- [ ] **Step 4: Gesamte Testsuite**

Run: `bin/fc tests/run_tests.py`
Expected: alle Tests PASS (Laufzeit ~10-20 min inkl. FEM-Grobnetzläufe).

- [ ] **Step 5: Abschluss-Checkpoint** — Gesamtergebnis melden (Report-Auszug,
Dateiliste), Commit-Freigabe erfragen.
Vorschlag: `feat: Gesamtpipeline run_all.py mit Verifikations-Gate und Regression`

---

### Task 14: Rippenkammern (Rework build_frame — User-Entscheidung 2026-07-12)

Ersetzt die Slicer-Infill-Struktur durch **geschlossene Rippenkammern**: Festigkeit wird
geometrie-definiert, FEM rechnet auf echter Geometrie mit vollem E-Modul, Montagenotiz
verlangt künftig 100 % Infill (Kammern übernehmen die Gewichtsreduktion).

**Files:**
- Modify: `params.py` (Kammer-Parameter + INFILL_FACTOR 0.5 → 1.0)
- Modify: `model/frame.py` (Kammer-Cuts + `chamber_cell_count(p)`)
- Modify: `model/dfm.py` (`_allowed_bridge_area`: Vent-Bohrungs-Zone ergänzen)
- Modify: `tests/test_frame.py` (Volumenband, neuer Kammertest)

**Interfaces:**
- `build_frame(p)` Signatur/Koordinaten UNVERÄNDERT (alle Konsumenten bleiben kompatibel)
- Neu: `chamber_cell_count(p) -> int` (für DFM-Vent-Allowance)

**Parameter (in params.py ergänzen, Kommentare sinngemäß):**
```python
    # --- Rippenkammern (geschlossene Zellen; User-Entscheidung 2026-07-12) ---
    CHAMBERS: bool = True
    DECK_T: float = 5.0        # Deckplatte: Gusset-Freistellung 3 + 2 Rest
    BOTTOM_T: float = 4.0      # Bodenplatte: enthält Kleberille (Tiefe 2)
    INNER_WALL: float = 8.0    # Schraubgrund seitliche Verschraubung
    CHAMBER_W: float = 15.0    # radiale Kammerbreite (2 konzentrische Ringe)
    CHAMBER_RIB: float = 4.0   # Steg zwischen den Kammerringen
    CELL_L: float = 45.0       # Zellenteilung entlang der Seite
    CELL_RIB: float = 3.0      # Quersteg zwischen Zellen
    SOLID_CORNER: float = 45.0 # massiv ab Eck-Außenkante
    SOLID_JOINT_HALF: float = 40.0  # massiv um Seitenmitte (deckt Lap + M5)
    CHEVRON_DEG: float = 47.0  # Kammerboden-Zelt; >45° mit Reserve (DFM-Kante)
    VENT_D: float = 4.0        # Druckausgleichsbohrung je Zelle (FDM; SLS verworfen)
    VENT_Z: float = 17.0       # Bohrungshöhe (weit weg von Schraubzone)
```

**Geometrie (install-Koordinaten, Deckfläche z=25):**
- Kammerring 1: r 208–223, Ring 2: r 227–242 (Innenwand 8, Steg 4, Außenwand 8).
- Kammerprofil (radialer Querschnitt): flache Decke z = 25−DECK_T = 20; senkrechte Wände;
  Boden als Zelt (∧, Apex mittig): an den Wänden z = BOTTOM_T, Apex z = BOTTOM_T +
  tan(CHEVRON_DEG)·CHAMBER_W/2 ≈ 12,0. In Druckorientierung (kopfüber) ist der Zeltboden
  die Kammer-„Decke" mit 47°-Flanken → stützenfrei, kein neuer DFM-Beitrag.
- Zellen je Seite zwischen den massiven Zonen (Ecken: SOLID_CORNER ab Außenkante;
  Stöße: ±SOLID_JOINT_HALF um die Seitenmitte), Raster CELL_L mit CELL_RIB.
- Vents (Druckausgleich der geschlossenen Zellen bei −20…+85 °C): je Zelle Ø VENT_D
  horizontal von der Innenfläche (r=200) bei z=VENT_Z in Ring 1,
  plus Durchgang Ring 1→Ring 2 durch den Steg. Dadurch sind ALLE Kammern belüftet →
  das Solid bleibt topologisch EINE geschlossene Shell (kein eingeschlossener Hohlraum) —
  der bestehende Test `len(Shells)==1 && isClosed` erzwingt damit korrekt verbundene Vents.
- Implementierung: Profil-Polygon in (r,z) → Part.Face → Extrusion entlang der Seite,
  pro Seite um k·90° rotiert; Cut-Reihenfolge in build_frame: Grundring → Freistellung →
  **Kammern** → Rille → Fase → Noppen; nach jeder Boolean-Gruppe removeSplitter + isValid-Guard.

**DFM:** `_allowed_bridge_area` um Vent-Zone erweitern:
`vent = chamber_cell_count(p) * 2 * (math.pi/2) * (p.VENT_D/2) * max(p.INNER_WALL, p.CHAMBER_RIB)`
(obere Halbzylinder der horizontalen Ø4-Kanäle; Ø4 ist brückenfrei druckbar).

**Tests (tests/test_frame.py):**
- `test_volumen_plausibel`: Band neu `1.55e6 < v < 1.95e6`
- Neu `test_kammern_wirken`:
```python
def test_kammern_wirken():
    import params as PRM
    from model.frame import build_frame
    v_solid = build_frame(PRM.Params(CHAMBERS=False)).Volume
    v_cham = build_frame().Volume
    assert 2.5e5 < (v_solid - v_cham) < 5.0e5, f"Kammervolumen {v_solid - v_cham:.0f}"
```
- Alle übrigen Tests (Öffnung R5.5-Probe, BBox, Deckfläche, 1 geschlossene Shell,
  Segmente, DFM) müssen UNVERÄNDERT grün bleiben. Volle Suite: 29 Tests.

**Steps:** RED (neue/angepasste frame-Tests) → Implementierung → GREEN →
volle Suite → Checkpoint (Commit nach Freigaberegel).

---

## Verifikation nach Planabschluss (Spec §7 Freigabe-Workflow)

0. VOR jeder ASA-Bestellung (DA-Review 2026-07-12): Messkampagne Punkte 4, 5 und 7
   (Gussets, Klips-Positionen, Kantenabstand/-höhe) eintragen → Pipeline-Rerun;
   danach EIN Segment als PLA-Billigdruck zur physischen Passform-/Freigangprobe.
   Solange EDGE_DIST/EDGE_H Schätzwerte sind, kennzeichnet der Report den
   Haubenfreigang als OFFEN (kein PASS-by-inf).
1. `bin/fc run_all.py` → Gesamt-PASS
2. `out/report_<hash>.md` dem User zeigen
3. `out/frame_<hash>.step` in der FreeCAD-GUI öffnen: Sichtkontrolle Deckfläche,
   Rille, Noppen, Stöße
4. Erst nach User-OK gelten die Druckdateien als freigegeben; Messkampagnen-Werte
   (Spec §8) ersetzen danach die Defaults → Pipeline-Rerun → neuer Hash → neue Freigabe.

## Abweichungen von der Spec (bei Übergabe dem User melden)

1. **Gmsh statt Netgen** — Netgen-Python fehlt im FreeCAD-1.1.1-Bundle (verifiziert).
2. **Massiver Körper + Slicer-Infill statt modellierter CAD-Rippen** — gleiche Funktion,
   deutlich robustere Booleans; FEM kompensiert mit `INFILL_FACTOR` 0,5.
3. **Halbüberlappungsstoß statt vertikaler Nut-Feder** — druckfreundlicher, selbstzentrierend,
   wasserführend günstiger; Segment-BBox dadurch ~275 mm → Kriterium 300 statt 250 mm.
4. **Zulässigkeiten exakt gerechnet: 3,36 / 8,4 MPa** statt der gerundeten ≈5/≈10 in Spec §6
   (Spec-Werte waren arithmetisch zu optimistisch; Plan ist konservativer).
5. **GLUE_GAP = 3,0 mm** (oberes Ende des Spec-Bereichs 2–3 mm) — aus der Thermik-Analytik.
6. **Stoßnachweis:** Mini-FEM-Submodell + Analytik statt Schnittkraft-Übertrag aus dem
   Globalmodell (CalculiX-Kontaktmodell wäre unverhältnismäßig).
