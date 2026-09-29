#!/usr/bin/env python3
"""Crystal V40: phase-normalized source-biadic same-anchor returns.

Bounded discovery gate on three frozen exact V23-lineage natural sources.
Unlike V39's sliding 12-odd windows, this parses exact odd/even episodes and
compares only consecutive returns to the same intrinsic episode anchor
    r = v2(x+1), x = 2^r*m - 1.
Each return is therefore an exact affine map
    m' = (A*m+B)/2^D
with defect Delta(m) = (2^D-A)*m-B.

The protected cell carries the exact return Q2 cylinder, the intrinsic Q3
future ball, and the fixed-origin source fibre at those same precisions.
This is theorem-discovery evidence only: acyclicity on these frozen sources
does not establish the all-depth transition/completeness theorem required by
V37's Lean closeout.
"""
from __future__ import annotations
from collections import defaultdict
from contextlib import redirect_stdout
import hashlib, io, json

with redirect_stdout(io.StringIO()):
    import collatz_q0_rigid_recharge_audit as ra
    import collatz_crystal_parameter_quotient_v25 as v25
    import collatz_crystal_post_p36_adversary_v26 as v26

def T(x:int)->int:
    return (3*x+1)//2 if x&1 else x//2

def simple_exit(n:int,y:int,k:int):
    if 0 < y < n:
        return {"kind":"D","depth":k,"endpoint":str(y)}
    if y%8==5 and y<=4*n:
        return {"kind":"S","depth":k,"endpoint":str(y)}
    if y%3==2:
        p=(2*y-1)//3
        if 0<p<n and T(p)==y:
            return {"kind":"M1","depth":k,"endpoint":str(y),"p":str(p)}
    return None

