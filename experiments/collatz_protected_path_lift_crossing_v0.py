#!/usr/bin/env python3
"""Path-lift depth-20 protected source cylinders to their first coefficient crossing.

A depth-20 V3 survivor is not identified with a crossing state.  We extend its
source parity cylinder exactly, carrying q and affine bias B.  A branch stops at
its first k with 3^q < 2^k.  At that point the Lean-verified necessary condition
for a nondescending source is M = B-(2^k-3^q)R >= 0, where R is the source
residue mod 2^k.  M<0 certifies closure of that crossing cylinder.

Finite-prefix audit only: if live prefixes remain at max depth, verdict UNKNOWN.
"""
import argparse,json
from pathlib import Path
import collatz_reverse_trit_bicell_v3_quotient as v3
import collatz_reverse_trit_bicell_v2 as v2

START=20

def affine(r,k):
    A,B,_=v2.forward_affine(r,k)
    q=0;z=A
    while z>1:
        assert z%3==0;z//=3;q+=1
    return q,B

def run(max_depth,out):
    parents,langs,_=v3.evolve(START)
    sets=[set(langs[START][i]) for i in range(len(parents))]
    assert all(s==sets[0] for s in sets)
    live=set(sets[0])
    rows=[]
    # Verify all starting states are genuinely pre-crossing.
    qhist={}
    for r in live:
        q,B=affine(r,START)
        qhist[q]=qhist.get(q,0)+1
        assert (1<<START) <= 3**q

    for k in range(START+1,max_depth+1):
        bit=1<<(k-1)
        expanded={x for r in live for x in (r,r|bit)}
        nxt=set(); crossed=closed=margin_live=0
        minM=None; examples=[]
        for R in expanded:
            q,B=affine(R,k)
            if (1<<k) > 3**q:
                crossed+=1
                M=B-((1<<k)-3**q)*R
                minM=M if minM is None else min(minM,M)
                if M < 0:
                    closed+=1
                else:
                    margin_live+=1
                    if len(examples)<20:
                        examples.append({"k":k,"q":q,"R":R,"B":B,"M":M})
            else:
                nxt.add(R)
        live=nxt
        row={"depth":k,"expanded":len(expanded),"first_crossings":crossed,
             "closed_M_negative":closed,"crossing_M_nonnegative":margin_live,
             "pre_crossing_live":len(live),"min_M":minM,
             "M_nonnegative_examples":examples}
        rows.append(row);print("DEPTH",json.dumps(row,sort_keys=True))
        # Any M>=0 crossing is the exact canonical obstruction; stop immediately.
        if margin_live:
            break
        if not live:
            break

    result={"schema":"COLLATZ_PROTECTED_PATH_LIFT_TO_FIRST_CROSSING_V0",
      "start_depth":START,"start_states":len(sets[0]),"start_q_histogram":qhist,
      "max_depth":max_depth,"rows":rows,
      "status":("EXACT_M_NONNEGATIVE_CROSSING_OBSTRUCTION" if rows and rows[-1]["crossing_M_nonnegative"]
                else "BOUNDED_ALL_CLOSED" if not live else "UNKNOWN_DEPTH_LIMIT"),
      "remaining_pre_crossing":len(live),
      "global_collatz":"UNKNOWN"}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+"\n")
    print("STATUS",result["status"],"REMAINING",len(live))

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--max-depth",type=int,default=64)
    ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
    run(a.max_depth,a.output)
