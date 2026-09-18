#!/usr/bin/env python3
"""Fast prospective frozen-H71 gate with sound direct-descent prefilter.

Direct descent within H is already terminal, so expensive Complete-O checks
are needed only for raw H-step non-descenders.
"""
from __future__ import annotations
import argparse
from collections import Counter
import collatz_q0_rigid_recharge_audit as ra
import collatz_q0_coalescence_component_audit as base
import collatz_reverse_episode_bfs_probe as rb

def raw_survives(n,H):
    y=n
    for d in range(1,H+1):
        y=base.T(y)
        if y<n:return False,(d,y)
    return True,y

def rigid_survives(n,H):
    k0=n.bit_length()
    if ra.q0_status(k0,n)!='RIGID':return False,('birth',ra.q0_status(k0,n))
    for d in range(1,H+1):
        st=ra.q0_status(k0+d,n)
        if st!='RIGID':return False,(d,k0+d,st)
    return True,None

def reverse_close(n,K):
    starts,branches=ra.rigid_episode_segment(n,K)
    best=None
    for k,r,m,x in starts:
        row,b=rb.search_from_endpoint(n,x,4,28,20,12)
        if b is not None:
            q=(b[0],k)+b[1:]
            if best is None or q<best:best=q
        if row is not None:return (k,row),best
    return None,best

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=8193)
    ap.add_argument("--hi",type=int,default=32767)
    ap.add_argument("--H",type=int,default=71)
    ap.add_argument("--K",type=int,default=130)
    a=ap.parse_args()
    cnt=Counter();cands=[];rigid=[];sep=[];closed=[]
    start=a.lo if a.lo%2 else a.lo+1
    for n in range(start,a.hi+1,2):
        cnt['odd']+=1
        ok,info=raw_survives(n,a.H)
        if not ok:
            cnt['raw_direct']+=1;continue
        cnt['raw_survive']+=1;cands.append(n)
        ok2,why=rigid_survives(n,a.H)
        if not ok2:
            cnt['complete_o_close']+=1;continue
        cnt['rigid_survive_H']+=1;rigid.append(n)
        rev,best=reverse_close(n,a.K)
        if rev is None:
            cnt['separator']+=1;sep.append((n,best));print("H71_SEPARATOR",n,best,flush=True)
        else:
            cnt['reverse_close']+=1;closed.append((n,rev));print("H71_REVERSE_CLOSE",n,rev,flush=True)
    print("SOURCE_RANGE",a.lo,a.hi,"H",a.H)
    print("COUNTS",dict(cnt))
    print("RAW_SURVIVORS",cands)
    print("RIGID_SURVIVORS",rigid)
    print("SEPARATORS",sep)
    if sep:print("FAIL_FROZEN_H71",sep[0])
    else:print("PASS_FROZEN_H71_HELDOUT")
    print("STATUS FAST_FROZEN_H71_GATE")

if __name__=="__main__":main()
