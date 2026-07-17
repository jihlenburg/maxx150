"""Parametrische Rekonstruktion der Belluna-Karosseriebefestigungsplatte.

Dies ist ausdrücklich **kein Hersteller-CAD-Modell**. Die Geometrie bildet
die fotografisch und manuell vermessene Schnittstelle für Passungsprüfung,
Renderings und Montageanleitung ab. Gemessene und angenommene Größen werden
im Exportmanifest unter ``references/belluna/models`` getrennt ausgewiesen.

Koordinaten: z=0 = Flansch-UNTERSEITE (Auflage-/Kontaktebene auf unserem
Adapterdeck), Ursprung Plattenmitte. z+ zeigt zum Luefter.

Der Modulimport erzeugt keine Dateien. Versionierte STEP-/STL-Referenzen
werden mit ``python3 -m pipeline references`` exportiert.
"""
from __future__ import annotations

import FreeCAD as App
import Part

# --- GEMESSEN (messwerte.json, 2026-07-13) ---
FL_HALF = 225.0      # A1a/A1b: Flansch 450 x 450, voll symmetrisch
BAND_W = 26.0        # A1c-f: Flanschbreite je Seite (Doku, ergibt sich unten)
TROUGH_D = 2.0       # A2c: Steghoehe = Kanaltiefe
FL_T = 1.5           # Flanschdicke (gemessen 2026-07-13): DUENNES Spritzguss-
                     # teil; die 'Kanaele' sind Zwischenraeume zwischen 2 mm
                     # nach unten stehenden Stegen, keine Nuten im Vollmaterial
# Unterseiten-Bandprofil (IMG_0314): von INNEN nach AUSSEN
# 8er-Kanal | 2er-Steg | 6er-Kanal | 2er-Steg | 6er-Kanal | 2er-Steg = 26
STEGE = ((207.0, 209.0), (215.0, 217.0), (223.0, 225.0))     # (innen, aussen) je Steg
PLATE_BOT = TROUGH_D           # Platten-Unterseite (z=0 = Steg-Spitzen/Auflage)
PLATE_TOP = TROUGH_D + FL_T    # 3.5 = Flansch-Oberseite
COLLAR_H = 20.0      # A3b: oberer Clip-Kragen
KRAGEN_D = 19.0      # A4a: unterer Einbaukragen unter Flansch-Unterseite (gemessen 19)
CLIP_Z = 12.0        # A5a: Clip-Loch ueber Flansch-OBERSEITE
CLIP_OFF = 60.0      # A5b: Clip-Mitte ab OEFFNUNGS-Ecke (Zollstock-Foto), je Seite 2x
OPEN_HALF = 173.0    # A6: lichte Oeffnung 346 (gemessen 2026-07-13)
SEAL_W = 6.0         # A8: Runddichtung am Kragenfuss, aussen (gemessen)
COLLAR_WALL = 3.0    # A9: Wandstaerke oberer Clip-Kragen (gemessen)
RIB_W = 2.0          # A10a: Haltesteg um die Dichtung, Breite (gemessen)
RIB_H = 8.0          # A10b: Haltesteg Hoehe ueber Flansch (gemessen)
# Oberseite von innen nach aussen, an A6 verankert (A10-Notiz messwerte.json):
# Oeffnung 173 | Kragen 3 | Dichtung 6 | Haltesteg 2 -> Auflage 41 (~A7=40)
COLLAR_OUT = OPEN_HALF + COLLAR_WALL               # 176
SEAL_OUT = COLLAR_OUT + SEAL_W                     # 182
RIB_OUT = SEAL_OUT + RIB_W                         # 184

