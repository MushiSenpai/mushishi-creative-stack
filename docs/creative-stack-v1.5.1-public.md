---
tags:
  - ai/setup
  - ai/comfyui
  - ai/video
  - ai/vllm
  - ai/upscale
  - ai/interpolation
  - hardware/rtx5090
  - linux/ubuntu
  - llm/local
  - docker
  - remote-agent
status: active
created: 2026-04-25
hardware: RTX 5090 · Ryzen 9 9900X3D · 128GB DDR5 · Ubuntu 24.04
stack: vLLM · ComfyUI · FLUX.2-klein · Wan 2.2 · HunyuanVideo-1.5 · SeedVR2 · RIFE
adds: Tier 5 (unrestricted-local) integration · Tier 6 (4K60 finishing pipeline)
new_tools: SeedVR2 7B (Apache 2.0) · ComfyUI-Frame-Interpolation RIFE (MIT/Apache)
cuda_verified: "13.2 — confirmed 2026-04-25"
version: "1.5.1"
updated: 2026-06-10
changelog:
  - "v1.5.1 (2026-06-10): Status patch. KNOWN STALE: the Architecture Overview diagram shows 'Hermes Agent (cloud, always on)' — Hermes has run LOCALLY on mushishi as a systemd service (:8642) since main-stack v1.6/v1.7; the Mac is a thin client over Tailscale. Diagram rewrite pending (EXECUTION-PLAN.md task C1). Also: creative-ctl.sh GIT_BACKUP_REMOTE was a placeholder until 2026-06-10 — workflow git repo now initialized locally (branch main), remote push pending. ComfyUI :8188 LAN exposure to be closed by scripts/harden-docker-firewall.sh (run with sudo). Cross-stack priorities now tracked in ~/Documents/EXECUTION-PLAN.md."
  - "v1.5 (2026-06-08): Phases 3-4-5 executed. Forensic bridge built + connected (forensic_analyzer schema-stamped, forensic_converter.py + forensic_to_comfy.py created). NVFP4 FLUX.2 Klein 4B+9B downloaded; t1-flux2-9b-flashfire.json added. RIFE + SeedVR2 v2.5 installed; SeedVR2 weights relocated to /data/ai/02-models/SEEDVR2/ (DiT + VAE). Finishing folders created. MAJOR FIX: Shapeshifter SAM3 was image-mode (single [1,H,W] mask) causing tensor-dimension mismatch with VACE — rebuilt to SAM3 video pipeline (LoadSAM3Model → SAM3VideoSegmentation → SAM3Propagate → SAM3VideoOutput) producing per-frame [N,H,W] masks. SAM3 custom node identified as PozzettiAndrea/ComfyUI-SAM3. VOID confirmed working on real footage (blackboard removed via 'writing board' SAM3 label). RTX VSR + LBM install still pending."
  - "v1.4 (2026-05-28): All six named workflows built + tested (Flashfire, Goldsmith, Silkmotion, Crystalforge, Vanisher, Shapeshifter). Wan 2.2 two-sampler fix confirmed (no crystalline artifact). Docker data-root migrated to /data/ai/docker-data. Four WanVideoWrapper VRAM patches applied + documented. Silkmotion set to 60fps. Added Problems & Solutions Glossary. Confirmed node names + params."
  - "v1.3 (2026-05-24): Added Editing Tier (Tier 4.5 — VOID/VACE/SAM3/relight) for client post-production. Corrected Wan 2.2 I2V to the required two-sampler high→low design. SeedVR2 updated to v2.5 + SageAttention (no NVFP4). NVFP4 FLUX.2 Klein variants added. RTX VSR re-evaluated (no longer playback-only). Wan open-weights ceiling = 2.2 (2.5/2.6 are commercial). Audio = on-demand stage. Web-verified."
---

# Production AI Creative Stack — Final Architecture
> [!note] Public edition
> This is the public edition of the working spec. A private Tier 5 addendum
> (model-restriction research) is omitted. Everything else is as-built.


> [!info] Version 1.3 — Editing reframe
> The client work (rain/object removal, reframing, VFX) is video **editing**, not generation.
> v1.3 adds a dedicated **Editing Tier** above the generation tiers, corrects the Wan 2.2 I2V
> architecture, and refreshes the finishing stack to 2026 reality. Generation tiers (1–4) are
> unchanged. All render-time / VRAM figures remain **calibrate-on-box** — published numbers are
> mostly 24GB/4090-class.

> [!success] Version 1.4 — all six workflows validated (2026-05-28)
> The six named workflows are built and tested: ⚡ Flashfire (distilled 4B, seed-locked) · 🔨
> Goldsmith (base 4B, 20-step) · 🪶 Silkmotion (RIFE → 60fps) · 💎 Crystalforge (SeedVR2 → 4K,
> visually confirmed) · 🫥 Vanisher (VOID removal — confirmed it strips an object AND its
> reflection) · 🦎 Shapeshifter (Wan 2.1 VACE masked edit). The days-long Wan 2.2 crystalline-shadow
> bug is fixed via the two-sampler MoE chain. Docker storage migrated to the 1.6TB drive. See the
> companion **Problems & Solutions Glossary** for the full build log of issues + fixes.

> [!success] Version 1.5 — forensic bridge connected, Tier 5/6 built, SAM3 video-mode fixed (2026-06-08)
> The forensic bridge is built and wired: `forensic_analyzer.py` (schema-stamped, pixel-dense
> Pass 2/3) → `forensic_converter.py` (human-readable → machine payload) → `forensic_to_comfy.py`
> (drives VOID/VACE via the ComfyUI API). Tier 5 Wan unrestricted-local workflows built with the
> distillation LoRA stack. Tier 6 (RIFE + SeedVR2 v2.5) installed. The big fix this round: a
> SAM3 image-mode vs video-mode mismatch was producing single-frame masks that crashed VACE on a
> tensor-dimension error — Shapeshifter now uses the four-node SAM3 video pipeline for true
> per-frame masks. VOID confirmed on real lab footage. See the updated Glossary for the full log.

> [!warning] Guide Corrected — Read This First
> The previous guide had a **critical error** in the drive layout. It instructed you to partition and format a drive for `/models` — but that drive is actually your **OS drive** (nvme1n1 hosts `/`, `/home`, `/var`). Following that instruction would have wiped Ubuntu.
> 
> Your actual layout:
> - **nvme1n1** → OS drive: `/` (200G), `/var` (200G), `/home` (1.3T), `[SWAP]` (131G), `/tmp`
> - **nvme0n1** → Data drive: `/boot/efi`, `/data` (1.5T) ← **your AI workspace**

> [!tip] Where Everything Lives
> All AI work lives under **`/data/ai/`** — your existing, already-organised workspace. Nothing gets installed anywhere else.

> [!tip] CUDA 13.2 Already Verified ✅
> `nvcc --version` confirms CUDA 13.2, build March 2026. **Phase 1.1 is complete — skip straight to Phase 1.2.**

---

## Your Actual Drive Layout

```
nvme0n1 (1.8T) — DATA DRIVE
├── nvme0n1p1   200M    /boot/efi
├── nvme0n1p2    16M    (BIOS boot)
├── nvme0n1p3   292G    (reserved/unallocated)
├── nvme0n1p4   735M    (reserved)
└── nvme0n1p5   1.5T    /data  ← ALL AI WORK HERE

nvme1n1 (1.8T) — OS DRIVE  ← DO NOT TOUCH
├── nvme1n1p1   200G    /
├── nvme1n1p2   200G    /var
├── nvme1n1p3   131G    [SWAP]
├── nvme1n1p4   1.3T    /home
└── nvme1n1p5   834M    /tmp
```

---

## Target Folder Structure at /data/ai/

This maps your existing folders to their new roles. Nothing gets deleted — only expanded.

```
/data/ai/
├── 01-workspace/
│   ├── comfyui/          ← ComfyUI installs here (new)
│   ├── llama.cpp/        ← keep for GGUF experiments (existing)
│   ├── vllm/             ← update to latest (existing, unused)
│   └── scripts/          ← management scripts (existing + new)
│
├── 02-models/
│   ├── gguf/             ← existing GGUF models (llama.cpp only)
│   ├── vllm/             ← HF-format models for vLLM GPU inference
│   │   ├── hermes-3-8b/
│   │   └── Dolphin3.0-R1-Mistral-24B-AWQ/
│   │   ├── hermes-3-8b/
│   ├── flux2/            ← FLUX.2 [klein] 4B + 9B weights
│   │   └── nvfp4/        ← NVFP4 Klein 4B + 9B variants
│   ├── flux1/            ← FLUX.1 Dev weights (commercial fallback)
│   ├── wan22/            ← Wan 2.2 14B + Wan 2.1 1.3B weights
│   ├── hunyuan15/        ← HunyuanVideo 1.5 weights
│   ├── clip/             ← shared text encoders (Qwen3, T5, LLaVA-Llama3)
│   ├── vae/              ← shared VAE weights (FLUX.2, FLUX.1, HunyuanVideo)
│   ├── SEEDVR2/          ← Tier 6 — SeedVR2 v2.5 DiT + VAE (note: capital, container expects /models/SEEDVR2/)
│   ├── void/             ← VOID pass1+pass2 diffusion models
│   ├── optical_flow/     ← RAFT optical flow (VOID Pass 2)
│   ├── sam/ or sam3/     ← SAM3 segmentation checkpoint
│   └── esrgan/           ← upscaling (optional fallback only)
│
├── 03-data/              ← existing (datasets, references)
├── 04-logs/              ← existing + Docker/vLLM logs
├── 05-benchmarks/        ← existing
│
├── 06-configs/           ← ALL config files live here
│   ├── creative-stack/
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile
│   │   └── model_paths.yaml
│   ├── vllm/
│   │   └── docker-compose.yml
│   └── tailscale/        ← remote access config
│
├── 07-cache/             ← existing (HF cache, pip cache)
│
└── 08-portfolio/
    └── outputs/          ← all generated content organised by project
        ├── social-media/
        ├── client-work/
        │   └── _finishing/         ← NEW — staging for 60fps + 4K finishing passes
        │       ├── 01-source-720p/
        │       ├── 02-interpolated-60fps/
        │       └── 03-upscaled-4k/
        └── experiments/

# NOTE: Workflows live at:
# /data/ai/01-workspace/comfyui/user/default/workflows/
# These are auto-backed up to Git on every `creative-ctl.sh stop`
# Set GIT_BACKUP_REMOTE in creative-ctl.sh to your private repo URL
```

---

## Architecture Overview

```
                        INTERNET
                           │
                    ┌──────┴──────┐
                    │ Hermes Agent │  (cloud, always on)
                    │  + Your Phone│
                    └──────┬──────┘
                           │ Tailscale VPN (encrypted)
                           │
┌──────────────────────────┼──────────────────────────┐
│         Your Machine (Ubuntu 24.04)                  │
│                          │                           │
│              ┌───────────┴────────────┐              │
│              │    Tailscale Daemon     │              │
│              └───────────┬────────────┘              │
│                          │                           │
│         ┌────────────────┼────────────────┐          │
│         │                │                │          │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌─────┴──────┐  │
│  │  vLLM       │  │  ComfyUI    │  │  Other     │  │
│  │  Container  │  │  Container  │  │  Projects  │  │
│  │  port:8000  │  │  port:8188  │  │            │  │
│  └──────┬──────┘  └──────┬──────┘  └────────────┘  │
│         └────────────────┘                          │
│                  │ GPU Passthrough                   │
│         ┌────────┴────────┐                         │
│         │  RTX 5090 32GB  │                         │
│         │  NVIDIA CT Kit  │                         │
│         └─────────────────┘                         │
│                                                      │
│    /data/ai/02-models  (shared read-only volume)     │
└──────────────────────────────────────────────────────┘
```

**How Hermes controls your machine:**
1. You send instruction via phone → Hermes agent (cloud)
2. Hermes SSH-es into your machine via Tailscale
3. Hermes runs: `docker compose -f /data/ai/06-configs/creative-stack/docker-compose.yml up -d`
4. Hermes calls ComfyUI API via Tailscale IP to submit generation jobs
5. Hermes retrieves outputs from `/data/ai/08-portfolio/outputs/`

---

## Phase 1 — Verify Existing Setup

> [!tip] You skip most of Phase 1 from the old guide
> You already have Ubuntu + NVIDIA driver. Just verify what's working.

### 1.1 Verify Driver & CUDA

```bash
# Confirm GPU and driver
nvidia-smi
# Expected: Driver Version: 595.58+   CUDA Version: 13.2
# GPU: NVIDIA GeForce RTX 5090   32768MiB

# Confirm Blackwell SM_120
nvidia-smi --query-gpu=compute_cap --format=csv,noheader
# Expected: 12.0

# Check CUDA toolkit
nvcc --version
# Expected: release 13.2
```

> [!warning]
> If `nvcc` is missing:
> ```bash
> sudo apt install -y cuda-toolkit-13-2
> echo 'export PATH=/usr/local/cuda-13.2/bin:$PATH' >> ~/.bashrc
> echo 'export LD_LIBRARY_PATH=/usr/local/cuda-13.2/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
> source ~/.bashrc
> ```

### 1.2 Expand /data/ai/02-models Structure

Your `02-models` folder exists but needs subdirectories for the new stack.

```bash
# Add new subdirectories (won't touch existing gguf/ folder)
mkdir -p /data/ai/02-models/{vllm,flux,wan21,hunyuan,clip,vae,lora,esrgan}

# Verify full structure
ls /data/ai/02-models/
# Should show: gguf/  vllm/  flux/  wan21/  hunyuan/  clip/  vae/  lora/  esrgan/

# Create ComfyUI location in 01-workspace
mkdir -p /data/ai/01-workspace/comfyui

# Create config dirs
mkdir -p /data/ai/06-configs/{creative-stack,vllm,tailscale}

# Create output structure
mkdir -p /data/ai/08-portfolio/outputs/{social-media,client-work,experiments}
```

### 1.3 Investigate myenv

```bash
# Check what Python environment myenv is
cat /data/ai/myenv/pyvenv.cfg

# Check what's installed
/data/ai/myenv/bin/pip list 2>/dev/null | head -30

# If it's not ComfyUI-related, you can ignore it for now
# We'll create fresh venvs inside each tool's folder
```

### 1.4 Install Docker CE + NVIDIA Container Toolkit

```bash
# Remove any legacy Docker
sudo apt remove -y docker docker-engine docker.io containerd runc

# Add Docker repo
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-buildx-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update && sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify GPU passthrough into Docker
# Image tag must match your actual CUDA (13.2) and Ubuntu (24.04)
docker run --rm --gpus all nvidia/cuda:13.2.0-base-ubuntu24.04 nvidia-smi
# Should show RTX 5090 with Driver Version: 595.58+ and CUDA Version: 13.2
```

---

## Phase 2 — Tailscale (Remote Agent Access)

Install Tailscale first. Without it, Hermes cannot reach your machine, and nothing else in Phase 6 works.

### 2.1 Install Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate (opens browser or gives you a URL)
sudo tailscale up

# Get your machine's Tailscale IP (save this — Hermes needs it)
tailscale ip -4
# Example output: 100.x.x.x  ← your permanent private Tailscale IP
```

### 2.2 Enable SSH via Tailscale

```bash
# Enable Tailscale SSH (recommended — no need to open port 22 to internet)
sudo tailscale up --ssh

# Test from another device on Tailscale:
# ssh your-username@100.x.x.x
```

### 2.3 Configure Auto-Start

```bash
sudo systemctl enable tailscaled
sudo systemctl start tailscaled
```

### 2.3a Tailscale Funnel — Portfolio Sharing (Optional)

By default, ComfyUI is only reachable from devices on your Tailscale network. **Tailscale Funnel** lets you securely expose ComfyUI to a public HTTPS URL — useful for reviewing your work on a phone, sharing outputs with a client, or testing from outside your network.

> [!note] Prerequisite
> Tailscale Funnel must be enabled on your account first. Go to **[tailscale.com/admin/dns](https://login.tailscale.com/admin/dns)** → enable "HTTPS Certificates", then **[tailscale.com/admin/acls](https://login.tailscale.com/admin/acls)** → add `"funnel": true` to your node policy. Without this the command below will return a permission error.

```bash
# Enable Funnel on port 8188
sudo tailscale funnel --bg 8188

# Check status and get your exact public URL
tailscale funnel status
# Output includes something like:
# https://mushishi.tail12345.ts.net/ proxies to http://127.0.0.1:8188

# Test it from your phone browser using the URL above

# Disable when done — ComfyUI goes back to Tailscale-only
sudo tailscale funnel --bg off

# Confirm it is off
tailscale funnel status
# Should show: No funnel serving
```

> [!warning] Funnel Security
> Anyone with the URL can access your ComfyUI interface while Funnel is active. Use it only when sharing intentionally and disable immediately after. The `creative-ctl.sh funnel-on` / `funnel-off` commands in Phase 2.4 handle this with a reminder.
>
> ComfyUI has **no built-in authentication** — do not leave Funnel permanently enabled.

### 2.4 Create Remote Management Script for Hermes

This is the script Hermes will call via SSH to start/stop/query your creative stack.

```bash
cat > /data/ai/01-workspace/scripts/creative-ctl.sh << 'CTLEOF'
#!/bin/bash
# Creative stack controller — called locally or by Hermes agent via SSH
# Usage: ./creative-ctl.sh [start|stop|status|generate|monitor|backup|funnel-on|funnel-off|video-mode|resume-llm]

COMPOSE_FILE="/data/ai/06-configs/creative-stack/docker-compose.yml"
VLLM_COMPOSE="/data/ai/06-configs/vllm/docker-compose.yml"
OUTPUT_DIR="/data/ai/08-portfolio/outputs"
WORKFLOW_DIR="/data/ai/01-workspace/comfyui/user/default/workflows"
GIT_BACKUP_REMOTE="git@github.com:YOUR_USERNAME/comfyui-workflows-private.git"

