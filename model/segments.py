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
            cuts.append(F.rotz(c, k))
    return cuts


def _one_segment(frame, p, k):
    """Segment für Quadrant k (0: +x/+y, dann gegen den Uhrzeigersinn)."""
    h = top_z(p)
    lap_h = h / 2
    t = p.TOL_JOINT
    # z-Start der Lappen-Werkzeuge: unter die Noppenbasis (statt nur -0.5)
    # ziehen. Grund: Von den 4 Rand-Noppenringen (rect_path_points, siehe
    # frame._nopple_positions) liegt je Seite genau eine Noppe exakt auf der
    # Symmetrieachse (x=0 bzw. y=0) -- Mittelpunkt der jeweiligen Kantenpunkt-
    # folge. Diese Noppe fällt zugleich in das Stoßband x/y in [0, LAP_L].
    # Endete der Lappenschnitt (wie ursprünglich) erst bei z=-0.5, würde nur
    # der obere Rand dieser Noppe (z -0.5..0) abgetrennt, der Noppenfuß
    # (z -GLUE_GAP..-0.5) aber unverbunden als eigene, hauchdünne Shell
    # zurückbleiben (Volumen ~63 mm³, isValid() zunächst noch True). Diese
    # lose Shell macht spätere Booleans (z. B. das Fuse+removeSplitter im
    # Union-Test) numerisch instabil und lässt Segmente nachträglich als
    # "Unorientable shape" ungültig werden. Fix: Lappenwerkzeuge bis unter
    # die Noppenbasis ausdehnen, damit eine im Stoßband liegende Noppe IMMER
    # vollständig abgegeben wird (nie angeschnitten):
    z_lap0 = -(p.GLUE_GAP + 1)
    # Unterkragen (GEOM_REV 3): Lappenwerkzeuge bis unter die Kragenkante
    # ziehen, damit der Halbüberlappungsstoß auch durch den Kragen läuft
    # (statt eines gemischten Lap/Stumpf-Stoßes ab z=-GLUE_GAP-1). Die
    # Kragenlöcher liegen per validate() mindestens LAP_L+10 von der
    # Seitenmitte entfernt und bleiben vom Stoßband unberührt.
    if p.BOT_KRAGEN:
        z_lap0 = -(p.GLUE_GAP + p.BOT_KRAGEN_DEPTH + 1)
    # Kernquadrant x>=0, y>=0:
    core = Part.makeBox(BIG, BIG, BIG, Vector(0, 0, -BIG / 2))
    # Lappe (untere Hälfte inkl. evtl. Stoßband-Noppe), ragt am Stoß A um
    # LAP_L-t nach y<0, im +x-Band:
    lap_add = Part.makeBox(BIG, p.LAP_L - t, (lap_h - t) - z_lap0,
                           Vector(p.CUTOUT_W / 2 - 5, -(p.LAP_L - t), z_lap0))
    # Abgabe am Stoß B: untere Hälfte (inkl. evtl. Stoßband-Noppe) bis LAP_L
    # im +y-Band entfernen. Endet exakt bei z=lap_h (kein Rest oberhalb, sonst
    # Überschneidung mit lap_add des Nachbarn um TOL_JOINT statt Luftspalt):
    lap_cut = Part.makeBox(p.LAP_L, BIG, lap_h - z_lap0,
                           Vector(0, p.CUTOUT_W / 2 - 5, z_lap0))
    seg = frame.common(F.rotz(core, k))
    seg = seg.fuse(frame.common(F.rotz(lap_add, k)))
    seg = seg.cut(F.rotz(lap_cut, k))
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
