#!/usr/bin/env python3
"""Compile the depth-20 protected language into the exact coefficient CNF.

Instead of enumerating all descendants, add one selector clause saying the
low 20 source bits are one of the already-qualified protected V3 survivors,
then use the retained coefficient-persistence transition circuit.  Query
successive horizons under assumptions to find whether any protected lineage
can remain pre-crossing.

Bounded symbolic experiment; SAT at the maximum horizon is UNKNOWN globally.
"""
import argparse,json,time
from pathlib import Path
from pysat.solvers import Cadical195
from collatz_coefficient_cnf import C,req_odds,replay
from collatz_coefficient_cnf_v2 import worst_widths,step_conditional
import collatz_reverse_trit_bicell_v3_quotient as v3

BASE=20

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--bits",type=int,default=48)
    ap.add_argument("--horizon",type=int,default=128);ap.add_argument("--out",required=True)
    A=ap.parse_args();K=A.bits;H=A.horizon
    parents,langs,_=v3.evolve(BASE)
    sets=[set(langs[BASE][i]) for i in range(len(parents))]
    assert all(s==sets[0] for s in sets)
    protected=sorted(sets[0])

    # upper is all K-bit seeds; widths are exact safe widths for that domain.
    U=(1<<K)-1; req=req_odds(H); widths=worst_widths(U,H)
    qwidth=(H+1).bit_length()+1; start=time.time()
    with Cadical195() as solver:
        c=C(solver);seed=[c.var() for _ in range(K)]
        # DNF selector for the qualified low-20 language.
        sels=[]
        for r in protected:
            z=c.var();sels.append(z)
            for i in range(BASE):
                c.add([-z, seed[i] if ((r>>i)&1) else -seed[i]])
        c.add(sels)
        # Ensure any selected low-20 assignment has some selector true;
        # selector -> pattern plus OR selectors is sufficient since patterns are distinct.
        x=seed+[c.F]*max(0,widths[0]-K)
        qbits=[c.F]*qwidth;ok=[]
        for t in range(1,H+1):
            x,odd=step_conditional(c,x,widths[t]);qbits=c.inc_if(qbits,odd)
            ok.append(c.uge_const(qbits,req[t]))

        # Query only consequential depths, exponentially then binary if closure appears.
        queries=[]; depths=[32,48,64,96,H]
        seen=set()
        for h in depths:
            if h>H or h in seen:continue
            seen.add(h);t=time.time();sat=solver.solve(assumptions=ok[:h]);sec=time.time()-t
            row={"horizon":h,"sat":sat,"seconds":sec}
            if sat:
                model={v for v in solver.get_model() if v>0}
                n=sum((1<<i) for i,v in enumerate(seed) if v in model)
                row["witness"]=n;row["low20"]=n&((1<<20)-1)
                row["replay"]=replay(n,max(H+100,500))
            queries.append(row);print("QUERY",json.dumps(row,separators=(",",":")),flush=True)
            if not sat:break
        result={"schema":"COLLATZ_PROTECTED_COEFFICIENT_CNF_V0",
          "seed_bits":K,"protected_low20_count":len(protected),"requested_horizon":H,
          "queries":queries,
          "status":("BOUNDED_CLOSED" if queries and not queries[-1]["sat"] else "UNKNOWN_SAT_FRONTIER"),
          "global_collatz":"UNKNOWN","wall_seconds":time.time()-start}
        Path(A.out).parent.mkdir(parents=True,exist_ok=True);Path(A.out).write_text(json.dumps(result,indent=2)+"\n")
        print("STATUS",result["status"])
if __name__=="__main__":main()
