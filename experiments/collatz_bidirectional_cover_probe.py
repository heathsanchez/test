#!/usr/bin/env python3
"""Bidirectional tradeoff: forward RIGID survival vs reverse lower-merge depth.

For each q=0 RIGID source in a bounded corpus:
  * measure exact forward RIGID lifetime until first non-RIGID classifier state;
  * search reverse-episode lower merges with a fixed small budget.

The key quantity is the maximum forward RIGID lifetime among sources for which
the reverse search fails. If reverse-hard cases are uniformly short-lived,
forward termination + reverse closure may form a bidirectional certificate.
"""
from __future__ import annotations
import argparse
from collections import Counter
import collatz_q0_rigid_recharge_audit as ra
import collatz_q0_coalescence_component_audit as base
import collatz_reverse_episode_bfs_probe as rb

def forward_lifetime(n,K):
    k0=n.bit_length()
    if ra.q0_status(k0,n)!='RIGID':
        return 0,(k0,ra.q0_status(k0,n))
    for k in range(k0+1,K+1):
        st=ra.q0_status(k,n)
        if st!='RIGID':
            return k-k0,(k,st,base.cylinder_status(k,n))
    return None,None

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

def audit(lo,N,K,maxep,maxsteps,Rmax,Smax):
    rows=[];hard=[];closed=[];censored=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,N+1,2):
        k0=n.bit_length()
        if ra.q0_status(k0,n)!='RIGID':continue
        starts,branches=ra.rigid_episode_segment(n,K)
        if not branches:continue
        life,exitinfo=forward_lifetime(n,K)
        rev,best=reverse_close(n,K,maxep,maxsteps,Rmax,Smax)
        row=(n,k0,life,exitinfo,rev,best,len(branches))
        rows.append(row)
        if rev is None:
            hard.append(row)
        else:
            closed.append(row)
        if life is None:censored.append(row)

    finite_hard=[z for z in hard if z[2] is not None]
    finite_closed=[z for z in closed if z[2] is not None]
    print("SOURCE_RANGE",lo,N)
    print("SOURCES",len(rows),"REVERSE_CLOSED",len(closed),"REVERSE_HARD",len(hard))
    print("FORWARD_CENSORED",len(censored))
    print("HARD_MAX_LIFETIME",max((z[2] for z in finite_hard),default=None))
    print("CLOSED_MAX_LIFETIME",max((z[2] for z in finite_closed),default=None))
    hist=Counter(z[2] for z in finite_hard)
    print("HARD_LIFETIME_HIST",dict(sorted(hist.items())))
    print("HARD_LONGEST",sorted(finite_hard,key=lambda z:z[2],reverse=True)[:40])
    print("CLOSED_LONGEST",sorted(finite_closed,key=lambda z:z[2],reverse=True)[:20])
    # For thresholds H, test whether every source surviving >H is reverse-closed.
    maxlife=max((z[2] for z in rows if z[2] is not None),default=0)
    for H in range(0,min(maxlife,80)+1):
        survivors=[z for z in rows if z[2] is None or z[2]>H]
        bad=[z for z in survivors if z[4] is None]
        if not bad:
            print("BIDIRECTIONAL_COVER_THRESHOLD",H,
                  "SURVIVORS",len(survivors),"ALL_REVERSE_CLOSED")
            break
    else:
        print("NO_BIDIRECTIONAL_COVER_THRESHOLD_WITHIN_RANGE")
    print("STATUS BIDIRECTIONAL_FORWARD_REVERSE_SPIKE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=3)
    ap.add_argument("--N",type=int,default=8191)
    ap.add_argument("--K",type=int,default=100)
    ap.add_argument("--maxepisodes",type=int,default=4)
    ap.add_argument("--maxsteps",type=int,default=28)
    ap.add_argument("--Rmax",type=int,default=20)
    ap.add_argument("--Smax",type=int,default=12)
    a=ap.parse_args()
    audit(a.lo,a.N,a.K,a.maxepisodes,a.maxsteps,a.Rmax,a.Smax)
