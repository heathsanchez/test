#!/usr/bin/env python3
import argparse, json, time
from pathlib import Path
from pysat.solvers import Cadical195
from collatz_coefficient_cnf import C, req_odds, replay

def worst_widths(U,H):
    x=U
    out=[max(1,x.bit_length()+1)]
    for _ in range(H):
        x=(3*x+1)//2
        out.append(max(1,x.bit_length()+1))
    return out

def step_conditional(c,x,wnext):
    """
    Exact shortcut-Collatz step with one full adder.

    Write x=2u+p, p in {0,1}. Then
      p=0: T(x)=u
      p=1: T(x)=3u+2 = u + 2(u+1).
    Build w = p ? (u+1) : 0 using a conditional increment, then y=u+2w.
    """
    p=x[0]
    u=x[1:]
    u=u[:wnext]+[c.F]*max(0,wnext-len(u))

    carry=p
    w=[]
    for ui in u:
        inc=c.xor(ui,carry)
        w.append(c.land(p,inc))
        carry=c.land(ui,carry)

    addend=[c.F]+w[:-1]
    y=c.add2(u,addend,wnext)
    return y,p

def checkpoints(s,H):
    xs=sorted({int(x) for x in s.split(",") if x.strip() and int(x)<=H})
    if H not in xs: xs.append(H)
    return xs

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bits",type=int,required=True)
    ap.add_argument("--lower",type=int,required=True)
    ap.add_argument("--upper",type=int,required=True)
    ap.add_argument("--horizon",type=int,required=True)
    ap.add_argument("--checkpoints",required=True)
    ap.add_argument("--replay-limit",type=int,default=5000)
    ap.add_argument("--out",default="coefficient-v2.json")
    A=ap.parse_args()

    K,H=A.bits,A.horizon
    assert 0<=A.lower<=A.upper<(1<<K)
    cps=checkpoints(A.checkpoints,H); cp=set(cps)
    req=req_odds(H); widths=worst_widths(A.upper,H)
    QW=(H+1).bit_length()+1
    rows=[]; start=time.time()

    with Cadical195() as solver:
        c=C(solver)
        seed=[c.var() for _ in range(K)]
        c.add([c.uge_const(seed,A.lower)])
        c.add([c.ule_const(seed,A.upper)])
        x=seed+[c.F]*max(0,widths[0]-K)
        qbits=[c.F]*QW

        print(f"COEFF_CNF_V2 bits={K} lo={A.lower} hi={A.upper} H={H} w0={widths[0]} wH={widths[-1]}",flush=True)

        for t in range(1,H+1):
            x,odd=step_conditional(c,x,widths[t])
            qbits=c.inc_if(qbits,odd)
            c.add([c.uge_const(qbits,req[t])])

            if t not in cp:
                continue

            s0=time.time(); ok=solver.solve(); sec=time.time()-s0
            row={"horizon":t,"status":"SAT" if ok else "UNSAT",
                 "solve_seconds":sec,"vars":c.nv,"clauses":c.nc,
                 "wall_seconds":time.time()-start}
            if ok:
                model=set(v for v in solver.get_model() if v>0)
                n=sum((1<<i) for i,v in enumerate(seed) if v in model)
                rep=replay(n,A.replay_limit)
                assert A.lower<=n<=A.upper
                assert rep["first_contract"] is None or rep["first_contract"]>t,(n,t,rep)
                row["witness"]=n; row["replay"]=rep
            rows.append(row)
            print("CHECK",json.dumps(row,separators=(",",":")),flush=True)
            if not ok: break

        summary={"kind":"exact_coefficient_persistence_cnf_v2","bits":K,
                 "lower":A.lower,"upper":A.upper,"requested_horizon":H,
                 "width_start":widths[0],"width_end":widths[-1],
                 "results":rows,"status":rows[-1]["status"] if rows else "NO_CHECK",
                 "wall_seconds":time.time()-start}
        Path(A.out).write_text(json.dumps(summary,indent=2)+"\n")
        print("RESULT_JSON",json.dumps(summary,separators=(",",":")),flush=True)

if __name__=="__main__":
    main()
