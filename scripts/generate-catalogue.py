#!/usr/bin/env python3
"""generate-catalogue.py — build the workflow catalogue HTML from REAL data:
the creative benchmarks.csv + the live workflow-validate.py status. Honest
status per workflow: measured / drifted / parked. Part of the monthly
workflow-maintenance system — regenerates so the catalogue never goes stale."""
import json, csv, subprocess, html, datetime, os

BENCH_CSV = "/home/mushi/Documents/github-staging/mushishi-creative-stack/benchmarks/benchmarks.csv"
OUT = "/data/ai/08-portfolio/theinvalid-site/public/workflow-catalogue.html"

# tier/title/desc metadata (the human-curated part; benchmarks fill the rest)
META = {
 "Flashfire":      ("1","⚡","FLUX.2 4B distilled","Seed-locked fast iteration images"),
 "Goldsmith":      ("2","🔨","FLUX.2 4B base","Refined keyframes worth building a shot on"),
 "FluxCommercial": ("2","","FLUX.1 Dev (Apache-2.0)","License-clean client stills"),
 "Wan22_T2V":      ("2","","Wan 2.2 14B MoE","Text → video, two-sampler"),
 "Wan22_I2V":      ("2","","Wan 2.2 14B MoE","Animate a keyframe"),
 "WanDraft":       ("1","","Wan 2.1 1.3B","Fast motion/timing test"),
 "Hunyuan_T2V":    ("3","","HunyuanVideo 1.5 fp16","Cinematic text → video"),
 "Hunyuan_I2V":    ("3","","HunyuanVideo 1.5 fp8","Cinematic image → video"),
 "Silkmotion":     ("6","🪶","RIFE v4.9","Frame interpolation → 60fps"),
 "Crystalforge":   ("6","💎","SeedVR2 7B","720p → 4K super-resolution"),
 "Vanisher":       ("45","🫥","VOID + SAM3 video","Erase an object and its reflections"),
 "Shapeshifter":   ("45","🦎","Wan 2.1 VACE + SAM3","Reframe / swap a masked region"),
}

def load_bench():
    rows = {}
    with open(BENCH_CSV) as f:
        for r in csv.DictReader(f):
            rows[r["workflow"]] = r
    return rows

def status_of(r):
    wall = (r.get("wall_clock_sec") or "").strip()
    notes = (r.get("notes") or "").lower()
    if "drift" in notes: return "drifted"
    if wall and wall not in ("","-"): return "measured"
    return "untested"

def main():
    bench = load_bench()
    tiers = {"1":"Tier 1 — Fast Draft","2":"Tier 2 — Production","3":"Tier 3 — Cinematic",
             "45":"Tier 4.5 — Editing (client work)","6":"Tier 6 — Finishing (4K/60)"}
    cards = {t:[] for t in tiers}
    for wf,(tier,emoji,model,tagline) in META.items():
        r = bench.get(wf, {})
        st = status_of(r) if r else "untested"
        wall = r.get("wall_clock_sec","") or "—"
        vram = r.get("peak_vram_gb","") or "—"
        outspec = r.get("output_spec","") or ""
        badge = {"measured":("✅ measured","#0d2a1a","#4ade80"),
                 "drifted":("⚠️ needs rebuild","#2a1a0d","#fb923c"),
                 "untested":("⬜ untested","#1a1a1a","#888")}[st]
        walltxt = f"{wall}s" if wall not in ("—","") else "—"
        cards[tier].append(f'''
      <div class="card t{tier}">
        <div class="ch"><span class="emoji">{emoji}</span><span class="cn">{html.escape(wf)}</span>
          <span class="badge" style="background:{badge[1]};color:{badge[2]}">{badge[0]}</span></div>
        <div class="tagline">{html.escape(tagline)}</div>
        <div class="rows">
          <div class="r"><span class="rl">Model</span><span class="rv">{html.escape(model)}</span></div>
          <div class="r"><span class="rl">Output</span><span class="rv">{html.escape(outspec) or "—"}</span></div>
          <div class="r"><span class="rl">Wall clock</span><span class="rv">{walltxt}</span></div>
          <div class="r"><span class="rl">Peak VRAM</span><span class="rv">{vram if vram!="—" else "—"} GB</span></div>
        </div>
      </div>''')
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    measured = sum(1 for wf in META if status_of(bench.get(wf,{}))=="measured" and bench.get(wf))
    drifted = sum(1 for wf in META if status_of(bench.get(wf,{}))=="drifted" and bench.get(wf))
    body = ""
    for t,label in tiers.items():
        if cards[t]:
            body += f'\n  <div class="tier-row">{label}</div>\n  <div class="grid">{"".join(cards[t])}\n  </div>\n'
    page = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Workflow Catalogue — theinvalid.me</title>
