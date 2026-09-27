#!/usr/bin/env python3
"""Compile the Crystal-discovered bounded Q graph and inspect recurrent structure.

Q=(j mod 2, floor(2^j P_j(2^m)/F_j)).
Edges are exact observed one-step live-origin transitions. Each source state also
has its exact minimum envelope-paying macro length <=21. We quotient only after
the prior transition-falsifier established no bounded signature separator.

Outputs SCC/cycle structure and a candidate rank if the observed graph is a DAG.
Bounded evidence only; universal simulation remains a separate theorem.
"""
import json
from collections import defaultdict,deque
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512;BMAX=21
qmin,F,_=language_counts(DEPTH)
hist=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for n in range(1,1<<BITS,2):
 z=first_crossing(n,qmin)
 if z:
  j,_,_=z;hist[j][n.bit_length()]+=1
C=[[0]*(BITS+1) for _ in range(DEPTH+1)];P=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for j in range(1,DEPTH+1):
 for m in range(1,BITS+1):C[j][m]=C[j][m-1]+hist[j][m]
for m in range(1,BITS+1):
 P[0][m]=1<<(m-1)
 for j in range(1,DEPTH+1):P[j][m]=P[j-1][m]-C[j][m]
def Q(j,m): return (j&1,(P[j][m]<<j)//F[j]) if P[j][m] else None
def good(j,b,m):
 if not P[j][m]:return True
 a=P[j+b][m]*F[j];d=P[j][m]*F[j+b]
 e=(6*(j+b))//125-(6*j)//125-b
 return a <= (d<<e) if e>=0 else (a<<(-e))<=d
def block(j,m):
 for b in range(1,BMAX+1):
  if j+b<=DEPTH and good(j,b,m):return b
 return 0

edges=defaultdict(set); reps=defaultdict(list); exits=set()
for j in range(60,DEPTH-BMAX):
 for m in range(1,BITS+1):
  if not P[j][m]:continue
  u=Q(j,m);v=Q(j+1,m)
  reps[u].append((j,m,block(j,m)))
  if v is None: exits.add(u)
  else: edges[u].add(v)
nodes=set(reps)|set(edges)
for vs in edges.values():nodes|=vs

# Tarjan SCC
idx=0;stack=[];on=set();I={};L={};sccs=[]
def dfs(v):
 global idx
 I[v]=L[v]=idx;idx+=1;stack.append(v);on.add(v)
 for w in edges.get(v,()):
  if w not in I: dfs(w);L[v]=min(L[v],L[w])
  elif w in on:L[v]=min(L[v],I[w])
 if L[v]==I[v]:
  c=[]
  while True:
   w=stack.pop();on.remove(w);c.append(w)
   if w==v:break
  sccs.append(c)
for v in nodes:
 if v not in I:dfs(v)
cyclic=[c for c in sccs if len(c)>1 or (len(c)==1 and c[0] in edges.get(c[0],()))]

# DAG longest-distance-to-exit rank only if no cycles.
rank={}
if not cyclic:
 order=[];seen=set()
 def topo(v):
  if v in seen:return
  seen.add(v)
  for w in edges.get(v,()):topo(w)
  order.append(v)
 for v in nodes:topo(v)
 for v in order:
  rank[v]=0 if (v in exits or not edges.get(v)) else 1+max(rank[w] for w in edges[v])

result={"schema":"COLLATZ_CRYSTAL_Q_GRAPH_V0","nodes":len(nodes),
 "edges":sum(len(v) for v in edges.values()),"exit_nodes":len(exits),
 "scc_count":len(sccs),"cyclic_scc_count":len(cyclic),
 "largest_cyclic_scc":max((len(c) for c in cyclic),default=0),
 "cyclic_examples":[[list(x) for x in c[:20]] for c in cyclic[:10]],
 "candidate_rank_max":max(rank.values()) if rank else None,
 "all_observed_macro_blocks_positive":all(b>0 for xs in reps.values() for _,_,b in xs),
 "status":"BOUNDED_DAG_RANK_CERTIFICATE" if not cyclic else "BOUNDED_RECURRENT_Q_OBSTRUCTION",
 "universal_simulation":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
