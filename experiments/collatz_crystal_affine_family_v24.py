#!/usr/bin/env python3
"""Crystal V24: exact unsplit affine-family audit for the sole V23 cell.

Family:
  n(t) = N0 + NC*t,  t>=0
with the exact V23 congruence cell:
  n == 288230376151711771 (mod 2^59)
  n == 0 (mod 3^8).

Goals:
1) derive the maximal fixed ordinary shortcut prefix shared by every t;
2) prove the next parity genuinely depends on t, so no longer fixed forward
   word can extend the family without splitting t;
3) exhaust every uniform reverse E/O predecessor word reachable from every
   fixed prefix, pruning only when even using all remaining 3-adic odd-inverse
   fuel cannot make the affine slope no larger than the source slope.

This is a falsifier for the strongest *unsplit* #6/#13 route only.  It does
not rule out finite-cell contraction after splitting t, nor any other global
Collatz route.
"""
from __future__ import annotations
from collections import deque
import json

N0 = 38_911_100_780_481_085_467
NC = 3_782_158_995_862_761_504_768

def T(x:int)->int:
    return (3*x+1)//2 if x&1 else x//2

def v3(x:int)->int:
    c=0
    while x and x%3==0:
        c+=1
        x//=3
    return c

# Exact fixed affine prefix n_j(t)=A_j+C_j*t while C_j is even.
prefix=[]
A,C=N0,NC
q=0
for j in range(60):
    prefix.append((j,A,C,q))
    if j==59:
        break
    assert C%2==0
    odd=A&1
    if odd:
        A=(3*A+1)//2
        C=3*C//2
        q+=1
    else:
        A//=2
        C//=2

assert prefix[-1][0]==59
J,A59,C59,Q59=prefix[-1]
assert Q59==38
assert C59==3**46
assert A59==91_182_490_942_926_966_077

# At depth 59 both affine coefficients are odd, hence parity flips with t.
assert A59%2==1 and C59%2==1
assert (A59 + C59*0)%2 == 1
assert (A59 + C59*1)%2 == 0

# Exhaust uniform reverse words from each fixed prefix.
# E: y <- 2y (always valid).
# O: y <- (2y-1)/3, valid uniformly iff A==2 mod3 and C divisible by3.
# A uniform lower source requires p0<N0 and pSlope<=NC (or symmetric strict
# slope with nonlarger intercept).  Pruning is sound: if c has b remaining
# factors of 3, the smallest slope attainable even with b consecutive O moves
# and zero future E moves is c*(2/3)^b.  If that still exceeds NC, no
# continuation can recover.
visited=0
max_reverse_depth=0
depth_cap_hit=False
witness=None
per_prefix=[]
MAX_DEPTH=100

for j,A0,C0,_ in prefix:
    todo=deque([(A0,C0,"")])
    seen={(A0,C0)}
    local=0
    local_max=0
    while todo:
        a,c,w=todo.popleft()
        visited+=1
        local+=1
        local_max=max(local_max,len(w))
        max_reverse_depth=max(max_reverse_depth,len(w))

        if w and a>0 and ((a < N0 and c <= NC) or (a <= N0 and c < NC)):
            witness={"prefix_depth":j,"word":w,"p0":a,"pSlope":c}
            break

        if len(w)>=MAX_DEPTH:
            depth_cap_hit=True
            continue

        b=v3(c)
        if c*(2**b) > NC*(3**b):
            continue

        # If constant is divisible by 3, no future O becomes admissible:
        # E preserves 3-divisibility and only increases slope.
        if a%3==0:
            continue

        ae,ce=2*a,2*c
        if (ae,ce) not in seen:
            seen.add((ae,ce))
            todo.append((ae,ce,w+"E"))

        if a%3==2 and c%3==0:
            ao,co=(2*a-1)//3,2*c//3
            if ao>0 and (ao,co) not in seen:
                seen.add((ao,co))
                todo.append((ao,co,w+"O"))

    per_prefix.append({
        "prefix_depth":j,
        "states":local,
        "max_reverse_depth":local_max,
    })
    if witness is not None:
        break

assert witness is None
assert depth_cap_hit is False
assert max_reverse_depth==67

# Exact first t-parity split after the maximal fixed prefix.
# t=2u -> odd endpoint; t=2u+1 -> even endpoint.
even_t = {
    "condition":"t=2*u",
    "next_endpoint_constant":(3*A59+1)//2,
    "next_endpoint_slope":3*C59,
}
odd_t = {
    "condition":"t=2*u+1",
    "next_endpoint_constant":(A59+C59)//2,
    "next_endpoint_slope":C59,
}

result={
  "schema":"COLLATZ_CRYSTAL_AFFINE_FAMILY_V24",
  "family":{"N0":N0,"NC":NC},
  "maximal_uniform_forward_prefix":{
      "ordinary_depth":59,
      "odd_count":Q59,
      "endpoint_constant":A59,
      "endpoint_slope":C59,
      "next_parity_depends_on_t_mod2":True,
  },
  "uniform_reverse_search":{
      "prefixes_checked":len(prefix),
      "states_exhausted":visited,
      "max_reverse_depth":max_reverse_depth,
      "depth_cap_hit":depth_cap_hit,
      "uniform_lower_source_witness":witness,
      "pruning_rule":"remaining v3 slope fuel cannot reach source slope",
  },
  "first_parameter_split":{"t_even":even_t,"t_odd":odd_t},
  "scientific_verdict":"UNSPLIT_AFFINE_RETURN_OR_LOWER_SOURCE_ROUTE_REJECTED_ON_V23_CELL",
  "next_residual":{
      "name":"FINITE_CELL_PARAMETER_HALVING_QUOTIENT",
      "statement":(
          "split only on the forced next t bit, rewrite t=2u+b, and build the "
          "smallest exact symbolic cell transition system. Seek direct/splice/"
          "lower-source exits or a well-founded u-decrease; otherwise certify "
          "the reachable nonterminal SCC structure."
      ),
      "universal":"UNKNOWN",
  },
  "global_collatz":"UNKNOWN",
}
print(json.dumps(result,indent=2))
