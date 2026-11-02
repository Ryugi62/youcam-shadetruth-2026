"""데모 영상 조립: 실제 앱 화면 캡처(Aside 브라우저) + 영어 자막 + 설명 카드. 음성·음악 없음."""
import glob, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

SRC = sys.argv[1]            # 캡처 폴더
OUT = os.path.abspath(sys.argv[2])
W, H, BAR = 1920, 1200, 150
FONT = "/System/Library/Fonts/Helvetica.ttc"
f_big, f_mid, f_cap = (ImageFont.truetype(FONT, s) for s in (84, 46, 44))
tmp = os.path.join(os.path.dirname(OUT), "_frames"); os.makedirs(tmp, exist_ok=True)
for f in glob.glob(tmp + "/*"): os.remove(f)
entries = []   # (png, seconds)
n = 0


def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]


def card(lines_big, lines_small, secs):
    global n
    im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im); y = 260
    for t in lines_big:
        for l in wrap(d, t, f_big, W - 240):
            d.text((120, y), l, font=f_big, fill=(25, 31, 40)); y += 104
    y += 36
    for t in lines_small:
        for l in wrap(d, t, f_mid, W - 240):
            d.text((120, y), l, font=f_mid, fill=(78, 89, 104)); y += 62
        y += 16
    p = f"{tmp}/{n:05d}.png"; im.save(p); n += 1; entries.append((p, secs))


def shot(path, cap, secs):
    global n
    im = Image.open(path).convert("RGB").resize((W, H - BAR), Image.LANCZOS)
    can = Image.new("RGB", (W, H), (25, 31, 40)); can.paste(im, (0, 0)); d = ImageDraw.Draw(can)
    lines = wrap(d, cap, f_cap, W - 120)[:2]
    y = H - BAR + (BAR - 52 * len(lines)) // 2
    for l in lines:
        d.text((60, y), l, font=f_cap, fill=(255, 255, 255)); y += 52
    p = f"{tmp}/{n:05d}.png"; can.save(p); n += 1; entries.append((p, secs))


def one(name): return sorted(glob.glob(f"{SRC}/*{name}.png"))[0]


card(["ShadeTruth"], ["Does the virtual try-on show the shade the brand actually sells?", "Built on the YouCam API for the Skin AI & eCommerce VTO Hackathon"], 5)
card(["The problem"], ["A shopper sees a lipstick shade on screen, right before buying.", "Nobody checks whether the rendered color is the brand's digital color.", "ShadeTruth measures that gap and shows a badge."], 8)
card(["YouCam APIs used"], ["1. File API: upload the photo", "2. AI Makeup VTO (lip_color): render the brand HEX on the lips, 1 unit", "3. AI Facial Color Tones Analyzer: independent read-back of the rendered lip color, 20 units", "API key stays on the server."], 9)
shot(one("top"), "ShadeTruth web app: real results from 24 YouCam renders are shown at the top.", 5)
shot(one("inputs"), "Pick a sample model photo and a brand shade (HEX). Here: Berry #C2185B, matte.", 5)
waits = sorted(glob.glob(f"{SRC}/*wait.png"))
capw = "Check shade: the server calls YouCam (upload, makeup-vto, skin-tone-analysis). Real time, no cuts."
for w in waits: shot(w, capw, 1 / 12)
shot(one("resultimg"), "Result: original photo and the YouCam try-on rendering.", 6)
shot(one("resultnum"), "Badge + hue/chroma drift (CIEDE2000) + lightness + YouCam's own read-back of the rendered color.", 9)
shot(one("table"), "Recorded runs: 12 matte + 12 gloss renders, 2 photos x 6 shades.", 8)
shot(one("table2"), "Hue and chroma stay close to the brand color; lips render about 4-5 L* darker (partly real shading).", 8)
shot(one("method"), "Honest limits: brand digital color is ground truth; 2 sample photos; badge cut-offs set before the first call.", 9)
card(["Try it"], ["github.com/Ryugi62/youcam-shadetruth-2026", "Recorded demo on GitHub Pages; run live with your own YouCam key (make run).", "Cosmetic use only. Sample model photos from YouCam's public docs."], 7)
with open(tmp + "/list.txt", "w") as fh:
    for p, s in entries: fh.write(f"file '{p}'\nduration {s:.4f}\n")
    fh.write(f"file '{entries[-1][0]}'\n")
subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", tmp + "/list.txt",
                       "-vf", "fps=24,format=yuv420p", "-c:v", "libx264", "-crf", "20", "-movflags", "+faststart", OUT])
print("total seconds", sum(s for _, s in entries))
