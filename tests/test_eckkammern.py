"""Eckkammern (Task 17): 90°-Rotationsfortsetzung der Seiten-Kammerringe um
die vier massiven Eckblöcke (Haupt-Schrumpfspannungs-Reservoirs laut
Herstellbarkeitsanalyse). Seit Task 20 (User-Entscheidung 2026-07-12)
Default EIN (CORNER_CHAMBERS=True). Die GEOM_REV-10-Anker enthalten den
kompakten 50-mm-Hybridrahmen mit zwei Kammerringen: EIN 1673116.7934465515,
AUS 1720654.8776221776 mm³ (siehe test_eckkammern_default_anker und
test_eckkammern_ausschalt_anker unten). GEOM_REV blieb beim Flip 2: reine
Parameter-, keine Code-Änderung -- params_hash ändert sich über das Feld
selbst (neuer Default-Hash, AUS-Variante hasht exakt auf den alten Stand).

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
(Fix-Verifikation) und test_eckkammern_delta_und_keepout_exakt (Fix darf
das Eckkammern-EIN-Volumen NICHT verändern; bis Task 20 hieß der Test
test_eckkammern_p_eck_volumen_exakt_unveraendert)."""
import math

import Part

import params as PRM
from model import dfm
from model import features as F
from model import frame
from model.frame import build_frame
from model.segments import build_segments

# Task 20: der frühere P_ECK-Sonderfall (CORNER_CHAMBERS=True) ist jetzt der
# Default -- alle EIN-Tests laufen direkt auf PRM.P. Die AUS-Variante bleibt
# als eigener Parametersatz beweisbar (alter Default-Anker).
# Anker-Fixtures bauen seit GEOM_REV 3 explizit OHNE Unterkragen: der
# Kragen ist rein additiv, ohne ihn ist die Geometrie bitidentisch zum in
# Task 17/20 verifizierten GEOM-REV-2-Stand -- die exakten Volumen-Anker
# unten bleiben damit beweisbar gueltig (Kragen-Delta prueft
# tests/test_bot_kragen.py gegen den EIN-Anker).
# ...und pinnen zusätzlich CELL_L=45/REC_GUSSET_D=3 (die Defaults, unter
# denen die Anker in Task 17/20 gemessen wurden -- seit der Messwertübernahme
# 2026-07-13 sind die Projekt-Defaults 43/0).
P_EIN_OHNE_KRAGEN = PRM.Params(BOT_KRAGEN=False, CELL_L=45.0, REC_GUSSET_D=3.0)
P_AUS = PRM.Params(CORNER_CHAMBERS=False, BOT_KRAGEN=False,
                   CELL_L=45.0, REC_GUSSET_D=3.0)


def _frame_default():
    """Eckkammern-EIN-Referenz OHNE Unterkragen (GEOM-REV-2-Anker; seit
    GEOM_REV 3 bewusst nicht mehr PRM.P -- siehe P_EIN_OHNE_KRAGEN oben)."""
    global _CACHED_FRAME_DEFAULT
    try:
        return _CACHED_FRAME_DEFAULT
    except NameError:
        _CACHED_FRAME_DEFAULT = build_frame(P_EIN_OHNE_KRAGEN)
        return _CACHED_FRAME_DEFAULT


def _frame_aus():
    global _CACHED_FRAME_AUS
    try:
        return _CACHED_FRAME_AUS
    except NameError:
        _CACHED_FRAME_AUS = build_frame(P_AUS)
        return _CACHED_FRAME_AUS


def _segs_default():
    global _CACHED_SEGS_DEFAULT
    try:
        return _CACHED_SEGS_DEFAULT
    except NameError:
        _CACHED_SEGS_DEFAULT = build_segments(PRM.P)
        return _CACHED_SEGS_DEFAULT


def test_eckkammern_frame_valide_und_wasserdicht():
    s = _frame_default()
    assert s.isValid()
    assert len(s.Shells) == 1 and s.Shells[0].isClosed()


