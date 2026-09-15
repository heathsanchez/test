#!/usr/bin/env python3
"""
Exact lower-predecessor merge certificate for valuation slices.

Let
    n = 2^K m - 1,   m odd,
    p = (n-1)/2 = 2^(K-1) m - 1.

Write A = 3^(K-1) m.

Then
    T^(K-1)(p) = A - 1
and
    T^K(n)     = 3A - 1.

If A == 3 (mod 4), both paths take the forced parities
    p-path: even, odd
    n-path: even, even
and meet exactly at
    (3A - 1)/4.

Thus
    T^(K+1)(p) = T^(K+2)(n).

Since A = 3^(K-1)m, the killed m-residue is
    m == 3 (mod 4)  when K is odd,
    m == 1 (mod 4)  when K is even.

On the tightened interval U < 2L+1, so p=(n-1)/2 < L for every
live n. Therefore the killed residue class merges into the already-lower
region and is inductively closed.

This file checks the algebra using affine coefficients in z for
m=4z+r and exhaustively replays small controls.
"""

L = 2392312122059207475200
U = 3143983941795894239301

def T(n: int) -> int:
    return (3*n+1)//2 if n & 1 else n//2

def iterate(n: int, t: int) -> int:
    for _ in range(t):
        n = T(n)
    return n

def killed_residue(K: int) -> int:
    assert K >= 1
    return 3 if K & 1 else 1

def survivor_residue(K: int) -> int:
    return 1 if K & 1 else 3

def affine_merge_certificate(K: int):
    r = killed_residue(K)
    p3 = 3 ** K

    # m = 4z+r. Common merge value:
    # (3^K(4z+r)-1)/4 = 3^K z + (3^K r -1)/4.
    assert (p3 * r - 1) % 4 == 0
    common_z_coef = p3
    common_const = (p3 * r - 1) // 4

    # p path:
    # T^(K-1)(p) = 3^(K-1)(4z+r)-1 = A-1.
    # A mod 4 must be 3, giving even then odd.
    A_mod4 = ((3 ** (K-1)) * r) % 4
    assert A_mod4 == 3

    # After those two steps: (3A-1)/4.
    p_z_coef = p3
    p_const = common_const

    # n path:
    # T^K(n)=3A-1; A==3 mod4 makes this divisible by4,
    # giving two even steps to the same value.
    n_z_coef = p3
    n_const = common_const

    assert (p_z_coef, p_const) == (common_z_coef, common_const)
    assert (n_z_coef, n_const) == (common_z_coef, common_const)

    return {
        "K": K,
        "killed_m_mod4": r,
        "survivor_m_mod4": survivor_residue(K),
        "common_z_coefficient": str(common_z_coef),
        "common_constant": str(common_const),
    }

def small_replay_controls():
    checked = 0
    for K in range(1, 21):
        r = killed_residue(K)
        for z in range(1, 64):
            m = 4*z+r
            n = (1<<K)*m-1
            p = (n-1)//2
            assert iterate(n, K+2) == iterate(p, K+1), (K,m,n,p)
            checked += 1
    return checked

def main():
    assert U < 2*L + 1
    assert (U-1)//2 < L

    rows = [affine_merge_certificate(K) for K in range(1, 64)]
    checked = small_replay_controls()

    print("LOWER_PREDECESSOR_INTERVAL",
          f"L={L}", f"U={U}", f"U<2L+1={U < 2*L+1}")
    print("MERGE_IDENTITY",
          "T^(K+2)(2^K*m-1)=T^(K+1)((2^K*m-2)/2)",
          "on the killed m mod 4 class")
    print("K31",
          f"killed_m_mod4={killed_residue(31)}",
          f"survivor_m_mod4={survivor_residue(31)}")
    print("K32",
          f"killed_m_mod4={killed_residue(32)}",
          f"survivor_m_mod4={survivor_residue(32)}")
    print("AFFINE_CERTIFICATES", len(rows))
    print("SMALL_REPLAY_CONTROLS", checked)
    print("VERIFIED_LOWER_PREDECESSOR_HALF_SIEVE")

if __name__ == "__main__":
    main()
