#!/usr/bin/env python3
"""generate-catalogue.py — build the UNIFIED workflow catalogue HTML from REAL data.

Three sources, one honest page:
  - creative benchmarks.csv  (image + video + editing + finishing + pipelines)
  - audio  benchmarks.csv    (TTS, voice clone, lipsync, music, transcribe, dub)
  - inline scriptwriting LLM numbers (sovereign-stack stress tests)

Each tile carries BOTH a quality tier AND a capability. The page renders with a
"Group by" toggle (Quality tier = default, or Capability) and a modality filter,
so the same tiles can be sliced either way — client-side, no rebuild needed.

Status per tile is derived from the data, never faked:
  measured  = clean wall-clock from a real run
  estimate  = wall-clock present but estimated (~ / "estimate" in notes)
  pending   = built / runs, but not yet timed (empty wall-clock)
  blocked   = a known blocker in notes

Part of the monthly workflow-maintenance system — regenerates so nothing goes stale."""
import csv, html, json, datetime

CREATIVE_CSV = "/home/mushi/Documents/github-staging/mushishi-creative-stack/benchmarks/benchmarks.csv"
AUDIO_CSV    = "/home/mushi/Documents/github-staging/mushishi-audio-stack/benchmarks/audio-benchmarks.csv"
OUT          = "/data/ai/08-portfolio/theinvalid-site/public/workflow-catalogue.html"

