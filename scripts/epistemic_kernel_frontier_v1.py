#!/usr/bin/env python3
"""
Epistemic Kernel Frontier V1 — exhaustive over every nonempty subset of the
15 equivalence relations on four states.
"""
from itertools import combinations

FROZEN="2e9654e5c6b2d38de3ef7abcdcf0dbfc3a95a3ba"
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

def clsmap(p):
    return {x:i for i,b in enumerate(p) for x in b}

CMAPS=tuple(clsmap(p) for p in PARTS)

def merged(p,a,b):
    c=clsmap(p); return c[a]==c[b]

def refines(p,q):
    # p is finer / at least as committed as q
    cp=clsmap(p); cq=clsmap(q)
    return all(cp[a]!=cp[b] or cq[a]==cq[b] for a in X for b in X)

def strictly_coarser(q,p):
    return q!=p and refines(p,q)

def classify(ks):
    eq=set(); dist=set(); unk=set()
    maps=[clsmap(k) for k in ks]
    for a,b in PAIRS:
        ms=[m[a]==m[b] for m in maps]
        if all(ms): eq.add((a,b))
        elif not any(ms): dist.add((a,b))
        else: unk.add((a,b))
    return frozenset(eq),frozenset(dist),frozenset(unk)

def adequate(p,dist):
    c=clsmap(p)
    return all(c[a]!=c[b] for a,b in dist)

def frontier(dist):
    good=[p for p in PARTS if adequate(p,dist)]
    return tuple(p for p in good if not any(strictly_coarser(q,p) and adequate(q,dist) for q in PARTS))

def robust_intersection(ks):
    maps=[clsmap(k) for k in ks]
    sigs={x:tuple(m[x] for m in maps) for x in X}
    groups={}
    for x,s in sigs.items(): groups.setdefault(s,[]).append(x)
    return canon(groups.values())

def run():
    checks=[]; failures=[]
    def chk(name,cond,detail=""):
        checks.append((name,bool(cond),detail))
        if not cond: failures.append((name,detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("="*104)
    print("EPISTEMIC KERNEL FRONTIER V1 — EXHAUSTIVE BELL(4) WORLD-SET AUDIT")
    print("frozen =",FROZEN)
    print("="*104)

    total=0
    singleton_ok=True
    class_overlap=False
    robust_always_adequate=True
    robust_overcommit=0
    robust_in_frontier=0
    nonunique_frontier=0
    max_frontier=0
    frontier_size_dist={}
    min_block_dist={}
    eq_split_frontier_cases=0
    first_over=None
    first_nonunique=None

    # 15 possible exact kernels -> 2^15-1 nonempty model sets.
    for bits in range(1,1<<len(PARTS)):
        ks=tuple(PARTS[i] for i in range(len(PARTS)) if bits&(1<<i))
        total+=1
        eq,dist,unk=classify(ks)
        if (eq&dist) or (eq&unk) or (dist&unk) or len(eq|dist|unk)!=len(PAIRS):
            class_overlap=True

        fr=frontier(dist)
        fs=len(fr)
        frontier_size_dist[fs]=frontier_size_dist.get(fs,0)+1
        max_frontier=max(max_frontier,fs)
        if fs>1:
            nonunique_frontier+=1
            if first_nonunique is None:
                first_nonunique=(ks,eq,dist,unk,fr)

        mb=min(len(p) for p in fr)
        min_block_dist[mb]=min_block_dist.get(mb,0)+1

        if len(ks)==1 and fr!=(ks[0],):
            singleton_ok=False

        ki=robust_intersection(ks)
        if not adequate(ki,dist):
            robust_always_adequate=False

        if ki in fr:
            robust_in_frontier+=1
        else:
            robust_overcommit+=1
            if first_over is None:
                first_over=(ks,eq,dist,unk,ki,fr)

        # Quantify whether globally minimal partitions ever split a pair that is
        # EQ in all compatible exact worlds due to partition-level constraints.
        for p in fr:
            c=clsmap(p)
            if any(c[a]!=c[b] for a,b in eq):
                eq_split_frontier_cases+=1
                break

    chk("A1 enumerated all 32,767 nonempty compatible-kernel sets",total==32767,total)
    chk("A2 EQ/DIST/UNKNOWN are disjoint and exhaustive for every nonempty set",not class_overlap)
    chk("A3 every singleton world set recovers exactly its own kernel",singleton_ok)
    chk("A4 robust intersection always preserves all universally warranted DIST pairs",robust_always_adequate)
    chk("A5 robust intersection is often NOT least-committed",
        robust_overcommit>0,
        f"overcommit_sets={robust_overcommit} in_frontier={robust_in_frontier} first={first_over}")
    chk("A6 nonunique least-commitment frontiers genuinely occur",
        nonunique_frontier>0,
        f"sets={nonunique_frontier} max_frontier={max_frontier} first={first_nonunique}")
    chk("A7 quantified frontier-size distribution",sum(frontier_size_dist.values())==32767,
        frontier_size_dist)
    chk("A8 quantified minimum-block distribution",sum(min_block_dist.values())==32767,
        min_block_dist)
    # This is exploratory: if zero, warranted EQ pairs always merge in every
    # minimal frontier in this finite universe; if positive, the candidate's
    # 'unless globally forced' rider is doing real work.
    print("eq_split_frontier_sets",eq_split_frontier_cases)

    # Explicit crossed-two-world witness from prior antichain work.
    k1=canon(((0,1),(2,3)))
    k2=canon(((0,2),(1,3)))
    eq,dist,unk=classify((k1,k2))
    fr=frontier(dist)
    ki=robust_intersection((k1,k2))
    chk("B1 crossed two-world case has warranted DIST but unresolved pairs",
        len(dist)>0 and len(unk)>0,
        f"EQ={sorted(eq)} DIST={sorted(dist)} UNKNOWN={sorted(unk)}")
    chk("B2 crossed case robust intersection is the discrete four-state quotient",
        len(ki)==4,ki)
    chk("B3 crossed case least-commitment frontier uses fewer states than robust quotient",
        min(len(p) for p in fr)<len(ki),
        f"robust={ki} frontier={fr}")
    chk("B4 crossed case frontier is nonunique",len(fr)>1,fr)

    passed=sum(ok for _,ok,_ in checks); totalc=len(checks)
    print("\n"+"="*104)
    print(f"VERDICT: {'PASS' if not failures else 'FAIL'} {passed}/{totalc}")
    if failures:
        print("FALSIFIED_EPISTEMIC_KERNEL_FRONTIER_V1")
        raise SystemExit(1)
    print("VERIFIED_RESOLVED_KERNEL_AS_SINGLETON_SPECIAL_CASE")
    print("VERIFIED_ROBUST_INTERSECTION_CAN_OVERCOMMIT")
    print("VERIFIED_EPISTEMIC_UNCERTAINTY_REQUIRES_LEAST_COMMITMENT_FRONTIER")
    print("SURVIVED_EPISTEMIC_KERNEL_FRONTIER_V1")

if __name__=="__main__":
    run()
