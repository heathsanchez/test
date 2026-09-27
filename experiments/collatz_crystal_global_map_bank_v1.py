#!/usr/bin/env python3
"""Crystal global return-map capability bank.

Compile exact return maps learned from an earlier frozen source band. Apply each
verified map inversely at actual later endpoints of untouched prospective
sources. Map validity is global algebra; predecessor legality and y<n are checked
source-pinned. This tests whether Crystal's 'never pay twice' capability reuse
turns apparent novel-centre growth into lower merges.
"""
import json
from collections import defaultdict,Counter
import collatz_q0_rigid_recharge_audit as ra

def returns(n,K):
 starts,branches=ra.rigid_episode_segment(n,K);cache={};last={};out=[]
 for end in range(1,len(starts)):
  r=starts[end][1]
  if r in last:
   st=last[r];w=tuple(branches[st:end]);c=cache.setdefault(w,ra.certificate(w))
   m0=starts[st][2];m1=starts[end][2]
   assert ra.admissible(c,m0) and ra.replay(c,m0)==m1
   out.append((r,c,m1,starts[end][0]))
  last[r]=end
 return out
def inv(c,m):
 num=(1<<c['D'])*m-c['B']
 if num<=0 or num%c['A']:return None
 p=num//c['A']
 if p<=0 or not(p&1) or not ra.admissible(c,p) or ra.replay(c,p)!=m:return None
 return p
def compile_bank(lo,hi,K):
 bank={}
 for n in range(lo|1,hi+1,2):
  for r,c,m,k in returns(n,K):
   bank[(r,tuple(c['q']))]=c
 return bank
def audit(lo,hi,K,bank):
 cnt=Counter();hard=[];wits=[]
 for n in range(lo|1,hi+1,2):
  rs=returns(n,K)
  if not rs:continue
  closed=False
  for r,c,m,k in rs:
   cnt['endpoints']+=1
   for (rr,q),old in bank.items():
    if rr!=r:continue
    cnt['bank_attempts']+=1
    p=inv(old,m)
    if p is None:continue
    cnt['legal']+=1;y=(1<<r)*p-1
    if y<n:
     cnt['lower_merge']+=1;wits.append([n,r,k,y,m,list(q)]);closed=True;break
   if closed:break
  if not closed:hard.append(n)
 return {"counts":dict(cnt),"sources_with_returns":len(set(n for n in range(lo|1,hi+1,2) if returns(n,K))),
   "closed_sources":len(set(w[0] for w in wits)),"hard_count":len(hard),"first_hard":hard[:50],
   "first_witnesses":wits[:30]}
if __name__=="__main__":
 bank=compile_bank(3,8191,160)
 print(json.dumps({"schema":"COLLATZ_CRYSTAL_GLOBAL_MAP_BANK_V1",
  "frozen_bank_size":len(bank),"prospective":audit(8193,32767,160,bank),
  "interpretation":"verified return maps are reusable global capabilities; all inverse witnesses remain actual-source checked",
  "global_collatz":"UNKNOWN"},indent=2))