# --- Gemessen 2026-07-14 bzw. weiterhin angenommene Detailgrößen ---
R_OUT_ANN = 18.0         # ANNAHME: Außeneckenradius (nur Foto/kosmetisch)
KRAGEN_OUT = 198.5       # A3a GEMESSEN: unterer Kragen außen 397 mm
LOWER_WALL = 1.5         # A3c GEMESSEN: Wandstärke unterer Einbaukragen
HOLE_D = 4.0             # F3 GEMESSEN: Befestigungsloch-Durchmesser
HOLE_Z = -10.0           # F2 GEMESSEN: Lochmitte 10 unter der Auflageflaeche
HOLE_OFF_3 = 140.0       # F1a GEMESSEN: 3-Loch-Seiten, Aussenpaar ab Mittelloch
HOLE_OFF_2 = 165.0       # F1b GEMESSEN: 2-Loch-Seiten, Paar ab Seitenmitte
GUSSET_W = 1.0           # G1 GEMESSEN: Gussetbreite
GUSSET_POS = (-150.0, -50.0, 50.0, 150.0)   # G2 GEMESSEN: Teilung 100


def rr(half, r, z0, z1):
    """Gerundetes Quadrat (Fillet an den 4 senkrechten Kanten)."""
    box = Part.makeBox(2 * half, 2 * half, z1 - z0, App.Vector(-half, -half, z0))
    senkrecht = [e for e in box.Edges
                 if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6]
    return box.makeFillet(r, senkrecht)


def ring(half_out, r_out, half_in, r_in, z0, z1):
    """Rechteckiger Ring: gerundetes Aussenquadrat (Halbseite half_out,
    Eckradius r_out) minus gerundetes Innenquadrat (half_in, r_in); z von z0
    bis z1."""
    return rr(half_out, r_out, z0, z1).cut(rr(half_in, r_in, z0 - 1, z1 + 1))


def rot4(shape):
    """Ein Werkzeug fuer die +y-Seite -> alle 4 Seiten."""
    out = [shape]
    for ang in (90, 180, 270):
        s = shape.copy()
        s.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), ang)
        out.append(s)
    return out


# --- Flansch: 1,5-mm-Grundplatte + 3 nach unten stehende 2er-Stege ---
flansch = rr(FL_HALF, R_OUT_ANN, PLATE_BOT, PLATE_TOP)


def _r(h):
    """Eckradius eines Rings im Band, vom Aussenradius abgeleitet."""
    return max(3.0, R_OUT_ANN - (FL_HALF - h))


for s_in, s_out in STEGE:
    flansch = flansch.fuse(ring(s_out, _r(s_out), s_in, _r(s_in), 0, PLATE_BOT + 0.5))

# --- oberer Clip-Kragen (bildet die Oeffnungskante; sitzt weit innen,
# die beiden Kragen fluchten NICHT) ---
collar = ring(COLLAR_OUT, 21, OPEN_HALF, 20,
              PLATE_TOP, PLATE_TOP + COLLAR_H)
# Runddichtung (A8) in der Tasche zwischen Kragen und Haltesteg
dichtring = ring(SEAL_OUT, 22, COLLAR_OUT, 21,
                 PLATE_TOP, PLATE_TOP + SEAL_W)
# Haltesteg (A10) aussen um die Dichtung
haltesteg = ring(RIB_OUT, 23, SEAL_OUT, 22, PLATE_TOP, PLATE_TOP + RIB_H)

# --- unterer Einbaukragen (taucht in den 400er-Ausschnitt) ---
kragen = ring(KRAGEN_OUT, 26, KRAGEN_OUT - LOWER_WALL, 24,
              -KRAGEN_D, PLATE_BOT + 1)

# --- Gussets: unter der inneren Flansch-Lippe, tauchen mit ein ---
g_in = KRAGEN_OUT - LOWER_WALL
gussets = []
for pos in GUSSET_POS:
    x = pos - GUSSET_W / 2
    poly = Part.makePolygon([App.Vector(x, OPEN_HALF, PLATE_BOT + 0.5),
                             App.Vector(x, g_in, PLATE_BOT + 0.5),
                             App.Vector(x, g_in, -KRAGEN_D),
                             App.Vector(x, OPEN_HALF, PLATE_BOT + 0.5)])
    tri = Part.Face(poly).extrude(App.Vector(GUSSET_W, 0, 0))
    gussets.extend(rot4(tri))
