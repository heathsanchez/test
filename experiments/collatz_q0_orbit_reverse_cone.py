#!/usr/bin/env python3
"""Forward-orbit / reverse-cone lower-merge audit on q=0 component anchors.

For an anchor n, follow y=T^t(n).  At every y, test exact first-contracting
reverse Collatz certificates w:
    p = R_w(y),  p<y,  T^|w|(p)=y.
If p<n, then n and the already-lower p share the tail y, giving a lower merge.

This strictly generalizes:
  * direct descent y<n;
  * the immediate inverse-odd predecessor (word O);
  * source-only qQ predecessor sieves.

The reverse certificate banks are generated and independently verified by
collatz_reverse_predecessor_tree.py.  Results remain bounded discovery data.
"""
from __future__ import annotations
import argparse
from collections import Counter

import collatz_q0_anchor_q7_tournament as comp
import collatz_q0_coalescence_component_audit as base
import collatz_reverse_predecessor_tree as pred


def bank(Q:int):
    cs=pred.enumerate_first_contractions(Q)
    # Index by denominator / residue; all are exact first-contracting certs.
    by={}
    for c in cs:
        by.setdefault(c.d,{}).setdefault(c.residue,[]).append(c)
    return cs,by


def best_reverse(y:int,n:int,by):
    best=None
    for d,rows in by.items():
        arr=rows.get(y%d)
        if not arr: continue
        for c in arr:
            num=c.a*y-c.c
            assert num%d==0
            p=num//d
            if not (0<p<n): continue
            # Independent replay of the winning candidate is done by caller.
            cand=(p,c.steps,c.word,c)
            if best is None or (p,c.steps,c.word)<(best[0],best[1],best[2]):
                best=cand
    return best


def verify(n:int,y:int,t:int,hit):
    p,steps,word,c=hit
    q=pred.reverse_apply(y,word)
    assert q==p and 0<p<n
    x=p
    for _ in word:
        x=base.T(x)
    assert x==y
    z=n
    for _ in range(t):
        z=base.T(z)
    assert z==y


def first_cert(n:int,H:int,by):
    y=n
    # Source itself is allowed.
    hit=best_reverse(y,n,by)
    if hit is not None:
        verify(n,y,0,hit)
        return ("R",0,y,hit)
    for t in range(1,H+1):
        y=base.T(y)
        if y<n:
            return ("D",t,y,None)
        hit=best_reverse(y,n,by)
        if hit is not None:
            verify(n,y,t,hit)
            return ("R",t,y,hit)
    return None


def audit(N:int,H:int,Q:int):
    survivors,components=comp.build_components(N,H)
    anchors=sorted(components)
    certs,by=bank(Q)
    counts=Counter();uncert=[];hard=[];words=Counter();examples=[]

    for n in anchors:
        c=first_cert(n,H,by)
        if c is None:
            uncert.append(n);continue
        kind,t,y,hit=c
        counts[kind]+=1
        if kind=="R":
            p,steps,word,_=hit
            words[word]+=1
            hard.append((t,n,kind,y,p,word))
        else:
            hard.append((t,n,kind,y,None,None))
        if len(examples)<30:
            examples.append((n,c if kind=="D" else (kind,t,y,hit[:3])))

    hard.sort(reverse=True)
    print("SOURCE_LIMIT",N)
    print("COMPONENT_ANCHORS",len(anchors))
    print("REVERSE_Q",Q)
    print("FIRST_CONTRACTION_CERTIFICATES",len(certs))
    print("ORBIT_CONE_CERT_COUNTS",dict(counts))
    print("UNCERTIFIED_ANCHORS",len(uncert),uncert[:30])
    print("MAX_FORWARD_STEPS_TO_CERT",max((x[0] for x in hard),default=0))
    print("HARDEST",hard[:30])
    print("TOP_REVERSE_WORDS",words.most_common(30))
    for x in examples: print("EXAMPLE",x)
    if uncert:
        print("SEPARATOR_ORBIT_REVERSE_CONE",uncert[0])
    else:
        print("OBSERVED_ALL_BOUNDED_ANCHORS_CLOSED_BY_ORBIT_REVERSE_CONE")
    print("STATUS BOUNDED_DISCOVERY_ONLY")
    print("MISSING_THEOREM universal_orbit_reverse_cone_termination")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--N",type=int,default=262143)
    ap.add_argument("--H",type=int,default=512)
    ap.add_argument("--Q",type=int,default=7)
    a=ap.parse_args()
    audit(a.N,a.H,a.Q)