# join_key -> rich, human-curated metadata.
#   src  : modality bucket for the filter (script / creative / audio / pipeline)
#   tier : quality tier (1,2,3,45,6,7)  ·  cap : capability bucket
#   static: inline numbers for tiles NOT in any CSV (the scriptwriting LLMs + the avatar pipeline)
META = {
 # ── Scriptwriting (LLM) — the two sovereign text models ───────────────────
 "Scribe": dict(name="Scribe", src="script", tier="1", cap="script", emoji="✍️",
    model="Nemotron 3 Nano 30B PRISM", inp="Brief / scene idea", out="Script, shot-prompts, beats",
    purpose="Fast structured scriptwriting + shot-prompt drafting.",
    diff="The sovereign reasoning model (also writes the forensic scene specs). Always-on, fast, structured — for prompts, beats, and JSON the pipeline obeys. For long-form uncensored prose use Inkwell.",
    static=dict(speed="276 tok/s · knee @ 8 concurrent (728 agg)", vram="~22 GB (agent mode)", thr="stress-tested 2026-06-13", status="measured")),
 "Inkwell": dict(name="Inkwell", src="script", tier="2", cap="script", emoji="🖋️",
    model="Dolphin 3.0 R1 Mistral 24B (AWQ)", inp="Logline / premise", out="Screenplay / long-form script",
    purpose="Long-form unrestricted creative scriptwriting.",
    diff="Unrestricted local writer with 96K context (Script Mode) — full screenplays, character bibles, no refusals. Wider creative range than Scribe; slower, needs creative-mode VRAM.",
    static=dict(speed="~80 tok/s (AWQ INT4, est)", vram="~12–14 GB", thr="96K context", status="pending")),

 # ── Image ─────────────────────────────────────────────────────────────────
 "Flashfire": dict(name="Flashfire", src="creative", tier="1", cap="image", emoji="⚡", model="FLUX.2 4B (distilled)",
    inp="Text prompt", out="1024² PNG", purpose="Instant still drafts for fast iteration.",
    diff="4-step distilled — the FASTEST stills. For composition/seed exploration. Lower fidelity than Goldsmith."),
 "Goldsmith": dict(name="Goldsmith", src="creative", tier="2", cap="image", emoji="🔨", model="FLUX.2 4B (base)",
    inp="Text prompt", out="1024² PNG", purpose="Refined keyframes worth building a shot on.",
    diff="Full-step base model — markedly higher fidelity than Flashfire. The still you animate or deliver."),
 "FluxCommercial": dict(name="Ledger", src="creative", tier="2", cap="image", emoji="⚖️", model="FLUX.1 Dev (Apache-2.0)",
    inp="Text prompt", out="PNG", purpose="License-clean stills you can sell to clients.",
    diff="The ONLY image model here under a commercial-safe license (Apache-2.0). Pick it for paid client deliverables."),

 # ── Video (generate) ────────────────────────────────────────────────────────
 "WanDraft": dict(name="Quickdraw", src="creative", tier="1", cap="video", emoji="✏️", model="Wan 2.1 1.3B",
    inp="Text prompt", out="~480p short clip", purpose="Throwaway motion/timing test before a real render.",
    diff="Tiny 1.3B — quickest way to check motion & composition. Draft quality; commit the shot, then use a Tier-2/3 model."),
 "Wan22_T2V": dict(name="Conjurer", src="creative", tier="2", cap="video", emoji="🎞️", model="Wan 2.2 14B MoE",
    inp="Text prompt", out="480/720p video", purpose="Production text→video.",
    diff="14B mixture-of-experts (high+low-noise two-sampler) — production quality. Slower than Quickdraw, faster/lighter than the cinematic Tier-3 Hunyuans."),
 "Wan22_I2V": dict(name="Breath", src="creative", tier="2", cap="video", emoji="🌬️", model="Wan 2.2 14B MoE",
    inp="Image + prompt", out="480/720p video", purpose="Animate a still image into video.",
    diff="Fast, reliable image→video. Pick this over Quickening when you want speed/production over maximum cinematic polish."),
 "dreamforge": dict(name="dreamforge", src="creative", tier="3", cap="video", emoji="🌆", model="HunyuanVideo 1.5 720p (fp16)",
    inp="Text prompt", out="Cinematic 720p video", purpose="The hero cinematic text→video.",
    diff="HunyuanVideo 1.5 — the highest cinematic quality text→video here (atmosphere, camera, lighting). Slower than Conjurer; worth it for the money shot."),
 "quickening": dict(name="quickening", src="creative", tier="3", cap="video", emoji="✨", model="HunyuanVideo 1.5 I2V (fp8 distilled)",
    inp="Image + prompt", out="Cinematic 720p video", purpose="Cinematic image→video — bring a still to life.",
    diff="Hunyuan I2V — the most cinematic animation of a keyframe. Pick over Breath when polish matters more than speed."),

 # ── Video editing (client work) ─────────────────────────────────────────────
 "Vanisher": dict(name="Vanisher", src="creative", tier="45", cap="edit", emoji="🫥", model="VOID + SAM3 (video)",
    inp="Video + object to remove", out="Video, object erased", purpose="Erase an object from a video.",
    diff="VOID+SAM3 — removes an object AND its reflections/shadows (the forensic differentiator). Shapeshifter swaps; Vanisher erases."),
 "Shapeshifter": dict(name="Shapeshifter", src="creative", tier="45", cap="edit", emoji="🦎", model="Wan 2.1 VACE + SAM3",
    inp="Video + masked region", out="Video, region swapped/reframed", purpose="Swap or reframe a masked region.",
    diff="VACE — replaces/reframes content inside a mask (vs Vanisher which only erases). For client edits that change a region, not delete it."),

 # ── Finishing (4K / 60fps) ──────────────────────────────────────────────────
 "sharpscale": dict(name="sharpscale", src="creative", tier="3", cap="finish", emoji="🔎", model="HunyuanVideo 1.5 1080p SR",
    inp="720p Hunyuan video", out="True 1080p (1920×1072)", purpose="Super-resolve a Hunyuan clip to crisp 1080p.",
    diff="Hunyuan-native latent super-res — preserves Hunyuan detail. Use after dreamforge/quickening. For general 4K from any source, use Crystalforge instead."),
 "Silkmotion": dict(name="Silkmotion", src="creative", tier="6", cap="finish", emoji="🪶", model="RIFE v4.9",
    inp="Any video", out="60fps video", purpose="Smooth any clip to 60fps.",
    diff="Frame interpolation — adds MOTION smoothness, not resolution. Pair with Crystalforge/sharpscale for 4K@60."),
 "Crystalforge": dict(name="Crystalforge", src="creative", tier="6", cap="finish", emoji="💎", model="SeedVR2 7B",
    inp="720p video (any source)", out="4K video", purpose="General video super-resolution to 4K.",
    diff="SeedVR2 — source-agnostic 720p→4K. Use sharpscale instead when the source is Hunyuan and you only need 1080p (faster, native)."),

 # ── Voice / TTS ─────────────────────────────────────────────────────────────
 "FishSpeechTTS": dict(name="Narrator", src="audio", tier="2", cap="voice", emoji="🎙️", model="Fish Speech 1.5",
    inp="Text (+ optional voice clone)", out="WAV speech", purpose="Voiceover narration in any voice.",
    diff="Production TTS with voice cloning, ~145 wpm. The voice behind avatars, dubs, and narration. Clone a reference with Echo first for a custom speaker."),
 "VoiceClone": dict(name="Echo", src="audio", tier="2", cap="voice", emoji="🧬", model="Demucs + Fish Speech",
    inp="30s reference clip", out="Reusable voice profile", purpose="Turn a voice sample into a reusable cloned profile.",
    diff="Demucs strips music/noise first (raw samples clone robotic), then Fish Speech builds the profile Narrator reuses. Run once per speaker."),

 # ── Lip-sync / Avatar ───────────────────────────────────────────────────────
 "MuseTalk": dict(name="Mouthpiece", src="audio", tier="1", cap="lipsync", emoji="👄", model="MuseTalk 1.5 (DWPose/rtmlib)",
    inp="Portrait + audio", out="Talking-head MP4", purpose="Social-grade talking-head from a portrait.",
    diff="WORKING — runs in its own isolated container; DWPose via rtmlib/ONNX sidesteps the mmcv/cu130 wall. Social-grade: coherent mouth, distinct visemes, no melt (the LatentSync failure). Loads per job, 0 idle VRAM. The other two lipsync tiers stay rebuild-required; broadcast-grade = cloud."),
 "LatentSync": dict(name="Persona", src="audio", tier="2", cap="lipsync", emoji="🗣️", model="LatentSync",
    inp="Portrait + audio", out="H.264 talking-head", purpose="Talking-head from a portrait (REBUILD REQUIRED).",
    diff="Rebuild required — produces structurally corrupt output (mouth melt/seams) in the unified worker. All 3 local lip-sync models need their own pinned env. Local = social-grade; broadcast = cloud."),
 "Hallo2": dict(name="Thespian", src="audio", tier="3", cap="lipsync", emoji="🎭", model="Hallo2",
    inp="Portrait + audio", out="H.264 MP4 (half-body + expression)", purpose="Cinematic talking-head (REBUILD REQUIRED).",
    diff="Rebuild required — diffusers API break in the unified worker (worked in its own container before). The strongest local fallback once rebuilt in a pinned env. Broadcast-grade = cloud."),

 # ── Music ───────────────────────────────────────────────────────────────────
 "ACEStep": dict(name="Pulse", src="audio", tier="1", cap="music", emoji="🥁", model="ACE-Step 3.5B",
    inp="Genre / mood text", out="30s stereo 48kHz WAV", purpose="Fast, high-fidelity instrumental beds.",
    diff="Real stereo 48kHz instrumental in ~10s (1.8s diffusion, ~30× realtime) — higher fidelity than Anthem's mono. Runs in an isolated venv; gateway wiring pending. (Maestro's old 'ACE-Step' score was actually YuE.)"),
 "StableAudio": dict(name="Ambience", src="audio", tier="2", cap="music", emoji="🌌", model="Stable Audio Open 1.0",
    inp="Text prompt", out="Up to 47s audio", purpose="Cinematic / ambient underscore.",
    diff="Production ambient/cinematic beds. Richer than Pulse; instrumental only (no vocals). For songs with lyrics use Anthem."),
 "YuE7B": dict(name="Anthem", src="audio", tier="3", cap="music", emoji="🎵", model="YuE 7B",
    inp="Genre + lyrics", out="15s+ MP3 (mono)", purpose="Full song with vocals from lyrics.",
    diff="The only model here that sings — full song with vocals. Needs music-mode.sh (exclusive ~16GB); mono is a vocoder limit. Layer a cloned voice with RVC if needed."),

 # ── Transcribe ──────────────────────────────────────────────────────────────
 "Transcribe": dict(name="Stenographer", src="audio", tier="2", cap="asr", emoji="📝", model="Whisper V3 Turbo + WhisperX",
    inp="Audio / video", out="JSON + word timings (+SRT)", purpose="Transcribe speech with word-level timestamps.",
    diff="Draft = Whisper only; production adds WhisperX word alignment (the timestamps dubbing & subtitles need). ~2GB, runs in any mode."),

 # ── Dubbing ─────────────────────────────────────────────────────────────────
 "Dub": dict(name="Polyglot", src="audio", tier="45", cap="dub", emoji="🌐", model="Whisper → Nemotron → Fish Speech",
    inp="Video + target language", out="Dubbed MP4 + SRT", purpose="Dub a video into another language.",
    diff="Same-language dub works end-to-end (~20s: transcribe → TTS → SRT → mux). Cross-language routes translation via LiteLLM → local Nemotron; reliable cross-lang needs the GPU Nemotron loaded (the always-on CPU one is too slow for live routing). video_locked swaps the track; audio_first feeds Wan."),

 # ── Pipelines (idea → finished deliverable) ─────────────────────────────────
 "maestro": dict(name="Maestro", src="pipeline", tier="7", cap="pipeline", emoji="🎬",
    model="Scribe → FLUX.2 → Wan 2.2 I2V MoE → YuE", inp="One-line scene idea",
    out="832×480 cinematic clip + original score",
    purpose="One sentence → a finished, scored cinematic clip — fully automated, 100% local.",
    diff="The end-to-end sovereign pipeline: a local LLM writes the prompts, FLUX paints the keyframe, Wan animates it, YuE composes the score — one command, no cloud, no manual stitching."),
 "DailyPipeline": dict(name="Daybreak", src="pipeline", tier="7", cap="pipeline", emoji="🌅",
    model="Inkwell/LLM → FLUX.2 → Wan 2.2 I2V", inp="One-line text brief", out="Keyframe PNG + MP4 clip",
    purpose="Text brief → keyframe → animated clip (no score).",
    diff="Scriptwriting + image + video in one run: the LLM writes the shot, FLUX paints it, Wan animates it. No score — add Maestro for that. Wall-clock is an estimate from measured parts."),
 "Storyteller": dict(name="Storyteller", src="pipeline", tier="7", cap="pipeline", emoji="📖",
    model="Scribe → Echo/Narrator → Persona", inp="Portrait + script", out="Talking-avatar MP4",
    purpose="Portrait + script → cloned-voice talking avatar.",
    diff="Scriptwriting + voice + lip-sync end-to-end: clone the voice, narrate the script, sync to the face. The audio counterpart to Maestro — ~5min for a 34.5s avatar (E2, partial pass: social/preview tier).",
    static=dict(speed="~305s (TTS 25s + LatentSync 280s)", vram="~6 GB", thr="E2 2026-06-12, partial pass", status="measured")),
}

