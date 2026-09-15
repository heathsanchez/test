#!/usr/bin/env python3
"""Resolve the retained Collatz execution policy for one valuation slice.

This tool has no mathematical authority. It only prevents duplicate compute and
selects an already verifier-gated execution regime.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"experiments/collatz_residual_ledger.json"
POLICY=ROOT/"experiments/collatz_frontier_policy.json"

def compiled_k(ledger):
    out={}
    for r in ledger.get("compiled_regions",[]):
        m=re.search(r"v2\(n\+1\)\s*=\s*(\d+)",r.get("predicate",""))
        if m and r.get("status")=="compiled":
            out[int(m.group(1))]=r
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--k",type=int,required=True)
    ap.add_argument("--github-output")
    a=ap.parse_args()
    ledger=json.loads(LEDGER.read_text())
    policy=json.loads(POLICY.read_text())
    done=compiled_k(ledger)
    if a.k in done:
        result={
            "k":a.k,"should_scan":False,"reason":"compiled",
            "compiled_region":done[a.k],
        }
    else:
        regime=next((r for r in policy["regimes"] if r["k_min"]<=a.k<=r["k_max"]),None)
        if not regime:
            raise SystemExit(f"no retained regime for k={a.k}")
        production=regime.get("scanner") not in ("unknown","pending_sparse_compiled_scanner")
        result={
            "k":a.k,"should_scan":production,
            "reason":"retained_production_regime" if production else "research_regime_not_yet_production",
            "regime":regime,
            "deferred":a.k in policy.get("deferred_slices",[]),
        }
    print("FRONTIER_POLICY",json.dumps(result,separators=(",",":")))
    if a.github_output:
        p=Path(a.github_output)
        regime=result.get("regime",{})
        defines=regime.get("defines",{})
        lines=[
            f"should_scan={'true' if result['should_scan'] else 'false'}",
            f"k={a.k}",
            f"scanner={regime.get('scanner','')}",
            f"block_bits={defines.get('BLOCK_BITS','')}",
            f"prefix_bits={defines.get('PREFIX_BITS','')}",
            f"coal_bits={defines.get('COAL_BITS','')}",
            f"shards={regime.get('shards','')}",
            f"reason={result['reason']}",
        ]
        with p.open("a") as f:
            f.write("\n".join(lines)+"\n")

if __name__=="__main__":
    main()
