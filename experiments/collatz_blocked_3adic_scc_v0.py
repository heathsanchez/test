#!/usr/bin/env python3
"""SCC audit of the complete blocked 12/19 3-adic context graph.

States are nonzero-mod3 residues modulo 3^12 that admit no 12-odd/19-cost
contracting reverse block. Edges are symbolic shortcut-map residue transitions
for even/odd branches when the successor remains in the nonzero-mod3 blocked
domain. A recurrent SCC is an exact counterexample to any claim that 3-adic
context alone forces eventual 12/19 admissibility.

Reachability by an actual integer orbit with M>=0 is NOT inferred.
"""
from itertools import combinations
import json,sys
sys.setrecursionlimit(2000000)
O=12;S=19;M=3**O;inv2=pow(2,-1,M)
def comps(total,parts):
    for cuts in combinations(range(1,total),parts-1):
        p=0;w=[]
        for c in cuts+(total,):w.append(c-p);p=c
        yield w
def cocycle(w):
    C=0
    for i,a in enumerate(w):C=(1<<a)*C+3**i
    return C
A={(cocycle(w)*pow(1<<S,-1,M))%M for w in comps(S,O)}
blocked={r for r in range(M) if r%3 and r not in A}
def succs(r):
    for y in ((r*inv2)%M,((3*r+1)*inv2)%M):
        if y in blocked:yield y
# Tarjan iterative-ish recursion is safe at 531k with raised limit.
idx={};low={};stack=[];on=set();counter=0;sccs=[]
def strong(v):
    global counter
    idx[v]=counter;low[v]=counter;counter+=1;stack.append(v);on.add(v)
    for w in succs(v):
        if w not in idx:
            strong(w);low[v]=min(low[v],low[w])
        elif w in on:low[v]=min(low[v],idx[w])
    if low[v]==idx[v]:
        comp=[]
        while True:
            w=stack.pop();on.remove(w);comp.append(w)
            if w==v:break
        sccs.append(comp)
for v in blocked:
    if v not in idx:strong(v)
recurrent=[]
for comp in sccs:
    if len(comp)>1:recurrent.append(comp)
    elif comp[0] in set(succs(comp[0])):recurrent.append(comp)
recurrent.sort(key=len,reverse=True)
covered=sum(map(len,recurrent))
sample=[]
for comp in recurrent[:10]:
    Sset=set(comp);v=min(comp)
    # find an internal edge
    ed=next((w for w in succs(v) if w in Sset),None)
    sample.append({"size":len(comp),"min_state":v,"sample_internal_edge":[v,ed] if ed is not None else None})
result={
 "schema":"COLLATZ_BLOCKED_3ADIC_SCC_V0",
 "modulus":M,"blocked_states":len(blocked),"scc_count":len(sccs),
 "recurrent_sccs":len(recurrent),"states_in_recurrent_sccs":covered,
 "largest_recurrent_scc":len(recurrent[0]) if recurrent else 0,
 "sample_recurrent":sample,
 "decision":"3ADIC_CONTEXT_ALONE_INSUFFICIENT" if recurrent else "NO_BLOCKED_SYMBOLIC_CYCLE",
 "scope_warning":"symbolic parity edges do not establish reachability from legal M>=0 cylinders",
 "next":"intersect recurrent blocked SCCs with the exact 2-adic canonical-realization/M>=0 register before any further context theorem",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
