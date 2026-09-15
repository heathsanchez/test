#!/usr/bin/env python3
"""
Exact lawful low-residue partition for shortcut-Collatz coefficient persistence.

For the shortcut map
    T(n) = n/2            if n is even
           (3n+1)/2       if n is odd,
the first k parity decisions depend only on n mod 2^k.  Therefore the
residue classes whose first k steps satisfy 3^q_t >= 2^t are an exact cover
of every seed that can retain coefficient persistence beyond step k.

This is a quotient, not a heuristic: residues rejected here cannot satisfy
the H>=k persistence CNF for any higher bits.
"""
import argparse
import json
from pathlib import Path


def survives_prefix(residue: int, bits: int) -> bool:
    x = residue
    q = 0
    p3 = 1
    for t in range(1, bits + 1):
        if x & 1:
            q += 1
            p3 *= 3
            x = (3 * x + 1) // 2
        else:
            x //= 2
        if p3 < (1 << t):
            return False
    return True


def lawful_residues(bits: int) -> list[int]:
    return [r for r in range(1 << bits) if survives_prefix(r, bits)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bits", type=int, required=True)
    ap.add_argument("--out")
    ap.add_argument("--github-output", action="store_true")
    args = ap.parse_args()

    if not 1 <= args.bits <= 20:
        raise SystemExit("bits must be between 1 and 20")

    residues = lawful_residues(args.bits)
    payload = {
        "kind": "exact_coefficient_prefix_residue_partition",
        "bits": args.bits,
        "modulus": 1 << args.bits,
        "lawful_count": len(residues),
        "eliminated_count": (1 << args.bits) - len(residues),
        "residues": residues,
    }

    if args.bits == 12:
        # Frozen structural control: independently follows from the exact
        # prefix inequality and protects the Actions matrix from drift.
        assert len(residues) == 226

    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2) + "\n")

    print("PREFIX_PARTITION", json.dumps(payload, separators=(",", ":")))
    if args.github_output:
        print("residues=" + json.dumps(residues, separators=(",", ":")))
        print("count=" + str(len(residues)))


if __name__ == "__main__":
    main()
