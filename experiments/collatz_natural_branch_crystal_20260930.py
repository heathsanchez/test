#!/usr/bin/env python3
"""Crystal tournament for the exact natural-compatible switch residual.

For each completed same-anchor return sequence, pull every affine fixed centre
back through the already executed return prefix to one fixed natural owner m0.
A genuine centre switch has increasing source-coordinate 2-adic precision.

This tournament tests the exact "natural bar" candidates:
  A. no switch starts after precision has reached bit_length(m0);
  B. no switch lands beyond bit_length(m0);
  C. every newly resolved source-bit block contains a 1;
  D. the highest newly resolved source bit is 1.

C is the strongest useful form: infinitely many switches would force infinitely
many 1 bits in the fixed source coordinate, impossible for an ordinary natural.
Finite passage is discovery only, not a universal theorem.
"""
from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
import io

with redirect_stdout(io.StringIO()):
    import collatz_q0_rigid_recharge_audit as ra

def v2z(x:int):
    x=abs(int(x))
    if x==0:return None
    return (x & -x).bit_length()-1

def rat_v2(x:Fraction):
    if x==0:return None
    return v2z(x.numerator)-v2z(x.denominator)

def centre(c):
    return Fraction(c["B"],(1<<c["D"])-c["A"])

def returns(n,K):
    starts,branches=ra.rigid_episode_segment(n,K)
    cache={};last={};out=defaultdict(list)
    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            start=last[r]
            w=tuple(branches[start:end])
            c=cache.setdefault(w,ra.certificate(w))
            m0=starts[start][2];m1=starts[end][2]
            assert ra.admissible(c,m0)
            assert ra.replay(c,m0)==m1
            out[r].append((c,m0,m1,starts[start][0],starts[end][0]))
        last[r]=end
    return out

def audit(lo,hi,K):
    rows=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        for anchor,seq in returns(n,K).items():
            if len(seq)<2:continue
            mstart=seq[0][1]
            Abar,Bbar,Pbar=1,0,1
            states=[]
            for c,m0,m1,k0,k1 in seq:
                cc=centre(c)
                pulled=(Pbar*cc-Bbar)/Abar
                prec=rat_v2(Fraction(mstart)-pulled)
                assert prec is not None
                states.append((c,m0,m1,k0,k1,pulled,prec))
                Abar,Bbar,Pbar=(
                    c["A"]*Abar,
                    c["A"]*Bbar+c["B"]*Pbar,
                    (1<<c["D"])*Pbar,
                )
            for a,b in zip(states,states[1:]):
                ca,_,_,ka0,ka1,pa,p0=a
                cb,_,_,kb0,kb1,pb,p1=b
                if pa==pb:
                    continue
                assert p1>p0, (n,anchor,mstart,p0,p1,pa,pb)
                bits=mstart.bit_length()
                width=p1-p0
                new_block=(mstart>>p0)&((1<<width)-1)
                highest=(mstart>>(p1-1))&1
                rows.append({
                    "source":n,"anchor":anchor,"owner":mstart,"owner_bits":bits,
                    "old_precision":p0,"new_precision":p1,"jump":width,
                    "new_block":new_block,"highest_new_bit":highest,
                    "old_depth":[ka0,ka1],"new_depth":[kb0,kb1],
                    "old_centre":[pa.numerator,pa.denominator],
                    "new_centre":[pb.numerator,pb.denominator],
                    "old_law":[ca["A"],ca["B"],1<<ca["D"],ca["D"]],
                    "new_law":[cb["A"],cb["B"],1<<cb["D"],cb["D"]],
                })
    tests={
      "OLD_PRECISION_BELOW_OWNER_BITS":lambda z:z["old_precision"]<z["owner_bits"],
      "NEW_PRECISION_AT_MOST_OWNER_BITS":lambda z:z["new_precision"]<=z["owner_bits"],
      "NEW_BLOCK_HAS_ONE":lambda z:z["new_block"]!=0,
      "HIGHEST_NEW_BIT_ONE":lambda z:z["highest_new_bit"]==1,
    }
    out={}
    for name,fn in tests.items():
        bad=[z for z in rows if not fn(z)]
        out[name]={
          "pass":len(rows)-len(bad),"fail":len(bad),
          "first_fail":bad[0] if bad else None,
        }
    hist=Counter(z["jump"] for z in rows)
    beyond=[z for z in rows if z["old_precision"]>=z["owner_bits"]]
    zero_blocks=[z for z in rows if z["new_block"]==0]
    return {
      "range":[lo,hi],"K":K,"switches":len(rows),
      "tests":out,"jump_histogram":dict(sorted(hist.items())),
      "old_precision_beyond_natural_tail":len(beyond),
      "zero_new_bit_blocks":len(zero_blocks),
      "first_tail_switches":beyond[:10],
      "first_zero_blocks":zero_blocks[:10],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--train-lo",type=int,default=3)
    ap.add_argument("--train-hi",type=int,default=8191)
    ap.add_argument("--held-lo",type=int,default=8193)
    ap.add_argument("--held-hi",type=int,default=32767)
    ap.add_argument("--K",type=int,default=128)
    a=ap.parse_args()
    train=audit(a.train_lo,a.train_hi,a.K)
    held=audit(a.held_lo,a.held_hi,a.K)
    candidate="NEW_BLOCK_HAS_ONE"
    verdict=(
      "NATURAL_BIT_BAR_SURVIVES_BOUNDED_TOURNAMENT"
      if train["tests"][candidate]["fail"]==0 and held["tests"][candidate]["fail"]==0
      else "NATURAL_BIT_BAR_FALSIFIED"
    )
    result={
      "schema":"COLLATZ_NATURAL_BRANCH_CRYSTAL_20260930",
      "candidate":candidate,
      "train":train,"heldout":held,
      "verdict":verdict,
      "global_collatz":"UNKNOWN",
    }
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
