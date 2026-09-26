#!/usr/bin/env python3
"""Exact checks for the coefficient-corridor packing theorem; not Collatz closure."""
from __future__ import annotations
from fractions import Fraction
from math import comb
import hashlib, json
from pathlib import Path


def mul(a, b):
    c = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            c[i+j] += x*y
    return c


def certify() -> dict:
    # Exact coefficient identity, independent of trajectory enumeration.
    left = mul([0]*6+[729], [1,1])
    right = mul([comb(6,k)*3**k for k in range(7)], [-1,1])
    difference = [a-b for a,b in zip(left,right)]
    assert difference == [1,17,117,405,675,243,0,0]
    assert all(c >= 0 for c in difference) and difference[0] > 0
    assert Fraction(4,3)**6 > 3  # unshifted telescoping would be false
    assert Fraction(16,15)**60 > Fraction(24,4)  # duplicates invalidate packing
    paths = windows = 0
    max_depth = max_odds = 0
    digest = hashlib.sha256()
    for n in range(3, 8192, 2):
        y, A, B, q = n, 1, 1, 0
        odd_values = []
        correction = Fraction(1)
        largest_rho = Fraction(1)
        for j in range(1, 513):
            # The packed values are the odd terms before the endpoint.
            if y & 1:
                odd_values.append(y)
                correction *= Fraction(3*y+1,3*y)
                q += 1
                A *= 3
                y = (3*y+1)//2
            else:
                y //= 2
            B *= 2
            rho = Fraction(A,B)
            if rho < 1:
                break
            assert y >= n and len(set(odd_values)) == q
            largest_rho = max(largest_rho,rho)
            P = Fraction(y*B,n*A)
            assert P == correction
            # Exact telescoping upper envelope; both comparisons are integers.
            assert P**6 < Fraction(n+2*q-1,n-1)
            C = (largest_rho.numerator+largest_rho.denominator-1)//largest_rho.denominator
            L = n+2*q-2
            assert (n-1)*L**6 < C**6*n**6*(L+1)
            assert q < C*C*n
            windows += 1
            digest.update(f'{n},{j},{q},{C},{y}\n'.encode())
        else:
            raise AssertionError(f'unresolved finite probe: {n}')
        paths += 1
        max_depth = max(max_depth,j)
        max_odds = max(max_odds,q)
    return {
        'schema':'COLLATZ_COEFFICIENT_CORRIDOR_V1',
        'parent_head':'cb65e7143aded6744f464da00fe98f9dd64af488',
        'global_collatz':'UNKNOWN',
        'status':'ELEMENTARY_ALL_DEPTH_CONDITIONAL_THEOREM_AND_EXACT_FINITE_CHECKS',
        'polynomial_identity_coefficients_low_to_high':difference,
        'finite_odd_sources':paths,
        'source_interval':'3<=n<8192, odd',
        'coefficient_live_prefixes_checked':windows,
        'largest_first_crossing_in_probe':max_depth,
        'largest_odd_count_at_first_crossing':max_odds,
        'trace_sha256':digest.hexdigest(),
        'telescoping':'P^6 < (n+2q-1)/(n-1) for distinct odd terms >= odd n>=3',
        'corridor':'If all prefix coefficients are <= integer C>=1, then q<C^2*n, under the distinct-odd/no-descent hypotheses.',
        'infinite_consequence':'A positive never-coefficient-crossing orbit has unbounded prefix coefficients.',
        'rank_boundary':'C is fixed. Raising C replenishes the budget; no global rank is obtained.',
        'reset_counterexample':{'source':3,'before':{'q':0,'C':1,'budget':3},'after':{'q':1,'C':2,'budget':11}},
        'not_proved':['a source-dependent global upper bound on coefficients','global exclusion of never-crossing sources','unbounded canonical M-negativity'],
        'verification_boundary':'Full corridor and infinite consequence have written elementary proofs; exact polynomial identity and finite path inequalities replayed here. The factor comparison and arbitrary-length Packed-list telescoping theorem are separately submitted to Lean; the actual-orbit sorting and corridor-exhaustion application are not Lean formalized. No global Lean proof claimed.',
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }

if __name__ == '__main__':
    print(json.dumps(certify(),indent=2,sort_keys=True))
