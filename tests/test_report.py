from pathlib import Path

import params as PRM
from fem.report import write_report

FAKE_OK = {"vm_max_MPa": 1.0, "defl_max_mm": 0.1, "defl_top_mm": 0.05,
           "allowable_MPa": 8.4, "PASS": True, "defl_top_is_fallback": False}
FAKE_BAD = dict(FAKE_OK, vm_max_MPa=99.0, PASS=False)
FAKE_FALLBACK = dict(FAKE_OK, defl_top_is_fallback=True)


def test_report_pass_mit_vorbehalt(tmp="out/test_report_ok.md"):
    # Defaults: EDGE_DIST/EDGE_H sind Schätzwerte -> Freigang OFFEN,
    # Gesamtergebnis "PASS mit Vorbehalt" (DA-Review 2026-07-12)
    ok, vorbehalt = write_report({"LF1_wind": FAKE_OK}, FAKE_OK, PRM.P, tmp)
    assert ok is True
    assert vorbehalt is True
    text = Path(tmp).read_text(encoding="utf-8")
    assert "PASS mit Vorbehalt" in text and PRM.params_hash() in text
    assert "OFFEN" in text and "Messkampagne 7" in text
    assert "140" in text                      # Wellenwahl im Report

def test_report_pass_gemessen(tmp="out/test_report_meas.md"):
    # Mit gemessener Kante (Überlapp real, Freigang reicht): echtes PASS
    p = PRM.Params(HOOD_TIP_REACH=300.0, EDGE_DIST=200.0, EDGE_H=40.0)
    # clearance = 28 + 30 - 40 = 18 >= 5
    ok, vorbehalt = write_report({"LF1_wind": FAKE_OK}, FAKE_OK, p, tmp)
    assert ok is True
    assert vorbehalt is False
    text = Path(tmp).read_text(encoding="utf-8")
    assert "18.0 mm" in text
    assert "Vorbehalt" not in text

def test_report_fail(tmp="out/test_report_bad.md"):
    ok, vorbehalt = write_report({"LF1_wind": FAKE_BAD}, FAKE_OK, PRM.P, tmp)
    assert ok is False
    # Default-EDGE_* bleiben Schätzwerte -> vorbehalt unabhängig vom FEM-FAIL
    # weiterhin True; das Gesamtergebnis-Banner zeigt trotzdem FAIL (ok
    # sticht vorbehalt, siehe write_report-Bannerlogik).
    assert vorbehalt is True
    assert "FAIL" in Path(tmp).read_text(encoding="utf-8")

def test_report_leere_fem_results_wirft_valueerror():
    # M7: leeres fem_results ist ein Aufrufer-Fehler (kein Lastfall) --
    # ValueError statt eines stillen/irreführenden Reports.
    try:
        write_report({}, FAKE_OK, PRM.P, "out/test_report_empty.md")
        assert False, "erwartete ValueError"
    except ValueError as e:
        assert "kein Lastfall" in str(e)

def test_report_defl_top_fallback_annotation(tmp="out/test_report_fallback.md"):
    # fem/run_fem.py::run_case liefert defl_top_is_fallback=True, wenn keine
    # echten Deckflächen-Knoten gefunden wurden (Submodell-Fall, M3/Ledger
    # 32) -- der Report muss das sichtbar machen statt den defl_max-
    # Ersatzwert unkommentiert als Deckflächenverformung auszugeben.
    write_report({"LF1_wind": FAKE_FALLBACK}, FAKE_OK, PRM.P, tmp)
    text = Path(tmp).read_text(encoding="utf-8")
    assert "(Fallback)" in text
