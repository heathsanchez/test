#!/usr/bin/env python3
"""Tournament: does every genuine affine-centre switch expose a new 1-bit?

For each exact V53 residual streak, pull every active affine fixed centre back
to the one fixed starting owner m0, exactly as V60.  A switch raises the
2-adic precision p = v2(m0-C).  If p_old < p_new, then bits
[p_old, p_new) of the ordinary natural m0 have just become fixed by the new
centre.

Candidate natural-bar mechanism:
    every genuine centre switch fixes at least one NEW 1-bit of m0.

If universal, infinitely many switches would force infinitely many 1-bits in
one ordinary natural integer, impossible.  This script is bounded theorem
discovery only.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib, json

import collatz_crystal_nonpositive_budget_kernel_v53 as v53

def v2z(x:int):
    x=abs(x)
    if x==0:return None
    return (x & -x).bit_length()-1

def rat_v2(x:Fraction):
    if x==0:return None
    return v2z(x.numerator)-v2z(x.denominator)

def centre(s):
    return Fraction(s["B"],s["P"]-s["A"])

groups=defaultdict(list)
for tr in v53.transitions:
    if tr["src"]["residual"] and tr["kind"]=="RESIDUAL":
        groups[(tr["source"],tr["anchor"])].append(tr)
for g in groups.values():
    g.sort(key=lambda tr:(tr["src"]["k0"],tr["src"]["k1"]))

switch_rows=[]
same_rows=[]
for (source,anchor),trs in groups.items():
    chunks=[];cur=[]
    for tr in trs:
        if cur and cur[-1]["dst"]["k0"]!=tr["src"]["k0"]:
            chunks.append(cur);cur=[]
        cur.append(tr)
    if cur:chunks.append(cur)

    for chunk in chunks:
        states=[chunk[0]["src"]]+[tr["dst"] for tr in chunk]
        m0=states[0]["m0"]
        Abar,Bbar,Pbar=1,0,1
        prev=None
        for i,s in enumerate(states):
            c=centre(s)
            pulled=(Pbar*c-Bbar)/Abar
            p=rat_v2(Fraction(m0)-pulled)
            assert p is not None and p>=0
            row={
                "source":source,"anchor":anchor,"m0":m0,"state_index":i,
                "depth":[s["k0"],s["k1"]],
                "local_center":[c.numerator,c.denominator],
                "pulled_center":[pulled.numerator,pulled.denominator],
                "precision":p,
                "law":[s["A"],s["B"],s["P"],s["D"]],
            }
            if prev is not None:
                if pulled==prev["pulled"]:
                    assert p==prev["precision"]
                    same_rows.append((prev,row))
                else:
                    assert p>prev["precision"], (prev,row)
                    lo,hi=prev["precision"],p
                    width=hi-lo
                    mask=(1<<width)-1
                    block=(m0>>lo)&mask
                    switch_rows.append({
                        "source":source,"anchor":anchor,"m0":m0,
                        "old_precision":lo,"new_precision":hi,"jump":width,
                        "new_bit_block":block,
                        "new_bit_popcount":block.bit_count(),
                        "all_new_bits_zero":block==0,
                        "top_new_bit":(m0>>(hi-1))&1,
                        "old":prev,"new":row,
                    })
            prev={**row,"pulled":pulled}
            Abar,Bbar,Pbar=(
                s["A"]*Abar,
                s["A"]*Bbar+s["B"]*Pbar,
                s["P"]*Pbar,
            )

assert switch_rows
zero=[r for r in switch_rows if r["all_new_bits_zero"]]
topzero=[r for r in switch_rows if r["top_new_bit"]==0]
hist_jump=Counter(r["jump"] for r in switch_rows)
hist_pop=Counter(r["new_bit_popcount"] for r in switch_rows)

# A separate eventually-zero diagnostic: after the highest set bit of m0,
# no future precision increase can expose a 1.  Record how close observed
# switch precision gets to that hard natural ceiling.
ceiling_rows=[]
for r in switch_rows:
    ceiling=r["m0"].bit_length()
    ceiling_rows.append(ceiling-r["new_precision"])
past_or_at=sum(x<=0 for x in ceiling_rows)

result={
 "schema":"COLLATZ_SWITCH_NEWBIT_TOURNAMENT_20260930",
 "parent":"collatz-source-pulled-centre qualification run 36668941287",
 "switches":len(switch_rows),
 "same_center_steps":len(same_rows),
 "jump_histogram":dict(sorted(hist_jump.items())),
 "new_bit_popcount_histogram":dict(sorted(hist_pop.items())),
 "all_new_bits_zero_count":len(zero),
 "first_all_zero_new_bit_blocks":zero[:20],
 "top_new_bit_zero_count":len(topzero),
 "first_top_new_bit_zero":topzero[:20],
 "switches_reaching_or_passing_natural_bitlength":past_or_at,
 "minimum_bitlength_minus_new_precision":min(ceiling_rows),
 "maximum_bitlength_minus_new_precision":max(ceiling_rows),
 "verdict":"EVERY_SWITCH_EXPOSES_NEW_ONE_BIT" if not zero else "NEW_ONE_BIT_CANDIDATE_FALSIFIED",
 "interpretation":(
   "If every switch universally exposed a previously unseen 1-bit of the fixed "
   "ordinary owner, infinitely many switches would be impossible because a "
   "natural integer has only finitely many 1-bits. Any all-zero newly exposed "
   "block is an exact separator against that proposed natural-bar theorem."
 ),
 "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(
 json.dumps(result,sort_keys=True,separators=(",",":"),default=str).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True,default=str))
