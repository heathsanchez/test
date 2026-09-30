#!/usr/bin/env python3
"""Crystal cross-anchor test: pull every exact return centre to original source.

For event at source depth k with endpoint x = 2^r*m-1 and local affine return
centre c=B/(2^D-A), endpoint centre is 2^r*c-1.  The exact source prefix
2^k*x = 3^q*n + beta pulls this back to one rational centre in the original
source coordinate.  This makes centres from different anchors comparable.

Test whether chronological return-event centres form strictly improving
2-adic approximants to the fixed original natural source.
Bounded discovery only.
"""
from __future__ import annotations
import argparse,json
from collections import defaultdict,Counter
from fractions import Fraction
from contextlib import redirect_stdout
import io

with redirect_stdout(io.StringIO()):
    import collatz_q0_rigid_recharge_audit as ra
    import collatz_q0_coalescence_component_audit as base

def v2z(x:int):
    x=abs(int(x))
    if x==0:return None
    return (x&-x).bit_length()-1
def rv2(x:Fraction):
    if x==0:return None
    return v2z(x.numerator)-v2z(x.denominator)
def centre(c):
    return Fraction(c["B"],(1<<c["D"])-c["A"])

def returns(n,K):
    starts,branches=ra.rigid_episode_segment(n,K)
    cache={};last={};events=[]
    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            st=last[r];word=tuple(branches[st:end])
            c=cache.setdefault(word,ra.certificate(word))
            k0=starts[st][0];k1=starts[end][0]
            m0=starts[st][2];m1=starts[end][2]
            assert ra.admissible(c,m0) and ra.replay(c,m0)==m1
            q,x=base.forward_state(k0,n)
            assert x==(1<<r)*m0-1
            beta=(1<<k0)*x-(3**q)*n
            assert beta>=0
            local=centre(c)
            endpoint=(1<<r)*local-1
            pulled=((1<<k0)*endpoint-beta)/(3**q)
            precision=rv2(Fraction(n)-pulled)
            assert precision is not None
            events.append({
              "anchor":r,"k0":k0,"k1":k1,"m0":m0,
              "law":[c["r"],c["A"],c["B"],c["D"]],
              "pulled":pulled,"precision":precision,
            })
        last[r]=end
    events.sort(key=lambda e:(e["k0"],e["k1"],e["anchor"],e["law"]))
    return events

def audit(lo,hi,K):
    rows=[];duplicates=0;sources=0;noevents=0
    new_anchor_rows=[]
    for n in range(max(3,lo)+(max(3,lo)%2==0),hi+1,2):
        ev=returns(n,K)
        if not ev:
            noevents+=1;continue
        sources+=1
        # collapse identical pulled centres at same or later starts
        for a,b in zip(ev,ev[1:]):
            if a["pulled"]==b["pulled"]:
                duplicates+=1;continue
            rows.append({
              "source":n,
              "old_anchor":a["anchor"],"new_anchor":b["anchor"],
              "same_anchor":a["anchor"]==b["anchor"],
              "old_k":a["k0"],"new_k":b["k0"],
              "old_precision":a["precision"],"new_precision":b["precision"],
              "delta":b["precision"]-a["precision"],
              "old_law":a["law"],"new_law":b["law"],
              "old_pulled":[a["pulled"].numerator,a["pulled"].denominator],
              "new_pulled":[b["pulled"].numerator,b["pulled"].denominator],
            })
        seen=set()
        for e in ev:
            if e["anchor"] not in seen:
                new_anchor_rows.append((n,e["k0"],e["anchor"],e["precision"]))
                seen.add(e["anchor"])
    same=[z for z in rows if z["same_anchor"]]
    cross=[z for z in rows if not z["same_anchor"]]
    def stat(zs):
        bad=[z for z in zs if z["new_precision"]<=z["old_precision"]]
        return {
          "rows":len(zs),
          "strict_increase":len(zs)-len(bad),
          "fail":len(bad),
          "first_fail":bad[0] if bad else None,
          "delta_histogram":dict(sorted(Counter(z["delta"] for z in zs).items())),
        }
    return {
      "range":[lo,hi],"K":K,"sources_with_events":sources,"sources_without_events":noevents,
      "duplicate_pulled_centres":duplicates,
      "all":stat(rows),"same_anchor":stat(same),"cross_anchor":stat(cross),
      "new_anchor_occurrences":len(new_anchor_rows),
      "max_anchor":max((x[2] for x in new_anchor_rows),default=None),
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--K",type=int,default=128);a=ap.parse_args()
    tr=audit(3,8191,a.K);ho=audit(8193,32767,a.K)
    ok=tr["all"]["fail"]==0 and ho["all"]["fail"]==0
    print(json.dumps({
      "schema":"COLLATZ_GLOBAL_SOURCE_CENTRE_CRYSTAL_20260930",
      "train":tr,"heldout":ho,
      "verdict":"GLOBAL_PULLED_PRECISION_SURVIVES_BOUNDED" if ok else "CROSS_ANCHOR_PRECISION_FALSIFIED",
      "global_collatz":"UNKNOWN"
    },indent=2,default=str))
if __name__=="__main__":main()
