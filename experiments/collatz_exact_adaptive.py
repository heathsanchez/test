#!/usr/bin/env python3
import argparse, json, time
from pathlib import Path
from pysat.solvers import Cadical195
from collatz_exact_cnf_even import Circuit, worst_widths, replay

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bits",type=int,required=True)
    ap.add_argument("--lower",type=int,required=True)
    ap.add_argument("--upper",type=int,required=True)
    ap.add_argument("--start-horizon",type=int,required=True)
    ap.add_argument("--max-horizon",type=int,default=1000)
    ap.add_argument("--min-jump",type=int,default=16)
    ap.add_argument("--replay-limit",type=int,default=5000)
    ap.add_argument("--out",default="adaptive.json")
    A=ap.parse_args()
    K=A.bits
    assert 0<=A.lower<=A.upper<(1<<K)
    assert 1<=A.start_horizon<=A.max_horizon

    widths=worst_widths(A.upper,A.max_horizon)
    results=[]
    start=time.time()
    next_check=A.start_horizon

    with Cadical195() as solver:
        C=Circuit(solver)
        seed=[C.var() for _ in range(K)]
        C.add([C.uge_const(seed,A.lower)])
        C.add([C.ule_const(seed,A.upper)])
        x=list(seed)

        print(
            f"ADAPTIVE_EXACT bits={K} lower={A.lower} upper={A.upper} "
            f"start={A.start_horizon} max={A.max_horizon}",
            flush=True,
        )

        for t in range(1,A.max_horizon+1):
            p=x[0]
            u=x[1:]

            # Exact no-descent constraint. First descent can only occur when
            # the current iterate is even, because an odd shortcut step
            # (3x+1)/2 is strictly greater than x for x>1.
            low=u[:K]+[C.F]*max(0,K-len(u))
            low_ge=C.uge_bits(low,seed)
            high=u[K:] if len(u)>K else []
            C.add([p,low_ge]+high)

            ow=widths[t]
            uu=u[:ow]+[C.F]*max(0,ow-len(u))
            twice=([C.F]+u)[:ow]
            twice=twice+[C.F]*max(0,ow-len(twice))
            odd=C.add_const(C.add2(uu,twice,ow),2,ow)
            x=[C.mux(p,uu[i],odd[i]) for i in range(ow)]

            if t != next_check:
                continue

            s0=time.time()
            ok=solver.solve()
            sec=time.time()-s0
            row={
                "horizon":t,
                "status":"SAT" if ok else "UNSAT",
                "solve_seconds":sec,
                "vars":C.nv,
                "clauses":C.nc,
                "wall_seconds":time.time()-start,
            }

            if not ok:
                results.append(row)
                print("CHECK",json.dumps(row,separators=(",",":")),flush=True)
                break

            model=set(v for v in solver.get_model() if v>0)
            n=sum((1<<i) for i,v in enumerate(seed) if v in model)
            rep=replay(n,A.replay_limit)
            fd=rep["first_descent"]
            assert A.lower<=n<=A.upper
            assert fd is None or fd>t,(n,t,rep)
            row["witness"]=n
            row["replay"]=rep
            results.append(row)
            print("CHECK",json.dumps(row,separators=(",",":")),flush=True)

            if t>=A.max_horizon:
                break

            # Witness-guided leap. The SAT witness proves the current
            # horizon is too low; its exact first descent tells us the
            # smallest horizon at which that witness itself disappears.
            candidate=t+A.min_jump
            if fd is not None:
                candidate=max(candidate,fd+1)
            next_check=min(A.max_horizon,candidate)
            print(f"NEXT_CHECK {next_check}",flush=True)

        status=results[-1]["status"] if results else "NO_CHECK"
        summary={
            "kind":"adaptive_exact_even_step_cnf_no_descent",
            "bits":K,
            "lower":A.lower,
            "upper":A.upper,
            "start_horizon":A.start_horizon,
            "max_horizon":A.max_horizon,
            "min_jump":A.min_jump,
            "status":status,
            "results":results,
            "wall_seconds":time.time()-start,
        }
        Path(A.out).write_text(json.dumps(summary,indent=2)+"\n")
        print("RESULT_JSON",json.dumps(summary,separators=(",",":")),flush=True)

if __name__=="__main__":
    main()