TIER_ORDER = [
 ("1",  "Tier 1 — Fast Draft"),
 ("2",  "Tier 2 — Production"),
 ("3",  "Tier 3 — Cinematic"),
 ("45", "Tier 4.5 — Editing (client work)"),
 ("6",  "Tier 6 — Finishing (4K / 60fps)"),
 ("7",  "Tier 7 — Pipelines (idea → finished deliverable)"),
]
CAP_ORDER = [
 ("script",  "✍️ Scriptwriting (LLM)"),
 ("image",   "🖼️ Image"),
 ("video",   "🎞️ Video — generate"),
 ("edit",    "✂️ Video — editing"),
 ("finish",  "💠 Finishing (4K / 60fps)"),
 ("voice",   "🎙️ Voice / TTS"),
 ("lipsync", "🎭 Lip-sync / Avatar"),
 ("music",   "🎵 Music"),
 ("asr",     "📝 Transcribe"),
 ("dub",     "🌐 Dubbing"),
 ("pipeline","🎬 Pipelines — end-to-end"),
]
FILTERS = [
 ("all",      "Everything"),
 ("script",   "Scriptwriting"),
 ("creative", "Creative (image + video)"),
 ("audio",    "Audio"),
 ("pipeline", "Pipelines"),
]
BADGES = {
 "measured": ("✅ measured",    "#0d2a1a", "#4ade80"),
 "estimate": ("🟡 estimate",    "#2a230d", "#eab308"),
 "pending":  ("⬜ perf pending", "#161616", "#8a8a8a"),
 "blocked":  ("⚠️ blocked",     "#2a1a0d", "#fb923c"),
}

