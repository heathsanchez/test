#!/usr/bin/env python3
"""Aggregate exact Collatz swarm scouts into a compiled search policy.

Each scout is an exact, verifier-gated micro-world:
- same target consequence (close a bounded valuation microinterval through H5000),
- different representation/action,
- measured explicit residual size and wall cost.

The controller never grants mathematical authority to a score. It only allocates
future search. Exact scanners remain sovereign.

RealityGraph-style operations:
1. fingerprint consequence;
2. quotient equivalent consequences;
3. drop Pareto-dominated actions;
4. select the cheapest representative for each residual world;
5. compile the resulting allocation policy.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path


def load_rows(root: Path):
    rows=[]
    for p in sorted(root.glob("scout-*.json")):
        d=json.loads(p.read_text())
        d["_file"]=p.name
        rows.append(d)
    return rows


def consequence_key(row):
    # Mathematical consequence, deliberately excluding runtime/implementation.
    return (
        row["k"],
        row["full_seed_count"],
        row["merge_killed_seed_count"],
        row["transfer_killed_seed_count"],
        row["explicit_seed_count"],
        row["best_first_descent"],
        row["closed_through_h5000"],
    )


def pareto(rows):
    out=[]
    for a in rows:
        dominated=False
        for b in rows:
            if a is b:
                continue
            # Search allocation only: fewer explicit seeds and lower wall time
            # are both better. Mathematical consequence itself is separately
            # fingerprinted and never inferred from this score.
            if (b["explicit_seed_count"] <= a["explicit_seed_count"]
                and b["wall_seconds"] <= a["wall_seconds"]
                and (b["explicit_seed_count"] < a["explicit_seed_count"]
                     or b["wall_seconds"] < a["wall_seconds"])):
                dominated=True
                break
        if not dominated:
            out.append(a)
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--out",default="swarm-policy.json")
    A=ap.parse_args()

    rows=load_rows(Path(A.root))
    if not rows:
        raise SystemExit("no scout rows")

    by_k={}
    for r in rows:
        by_k.setdefault(r["k"],[]).append(r)

    policy={}
    for k, group in sorted(by_k.items(), reverse=True):
        # Quotient actions that produced exactly the same verified consequence;
        # retain the cheapest representative.
        buckets={}
        for r in group:
            buckets.setdefault(consequence_key(r),[]).append(r)
        quotient=[]
        for key, bucket in buckets.items():
            bucket=sorted(bucket,key=lambda r:(r["wall_seconds"],r["state_classes"],r["action"]))
            rep=bucket[0].copy()
            rep["equivalent_actions"]=[x["action"] for x in bucket]
            quotient.append(rep)

        frontier=pareto(quotient)
        winner=min(
            frontier,
            key=lambda r:(
                r["wall_seconds"],
                r["explicit_seed_count"],
                r["state_classes"],
                r["action"],
            ),
        )
        cold=min(group,key=lambda r:(0 if r["action"]=="merge" else 1,r["wall_seconds"]))
        policy[str(k)]={
            "winner":winner["action"],
            "winner_wall_seconds":winner["wall_seconds"],
            "winner_explicit_seed_count":winner["explicit_seed_count"],
            "cold_merge_wall_seconds":cold["wall_seconds"] if cold["action"]=="merge" else None,
            "runtime_reduction_vs_merge":(
                cold["wall_seconds"]/winner["wall_seconds"]
                if cold["action"]=="merge" and winner["wall_seconds"]>0 else None
            ),
            "consequence_classes":len(buckets),
            "pareto_actions":[r["action"] for r in frontier],
            "quotient":[
                {
                    "representative":r["action"],
                    "equivalent_actions":r["equivalent_actions"],
                    "explicit_seed_count":r["explicit_seed_count"],
                    "wall_seconds":r["wall_seconds"],
                    "state_classes":r["state_classes"],
                }
                for r in sorted(quotient,key=lambda x:(x["explicit_seed_count"],x["wall_seconds"]))
            ],
        }

    # Cross-k compiled rule: group adjacent k values choosing the same winner.
    ordered=sorted((int(k),v["winner"]) for k,v in policy.items())
    bands=[]
    start=end=None; current=None
    for k,w in ordered:
        if current is None:
            start=end=k; current=w
        elif w==current and k==end+1:
            end=k
        else:
            bands.append({"k_min":start,"k_max":end,"action":current})
            start=end=k; current=w
    if current is not None:
        bands.append({"k_min":start,"k_max":end,"action":current})

    result={
        "kind":"collatz_realitygraph_style_swarm_policy_v1",
        "mathematical_authority":"none; allocation policy only; exact verifier required",
        "scout_count":len(rows),
        "worlds":policy,
        "compiled_bands":bands,
    }
    Path(A.out).write_text(json.dumps(result,indent=2)+"\n")
    print("SWARM_POLICY",json.dumps(result,separators=(",",":")))


if __name__=="__main__":
    main()
