#!/usr/bin/env python3
"""Zero-exposure switch subgrammar tournament.

A natural integer has only finitely many 1-bits. Therefore an infinite
source-pulled centre-switch path compatible with one ordinary natural owner
would eventually have to consist entirely of switches whose newly exposed
precision block is all zero.

This audit isolates exactly those switches on the frozen V53/V60 corpus and
asks:
  * what is the longest consecutive zero-exposure run?
  * does the zero-exposure local-law graph contain a recurrent SCC?
  * does the zero-exposure exact-centre graph contain a recurrent SCC?
  * does a small exact arithmetic feature rank all zero-exposure edges?

Bounded theorem discovery only.
"""
from __future__ import annotations
from collections import Counter, defaultdict, deque
from fractions import Fraction
from itertools import combinations, product
import hashlib, json, sys

import collatz_crystal_nonpositive_budget_kernel_v53 as v53

def v2z(x:int):
    x=abs(x)
    if x==0:return None
    return (x & -x).bit_length()-1

def rat_v2(x:Fraction):
    if x==0:return None
    return v2z(x.numerator)-v2z(x.denominator)

def centre(s):
    return Fraction(s["B"],s["P"]-s["A"])

def law_id(anchor,s):
    return (anchor,s["A"],s["B"],s["P"],s["D"])

def center_id(anchor,s):
    c=centre(s)
    return (anchor,c.numerator,c.denominator)

def law_features(node):
    anchor,A,B,P,D=node
    C=P-A
    # A is a power of 3 on these exact return laws.
    q=0;tmp=A
    while tmp>1 and tmp%3==0:
        q+=1;tmp//=3
    return {
      "anchor":anchor,
      "D":D,
      "q":q,
      "C_abs_bits":abs(C).bit_length(),
      "B_abs_bits":abs(B).bit_length(),
      "P_bits":P.bit_length(),
      "gap_D_minus_q":D-q,
      "C_sign":(C>0)-(C<0),
    }

def tarjan(nodes,edges):
    sys.setrecursionlimit(max(10000,5*len(nodes)+100))
    g=defaultdict(set)
    for a,b in edges:g[a].add(b)
    idx=0;stack=[];on=set();ind={};low={};out=[]
    def go(v):
        nonlocal idx
        ind[v]=low[v]=idx;idx+=1;stack.append(v);on.add(v)
        for w in g.get(v,()):
            if w not in ind:
                go(w);low[v]=min(low[v],low[w])
            elif w in on:low[v]=min(low[v],ind[w])
        if low[v]==ind[v]:
            cc=[]
            while True:
                w=stack.pop();on.remove(w);cc.append(w)
                if w==v:break
            out.append(cc)
    for v in nodes:
        if v not in ind:go(v)
    rec=[]
    for cc in out:
        if len(cc)>1 or (len(cc)==1 and cc[0] in g.get(cc[0],())):
            rec.append(cc)
    return sorted(rec,key=lambda x:(-len(x),repr(x[0])))

groups=defaultdict(list)
for tr in v53.transitions:
    if tr["src"]["residual"] and tr["kind"]=="RESIDUAL":
        groups[(tr["source"],tr["anchor"])].append(tr)
for g in groups.values():
    g.sort(key=lambda tr:(tr["src"]["k0"],tr["src"]["k1"]))

zero_edges=[]
all_switches=[]
runs=[]
for (source,anchor),trs in groups.items():
    chunks=[];cur=[]
    for tr in trs:
        if cur and cur[-1]["dst"]["k0"]!=tr["src"]["k0"]:
            chunks.append(cur);cur=[]
        cur.append(tr)
    if cur:chunks.append(cur)
    for chunk in chunks:
        states=[chunk[0]["src"]]+[tr["dst"] for tr in chunk]
        m0=states[0]["m0"]
        Abar,Bbar,Pbar=1,0,1
        prev=None
        flags=[]
        for i,s in enumerate(states):
            c=centre(s)
            pulled=(Pbar*c-Bbar)/Abar
            p=rat_v2(Fraction(m0)-pulled)
            assert p is not None and p>=0
            currow={
              "source":source,"anchor":anchor,"m0":m0,
              "state_index":i,"precision":p,
              "law":law_id(anchor,s),"center":center_id(anchor,s),
              "depth":[s["k0"],s["k1"]],"pulled":pulled,
            }
            if prev is not None and pulled!=prev["pulled"]:
                assert p>prev["precision"]
                lo,hi=prev["precision"],p
                block=(m0>>lo)&((1<<(hi-lo))-1)
                row={
                  "source":source,"anchor":anchor,"m0":m0,
                  "old_precision":lo,"new_precision":hi,
                  "jump":hi-lo,"new_block":block,
                  "zero":block==0,
                  "old_law":prev["law"],"new_law":currow["law"],
                  "old_center":prev["center"],"new_center":currow["center"],
                  "old_depth":prev["depth"],"new_depth":currow["depth"],
                }
                all_switches.append(row)
                flags.append(row)
                if row["zero"]:zero_edges.append(row)
            prev=currow
            Abar,Bbar,Pbar=(
              s["A"]*Abar,
              s["A"]*Bbar+s["B"]*Pbar,
              s["P"]*Pbar,
            )
        # consecutive zero-exposure run lengths in this chunk
        cur_run=[]
        for e in flags:
            if e["zero"]:
                cur_run.append(e)
            elif cur_run:
                runs.append(cur_run);cur_run=[]
        if cur_run:runs.append(cur_run)