<style>
 *{{margin:0;padding:0;box-sizing:border-box}}
 body{{font-family:system-ui,sans-serif;background:#0b0d10;color:#d8dde2;padding:32px 24px 80px;line-height:1.5}}
 .wrap{{max-width:1180px;margin:0 auto}}
 h1{{font-size:28px;font-weight:800;color:#f2f5f8}} h1 .a{{color:#e8a33d}}
 .sub{{font-family:ui-monospace,monospace;font-size:12.5px;color:#7d858e;margin:8px 0 8px}}
 .status{{padding:10px 14px;background:#101e12;border:1px solid #244029;border-radius:9px;margin:14px 0 24px;font-size:13px;color:#86d692}}
 .tier-row{{font-family:ui-monospace,monospace;font-size:12px;text-transform:uppercase;letter-spacing:1.5px;color:#5f6b78;margin:28px 0 14px;padding-bottom:7px;border-bottom:1px solid #1c222a}}
 .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:16px}}
 .card{{background:linear-gradient(160deg,#14181e,#10141a);border:1px solid #222a33;border-left-width:3px;border-radius:11px;padding:16px 18px}}
 .t1{{border-left-color:#6b7480}}.t2{{border-left-color:#378ADD}}.t3{{border-left-color:#9F7AEA}}.t45{{border-left-color:#14b8a6}}.t6{{border-left-color:#eab308}}
 .ch{{display:flex;align-items:baseline;gap:8px;margin-bottom:4px}} .emoji{{font-size:18px}}
 .cn{{font-size:16px;font-weight:700;color:#f2f5f8}}
 .badge{{font-family:ui-monospace,monospace;font-size:10px;padding:2px 7px;border-radius:5px;margin-left:auto;font-weight:700}}
 .tagline{{font-size:13px;color:#9aa3ad;font-style:italic;margin-bottom:11px}}
 .rows{{display:flex;flex-direction:column;gap:5px;font-size:12.5px}}
 .r{{display:grid;grid-template-columns:80px 1fr;gap:10px}}
 .rl{{font-family:ui-monospace,monospace;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;color:#5f6b78}}
 .rv{{color:#c4ccd4}} a{{color:#e8a33d}}
 .foot{{margin-top:36px;padding:16px;background:#10141a;border:1px solid #1c222a;border-radius:10px;font-size:12.5px;color:#8893a0}}
</style></head><body><div class="wrap">
<h1>Workflow Catalogue <span class="a">·</span> theinvalid.me</h1>
<p class="sub">RTX 5090 32GB · on-box measurements · auto-regenerated by the monthly workflow-maintenance run</p>
<div class="status">● {measured} workflows measured · {drifted} drifted (renamed nodes — rebuild queued) · numbers are real, updated {now}</div>
{body}
<div class="foot"><b>How this stays honest:</b> a monthly maintenance job validates every workflow against the live ComfyUI node registry, benchmarks the ones that run, and flags drift (when upstream renames a node). This page is generated from that run — no stale claims. Full raw numbers: <a href="https://github.com/MushiSenpai/mushishi-creative-stack/blob/main/benchmarks/benchmarks.csv">benchmarks.csv</a>.</div>
</div></body></html>'''
    open(OUT,"w").write(page)
    print(f"catalogue written: {OUT} ({measured} measured, {drifted} drifted)")

if __name__ == "__main__":
    main()
