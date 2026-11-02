"""YouCam API 어댑터(표준 라이브러리만). 키는 호출자가 주입한다."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

BASE = "https://yce-api-01.makeupar.com"


def _redact(path: str) -> str:
    """폴링 경로의 task_id는 로그에서 가린다."""
    parts = path.split("/")
    if len(parts) >= 6 and parts[3] == "task":
        parts[5:] = ["<task_id>"]
    return "/".join(parts)


class YouCamError(Exception):
    pass


FINISHES = ("matte", "gloss")


def _palette(hex_color: str, finish: str) -> dict:
    if finish == "matte":
        return {"color": hex_color, "texture": "matte", "colorIntensity": 100}
    if finish == "gloss":
        return {"color": hex_color, "texture": "gloss", "colorIntensity": 100, "gloss": 60,
                "transparencyIntensity": 30}
    raise ValueError(f"지원하지 않는 마감: {finish}")


class YouCamClient:
    def __init__(self, api_key: str, base: str = BASE, poll_interval: float = 2.0, timeout: float = 120.0,
                 log=None):
        if not api_key:
            raise YouCamError("YOUCAM_API_KEY가 없습니다")
        self._key, self._base = api_key, base
        self._poll, self._timeout = poll_interval, timeout
        self.log = log if log is not None else []   # 호출 로그(키·URL 서명 제외)

    # --- 저수준 ---
    def _req(self, method: str, path: str, body=None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self._base + path, data=data, method=method, headers={
            "Authorization": f"Bearer {self._key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")[:400]
            self.log.append({"call": f"{method} {_redact(path)}", "http": e.code, "body": raw})
            raise YouCamError(f"{method} {path} -> HTTP {e.code}: {raw}") from None
        self.log.append({"call": f"{method} {_redact(path)}", "http": 200, "status": out.get("status")})
        return out

    def upload(self, data: bytes, content_type: str = "image/jpeg", name: str = "photo.jpg") -> str:
        out = self._req("POST", "/s2s/v2.0/file", {"files": [{"content_type": content_type, "file_name": name,
                                                              "file_size": len(data)}]})
        f = out["data"]["files"][0]
        rq = f["requests"][0]
        put = urllib.request.Request(rq["url"], data=data, method=rq.get("method", "PUT"),
                                     headers=rq.get("headers", {"Content-Type": content_type}))
        with urllib.request.urlopen(put, timeout=60) as r:
            if r.status >= 300:
                raise YouCamError(f"업로드 실패 HTTP {r.status}")
        self.log.append({"call": "PUT presigned", "http": 200, "bytes": len(data)})
        return f["file_id"]

    def run_task(self, task: str, body: dict) -> dict:
        start = self._req("POST", f"/s2s/v2.0/task/{task}", body)
        tid = start["data"]["task_id"]
        t0 = time.time()
        while time.time() - t0 < self._timeout:
            time.sleep(self._poll)
            st = self._req("GET", f"/s2s/v2.0/task/{task}/{tid}")["data"]
            s = st.get("task_status")
            if s == "success":
                return st
            if s == "error":
                raise YouCamError(f"{task} 실패: {st.get('error')} {st.get('error_message', '')}".strip())
        raise YouCamError(f"{task} 시간 초과")

    def credit(self) -> int:
        """남은 유닛 원문 응답(잔액 조회)."""
        return self._req("GET", "/s2s/v1.0/client/credit")

    @staticmethod
    def download(url: str) -> bytes:
        with urllib.request.urlopen(url, timeout=60) as r:
            return r.read()

    # --- 포트(VtoPort) 구현 ---
    def render_lip(self, photo: bytes, hex_color: str, finish: str = "matte") -> bytes:
        fid = self.upload(photo)
        st = self.run_task("makeup-vto", {
            "src_file_id": fid,
            "version": "1.0",
            "effects": [
                {"category": "skin_smooth", "skinSmoothStrength": 0, "skinSmoothColorIntensity": 0},
                {"category": "lip_color", "shape": {"name": "original"},
                 "palettes": [_palette(hex_color, finish)],
                 "style": {"type": "full"}},
            ],
        })
        res = st["results"]
        first = res if isinstance(res, dict) else res[0]
        return self.download(first.get("url") or first["download_url"])

    def read_lip_color(self, photo: bytes) -> str:
        fid = self.upload(photo)
        st = self.run_task("skin-tone-analysis", {"src_file_id": fid, "face_angle_strictness_level": "low"})
        return st["results"]["color"]["lip_color"]
