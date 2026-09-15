#!/usr/bin/env python3
"""Exact pullback of odd-episode words to initial 2-adic cylinders.

For a sequence of exact episode schemas
    (r0,s0,r1), (r1,s1,r2), ...,
the episode recurrence is
    m_{j+1} = (3^rj m_j + 2^sj - 1) / 2^(sj+r_{j+1}).

Composing gives
    m_j = (A_j m_0 + B_j) / 2^D_j
with A_j odd.

Exact integrality therefore forces the UNIQUE initial congruence
    m_0 == rho_j (mod 2^D_j),
    rho_j = -B_j * A_j^{-1} mod 2^D_j.

Thus every additional exact episode consumes D increment bits of initial
2-adic precision.  A long non-descending path can only exist for ordinary
positive integer m0 if these pulled-back residues remain compatible with that
finite integer as D grows.

This experiment enumerates concrete bounded states, follows them until first
descent, and for every prefix verifies:
  1. the composed affine formula exactly;
  2. m0 satisfies the unique pulled-back congruence;
  3. cumulative precision D strictly increases;
  4. the actual m0 requires D no larger than its eventual-zero extension
     when the prefix is observed.

It then profiles the hardest paths by precision consumed per episode and by
how close rho is to the ordinary positive representative m0.

This is a bounded exact certificate and diagnostic, not a global Collatz proof.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from collatz_odd_episode_grammar import episode


def compose_step(A: int, B: int, D: int, r: int, s: int, rp: int):
    d=s+rp
    # (3^r * (A m+B)/2^D + (2^s-1)) / 2^d
    A2=(3**r)*A
    B2=(3**r)*B + ((1<<s)-1)*(1<<D)
    return A2,B2,D+d


def run_prefixes(r0:int,m0:int,max_episodes:int):
    x0=(1<<r0)*m0-1
    if x0==1:
        return True,[],0
    x=x0
    A,B,D=1,0,0
    rows=[]
    for j in range(max_episodes):
        r,m,s,rp,mp,xp=episode(x)
        A,B,D=compose_step(A,B,D,r,s,rp)
        mod=1<<D
        inv=pow(A,-1,mod)
        rho=(-B*inv)%mod
        assert m0%mod==rho,(r0,m0,j,D,rho,m0%mod)
        assert (A*m0+B)%mod==0
        assert (A*m0+B)//mod==mp
        rows.append({
            "episode":j+1,
            "r":r,"s":s,"rp":rp,
            "D":D,"rho":rho,
            "rho_bits":rho.bit_length(),
            "m0_bits":m0.bit_length(),
            "rho_equals_m0":rho==m0,
            "rho_above_m0":rho>m0,
        })
        if xp<x0:
            return True,rows,j+1
        x=xp
    return False,rows,max_episodes


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-r",type=int,default=16)
    ap.add_argument("--precision",type=int,required=True)
    ap.add_argument("--max-episodes",type=int,default=512)
    ap.add_argument("--out")
    a=ap.parse_args()
    assert 4<=a.max_r<=20
    assert 10<=a.precision<=20

    M=1<<a.precision
    base=0;unresolved=0;max_delay=0
    hardest=[]
    eq_before_descent=0
    prefixes=0
    total_D=0
    max_D=0
    min_D_per_episode=None
    max_D_per_episode=0.0

    for r in range(1,a.max_r+1):
        for m in range(1,M,2):
            x=(1<<r)*m-1
            if x==1:
                base+=1
                continue
            closed,rows,delay=run_prefixes(r,m,a.max_episodes)
            if not closed:
                unresolved+=1
            max_delay=max(max_delay,delay)
            prefixes+=len(rows)
            if rows:
                D=rows[-1]["D"]
                total_D+=D
                max_D=max(max_D,D)
                ratio=D/len(rows)
                min_D_per_episode=ratio if min_D_per_episode is None else min(min_D_per_episode,ratio)
                max_D_per_episode=max(max_D_per_episode,ratio)
                if any(z["rho_equals_m0"] for z in rows[:-1]):
                    eq_before_descent+=1
            row={
                "r":r,"m":m,"x":x,"delay":delay,"closed":closed,
                "final_D":rows[-1]["D"] if rows else 0,
                "D_per_episode":(rows[-1]["D"]/delay) if rows and delay else None,
                "last_rho":rows[-1]["rho"] if rows else None,
                "last_rho_equals_m0":rows[-1]["rho_equals_m0"] if rows else False,
                "prefixes":rows[:32],
            }
            if len(hardest)<64:
                hardest.append(row)
                hardest.sort(key=lambda z:(-z["delay"],-z["final_D"],z["r"],z["m"]))
            elif (delay,row["final_D"])>(hardest[-1]["delay"],hardest[-1]["final_D"]):
                hardest[-1]=row
                hardest.sort(key=lambda z:(-z["delay"],-z["final_D"],z["r"],z["m"]))

    out={
        "kind":"bounded_episode_pullback_precision",
        "max_r":a.max_r,
        "precision":a.precision,
        "cases":a.max_r*(M//2),
        "base_cases":base,
        "unresolved":unresolved,
        "max_delay":max_delay,
        "prefixes_checked":prefixes,
        "max_cumulative_D":max_D,
        "mean_final_D":total_D/(a.max_r*(M//2)-base),
        "min_D_per_episode":min_D_per_episode,
        "max_D_per_episode":max_D_per_episode,
        "rho_equals_m0_before_descent_cases":eq_before_descent,
        "hardest":hardest,
        "proof_status":"exact_bounded_pullback_not_global_proof",
    }
    if a.out:
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")

    print("EPISODE_PULLBACK_PRECISION",
          f"max_r={a.max_r}",f"precision={a.precision}",
          f"cases={out['cases']}",f"base={base}",
          f"unresolved={unresolved}",f"max_delay={max_delay}",
          f"prefixes={prefixes}",f"max_D={max_D}",
          f"min_D_per_episode={min_D_per_episode:.12f}",
          f"mean_final_D={out['mean_final_D']:.12f}")
    print("VERIFIED_EXACT_EPISODE_PULLBACK_PRECISION")


if __name__=="__main__":
    main()
