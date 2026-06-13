#!/usr/bin/env python3
"""workflow-validate.py — health-check every ComfyUI workflow against the LIVE
node registry. Detects drift (missing node types) WITHOUT rendering. GPU-light.
Outputs JSON: {workflow: {status, missing_nodes[]}}.
Part of the monthly workflow-maintenance system."""
import json, sys, urllib.request, glob, os

WF_DIR = "/data/ai/01-workspace/comfyui/user/default/workflows"
COMFY = "http://localhost:8188"

def live_node_types():
    d = json.load(urllib.request.urlopen(f"{COMFY}/object_info", timeout=30))
    return set(d.keys())

def workflow_node_types(path):
    """Extract every node 'type' from a UI workflow (incl. subgraph defs)."""
    w = json.load(open(path))
    types = set()
    def scan(nodes):
        for n in nodes:
            t = n.get("type", "")
            # subgraph instances reference a definition by UUID type — skip those
            if t and not (len(t) == 36 and t.count("-") == 4):
                types.add(t)
    scan(w.get("nodes", []))
    for sg in w.get("definitions", {}).get("subgraphs", []):
        scan(sg.get("nodes", []))
    return types

def main():
    live = live_node_types()
    results = {}
    for path in sorted(glob.glob(f"{WF_DIR}/*.json")):
        name = os.path.basename(path).replace(".json", "")
        if name.startswith("_") or name in ("void", "crystalforge", "void-e1c", "void-e1b", "t45-void-vanisher-e1b", "t6-crystalforge-e1b"):
            continue  # skip API-exports + scratch variants
        try:
            wf_types = workflow_node_types(path)
            missing = sorted(wf_types - live)
            # core/registered nodes that legitimately aren't in object_info (notes etc.)
            missing = [m for m in missing if m not in ("Note", "MarkdownNote", "Reroute", "PrimitiveNode")]
            results[name] = {"status": "ok" if not missing else "drift", "missing_nodes": missing}
        except Exception as e:
            results[name] = {"status": "error", "missing_nodes": [], "err": str(e)[:100]}
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
