#!/usr/bin/env python3
"""Exact return-cycle certificates plus loop-erased r-spine compression.

For each bounded odd state x=2^r m-1, follow complete odd episodes until the
first x_j<x_0.

Two representations are maintained deliberately separately:

1. FULL ACTUAL HISTORY.
   Whenever the next r' has appeared before, use its most recent actual
   occurrence in the unmodified trajectory.  The contiguous branch segment
   from that occurrence to the new state is an exact closed r-return.  Compose

       F(m)=(A m+B)/2^D

   and verify it maps the actual entry cofactor to the actual exit cofactor.

2. LOOP-ERASED r-SPINE.
   Independently maintain only the simple r-state spine.  When r' repeats,
   erase the loop topologically and count how many spine edges were removed.
   This measures how much of a long episode path is recurrence versus genuinely
   new r-state exploration, without pretending erased affine maps disappeared.

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


def v2_abs(n:int)->int:
    n=abs(n)
    assert n>0
    return (n & -n).bit_length()-1


def classify_cycle(bs,entry_m,exit_m):
    A,B,D=compose(bs)
    mod=1<<D
    assert (A*entry_m+B)%mod==0
    assert (A*entry_m+B)//mod==exit_m
    den=mod-A
    q=None if den==0 else Fraction(B,den)
    kind=(
        "neutral" if q is None else
        "positive_integer" if q>0 and q.denominator==1 else
        "positive_noninteger" if q>0 else
        "zero" if q==0 else
        "negative"
    )

    # For the cycle fixed-point numerator N=(2^D-A)m-B:
    # N_exit = A*N_entry/2^D.  Thus every exact cycle traversal
    # has v2(N_entry)>=D unless N=0 (an exact integer fixed point).
    N=den*entry_m-B
    if N==0:
        countdown_bits=None
        repeat_budget=None
    else:
        countdown_bits=v2_abs(N)
        assert countdown_bits>=D,(A,B,D,entry_m,exit_m,N,countdown_bits)
        repeat_budget=countdown_bits//D

    direction=(
        "down" if exit_m<entry_m else
        "up" if exit_m>entry_m else
        "fixed"
    )
    return {
        "length":len(bs),"A":A,"B":B,"D":D,
        "entry_m":entry_m,"exit_m":exit_m,
        "fixed_point":str(q) if q is not None else None,
        "kind":kind,"direction":direction,
        "countdown_bits":countdown_bits,
        "immediate_repeat_budget":repeat_budget,
        "schemas":[[z.r,z.s,z.rp] for z in bs],
    }


def analyze(r0,m0,cap):
    x0=(1<<r0)*m0-1
    if x0==1:
        return {"base":True,"closed":True,"delay":0}

    x=x0

    # Full actual state/edge history.
    actual_nodes=[(r0,m0)]
    actual_edges=[]
    last_index={r0:0}
    return_cycles=[]

    # Pure topology for chronological loop erasure.
    spine=[r0]
    spine_pos={r0:0}
    erased_edges=0
    max_spine=1
    max_r_seen=r0

    for j in range(cap):
        r,m,s,rp,mp,xp=episode(x)
        assert (r,m)==actual_nodes[-1]
        b=branch_for_residue(r,m)
        assert (b.r,b.s,b.rp)==(r,s,rp)
        assert b.map_m(m)==mp

        # Exact contiguous return-cycle in actual history.
        if rp in last_index:
            start=last_index[rp]
            bs=actual_edges[start:]+[b]
            entry_m=actual_nodes[start][1]
            z=classify_cycle(bs,entry_m,mp)
            z["episode_end"]=j+1
            z["start_r"]=rp
            return_cycles.append(z)

        actual_edges.append(b)
        actual_nodes.append((rp,mp))
        last_index[rp]=len(actual_nodes)-1

        # Independent loop-erased r-spine.
        if rp in spine_pos:
            start=spine_pos[rp]
            # Current edge plus all retained spine edges after repeated node.
            erased_edges += len(spine)-start
            for rr in spine[start+1:]:
                spine_pos.pop(rr,None)
            spine=spine[:start+1]
        else:
            spine.append(rp)
            spine_pos[rp]=len(spine)-1

        max_spine=max(max_spine,len(spine))
        max_r_seen=max(max_r_seen,rp)

        if xp<x0:
            # Partition check: actual episode edges are either currently on
            # the simple spine or were erased by a repeat.
            assert erased_edges + (len(spine)-1) == j+1, (
                r0,m0,j+1,erased_edges,len(spine)-1,spine
            )
            nonbase_positive=[
                z for z in return_cycles
                if z["kind"]=="positive_integer"
                and not (z["fixed_point"]=="1" and z["start_r"]==1)
            ]
            return {
                "base":False,"closed":True,"delay":j+1,
                "return_cycles":return_cycles,
                "return_cycle_count":len(return_cycles),
                "erased_edges":erased_edges,
                "erased_fraction":erased_edges/(j+1),
                "max_spine":max_spine,
                "final_spine":spine,
                "max_r_seen":max_r_seen,
                "nonbase_positive_cycles":nonbase_positive,
            }
        x=xp

    return {
        "base":False,"closed":False,"delay":cap,
        "return_cycles":return_cycles,
        "return_cycle_count":len(return_cycles),
        "erased_edges":erased_edges,
        "erased_fraction":erased_edges/cap,
        "max_spine":max_spine,"final_spine":spine,
        "max_r_seen":max_r_seen,
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
    max_spine=0;max_returns=0;max_r_seen=0
    total_delay=0;total_erased=0;total_returns=0
    nonbase_positive=0
    cycle_kind_counts={}
    cycle_direction_counts={}
    min_repeat_budget=None
    max_repeat_budget=0
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
            max_returns=max(max_returns,z["return_cycle_count"])
            max_r_seen=max(max_r_seen,z["max_r_seen"])
            total_delay+=z["delay"]
            total_erased+=z["erased_edges"]
            total_returns+=z["return_cycle_count"]
            nonbase_positive+=len(z["nonbase_positive_cycles"])
            for cyc in z["return_cycles"]:
                cycle_kind_counts[cyc["kind"]]=cycle_kind_counts.get(cyc["kind"],0)+1
                cycle_direction_counts[cyc["direction"]]=cycle_direction_counts.get(cyc["direction"],0)+1
                rb=cyc["immediate_repeat_budget"]
                if rb is not None:
                    min_repeat_budget=rb if min_repeat_budget is None else min(min_repeat_budget,rb)
                    max_repeat_budget=max(max_repeat_budget,rb)

            row={
                "r":r,"m":m,"x":(1<<r)*m-1,
                "delay":z["delay"],
                "return_cycle_count":z["return_cycle_count"],
                "erased_edges":z["erased_edges"],
                "erased_fraction":z["erased_fraction"],
                "max_spine":z["max_spine"],
                "max_r_seen":z["max_r_seen"],
                "final_spine":z["final_spine"],
                "return_cycles":z["return_cycles"][:32],
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
        "max_delay":max_delay,"max_spine":max_spine,
        "max_return_cycles":max_returns,"max_r_seen":max_r_seen,
        "mean_delay":total_delay/nonbase,
        "mean_return_cycle_count":total_returns/nonbase,
        "erased_episode_fraction":total_erased/total_delay if total_delay else 0,
        "nonbase_positive_integer_return_cycles":nonbase_positive,
        "cycle_kind_counts":cycle_kind_counts,
        "cycle_direction_counts":cycle_direction_counts,
        "min_immediate_repeat_budget":min_repeat_budget,
        "max_immediate_repeat_budget":max_repeat_budget,
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
          f"max_return_cycles={max_returns}",f"max_r_seen={max_r_seen}",
          f"erased_episode_fraction={out['erased_episode_fraction']:.12f}",
          f"nonbase_positive_return_cycles={nonbase_positive}",
          f"cycle_kinds={cycle_kind_counts}",
          f"cycle_directions={cycle_direction_counts}",
          f"repeat_budget_range={min_repeat_budget}:{max_repeat_budget}")
    print("VERIFIED_BOUNDED_EPISODE_CYCLE_ERASURE")


if __name__=="__main__":
    main()
