from dataclasses import FrozenInstanceError

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
    # 200 km/h, cd 1.2, A 0.108 (MaxxFan Deluxe offen, Maßblatt), SF 2
    assert abs(PRM.wind_force() - 480.0) < 1.0

def test_zulaessigkeiten():
    # Würth ASA GF15 Projektannahme: 45*0.5*0.5 = 11.25 kurz, *0.4 = 4.5 lang.
    lang, kurz = PRM.allowables()
    assert abs(lang - 4.50) < 0.01
    assert abs(kurz - 11.25) < 0.01

def test_wuerth_asa_gf15_planstand_abgebildet():
    p = PRM.P
    assert "Würth ASA GF15" in p.MATERIAL_NAME
    assert "4954641200" in p.MATERIAL_NAME
    assert p.RHO == 1100.0
    assert p.E_BASE == 3000.0 and p.SIGMA_BASE == 45.0
    assert p.HDT_045 == 99.0 and p.HDT_182 is None
    assert p.T_MAX < p.HDT_045


def test_universal_segment_schraubraster():
    p = PRM.P
    assert p.GEOM_REV == 6
    assert p.PLATE_KRAGEN_W == 397.0 and p.PLATE_KRAGEN_MEASURED
    assert p.BOT_KRAGEN_HOLE_OFFS == (-140.0, 140.0)
    assert p.PLATE_SCREW_OFFS == (-165.0, -140.0, 140.0, 165.0)
    assert p.PLATE_SCREW_BOSS_L == 25.0


def test_obere_schraubrippen_werden_ohne_unterkragen_validiert():
    kaputt = PRM.Params(BOT_KRAGEN=False, PLATE_SCREW_OFFS=(-165.0, -140.0, 140.0))
    try:
        PRM.validate(kaputt)
        assert False, "asymmetrische obere Schraubrippen wurden akzeptiert"
    except ValueError as exc:
        assert "PLATE_SCREW_OFFS" in str(exc)

def test_aussenmasse_und_hash():
    L, W = PRM.outer_dims()
    assert L == 500.0 and W == 500.0
    h1 = PRM.params_hash()
    h2 = PRM.params_hash(PRM.Params(H_RAISE=30.0))
    assert len(h1) == 8 and h1 != h2

def test_validate_defaults_ok():
    PRM.validate()                                    # Defaults müssen sauber sein

def test_validate_faengt_inkonsistente_messwertvarianten():
    for kaputt in (PRM.Params(W_TOP_FRONT=40.0, W_TOP_REAR=40.0,
                              W_TOP_LEFT=40.0, W_TOP_RIGHT=40.0),
                   PRM.Params(REC_GUSSET_D=6.0),
                   PRM.Params(VENT_Z=24.0),
                   PRM.Params(GLUE_GAP=1.0)):
        try:
            PRM.validate(kaputt)
            assert False, "erwartete ValueError"
        except ValueError:
            pass

def test_params_frozen():
    # Ledger 3: Params ist ein frozen dataclass -- Zuweisung nach der
    # Konstruktion muss verlässlich scheitern (verhindert stille
    # Parameter-Drift zur Laufzeit).
    p = PRM.Params()
    try:
        p.H_RAISE = 99.0
        assert False, "erwartete FrozenInstanceError"
    except FrozenInstanceError:
        pass
