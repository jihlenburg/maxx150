"""Nicht freigabewirksamer FEM-Check der offenen CFD-Mittelnetzlast.

Das Skript läuft in FreeCAD, liest ausschließlich die bereits ausgewertete
CFD-Fallmatrix und lässt die bestehenden LF1--LF4 unverändert.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(line_buffering=True)

from FreeCAD import Vector  # noqa: E402

import params as PRM  # noqa: E402
from cfd.config import comparison_hash  # noqa: E402
from fem import analytic as A  # noqa: E402
from fem.loadcases import (  # noqa: E402
    Case,
    nopple_faces,
    outer_wall_faces,
    top_faces,
)
from fem.run_fem import run_case  # noqa: E402
from model.frame import build_frame  # noqa: E402
from project_paths import cfd_matrix_dir  # noqa: E402


def _axis(value: float, axis: tuple[float, float, float]) -> Vector:
    sign = 1.0 if value >= 0 else -1.0
    return Vector(*(sign * component for component in axis))


def _load_case(force: list[float], moment: list[float]) -> Case:
    def loads(shape, p):
        out = []
        axes = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
        deck = top_faces(shape, p)
        for value, axis in zip(force, axes):
            if abs(value) > 1e-6:
                out.append((deck, _axis(value, axis), abs(value)))

        # OpenFOAM liefert My um die Adapter-Oberseite. Dieses freie Moment
        # wird als vertikales Kräftepaar über Front-/Heck-Außenwand verteilt;
        # die am Deck eingeleitete CFD-Kraft erzeugt ihren Basishebel separat.
        my = moment[1]
        if abs(my) > 1e-6:
            couple = abs(my) * 1000.0 / PRM.outer_dims(p)[0]
            front_z = 1.0 if my >= 0 else -1.0
            out.extend((
                (outer_wall_faces(shape, p, -1), Vector(0, 0, front_z), couple),
                (outer_wall_faces(shape, p, +1), Vector(0, 0, -front_z), couple),
            ))
        return out

    return Case(
        "CFD_open_medium_x1p5",
        "kurz",
        nopple_faces,
        loads,
    )


def main() -> dict:
    matrix_dir = cfd_matrix_dir(comparison_hash())
    comparison_path = matrix_dir / "comparison.json"
    if not comparison_path.exists():
        raise RuntimeError(
            f"CFD-Vergleich fehlt: {comparison_path}; zuerst cfd.compare ausführen"
        )
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    transfer = comparison["structural_transfer_open_medium"]
    force = transfer["force_N"]
    moment = transfer["moment_Nm"]

    p = PRM.P
    print("CFD-FEM: baue Adapterrahmen …", flush=True)
    t0 = time.time()
    frame = build_frame(p)
    print(f"  Rahmen gebaut ({time.time() - t0:.1f} s)", flush=True)
    print("CFD-FEM: kombinierter offener Lastfall auf Produktionsnetz …", flush=True)
    t0 = time.time()
    fem = run_case(frame, _load_case(force, moment), p, p.MESH_MM)
    print(
        f"  vM {fem['vm_max_MPa']:.3f}/{fem['allowable_MPa']:.3f} MPa, "
        f"Deckverformung {fem['defl_top_mm']:.4f} mm "
        f"({time.time() - t0:.1f} s)",
        flush=True,
    )

    horizontal = math.hypot(force[0], force[1])
    uplift = max(force[2], 0.0)
    resultant = math.sqrt(sum(value * value for value in force))
    groove_area = PRM.groove_centerline_len(p) * p.GROOVE_W
    joints = A.joint_checks(p, horizontal)
    glue = A.glue_load_shear(p, horizontal)
    side_screw = A.side_screw_pullout(p)
    try:
        source_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        source_commit = "UNBEKANNT"

    output = {
        "schema": 1,
        "status": "PRELIMINARY_STRUCTURAL_CHECK",
        "structural_use": "INFORMATIONAL_NON_GATING",
        "comparison_hash": comparison["comparison_hash"],
        "source_commit": source_commit,
        "loads_after_model_factor": {
            "force_N": force,
            "moment_Nm": moment,
            "horizontal_resultant_N": horizontal,
            "force_resultant_N": resultant,
        },
        "frame_fem": fem,
        "analytic_indicators": {
            "groove_area_mm2": groove_area,
            "average_glue_shear_MPa": horizontal / groove_area,
            "average_glue_normal_tension_MPa": uplift / groove_area,
            "glue_shear_check": glue,
            "segment_joint_horizontal_check": joints,
            "belluna_screw_uplift_share_N_each_assuming_8": uplift / 8.0,
            "belluna_screw_pullout_reference": side_screw,
            "roof_screw_resultant_share_N_each_assuming_8": resultant / 8.0,
        },
        "omitted_moment_components": {
            "Mx_Nm": moment[0],
            "Mz_Nm": moment[2],
            "reason": (
                "Der bestehende Rahmen-FEM-Lastselektor bildet nur My als "
                "sauberes Kräftepaar ab; Mx/Mz werden ausgewiesen und sind "
                "bei symmetrischer Frontalanströmung auf Relevanz zu prüfen."
            ),
        },
        "limitations": [
            "monolithischer Rahmen; Klebfugen und vier Segmentstöße nicht als Kontakte modelliert",
            "Noppenflächen als starre Fixierung statt nachgiebigem GFK-Dach und Klebstoff",
            "globale Lasten gleichmäßig auf die Adapter-Deckfläche verteilt",
            "nur My explizit als Kräftepaar; Mx und Mz nicht in CalculiX eingeleitet",
            "CFD selbst ist weder vollständig netzkonvergiert noch experimentell korreliert",
            "Schraubenwerte sind reine Gleichverteilungsindikatoren, kein Schrauben-/GFK-Nachweis",
        ],
    }
    result_path = matrix_dir / "structural_check.json"
    result_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    util = transfer["utilization_of_existing_envelopes"]
    lines = [
        "# Vorläufiger Strukturcheck der offenen CFD-Last",
        "",
        f"Matrix `{comparison['comparison_hash']}` · "
        "**PRELIMINARY_STRUCTURAL_CHECK** · nicht freigabewirksam",
        "",
        f"- Kraft nach Modellfaktor: `{force}` N",
        f"- Moment nach Modellfaktor: `{moment}` Nm",
        f"- Horizontale Hülllastauslastung: **{util['horizontal']:.1%}**",
        f"- Nickmoment-Hülllastauslastung: **{util['pitch_y']:.1%}**",
        f"- Vertikal gegenüber Schlechtweg-Betrag: "
        f"**{util['vertical_vs_road_magnitude']:.1%}**",
        "",
        "## Rahmen-FEM",
        "",
        f"- von Mises: **{fem['vm_max_MPa']:.3f} MPa** bei "
        f"{fem['allowable_MPa']:.3f} MPa Kurzzeitzulässigkeit",
        f"- maximale Verformung: **{fem['defl_max_mm']:.4f} mm**",
        f"- Deckflächenverformung: **{fem['defl_top_mm']:.4f} mm**",
        f"- rechnerisch: **{'PASS' if fem['PASS'] else 'FAIL'}**",
        "",
        "## Einfache Lastpfad-Indikatoren",
        "",
        f"- Kleberille: {groove_area:.0f} mm²; mittlere Schubspannung "
        f"{horizontal / groove_area:.4f} MPa; mittlere Zugspannung "
        f"{uplift / groove_area:.4f} MPa",
        f"- Segmentstoß unter voller Horizontallast: "
        f"{'PASS' if joints['PASS'] else 'FAIL'}",
        f"- Belluna-Schraube bei ideal 8-facher Aufteilung der Zuglast: "
        f"{uplift / 8.0:.1f} N je Schraube",
        f"- Dachschraube bei ideal 8-facher Aufteilung der Resultierenden: "
        f"{resultant / 8.0:.1f} N je Schraube (ohne Kapazitätsaussage)",
        "",
        "Diese Rechnung ergänzt LF1–LF4, ändert sie aber nicht. Kontakte, "
        "Dachnachgiebigkeit, Beschichtungszustand und reale Lastverteilung "
        "müssen für eine Freigabe separat validiert werden.",
        "",
    ]
    (matrix_dir / "structural_check.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(f"CFD-FEM-ERGEBNIS: {result_path}", flush=True)
    return output


# freecadcmd führt Skripte nicht auf allen macOS-Versionen als __main__ aus.
main()
