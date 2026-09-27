#!/usr/bin/env python3
"""
Crystal V7: exact source-relative band-return calculus for the quarter-splice residual.

This is a bounded theorem-discovery/falsification experiment, not a Collatz proof.

For each odd source n in the declared finite range, follow the odd-only Collatz map
    U(y) = (3y+1)/2^v2(3y+1).
A hypothetical minimal bad source cannot descend below n.  While y is in [n,4n],
quarter-splice avoidance forces v2(3y+1) in {1,2}.  We compile the exact macro
from one non-splice band state to the next band state/descent:
    2^D y1 = 3^R y0 + B.
We then compare observed continuation graphs under:
  CONTROL         exact affine macro (R,D,B)
  OWN_V23         CONTROL + active exact defect (v2 excess, v3)
  ENDPOINT        exact band endpoint y0
  SOURCE_ENDPOINT exact (n,y0) sanity baseline

A nonempty greatest kernel means that representation admits an observed recurrent
possibility after cross-source identification.  Empty kernel means the finite
observed graph is rankable; it is not a universal theorem.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter, defaultdict, deque
from pathlib import Path

def v2(x:int)->int:
    assert x>0
    return (x & -x).bit_length()-1

def vp(x:int,p:int):
    x=abs(x)
    if x==0: return None
    k=0
    while x%p==0:
        x//=p; k+=1
    return k

def odd_step(y:int):
    z=3*y+1
    a=v2(z)
    return z>>a,a

def add_node(g,k):
    g.setdefault(k,set())

def add_edge(g,a,b):
    g.setdefault(a,set()).add(b)
    g.setdefault(b,set())

def kernel_rank(g):
    rev=defaultdict(list)
    outdeg={u:len(vs) for u,vs in g.items()}
    for u,vs in g.items():
        for v in vs: rev[v].append(u)
    q=deque(u for u,d in outdeg.items() if d==0)
    rank={u:0 for u in q}
    removed=0
    while q:
        u=q.popleft(); removed+=1
        ru=rank[u]
        for p in rev.get(u,()):
            if outdeg[p]<=0: continue
            outdeg[p]-=1
            rank[p]=max(rank.get(p,0),ru+1)
            if outdeg[p]==0: q.append(p)
    kernel=[u for u,d in outdeg.items() if d>0]
    hist=Counter(rank.values())
    return {
        "nodes":len(g),
        "edges":sum(len(v) for v in g.values()),
        "kernel_nodes":len(kernel),
        "max_rank":max(rank.values(),default=0),
        "rank_histogram":{str(k):hist[k] for k in sorted(hist)},
        "kernel_witness":repr(min(kernel,key=repr))[:500] if kernel else None,
    }

def run(limit:int,cap:int,out:Path):
    graphs={k:{} for k in ("CONTROL","OWN_V23","ENDPOINT","SOURCE_ENDPOINT")}
    counts=Counter()
    first_unresolved=[]
    rec_macro=(0,0,0,0,0) # length,n,y0,y1,D
    rec_events=(0,0)
    rec_steps=(0,0)
    for n in range(3,limit,2):
        counts["tested_odd_sources"]+=1
        y=n; steps=0; events=0
        prev={k:None for k in graphs}
        resolved=None
        while steps<cap:
            if y<n:
                resolved="descent"; break
            if y<=4*n and y%8==5:
                resolved="splice"; break
            if y>4*n:
                # Every macro starts in-band; reaching here means the cap logic
                # was interrupted before a first return.
                resolved="internal_error"; break

            y0=y
            a0=v2(3*y0+1)
            assert a0 in (1,2), (n,y0,a0)
            counts["low_band_valuation_checks"]+=1
            R=D=B=0
            while steps<cap:
                y1,a=odd_step(y)
                B=3*B+(1<<D)
                R+=1; D+=a; steps+=1
                y=y1
                if y<n or y<=4*n:
                    break
            if steps>=cap and y>=n and y>4*n:
                resolved="cap"; break

            assert (1<<D)*y == pow(3,R)*y0+B
            C=(1<<D)-pow(3,R)
            defect=C*y0-B
            assert defect==(1<<D)*(y0-y)
            counts["affine_macro_checks"]+=1
            events+=1
            if R>rec_macro[0]:
                rec_macro=(R,n,y0,y,D)

            sem=(R,D,B)
            dv2=None if defect==0 else vp(defect,2)
            dv3=vp(defect,3)
            own=(sem,None if dv2 is None else dv2-D,dv3)
            keys={
                "CONTROL":sem,
                "OWN_V23":own,
                "ENDPOINT":y0,
                "SOURCE_ENDPOINT":(n,y0),
            }
            for mode,k in keys.items():
                add_node(graphs[mode],k)
                if prev[mode] is not None: add_edge(graphs[mode],prev[mode],k)
                prev[mode]=k

            if y<n:
                resolved="descent"; break
            if y%8==5:
                resolved="splice"; break
            # otherwise y is the next non-splice band state
        if resolved is None: resolved="cap"
        counts["resolved_"+resolved]+=1
        if resolved in ("cap","internal_error") and len(first_unresolved)<20:
            first_unresolved.append([n,steps,y])
        if events>rec_events[0]: rec_events=(events,n)
        if steps>rec_steps[0]: rec_steps=(steps,n)

    stats={mode:kernel_rank(g) for mode,g in graphs.items()}
    unresolved=counts["resolved_cap"]+counts["resolved_internal_error"]
    if unresolved:
        verdict="EXACT_RESIDUAL_UNRESOLVED_ON_BOUNDARY"
    elif (stats["CONTROL"]["kernel_nodes"]>0
          and stats["OWN_V23"]["kernel_nodes"]>0
          and stats["ENDPOINT"]["kernel_nodes"]==0
          and stats["SOURCE_ENDPOINT"]["kernel_nodes"]==0):
        verdict="PASS_BOUNDED_ENDPOINT_DAG_SEPARATOR"
    elif stats["ENDPOINT"]["kernel_nodes"]>0:
        verdict="EXACT_ENDPOINT_RECURRENCE_WITNESS"
    else:
        verdict="BOUNDED_SEPARATOR_DIFFERENT_THAN_EXPECTED"

    result={
        "schema":"COLLATZ_CRYSTAL_BAND_RETURN_V7",
        "limit":limit,
        "odd_step_cap":cap,
        "counts":dict(sorted(counts.items())),
        "first_unresolved":first_unresolved,
        "record_macro":{"odd_length":rec_macro[0],"source":rec_macro[1],"start":rec_macro[2],"end":rec_macro[3],"D":rec_macro[4]},
        "record_band_events":{"count":rec_events[0],"source":rec_events[1]},
        "record_odd_steps":{"count":rec_steps[0],"source":rec_steps[1]},
        "representations":stats,
        "verdict":verdict,
        "claim_boundary":"Exact bounded actual-source band-return graph. Empty finite kernel is evidence for a candidate residual rank only; it is not a universal well-foundedness proof.",
        "universal_status":"UNKNOWN",
        "global_collatz":"UNKNOWN",
    }
    body=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["closure_certificate"]=hashlib.sha256(body.encode()).hexdigest()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--limit",type=int,default=1<<20)
    ap.add_argument("--cap",type=int,default=4096)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    run(a.limit,a.cap,a.output)
