#!/usr/bin/env python3
"""Compare exact Collatz rescue operators on known H512 boundary seeds.

For each supplied odd seed n, scan the shortcut trajectory and record the
first t at which each nested consequence operator gives a lower witness:

D: direct descent, y < n.
O1: one inverse odd step, y == 2 mod 3 and (2y-1)/3 < n.
O*: maximal inverse-odd cone, r=v3(y+1),
    p=2^r*(y+1)/3^r - 1 < n.

O* strictly contains O1 as a consequence test.  All witnesses are replayed.
"""

from __future__ import annotations

SEEDS = [
    (33, 12235060455),
    (33, 14500812391),
]


def T(n: int) -> int:
    return (3*n+1)//2 if n & 1 else n//2


def v3(x: int) -> int:
    r=0
    while x % 3 == 0:
        x//=3
        r+=1
    return r


def scan(K: int, n: int, H: int = 4096):
    y=n
    first={"D":None,"O1":None,"O*":None}
    witness={}

    for t in range(H+1):
        if first["D"] is None and y<n:
            first["D"]=t
            witness["D"]=y

        if y%3==2:
            p=(2*y-1)//3
            if 0<p<n and first["O1"] is None:
                assert T(p)==y
                first["O1"]=t
                witness["O1"]=p

        r=v3(y+1)
        if r:
            p=(2**r)*((y+1)//(3**r))-1
            if 0<p<n and first["O*"] is None:
                z=p
                for _ in range(r):
                    z=T(z)
                assert z==y
                first["O*"]=t
                witness["O*"]=(p,r)

        if all(x is not None for x in first.values()):
            break
        y=T(y)

    print("BOUNDARY_OPERATOR_COMPARE",
          f"K={K}",f"n={n}",
          f"direct_t={first['D']}",
          f"one_step_t={first['O1']}",
          f"maximal_o_t={first['O*']}",
          f"one_step_postK={None if first['O1'] is None else first['O1']-K}",
          f"maximal_o_postK={None if first['O*'] is None else first['O*']-K}")
    return first


def main():
    for K,n in SEEDS:
        first=scan(K,n)
        assert first["O1"] is not None
        assert first["O*"] is not None
        assert first["O*"] <= first["O1"]
    print("VERIFIED_BOUNDARY_OPERATOR_COMPARISON")


if __name__=="__main__":
    main()
