#!/usr/bin/env python3
"""
Exact low-bit partition for coefficient persistence.

The first k seed bits determine the earliest shortcut-Collatz dynamics.
Build one exact H-step CNF, then cover every low-k residue under SAT
assumptions, reusing CaDiCaL's learned clauses across residues.
"""
import argparse, json, time
from pathlib import Path
from pysat.solvers import Cadical195
from collatz_coefficient_cnf import C, req_odds, replay
from collatz_coefficient_cnf_v2 import worst_widths, step_conditional

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bits",type=int,required=True)
    ap.add_argument("--lower",type=int,required=True)
    ap.add_argument("--upper",type=int,required=True)
    ap.add_argument("--horizon",type=int,required=True)
    ap.add_argument("--split-bits",type=int,default=4)
    ap.add_argument("--replay-limit",type=int,default=10000)
    ap.add_argument("--out",default="coefficient-residue-split.json")
    A=ap.parse_args()

    K,H,k=A.bits,A.horizon,A.split_bits
    assert 1<=k<=K
    assert 0<=A.lower<=A.upper<(1<<K)
    req=req_odds(H)
    widths=worst_widths(A.upper,H)
    qwidth=(H+1).bit_length()+1
    start=time.time()
    rows=[]

    with Cadical195() as solver:
        c=C(solver)
        seed=[c.var() for _ in range(K)]
        c.add([c.uge_const(seed,A.lower)])
        c.add([c.ule_const(seed,A.upper)])
        x=seed+[c.F]*max(0,widths[0]-K)
        qbits=[c.F]*qwidth

        for t in range(1,H+1):
            x,odd=step_conditional(c,x,widths[t])
            qbits=c.inc_if(qbits,odd)
            c.add([c.uge_const(qbits,req[t])])

        build_seconds=time.time()-start
        print("BUILD",json.dumps({"vars":c.nv,"clauses":c.nc,
              "seconds":build_seconds,"split_bits":k}),flush=True)

        all_unsat=True
        for residue in range(1<<k):
            assumptions=[]
            for i in range(k):
                assumptions.append(seed[i] if ((residue>>i)&1) else -seed[i])
            s0=time.time()
            sat=solver.solve(assumptions=assumptions)
            sec=time.time()-s0
            row={"residue":residue,"modulus":1<<k,
                 "status":"SAT" if sat else "UNSAT",
                 "solve_seconds":sec}
            if sat:
                all_unsat=False
                model={v for v in solver.get_model() if v>0}
                n=sum((1<<i) for i,v in enumerate(seed) if v in model)
                rep=replay(n,A.replay_limit)
                assert A.lower<=n<=A.upper
                assert n%(1<<k)==residue
                assert rep["first_contract"] is None or rep["first_contract"]>H,(n,H,rep)
                row["witness"]=str(n); row["replay"]=rep
            rows.append(row)
            print("RESIDUE",json.dumps(row,separators=(",",":")),flush=True)

        summary={
            "kind":"exact_coefficient_low_bit_partition",
            "bits":K,"lower":str(A.lower),"upper":str(A.upper),
            "horizon":H,"split_bits":k,
            "coverage_classes":1<<k,
            "status":"UNSAT" if all_unsat else "SAT",
            "all_classes_unsat":all_unsat,
            "vars":c.nv,"clauses":c.nc,
            "build_seconds":build_seconds,
            "rows":rows,"wall_seconds":time.time()-start,
        }
    Path(A.out).write_text(json.dumps(summary,indent=2)+"\n")
    print("RESULT_JSON",json.dumps(summary,separators=(",",":")),flush=True)

if __name__=="__main__":
    main()
