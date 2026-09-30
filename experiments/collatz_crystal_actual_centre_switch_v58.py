#!/usr/bin/env python3
"""V58: actual affine-centre / defect dynamics on V53 residual edges.

V54 searched V52 classifier coordinates.  Here we use the exact fixed centre
c=B/(P-A) of each realized affine return P*m'=A*m+B.

Exact law:
  P*((P-A)m' - B) = A*((P-A)m - B).
Since A is odd and P=2^D, every use of one fixed centre consumes D powers
of two from the integer defect.  V58 asks whether residual switching itself
has a simple well-founded law in these true-centre coordinates.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
from math import gcd
import hashlib, io, json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_nonpositive_budget_kernel_v53 as v53

def v2z(x:int):
    x=abs(x)
    if x==0: return None
    return (x & -x).bit_length()-1

def centre(z):
    den=z["P"]-z["A"]
    assert den != 0
    return Fraction(z["B"],den)

def defect(z,mkey="m0"):
    return (z["P"]-z["A"])*z[mkey]-z["B"]

def rat_v2(q:Fraction):
    if q==0: return None
    return v2z(q.numerator)-v2z(q.denominator)

edges=[]
nodes=set()
for tr in v53.transitions:
    if not tr["src"]["residual"] or tr["kind"]!="RESIDUAL":
        continue
    s,d=tr["src"],tr["dst"]
    assert s["m1"]==d["m0"]
    cs,cd=centre(s),centre(d)
    zs0=defect(s,"m0"); zs1=defect(s,"m1")
    zd0=defect(d,"m0")
    vs0=v2z(zs0); vs1=v2z(zs1); vd0=v2z(zd0)
    # Exact centre-defect transport.
    assert s["P"]*zs1 == s["A"]*zs0
    assert vs0 is not None and vs1 is not None
    assert vs0-vs1==s["D"]
    sep=rat_v2(cs-cd)
    row={
      "src_key":s["key"],"dst_key":d["key"],
      "src_law":(s["A"],s["B"],s["P"],s["D"]),
      "dst_law":(d["A"],d["B"],d["P"],d["D"]),
      "src_center":cs,"dst_center":cd,
      "same_law":(s["A"],s["B"],s["P"],s["D"])==(d["A"],d["B"],d["P"],d["D"]),
      "same_center":cs==cd,
      "src_defect_v2_before":vs0,
      "src_defect_v2_after":vs1,
      "dst_defect_v2":vd0,
      "center_sep_v2":sep,
      "src_D":s["D"],"dst_D":d["D"],
    }
    edges.append(row); nodes.add(s["key"]);nodes.add(d["key"])

# Rebuild V53 elimination rank for comparison.
succ=defaultdict(set)
for e in edges: succ[e["src_key"]].add(e["dst_key"])
allnodes=set()
for tr in v53.transitions:
    if tr["src"]["residual"]:
        allnodes.add(tr["src"]["key"]); succ.setdefault(tr["src"]["key"],set())
        if tr["kind"]=="RESIDUAL":
            allnodes.add(tr["dst"]["key"]); succ.setdefault(tr["dst"]["key"],set())
rank,left,layers=v53.elimination_rank(allnodes,succ)
assert not left

for e in edges:
    e["src_rank"]=rank[e["src_key"]]; e["dst_rank"]=rank[e["dst_key"]]

same_law=sum(e["same_law"] for e in edges)
same_center=sum(e["same_center"] for e in edges)

# Test exact-centre candidate quantities as edge potentials.
fields=[
 "src_defect_v2_before","src_defect_v2_after","dst_defect_v2",
 "src_D","dst_D"
]
# Candidate source value -> corresponding destination value where meaningful.
pairs={
 "defect_before":("src_defect_v2_before","dst_defect_v2"),
 "postdefect_to_nextdefect":("src_defect_v2_after","dst_defect_v2"),
 "D":("src_D","dst_D"),
}
mono={}
for name,(a,b) in pairs.items():
    ds=[e[a]-e[b] for e in edges]
    mono[name]={
      "strict_decrease":all(x>0 for x in ds),
      "nonincrease":all(x>=0 for x in ds),
      "min_delta":min(ds),"max_delta":max(ds),
      "hist":dict(sorted(Counter(ds).items())),
    }

# Ultrametric switch identity diagnostics.
sep_rows=[]
ultra=Counter()
for e in edges:
    if e["same_center"]:
        ultra["SAME_CENTER"]+=1
        continue
    sep=e["center_sep_v2"]
    a=e["src_defect_v2_after"]; b=e["dst_defect_v2"]
    assert sep is not None
    ultra["sep_eq_min"] += (sep==min(a,b))
    ultra["sep_ge_min"] += (sep>=min(a,b))
    ultra["next_closer_than_old"] += (b>a)
    ultra["old_closer_than_next"] += (a>b)
    ultra["equal_closeness"] += (a==b)
    if len(sep_rows)<30:
        sep_rows.append({
          "src_rank":e["src_rank"],"dst_rank":e["dst_rank"],
          "src_center":[e["src_center"].numerator,e["src_center"].denominator],
          "dst_center":[e["dst_center"].numerator,e["dst_center"].denominator],
          "old_center_after_v2":a,"next_center_v2":b,
          "center_sep_v2":sep,
          "src_D":e["src_D"],"dst_D":e["dst_D"],
        })

# Actual-law counts by empirical layer.
laws_by_rank=defaultdict(set); centers_by_rank=defaultdict(set)
for tr in v53.transitions:
    s=tr["src"]
    if not s["residual"]: continue
    r=rank[s["key"]]
    laws_by_rank[r].add((s["A"],s["B"],s["P"],s["D"]))
    centers_by_rank[r].add(centre(s))
layer_laws={}
for r in sorted(laws_by_rank):
    layer_laws[str(r)]={
      "laws":len(laws_by_rank[r]),
      "centers":len(centers_by_rank[r]),
      "sample_laws":[list(x) for x in sorted(laws_by_rank[r])[:20]],
      "sample_centers":[[x.numerator,x.denominator] for x in sorted(centers_by_rank[r])[:20]],
    }

result={
 "schema":"COLLATZ_CRYSTAL_ACTUAL_CENTRE_SWITCH_V58",
 "parent":"collatz-crystal-nonpositive-budget-kernel-v53@2b49ce24eb1593e045a7e1b7bcb8782f3f426d02",
 "residual_edges":len(edges),
 "same_exact_law_edges":same_law,
 "same_actual_center_edges":same_center,
 "actual_laws_by_rank":layer_laws,
 "candidate_monotonicity":mono,
 "ultrametric_switch_counts":dict(sorted(ultra.items())),
 "switch_examples":sep_rows,
 "verdict":(
   "ACTUAL_CENTRE_SCALAR_RANK_FOUND"
   if any(z["strict_decrease"] for z in mono.values())
   else "INFINITE_RESIDUAL_REQUIRES_ACTUAL_CENTRE_SWITCHING"
 ),
 "interpretation":(
   "Every repeated fixed affine centre has an exact 2-adic countdown. "
   "If no scalar defect quantity ranks switches, the only remaining infinite "
   "mechanism is unbounded switching among distinct rational affine centres."
 ),
 "promotion_boundary":(
   "Bounded V53 edge census. Universal QED requires proving that an actual "
   "positive-natural zero-tail no-Exit orbit cannot switch centres forever."
 ),
 "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(
 json.dumps(result,sort_keys=True,separators=(",",":"),default=str).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True,default=str))
