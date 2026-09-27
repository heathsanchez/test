#!/usr/bin/env python3
"""Crystal fixed-source return-bank campaign.

For each actual source/anchor return sequence, maintain all prior distinct exact
return maps. At each later endpoint invert every banked map. A legal predecessor
p gives source y=2^r p-1 with the same later endpoint; y<n is OrdinaryExit by
lower merge. If no lower merge, record whether the new map is genuinely novel
and its rational centre. This directly tests the C residual:
  infinite coherent path must either reuse a map (defect fuel applies),
  acquire a lower merge from the consequence bank, or keep generating novel
  source-coupled centres.
Bounded discovery only.
"""
import json
from collections import Counter,defaultdict
import collatz_q0_rigid_recharge_audit as ra

def returns(n,K):
 starts,branches=ra.rigid_episode_segment(n,K);cache={};last={};out=defaultdict(list)
 for end in range(1,len(starts)):
  r=starts[end][1]
  if r in last:
   st=last[r];word=tuple(branches[st:end]);c=cache.setdefault(word,ra.certificate(word))
   m0=starts[st][2];m1=starts[end][2]
   assert ra.admissible(c,m0) and ra.replay(c,m0)==m1
   out[r].append((c,m0,m1,starts[st][0],starts[end][0]))
  last[r]=end
 return out
def inv(c,m):
 num=(1<<c['D'])*m-c['B']
 if num<=0 or num%c['A']:return None
 p=num//c['A']
 if p<=0 or not(p&1) or not ra.admissible(c,p) or ra.replay(c,p)!=m:return None
 return p
def audit(lo,hi,K):
 cnt=Counter(); residual=[]
 for n in range(lo|1,hi+1,2):
  for r,seq in returns(n,K).items():
   bank=[];closed=False
   for idx,(c,m0,m1,k0,k1) in enumerate(seq):
    # reuse/current q against previous bank
    for old in bank:
     p=inv(old,m1)
     if p is None:continue
     y=(1<<r)*p-1
     cnt['legal_bank_inverse']+=1
     if y<n:
      cnt['lower_merge']+=1;closed=True;break
    if closed:break
    if any(old['q']==c['q'] for old in bank):
     cnt['map_reuse_without_bank_merge']+=1
    else:
     bank.append(c);cnt['novel_map']+=1
   if not closed and seq:
    residual.append({"n":n,"r":r,"returns":len(seq),"distinct_maps":len(bank),
      "centres":[list(c['q']) for c in bank[-12:]]})
 result={"schema":"COLLATZ_CRYSTAL_FIXED_SOURCE_MAP_BANK_V1","range":[lo,hi],"K":K,
  "counts":dict(cnt),"residual_count":len(residual),"first_residual":residual[:30],
  "protected_trichotomy":"reuse -> defect fuel; bank lower merge -> OrdinaryExit; otherwise genuine novel centre",
  "global_collatz":"UNKNOWN"}
 return result
if __name__=="__main__":
 print(json.dumps({"frozen":audit(3,8191,160),"prospective":audit(8193,32767,160)},indent=2))
