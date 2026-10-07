#!/usr/bin/env python3
"""V89: exact audit of V88's separated-cylinder premise on V81 authority.

No new sources are introduced. Rebuild the already-qualified V81 old+fresh
transition authority unchanged and inspect every actual RESIDUAL->RESIDUAL
transition between distinct affine centres.

For each switch at owner m:
  * new return-cylinder admission requires v2(Delta_new(m)) >= D_new+1;
  * centre separation has order h=v2(J);
  * V88's universal algebra applies when h < D_new+1.

Emit the first exact violating edge if any. This is diagnostic evidence only;
zero violations do not prove the universal first-return/certificate theorem.
"""
from __future__ import annotations
from collections import Counter
import hashlib, io, json
from contextlib import redirect_stdout

with redirect_stdout(io.StringIO()):
    import collatz_v80_fresh_interface_v81 as v81

PARENT_V88_QUAL="79b4d17de53a7e7f532440e253728c6a18164cdb741fe0058e48f1bc9ecd898d"

def v2z(x:int):
    x=abs(x)
    if x==0:
        return None
    return (x & -x).bit_length()-1

def centre_key(z):
    # equality of B/(P-A) without Fraction allocation
    return (z["B"], z["P"]-z["A"])

def same_centre(s,d):
    c1=s["P"]-s["A"]; c2=d["P"]-d["A"]
    return s["B"]*c2 == d["B"]*c1

old=[tr for tr in v81.v53.transitions if tr["src"]["residual"]]
combined=old+v81.A["transitions"]+v81.B["transitions"]

stats=Counter()
first_bad=None
samples=[]

for tr in combined:
    if not tr["src"]["residual"] or tr["kind"]!="RESIDUAL":
        continue
    s,d=tr["src"],tr["dst"]
    assert s["m1"]==d["m0"]
    stats["residual_edges"]+=1
    if same_centre(s,d):
        stats["same_centre_edges"]+=1
        continue
    stats["distinct_centre_edges"]+=1
    m=d["m0"]
    C1=s["P"]-s["A"]
    C2=d["P"]-d["A"]
    J=C1*d["B"]-C2*s["B"]
    assert J!=0
    h=v2z(J)
    new_def=C2*m-d["B"]
    old_def=C1*m-s["B"]
    forced=d["D"]+1
    if new_def==0:
        stats["new_zero_defect"]+=1
        row={
          "source":str(tr["source"]),"anchor":tr["anchor"],
          "depth":[s["k0"],s["k1"],d["k1"]],
          "old_law":[s["A"],s["B"],s["P"],s["D"]],
          "new_law":[d["A"],d["B"],d["P"],d["D"]],
          "separation_h":h,"new_forced":forced,
          "old_defect_order":v2z(old_def),
          "new_defect_order":None,
        }
    else:
        w=v2z(new_def)
        vold=v2z(old_def)
        assert w is not None and vold is not None
        admitted=w>=forced
        separated=h<forced
        old_exact=(vold==h)
        gain=(w>vold)
        stats["new_nonzero_defect"]+=1
        stats["new_cylinder_admitted"]+=int(admitted)
        stats["separated"]+=int(separated)
        stats["old_order_equals_separation"]+=int(old_exact)
        stats["strict_new_closer"]+=int(gain)
        row={
          "source":str(tr["source"]),"anchor":tr["anchor"],
          "depth":[s["k0"],s["k1"],d["k1"]],
          "old_law":[s["A"],s["B"],s["P"],s["D"]],
          "new_law":[d["A"],d["B"],d["P"],d["D"]],
          "separation_h":h,"new_forced":forced,
          "old_defect_order":vold,"new_defect_order":w,
          "admitted":admitted,"separated":separated,
          "old_exact":old_exact,"strict_gain":gain,
        }
        if not (admitted and separated and old_exact and gain):
            stats["violations"]+=1
            if first_bad is None:
                first_bad=row
    if len(samples)<20:
        samples.append(row)

result={
  "schema":"COLLATZ_V88_SWITCH_ADMISSION_AUDIT_V89",
  "parent_v88_qualification_sha256":PARENT_V88_QUAL,
  "authority":{
    "old_rows":len(old),
    "fresh_A_rows":len(v81.A["transitions"]),
    "fresh_B_rows":len(v81.B["transitions"]),
    "combined_rows":len(combined),
    "v81_interface_survives":v81.interface_survives,
  },
  "stats":dict(sorted(stats.items())),
  "first_violation":first_bad,
  "sample_switches":samples,
  "status":(
    "ALL_NONZERO_DISTINCT_SWITCHES_SATISFY_V88_PREMISE"
    if first_bad is None
    else "V88_SEPARATION_PREMISE_SEPARATOR"
  ),
  "interpretation":(
    "This reuses the already-qualified V81 old+fresh authority unchanged. "
    "A zero-violation result supports, but does not prove, the universal claim "
    "that deterministic same-anchor first-return certificate cylinders are "
    "source-admittedly separated. Any emitted edge is the exact next separator."
  ),
  "global_collatz":"UNKNOWN",
  "qed":False,
}
result["certificate_sha256"]=hashlib.sha256(
  json.dumps(result,sort_keys=True,separators=(",",":")).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
