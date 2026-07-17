"""Aerodynamisches Belluna-Hüllmodell aus der Einbauanleitung.

Das Modell ist **kein Hersteller-CAD**. Es rekonstruiert ausschließlich die
für globale Windkräfte maßgebenden Silhouetten aus Seite 10: 593 x 420 mm,
127 mm geschlossen und 182 mm vollständig geöffnet. Kleine Sicken,
Mechanikdetails und Wanddicken werden absichtlich nicht nachgebildet.

Koordinaten: Ausschnittmitte x/y=0, Dachoberseite z=0, +x zum Fahrzeugheck.
Alle Geometriewerte in diesem FreeCAD-Modul sind Millimeter.
"""
from __future__ import annotations

import FreeCAD as App
import Part

import params as PRM
from cfd.config import AERO, MODEL_REV


# Stationswerte nach der maßstäblichen Seiten-/Draufsicht angenähert. Die
# dokumentierten Gesamtmaße sind exakt; Zwischenkonturen sind Hüllannahmen.
_X_FRAC = (-1.0, -0.91, -0.74, -0.51, -0.17, 0.17, 0.51, 0.74, 0.91, 1.0)
_HALF_WIDTH_FRAC = (0.06, 0.72, 0.94, 1.0, 0.99, 0.97, 0.93, 0.86, 0.66, 0.06)
_TOP_HEIGHT_FRAC = (0.34, 0.47, 0.64, 0.78, 0.91, 0.98, 1.0, 0.97, 0.80, 0.50)
_EDGE_HEIGHT_FRAC = (0.25, 0.25, 0.24, 0.23, 0.23, 0.23, 0.24, 0.25, 0.27, 0.30)


def _rounded_box(length: float, width: float, radius: float,
                 z0: float, z1: float) -> Part.TopoShape:
    box = Part.makeBox(length, width, z1 - z0,
                       App.Vector(-length / 2, -width / 2, z0))
    vertical = [edge for edge in box.Edges
                if abs(edge.Vertexes[0].Point.z -
                       edge.Vertexes[1].Point.z) > 1e-6]
    return box.makeFillet(radius, vertical)


def _hood_loft(*, inset_mm: float = 0.0,
               top_offset_mm: float = 0.0,
               bottom_mm: float | None = None) -> Part.TopoShape:
    """Geschlossene Querschnittslofts; inset/top_offset bauen die Innenschale."""
    mount = PRM.P.H_RAISE
    half_length = AERO.hood_length_mm / 2 - inset_mm
    half_width = AERO.hood_width_mm / 2 - inset_mm
    bottom = mount if bottom_mm is None else bottom_mm
    wires = []
    for xf, wf, zf, ef in zip(_X_FRAC, _HALF_WIDTH_FRAC,
                              _TOP_HEIGHT_FRAC, _EDGE_HEIGHT_FRAC):
        x = xf * half_length
        width = max(2.0, wf * half_width)
        z_center = mount + zf * AERO.closed_height_mm - top_offset_mm
        z_edge = mount + ef * AERO.closed_height_mm - top_offset_mm
        points = [App.Vector(x, -width, bottom)]
        for index in range(17):
            ratio = -1.0 + 2.0 * index / 16
            crown = max(0.0, 1.0 - ratio * ratio) ** 0.58
            z = z_edge + (z_center - z_edge) * crown
            points.append(App.Vector(x, ratio * width, z))
        points.extend((App.Vector(x, width, bottom), points[0]))
        wires.append(Part.makePolygon(points))
    # Ruled verhindert das bei glatten OCC-Lofts beobachtete Überschwingen
    # außerhalb der dokumentierten 593/127-mm-Hülle. Zehn eng gesetzte
    # Stationen halten die aerodynamische Kontur trotzdem ausreichend glatt.
    return Part.makeLoft(wires, True, True)


def _base_body() -> Part.TopoShape:
    mount = PRM.P.H_RAISE
    return _rounded_box(AERO.mounting_plate_mm, AERO.mounting_plate_mm,
                        18.0, mount, mount + 34.0)


