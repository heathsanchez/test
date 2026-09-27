#!/usr/bin/env python3
"""Exact Q14 audit of reverse certificates that are strong enough to force a
lower merge on the large-source hard-first-crossing regime q<n.

For a first-contracting reverse certificate
    p = (a*y - c)/d,   a<d,
and a hard first-crossing endpoint y=n+g with 3g<q, no ordinary exit implies
p>=n. Therefore
    3(d-a)n + 3c < a q.
If q<n, any certificate with 3(d-a) >= a is impossible, independent of the
unknown exact q/n ratio. This script measures exactly how much of y mod 3 = 1
is eliminated by those ratio-robust certificates at Q=14.

Finite audit only; not a Collatz proof.
"""
from collatz_reverse_predecessor_tree import enumerate_first_contractions

Q = 14
M = 3 ** Q
certs = enumerate_first_contractions(Q)
strong = [c for c in certs if 3 * (c.d - c.a) >= c.a]

killed = bytearray(M)
for c in strong:
    for r in range(c.residue, M, c.d):
        if r % 3 == 1:
            killed[r] = 1

relevant = range(1, M, 3)
total = len(range(1, M, 3))
covered = sum(killed[r] for r in relevant)
live = total - covered

by9 = {}
for cls in (1, 4, 7):
    vals = range(cls, M, 9)
    t = len(range(cls, M, 9))
    c = sum(killed[r] for r in vals)
    by9[cls] = (c, t, t-c)

print("Q", Q)
print("FIRST_CONTRACTION_CERTIFICATES", len(certs))
print("RATIO_ROBUST_CERTIFICATES", len(strong))
print("REGIME", "hard_first_crossing_and_q_lt_n")
print("ROBUSTLY_EXCLUDED_RELEVANT_RESIDUES", covered)
print("TOTAL_RELEVANT_RESIDUES", total)
print("LIVE_RELEVANT_RESIDUES", live)
print("ROBUST_EXCLUSION_FRACTION", f"{covered}/{total}", f"{covered/total:.12f}")
for cls,(c,t,l) in by9.items():
    print("MOD9_CLASS", cls, "EXCLUDED", c, "TOTAL", t, "LIVE", l,
          "FRACTION", f"{c/t:.12f}")

assert (covered, total, live) == (33723, 1594323, 1560600)
assert by9[1] == (24462, 531441, 506979)
assert by9[4] == (8370, 531441, 523071)
assert by9[7] == (891, 531441, 530550)

print("DECISION Q14_RATIO_ROBUST_REVERSE_BANK_FAR_FROM_COMPLETE")
print("REJECTED universal_large_source_finish_by_fixed_q14_reverse_bank")
print("GLOBAL_COLLATZ UNKNOWN")
