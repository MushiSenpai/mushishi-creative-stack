# Creative Stack — Problems & Solutions Glossary
> [!note] Public edition
> This is the public edition of the working spec. A private Tier 5 addendum
> (model-restriction research) is omitted. Everything else is as-built.


*A field log of every real problem hit while building the RTX 5090 creative stack, and how
each was solved. Each entry has a **technical** account (for engineering write-ups) and a
**plain-language** version (for general-audience posts). Use freely as blog source material.*

> Hardware context: RTX 5090 32GB · SM_120 Blackwell · CUDA 13.2 · Ubuntu 24.04 · multi-stack
> box (creative + sovereign/Nemotron + audio). ComfyUI in Docker, vLLM for local LLMs.

---

## 1. The Wan 2.2 "crystalline shadow" video bug — the days-long one

**Technical:** Wan 2.2 14B is a Mixture-of-Experts model split into a high-noise expert
(composition/motion) and a low-noise expert (detail/texture). The workflow loaded *both* expert
files in the model loader, which made it *look* correct, but ran them through a **single
sampler**. A single sampler cannot transition between the two experts — only the high-noise pass
effectively ran, so the detail pass never happened. Output showed a characteristic crystalline /
blurry-moving-shadow artifact. The fix is a **two-sampler chain**: high-noise sampler (steps
0→N/2) → latent → low-noise sampler (steps N/2→N) → VAE decode, with the step budget split
between them. A documented gotcha: naively chaining a second sampler can throw a start/end-step
type error and feed noise to the second stage, so the wiring (start_step/end_step, latent
hand-off) must follow the current Kijai/native example exactly.

**Plain-language:** The video model is really two specialists working in sequence — one that
blocks out the scene and motion, and one that paints in the fine detail. Our setup had both
specialists in the room but only let the first one work, so every video came out half-finished:
shimmery, crystalline shadows that wouldn't settle. The fix was making them work as a relay —
first specialist hands off to the second — instead of trying to do it all in one pass. This was
the bug that cost days, and it turned out to be architectural, not a settings tweak.

**Lesson:** "Both models loaded" ≠ "both models used." For MoE video models, verify the *sampler
structure*, not just the loader.

---

## 2. The FLUX 4B "base vs distilled" filename trap

**Technical:** FLUX.2 klein ships a base 4B and a distilled 4B. The distilled (fast, 4-step,
CFG 1.0) is named `flux-2-klein-4b-fp8.safetensors`; the base (quality, ~20-step, CFG 3.5) has
"base" in the name: `flux-2-klein-base-4b-fp8.safetensors`. A workflow titled/commented
"distilled, 4 steps" but assumed to be running the base model created a false diagnosis — it was
*actually* the distilled model all along, so 4 steps was correct. The real cause of any image
inconsistency was the randomized seed, not a step/model mismatch. (Documented honestly because
the first diagnosis here was wrong and had to be corrected mid-build.)

**Plain-language:** Two versions of the same image model look almost identical by filename — one
is the "quick sketch" version, one is the "refined" version, and the only difference in the name
is the word "base." We briefly thought we had the refined one running too fast, when really we
had the quick one running exactly right. The actual cause of inconsistent images was just that
the random seed was on. Lesson: read model filenames *very* carefully, and lock your seed before
blaming anything else.

**Lesson:** Lock the seed first when diagnosing "inconsistent" generative output — randomness
masquerades as bugs. And verify which model variant you actually have on disk.

---

## 3. `/var` filling up and `docker system prune` deleting ComfyUI

**Technical:** Docker's storage (`/var/lib/docker`) sat on the small OS drive. Images from
multiple stacks filled it. Running `docker system prune -a` removed any image not attached to a
*running* container — so the stopped ComfyUI image was repeatedly deleted, forcing rebuilds. Root
cause was disk layout + a too-aggressive prune habit, not anything in ComfyUI.

**Plain-language:** Every time the system drive filled up, the cleanup command we ran was
deleting our main video app to free space — because the app wasn't running at that moment, the
cleanup thought it was junk. We kept rebuilding the same thing over and over without realizing
the cleanup was the culprit.

**Lesson:** Never use `docker system prune -a` on a multi-project box. Use `docker image prune`
(dangling only) and `docker builder prune` (cache). And put Docker's storage on your big drive.

