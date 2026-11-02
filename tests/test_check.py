import io
import numpy as np
from PIL import Image
from shadetruth.application.check import run_check


def _png(arr):
    b = io.BytesIO()
    Image.fromarray(arr).save(b, "PNG")
    return b.getvalue()


class FakePort:
    def __init__(self, paint=(194, 24, 91), read="#C2185B"):
        self.paint, self.read = paint, read

    def render_lip(self, photo, hex_color, finish="matte"):
        a = np.asarray(Image.open(io.BytesIO(photo)).convert("RGB")).copy()
        if self.paint:
            a[90:110, 80:120] = self.paint
        return _png(a)

    def read_lip_color(self, photo):
        return self.read


PHOTO = _png(np.full((200, 200, 3), 200, np.uint8))


def test_exact_render_gets_matches_badge_and_agree():
    res, rendered = run_check(FakePort(), PHOTO, "#C2185B")
    assert res.badge == "Matches brand digital shade"
    assert res.drift_hc < 1 and res.agree is True and rendered


def test_washed_out_render_drifts():
    res, _ = run_check(FakePort(paint=(215, 120, 150), read="#D77896"), PHOTO, "#C2185B")
    assert res.badge in ("Close to brand digital shade", "Approximate preview")
    assert res.drift_hc > 5


def test_no_change_is_unverifiable_without_invented_numbers():
    res, _ = run_check(FakePort(paint=None), PHOTO, "#C2185B")
    assert res.badge == "Unverifiable"
    assert res.drift_hc is None and res.measured_hex is None and res.note


def test_finish_is_passed_through_and_reported():
    seen = []

    class P(FakePort):
        def render_lip(self, photo, hex_color, finish="matte"):
            seen.append(finish)
            return super().render_lip(photo, hex_color, finish)

    res, _ = run_check(P(), PHOTO, "#C2185B", finish="gloss")
    assert seen == ["gloss"] and res.finish == "gloss"
