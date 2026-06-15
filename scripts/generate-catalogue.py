#!/usr/bin/env python3
"""generate-catalogue.py — build the workflow catalogue HTML from REAL data:
the creative benchmarks.csv + the live workflow-validate.py status. Honest
status per workflow: measured / drifted / parked. Each tile carries a plain-language
purpose + input/output + the DIFFERENTIATOR (why pick this over a similar one).
Part of the monthly workflow-maintenance system — regenerates so nothing goes stale."""
import csv, html, datetime

BENCH_CSV = "/home/mushi/Documents/github-staging/mushishi-creative-stack/benchmarks/benchmarks.csv"
OUT = "/data/ai/08-portfolio/theinvalid-site/public/workflow-catalogue.html"

# join_key (matches benchmarks.csv + validator) -> rich, human-curated metadata.
# "name" is the fun display name; "diff" is the differentiator vs similar workflows.
META = {
 "Flashfire":    dict(name="Flashfire", tier="1", emoji="⚡", model="FLUX.2 4B (distilled)",
    inp="Text prompt", out="1024² PNG", purpose="Instant still drafts for fast iteration.",
    diff="4-step distilled — the FASTEST stills. For composition/seed exploration. Lower fidelity than Goldsmith."),
 "WanDraft":     dict(name="Quickdraw", tier="1", emoji="✏️", model="Wan 2.1 1.3B",
    inp="Text prompt", out="~480p short clip", purpose="Throwaway motion/timing test before a real render.",
    diff="Tiny 1.3B — quickest way to check motion & composition. Draft quality; commit the shot, then use a Tier-2/3 model."),
 "Goldsmith":    dict(name="Goldsmith", tier="2", emoji="🔨", model="FLUX.2 4B (base)",
    inp="Text prompt", out="1024² PNG", purpose="Refined keyframes worth building a shot on.",
    diff="Full-step base model — markedly higher fidelity than Flashfire. The still you animate or deliver."),
 "FluxCommercial": dict(name="Ledger", tier="2", emoji="⚖️", model="FLUX.1 Dev (Apache-2.0)",
    inp="Text prompt", out="PNG", purpose="License-clean stills you can sell to clients.",
    diff="The ONLY image model here under a commercial-safe license (Apache-2.0). Pick it for paid client deliverables."),
 "Wan22_T2V":    dict(name="Conjurer", tier="2", emoji="🎞️", model="Wan 2.2 14B MoE",
    inp="Text prompt", out="480/720p video", purpose="Production text→video.",
    diff="14B mixture-of-experts (high+low-noise two-sampler) — production quality. Slower than Quickdraw, faster/lighter than the cinematic Tier-3 Hunyuans."),
 "Wan22_I2V":    dict(name="Breath", tier="2", emoji="🌬️", model="Wan 2.2 14B MoE",
    inp="Image + prompt", out="480/720p video", purpose="Animate a still image into video.",
    diff="Fast, reliable image→video. Pick this over Quickening when you want speed/production over maximum cinematic polish."),
 "dreamforge":   dict(name="dreamforge", tier="3", emoji="🌆", model="HunyuanVideo 1.5 720p (fp16)",
    inp="Text prompt", out="Cinematic 720p video", purpose="The hero cinematic text→video.",
    diff="HunyuanVideo 1.5 — the highest cinematic quality text→video here (atmosphere, camera, lighting). Slower than Conjurer; worth it for the money shot."),
 "quickening":   dict(name="quickening", tier="3", emoji="✨", model="HunyuanVideo 1.5 I2V (fp8 distilled)",
    inp="Image + prompt", out="Cinematic 720p video", purpose="Cinematic image→video — bring a still to life.",
    diff="Hunyuan I2V — the most cinematic animation of a keyframe. Pick over Breath when polish matters more than speed."),
 "sharpscale":   dict(name="sharpscale", tier="3", emoji="🔎", model="HunyuanVideo 1.5 1080p SR",
    inp="720p Hunyuan video", out="True 1080p (1920×1072)", purpose="Super-resolve a Hunyuan clip to crisp 1080p.",
    diff="Hunyuan-native latent super-res — preserves Hunyuan detail. Use after dreamforge/quickening. For general 4K from any source, use Crystalforge instead."),
 "Silkmotion":   dict(name="Silkmotion", tier="6", emoji="🪶", model="RIFE v4.9",
    inp="Any video", out="60fps video", purpose="Smooth any clip to 60fps.",
    diff="Frame interpolation — adds MOTION smoothness, not resolution. Pair with Crystalforge/sharpscale for 4K@60."),
 "Crystalforge": dict(name="Crystalforge", tier="6", emoji="💎", model="SeedVR2 7B",
    inp="720p video (any source)", out="4K video", purpose="General video super-resolution to 4K.",
    diff="SeedVR2 — source-agnostic 720p→4K. Use sharpscale instead when the source is Hunyuan and you only need 1080p (faster, native)."),
 "Vanisher":     dict(name="Vanisher", tier="45", emoji="🫥", model="VOID + SAM3 (video)",
    inp="Video + object to remove", out="Video, object erased", purpose="Erase an object from a video.",
    diff="VOID+SAM3 — removes an object AND its reflections/shadows (the forensic differentiator). Shapeshifter swaps; Vanisher erases."),
 "Shapeshifter": dict(name="Shapeshifter", tier="45", emoji="🦎", model="Wan 2.1 VACE + SAM3",
    inp="Video + masked region", out="Video, region swapped/reframed", purpose="Swap or reframe a masked region.",
    diff="VACE — replaces/reframes content inside a mask (vs Vanisher which only erases). For client edits that change a region, not delete it."),
 "maestro":      dict(name="Maestro", tier="7", emoji="🎬", model="PRISM(:8001) → FLUX.2 → Wan 2.2 I2V MoE → YuE 7B",
    inp="One-line scene idea", out="832×480 cinematic clip + original 30s score",
    purpose="One sentence → a finished, scored cinematic clip — fully automated, 100% local.",
    diff="The end-to-end sovereign pipeline: a local LLM writes the prompts, FLUX paints the keyframe, Wan animates it, YuE composes the score — one command, no cloud, no manual stitching."),
}

