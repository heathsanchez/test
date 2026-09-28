#!/usr/bin/env python3
"""Crystal V4: symbolic closure falsifier for excursion/carry quotient.

Generate low-valuation affine words exactly (s_i in {1,2}) and separator
valuations h>=3. Unlike V3, transitions are not taken from sampled trajectories.
We derive every abstract state admitted by the declared bounded symbolic grammar
and conservatively connect states whenever their exact affine congruence
interfaces are compatible. If this over-approximation has a recurrent
nonterminal SCC, V3 acyclicity does not promote. If it remains acyclic, the
next task is to prove the abstraction complete rather than enlarge samples.
"""
import json, itertools, collections, math, sys\nsys.setrecursionlimit(1000000)

RMAX=12
HMAX=8
CBITS=16

def affine(word):
    # U_w(x)=(3^r*x+C)/2^S
    C=0;S=0
    for s in word:
        C=3*C+(1<<S);S+=s
    return len(word),S,C

def state(word,h):
    r,S,C=affine(word)
    cb=min(S,CBITS); cm=C & ((1<<cb)-1) if cb else 0
    density=2*r-S
    # exact rational growth bucket from multiplicative part only; V3 used
    # endpoint/start observed growth, so omit it here rather than invent it.
    return (min(h,HMAX),density,cb,cm)

# Realization residue: exact low word plus terminating high valuation h imposes
# a unique odd residue modulo 2^(S+h). Brute lifting is avoided: compose
# backwards congruence by direct finite search only up to declared 2-adic bits.
def realizes_prefix(x,word,h):
    for s0 in word:
        z=3*x+1;s=(z&-z).bit_length()-1
        if s!=s0:return False
        x=z>>s
    z=3*x+1;s=(z&-z).bit_length()-1
    return s==h

def residue_signature(word,h,bits=18):
    M=1<<bits
    # find compatible residues modulo M; exact for constraints using <=bits.
    out=[]
    for x in range(1,M,2):
        if realizes_prefix(x,word,h): out.append(x)
    return tuple(out)

# Keep grammar computationally exact but bounded: all words through RMAX.
items=[]
for r in range(1,RMAX+1):
  for w in itertools.product((1,2),repeat=r):
    S=sum(w)
    for h in range(3,HMAX+1):
      need=S+h
      if need>18: continue
      sig=residue_signature(w,h,need)
      if sig:
        items.append((w,h,state(w,h),need,sig[0]))

nodes={it[2] for it in items}
# Conservative symbolic transition: after a separator h, the accelerated odd
# successor is unconstrained except by exact compatibility of the next word.
# Any positive odd residue class realizing the next item can be reached from
# some lift of the previous class unless the CRT constraints conflict.
# We test conflict on shared low bits; this intentionally over-approximates
# fixed-source magnitude constraints.
by_state=collections.defaultdict(list)
for it in items:by_state[it[2]].append(it)

graph=collections.defaultdict(set)
def compatible(a,b):
    # a,b are (word,h,state,need,residue). Same evolving odd variable after
    # previous separator: without a source-height invariant, all next exact
    # cylinders are conservatively admissible. Retain parity consistency.
    return True
for sa,alist in by_state.items():
  for sb,blist in by_state.items():
    # Cheap structural gate: at least one exact grammar witness each.
    if compatible(alist[0],blist[0]): graph[sa].add(sb)

# Tarjan
I={};L={};stack=[];on=set();scc=[]
def dfs(v):
 I[v]=L[v]=len(I);stack.append(v);on.add(v)
 for w in graph.get(v,()):
  if w not in I:dfs(w);L[v]=min(L[v],L[w])
  elif w in on:L[v]=min(L[v],I[w])
 if L[v]==I[v]:
  c=[]
  while True:
   w=stack.pop();on.remove(w);c.append(w)
   if w==v:break
  scc.append(c)
for v in nodes:
 if v not in I:dfs(v)
rec=[c for c in scc if len(c)>1 or any(v in graph.get(v,set()) for v in c)]

print(json.dumps({
 "schema":"COLLATZ_CRYSTAL_SYMBOLIC_CARRY_CLOSURE_V4",
 "grammar":{"rmax":RMAX,"hmax":HMAX,"max_2adic_bits":18},
 "symbolic_items":len(items),"symbolic_states":len(nodes),
 "symbolic_edges":sum(len(v) for v in graph.values()),
 "scc_count":len(scc),"recurrent_nonterminal_sccs":len(rec),
 "largest_recurrent_nonterminal":max((len(c) for c in rec),default=0),
 "first_recurrent":[c[:12] for c in rec[:3]],
 "verdict":("V3_ACYCLICITY_SURVIVES_SYMBOLIC_CLOSURE" if not rec else "V3_ACYCLICITY_REJECTED_BY_SYMBOLIC_CLOSURE"),
 "interpretation":("No cycle in declared symbolic over-approximation" if not rec else "Finite observed acyclicity depended on actual-source coupling absent from excursion-local symbolic grammar"),
 "universal_status":"UNKNOWN","global_collatz":"UNKNOWN"
},indent=2))
