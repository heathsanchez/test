#!/usr/bin/env python3
"""Crystal macro-transfer falsifier across source-window scales.

Protected consequence: first b<=21 such that the exact live-origin envelope
resource does not increase:
 P_(j+b)/P_j <= E_(j+b)/E_j, where
 E_j proportional to F_j*2^(floor(6j/125)-j) for fixed window m.

Test whether Q=(j mod2, floor(2^j P_j/F_j)) determines this macro consequence
across all observed m. Emit exact cross-scale collisions.
"""
import json
from collections import defaultdict
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512;BMAX=21
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
def D(j,m):return (P[j][m]<<j)//F[j] if P[j][m] else None
def pays(j,b,m):
 if not P[j][m]:return True
 # P[j+b]/P[j] <= F[j+b]/F[j] * 2^(floor6diff-b)
 a=P[j+b][m]*F[j]; d=P[j][m]*F[j+b]
 e=(6*(j+b))//125-(6*j)//125-b
 return a <= (d<<e) if e>=0 else (a<<(-e))<=d
def sig(j,m):
 for b in range(1,BMAX+1):
  if j+b<=DEPTH and pays(j,b,m):
   # also retain exact whether the endpoint exits.
   return (b,P[j+b][m]==0)
 return (0,False)
G=defaultdict(list)
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  d=D(j,m)
  if d is not None:G[(j&1,d)].append((j,m,sig(j,m)))
coll=[]
for q,xs in G.items():
 ss={x[2] for x in xs}
 if len(ss)>1:
  coll.append({"Q":list(q),"signatures":[list(x) for x in sorted(ss)],
    "examples":[{"j":j,"m":m,"sig":list(s)} for j,m,s in xs[:12]]})
# More consequential: even if exact minimum b differs, does every realization
# share at least one common paying b<=21?
no_common=[]
for q,xs in G.items():
 common=set(range(1,BMAX+1))
 for j,m,_ in xs:
  common &= {b for b in range(1,BMAX+1) if j+b<=DEPTH and pays(j,b,m)}
 if not common:
  no_common.append({"Q":list(q),"count":len(xs),
                    "examples":[{"j":j,"m":m} for j,m,_ in xs[:12]]})
result={"schema":"COLLATZ_CRYSTAL_MACRO_TRANSFER_V0","q_classes":len(G),
 "exact_signature_collision_count":len(coll),"first_exact_collisions":coll[:10],
 "no_common_paying_block_count":len(no_common),"first_no_common":no_common[:10],
 "status":"BOUNDED_COMMON_MACRO_TRANSFER" if not no_common else "MACRO_Q_SEPARATOR_REQUIRED",
 "theorem_target":"for every lawful Q class, one b<=21 pays envelope debt for every realization, including growing source windows",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