def closed_shape() -> Part.TopoShape:
    """Geschlossene Belluna-Hülle als ein Körper: Haubenloft verschmolzen mit
    dem Sockelkörper (450-mm-Montageplatte)."""
    return _hood_loft().fuse(_base_body()).removeSplitter()


def open_shape() -> Part.TopoShape:
    """Dünne Haube in einer aus der 127/182-mm-Hüllhöhe abgeleiteten Lage."""
    outer = _hood_loft()
    inner = _hood_loft(
        inset_mm=AERO.lid_thickness_mm,
        top_offset_mm=AERO.lid_thickness_mm,
        bottom_mm=PRM.P.H_RAISE - 12.0,
    )
    lid = outer.cut(inner)
    pivot = App.Vector(-0.43 * AERO.hood_length_mm, 0,
                       PRM.P.H_RAISE + 42.0)
    lid.rotate(pivot, App.Vector(0, 1, 0), -6.2)
    target = PRM.P.H_RAISE + AERO.open_height_mm
    lid.translate(App.Vector(0, 0, target - lid.BoundBox.ZMax))
    return Part.makeCompound((_base_body(), lid))


def adapter_shape() -> Part.TopoShape:
    """Vereinfachter Adapter-Hüllquader (Außenmaße x R_OUT, z von 0 bis
    H_RAISE) als CFD-Referenzkörper unter der Haube."""
    length, width = PRM.outer_dims(PRM.P)
    return _rounded_box(length, width, PRM.P.R_OUT, 0.0, PRM.P.H_RAISE)


def roof_edge_shape() -> Part.TopoShape:
    """Quaderförmiger Dachkanten-Störkörper an der Ausschnitt-Hinterkante
    (x = CUTOUT_W/2 + EDGE_DIST, Höhe EDGE_H), obere Kanten verrundet; liefert
    die anströmseitige Dachkante der CFD-Domäne."""
    edge_x = PRM.P.CUTOUT_W / 2 + PRM.P.EDGE_DIST
    shape = Part.makeBox(AERO.roof_edge_depth_mm, AERO.roof_edge_span_mm,
                         PRM.P.EDGE_H,
                         App.Vector(edge_x, -AERO.roof_edge_span_mm / 2, 0))
    top_edges = [edge for edge in shape.Edges
                 if all(vertex.Point.z > PRM.P.EDGE_H - 1e-6
                        for vertex in edge.Vertexes)]
    try:
        return shape.makeFillet(min(25.0, PRM.P.EDGE_H * 0.45), top_edges)
    except Part.OCCError:
        return shape


def shapes() -> dict[str, Part.TopoShape]:
    """Alle CFD-Hüllgeometrien als Dict: belluna_closed, belluna_open, adapter
    und roof_edge."""
    return {
        "belluna_closed": closed_shape(),
        "belluna_open": open_shape(),
        "adapter": adapter_shape(),
        "roof_edge": roof_edge_shape(),
    }


def metadata() -> dict:
    """Provenienz-Metadaten der CFD-Hüllrekonstruktion (Klassifikation, Quelle
    Seite 10, dokumentierte vs. angenommene Maße, Einbaulage); fließt in den
    CFD-Hash und die Manifeste ein."""
    return {
        "classification": "AERODYNAMIC_ENVELOPE_RECONSTRUCTION",
        "manufacturer_cad": False,
        "model_rev": MODEL_REV,
        "source": "Belluna Super Fan Einbauanleitung, Seite 10",
        "documented_mm": {
            "hood_length": AERO.hood_length_mm,
            "hood_width": AERO.hood_width_mm,
            "mounting_plate": AERO.mounting_plate_mm,
            "closed_height_above_mount": AERO.closed_height_mm,
            "open_height_above_mount": AERO.open_height_mm,
        },
        "assumptions": {
            "intermediate_sections": "scaled visual reconstruction",
            "open_motion_deg": 6.2,
            "small_details": "omitted",
            "flow_direction": "+x toward vehicle rear",
        },
        "installation_mm": {
            "adapter_raise": PRM.P.H_RAISE,
            "roof_edge_x_from_cutout_centre": (
                PRM.P.CUTOUT_W / 2 + PRM.P.EDGE_DIST),
            "roof_edge_height": PRM.P.EDGE_H,
        },
    }
