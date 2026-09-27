#!/usr/bin/env python3
"""Adversarial finite audit of the zero-loss-tail residual.

Tests the exact live-origin recurrence P[j-1,m] = P[j,m] + C[j,m].
For every positive tested live state, measure the longest consecutive future
interval with C=0 before the next strict loss. This is a falsifier for P as a
natural-valued progress resource; it is not a universal proof.
"""
import argparse, json
from collatz_live_origin_bridge_v1 import language_counts, first_crossing

def audit(bits:int, depth:int, start:int):
    qmin,_,_=language_counts(depth)
    hist=[[0]*(bits+1) for _ in range(depth+1)]
    unresolved=0
    for n in range(1,1<<bits,2):
        z=first_crossing(n,qmin)
        if z is None:
            unresolved += 1
        else:
            j,_,_=z
            hist[j][n.bit_length()] += 1
    C=[[0]*(bits+1) for _ in range(depth+1)]
    P=[[0]*(bits+1) for _ in range(depth+1)]
    for j in range(1,depth+1):
        for m in range(1,bits+1):
            C[j][m]=C[j][m-1]+hist[j][m]
    for m in range(1,bits+1):
        P[0][m]=1<<(m-1)
        for j in range(1,depth+1):
            P[j][m]=P[j-1][m]-C[j][m]
            assert P[j][m] >= 0
            assert P[j-1][m] == P[j][m] + C[j][m]

    checked=0
    censored=[]
    records=[]
    max_wait=-1
    worst=None
    for j in range(start,depth):
        for m in range(1,bits+1):
            if P[j][m] <= 0:
                continue
            checked += 1
            r=j+1
            while r<=depth and C[r][m]==0:
                r+=1
            if r>depth:
                censored.append({"j":j,"m":m,"P":P[j][m],
                                 "remaining_horizon":depth-j})
                continue
            wait=r-j
            assert C[r][m] > 0
            assert P[r][m] < P[j][m]
            rec={"j":j,"m":m,"P":P[j][m],"next_loss_depth":r,
                 "wait":wait,"loss":C[r][m],"P_after":P[r][m]}
            if wait>max_wait:
                max_wait=wait; worst=rec
            records.append(rec)

    # Maximal zero-loss plateaus, deduplicated by their start immediately after
    # a loss (or at start). These are the adversarial objects for the next split.
    plateaus=[]
    for m in range(1,bits+1):
        j=start
        while j<depth:
            if P[j][m]<=0:
                j+=1; continue
            if j>start and C[j][m]==0:
                j+=1; continue
            r=j+1
            while r<=depth and C[r][m]==0:
                r+=1
            if r<=depth:
                plateaus.append({"m":m,"j":j,"P":P[j][m],
                    "zero_loss_steps":r-j-1,"next_loss_depth":r,
                    "next_loss":C[r][m]})
            j=max(j+1,r)
    plateaus.sort(key=lambda x:(-x["zero_loss_steps"],-x["j"],-x["m"]))

    return {
      "schema":"COLLATZ_CRYSTAL_ZERO_LOSS_TAIL_V1",
      "source_bits":bits,"depth":depth,"start_depth":start,
      "checked_positive_states":checked,
      "unresolved_sources_at_horizon":unresolved,
      "states_censored_without_future_loss":len(censored),
      "first_censored":censored[:20],
      "max_wait_to_strict_loss":max_wait,
      "worst_wait":worst,
      "longest_zero_loss_plateaus":plateaus[:40],
      "status":"FINITE_NO_ZERO_LOSS_TAIL_OBSERVED" if not censored else "FINITE_HORIZON_CENSORED",
      "candidate_resource":"P_j(X) in Nat",
      "universal_target":"P_j(X)>0 -> exists b>0, P_(j+b)(X)<P_j(X)",
      "global_collatz":"UNKNOWN"
    }

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-bits",type=int,default=20)
    ap.add_argument("--depth",type=int,default=1024)
    ap.add_argument("--start-depth",type=int,default=60)
    a=ap.parse_args()
    print(json.dumps(audit(a.source_bits,a.depth,a.start_depth),indent=2))
