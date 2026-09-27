#!/usr/bin/env python3
"""Adversarial polynomial-injection audit.

For X_j=(j+1)^15 and b<=21:
P_{j+b}(X_{j+b}) <= P_{j+b}(X_j) + (X_{j+b}-X_j).
Use the exact fixed-window normalized macro ratios observed in the qualified
world, but charge the WORST possible admission of every new integer in the
polynomial strip. Determine whether contraction surplus can absorb injection.

This does not universalize fixed-window contraction; it tests whether moving
window requires any additional origin-distribution theorem once that lemma is
available.
"""
import json
from fractions import Fraction
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
def normfactor(j):
 return Fraction(1<<j,F[j]*(1<<((6*j)//125)))
def fixed_after_bound(j,b,m):
 # exact observed fixed-window live count
 return P[j+b][m]
rows=[]
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  p=P[j][m]
  if not p:continue
  E0=Fraction(p)*normfactor(j)
  opts=[]
  for b in range(1,BMAX+1):
   Efix=Fraction(P[j+b][m])*normfactor(j+b)
   inj=((j+b+1)**15-(j+1)**15+1)//2 # odd-origin worst case
   Einj=Fraction(inj)*normfactor(j+b)
   opts.append((Efix+Einj,b,Efix,Einj))
  best=min(opts)
  rows.append((best[0]/E0,best[1],j,m,best[2]/E0,best[3]/E0))
good=sum(r<=RHO for r,_,_,_,_,_ in rows)
result={"schema":"COLLATZ_POLYNOMIAL_INJECTION_ADVERSARIAL_V0","states":len(rows),
 "states_paying_rho_even_with_all_new_odd_origins_live":good,
 "failures":len(rows)-good,
 "best_total_ratio_max":None if not rows else [max(rows)[0].numerator,max(rows)[0].denominator],
 "worst":[{"total":[r.numerator,r.denominator],"b":b,"j":j,"m":m,
           "fixed":[rf.numerator,rf.denominator],"injection":[ri.numerator,ri.denominator]}
          for r,b,j,m,rf,ri in sorted(rows,reverse=True)[:20]],
 "interpretation":"If failures exist, arbitrary admission is too pessimistic; only the injected polynomial strip needs origin-sensitive control. Fixed-window and moving-window obligations remain separate.",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