assert len(all_switches)==613
assert zero_edges

law_nodes={e["old_law"] for e in zero_edges}|{e["new_law"] for e in zero_edges}
law_edges={(e["old_law"],e["new_law"]) for e in zero_edges}
center_nodes={e["old_center"] for e in zero_edges}|{e["new_center"] for e in zero_edges}
center_edges={(e["old_center"],e["new_center"]) for e in zero_edges}
law_scc=tarjan(law_nodes,law_edges)
center_scc=tarjan(center_nodes,center_edges)

# Elimination rank on the observed zero-law graph.
succ=defaultdict(set)
for a,b in law_edges:succ[a].add(b)
live=set(law_nodes);rank={};layers=[];level=0
while live:
    dead={x for x in live if not (succ.get(x,set())&live)}
    layers.append(len(dead))
    if not dead:break
    for x in dead:rank[x]=level
    live-=dead;level+=1

# Search simple scalar/lexicographic potentials restricted to zero edges.
features=["D","q","C_abs_bits","B_abs_bits","gap_D_minus_q","C_sign"]
F={n:law_features(n) for n in law_nodes}
scalar={}
for k in features:
    ds=[F[a][k]-F[b][k] for a,b in law_edges]
    scalar[k]={
      "strict_decrease":all(d>0 for d in ds),
      "nonincrease":all(d>=0 for d in ds),
      "strict_increase":all(d<0 for d in ds),
      "nondecrease":all(d<=0 for d in ds),
      "down":sum(d>0 for d in ds),"up":sum(d<0 for d in ds),"eq":sum(d==0 for d in ds),
    }
lex=[]
for a,b in combinations(features,2):
    for sa,sb in product((1,-1),repeat=2):
        if all((sa*F[x][a],sb*F[x][b])>(sa*F[y][a],sb*F[y][b]) for x,y in law_edges):
            lex.append({"features":[a,b],"signs":[sa,sb]})

run_hist=Counter(len(r) for r in runs)
longest=max(runs,key=len)
result={
 "schema":"COLLATZ_ZERO_EXPOSURE_SWITCH_GRAMMAR_20260930",
 "parent":"COLLATZ_SWITCH_NEWBIT_TOURNAMENT_20260930",
 "all_switches":len(all_switches),
 "zero_exposure_switches":len(zero_edges),
 "zero_exposure_unique_law_edges":len(law_edges),
 "zero_exposure_law_nodes":len(law_nodes),
 "zero_exposure_unique_center_edges":len(center_edges),
 "zero_exposure_center_nodes":len(center_nodes),
 "zero_run_histogram":dict(sorted(run_hist.items())),
 "max_consecutive_zero_exposure_switches":len(longest),
 "longest_zero_run":[{
   "source":e["source"],"anchor":e["anchor"],
   "old_precision":e["old_precision"],"new_precision":e["new_precision"],
   "old_law":e["old_law"],"new_law":e["new_law"],
   "old_depth":e["old_depth"],"new_depth":e["new_depth"],
 } for e in longest],
 "law_recurrent_sccs":len(law_scc),
 "largest_law_recurrent_scc":max((len(x) for x in law_scc),default=0),
 "first_law_sccs":[x[:20] for x in law_scc[:10]],
 "center_recurrent_sccs":len(center_scc),
 "largest_center_recurrent_scc":max((len(x) for x in center_scc),default=0),
 "law_elimination_layers":layers,
 "law_leftover_nodes":len(live),
 "law_max_rank":max(rank.values(),default=None),
 "scalar_zero_edge_tests":scalar,
 "lexicographic_zero_edge_potentials":lex,
 "verdict":(
   "ZERO_EXPOSURE_SUBGRAMMAR_ACYCLIC_ON_CORPUS"
   if not law_scc and not center_scc
   else "ZERO_EXPOSURE_RECURRENT_SEPARATOR"
 ),
 "interpretation":(
   "An ordinary natural can support only finitely many switches exposing new "
   "1-bits. Therefore any infinite natural-compatible switch tail must "
   "eventually remain inside this all-zero-exposure subgrammar. Acyclicity here "
   "is the exact bounded analogue of the natural-bar theorem."
 ),
 "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(
 json.dumps(result,sort_keys=True,separators=(",",":"),default=str).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True,default=str))
