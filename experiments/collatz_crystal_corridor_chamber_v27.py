#!/usr/bin/env python3
"""Crystal V27: exact 110/-5 corridor -> 12/19 chamber join.

Parent authority:
  collatz-crystal-post-p36-adversary-v26@9c68bf8f64f83ac90aa892157bd24806b511ec06

V26 proved a natural source can shadow the 2-adic parity cycle (110)^m
arbitrarily far on the current bounded evidence, so raw parameter depth is not
a proof state.  V27 composes that exact 2-adic corridor with the already-earned
12-odd / <=19 reverse chamber.

The 2-adic cycle is
  -5 --odd--> -7 --odd--> -10 --even--> -5.
For every a>0,
  T^3(8*a-5)=9*a-5.
Hence a natural positive source can shadow the cycle for a finite number of
blocks, but its first deviation is one of only three phase deviations.

Modulo 3^12 the long corridor term 9^m*a vanishes for m>=6.  Therefore the
first deviation has a depth-independent K/I/B chamber classification.  This
script compiles the full <=19 chamber independently, proves the exact six
local escape templates, and identifies the only three blocked B centers.

It also continues the exact V26 389-bit natural adversary past depth 448 until
its first source-order exit.  That witness is diagnostic only; the universal
claim remains UNKNOWN.
"""
from itertools import combinations
import json

N0 = 38_911_100_780_481_085_467
NC = 3_782_158_995_862_761_504_768
A59 = 91_182_490_942_926_966_077
C59 = 3**46
B59 = (1<<59)*A59 - (3**38)*N0

O=12
MOD=3**O
INV2=pow(2,-1,MOD)

def T(x:int)->int:
    return (3*x+1)//2 if x&1 else x//2

def comps(total:int,parts:int):
    for cuts in combinations(range(1,total),parts-1):
        p=0; w=[]
        for c in cuts+(total,):
            w.append(c-p); p=c
        yield tuple(w)

def cocycle(w):
    C=0
    for i,a in enumerate(w):
        C=(1<<a)*C+3**i
    return C

# Full local <=19 chamber.
minS={}
for S in range(12,20):
    inv=pow(1<<S,-1,MOD)
    for w in comps(S,O):
        r=cocycle(w)*inv%MOD
        if S < minS.get(r,99):
            minS[r]=S

def cls(r:int)->str:
    if r%3==0:
        return "OUT"
    s=minS.get(r)
    if s is None:
        return "B"
    return "K" if s<19 else "I"

def step_res(r:int,b:int)->int:
    return (r*INV2)%MOD if b==0 else ((3*r+1)*INV2)%MOD

def rat(a:int,b:int)->int:
    return (a*pow(b,-1,MOD))%MOD

# Recheck the exact 2-adic negative cycle and its three phase deviations.
cycle=[rat(-5,1),rat(-7,1),rat(-10,1)]
assert step_res(cycle[0],1)==cycle[1]
assert step_res(cycle[1],1)==cycle[2]
assert step_res(cycle[2],0)==cycle[0]
assert [(cls(r),minS.get(r)) for r in cycle] == [("K",18),("K",18),("K",17)]

# Algebraic corridor identity, sampled only as an implementation guard; the
# identity itself is literal integer algebra.
for a in range(1,100):
    x=8*a-5
    assert x&1
    assert T(T(T(x))) == 9*a-5

# Phase-0 deviation: -5 takes even instead of odd.
I0=step_res(cycle[0],0)
assert I0==rat(-5,2) and cls(I0)=="I" and minS[I0]==19
I0_0=step_res(I0,0)
I0_1=step_res(I0,1)
assert I0_0==rat(-5,4) and cls(I0_0)=="B"
assert I0_1==rat(-13,4) and cls(I0_1)=="I" and minS[I0_1]==19
I0_10=step_res(I0_1,0)
I0_11=step_res(I0_1,1)
assert I0_10==rat(-13,8) and cls(I0_10)=="B"
assert I0_11==rat(-35,8) and cls(I0_11)=="K" and minS[I0_11]==18

# Phase-1 deviation: -7 takes even instead of odd.
I1=step_res(cycle[1],0)
assert I1==rat(-7,2) and cls(I1)=="I" and minS[I1]==19
I1_0=step_res(I1,0)
I1_1=step_res(I1,1)
assert I1_0==rat(-7,4) and cls(I1_0)=="B"
assert I1_1==rat(-19,4) and cls(I1_1)=="K" and minS[I1_1]==18

# Phase-2 deviation: -10 takes odd instead of even.
K2=step_res(cycle[2],1)
assert K2==rat(-29,2) and cls(K2)=="K" and minS[K2]==17

# Exact suffix cost of the last 12 odd steps.  These show that the K exits are
# identity-cost rewinds, while every blocked exit is the first cost-20 case.
def last12_cost(bits):
    q=0
    for k,b in enumerate(reversed(bits),1):
        q+=b
        if q==12:
            return k
    raise AssertionError("not enough odd bits")

base=[1,1,0]*10
templates={
  "phase0_B0":"00",
  "phase0_B10":"010",
  "phase1_B0":"100",
  "phase0_K11":"011",
  "phase1_K1":"101",
  "phase2_K":"111",
}
costs={name:last12_cost(base+[int(x) for x in word])
       for name,word in templates.items()}
