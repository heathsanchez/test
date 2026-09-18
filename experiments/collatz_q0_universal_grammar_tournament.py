#!/usr/bin/env python3
"""Universal lower-merge grammar tournament on q=0 component anchors.

This combines two independently proved source-independent certificate families:

1. Cross-valuation predecessor coalescence:
   n=2^K m-1, p=(n-1)/2<n.  For certified m mod 2^S classes,
   trajectories of n and p merge exactly.

2. q7 reverse-predecessor certificates:
   for 1013/2187 source residues there is an explicit p<n with T^a(p)=n.

Unlike the failed frozen D/P trajectory bank, these are theorem-derived residue
grammars, not learned per-anchor witnesses.

The audit measures their exact bounded consequence on component anchors and
prints the residual mixed (K, m mod 2^S, n mod 3^7) language.  It is discovery
evidence only, not a Collatz proof.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict

import collatz_q0_anchor_q7_tournament as comp
import collatz_q0_coalescence_component_audit as base
import collatz_predecessor_coalescence as coal
import collatz_reverse_predecessor_tree as pred


def v2(x:int)->int:
    assert x>0
    return (x & -x).bit_length()-1


def q7_table():
    certs=pred.enumerate_first_contractions(7)
    killed,selected=pred.quotient(certs,7)
    assert (sum(killed),len(killed),len(selected))==(1013,2187,13)
    return killed,selected


def coalescence_tables(anchors,S:int):
    ks=sorted({v2(n+1) for n in anchors})
    tables={}
    for K in ks:
        rows=coal.census(K,S)
        killed={row["r"] for row in rows}
        # Every returned row was independently replayed by merge_certificate.
        tables[K]=killed
        print("COAL_TABLE",K,len(killed),1<<(S-1))
    return tables


def scalar_fallback(n,H):
    d=base.first_direct(n,H)
    p=base.first_immediate_lower_predecessor(n,H)
    cand=[]
    if d is not None:cand.append((d[0],"D",d))
    if p is not None:cand.append((p[0],"P",p))
    return min(cand) if cand else None


def audit(N,H,S):
    survivors,components=comp.build_components(N,H)
    anchors=sorted(components)
    q7,_=q7_table()
    coal_tab=coalescence_tables(anchors,S)
    mask=(1<<S)-1

    counts=Counter()
    residual=[]
    byK=Counter()
    examples=defaultdict(list)

    for n in anchors:
        K=v2(n+1)
        m=(n+1)>>K
        cq=(m & mask) in coal_tab[K]
        q7hit=bool(q7[n%2187])
        if cq and q7hit:key="BOTH"
        elif cq:key="COAL"
        elif q7hit:key="Q7"
        else:key="RESIDUAL"
        counts[key]+=1
        if len(examples[key])<20:
            examples[key].append((n,K,m&mask,n%2187))
        if key=="RESIDUAL":
            residual.append(n)
            byK[K]+=1

    fallback=Counter();uncert=[];hard=[]
    for n in residual:
        c=scalar_fallback(n,H)
        if c is None:
            uncert.append(n)
        else:
            fallback[c[1]]+=1
            hard.append((c[0],n,c[1],c[2]))
    hard.sort(reverse=True)

    # Mixed residual language at this finite precision.
    states=Counter()
    for n in residual:
        K=v2(n+1);m=(n+1)>>K
        states[(K,m&mask,n%2187)]+=1

    print("SOURCE_LIMIT",N)
    print("HEREDITARY_Q0_RIGID_SOURCES",len(survivors))
    print("COMPONENT_ANCHORS",len(anchors))
    print("GRAMMAR_COUNTS",dict(counts))
    print("UNIVERSAL_GRAMMAR_COVER",len(anchors)-len(residual),"/",len(anchors))
    print("RESIDUAL_ANCHORS",len(residual))
    print("RESIDUAL_BY_K",dict(sorted(byK.items())))
    print("RESIDUAL_MIXED_STATES",len(states))
    print("SCALAR_FALLBACK_ON_RESIDUAL",dict(fallback))
    print("UNCERTIFIED_RESIDUAL",len(uncert),uncert[:30])
    print("HARDEST_RESIDUAL_FALLBACKS",hard[:30])
    for k in ("COAL","Q7","BOTH","RESIDUAL"):
        print("EXAMPLES",k,examples[k])
    if uncert:
        print("SEPARATOR_UNCERTIFIED_AFTER_UNIVERSAL_GRAMMAR",uncert[0])
    else:
        print("OBSERVED_ALL_BOUNDED_RESIDUAL_ANCHORS_HAVE_SCALAR_CERT")
    print("STATUS BOUNDED_DISCOVERY_ONLY")
    print("MISSING_THEOREM recursive_cover_of_mixed_residual_language")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--N",type=int,default=262143)
    ap.add_argument("--H",type=int,default=512)
    ap.add_argument("--S",type=int,default=12)
    a=ap.parse_args()
    audit(a.N,a.H,a.S)