case "$1" in

  start)
    echo "[creative-ctl] Starting vLLM..."
    docker compose -f $VLLM_COMPOSE up -d
    echo "[creative-ctl] Starting ComfyUI..."
    docker compose -f $COMPOSE_FILE up -d
    echo "[creative-ctl] Stack ready."
    LOCAL_IP=$(tailscale ip -4 2>/dev/null || hostname -I | awk '{print $1}')
    echo "  ComfyUI API: http://${LOCAL_IP}:8188"
    echo "  vLLM API:    http://${LOCAL_IP}:8000"
    ;;

  stop)
    echo "[creative-ctl] Backing up workflows before shutdown..."
    /data/ai/01-workspace/scripts/creative-ctl.sh backup
    echo "[creative-ctl] Stopping creative stack..."
    docker compose -f $COMPOSE_FILE down
    docker compose -f $VLLM_COMPOSE down
    echo "[creative-ctl] Stack stopped. GPU fully free."
    nvidia-smi --query-gpu=memory.free --format=csv,noheader
    ;;

  status)
    echo "=== GPU (per-process) ==="
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>/dev/null       || nvidia-smi --query-gpu=name,memory.used,memory.free,temperature.gpu --format=csv,noheader
    echo ""
    echo "=== GPU Summary ==="
    nvidia-smi --query-gpu=name,memory.used,memory.free,temperature.gpu --format=csv,noheader
    echo ""
    echo "=== Containers ==="
    docker ps --filter "name=creative-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    ;;

  generate)
    # Submit a ComfyUI workflow via API
    # Hermes passes workflow object JSON as $2
    # ComfyUI expects {"prompt": <workflow_object>}
    WORKFLOW_JSON="$2"
    if [ -z "$WORKFLOW_JSON" ]; then
      echo "Usage: $0 generate '<workflow_json>'"
      exit 1
    fi
    RESPONSE=$(curl -s -X POST http://localhost:8188/prompt \
      -H "Content-Type: application/json" \
      -d "{"prompt": ${WORKFLOW_JSON}}")
    PROMPT_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('prompt_id','error'))" 2>/dev/null)
    echo "[creative-ctl] Job queued: $PROMPT_ID"
    echo "$PROMPT_ID"
    ;;

  monitor)
    # Live per-process VRAM monitor — stays running until Ctrl+C
    # Uses nvitop if available, falls back to watch+nvidia-smi
    echo "[creative-ctl] Starting VRAM monitor (Ctrl+C to exit)..."
    if command -v nvitop &>/dev/null; then
      nvitop
    elif docker images | grep -q nvitop; then
      docker run --rm --gpus all --pid=host wernight/nvitop
    else
      echo "[creative-ctl] nvitop not found — using nvidia-smi watch (install nvitop for per-process detail)"
      watch -n 2 nvidia-smi
    fi
    ;;

  backup)
    # Push ComfyUI workflows to private Git repo
    if [ ! -d "$WORKFLOW_DIR/.git" ]; then
      echo "[creative-ctl] Initialising workflow Git repo..."
      git -C "$WORKFLOW_DIR" init
      git -C "$WORKFLOW_DIR" remote add origin "$GIT_BACKUP_REMOTE" 2>/dev/null || true
    fi
    cd "$WORKFLOW_DIR"
    git add -A
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M")
    CHANGED=$(git diff --cached --name-only | wc -l)
    if [ "$CHANGED" -gt 0 ]; then
      git commit -m "auto-backup: $CHANGED workflow(s) — $TIMESTAMP"
      git push origin main 2>/dev/null         && echo "[creative-ctl] Workflows backed up to Git ($CHANGED files)."         || echo "[creative-ctl] Git push failed — check remote config. Local commit saved."
    else
      echo "[creative-ctl] No workflow changes since last backup."
    fi
    ;;

  funnel-on)
    # Expose ComfyUI port publicly via Tailscale Funnel (portfolio sharing)
    # Accessible at: https://your-machine-name.tail12345.ts.net
    echo "[creative-ctl] Enabling Tailscale Funnel on port 8188..."
    sudo tailscale funnel --bg 8188
    echo "[creative-ctl] ComfyUI now publicly accessible at:"
    tailscale funnel status 2>/dev/null | grep "https://" || echo "  Run: tailscale funnel status to get your URL"
    echo ""
    echo "[creative-ctl] WARNING: Anyone with the URL can access your ComfyUI."
    echo "              Disable when done: ./creative-ctl.sh funnel-off"
    ;;

  funnel-off)
    echo "[creative-ctl] Disabling Tailscale Funnel..."
    sudo tailscale funnel --bg off
    echo "[creative-ctl] ComfyUI is private again (Tailscale-only)."
    ;;

  video-mode)
    echo "[creative-ctl] Stopping vLLM — full VRAM for video generation..."
    docker stop creative-vllm
    FREE=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader)
    echo "[creative-ctl] Done. ${FREE} VRAM now free."
    ;;

  resume-llm)
    echo "[creative-ctl] Restarting vLLM..."
    docker start creative-vllm
    echo "[creative-ctl] vLLM starting — ready in ~60s."
    ;;

  *)
    echo "Usage: $0 {start|stop|status|generate|monitor|backup|funnel-on|funnel-off|video-mode|resume-llm}"
    echo ""
    echo "  start        — Start vLLM + ComfyUI containers"
    echo "  stop         — Backup workflows, then stop all containers"
    echo "  status       — GPU usage, container health"
    echo "  generate     — Submit workflow JSON to ComfyUI API"
    echo "  monitor      — Live per-process VRAM monitor"
    echo "  backup       — Push ComfyUI workflows to Git"
    echo "  funnel-on    — Expose ComfyUI publicly via Tailscale Funnel"
    echo "  funnel-off   — Make ComfyUI private again"
    echo "  video-mode   — Stop vLLM, free all VRAM for video generation"
    echo "  resume-llm   — Restart vLLM after video generation"
    exit 1
    ;;

esac
CTLEOF

chmod +x /data/ai/01-workspace/scripts/creative-ctl.sh
```

> [!tip] How Hermes Uses This
> Your Hermes agent (cloud) runs:
> ```bash
> ssh your-username@100.x.x.x '/data/ai/01-workspace/scripts/creative-ctl.sh start'
> ```
> Then submits jobs to ComfyUI via the Tailscale IP directly.

---

## Phase 3 — vLLM: Local LLMs on GPU

**Why vLLM over Ollama for you:**
- AWQ quantised models up to 32B fit in your 32GB VRAM → 10–50x faster than CPU inference
- OpenAI-compatible API → Hermes agent can call it like any OpenAI endpoint
- Production-grade → this is what you want to learn properly
- Correct model ceiling: 24–32B AWQ (not 70B — those exceed 32GB VRAM)

### 3.1 Understanding GGUF vs vLLM

| Format | Tool | VRAM | Speed | Quality |
|--------|------|-------|-------|---------|
| GGUF (Q4_K_M) | llama.cpp / Ollama | CPU RAM | Slow (~3 tok/s) | Good |
| AWQ INT4 | **vLLM** | GPU VRAM | **Fast (~80 tok/s)** | Very Good |
| GPTQ INT4 | vLLM | GPU VRAM | Fast (~60 tok/s) | Very Good |
| bf16 / fp16 | vLLM | GPU VRAM | Fastest | Best |

> [!note]
> Your existing GGUF models in `02-models/gguf/` are **not compatible with vLLM**. Keep them — llama.cpp can still use them for experiments. But for the production creative stack, we download fresh HF-format models.

### 3.2 Best Unrestricted-local Models for vLLM (2025–2026)

Models listed below are confirmed to fit within your 32GB VRAM. 70B AWQ models (~35GB) are excluded — they exceed your card's capacity and will not load.

| Model | HF Repo | VRAM | Speed | Best For |
|-------|---------|------|-------|---------|
| **Dolphin 3.0 R1 Mistral 24B AWQ** | `Valdemardi/Dolphin3.0-R1-Mistral-24B-AWQ` | ~12GB | ⭐⭐⭐⭐⭐ | **Primary 24B** (after download). INT4 AWQ. Add `--quantization awq`. Temp 0.05–0.1 |
| **Hermes 3 Llama 3.1 8B** | `NousResearch/Hermes-3-Llama-3.1-8B` | ~16GB bfloat16 | ⭐⭐⭐⭐⭐ | **Already downloaded** ✅. Local folder: `hermes-3-8b`. gpu_memory_utilization 0.80 = 25GB (model + KV cache) |
| ~~Any 70B AWQ/GPTQ model~~ | ~~any~~ | ~~35GB~~ | ❌ | **Will NOT load — exceeds 32GB VRAM** |

> [!note] Only Two Models to Download
> The Dolphin Qwen2.5 series only exists in 0.5B, 1.5B, and 3B — no 14B or 32B. Download only the two models above.

> [!warning] 70B Models Do NOT Fit in 32GB VRAM
> AWQ INT4 of a 70B model = ~35GB. Your card has 32GB. These models will crash at load time, not just fail to run concurrently. The 24B Mistral is the practical ceiling for your hardware.

> [!tip] Recommended Starting Point
> **Hermes 3 8B** (`NousResearch/Hermes-3-Llama-3.1-8B`) — start here, already downloaded, 16GB bfloat16, gpu_memory_utilization 0.80. Then upgrade to **Dolphin 3.0 R1 Mistral 24B AWQ** (`Valdemardi/Dolphin3.0-R1-Mistral-24B-AWQ`) — 12GB INT4, gpu_memory_utilization 0.45, concurrent with HunyuanVideo 1.5. Full bfloat16 24B = 48GB = will OOM.

### 3.3 Download Models

```bash
pip3 install --break-system-packages --upgrade huggingface_hub
huggingface-cli login   # enter your HF token

# PRIMARY: Dolphin 3.0 Mistral 24B (14GB VRAM, fully unrestricted-local)
# STEP 1: Download Hermes 3 8B (working immediately, 16GB bfloat16)
huggingface-cli download NousResearch/Hermes-3-Llama-3.1-8B \
  --local-dir /data/ai/02-models/vllm/hermes-3-8b
# NOTE: The folder downloads as hermes-3-8b (not Hermes-3-Llama-3.1-8B)
# Your .env and compose file must reference: /models/vllm/hermes-3-8b

# STEP 2: Download Dolphin 24B AWQ (~12GB INT4 — fits in 32GB with ComfyUI concurrent)
# This is the quantized version — NOT the full bfloat16 which is 48GB and will OOM
huggingface-cli download Valdemardi/Dolphin3.0-R1-Mistral-24B-AWQ \
  --local-dir /data/ai/02-models/vllm/Dolphin3.0-R1-Mistral-24B-AWQ

# ❌ DO NOT run this — full bfloat16 = 48GB = OOM crash on 32GB card:
# huggingface-cli download cognitivecomputations/Dolphin3.0-R1-Mistral-24B

# FAST: Hermes 3 8B (6GB VRAM, great for always-on prompt enhancement)
huggingface-cli download NousResearch/Hermes-3-Llama-3.1-8B \
  --local-dir /data/ai/02-models/vllm/hermes-3-8b
# NOTE: The folder downloads as hermes-3-8b (not Hermes-3-Llama-3.1-8B)
# Your .env and compose file must reference: /models/vllm/hermes-3-8b

# ALTERNATIVE: Dolphin Qwen 2.5 32B AWQ (18GB VRAM, stronger reasoning)
# Only download this if you want to stop ComfyUI during LLM-heavy tasks

# NOTE: Do NOT download any 70B models — they require ~35GB VRAM and will
# fail to load entirely on your RTX 5090 (32GB).
```

### 3.4 vLLM — Docker Only, No Host Install Required

> [!warning] Do NOT install vLLM on the host
> Ubuntu 24.04 blocks system-wide pip installs (PEP 668), and more importantly **you do not need vLLM on the host at all**. vLLM runs entirely inside the Docker container defined in §3.5. The image `vllm/vllm-openai` already contains vLLM, all its dependencies, and the CUDA libraries it needs. Nothing installs on your host system.

Your existing `/data/ai/01-workspace/vllm` folder (the old git clone) is not used — leave it as-is or delete it, doesn't matter.

```bash
# Pull the vLLM Docker image — this is the only "install" step needed
docker pull vllm/vllm-openai:v0.9.0

# Confirm it downloaded (~15-20GB)
docker images vllm/vllm-openai
# Expected: vllm/vllm-openai   v0.9.0   <hash>   <date>   ~18GB

# Check the vLLM version inside the image
docker run --rm vllm/vllm-openai:v0.9.0 python3 -c "import vllm; print(vllm.__version__)"
```

> [!tip] How to upgrade vLLM in future
> Change the image tag in `/data/ai/06-configs/vllm/docker-compose.yml` then pull and restart:
> ```bash
> sudo docker pull vllm/vllm-openai:cu130-nightly
> sudo docker compose -f /data/ai/06-configs/vllm/docker-compose.yml down
> sudo docker compose -f /data/ai/06-configs/vllm/docker-compose.yml up -d
> ```
> No pip, no venv, no host changes required.
> 
> **RTX 5090 note:** Always use `cu130-nightly` — stable releases (`v0.9.0` etc.) do not include SM_120 kernels and crash with `no kernel image available` on first inference.

### 3.5 vLLM Docker Compose

**Step 1 — Create the `.env` file (controls which model runs):**

> [!note] One .env File — Two Purposes
> This single file stores both your HuggingFace token AND the active model config. You never need two separate files. When switching models, you only edit `VLLM_MODEL` and `VLLM_GPU_MEM` — never touch `HF_TOKEN`.

```bash
cat > /data/ai/06-configs/vllm/.env << 'EOF'
# ── HuggingFace token — for downloading gated models ─────────────────────
# Set this once. Get your token at: huggingface.co/settings/tokens
HF_TOKEN=hf_your_actual_token_here

# ── Active model — only edit these two lines to switch models ─────────────
VLLM_MODEL=/models/vllm/hermes-3-8b
VLLM_GPU_MEM=0.80

# ── Switch to Dolphin 24B AWQ after downloading (comment/uncomment) ───────
# VLLM_MODEL=/models/vllm/Dolphin3.0-R1-Mistral-24B-AWQ
# VLLM_GPU_MEM=0.45
# ─────────────────────────────────────────────────────────────────────────

VLLM_MAX_LEN=8192
EOF

chmod 600 /data/ai/06-configs/vllm/.env
```

**Step 2 — Docker Compose file:**

```yaml
# /data/ai/06-configs/vllm/docker-compose.yml

services:
  vllm:
    image: vllm/vllm-openai:cu130-nightly  # Required for RTX 5090 SM_120 — stable releases OOM
    container_name: creative-vllm
    runtime: nvidia
    ipc: host
    shm_size: "8gb"
    env_file:
      - /data/ai/06-configs/vllm/.env
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=all
      - VLLM_ATTENTION_BACKEND=FLASHINFER   # Required: flash-attn crashes on SM_120
      - VLLM_FLASH_ATTN_VERSION=2           # Required: FA3 not yet stable on Blackwell
    volumes:
      - /data/ai/02-models:/models:ro
    ports:
      - "8000:8000"
    # ═══════════════════════════════════════════════════════════════════════
    # COMMAND BLOCK — change this when switching models
    # Only ONE command: block active at a time
    # ═══════════════════════════════════════════════════════════════════════

    # ── MODE A: Hermes 3 8B (CURRENTLY ACTIVE — confirmed working) ──────────
    # Use when: daily prompt work, running alongside ComfyUI
    # Leave this uncommented for normal use
    command: >
      --model ${VLLM_MODEL}
      --dtype bfloat16
      --max-model-len ${VLLM_MAX_LEN}
      --gpu-memory-utilization ${VLLM_GPU_MEM}
      --trust-remote-code
      --served-model-name local-llm

    # ── MODE B: Dolphin 24B AWQ — Prompt Mode ───────────────────────────────
    # Use when: higher quality prompts, complex scenes, concurrent with ComfyUI
    # To activate: comment out Mode A command above, uncomment this block
    # Also update .env: VLLM_GPU_MEM=0.45, VLLM_MAX_LEN=32768
    # command: >
    #   --model ${VLLM_MODEL}
    #   --quantization awq
    #   --dtype auto
    #   --max-model-len ${VLLM_MAX_LEN}
    #   --gpu-memory-utilization ${VLLM_GPU_MEM}
    #   --trust-remote-code
    #   --served-model-name local-llm

    # ── MODE C: Dolphin 24B AWQ — Script Mode ───────────────────────────────
    # Use when: full scripts, production bibles, 90-min screenplays — standalone
    # To activate: comment out Mode A command above, uncomment this block
    # Also update .env: VLLM_GPU_MEM=0.85, VLLM_MAX_LEN=98304
    # Stop ComfyUI before using this mode (vLLM uses 27GB)
    # command: >
    #   --model ${VLLM_MODEL}
    #   --quantization awq
    #   --dtype auto
    #   --max-model-len ${VLLM_MAX_LEN}
    #   --gpu-memory-utilization ${VLLM_GPU_MEM}
    #   --trust-remote-code
    #   --served-model-name local-llm

    # ═══════════════════════════════════════════════════════════════════════
    # KEY DIFFERENCES BETWEEN MODES:
    #   Hermes 8B:      --dtype bfloat16   (NO --quantization flag)
    #   Dolphin 24B AWQ: --quantization awq  --dtype auto  (NOT bfloat16)
    # Temperature is set per API request, not here:
    #   Hermes 8B:       "temperature": 0.7
    #   Dolphin 24B AWQ: "temperature": 0.07  ← REQUIRED, model degrades at high temp
    # ═══════════════════════════════════════════════════════════════════════
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 120s
    restart: unless-stopped
```

---

## Model Selection Guide — When to Use Which

This is the decision framework for choosing between your three LLM modes. The right model depends entirely on what you are creating.

### Context Window & Script Length Reference

| Content Type | Approx Tokens | Use This Mode |
|-------------|--------------|--------------|
| Single ComfyUI prompt enhancement | 200–500 | **Hermes 8B** |
| Short scene description (1 scene) | 200–400 | **Hermes 8B** |
| Social media video brief | 500–1,000 | **Hermes 8B** |
| Multi-scene outline (5–10 scenes) | 2,000–5,000 | **Hermes 8B** |
| Short film script (10 min) | 8,000–15,000 | **Dolphin 24B — Prompt Mode** |
| Complex multi-character script (30 min) | 25,000–45,000 | **Dolphin 24B — Prompt Mode** |
| Feature length script (90 min) | 80,000–120,000 | **Dolphin 24B — Script Mode** |
| Full production bible + script | 60,000–100,000 | **Dolphin 24B — Script Mode** |

---

### Mode A — Hermes 3 8B (Daily Driver)

**When to use:** Any single prompt, quick enhancement, social media content, iterating on ideas, running alongside ComfyUI video generation.

**Practical workflows this enables:**
- Type a rough scene idea → Hermes expands it into a detailed ComfyUI prompt → FLUX.2 generates the image → all in one session
- Run 20 variations of a prompt quickly without stopping ComfyUI
- Always-on background assistant while generating video with HunyuanVideo or Wan 2.2

**Settings:**
```bash
VLLM_MODEL=/models/vllm/hermes-3-8b
VLLM_GPU_MEM=0.80
VLLM_MAX_LEN=32768    # 32K — more than enough for any single prompt
```
**Temperature:** 0.7 — **ComfyUI concurrent:** ✅ yes (stop vLLM only for HunyuanVideo full VRAM mode)

---

### Mode B — Dolphin 24B AWQ, Prompt Mode (Quality Enhancement)

**When to use:** High quality cinematic prompts, complex scene descriptions with specific character details, mood references, colour grading instructions. When you want noticeably richer output than Hermes 8B but are still feeding individual prompts into ComfyUI.

**Practical workflows this enables:**
- Describe a complex shot with lighting, character position, emotional subtext → Dolphin generates a detailed, nuanced prompt that Hermes would simplify
- Multi-character scene with specific dialogue-driven expressions → richer facial detail prompts
- Style transfer prompts referencing specific cinematographers or directors → more accurate stylistic vocabulary

**Settings:**
```bash
VLLM_MODEL=/models/vllm/Dolphin3.0-R1-Mistral-24B-AWQ
VLLM_GPU_MEM=0.45
VLLM_MAX_LEN=32768    # 32K — fits with ~17GB left for ComfyUI
```
**Temperature:** 0.07 (REQUIRED — degrades badly at higher values)
**ComfyUI concurrent:** ✅ yes with HunyuanVideo 1.5 (~14GB) — both fit in 32GB

---

### Mode C — Dolphin 24B AWQ, Script Mode (Long-Form Creative)

**When to use:** Full multi-scene scripts with dialogue, character arcs, production notes. Feeding an entire treatment and getting a complete screenplay back. This is your creative writing engine for large projects.

**Practical workflows this enables:**
- Feed a 2-page treatment → receive a complete 30-scene script with dialogue, action lines, and shot descriptions
- Maintain character voice and consistency across an entire feature-length narrative in one context window
- Include a full character bible, world-building notes, and tone references alongside the script in the same session
- Generate shot-by-shot video prompts for each scene in sequence — ComfyUI then processes them as a batch
- Full production bible (characters + locations + scenes + dialogue) = ~60K tokens — fits with 12K to spare

**Settings:**
```bash
VLLM_MODEL=/models/vllm/Dolphin3.0-R1-Mistral-24B-AWQ
VLLM_GPU_MEM=0.85     # Standalone mode — vLLM gets 27GB
VLLM_MAX_LEN=98304    # 96K tokens — enough for a full feature film script
```
**Temperature:** 0.07
**ComfyUI concurrent:** ❌ — vLLM uses 27GB at 0.85 utilisation; stop ComfyUI first
**Restart vLLM to switch back** after script work is done

> [!note] Why 96K and not 128K?
> Dolphin 24B AWQ supports 128K natively. At 128K the KV cache needs ~21GB which pushes the total to ~33GB — just over your 32GB card. At 96K (98304 tokens) the total sits comfortably at ~28GB with 4GB headroom for memory spikes. If you hit OOM at 96K, drop to `VLLM_MAX_LEN=65536`.

---

### Switching Between Modes — One File, One Restart

```bash
nano /data/ai/06-configs/vllm/.env
# Uncomment the mode you want, comment out the others
# DO NOT touch HF_TOKEN — that stays the same always

