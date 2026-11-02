"""검사 유스케이스. 포트(VtoPort)만 알고 HTTP·SDK는 모른다."""
from __future__ import annotations

import io
from dataclasses import dataclass, asdict
from typing import Optional, Protocol

import numpy as np
from PIL import Image

from ..domain.color import (Badge, badge_for, drift_hc, hex_to_lab, lab_to_hex, lightness_word)
from ..domain.region import RegionError, find_rendered_region, region_color_lab

AGREE_MAX = 4.0


class VtoPort(Protocol):
    def render_lip(self, photo: bytes, hex_color: str, finish: str = "matte") -> bytes: ...
    def read_lip_color(self, photo: bytes) -> str: ...


@dataclass
class CheckResult:
    target_hex: str
    badge: str
    measured_hex: Optional[str]
    drift_hc: Optional[float]
    dL_star: Optional[float]
    lightness: Optional[str]
    region_frac: Optional[float]
    api_read_hex: Optional[str]
    api_read_drift_hc: Optional[float]
    agree: Optional[bool]
    note: str = ""
    finish: str = "matte"

    def to_dict(self) -> dict:
        return asdict(self)


def _rgb(b: bytes) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(b)).convert("RGB"))


def run_check(port: VtoPort, photo: bytes, hex_color: str, finish: str = "matte") -> tuple:
    """(결과, 렌더 이미지 바이트). 영역을 못 잡으면 Unverifiable이고 숫자를 만들지 않는다."""
    target = hex_to_lab(hex_color)
    rendered = port.render_lip(photo, hex_color, finish)
    orig = _rgb(photo)
    rend = _rgb(rendered)
    if rend.shape != orig.shape:
        rend = np.asarray(Image.fromarray(rend).resize((orig.shape[1], orig.shape[0]), Image.LANCZOS))
    api_hex = port.read_lip_color(rendered)
    api_hc = drift_hc(target, hex_to_lab(api_hex))["hc"] if api_hex else None
    try:
        mask = find_rendered_region(orig, rend)
    except RegionError as e:
        return CheckResult(hex_color.upper(), badge_for(None).value, None, None, None, None, None,
                           api_hex, api_hc, None, note=str(e), finish=finish), rendered
    lab = region_color_lab(rend, mask)
    d = drift_hc(target, lab)
    agree = None if api_hc is None else abs(api_hc - d["hc"]) <= AGREE_MAX
    return CheckResult(hex_color.upper(), badge_for(d["hc"]).value, lab_to_hex(lab), round(d["hc"], 2),
                       round(d["dL_star"], 1), lightness_word(d["dL_star"]), round(float(mask.mean()), 4),
                       api_hex, None if api_hc is None else round(api_hc, 2), agree, finish=finish), rendered
