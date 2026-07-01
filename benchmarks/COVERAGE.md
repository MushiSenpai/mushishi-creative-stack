# Workflow Coverage & Benchmark Status

Honest map of every workflow in the stack: what's **measured** (real numbers in
`benchmarks.csv`), what's **built but unmeasured**, and what's **defined but not
built**. The goal: even where the workflow JSON isn't published, the *measured
capability* is — "this produces X in Y seconds at Z GB" is itself the proof.

Hardware: RTX 5090 32GB · Ryzen 9 9900X3D · 128GB DDR5 · Ubuntu 24.04 · CUDA 13.2.
All numbers are on-box measurements, indicative not guaranteed.

## ✅ Measured — real numbers committed (sweep 2026-06-13)

| Workflow | Tier | Result | Verdict |
|---|---|---|---|
| **Flashfire** (FLUX.2 4B *distilled*, 4-step/CFG 1.0) | 1 | 10s, 1024² | render-verified 2026-06-15 (cold-load incl); fast draft |
| **Goldsmith** (FLUX.2 4B keyframe) | 2 | 6s, 11.2GB, 1024² | clean |
| **Sterling** (Qwen-Image 20B fp8, Apache-2.0 — commercial hero) | 2 | 12s warm / 16–20s cold, ~28GB, 1024×576 | measured 2026-06-22; eye-verified 3 seeds (42/99/123), clean commercial product shots; `--keyframe qwen` + the new `--mode commercial` default. **Genuinely commercial-safe** (Apache-2.0) unlike Ledger |
| **Wan 2.2 T2V** (two-sampler MoE) | 2 | 483s, 20GB, 720p 81fr | clean; confirms ~497s est |
| **Wan 2.2 I2V** (keyframe animation) | 2 | 502s, 20GB, 720p 81fr | clean; confirms ~506s est |
| **Silkmotion** (RIFE interpolation) | 6 | 12s, 3.5GB, →60fps | clean; confirms ~8.3s |
| **Shapeshifter** (Wan2.1 VACE + SAM3 video) | 4.5 | 802s, 20.6GB | clean; SAM3-video mask works |
| **Vanisher** (VOID removal) | 4.5 | 149-189s, 27GB | clean on representative footage (E1d) |
| **Crystalforge** (SeedVR2 4K) | 6 | 586s, 25.7GB | clean upscale |
| **dreamforge / quickening / sharpscale** (Hunyuan 1.5 T2V/I2V/SR) | 3 | 16s / 21s / 73s | render-verified 2026-06-15 |
| **Maestro** (idea → cinematic clip + score) | 7 | 512s, ~18GB | end-to-end, render-verified 2026-06-15; single segment is 3.375s (Wan I2V frame cap) — for >3.375s see the long-clip chain + drift finding below |
| **Commercial pipeline (CRE-2)** (FLUX.1-dev 'ledger' kf → Wan I2V → ACE-Step → mux) | 7 | 658s (kf 16s + i2v 510s + music 8s) | measured 2026-06-22; output `commercial_s42_final.mp4` (3.375s). ⚠ keyframe is **non-commercial** FLUX.1-dev — see licence note |
| **Commercial pipeline — Qwen default (CRE-2 closed)** (Sterling/Qwen-Image kf → Wan I2V → ACE-Step → mux) | 7 | 560s (kf 32s cold + i2v 520s + music 8s), 28.1GB peak | measured 2026-07-02 on the `--mode commercial` **default** — **every link commercially licensed** (Apache-2.0 keyframe); keyframe + last frame eye-verified clean (no melt through I2V). A "Commercial" full-pipeline tile is warranted |
| **DailyPipeline** (brief → keyframe → video, no score) | 7 | 510–526s | measured 2026-06-22 (was estimate) — derived from the maestro+CRE-2 A+B components |
| **Long-clip chain (CRE-3)** (3× I2V segment chain) | 7 | 1592s (kf 8s + i2v 1480s + music 8s) | measured 2026-06-22; `maestro_chained.mp4` (10.125s, 243fr @24fps). Clean concat but **visible inter-segment drift** — see verdict below. **Reproduced + metric-backed + loop-compared 2026-07-02** (chain 1508s vs loop 494s) |
| Nemotron LLM (**Scribe**) | — | 276 tok/s single-stream; knee@8 concurrent (728 agg); sustained 2-stream 437 agg / 218 per-stream; **sustained 8-stream saturation 717 agg / 89.6 per-stream (240s, 0 errors), 406W avg / 419W peak @ 64–68°C, clocks flat ~2865MHz, zero throttle** | concurrency knee 2026-06-13; sustained 2-stream 2026-06-22; saturation sweep 2026-07-02 — **the knee holds sustained** (98% of burst) |
| **Inkwell** (Dolphin 3.0 R1 Mistral 24B AWQ) | 2 | 106 tok/s single-stream decode, 32K ctx (63.6K KV) | measured 2026-06-22 (was ~80 est); decode trap fixed |
| Score (ACE-Step) | audio | ACE-Step 3.5B: 20s instrumental score in ~8s | used by Maestro pipeline |

