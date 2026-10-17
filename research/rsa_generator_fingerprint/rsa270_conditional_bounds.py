#!/usr/bin/env python3
"""Conditional RSA-270 search-width certificate; NO factoring claim.

Archived RSA list documents p=q=2 (mod 3), approximately balanced.
Hypotheses NOT established for unfactored RSA-270: both prime bitstrings
start 11, and p/q bit lengths are 447/448 as in solved challenge examples.
Counts possible integers p, not divisors; never an algorithmic lower bound.
"""
from pathlib import Path
from json import loads, dumps
from math import isqrt

def interval(n: int, pb: int, qb: int):
    pmin, pmax = 3 * 2**(pb-2), 2**pb-1
    qmin, qmax = 3 * 2**(qb-2), 2**qb-1
    return max(pmin, (n+qmax-1)//qmax), min(pmax, n//qmin)

def count_mod(lo: int, hi: int, residue: int, modulus: int) -> int:
    return (hi-residue)//modulus - (lo-1-residue)//modulus

def measure(n: int, pb: int, qb: int) -> dict:
    assert n.bit_length() == pb + qb
    lo, hi = interval(n, pb, qb)
    width = hi-lo+1
    assert width > 0
    fourth = isqrt(isqrt(n))
    assert fourth**4 <= n < (fourth+1)**4
    possible = count_mod(lo, hi, 5, 6)
    return dict(
        status="EXACT_CONDITIONAL_ARITHMETIC_NOT_FACTORING",
        bits_n=n.bit_length(), assumed_bits_p=pb, assumed_bits_q=qb,
        documented_mod3_rule=True, assumed_11_prefix_unverified_for_RSA270=True,
        interval_size=str(width), interval_size_bit_length=width.bit_length(),
        candidate_integers_p_mod6_eq5=str(possible),
        candidate_bit_length=possible.bit_length(),
        floor_fourth_root_n=str(fourth), fourth_root_bit_length=fourth.bit_length(),
        bits_of_extra_location_information_for_fourth_root_width=(
            (width+fourth-1)//fourth-1
        ).bit_length(),
        factor_found=False,
        limit="Counts congruent integers consistent with hypothesized ranges; "
              "not primes/divisors, an algorithmic lower bound, or proof the "
              "high-bit pattern extends to RSA-270")

def main():
    data = loads(Path(__file__).with_name("data.json").read_text())
    row = next(v for v in data["all"] if v["name"] == "RSA-270")
    n = int(row["n"])
    assert len(str(n)) == 270 and n.bit_length() == 895
    assert n % 991889 == 10237 and n % 6 == 1
    for p, q in [(59,107), (197,401)]:
        assert p%6 == q%6 == 5
        assert bin(p)[2:].startswith("11") and bin(q)[2:].startswith("11")
        lo, hi = interval(p*q, p.bit_length(), q.bit_length())
        assert lo <= p <= hi
        assert p.bit_length()+q.bit_length() == (p*q).bit_length()
    print(dumps(measure(n,447,448),indent=2))

if __name__ == "__main__":
    main()
