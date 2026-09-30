#!/usr/bin/env python3
"""Prospective holdout for the candidate law:
zero newly-exposed source bits at a genuine centre switch => D_next < D_old.

Uses independent q0 RIGID source ranges, not the V53 prospective source family.
Exact arithmetic only. Bounded falsifier; global Collatz remains UNKNOWN.
"""
from __future__ import annotations
from collections import Counter
from fractions import Fraction
import argparse, hashlib, json

import collatz_switch_state_rank_probe as sr

def v2z(x:int):
    x=abs(x)
    if x==0:return None
    return (x & -x).bit_length()-1

def rat_v2(x:Fraction):
    if x==0:return None
    return v2z(x.numerator)-v2z(x.denominator)

def centre(c):
    return Fraction(c["B"],(1<<c["D"])-c["A"])

def audit(lo,hi,K):
    rows=[]; switches=0; same=0; nonincrease=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        by=sr.returns(n,K)
        for anchor,seq in by.items():
            if not seq:continue
            mstart=seq[0][1]
            Abar,Bbar,Pbar=1,0,1
            prev=None
            for c,m0,m1,k0 in seq:
                cc=centre(c)
                pulled=(Pbar*cc-Bbar)/Abar
                p=rat_v2(Fraction(mstart)-pulled)
                if p is None:
                    # exact fixed centre is a separate exceptional branch
                    prev=None
                else:
                    cur={"c":c,"m0":m0,"m1":m1,"k0":k0,"pulled":pulled,"p":p}
                    if prev is not None:
                        if pulled==prev["pulled"]:
                            same+=1
                            assert p==prev["p"]
                        else:
                            switches+=1
                            if p<=prev["p"]:
                                nonincrease.append({
                                  "source":n,"anchor":anchor,
                                  "old_p":prev["p"],"new_p":p,
                                  "old_D":prev["c"]["D"],"new_D":c["D"],
                                  "old_q":prev["c"]["q"],"new_q":c["q"],
                                  "depth":[prev["k0"],k0],
                                })
                            else:
                                loP,hiP=prev["p"],p
                                block=(mstart>>loP)&((1<<(hiP-loP))-1)
                                if block==0:
                                    rows.append({
                                      "source":n,"anchor":anchor,"mstart":mstart,
                                      "old_precision":loP,"new_precision":hiP,
                                      "jump":hiP-loP,
                                      "old_D":prev["c"]["D"],"new_D":c["D"],
                                      "old_q":prev["c"]["q"],"new_q":c["q"],
                                      "old_law":[prev["c"]["A"],prev["c"]["B"],1<<prev["c"]["D"],prev["c"]["D"]],
                                      "new_law":[c["A"],c["B"],1<<c["D"],c["D"]],
                                      "depth":[prev["k0"],k0],
                                      "D_drop":prev["c"]["D"]-c["D"],
                                    })
                    prev=cur
                Abar,Bbar,Pbar=(
                    c["A"]*Abar,
                    c["A"]*Bbar+c["B"]*Pbar,
                    (1<<c["D"])*Pbar,
                )
    bad=[r for r in rows if not r["new_D"]<r["old_D"]]
    qbad=[r for r in rows if not r["new_q"][1] if False]
    return {
      "range":[lo,hi],"K":K,
      "switches":switches,"same_center":same,
      "precision_nonincrease":len(nonincrease),
      "first_precision_nonincrease":nonincrease[:10],
      "zero_exposure_switches":len(rows),
      "D_drop_histogram":dict(sorted(Counter(r["D_drop"] for r in rows).items())),
      "D_drop_failures":len(bad),
      "first_D_drop_failures":bad[:20],
      "first_zero_exposure":rows[:20],
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--K",type=int,default=128)
    a=ap.parse_args()
    train=audit(3,8191,a.K)
    held=audit(8193,32767,a.K)
    result={
      "schema":"COLLATZ_ZERO_EXPOSURE_D_HOLDOUT_20260930",
      "candidate":"zero_exposure => D_next < D_old",
      "train":train,"heldout":held,
      "verdict":(
        "CANDIDATE_SURVIVES_INDEPENDENT_HOLDOUT"
        if train["D_drop_failures"]==0 and held["D_drop_failures"]==0
           and train["precision_nonincrease"]==0 and held["precision_nonincrease"]==0
        else "CANDIDATE_FALSIFIED"
      ),
      "promotion_boundary":"Finite independent exact RIGID corpus only; universal proof still required.",
      "global_collatz":"UNKNOWN",
    }
    result["certificate_sha256"]=hashlib.sha256(
      json.dumps(result,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()
    print(json.dumps(result,indent=2,sort_keys=True,default=str))

if __name__=="__main__":main()
