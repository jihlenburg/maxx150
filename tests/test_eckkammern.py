"""Eckkammern (Task 17): optionale 90°-Rotationsfortsetzung der Seiten-
Kammerringe um die vier massiven Eckblöcke (Haupt-Schrumpfspannungs-
Reservoirs laut Herstellbarkeitsanalyse). Default AUS (CORNER_CHAMBERS=False)
-- der verifizierte Stand (GEOM_REV=2) ändert sich geometrisch NICHT; nur
params_hash ändert sich zwangsläufig durch die zwei neuen Parameterfelder
(siehe test_eckkammern_default_anker_unveraendert unten und Report).

Review-Critical-Fix (nach 66/66-grün-Stand 80c6fbb): die ursprüngliche
validate()-Ungleichung verglich den UNKRITISCHEN Sektorpunkt (Außenradius
r_out2) mit der Zellbandgrenze -- der tatsächlich kritische Punkt liegt am
Innenradius r_in1 (siehe model/frame.py::_corner_keepout-Docstring für die
vollständige Herleitung). Empirisch belegt: CORNER_CHAMBERS=True + CELL_L=53
(Defaults sonst unverändert) überschnitt VOR dem Fix die letzte Ring-1-Zelle
der REAR-+u-Halbseite mit dem Ecksektor um 516.3 mm³, obwohl validate() PASS
meldete und build_frame().isValid() sogar True blieb (ein Boolean-Cut mit
überlappenden Werkzeugen bleibt topologisch gültig, entfernt aber zu viel
Material -- die Kollision war "still", keine der bisherigen 6 Eckkammern-
Tests deckte CELL_L != Default ab). Fix: _chamber_cell_centers filtert das
fertig zentrierte Zellraster gegen _corner_keepout(p); PRM.validate() prüft
nur noch die Kohärenzbedingung (Platz für mindestens eine Zelle). Neue
Tests unten: test_eckkammern_kein_kollision_zellraster_ecksektor_cell_l_53
(Fix-Verifikation) und test_eckkammern_p_eck_volumen_exakt_unveraendert
(Fix darf das Default-Eckkammern-Volumen NICHT verändern)."""
import math

import Part

import params as PRM
from model import dfm
from model import features as F
from model import frame
from model.frame import build_frame
from model.segments import build_segments

P_ECK = PRM.Params(CORNER_CHAMBERS=True)


def _frame_eck():
    global _CACHED_FRAME_ECK
    try:
        return _CACHED_FRAME_ECK
    except NameError:
        _CACHED_FRAME_ECK = build_frame(P_ECK)
        return _CACHED_FRAME_ECK


def _frame_default():
    global _CACHED_FRAME_DEFAULT
    try:
        return _CACHED_FRAME_DEFAULT
    except NameError:
        _CACHED_FRAME_DEFAULT = build_frame(PRM.P)
        return _CACHED_FRAME_DEFAULT


def _segs_eck():
    global _CACHED_SEGS_ECK
    try:
        return _CACHED_SEGS_ECK
    except NameError:
        _CACHED_SEGS_ECK = build_segments(P_ECK)
        return _CACHED_SEGS_ECK


def test_eckkammern_frame_valide_und_wasserdicht():
    s = _frame_eck()
    assert s.isValid()
    assert len(s.Shells) == 1 and s.Shells[0].isClosed()


def test_eckkammern_volumendelta_plausibel():
    delta = _frame_default().Volume - _frame_eck().Volume
    assert 2.5e4 < delta < 7.0e4, f"Eckkammer-Volumendelta {delta:.0f} mm³ unplausibel"


def test_eckkammern_segmente_valide_ueberschneidungsfrei():
    segs = _segs_eck()
    assert len(segs) == 4
    for s in segs:
        assert s.isValid() and s.Volume > 1e5
    for i in range(4):
        for j in range(i + 1, 4):
            ov = segs[i].common(segs[j]).Volume
            assert ov < 1.0, f"Segmente {i}/{j} überschneiden sich: {ov:.3f} mm³"


def test_eckkammern_dfm_ueberhang():
    for i, s in enumerate(_segs_eck()):
        bad, allowed = dfm.overhang_area(s, P_ECK)
        assert bad <= allowed * 1.2 + 200, \
            f"Segment {i}: {bad:.0f} mm² Überhang (erlaubt ~{allowed:.0f})"


def test_eckkammern_ohne_chambers_wirft_valueerror():
    try:
        PRM.validate(PRM.Params(CORNER_CHAMBERS=True, CHAMBERS=False))
        assert False, "erwartete ValueError"
    except ValueError:
        pass


