import params as PRM
from analysis import load_paths as LP


def test_ringflaechen_stammen_aus_der_konstruktionsgeometrie():
    result = LP.assess(include_cfd=False)
    assert result["geometry"]["elastic_ring"]["area_mm2"] == 14016.0
    # Nur eine der zwei 30-mm-Holz/GFK-Flächen wird angerechnet.
    assert result["geometry"]["wood_frame_one_face_only"]["area_mm2"] == 51600.0


def test_480_n_huelle_wird_nicht_durch_cfd_reduziert():
    result = LP.assess(include_cfd=False)
    cases = result["load_cases"]
    assert set(cases) == {
        "wind_envelope_480N", "road_uplift_lateral", "snow_compression"
    }
    assert cases["wind_envelope_480N"]["force_N"][0] == PRM.wind_force()


def test_wind_zeigt_warum_die_seitenschrauben_tragend_sind():
    result = LP.assess(include_cfd=False)
    wind = result["load_cases"]["wind_envelope_480N"]
    top = wind["belluna_to_adapter"]
    bottom = wind["adapter_to_wood"]
    assert not top["elastic_ring_bond_only"]["PASS"]
    assert not bottom["elastic_ring_bond_only"]["PASS"]
    assert top["eight_side_screws_full_case"]["PASS"]
    assert bottom["eight_side_screws_full_case"]["PASS"]
    assert 0.80 < bottom["eight_side_screws_full_case"]["utilization"] < 0.85
    assert wind["serial_load_path_PASS"]


def test_segmentstoss_und_thermik_bleiben_getrennte_nachweise():
    result = LP.assess(include_cfd=False)
    joint = result["segment_joint"]
    assert 0.75 < joint["rk1300_utilization"] < 0.80
    assert 0.60 < joint["m5_bearing_utilization"] < 0.65
    assert joint["PASS"]
    assert 0.37 < result["thermal_movement"]["utilization"] < 0.39
    assert result["thermal_movement"]["PASS"]


def test_beiliegende_dachschraube_ist_nur_abgeminderte_analogie():
    result = LP.assess(include_cfd=False)
    screw = result["capacities"]["roof_screw"]
    assert screw["assumed_embed_mm"] >= screw["minimum_embed_4d_mm"]
    assert 170.0 < screw["project_capacity_per_screw_N"] < 180.0
    assert "keine Zulassung" in screw["warning"]


def test_systemstatus_benennt_die_erkenntnisgrenze():
    result = LP.assess(include_cfd=False)
    assert result["system_PASS"]
    assert result["status"] == "PASS_ASSUMPTION_BASED"
    assert "keine Zulassung" in result["claim_limit"]


def test_alle_acht_dachschrauben_bleiben_erforderlich():
    result = LP.assess(include_cfd=False)
    sensitivity = result["fastener_sensitivity"]["bottom_group"]
    assert 0.91 < sensitivity["1_missing"]["best_utilization"] < 0.93
    assert 0.96 < sensitivity["1_missing"]["worst_utilization"] < 0.98
    assert not sensitivity["2_missing"]["all_configurations_PASS"]
    assert sensitivity["2_missing"]["best_utilization"] > 1.0
