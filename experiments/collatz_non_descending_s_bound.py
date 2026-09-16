#!/usr/bin/env python3
"""Exact branch bound for a non-descending complete odd Collatz episode.

For odd x>1 write x=2^r m-1, r>=1, m odd.  A complete odd episode is

    x' = (3^r m - 1) / 2^s,

where s=v2(3^r m-1)>=1.

If x' >= x, then

    2^s <= (3^r m - 1)/(2^r m - 1).

For a=3^r>b=2^r, f(m)=(a m-1)/(b m-1) is strictly decreasing on m>=1,
because f'(m)=(b-a)/(b m-1)^2 < 0.  Therefore

    2^s <= (3^r - 1)/(2^r - 1),

and hence

    s <= S(r) = floor(log2((3^r-1)/(2^r-1))).

Thus, if r and r' are bounded, the branch schemas of LOCALLY
NONDECREASING episodes range over a finite set.

Important limitation: a trajectory that never falls below its ORIGINAL
starting value may still contain locally decreasing episodes x'<x that remain
above that original value.  Those edges are not covered by this s-bound and
can have larger s.  Therefore this lemma alone does NOT reduce an arbitrary
globally non-descending trajectory to a finite schema grammar.

This script verifies the integer inequality exhaustively on bounded residues
and emits the exact S(r) table.  The algebraic derivation above is general
for each locally nondecreasing episode; the enumeration is only an
implementation control.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from collatz_odd_episode_grammar import episode


def S(r:int)->int:
    num=3**r-1
    den=2**r-1
    # Largest s with 2^s * den <= num.
    s=0
    while (1<<(s+1))*den <= num:
        s+=1
    return s


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-r",type=int,default=64)
    ap.add_argument("--control-r",type=int,default=16)
    ap.add_argument("--precision",type=int,default=16)
    ap.add_argument("--out")
    a=ap.parse_args()
    assert 1<=a.control_r<=a.max_r<=256
    assert 8<=a.precision<=20

    table=[]
    for r in range(1,a.max_r+1):
        s=S(r)
        assert (1<<s)*(2**r-1) <= 3**r-1
        assert (1<<(s+1))*(2**r-1) > 3**r-1
        table.append({"r":r,"max_non_descending_s":s})

    M=1<<a.precision
    controls=0
    non_desc=0
    max_slack=0

    for r in range(1,a.control_r+1):
        sr=S(r)
        for m in range(1,M,2):
            x=(1<<r)*m-1
            if x==1:
                continue
            rr,mm,s,rp,mp,xp=episode(x)
            assert rr==r and mm==m
            if xp>=x:
                non_desc+=1
                assert s<=sr,(r,m,s,sr,x,xp)
                lhs=(1<<s)*(2**r*m-1)
                rhs=3**r*m-1
                assert lhs<=rhs
                max_slack=max(max_slack,sr-s)
            controls+=1

    out={
        "kind":"global_non_descending_episode_s_bound",
        "max_r":a.max_r,
        "control_r":a.control_r,
        "precision":a.precision,
        "table":table,
        "controls":controls,
        "non_descending_controls":non_desc,
        "max_s_bound_slack":max_slack,
        "global_statement":
            "x_prime>=x implies s<=floor(log2((3^r-1)/(2^r-1)))",
        "scope":[
            "locally_nondecreasing_episode_only",
            "does_not_bound_locally_decreasing_edges_above_original_baseline",
        ],
    }

    if a.out:
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")

    print("NON_DESCENDING_EPISODE_S_BOUND",
          f"max_r={a.max_r}",
          f"control_r={a.control_r}",
          f"precision={a.precision}",
          f"controls={controls}",
          f"non_descending={non_desc}",
          f"S_max={max(z['max_non_descending_s'] for z in table)}")
    print("VERIFIED_GLOBAL_NON_DESCENDING_EPISODE_S_BOUND")


if __name__=="__main__":
    main()
