#!/usr/bin/env python3
"""Enumerate exact strong-induction predecessor sieves for shortcut Collatz.

Reverse operations from x:
  E: x <- 2x                    (reverse of an even shortcut step)
  O: x <- (2x-1)/3              (reverse of an odd shortcut step)

A reverse word w with r total steps and o O-steps has the exact affine form
    p = (2^r n - c) / 3^o
on one residue class n (mod 3^o).

The first time 2^r < 3^o, every positive n in that residue class has p<n.
Thus strong induction closes the entire class. Descendants need not be searched.

This script enumerates those first-contracting words, independently replays every
certificate, quotients residue-equivalent/redundant certificates, and reports the
exact killed density modulo 3^Q.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass


def T(n: int) -> int:
    return (3 * n + 1) // 2 if n & 1 else n // 2


def reverse_apply(n: int, word: str) -> int | None:
    x = n
    for ch in word:
        if ch == "E":
            x *= 2
        else:
            z = 2 * x - 1
            if z % 3:
                return None
            x = z // 3
            if not (x & 1):
                return None
    return x


@dataclass(frozen=True)
class Cert:
    word: str
    steps: int
    odd_inverse_steps: int
    a: int
    c: int
    d: int
    residue: int


def enumerate_first_contractions(Q: int) -> list[Cert]:
    D = 3**Q
    max_depth = D.bit_length() - 1  # floor(log2(3^Q))
    out: list[Cert] = []

    def visit(word: str, a: int, c: int, d: int, o: int) -> None:
        if len(word) >= max_depth:
            return
        for ch in ("E", "O"):
            if ch == "E":
                na, nc, nd, no = 2 * a, 2 * c, d, o
            else:
                if o >= Q:
                    continue
                na, nc, nd, no = 2 * a, 2 * c + d, 3 * d, o + 1

            nw = word + ch
            if no and na < nd:
                r = (nc * pow(na, -1, nd)) % nd
                cert = Cert(nw, len(nw), no, na, nc, nd, r)

                # Independent exact replay on two members of the congruence class.
                for mult in (5, 17):
                    n = r + mult * nd
                    p = reverse_apply(n, nw)
                    assert p is not None, cert
                    assert p == (na * n - nc) // nd, cert
                    assert p < n, cert
                    x = p
                    for _ in nw:
                        x = T(x)
                    assert x == n, (cert, n, p, x)
                out.append(cert)
            else:
                visit(nw, na, nc, nd, no)

    visit("", 1, 0, 1, 0)
    return out


def quotient(certs: list[Cert], Q: int):
    M = 3**Q
    killed = bytearray(M)
    selected = []
    for c in sorted(certs, key=lambda z: (z.odd_inverse_steps, z.residue, z.steps, z.word)):
        added = 0
        for r in range(c.residue, M, c.d):
            if not killed[r]:
                killed[r] = 1
                added += 1
        if added:
            selected.append((c, added))
    return killed, selected


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", type=int, default=7)
    A = ap.parse_args()
    assert 1 <= A.q <= 14

    certs = enumerate_first_contractions(A.q)
    killed, selected = quotient(certs, A.q)
    M = len(killed)
    K = sum(killed)

    print("REVERSE_TREE_Q", A.q)
    print("FIRST_CONTRACTION_CERTIFICATES", len(certs))
    print("NONREDUNDANT_CERTIFICATES", len(selected))
    for c, added in selected:
        print(
            "CERT",
            f"word={c.word}",
            f"steps={c.steps}",
            f"odd_inverse_steps={c.odd_inverse_steps}",
            f"mod={c.d}",
            f"residue={c.residue}",
            f"predecessor=({c.a}*n-{c.c})/{c.d}",
            f"new_mod_3q_residues={added}",
        )
    print("KILLED_RESIDUES", K)
    print("TOTAL_RESIDUES", M)
    print("KILL_FRACTION", f"{K}/{M}", f"{K/M:.12f}")
    print("LIVE_FRACTION", f"{M-K}/{M}", f"{(M-K)/M:.12f}")

    if A.q >= 2:
        assert K * 9 >= 4 * M  # must contain the exact mod-9 sieve
    if A.q == 7:
        assert (K, M) == (1013, 2187)
        expected = {
            (3, 2), (9, 4), (81, 10), (729, 433), (729, 604),
            (2187, 205), (2187, 325), (2187, 919), (2187, 991),
            (2187, 1000), (2187, 1090), (2187, 1171), (2187, 2170),
        }
        got = {(c.d, c.residue) for c, _ in selected}
        assert got == expected, got

    print("VERIFIED_SHORTCUT_COLLATZ_REVERSE_PREDECESSOR_TREE")


if __name__ == "__main__":
    main()
