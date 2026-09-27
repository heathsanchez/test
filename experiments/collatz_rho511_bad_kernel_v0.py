#!/usr/bin/env python3
"""Bad-kernel view of the rho=511/512 Collatz macro theorem.

A state (j,m) is BAD iff no b<=21 gives normalized resource ratio <=511/512.
On the exact qualified world there should be no BAD roots; to expose an
inductive proof object, compute each state's 21 threshold deficits and ask
how early a prefix b already certifies non-badness. Group by exact carry
exit-vector prefixes and test whether a bounded prefix of cumulative exits,
together with deterministic phase j mod 125, is sufficient to certify
non-badness without selecting an exact policy.

This is theorem discovery, not a universal proof.
"""
import json
from fractions import Fraction
from collections import Counter,defaultdict
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512;BMAX=21;RHO=Fraction(511,512)
qmin,F,_=language_counts(DEPTH)
hist=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for n in range(1,1<<BITS,2):
 z=first_crossing(n,qmin)
 if z:
  j,_,_=z;hist[j][n.bit_length()]+=1
C=[[0]*(BITS+1) for _ in range(DEPTH+1)];P=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for j in range(1,DEPTH+1):
 for m in range(1,BITS+1):C[j][m]=C[j][m-1]+hist[j][m]
for m in range(1,BITS+1):
 P[0][m]=1<<(m-1)
 for j in range(1,DEPTH+1):P[j][m]=P[j-1][m]-C[j][m]
def ratio(j,b,m):
 a=Fraction(P[j+b][m]*F[j],P[j][m]*F[j+b])
 e=(6*(j+b))//125-(6*j)//125-b
 return a/Fraction(2**e if e>=0 else 1,1 if e>=0 else 2**(-e))
rows=[];bad=[]
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  p=P[j][m]
  if not p:continue
  rs=[ratio(j,b,m) for b in range(1,BMAX+1)]
  wins=[b for b,r in enumerate(rs,1) if r<=RHO]
  if not wins:bad.append((j,m))
  first=min(wins) if wins else None
  cum=[p-P[j+b][m] for b in range(1,BMAX+1)]
  rows.append((j,m,p,first,cum,rs))
# The actual proof obligation is existential; summarize how many remain
# uncertified after each allowed prefix of horizons.
uncert={}
for h in range(1,BMAX+1):
 uncert[h]=sum(1 for _,_,_,_,_,rs in rows if all(r>RHO for r in rs[:h]))
# Normalize cumulative exits by P using integer cross-products. Search for a
# simple universal lower bound max_{b<=21} exits/P >= c/d in corpus.
besthaz=[]
for j,m,p,first,cum,rs in rows:
 h=max(Fraction(x,p) for x in cum)
 besthaz.append((h,j,m,p))
minhaz=min(besthaz)
# Test simple hazard floors. These alone need not imply rho; they reveal
# whether carry loss has an extremely crude universal floor.
floors=[]
for d in (512,256,128,64,32,16,8):
 c=Fraction(1,d)
 floors.append({"floor":[1,d],"failures":sum(1 for h,_,_,_ in besthaz if h<c)})
result={"schema":"COLLATZ_RHO511_BAD_KERNEL_V0","states":len(rows),
 "bad_roots":len(bad),"first_bad":bad[:20],
 "uncertified_after_horizon_prefix":uncert,
 "minimum_max_21step_exit_hazard":{"value":[minhaz[0].numerator,minhaz[0].denominator],
   "state":{"j":minhaz[1],"m":minhaz[2],"live":minhaz[3]}},
 "simple_hazard_floors":floors,
 "status":"BOUNDED_BAD_KERNEL_EMPTY" if not bad else "BAD_KERNEL_NONEMPTY",
 "next_theorem":"propagate the conjunction of 21 failed threshold inequalities through exact carry recursion and prove it has no lawful child cycle/path",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
