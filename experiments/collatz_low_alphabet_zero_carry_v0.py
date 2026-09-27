#!/usr/bin/env python3
"""Carry criterion audit for infinite low valuation codes a_k in {1,2}.

For a finite code prefix define q_k=sum a_i and C_{k+1}=3C_k+2^q_k.
Define M_k in [1,3^k) by 2^q_k M_k == C_k mod 3^k.
Then 2^a_k M_{k+1}=3M_k+1+t_k 3^(k+1), t_k in [0,2^a_k).
For actual positive-integer infinite codes, literature criterion says t_k=0 eventually.
We derive what eventual t=0 forces when a_k in {1,2}.
"""
import itertools,json
def inv(a,m): return pow(a,-1,m)
def prefix_state(w):
 q=0;C=0;Ms=[0];ts=[]
 for k,a in enumerate(w):
  # update C,q to k+1
  C=3*C+(1<<q);q+=a
  mod=3**(k+1)
  M=(C*inv(pow(2,q,mod),mod))%mod
  if M==0:M=mod
  # criterion convention requires 1<=M<3^k; inspect raw
  Ms.append(M)
  if k>=0:
   prev=Ms[k]
   num=(1<<a)*M-(3*prev+1)
   den=3**(k+1)
   ts.append(num//den if num%den==0 else None)
 return q,C,Ms,ts

# Direct recurrence under eventual t=0:
# 2^a M' = 3M+1. For a=1 requires M ==1 mod2; for a=2 requires 3M+1 divisible4.
# enumerate positive integer M transitions with a in {1,2}, t=0 and see cycles/paths.
N=100000
edges={}; incoming={}
for M in range(1,N+1):
 out=[]
 for a in (1,2):
  z=3*M+1;d=1<<a
  if z%d==0:
   Mp=z//d
   if Mp>0:
    out.append((a,Mp));incoming.setdefault(Mp,[]).append((M,a))
 edges[M]=out
# find states whose t=0 path can stay within finite range for 200 steps adversarially
surv=[]
for M0 in range(1,10000):
 frontier={M0}
 for _ in range(200):
  nxt=set()
  for M in frontier:
   for a,Mp in edges.get(M,[]):
    if Mp<=N:nxt.add(Mp)
  frontier=nxt
  if not frontier:break
 if frontier:surv.append(M0)
print(json.dumps({"schema":"COLLATZ_LOW_ALPHABET_EVENTUAL_ZERO_CARRY_V0",
 "zero_carry_transition":"2^a M' = 3M+1, a in {1,2}",
 "survivors_200_from_M_lt_10000":surv[:100],"survivor_count":len(surv),
 "note":"If only M=1 survives, derive by minimal/cycle or monotonic argument; otherwise inspect exact survivor structure.",
 "global_collatz":"UNKNOWN"},indent=2))
