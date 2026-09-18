#!/usr/bin/env python3
"""Focused audit of the three observed 17-bit near misses to the C9 high-fuel cylinder.

Target endpoint residue:
    x == 468713 (mod 2^20).

The full million-source census found exactly three hereditary-q0-birth orbit
states matching the target through 17 low bits and none through 18.

For every >=17-bit match, this script records:
  * source/depth/endpoint and target difference;
  * whether the entire post-q0 prefix to that state remained RIGID;
  * C9 composite-cycle defect valuation v2((2^9-729)m-467);
  * exact replay budget floor((V-1)/9);
  * the first non-RIGID state during one C9 replay when the word is admissible.

Bounded diagnostic only; not a Collatz proof.
"""
from __future__ import annotations
import argparse

import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra

TARGET=468713
FULL_BITS=20
MATCH_BITS=17
A=729; B=467; D=9; R=1
C=(1<<D)-A
WORD=((1,1,4),(4,1,1),(1,1,1))
CERT=ra.certificate(WORD)
L=sum(r+s for r,s,rp in WORD)


def v2(x:int)->int:
    if x==0: return 10**9
    x=abs(x)
    return (x & -x).bit_length()-1


def prefix_rigid(n:int,k0:int,k1:int):
    for k in range(k0,k1+1):
        out,data=base.cylinder_status(k,n)
        if out!='RIGID':
            return False,(k,out,data)
    return True,None


def replay_diagnostic(n:int,k:int,y:int):
    m=(y+1)//2
    V=v2(C*m-B)
    budget=(V-1)//D
    admissible=ra.admissible(CERT,m)
    row={'m':m,'V':V,'budget':budget,'admissible':admissible}
    if not admissible:
        return row
    m1=ra.replay(CERT,m)
    z=y; kk=k; first_non=None
    for _ in range(L):
        z=base.T(z); kk+=1
        if first_non is None:
            out,data=base.cylinder_status(kk,n)
            if out!='RIGID':
                first_non=(kk,out,data,z)
    assert z==2*m1-1
    row.update({'m1':m1,'end_y':z,'end_k':kk,'first_nonrigid':first_non})
    return row


def audit(N:int,H:int):
    mask=(1<<MATCH_BITS)-1
    target17=TARGET&mask
    rows=[]
    for n in range(3,N+1,2):
        if base.birth_status(n)[0]!='RIGID':
            continue
        survives,_=base.survives_to_q0(n)
        if not survives:
            continue
        k0=n.bit_length()
        _,y=base.forward_state(k0,n)
        for t in range(H+1):
            if t: y=base.T(y)
            if y&mask != target17:
                continue
            k=k0+t
            j=min(FULL_BITS,v2(y-TARGET))
            if j<MATCH_BITS:
                continue
            rigid,why=prefix_rigid(n,k0,k)
            diag=replay_diagnostic(n,k,y)
            row=(n,k0,t,k,y,j,y-TARGET,(y-TARGET)>>MATCH_BITS,
                 y%(1<<FULL_BITS),rigid,why,diag)
            rows.append(row)
            print("C9_NEAR_MISS",row)
    print("NEAR_MISS_COUNT",len(rows))
    print("RIGID_NEAR_MISS_COUNT",sum(1 for r in rows if r[9]))
    print("MAX_MATCH_BITS",max((r[5] for r in rows),default=None))
    print("FUEL_VALUES",[(r[0],r[11]['V'],r[11]['budget']) for r in rows])
    if any(r[5]>=18 for r in rows):
        print("SEPARATOR_C9_18BIT_MATCH_FOUND")
    else:
        print("OBSERVED_C9_NEAR_MISSES_STOP_AT_17_BITS")
    print("STATUS BOUNDED_NEAR_MISS_DIAGNOSTIC_ONLY")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--N",type=int,default=(1<<20)-1)
    ap.add_argument("--H",type=int,default=512)
    a=ap.parse_args()
    audit(a.N,a.H)
