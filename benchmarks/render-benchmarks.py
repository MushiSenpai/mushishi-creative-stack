#!/usr/bin/env python3
"""
Render 05-benchmarks/benchmarks.csv into benchmarks.md.
CSV is the single source of truth; this only produces a readable/portfolio view.
Re-run after every benchmarked row.

    python3 render-benchmarks.py --csv 05-benchmarks/benchmarks.csv --out 05-benchmarks/benchmarks.md
"""
import argparse, csv, datetime, os

COLS = ["workflow","model","input_spec","output_spec","wall_clock_sec","peak_vram_gb",
        "throughput","concurrency","marginal_cost","cloud_equivalent_cost","date","notes","sample_output"]
HEAD = ["Workflow","Model","Input","Output","Wall (s)","Peak VRAM (GB)","Throughput",
        "Concurrent vLLM","Marginal $","Cloud-equiv $","Date","Notes","Sample"]


def render(csv_path, out_path):
    rows = list(csv.DictReader(open(csv_path)))
    done = [r for r in rows if r.get("wall_clock_sec","").strip()]
    pend = [r for r in rows if not r.get("wall_clock_sec","").strip()]

    L = []
    L.append("# Creative Stack — Benchmarks\n")
    L.append(f"> Rendered from `benchmarks.csv` (source of truth) on "
             f"{datetime.date.today().isoformat()}. Do not hand-edit this file — edit the CSV.\n")
    L.append("**Platform:** RTX 5090 (Blackwell SM_120), Ubuntu 24.04, CUDA 13.2. "
             "All runs local, $0 marginal compute beyond electricity.\n")
    L.append(f"\n**Coverage:** {len(done)}/{len(rows)} workflows benchmarked.\n")

    def table(rs):
        out = ["| " + " | ".join(HEAD) + " |",
               "|" + "|".join(["---"]*len(HEAD)) + "|"]
        for r in rs:
            out.append("| " + " | ".join((r.get(c,"") or "").replace("|","\\|") for c in COLS) + " |")
        return "\n".join(out)

    if done:
        L.append("\n## Benchmarked\n\n" + table(done) + "\n")
    if pend:
        L.append("\n## Pending (awaiting a real run)\n\n" + table(pend) + "\n")

    L.append("\n## Why these columns\n")
    L.append("Each row is the evidence for one capability claim. The pairing that signals "
             "systems work, not just output: model + resolution/frames + wall-clock + peak "
             "VRAM + concurrency with the LLM + marginal cost vs cloud-equivalent.\n")
    open(out_path,"w").write("\n".join(L))
    print(f"Wrote {out_path} ({len(done)} done, {len(pend)} pending)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="benchmarks.csv")
    ap.add_argument("--out", default="benchmarks.md")
    a = ap.parse_args()
    render(a.csv, a.out)