assert costs=={
  "phase0_B0":20,
  "phase0_B10":20,
  "phase1_B0":20,
  "phase0_K11":18,
  "phase1_K1":18,
  "phase2_K":17,
}

blocked_centers=[
  {"center":"-5/4","residue":rat(-5,4)},
  {"center":"-13/8","residue":rat(-13,8)},
  {"center":"-7/4","residue":rat(-7,4)},
]
assert [x["residue"] for x in blocked_centers]==[132859,332149,398579]
assert all(cls(x["residue"])=="B" for x in blocked_centers)

identity_centers=[
  {"center":"-35/8","residue":rat(-35,8),"cost":18},
  {"center":"-19/4","residue":rat(-19,4),"cost":18},
  {"center":"-29/2","residue":rat(-29,2),"cost":17},
]
assert all(cls(x["residue"])=="K" and minS[x["residue"]]==x["cost"]
           for x in identity_centers)

# Reconstruct the V26 post-P36 adversary exactly.
P36_BOUND=447
PARITY_LEN=P36_BOUND-59+1

def parity_residue(bits):
    r=0; mod=1
    for i,bit in enumerate(bits):
        found=None
        for cand in (r,r+mod):
            x=cand
            for _ in range(i):
                x=T(x)
            if (x&1)==bit:
                found=cand; break
        assert found is not None
        r=found; mod<<=1
    return r,mod

bits=([1,1,0]*((PARITY_LEN+2)//3))[:PARITY_LEN]
yres,mod=parity_residue(bits)
t=((yres-A59)*pow(C59,-1,mod))%mod
n=N0+NC*t
y=A59+C59*t

# The natural witness actually shadows the -5 cycle longer than the declared
# 389-bit protected gate.
z=y+5
L=0
while z%2==0:
    z//=2; L+=1
h=z
assert L==391 and h&1

q=38
first_merge=None
first_splice=None
first_direct=None
first_cross=None
class_trace=[]
for k in range(59,800):
    c=cls(y%MOD)
    if k>=440 and k<=530:
        class_trace.append({"depth":k,"parity":y&1,"class":c,
                            "min_reverse_cost":minS.get(y%MOD)})
    if first_direct is None and y<n:
        first_direct={"depth":k,"endpoint":y}
    if first_splice is None and y%8==5 and y<=4*n:
        first_splice={"depth":k,"endpoint":y}
    if first_cross is None and 3**q < 2**k:
        first_cross={"depth":k,"odd_count":q,"endpoint":y}
    if first_merge is None and y%3==2:
        p=(2*y-1)//3
        if 0<p<n:
            assert T(p)==y
            first_merge={"depth":k,"endpoint":y,"p":p,
                         "reverse_word":"O"}
    if first_merge and first_splice and first_direct and first_cross:
        break
    b=y&1
    y=T(y)
    q+=b

assert first_merge and first_merge["depth"]==518
assert first_splice and first_splice["depth"]==525
assert first_direct and first_direct["depth"]==528
assert first_cross and first_cross["depth"]==528

# Canonical source-relative margin register W_k=2^k*(y_k-n).
# Every even I->B step has the exact decrement W_(k+1)=W_k-2^k*n.
# This is algebraic and is the precise register effect to formalize next.
margin_even_law = "W_(k+1)=W_k-2^k*n for W_k=2^k*(y_k-n) on an even step"

result={
  "schema":"COLLATZ_CRYSTAL_CORRIDOR_CHAMBER_V27",
  "parent":"collatz-crystal-post-p36-adversary-v26@9c68bf8f64f83ac90aa892157bd24806b511ec06",
  "corridor":{
    "cycle":["-5","-7","-10"],
    "parity_word":"110",
    "macro_identity":"T^3(8*a-5)=9*a-5",
    "long_corridor_threshold_blocks_for_3adic_freeze":6,
  },
  "escape_quotient":{
    "blocked_B_centers":blocked_centers,
    "identity_K_centers":identity_centers,
    "suffix_costs":costs,
    "interpretation":(
      "After a sufficiently long maximal 110/-5 shadow, the first deviation "
      "can only reach one of three cost-20 blocked centers or one of three "
      "identity-cost K centers. No arbitrary 3-adic context is introduced."
    ),
  },
  "canonical_M_register":{
    "register":"W_k=2^k*(y_k-n)",
    "even_I_to_B_update":margin_even_law,
    "meaning":"every blocked escape from the frozen I states is an even step and pays this exact source-relative decrement",
  },
  "v26_adversary_continuation":{
    "parameter":t,
    "source":n,
    "v2_endpoint_plus_5_at_depth59":L,
    "odd_tail_h":h,
    "first_lower_source_merge":first_merge,
    "first_quarter_splice":first_splice,
    "first_direct_descent":first_direct,
    "first_coefficient_crossing":first_cross,
    "trace_440_530":class_trace,
  },
  "scientific_verdict":"ALL_DEPTH_LOCAL_CORRIDOR_ESCAPE_COMPRESSED_TO_THREE_B_CENTERS",
  "next_residual":(
    "Prove that a reachable B-center with nonnegative canonical source margin "
    "cannot recur without either accumulating a strict source-order merge or "
    "decreasing a well-founded M/crossing register. The raw 110 corridor and "
    "raw 3-adic context are both superseded as proof states."
  ),
  "universal_status":"UNKNOWN",
  "global_collatz":"UNKNOWN",
}
print(json.dumps(result,indent=2))
