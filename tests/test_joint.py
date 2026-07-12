import params as PRM
from fem.joint_check import run_joint_submodel


def test_stoss_submodell():
    r = run_joint_submodel(PRM.P, PRM.wind_force())
    assert r["vm_max_MPa"] > 0.01
    assert r["PASS"], f"Stoß versagt: {r['vm_max_MPa']:.2f} > {r['allowable_MPa']:.2f} MPa"
