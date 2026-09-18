#!/usr/bin/env python3
"""Complete finite ancestor audit for low-charge high-fuel cycle endpoints.

The low-charge concrete RIGID cycles found so far have two-replay endpoints:
  x=1069   for G(m)=(9m+17)/32,
  x=468713 for G(m)=(729m+467)/512.

A dangerous q=0 lift that is not already direct descent must have source
1 < n <= x and T^k(n)=x with n < 2^k.

For fixed finite x this can be decided exhaustively over every n<=x, with no
reverse-depth horizon.  We memoize deterministic shortcut trajectories until
they either hit x or hit a state already known not to hit x.  A generous hard
guard is only an implementation assertion; the complete finite seed set is
exhausted and every trajectory in these small ranges resolves.

This is endpoint-specific finite certification, not a universal Collatz proof.
"""
from __future__ import annotations


def T(n:int)->int:
    return n//2 if n%2==0 else (3*n+1)//2


def hitting_time(n:int,x:int,memo:dict[int,int|None],guard:int=10000):
    """Return k>=0 with T^k(n)=x, or None if the resolved trajectory misses x."""
    if n in memo:
        return memo[n]
    path=[]
    pos={}
    y=n
    for _ in range(guard):
        if y==x:
            tail=0
            for z in reversed(path):
                tail+=1
                memo[z]=tail
            return memo[n]
        if y in memo:
            t=memo[y]
            if t is None:
                for z in path:
                    memo[z]=None
                return None
            tail=t
            for z in reversed(path):
                tail+=1
                memo[z]=tail
            return memo[n]
        if y in pos:
            # A cycle not containing x.
            for z in path:
                memo[z]=None
            return None
        pos[y]=len(path)
        path.append(y)
        y=T(y)
    raise AssertionError(("trajectory guard exceeded",n,x,y,len(path)))


def audit_endpoint(x:int):
    # 1 is known to miss these nontrivial endpoints; x itself hits at k=0.
    memo={1:None,x:0}
    ancestors=[]
    dangerous=[]
    maxk=0
    for n in range(2,x+1):
        k=hitting_time(n,x,memo)
        if k is None:
            continue
        ancestors.append((n,k))
        maxk=max(maxk,k)
        if k>0 and n < (1<<k):
            dangerous.append((n,k))
    proper=[z for z in ancestors if z[1]>0]
    print("ENDPOINT",x)
    print("SEEDS_EXHAUSTED",x-1)
    print("PROPER_ANCESTORS_LE_X",len(proper))
    print("MAX_HIT_TIME",maxk)
    print("Q0_COMPATIBLE_NON_DIRECT",len(dangerous))
    print("FIRST_PROPER_ANCESTORS",proper[:30])
    if dangerous:
        print("SEPARATOR_COMPLETE_HIGH_FUEL_ENDPOINT",dangerous[:20])
    else:
        print("COMPLETE_NO_Q0_COMPATIBLE_NON_DIRECT_ANCESTOR",x)
    return dangerous


def main():
    bad=[]
    for x in (1069,468713):
        bad.extend((x,)+z for z in audit_endpoint(x))
    print("TOTAL_DANGEROUS",len(bad))
    if bad:
        print("SEPARATOR_LOW_CHARGE_HIGH_FUEL_THEOREM",bad[0])
    else:
        print("PASS_COMPLETE_LOW_CHARGE_HIGH_FUEL_ENDPOINTS")


if __name__=="__main__":
    main()
