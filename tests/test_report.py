from pathlib import Path

import params as PRM
from fem.report import write_report

FAKE_OK = {"vm_max_MPa": 1.0, "defl_max_mm": 0.1, "defl_top_mm": 0.05,
           "allowable_MPa": 8.4, "PASS": True}
FAKE_BAD = dict(FAKE_OK, vm_max_MPa=99.0, PASS=False)


def test_report_pass_mit_vorbehalt(tmp="out/test_report_ok.md"):
    # Defaults: EDGE_DIST/EDGE_H sind Schätzwerte -> Freigang OFFEN,
    # Gesamtergebnis "PASS mit Vorbehalt" (DA-Review 2026-07-12)
    ok = write_report({"LF1_wind": FAKE_OK}, FAKE_OK, PRM.P, tmp)
    assert ok is True
    text = Path(tmp).read_text()
    assert "PASS mit Vorbehalt" in text and PRM.params_hash() in text
    assert "OFFEN" in text and "Messkampagne 7" in text
    assert "140" in text                      # Wellenwahl im Report

def test_report_pass_gemessen(tmp="out/test_report_meas.md"):
    # Mit gemessener Kante (Überlapp real, Freigang reicht): echtes PASS
    p = PRM.Params(HOOD_TIP_REACH=300.0, EDGE_DIST=200.0, EDGE_H=40.0)
    # clearance = 28 + 30 - 40 = 18 >= 5
    ok = write_report({"LF1_wind": FAKE_OK}, FAKE_OK, p, tmp)
    assert ok is True
    text = Path(tmp).read_text()
    assert "18.0 mm" in text
    assert "Vorbehalt" not in text

def test_report_fail(tmp="out/test_report_bad.md"):
    ok = write_report({"LF1_wind": FAKE_BAD}, FAKE_OK, PRM.P, tmp)
    assert ok is False
    assert "FAIL" in Path(tmp).read_text()
