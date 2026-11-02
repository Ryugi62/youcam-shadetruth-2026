"""렌더 영역 판정: 원본과 렌더 결과의 차이로 바뀐 안쪽 픽셀만 잡는다."""
from __future__ import annotations

import numpy as np

from .color import rgb_to_lab

MIN_FRAC, MAX_FRAC = 0.001, 0.12
CHANGE_THRESHOLD = 40.0   # RGB 유클리드 거리(0~441)
ERODE_PX = 2
TRIM = (0.1, 0.9)         # 하이라이트·그림자 트림(명도 분위수)


class RegionError(Exception):
    pass


def _erode(mask: np.ndarray, n: int) -> np.ndarray:
    m = mask.copy()
    for _ in range(n):
        p = np.pad(m, 1, constant_values=False)
        m = (p[1:-1, 1:-1] & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    return m


def find_rendered_region(orig: np.ndarray, rend: np.ndarray) -> np.ndarray:
    if orig.shape != rend.shape:
        raise RegionError("원본과 렌더 결과의 크기가 다릅니다")
    diff = np.sqrt(((orig.astype(np.float32) - rend.astype(np.float32)) ** 2).sum(axis=2))
    raw = diff > CHANGE_THRESHOLD
    frac = raw.mean()
    if frac < MIN_FRAC:
        raise RegionError(f"바뀐 픽셀이 너무 적습니다({frac:.4%})")
    if frac > MAX_FRAC:
        raise RegionError(f"바뀐 픽셀이 너무 많습니다({frac:.2%}) — 입술 한 영역이 아님")
    mask = _erode(raw, ERODE_PX)
    if mask.sum() < 30:
        raise RegionError("가장자리를 걷어내고 남은 픽셀이 없습니다")
    return mask


def region_color_lab(rend: np.ndarray, mask: np.ndarray) -> tuple:
    px = rend[mask].astype(np.float64)
    labs = np.array([rgb_to_lab(*p) for p in px[:: max(1, len(px) // 4000)]])
    lo, hi = np.quantile(labs[:, 0], TRIM)
    keep = labs[(labs[:, 0] >= lo) & (labs[:, 0] <= hi)]
    if len(keep) == 0:
        keep = labs
    m = keep.mean(axis=0)
    return (float(m[0]), float(m[1]), float(m[2]))
