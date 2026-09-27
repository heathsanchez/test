#!/usr/bin/env python3
"""Case-B residual quotient / scale test for rho=511/512.

Case A: some BAD lower bound LB_b(P)>P, contradiction by monotonicity.
Case B: all LB_b(P)<=P. Define required cumulative exits
 R_b(P)=P-LB_b(P)+1, and actual cumulative exits X_b=P-P_b.
BAD requires X_b < R_b for all b.

For observed states, encode normalized integer deficits
 d_b = R_b-X_b (>0 means horizon b still BAD), clipped at <=0 as CLOSED.
Test whether the 21-sign vector / small clipped deficit vector stabilizes
across source-window scales for same phase and whether any all-positive
Case-B vector exists through b=21.
"""
import json
from fractions import Fraction
from collections import defaultdict,Counter
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
def fac(j,b):
 e=(6*(j+b))//125-(6*j)//125-b
 return RHO*Fraction(F[j+b],F[j])*Fraction(2**e if e>=0 else 1,1 if e>=0 else 2**(-e))
def lb(j,b,p):
 x=fac(j,b)*p
 return x.numerator//x.denominator+1
rows=[];caseA=0;caseB=0;caseBbad=[]
byjm={}
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  p=P[j][m]
  if not p:continue
  lbs=[lb(j,b,p) for b in range(1,BMAX+1)]
  if any(x>p for x in lbs):
   caseA+=1; kind="A"
  else:
   caseB+=1;kind="B"
  deficits=[]
  for b,L in enumerate(lbs,1):
   req=p-L+1
   exits=p-P[j+b][m]
   deficits.append(req-exits)
  bad=all(d>0 for d in deficits)
  if kind=="B" and bad:caseBbad.append((j,m,p,deficits))
  sign=tuple(1 if d>0 else 0 for d in deficits)
  clip=tuple(max(-1,min(2,d)) for d in deficits)
  row=(j,m,p,kind,sign,clip,deficits)
  rows.append(row);byjm[(j,m)]=row
# Same-j adjacent-window scale comparison: do residual signatures stabilize?
pairs=0;sign_same=0;clip_same=0;changes=[]
for j,m,p,k,s,c,d in rows:
 nxt=byjm.get((j,m+1))
 if nxt and k=="B" and nxt[3]=="B":
  pairs+=1
  if s==nxt[4]:sign_same+=1
  if c==nxt[5]:clip_same+=1
  if s!=nxt[4] and len(changes)<20:
   changes.append({"j":j,"m":m,"P":p,"Pnext":nxt[2],
                   "sign":list(s),"sign_next":list(nxt[4])})
# Phase-only set of Case-B sign signatures
phase=defaultdict(set)
for j,m,p,k,s,c,d in rows:
 if k=="B":phase[j%125].add(s)
result={"schema":"COLLATZ_CASE_B_SCALE_QUOTIENT_V0","states":len(rows),
 "case_A":caseA,"case_B":caseB,"case_B_all21_bad":len(caseBbad),
 "adjacent_window_caseB_pairs":pairs,"sign_signature_same":sign_same,
 "clipped_deficit_same":clip_same,"first_scale_changes":changes,
 "phase_signature_counts":{str(k):len(v) for k,v in sorted(phase.items())},
 "max_signatures_per_phase":max(map(len,phase.values()),default=0),
 "status":"BOUNDED_CASE_B_BAD_EMPTY" if not caseBbad else "CASE_B_BAD_SURVIVES",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
