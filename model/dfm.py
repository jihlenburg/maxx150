"""Design-for-Manufacturing-Prüfung: Überhänge in Druckorientierung.
Druckorientierung FDM: Deckfläche auf dem Bett (Teil kopfüber). Facetten,
deren Normale steiler als 45° nach unten zeigt und die nicht auf dem Bett
liegen, brauchen Stützen — außer in bewusst zugelassenen Brückenzonen."""
import math

import MeshPart
from FreeCAD import Matrix

import params as PRM
from model.frame import chamber_slot_count

COS45 = math.cos(math.radians(45))


def _allowed_bridge_area(p):
    """Bewusst zugelassene Brücken (in Druckorientierung nach unten offen):
    1. Gusset-Freistellungsring (Boden 3 mm über Bett),
    2. 4 Kopfsenkungen (Ringdecke über der Bohrung),
    3. 4 Muttertaschen-Decken,
    4. 4 Stoßstufen des Halbüberlappungsstoßes: (LAP_L−TOL_JOINT) Spannweite
       auf halber Bauhöhe — kurze, gerade Brücke (~25 mm), druckbar ohne
       Stützen; Qualität dort unkritisch (innenliegende Fügefläche). Bandbreite
       je Stoß SEITENSPEZIFISCH (Ledger 21/22, vormals global min(W_TOP) für
       alle vier): Summe der vier W_TOP statt 4x min(W_TOP) -- bei
       symmetrischen Defaults identisch (4*min == Summe), siehe
       tests/test_asymmetrie.py für den asymmetrischen Fall;
    5. Vent-Bohrungen der Rippenkammern (Task 14): je Zelle 2 horizontale
       Ø VENT_D-Kanäle (Innenfläche->Ring 1, Ring 1->Ring 2 durch den Steg);
       obere Halbzylinder-Fläche je Kanal, Wandstärke konservativ mit
       max(INNER_WALL, CHAMBER_RIB) angesetzt -- Ø4 ist ohnehin brückenfrei
       druckbar, die Kammerböden selbst (47°-Chevron) tragen sich über die
       Flankenneigung, brauchen also keinen eigenen Term hier.
    6. Eck-Vents der Eckkammern (Task 17, nur wenn CORNER_CHAMBERS): 4 Ecken
       x 2 radiale Ø VENT_D-Kanäle entlang der 45°-Diagonale (analog Zone 5,
       siehe model/frame.py::_corner_chamber_cuts) = 8 Kanäle gesamt, obere
       Halbzylinder-Fläche je Kanal, Wandstärke wieder konservativ mit
       max(INNER_WALL, CHAMBER_RIB) angesetzt. Zusätzlicher Faktor 2
       gegenüber der Zone-5-Formel: die Eck-Kanäle liegen DIAGONAL (45° zu
       beiden Druck-Kippachsen) statt achsparallel -- die projizierte
       Überhangfläche in Druckorientierung (kopfüber, 180°-Kippung um x)
       fällt für eine diagonale Bohrung ungünstiger aus als für eine rein
       x-/y-achsparallele; konservativ verdoppelt statt exakt hergeleitet
       (die Chevron-Sektorböden selbst brauchen weiterhin keinen eigenen
       Term -- gleiches Argument wie Zone 5: >45° in JEDER Radialebene des
       Sektors, siehe _corner_chamber_cuts-Docstring)."""
    # Zone 1 nur, solange die Freistellung existiert (REC_GUSSET_D=0 seit der
    # Messbefund 2026-07-13: kein Recess -> keine Brücke -> kein Freibetrag,
    # sonst würde das Gate um ~30000 mm² zu lasch)
    rec_ring = ((p.CUTOUT_W + 2 * p.REC_GUSSET_W) ** 2 - p.CUTOUT_W ** 2
                if p.REC_GUSSET_D > 0 else 0.0)
    cb = 4 * math.pi * (p.JOINT_CB_D / 2) ** 2
    nut = 4 * 2 * math.sqrt(3) * (p.JOINT_NUT_AF / 2) ** 2
    lap_step = ((p.LAP_L - p.TOL_JOINT)
                * (p.W_TOP_FRONT + p.W_TOP_REAR + p.W_TOP_LEFT + p.W_TOP_RIGHT))
    vent = (chamber_slot_count(p) * 2 * (math.pi / 2) * (p.VENT_D / 2)
            * max(p.INNER_WALL, p.CHAMBER_RIB))
    eck_vent = 0.0
    if p.CORNER_CHAMBERS:
        eck_vent = (8 * (math.pi / 2) * (p.VENT_D / 2)
                    * max(p.INNER_WALL, p.CHAMBER_RIB) * 2)
    # 7. Unterkragen-Schraubenlöcher: 8 horizontale Ø HOLE_D-
    #    Kanäle durch die Kragenwand (achsparallel, analog Zone 5); die
    #    45°-Übergangsfase trägt sich über die Flankenneigung selbst
    #    (Noppenkegel-Präzedenz), braucht keinen eigenen Term.
    kragen_loch = 0.0
    if p.BOT_KRAGEN:
        kragen_loch = (PRM.bot_kragen_hole_count(p) * (math.pi / 2)
                       * (p.BOT_KRAGEN_HOLE_D / 2) * p.BOT_KRAGEN_T)
    return rec_ring + cb + nut + lap_step + vent + eck_vent + kragen_loch


def _facet_points(facet):
    return facet.Points


def _facet_area(facet, pts):
    if hasattr(facet, "Area"):
        return facet.Area
    # Fallback: Fläche aus den drei Eckpunkten per Kreuzprodukt (0.5*|AB x AC|)
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = pts
    abx, aby, abz = bx - ax, by - ay, bz - az
    acx, acy, acz = cx - ax, cy - ay, cz - az
    cx_ = aby * acz - abz * acy
    cy_ = abz * acx - abx * acz
    cz_ = abx * acy - aby * acx
    return 0.5 * math.sqrt(cx_ * cx_ + cy_ * cy_ + cz_ * cz_)


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
        pts = _facet_points(facet)
        z = min(pt.z for pt in pts) if hasattr(pts[0], "z") \
            else min(pt[2] for pt in pts)
        on_bed = z < zmin + 0.3
        if n.z < -COS45 and not on_bed:
            bad += _facet_area(facet, pts)
    return bad, _allowed_bridge_area(p)