> **Inkwell decode-trap note (2026-06-22):** the AWQ repo ships `tokenizer_config.json`
> with `tokenizer_class: LlamaTokenizer`, which transformers 5.x routes through the
> broken Mistral-regex slow path → raw byte-level BPE leak (`Ġ`/`Ċ` for space/newline —
> the queue.md C-trap symptom). The `tokenizer.json` itself is correct (ByteLevel decoder
> round-trips cleanly under `PreTrainedTokenizerFast`/`tokenizers`). Fix: serve with a
> tokenizer-only overlay dir whose `tokenizer_class` is overridden to
> `PreTrainedTokenizerFast` (weights stay read-only) via vLLM `--tokenizer`. Real
> throughput is GPU-resident — the historic ~2 tok/s was `--cpu-offload-gb 10`, not the
> model. Run config: `--quantization awq_marlin --dtype float16 --max-model-len 32768
> --gpu-memory-utilization 0.80`, no CPU offload, temp 0.07.

> **Scribe sustained-load + thermal envelope (2026-06-22):** clean end-of-session
> max-load sweep on the **agent-mode** Nemotron (`:8000`, 32K ctx, util 0.82, kv-cache
> fp8, `--max-num-seqs 2`) — 180s steady window after a 15s warmup discard, 154 requests,
> 78.8K tokens decoded. **437 tok/s aggregate** at the config's 2-stream cap; **218 tok/s
> per stream** (very tight: 215–221); 2.4s median request latency. **GPU 96.5% util,
> 367W avg / 380W peak** (well under the 450W cap — a 3B-active MoE decode is compute-bound
> on a sparse path, not power-bound), **61°C avg / 66°C peak, zero throttle** across the
> whole window; VRAM flat at 27.9GB. Replaces the prior passive "~139-avg" observation
> with a real sustained number. (The 437/218 figures exceed the 276 single-stream peak
> because continuous batching adds the second stream on top — consistent with the B-1
> curve. Higher concurrency would need a larger `--max-num-seqs`; the B-1 knee@8 was
> measured on the forensic config.)

