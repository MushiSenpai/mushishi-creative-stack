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
| Nemotron LLM | — | 276 tok/s sustained, knee@8 concurrent (728 agg) | stress-tested 2026-06-13 |
| Avatar / YuE audio | audio | see audio repo | partial/measured |

## ❌ DRIFTED — broke from ComfyUI upstream changes (sweep 2026-06-13)

The sweep's big finding: 4 of 9 "tested weeks ago" workflows no longer run.
"Tested-and-working" has a shelf life without pinned node versions.

| Workflow | Failure |
|---|---|
| FLUX.1 Dev commercial | `ModelSamplingFlux.patch()` unexpected kwarg — node API changed |
| Wan 2.1 draft | `Node 'Video Latent' has no class_type` — custom node renamed/removed |
| HunyuanVideo 1.5 T2V | 4 nodes missing class_type |
| HunyuanVideo 1.5 I2V | 5 nodes missing class_type |

**To-do:** re-validate/rebuild the 4 drifted workflows; pin custom-node versions.
Technique that found it fast: `app.graphToPrompt()` headlessly validates node
availability without rendering — run it across the whole library periodically.

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
