#!/usr/bin/env python3
"""Translate rho=511/512 macro contraction into exact integer exit obligations.

For each state/block compute the minimum integer exits e=Pj-Pjb needed for the
rho inequality. Compare with actual exits. Test simple theorem-shaped rules:
(A) at least one exit within 21; (B) ceil(P/32), ceil(P/64), etc.
"""
import json,math
from fractions import Fraction
from collections import Counter
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
def factor(j,b):
 # Need Pafter/P <= rho * Fafter/Fj * 2^(floor6diff-b)
 e=(6*(j+b))//125-(6*j)//125-b
 return RHO*Fraction(F[j+b],F[j])*Fraction(2**e if e>=0 else 1,1 if e>=0 else 2**(-e))
def req_exits(j,b,p):
 f=factor(j,b)
 # p_after <= f*p; minimum integer exits p-ceil? largest integer <= f*p
 max_after=(f.numerator*p)//f.denominator
 return max(0,p-max_after)
states=[];one_exit_suff=0;rules={k:0 for k in (16,32,64,128,256,512)}
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  p=P[j][m]
  if not p:continue
  opts=[]
  for b in range(1,BMAX+1):
   req=req_exits(j,b,p); actual=p-P[j+b][m]
   opts.append((req,b,actual,factor(j,b)))
  req,b,actual,f=min(opts,key=lambda x:(x[0],x[1]))
  if req<=1:one_exit_suff+=1
  for k in rules:
   if req<=math.ceil(p/k):rules[k]+=1
  states.append((req,p,b,actual,j,m,f))
states.sort(reverse=True)
result={"schema":"COLLATZ_RHO511_EXIT_OBLIGATION_V0","states":len(states),
 "states_where_one_exit_suffices":one_exit_suff,
 "max_required_exits":max(x[0] for x in states),
 "simple_rule_coverage":{f"ceil(P/{k})":v for k,v in rules.items()},
 "hardest_exit_obligations":[{"required":r,"live":p,"b":b,"actual":a,"j":j,"m":m,
   "factor":[f.numerator,f.denominator]} for r,p,b,a,j,m,f in states[:30]],
 "status":"BOUNDED_EXIT_OBLIGATION_COMPILED","universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
