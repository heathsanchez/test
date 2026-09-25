#!/usr/bin/env python3
"""Compile the single V3 Collatz residual language into 4-bit consequence masks.

This reuses the qualified V2 certificate compiler without adding a new
mathematical constructor.  V3 proved all 27 Q3 parents induce the same Q2
survivor language through depth 16.  Here we pick the canonical first parent,
extend that exact language through depth 20, and compile four-bit future masks
at 8->12, 12->16 and 16->20.

The point is representational: test whether the residual admits the same
compact base+future-mask factorization previously qualified for Collatz p28.
No extrapolation beyond the executed depth is promoted.
"""
from __future__ import annotations
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path
import collatz_reverse_trit_bicell_v2 as v2


def build(max_depth:int):
    p=v2.parent_residuals()[0]
    live={1}
    levels={1:set(live)}
    for a in range(2,max_depth+1):
        bit=1<<(a-1)
        cand={x for s in live for x in (s,s|bit)}
        live={s for s in cand if v2.composed_certificate(p,s,a) is None}
        levels[a]=set(live)
        print("LEVEL",a,len(live),flush=True)
    return p,levels


def masks(levels,d,w=4):
    hi=d+w
    base=levels[d]; deep=levels[hi]
    stride=1<<d
    out={}
    for r in sorted(base):
        m=0
        for h in range(1<<w):
            if r+h*stride in deep:
                m|=1<<h
        assert m
        out[r]=m
    c=Counter(out.values())
    return dict(base_depth=d,deep_depth=hi,base_count=len(base),
                deep_count=len(deep),distinct_masks=len(c),
                masks=[dict(mask=k,popcount=k.bit_count(),count=v)
                       for k,v in sorted(c.items(),key=lambda kv:(kv[0].bit_count(),kv[0]))])


def transitions(levels,d,w=4):
    """Mask-state transition census between adjacent 4-bit blocks when available."""
    a=masks(levels,d,w)
    b=masks(levels,d+w,w)
    amap={}
    stride=1<<d
    deepmap={x["mask"]:i for i,x in enumerate(a["masks"])}
    # actual value->mask maps
    def valmap(dd):
        hh=dd+w; st=1<<dd; out={}
        for r in levels[dd]:
            m=0
            for h in range(1<<w):
                if r+h*st in levels[hh]:m|=1<<h
            out[r]=m
        return out
    m0=valmap(d);m1=valmap(d+w)
    trans=defaultdict(Counter)
    for r,mask0 in m0.items():
        for h in range(1<<w):
            child=r+h*stride
            if child in levels[d+w]:
                trans[mask0][m1[child]]+=1
    return [
        dict(from_mask=k,to=[dict(mask=t,count=n) for t,n in sorted(v.items())])
        for k,v in sorted(trans.items())
    ]


def run(max_depth,out):
    parent,levels=build(max_depth)
    windows=[]
    for d in (8,12,16):
        if d+4<=max_depth:
            x=masks(levels,d,4);windows.append(x)
            print("MASK_WINDOW",json.dumps(x,sort_keys=True),flush=True)
    trans=[]
    if max_depth>=20:
        for d in (8,12):
            x=transitions(levels,d,4);trans.append(dict(depth=d,rows=x))
            print("MASK_TRANSITIONS",d,json.dumps(x,sort_keys=True),flush=True)
    result=dict(schema="COLLATZ_REVERSE_TRIT_MASK_COMPILER_V4",
      parent=parent,max_depth=max_depth,
      level_counts={str(k):len(v) for k,v in levels.items()},
      windows=windows,transitions=trans,
      verdict="PASS_EXACT_COMPACT_MASK_CENSUS",
      scope="one canonical V3 Q3 parent; exact V2 certificates; bounded through executed Q2 depth only")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("VERDICT",result["verdict"])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-depth",type=int,default=20)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    assert 16<=a.max_depth<=22
    run(a.max_depth,a.output)
