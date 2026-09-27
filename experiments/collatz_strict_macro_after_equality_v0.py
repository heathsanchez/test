#!/usr/bin/env python3
"""Extract strict macro progress after equality chains.

For each exact fixed-window live state, consider all b<=21 that pay the envelope
resource (ratio<=1). Choose a progress-optimal macro: minimize ratio, then b.
Build transitions on concrete (j,m) states, measure equality chains (ratio==1),
and the minimum strict contraction that follows. Also compute the explicit J
needed for polynomial window growth (1+L/(J+1))^15 to be absorbed by delta.

Bounded theorem discovery only; universal carry law remains separate.
"""
import json
from fractions import Fraction
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
def ratio(j,b,m):
 if not P[j][m]:return Fraction(0)
 a=Fraction(P[j+b][m]*F[j],P[j][m]*F[j+b])
 e=(6*(j+b))//125-(6*j)//125-b
 return a/Fraction(2**e if e>=0 else 1,1 if e>=0 else 2**(-e))
policy={}
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  if not P[j][m]:continue
  pays=[(ratio(j,b,m),b) for b in range(1,BMAX+1) if j+b<=DEPTH and ratio(j,b,m)<=1]
  if pays:policy[(j,m)]=min(pays)
eq_starts=[];strict=[]
for s,(r,b) in policy.items():
 if r==1:eq_starts.append(s)
 else:strict.append((r,s,b))
# Follow chosen macro policy; count consecutive equality macros.
chains=[]
for s in eq_starts:
 cur=s;steps=0;depth_span=0;seen=set();follow=None
 while cur in policy and cur not in seen:
  seen.add(cur);r,b=policy[cur]
  if r<1:
   follow=(r,cur,b);break
  steps+=1;depth_span+=b
  cur=(cur[0]+b,cur[1])
 chains.append((steps,depth_span,s,follow))
max_steps=max((x[0] for x in chains),default=0)
max_span=max((x[1] for x in chains),default=0)
unresolved=[x for x in chains if x[3] is None]
strict_follow=[x[3][0] for x in chains if x[3] is not None]
delta=None
rho=None
if strict_follow:
 rho=max(strict_follow) # weakest strict contraction
 delta=1-rho
# Find integer J such that rho*(1+max_span/(J+1))^15 < 1 exactly.
J=None
if rho is not None and rho<1 and max_span>0:
 j=1
 # exponential search then binary
 while rho*Fraction((j+1+max_span)**15,(j+1)**15)>=1:j*=2
 lo=max(0,j//2);hi=j
 while lo+1<hi:
  mid=(lo+hi)//2
  if rho*Fraction((mid+1+max_span)**15,(mid+1)**15)<1:hi=mid
  else:lo=mid
 J=hi
result={"schema":"COLLATZ_STRICT_MACRO_AFTER_EQUALITY_V0",
 "policy_states":len(policy),"equality_starts":len(eq_starts),
 "max_equality_macro_count":max_steps,"max_equality_depth_span":max_span,
 "unresolved_equality_chains":len(unresolved),
 "weakest_following_strict_ratio":[rho.numerator,rho.denominator] if rho else None,
 "strict_delta":[delta.numerator,delta.denominator] if delta else None,
 "polynomial_growth_absorption_J":J,
 "J_below_existing_finite_cutoff":(J is not None and J<=271782),
 "worst_chains":[{"start":list(x[2]),"macro_count":x[0],"depth_span":x[1],
                  "follow_ratio":([x[3][0].numerator,x[3][0].denominator] if x[3] else None)}
                 for x in sorted(chains,reverse=True)[:20]],
 "status":"BOUNDED_STRICT_PROGRESS_CERTIFICATE" if not unresolved and rho is not None else "EQUALITY_CHAIN_OBSTRUCTION",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
