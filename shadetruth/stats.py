"""drift.json에서 README·화면 숫자를 만든다(문서-실측 불일치 방지)."""
import statistics


def summarize(d: dict) -> dict:
    out = {"n": d["n"], "units": d["units_spent"], "by_finish": {}}
    for f in sorted({r.get("finish", "matte") for r in d["rows"]}):
        rows = [r for r in d["rows"] if r.get("finish", "matte") == f]
        hc = [r["drift_hc"] for r in rows if r.get("drift_hc") is not None]
        dl = [r["dL_star"] for r in rows if r.get("dL_star") is not None]
        badges = {}
        for r in rows:
            k = r["badge"].split(" ")[0]
            badges[k] = badges.get(k, 0) + 1
        out["by_finish"][f] = {
            "n": len(rows), "median_hc": round(statistics.median(hc), 2) if hc else None,
            "max_hc": max(hc) if hc else None, "median_dL": round(statistics.median(dl), 1) if dl else None,
            "agree": sum(1 for r in rows if r.get("agree") is True), "badges": badges}
    return out


def readme_block(d: dict) -> str:
    s = summarize(d)
    lines = [f"N = {s['n']} real renders, {s['units']:.0f} YouCam units spent.", "",
             "| finish | n | median hue+chroma drift (ΔE00) | max | median ΔL* | read-back agrees | badges |", "|---|---|---|---|---|---|---|"]
    for f, v in s["by_finish"].items():
        lines.append(f"| {f} | {v['n']} | {v['median_hc']} | {v['max_hc']} | {v['median_dL']} | {v['agree']}/{v['n']} | {v['badges']} |")
    return "\n".join(lines)
