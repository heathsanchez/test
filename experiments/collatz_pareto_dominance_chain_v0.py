#!/usr/bin/env python3
"""Test whether exact joint Pareto frontiers are dominance chains.

P15: only nondominated (R,B) points can maximize M=B-D*R.
P20/P21: dominance-comparable legal words have coherent contracting endpoint
order (P21 composition is conditional on P20's Rhin-backed edge theorem).

If Pareto points form a dominance chain, the joint residual has a much smaller
ordered representation. This script is exact finite discovery evidence.
"""
import json

def feasible(J,q):
    return 3**q < 2**J and 3**q >= 2**(J-1)

def dominance(a,b,J):
    # +1 if a dominates b in prefix-one counts, -1 reverse, 0 incomparable/equal
    ca=cb=0;ge=le=True
    for i in range(J):
        ca+=(a>>i)&1;cb+=(b>>i)&1
        if ca<cb:ge=False
        if ca>cb:le=False
    if ge and not le:return 1
    if le and not ge:return -1
    return 0

def terminal_states(J):
    # state: (q,R,Y,bits); bits low-to-high chronological
    states=[(0,0,0,0)]
    for k in range(J):
        nxt=[]
        for q,R,Y,bits in states:
            for b in (0,1):
                e=b^(Y&1)
                R2=R+(e<<k);Z=Y+e*3**q
                Y2=Z//2 if b==0 else (3*Z+1)//2
                q2=q+b;bits2=bits|(b<<k)
                if k+1<J:
                    if 3**q2 >= 2**(k+1):nxt.append((q2,R2,Y2,bits2))
                else:
                    if 3**q2 < 2**J and 3**q2 >= 2**(J-1):
                        nxt.append((q2,R2,Y2,bits2))
        states=nxt
    return states

rows=[];fail=[]
for J in range(2,28):
    sts=terminal_states(J)
    if not sts:continue
    qs={x[0] for x in sts};assert len(qs)==1
    q=next(iter(qs));D=2**J-3**q
    pts=[]
    for _,R,Y,w in sts:
        B=2**J*Y-3**q*R
        pts.append((R,B,Y,w))
    pts.sort()
    frontier=[];bestB=-1
    for p in pts:
        if p[1]>bestB:
            frontier.append(p);bestB=p[1]
    chain=True;bad=None
    for a,b in zip(frontier,frontier[1:]):
        if dominance(a[3],b[3],J)==0:
            chain=False;bad=(a,b);break
    # also global pairwise chain if adjacent comparable in same orientation is enough transitive,
    # but record orientations.
    orients=[dominance(frontier[i][3],frontier[i+1][3],J) for i in range(len(frontier)-1)]
    same_orientation=len(set(orients))<=1 if orients else True
    if not chain or not same_orientation:fail.append(J)
    rows.append({"J":J,"q":q,"legal":len(pts),"pareto":len(frontier),
                 "adjacent_dominance_chain":chain,"same_orientation":same_orientation,
                 "orientations":sorted(set(orients))})
result={
 "schema":"COLLATZ_PARETO_DOMINANCE_CHAIN_V0",
 "classes":len(rows),"j_max":27,
 "all_frontiers_dominance_chains":not fail,
 "failures":fail,"rows":rows,
 "interpretation":"finite discovery test for P15+P21 compression; not a universal theorem",
 "next":"if chain holds, derive Pareto record recursion along the legal dominance lattice; if false, preserve first incomparable frontier pair as obstruction",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