def source_v26():
    bits=([1,1,0]*((v26.PARITY_LEN+2)//3))[:v26.PARITY_LEN]
    yres,mod=v26.parity_residue(bits)
    t=((yres-v26.A59)*pow(v26.C59,-1,mod))%mod
    return v26.N0+v26.NC*t

def v3z(x:int):
    x=abs(x)
    if x==0:
        return None
    v=0
    while x%3==0:
        x//=3; v+=1
    return v

def cert_id(c):
    raw=(c["r"],c["A"],c["B"],c["D"],c["rho"])
    return hashlib.sha256(repr(raw).encode()).hexdigest()[:20]

def actual_episode_returns(name:str,n:int,cap:int):
    zero_depth=n.bit_length()
    y=n
    k=0
    first_exit=None

    while k < zero_depth:
        ex=simple_exit(n,y,k)
        if ex is not None:
            return {
                "name":name,"source":n,"zero_depth":zero_depth,
                "first_exit":ex,"starts":[],"branches":[],"events":[],
                "note":"ordinary exit before zero-tail",
            }
        y=T(y); k+=1

    starts=[]
    branches=[]
    while k<=cap and not (y&1):
        ex=simple_exit(n,y,k)
        if ex is not None:
            first_exit=ex; break
        y=T(y); k+=1

    while first_exit is None and k<=cap:
        ex=simple_exit(n,y,k)
        if ex is not None:
            first_exit=ex; break
        assert y&1
        r,m,s,rp,mp,yend=ra.episode(y)
        starts.append((k,r,m,y))
        end=k+r+s
        if end>cap:
            break

        z=y
        blocked=False
        for j in range(k+1,end+1):
            z=T(z)
            ex=simple_exit(n,z,j)
            if ex is not None:
                first_exit=ex
                blocked=True
                break
        if blocked:
            break
        assert z==yend
        branches.append((r,s,rp))
        k=end; y=yend

    events=[]
    last={}
    for end_idx,st in enumerate(starts):
        depth,r,m,x=st
        if r in last:
            start_idx=last[r]
            word=tuple(branches[start_idx:end_idx])
            assert word
            c=ra.certificate(word)
            m0=starts[start_idx][2]
            m1=m
            assert ra.admissible(c,m0)
            assert ra.replay(c,m0)==m1
            assert c["r"]==r
            C=(1<<c["D"])-c["A"]
            defect=C*m0-c["B"]
            events.append({
                "source_name":name,"source":n,"anchor":r,
                "start_index":start_idx,"end_index":end_idx,
                "k0":starts[start_idx][0],"k1":depth,
                "m0":m0,"m1":m1,
                "cert":c,"cert_id":cert_id(c),
                "defect":defect,
                "zero_defect":defect==0,
            })
        last[r]=end_idx

    return {
        "name":name,"source":n,"zero_depth":zero_depth,
        "first_exit":first_exit,"starts":starts,"branches":branches,
        "events":events,"note":None,
    }

sources=[
    ("V23_MIN",v25.N0,800),
    ("V36_SOURCE",v25.N0+v25.NC*1_018_706,800),
    ("V26_HARD",source_v26(),900),
]
runs=[actual_episode_returns(*s) for s in sources]

banks=defaultdict(dict)
for rr in runs:
    for e in rr["events"]:
        banks[e["anchor"]][e["cert_id"]]=e["cert"]
banks={r:tuple(v for _,v in sorted(d.items())) for r,d in banks.items()}

def q3ball(m:int,bank):
    vals=[v3z(((1<<c["D"])-c["A"])*m-c["B"]) for c in bank]
    if any(v is None for v in vals):
        return (None,None)
    rad=max(vals,default=0)
    return (rad,m%(3**rad) if rad else 0)

def event_keys(e):
    c=e["cert"]; n=e["source"]; m=e["m0"]; anchor=e["anchor"]
    d2=c["D"]+1
    rho=c["rho"]
    assert m%(1<<d2)==rho
    r3,res3=q3ball(m,banks[anchor])
    intrinsic=(anchor,d2,rho,r3,res3)
    if r3 is None:
        source_cell=(anchor,d2,rho,None,None,n%(1<<d2),None)
    else:
        source_cell=(anchor,d2,rho,r3,res3,n%(1<<d2),
                     n%(3**r3) if r3 else 0)
    return intrinsic,source_cell

for rr in runs:
    for e in rr["events"]:
        e["intrinsic_key"],e["source_key"]=event_keys(e)

def build_graph(key_name):
    nodes=set(); succ=defaultdict(set); exits=set(); paths=[]
    for rr in runs:
        by=defaultdict(list)
        for e in rr["events"]:
            by[e["anchor"]].append(e)
        for anchor,es in by.items():
            es.sort(key=lambda z:(z["k0"],z["k1"]))
            keys=[e[key_name] for e in es]
            nodes.update(keys)
            for a,b in zip(keys,keys[1:]):
                succ[a].add(b)
            if keys:
                exits.add(keys[-1])
                paths.append((rr["name"],anchor,keys))
    for x in nodes:
        succ.setdefault(x,set())
    return nodes,succ,exits,paths

def tarjan(nodes,succ):
    idx=0; ind={}; low={}; stack=[]; on=set(); comps=[]
    def visit(v):
        nonlocal idx
        ind[v]=low[v]=idx; idx+=1; stack.append(v); on.add(v)
        for w in succ[v]:
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
    for v in sorted(nodes,key=repr):
        if v not in ind: visit(v)
    recurrent=[]
    for cc in comps:
        cyc=len(cc)>1 or any(v in succ[v] for v in cc)
        if cyc:
            recurrent.append(cc)
    recurrent.sort(key=lambda c:(-len(c),repr(sorted(c,key=repr)[0])))
    return recurrent

def elimination_rank(nodes,succ):
    live=set(nodes); rank={}; level=0; layers=[]
    while live:
        dead={x for x in live if not (succ[x]&live)}
        layers.append(len(dead))
        if not dead: break
        for x in dead: rank[x]=level
        live-=dead; level+=1
    return rank,live,layers

graphs={}
for key_name in ("intrinsic_key","source_key"):
    nodes,succ,exits,paths=build_graph(key_name)
    recurrent=tarjan(nodes,succ)
    rank,residual,layers=elimination_rank(nodes,succ)
    concrete_cycles=[]
    for name,anchor,keys in paths:
        seen={}
        for i,k in enumerate(keys):
            if k in seen:
                concrete_cycles.append({
                    "source":name,"anchor":anchor,
                    "from_event":seen[k],"to_event":i,"key":repr(k)
                })
                break
            seen[k]=i
    graphs[key_name]={
        "nodes":len(nodes),
        "edges":sum(len(v) for v in succ.values()),
        "terminal_nodes":len(exits),
        "recurrent_sccs":len(recurrent),
        "largest_scc":max((len(c) for c in recurrent),default=0),
        "first_sccs":[[repr(x) for x in sorted(c,key=repr)[:20]]
                      for c in recurrent[:10]],
        "residual_nodes_after_elimination":len(residual),
        "elimination_layers":layers,
        "max_rank":max(rank.values(),default=None),
        "concrete_path_cycles":concrete_cycles[:20],
    }

source_rows=[]
event_rows=[]
for rr in runs:
    source_rows.append({
        "name":rr["name"],"source":str(rr["source"]),
        "zero_depth":rr["zero_depth"],
        "first_exit":rr["first_exit"],
        "episode_starts":len(rr["starts"]),
        "same_anchor_returns":len(rr["events"]),
        "distinct_anchors":len({e["anchor"] for e in rr["events"]}),
        "zero_defect_returns":sum(e["zero_defect"] for e in rr["events"]),
        "note":rr["note"],
    })
    for e in rr["events"][:100]:
        c=e["cert"]
        event_rows.append({
            "source":rr["name"],"anchor":e["anchor"],
            "k0":e["k0"],"k1":e["k1"],
            "m0":str(e["m0"]),"m1":str(e["m1"]),
            "A":str(c["A"]),"B":str(c["B"]),"D":c["D"],
            "rho":str(c["rho"]),
            "defect":str(e["defect"]),
            "zero_defect":e["zero_defect"],
            "intrinsic_key":repr(e["intrinsic_key"]),
            "source_key":repr(e["source_key"]),
        })

source_graph=graphs["source_key"]
if source_graph["recurrent_sccs"]:
    verdict="SOURCE_BIADIC_RETURN_RECURRENT_CELL_EMITTED"
elif sum(x["same_anchor_returns"] for x in source_rows)==0:
    verdict="NO_POST_ZERO_TAIL_SAME_ANCHOR_RETURNS_ON_FROZEN_SOURCES"
else:
    verdict="BOUNDED_SOURCE_BIADIC_RETURN_GRAPH_ACYCLIC"

result={
    "schema":"COLLATZ_CRYSTAL_PHASE_NORMALIZED_RETURN_V40",
    "parents":{
        "V37":"collatz-crystal-biadic-ranked-normalization-v37@0927aa8db1cde53b84a6327b661b5969c0ab3022",
        "V38":"collatz-crystal-b-transient-v38@b92b6e88a7f55cccd4330a4175d383096a40553b",
        "V39":"collatz-crystal-zero-tail-k-rank-v39@ca6723d8db2263217733ff7c8d6f85b7b2735520",
        "A8":"collatz-biadic-cell-v0@2f4ee9e006b174814dcc77f8ce1580b5969708f7",
    },
    "sources":source_rows,
    "return_law_bank":{"anchors":len(banks),
                       "laws":sum(len(v) for v in banks.values()),
                       "laws_by_anchor":{str(k):len(v) for k,v in sorted(banks.items())}},
    "graphs":graphs,
    "sample_events":event_rows,
    "verdict":verdict,
    "interpretation":(
        "Sliding-window phase transport is removed: every event is an exact "
        "same-anchor episode return. The source graph additionally carries the "
        "fixed-origin source fibre at the active Q2/Q3 precisions."
    ),
    "promotion_boundary":(
        "Acyclicity here is bounded discovery evidence only. QED still requires "
        "an all-depth/source-independent completeness and successor theorem for "
        "this quotient, then instantiation of V37 hprogress. A recurrent SCC or "
        "zero-defect event is an exact obstruction, not a proof failure to hide."
    ),
    "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(
    json.dumps(result,sort_keys=True,separators=(",",":")).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
