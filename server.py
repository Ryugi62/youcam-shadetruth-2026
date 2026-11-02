"""ShadeTruth 서버: 정적 파일 + /api/check. API 키는 서버 프로세스에만 있다."""
import base64, io, json, os, sys, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from PIL import Image

from shadetruth.adapters.youcam import FINISHES, YouCamClient, YouCamError
from shadetruth.application.check import run_check
from shadetruth.domain.color import hex_to_rgb
from shadetruth.keys import load_key

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
BUDGET = int(os.environ.get("CHECK_BUDGET", "20"))   # 검사 1회 = 21유닛, 폭주 방지용 상한
_used = 0
_lock = threading.Lock()
CLIENT = None


def prepare_photo(raw: bytes) -> bytes:
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    im.thumbnail((1800, 1800))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=92)
    return b.getvalue()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/health":
            return self._json(200, {"live": CLIENT is not None, "budget_left": max(0, BUDGET - _used)})
        return super().do_GET()

    def do_POST(self):
        global _used
        if self.path != "/api/check":
            return self._json(404, {"error": "not found"})
        if CLIENT is None:
            return self._json(503, {"error": "서버에 YOUCAM_API_KEY가 없습니다(기록된 실행만 볼 수 있음)"})
        n = int(self.headers.get("Content-Length", "0"))
        if n <= 0 or n > 12_000_000:
            return self._json(400, {"error": "사진은 12MB 이하여야 합니다"})
        try:
            req = json.loads(self.rfile.read(n))
            hex_color = req["hex"]
            hex_to_rgb(hex_color)
            finish = req.get("finish", "matte")
            if finish not in FINISHES:
                raise ValueError(f"finish는 {FINISHES} 중 하나")
            photo = prepare_photo(base64.b64decode(req["photo_b64"]))
        except Exception as e:
            return self._json(400, {"error": f"입력 오류: {e}"})
        with _lock:
            if _used >= BUDGET:
                return self._json(429, {"error": "이 서버의 검사 한도에 도달했습니다"})
            _used += 1
        try:
            res, rendered = run_check(CLIENT, photo, hex_color, finish)
        except YouCamError as e:
            return self._json(502, {"error": str(e)[:400]})
        im = Image.open(io.BytesIO(rendered)).convert("RGB")
        im.thumbnail((720, 960))
        b = io.BytesIO()
        im.save(b, "JPEG", quality=88)
        d = res.to_dict()
        d["render_b64"] = base64.b64encode(b.getvalue()).decode()
        return self._json(200, d)   # 사진은 메모리에서만 쓰고 저장하지 않는다

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    global CLIENT
    key = load_key()
    CLIENT = YouCamClient(key) if key else None
    port = int(os.environ.get("PORT", "8765"))
    print(f"ShadeTruth http://127.0.0.1:{port}  live={'on' if CLIENT else 'off(기록만)'}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
