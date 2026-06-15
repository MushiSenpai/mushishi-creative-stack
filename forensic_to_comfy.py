#!/usr/bin/env python3
"""
forensic_to_comfy.py — Read forensic machine payload → drive ComfyUI via API.

Reads forensic_machine_payload.json from a job directory, builds a ComfyUI
API-format prompt payload for VOID (Vanisher) or VACE (Shapeshifter) workflows,
posts it to the ComfyUI /prompt endpoint, and polls /history to track completion.

This is an external orchestration script — NOT a ComfyUI custom node. It keeps
the forensic bridge cleanly separated from ComfyUI internals.

Usage:
    python3 forensic_to_comfy.py <job_id> --workflow [void|vace] --input <video_path>
    python3 forensic_to_comfy.py <job_id> --workflow void --input /path/to/clip.mp4
    python3 forensic_to_comfy.py <job_id> --workflow vace --input /path/to/clip.mp4
    python3 forensic_to_comfy.py <job_id> --workflow void --input /path/to/clip.mp4 --anchor-mode i2v
    python3 forensic_to_comfy.py <job_id> --workflow void --input /path/to/clip.mp4 --anchor-mode flux

Anchor modes (Step 3.9):
    i2v   — Use hero frame from forensic bundle as locked first frame for I2V (primary path)
    flux  — Generate FLUX.2 keyframe with locked seed → feed into I2V (secondary path, no real plate)
    none  — No pixel anchor (default for editing workflows that use existing plate)

Requirements:
    - ComfyUI running at COMFYUI_URL (default: http://localhost:8188)
    - Vanisher workflow JSON loaded in ComfyUI (for --workflow void)
    - Shapeshifter workflow JSON loaded in ComfyUI (for --workflow vace)
    - forensic_machine_payload.json present in job directory
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


FORENSIC_BASE = Path("/data/ai/08-portfolio/forensic")
COMFYUI_URL = "http://localhost:8188"
POLL_INTERVAL_SEC = 5
POLL_TIMEOUT_SEC = 1800  # 30 min max

# ---------------------------------------------------------------------------
# Workflow node IDs — update these to match the actual node IDs in your
# Vanisher and Shapeshifter workflow JSONs. These are placeholder defaults.
#
# HOW TO FIND: Open the workflow in ComfyUI, right-click each node → "Copy ID"
# Then replace the values below.
# ---------------------------------------------------------------------------

VOID_NODE_IDS = {
    # Real IDs from the API export of t45-void-vanisher (workflows/void.json,
    # extracted from /history 2026-06-12 — see EXECUTION-PLAN E1b). Subgraph
    # nodes flatten to colon-joined IDs.
    # UPDATED 2026-06-13 (E4): void.json is now the E1c SAM3 *video* pipeline.
    # SAM3 moved from image-node 167:149:78 to video-node sam_seg (key=text_prompt,
    # not text). LoadVideo input key is "file" not "video".
    "sam3_text_prompt":     "sam_seg",           # SAM3VideoSegmentation (key: text_prompt)
    "void_fill_prompt":     "167:6",            # VOID fill prompt (CLIPTextEncode)
    "load_video":           "169",              # core LoadVideo node (key: file)
    "save_video":           "168",              # core SaveVideo node
}

VACE_NODE_IDS = {
    "sam3_text_prompt":     "sam3_prompt",      # SAM3 text prompt input node
    "vace_edit_prompt":     "vace_prompt",      # VACE edit prompt
    "load_video":           "load_video",       # VHS LoadVideo node
    "save_video":           "save_video",       # VHS SaveVideo node
}

# ---------------------------------------------------------------------------
# ComfyUI API helpers
# ---------------------------------------------------------------------------

def api_get(endpoint: str) -> dict:
    url = f"{COMFYUI_URL}{endpoint}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def api_post(endpoint: str, data: dict) -> dict:
    url = f"{COMFYUI_URL}{endpoint}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def queue_prompt(prompt_payload: dict) -> str:
    """Submit prompt to ComfyUI queue. Returns prompt_id."""
    result = api_post("/prompt", {"prompt": prompt_payload})
    prompt_id = result.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI rejected prompt: {result}")
    return prompt_id


def poll_completion(prompt_id: str) -> dict:
    """Poll /history until prompt_id completes. Returns history entry."""
    print(f"[comfy] Queued prompt_id: {prompt_id}")
    deadline = time.time() + POLL_TIMEOUT_SEC
    dots = 0
    while time.time() < deadline:
        try:
            history = api_get(f"/history/{prompt_id}")
        except urllib.error.URLError as e:
            print(f"\n[comfy] Poll error: {e} — retrying...")
            time.sleep(POLL_INTERVAL_SEC)
            continue

        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {})
            if status.get("completed"):
                print(f"\n[comfy] ✅ Complete — status: {status.get('status_str', 'done')}")
                return entry
            if status.get("status_str") == "error":
                print(f"\n[comfy] ❌ Error in execution")
                return entry

        # Progress dots
        print(".", end="", flush=True)
        dots += 1
        if dots % 12 == 0:
            print(f" [{int(time.time() % 1000)}s]")
        time.sleep(POLL_INTERVAL_SEC)

    raise TimeoutError(f"Prompt {prompt_id} did not complete within {POLL_TIMEOUT_SEC}s")


def get_output_files(history_entry: dict) -> list[str]:
    """Extract output file paths from a completed history entry."""
    outputs = []
    for node_output in history_entry.get("outputs", {}).values():
        for key in ("videos", "images", "gifs"):
            for item in node_output.get(key, []):
                if "filename" in item:
                    subfolder = item.get("subfolder", "")
                    fname = item["filename"]
                    outputs.append(f"{subfolder}/{fname}" if subfolder else fname)
    return outputs


# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------

def set_node_input(prompt: dict, node_id: str, input_key: str, value) -> None:
    """Set a specific input on a node in the ComfyUI prompt dict."""
    if node_id not in prompt:
        print(f"[comfy] ⚠️  Node '{node_id}' not found in workflow — skipping input '{input_key}'")
        return
    inputs = prompt[node_id].get("inputs", {})
    inputs[input_key] = value
    prompt[node_id]["inputs"] = inputs


def build_void_payload(
    workflow: dict,
    payload: dict,
    input_video: str,
) -> dict:
    """
    Inject forensic machine payload into the VOID (Vanisher) workflow.

    Modifies:
    - SAM3 text prompt  → payload["sam3_mask_prompts"]["remove"][0]
    - VOID fill prompt  → payload["void_fill_prompt"]
    - LoadVideo path    → input_video
    """
    prompt = dict(workflow)  # shallow copy of top-level nodes

    sam3_prompts = payload.get("sam3_mask_prompts", {})
    remove_list = sam3_prompts.get("remove", [])
    sam3_text = remove_list[0] if remove_list else ""

    # E1c video pipeline keys: SAM3VideoSegmentation uses "text_prompt"; LoadVideo
    # uses "file" and wants the basename present in the ComfyUI container input/.
    from pathlib import Path as _P
    set_node_input(prompt, VOID_NODE_IDS["sam3_text_prompt"], "text_prompt", sam3_text)
    set_node_input(prompt, VOID_NODE_IDS["void_fill_prompt"], "text", payload.get("void_fill_prompt", ""))
    set_node_input(prompt, VOID_NODE_IDS["load_video"], "file", _P(input_video).name)

    print(f"[comfy/void] SAM3 remove prompt: {sam3_text[:80]}")
    print(f"[comfy/void] VOID fill prompt:   {payload.get('void_fill_prompt', '')[:80]}")
    return prompt


def build_vace_payload(
    workflow: dict,
    payload: dict,
    input_video: str,
) -> dict:
    """
    Inject forensic machine payload into the VACE (Shapeshifter) workflow.

    Modifies:
    - SAM3 text prompt  → payload["sam3_mask_prompts"]["remove"][0]
    - VACE edit prompt  → payload["vace_fields"]["edit_prompt"]
    - LoadVideo path    → input_video
    """
    prompt = dict(workflow)

    sam3_prompts = payload.get("sam3_mask_prompts", {})
    remove_list = sam3_prompts.get("remove", [])
    sam3_text = remove_list[0] if remove_list else ""

    vace = payload.get("vace_fields", {})
    edit_prompt = vace.get("edit_prompt", "")

    set_node_input(prompt, VACE_NODE_IDS["sam3_text_prompt"], "text", sam3_text)
    set_node_input(prompt, VACE_NODE_IDS["vace_edit_prompt"], "text", edit_prompt)
    set_node_input(prompt, VACE_NODE_IDS["load_video"], "video", input_video)

    print(f"[comfy/vace] SAM3 prompt:   {sam3_text[:80]}")
    print(f"[comfy/vace] Edit prompt:   {edit_prompt[:80]}")
    return prompt


# ---------------------------------------------------------------------------
# Anchor mode (Step 3.9)
# ---------------------------------------------------------------------------

def apply_anchor_i2v(prompt: dict, payload: dict, job_dir: Path) -> dict:
    """
    Path A — I2V real-first-frame anchor.
    Extracts hero frame from the forensic bundle as a reference image.
    The I2V workflow takes it as the locked first frame.
    """
    # Look for a hero frame saved by the analyzer (convention: hero_frame.jpg/png)
    candidates = list(job_dir.glob("hero_frame.*"))
    if not candidates:
        # Fall back to any extracted frame in the job dir
        candidates = list(job_dir.glob("frame_*.jpg")) + list(job_dir.glob("frame_*.png"))

    if not candidates:
        print("[anchor/i2v] ⚠️  No hero frame found in job dir — I2V anchor skipped.")
        print("[anchor/i2v]    Extract the hero frame manually and save as hero_frame.jpg")
        return prompt

    hero_frame = str(candidates[0].resolve())
    print(f"[anchor/i2v] Locking first frame: {hero_frame}")

    # Set the reference image input on the I2V clip_vision node
    # Node ID "i2v_ref_image" must exist in the workflow — update VOID/VACE_NODE_IDS if needed
    set_node_input(prompt, "i2v_ref_image", "image", hero_frame)
    return prompt


def apply_anchor_flux(prompt: dict, payload: dict) -> dict:
    """
    Path B — FLUX keyframe anchor via IP-Adapter.
    Generates a FLUX.2 keyframe with locked seed → feeds into I2V via clip_vision_h.
    Secondary path when no real plate exists.
    """
    constraints = payload.get("generation_constraints", {})
    locked_seed = constraints.get("locked_seed")

    if locked_seed is None:
        # Generate a deterministic seed from job_id hash
        import hashlib
        job_id = payload.get("job_id", "unknown")
        locked_seed = int(hashlib.md5(job_id.encode()).hexdigest()[:8], 16)
        print(f"[anchor/flux] No locked_seed in payload — derived seed: {locked_seed}")

    print(f"[anchor/flux] FLUX keyframe with locked seed: {locked_seed}")

    # Set seed on the FLUX KSampler node
    set_node_input(prompt, "flux_ksampler", "seed", locked_seed)
    # Set colour grade prompt if available
    grade = constraints.get("colour_grade_fingerprint", "")
    if grade:
        set_node_input(prompt, "flux_positive_prompt", "text_append",
                       f" Colour grade: {grade}.")
    return prompt


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_workflow(workflow_name: str) -> dict:
    """Load a ComfyUI workflow JSON from the workflows directory."""
    workflow_dirs = [
        Path("/data/ai/01-workspace/comfyui/user/default/workflows"),
    ]
    search_names = [
        f"{workflow_name}.json",
        f"t4-{workflow_name}.json",
        f"t3-{workflow_name}.json",
        f"t2-{workflow_name}.json",
    ]
    for d in workflow_dirs:
        for name in search_names:
            p = d / name
            if p.exists():
                print(f"[comfy] Loading workflow: {p}")
                with open(p) as f:
                    return json.load(f)

    raise FileNotFoundError(
        f"Workflow '{workflow_name}' not found in {workflow_dirs}.\n"
        f"Searched for: {search_names}\n"
        f"Export the workflow from ComfyUI as API JSON and save to the workflows directory."
    )


def main():
    parser = argparse.ArgumentParser(description="Forensic bundle → ComfyUI execution")
    parser.add_argument("job_id", help="Job ID or path to forensic job directory")
    parser.add_argument("--workflow", required=True, choices=["void", "vace"],
                        help="Which editing workflow to drive (void=Vanisher, vace=Shapeshifter)")
    parser.add_argument("--input", required=True, metavar="VIDEO_PATH",
                        help="Path to input video clip")
    parser.add_argument("--anchor-mode", choices=["i2v", "flux", "none"], default="none",
                        help=(
                            "Pixel anchor for generation tier: "
                            "i2v=real first frame (primary), "
                            "flux=FLUX keyframe via IP-Adapter (secondary), "
                            "none=no anchor (default, for editing existing plate)"
                        ))
    parser.add_argument("--workflow-file", metavar="PATH",
                        help="Explicit path to workflow JSON (overrides auto-search)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Build payload and print it without submitting to ComfyUI")
    args = parser.parse_args()

    # Resolve job directory
    job_dir = Path(args.job_id)
    if not job_dir.is_absolute():
        job_dir = FORENSIC_BASE / args.job_id
    if not job_dir.exists():
        print(f"[comfy] ❌ Job directory not found: {job_dir}")
        sys.exit(1)

    # Load machine payload
    payload_path = job_dir / "forensic_machine_payload.json"
    if not payload_path.exists():
        print(f"[comfy] ❌ forensic_machine_payload.json not found in {job_dir}")
        print(f"[comfy]    Run forensic_converter.py {args.job_id} first.")
        sys.exit(1)
    with open(payload_path) as f:
        payload = json.load(f)

    sv = payload.get("schema_version")
    if sv != "1.0":
        print(f"[comfy] ❌ Payload schema_version '{sv}' != '1.0'. Re-run converter.")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"Forensic → ComfyUI  |  Job: {payload['job_id']}  |  Workflow: {args.workflow}")
    print(f"Input video: {args.input}")
    print(f"Anchor mode: {args.anchor_mode}")
    print(f"{'='*70}\n")

    # Load workflow
    if args.workflow_file:
        with open(args.workflow_file) as f:
            workflow = json.load(f)
        print(f"[comfy] Loaded workflow from: {args.workflow_file}")
    else:
        # API-format exports: void.json (VOID/Vanisher) / vace.json (VACE/Shapeshifter)
        wf_name = "void" if args.workflow == "void" else "vace"
        workflow = load_workflow(wf_name)

    # Build prompt payload
    if args.workflow == "void":
        prompt = build_void_payload(workflow, payload, args.input)
    else:
        prompt = build_vace_payload(workflow, payload, args.input)

    # Apply pixel anchor
    if args.anchor_mode == "i2v":
        prompt = apply_anchor_i2v(prompt, payload, job_dir)
    elif args.anchor_mode == "flux":
        prompt = apply_anchor_flux(prompt, payload)

    if args.dry_run:
        print("\n[comfy] DRY RUN — payload (first 2000 chars):")
        print(json.dumps(prompt, indent=2)[:2000])
        return

    # Submit and poll
    try:
        prompt_id = queue_prompt(prompt)
        history = poll_completion(prompt_id)
        outputs = get_output_files(history)
        if outputs:
            print(f"[comfy] Output files:")
            for f in outputs:
                print(f"          {f}")
        else:
            print("[comfy] No output files found in history — check ComfyUI UI for results.")
    except urllib.error.URLError as e:
        print(f"[comfy] ❌ Cannot reach ComfyUI at {COMFYUI_URL}: {e}")
        print("[comfy]    Is ComfyUI running? Check: docker ps | grep creative-comfyui")
        sys.exit(1)


if __name__ == "__main__":
    main()
