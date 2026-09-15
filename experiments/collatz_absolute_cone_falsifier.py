#!/usr/bin/env python3
"""Exact falsifier for any K-independent fixed-horizon Collatz cone claim.

For n=2^M-1 and shortcut Collatz T:
    T^t(n)=3^t*2^(M-t)-1  for 0<=t<=M.

Thus for every fixed H, choose M>H.  During t<=H:
- T^t(n) >= n;
- for t>=1, T^t(n) == 2 (mod 3);
- its one-step inverse-odd predecessor is T^(t-1)(n), which is >= n
  (equal only at t=1).

So neither direct descent nor the one-step cone closes n within H.
This disproves only the over-strong *K-independent fixed-horizon lemma*.
It does NOT disprove Collatz and does NOT touch the bit-length-normalized
rule that first advances K=floor(log2 n) steps.
"""

import argparse


def T(n: int) -> int:
    return (3*n+1)//2 if n & 1 else n//2


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--h",type=int,default=512)
    ap.add_argument("--margin",type=int,default=32)
    a=ap.parse_args()
    H=a.h
    M=H+a.margin
    n=(1<<M)-1
    y=n

    for t in range(H+1):
        expected=(3**t)*(1<<(M-t))-1
        assert y==expected,(t,y,expected)
        assert y>=n,(t,y,n)
        if y%3==2:
            p=(2*y-1)//3
            assert T(p)==y
            assert p>=n,(t,p,n)
            if t==1:
                assert p==n
        if t<H:
            y=T(y)

    print("ABSOLUTE_CONE_COUNTEREXAMPLE_FAMILY",
          f"H={H}",f"M={M}",f"n_bits={n.bit_length()}")
    print("FIXED_HORIZON_FROM_TIME_ZERO_REJECTED")
    print("BIT_LENGTH_NORMALIZED_CONE_NOT_AFFECTED")


if __name__=="__main__":
    main()