# Diagonal-Gussets in den 4 Ecken (Fotos 2026-07-13); Radialmasse werden vom
# Oeffnungs-Cut bzw. der Kragenwand sauber getrimmt/eingebettet
_u = 2 ** 0.5 / 2


def _p(d, z):
    return App.Vector(d * _u, d * _u, z)


eck = Part.Face(Part.makePolygon([_p(232, PLATE_BOT + 0.5), _p(268, PLATE_BOT + 0.5),
                                  _p(268, -KRAGEN_D), _p(232, PLATE_BOT + 0.5)]))
eck = eck.extrude(App.Vector(-_u * 2, _u * 2, 0))
gussets.extend(rot4(eck))

body = flansch
for s in [collar, haltesteg, kragen] + gussets:
    body = body.fuse(s)

# zentrale Oeffnung + seitliche Befestigungsloecher im unteren Kragen
# (F1-Zaehlung gemessen: 3 je +-y-Seite [Mitte+Paar], 2 je +-x-Seite)
body = body.cut(rr(OPEN_HALF, 25, -KRAGEN_D - 5, PLATE_TOP + COLLAR_H + 5))


def _loch(xo):
    return Part.makeCylinder(HOLE_D / 2, 12,
                             App.Vector(xo, g_in - 4, HOLE_Z),
                             App.Vector(0, 1, 0))


loecher = []
for xo in (-HOLE_OFF_3, 0.0, HOLE_OFF_3):
    for ang in (0, 180):
        z = _loch(xo)
        z.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), ang)
        loecher.append(z)
for xo in (-HOLE_OFF_2, HOLE_OFF_2):
    for ang in (90, 270):
        z = _loch(xo)
        z.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), ang)
        loecher.append(z)
for z in loecher:
    body = body.cut(z)

# --- Metallclips (2 je Seite, CLIP_OFF ab Oeffnungs-Ecke, Loch bei CLIP_Z) ---
c_in = OPEN_HALF                                   # 173 = Collar innen = Oeffnung
clips = []
for xo in (-(OPEN_HALF - CLIP_OFF), OPEN_HALF - CLIP_OFF):    # +-113 ab Seitenmitte
    tab = Part.makeBox(12, 1.2, 18, App.Vector(xo - 6, c_in - 1.2, 10))
    loch = Part.makeCylinder(2, 6, App.Vector(xo, c_in - 4, PLATE_TOP + CLIP_Z),
                             App.Vector(0, 1, 0))
    clips.extend(rot4(tab.cut(loch)))
clips_comp = Part.makeCompound(clips)


PLATTE = body
CLIPS = clips_comp
DICHTRING = dichtring


def shapes() -> dict[str, Part.TopoShape]:
    """Liefert unabhängige Kopien der drei Referenzkomponenten."""
    return {
        "belluna_platte": PLATTE.copy(),
        "belluna_metallclips": CLIPS.copy(),
        "belluna_dichtring": DICHTRING.copy(),
    }


def metadata() -> dict:
    """Provenienz der Rekonstruktion, maschinenlesbar für das Manifest."""
    return {
        "classification": "MEASURED_RECONSTRUCTION",
        "manufacturer_cad": False,
        "measured_mm": {
            "flange_outer": 2 * FL_HALF,
            "flange_thickness": FL_T,
            "lower_collar_outer": 2 * KRAGEN_OUT,
            "lower_collar_wall": LOWER_WALL,
            "lower_collar_depth": KRAGEN_D,
            "clear_opening": 2 * OPEN_HALF,
            "upper_collar_wall": COLLAR_WALL,
            "seal_width": SEAL_W,
            "clip_hole_diameter": 2 * 2.0,
        },
        "assumed_mm": {
            "outer_corner_radius": R_OUT_ANN,
            "lower_collar_corner_radius_outer": 26.0,
            "lower_collar_corner_radius_inner": 24.0,
        },
    }