def test_eckkammern_volumendelta_plausibel():
    # Beim kompakten 50-mm-Band entfernen die Ecksektoren netto Material aus
    # den sonst massiven Eckblöcken: AUS minus EIN ist daher positiv.
    delta = _frame_aus().Volume - _frame_default().Volume
    assert 4.0e4 < delta < 5.5e4, \
        f"Eckkammer-Volumendelta {delta:.0f} mm³ unplausibel"


def test_eckkammern_segmente_valide_ueberschneidungsfrei():
    segs = _segs_default()
    assert len(segs) == 4
    for s in segs:
        assert s.isValid() and s.Volume > 1e5
    for i in range(4):
        for j in range(i + 1, 4):
            ov = segs[i].common(segs[j]).Volume
            assert ov < 1.0, f"Segmente {i}/{j} überschneiden sich: {ov:.3f} mm³"


def test_eckkammern_dfm_ueberhang():
    for i, s in enumerate(_segs_default()):
        bad, allowed = dfm.overhang_area(s, PRM.P)
        assert bad <= allowed * 1.2 + 200, \
            f"Segment {i}: {bad:.0f} mm² Überhang (erlaubt ~{allowed:.0f})"


def test_eckkammern_ohne_chambers_wirft_valueerror():
    try:
        PRM.validate(PRM.Params(CORNER_CHAMBERS=True, CHAMBERS=False))
        assert False, "erwartete ValueError"
    except ValueError:
        pass


def test_eckkammern_default_anker():
    """GEOM_REV-10-Anker des kompakten Hybridrahmens.

    Flache Raupenführungen und 16 Pads ersetzen die tiefen Rillen und 68
    Rundnoppen; der größere verbleibende Boden erklärt die Volumenzunahme.
    """
    v = _frame_default().Volume
    assert abs(v - 1673116.7934465515) < 1.0, \
        f"Default-Volumen (EIN) driftete: {v}"
    h_default = PRM.params_hash(PRM.P)
    h_alt_feld = PRM.params_hash(PRM.Params(CORNER_ANGLE_MARGIN=25.0))
    assert h_default != h_alt_feld


def test_eckkammern_ausschalt_anker():
    """GEOM_REV-10-AUS-Anker ohne Eckkammern."""
    v = _frame_aus().Volume
    assert abs(v - 1720654.8776221776) < 1.0, f"AUS-Volumen driftete: {v}"


def _side_cavities_only(p):
    """Isoliert NUR die geraden Zell-Kavitäten (ohne Vents, ohne Eck-
    Sektoren) -- identische Konstruktion wie frame._chamber_cuts, aber ohne
    die Vent-Bohrungen und ohne den Eck-Sektor-Anhang, damit sie gezielt
    gegen die Eck-Sektor-Kavitäten (frame._corner_chamber_cuts) auf
    Überschneidung geprüft werden können (siehe Test unten)."""
    bands = frame._ring_bands(p)
    apex_z = p.BOTTOM_T + math.tan(math.radians(p.CHEVRON_DEG)) * (p.CHAMBER_W / 2)
    neighbor_bounds = frame._side_neighbor_bounds(p)
    side_widths = PRM.side_top_widths(p)
    tools = []
    for k in range(4):
        plus_w, minus_w = neighbor_bounds[k]
        plus_half = frame._chamber_cell_centers(p, plus_w)
        minus_half = frame._chamber_cell_centers(p, minus_w)
        centers = plus_half + [-c for c in minus_half]
        for uc in centers:
            y0 = uc - p.CELL_L / 2
            for r_in, r_out in bands:
                cav = frame._chamber_cavity(r_in, r_out, apex_z, y0, p.CELL_L,
                                            p, side_widths[k])
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
        f"kollidierende dritte Zelle muss herausgefiltert sein)"

    straight = Part.makeCompound(_side_cavities_only(p))
    corner_count = 4 * p.CHAMBER_RING_COUNT
    corner_sectors = Part.makeCompound(
        frame._corner_chamber_cuts(p)[:corner_count])
    # Nur die Ring-Sektorsolids, ohne die danach folgenden Diagonal-Vents.
    overlap = straight.common(corner_sectors).Volume
    assert overlap < 1e-6, \
        f"Zellraster überschneidet Ecksektor: {overlap:.3f} mm³ (Regression!)"

    body = build_frame(p)
    assert body.isValid()
    assert len(body.Shells) == 1 and body.Shells[0].isClosed()


