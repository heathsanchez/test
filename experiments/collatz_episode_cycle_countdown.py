#!/usr/bin/env python3
"""Exact cycle-countdown analysis for the odd-episode Collatz grammar.

For an exact episode branch

    m' = (3^r m + 2^s - 1) / 2^(s+r'),

a fixed branch word W composes to

    F_W(m) = (A m + B) / 2^D,

where A is odd.  Its rational fixed point is

    q = B / (2^D - A).

Because 2^D-A is odd,

    F_W(m)-q = (A/2^D)(m-q)

and therefore each exact repetition of W decreases the 2-adic valuation of
m-q by exactly D.  Thus a fixed cycle cannot repeat forever for an ordinary
integer m unless m=q exactly.

This experiment enumerates exact bounded branch cylinders, finds short simple
r-cycles, composes every compatible branch-schema cycle, and classifies its
fixed point.  It is evidence toward a global rank theorem; bounded cycle
coverage is NOT a Collatz proof.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict, Counter
from fractions import Fraction
from pathlib import Path

from collatz_odd_episode_grammar import first_branch_partition


def compose(branches):
    A,B,D=1,0,0
    for b in branches:
        B=b.A*B + b.B*(1<<D)
        A=b.A*A
        D+=b.D
    return A,B,D


def canonical_schema(b):
    return (b.r,b.s,b.rp)


def simple_r_cycles(edges, max_len):
    adj=defaultdict(set)
    for a,b in edges:
        adj[a].add(b)
    cycles=set()

    def canon(c):
        # c is nodes without repeated terminal start.
        rots=[tuple(c[i:]+c[:i]) for i in range(len(c))]
        return min(rots)

    nodes=sorted(adj)
    for start in nodes:
        stack=[(start,[start])]
        while stack:
            cur,path=stack.pop()
            if len(path)>max_len:
                continue
            for nxt in adj[cur]:
                if nxt==start:
                    cycles.add(canon(path))
                elif nxt not in path and len(path)<max_len:
                    stack.append((nxt,path+[nxt]))
    return sorted(cycles,key=lambda z:(len(z),z))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-r",type=int,default=12)
    ap.add_argument("--precision",type=int,default=16)
    ap.add_argument("--max-cycle-len",type=int,default=4)
    ap.add_argument("--out")
    a=ap.parse_args()

    assert 2<=a.max_r<=20
    assert 8<=a.precision<=20
    assert 1<=a.max_cycle_len<=6

    by_edge=defaultdict(dict)
    edges=set()
    precision_boundary=0

    for r in range(1,a.max_r+1):
        branches,covered,unresolved=first_branch_partition(r,a.precision)
        precision_boundary+=unresolved
        for b in branches:
            if b.rp>a.max_r:
                continue
            edges.add((b.r,b.rp))
            # Map schema -> one exact representative. Formula depends only on
            # (r,s,rp), so duplicate residue cylinders share the same map.
            by_edge[(b.r,b.rp)].setdefault(canonical_schema(b),b)

    rcycles=simple_r_cycles(edges,a.max_cycle_len)
    classified=Counter()
    cycle_rows=[]
    total_schema_cycles=0
    positive_integer_fixed=[]

    for nodes in rcycles:
        L=len(nodes)
        choices=[]
        ok=True
        for i in range(L):
            e=(nodes[i],nodes[(i+1)%L])
            bs=list(by_edge[e].values())
            if not bs:
                ok=False;break
            choices.append(bs)
        if not ok:
            continue

        # Enumerate branch-schema products for this short r-cycle.
        def rec(i,word):
            nonlocal total_schema_cycles
            if i==L:
                total_schema_cycles+=1
                A,B,D=compose(word)
                den=(1<<D)-A
                if den==0:
                    kind="neutral"
                    q=None
                else:
                    q=Fraction(B,den)
                    if q.denominator==1 and q>0:
                        kind="positive_integer"
                    elif q>0:
                        kind="positive_noninteger"
                    elif q==0:
                        kind="zero"
                    else:
                        kind="negative"
                classified[kind]+=1

                # Exact 2-adic countdown identity: den is odd whenever nonzero.
                assert den==0 or abs(den)%2==1
                if kind=="positive_integer":
                    row={
                        "r_cycle":list(nodes),
                        "schemas":[list(canonical_schema(b)) for b in word],
                        "A":A,"B":B,"D":D,
                        "fixed_point":int(q),
                    }
                    positive_integer_fixed.append(row)
                if len(cycle_rows)<500:
                    cycle_rows.append({
                        "r_cycle":list(nodes),
                        "schemas":[list(canonical_schema(b)) for b in word],
                        "A":A,"B":B,"D":D,
                        "fixed_point":str(q) if q is not None else None,
                        "kind":kind,
                        "countdown_per_repeat":D,
                    })
                return
            for b in choices[i]:
                rec(i+1,word+[b])
        rec(0,[])

    nonbase_positive=[
        z for z in positive_integer_fixed
        if not (z["fixed_point"]==1 and z["r_cycle"]==[1])
    ]

    out={
        "kind":"bounded_odd_episode_cycle_countdown",
        "max_r":a.max_r,
        "precision":a.precision,
        "max_cycle_len":a.max_cycle_len,
        "precision_boundary_unresolved":precision_boundary,
        "r_cycle_count":len(rcycles),
        "schema_cycle_count":total_schema_cycles,
        "fixed_point_classes":dict(classified),
        "positive_integer_fixed_points":positive_integer_fixed[:500],
        "nonbase_positive_integer_fixed_points":nonbase_positive[:500],
        "sample_cycles":cycle_rows,
        "proof_status":"bounded_cycle_countdown_not_global_proof",
    }

    if a.out:
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")

    print("EPISODE_CYCLE_COUNTDOWN",
          f"max_r={a.max_r}",
          f"precision={a.precision}",
          f"max_cycle_len={a.max_cycle_len}",
          f"r_cycles={len(rcycles)}",
          f"schema_cycles={total_schema_cycles}",
          f"positive_integer={classified['positive_integer']}",
          f"nonbase_positive={len(nonbase_positive)}",
          f"precision_boundary={precision_boundary}")
    if positive_integer_fixed:
        print("EPISODE_CYCLE_POSITIVE_FIXED",
              json.dumps(positive_integer_fixed[:20],separators=(",",":")))
    if not nonbase_positive:
        print("NO_NONBASE_POSITIVE_INTEGER_FIXED_POINT_IN_BOUNDED_CYCLES")
    print("VERIFIED_BOUNDED_EPISODE_CYCLE_COUNTDOWN")


if __name__=="__main__":
    main()
