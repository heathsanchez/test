#!/usr/bin/env python3
"""Sparse exact reverse-predecessor quotient for shortcut Collatz.

This is mathematically equivalent to collatz_reverse_predecessor_tree.py but
never materializes a bytearray of length 3^Q.

Each first-contracting reverse word yields one exact congruence cylinder

    n == residue (mod 3^o)

and an exact lower predecessor

    p = (2^r n - c) / 3^o < n,
    T^r(p) = n.

Because every modulus is a power of 3, two such cylinders are either disjoint
or nested.  Therefore quotienting is sparse:

- process certificates in increasing o;
- reject a certificate iff one of its coarser base-3 prefixes has already
  been retained;
- otherwise retain it;
- at target Q its exact contribution is 3^(Q-o) residue classes.

So the exact union census is

    killed(Q) = sum_{retained c} 3^(Q-o(c))

without enumerating any of the 3^Q residues.

The enumeration itself still explores all first-contracting reverse words.
This experiment isolates that true combinatorial cost from the avoidable
3^Q residue-materialization cost.
"""

from __future__ import annotations

import argparse
from collections import Counter
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
    o: int
    a: int
    c: int
    d: int
    residue: int


def enumerate_first_contractions(Q: int) -> list[Cert]:
    D = 3**Q
    max_depth = D.bit_length() - 1
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
                residue = (nc * pow(na, -1, nd)) % nd
                cert = Cert(nw, len(nw), no, na, nc, nd, residue)

                # Independent exact controls on two positive members.
                for mult in (5, 17):
                    n = residue + mult * nd
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


def sparse_quotient(certs: list[Cert], Q: int):
    powers = [1]
    for _ in range(Q):
        powers.append(powers[-1] * 3)

    # selected_by_o[o] stores exact retained residues modulo 3^o.
    selected_by_o: list[set[int]] = [set() for _ in range(Q + 1)]
    selected: list[Cert] = []
    covered_redundant = 0

    for cert in sorted(certs, key=lambda z: (z.o, z.residue, z.steps, z.word)):
        covered = False
        for j in range(1, cert.o + 1):
            if (cert.residue % powers[j]) in selected_by_o[j]:
                covered = True
                break

        if covered:
            covered_redundant += 1
            continue

        selected_by_o[cert.o].add(cert.residue)
        selected.append(cert)

    killed = sum(powers[Q - cert.o] for cert in selected)
    total = powers[Q]
    return killed, total, selected, covered_redundant


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", type=int, required=True)
    args = ap.parse_args()
    Q = args.q
    assert 1 <= Q <= 30

    certs = enumerate_first_contractions(Q)
    killed, total, selected, redundant = sparse_quotient(certs, Q)

    by_o = Counter(c.o for c in selected)
    first_by_o = Counter(c.o for c in certs)

    print("SPARSE_REVERSE_TREE_Q", Q)
    print("FIRST_CONTRACTION_CERTIFICATES", len(certs))
    print("NONREDUNDANT_CERTIFICATES", len(selected))
    print("REDUNDANT_NESTED_CERTIFICATES", redundant)
    for o in sorted(first_by_o):
        retained = by_o.get(o, 0)
        contribution = retained * (3 ** (Q - o))
        print(
            "SPARSE_REVERSE_DEPTH",
            f"o={o}",
            f"first={first_by_o[o]}",
            f"retained={retained}",
            f"target_residue_contribution={contribution}",
        )

    print("KILLED_RESIDUES", killed)
    print("TOTAL_RESIDUES", total)
    print("KILL_FRACTION", f"{killed}/{total}", f"{killed/total:.15f}")
    print("LIVE_FRACTION", f"{total-killed}/{total}", f"{(total-killed)/total:.15f}")

    # Frozen exact regressions from the independent bitmap implementation.
    refs = {
        7: (1013, 2187, 13),
        9: (9145, 19683, 41),
        11: (82429, 177147, 165),
        12: (247889, 531441, 767),
        14: (2233499, 4782969, 3265),
    }
    if Q in refs:
        ek, et, ec = refs[Q]
        assert (killed, total, len(selected)) == (ek, et, ec), (
            Q, killed, total, len(selected), refs[Q]
        )
        print("SPARSE_REVERSE_REFERENCE_CONTROL_OK", Q)

    print("VERIFIED_SPARSE_REVERSE_PREDECESSOR_QUOTIENT")


if __name__ == "__main__":
    main()
