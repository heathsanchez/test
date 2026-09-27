#!/usr/bin/env python3
"""Crystal consequence quotient: erase constructor labels.

Protected observation at an actual prefix (n,j,y):
  EXIT iff there exists a replayable lower-source certificate currently exposed
  by either direct descent or the exact one-step inverse-odd law.

This deliberately tests whether the minimum present-state relation discovered
by Crystal is simpler than historical constructor labels. It is discovery only.
"""
import json
from collections import defaultdict

SOURCES=[13421671,14378779,8088063,12132095,9280639,13774695,1126015,2252031,1689023,6206655,63728127]
H=1024

def T(x): return (3*x+1)//2 if x&1 else x//2

def cert(n,j,y):
    # protected consequences, not labels
    if 0<y<n:
        return (j,y,0,y)
    if y%3==2:
        p=(2*y-1)//3
        if 0<p<n and T(p)==y:
            return (j,p,1,y)
    return None

rows=[]
for n in SOURCES:
    y=n
    for j in range(H+1):
        c=cert(n,j,y)
        # label-free exact relational observables
        rows.append(dict(n=n,j=j,y=y,exit=c is not None,
          parity=y&1,
          cmp_n=(y>n)-(y<n),
          cmp_3n_2=(2*y>3*n)-(2*y<3*n),
          mod3=y%3,
          even_half_below=(y%2==0 and y//2<n),
          invodd_below=(y%3==2 and (2*y-1)//3<n),
          certificate=c))
        if c is not None: break
        y=T(y)

# Find atomic predicates whose truth implies EXIT on every observed row and
# which actually cover an exit. This is the simplest consequence-pure quotient.
fields=["cmp_n","even_half_below","invodd_below","parity","mod3","cmp_3n_2"]
pure=[]
for f in fields:
    vals=defaultdict(lambda:[0,0])
    for r in rows:
        vals[repr(r[f])][int(r["exit"])]+=1
    for v,(neg,pos) in vals.items():
        if pos and not neg:
            pure.append((f,v,pos))

# Verify the obvious relational collapse mechanically:
# direct certificate is exactly y<n; inverse-odd certificate is exactly
# y==2 mod3 and y<(3n+1)/2 (integer form via predecessor<n).
bad_direct=[]
bad_inverse=[]
for r in rows:
    n,y=r["n"],r["y"]
    direct=(0<y<n)
    inv=(y%3==2 and 0<(2*y-1)//3<n)
    if direct != (r["cmp_n"]==-1): bad_direct.append((n,r["j"],y))
    inv_formula=(y%3==2 and 2*y < 3*n+1)
    if inv != inv_formula: bad_inverse.append((n,r["j"],y))
assert not bad_direct and not bad_inverse

out={
 "schema":"COLLATZ_CRYSTAL_CONSEQUENCE_QUOTIENT_V1",
 "rows":len(rows),"sources":len(SOURCES),
 "constructor_labels_used_as_features":False,
 "protected_observation":"replayable lower-source certificate exists now",
 "consequence_pure_atomic_values":pure,
 "discovered_exact_relations":{
   "direct":"y<n",
   "inverse_odd":"y%3=2 and 2*y<3*n+1"
 },
 "crystal_residual":"certificate-free actual prefix must remain in y>=n and, whenever y%3=2, 2*y>=3*n+1",
 "status":"BOUNDED_CONSEQUENCE_QUOTIENT",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(out,indent=2))