---

## 4. Migrating Docker `data-root` without breaking three stacks

**Technical:** Moved `/var/lib/docker` → `/data/ai/docker-data` via: stop all stacks → stop
Docker → `rsync -aP` the full tree (preserves named volumes like `trtllm-pip-cache`) → add
`"data-root"` to daemon.json → restart → verify `Docker Root Dir` + image/volume parity → only
then rename old dir, delete after a confidence period. The trap: daemon.json already held the
nvidia runtime block; *overwriting* it instead of *adding* the data-root key would have killed
GPU passthrough for all three stacks. Stacks needed no doc changes because all real data lives in
`/data/ai/` bind-mounts, not Docker-managed volumes.

**Plain-language:** We moved Docker's entire storage to the big drive so it'd never fill up again.
The risky part: one shared config file controls GPU access for *all* our projects, so a careless
edit would have blinded the graphics card for everything at once. We added one line instead of
replacing the file, copied everything (never deleted first), and verified nothing was lost before
cleaning up. Migration succeeded with zero data loss.

**Lesson:** On shared infra, identify the load-bearing config (here: the nvidia runtime block) and
*add* to it, never overwrite. Copy-verify-then-delete, never delete-first.

---

## 5. The multi-stack boundary — not nuking the neighbors

**Technical:** One box runs creative + sovereign/Nemotron + audio stacks, each with its own
containers, vLLM sessions, ports, and compose files. The risk: a broad `docker stop`, a
wildcard grep matching the wrong vLLM image, or a `docker compose down` in a shared dir taking out
the Nemotron or audio stack. Mitigation: a discover-and-confirm rule — inventory all containers,
have the operator label creative-vs-other, then act only on named creative containers, never
broadly.

**Plain-language:** The same computer runs several separate AI projects. A sloppy "clean up" or
"restart" command could accidentally shut down a totally different project mid-work. The rule we
built: always list everything first, confirm which belongs to which project, and only touch the
ones you mean to — by exact name, never with a broad sweep.

**Lesson:** On a multi-tenant machine, every destructive command needs an explicit allowlist.
Discovery + human confirmation beats a hardcoded guess.

---

## 6. The four WanVideoWrapper VRAM-management patches

**Technical:** Getting Wan VACE (Shapeshifter) running under WanVideoVRAMManagement required four
surgical fixes to the third-party node's source (pre-existing bugs in the `vram_management_args`
path only): (1) call `load_weights()` before `enable_vram_management()` to materialize meta-device
tensors; (2) set `module_config.onload_device` to CPU so forward always casts to CUDA; (3) move
non-AutoWrapped params (e.g. modulation) to CUDA after wrapping; (4) make `AutoWrappedModule.
forward` use in-place `.to()` instead of deepcopy, plus a `__getattr__` proxy so
`norm_layer.weight.dtype` works on wrapped modules.

**Plain-language:** To run the most memory-hungry editing model, we had to patch four small bugs
in someone else's code that only showed up under heavy memory-offloading. They're the kind of
fixes that work but live *on top of* the original code — so if that code ever updates, our patches
vanish and the feature silently breaks.

**Lesson — important:** Patches to third-party node source are fragile. **Document them
durably** (file, function, change, reason) so a future update doesn't silently break the feature.
This is logged here precisely so future-you knows to re-apply or upstream them.

---

## 7. VOID "Prompt has no outputs" — the subgraph trap

**Technical:** VOID's full pipeline was correctly wired *inside* a ComfyUI subgraph (node 167),
but the subgraph's VIDEO outputs fed nothing in the outer graph. ComfyUI requires at least one
`OUTPUT_NODE = True` at the top level to queue. Fix: add a native `SaveVideo` node in the outer
graph connected to the subgraph's `final_pass_2_video` output. Minimal edit, no rebuild.

**Plain-language:** The object-removal tool was fully assembled inside a sealed "black box," but we
never plugged the box's output into a "save" step — so the software refused to run, saying it had
nothing to produce. One missing connection. Added a save node, and it ran.

**Lesson:** With subgraphs, the inner wiring can be perfect while the outer graph has no terminal
output. "No outputs" almost always means a missing top-level save/preview node, not a broken graph.

---

## 8. VACE color-splotches — the unconnected mask

