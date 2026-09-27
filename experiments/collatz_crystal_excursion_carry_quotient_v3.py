#!/usr/bin/env python3
"""Crystal V3: exact excursion/carry transition quotient for fixed-origin residual.

Compress a trajectory before first protected exit into maximal odd-accelerated
low-valuation excursions (s in {1,2}), separated by high-valuation events.
State records only exact transition data derived from consecutive excursions.
Build observed transition graph and report recurrent nonterminal SCCs.
Bounded discovery only; never promotes a universal theorem.
"""
import json, collections
LIMIT=1<<24; CAP=4096
HARD={27,31,3041391,8088063,13353631,13421671,63728127}

def T(x): return (3*x+1)//2 if x&1 else x//2
def v2(z): return (z&-z).bit_length()-1

def trace(n):
    x=n; j=0; events=[]; word=[]; S=0; C=0; r=0; start=None
    def flush(endx,sep_s):
        nonlocal word,S,C,r,start
        if r:
            # exact low excursion signature plus separator valuation/carry class.
            events.append({"r":r,"S":S,"C":C,"start":start,"end":endx,
                           "sep":sep_s,"growth":(endx*1024)//max(1,start)})
        word=[];S=C=r=0;start=None
    while j<=CAP:
        if x<n:
            flush(x,-1); return "DESCENT",j,x,events
        if x%8==5 and x<=4*n:
            flush(x,-2); return "SPLICE",j,x,events
        if x&1:
            z=3*x+1; s=v2(z)
            if s in (1,2):
                if start is None:start=x
                C=3*C+(1<<S); S+=s; r+=1; word.append(s)
            else:
                flush(x,s)
        x=T(x);j+=1
    flush(x,-3);return "UNRESOLVED",CAP,x,events

sources=set(HARD)
for n in range(3,LIMIT,4099*2):sources.add(n|1)
sources=sorted(sources)

# Transition state: separator valuation bucket, previous excursion density,
# affine bias normalized to its dyadic denominator, and next separator direction.
def state(e):
    sb=e["sep"] if e["sep"]<0 else min(e["sep"],8)
    density=2*e["r"]-e["S"] # signed excess of low 1-valuations
    cbits=min(e["S"],16); cm=e["C"] & ((1<<cbits)-1) if cbits else 0
    # structural coarse exact-derived coordinates, no source modulus.
    return (sb,density,cbits,cm,e["growth"]//128)

graph=collections.defaultdict(set); outcomes=collections.defaultdict(set)
rows=[]
for n in sources:
    out,j,x,es=trace(n); sts=[state(e) for e in es]
    for a,b in zip(sts,sts[1:]): graph[a].add(b)
    if sts: outcomes[sts[-1]].add(out)
    rows.append({"n":n,"outcome":out,"j":j,"excursions":len(es),"states":sts[-8:]})

nodes=set(graph)|{v for vs in graph.values() for v in vs}
# Tarjan SCC
idx=0;stack=[];on=set();I={};L={};scc=[]
def dfs(v):
    global idx
    I[v]=L[v]=len(I);stack.append(v);on.add(v)
    for w in graph.get(v,()):
        if w not in I: dfs(w);L[v]=min(L[v],L[w])
        elif w in on:L[v]=min(L[v],I[w])
    if L[v]==I[v]:
        c=[]
        while 1:
            w=stack.pop();on.remove(w);c.append(w)
            if w==v:break
        scc.append(c)
for v in nodes:
    if v not in I:dfs(v)
recurrent=[]
for c in scc:
    cs=set(c); cyc=len(c)>1 or any(v in graph.get(v,set()) for v in c)
    terminal=any(outcomes.get(v) for v in c)
    if cyc and not terminal: recurrent.append(c)

print(json.dumps({
 "schema":"COLLATZ_CRYSTAL_EXCURSION_CARRY_QUOTIENT_V3",
 "boundary":{"limit":LIMIT,"cap":CAP,"sources":len(sources)},
 "resolved":collections.Counter(r["outcome"] for r in rows),
 "max_decision_steps":max(r["j"] for r in rows),
 "max_excursions":max(r["excursions"] for r in rows),
 "quotient_nodes":len(nodes),"quotient_edges":sum(map(len,graph.values())),
 "scc_count":len(scc),"recurrent_nonterminal_sccs":len(recurrent),
 "largest_recurrent_nonterminal":max((len(c) for c in recurrent),default=0),
 "recurrent_examples":[c[:8] for c in recurrent[:8]],
 "hard_rows":[r for r in rows if r["n"] in HARD],
 "candidate":("OBSERVED_QUOTIENT_ACYCLIC_NONTERMINAL" if not recurrent else "RECURRENT_NONTERMINAL_RESIDUAL"),
 "universal_status":"UNKNOWN","global_collatz":"UNKNOWN"
},indent=2,default=list))
