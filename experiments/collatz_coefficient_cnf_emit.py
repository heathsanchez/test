#!/usr/bin/env python3
"""Emit the exact coefficient-persistence CNF without trusting any SAT solver."""
import argparse, json, time
from pathlib import Path
from collatz_coefficient_cnf import C, req_odds
from collatz_coefficient_cnf_v2 import worst_widths, step_conditional

class ClauseSink:
    def __init__(self):
        self.clauses=[]
    def add_clause(self,clause):
        self.clauses.append(list(clause))

def write_dimacs(path,nv,clauses):
    with open(path,"w",encoding="ascii") as f:
        f.write(f"p cnf {nv} {len(clauses)}\n")
        for cl in clauses:
            f.write(" ".join(map(str,cl))+" 0\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bits",type=int,required=True)
    ap.add_argument("--lower",type=int,required=True)
    ap.add_argument("--upper",type=int,required=True)
    ap.add_argument("--horizon",type=int,required=True)
    ap.add_argument("--out-dir",required=True)
    A=ap.parse_args()
    K,H=A.bits,A.horizon
    assert 0<=A.lower<=A.upper<(1<<K)
    out=Path(A.out_dir); out.mkdir(parents=True,exist_ok=True)
    start=time.time()
    sink=ClauseSink()
    c=C(sink)
    seed=[c.var() for _ in range(K)]
    c.add([c.uge_const(seed,A.lower)])
    c.add([c.ule_const(seed,A.upper)])
    widths=worst_widths(A.upper,H)
    x=seed+[c.F]*max(0,widths[0]-K)
    qbits=[c.F]*((H+1).bit_length()+1)
    req=req_odds(H)
    for t in range(1,H+1):
        x,odd=step_conditional(c,x,widths[t])
        qbits=c.inc_if(qbits,odd)
        c.add([c.uge_const(qbits,req[t])])
    cnf=out/"problem.cnf"
    write_dimacs(cnf,c.nv,sink.clauses)
    meta={"kind":"exact_coefficient_persistence_cnf",
          "bits":K,"lower":str(A.lower),"upper":str(A.upper),
          "horizon":H,"vars":c.nv,"clauses":len(sink.clauses),
          "build_seconds":time.time()-start,"cnf":cnf.name}
    (out/"metadata.json").write_text(json.dumps(meta,indent=2)+"\n")
    print("CNF_JSON",json.dumps(meta,separators=(",",":")),flush=True)

if __name__=="__main__":
    main()
