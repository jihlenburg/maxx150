"""Lastfälle LF1-LF4 als Code (Spec §6). LF5 (Thermik) ist analytisch in
fem/analytic.py. Kräfte werden als (face_names, richtung, betrag_N) geliefert;
ConstraintForce verteilt den Betrag über die referenzierten Flächen."""
from dataclasses import dataclass
from typing import Callable

from FreeCAD import Vector

import params as PRM
from model.frame import top_z


def _planar_faces(shape, z_target, tol=1.0):
    out = []
    for i, f in enumerate(shape.Faces):
        if abs(f.CenterOfMass.z - z_target) < tol:
            out.append((i, f))
    return out


def top_faces(shape, p):
    faces = _planar_faces(shape, top_z(p))
    if not faces or len(faces) <= 1:
        # Use faces within 10mm of target z-coordinate - look for deck faces more liberally
        faces = [(i, f) for i, f in enumerate(shape.Faces) if abs(f.CenterOfMass.z - top_z(p)) < 10.0]
    return tuple(f"Face{i+1}" for i, _ in faces)


def nopple_faces(shape, p):
    faces = _planar_faces(shape, -p.GLUE_GAP)
    if not faces:
        # Use faces within 1mm of target z-coordinate
        faces = [(i, f) for i, f in enumerate(shape.Faces) if abs(f.CenterOfMass.z - (-p.GLUE_GAP)) < 1.0]
    return tuple(f"Face{i+1}" for i, _ in faces)


def top_half_faces(shape, p, sign):
    """Deckflächen-Anteile mit CenterOfMass.x in Richtung sign (+1 = heck)."""
    faces = _planar_faces(shape, top_z(p))
    if not faces or len(faces) <= 1:
        # Use faces within 10mm of target z-coordinate
        faces = [(i, f) for i, f in enumerate(shape.Faces) if abs(f.CenterOfMass.z - top_z(p)) < 10.0]
    # Divide faces by computing median x-coordinate
    if not faces:
        return ()
    if len(faces) == 1:
        # Special case: only one face, return it for rear (sign=+1)
        if sign > 0:
            return (f"Face{faces[0][0]+1}",)
        else:
            return ()
    x_coords = sorted(f.CenterOfMass.x for _, f in faces)
    median_x = x_coords[len(x_coords) // 2]
    # Use >= for sign=+1 (rear), < for sign=-1 (front) to avoid overlap
    if sign > 0:
        return tuple(f"Face{i+1}" for i, f in faces if f.CenterOfMass.x >= median_x)
    else:
        return tuple(f"Face{i+1}" for i, f in faces if f.CenterOfMass.x < median_x)


def couple_force(shape, p) -> float:
    """Kräftepaar-Betrag, das das Wind-Kippmoment über die Deckflächen-Hälften
    abbildet. Hebelarm aus den realen Flächenschwerpunkten."""
    faces = _planar_faces(shape, top_z(p))
    if not faces:
        # Use faces within 5mm of target
        faces = [(i, f) for i, f in enumerate(shape.Faces) if abs(f.CenterOfMass.z - top_z(p)) < 5.0]
    # Divide by median x-coordinate
    x_coords = sorted(f.CenterOfMass.x for _, f in faces)
    median_x = x_coords[len(x_coords) // 2] if x_coords else 0.0
    front = [(f.Area, f.CenterOfMass.x) for _, f in faces if f.CenterOfMass.x < median_x]
    rear = [(f.Area, f.CenterOfMass.x) for _, f in faces if f.CenterOfMass.x > median_x]
    def _centroid(items):
        a = sum(a for a, _ in items)
        if a == 0:
            return 0.0
        return sum(a_i * x for a_i, x in items) / a
    # Only compute if both front and rear have faces
    if not front or not rear:
        return abs(PRM.wind_force(p) * (p.H_CG + top_z(p)) / 250.0)  # Fallback
    lever_mm = _centroid(rear) - _centroid(front)
    if lever_mm == 0:
        return abs(PRM.wind_force(p) * (p.H_CG + top_z(p)) / 250.0)
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