> **Flashfire reconciliation (2026-06-22):** this row was previously listed under
> *parked — "needs the distilled model file."* That was stale. The distilled checkpoint
> the `t1-flux2-4b-flashfire.json` UNETLoader names —
> `flux-2-klein-4b-fp8.safetensors` (the 4-step/CFG-1.0 distilled variant, *distinct*
> from Goldsmith's `flux-2-klein-base-4b-fp8.safetensors` base) — is present on disk
> (3.8 GB, predates the 06-15 render) and resolvable via the ComfyUI `unet`/`checkpoints`
> search paths. So the `benchmarks.csv` "render-verified 2026-06-15" claim is genuine,
> not a stand-in. Moved from parked → measured to match the CSV and the catalogue tile.

> **Long-clip chain + drift verdict (CRE-3, measured 2026-06-22):** the >3.375s
> question — Wan I2V caps a single segment at 3.375s (81fr), so longer clips need
> chaining. Measured a **3×3.375s chain** in maestro mode: keyframe 8s + I2V 1480s
> (3 segments) + ACE-Step score 8s = **1592s total** → `maestro_chained.mp4`
> (**10.125s, 243 frames @24fps**). **Honest verdict (per "honest incl. failures"):**
> the chain produces a *clean concat*, **but inter-segment drift is real and visible** —
> the colour palette wanders (blue→pink→blue across segments), the subject's
> scale/position/shape shifts at each seam, the dolly motion **restarts** (a cadence
> hitch) at the joins, and a **seam artifact** appeared (a malformed gull). Practical
> rule: **viable for gentle/ambient shots >3.375s but NOT seamless** — best kept to
> **≤2 segments**, or use **loop-mode** for static scenes. This is the measured data
> behind the single-segment **3.375s cap** caveat in the measured table above.

> **CRE-3 reproduction + chain-vs-loop comparison (2026-07-02):** re-ran the 10s
> chain at full segment length on a different (misty/ambient) scene and — for the
> first time — the **loop fallback on the same scene/seed**, with metric-backed QA
> (`cre3_drift_qa`: per-boundary color/brightness/saturation L1 + a coarse structure
> MAE). **Chain** (kf 8s + 3×~500s I2V = 1508s): the *seams themselves are clean* —
> join deltas color_L1 ≤1.5 / struct MAE 0.0027 at both joins, visually a continuous
> shot — but **cumulative drift compounds monotonically** (last-frame vs anchor:
> color_L1 7.8 → 12.2 → 14.5; struct MAE 0.028 → 0.030 → 0.032): the subject grows
> (compounded dolly), the palette saturates/warms, and silhouette detail erodes by
> segment 3. No catastrophic seam artifact this run (vs 06-22's malformed gull) —
> ambient scenes are the favorable case. **Loop** (kf 4s + 1×490s I2V + ffmpeg
> ping-pong fill = 494s, **1/3 the GPU time**): zero drift by construction, the
> ping-pong turn and restart frames are visually identical — but **motion reverses**
> (a walking subject moonwalks), so loop only suits static/ambient scenes. **Refined
> verdict:** >3.375s chaining **is client-usable for gentle/ambient shots up to ~3
> segments** (drift, not seams, is the limit); keep identity/detail-critical subjects
> to ≤2 segments; prefer loop-mode for static scenes at a third of the cost. I2V power
> envelope, measured: 448.7W avg / 451.8W peak (pegged at the 450W cap), 72–76°C, no
> thermal throttle, 17.9GB VRAM.

> **Licence correction — FLUX.1-dev / 'Ledger' is NON-COMMERCIAL (2026-06-22):** the
> `FluxCommercial` CSV row and the "FLUX.1 Dev commercial (Ledger)" label previously
> read as commercial-safe/Apache-2.0. **That is wrong.** FLUX.1 [dev] ships under the
> **FLUX.1 [dev] Non-Commercial License** — it is **NON-COMMERCIAL, fast drafts only,
> not for paid/client work.** Any claim that `flux1-dev`/Ledger is "Apache-2.0" or
> "commercial-safe" is corrected to that. The **commercial-safe keyframe hero is now
> Qwen-Image (20B, Apache-2.0)** — wired as `--keyframe qwen` and promoted to the
> **`--mode commercial` default** on 2026-06-22 (measured: 12s warm / 16–20s cold,
> ~28GB, eye-verified 3 seeds; strong prompt-adherence + native text). The auto keyframe
> map now resolves `commercial → qwen`; **Chroma1-HD (Apache-2.0)** remains a commercial-safe
> artistic alt via explicit `--keyframe chroma`; `ledger`/FLUX.1-dev stays reachable only via
> explicit `--keyframe ledger` for non-commercial drafts. The CRE-2 commercial-pipeline
> benchmark uses the `ledger` keyframe to demonstrate the *pipeline shape*, not a
> commercially-licensed deliverable. **Update 2026-07-02:** the full pipeline has now
> also been measured on the Qwen default (560s end-to-end, see the measured table) —
> the commercially-licensed chain is no longer a gap.

## ⟳ DRIFT — found 2026-06-13, REBUILT + render-verified 2026-06-15

The sweep's big finding: 4 of 9 "tested weeks ago" workflows no longer ran.
"Tested-and-working" has a shelf life without pinned node versions. All since
rebuilt against the current nodes and **render-verified** (not just re-validated):

| Workflow | Was | Now |
|---|---|---|
| HunyuanVideo 1.5 T2V (**dreamforge**) | 4 nodes missing | ✅ 16s, render-verified |
| HunyuanVideo 1.5 I2V (**quickening**) | 5 nodes missing | ✅ 21s, render-verified |
| HunyuanVideo 1.5 SR (**sharpscale**) | — | ✅ 73s → true 1080p |
| Wan 2.1 draft (**Quickdraw**) | `Video Latent` no class_type | ✅ rebuilt 1.3B draft |
| FLUX.1 Dev draft (**Ledger**, **NON-COMMERCIAL** — see licence note) | `ModelSamplingFlux.patch()` kwarg | ✅ rebuilt |

Method: adapt the pack's own example template (don't edit-in-place) + a reusable
litegraph→API converter (`scripts/ui2api_render.py`) + render-and-eye-verify each.
Lesson logged: pin custom-node versions or treat re-validation as routine maintenance.

## ✖ Retired — superseded by the host orchestrator (closes the drift saga, 2026-06-22)

Of the original 9 drifted workflows, 7 were rebuilt + render-verified (above + the
Wan/VACE/SeedVR2 set). The **last 2 were the in-graph LLM-orchestration cinematic
graphs** — graphs that embedded an LLM node *inside* the ComfyUI graph to write the
prompt before the diffusion stage. These are **retired, not rebuilt**, and the
capability is delivered instead by a **host-side orchestrator** that runs the LLM as
a pre-step and feeds the prompt into the diffusion graph. Three reasons the in-graph
approach was abandoned (each stands; this is a deliberate design choice, not a
skipped fix):

1. **Network isolation** — the ComfyUI container cannot reach the host CPU LLM
   endpoint over the docker bridge, and widening that endpoint to all interfaces
   just to satisfy an in-graph node was declined on exposure grounds.
2. **Reasoning-model contract** — a reasoning LLM returns empty `content` unless
   given a large token budget (it spends it in `reasoning_content` first); an
   in-graph node with default limits silently produces nothing.
3. **Fragility** — an in-graph *blocking* call to a slow CPU endpoint is brittle and
   fails the whole render; a host pre-step is retryable and never co-loads the LLM
   with the diffusion models on the one GPU.

Net effect: the **idea/brief → prompt → cinematic clip** capability is COVERED (see
**Maestro**, render-verified above) — by the host orchestrator, not an in-graph LLM.
The 2 retired graphs will never validate against the current nodes and are
intentionally **not** in this repo's `workflows/`. This entry is the canonical
record of the retirement; the monthly workflow-maintenance drift check should treat
them as `retired` (not `drift`) so the report stops flagging them as an open rebuild.

## ⬜ Defined but not built / parked

- **RTX VSR** — fast preview upscaler, not yet installed (calibrate vs SeedVR2)
- **LBM relight** — relight inserted elements to match plate; pairs with the
  forensic consistency map
- **The four T4 full-pipelines** (daily / cinematic / screenplay→scene /
  commercial) — chains of the above; benchmark the links first, then the chain.
  Note: these are the *host-orchestrated* chains (LLM as a pre-step), not the
  retired *in-graph*-LLM graphs above — Maestro is the render-verified one.

## ✅ `--face-forward` keyframe conditioning (A/B VERIFIED, 2026-06-22)

The orchestrator's `--face-forward` flag (`cinematic-orchestrator.py`: `FACE_FORWARD_POS`
appended to the positive prompt for every keyframe model; `FACE_FORWARD_NEG` —
"profile / side profile / turned away / looking away" — added to the *negative* only on
models that take one) was built but never render-verified (handoff item 11: "offered, not
done"; no face-forward output existed on disk). Now A/B-verified across all three supporting
keyframe models on the **same seed (42) and same one-line scene** ("a lone violinist on a
city rooftop at dusk, portrait"), eye-checking each OFF vs ON pair:

| Keyframe model | Conditioning path | OFF (default) | ON (`--face-forward`) | Verdict |
|---|---|---|---|---|
| **klein** (FLUX.2 Klein 4b, distilled) | **positive-only** (cfg 1.0, empty negative) | subject in profile, turned away over the city | torso squared to camera, head-on framing (back-lit → face in silhouette) | ✅ orientation flips profile→frontal; the pos-only path can't fully fix gaze when the scene is back-lit |
| **lustify** (SDXL) | **pos + neg** | full side-profile playing stance | frontal portrait, **direct eye contact** | ✅ strongest — the negative actively suppresses the profile (kept PRIVATE per policy) |
| **chroma** (Chroma1-HD, FLUX-based) | **pos + neg**, 26 steps / CFG 4.0 (C-17) | tiny distant side-profile silhouette | centered frontal portrait facing camera | ✅ rotates frontal *and* pulls framing to portrait scale |

**Finding:** the flag works on every model; the **pos+neg** models (lustify, chroma) give a
cleaner frontal result than klein's **positive-only** path, because the negative fragment
explicitly penalises "profile / turned away" — exactly the design rationale in the code. The
positive-only klein path reliably flips body *orientation* to frontal but can leave gaze
ambiguous under back-light. Practical guidance: for a guaranteed camera-facing subject, prefer
a pos+neg keyframe model (chroma for SFW/artistic, lustify for the private path) with
`--face-forward`; on klein, pair it with a front-light cue in the scene. Keyframe render cost
is unchanged (klein ~4s, lustify ~4–8s, chroma ~12–20s incl. its 17.8 GB load). Before/after
still pairs on disk: `outputs/cinematic/cre4_{klein,chroma}_ff-{OFF,ON}_seed42.png`
(lustify pair kept PRIVATE-suffixed, local only).

**I2V-survival (BS-9) — VERIFIED.** The second half of CRE-4: animate a face-forward keyframe
through Wan I2V and confirm the frontal framing survives (a bad keyframe propagates — Wan I2V
faithfully animates whatever is in frame 0). Ran `--mode maestro --stage B --keyframe klein
--face-forward --seg-frames 25` on a free GPU window (no foreign render evicted; ComfyUI
idle-unloaded the resident chroma weights on its own before the I2V loaded). The face-forward
klein keyframe → Wan 2.2 I2V MoE (dual-expert, 30 steps) → `maestro_video_00002.mp4` (832×480,
25 fr, 1.04 s draft, 140 s wall incl. cold-load). Eye-check of frame 0 vs the last frame: the
subject stays **squared to camera and frontal across the whole clip** — it does not rotate to
profile. Expected draft-grade Wan motion softening of the upper body/violin, but the framing
verdict holds: a frontal keyframe yields a camera-facing animation. Proof: `cre4_i2v_ff-ON_
klein_seed42.mp4` + extracted `cre4_i2v_frame_{first,last}.png`. Cost note: the wall time was
dominated NOT by the GPU (I2V was 140 s) but by the CPU-PRISM `expand_scene` reasoning pre-step
on :8001, which serialized for several minutes per orchestrator call this session — a host-LLM
latency property, orthogonal to `--face-forward`.

## ✅ Chroma vs LUSTIFY keyframe A/B (VERIFIED, 2026-06-22)

Both checkpoints are live `--keyframe` choices in `cinematic-orchestrator.py`
(`{auto,klein,lustify,chroma,ledger}`), but only LUSTIFY had ever produced a full I2V;
Chroma had never been properly A/B'd (handoff item 10: "the softer/artistic alt … never
properly A/B'd"). Now run as a controlled A/B: **same scene, same seed, same motion prompt
— only the keyframe checkpoint varies** — keyframe + a 25-frame Wan 2.2 I2V draft on each.
SFW scene on purpose so the comparison is publishable (*"a close three-quarter portrait of
a woman potter at her wheel, both hands cupped around a wet clay vessel"* — chosen to stress
the two structures distilled models melt: **hands and face**). C-17 honoured: Chroma is
Flux-based and **un-distilled**, so it runs at real steps + real CFG (26 / CFG 4.0), not
Klein's 4-step/cfg-1.0; LUSTIFY (SDXL) at 30 / CFG 6.0. Identical anatomy negative on both.

| Axis | **chroma** (Chroma1-HD, FLUX-based) | **lustify** (SDXL) |
|---|---|---|
| Character | soft, painterly, **editorial/lifestyle** palette, warm ambient mood | **photoreal**, sharp, cinematic, crisp specular detail (wet skin/clay) |
| Hand/anatomy (keyframe) | plausible but lower-detail; one hand crisp, the second arm soft/ambiguous near the vessel | **crisp two-hand articulation, well-formed fingers**, no fusion |
| Face fidelity (keyframe) | calm, frontal-ish, lower detail | sharp, three-quarter, defined features |
| Anatomy survival under I2V | hands soften toward an under-defined blob by the last frame (a soft keyframe gives Wan less structure to hold) | **hands stay articulated** through the clip; mild Wan motion-softening only; identity/pose stable |
| Load cost | **17.8 GB**, ~16 s/keyframe | **6.9 GB**, ~4–8 s/keyframe |

**Finding (BS-12 confirmed):** the domain-appropriate checkpoint wins on human anatomy.
LUSTIFY gives sharper, more reliable hands/face *and* that fidelity survives Wan I2V
better — a crisp keyframe gives the animator more structure to preserve (the same BS-9
principle: Wan faithfully animates whatever is in frame 0, so it also faithfully animates
*softness*). Chroma's strength is the opposite axis — a softer, warmer, painterly/editorial
look at a much heavier VRAM+time cost (17.8 GB vs 6.9 GB; ~16 s vs ~4–8 s/keyframe).

**Default per job type:**
- **Photoreal / human-anatomy-critical / commercial-realism** → **LUSTIFY** (SDXL) — best
  hands/face, cheapest, animates cleanest. (Its separate **private** path keeps its own
  numbers in `business/`, never here — that disclosure is an owner decision, out of scope.)
- **Soft / artistic / editorial / mood-piece, anatomy not load-bearing** → **chroma**.
- **Fast SFW draft where neither look matters** → **klein** (FLUX.2, ~4 s, distilled).

This resolves the long-floated *"rebuild on Chroma or retire"* note (below, drift repair
2026-06-14) and the handoff's open "Chroma never A/B'd" item: **Chroma is kept, scoped to the
soft/artistic niche**, not promoted to the human-realism default. SFW before/after proof on
disk: `outputs/cinematic/cre5_{chroma,lustify}_keyframe_seed1234.png` +
`cre5_{chroma,lustify}_i2v_seed1234.mp4` + extracted `cre5_*_i2v_frame_{first,last}.png`.
GPU etiquette honoured: ran in a free window alongside the idle foreign
ComfyUI/audio tenants (~3.2 GB), evicted nothing; ComfyUI auto-unloaded its own weights
between renders. Per-keyframe load cost dominated by Chroma's 17.8 GB cold-load, not sampling.

## ✅ The differentiator — forensic bridge (VERIFIED end-to-end, 2026-06-15)

`forensic_analyzer.py` (Nemotron 3-pass → JSON) → `forensic_converter.py` →
`forensic_to_comfy.py` → drives Vanisher/Shapeshifter via the ComfyUI API.
**Now run end-to-end:** the forensic payload's SAM3 prompt ("the egg in the black
frying pan") and VOID fill prompt drove an automated removal on the e4-kitchen clip
→ `void-e1c_00004_.mp4` (672×384, 144fr, 935s). The egg is removed from the pan and
the pan interior reconstructed (partial on the active pour stream). This proves the
stack's core thesis: **dense forensic description conditions the removal, no manual
masking.** Fix this pass needed: the bridge's workflow-name map pointed at a stale
filename (`vanisher.json`) — corrected to the API-format `void.json` (validates clean).

## ✅ Local coding stack (AI-1, sovereign/AI-stack — BUILT + failover-VERIFIED 2026-06-22)

Not a creative workflow — the always-on local coding endpoint Claude Code can point
at, recorded here because this is the benchmark sink. A single LiteLLM model name
`coding` (:4000) backed by GPU Qwen3-Coder by default, CPU Qwen coder when the GPU
is busy with a render.

- **GPU primary:** `Qwen3-Coder-30B-A3B-Instruct` AWQ-INT4 on vLLM 0.20.0 (:8000,
  container `vllm-coding`). `--moe-backend triton` (FlashInfer MoE broken on
  consumer Blackwell), `--dtype float16` (AWQ requires fp16), `--kv-cache-dtype fp8`,
  `--max-model-len 114688`, `--gpu-memory-utilization 0.88` (~28.7GB), image pinned
  (proven SM120 build). **~110 tok/s single-stream**; returns proper structured
  `tool_calls` via the `qwen3_coder` parser — VERIFIED.
- **CPU fallback:** `Qwen2.5-Coder-7B-Instruct` Q5_K_M on llama.cpp (:8002,
  always-on systemd user unit `qwen-coder-cpu`).
- **Failover (load-bearing, failure-based):** GPU up → GPU answers; `docker stop
  vllm-coding` → `coding` fails over to CPU (plain completions OK); GPU restart →
  returns to GPU. All three verified.
- **CAVEAT (honest):** the CPU tier's tool calls are NOT structured — this llama.cpp
  build (b9283, peg-native) does not promote Qwen2.5-Coder's tool output into the
  `tool_calls` field (emits a text-wrapped call). GPU is the daily driver; the CPU
  tier is a degraded keep-typing-during-render backstop. Fix options (owner
  decision) documented in `/data/ai/06-configs/vllm-coding/README.md`.
- **Firewall fix:** litellm-proxy attached to docker0 so it can reach the host CPU
  llama-servers on `172.17.0.1:8001/8002` past the DOCKER-USER chain (also
  un-broke the pre-existing `personal-chain-cpu` :8001 route).
- **ComfyUI VRAM-handoff hook:** documented GAP — the failure-based fallback makes
  the system correct without it; adding `vllm-coding` to the mode-script stop-list
  is a one-line follow-up.
- GPU etiquette: foreign ComfyUI + Fish-Speech (~3.25GB) left running, nothing
  evicted. NOT yet pointed at Claude Code (owner step).

## ✅ agent-mode.sh shakedown (AI-5b, sovereign/AI-stack — VERIFIED on-demand path 2026-06-22)

Not a creative workflow — the on-demand "light Nemotron + TTS coexist" mode, recorded
here because this is the benchmark sink. This is the path AI-1's coding-stack failover
trigger wires to (a healthy `:8000` is the up-signal). End-to-end shakedown in the
owner-freed exclusive GPU window: **PASS — reliable on-demand path confirmed.**

- **What ran:** `/data/ai/01-workspace/scripts/agent-mode.sh` from a clean card (2 MiB
  used). Brought up `vllm-nemotron-agent` (Nemotron-3-nano-omni-30b-a3b-reasoning, NVFP4,
  32K ctx, `--gpu-memory-utilization 0.82`, kv-cache fp8, `--max-num-seqs 2`, reasoning
  parser `nemotron_v3`, auto tool-choice) **+** the light audio stack (redis, gateway
  `:9000`, RQ worker, Fish Speech `creative-tts :9002`). Script exited 0 with the
  "AGENT MODE READY" banner; model engine init (KV cache + warmup + CUDA-graph capture)
  ~27s after image start; cache volumes external so JIT warmup was paid once.
- **Coexistence (the headline):** both models resident and **functional simultaneously**,
  not merely loaded. Peak **28,294 MiB used / 3,817 MiB free** during a concurrent run
  (3 parallel vLLM chat completions + 1 Fish Speech TTS job). Steady idle-resident
  ~28,162 MiB. Comfortably inside 32 GB with ~3.8 GB headroom at peak. Per-proc:
  vLLM EngineCore 25,382 MiB + Fish Speech ~2,262 MiB + ~498 MiB.
- **Functional proof:** vLLM returned correct, **clean-decode** output ("17+25" → `42`,
  finish_reason `stop`, **zero BPE artifacts** — no Ġ/Ċ leak; the Mistral-regex tokenizer
  WARNING in the log is benign for this model). Fish Speech TTS job via gateway went
  queued → finished in ~4 s, wrote a real 614 KB RIFF WAVE 16-bit/44.1 kHz mono to
  `outputs/audio/voiceover/954c8f67_speech.wav`. `/health` and `/v1/models` both 200.
- **On-demand discipline:** agent container is `restart: no` (brought up when needed,
  torn down to free the card) and reported `health=healthy`. Correct for a failover
  trigger — AI-1 keys off `:8000` reachability.
- **Reasoning-model gotcha re-confirmed (BS-8):** a 64-token cap returned empty `content`
  (`finish_reason: length`) — the model spends budget on reasoning first. Give it room
  (≥256–1024 tok) and content materializes. Callers/probes must allow headroom.
- **HARDENING GAP found (out of AI-5b scope, flagged):** `agent-mode.sh`'s GPU-tenant
  stop logic (`docker stop vllm-nemotron` + grep `comfyui|creative-stack|creative-lipsync|creative-music`)
  does **not** stop (a) `vllm-coding` — the AI-1 container that binds the **same :8000**,
  `restart: unless-stopped`; if it were running when agent-mode fires, the agent vLLM
  fails to bind :8000 → conflict/OOM; nor (b) the post-06-22 lipsync tiers
  `creative-latentsync` / `creative-hallo2` / `creative-musetalk` (GPU-capable, lazy VRAM —
  a lipsync job firing mid-agent-mode could OOM the card). These didn't bite this run
  (`vllm-coding` was already exited; lipsync stopped pre-flight), so the shakedown stands,
  but the stop-list should add `vllm-coding` (the same one-liner AI-1's note already calls
  out) and the three lipsync names. This is the EXECUTION-PLAN B2 "kill the OOM-from-stale-load
  bug class" item — a declarative `mode.sh` with a complete GPU-tenant stop-list would close it.
- GPU etiquette: ran in the owner-freed exclusive window; stopped only what this task
  started; card returned to free at end (see card-state note in the session record).

## Recommended order
1. **Benchmark sweep** of the 9 built-but-unmeasured workflows (cheap, high git-value)
2. **E4** — forensic bridge end-to-end (the differentiator)
3. **E1e** — Shapeshifter with the SAM3 video mask (same fix as E1c, now available)
4. Parked items only if a concrete client need appears

## Drift repair investigation (2026-06-14) — diagnosed, NOT blind-fixed

Investigated each drifted workflow for a safe fix. Verdict: none are quick edits.
- **FLUX.1 Dev**: ModelSamplingFlux inputs UNCHANGED, but its internal `.patch()`
  signature changed in ComfyUI core → needs a ComfyUI/node version fix, not a
  workflow edit.
- **Wan 2.1 draft / Hunyuan T2V+I2V**: nodes RENAMED with different I/O
  (HunyuanVideoModelLoader→HunyuanVideo15*, EmptyWanLatentVideo→Wan22ImageToVideoLatent)
  → each needs the graph rebuilt against the new nodes + visual QA.
- **A drifted FLUX image workflow**: dangling CLIP link from a deleted community LoRA
  → rebuild on Chroma or retire. **RESOLVED 2026-06-22 (CRE-5):** Chroma is now
  A/B-verified and kept, scoped to the soft/artistic niche (see the Chroma-vs-LUSTIFY
  A/B above), so the rebuild target is settled — Chroma, used for soft/editorial looks,
  with LUSTIFY the human-realism default.

DECISION: not shipping blind rebuilds (could pass validation but render garbage —
exactly what the brand promises it won't do). These need a focused rebuild
session with frame-by-frame QA. Tracked as ⚠️ in the catalogue until then. The
5 working workflows + Vanisher + Crystalforge cover the deliverable pipeline.
