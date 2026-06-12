# Workflow Coverage & Benchmark Status

Honest map of every workflow in the stack: what's **measured** (real numbers in
`benchmarks.csv`), what's **built but unmeasured**, and what's **defined but not
built**. The goal: even where the workflow JSON isn't published, the *measured
capability* is — "this produces X in Y seconds at Z GB" is itself the proof.

Hardware: RTX 5090 32GB · Ryzen 9 9900X3D · 128GB DDR5 · Ubuntu 24.04 · CUDA 13.2.
All numbers are on-box measurements, indicative not guaranteed.

## ✅ Measured — real numbers committed

| Workflow | Tier | Result | Verdict |
|---|---|---|---|
| **Vanisher** (VOID object removal) | 4.5 edit | 149–189s, ~27GB, 6s clip | **Clean on representative footage (E1d)**; ghost only on worst-case low-light/occluded clips |
| **Crystalforge** (SeedVR2 4K) | 6 finish | 586s, 25.7GB, 672×384→1890×1080 | Clean upscale, no artifacts |
| Avatar chain (clone→TTS→LatentSync) | audio | TTS 25s + lipsync 280s | Gross sync correct; lip-interior artifacts at full-frame (social-OK) |
| YuE music | audio | 2m56s, ~16GB, 15s song | Works; mono vocoder limit |

## 🟡 Built + tested, NOT yet benchmarked — the sweep backlog

These are confirmed working (per the v1.4 catalogue) but have no committed
numbers. **Highest-value cheap win: one render each, record, commit.** Catalogue
gives indicative figures (italic) to confirm against.

| Workflow | Tier | Indicative | Why it matters |
|---|---|---|---|
| **Goldsmith** (FLUX.2 4B base keyframe) | 2 | *~3.3s, 9GB, 1024²* | The keyframe that anchors every generated shot |
| **Wan 2.2 T2V** (two-sampler MoE) | 2 | *~497s, 81fr, 720p* | Primary text→video; the days-long crystalline-bug fix lives here |
| **Wan 2.2 I2V** | 2 | *~506s, 81fr* | Animate a Goldsmith keyframe |
| **HunyuanVideo 1.5 T2V** fp16 | 3 | *~8–12min, 720p* | Cinema-grade hero clips |
| **HunyuanVideo 1.5 I2V** fp8 | 3 | *65fr, 720p, LLM-concurrent* | Cinema keyframe animation |
| **Silkmotion** (RIFE 60fps) | 6 | *~8.3s* | Fluid-motion finishing pass |
| **Shapeshifter** (Wan 2.1 VACE edit) | 4.5 | *~14GB* | Masked object/clothing swap, reframe — SAM3-video-mask fix lives here |
| **Wan 2.1 1.3B draft** | 1 | *~4min, 480p* | Cheap motion test before 14B commit |
| **FLUX.1 Dev** (Apache-2.0 commercial) | 2 | *~15s, 1024²* | License-clean client stills |

## ⬜ Defined but not built / parked

- **Flashfire** (FLUX.2 4B *distilled*) — needs the distilled model file
- **RTX VSR** — fast preview upscaler, not yet installed (calibrate vs SeedVR2)
- **LBM relight** — relight inserted elements to match plate; pairs with the
  forensic consistency map
- **The four T4 full-pipelines** (daily / cinematic / screenplay→scene /
  commercial) — chains of the above; benchmark the links first, then the chain

## 🔬 The untested differentiator — forensic bridge (priority)

`forensic_analyzer.py` (Nemotron 3-pass → JSON) → `forensic_converter.py` →
`forensic_to_comfy.py` → drives Vanisher/Shapeshifter via the ComfyUI API.
**Built and now runnable** (node IDs were placeholders, corrected 2026-06-12),
but **never run end-to-end** — forensic JSON has never actually conditioned a
removal job. This is the stack's core thesis (dense scene description prevents
diffusion hallucination) and its most valuable untested path. → **E4.**

## Recommended order
1. **Benchmark sweep** of the 9 built-but-unmeasured workflows (cheap, high git-value)
2. **E4** — forensic bridge end-to-end (the differentiator)
3. **E1e** — Shapeshifter with the SAM3 video mask (same fix as E1c, now available)
4. Parked items only if a concrete client need appears
