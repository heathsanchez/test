#!/usr/bin/env python3
"""Exact mod-3 obstruction for q=0-compatible endpoint ancestry.

For the shortcut map T(n)=n/2 (even), (3n+1)/2 (odd), reverse predecessors of
an endpoint x are:
    E: 2x, always;
    O: (2x-1)/3, only when this is a positive odd integer.

If 3 | x, then 3 | 2^j x for every j, so the O predecessor is unavailable at
every reverse depth.  Therefore the unique depth-k predecessor is 2^k x.
For x>1 this is >2^k, hence it cannot be a q=0-compatible source n<2^k.

For the C9 two-replay endpoint family
    x(q)=468713 + 2^20 q,
we have x(q) == q+2 (mod 3), because 2^20 == 1 (mod 3) and 468713 == 2.
Thus every q == 1 (mod 3) lift is universally impossible as a q=0 endpoint.

Pure arithmetic theorem/check; no Collatz convergence claim.
"""
from __future__ import annotations
import argparse

B=468713
M=1<<20

def endpoint(q:int)->int:
    return B+M*q

def main(K:int):
    assert M%3==1
    assert B%3==2
    for q in range(K):
        x=endpoint(q)
        assert x%3==(q+2)%3
        if q%3!=1:
            continue
        assert x%3==0
        # Exact induction consequence for a sample of depths.
        for k in range(1,65):
            n=(1<<k)*x
            assert n>(1<<k)
            # An odd reverse predecessor from any E-only ancestor is impossible.
            y=(1<<(k-1))*x
            assert y%3==0
            assert (2*y-1)%3!=0
    print("C9_ENDPOINT_FAMILY",B,M)
    print("IMPOSSIBLE_Q_CLASS_MOD3 1")
    print("PROSPECTIVE_Q562_ENDPOINT",endpoint(562))
    print("PROSPECTIVE_Q562_MOD3",endpoint(562)%3)
    print("PASS_Q0_ENDPOINT_MOD3_OBSTRUCTION")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--q-limit",type=int,default=4096)
    a=ap.parse_args()
    main(a.q_limit)
