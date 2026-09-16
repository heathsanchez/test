#!/usr/bin/env python3
"""Cycle-erasure structure of the eventually-stable pullback tail.

Combines two exact views:
  1) exact pullback cylinders identify an ordinary positive m0 once
     2^(D+1) > m0, after which canonical pullback residue equals m0 forever;
  2) complete odd episodes produce an r-sequence that can be loop-erased.

For every bounded concrete trajectory until first descent below x0, this script
starts measuring at the first prefix where the pullback residue has stabilized
numerically to m0.  It then loop-erases the r-sequence and records how much of
the stable tail is return-cycle churn versus genuinely new spine growth.

This does not prove the spine is globally bounded and does not prove that
arbitrary varying return cycles share one countdown.  It isolates exactly
which of those obligations remains if the bounded pattern persists.
"""

from __future__ import annotations

import argparse,json
from collections import Counter
from pathlib import Path
from collatz_odd_episode_grammar import episode


def compose(A,B,D,r,s,rp):
    d=s+rp
    return 3**r*A, 3**r*B + ((1<<s)-1)*(1<<D), D+d


def rho(A,B,D):
    mod=1<<(D+1)
    return ((1<<D)-B)*pow(A,-1,mod)%mod,mod


def loop_erase_push(spine:list[int], nxt:int):
    """Return erased cycle length (0 if no return); keep one copy of nxt."""
    if nxt not in spine:
        spine.append(nxt)
        return 0
    i=spine.index(nxt)
    erased=len(spine)-i
    del spine[i+1:]
    return erased


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-r",type=int,default=16)
    ap.add_argument("--precision",type=int,default=16)
    ap.add_argument("--episode-cap",type=int,default=256)
    ap.add_argument("--out")
    a=ap.parse_args()
    M=1<<a.precision

    cases=0; unresolved=0; stabilized=0
    max_stable_len=0; max_stable_spine=0; max_stable_cycles=0
    max_cycle_erased_steps=0
    max_case=None
    spine_hist=Counter(); cycle_hist=Counter(); stable_hist=Counter()
    signature_hist=Counter()

    for r0 in range(1,a.max_r+1):
        for m0 in range(1,M,2):
            x0=(1<<r0)*m0-1
            if x0==1: continue
            cases+=1
            x=x0; A=B=D=0
            A=1
            stable=False
            stable_len=0; cycles=0; erased_steps=0
            spine=[]
            descended=False

            for j in range(1,a.episode_cap+1):
                r,m,s,rp,mp,xp=episode(x)
                A,B,D=compose(A,B,D,r,s,rp)
                rr,mod=rho(A,B,D)
                assert m0%mod==rr
                assert (A*m0+B)==(1<<D)*mp

                if mod>m0:
                    assert rr==m0
                    if not stable:
                        stable=True; stabilized+=1
                        spine=[r]
                    stable_len+=1
                    erased=loop_erase_push(spine,rp)
                    if erased:
                        cycles+=1
                        erased_steps+=erased
                        # Local return signature: enough to distinguish exact
                        # one-episode returns and give a lower bound on
                        # signature diversity. Longer erased cycles are counted
                        # by their endpoint r and erased length.
                        signature_hist[(r,rp,s,erased)]+=1

                    max_stable_spine=max(max_stable_spine,len(spine))

                if xp<x0:
                    descended=True
                    break
                x=xp

            if not descended: unresolved+=1
            if stable:
                stable_hist[stable_len]+=1
                spine_hist[len(spine)]+=1
                cycle_hist[cycles]+=1
                if stable_len>max_stable_len or (
                    stable_len==max_stable_len and cycles>max_stable_cycles
                ):
                    max_stable_len=stable_len
                    max_stable_cycles=cycles
                    max_cycle_erased_steps=erased_steps
                    max_case={
                        "r0":r0,"m0":m0,"x0":x0,
                        "stable_len":stable_len,"cycles":cycles,
                        "erased_steps":erased_steps,
                        "final_spine":spine.copy(),
                        "final_spine_len":len(spine),
                        "episodes":j,"D":D,
                    }

    assert unresolved==0,(unresolved,cases)
    out={
        "kind":"stable_pullback_cycle_erasure",
        "max_r":a.max_r,"precision":a.precision,"cases":cases,
        "stabilized_cases":stabilized,"unresolved":unresolved,
        "max_stable_tail_episodes":max_stable_len,
        "max_stable_loop_erased_spine":max_stable_spine,
        "max_stable_return_cycles_on_record_case":max_stable_cycles,
        "max_cycle_erased_steps_on_record_case":max_cycle_erased_steps,
        "record_case":max_case,
        "stable_length_hist":dict(sorted(stable_hist.items())),
        "final_spine_hist":dict(sorted(spine_hist.items())),
        "stable_cycle_count_hist":dict(sorted(cycle_hist.items())),
        "distinct_observed_return_signatures":len(signature_hist),
        "top_return_signatures":[
            {"signature":list(k),"count":v}
            for k,v in signature_hist.most_common(40)
        ],
        "remaining_global_obligations":[
            "prove_or_refute_uniform_bound_on_loop_erased_stable_r_spine",
            "find_common_well_founded_rank_for_varying_exact_return_cycles",
            "or_show_infinite_stable_tail_forces_nonpositive_or_nonordinary_2adic_input",
        ],
        "proof_status":"bounded_exact_decomposition_not_Collatz_proof",
    }
    if a.out:
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")

    print("STABLE_TAIL_CYCLE_ERASURE",
          f"max_r={a.max_r}",f"precision={a.precision}",f"cases={cases}",
          f"stabilized={stabilized}",f"unresolved={unresolved}",
          f"max_stable_tail={max_stable_len}",
          f"max_stable_spine={max_stable_spine}",
          f"record_cycles={max_stable_cycles}",
          f"record_erased_steps={max_cycle_erased_steps}",
          f"distinct_return_signatures={len(signature_hist)}")
    if max_case: print("STABLE_TAIL_RECORD",json.dumps(max_case,separators=(",",":")))
    print("STABLE_PULLBACK_TAIL_DECOMPOSED_INTO_SPINE_PLUS_RETURN_CYCLES")
    print("VERIFIED_STABLE_TAIL_CYCLE_ERASURE")


if __name__=="__main__":
    main()
