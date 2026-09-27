#!/usr/bin/env python3
"""Mine the hard frontier for the deliberately loose rho=511/512 theorem.

For each exact state compute best b<=21 and slack rho-target - best_ratio.
Rank hardest states. Generate theorem-oriented descriptors from exact carry/live
state and find which simple descriptors isolate the hard frontier. This is
input to P35/P37 residual-depth case generation, not a universal proof.
"""
import json
from fractions import Fraction
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512;BMAX=21;TARGET=Fraction(511,512)
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
rows=[]
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  if not P[j][m]:continue
  r,b=min((ratio(j,b,m),b) for b in range(1,BMAX+1))
  d=(P[j][m]<<j)//F[j]
  rows.append((TARGET-r,j,m,b,r,d,C[j+1][m],P[j][m],qmin[j]-qmin[j-1]))
rows.sort()
hard=rows[:40]
# Count hard states under progressively generous margins to see frontier size.
thresholds=[Fraction(1,2**k) for k in (6,8,10,12,14,16)]
front={f"1/2^{k}":sum(1 for s,*_ in rows if s<Fraction(1,2**k)) for k in (6,8,10,12,14,16)}
result={"schema":"COLLATZ_RHO_511_HARD_FRONTIER_V0","states":len(rows),
 "target":[511,512],"frontier_counts":front,
 "hardest":[{"slack":[s.numerator,s.denominator],"j":j,"m":m,"best_b":b,
             "best_ratio":[r.numerator,r.denominator],"D":d,
             "next_exit_count":c,"live_count":p,"qmin_jump":qj}
            for s,j,m,b,r,d,c,p,qj in hard],
 "status":"BOUNDED_HARD_FRONTIER_MINED","universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