def test_eckkammern_delta_und_keepout_exakt():
    """Exaktes Eckkammer-Delta und Keepout (Review-Critical-Nachweis Task 17,
    Task 20 auf die gedrehte Semantik umgestellt -- vorher hieß der Test
    test_eckkammern_p_eck_volumen_exakt_unveraendert und verglich P_ECK
    gegen den damaligen AUS-Default): der Keepout-Filter greift bei
    Default-Parametern NICHT -- corner_keepout ist 196.22 mm (siehe
    frame._corner_keepout), die tatsächliche Reichweite der letzten Zelle
    bei Default-CELL_L=43 ist nur 193 mm, es wird also nichts gefiltert und
    das Zellraster bleibt bitidentisch zum Stand ohne Filter. Deshalb ist
    das GEOM_REV-9-Delta AUS-EIN exakt 47538.084176 mm³."""
    v_eck = _frame_default().Volume
    delta = _frame_aus().Volume - v_eck
    assert abs(delta - 47538.0841838331) < 1.0, \
        f"Delta driftete: {delta:.3f} mm³"
    keepout = frame._corner_keepout(PRM.P)
    assert abs(keepout - 196.223956) < 1e-3, f"corner_keepout driftete: {keepout}"


def test_eckkammern_werkzeugzahl_konsistent_zu_slot_count_cell_l_53(p=None):
    """Task-17-Re-Review Minor 2 (-> Task 16): explizite Konsistenzprüfung
    der GESAMTEN _chamber_cuts-Werkzeugliste gegen chamber_slot_count, INKL.
    der fixen Eck-Werkzeuge -- bisherige Tests prüften nur Volumen/Kollision,
    nicht die WerkzeugANZAHL selbst (die z. B. bei einer künftigen Änderung
    an der Vent-Zahl je Slot oder je Ecke still auseinanderdriften könnte,
    ohne dass Volumen-/Kollisionstests das zwingend auffangen).

    Je Slot entstehen pro Ring eine Kavität und ein Vent. Bei
    CORNER_CHAMBERS=True kommen pro Ring vier Sektor-Kavitäten und vier
    Diagonal-Vents hinzu, unabhängig von CELL_L/Slot-Zahl. Deshalb testet dieser Test
    explizit mit CELL_L=53 (Reviewer-Regressionsrezept, siehe
    test_eckkammern_kein_kollision_zellraster_ecksektor_cell_l_53 oben), wo
    der Keepout-Filter das Zellraster bereits sichtbar verändert (3 Zellen
    -> 2 Zellen je Halbseite an der REAR-Seite): die Formel muss auch dann
    exakt aufgehen, nicht nur bei unveränderten Defaults."""
    p = p or PRM.Params(CORNER_CHAMBERS=True, CELL_L=53.0)
    PRM.validate(p)
    tools = frame._chamber_cuts(p)
    slots = frame.chamber_slot_count(p)
    per_slot = 2 * p.CHAMBER_RING_COUNT
    corner = 8 * p.CHAMBER_RING_COUNT
    assert len(tools) == per_slot * slots + corner, (
        f"{len(tools)} Werkzeuge != {per_slot}*{slots} "
        f"(Slot-Kavitäten+Vents) + {corner} (Eck-Werkzeuge)"
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
    assert len(tools) == 2 * p.CHAMBER_RING_COUNT * slots
    assert frame._corner_chamber_cuts(p) == []
