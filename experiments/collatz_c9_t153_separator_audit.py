#!/usr/bin/env python3
"""Exact audit of the first discovered non-direct three-replay endpoint ancestor.

Candidate:
    t = 153
    x = 326575849 + 153*2^29 = 82467825385
    n = 30098547115
    T^35(n) = x

The source satisfies n < 2^35 and n < x, so it is q=0-compatible and
non-direct at the endpoint.  This audit asks the decisive questions:

  1. does n survive every pre-q0 symbolic decision?
  2. is its q=0 birth exactly RIGID?
  3. if so, how long until the first non-RIGID boundary state / direct descent?
  4. does an immediate lower-predecessor certificate appear earlier?

Exact targeted audit only; not a Collatz proof.
"""
from __future__ import annotations
import argparse

import collatz_q0_coalescence_component_audit as base

N=30098547115
K=35
T_LIFT=153
X=82467825385


def first_direct(n:int,H:int):
    y=n
    for t in range(1,H+1):
        y=base.T(y)
        if y<n:
            return t,y
    return None


def first_immediate_lower_predecessor(n:int,H:int):
    y=n
    for t in range(H+1):
        if y%3==2:
            p=(2*y-1)//3
            if 0<p<n and base.T(p)==y:
                return t,y,p
        y=base.T(y)
    return None


def main(H:int):
    y=N
    for _ in range(K):
        y=base.T(y)
    assert y==X,(y,X)
    assert N < (1<<K)
    assert N < X

    print("SOURCE",N)
    print("BIT_LENGTH",N.bit_length())
    print("Q0_DEPTH",K)
    print("THREE_REPLAY_LIFT_T",T_LIFT)
    print("Q0_ENDPOINT",X)
    print("Q0_COMPATIBLE",N < (1<<K))
    print("NON_DIRECT_AT_ENDPOINT",N < X)

    survives,detail=base.survives_to_q0(N)
    birth=base.birth_status(N)
    print("SURVIVES_TO_Q0",survives,detail)
    print("BIRTH_STATUS",birth)

    direct=first_direct(N,H)
    pred=first_immediate_lower_predecessor(N,H)
    print("FIRST_DIRECT",direct)
    print("FIRST_IMMEDIATE_LOWER_PREDECESSOR",pred)

    first_non=None
    _,z=base.forward_state(K,N)
    for k in range(K,K+H+1):
        if k>K:
            z=base.T(z)
        out,data=base.cylinder_status(k,N)
        if out!="RIGID":
            first_non=(k,z,out,data)
            break
    print("FIRST_NONRIGID_FROM_Q0",first_non)

    if survives and birth[0]=="RIGID":
        print("PASS_T153_IS_HEREDITARY_Q0_RIGID_SEPARATOR")
    else:
        print("T153_CLOSED_BEFORE_HEREDITARY_RIGID")

    if direct is not None or pred is not None:
        print("T153_HAS_BOUNDED_LOWER_MERGE_CERTIFICATE")
    else:
        print("T153_REMAINS_UNCLOSED_WITHIN_HORIZON")

    print("STATUS EXACT_TARGETED_T153_AUDIT")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--H",type=int,default=2048)
    a=ap.parse_args()
    main(a.H)
