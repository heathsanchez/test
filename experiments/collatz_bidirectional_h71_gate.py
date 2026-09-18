#!/usr/bin/env python3
"""Optimized prospective gate for the frozen H=71 bidirectional candidate.

For each source in a held-out range:
  1. if q=0 birth is not RIGID, ignore;
  2. if RIGID exits within H=71 depths, covered by forward closure;
  3. only if it survives beyond H, run the frozen reverse search
     (4 episodes, 28 reverse shortcut steps, R<=20, S<=12).

Any >H survivor with no reverse certificate is the exact separator.
"""
from __future__ import annotations
import argparse
from collections import Counter
import collatz_q0_rigid_recharge_audit as ra
import collatz_reverse_episode_bfs_probe as rb

def survives_H(n,H):
    k0=n.bit_length()
    if ra.q0_status(k0,n)!='RIGID':
        return False,None
    for d in range(1,H+1):
        st=ra.q0_status(k0+d,n)
        if st!='RIGID':
            return False,(d,k0+d,st)
    return True,None

def reverse_close(n,K,maxep,maxsteps,Rmax,Smax):
    starts,branches=ra.rigid_episode_segment(n,K)
    if not branches:return None,None
    best=None
    for k,r,m,x in starts:
        row,b=rb.search_from_endpoint(n,x,maxep,maxsteps,Rmax,Smax)
        if b is not None:
            q=(b[0],k)+b[1:]
            if best is None or q<best:best=q
        if row is not None:
            return (k,row),best
    return None,best

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=8193)
    ap.add_argument("--hi",type=int,default=32767)
    ap.add_argument("--H",type=int,default=71)
    ap.add_argument("--K",type=int,default=130)
    a=ap.parse_args()
    cnt=Counter();survivors=[];separators=[];closed=[]
    start=a.lo if a.lo%2 else a.lo+1
    for n in range(start,a.hi+1,2):
        k0=n.bit_length()
        if ra.q0_status(k0,n)!='RIGID':
            continue
        cnt['birth_rigid']+=1
        alive,exitinfo=survives_H(n,a.H)
        if not alive:
            cnt['forward_closed_by_H']+=1
            continue
        cnt['survive_H']+=1;survivors.append(n)
        rev,best=reverse_close(n,a.K,4,28,20,12)
        if rev is None:
            cnt['separator']+=1
            separators.append((n,best))
            print("H71_SEPARATOR",n,"best",best)
        else:
            cnt['reverse_closed']+=1
            closed.append((n,rev))
            print("H71_REVERSE_CLOSE",n,rev)
    print("SOURCE_RANGE",a.lo,a.hi,"H",a.H)
    print("COUNTS",dict(cnt))
    print("SURVIVORS",survivors)
    print("REVERSE_CLOSED",closed)
    print("SEPARATORS",separators)
    if separators:
        print("FAIL_FROZEN_H71",separators[0])
    else:
        print("PASS_FROZEN_H71_HELDOUT")
    print("STATUS PROSPECTIVE_FROZEN_BIDIRECTIONAL_GATE")

if __name__=="__main__":
    main()
