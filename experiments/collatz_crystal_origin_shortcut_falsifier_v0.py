#!/usr/bin/env python3
"""Exact symbolic falsifier for the proposed origin shortcut:
nondescending first crossing => source residue R > q.

Enumerates the source-product first-crossing language exactly, with one state
per canonical source residue R mod 2^j. No floating point; no sampled sources.
"""
import argparse, json
from collatz_live_origin_bridge_v1 import language_counts

def shortcut_from_parity(z, bit):
    return (3*z+1)//2 if bit else z//2

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--depth",type=int,default=24)
    A=ap.parse_args()
    qmin,live,_=language_counts(A.depth)
    states=[(0,0,0)] # q,R,Y at current depth
    rows=[]; bad=[]
    for j in range(1,A.depth+1):
        nxt=[]; leaves=0; nd=0; nd_R_le_q=0; examples=[]
        scale=1<<(j-1)
        for q,R,Y in states:
            for bit in (0,1):
                lift=(bit-Y)&1
                Rp=R+lift*scale
                z=Y+(3**q)*lift
                assert (z&1)==bit
                Yp=shortcut_from_parity(z,bit)
                qp=q+bit
                if qp<qmin[j]:
                    leaves+=1
                    if Rp>1 and Yp>=Rp:
                        nd+=1
                        if Rp<=qp:
                            nd_R_le_q+=1
                            ex={"depth":j,"source":Rp,"q":qp,"endpoint":Yp,
                                "gap":Yp-Rp}
                            if len(examples)<20: examples.append(ex)
                            if len(bad)<100: bad.append(ex)
                else:
                    nxt.append((qp,Rp,Yp))
        assert len(nxt)==live[j]
        rows.append({"depth":j,"live":len(nxt),"leaves":leaves,
                     "nondescending_first_crossings":nd,
                     "nondescending_with_R_le_q":nd_R_le_q,
                     "examples":examples})
        states=nxt
    print(json.dumps({
      "schema":"COLLATZ_CRYSTAL_ORIGIN_SHORTCUT_FALSIFIER_V0",
      "depth":A.depth,
      "candidate":"nondescending first crossing with source R>1 implies R>q",
      "counterexamples":bad,
      "status":"FINITE_EXACT_FALSIFIER",
      "global_collatz":"UNKNOWN",
      "rows":rows},indent=2))
if __name__=="__main__": main()
