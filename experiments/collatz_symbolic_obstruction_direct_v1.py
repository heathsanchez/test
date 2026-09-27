#!/usr/bin/env python3
"""Direct symbolic audit of canonical M>=0 first-crossing obstructions.

Enumerate the obstruction language itself (not successful Collatz sources).
A state (q,R,Y,w) is the exact canonical source-product state. Prefixes must
remain coefficient-live; the terminal child is the first crossing. Retain
only R>1, M=2^J(Y-R)>=0 and terminal source-lift carry e=0.

For each obstruction endpoint Y, search the complete local 12-odd reverse
chamber with cost <=19 for an exact smaller positive predecessor p<R.
Classify absence as blocked/identity residual. This decides whether the
existing local reverse chamber already covers the symbolic obstruction
language on the declared exact depth.
"""
from itertools import combinations
import json

JMAX=29; O=12
def T(x): return (3*x+1)//2 if x&1 else x//2
def comps(total,parts):
  for cuts in combinations(range(1,total),parts-1):
    z=0;w=[]
    for c in cuts+(total,): w.append(c-z);z=c
    yield tuple(w)
def reverse(y,w):
  x=y
  # inverse odd accelerated blocks: predecessor before O odd steps
  for a in reversed(w):
    x <<= a
    if x<=1 or (x-1)%3: return None
    x=(x-1)//3
    if x%2==0: return None
  return x
words=[]
for S in range(O,20):
  for w in comps(S,O): words.append((S,w))
def terminals(J):
  st=[(0,0,0,0)]
  for k in range(J):
    nx=[]
    for q,R,Y,wbits in st:
      for b in (0,1):
        e=b^(Y&1); R2=R+(e<<k); Z=Y+e*3**q
        Y2=Z//2 if b==0 else (3*Z+1)//2
        q2=q+b; w2=wbits|(b<<k)
        if k+1<J:
          if 3**q2>=2**(k+1): nx.append((q2,R2,Y2,w2))
        elif 3**q2<2**J and 3**q2>=2**(J-1):
          nx.append((q2,R2,Y2,w2))
    st=nx
  return st
obs=[];covered=0;uncovered=[];classes={"K":0,"I":0,"B":0}
for J in range(2,JMAX+1):
  for q,R,Y,wbits in terminals(J):
    e=(R>>(J-1))&1
    M=(1<<J)*(Y-R)
    if not (R>1 and M>=0 and e==0): continue
    best=None;bestS=None
    for S,w in words:
      p=reverse(Y,w)
      if p is not None and 0<p<R:
        if best is None or (S,p)<(bestS,best):best,bestS=p,S
    if best is not None:
      covered+=1;c="K" if bestS<19 else "I"
    else:c="B"
    classes[c]+=1
    row={"J":J,"q":q,"R":R,"Y":Y,"M":M,"word":wbits,"class":c,
         "lower_reverse":None if best is None else {"p":best,"cost":bestS}}
    obs.append(row)
    if best is None and len(uncovered)<100:uncovered.append(row)
out={"schema":"COLLATZ_SYMBOLIC_OBSTRUCTION_DIRECT_V1","J_max":JMAX,
 "obstructions":len(obs),"local_reverse_covered":covered,"classes":classes,
 "uncovered_count":sum(r["class"]=="B" for r in obs),
 "uncovered_sample":uncovered,
 "decision":"LOCAL_CHAMBER_NOT_TOTAL" if uncovered else "LOCAL_CHAMBER_COVERS_DECLARED_SYMBOLIC_OBSTRUCTIONS",
 "next":"If uncovered, quotient exact B-class obstructions by consequential source/carry state and acquire one new constructor; if none, formalize parametric chamber coverage.",
 "global_collatz":"UNKNOWN"}
print(json.dumps(out,indent=2))
