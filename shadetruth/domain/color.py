"""색 수학과 배지 규칙. 외부 I/O를 모른다(도메인)."""
from __future__ import annotations

import math
from enum import Enum

_D65 = (95.047, 100.0, 108.883)

MATCHES_MAX = 5.0   # 판정선은 첫 API 호출 전(2026-10-17)에 고정한 값
CLOSE_MAX = 10.0


class Badge(str, Enum):
    MATCHES = "Matches brand digital shade"
    CLOSE = "Close to brand digital shade"
    APPROX = "Approximate preview"
    UNVERIFIABLE = "Unverifiable"


def _lin(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb_to_lab(r: float, g: float, b: float) -> tuple:
    rl, gl, bl = _lin(r), _lin(g), _lin(b)
    x = (0.4124564 * rl + 0.3575761 * gl + 0.1804375 * bl) * 100
    y = (0.2126729 * rl + 0.7151522 * gl + 0.0721750 * bl) * 100
    z = (0.0193339 * rl + 0.1191920 * gl + 0.9503041 * bl) * 100

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116

    fx, fy, fz = f(x / _D65[0]), f(y / _D65[1]), f(z / _D65[2])
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def hex_to_rgb(h: str) -> tuple:
    s = h.strip().lstrip("#")
    if len(s) != 6:
        raise ValueError(f"HEX는 #RRGGBB 형식이어야 합니다: {h!r}")
    try:
        return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    except ValueError as e:
        raise ValueError(f"HEX는 #RRGGBB 형식이어야 합니다: {h!r}") from e


def hex_to_lab(h: str) -> tuple:
    return rgb_to_lab(*hex_to_rgb(h))


def lab_to_hex(lab: tuple) -> str:
    L, a, b = lab
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200

    def finv(t: float) -> float:
        return t ** 3 if t ** 3 > 216 / 24389 else (116 * t - 16) / (24389 / 27)

    x, y, z = finv(fx) * _D65[0] / 100, finv(fy) * _D65[1] / 100, finv(fz) * _D65[2] / 100
    rl = 3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    gl = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    bl = 0.0556434 * x - 0.2040259 * y + 1.0572252 * z

    def gam(c: float) -> int:
        c = max(0.0, min(1.0, c))
        v = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
        return int(round(v * 255))

    return "#%02X%02X%02X" % (gam(rl), gam(gl), gam(bl))


def ciede2000(lab1: tuple, lab2: tuple) -> dict:
    """CIEDE2000(Sharma, Wu, Dalal 2005). 가중된 명도·채도·색상 항과 합계를 돌려준다."""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if (b1 or a1p) else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if (b2 or a2p) else 0.0
    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    else:
        d = h2p - h1p
        dhp = d - 360 if d > 180 else d + 360 if d < -180 else d
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2))
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    else:
        hbp = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30)) + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6)) - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dTheta = 30 * math.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lbp - 50) ** 2 / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * dTheta)) * Rc
    tL, tC, tH = dLp / Sl, dCp / Sc, dHp / Sh
    total = math.sqrt(tL ** 2 + tC ** 2 + tH ** 2 + Rt * tC * tH)
    return {"total": total, "dL": tL, "dC": tC, "dH": tH}


def drift_hc(target_lab: tuple, measured_lab: tuple) -> dict:
    """색상·채도 항만의 드리프트(hc)와 명도 차(dL_star = 측정 - 목표)를 따로 돌려준다."""
    p = ciede2000(target_lab, measured_lab)
    return {
        "hc": math.hypot(p["dC"], p["dH"]),
        "dL_star": measured_lab[0] - target_lab[0],
        "total": p["total"],
        "parts": {"dL": p["dL"], "dC": p["dC"], "dH": p["dH"]},
    }


def badge_for(hc) -> Badge:
    if hc is None:
        return Badge.UNVERIFIABLE
    if hc <= MATCHES_MAX:
        return Badge.MATCHES
    if hc <= CLOSE_MAX:
        return Badge.CLOSE
    return Badge.APPROX


def lightness_word(dL_star: float) -> str:
    if abs(dL_star) < 3:
        return "similar lightness"
    return "lighter than brand shade" if dL_star > 0 else "darker than brand shade"
