#!/usr/bin/env python3
"""
Exact maximum coefficient-persistence frontier over a finite seed interval.

Build the shortcut-Collatz transition circuit once through Hmax.  Prefix
persistence constraints are literals, not hard clauses, so CaDiCaL can
answer different horizons under assumptions while retaining learned clauses.
If Hmax is UNSAT, binary search finds the exact SAT/UNSAT boundary.
"""
import argparse, json, time
from pathlib import Path
from pysat.solvers import Cadical195
from collatz_coefficient_cnf import C, req_odds, replay
from collatz_coefficient_cnf_v2 import worst_widths, step_conditional

def solve_horizon(solver, ok_lits, h):
    t0=time.time()
    sat=solver.solve(assumptions=ok_lits[:h])
    return sat, time.time()-t0

def model_seed(solver, seed):
    model={v for v in solver.get_model() if v>0}
    return sum((1<<i) for i,v in enumerate(seed) if v in model)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bits",type=int,required=True)
    ap.add_argument("--lower",type=int,required=True)
    ap.add_argument("--upper",type=int,required=True)
    ap.add_argument("--max-horizon",type=int,required=True)
    ap.add_argument("--replay-limit",type=int,default=10000)
    ap.add_argument("--out",default="coefficient-frontier.json")
    A=ap.parse_args()

    K,H=A.bits,A.max_horizon
    assert 0<=A.lower<=A.upper<(1<<K)
    req=req_odds(H)
    widths=worst_widths(A.upper,H)
    qwidth=(H+1).bit_length()+1
    rows=[]
    start=time.time()

    with Cadical195() as solver:
        c=C(solver)
        seed=[c.var() for _ in range(K)]
        c.add([c.uge_const(seed,A.lower)])
        c.add([c.ule_const(seed,A.upper)])
        x=seed+[c.F]*max(0,widths[0]-K)
        qbits=[c.F]*qwidth
        ok=[]

        for t in range(1,H+1):
            x,odd=step_conditional(c,x,widths[t])
            qbits=c.inc_if(qbits,odd)
            ok.append(c.uge_const(qbits,req[t]))

        build_seconds=time.time()-start
        sat_hi,sec=solve_horizon(solver,ok,H)
        row={"horizon":H,"status":"SAT" if sat_hi else "UNSAT","solve_seconds":sec}
        if sat_hi:
            n=model_seed(solver,seed)
            rep=replay(n,A.replay_limit)
            assert A.lower<=n<=A.upper
            assert rep["first_contract"] is None or rep["first_contract"]>H,(n,H,rep)
            row["witness"]=str(n); row["replay"]=rep
        rows.append(row)
        print("QUERY",json.dumps(row,separators=(",",":")),flush=True)

        if sat_hi:
            summary={
                "kind":"exact_coefficient_frontier",
                "bits":K,"lower":str(A.lower),"upper":str(A.upper),
                "max_horizon":H,"closed":False,
                "survives_max_horizon":True,
                "witness":row["witness"],"replay":row["replay"],
                "vars":c.nv,"clauses":c.nc,
                "build_seconds":build_seconds,"queries":rows,
                "wall_seconds":time.time()-start,
            }
        else:
            lo=0
            hi=H
            while hi-lo>1:
                mid=(lo+hi)//2
                sat,sec=solve_horizon(solver,ok,mid)
                row={"horizon":mid,"status":"SAT" if sat else "UNSAT","solve_seconds":sec}
                if sat:
                    n=model_seed(solver,seed)
                    rep=replay(n,A.replay_limit)
                    assert A.lower<=n<=A.upper
                    assert rep["first_contract"] is None or rep["first_contract"]>mid,(n,mid,rep)
                    row["witness"]=str(n); row["replay"]=rep
                    lo=mid
                else:
                    hi=mid
                rows.append(row)
                print("QUERY",json.dumps(row,separators=(",",":")),flush=True)

            sat,sec=solve_horizon(solver,ok,lo)
            assert sat
            n=model_seed(solver,seed)
            rep=replay(n,A.replay_limit)
            assert rep["first_contract"]==hi,(n,lo,hi,rep)
            final={"horizon":lo,"status":"SAT","solve_seconds":sec,
                   "witness":str(n),"replay":rep}
            rows.append(final)
            print("BOUNDARY",json.dumps(final,separators=(",",":")),
                  "FIRST_UNSAT",hi,flush=True)
            summary={
                "kind":"exact_coefficient_frontier",
                "bits":K,"lower":str(A.lower),"upper":str(A.upper),
                "max_horizon":H,"closed":True,
                "last_sat_horizon":lo,
                "first_unsat_horizon":hi,
                "extremal_seed":str(n),
                "extremal_replay":rep,
                "vars":c.nv,"clauses":c.nc,
                "build_seconds":build_seconds,"queries":rows,
                "wall_seconds":time.time()-start,
            }

    Path(A.out).write_text(json.dumps(summary,indent=2)+"\n")
    print("RESULT_JSON",json.dumps(summary,separators=(",",":")),flush=True)

if __name__=="__main__":
    main()
