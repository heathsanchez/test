#!/usr/bin/env python3
"""Exact online cycle-erasure of non-descending odd-episode paths.

For each bounded odd state x=2^r m-1, follow complete odd episodes until the
first x_j < x_0.  Maintain the current simple stack of r-states.  Whenever the
next r' already occurs on the stack, the intervening branch word is a closed
r-cycle.  Extract it, compose its exact affine m-map

    F(m) = (A m + B) / 2^D,

classify q=B/(2^D-A), verify the concrete entry/exit m values, and erase the
cycle from the stack.

This gives a consequence-specific decomposition

    long episode path = short simple r-spine + exact closed cycles.

The experiment measures how much of the delay is explained by cycle reuse and
whether any observed erased cycle has a non-base positive-integer fixed point.

Bounded exact evidence only; not a global Collatz proof.
"""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path

from collatz_odd_episode_grammar import episode, branch_for_residue


def compose(bs):
    A,B,D=1,0,0
    for b in bs:
        B=b.A*B + b.B*(1<<D)
        A=b.A*A
        D+=b.D
    return A,B,D


def analyze(r0,m0,cap):
    x0=(1<<r0)*m0-1
    if x0==1:
        return {"base":True,"closed":True,"delay":0,"cycles":[],"spine":[1]}

    x=x0
    # stack nodes are r values; edges[i] maps nodes[i] -> nodes[i+1]
    nodes=[r0]
    edge_branches=[]
    edge_entry_m=[]
    pos={r0:0}
    cycles=[]
    max_spine=1

    for j in range(cap):
        r,m,s,rp,mp,xp=episode(x)
        assert r==nodes[-1]
        b=branch_for_residue(r,m)
        assert (b.r,b.s,b.rp)==(r,s,rp)
        assert b.map_m(m)==mp

        if rp in pos:
            start=pos[rp]
            bs=edge_branches[start:]+[b]
            entry_m=edge_entry_m[start] if start<len(edge_entry_m) else m
            A,B,D=compose(bs)
            assert (A*entry_m+B)%(1<<D)==0
            exit_m=(A*entry_m+B)//(1<<D)
            assert exit_m==mp,(r0,m0,j,start,entry_m,exit_m,mp)

            den=(1<<D)-A
            q=None if den==0 else Fraction(B,den)
            kind=(
                "neutral" if q is None else
                "positive_integer" if q>0 and q.denominator==1 else
                "positive_noninteger" if q>0 else
                "zero" if q==0 else
                "negative"
            )
            cycles.append({
                "episode_end":j+1,
                "start_r":rp,
                "length":len(bs),
                "A":A,"B":B,"D":D,
                "entry_m":entry_m,"exit_m":exit_m,
                "fixed_point":str(q) if q is not None else None,
                "kind":kind,
                "schemas":[[z.r,z.s,z.rp] for z in bs],
            })

            # Erase edges/nodes after the retained repeated node.
            for rr in nodes[start+1:]:
                pos.pop(rr,None)
            nodes=nodes[:start+1]
            edge_branches=edge_branches[:start]
            edge_entry_m=edge_entry_m[:start]
            # Current episode lands at retained node rp with new cofactor mp.
            # The next outgoing edge will use mp; store state via x below.
        else:
            edge_entry_m.append(m)
            edge_branches.append(b)
            nodes.append(rp)
            pos[rp]=len(nodes)-1

        max_spine=max(max_spine,len(nodes))
        if xp<x0:
            nonbase_positive=[
                z for z in cycles
                if z["kind"]=="positive_integer"
                and not (z["fixed_point"]=="1" and z["start_r"]==1)
            ]
            return {
                "base":False,"closed":True,"delay":j+1,
                "cycles":cycles,"cycle_episode_total":sum(z["length"] for z in cycles),
                "cycle_count":len(cycles),
                "max_spine":max_spine,"final_spine":nodes,
                "max_r_seen":max([r0]+[z["start_r"] for z in cycles]+nodes),
                "nonbase_positive_cycles":nonbase_positive,
            }
        x=xp

    return {
        "base":False,"closed":False,"delay":cap,
        "cycles":cycles,"cycle_episode_total":sum(z["length"] for z in cycles),
        "cycle_count":len(cycles),"max_spine":max_spine,
        "final_spine":nodes,
        "nonbase_positive_cycles":[],
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-r",type=int,default=12)
    ap.add_argument("--precision",type=int,required=True)
    ap.add_argument("--max-episodes",type=int,default=512)
    ap.add_argument("--out")
    a=ap.parse_args()
    assert 4<=a.max_r<=20
    assert 10<=a.precision<=18

    M=1<<a.precision
    base=0;unresolved=0;max_delay=0
    max_spine=0;max_cycles=0
    total_delay=0;total_cycle_episodes=0;total_cycles=0
    nonbase_positive=0
    hardest=[]

    for r in range(1,a.max_r+1):
        for m in range(1,M,2):
            z=analyze(r,m,a.max_episodes)
            if z["base"]:
                base+=1
                continue
            if not z["closed"]:
                unresolved+=1
            max_delay=max(max_delay,z["delay"])
            max_spine=max(max_spine,z["max_spine"])
            max_cycles=max(max_cycles,z["cycle_count"])
            total_delay+=z["delay"]
            total_cycle_episodes+=z["cycle_episode_total"]
            total_cycles+=z["cycle_count"]
            nonbase_positive+=len(z["nonbase_positive_cycles"])

            row={
                "r":r,"m":m,"x":(1<<r)*m-1,
                "delay":z["delay"],"cycle_count":z["cycle_count"],
                "cycle_episode_total":z["cycle_episode_total"],
                "cycle_fraction":z["cycle_episode_total"]/z["delay"] if z["delay"] else 0,
                "max_spine":z["max_spine"],
                "final_spine":z["final_spine"],
                "cycles":z["cycles"][:32],
            }
            if len(hardest)<32:
                hardest.append(row)
                hardest.sort(key=lambda q:(-q["delay"],q["r"],q["m"]))
            elif row["delay"]>hardest[-1]["delay"]:
                hardest[-1]=row
                hardest.sort(key=lambda q:(-q["delay"],q["r"],q["m"]))

    cases=a.max_r*(M//2)
    nonbase=cases-base
    out={
        "kind":"bounded_episode_cycle_erasure",
        "max_r":a.max_r,"precision":a.precision,
        "cases":cases,"base_cases":base,"unresolved":unresolved,
        "max_delay":max_delay,"max_spine":max_spine,"max_cycles":max_cycles,
        "mean_delay":total_delay/nonbase,
        "mean_cycle_count":total_cycles/nonbase,
        "cycle_episode_fraction":total_cycle_episodes/total_delay if total_delay else 0,
        "nonbase_positive_integer_cycles":nonbase_positive,
        "hardest":hardest,
        "proof_status":"exact_bounded_cycle_erasure_not_global_proof",
    }
    if a.out:
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")

    print("EPISODE_CYCLE_ERASURE",
          f"max_r={a.max_r}",f"precision={a.precision}",
          f"cases={cases}",f"base={base}",f"unresolved={unresolved}",
          f"max_delay={max_delay}",f"max_spine={max_spine}",
          f"max_cycles={max_cycles}",
          f"cycle_episode_fraction={out['cycle_episode_fraction']:.12f}",
          f"nonbase_positive_cycles={nonbase_positive}")
    print("VERIFIED_BOUNDED_EPISODE_CYCLE_ERASURE")


if __name__=="__main__":
    main()