def load_csv(path):
    rows = {}
    try:
        with open(path) as f:
            for r in csv.DictReader(f): rows[r["workflow"]] = r
    except FileNotFoundError: pass
    return rows

def status_of(wall, notes):
    nt = notes or ""
    if "BLOCKED" in nt: return "blocked"   # intentional uppercase marker, not prose
    n = nt.lower()
    w = (wall or "").strip()
    if w and w not in ("", "-"):
        if w.startswith("~") or "estimate" in n: return "estimate"
        return "measured"
    return "pending"

def main():
    bench = {}
    bench.update(load_csv(CREATIVE_CSV))
    bench.update(load_csv(AUDIO_CSV))
    e = html.escape
    tiles = []
    counts = {"measured":0, "estimate":0, "pending":0, "blocked":0}

    for key, m in META.items():
        r = bench.get(key, {})
        static = m.get("static")
        if static:
            st = static["status"]
            speed_str = static.get("speed", "—")
            vram_str  = static.get("vram", "—")
            thr_str   = static.get("thr", "")
        else:
            wall = (r.get("wall_clock_sec") or "").strip()
            vram = (r.get("peak_vram_gb") or "").strip()
            thr  = (r.get("throughput") or "").strip()
            st = status_of(wall, r.get("notes"))
            speed_str = (wall + "s on a 5090") if wall else "—"
            vram_str  = (vram + " GB") if vram else "—"
            thr_str   = thr
        counts[st] += 1
        b = BADGES[st]
        thr_row = (f'\n          <div class="r"><span class="rl">Throughput</span><span class="rv">{e(thr_str)}</span></div>'
                   if thr_str else "")
        card = f'''<div class="card t{m['tier']}" data-cap="{m['cap']}" data-tier="{m['tier']}" data-src="{m['src']}">
        <div class="ch"><span class="emoji">{m['emoji']}</span><span class="cn">{e(m['name'])}</span>
          <span class="badge" style="background:{b[1]};color:{b[2]}">{b[0]}</span></div>
        <div class="tagline">{e(m['purpose'])}</div>
        <div class="io"><span class="io1"><b>In</b> {e(m['inp'])}</span><span class="io1"><b>Out</b> {e(m['out'])}</span></div>
        <div class="diff"><b>Why this one →</b> {e(m['diff'])}</div>
        <div class="rows">
          <div class="r"><span class="rl">Model</span><span class="rv">{e(m['model'])}</span></div>
          <div class="r"><span class="rl">Speed</span><span class="rv">{e(speed_str)}</span></div>
          <div class="r"><span class="rl">Peak VRAM</span><span class="rv">{e(vram_str)}</span></div>{thr_row}
        </div>
      </div>'''
        tiles.append({"html": card, "tier": m["tier"], "cap": m["cap"], "src": m["src"]})

    now = datetime.datetime.now().strftime("%Y-%m-%d")
    total = len(tiles)
    statusline = (f"● {total} workflows · {counts['measured']} measured · "
                  f"{counts['estimate']} estimated · {counts['pending']} perf-pending · "
                  f"{counts['blocked']} blocked — numbers are real, empty cells are honest. Updated {now}.")

    STYLE = """<style>
 *{margin:0;padding:0;box-sizing:border-box}
 body{font-family:system-ui,sans-serif;background:#0b0d10;color:#d8dde2;padding:32px 24px 80px;line-height:1.5}
 .wrap{max-width:1180px;margin:0 auto}
 h1{font-size:28px;font-weight:800;color:#f2f5f8} h1 .a{color:#e8a33d}
 .sub{font-family:ui-monospace,monospace;font-size:12.5px;color:#7d858e;margin:8px 0}
 .status{padding:10px 14px;background:#101e12;border:1px solid #244029;border-radius:9px;margin:14px 0 18px;font-size:13px;color:#86d692}
 .controls{display:flex;gap:18px;flex-wrap:wrap;align-items:center;margin:0 0 8px;font-size:12.5px}
 .controls label{font-family:ui-monospace,monospace;font-size:10.5px;text-transform:uppercase;letter-spacing:.6px;color:#5f6b78;margin-right:7px}
 .controls select{background:#14181e;color:#d8dde2;border:1px solid #2a333d;border-radius:7px;padding:6px 10px;font-size:12.5px;font-family:inherit;cursor:pointer}
 .controls select:hover{border-color:#3a4654}
 .tier-row{font-family:ui-monospace,monospace;font-size:12px;text-transform:uppercase;letter-spacing:1.5px;color:#5f6b78;margin:28px 0 14px;padding-bottom:7px;border-bottom:1px solid #1c222a}
 .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(345px,1fr));gap:16px}
 .card{background:linear-gradient(160deg,#14181e,#10141a);border:1px solid #222a33;border-left-width:3px;border-radius:11px;padding:16px 18px}
 .t1{border-left-color:#6b7480}.t2{border-left-color:#378ADD}.t3{border-left-color:#9F7AEA}.t45{border-left-color:#14b8a6}.t6{border-left-color:#eab308}.t7{border-left-color:#ec4899}
 .ch{display:flex;align-items:baseline;gap:8px;margin-bottom:4px} .emoji{font-size:18px}
 .cn{font-size:16px;font-weight:700;color:#f2f5f8}
 .badge{font-family:ui-monospace,monospace;font-size:10px;padding:2px 7px;border-radius:5px;margin-left:auto;font-weight:700;white-space:nowrap}
 .tagline{font-size:13px;color:#aeb6bf;margin-bottom:9px}
 .io{display:flex;gap:14px;font-size:12px;color:#c4ccd4;margin-bottom:9px;flex-wrap:wrap}
 .io1 b{font-family:ui-monospace,monospace;font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:#5f6b78;margin-right:4px}
 .diff{font-size:12.5px;color:#9aa3ad;background:#0e1217;border:1px solid #1c222a;border-radius:7px;padding:8px 10px;margin-bottom:11px}
 .diff b{color:#c9a05a}
 .rows{display:flex;flex-direction:column;gap:5px;font-size:12.5px}
 .r{display:grid;grid-template-columns:84px 1fr;gap:10px}
 .rl{font-family:ui-monospace,monospace;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;color:#5f6b78}
 .rv{color:#c4ccd4} a{color:#e8a33d}
 .empty{color:#5f6b78;font-size:13px;padding:20px 4px}
 .foot{margin-top:36px;padding:16px;background:#10141a;border:1px solid #1c222a;border-radius:10px;font-size:12.5px;color:#8893a0}
</style>"""

    data = {
        "tiles": tiles,
        "tierOrder": TIER_ORDER,
        "capOrder": CAP_ORDER,
    }
    SCRIPT = (
        "<script>\n"
        "const DATA = " + json.dumps(data) + ";\n"
        "const cat = document.getElementById('catalogue');\n"
        "function render(){\n"
        "  const axis = document.getElementById('groupBy').value;\n"
        "  const filt = document.getElementById('filterBy').value;\n"
        "  const order = axis === 'cap' ? DATA.capOrder : DATA.tierOrder;\n"
        "  const keyOf = t => axis === 'cap' ? t.cap : t.tier;\n"
        "  const pool = DATA.tiles.filter(t => filt === 'all' ? true : t.src === filt);\n"
        "  let out = '';\n"
        "  for (const [k, label] of order){\n"
        "    const items = pool.filter(t => keyOf(t) === k);\n"
        "    if (!items.length) continue;\n"
        "    out += '<div class=\"tier-row\">' + label + '</div><div class=\"grid\">' + items.map(t => t.html).join('') + '</div>';\n"
        "  }\n"
        "  cat.innerHTML = out || '<div class=\"empty\">No workflows match this filter.</div>';\n"
        "}\n"
        "document.getElementById('groupBy').addEventListener('change', render);\n"
        "document.getElementById('filterBy').addEventListener('change', render);\n"
        "render();\n"
        "</script>"
    )

    page = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>Workflow Catalogue — theinvalid.me</title>\n'
        + STYLE +
        '</head><body><div class="wrap">\n'
        '<h1>Workflow Catalogue <span class="a">·</span> theinvalid.me</h1>\n'
        '<p class="sub">RTX 5090 32GB · on-box measurements · scriptwriting + creative + audio, one sovereign stack · auto-regenerated by the monthly workflow-maintenance run</p>\n'
        f'<div class="status">{statusline}</div>\n'
        '<div class="controls">\n'
        '  <span><label>Group by</label><select id="groupBy">'
        '<option value="tier">Quality tier</option>'
        '<option value="cap">Capability</option></select></span>\n'
        '  <span><label>Show</label><select id="filterBy">'
        + "".join(f'<option value="{v}">{e(lbl)}</option>' for v, lbl in FILTERS) +
        '</select></span>\n'
        '</div>\n'
        '<div id="catalogue"></div>\n'
        '<div class="foot"><b>How this stays honest:</b> a monthly job validates every workflow against the live registries, '
        'benchmarks the ones that run, and flags drift. This page is generated from that run — no stale claims. '
        'Badges: <b>measured</b> = clean wall-clock from a real run · <b>estimate</b> = derived from measured parts · '
        '<b>perf pending</b> = built &amp; runs, not yet timed · <b>blocked</b> = a known dependency blocker. '
        'Raw numbers: <a href="https://github.com/MushiSenpai/mushishi-creative-stack/blob/main/benchmarks/benchmarks.csv">creative benchmarks.csv</a> · '
        '<a href="https://github.com/MushiSenpai/mushishi-audio-stack/blob/main/benchmarks/audio-benchmarks.csv">audio benchmarks.csv</a>. '
        'Scriptwriting throughput from the sovereign-stack stress tests. '
        '<b>Lip-sync / avatar:</b> all local models are pending a dedicated-environment rebuild (MuseTalk 1.5 target) — '
        'local output tops at <b>social-grade</b>; broadcast-grade uses a <b>cloud</b> path.</div>\n'
        + SCRIPT +
        '\n</div></body></html>'
    )
    open(OUT, "w").write(page)
    print(f"catalogue written: {OUT} ({total} tiles — "
          f"{counts['measured']} measured, {counts['estimate']} est, "
          f"{counts['pending']} pending, {counts['blocked']} blocked)")

if __name__ == "__main__":
    main()
