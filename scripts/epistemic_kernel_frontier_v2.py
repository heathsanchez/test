#!/usr/bin/env python3
"""
Epistemic Kernel Frontier V2 — exhaustive over all nonempty subsets of Bell(4).
Admissibility constrains BOTH warranted EQ merges and warranted DIST splits.
"""
from itertools import combinations

FROZEN="7b67adf37856764008a19ce2ba3b295e43d33a5f"
X=tuple(range(4))
PAIRS=tuple(combinations(X,2))

def canon(blocks):
    return tuple(sorted((tuple(sorted(b)) for b in blocks), key=lambda b:(b[0],len(b),b)))

def partitions(items):
    out=[]; blocks=[]
    def rec(i):
        if i==len(items):
            out.append(canon(blocks)); return
        x=items[i]
        for j in range(len(blocks)):
            blocks[j].append(x); rec(i+1); blocks[j].pop()
        blocks.append([x]); rec(i+1); blocks.pop()
    rec(0)
    return tuple(sorted(set(out), key=lambda p:(len(p),p)))

PARTS=partitions(X)
assert len(PARTS)==15

def cmap(p):
    return {x:i for i,b in enumerate(p) for x in b}

CM={p:cmap(p) for p in PARTS}

def refines(p,q):
    cp=CM[p]; cq=CM[q]
    return all(cp[a]!=cp[b] or cq[a]==cq[b] for a in X for b in X)

def strictly_coarser(q,p):
    return q!=p and refines(p,q)

def classify(ks):
    eq=set(); dist=set(); unk=set()
    maps=[CM[k] for k in ks]
    for a,b in PAIRS:
        vals=[m[a]==m[b] for m in maps]
        if all(vals): eq.add((a,b))
        elif not any(vals): dist.add((a,b))
        else: unk.add((a,b))
    return frozenset(eq),frozenset(dist),frozenset(unk)

def admissible_v2(p,eq,dist):
    c=CM[p]
    return all(c[a]==c[b] for a,b in eq) and all(c[a]!=c[b] for a,b in dist)

def admissible_v1(p,dist):
    c=CM[p]
    return all(c[a]!=c[b] for a,b in dist)

def frontier_v2(eq,dist):
    good=[p for p in PARTS if admissible_v2(p,eq,dist)]
    return tuple(p for p in good if not any(strictly_coarser(q,p) and admissible_v2(q,eq,dist) for q in PARTS))

def frontier_v1(dist):
    good=[p for p in PARTS if admissible_v1(p,dist)]
    return tuple(p for p in good if not any(strictly_coarser(q,p) and admissible_v1(q,dist) for q in PARTS))

def robust_intersection(ks):
    maps=[CM[k] for k in ks]
    groups={}
    for x in X:
        sig=tuple(m[x] for m in maps)
        groups.setdefault(sig,[]).append(x)
    return canon(groups.values())

def run():
    checks=[]; failures=[]
    def chk(name,cond,detail=""):
        checks.append((name,bool(cond),detail))
        if not cond: failures.append((name,detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("="*104)
    print("EPISTEMIC KERNEL FRONTIER V2 — EQ+DIST CONSTRAINED EXHAUSTIVE AUDIT")
    print("frozen =",FROZEN)
    print("="*104)

    total=0
    all_nonempty=True
    all_respect=True
    singleton_ok=True
    robust_ok=True
    robust_over=0
    nonunique=0
    max_front=0
    size_dist={}
    changed_from_v1=0
    first_changed=None
    first_nonunique=None

    for bits in range(1,1<<len(PARTS)):
        ks=tuple(PARTS[i] for i in range(len(PARTS)) if bits&(1<<i))
        total+=1
        eq,dist,unk=classify(ks)
        fr=frontier_v2(eq,dist)
        if not fr:
            all_nonempty=False
        size_dist[len(fr)]=size_dist.get(len(fr),0)+1
        max_front=max(max_front,len(fr))
        if len(fr)>1:
            nonunique+=1
            if first_nonunique is None:
                first_nonunique=(ks,eq,dist,unk,fr)

        for p in fr:
            c=CM[p]
            if any(c[a]!=c[b] for a,b in eq) or any(c[a]==c[b] for a,b in dist):
                all_respect=False

        if len(ks)==1 and fr!=(ks[0],):
            singleton_ok=False

        ki=robust_intersection(ks)
        if not admissible_v2(ki,eq,dist):
            robust_ok=False
        if ki not in fr:
            robust_over+=1

        old=frontier_v1(dist)
        if fr!=old:
            changed_from_v1+=1
            if first_changed is None:
                first_changed=(ks,eq,dist,unk,old,fr)

    chk("A1 enumerated all 32,767 nonempty compatible-kernel sets",total==32767,total)
    chk("A2 every nonempty world-set has at least one EQ+DIST-admissible partition",all_nonempty)
    chk("A3 every V2 frontier member merges all EQ and separates all DIST",all_respect)
    chk("A4 every singleton world-set recovers exactly its exact kernel",singleton_ok)
    chk("A5 robust intersection is always EQ+DIST-admissible",robust_ok)
    chk("A6 robust intersection still often overcommits",robust_over>0,robust_over)
    chk("A7 nonunique least-commitment frontiers still occur",nonunique>0,f"sets={nonunique} max={max_front} first={first_nonunique}")
    chk("A8 V2 changes the DIST-only frontier on a nonzero set of evidence states",
        changed_from_v1>0,
        f"changed={changed_from_v1} first={first_changed}")
    chk("A9 frontier-size distribution accounts for all world-sets",
        sum(size_dist.values())==32767,size_dist)

    # Crossed two-world witness remains unchanged because EQ is empty.
    k1=canon(((0,1),(2,3)))
    k2=canon(((0,2),(1,3)))
    eq,dist,unk=classify((k1,k2))
    fr=frontier_v2(eq,dist)
    ki=robust_intersection((k1,k2))
    chk("B1 crossed witness has empty EQ, nonempty DIST and UNKNOWN",
        len(eq)==0 and len(dist)>0 and len(unk)>0,
        f"EQ={eq} DIST={dist} UNKNOWN={unk}")
    chk("B2 crossed witness retains the two incomparable 2-block minima",
        set(fr)=={k1,k2},fr)
    chk("B3 robust intersection remains the overcommitted 4-block partition",
        len(ki)==4 and ki not in fr,
        f"robust={ki} frontier={fr}")

    passed=sum(ok for _,ok,_ in checks); totalc=len(checks)
    print("\n"+"="*104)
    print(f"VERDICT: {'PASS' if not failures else 'FAIL'} {passed}/{totalc}")
    if failures:
        print("FALSIFIED_EPISTEMIC_KERNEL_FRONTIER_V2")
        raise SystemExit(1)
    print("VERIFIED_EPISTEMIC_FRONTIER_CONSTRAINS_BOTH_EQ_AND_DIST")
    print("VERIFIED_UNKNOWN_ALONE_REMAINS_FREE")
    print("VERIFIED_ROBUST_INTERSECTION_STILL_OVERCOMMITS")
    print("SURVIVED_EPISTEMIC_KERNEL_FRONTIER_V2")

if __name__=="__main__":
    run()