sudo docker compose -f /data/ai/06-configs/vllm/docker-compose.yml restart
# Watch logs until: Application startup complete.
# Hermes 8B loads in ~60s. Dolphin 24B AWQ loads in ~90s.
```

> [!warning] Dolphin 24B AWQ also needs `--quantization awq` in the compose command
> When switching to either Dolphin 24B mode, add this flag to the `command:` block in `docker-compose.yml`:
> ```yaml
>     command: >
>       --model ${VLLM_MODEL}
>       --quantization awq
>       --dtype auto
>       --max-model-len ${VLLM_MAX_LEN}
>       --gpu-memory-utilization ${VLLM_GPU_MEM}
>       --trust-remote-code
>       --served-model-name local-llm
> ```
> Switch back to `--dtype bfloat16` (no `--quantization`) when returning to Hermes 8B.

---

### Complete .env Reference

The full populated file — all three modes documented, only one active at a time:

```bash
# /data/ai/06-configs/vllm/.env
# ─────────────────────────────────────────────────────────────────────────
# SECTION 1: HuggingFace Authentication
# Set once. Never changes unless you regenerate your token.
# Get token at: huggingface.co/settings/tokens (Read scope is sufficient)
# ─────────────────────────────────────────────────────────────────────────
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ─────────────────────────────────────────────────────────────────────────
# SECTION 2: Active Model — uncomment ONE block only, comment out the others
# After editing: sudo docker compose -f .../vllm/docker-compose.yml restart
# ─────────────────────────────────────────────────────────────────────────

# ── MODE A: Hermes 3 8B ───────────────────────────────────────────────────
# Use for: single prompts, quick enhancement, concurrent with ComfyUI
# Context: up to 32K tokens (social media, short scenes, outlines)
# Temperature: 0.7 | ComfyUI concurrent: YES
VLLM_MODEL=/models/vllm/hermes-3-8b
VLLM_GPU_MEM=0.80
VLLM_MAX_LEN=32768

# ── MODE B: Dolphin 24B AWQ — Prompt Mode ────────────────────────────────
# Use for: high quality prompts, complex scenes, multi-character shots
# Context: up to 32K tokens (short film scripts, detailed scene packs)
# Temperature: 0.07 REQUIRED | ComfyUI concurrent: YES (with HunyuanVideo 1.5)
# Also requires --quantization awq and --dtype auto in compose command
# VLLM_MODEL=/models/vllm/Dolphin3.0-R1-Mistral-24B-AWQ
# VLLM_GPU_MEM=0.45
# VLLM_MAX_LEN=32768

# ── MODE C: Dolphin 24B AWQ — Script Mode ────────────────────────────────
# Use for: full feature scripts, production bibles, 90-min screenplays
# Context: up to 96K tokens (entire feature film + character bible)
# Temperature: 0.07 REQUIRED | ComfyUI concurrent: NO — stop ComfyUI first
# Also requires --quantization awq and --dtype auto in compose command
# VLLM_MODEL=/models/vllm/Dolphin3.0-R1-Mistral-24B-AWQ
# VLLM_GPU_MEM=0.85
# VLLM_MAX_LEN=98304

# ─────────────────────────────────────────────────────────────────────────
# SECTION 3: Notes
# ─────────────────────────────────────────────────────────────────────────
# Context window reference:
#   1 scene description    = ~300 tokens
#   1 page of dialogue     = ~400 tokens
#   Short film (10 min)    = ~10,000 tokens
#   Feature film (90 min)  = ~100,000 tokens
#   Full production bible  = ~60,000 tokens
```

> [!warning] Keep HF_TOKEN Secret
> Never commit `.env` to Git. The file already has `chmod 600` applied. If you accidentally expose it, regenerate your token immediately at huggingface.co/settings/tokens.

### 3.6 Test vLLM API

```bash
# Start vLLM
docker compose -f /data/ai/06-configs/vllm/docker-compose.yml up -d

# Watch logs — success looks like:
# INFO:     Application startup complete.
# INFO:     127.0.0.1:xxxxx - "GET /health HTTP/1.1" 200 OK
# ← This confirms model loaded, API is up, ready to accept requests
#
# CONFIRMED WORKING on RTX 5090 with:
#   image: vllm/vllm-openai:cu130-nightly
#   VLLM_ATTENTION_BACKEND=FLASHINFER
#   VLLM_FLASH_ATTN_VERSION=2
#   model: hermes-3-8b (NousResearch/Hermes-3-Llama-3.1-8B)

# Wait for the above, then test
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-llm",
    "messages": [
      {"role": "user", "content": "Write a detailed cinematic prompt for a dark noir film sequence with heavy noir atmosphere"}
    ],
    "max_tokens": 500,
    "temperature": 0.07
  }'

# From Hermes agent via Tailscale:
# curl http://100.x.x.x:8000/v1/chat/completions ...
```

### 3.7 Switch Between Models (No Rebuild)

```bash
# Edit the model path in docker-compose.yml
nano /data/ai/06-configs/vllm/docker-compose.yml
# Change MODEL_PATH and --model to point to different model folder

# Restart vLLM with new model
docker compose -f /data/ai/06-configs/vllm/docker-compose.yml restart
```

---

## Phase 4 — ComfyUI Docker Container

### 4.1 Dockerfile

```dockerfile
# /data/ai/06-configs/creative-stack/Dockerfile
FROM nvidia/cuda:13.2.0-devel-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive

# Ubuntu 24.04 ships Python 3.12 — python3.11 does NOT exist in its repos
# Also install libportaudio2 for whisper/audio nodes in LLM Party
RUN apt update && apt install -y \
    python3 python3-venv python3-pip \
    git wget curl ffmpeg \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    libportaudio2 libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 3.12 is already default — no update-alternatives needed
RUN python3 --version

# PyTorch nightly with cu130 — required for RTX 5090 SM_120 Blackwell
# cu130 not cu132 — unlocks NVFP4 Blackwell-native acceleration
RUN pip3 install --no-cache-dir --break-system-packages \
    --pre torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/nightly/cu130

# NOTE: Do NOT verify GPU capability during build — no GPU access at build time.
# GPU verification happens at runtime in start.sh when the container actually starts.

# Clone ComfyUI
WORKDIR /app
RUN git clone https://github.com/comfyanonymous/ComfyUI.git
WORKDIR /app/ComfyUI
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# ComfyUI Manager
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager
RUN pip3 install --no-cache-dir --break-system-packages \
    -r custom_nodes/ComfyUI-Manager/requirements.txt

# ComfyUI-LLM-Party (OpenAI-compatible API node — connects to vLLM)
RUN git clone https://github.com/heshengtao/comfyui_LLM_party.git custom_nodes/comfyui_LLM_party
RUN pip3 install --no-cache-dir --break-system-packages \
    -r custom_nodes/comfyui_LLM_party/requirements.txt

# LLM Party optional dependencies — baked into image so they don't reinstall on every start
# py-cord[voice]: Discord bot integration (Hermes → Discord → ComfyUI)
# moviepy: video editing nodes
# browser-use: browser automation nodes
# openai-whisper: audio transcription nodes
RUN pip3 install --no-cache-dir --break-system-packages \
    "py-cord[voice]" \
    moviepy \
    browser-use \
    openai-whisper

EXPOSE 8188

COPY start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]
```

### 4.2 Startup Script

```bash
# /data/ai/06-configs/creative-stack/start.sh
#!/bin/bash
set -e

echo "=== ComfyUI Creative Stack ==="
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
echo "VRAM: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader)"
python3 -c "import torch; print(f'PyTorch: {torch.__version__} | CUDA: {torch.cuda.is_available()} | SM: {torch.cuda.get_device_capability()}')"

cd /app/ComfyUI
exec python3 main.py \
  --listen 0.0.0.0 \
  --port 8188 \
  --extra-model-paths-config /app/model_paths.yaml
```

### 4.3 Model Paths Config

> [!warning] YAML Format — Critical
> ComfyUI's parser calls `.split("\n")` on path values — it expects **strings**, not YAML lists.
> Always use the `|` block scalar with indented paths. Never use `- /path` list syntax or you get:
> `TypeError: list indices must be integers or slices, not str`

```yaml
# /data/ai/06-configs/creative-stack/model_paths.yaml
#
# Use | block scalar — NOT YAML list syntax (no - dashes)
# This is the confirmed working format.

comfyui:
    # FLUX models — both unet and checkpoints keys needed for different loaders
    checkpoints: |
        /models/flux1
        /models/flux2

    unet: |
        /models/flux1
        /models/flux2

    # Video diffusion models
    diffusion_models: |
        /models/hunyuan15
        /models/wan22

    # Shared text encoders (Qwen3 for FLUX.2, T5 for FLUX.1, LLaVA-Llama3 for HunyuanVideo, UMT5 for Wan)
    clip: |
        /models/clip

    text_encoders: |
        /models/clip

    vae: |
        /models/vae

    loras: |
        /models/lora

    upscale_models: |
        /models/esrgan
```

### 4.4 Docker Compose for ComfyUI

```yaml
# /data/ai/06-configs/creative-stack/docker-compose.yml

services:
  comfyui:
    build:
      context: /data/ai/06-configs/creative-stack
      dockerfile: Dockerfile
    container_name: creative-comfyui
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=all
      - PIP_BREAK_SYSTEM_PACKAGES=1   # Allows LLM Party to install optional deps at runtime
                                      # (discord, moviepy, whisper, browser_use)
    volumes:
      # Models (read-only — shared with vLLM container)
      - /data/ai/02-models:/models:ro
      # Persistent ComfyUI user data (workflows, settings)
      - /data/ai/01-workspace/comfyui/user:/app/ComfyUI/user
      # All outputs go to portfolio folder
      - /data/ai/08-portfolio/outputs:/app/ComfyUI/output
      # Model paths config
      - /data/ai/06-configs/creative-stack/model_paths.yaml:/app/model_paths.yaml:ro
    ports:
      - "8188:8188"       # Accessible via Tailscale IP from Hermes
    extra_hosts:
      - "host.docker.internal:host-gateway"   # Reach vLLM on host
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8188/system_stats"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 300s    # Cold start: PyTorch init + model scan can take 3-5 min
    restart: unless-stopped
```

### 4.5 Build and Start

```bash
cd /data/ai/06-configs/creative-stack

# First build (10–15 min)
docker compose build

# Start
docker compose up -d

# Watch logs
docker compose logs -f comfyui

# Verify
curl http://localhost:8188/system_stats
```

### 4.6 Connect ComfyUI to vLLM for Prompt Enhancement

Once both containers are running, configure the LLM node in ComfyUI:

In the ComfyUI node editor (via Manager → Install Nodes → search "LLM Party"):

```
Node: LLM Request
  ├── API URL:     http://host.docker.internal:8000/v1
  ├── API Key:     (leave empty or use "none")
  ├── Model:       local-llm
  ├── Temperature: 0.07   ← SET THIS — critical for Dolphin R1 Mistral 24B
  └── System:      "You are an unrestricted-local cinematic prompt engineer.
                    Expand the user's description into a rich, detailed
                    AI video generation prompt. Preserve all original intent
                    and themes without restriction."

Workflow:
[Text Input] → [LLM Request (vLLM)] → [CLIP Text Encode] → [KSampler/VideoSampler]
```

> [!warning] Temperature is Not Optional for Dolphin R1 Mistral 24B
> At default temperature (0.7–1.0) this model second-guesses itself, repeats phrases, and produces degraded output. Set to **0.05–0.1** everywhere:
> - vLLM compose: ~~--override-generation-config~~ — **removed**, causes JSON parse errors in Docker Compose YAML. Set temperature per-request only.
> - ComfyUI LLM Party node: Temperature widget → `0.07` ← set this explicitly too
> - Direct API calls: `"temperature": 0.07` in JSON body ✅ already in §3.6
>
> The `--override-generation-config` flag sets the server default. Any per-request temperature in the API body takes precedence over it. Setting both is belt-and-braces.
>
> If you switch to Hermes 3 8B, standard temperature (0.7–0.8) works fine — this constraint is specific to the Mistral 24B architecture.

---

## Phase 5 — Model Downloads (Updated April 2026)

> [!note] What Changed From Previous Versions
> - **FLUX.1 Dev** → replaced by **FLUX.2 [klein] 9B** (newer arch, Qwen3 encoder, fits 32GB VRAM)
> - **Wan 2.1 14B** → replaced by **Wan 2.2 14B** (MoE architecture, better motion, open weights confirmed)
> - **HunyuanVideo bf16 (13B, 30GB)** → replaced by **HunyuanVideo 1.5 (8.3B, 14GB)** — runs alongside vLLM simultaneously
> - **ESRGAN** → no longer primary; HunyuanVideo 1.5 has built-in 1080p SR UNet

### 5.1 HuggingFace Setup

All model downloads run on the **host** machine (not inside a container). Models land on `/data/ai/02-models/` and are mounted read-only into containers.

```bash
# Install huggingface_hub on the host
pip3 install --break-system-packages --upgrade huggingface_hub

# Get your token at: huggingface.co/settings/tokens
# Create a token with "Read" scope — that's all downloads need
huggingface-cli login
# Paste your token when prompted. It saves to ~/.cache/huggingface/token

# CRITICAL: Redirect HF cache to your data drive, not the OS drive
# Without this, HF caches model shards to ~/.cache which is on nvme1n1 (OS drive, 200GB /)
echo 'export HF_HOME=/data/ai/07-cache/huggingface' >> ~/.bashrc
echo 'export HUGGINGFACE_HUB_CACHE=/data/ai/07-cache/huggingface/hub' >> ~/.bashrc
source ~/.bashrc

# Create the cache dir
mkdir -p /data/ai/07-cache/huggingface/hub

# Store your token in the vLLM .env file
# NOTE: This file also contains model config — see §3.5 for the full combined file
# If the .env already exists (created in §3.5), just add the token to it:
HF_TOKEN_VALUE=$(cat ~/.cache/huggingface/token)
if grep -q "HF_TOKEN" /data/ai/06-configs/vllm/.env 2>/dev/null; then
  # Update existing token line
  sed -i "s|HF_TOKEN=.*|HF_TOKEN=${HF_TOKEN_VALUE}|" /data/ai/06-configs/vllm/.env
else
  # Add token to existing file or create new
  echo "HF_TOKEN=${HF_TOKEN_VALUE}" >> /data/ai/06-configs/vllm/.env
fi
chmod 600 /data/ai/06-configs/vllm/.env
echo "Token saved to /data/ai/06-configs/vllm/.env"

# Export token as env var so all downloads are authenticated
export HF_TOKEN=$(cat ~/.cache/huggingface/token)

# Verify login works
huggingface-cli whoami
```

> [!warning] HF_HOME is Critical
> Without setting `HF_HOME`, `huggingface-cli download` caches partial downloads to `~/.cache` which sits on your OS drive (nvme1n1, 200GB partition). FLUX.2 + Wan 2.2 + HunyuanVideo 1.5 total ~100GB — this will fill your OS partition and break Ubuntu. Always confirm `HF_HOME` points to `/data/ai/07-cache/huggingface` before downloading.

---

### 5.2 FLUX.2 [klein] — Image Generation

> [!warning] Licence
> FLUX.2 [klein] uses the **FLUX Non-Commercial Licence** — not Apache 2.0. Free for personal use. For commercial workflows, use FLUX.1 Dev (Apache 2.0) at section 5.2c.

**Architecture note:** FLUX.2 [klein] uses a **Qwen3 text encoder** — different from FLUX.1's T5. Download the correct encoder below.

> [!tip] Authenticate Before Every Download Session
> ```bash
> # Run this once at the start of each download session
> # Prevents rate limiting and "unauthenticated" warnings
> export HF_TOKEN=$(cat ~/.cache/huggingface/token)
> export HUGGINGFACE_HUB_CACHE=/data/ai/07-cache/huggingface/hub
> huggingface-cli whoami   # should show your username
> ```

> [!note] Why Qwen3 and not Mistral?
> FLUX.2 has two variants with **different text encoders**:
> - **FLUX.2 Klein** (4B and 9B) — uses **Qwen3** encoders. Repo: `vae-text-encorder-for-flux-klein-4b/9b`
> - **FLUX.2 Dev** — uses **Mistral** encoders. Repo: `flux2-dev`
>
> The earlier download error happened because the document incorrectly pointed to `flux2-dev` for Klein models. That repo has Mistral encoders which are incompatible with Klein — produces black/corrupted output. The Qwen3 repos are correct.

#### 5.2a FLUX.2 [klein] 4B Distilled — Start Here (~8GB VRAM, ~1.2s/image)

Download this first. It runs in 8GB VRAM, concurrent with Dolphin 24B AWQ, and verifies your full FLUX.2 pipeline before committing to the 29GB 9B download.

```bash
mkdir -p /data/ai/02-models/flux2

# STEP 1: Accept licence at huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8
huggingface-cli download black-forest-labs/FLUX.2-klein-4b-fp8   flux-2-klein-4b-fp8.safetensors   --local-dir /data/ai/02-models/flux2

# STEP 2: Qwen3 4B text encoder — from the klein-4b specific repo
# (note typo "encorder" is intentional — that is the actual repo name)
huggingface-cli download Comfy-Org/vae-text-encorder-for-flux-klein-4b   split_files/text_encoders/qwen_3_4b_fp4_flux2.safetensors   --local-dir /data/ai/02-models/clip

# STEP 3: FLUX.2 VAE — shared by both 4B and 9B, download once
huggingface-cli download Comfy-Org/vae-text-encorder-for-flux-klein-9b   split_files/vae/flux2-vae.safetensors   --local-dir /data/ai/02-models/vae
```

**VRAM:** ~8GB — runs concurrently with Dolphin 24B AWQ (total ~22GB ✅)
**Speed:** ~1.2s per image on RTX 5090
**Use for:** Daily image generation, prompt iteration, testing workflows

#### 5.2b FLUX.2 [klein] 9B Base — Upgrade for Maximum Quality (~29GB VRAM)

Download after 4B is confirmed working. Needs vLLM stopped (29GB model + overhead exceeds 32GB alongside any LLM).

```bash
# STEP 1: Accept licence at huggingface.co/black-forest-labs/FLUX.2-klein-base-9b-fp8
huggingface-cli download black-forest-labs/FLUX.2-klein-base-9b-fp8   flux-2-klein-base-9b-fp8.safetensors   --local-dir /data/ai/02-models/flux2

# STEP 2: Qwen3 8B text encoder — from the klein-9b specific repo
huggingface-cli download Comfy-Org/vae-text-encorder-for-flux-klein-9b   split_files/text_encoders/qwen_3_8b_fp8mixed.safetensors   --local-dir /data/ai/02-models/clip

# VAE already downloaded in §5.2a — skip
```

**VRAM:** ~29GB — stop vLLM before loading (`docker stop creative-vllm`)
**Speed:** ~17s per image on RTX 5090
**Use for:** Final renders, portfolio-quality output

> [!tip] NVFP4 / FP8 FLUX.2 Klein variants now exist (GDC 2026) — use them on the 5090
> Black Forest Labs + NVIDIA released official NVFP4 and FP8 variants of FLUX.2 Klein 4B and 9B
> on HuggingFace. On RTX 50-series (native FP4 hardware): ~2.5–3× faster, ~60% less VRAM, with
> quality holding well. This relaxes the one-model-at-a-time pressure — a 9B keyframe pass in
> NVFP4 is far lighter than the ~29GB fp8 figures above.
> **Caveat for client work:** NVFP4 softens in-frame text/fine signage. If a plate has
> brand text/signage as an invariant, use the FP8 variant for that pass or fix text in post.

#### 5.2c FLUX.1 Dev — Commercial-Safe Fallback (Apache 2.0)

```bash
mkdir -p /data/ai/02-models/flux1

# Accept terms at: huggingface.co/black-forest-labs/FLUX.1-dev
huggingface-cli download black-forest-labs/FLUX.1-dev \
  flux1-dev.safetensors \
  --local-dir /data/ai/02-models/flux1

# FLUX.1 uses T5 encoder — separate from FLUX.2's Qwen3
huggingface-cli download comfyanonymous/flux_text_encoders \
  t5xxl_fp16.safetensors clip_l.safetensors \
  --local-dir /data/ai/02-models/clip

huggingface-cli download black-forest-labs/FLUX.1-dev \
  ae.safetensors \
  --local-dir /data/ai/02-models/vae
