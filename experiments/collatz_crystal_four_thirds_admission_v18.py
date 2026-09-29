#!/usr/bin/env python3
"""Crystal V18: exact affine-bias admission hierarchy at the four-thirds boundary.

No source-range census and no post-boundary trajectory search.

The cycle separates four logically different layers:
  1. V17 scalar/owner envelope.
  2. Universal exact bias min/max envelopes.
  3. Exact finite parity-word bias grammar for concrete separators.
  4. Protected-prefix admissibility.

It also scans only the deterministic deficit-one qmin boundary types
q=qmin(k)-1 through the already-standard depth 4096.  This is a coefficient
type scan, not a source census.  The purpose is consequence pruning:
identify what the universal proof still has to know after the new Lean bias
theorems.
"""
from functools import lru_cache
import json

H = 4096
SOURCE_Q_MOD32 = {4, 9, 20, 25}

def T(x):
    return (3*x+1)//2 if x & 1 else x//2

def bias_min(q):
    return 3**q - 2**q

def bias_max(k,q):
    assert 0 <= q <= k
    return (1 << (k-q)) * bias_min(q)

@lru_cache(maxsize=None)
def bias_word(k,q,B):
    """Return odd positions for an exact length-k, q-odd bias B, or None."""
    if q == 0:
        return () if B == 0 else None
    if k < q or B < bias_min(q) or B > bias_max(k,q):
        return None
    # Peel the last odd insertion B = 3*Bprev + 2^i.
    for i in range(k-1, q-2, -1):
        bit = 1 << i
        if B < bit:
            continue
        rem = B-bit
        if rem % 3:
            continue
        prev = bias_word(i,q-1,rem//3)
        if prev is not None:
            return prev+(i,)
    return None

def replay_word(n,k,positions):
    odds=set(positions)
    x=n
    protected=True
    first_failure=None
    q=0
    for i in range(k+1):
        if x<n and first_failure is None:
            protected=False; first_failure={"kind":"DESCENT","depth":i,"x":x}
        if (x%8==5 and x<=4*n) and first_failure is None:
            protected=False; first_failure={"kind":"QUARTER_SPLICE","depth":i,"x":x}
        if i==k:
            break
        if bool(x&1) != (i in odds):
            return {"parity_matches":False}
        if x&1: q+=1
        x=T(x)
    return {"parity_matches":True,"endpoint":x,"odd_count":q,
            "protected":protected,"first_failure":first_failure}

# Exact qmin + lagged-one-deficit maximal bias.
p2=p3=1
qm=0
lag_q=0
lag_B=0
deficit_rows=[]
for k in range(1,H+1):
    p2 <<= 1
    old_qm=qm
    if p3 < p2:
        p3 *= 3
        qm += 1
    target_lag=max(0,qm-1)
    if target_lag==lag_q+1:
        lag_B=3*lag_B+(1<<(k-1))
        lag_q+=1
    assert target_lag==lag_q
    q=qm-1
    if q<=0 or q%32 not in SOURCE_Q_MOD32:
        continue
    # q=floor(4n/3), with minimal-bad source classes forcing q mod 4 in {0,1}.
    if q%4==0:
        n=3*q//4
    elif q%4==1:
        n=(3*q+1)//4
    else:
        continue
    if n%24 not in {3,7,15,19}:
        continue
    D=(1<<k)-3**q
    assert D>0
    deficit_rows.append({
      "k":k,"q":q,"n":n,
      "lag_bias_ge_nondescending_payment": lag_B >= D*n,
      "payment_gap": lag_B-D*n,
    })

near=[r for r in deficit_rows if r["lag_bias_ge_nondescending_payment"]]
closed=[r for r in deficit_rows if not r["lag_bias_ge_nondescending_payment"]]

# Three separator layers.
cases=[]
for name,n,k,q,x in [
    ("V17_LOCAL_SCALAR_SEPARATOR",27,53,36,451),
    ("BIAS_SANDWICH_SEPARATOR",3,5,4,11),
    ("EXACT_BIAS_BUT_UNPROTECTED",3,9,4,1),
]:
    B=(1<<k)*x-3**q*n
    lo=bias_min(q); hi=bias_max(k,q)
    word=bias_word(k,q,B) if B>=0 else None
    row={"name":name,"n":n,"k":k,"q":q,"x":x,"required_bias":B,
         "bias_min":lo,"bias_max":hi,
         "passes_bias_sandwich":lo<=B<=hi,
         "exact_bias_word":None if word is None else list(word)}
    if word is not None:
        row["replay"]=replay_word(n,k,word)
    cases.append(row)

assert not cases[0]["passes_bias_sandwich"]  # V17 451 dies by universal lower envelope.
assert cases[1]["passes_bias_sandwich"] and cases[1]["exact_bias_word"] is None
assert cases[2]["exact_bias_word"] == [0,1,5,7]
assert cases[2]["replay"]["parity_matches"]
assert not cases[2]["replay"]["protected"]

result={
 "schema":"COLLATZ_CRYSTAL_FOUR_THIRDS_ADMISSION_V18",
 "declared_boundary":{"qmin_depth":H,"source_census":False,
   "post_boundary_trajectory_search":False},
 "universal_bias_laws":{
   "lower":"3^q <= B + 2^q",
   "upper":"2^q*(B+2^k) <= 2^k*3^q",
   "authority":"Lean target in formal/Collatz/FourThirdsAdmission.lean"
 },
 "separator_ladder":cases,
 "deficit_one_qmin_scan":{
   "candidate_types":len(deficit_rows),
   "closed_by_lagged_qmin_bias_max":len(closed),
   "near_resonant_types":len(near),
   "first_near_resonant":near[:20],
   "interpretation":"deficit-one prefix corridor gives a deterministic latest-odd bias maximum; payment closes many types but leaves near-resonant source-admission cells"
 },
 "residual":{
   "deficit_branch":"exact source-admission/protected-prefix exclusion on the near-resonant qmin types",
   "survival_branch":"prefix-high-odd source-order coalescence / exact source admission",
   "common_missing_coordinate":"the exact parity-word/source coupling, not another scalar envelope",
   "universal":"UNKNOWN"
 },
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
