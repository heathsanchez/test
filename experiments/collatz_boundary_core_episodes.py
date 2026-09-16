#!/usr/bin/env python3
"""Exact odd-episode decomposition of the first H512 boundary lineage.

The four K33/K34 H512 failures coalesce to CORE=26130934783.
This script decomposes CORE until its first direct descent, computes exact
pullback cylinders with corrected D+1 semantics, marks the point at which the
pullback residue has numerically stabilized to the ordinary initial cofactor,
and loop-erases the r-sequence.

Purpose: determine whether the first late one-step boundary is a genuinely new
long spine or mostly return-cycle churn around a small exact episode skeleton.
"""

from __future__ import annotations
import json
from collatz_odd_episode_grammar import episode

CORE=26130934783


def v2(n:int)->int:
    assert n>0
    return (n & -n).bit_length()-1


def decompose_odd(x:int):
    assert x&1
    r=v2(x+1)
    m=(x+1)>>r
    assert m&1
    return r,m


def compose(A,B,D,r,s,rp):
    d=s+rp
    return 3**r*A, 3**r*B + ((1<<s)-1)*(1<<D), D+d


def rho(A,B,D):
    mod=1<<(D+1)
    return ((1<<D)-B)*pow(A,-1,mod)%mod,mod


def loop_push(spine,nxt):
    if nxt not in spine:
        spine.append(nxt)
        return None
    i=spine.index(nxt)
    cyc=spine[i:]+[nxt]
    del spine[i+1:]
    return cyc


def T(n:int)->int:
    return (3*n+1)//2 if n&1 else n//2


def first_direct(n:int):
    y=n
    for t in range(10000):
        if t and y<n:return t,y
        y=T(y)
    raise AssertionError("no direct descent in bound")


def main():
    r0,m0=decompose_odd(CORE)
    x=CORE
    A,B,D=1,0,0
    spine=[r0]
    cycles=[]
    rows=[]
    stable_at=None

    for j in range(1,1000):
        r,m,s,rp,mp,xp=episode(x)
        A,B,D=compose(A,B,D,r,s,rp)
        rr,mod=rho(A,B,D)
        assert m0%mod==rr
        assert (A*m0+B)==(1<<D)*mp
        stable=(mod>m0)
        if stable:
            assert rr==m0
            if stable_at is None:stable_at=j

        cyc=loop_push(spine,rp)
        if cyc is not None:cycles.append(cyc)

        rows.append({
            "episode":j,"x":x,"r":r,"m":m,"s":s,"rp":rp,
            "xp":xp,"D":D,"rho":rr,"mod_bits":D+1,
            "pullback_stable":stable,
            "spine":spine.copy(),
            "cycle":cyc,
        })
        if xp<CORE:
            break
        x=xp
    else:
        raise AssertionError("episode cap")

    t,y=first_direct(CORE)
    assert t==531,(t,y)
    assert y==25459365718,(t,y)

    out={
        "core":CORE,
        "r0":r0,"m0":m0,
        "shortcut_first_direct_t":t,
        "shortcut_first_direct_y":y,
        "episodes_to_direct_descent":len(rows),
        "pullback_stabilizes_at_episode":stable_at,
        "stable_tail_episodes":len(rows)-stable_at+1 if stable_at else 0,
        "max_spine_len":max(len(z["spine"]) for z in rows),
        "final_spine":rows[-1]["spine"],
        "return_cycle_count":len(cycles),
        "return_cycles":cycles,
        "rows":rows,
        "scope":"exact decomposition of first observed H512 boundary lineage, not global proof",
    }

    print("BOUNDARY_CORE_EPISODES",
          f"core={CORE}",f"r0={r0}",f"m0={m0}",
          f"episodes={len(rows)}",f"stable_at={stable_at}",
          f"stable_tail={out['stable_tail_episodes']}",
          f"max_spine={out['max_spine_len']}",
          f"return_cycles={len(cycles)}",
          f"direct_t={t}")
    for z in rows:
        print("BOUNDARY_CORE_EPISODE",
              f"j={z['episode']}",f"r={z['r']}",f"s={z['s']}",
              f"rp={z['rp']}",f"D={z['D']}",
              f"stable={int(z['pullback_stable'])}",
              "spine="+",".join(map(str,z["spine"])))
    print("VERIFIED_BOUNDARY_CORE_EPISODE_DECOMPOSITION")


if __name__=="__main__":
    main()
