#!/usr/bin/env python3
"""Diagnose elimination rank of intrinsic Q2 x Q3 Collatz cells."""
from __future__ import annotations
import argparse,json
from collections import defaultdict,Counter
from pathlib import Path
import collatz_biadic_cell_v0 as bc
import collatz_stateful_future_kernel_v0 as fk

def elimination_rank(nodes,succ):
    live=set(nodes); rank={}; r=0
    while live:
        dead={n for n in live if not (succ[n]&live)}
        if not dead: break
        for n in dead: rank[n]=r
        live-=dead; r+=1
    return rank,live

def analyze(lo,hi,K,out):
    seqs,bank=bc.collect(lo,hi,K)
    nodes=set();succ=defaultdict(set);exits=set();occ=defaultdict(list)
    for anchor,seq in seqs:
        cs=bank[anchor]
        keys=[]
        for idx,e in enumerate(seq):
            k=bc.key(e,cs,"BI_CELL")
            keys.append(k);nodes.add(k)
            c=e["cert"]
            occ[k].append({
                "source":e["source"],"anchor":anchor,"m":e["m0"],"k0":e["k0"],
                "active":fk.semantic_tuple(c),"R":fk.vpz(c["A"],3),
                "position":idx,"sequence_len":len(seq),
                "remaining_edges":len(seq)-1-idx
            })
        for a,b in zip(keys,keys[1:]):succ[a].add(b)
        if keys:exits.add(keys[-1])
    for n in nodes:succ.setdefault(n,set())
    rank,resid=elimination_rank(nodes,succ)

    rows=[]
    for n in sorted(nodes,key=repr):
        d2,rho,r3,res3=n
        os=occ[n]
        rem=sorted({x["remaining_edges"] for x in os})
        active=sorted({tuple(x["active"]) for x in os})
        Rs=sorted({x["R"] for x in os})
        row={
          "cell":[d2,rho,r3,res3],
          "elim_rank":rank.get(n),
          "terminal":n in exits,
          "succ":[list(x) for x in sorted(succ[n],key=repr)],
          "occurrences":len(os),"remaining_edges":rem,
          "active_laws":[list(x) for x in active],"R":Rs,
          "d2_minus_r3":None if r3 is None else d2-r3,
          "d2_plus_r3":None if r3 is None else d2+r3,
          "source_sample":sorted({x["source"] for x in os})[:8],
        }
        rows.append(row)
    # simple exact rank candidate tests
    candidates={}
    for expr in ["r3","d2","d2-r3","d2+r3","remaining"]:
        pairs=[]
        for row in rows:
            if row["elim_rank"] is None: continue
            if expr=="r3": val=row["cell"][2]
            elif expr=="d2": val=row["cell"][0]
            elif expr=="d2-r3": val=row["d2_minus_r3"]
            elif expr=="d2+r3": val=row["d2_plus_r3"]
            else:
                val=row["remaining_edges"][0] if len(row["remaining_edges"])==1 else None
            pairs.append((val,row["elim_rank"]))
        candidates[expr]=pairs
    result={"range":[lo|1,hi],"nodes":len(nodes),"residual_nodes":len(resid),
            "rows":rows,"candidates":candidates}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("NODES",len(nodes),"RESIDUAL",len(resid))
    print("ROWS",json.dumps(rows,sort_keys=True))
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--lo",type=int,required=True);ap.add_argument("--hi",type=int,required=True)
    ap.add_argument("--K",type=int,default=128);ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args();analyze(a.lo,a.hi,a.K,a.output)
