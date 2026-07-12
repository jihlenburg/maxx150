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
    assert abs(PRM.wind_force() - 444.4) < 1.0   # 200 km/h, cd 1.2, A 0.1, SF 2

def test_zulaessigkeiten():
    lang, kurz = PRM.allowables()
    assert abs(lang - 3.36) < 0.01               # 40*0.35*0.6*0.4
    assert abs(kurz - 8.40) < 0.01               # 40*0.35*0.6

def test_aussenmasse_und_hash():
    L, W = PRM.outer_dims()
    assert L == 500.0 and W == 500.0
    h1 = PRM.params_hash()
    h2 = PRM.params_hash(PRM.Params(H_RAISE=30.0))
    assert len(h1) == 8 and h1 != h2
