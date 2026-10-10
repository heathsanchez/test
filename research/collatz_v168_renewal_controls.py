"""V168: exact finite negative controls for quantitative Collatz renewal.
No global convergence theorem is asserted. Formal Lean promotion NOT claimed.
"""
from collections import Counter
from fractions import Fraction
from math import log


def step(n: int, c: int = 1) -> int:
    assert n > 0 and c > 0 and c % 2
    return n // 2 if n % 2 == 0 else (3 * n + c) // 2


def parity_word(n: int, c: int, h: int) -> int:
    bits = 0
    for j in range(h):
        bits |= (n % 2) << j
        n = step(n, c)
    return bits


def cycle(start: int, c: int, cap: int = 100) -> list[int]:
    values = [start]
    n = step(start, c)
    while n != start:
        assert n not in values and len(values) < cap
        values.append(n)
        n = step(n, c)
    return values


def cycle_affine_data(values: list[int], c: int) -> dict:
    a, B = 0, 0
    for i, n in enumerate(values):
        if n % 2:
            B = 3 * B + 2**i
            a += 1
        assert step(n, c) == values[(i + 1) % len(values)]
    D = 2 ** len(values) - 3**a
    assert D > 0 and D * values[0] == c * B
    return {'length': len(values), 'odd_steps': a, 'B': B, 'D': D,
            'T1_rational_start': str(Fraction(B, D))}


def bad_seven_below(X: int) -> int:
    return X - 1 - (X - 1) // 7


def reverse_renewal(X: int, c: int, good_or_bad) -> int:
    evens = sum(good_or_bad(y) for y in range(1, (X + 1) // 2))
    odds = 0
    for y in range((3 + c) // 2, (3 * X + c + 1) // 2):
        q = 2 * y - c
        if q > 0 and q % 3 == 0 and 0 < q // 3 < X:
            assert (q // 3) % 2 == 1
            odds += good_or_bad(y)
    return evens + odds


def main() -> None:
    assert cycle(7, 7) == [7, 14]
    assert cycle(5, 7) == [5, 11, 20, 10]
    for n in range(1, 50001):
        assert (n % 7 != 0) == (step(n, 7) % 7 != 0)
    print('G7 primitive class invariant: 50000 finite checks')
    for c in (1, 5, 7):
        for h in range(1, 11):
            words = {parity_word(n, c, h) for n in range(1, 2**h + 1)}
            assert words == set(range(2**h))
    print('Parity-word bijections: intercepts 1,5,7; horizons 1..10')
    for h in range(1, 10):
        hist = Counter(parity_word(n, 7, h)
                       for n in range(1, 7 * 2**h + 1) if n % 7 != 0)
        assert len(hist) == 2**h and set(hist.values()) == {6}
    print('G7 conditional bad-set parity exactly uniform: horizons 1..9')
    bad = lambda y: int(y > 0 and y % 7 != 0)
    for X in (8, 13, 27, 50, 64, 101, 1024, 16384):
        assert reverse_renewal(X, 7, bad) == bad_seven_below(X)
    print('G7 guarded reverse-source renewal: eight height cutoffs')
    values = cycle(187, 5)
    assert len(values) == 27 and min(values) == 187
    data = cycle_affine_data(values, 5)
    assert (data['odd_steps'], data['D'], data['B']) == (
        17, 5077565, 189900931)
    assert data['T1_rational_start'] == '187/5'
    assert cycle(19, 5) != values and cycle(5, 5) != values
    print('G5 high-odd cycle and exact T1 rational shadow:', data)
    for M in range(1, 50):
        for q in (1, 3, 11):
            y = 3 * M * q - 1
            p = 2 * M * q - 1
            assert 0 < p < y and p % M == y % M
            assert p % 2 == 1 and step(p, 1) == y
    print('Adverse inverse-odd periodic-residue edge: 147 controls')
    theta = log(2) / log(10 / 3)
    assert theta > 4 / 7 and 10**4 < 3**4 * 2**7
    print('Minimum-orbit necessary odd-step threshold >4/7')
    print('STATUS: BOUNDED_EXACT; NO SPECTRAL GAP, COLLATZ UNKNOWN')


if __name__ == '__main__':
    main()