```

> [!tip] Which FLUX When
> | Scenario | Model | VRAM | Speed | Concurrent with LLM? |
> |----------|-------|------|-------|---------------------|
> | **Start here** — daily generation, iteration | FLUX.2 [klein] 4B distilled | ~8GB | ~1.2s | ✅ Yes |
> | Maximum quality — final renders | FLUX.2 [klein] 9B base | ~29GB | ~17s | ❌ Stop vLLM |
> | Commercial-safe licence needed | FLUX.1 Dev | ~18GB | ~15s | ✅ with Dolphin 24B |

---

### 5.3 Wan 2.2 14B — Primary Video Model

> [!important] Wan 2.2 Architecture — Why Two Files Are Required
> Wan 2.2 uses **Mixture of Experts (MoE)** — two specialist networks working in sequence:
> - **High-noise expert** → handles early denoising (layout, composition, motion)
> - **Low-noise expert** → handles late denoising (fine details, textures, sharpness)
>
> Both files load simultaneously and hand off at each denoising step. This is intentional — not two alternatives. Total params = 27B, active at once = 14B, VRAM = ~14GB.
>
> The official Alibaba repo is `Wan-AI/Wan2.2-T2V-A14B` (A = Active 14B).
> For ComfyUI we use `Comfy-Org/Wan_2.2_ComfyUI_Repackaged` — pre-converted to fp8 + split for ComfyUI loaders.

```bash
mkdir -p /data/ai/02-models/wan22

# Both files are REQUIRED — they are the two MoE experts, not alternatives
# High-noise expert (early denoising — layout and motion)
huggingface-cli download Comfy-Org/Wan_2.2_ComfyUI_Repackaged   split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors   --local-dir /data/ai/02-models/wan22

# Low-noise expert (late denoising — detail and texture)
huggingface-cli download Comfy-Org/Wan_2.2_ComfyUI_Repackaged   split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors   --local-dir /data/ai/02-models/wan22

# Text encoder — comes from Wan 2.1 repo (Wan 2.2 Comfy-Org repo doesn't include it)
huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged   split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors   --local-dir /data/ai/02-models/clip

# VAE — from Wan 2.1 repo (shared with Wan 2.2)
huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged   split_files/vae/wan_2.1_vae.safetensors   --local-dir /data/ai/02-models/vae
```

> [!warning] If Comfy-Org/Wan_2.2_ComfyUI_Repackaged 404s
> Comfy-Org sometimes delays repackaging new releases. If the above fails, use the official Alibaba repo directly. Note: this downloads raw bf16 weights (~56GB) — use only as a fallback.
>
> **Correct fallback repo name is `Wan-AI/Wan2.2-T2V-A14B`** (the "A" means Active 14B — MoE architecture):
> ```bash
> # Fallback — official Alibaba repo (bf16, much larger download ~56GB)
> huggingface-cli download Wan-AI/Wan2.2-T2V-A14B >   --local-dir /data/ai/02-models/wan22
> ```
> The previous fallback command used `Wan-AI/Wan2.2-T2V-14B` which does NOT exist — that caused the 404 you saw.

> [!tip] I2V — Image-to-Video variant
> If you want to animate still images (I2V), download these two files instead of (or alongside) T2V:
> ```bash
> huggingface-cli download Comfy-Org/Wan_2.2_ComfyUI_Repackaged >   split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors >   --local-dir /data/ai/02-models/wan22
>
> huggingface-cli download Comfy-Org/Wan_2.2_ComfyUI_Repackaged >   split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors >   --local-dir /data/ai/02-models/wan22
> ```
> Text encoder and VAE are shared with T2V — no additional downloads needed.

### 5.4 Wan 2.1 1.3B — Fast Iteration (Keep)

```bash
# 8GB VRAM, great for prompt testing before committing to 14B generation
huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged \
  split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors \
  --local-dir /data/ai/02-models/wan22
# VAE + encoder already downloaded above
```

### 5.5 Unrestricted-local Wan Variants

Two censorship layers exist independently — both need addressing:

| Layer | Controls | Solution |
|-------|----------|---------|
| LLM (vLLM) | Prompt enhancement refusals | Dolphin / Hermes models — Phase 3 |

```bash
# Search HuggingFace: "wan2.2 unrestricted-local" or "wan2.1 unrestricted-local"
# Place weights:
/data/ai/02-models/wan22/    # unrestricted-local model weights
```

---

### 5.6 HunyuanVideo 1.5 — Quality Video Model

Replaces the original HunyuanVideo bf16 entirely. 8.3B parameters vs original 13B.

**VRAM by file format:**
- T2V fp16 (`hunyuanvideo1.5_720p_t2v_fp16`): ~17GB — runs concurrently with Hermes 8B (16+17=33GB ❌, stop vLLM first) or Dolphin 24B AWQ (12+17=29GB ✅)
- I2V fp8 (`hunyuanvideo1.5_720p_i2v_cfg_distilled_fp8_scaled`): ~14GB — runs concurrently with Dolphin 24B AWQ (12+14=26GB ✅)
- SR fp8: ~6GB additional on top of whichever model is running

```bash
mkdir -p /data/ai/02-models/hunyuan15

# T2V — text-to-video 720p fp16 (~26GB, best quality)
huggingface-cli download Comfy-Org/HunyuanVideo_1.5_repackaged \
  split_files/diffusion_models/hunyuanvideo1.5_720p_t2v_fp16.safetensors \
  --local-dir /data/ai/02-models/hunyuan15

# I2V — image-to-video 720p fp8 (~14GB, concurrent with vLLM)
huggingface-cli download Comfy-Org/HunyuanVideo_1.5_repackaged \
  split_files/diffusion_models/hunyuanvideo1.5_720p_i2v_cfg_distilled_fp8_scaled.safetensors \
  --local-dir /data/ai/02-models/hunyuan15

# SR — built-in super-resolution 720p → 1080p (no ESRGAN needed)
huggingface-cli download Comfy-Org/HunyuanVideo_1.5_repackaged \
  split_files/diffusion_models/hunyuanvideo1.5_720p_sr_distilled_fp8_scaled.safetensors \
  --local-dir /data/ai/02-models/hunyuan15

# VAE — note naming uses hunyuanvideo15 prefix
huggingface-cli download Comfy-Org/HunyuanVideo_1.5_repackaged \
  split_files/vae/hunyuanvideo15_vae_fp16.safetensors \
  --local-dir /data/ai/02-models/vae

# Text encoder — from original HunyuanVideo repo (1.5 shares same encoder)
huggingface-cli download Comfy-Org/HunyuanVideo_repackaged \
  split_files/text_encoders/llava_llama3_fp8_scaled.safetensors \
  --local-dir /data/ai/02-models/clip
```

> [!tip] HunyuanVideo 1.5 vs Original
> | | Original bf16 | **1.5 fp8** |
> |---|---|---|
> | Parameters | 13B | **8.3B** |
> | VRAM | ~30GB | **~14GB** |
> | I2V steps | 50 | **8–12** |
> | vLLM concurrent | ❌ | **✅** |
> | 1080p built-in | ❌ | **✅** |

---

---

## Verified Model Inventory — As Downloaded on Disk

*Last verified: 2026-04-30. Use as ground truth for building ComfyUI workflows and as context for AI assistants when setting up workflows.*

```
/data/ai/02-models/
│
├── vllm/                                          ← LLM models for vLLM inference
│   ├── hermes-3-8b/                              ✅ DOWNLOADED
│   │   ├── config.json
│   │   ├── tokenizer.json
│   │   ├── model-00001-of-00004.safetensors      (5.0GB)
│   │   ├── model-00002-of-00004.safetensors      (5.0GB)
│   │   ├── model-00003-of-00004.safetensors      (4.9GB)
│   │   └── model-00004-of-00004.safetensors      (1.2GB)
│   │   Total: ~16GB bfloat16
│   │
│   └── Dolphin3.0-R1-Mistral-24B-AWQ/            ✅ COMPLETE (3 shards, ~12GB INT4)
│
├── flux2/                                         ← FLUX.2 klein image models
│   ├── flux-2-klein-4b-fp8.safetensors           ✅ COMPLETE (~4GB fp8)
│   └── flux-2-klein-base-9b-fp8.safetensors      ✅ COMPLETE (~29GB fp8)
│
├── flux1/                                         ← FLUX.1 Dev (Apache 2.0 commercial)
│   └── flux1-dev.safetensors                     ✅ COMPLETE (~17GB)
│
├── wan22/                                         ← Wan 2.2 video models
│   └── split_files/
│       └── diffusion_models/
│           ├── wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors  ✅ (14.3GB)
│           ├── wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors   ✅ (14.3GB)
│           ├── wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors  ✅ (14.3GB)
│           ├── wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors   ✅ (14.3GB)
│           └── wan2.1_t2v_1.3B_fp16.safetensors                  ✅ BONUS (3GB)
│
├── hunyuan15/                                     ← HunyuanVideo 1.5 — ALL COMPLETE
│   └── split_files/
│       └── diffusion_models/
│           ├── hunyuanvideo1.5_720p_t2v_fp16.safetensors         ✅ (~17GB)
│           ├── hunyuanvideo1.5_720p_i2v_cfg_distilled_fp8_scaled.safetensors  ✅ (~14GB)
│           └── hunyuanvideo1.5_720p_sr_distilled_fp8_scaled.safetensors       ✅ (~14GB)
│
├── clip/                                          ← Shared text encoders — ALL COMPLETE
│   ├── clip_l.safetensors                        ✅ FLUX.1 CLIP-L
│   ├── t5xxl_fp16.safetensors                    ✅ FLUX.1 T5
│   └── split_files/
│       └── text_encoders/
│           ├── qwen_3_4b_fp4_flux2.safetensors   ✅ FLUX.2 4B encoder
│           ├── qwen_3_8b_fp8mixed.safetensors     ✅ FLUX.2 9B encoder
│           ├── umt5_xxl_fp8_e4m3fn_scaled.safetensors  ✅ Wan encoder
│           └── llava_llama3_fp8_scaled.safetensors     ✅ HunyuanVideo encoder
│
├── vae/                                           ← Shared VAE weights — ALL COMPLETE
│   ├── ae.safetensors                            ✅ FLUX.1 VAE
│   └── split_files/
│       └── vae/
│           ├── flux2-vae.safetensors              ✅ (336MB)
│           ├── wan_2.1_vae.safetensors            ✅ (254MB)
│           └── hunyuanvideo15_vae_fp16.safetensors  ✅ (~1GB)
│
├── lora/                                          ← LoRA adapters (empty — optional)
│
└── esrgan/                                        ← Upscaling (empty — optional)
```

## model_paths.yaml — Updated for Your Actual Disk Layout

> [!important] Files landed in nested `split_files/` subdirectories
> `huggingface-cli download repo file --local-dir /path` preserves the repo folder
> structure. So your Wan 2.2 files are at `/models/wan22/split_files/diffusion_models/`
> not at `/models/wan22/` directly. Adding both paths below ensures ComfyUI finds everything.

```yaml
# /data/ai/06-configs/creative-stack/model_paths.yaml

comfyui:
    checkpoints: |
        /models/flux1
        /models/flux2

    unet: |
        /models/flux1
        /models/flux2

    diffusion_models: |
        /models/hunyuan15
        /models/wan22
        /models/wan22/split_files/diffusion_models

    clip: |
        /models/clip
        /models/clip/split_files/text_encoders

    text_encoders: |
        /models/clip
        /models/clip/split_files/text_encoders

    vae: |
        /models/vae
        /models/vae/split_files/vae

    loras: |
        /models/lora

    upscale_models: |
        /models/esrgan
```

## Download Status — Final (verified 2026-04-30)

> [!success] All creative models are downloaded and complete. Every workflow in the catalogue is fully supported.

| Status | Model | Size | Notes |
|--------|-------|------|-------|
| ✅ Complete | Hermes 3 8B | ~16GB | LLM daily driver |
| ✅ Complete | Dolphin 24B AWQ | ~12GB | LLM upgrade — concurrent with all video |
| ✅ Complete | FLUX.2 klein 4B | ~4GB | Fast image generation |
| ✅ Complete | FLUX.2 klein 9B | ~29GB | Maximum quality images |
| ✅ Complete | FLUX.1 Dev | ~17GB | Apache 2.0 commercial licence |
| ✅ Complete | Wan 2.2 T2V (both experts) | 28.6GB | Primary text-to-video |
| ✅ Complete | Wan 2.2 I2V (both experts) | 28.6GB | Image-to-video animation |
| ✅ Complete | Wan 2.1 1.3B | ~3GB | Fast draft video |
| ✅ Complete | HunyuanVideo 1.5 T2V fp16 | ~17GB | Cinema quality T2V |
| ✅ Complete | HunyuanVideo 1.5 I2V fp8 | ~14GB | Cinema quality I2V |
| ✅ Complete | HunyuanVideo 1.5 SR fp8 | ~14GB | 720p → 1080p upscaler |
| ✅ Complete | All text encoders (5 files) | ~27GB | Qwen3 4B/8B, T5, CLIP-L, UMT5, LLaVA |
| ✅ Complete | All VAEs (4 files) | ~2GB | flux2, ae, wan, hunyuanvideo15 |
| ❌ Delete | Dolphin3.0-R1-Mistral-24B (full bf16) | ~48GB | OOMs 32GB — unusable, AWQ version present |
| ⬜ Future | Gemma4 26B MoE fp8 (orchestrator) | ~14GB | Layer 2 agent brain |
| ⬜ Future | Qwen3 27B AWQ (orchestrator alt) | ~14GB | Layer 2 agent brain alternative |

**One action required — delete 48GB unusable folder:**
```bash
rm -rf /data/ai/02-models/vllm/Dolphin3.0-R1-Mistral-24B
du -sh /data/ai/02-models/vllm/
# Should show only: hermes-3-8b/ and Dolphin3.0-R1-Mistral-24B-AWQ/
```

---

### 5.7 Updated model_paths.yaml

Update ComfyUI's model paths config to reflect new folder names:

```yaml
# /data/ai/06-configs/creative-stack/model_paths.yaml
#
# IMPORTANT: ComfyUI expects newline-separated strings using YAML block scalar (|)
# Do NOT use YAML list syntax (- /path) — it causes:
#   TypeError: list indices must be integers or slices, not str
#
# Correct format: use | and indent paths, no dashes

comfyui:
    # FLUX models use the 'checkpoints' and 'unet' keys
    checkpoints: |
        /models/flux1
        /models/flux2

    unet: |
        /models/flux1
        /models/flux2

    # Video models (HunyuanVideo, Wan) use diffusion_models
    diffusion_models: |
        /models/hunyuan15
        /models/wan22

    # Text encoders: Qwen3 (FLUX.2), T5/CLIP-L (FLUX.1), LLaVA-Llama3 (HunyuanVideo), UMT5 (Wan)
    clip: |
        /models/clip

    text_encoders: |
        /models/clip

    vae: |
        /models/vae

    loras: |
        /models/lora

    upscale_models: |
        /models/esrgan
```

---

### 5.8 ESRGAN — Optional Fallback Only

HunyuanVideo 1.5's built-in SR UNet handles video upscaling. ESRGAN is only needed for FLUX.1 image upscaling.

```bash
mkdir -p /data/ai/02-models/esrgan
wget -O /data/ai/02-models/esrgan/RealESRGAN_x4plus.pth \
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
```


---

---

## Interactive Workflow Tiles

> [!tip] Open the interactive version
> A standalone HTML file with filterable tiles, dark theme, and VRAM table is saved alongside this document.
> Open in any browser: `workflow_catalogue.html`
> — or double-click the file in your file manager.

The tiles below are the visual reference embedded in this document. Each tile maps directly to the detailed workflow entry above it.

---

### Tier 1 — Fast Draft

```
┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐
│ FLUX.2 4B quick image      [Image]  │  │ Wan 2.1 1.3B draft video   [Video]  │
│                                     │  │                                     │
│ Fast daily image. 1.2s per image.   │  │ Ultra-fast 480p for testing motion  │
│ Concurrent with Dolphin 24B AWQ.    │  │ and composition before committing   │
│ For iteration and testing before    │  │ to a full 14B render. Test camera   │
│ final quality renders.              │  │ moves and scene timing here first.  │
│                                     │  │                                     │
│ → flux-2-klein-4b-fp8               │  │ → wan2.1_t2v_1.3B_fp16             │
│ → qwen_3_4b_fp4_flux2               │  │ → umt5_xxl_fp8                     │
│ → flux2-vae                         │  │ → wan_2.1_vae                      │
│                                     │  │                                     │
│ VRAM ~8GB  Speed ~1.2s  LLM: Yes    │  │ VRAM ~6GB  Speed ~4min  Res: 480p  │
│                                [T1] │  │                                [T1] │
└─────────────────────────────────────┘  └─────────────────────────────────────┘
```

---

### Tier 2 — Production Quality

```
┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐
│ FLUX.1 Dev commercial image [Image] │  │ Wan 2.2 T2V — text to video [Video] │
│                                     │  │                                     │
│ Apache 2.0 licensed — safe for      │  │ Primary video model. MoE dual-      │
│ commercial deliverables. T5 +       │  │ expert: high-noise expert handles   │
│ CLIP-L dual encoder for richer      │  │ layout/motion, low-noise handles    │
│ text understanding.                 │  │ detail/texture. 480p and 720p.      │
│                                     │  │                                     │
│ → flux1-dev                         │  │ → wan2.2_t2v_high_noise_14B_fp8    │
│ → t5xxl_fp16 + clip_l               │  │ → wan2.2_t2v_low_noise_14B_fp8     │
│ → ae.safetensors                    │  │ → umt5_xxl_fp8 → wan_2.1_vae       │
│                                     │  │                                     │
│ VRAM ~18GB  Speed ~15s  ✅ Comml    │  │ VRAM ~14GB  Res 480/720p  LLM: Yes │
│                                [T2] │  │                                [T2] │
└─────────────────────────────────────┘  └─────────────────────────────────────┘

┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐
│ Wan 2.2 I2V — animate image [Video] │  │ Hermes 8B prompt enhancer   [LLM]   │
│                                     │  │                                     │
│ Takes a still image and animates    │  │ Always-on prompt enhancement via    │
│ it — camera movement, character     │  │ vLLM. Takes rough ideas and         │
│ motion, environmental effects.      │  │ expands into detailed cinematic     │
│ Use after FLUX.2 4B generates       │  │ descriptions. Runs alongside all    │
│ your keyframe image.                │  │ video models. Temp 0.7.             │
│                                     │  │                                     │
│ → wan2.2_i2v_high_noise_14B_fp8    │  │ → Hermes 3 8B / vLLM port 8000     │
│ → wan2.2_i2v_low_noise_14B_fp8     │  │   API: host.docker.internal:8000   │
│ → umt5_xxl_fp8 → wan_2.1_vae       │  │   Model name: local-llm       │
│                                     │  │                                     │
│ VRAM ~14GB  Input: Img+text  ✅LLM  │  │ VRAM 25GB total  ~120 tok/s  T=0.7 │
│                                [T2] │  │                                [T2] │
└─────────────────────────────────────┘  └─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Dolphin 24B AWQ enhancer    [LLM]   │
│                                     │
│ Higher quality prompt expansion     │
│ with DeepSeek-R1 reasoning. Use     │
│ for complex multi-character scenes, │
│ cinematographer references, or      │
│ detailed atmosphere descriptions.   │
│                                     │
│ → Dolphin 24B AWQ / vLLM :8000     │
│   Model name: local-llm       │
│   Temp: 0.07 REQUIRED              │
│                                     │
│ VRAM 14GB+14GB video  Temp: 0.07   │
│                                [T2] │
└─────────────────────────────────────┘
```

---

### Tier 3 — Cinematic Quality

```
┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐
│ HunyuanVideo 1.5 T2V fp16  [Video]  │  │ HunyuanVideo 1.5 I2V fp8   [Video]  │
│                                     │  │                                     │
│ Highest quality text-to-video.      │  │ Animate a reference image at 720p.  │
│ Full fp16 precision — more detail   │  │ fp8 saves 3GB vs T2V fp16 allowing  │
│ and temporal consistency than fp8.  │  │ concurrent with Dolphin 24B AWQ     │
│ Best for hero scenes and final      │  │ (12+14=26GB). Ideal for specific    │
│ deliverables.                       │  │ keyframe animation.                 │
│                                     │  │                                     │
│ → hunyuanvideo1.5_720p_t2v_fp16    │  │ → hunyuanvideo1.5_720p_i2v_fp8     │
│ → llava_llama3_fp8_scaled           │  │ → llava_llama3_fp8_scaled           │
│ → hunyuanvideo15_vae_fp16           │  │ → hunyuanvideo15_vae_fp16           │
│                                     │  │                                     │
│ VRAM ~17GB  720p  ~8–12 min         │  │ VRAM ~14GB  720p  LLM concurrent ✅ │
│                                [T3] │  │                                [T3] │
└─────────────────────────────────────┘  └─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ HunyuanVideo T2V + SR → 1080p [Vid] │
│                                     │
│ Two-stage pipeline. Stage 1         │
│ generates 720p via T2V fp16.        │
│ Stage 2 runs built-in SR model      │
│ in latent space to reach 1080p.     │
│ No external upscaler needed.        │
│                                     │
│ Stage 1: T2V fp16 → 720p latent    │
│ Stage 2: SR distilled fp8 → 1080p  │
│ → hunyuanvideo15_vae_fp16           │
│                                     │
│ VRAM ~23GB peak  Output: 1080p      │
│                                [T3] │
└─────────────────────────────────────┘
```

---

### Tier 4 — Full AI Pipelines

```
┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐
│ Daily creative pipeline    [Full]   │  │ Cinematic production pipeline [Full] │
│                                     │  │                                     │
│ Rough idea → short video in one     │  │ Maximum quality end-to-end.         │
│ continuous workflow. Everything     │  │ 4-stage pipeline producing          │
│ runs concurrently at ~26GB.         │  │ cinema-ready 1080p deliverable.     │
│ Best for high-volume daily work.    │  │                                     │
│                                     │  │ Concept                             │
│ Rough idea                          │  │ → Dolphin AWQ (shot description)    │
│ → Dolphin AWQ (enhanced prompt)     │  │ → FLUX.2 4B (keyframe image)        │
│ → FLUX.2 4B (keyframe image)        │  │ → HunyuanVideo I2V fp8 (720p)      │
│ → Wan 2.2 I2V (video)               │  │ → HunyuanVideo SR fp8 (1080p)      │
│                                     │  │                                     │
│ VRAM ~26GB  Concurrent ✅  480–720p │  │ VRAM ~26GB peak  Output: 1080p      │
│                                [T4] │  │                                [T4] │
└─────────────────────────────────────┘  └─────────────────────────────────────┘

┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐
│ Screenplay → scene batch   [Full]   │  │ Commercial pipeline (Apache 2.0)    │
│                                     │  │                                [Full]│
│ Dolphin 24B AWQ in script mode      │  │                                     │
│ (96K context) writes a complete     │  │ Fully commercial-safe pipeline.     │
│ multi-scene script. Each shot       │  │ All outputs deliverable to clients  │
│ feeds into FLUX.2 4B for keyframes  │  │ without IP concerns.                │
│ then Wan 2.2 I2V as a batch.        │  │                                     │
│                                     │  │ Brief                               │
│ Treatment                           │  │ → Dolphin AWQ (safe prompt)         │
│ → Dolphin AWQ 96K (full script)     │  │ → FLUX.1 Dev + T5 + CLIP-L          │
│ → FLUX.2 4B (per-scene keyframes)   │  │ → Wan 2.2 I2V (optional animation) │
│ → Wan 2.2 I2V (animated scenes)     │  │                                     │
│                                     │  │ Licence: Apache 2.0  VRAM ~26GB     │
│ Context: up to 96K tokens      [T4] │  │                                [T4] │
└─────────────────────────────────────┘  └─────────────────────────────────────┘
```

> [!tip] Full interactive version with filters and VRAM table
> Open `workflow_catalogue.html` in your browser for the filterable dark-theme version.
> It includes all 11 tiles plus the complete VRAM state reference table.

### Tier 4.5 — Editing & Restoration (client post-production)

> [!important] This is the tier the client work actually lives in
> "Remove the rain," "remove that vehicle," "reframe this shot," "VFX it" are **editing** tasks
> on existing footage — not text/image-to-video generation. These tools take the client plate
> as input and modify it, preserving everything that must stay.

```
┌──────────────────────────────────────────────────────────────────────┐
│ [T4.5]  VOID — interaction-aware object removal        Apache 2.0      │
│  Load Video → SAM3 (mask by label) → VOID Pass1 → VOID Pass2           │
│  Removes object + ITS shadows, reflections, induced motion            │
│  Models: void_pass1/2 · cogvideox_vae · raft · sam3.1 · t5xxl_fp16    │
│  Native in ComfyUI (PR #13403) — needs latest/nightly. ~CogVideoX VRAM │
└──────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────┐
│ [T4.5]  Wan 2.1 VACE 14B — unified video edit          Apache 2.0      │
│  Move/Swap/Reference/Expand/Animate-Anything · inpaint · OUTPAINT      │
│  The reframe / aspect-change / object-swap workhorse (fully native)    │
│  Wan 2.2 VACE = blocks-only, Kijai WanVideoWrapper path — use 2.1 here │
└──────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────┐
│ [T4.5]  Support: SAM2/SAM3 (auto-mask) · DiffuEraser (alt inpaint)    │
│         LBM (relight subject to match plate) · BiRefNet (matte)        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## ComfyUI Workflow Catalogue — All Generation Combinations

*Use this section as context when building ComfyUI workflow JSON files. Each entry lists the exact model files, their paths on disk, and what the workflow achieves.*

---

### Tier 1 — Fast Draft (test before committing render time)

#### Workflow 1.1 — FLUX.2 4B quick image
**What it achieves:** Fast daily image generation. 1.2 seconds per image. Good for prompt iteration and testing compositions before committing to the 9B model.
**Use when:** Testing a prompt idea, iterating on composition, generating reference frames quickly.
**Models used:**
- Diffusion: `flux2/flux-2-klein-4b-fp8.safetensors`
- Text encoder: `clip/split_files/text_encoders/qwen_3_4b_fp4_flux2.safetensors`
- VAE: `vae/split_files/vae/flux2-vae.safetensors`

**VRAM:** ~8GB | **Speed:** ~1.2s | **LLM concurrent:** Yes (with Dolphin 24B AWQ)

---

#### Workflow 1.2 — Wan 2.1 1.3B draft video
**What it achieves:** Ultra-fast 480p video for testing motion, camera moves, and scene timing before committing to a 14B render.
**Use when:** Testing motion choreography, validating timing, quick client previews before full quality render.
**Models used:**
- Diffusion: `wan22/split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors`
- Text encoder: `clip/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- VAE: `vae/split_files/vae/wan_2.1_vae.safetensors`

**VRAM:** ~6GB | **Speed:** ~4 min | **Resolution:** 480p | **LLM concurrent:** Yes

---

### Tier 2 — Production Quality (daily workhorses)

#### Workflow 2.1 — FLUX.1 Dev commercial image
**What it achieves:** Apache 2.0 licensed images safe for commercial use. T5 + CLIP-L dual encoder gives richer text understanding than single-encoder models.
**Use when:** Client work where licence matters, commercial deliverables, projects requiring explicit Apache 2.0 clearance.
**Models used:**
- Diffusion: `flux1/flux1-dev.safetensors`
- Text encoders: `clip/t5xxl_fp16.safetensors` + `clip/clip_l.safetensors`
- VAE: `vae/ae.safetensors`

**VRAM:** ~18GB | **Speed:** ~15s | **Licence:** Apache 2.0 commercial OK | **LLM concurrent:** Yes (Dolphin AWQ)

---

#### Workflow 2.2 — Wan 2.2 T2V text to video
**What it achieves:** Primary video model. MoE dual-expert architecture — high-noise expert handles layout and motion, low-noise handles detail and texture. Supports 480p and 720p, multilingual text in frame.
**Use when:** Most video generation tasks. Strong motion dynamics, excellent for action sequences and atmospheric scenes.
**Models used (both files required — they are the two MoE experts):**
- Expert 1 (layout/motion): `wan22/split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors`
- Expert 2 (detail/texture): `wan22/split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors`
- Text encoder: `clip/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- VAE: `vae/split_files/vae/wan_2.1_vae.safetensors`

**VRAM:** ~14GB | **Resolution:** 480p/720p | **LLM concurrent:** Yes (Dolphin AWQ, 14+14=28GB)

---

#### Workflow 2.3 — Wan 2.2 I2V animate an image
**What it achieves:** Takes a still image and animates it — camera movement, character motion, environmental effects. Works with any input image: generated by FLUX.2 or a real photograph.
**Use when:** Animating FLUX.2-generated keyframes, bringing reference photos to life, controlled character animation.
**Models used:**
- Expert 1: `wan22/split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`
- Expert 2: `wan22/split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`
- Text encoder: `clip/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- VAE: `vae/split_files/vae/wan_2.1_vae.safetensors`

**VRAM:** ~14GB | **Input:** Image + text prompt | **LLM concurrent:** Yes (Dolphin AWQ)

> [!warning] Wan 2.2 14B is a TWO-SAMPLER pipeline — not one sampler with two files loaded
> The MoE design requires two sequential sampler passes, with steps split between them:
> ```
>   high-noise expert  → sampler pass 1  (composition / layout / motion)
>          ↓ latent
>   low-noise expert   → sampler pass 2  (detail / texture)
>          ↓
>   VAE decode
> ```
> Loading both files but running a SINGLE sampler (or only the high-noise pass) leaves the
> detail pass undone — this produces the crystalline / blurry-moving-shadow, under-resolved
> artifact. The official native template ("Browse Templates → Video → Wan2.2 14B I2V") wires
> this correctly with two `Load Diffusion Model` nodes + two sampler passes. Rebuild the
> workflow from that template rather than patching an older single-sampler graph.
>
> **Native vs Kijai:** standardize on the native template (stock `Load Diffusion Model` ×2 +
> native sampler chain, `umt5_xxl_fp8` encoder, `wan_2.1_vae`). Mixing native and Kijai
> `WanVideo*` nodes is a top cause of red nodes. Don't mix ecosystems.
>
> **Speed-LoRA path:** with Lightx2v/Lightning 4-step LoRA set **CFG = 1.0** (disables the
> negative prompt; required or the LoRA deep-fries the image), ~4 steps high + 4 steps low.
> LoRA placement: only Wan 2.2 high-noise LoRAs in the high-noise stage; Wan 2.1 LoRAs work in
> the low-noise stage only — never cross them. SageAttention strongly recommended.
>
> **Staged debug:** lock seed → save a known-good FLUX frame → LoadImage to bypass FLUX →
> confirm BOTH experts load AND both sampler passes run → run Wan in isolation → re-add FLUX.

> [!warning] Wan open-weights ceiling = 2.2 — do not chase 2.5/2.6
> Alibaba released Wan 2.2 as open-source (Apache 2.0, July 2025). Wan 2.5 and 2.6 are
> primarily **commercial / API-only** (cloud, paid per-second). They violate the sovereign,
> local, open-source, no-paid-tools constraint. Wan 2.2 (generation) + Wan 2.1 VACE (editing)
> are the open ceiling for this build. Revisit only if Alibaba open-weights a later version.

---

#### Workflow 2.4 — Hermes 8B prompt enhancer (LLM only)
**What it achieves:** Always-on prompt enhancement via vLLM. Takes rough ideas and expands into detailed cinematic descriptions. Runs alongside all video models with no VRAM conflict when using Dolphin AWQ.
**Use when:** Every session — connect to ComfyUI LLM Party node at `http://host.docker.internal:8000/v1`.
**Model:** `vllm/hermes-3-8b/` — served as `local-llm` on port 8000
**Temperature:** 0.7 | **VRAM:** 25GB total (vLLM at 0.80 utilization)

---

#### Workflow 2.5 — Dolphin 24B AWQ prompt enhancer (LLM only)
**What it achieves:** Higher quality prompt expansion with DeepSeek-R1 reasoning. Richer, more specific output than Hermes 8B for complex scenes. Runs concurrently with HunyuanVideo 1.5 I2V (12+14=26GB).
**Use when:** Complex multi-character scenes, specific cinematographer references, atmosphere-heavy descriptions.
**Model:** `vllm/Dolphin3.0-R1-Mistral-24B-AWQ/` — served as `local-llm`
**Temperature:** 0.07 REQUIRED | **VRAM:** 14GB (vLLM at 0.45 utilization)

---

### Tier 3 — Cinematic Quality (hero shots and final renders)

#### Workflow 3.1 — HunyuanVideo 1.5 T2V fp16
**What it achieves:** Highest quality text-to-video. Full fp16 precision gives superior detail and temporal consistency vs fp8. Best for establishing shots, hero scenes, and any sequence where quality is non-negotiable.
**Use when:** Final deliverables, portfolio work, scenes that will be seen at full quality.
**Models used:**
- Diffusion: `hunyuan15/split_files/diffusion_models/hunyuanvideo1.5_720p_t2v_fp16.safetensors`
- Text encoder: `clip/split_files/text_encoders/llava_llama3_fp8_scaled.safetensors`
- VAE: `vae/split_files/vae/hunyuanvideo15_vae_fp16.safetensors`

**VRAM:** ~17GB | **Resolution:** 720p | **Speed:** ~8–12 min | **LLM concurrent:** Yes (Dolphin AWQ, 12+17=29GB)

---

#### Workflow 3.2 — HunyuanVideo 1.5 I2V fp8
**What it achieves:** Animate a reference image at 720p with HunyuanVideo quality. fp8 saves 3GB vs T2V fp16 allowing full concurrency with Dolphin 24B AWQ (12+14=26GB). Ideal when you have a specific keyframe to work from.
**Use when:** Animating FLUX.2-generated keyframes at maximum quality, controlled character motion from reference images.
**Models used:**
- Diffusion: `hunyuan15/split_files/diffusion_models/hunyuanvideo1.5_720p_i2v_cfg_distilled_fp8_scaled.safetensors`
- Text encoder: `clip/split_files/text_encoders/llava_llama3_fp8_scaled.safetensors`
- VAE: `vae/split_files/vae/hunyuanvideo15_vae_fp16.safetensors`

**VRAM:** ~14GB | **Resolution:** 720p | **LLM concurrent:** Yes (Dolphin AWQ, 26GB total)

---

#### Workflow 3.3 — HunyuanVideo 1.5 T2V + SR upscale (720p → 1080p)
**What it achieves:** Two-stage pipeline. Stage 1 generates 720p video via T2V fp16. Stage 2 runs the built-in SR model in latent space to reach 1080p. No external upscaler needed — both stages are within HunyuanVideo 1.5. Cinema-ready output.
**Use when:** Final deliverables requiring 1080p, portfolio showreel, client presentations.
**Models used (run sequentially):**
- Stage 1: `hunyuanvideo1.5_720p_t2v_fp16.safetensors` → 720p latent
- Stage 2: `hunyuan15/split_files/diffusion_models/hunyuanvideo1.5_720p_sr_distilled_fp8_scaled.safetensors` → 1080p
- Text encoder: `clip/split_files/text_encoders/llava_llama3_fp8_scaled.safetensors`
- VAE: `vae/split_files/vae/hunyuanvideo15_vae_fp16.safetensors`

**VRAM:** ~23GB peak | **Output:** 1080p | **Stages:** 2 sequential

---

### Tier 4 — Full AI Pipelines (LLM → Image → Video)

#### Workflow 4.1 — Daily creative pipeline (concurrent, fast)
**What it achieves:** Rough idea → short video in one continuous workflow. Everything runs concurrently at 26GB total VRAM. Best for high-volume daily creative work.

**Node chain:**
```
[Text Input: rough idea]
    ↓
[LLM Party API Node] → Dolphin 24B AWQ (enhanced prompt)
    ↓
[CLIP Text Encode] → FLUX.2 4B + Qwen3 4B (keyframe image)
    ↓
[Wan 2.2 I2V Loader] → wan2.2_i2v_high/low_noise (video)
    ↓
[Video Output]
```
**Peak VRAM:** ~26GB | **LLM model:** Dolphin 24B AWQ | **Output:** 480–720p video

---

#### Workflow 4.2 — Cinematic production pipeline (maximum quality)
**What it achieves:** Maximum quality end-to-end. Dolphin 24B AWQ writes the shot description. FLUX.2 4B generates the keyframe. HunyuanVideo 1.5 I2V animates at 720p. SR upscales to 1080p. Four stages, cinema-ready output.

**Node chain:**
```
[Text Input: scene concept]
    ↓
[LLM Party API Node] → Dolphin 24B AWQ (detailed shot description)
    ↓
[CLIP Text Encode] → FLUX.2 4B + Qwen3 4B (keyframe image)
    ↓
[HunyuanVideo 1.5 I2V Loader] → i2v_fp8 (720p video)
    ↓
[HunyuanVideo 1.5 SR Loader] → sr_fp8 (1080p upscale)
    ↓
[Video Output: 1080p]
```
**Peak VRAM:** ~26GB | **Output:** 1080p | **Stages:** 4

---

#### Workflow 4.3 — Screenplay → scene batch pipeline (long-form)
**What it achieves:** Full production pipeline. Dolphin 24B AWQ in script mode (96K context) writes a complete multi-scene script with per-shot descriptions. Each shot feeds into FLUX.2 4B for keyframes, then Wan 2.2 I2V for animation. Produces a coordinated sequence of scenes from a single treatment document.

**Process:**
1. Switch vLLM to Dolphin 24B AWQ script mode (`VLLM_GPU_MEM=0.85`, `VLLM_MAX_LEN=98304`)
2. Feed full treatment → Dolphin generates complete script with shot descriptions
3. Extract individual shot descriptions
4. Batch through FLUX.2 4B → keyframe images for each shot
5. Batch through Wan 2.2 I2V → animated video for each shot

**Context:** Up to 96K tokens (full feature film script) | **LLM VRAM:** 27GB standalone

---

#### Workflow 4.4 — Commercial production pipeline (Apache 2.0 safe)
**What it achieves:** Fully commercial-safe pipeline using only Apache 2.0 licensed models. Dolphin 24B AWQ enhances the brief. FLUX.1 Dev generates the image. Optional Wan 2.2 I2V for animation. Everything deliverable to clients without IP concerns.

**Node chain:**
```
[Client brief]
    ↓
[LLM Party] → Dolphin 24B AWQ (commercial-safe prompt)
    ↓
[FLUX.1 Dev + T5 fp16 + CLIP-L + ae VAE] (commercial image)
    ↓
[Optional: Wan 2.2 I2V] (animated version)
```
**Licence:** Apache 2.0 | **VRAM:** ~26GB peak

---

### Tier 4.5 — Editing & Restoration (client post-production)

> [!warning] Generation vs editing — pick the right tool
> The Tier 1–4 generators make new video. Tier 4.5 modifies existing client footage. Most
> client jobs start here. A clip may pass through Tier 4.5 (edit) then Tier 6 (finish to 4K60).

#### Why an editing tier exists
The brief is post-production fixes on shot footage: remove rain, remove a vehicle/person,
change framing, add VFX — while shadows, reflections, lighting, and untouched regions stay
consistent. Pure generation hallucinates these. Dedicated editing/inpainting models are built
to preserve the plate and only change the masked region (and its physical consequences).

#### Workflow 4.5.1 — VOID object/element removal (Netflix, Apache 2.0)
**What it achieves:** Removes an object AND all interactions it induced on the scene — shadows,
reflections, and physical effects (e.g. remove a person holding a guitar → the guitar falls
naturally). Two-pass diffusion on CogVideoX. Temporally coherent fill.
**Native in ComfyUI** via PR #13403 — no custom node, but requires latest/nightly ComfyUI.
**License:** Apache 2.0 — client-safe.

Models (download to the paths shown; HF repo `Comfy-Org/void-model` unless noted):
```
ComfyUI/models/diffusion_models/void_pass1.safetensors      (primary pass)
ComfyUI/models/diffusion_models/void_pass2.safetensors      (temporal refinement)
ComfyUI/models/vae/cogvideox_vae.safetensors
ComfyUI/models/optical_flow/raft_large_C_T_SKHT_V2-ff5fadd5.safetensors
ComfyUI/models/checkpoints/sam3.1_multiplex_fp16.safetensors   (repo Comfy-Org/sam3.1)
ComfyUI/models/text_encoders/t5xxl_fp16.safetensors            (repo comfyanonymous/flux_text_encoders)
```
On this stack, place these under `/data/ai/02-models/` matching the existing folder scheme
(`vae/`, `clip/` for text encoders, a new `optical_flow/`, and `diffusion_models` under a
`void/` subfolder) and ensure `model_paths.yaml` exposes them. t5xxl_fp16 is already on disk.

Node chain:
```
[Load Video]  (client plate → ComfyUI input/)
      ↓
[SAM3]  object prompt = WHAT to remove (semantic mask; 32-token limit;
        multi-target: "eye:2, window panels:4")
      ↓ mask
[VOID Pass 1]  positive prompt = HOW the hole fills — describe scene AFTER removal,
        not the removal ("empty wet asphalt, overcast daylight, reflections on road")
      ↓
[VOID Pass 2]  optical-flow temporal refine — use for longer/textured clips
      ↓
[VHS_VideoCombine] → client-work/_edit/
```
**Limitation (verbatim from Netflix/Comfy docs):** unclear masks, chaotic motion, or a target
that dominates the frame can give poor results — prompting cannot fix wrong segmentation. Mask
quality is everything. Pass 1 alone is fine for fast iteration; add Pass 2 for delivery.

#### Workflow 4.5.2 — Wan 2.1 VACE editing & reframe (Apache 2.0)
**What it achieves:** Unified video editing — Move-Anything, Swap-Anything, Reference-Anything,
Expand-Anything (**outpainting** for aspect/reframe), Animate-Anything, motion brush, inpaint,
add elements. This is the tool for "director wants a different framing / wider shot / element
swapped." Fully native in ComfyUI.
**Model:** Wan 2.1 VACE 14B (native). Use the existing UMT5 encoder + Wan VAE already on disk.
**Note:** Wan **2.2** VACE is VACE-blocks-only and runs via Kijai's WanVideoWrapper — for the
mature, fully-native editing toolset use **Wan 2.1 VACE 14B**. Reserve Wan 2.2 for generation.

Node chain (object removal/replace variant):
```
[Load Video] → [mask: SAM2/SAM3 or manual] → [WanVaceToVideo]
      → [KSampler] → [VAEDecode] → [TrimVideoLatent]/[CreateVideo]
      → [ImageCompositeMasked] (blend edit back over untouched plate) → save
```
For reframe/aspect change use the VACE **outpainting** template (Expand-Anything).

> [!danger] SAM3 image-mode vs video-mode — the silent VACE crash (fixed v1.5)
> SAM3 has two distinct modes. Image-mode nodes (SAM3Grounding / SAM3_Detect) output a single
> `[1,H,W]` mask. VACE Encode's `input_masks` requires a per-frame `[N,H,W]` mask matching the
> frame count. Feeding an image-mode mask produces:
> `Sizes of tensors must match except in dimension 0. Expected size 21 but got size 1`
> The fix is the four-node SAM3 VIDEO pipeline:
> ```
> LoadSAM3Model ─────────────────────────────┐
> VHS_LoadVideo (IMAGE) → SAM3VideoSegmentation → SAM3Propagate → SAM3VideoOutput → VACE input_masks
> ```
> SAM3VideoSegmentation takes the full IMAGE batch + a text prompt; SAM3Propagate tracks the
> object across all frames; SAM3VideoOutput converts to a standard `[N,H,W]` MASK tensor. This
> is the architecture Shapeshifter now uses. Do NOT revert to image-mode SAM3 for video.
>
> **SAM3 custom node:** `PozzettiAndrea/ComfyUI-SAM3`. Its `install.py` (pixi/comfy-env) may fail
> on RTX 5090 (no CUDA 13 wheels for flash-attn/cc_torch, pixi network blocked) — but it falls
> back to in-process import and registers all 15 SAM3 nodes anyway. The install.py failure is
> NOT fatal. Confirm with: logs show `[comfy-env] Registered 15 total nodes`.
>
> **SAM3 model file:** symlinked as `/app/ComfyUI/models/sam3/sam3.safetensors`.
>
> **Label-matching is semantic, not literal:** functional descriptions beat common names.
> `writing board` worked where `blackboard` and `chalkboard` failed. `clock`/`watch` matched
> fine (common object); `fan` and `board` did not until relabeled.

#### Workflow 4.5.3 — Relight to match plate (LBM)
**What it achieves:** Relights a regenerated/inserted element using an image-based lighting
reference so it matches the original plate's lighting. Pairs directly with the forensic
consistency map's LIGHTING/SHADOWS fields.

#### When to use which (decision table)
| Client ask | Tool | Note |
|---|---|---|
| Remove object/vehicle/person + its shadows/reflections | VOID (4.5.1) | the default removal tool |
| Remove rain / atmospheric layer | VOID or DiffuEraser + SAM3 | inpaint-recreate |
| Reframe / wider shot / aspect change | Wan 2.1 VACE outpaint (4.5.2) | Expand-Anything |
| Swap / insert an object | Wan 2.1 VACE inpaint + ImageCompositeMasked | preserves surround |
| Relight inserted element | LBM (4.5.3) | match plate lighting |
| Auto-masking for any of the above | SAM2 / SAM3 | semantic, text-labelled |
| Literal NEW camera angle of a real scene | (set expectations) | not reliably solved by local open tools mid-2026; VACE gets plausible reframes/extensions, not true novel-view — this stays a VFX/3D problem |

### Forensic JSON → Editing pipeline (revised role)
The Nemotron `_final-bundle.json` (consistency map: lighting, shadows, colour grade, camera,
atmosphere, scale, invariants) is **not** generator conditioning. In an editing pipeline its
jobs are: (1) drive masking/preservation decisions (invariants = regions to protect);
(2) constrain the VOID/VACE fill + LBM relight prompts so the model has specs to obey;
(3) **validate** — a second Nemotron pass scores the output against its own map to catch drift.
There is no community node that ingests this JSON — it's a small custom node/pre-step to build
**after** VOID/VACE work by hand. Do not block the pipeline on it.

### Forensic Bridge — connected (v1.5)

The Nemotron forensic layer is now wired to the editing tier via three scripts in
`/data/ai/01-workspace/nemotron-forensic/`:

```
client plate
  → forensic_analyzer.py (Nemotron, 3 passes, schema_version stamped, pixel-dense Pass 2/3)
  → [optional human edit of human-readable prose]
  → forensic_converter.py → forensic_machine_payload.json
       (SAM3 mask prompts, VOID fill prompt, VACE region spec, LBM lighting, invariants)
  → forensic_to_comfy.py → POST to ComfyUI /prompt → poll /history
```

`forensic_to_comfy.py` injects forensic-derived values into specific node widget values by node
ID. The node IDs come from API-format JSON exports of the Vanisher and Shapeshifter workflows
(ComfyUI UI: Save → API Format). Generation-path consistency additionally requires a visual
pixels.

**Design principle:** Pass 2/3 stay human-readable prose intentionally — a VFX artist reads and
hand-edits before the converter runs. The converter is downstream of human edits, not upstream.

> [!note] Audio stack — on-demand, not wired into every workflow
> The audio stack (Fish Speech voice clone · MuseTalk/LatentSync/Hallo2 lip-sync · YuE music)
> is already architected to plug in (disk hand-off, async queue, ComfyUI-concurrent VRAM).
> Invoke it per-job: needed for re-voicing after a reshoot/reframe, lip-sync to a regenerated
> face, or replacing a music bed (YuE — note MusicGen Stereo is CC-BY-NC, NOT client-safe).
> Skip it for pure visual fixes where the original production audio is carried through. Per the
> audio doc's own judgment, full-body talking heads are still best done by Wan 2.2 I2V.

### Quick Reference — Which Models Go With Which Workflow

| Workflow | Diffusion | Text Encoder | VAE |
|----------|-----------|-------------|-----|
| 1.1 FLUX.2 4B | `flux-2-klein-4b-fp8` | `qwen_3_4b_fp4_flux2` | `flux2-vae` |
| 1.2 Wan 2.1 1.3B | `wan2.1_t2v_1.3B_fp16` | `umt5_xxl_fp8` | `wan_2.1_vae` |
| 2.1 FLUX.1 Dev | `flux1-dev` | `t5xxl_fp16` + `clip_l` | `ae` |
| 2.2 Wan 2.2 T2V | `wan2.2_t2v_high+low_noise` | `umt5_xxl_fp8` | `wan_2.1_vae` |
| 2.3 Wan 2.2 I2V | `wan2.2_i2v_high+low_noise` | `umt5_xxl_fp8` | `wan_2.1_vae` |
| 3.1 HunyuanVideo T2V | `hunyuanvideo1.5_720p_t2v_fp16` | `llava_llama3_fp8` | `hunyuanvideo15_vae` |
| 3.2 HunyuanVideo I2V | `hunyuanvideo1.5_720p_i2v_fp8` | `llava_llama3_fp8` | `hunyuanvideo15_vae` |
| 3.3 HunyuanVideo + SR | `t2v_fp16` then `sr_fp8` | `llava_llama3_fp8` | `hunyuanvideo15_vae` |

All model files are under `/data/ai/02-models/` — paths as listed in the verified inventory above.

---

## Phase 6 — VRAM Management

### 6.1 VRAM Budget (Updated with New Models)

> [!note] VRAM Reality Check
> Wan 2.2 14B fp8 ≈ **14GB** weights in ComfyUI (fp8_scaled format). The "60-70GB" figure cited in some guides applies to datacenter inference *without* fp8 quantisation. In ComfyUI with fp8_scaled models, the RTX 5090 runs Wan 2.2 14B at ~1s/frame at 720p. NVFP4 (Blackwell-native) reduces it further to ~7.5GB but needs PyTorch cu130.

| Scenario | vLLM | ComfyUI Model | Total VRAM | Status |
|----------|------|--------------|-----------|--------|
| Hermes 8B + FLUX.2 klein 4B | ~16GB | ~8GB | **24GB** ✅ | Good headroom, fast image |
| Dolphin R1 24B + FLUX.2 klein 4B | ~14GB | ~8GB | **22GB** ✅ | **Best daily driver** |
| Dolphin R1 24B + HunyuanVideo 1.5 I2V fp8 | ~12GB | ~14GB | **26GB** ✅ | Best concurrent video combo |
| Dolphin R1 24B + HunyuanVideo 1.5 T2V fp16 | ~12GB | ~17GB | **29GB** ✅ | Just fits — watch VRAM closely |
| Dolphin R1 24B + Wan 2.2 14B fp8 | ~14GB | ~14GB | **28GB** ✅ | Concurrent — both fp8 |
| Dolphin R1 24B + FLUX.2 klein 9B | ~14GB | ~29GB | **43GB** ❌ | Stop vLLM first |
| Dolphin R1 24B + Wan 2.2 14B fp16 | ~14GB | ~28GB | **42GB** ❌ | Stop vLLM or use fp8 |
| Stopped + FLUX.2 klein 9B | 0GB | ~29GB | **29GB** ✅ | Fine |
| Stopped + Wan 2.2 14B fp16 | 0GB | ~28GB | **28GB** ✅ | Fine |
| ~~70B AWQ + anything~~ | ~~35GB~~ | ~~any~~ | ❌ | **Will not load at all** |

### 6.2 Quick Session Commands

```bash
# === START FULL CREATIVE SESSION ===
docker compose -f /data/ai/06-configs/vllm/docker-compose.yml up -d
docker compose -f /data/ai/06-configs/creative-stack/docker-compose.yml up -d

# === SWITCH TO HEAVY VIDEO (stop vLLM first) ===
docker stop creative-vllm
# Now run HunyuanVideo or Wan 2.1 at full VRAM

# === RESUME AFTER VIDEO ===
docker start creative-vllm

# === END SESSION (free everything) ===
docker stop creative-comfyui creative-vllm

# === CHECK STATUS ===
nvidia-smi
docker ps --filter "name=creative-"

# === VIA HERMES (remote) ===
ssh your-username@100.x.x.x '/data/ai/01-workspace/scripts/creative-ctl.sh start'
ssh your-username@100.x.x.x '/data/ai/01-workspace/scripts/creative-ctl.sh status'
ssh your-username@100.x.x.x '/data/ai/01-workspace/scripts/creative-ctl.sh stop'
```

### 6.3 Status Alias (Add to ~/.bashrc)

```bash
echo "alias ai-status='nvidia-smi --query-gpu=name,memory.used,memory.free,temperature.gpu --format=csv && echo && docker ps --filter name=creative- --format \"table {{.Names}}\t{{.Status}}\"'" >> ~/.bashrc
source ~/.bashrc

# Usage:
ai-status
```

### 6.3a Install nvitop — Per-Process VRAM Monitor

`nvidia-smi` only shows GPU totals. `nvitop` shows **which process inside which container** is consuming VRAM — essential for debugging OOM issues in a multi-container setup.

```bash
# nvitop is a CLI tool — use pipx (correct for standalone apps, no --break-system-packages needed)
sudo apt install pipx
pipx install nvitop
pipx ensurepath      # adds ~/.local/bin to PATH
source ~/.bashrc     # reload PATH

# Run (shows live per-process GPU + VRAM breakdown)
nvitop

# Or use via creative-ctl.sh:
/data/ai/01-workspace/scripts/creative-ctl.sh monitor
```

> [!tip]
> When ComfyUI and vLLM are both running, `nvitop` will show two separate rows — one per container process — with individual VRAM bars. Much more useful than `nvidia-smi` when debugging concurrent model loading.

---

### 6.4 Automated VRAM Handoff — ComfyUI Custom Node (Chosen Approach)

When a workflow uses both vLLM (prompt enhancement) and HunyuanVideo/Wan 2.2 (video generation), the handoff is **fully automated inside ComfyUI** using a custom node. Place it between the CLIP encoder and the video sampler — it stops vLLM, clears CUDA cache, waits for VRAM to free, then passes the conditioning through. When the queue empties, it restarts vLLM automatically in the background.

**Why this beats other options:**
- Hermes submits **one** workflow and is done — no second SSH call, no timing guesses
- Works locally too — no Hermes dependency
- VRAM is verified before passing to the sampler — no OOM surprises
- Auto-restarts vLLM after generation via background thread

#### 6.4.1 Create the Custom Node

```bash
mkdir -p /data/ai/01-workspace/comfyui/custom_nodes/VRAMHandoff
```

```python
# /data/ai/01-workspace/comfyui/custom_nodes/VRAMHandoff/__init__.py

import subprocess
import threading
import time
import torch
import comfy.model_management as mm


class VRAMHandoffNode:
    """
    Stops vLLM before heavy GPU operations, restarts it after queue empties.
    Place between CLIPTextEncode and the video sampler.

    Workflow:
      [LLM Enhance] → [CLIPTextEncode] → [VRAMHandoff] → [VideoSampler]
    """

    CONTAINER_NAME     = "creative-vllm"
    VRAM_CHECK_INTERVAL = 2   # seconds between polls
    VRAM_CHECK_TIMEOUT  = 60  # max seconds to wait for VRAM
    RESTART_POLL        = 10  # seconds between queue checks

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "conditioning": ("CONDITIONING",),
                "action": (
                    ["stop_vllm_and_restart_after", "stop_vllm_only", "none"],
                    {"default": "stop_vllm_and_restart_after"}
                ),
                "min_free_vram_gb": ("FLOAT", {
                    "default": 16.0, "min": 4.0, "max": 31.0, "step": 1.0
                }),
            }
        }

    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    FUNCTION     = "handoff"
    CATEGORY     = "VRAM Management"
    OUTPUT_NODE  = False

    def handoff(self, conditioning, action, min_free_vram_gb):
        if action == "none":
            return (conditioning,)

        # 1. Stop vLLM
        print(f"[VRAMHandoff] Stopping {self.CONTAINER_NAME}...")
        result = subprocess.run(
            ["docker", "stop", self.CONTAINER_NAME],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"[VRAMHandoff] Note: {result.stderr.strip()}")

        # 2. Clear CUDA cache
        mm.unload_all_models()
        mm.soft_empty_cache()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        print("[VRAMHandoff] CUDA cache cleared.")

        # 3. Wait for VRAM to reach target
        target_bytes = min_free_vram_gb * (1024 ** 3)
        elapsed = 0
        while elapsed < self.VRAM_CHECK_TIMEOUT:
            free    = mm.get_free_memory()
            free_gb = free / (1024 ** 3)
            print(f"[VRAMHandoff] Free VRAM: {free_gb:.1f} GB / target {min_free_vram_gb:.0f} GB")
            if free >= target_bytes:
                break
            time.sleep(self.VRAM_CHECK_INTERVAL)
            elapsed += self.VRAM_CHECK_INTERVAL
        else:
            print(f"[VRAMHandoff] Warning: target not reached after {self.VRAM_CHECK_TIMEOUT}s — proceeding anyway.")

        free_gb = mm.get_free_memory() / (1024 ** 3)
        print(f"[VRAMHandoff] Handoff complete. Free VRAM: {free_gb:.1f} GB → video sampler.")

        # 4. Spawn auto-restart thread
        if action == "stop_vllm_and_restart_after":
            threading.Thread(target=self._restart_when_idle, daemon=True).start()

        return (conditioning,)

    def _restart_when_idle(self):
        """Restart vLLM once the ComfyUI queue is empty."""
        import urllib.request, json as _json
        print("[VRAMHandoff] Auto-restart thread active — watching queue...")
        while True:
            time.sleep(self.RESTART_POLL)
            try:
                with urllib.request.urlopen("http://localhost:8188/queue", timeout=5) as r:
                    q = _json.loads(r.read())
                if len(q.get("queue_running", [])) == 0 and len(q.get("queue_pending", [])) == 0:
                    break
            except Exception:
                continue
        print(f"[VRAMHandoff] Queue empty. Restarting {self.CONTAINER_NAME}...")
        subprocess.run(["docker", "start", self.CONTAINER_NAME], capture_output=True, timeout=30)
        print("[VRAMHandoff] vLLM restarted — ready in ~60s.")


NODE_CLASS_MAPPINGS       = {"VRAMHandoff": VRAMHandoffNode}
NODE_DISPLAY_NAME_MAPPINGS = {"VRAMHandoff": "VRAM Handoff (Stop vLLM → Video)"}
```

#### 6.4.2 Mount into the Docker Container

Add two lines to your ComfyUI `docker-compose.yml` under `volumes:`:

```yaml
# /data/ai/06-configs/creative-stack/docker-compose.yml

    volumes:
      - /data/ai/02-models:/models:ro
      - /data/ai/01-workspace/comfyui/user:/app/ComfyUI/user
      - /data/ai/08-portfolio/outputs:/app/ComfyUI/output
      - /data/ai/06-configs/creative-stack/model_paths.yaml:/app/model_paths.yaml:ro
      # Mount custom nodes (including VRAMHandoff):
      - /data/ai/01-workspace/comfyui/custom_nodes:/app/ComfyUI/custom_nodes/local
      # Docker socket — lets ComfyUI stop/start containers:
      - /var/run/docker.sock:/var/run/docker.sock
```

> [!warning] Docker Socket Security
> Mounting `/var/run/docker.sock` gives the container root-equivalent access to the host Docker daemon. Only do this on a machine you physically control. Never expose port 8188 to the public internet without auth.

```bash
# Restart container to apply
docker compose -f /data/ai/06-configs/creative-stack/docker-compose.yml down
docker compose -f /data/ai/06-configs/creative-stack/docker-compose.yml up -d
```

#### 6.4.3 Workflow Placement

```
[Text Input]
     │
     ▼
[LLM Party Node] ──── vLLM API (host:8000) → Dolphin 24B enhances prompt
     │
     ▼
[CLIP Text Encode]
     │
     ▼
┌──────────────────────────────────────────┐
│  VRAMHandoff Node                        │
│  action: stop_vllm_and_restart_after     │ ← stops vLLM, clears cache
│  min_free_vram_gb: 16.0                 │ ← waits until 16GB free
└──────────────────────────────────────────┘
     │  (full 32GB now available)
     ▼
[HunyuanVideoSampler / WanVideoSampler]
     │
     ▼
[VAEDecode] → [VideoCombine] → [Save Video]

          (background thread restarts vLLM when queue empties)
```

#### 6.4.4 Node Settings Reference

| Setting | Value | When |
|---------|-------|------|
| `action` | `stop_vllm_and_restart_after` | **Default** — use for all video generation |
| `action` | `stop_vllm_only` | Long multi-job batch sessions |
| `action` | `none` | FLUX.2 klein 4B (~8GB) — no stop needed |
| `min_free_vram_gb` | `16.0` | HunyuanVideo 1.5 / Wan 2.2 fp8 |
| `min_free_vram_gb` | `20.0` | Safety margin for 720p long clips |
| `min_free_vram_gb` | `6.0` | FLUX.2 klein 4B with vLLM running |

> [!tip]
> For FLUX.2 [klein] 4B + Dolphin 24B (22GB total), set `action: none` — no handoff needed. Only use the stop action for HunyuanVideo 1.5, Wan 2.2 14B fp16, or FLUX.2 [klein] 9B.

#### 6.4.5 Manual Override Commands

The `video-mode` and `resume-llm` cases are already included in the `creative-ctl.sh` script written in Phase 2.4. Use them directly:

```bash
# Manually stop vLLM and free VRAM (without triggering via workflow node)
/data/ai/01-workspace/scripts/creative-ctl.sh video-mode

# Restart vLLM after manual video generation
/data/ai/01-workspace/scripts/creative-ctl.sh resume-llm

# Check current VRAM state
/data/ai/01-workspace/scripts/creative-ctl.sh status
```

> [!note]
> You only need these commands when running generation manually without the VRAMHandoff node active (e.g. testing a workflow where you bypassed the node). In normal use, the VRAMHandoff node in §6.4.1 handles the stop/restart automatically.

---

## Phase 7 — Hermes Agent Integration

> [!note] Discord Integration for Hermes → ComfyUI
> For Hermes to control ComfyUI via Discord, three things must be in place:
> 1. `PIP_BREAK_SYSTEM_PACKAGES=1` in ComfyUI compose env (§4.4) — allows LLM Party to install `py-cord`
> 2. A Discord bot token configured in `/app/ComfyUI/custom_nodes/comfyui_LLM_party/config.ini`
> 3. Create your bot at: [discord.com/developers/applications](https://discord.com/developers/applications)
>
> Once `py-cord` installs cleanly (check logs on next restart), configure the token:
> ```bash
> docker exec creative-comfyui >   cat /app/ComfyUI/custom_nodes/comfyui_LLM_party/config.ini
> ```

### 7.1 What Hermes Can Do (API Reference)

```bash
# Hermes calls these endpoints via Tailscale IP (100.x.x.x):

# 1. Check if stack is running
curl http://100.x.x.x:8188/system_stats

# 2. Get available models in ComfyUI
curl http://100.x.x.x:8188/models

# 3. Submit a generation job (POST workflow JSON)
curl -X POST http://100.x.x.x:8188/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": {...comfyui_workflow...}}'

# 4. Check job status
curl http://100.x.x.x:8188/queue

# 5. Call vLLM for prompt enhancement
curl http://100.x.x.x:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "local-llm", "messages": [...]}'

# 6. Start/stop stack via SSH
ssh your-username@100.x.x.x '/data/ai/01-workspace/scripts/creative-ctl.sh start'
```

### 7.2 Recommended Hermes Workflow

```
Phone: "Generate a noir action scene, 720p, 10 seconds"
  ↓
Hermes (cloud):
  1. SSH → creative-ctl.sh start
  2. Call vLLM API → enhance prompt (unrestricted-local, cinematic detail)
  3. Build ComfyUI workflow JSON with enhanced prompt
  4. POST to ComfyUI /prompt API
  5. Poll /queue until complete
  6. Notify you when done (outputs in /data/ai/08-portfolio/outputs/)
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `CUDA error: no kernel image is available` | RTX 5090 SM_120 not supported by stable vLLM image | Use `vllm/vllm-openai:cu130-nightly` image + `VLLM_ATTENTION_BACKEND=FLASHINFER` + `VLLM_FLASH_ATTN_VERSION=2` env vars |
| `nvcc not found on host` | Expected — CUDA toolkit lives inside containers, not on host | Run `docker exec creative-comfyui nvcc --version` to verify inside container. **Do NOT install cuda-toolkit on host — it breaks your driver.** |
| OOM during video gen | vLLM using VRAM | `docker stop creative-vllm` first |
| Black output from FLUX | Wrong text encoder | FLUX.2 needs Qwen3 encoder. FLUX.1 needs `t5xxl_fp16.safetensors`. Do not mix. |
| SM_120 not supported | PyTorch nightly mismatch | Dockerfile uses `cu130` not `cu132`. Rebuild with `docker compose build --no-cache` |
| ComfyUI can't reach vLLM | Missing extra_hosts | Ensure `host.docker.internal:host-gateway` in compose |
| Hermes can't SSH | Tailscale not running | `sudo systemctl start tailscaled && sudo tailscale up` |
| Model not found in ComfyUI | Wrong path in yaml | Check paths in `model_paths.yaml` match `/data/ai/02-models/` |
| LLM Party optional nodes fail (discord, moviepy, whisper) | PEP 668 blocks runtime pip installs inside container | Add `PIP_BREAK_SYSTEM_PACKAGES=1` to ComfyUI compose environment. Restart container — LLM Party retries installs on next startup. |
| Deprecation warnings in ComfyUI logs | LLM Party uses old JS APIs | Harmless — wait for LLM Party update via Manager → Check for Updates. No action needed. |
| `TypeError: list indices must be integers or slices, not str` | model_paths.yaml uses YAML list syntax (`-`) but ComfyUI expects newline strings | Use `|` block scalar in model_paths.yaml — see §4.3 for correct format. No `-` dashes. |
| `Found no NVIDIA driver` during build | GPU not available at build time — only at runtime | Remove `RUN python3 -c "import torch..."` from Dockerfile. GPU check belongs in start.sh only. |
| `externally-managed-environment` pip error | Ubuntu 24.04 PEP 668 blocks system pip | Add `--break-system-packages` flag to pip3 install commands in Dockerfile |
| vLLM slow to load | Large model cold start | Normal — 8B takes ~60s to load. Success = `Application startup complete` + `200 OK` in logs |
| GGUF models ignored by vLLM | Format incompatible | GGUF = llama.cpp only. Use HF format for vLLM |

---


---

## Layer 2 — Agent Orchestration Framework

*This section defines how an AI agent (Gemma4 26B MoE fp8 or Qwen3 27B dense) decides which workflow to run, manages VRAM, and routes requests to the right models. Use this as context when building the agent system in a separate session.*

---

### Architecture Overview

```
User Request
    ↓
[Orchestrator Agent: Gemma4 26B MoE fp8 OR Qwen3 27B dense]
    ↓ (assesses complexity, asks qualifying questions)
    ↓
[VRAM Decision: unload orchestrator, load creative models]
    ↓
[Creative Pipeline: vLLM + ComfyUI]
    ↓ (generation complete)
    ↓
[Reload orchestrator for next request]
```

**Key principle:** The orchestrator and creative models cannot run simultaneously on 32GB. The agent must unload itself before loading video models, then reload after generation completes.

**Orchestrator VRAM usage:**
| Model | Format | VRAM | Context |
|-------|--------|------|---------|
| Gemma4 26B MoE fp8 | INT8 MoE | ~14GB | Excellent reasoning, multimodal |
| Qwen3 27B dense | bfloat16 | ~27GB | Dense model, strong code/logic |
| Qwen3 27B dense AWQ | INT4 | ~14GB | Quantized, saves 13GB |

> [!important] Use Gemma4 26B MoE fp8 OR Qwen3 27B AWQ as orchestrator
> Both use ~14GB which leaves 18GB free for creative models.
> Full Qwen3 27B bfloat16 at 27GB leaves only 5GB — not viable.

---

### Qualifying Questions — What the Agent Asks Before Choosing a Workflow

When a request comes in, the agent asks these questions in order to pick the right workflow:

**Q1 — Output type:**
> "Do you want a still image, a video, or both (image that becomes a video)?"

**Q2 — Quality vs speed:**
> "Is this a draft/preview or a final deliverable? Draft = fast, Final = best quality."

**Q3 — Commercial use (if image):**
> "Is this for commercial use? If yes, I'll use FLUX.1 Dev (Apache 2.0 licensed)."

**Q4 — Reference image available (if video):**
> "Do you have a reference image to animate, or should I generate from text only?"

**Q5 — Script length (if complex request):**
> "Is this a single scene or a multi-scene sequence? Single scene = one workflow. Multi-scene = Dolphin 24B script mode generates the full script first."

**Q6 — Quality tier (for video):**
> "Fast output (Wan 2.2, ~5 min) or cinema quality (HunyuanVideo 1.5, ~10 min + 1080p SR)?"

---

### Decision Tree — Agent Logic

```
REQUEST RECEIVED
│
├── Output = Image only
│   ├── Commercial? → FLUX.1 Dev (Apache 2.0) + T5 + CLIP-L + ae VAE
│   ├── Draft/fast? → FLUX.2 4B + Qwen3 4B + flux2-vae
│   └── Best quality? → FLUX.2 9B + Qwen3 8B + flux2-vae (stop vLLM)
│
├── Output = Video only (text prompt)
│   ├── Draft/test? → Wan 2.1 1.3B (fast, 480p)
│   ├── Production? → Wan 2.2 T2V 14B (480p/720p)
│   └── Cinema? → HunyuanVideo 1.5 T2V fp16 + SR → 1080p
│
├── Output = Video from image (I2V)
│   ├── Fast? → Wan 2.2 I2V 14B
│   └── Cinema? → HunyuanVideo 1.5 I2V fp8 (+ optional SR)
│
├── Output = Image → Video (full pipeline)
│   ├── Fast concurrent → FLUX.2 4B → Wan 2.2 I2V (Dolphin AWQ runs throughout)
│   └── Cinema quality → FLUX.2 4B → HunyuanVideo 1.5 I2V → SR 1080p
│
└── Output = Multi-scene sequence
    ├── Write script → Dolphin 24B AWQ script mode (96K context)
    └── Per-scene → FLUX.2 4B keyframes → Wan 2.2 I2V batch
```

---

### VRAM Management — Agent Load/Unload Sequence

The agent must manage VRAM explicitly. Here are the exact sequences:

#### Scenario A — Simple prompt enhancement (Hermes stays running)
```bash
# State: Hermes 8B running (25GB), 7GB free
# Suitable for: FLUX.2 4B (8GB) — exceeds free VRAM
# Action: Stop Hermes, load Dolphin AWQ instead

docker stop creative-vllm
# Edit .env: VLLM_MODEL=Dolphin3.0-R1-Mistral-24B-AWQ, VLLM_GPU_MEM=0.45
docker compose -f /data/ai/06-configs/vllm/docker-compose.yml up -d
# Now: 14GB used, 18GB free for ComfyUI
```

#### Scenario B — Orchestrator → creative pipeline handoff
```bash
# State: Gemma4/Qwen3 AWQ running (~14GB), 18GB free
# Request assessed, workflow decided
# Unload orchestrator:
docker stop orchestrator-container   # or kill the local inference process
# Free VRAM: ~32GB
# Load vLLM with Dolphin 24B AWQ for prompt enhancement:
docker compose -f /data/ai/06-configs/vllm/docker-compose.yml up -d
# Run ComfyUI workflow (API call or direct)
# After generation:
docker stop creative-vllm
# Reload orchestrator:
docker start orchestrator-container
```

#### Scenario C — Heavy video (stop everything)
```bash
# For FLUX.2 9B (29GB) or HunyuanVideo T2V fp16 (17GB) + SR fp8 (6GB) = 23GB
# Need maximum free VRAM
docker stop creative-vllm          # free 14GB LLM
# Stop orchestrator
# ComfyUI now has ~32GB
# Run generation
# Reload when done
```

---

### VRAM State Machine — All Possible States

| State | What's Running | VRAM Used | Free | Can Also Run |
|-------|---------------|-----------|------|-------------|
| **Idle** | Nothing | 0GB | 32GB | Anything |
| **Orchestrator** | Gemma4/Qwen3 AWQ | ~14GB | ~18GB | Any creative model |
| **Hermes only** | Hermes 8B | ~25GB | ~7GB | Wan 2.1 1.3B only |
| **Dolphin AWQ** | Dolphin 24B AWQ | ~14GB | ~18GB | FLUX.2 4B, Wan 2.2, HunyuanVideo I2V |
| **Orch + FLUX.2 4B** | Orch + FLUX.2 4B | ~22GB | ~10GB | Nothing else |
| **Orch + Wan 2.2** | Orch + Wan 2.2 | ~28GB | ~4GB | SR only |
| **Orch + HunyuanVideo I2V** | Orch + HunyuanVideo I2V fp8 | ~28GB | ~4GB | SR only |
| **Orch + HunyuanVideo T2V** | Orch + HunyuanVideo T2V fp16 | ~31GB | ~1GB | Nothing |
| **FLUX.2 9B** | FLUX.2 9B standalone | ~29GB | ~3GB | Nothing |

---

### Text Encoder Selection — Agent Decision

Each creative model requires a specific text encoder. The agent must load the correct one:

| User Request | Model | Text Encoder to Load | VAE to Load |
|-------------|-------|---------------------|------------|
| Fast image | FLUX.2 4B | `qwen_3_4b_fp4_flux2.safetensors` | `flux2-vae.safetensors` |
| Quality image | FLUX.2 9B | `qwen_3_8b_fp8mixed.safetensors` | `flux2-vae.safetensors` |
| Commercial image | FLUX.1 Dev | `t5xxl_fp16.safetensors` + `clip_l.safetensors` | `ae.safetensors` |
| Any Wan 2.2 video | Wan 2.2 T2V or I2V | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `wan_2.1_vae.safetensors` |
| Wan 2.1 1.3B draft | Wan 2.1 1.3B | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `wan_2.1_vae.safetensors` |
| HunyuanVideo any | HunyuanVideo 1.5 T2V/I2V/SR | `llava_llama3_fp8_scaled.safetensors` | `hunyuanvideo15_vae_fp16.safetensors` |

> [!note] ComfyUI loads text encoders per-workflow, not globally
> The agent does not need to manage text encoder memory separately — ComfyUI loads and unloads them as part of each workflow execution. The agent only needs to manage the vLLM container (LLM memory) and ensure ComfyUI has enough VRAM headroom.

---

### Agent System Prompt Template

When building the orchestration agent, use this system prompt as the foundation:

```
You are a creative AI production orchestrator running on a local RTX 5090 (32GB VRAM) system.

Your role:
1. Receive creative requests from the user
2. Assess complexity and output requirements
3. Ask qualifying questions to determine the right workflow
4. Make VRAM management decisions (which models to load/unload)
5. Trigger the appropriate ComfyUI workflow via API
6. Report generation status and results

Available workflows (from your workflow catalogue):
- Tier 1: FLUX.2 4B image (8GB), Wan 2.1 1.3B draft video (6GB)
- Tier 2: FLUX.1 Dev commercial (18GB), Wan 2.2 T2V/I2V (14GB each)
- Tier 3: HunyuanVideo 1.5 T2V fp16 (17GB), I2V fp8 (14GB), + SR (6GB)
- Tier 4: Full pipelines combining LLM + image + video

VRAM constraint: You (the orchestrator) use ~14GB.
Remaining 18GB available for creative models when you are running.
For FLUX.2 9B or HunyuanVideo T2V fp16 + SR simultaneously, you must unload yourself first.

Always ask these questions before starting:
1. Image, video, or image-that-becomes-video?
2. Draft/preview or final deliverable?
3. Commercial use? (affects model licence choice)
4. Reference image available? (enables I2V workflows)
5. Single scene or multi-scene sequence?

ComfyUI API endpoint: http://localhost:8188
vLLM API endpoint: http://localhost:8000/v1
Model paths: /data/ai/02-models/
```

---

### Workflow Trigger — ComfyUI API Call Format

The agent triggers ComfyUI workflows via HTTP API. Base format:

```python
import requests, json

def run_comfyui_workflow(workflow_json: dict) -> str:
    # Queue the workflow
    response = requests.post(
        "http://localhost:8188/prompt",
        json={"prompt": workflow_json}
    )
    prompt_id = response.json()["prompt_id"]
    return prompt_id

def check_status(prompt_id: str) -> dict:
    response = requests.get(f"http://localhost:8188/history/{prompt_id}")
    return response.json()

# For each workflow tier, load the matching JSON from:
# /data/ai/01-workspace/comfyui/user/default/workflows/
# e.g. workflow_flux2_4b.json, workflow_wan22_t2v.json, etc.
```

---

### Download Status — Final (verified 2026-04-30)

All creative models complete. Only future orchestrator models remain.

| File | Status |
|------|--------|
| All FLUX.2, FLUX.1, Wan 2.2, HunyuanVideo 1.5, encoders, VAEs | ✅ Complete |
| Dolphin 24B AWQ (Valdemardi repo) | ✅ Complete |
| Dolphin3.0-R1-Mistral-24B full bf16 (10 shards) | ❌ Delete — unusable |
| Gemma4 26B MoE fp8 | ⬜ Future orchestrator |
| Qwen3 27B AWQ | ⬜ Future orchestrator alternative |

```bash
# Delete the unusable full bfloat16 Dolphin — frees 48GB
rm -rf /data/ai/02-models/vllm/Dolphin3.0-R1-Mistral-24B
```

---

### Document Usage Notes for Future Sessions

This document is the complete context for your AI creative stack. When starting a new session:

1. **For ComfyUI workflow building** — provide the workflow catalogue section and the verified model inventory section. The agent will know exactly which safetensor files to reference in each node.

2. **For agent orchestration** — provide Layer 2 (this section). The VRAM state machine and decision tree are the core logic.

3. **For troubleshooting** — provide the troubleshooting table. Every error encountered during setup is documented with its fix.

4. **For audio tools** — when adding Whisper (already installed in Docker via `openai-whisper`) or other audio nodes, the text encoder selection table and VRAM state machine already account for their integration via LLM Party.

**Stack confirmed working as of 2026-04-30:**
- ✅ vLLM: `cu130-nightly` + Hermes 3 8B + `VLLM_ATTENTION_BACKEND=FLASHINFER`
- ✅ ComfyUI: `nvidia/cuda:13.2.0-devel-ubuntu24.04` + PyTorch 2.13.0 + SM (12,0)
- ✅ All Tier 1-3 creative models downloaded
- ✅ Dolphin 24B AWQ downloaded (switch to it in .env when ready)
- ⚠️ Delete unused 48GB full bfloat16 Dolphin folder
- ⬜ Tier 6 nodes — RIFE + SeedVR2 not yet installed (see Tier 6 section below)
- ⬜ Tier 4.5 Editing — VOID (native, needs latest ComfyUI) + Wan 2.1 VACE 14B + SAM3 + LBM — not yet installed
- ⬜ RTX VSR node — install + calibrate vs SeedVR2 on one real clip
- ⬜ Forensic-JSON bridge — build only after VOID/VACE proven by hand
- ⬜ NVFP4 FLUX.2 Klein variants — download, confirm text/signage quality for keyframes


---

## Tier 6 — Finishing Pipeline (4K60, append to any video workflow)

> [!info] What this tier is
> Purely additive. Every Tier 2/3/5 video workflow ends at "decode video → save MP4". Tier 6
> takes that saved video as its **input** and runs two more stages. Because of the
> one-model-at-a-time policy, run these as **separate ComfyUI runs**, purging VRAM between
> them.

> [!warning] Operating policy
> **One model on the GPU at a time.** Load → produce → unload → purge VRAM → load next.
> The full 32GB is dedicated to whichever stage is running. System monitor has been moved to
> the iGPU.

### Why a finishing tier exists

The client brief requires **TV/cinema-grade upscaling — locally, privately, on sovereign
hardware, open-source only, no paid tools**. That rules out Topaz, cloud upscalers, and
anything driver-locked or playback-only (NVIDIA RTX VSR is a playback feature, not a
frame-accurate file producer).

Two needs follow from "4K60":

1. **Temporal** — bring framerate up to 60fps → **RIFE** frame interpolation.
2. **Spatial** — bring resolution toward 4K with genuine detail → **SeedVR2** video-native
   diffusion super-resolution (not per-frame image upscalers, which flicker on video).

### Tool decisions (finalized)

| Need | Tool | License | Why |
|------|------|---------|-----|
| Framerate → 60fps | **RIFE v4.7+** via `ComfyUI-Frame-Interpolation` | MIT/Apache | Fast, clean on smooth Wan/Hunyuan motion. |
| Large-motion fallback | **FILM** (same node pack) | Same | ~7x slower — fallback only for violent-motion clips. |
| Video super-resolution | **SeedVR2 7B Sharp FP16** via `ComfyUI-SeedVR2_VideoUpscaler` | Apache 2.0 | Video-native, temporally consistent. Meets cinema-grade bar. |

> [!note] Phase 2 — deferred
> Distillation LoRAs (Lightx2v / CausVid-style) to cut Wan step count are **not** part of
> this build. Treat as Phase 2 after Tier 6 is measured. **Verify licenses individually
> before client use** — LoRA licensing is messier than base-model licensing.

### Model choice for this card

- **Use `seedvr2-7b-sharp-fp16.safetensors` (~14.5GB).** The quality-bar model. Fits 32GB
  comfortably under the one-model-at-a-time policy.
- **Do NOT use GGUF quantization.** Q3/Q4 exists for 8–12GB cards and carries visible quality
  loss. On a 5090 run native FP16.
- **Generate at 720p, then upscale.** Feeding SeedVR2 a 720p source produces better results
  than 1080p. Do not pre-upscale before SeedVR2.
- **Multi-step toward 4K:** 720p → 1080p → 2160p, not one giant jump.

### Hard limits to design around

- **Never process 30+ seconds in a single batch — even a 5090 will OOM.** Chunk on natural
  cut points.
- **Batch size must follow the 4n+1 rule** (1, 5, 9, 13, 17, 25, 49…) — how SeedVR2
  preserves temporal consistency. Non-conforming sizes waste padding or warp.
- **Do not split a continuous shot mid-motion** across separate batches.
- **torch.compile** (`mode: max-autotune`, `backend: inductor`) costs 2–5 min on first run,
  then 20–40% faster on subsequent runs. Worth enabling for production batch sessions.
- **Block swap** (7B: 0–36 blocks): keep at 0; raise only if a 4K chunk OOMs.

### Install — Tier 6 nodes

> [!warning] SeedVR2 is now v2.5 — paths and architecture changed since this section was written
> - Node architecture is now a **4-node** design (separate DiT load · VAE load · upscaler ·
>   torch-compile settings) plus GGUF support. Rebuild any SeedVR2 graph against v2.5.
> - Repo clones to `custom_nodes/seedvr2_videoupscaler`; **weights auto-download to
>   `ComfyUI/models/SEEDVR2`** (not `/data/ai/02-models/seedvr2` — symlink if you want it there).
> - Correct model filename is **`seedvr2_ema_7b_fp16.safetensors`** (~15GB).
> - **Blackwell (SM_120):** install **SageAttention** (SA3 supported on RTX 50xx, auto-falls
>   back to PyTorch SDPA). It's effectively mandatory for acceptable speed.
> - **Do NOT use NVFP4 for SeedVR2** — the community NVFP4 port failed (the VAE/DiT are too
>   entangled). Run native **FP16**. (NVFP4 is great for FLUX.2/Wan generation — just not here.)
> Keep everything else in this section as-is (FP16 not GGUF · 720p source · 4n+1 batch · no
> 30s+ batches · block-swap 0 unless 4K OOM · multi-step 720p→1080p→2160p).

```bash
# Frame interpolation (RIFE + FILM)
cd /data/ai/01-workspace/comfyui/custom_nodes
git clone https://github.com/Fannovel16/ComfyUI-Frame-Interpolation
cd ComfyUI-Frame-Interpolation
pip install --break-system-packages -r requirements.txt
# RIFE / FILM weights auto-download on first node use

# SeedVR2 video upscaler
cd /data/ai/01-workspace/comfyui/custom_nodes
git clone https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler
cd ComfyUI-SeedVR2_VideoUpscaler
pip install --break-system-packages -r requirements.txt
```

```bash
# SeedVR2 weights folder
mkdir -p /data/ai/02-models/seedvr2
# 7B Sharp FP16 (~14.5GB) — auto-downloads on first run, or fetch manually from
# ByteDance-Seed on HuggingFace into /data/ai/02-models/seedvr2/
# 3B FP8 (~3.1GB) — fast preview only, NOT for deliverables
```

> [!note] Rebuild note for the Docker stack
> Clone into the **mounted** `custom_nodes` path and rebuild/restart the container per
> Phase 4 of this doc so the nodes and their deps are present inside the image.

### Tier 6 alternative — RTX Video Super Resolution (re-evaluate; was wrongly dismissed)

> [!note] RTX VSR is now a real ComfyUI node (GDC 2026) — the earlier "playback-only" note is stale
> NVIDIA shipped RTX Video Super Resolution as a ComfyUI node (also a PyPI wheel). It runs on
> Tensor Cores, claims ~30× faster than competing local upscalers, sharpens edges and cleans
> compression artifacts. It is free/local, so it fits the sovereignty constraint.
>
> **Quality vs speed:** SeedVR2 (diffusion, video-native) remains the cinema-grade *quality*
> finisher. RTX VSR is the *speed* path — fast previews / less-critical clips / real-time 4K.
> Decision: keep SeedVR2 as the client-delivery finisher; add RTX VSR as the draft/preview
> finisher. Calibrate both on one real clip and compare before fixing the client default.

### Workflow 6.1 — RIFE interpolation (→ 60fps)

**What it achieves:** Raises framerate to 60fps by synthesizing intermediate frames.
**Use when:** Any clip destined for a 60fps deliverable, before upscaling.
**Stage input:** Decoded frames or MP4 from a Tier 2/3/5 video workflow (at 720p).

```
[Load Video / frames]  (720p, ~24fps source)
        ↓
[RIFE VFI]  model: rife47 or rife49 · multiplier to reach 60fps
        ↓
[VHS_VideoCombine]  frame_rate: 60  → 02-interpolated-60fps/
```

**VRAM:** low (RIFE is light) | **Fallback:** swap to `FILM VFI` only if a clip shows
ghosting on fast motion (~7x slower).

### Workflow 6.2 — SeedVR2 super-resolution (→ toward 4K)

**What it achieves:** Video-native diffusion super-resolution with cross-frame temporal
consistency. The dominant render-time stage — calibrate before committing to client.
**Stage input:** 60fps frames from 6.1 (kept at 720p — do not pre-upscale).

```
[Load Video / frames]  (720p, 60fps from 6.1)
        ↓
[SeedVR2 Torch Compile Settings]  mode: max-autotune · backend: inductor   (batch sessions)
        ↓
[SeedVR2 Load DiT Model]  seedvr2-7b-sharp-fp16.safetensors · device: cuda:0
        ↓
[SeedVR2 Load VAE Model]  ema_vae_fp16.safetensors · device: cuda:0
        ↓
[SeedVR2 Video Upscaler]  batch_size: 4n+1 (e.g. 25) · resolution: 1080  (then repeat → 2160)
        ↓
[VHS_VideoCombine]  → 03-upscaled-4k/
```

**Model:** `seedvr2/seedvr2-7b-sharp-fp16.safetensors` (Apache 2.0) | **VRAM:** ~15–20GB+ at
720p→1080p, fits 32GB; raise block swap only if a 4K chunk OOMs.

### Workflow 6.3 — Full finishing chain (sequential)

Each step is its own ComfyUI run; purge VRAM between:

1. Produce base clip at **720p** via chosen Tier 2/3/5 workflow → `01-source-720p/`
2. Purge VRAM. Run **6.1 RIFE** → 60fps → `02-interpolated-60fps/`
3. Purge VRAM. Run **6.2 SeedVR2** → 1080p, then second SeedVR2 pass → 2160p →
   `03-upscaled-4k/`
4. Final mux/colour check in DaVinci Resolve (optional, open-source-friendly).

### Recommended build sequence

1. **Close out the existing I2V debug first.** Confirm the high→low expert handoff, lock the
   seed, produce one clean known-good 720p clip.
2. **Add only RIFE (6.1).** Confirm 24→60fps looks right. Cheap, fast, de-risks the easy half.
3. **Add SeedVR2 (6.2) and run the mandatory calibration clip.** Record wall-clock to
   `05-benchmarks/`. This number decides whether 4K60 is economic as-is.
4. **Decide on Phase 2.** Only after Tier 6 is measured: verify distillation-LoRA licenses,
   then add Lightx2v/CausVid-style LoRAs upstream to cut Wan step count.

> [!warning] Render time — calibrate, don't assume
> Published benchmarks are on 4090/Ada; your Blackwell SM_120 fp8/attention paths differ.
> SeedVR2 will likely dominate the total budget — more than Wan generation itself. Run a
> real clip end-to-end before any client commitment.

### Open items

- **Client deliverable spec:** confirm whether contractual target is literal 2160p or
  "visually 4K-grade" — it changes the SeedVR2 stage budget by ~4x.
- **Per-clip render budget vs. turnaround:** fill in after Step 3 calibration run.
  before client use.
- **Audio stack:** being implemented separately (`mushishi-audio-stack`); no dependency on
  Tier 6.

---

## Appendix B — Performance Benchmarks (Expected)

| Task | VRAM | Time (RTX 5090) | vLLM Concurrent? |
|------|------|-----------------|-----------------| 
| FLUX.2 klein 4B distilled | ~8GB | ~1.2s | ✅ yes |
| FLUX.2 klein 9B base | ~29GB | ~17s | ❌ stop vLLM |
| FLUX.1 Dev fp8 1024×1024 | ~18GB | ~15s | ✅ with Dolphin 24B |
| Wan 2.2 14B fp8 480p 25f | ~14GB | ~2–3 min | ✅ yes |
| Wan 2.2 14B fp8 720p 25f | ~14GB | ~4–6 min | ✅ yes |
| Wan 2.2 14B NVFP4 720p 25f | ~7.5GB | ~2–3 min | ✅ yes (fastest) |
| Wan 2.1 1.3B 480p 25f | ~8GB | ~3–4 min | ✅ yes |
| HunyuanVideo 1.5 I2V fp8 720p | ~14GB | ~5–8 min | ✅ yes with Dolphin 24B AWQ |
| HunyuanVideo 1.5 T2V fp16 720p | ~17GB | ~8–12 min | ✅ with Dolphin 24B AWQ (29GB total) |
| vLLM Dolphin R1 24B (Mistral) | ~14GB | ~60 tok/s | — |
| vLLM Hermes 3 8B (bfloat16) | ~16GB | ~120 tok/s | — |
| FLUX.2 klein 9B NVFP4 | ~12GB (est) | calibration pending — measure on-box | ✅ |
| SeedVR2 7B FP16 720p→1080p | ~15–20GB | calibration pending — v2.5 4-node arch (DiT + VAE); torch.compile max-autotune = 2-5min cold start, then 20-40% faster; batch must be 4n+1, ≤30s source per batch | ❌ sole-occupancy |
| VOID 2-pass (CogVideoX) | calibration pending | calibration pending — measure on-box | ❌ sole-occupancy |
| Wan 2.1 VACE 14B edit | ~14GB | calibration pending — measure on-box | ✅ |
| RTX VSR → 4K | low (Tensor Core) | calibration pending — measure on-box | varies |

---

## Appendix C — What to Do With Existing Files

| Existing Item | Location | Action |
|--------------|----------|--------|
| `02-models/gguf/` | `/data/ai/` | Keep — llama.cpp still uses these |
| `01-workspace/llama.cpp/` | `/data/ai/` | Keep — update with `git pull` |
| `01-workspace/vllm/` | `/data/ai/` | Not used — vLLM runs via Docker. Leave folder or delete it. |
| `myenv/` | `/data/ai/` | Investigate with `cat /data/ai/myenv/pyvenv.cfg`. Safe to ignore for now. |
| `pip_tmp/` | `/data/ai/` | Safe to delete: `rm -rf /data/ai/pip_tmp` |

---

## Outstanding work as of v1.5 (for the final push)

**On Reddy (ComfyUI UI):**
- Spot-test each t5- workflow; confirm uncensoring active (raise strength 0.8→1.2 if filtered)
- Calibration clip: RIFE + SeedVR2 (1080p + 2160p passes) + RTX VSR — log wall-clock/VRAM
- NVFP4 vs fp8 quality test on a text/signage prompt
- Tier 5 → Tier 6 end-to-end (one Wan unrestricted-local clip through RIFE + SeedVR2)
- Run forensic_to_comfy.py end-to-end against VOID once node IDs are patched

**On Claude Code:**
- Install RTX VSR node (verify current NVIDIA repo URL first)
- Install/confirm LBM relight node (ComfyUI-LBMWrapper) + weights
- Patch forensic_to_comfy.py placeholder node IDs from exported API JSONs
- Delete 48GB unused Dolphin bfloat16 folder (keep AWQ)

**Blocked / decisions:**

**Then Phase 2 (final):** output naming sweep (CreativeName/CreativeName), full benchmark sweep
across every tier, CSV → markdown render, git commit (workflows + samples + benchmarks + docs),
then GitHub repo + blog post from the Glossary.

---

## Quick Reference

```bash
# START creative session
docker compose -f /data/ai/06-configs/vllm/docker-compose.yml up -d
docker compose -f /data/ai/06-configs/creative-stack/docker-compose.yml up -d

# STOP (free GPU)
docker stop creative-comfyui creative-vllm

# STATUS
ai-status

# REMOTE (via Hermes/phone)
ssh user@$(tailscale ip -4) '/data/ai/01-workspace/scripts/creative-ctl.sh start'

# SWITCH vLLM MODEL (edit .env only — no compose file changes needed)
nano /data/ai/06-configs/vllm/.env
# Change VLLM_MODEL and VLLM_GPU_MEM, then:
docker compose -f /data/ai/06-configs/vllm/docker-compose.yml restart

# UPDATE COMFYUI
docker exec creative-comfyui bash -c "cd /app/ComfyUI && git pull"
docker compose -f /data/ai/06-configs/creative-stack/docker-compose.yml restart
```

---

*RTX 5090 · Ubuntu 24.04 · /data/ai/ workspace · vLLM unrestricted-local · ComfyUI · FLUX.2 [klein] · Wan 2.2 · HunyuanVideo 1.5 · Tailscale remote access*

---

## Problems & Solutions Glossary (v1.4)

The full build log of every issue hit and how it was solved lives in the companion file
**`Creative-Stack-PROBLEMS-AND-SOLUTIONS-GLOSSARY.md`** (dual-tone: technical + plain-language,
written as blog source material). Summary index:

1. Wan 2.2 crystalline-shadow bug → two-sampler high→low MoE chain (the days-long one)
2. FLUX 4B base-vs-distilled filename trap → lock seed first; verify variant
3. `/var` full + `prune -a` deleting ComfyUI → stop prune-all; move Docker to big drive
4. Docker data-root migration → add (don't overwrite) the nvidia block in daemon.json
5. Multi-stack boundary → inventory + confirm; act by exact container name only
6. Four WanVideoWrapper VRAM patches → fragile; re-apply after updates
7. VOID "Prompt has no outputs" → subgraph needed a top-level SaveVideo node
8. VACE color-splotches → connect a mask to input_masks
9. `flash_attn` KeyError → benign optional probe; ignore if model runs
10. SeedVR2 v2.5 + RTX VSR → re-verified current names/paths; FP16 not NVFP4
11. The reframe → generation vs editing (the premise-level course-correction)
12. (v1.5) SAM3 label matching is semantic, not literal → architectural surfaces need functional
    descriptions ("writing board" worked; "blackboard"/"chalkboard" failed). Clock/watch matched
    fine (common object); fan and board did not until relabeled.
13. (v1.5) SAM3 image-mode vs video-mode → image-mode gives [1,H,W], VACE needs [N,H,W] per frame;
    tensor mismatch "Expected size 21 but got size 1". Fix = 4-node SAM3 video pipeline.
14. (v1.5) SAM3 custom node install.py fails on RTX 5090 (no CUDA 13 flash-attn wheels, pixi
    network blocked) but falls back to in-process import — 15 nodes register anyway. Not fatal.
15. (v1.5) "Node Slots Error" on SAM3/VACE nodes was a missing custom node (SAM3 not installed),
    not a wiring fault — JSON links were intact. Diagnosis: check NODE_CLASS_MAPPINGS registration
    before assuming a wiring problem.
    not a LoRA; needs ComfyUI_FluxMod node).
18. (v1.5) VOID transparent-object edge case → blackboard visible through a glass beaker wasn't
    masked (mask covers painted region only; secondary visibility through transparent objects needs
    separate mask coverage). Mask-quality refinement, not a fault.
19. (v1.5) SeedVR2 weights stranded in user/SEEDVR2/ → container expects /models/SEEDVR2/
    (= /data/ai/02-models/SEEDVR2/ host). Moved; symlinks left behind for safety.

---

## CRITICAL — WanVideoWrapper local patches (re-apply after any update)

> [!danger] These patches live on top of third-party code. A ComfyUI-WanVideoWrapper update WILL
> overwrite them and silently break Shapeshifter (Wan VACE under VRAM management). Re-apply or
> upstream after any wrapper update. They affect ONLY the `vram_management_args` code path.

1. `nodes_model_loading.py` — call `load_weights()` before `enable_vram_management()` (materialize
   meta-device tensors).
2. `nodes_model_loading.py` — set `module_config.onload_device` to offload_device (CPU) so forward
   always casts to CUDA.
3. `nodes_model_loading.py` — move non-AutoWrapped params (e.g. modulation) to CUDA after wrapping.
4. `diffsynth/vram_management/layers.py` — `AutoWrappedModule.forward` uses in-place `.to()` instead
   of deepcopy; add `__getattr__` proxy so `norm_layer.weight.dtype` works on wrapped modules.

---

## Confirmed workflow params (v1.4 — tested on-box)

| Workflow | Model | Key params (confirmed) | Status |
|---|---|---|---|
| ⚡ Flashfire | flux-2-klein-4b-fp8 (distilled) | 4 steps · CFG 1.0 · seed fixed | ✅ seed-identity pass |
| 🔨 Goldsmith | flux-2-klein-base-4b-fp8 | 20 steps · FluxGuidance 3.5 · euler/simple | ✅ ~3.3s render |
| 🪶 Silkmotion | RIFE (Frame-Interpolation) | rife ×2 (30→60fps) | ✅ 60fps |
| 💎 Crystalforge | seedvr2_ema_7b_fp16 (v2.5) | FP16 · 720→1080→2160 · blocks_to_swap 32 · batch 1 | ✅ 4K confirmed |
| 🫥 Vanisher | VOID pass1+pass2 · SAM3 · cogvideox_vae | SAM3 mask prompt + fill prompt · Pass2 on | ✅ removes obj+reflection |
| 🦎 Shapeshifter (v1.5) | wan2.1_vace_14B_fp16 + SAM3 video pipeline | per-frame [N,H,W] masks via 4-node SAM3 video chain | ✅ mask-confined edit (red cube swap confirmed) |
| t1-flux2-9b-flashfire | flux-2-klein-9b-nvfp4 | weight_dtype default (NVFP4 self-quantized) | ✅ built, quality-test pending |

Wan 2.2 T2V/I2V (fixed): two-sampler high→low MoE chain, seeds locked at 42. No crystalline
artifact confirmed. Hunyuan I2V: CFG 1.0, flow_shift 5.0 (distilled). Hunyuan SR: link-integrity
fixed. DO-NOT-TOUCH (still bit-identical to backup): t2-flux1-dev-commercial, t1-wan21-draft-video,
t3-hunyuan15-t2v.

Remaining refinements (not blockers): Vanisher mask-tightening for limbs on fast motion (lower SAM3
threshold / dilate mask); Shapeshifter some frames incompletely changed (mask coverage). Both are
mask-quality refinements, not pipeline faults.