**Technical:** Wan VACE (Shapeshifter) first run produced random RGB patches because the VACE
Encode node's `input_masks` was unconnected — VACE ran full-frame at denoise 1.0, partially
regenerating arbitrary regions. Fix: feed a SAM3-generated mask into `input_masks` so the edit is
confined to the target region; the prompt then describes the *change* for that region only.

**Plain-language:** The "change this part of the video" tool, given no instruction about *which*
part, tried to repaint the whole frame and produced random colored blotches. Once we told it
exactly where to look (a mask), it changed only that region cleanly.

**Lesson:** Editing models (VACE, inpaint) are mask-driven. No mask = whole-frame chaos. The mask
is the instruction; the prompt only describes what the masked region becomes.

---

## 9. The `flash_attn` KeyError (the false alarm)

**Technical:** A `KeyError: 'flash_attn'` surfaced from Qwen's optional flash-attn detection.
Pre-existing and benign — flash_attn is in OPTIONAL_MODULES precisely because Qwen probes for it
and falls back (to SDPA/SageAttention) when absent. Not caused by any stack patch; cosmetic if the
model still generates.

**Plain-language:** A scary-looking error turned out to be the software politely checking whether
an optional speed-up was installed, not finding it, and carrying on fine. The error was just noise.

**Lesson:** Not every red error is a failure. Verify whether the component still *functions* before
chasing a fix — optional-dependency probes often log loudly and mean nothing.

---

## 10. SeedVR2 v2.5 + RTX VSR — keeping up with moving tools

**Technical:** SeedVR2 moved to a v2.5 4-node architecture with a new install path
(`custom_nodes/seedvr2_videoupscaler`, weights to `models/SEEDVR2`) and a renamed weight
(`seedvr2_ema_7b_fp16.safetensors`). On Blackwell: FP16 + SageAttention; **not** NVFP4 (the
community NVFP4 port failed — VAE/DiT too entangled). Separately, NVIDIA's RTX Video Super
Resolution became a real ComfyUI node (GDC 2026), invalidating an earlier "playback-only"
dismissal — now a valid fast-preview path alongside SeedVR2 as the quality finisher.

**Plain-language:** The upscaling tools changed faster than the docs. The good 4K upscaler got a
new version with different setup, and a tool we'd written off (NVIDIA's real-time upscaler) became
genuinely usable. Staying current meant re-checking assumptions we'd made only weeks earlier.

**Lesson:** In fast-moving AI tooling, last month's "right answer" expires. Re-verify model names,
install paths, and "this tool can't do X" claims against current sources before committing.

---

## 11. The reframe — generation vs editing

**Technical:** The stack was originally built for *generation* (T2V/I2V from scratch). The actual
client work — rain/object removal, reframing, VFX on shot footage — is *editing/inpainting*, a
different toolset (VOID, Wan VACE, SAM3, LBM). Netflix's open-source VOID (Apache 2.0, native
ComfyUI) landed mid-project and matched the removal use case exactly, including removing an
object's shadows/reflections/induced motion.

**Plain-language:** We realized partway through that we'd built a "make new video" studio when the
job was actually "fix existing client video." Those need different tools. A new open-source tool
from Netflix turned out to do exactly the hardest part — removing something *and* its shadow — so
the project pivoted to build around editing, not just generation.

**Lesson:** Periodically re-check that the tools match the *actual* job, not the job you assumed at
the start. The biggest course-correction came from questioning the premise.

---

## Quick-reference: problem → one-line fix

| Problem | Fix |
|---|---|
| Crystalline/shimmery Wan video | Two-sampler high→low MoE chain, split steps |
| Inconsistent images | Lock the seed first; verify model variant |
| ComfyUI image keeps vanishing | Stop `prune -a`; move Docker to big drive |
| GPU dies after a config edit | *Add* to daemon.json, never overwrite the nvidia block |
| Accidentally hitting another stack | Inventory + confirm; act by exact name only |
| Feature breaks after node update | Document third-party source patches durably |
| "Prompt has no outputs" | Add a top-level SaveVideo/output node |
| VACE color splotches | Connect a mask to input_masks |
| `flash_attn` KeyError | Ignore if model still runs (optional probe) |
| Upscaler setup "wrong" | Re-check current version/paths; FP16 not NVFP4 |
