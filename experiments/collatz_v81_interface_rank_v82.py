#!/usr/bin/env python3
"""V82: elimination rank on the prospectively qualified V81 interface.

Uses the frozen V80 interface unchanged and the exact old+fresh V81 transition
authority.  If the residual interface graph is acyclic, every represented
residual state reaches PROGRESS/EXIT in finitely many interface transitions.
A recurrent SCC is instead emitted as the exact next obstruction.

Bounded graph theorem only; universal Collatz still requires all-depth
admission/completeness of the interface transition relation.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from contextlib import redirect_stdout
import hashlib, io, json

with redirect_stdout(io.StringIO()):
    import collatz_v80_fresh_interface_v81 as v81

PARENT="d4PLACEHOLDER"
trs=v81.old+v81.A["transitions"]+v81.B["transitions"]

outs=defaultdict(set)
samples={}
for tr in trs:
    s=v81.interface(tr["src"],tr["t"])
    o=v81.outcome(tr)
    outs[s].add(o)
    samples.setdefault((s,o),tr)

assert all(len(v)==1 for v in outs.values())
out={s:next(iter(v)) for s,v in outs.items()}

succ=defaultdict(set)
terminal=Counter()
for s,o in out.items():
    if o[0]=="RESIDUAL":
        d=o[1]
        succ[s].add(d)
    else:
        terminal[o[0]]+=1
    succ.setdefault(s,set())

# Tarjan SCC.
idx=0; ind={}; low={}; stack=[]; on=set(); comps=[]
def visit(v):
    global idx
    ind[v]=low[v]=len(ind)
    stack.append(v); on.add(v)
    for w in succ.get(v,()):
        if w not in ind:
            visit(w); low[v]=min(low[v],low[w])
        elif w in on:
            low[v]=min(low[v],ind[w])
    if low[v]==ind[v]:
        cc=[]
        while True:
            w=stack.pop(); on.remove(w); cc.append(w)
            if w==v: break
        comps.append(cc)

for v in list(succ):
    if v not in ind: visit(v)

recurrent=[]
for cc in comps:
    cyc=len(cc)>1 or any(v in succ.get(v,()) for v in cc)
    if cyc: recurrent.append(cc)
recurrent.sort(key=lambda c:(-len(c),repr(c[0])))

# Exact elimination rank.
live=set(succ)
rank={}
layers=[]
level=0
while live:
    dead=set()
    for s in live:
        o=out.get(s)
        if o is None:
            dead.add(s)
        elif o[0]!="RESIDUAL":
            dead.add(s)
        else:
            d=o[1]
            if d not in live:
                dead.add(s)
    layers.append(len(dead))
    if not dead: break
    for s in dead: rank[s]=level
    live-=dead
    level+=1

rank_hist=Counter(rank.values())
cycle_samples=[]
for cc in recurrent[:8]:
    rows=[]
    for s in cc[:12]:
        o=out.get(s)
        rows.append({"state":repr(s),"outcome":repr(o)})
    cycle_samples.append(rows)

result={
  "schema":"COLLATZ_V81_INTERFACE_RANK_V82",
  "parent_v81_run":37437716076,
  "transition_rows":len(trs),
  "interface_states":len(out),
  "residual_edges":sum(len(v) for v in succ.values()),
  "terminal_state_kinds":dict(sorted(terminal.items())),
  "recurrent_sccs":len(recurrent),
  "largest_recurrent_scc":max((len(c) for c in recurrent),default=0),
  "recurrent_nodes":sum(map(len,recurrent)),
  "cycle_samples":cycle_samples,
  "eliminated_states":len(rank),
  "leftover_states":len(live),
  "elimination_layers":layers,
  "max_elimination_rank":max(rank.values(),default=None),
  "rank_histogram":{str(k):v for k,v in sorted(rank_hist.items())},
  "status":("ACYCLIC_BOUNDED_INTERFACE" if not recurrent else "RECURRENT_INTERFACE_RESIDUAL"),
  "interpretation":(
    "Acyclicity would compile the old+fresh finite transition authority into an "
    "exact elimination rank on the V80 interface. Recurrence instead localizes "
    "the minimum represented obstruction. Neither establishes all-depth source "
    "admission/completeness."
  ),
  "global_collatz":"UNKNOWN","qed":False,
}
result["certificate_sha256"]=hashlib.sha256(
 json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
