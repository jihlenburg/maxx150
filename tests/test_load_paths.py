import params as PRM
from analysis import load_paths as LP


def test_ringflaechen_stammen_aus_der_konstruktionsgeometrie():
    result = LP.assess(include_cfd=False)
    assert result["geometry"]["top_elastic_ring"]["area_mm2"] == 14016.0
    assert result["geometry"]["roof_elastic_ring"]["area_mm2"] == 43500.0
    # Nur eine der zwei 30-mm-Holz/GFK-Flächen wird angerechnet.
    assert result["geometry"]["wood_frame_one_face_only"]["area_mm2"] == 51600.0


def test_480_n_huelle_wird_nicht_durch_cfd_reduziert():
    result = LP.assess(include_cfd=False)
    cases = result["load_cases"]
    assert set(cases) == {
        "wind_envelope_480N", "road_uplift_lateral", "snow_compression"
    }
    assert cases["wind_envelope_480N"]["force_N"][0] == PRM.wind_force()


def test_wind_zeigt_getrennte_obere_schrauben_und_untere_klebung():
    result = LP.assess(include_cfd=False)
    wind = result["load_cases"]["wind_envelope_480N"]
    top = wind["belluna_to_adapter"]
    bottom = wind["adapter_to_roof"]
    assert not top["elastic_ring_bond_only"]["PASS"]
    assert top["eight_side_screws_full_case"]["PASS"]
    assert bottom["wide_elastic_ring_primary"]["PASS"]
    assert 0.57 < bottom["wide_elastic_ring_primary"]["normalized_interaction"] < 0.59
    assert bottom["roof_side_screws"] == "not_installed"
    assert wind["serial_load_path_PASS"]


def test_segmentstoss_und_thermik_bleiben_getrennte_nachweise():
    result = LP.assess(include_cfd=False)
    joint = result["segment_joint"]
    assert 0.54 < joint["rk1300_utilization"] < 0.56
    assert 0.30 < joint["m5_pair_bearing_utilization"] < 0.32
    assert 0.61 < joint["m5_one_remaining_utilization"] < 0.63
    assert joint["PASS"]
    assert 0.40 < result["thermal_movement"]["utilization"] < 0.42
    assert result["thermal_movement"]["PASS"]


def test_obere_beiliegende_schraube_ist_nur_abgeminderte_analogie():
    result = LP.assess(include_cfd=False)
    screw = result["capacities"]["asa_screw"]
    assert 170.0 < screw["project_capacity_per_screw_N"] < 180.0
    assert "keine Zulassung" in screw["warning"]


def test_systemstatus_benennt_die_erkenntnisgrenze():
    result = LP.assess(include_cfd=False)
    assert result["system_PASS"]
    assert result["status"] == "PASS_ASSUMPTION_BASED"
    assert "keine Zulassung" in result["claim_limit"]


def test_alle_acht_oberen_plattenschrauben_bleiben_erforderlich():
    result = LP.assess(include_cfd=False)
    sensitivity = result["fastener_sensitivity"]["top_group"]
    assert 0.82 < sensitivity["1_missing"]["best_utilization"] < 0.84
    assert 0.87 < sensitivity["1_missing"]["worst_utilization"] < 0.88
    assert not sensitivity["2_missing"]["all_configurations_PASS"]
    assert sensitivity["2_missing"]["worst_utilization"] > 1.0