def test_eckkammern_default_anker_unveraendert():
    """Default (CORNER_CHAMBERS=False) muss geometrisch IDENTISCH zum
    verifizierten Stand (Ledger 21/22, Task 15) bleiben -- Volumen-Anker
    1736006.070242394 mm³ (Symmetrie-Anker aus todo.md), GEOM_REV bleibt 2.
    params_hash ändert sich zwangsläufig (zwei neue Felder), das ist
    dokumentiert kein Geometrie-Bruch: Volumengleichheit ist der Beleg."""
    v = _frame_default().Volume
    assert abs(v - 1736006.070242394) < 1.0, f"Default-Volumen driftete: {v}"
    h_default = PRM.params_hash(PRM.P)
    h_alt_feld = PRM.params_hash(PRM.Params(CORNER_ANGLE_MARGIN=25.0))
    assert h_default != h_alt_feld


def _side_cavities_only(p):
    """Isoliert NUR die geraden Zell-Kavitäten (ohne Vents, ohne Eck-
    Sektoren) -- identische Konstruktion wie frame._chamber_cuts, aber ohne
    die Vent-Bohrungen und ohne den Eck-Sektor-Anhang, damit sie gezielt
    gegen die Eck-Sektor-Kavitäten (frame._corner_chamber_cuts) auf
    Überschneidung geprüft werden können (siehe Test unten)."""
    r_in1, r_out1, r_in2, r_out2 = frame._ring_radii(p)
    apex_z = p.BOTTOM_T + math.tan(math.radians(p.CHEVRON_DEG)) * (p.CHAMBER_W / 2)
    neighbor_bounds = frame._side_neighbor_bounds(p)
    tools = []
    for k in range(4):
        plus_w, minus_w = neighbor_bounds[k]
        plus_half = frame._chamber_cell_centers(p, plus_w)
        minus_half = frame._chamber_cell_centers(p, minus_w)
        centers = plus_half + [-c for c in minus_half]
        for uc in centers:
            y0 = uc - p.CELL_L / 2
            for r_in, r_out in ((r_in1, r_out1), (r_in2, r_out2)):
                cav = frame._chamber_cavity(r_in, r_out, apex_z, y0, p.CELL_L, p)
                tools.append(F.rotz(cav, k))
    return tools


def test_eckkammern_kein_kollision_zellraster_ecksektor_cell_l_53():
    """Reviewer-Regressionsrezept (Review-Critical, Stand 80c6fbb): CORNER_
    CHAMBERS=True + CELL_L=53 (Defaults sonst unverändert) überschnitt VOR
    dem Fix die letzte Ring-1-Zelle der REAR-+u-Halbseite mit dem Ecksektor
    um 516.3 mm³ -- obwohl PRM.validate() PASS meldete UND build_frame()
    .isValid() True blieb (ein Boolean-Cut mit überlappenden Werkzeugen
    bleibt topologisch gültig, entfernt aber real zu viel Material; siehe
    model/frame.py::_corner_keepout-Docstring für die vollständige
    Herleitung des korrekten, r_in1-basierten kritischen Punkts).

    Testansatz: Summen-Overlap ALLER geraden Zell-Kavitäten (ohne Vents)
    gegen ALLE Eck-Sektor-Kavitäten (ohne Vents), statt nur ein einzelnes
    Zell/Sektor-Paar zu konstruieren -- robuster gegen Interna, weil er
    nicht voraussetzt, WIE die Implementierung das Raster korrigiert. Der
    tatsächliche Fix filtert das fertig zentrierte Raster gegen den
    Keepout (statt es zu verschieben, um den unveränderlichen Default-
    Volumen-Anker zu erhalten, siehe test_eckkammern_p_eck_volumen_exakt_
    unveraendert) -- die im Review-Rezept vorgeschlagene 'letzte Zelle' der
    REAR-+u-Halbseite existiert nach dem Fix in dieser Konfiguration gar
    nicht mehr (sie wird herausgefiltert, siehe frame._chamber_cell_centers)
    -- ein Einzel-Paar-Test würde deshalb nur die (bereits sichere)
    verbleibende letzte Zelle treffen und den Fix nicht wirklich prüfen."""
    p = PRM.Params(CORNER_CHAMBERS=True, CELL_L=53.0)
    PRM.validate(p)  # muss OHNE ValueError durchlaufen (Kohärenz-Check reicht)

    plus_w, _ = frame._side_neighbor_bounds(p)[0]  # k=0 REAR, +u-Halbseite
    centers = frame._chamber_cell_centers(p, plus_w)
    assert centers == [66.5, 122.5], \
        f"REAR +u-Raster bei CELL_L=53 unerwartet: {centers} (erwartet: die " \
        f"kollidierende dritte Zelle bei uc=178.5 muss herausgefiltert sein)"

    straight = Part.makeCompound(_side_cavities_only(p))
    corner_sectors = Part.makeCompound(frame._corner_chamber_cuts(p)[:8])  # nur die
    # 8 Ring1/Ring2-Sektorsolids (Indizes 0..7), OHNE die 8 Diagonal-Vents
    # danach (siehe frame._corner_chamber_cuts: Ring1 k0..k3, Ring2 k0..k3,
    # dann Vents) -- Vents interessieren hier nicht, nur die Kavitäten.
    overlap = straight.common(corner_sectors).Volume
    assert overlap < 1e-6, \
        f"Zellraster überschneidet Ecksektor: {overlap:.3f} mm³ (Regression!)"

    body = build_frame(p)
    assert body.isValid()
    assert len(body.Shells) == 1 and body.Shells[0].isClosed()


