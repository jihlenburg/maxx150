"""Lastfälle LF1-LF4 als Code (Spec §6). LF5 (Thermik) ist analytisch in
fem/analytic.py. Kräfte werden als (face_names, richtung, betrag_N) geliefert;
ConstraintForce verteilt den Betrag über die referenzierten Flächen."""
from dataclasses import dataclass
from typing import Callable

import Part
from FreeCAD import Vector

import params as PRM
from model.frame import top_z


def top_faces(shape, p):
    """Exakte Selektion der Deckfläche: planar, Normale ~ +z, |z - top_z| <
    0.01. Kein Fallback -- nach removeSplitter existiert genau eine
    zusammenhängende Deckfläche bei top_z(p)."""
    target = top_z(p)
    out = []
    for i, f in enumerate(shape.Faces):
        if not isinstance(f.Surface, Part.Plane):
            continue
        n = f.normalAt(0, 0)
        if abs(n.x) > 1e-3 or abs(n.y) > 1e-3 or abs(n.z - 1.0) > 1e-3:
            continue
        if abs(f.CenterOfMass.z - target) < 0.01:
            out.append(i)
    return tuple(f"Face{i+1}" for i in out)


def nopple_faces(shape, p):
    """Exakte Selektion der Noppenflächen bei z = -GLUE_GAP: NUR die ebene,
    nach -z gerichtete Stirnfläche jeder Noppe -- nicht ihre Zylinder-/
    Kegelmantelfläche (Task 15: der Übergangskegel am Noppenfuß teilt die
    vormals durchgehende Zylindermantelfläche in eine kurze untere
    Restfläche + die neue Kegelflanke; deren CoM liegt näher an
    z=-GLUE_GAP als die volle, ungeteilte Mantelfläche vorher -- ein reiner
    CoM-Toleranzfilter [wie zuvor via _planar_faces] würde sie ab jetzt
    fälschlich mit einsammeln, siehe tests/test_loadcases.py::
    test_face_selektoren). Analog zu top_faces(): Plane + Normale ~ -z."""
    out = []
    for i, f in enumerate(shape.Faces):
        if not isinstance(f.Surface, Part.Plane):
            continue
        n = f.normalAt(0, 0)
        if abs(n.x) > 1e-3 or abs(n.y) > 1e-3 or abs(n.z + 1.0) > 1e-3:
            continue
        if abs(f.CenterOfMass.z - (-p.GLUE_GAP)) < 0.01:
            out.append(i)
    return tuple(f"Face{i+1}" for i in out)


def outer_wall_faces(shape, p, sign):
    """Außenwandflächen in Fahrtrichtung (sign=+1 Heck/+x, sign=-1
    Front/-x); leiten das Wind-Kippmoment über den Außenlängen-Hebel ein.
    Fase unten kürzt die Wandfläche (bleibt aber in ihrer x-Ebene), Ecken
    sind Zylinderflächen (R_OUT) -> fallen durch den Planaritäts-/
    Normalenfilter raus."""
    target = (p.CUTOUT_W / 2 + p.W_TOP_REAR) if sign > 0 else -(p.CUTOUT_W / 2 + p.W_TOP_FRONT)
    out = []
    for i, f in enumerate(shape.Faces):
        if not isinstance(f.Surface, Part.Plane):
            continue
        n = f.normalAt(0, 0)
        if abs(n.x) <= 0.99:
            continue
        if abs(f.CenterOfMass.x - target) < 0.5:
            out.append(i)
    return tuple(f"Face{i+1}" for i in out)


def couple_force(shape, p) -> float:
    """Kräftepaar-Betrag, das das Wind-Kippmoment über die Außenwände
    einleitet. Hebelarm = Außenlänge L (PRM.outer_dims(p)[0])."""
    L = PRM.outer_dims(p)[0]
    m_nmm = PRM.wind_force(p) * (p.H_CG + top_z(p))
    return m_nmm / L


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
    # Momenteneinleitung vereinfacht über die Außenwände (Hebel =
    # Außenlänge L); Vorzeichen sind für das linear-statische Maximum
    # irrelevant.
    return [
        (top_faces(shape, p), Vector(1, 0, 0), PRM.wind_force(p)),
        (outer_wall_faces(shape, p, -1), Vector(0, 0, -1), fc),
        (outer_wall_faces(shape, p, +1), Vector(0, 0, 1), fc),
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
