#!/usr/bin/env python3
"""Record q0 residence time of current least-counterexample candidates by bit length.

Candidate filter:
  * grammar survives to q0 as RIGID;
  * no direct descent before q0;
  * no immediate inverse-odd P certificate before q0.

Then follow the actual q0 orbit until first T^t(n)<n and record shortcut
steps, odd/even episodes, and the r=v2(d+1) episode sequence.

Finite census only.
"""
from __future__ import annotations
from collections import defaultdict
import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra

def preq0_dp(n):
    k0=n.bit_length(); y=n
    for t in range(1,k0+1):
        y=base.T(y)
        if y<n:return ('D',t,y)
        if y%3==2:
            p=(2*y-1)//3
            if 0<p<n and base.T(p)==y:return ('P',t,y,p)
    return None

def candidate(n):
    if preq0_dp(n) is not None:return False
    ok,_=base.survives_to_q0(n)
    return ok and base.birth_status(n)[0]=='RIGID'

def q0_residence(n,H=5000):
    k0=n.bit_length()
    _,y=base.forward_state(k0,n)
    t=0; eps=0; rseq=[]; sseq=[]
    # count initial even normalization as shortcut residence but not episode
    while t<H and y>=n:
        if y%2==0:
            y=base.T(y);t+=1
            continue
        r,m,s,rp,mp,z=ra.episode(y)
        rseq.append(r);sseq.append(s);eps+=1
        cur=y
        for j in range(1,r+s+1):
            cur=base.T(cur);t+=1
            if cur<n:
                return t,eps,cur,tuple(rseq),tuple(sseq)
            if t>=H:break
        y=cur
    if y<n:return t,eps,y,tuple(rseq),tuple(sseq)
    return None

by=defaultdict(list)
for n in range(3,65536,2):
    if not candidate(n):continue
    q=q0_residence(n)
    by[n.bit_length()].append((n,q))

for k in sorted(by):
    rows=by[k]
    bad=[z for z in rows if z[1] is None]
    good=[z for z in rows if z[1] is not None]
    maxstep=max(good,key=lambda z:z[1][0]) if good else None
    maxep=max(good,key=lambda z:z[1][1]) if good else None
    print("BITS",k,"CANDIDATES",len(rows),"NO_DESCENT_H5000",len(bad))
    print("MAX_STEPS",maxstep)
    print("MAX_EPISODES",maxep)
    if bad:print("BAD_HEAD",bad[:20])
print("TOTAL",sum(len(v) for v in by.values()))
print("STATUS MINIMAL_CANDIDATE_Q0_DESCENT_RECORDS")