def test_eckkammern_p_eck_volumen_exakt_unveraendert():
    """Der Fix darf das Eckkammern-Default-Volumen (P_ECK = alle Parameter
    Default außer CORNER_CHAMBERS=True) NICHT verändern: corner_keepout bei
    Defaults ist 196.22 mm (siehe frame._corner_keepout), die tatsächliche
    Reichweite der letzten Zelle bei Default-CELL_L=45 ist aber nur 193 mm
    -- der neue Keepout-Filter greift bei Defaults also gar nicht (nichts
    wird gefiltert), das Raster bleibt bitidentisch. Exakter Volumen-Anker
    aus dem ursprünglichen Task-17-Report (§7)."""
    v_eck = _frame_eck().Volume
    assert abs(v_eck - 1694758.489540970) < 1.0, f"P_ECK-Volumen driftete: {v_eck}"
    delta = _frame_default().Volume - v_eck
    assert abs(delta - 41247.580701424) < 1.0, f"Delta driftete: {delta:.3f} mm³"
    keepout = frame._corner_keepout(P_ECK)
    assert abs(keepout - 196.223956) < 1e-3, f"corner_keepout driftete: {keepout}"


def test_eckkammern_werkzeugzahl_konsistent_zu_slot_count_cell_l_53(p=None):
    """Task-17-Re-Review Minor 2 (-> Task 16): explizite Konsistenzprüfung
    der GESAMTEN _chamber_cuts-Werkzeugliste gegen chamber_slot_count, INKL.
    der fixen Eck-Werkzeuge -- bisherige Tests prüften nur Volumen/Kollision,
    nicht die WerkzeugANZAHL selbst (die z. B. bei einer künftigen Änderung
    an der Vent-Zahl je Slot oder je Ecke still auseinanderdriften könnte,
    ohne dass Volumen-/Kollisionstests das zwingend auffangen).

    Je Slot (u-Position, siehe frame._chamber_cuts) entstehen GENAU 4
    Werkzeuge: 2 Kammer-Kavitäten (Ring 1 + Ring 2) + 2 Vent-Bohrungen
    (Innenwand->Ring1, Ring1->Ring2). Bei CORNER_CHAMBERS=True kommen GENAU
    16 fixe Eck-Werkzeuge hinzu (frame._corner_chamber_cuts: 2 Ring-Profile x
    4 Ecken = 8 Sektor-Kavitäten + 2 Diagonal-Vent-Positionen x 4 Ecken = 8
    Vents), UNABHÄNGIG von CELL_L/Slot-Zahl -- deshalb testet dieser Test
    explizit mit CELL_L=53 (Reviewer-Regressionsrezept, siehe
    test_eckkammern_kein_kollision_zellraster_ecksektor_cell_l_53 oben), wo
    der Keepout-Filter das Zellraster bereits sichtbar verändert (3 Zellen
    -> 2 Zellen je Halbseite an der REAR-Seite): die Formel muss auch dann
    exakt aufgehen, nicht nur bei unveränderten Defaults."""
    p = p or PRM.Params(CORNER_CHAMBERS=True, CELL_L=53.0)
    PRM.validate(p)
    tools = frame._chamber_cuts(p)
    slots = frame.chamber_slot_count(p)
    assert len(tools) == 4 * slots + 16, (
        f"{len(tools)} Werkzeuge != 4*{slots} (Slot-Kavitäten+Vents) + "
        f"16 (fixe Eck-Werkzeuge)"
    )


def test_eckkammern_werkzeugzahl_konsistent_ohne_eckkammern():
    """Gegenprobe zur Formel oben mit CORNER_CHAMBERS=False (Default): der
    Eck-Term muss auf 0 zurückfallen (_corner_chamber_cuts liefert []),
    NICHT einfach die 16 fixen Eck-Werkzeuge weglassen, weil CELL_L o. Ä.
    sich ändert -- prüft, dass die Formel wirklich an CORNER_CHAMBERS hängt
    und nicht zufällig bei den Default-Zahlen aufgeht."""
    p = PRM.Params(CORNER_CHAMBERS=False)
    tools = frame._chamber_cuts(p)
    slots = frame.chamber_slot_count(p)
    assert len(tools) == 4 * slots
    assert frame._corner_chamber_cuts(p) == []
