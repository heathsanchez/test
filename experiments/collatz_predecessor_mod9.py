#!/usr/bin/env python3
"""Exact 3-adic predecessor certificates for shortcut Collatz."""

def T(n: int) -> int:
    return (3*n+1)//2 if n&1 else n//2

def main():
    # n == 2 mod 3: one odd predecessor p=(2n-1)/3 < n.
    for n in range(2,10000,3):
        p=(2*n-1)//3
        assert p&1 and p<n and T(p)==n

    # n == 4 mod 9: reverse sequence E,O,O gives
    # m=(8n-5)/9 < n and T^3(m)=n.
    for n in range(4,10000,9):
        m=(8*n-5)//9
        assert m&1 and m<n
        x=m
        for _ in range(3): x=T(x)
        assert x==n

    killed={r for r in range(9) if r%3==2 or r==4}
    assert killed=={2,4,5,8}
    print("MOD9_KILLED_RESIDUES",sorted(killed))
    print("MOD9_KILL_FRACTION",f"{len(killed)}/9")
    print("VERIFIED_SHORTCUT_COLLATZ_MOD9_PREDECESSOR_SIEVE")

if __name__=="__main__":
    main()
