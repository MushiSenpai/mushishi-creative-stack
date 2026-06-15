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
| **Goldsmith** (FLUX.2 4B keyframe) | 2 | 6s, 11.2GB, 1024² | clean |
| **Wan 2.2 T2V** (two-sampler MoE) | 2 | 483s, 20GB, 720p 81fr | clean; confirms ~497s est |
| **Wan 2.2 I2V** (keyframe animation) | 2 | 502s, 20GB, 720p 81fr | clean; confirms ~506s est |
| **Silkmotion** (RIFE interpolation) | 6 | 12s, 3.5GB, →60fps | clean; confirms ~8.3s |
| **Shapeshifter** (Wan2.1 VACE + SAM3 video) | 4.5 | 802s, 20.6GB | clean; SAM3-video mask works |
| **Vanisher** (VOID removal) | 4.5 | 149-189s, 27GB | clean on representative footage (E1d) |
| **Crystalforge** (SeedVR2 4K) | 6 | 586s, 25.7GB | clean upscale |
| **dreamforge / quickening / sharpscale** (Hunyuan 1.5 T2V/I2V/SR) | 3 | 16s / 21s / 73s | render-verified 2026-06-15 |
| **Maestro** (idea → cinematic clip + score) | 7 | 512s, ~18GB | end-to-end, render-verified 2026-06-15; clips are 3.375s (Wan I2V frame cap) |
| Nemotron LLM | — | 276 tok/s sustained, knee@8 concurrent (728 agg) | stress-tested 2026-06-13 |
| Score (ACE-Step) | audio | ACE-Step 3.5B: 20s instrumental score in ~8s | used by Maestro pipeline |

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
| FLUX.1 Dev commercial (**Ledger**) | `ModelSamplingFlux.patch()` kwarg | ✅ rebuilt |

Method: adapt the pack's own example template (don't edit-in-place) + a reusable
litegraph→API converter (`scripts/ui2api_render.py`) + render-and-eye-verify each.
Lesson logged: pin custom-node versions or treat re-validation as routine maintenance.

## ⬜ Defined but not built / parked

- **Flashfire** (FLUX.2 4B *distilled*) — needs the distilled model file
- **RTX VSR** — fast preview upscaler, not yet installed (calibrate vs SeedVR2)
- **LBM relight** — relight inserted elements to match plate; pairs with the
  forensic consistency map
- **The four T4 full-pipelines** (daily / cinematic / screenplay→scene /
  commercial) — chains of the above; benchmark the links first, then the chain

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
  → rebuild on Chroma or retire.

DECISION: not shipping blind rebuilds (could pass validation but render garbage —
exactly what the brand promises it won't do). These need a focused rebuild
session with frame-by-frame QA. Tracked as ⚠️ in the catalogue until then. The
5 working workflows + Vanisher + Crystalforge cover the deliverable pipeline.
