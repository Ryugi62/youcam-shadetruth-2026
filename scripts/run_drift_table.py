"""실호출 드리프트 표 생성: 사진 N장 × 색 M개 → data/drift.json + web/results/*.jpg.
사용: YOUCAM_API_KEY=... python3 scripts/run_drift_table.py"""
import io, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from shadetruth.adapters.youcam import YouCamClient
from shadetruth.application.check import run_check
from shadetruth.keys import load_key

SHADES = [("Berry", "#C2185B"), ("Coral", "#E8685A"), ("Nude Rose", "#C48B7B"),
          ("Classic Red", "#C8102E"), ("Plum", "#7B2D5B"), ("Soft Pink", "#D4688A")]
PHOTOS = [("face-a", "samples/face-a.jpg"), ("face-b", "samples/face-b.jpg")]


def credit_total(c):
    return sum(x.get("amount_dec", x.get("amount", 0)) for x in c.credit()["results"])


def main():
    finish = sys.argv[1] if len(sys.argv) > 1 else "matte"
    c = YouCamClient(load_key())
    before = credit_total(c)
    rows, t0 = [], time.time()
    for pid, path in PHOTOS:
        photo = open(path, "rb").read()
        for name, hx in SHADES:
            r0 = time.time()
            try:
                res, rend = run_check(c, photo, hx, finish)
                d = res.to_dict()
                im = Image.open(io.BytesIO(rend)).convert("RGB"); im.thumbnail((540, 720))
                fn = f"web/results/{pid}-{hx[1:].lower()}-{finish}.jpg"
                im.save(fn, quality=88)
                d["image"] = fn[4:]
            except Exception as e:  # 실패도 행으로 남긴다
                d = {"target_hex": hx, "badge": "Unverifiable", "note": f"API 오류: {e}"[:300]}
            d.update(photo=pid, shade=name, finish=finish, seconds=round(time.time() - r0, 1))
            rows.append(d)
            print(pid, name, d.get("badge"), d.get("drift_hc"), flush=True)
    after = credit_total(c)
    prev = json.load(open("data/drift.json")) if os.path.exists("data/drift.json") else None
    if prev:
        for r in prev["rows"]:
            r.setdefault("finish", "matte")
        rows = [r for r in prev["rows"] if r["finish"] != finish] + rows
        spent_prev = prev["units_spent"] if finish != "matte" else 0
    else:
        spent_prev = 0
    out = {"generated": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "n": len(rows), "units_before": before,
           "units_after": after, "units_spent": (before - after) + spent_prev,
           "settings": {"skin_smooth": 0, "colorIntensity": 100, "shape": "original", "finishes": {"matte": "matte", "gloss": "gloss 60, transparency 30"}},
           "photos": {pid: "YouCam API 문서의 공개 샘플 이미지(합성·모델 사진, 사용자 얼굴 아님)" for pid, _ in PHOTOS},
           "rows": rows}
    json.dump(out, open("data/drift.json", "w"), ensure_ascii=False, indent=1)
    for pid, path in PHOTOS:
        im = Image.open(path).convert("RGB"); im.thumbnail((540, 720)); im.save(f"web/results/{pid}-original.jpg", quality=88)
    print("units spent", before - after, "rows", len(rows))


main()
