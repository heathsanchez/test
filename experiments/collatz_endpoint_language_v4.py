#!/usr/bin/env python3
"""Deepen and quotient the exact first-resonance endpoint survivor language.

V3 proved that all 27 Q3 first-difference parents induce the same Q2 survivor
language through depth 14.  V4 extends that prospective equality and measures
fixed-lookahead future signatures.  The goal is representation discovery:
does the endpoint residual itself stabilize to a small finite automaton, or
does its future keep refining until the missing source relation is supplied?

No new Collatz certificate family is introduced.  Closure uses only the exact
V2 forward-descent / forward-then-reverse certificates.
"""
from __future__ import annotations
import argparse, json
from functools import lru_cache
from pathlib import Path

import collatz_reverse_trit_bicell_v2 as v2


def extend_parent(parent, max_depth):
    live_by_depth={1:{1}}
    rows=[]
    for a in range(1,max_depth+1):
        current=live_by_depth[a]
        survivors=set()
        closed=0
        kinds={}
        for s in sorted(current):
            cert=v2.composed_certificate(parent,s,a)
            if cert is None:
                survivors.add(s)
            else:
                closed+=1
                kinds[cert["kind"]]=kinds.get(cert["kind"],0)+1
        rows.append(dict(depth=a,input=len(current),closed=closed,
                         residual=len(survivors),closure_kinds=kinds))
        if a<max_depth:
            bit=1<<a
            nxt=set()
            for s in survivors:
                nxt.add(s);nxt.add(s|bit)
            live_by_depth[a+1]=nxt
        live_by_depth[a]=survivors
    return live_by_depth,rows


def truncated_sig(live_by_depth,max_depth,a,s,h,cache):
    key=(a,s,h)
    if key in cache:return cache[key]
    if h==0 or a==max_depth:
        out=()
    else:
        out=[]
        bit=1<<a
        nxt=live_by_depth.get(a+1,set())
        for child in (s,s|bit):
            if child in nxt:
                out.append(truncated_sig(live_by_depth,max_depth,a+1,child,h-1,cache))
            else:
                out.append(None)
        out=tuple(out)
    cache[key]=out
    return out


def quotient_stats(live_by_depth,max_depth,max_lookahead):
    out=[]
    cache={}
    for h in range(1,max_lookahead+1):
        per=[]
        union=set()
        for a in range(1,max_depth-h+1):
            sigs={truncated_sig(live_by_depth,max_depth,a,s,h,cache)
                  for s in live_by_depth[a]}
            union.update(sigs)
            per.append(dict(depth=a,live=len(live_by_depth[a]),classes=len(sigs)))
        out.append(dict(lookahead=h,union_classes=len(union),by_depth=per))
    return out


def full_future_stats(live_by_depth,max_depth):
    @lru_cache(None)
    def sig(a,s):
        if a==max_depth:return ()
        bit=1<<a
        nxt=live_by_depth[a+1]
        return tuple(sig(a+1,c) if c in nxt else None for c in (s,s|bit))
    rows=[]
    for a in range(1,max_depth+1):
        sigs={sig(a,s) for s in live_by_depth[a]}
        rows.append(dict(depth=a,live=len(live_by_depth[a]),classes=len(sigs),
                         remaining=max_depth-a))
    return rows


def run(max_depth,max_lookahead,out):
    parents=v2.parent_residuals()
    all_lang=[]
    parent_rows=[]
    for i,p in enumerate(parents):
        lang,rows=extend_parent(p,max_depth)
        all_lang.append(lang)
        parent_rows.append(rows)
        print("PARENT",i,"FINAL",len(lang[max_depth]))

    canonical=all_lang[0]
    equality=[]
    for a in range(1,max_depth+1):
        eq=all(L[a]==canonical[a] for L in all_lang[1:])
        equality.append(dict(depth=a,equal=eq,count=len(canonical[a])))
        print("LANGUAGE",a,len(canonical[a]),"PARENTS_EQUAL",eq)
    all_equal=all(x["equal"] for x in equality)

    qstats=quotient_stats(canonical,max_depth,max_lookahead)
    for row in qstats:
        print("LOOKAHEAD",row["lookahead"],"UNION_CLASSES",row["union_classes"],
              "TAIL",json.dumps(row["by_depth"][-5:],sort_keys=True))

    full=full_future_stats(canonical,max_depth)
    for row in full:
        if row["depth"]<=5 or row["depth"]>=max_depth-5:
            print("FULL_FUTURE",json.dumps(row,sort_keys=True))

    result=dict(
        schema="COLLATZ_ENDPOINT_LANGUAGE_V4",
        parent="collatz-reverse-trit-bicell-v3-quotient@65b2b3413aa8bb543bb470788b14e02b6d9b0bdf",
        max_depth=max_depth,
        parent_count=len(parents),
        parent_languages_equal=all_equal,
        language_counts=equality,
        fixed_lookahead=qstats,
        full_future_classes=full,
        verdict=("PASS_PARENT_QUOTIENT_EXTENDS"
                 if all_equal else "Q3_PARENT_SEPARATOR_REAPPEARS"),
        interpretation=("endpoint-only future quotient diagnostic; no new closure "
                        "and no global source-normalization claim")
    )
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("VERDICT",result["verdict"])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-depth",type=int,default=20)
    ap.add_argument("--max-lookahead",type=int,default=8)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    assert 14<a.max_depth<=24
    assert 1<=a.max_lookahead<=10
    run(a.max_depth,a.max_lookahead,a.output)
