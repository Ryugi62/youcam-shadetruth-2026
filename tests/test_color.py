import math
import pytest
from shadetruth.domain.color import hex_to_lab, ciede2000, drift_hc, badge_for, Badge

SHARMA = [
    ((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485), 2.0425),
    ((50.0, 3.1571, -77.2803), (50.0, 0.0, -82.7485), 2.8615),
    ((50.0, 2.8361, -74.0200), (50.0, 0.0, -82.7485), 3.4412),
    ((50.0, -1.3802, -84.2814), (50.0, 0.0, -82.7485), 1.0000),
    ((50.0, 0.0, 0.0), (50.0, -1.0, 2.0), 2.3669),
    ((50.0, 2.49, -0.001), (50.0, -2.49, 0.0009), 7.1792),
    ((50.0, 2.5, 0.0), (73.0, 25.0, -18.0), 27.1492),
    ((50.0, 2.5, 0.0), (61.0, -5.0, 29.0), 22.8977),
]


@pytest.mark.parametrize("lab1,lab2,expected", SHARMA)
def test_ciede2000_matches_sharma_pairs(lab1, lab2, expected):
    assert round(ciede2000(lab1, lab2)["total"], 4) == expected


def test_ciede2000_is_symmetric_in_total():
    a, b = (50.0, 2.5, 0.0), (73.0, 25.0, -18.0)
    assert math.isclose(ciede2000(a, b)["total"], ciede2000(b, a)["total"], abs_tol=1e-9)


def test_hex_to_lab_white_and_black():
    L, a, b = hex_to_lab("#FFFFFF")
    assert round(L, 1) == 100.0 and abs(a) < 0.01 and abs(b) < 0.01
    assert hex_to_lab("#000000")[0] == pytest.approx(0.0, abs=1e-6)


def test_hex_to_lab_accepts_no_hash_and_rejects_garbage():
    assert hex_to_lab("C2185B") == hex_to_lab("#c2185b")
    with pytest.raises(ValueError):
        hex_to_lab("#12345")
    with pytest.raises(ValueError):
        hex_to_lab("#GGGGGG")


def test_drift_hc_ignores_pure_lightness_change():
    target = hex_to_lab("#C2185B")
    L, a, b = target
    lighter = (L + 8.0, a, b)
    parts = drift_hc(target, lighter)
    assert parts["hc"] < 1.5          # 명도만 다르면 색상·채도 드리프트는 작다
    assert parts["dL_star"] == pytest.approx(8.0)


def test_drift_hc_grows_with_chroma_loss():
    target = hex_to_lab("#C2185B")
    L, a, b = target
    washed = (L, a * 0.5, b * 0.5)
    assert drift_hc(target, washed)["hc"] > 5.0


@pytest.mark.parametrize("hc,name", [(0.0, Badge.MATCHES), (5.0, Badge.MATCHES), (5.01, Badge.CLOSE),
                                     (10.0, Badge.CLOSE), (10.01, Badge.APPROX)])
def test_badge_boundaries_fixed_before_first_call(hc, name):
    assert badge_for(hc) is name


def test_badge_unverifiable_when_no_measure():
    assert badge_for(None) is Badge.UNVERIFIABLE
