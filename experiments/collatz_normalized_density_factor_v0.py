#!/usr/bin/env python3
"""Universal-law discovery for normalized live-origin density.

Derives exact recurrence identities, then tests whether Q=(j mod 2,D),
D=floor(2^j P_j/F_j), determines the next normalized state from algebraic
auxiliaries. Emits exact collisions and candidate transition formulas.
This is theorem discovery; no universal claim is made by finite tests.
"""
import json
from collections import defaultdict,Counter
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512
qmin,F,T=language_counts(DEPTH)
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
 for j in range(1,DEPTH+1):
  P[j][m]=P[j-1][m]-C[j][m]
  assert P[j-1][m]==P[j][m]+C[j][m]

def D(j,m):return (P[j][m]<<j)//F[j] if P[j][m] else None
rows=[]
for j in range(60,DEPTH):
 for m in range(1,BITS+1):
  if not P[j][m] or not P[j+1][m]:continue
  # Exact rational update:
  # Z_j = 2^j P_j/F_j.
  # Z_{j+1}/Z_j = 2*(P_j-C_{j+1})/P_j * F_j/F_{j+1}.
  # Store reduced integer factors and floor transition.
  p=P[j][m];c=C[j+1][m]
  g=__import__('math').gcd(p,c); a=p//g; e=c//g
  gf=__import__('math').gcd(F[j],F[j+1]); fj=F[j]//gf; fn=F[j+1]//gf
  rows.append((j,m,D(j,m),D(j+1,m),a,e,fj,fn,c))

# Does Q alone determine next D? (prior bounded falsifier says yes on its
# narrower protected signature; recheck algebraically and expose formulas.)
byq=defaultdict(list)
for r in rows:byq[(r[0]&1,r[2])].append(r)
coll=[]
for q,xs in byq.items():
 vals={x[3] for x in xs}
 if len(vals)>1:
  coll.append({"Q":q,"next_Ds":sorted(vals)[:20],
               "examples":[{"j":x[0],"m":x[1],"Dnext":x[3],
                            "survival_factor":[x[4]-x[5],x[4]],
                            "F_factor":[x[6],x[7]]} for x in xs[:10]]})

# Find whether F_{j+1}/F_j transition is controlled by a small phase.
ratios=defaultdict(set)
for j in range(60,DEPTH):
 g=__import__('math').gcd(F[j],F[j+1])
 ratios[j%2].add((F[j]//g,F[j+1]//g))

result={"schema":"COLLATZ_NORMALIZED_DENSITY_FACTOR_V0",
 "exact_identity":"Z_(j+1)=Z_j * 2*(1-C_(j+1)/P_j)*(F_j/F_(j+1)); D_j=floor(Z_j)",
 "states":len(rows),"q_classes":len(byq),"q_nextD_collision_count":len(coll),
 "first_collisions":coll[:10],
 "F_ratio_distinct_by_parity":{"0":len(ratios[0]),"1":len(ratios[1])},
 "consequence":("Q alone is not algebraically Markov on this domain; collision is separator"
                if coll else "bounded data supports Q-determined next floor state"),
 "universal_factorization":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2,default=list))
