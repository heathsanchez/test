#!/usr/bin/env python3
"""Transition audit of the universal cost-19 identity frontier.

Classes modulo 3^12:
 K = admits a lower-cost 12-odd reverse block (strictly cheaper for y>86)
 I = admits reverse blocks but minimal cost is exactly 19 (identity frontier)
 B = admits no 12-odd reverse block with cost <=19.

Apply both symbolic shortcut residue transitions and classify exits. Recurrent
I-only SCCs would refute an identity-frontier-only progress theorem. Transitions
to B show where the M/2-adic register is needed.
"""
from itertools import combinations
import json,sys
sys.setrecursionlimit(100000)
O=12;MOD=3**O;inv2=pow(2,-1,MOD)
def comps(total,parts):
    for cuts in combinations(range(1,total),parts-1):
        p=0;w=[]
        for c in cuts+(total,):w.append(c-p);p=c
        yield w
def C(w):
    x=0
    for i,a in enumerate(w):x=(1<<a)*x+3**i
    return x
minS={}
for S in range(12,20):
    inv=pow(1<<S,-1,MOD)
    for w in comps(S,O):
        r=C(w)*inv%MOD
        minS[r]=min(S,minS.get(r,99))
K={r for r,s in minS.items() if s<19}
I={r for r,s in minS.items() if s==19}
domain={r for r in range(MOD) if r%3}
B=domain-K-I
def step(r,b):return r*inv2%MOD if b==0 else (3*r+1)*inv2%MOD
def cls(y):
    if y in K:return "K"
    if y in I:return "I"
    if y in B:return "B"
    return "OUT"
counts={f"{b}:{c}":0 for b in (0,1) for c in ("K","I","B","OUT")}
edgesI={}
for r in I:
    es=[]
    for b in (0,1):
        y=step(r,b);c=cls(y);counts[f"{b}:{c}"]+=1
        if c=="I":es.append(y)
    edgesI[r]=es
# SCC on I-only graph.
idx={};low={};st=[];on=set();nxt=0;scc=[]
def strong(v):
    global nxt
    idx[v]=nxt;low[v]=nxt;nxt+=1;st.append(v);on.add(v)
    for w in edgesI[v]:
        if w not in idx:strong(w);low[v]=min(low[v],low[w])
        elif w in on:low[v]=min(low[v],idx[w])
    if low[v]==idx[v]:
        cc=[]
        while 1:
            w=st.pop();on.remove(w);cc.append(w)
            if w==v:break
        scc.append(cc)
for v in I:
    if v not in idx:strong(v)
rec=[]
for cc in scc:
    if len(cc)>1:rec.append(cc)
    elif cc[0] in edgesI[cc[0]]:rec.append(cc)
rec.sort(key=len,reverse=True)
result={
 "schema":"COLLATZ_IDENTITY_FRONTIER_TRANSITIONS_V0",
 "class_sizes":{"cheaper_K":len(K),"identity_I":len(I),"blocked_B":len(B)},
 "identity_edge_outcomes":counts,
 "identity_only_recurrent_sccs":len(rec),
 "identity_states_in_recurrent_sccs":sum(map(len,rec)),
 "largest_identity_scc":len(rec[0]) if rec else 0,
 "sample_recurrent":[sorted(x)[:10] for x in rec[:5]],
 "decision":"IDENTITY_ONLY_RECURRENCE_EXISTS" if rec else "IDENTITY_FRONTIER_FORCED_TO_EXIT",
 "next":"analyze exits to B with joint M register; exits to K are certified cheaper contractions for endpoints >86",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
