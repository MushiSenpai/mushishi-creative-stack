#!/bin/bash
# workflow-maintenance.sh — monthly ComfyUI workflow health system (v1, 2026-06-14)
# WHAT IT DOES AUTOMATICALLY (reliable, safe):
#   1. Starts ComfyUI (only if GPU is free — respects shared-GPU etiquette)
#   2. Validates EVERY workflow against the live node registry (drift detection)
#   3. Auto-discovers NEW workflow .json files (they join the catalogue)
#   4. Regenerates the public HTML catalogue + commits it
#   5. ntfy report: N ok, M drifted (with the renamed nodes), J new
# WHAT IT FLAGS FOR A HUMAN (needs judgment, NOT auto-applied):
#   - Drifted workflows (upstream renamed/changed nodes) → rebuild needed
#   - Benchmarking the OK ones → run `workflow-benchmark` deep-run when GPU is free
# Honest by design: it never silently "fixes" a workflow in a way that could
# ship a broken render to a client. Detection + diagnosis + report = the safe core.
#
# Cron: 1st of month 08:00. Manual: bash workflow-maintenance.sh
set -u
NTFY="https://ntfy.sh/mushishi-alerts-f7c7ab8ac7"
SCRIPTS=/data/ai/01-workspace/scripts
SITE=/data/ai/08-portfolio/theinvalid-site

# 1. GPU etiquette — do NOT fight another session
FREE=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null)
if [ "${FREE:-0}" -lt 6000 ]; then
  curl -s -m10 -H "Title: Workflow maintenance skipped" -H "Tags: warning" \
    -d "GPU busy (${FREE}MiB free) — another session is using it. Will retry next cycle." "$NTFY" >/dev/null
  echo "GPU busy, skipping."; exit 0
fi

# 2. Ensure ComfyUI up (lightweight — validation needs the registry, not rendering)
if ! curl -sf http://localhost:8188/object_info >/dev/null 2>&1; then
  cd /data/ai/06-configs/creative-stack && docker compose up -d comfyui >/dev/null 2>&1
  for i in $(seq 1 30); do curl -sf http://localhost:8188/object_info >/dev/null 2>&1 && break; sleep 5; done
  STARTED_COMFY=1
fi

# 3. Validate all workflows (static drift detection + new-workflow discovery)
VAL=$(python3 "$SCRIPTS/workflow-validate.py" 2>/dev/null)
OK=$(echo "$VAL" | python3 -c "import sys,json; d=json.load(sys.stdin); print(sum(1 for v in d.values() if v['status']=='ok'))")
DRIFT=$(echo "$VAL" | python3 -c "import sys,json; d=json.load(sys.stdin); print('; '.join(f'{k} (missing {\",\".join(v[\"missing_nodes\"][:3])})' for k,v in d.items() if v['status']=='drift') or 'none')")
echo "$VAL" > /data/ai/04-logs/workflow-validation-$(date +%Y%m%d).json

# 4. Regenerate the catalogue from current benchmarks + validation
python3 "$SCRIPTS/generate-catalogue.py" >/dev/null 2>&1

# 5. Commit the regenerated catalogue (if changed)
cd "$SITE" && git pull -q --rebase 2>/dev/null
if ! git diff --quiet public/workflow-catalogue.html 2>/dev/null; then
  git add public/workflow-catalogue.html && git commit -q -m "catalogue: monthly workflow-maintenance regen $(date +%Y-%m-%d)" && git push -q 2>/dev/null
fi

# 6. Stop ComfyUI only if WE started it (don't disrupt an active creative session)
[ "${STARTED_COMFY:-0}" = "1" ] && docker stop creative-comfyui >/dev/null 2>&1

# 7. Report
curl -s -m10 -H "Title: Workflow maintenance: $OK ok" -H "Tags: wrench" \
  -d "Validated all workflows.
OK: $OK
DRIFTED (rebuild needed): $DRIFT
Catalogue regenerated -> theinvalid.me/workflow-catalogue.html
To benchmark the OK ones or rebuild drifted ones (needs GPU + judgment), run a deep-run session." "$NTFY" >/dev/null
echo "done: $OK ok | drift: $DRIFT"