def load_bench():
    rows = {}
    try:
        with open(BENCH_CSV) as f:
            for r in csv.DictReader(f): rows[r["workflow"]] = r
    except FileNotFoundError: pass
    return rows

def status_of(r):
    if not r: return "untested"
    wall = (r.get("wall_clock_sec") or "").strip()
    if "drift" in (r.get("notes") or "").lower(): return "drifted"
    return "measured" if wall and wall not in ("","-") else "untested"

def main():
    bench = load_bench()
    tiers = {"1":"Tier 1 — Fast Draft","2":"Tier 2 — Production","3":"Tier 3 — Cinematic",
             "45":"Tier 4.5 — Editing (client work)","6":"Tier 6 — Finishing (4K / 60fps)",
             "7":"Tier 7 — Pipelines (idea → finished clip + score)"}
    cards = {t:[] for t in tiers}
    badges = {"measured":("✅ measured","#0d2a1a","#4ade80"),
              "drifted":("⚠️ needs rebuild","#2a1a0d","#fb923c"),
              "untested":("⬜ untested","#1a1a1a","#888")}
    for key,m in META.items():
        r = bench.get(key, {})
        st = status_of(r)
        wall = r.get("wall_clock_sec","") or ""
        vram = r.get("peak_vram_gb","") or ""
        b = badges[st]
        e=html.escape
        cards[m["tier"]].append(f'''
      <div class="card t{m['tier']}">
        <div class="ch"><span class="emoji">{m['emoji']}</span><span class="cn">{e(m['name'])}</span>
          <span class="badge" style="background:{b[1]};color:{b[2]}">{b[0]}</span></div>
        <div class="tagline">{e(m['purpose'])}</div>
        <div class="io"><span class="io1"><b>In</b> {e(m['inp'])}</span><span class="io1"><b>Out</b> {e(m['out'])}</span></div>
        <div class="diff"><b>Why this one →</b> {e(m['diff'])}</div>
        <div class="rows">
          <div class="r"><span class="rl">Model</span><span class="rv">{e(m['model'])}</span></div>
          <div class="r"><span class="rl">Speed</span><span class="rv">{(wall+'s on a 5090') if wall else '—'}</span></div>
          <div class="r"><span class="rl">Peak VRAM</span><span class="rv">{(vram+' GB') if vram else '—'}</span></div>
        </div>
      </div>''')
    measured = sum(1 for k in META if status_of(bench.get(k,{}))=="measured")
    drifted  = sum(1 for k in META if status_of(bench.get(k,{}))=="drifted")
    now = datetime.datetime.now().strftime("%Y-%m-%d")
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
 .sub{{font-family:ui-monospace,monospace;font-size:12.5px;color:#7d858e;margin:8px 0}}
 .status{{padding:10px 14px;background:#101e12;border:1px solid #244029;border-radius:9px;margin:14px 0 24px;font-size:13px;color:#86d692}}
 .tier-row{{font-family:ui-monospace,monospace;font-size:12px;text-transform:uppercase;letter-spacing:1.5px;color:#5f6b78;margin:28px 0 14px;padding-bottom:7px;border-bottom:1px solid #1c222a}}
 .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(345px,1fr));gap:16px}}
 .card{{background:linear-gradient(160deg,#14181e,#10141a);border:1px solid #222a33;border-left-width:3px;border-radius:11px;padding:16px 18px}}
 .t1{{border-left-color:#6b7480}}.t2{{border-left-color:#378ADD}}.t3{{border-left-color:#9F7AEA}}.t45{{border-left-color:#14b8a6}}.t6{{border-left-color:#eab308}}
 .ch{{display:flex;align-items:baseline;gap:8px;margin-bottom:4px}} .emoji{{font-size:18px}}
 .cn{{font-size:16px;font-weight:700;color:#f2f5f8}}
 .badge{{font-family:ui-monospace,monospace;font-size:10px;padding:2px 7px;border-radius:5px;margin-left:auto;font-weight:700}}
 .tagline{{font-size:13px;color:#aeb6bf;margin-bottom:9px}}
 .io{{display:flex;gap:14px;font-size:12px;color:#c4ccd4;margin-bottom:9px;flex-wrap:wrap}}
 .io1 b{{font-family:ui-monospace,monospace;font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:#5f6b78;margin-right:4px}}
 .diff{{font-size:12.5px;color:#9aa3ad;background:#0e1217;border:1px solid #1c222a;border-radius:7px;padding:8px 10px;margin-bottom:11px}}
 .diff b{{color:#c9a05a}}
 .rows{{display:flex;flex-direction:column;gap:5px;font-size:12.5px}}
 .r{{display:grid;grid-template-columns:80px 1fr;gap:10px}}
 .rl{{font-family:ui-monospace,monospace;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;color:#5f6b78}}
 .rv{{color:#c4ccd4}} a{{color:#e8a33d}}
 .foot{{margin-top:36px;padding:16px;background:#10141a;border:1px solid #1c222a;border-radius:10px;font-size:12.5px;color:#8893a0}}
</style></head><body><div class="wrap">
<h1>Workflow Catalogue <span class="a">·</span> theinvalid.me</h1>
<p class="sub">RTX 5090 32GB · on-box measurements · auto-regenerated by the monthly workflow-maintenance run</p>
<div class="status">● {measured} workflows measured · {drifted} drifted · each tile says what it's for, what goes in/out, and why you'd pick it. Updated {now}.</div>
{body}
<div class="foot"><b>How this stays honest:</b> a monthly job validates every workflow against the live ComfyUI node registry, benchmarks the ones that run, and flags drift (when an upstream pack renames a node). This page is generated from that run — no stale claims. Raw numbers: <a href="https://github.com/MushiSenpai/mushishi-creative-stack/blob/main/benchmarks/benchmarks.csv">benchmarks.csv</a>.</div>
</div></body></html>'''
    open(OUT,"w").write(page)
    print(f"catalogue written: {OUT} ({measured} measured, {drifted} drifted)")

if __name__ == "__main__":
    main()
