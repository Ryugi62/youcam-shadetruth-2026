import numpy as np
from shadetruth.domain.region import find_rendered_region, region_color_lab, RegionError
import pytest


def _scene(h=200, w=200):
    base = np.full((h, w, 3), 200, dtype=np.uint8)
    return base


def test_region_found_for_painted_patch_and_mean_lab_matches():
    orig = _scene()
    rend = orig.copy()
    rend[90:110, 80:120] = (194, 24, 91)   # 입술 대역: 면적 800/40000 = 2%
    mask = find_rendered_region(orig, rend)
    assert 0.005 < mask.mean() < 0.03
    lab = region_color_lab(rend, mask)
    from shadetruth.domain.color import hex_to_lab
    target = hex_to_lab("#C2185B")
    assert abs(lab[0] - target[0]) < 1.0 and abs(lab[1] - target[1]) < 1.0


def test_identical_images_unverifiable():
    orig = _scene()
    with pytest.raises(RegionError):
        find_rendered_region(orig, orig.copy())


def test_huge_change_unverifiable():
    orig = _scene()
    rend = orig.copy()
    rend[:, :] = (10, 10, 10)
    with pytest.raises(RegionError):
        find_rendered_region(orig, rend)


def test_edge_feather_pixels_are_excluded():
    orig = _scene()
    rend = orig.copy()
    rend[90:110, 80:120] = (194, 24, 91)
    rend[88:90, 80:120] = (197, 112, 145)   # 번진 가장자리
    rend[110:112, 80:120] = (197, 112, 145)
    mask = find_rendered_region(orig, rend)
    assert not mask[88:90].any() and not mask[110:112].any()
