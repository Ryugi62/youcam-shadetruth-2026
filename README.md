# ShadeTruth

**Does the virtual try-on show the shade the brand actually sells?** ShadeTruth sends a brand's digital lip color (HEX) to YouCam's makeup try-on, then *measures* how far the rendered lips drift from that color (CIEDE2000) and shows a badge — `Matches`, `Close`, or `Approximate preview` — before the shopper buys.

- Track: **eCommerce VTO** (right before a purchase: "is this the shade I'm about to buy?") with a Skin AI color read-back.
- Demo (recorded real API runs, no install): GitHub Pages link in the Devpost submission · Live run: `make run` (needs your own `YOUCAM_API_KEY`).
- Cosmetic use only — no skin diagnosis, no medical claims.

## Result (generated from `data/drift.json`; checked by `tests/test_stats.py`)
<!-- STATS -->
N = 24 real renders, 504 YouCam units spent.

| finish | n | median hue+chroma drift (ΔE00) | max | median ΔL* | read-back agrees | badges |
|---|---|---|---|---|---|---|
| gloss | 12 | 2.38 | 3.98 | -4.3 | 12/12 | {'Matches': 12} |
| matte | 12 | 2.5 | 3.96 | -5.2 | 12/12 | {'Matches': 12} |
<!-- /STATS -->

What this says, in one breath: YouCam's matte lip render keeps hue and chroma close to the HEX we send, but renders consistently darker than the brand digital shade (see median ΔL*). A shop that only looks at the picture never sees that; ShadeTruth reports it as a number. Sample is small (2 sample model photos × 6 shades × 2 finishes) — it is a measurement of this setup, not of YouCam in general.

## YouCam APIs used (server-side only)
| API | Endpoint | Units/call | Role |
|---|---|---|---|
| File API | `POST /s2s/v2.0/file` + pre-signed PUT | 0 | upload photo and rendered result |
| AI Makeup VTO (`lip_color`, `skin_smooth` 0) | `POST/GET /s2s/v2.0/task/makeup-vto` | 1 | render the brand HEX on the lips |
| AI Facial Color Tones Analyzer | `POST/GET /s2s/v2.0/task/skin-tone-analysis` | 20 | independent read-back of the rendered `lip_color` |

One shade check = 21 units. The recorded table spent exactly 21 × N units (balance read before/after via `GET /s2s/v1.0/client/credit`). Call flow: upload → create task → poll until `success` → use result (`shadetruth/adapters/youcam.py`). The API key lives only in the server environment; it never reaches the browser, the repo, or the video (`scripts/check_no_secret.sh`).

## How it is measured
- **Ground truth** = the HEX sent to the API (brand digital shade). Not the physical bottle, not your monitor.
- **Rendered region** = pixels that changed vs. the original (RGB distance > 40), eroded 2 px to drop the feathered edge, lightness trimmed to the 10–90% quantile. A heuristic, not an API mask. If the changed area is <0.1% or >12% of the image the badge is `Unverifiable` and **no number is invented**.
- **Drift** = CIEDE2000 hue and chroma terms only, `sqrt((ΔC'/S_C)² + (ΔH'/S_H)²)`; **ΔL\*** is reported separately as lighter/darker because matte shading and lighting legitimately move it. CIEDE2000 is verified against Sharma, Wu & Dalal (2005) test pairs in `tests/test_color.py`.
- **Badge cut-offs** (≤5 / ≤10) were fixed on 2026-10-17, before the first API call (see `SPEC.md`). They are our choice, not a standard.
- **Read-back** = YouCam's own Face Tone Analyzer reading of the rendered image; "agrees" when within 4 ΔE of our measurement.

## Honest limits
Two vendor-supplied sample model photos (from YouCam's public docs; no real customers, no user faces stored). Matte and one gloss setting only. Lighting/monitor/physical-product differences are out of scope. Gloss drift includes the finish's intended highlights.

## Why not just trust the try-on? (similar work)
| Project / product | What it does | What ShadeTruth adds |
|---|---|---|
| ShadeSpan (YouCam hackathon #1 round 2nd place, https://youcam-api.devpost.com/project-gallery) | grades a catalog against 6 skin tones | we grade the *rendered color vs brand HEX*, per shade |
| Aloud (round 1 winner, same gallery) | voice skin advice, claims limited to scores | different problem (accessibility) |
| CASTING (same gallery) | product → measured skin tones, coverage score | tone of the person, not accuracy of the render |
| YouCam consumer app / enterprise VTO (https://www.perfectcorp.com/business) | the try-on renderer itself | an outside check on its output |
| Sephora Virtual Artist color match (https://www.marketingdive.com/news/sephoras-virtual-artist-app-now-includes-ai-powered-color-matching/444484/) | photo → similar product | no published render-vs-HEX error that we could find |
| L'Oréal ModiFace (https://d3.harvard.edu/platform-rctom/submission/mirror-mirror-on-the-wall-loreals-modiface-uses-ai-to-find-your-perfect-shade-match/) | skin-tone detection (vendor-reported 98.3%) | detection accuracy ≠ render accuracy |
Our search was limited (web search, vendor blogs, the hackathon gallery); "could not find" is not proof of absence.

## Run it
```
pip install -r requirements.txt
cp .env.example .env   # put your YOUCAM_API_KEY (free 1,000-unit redeem code from the hackathon)
make test              # unit tests, no network
make run               # http://127.0.0.1:8765 — live checks (21 units each, capped by CHECK_BUDGET)
make drift             # re-run the recorded table (252 units per finish)
```
Without a key the page still opens and shows the recorded real runs.

## Layout (Clean Architecture)
`shadetruth/domain` (color math, badge rules, region finding — no I/O) ← `application` (check use case, port) ← `adapters` (YouCam HTTP) ← `server.py`. Spec: `SPEC.md`.

## Hackathon note
Newly built during the submission period (first commit 2026-11-02). Third-party: YouCam API (authorized via the hackathon redeem code), Pillow, NumPy. License: MIT.
