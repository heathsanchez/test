#!/usr/bin/env python3
"""Stateful cycle: split first-crossing cylinders by terminal lift carry e.

For a legal first crossing at J, the final parity bit must be 0. The canonical
lift from depth J-1 to J is R'=R+e*2^(J-1), where e is the endpoint parity
needed to realize that final even bit. Test whether any e=1 terminal can beat
the best e=0 margin, and whether any e=1 terminal has M>=0.

Exact finite discovery through J=29; not a universal theorem.
"""
import json

def terminals(J):
    st=[(0,0,0,0)]
    for k in range(J):
        nx=[]
        for q,R,Y,w in st:
            for b in (0,1):
                e=b^(Y&1); R2=R+(e<<k); Z=Y+e*3**q
                Y2=Z//2 if b==0 else (3*Z+1)//2
                q2=q+b; w2=w|(b<<k)
                if k+1<J:
                    if 3**q2>=2**(k+1): nx.append((q2,R2,Y2,w2))
                elif 3**q2<2**J and 3**q2>=2**(J-1):
                    assert b==0
                    nx.append((q2,R2,Y2,w2))
        st=nx
    return st

rows=[]; counterexamples=[]; dominance_fail=[]
for J in range(2,30):
    st=terminals(J)
    if not st: continue
    by={0:[],1:[]}
    for q,R,Y,w in st:
        e=(R>>(J-1))&1
        M=(1<<J)*(Y-R)
        by[e].append((M,R,Y,w))
        if e==1 and M>=0: counterexamples.append((J,q,R,Y,M,w))
    max0=max((x[0] for x in by[0]),default=None)
    max1=max((x[0] for x in by[1]),default=None)
    if max1 is not None and max0 is not None and max1>=max0:
        dominance_fail.append(J)
    rows.append({"J":J,"legal":len(st),"e0":len(by[0]),"e1":len(by[1]),
                 "maxM_e0":max0,"maxM_e1":max1,
                 "e1_below_e0":None if max1 is None else max1<max0})
result={
 "schema":"COLLATZ_TERMINAL_LIFT_CARRY_V0",
 "j_max":29,"classes":len(rows),
 "e1_M_nonnegative":len(counterexamples),
 "e1_beats_or_ties_e0_classes":dominance_fail,
 "all_e1_negative":not counterexamples,
 "all_e1_strictly_below_e0_when_present":not dominance_fail,
 "rows":rows,
 "candidate":"first-crossing M>=0 cylinders must use zero terminal lift carry",
 "next":"derive the carry-1 margin bound algebraically; if warranted, recurse only through zero-carry terminal parents",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
