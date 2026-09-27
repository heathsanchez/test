#!/usr/bin/env python3
"""Exact SAT search for a nontrivial nondescending first coefficient crossing.

Query, for each coefficient-boundary jump depth d in a declared range:

  exists n with 1 < n < 2^d such that
    * coefficient survives at every depth < d,
    * coefficient fails at d (so d is the first crossing),
    * T^d(n) >= n.

The source bound n<2^d is the canonical zero-tail domain already warranted for
a nondescending first crossing by the source-product line.  The query itself is
otherwise exact bit-level shortcut-Collatz arithmetic.

A SAT result is independently replayed in ordinary integers.
An UNSAT result is a bounded solver certificate only; global Collatz remains
UNKNOWN unless the universal tail is separately proved.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from pysat.solvers import Cadical195

from collatz_coefficient_cnf import C, req_odds
from collatz_coefficient_cnf_v2 import worst_widths, step_conditional


def uge_bits(c: C, a, b):
    """Unsigned a >= b. Bit vectors are little-endian literals."""
    w=max(len(a),len(b))
    aa=a+[c.F]*max(0,w-len(a))
    bb=b+[c.F]*max(0,w-len(b))
    gt=c.F
    eq=c.T
    for i in range(w-1,-1,-1):
        ai,bi=aa[i],bb[i]
        gt=c.lor(gt,c.land(eq,c.land(ai,-bi)))
        eq=c.land(eq,-c.xor(ai,bi))
    return c.lor(gt,eq)


def replay_to(n:int,d:int,req):
    x=n
    q=0
    first=None
    bits=[]
    trace=[]
    for t in range(1,d+1):
        bit=x&1
        bits.append(bit)
        x=(3*x+1)//2 if bit else x//2
        q+=bit
        live=q>=req[t]
        trace.append({"t":t,"bit":bit,"q":q,"qmin":req[t],"x":x,"live":live})
        if first is None and not live:
            first=t
    return {"first_crossing":first,"endpoint":x,"q":q,
            "nondescending":x>=n,"bits":"".join(map(str,bits)),
            "tail_trace":trace[-12:]}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-depth",type=int,default=128)
    ap.add_argument("--min-depth",type=int,default=32)
    ap.add_argument("--out",type=Path,required=True)
    A=ap.parse_args()

    H=A.max_depth
    K=H
    req=req_odds(H)
    upper=(1<<K)-1
    widths=worst_widths(upper,H)
    qwidth=(H+1).bit_length()+1

    rows=[]
    start=time.time()

    with Cadical195() as solver:
        c=C(solver)
        seed=[c.var() for _ in range(K)]
        # Nontrivial positive source. Per-depth n<2^d is added as an assumption.
        source_ge_2=c.uge_const(seed,2)

        x=seed+[c.F]*max(0,widths[0]-K)
        qbits=[c.F]*qwidth
        previous_live=[]

        for t in range(1,H+1):
            x,odd=step_conditional(c,x,widths[t])
            qbits=c.inc_if(qbits,odd)
            live=c.uge_const(qbits,req[t])

            # A first crossing can only happen when qmin jumps.
            jump=(t==1 or req[t]>req[t-1])
            if jump and t>=A.min_depth:
                source_lt_2t=c.ule_const(seed,(1<<t)-1)
                endpoint_ge_source=uge_bits(c,x,seed)
                assumptions=[source_ge_2,source_lt_2t,-live,endpoint_ge_source]
                assumptions.extend(previous_live)

                s0=time.time()
                sat=solver.solve(assumptions=assumptions)
                sec=time.time()-s0
                row={
                    "depth":t,
                    "qmin":req[t],
                    "status":"SAT" if sat else "UNSAT",
                    "solve_seconds":sec,
                    "vars":c.nv,
                    "clauses":c.nc,
                    "wall_seconds":time.time()-start,
                }
                if sat:
                    model={v for v in solver.get_model() if v>0}
                    n=sum((1<<i) for i,v in enumerate(seed) if v in model)
                    rep=replay_to(n,t,req)
                    assert 1<n<(1<<t)
                    assert rep["first_crossing"]==t,(n,t,rep)
                    assert rep["endpoint"]>=n,(n,t,rep)
                    row["witness"]=n
                    row["replay"]=rep
                rows.append(row)
                print("QUERY",json.dumps(row,separators=(",",":")),flush=True)

                # The first nontrivial hard crossing is the decisive residual.
                if sat:
                    break

            previous_live.append(live)

    result={
        "schema":"COLLATZ_FIRST_CROSSING_HARD_SAT_V1",
        "min_depth":A.min_depth,
        "max_depth":H,
        "queried_jump_depths":len(rows),
        "rows":rows,
        "status":(
            "EXACT_HARD_FIRST_CROSSING_WITNESS"
            if any(r["status"]=="SAT" for r in rows)
            else "BOUNDED_NO_NONTRIVIAL_HARD_FIRST_CROSSING"
        ),
        "interpretation":(
            "SAT gives an exact canonical nondescending first-crossing source; "
            "UNSAT eliminates the queried canonical depth band only."
        ),
        "global_collatz":"UNKNOWN",
    }
    A.out.parent.mkdir(parents=True,exist_ok=True)
    A.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
