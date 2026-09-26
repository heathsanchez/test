#!/usr/bin/env python3
"""Audit canonical-R adjacency in the legal first-crossing language.

If consecutive legal words in R-order differ by exactly one 0/1 exchange
(Hamming distance 2 at fixed weight), P29 would be enough to telescope global
R/Y order. This exact finite test decides that representation hypothesis.
"""
import json
def terminals(J):
    st=[(0,0,0,0)]
    for k in range(J):
        nx=[]
        for q,R,Y,w in st:
            for b in (0,1):
                e=b^(Y&1);R2=R+(e<<k);Z=Y+e*3**q
                Y2=Z//2 if b==0 else (3*Z+1)//2
                q2=q+b;w2=w|(b<<k)
                if k+1<J:
                    if 3**q2>=2**(k+1):nx.append((q2,R2,Y2,w2))
                elif 3**q2<2**J and 3**q2>=2**(J-1):nx.append((q2,R2,Y2,w2))
        st=nx
    return st
rows=[];first=None
for J in range(2,28):
    st=sorted(terminals(J),key=lambda x:x[1])
    if not st:continue
    one=0;maxham=0;hist={}
    for a,b in zip(st,st[1:]):
        h=(a[3]^b[3]).bit_count();hist[h]=hist.get(h,0)+1;maxham=max(maxham,h)
        if h==2:one+=1
        elif first is None:
            first={"J":J,"R1":a[1],"R2":b[1],"Y1":a[2],"Y2":b[2],
                   "word1":format(a[3],f"0{J}b")[::-1],"word2":format(b[3],f"0{J}b")[::-1],"hamming":h}
    rows.append({"J":J,"legal":len(st),"adjacent_pairs":max(0,len(st)-1),
                 "single_exchange_pairs":one,"max_hamming":maxham,"hamming_hist":hist})
result={
 "schema":"COLLATZ_R_ORDER_ADJACENCY_V0",
 "j_max":27,"all_adjacent_single_exchange":first is None,
 "first_failure":first,"rows":rows,
 "decision":"P29_SUFFICES_FOR_P19_BY_R_ADJACENCY" if first is None else "R_ADJACENCY_REQUIRES_MULTI_EXCHANGE",
 "next":"if red, measure whether every R-neighbor admits a monotone legal exchange path with no R overshoot; otherwise retire P29 as a direct P19 proof",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
