#!/usr/bin/env python3
"""Exact q14 audit of first-contracting reverse-predecessor coverage on the
large-source hard-first-crossing residue domain.

A large-source hard first crossing has endpoint y % 3 == 1.  The existing
reverse predecessor bank gives a lower-merge certificate whenever y lies in a
first-contracting residue class.  This audit asks whether increasing the bank
to Q=14 covers that whole relevant 3-adic domain.

This is a finite coverage audit only, not a Collatz proof.
"""
from collatz_reverse_predecessor_tree import enumerate_first_contractions, quotient

Q = 14
M = 3 ** Q
certs = enumerate_first_contractions(Q)
killed, selected = quotient(certs, Q)

relevant = list(range(1, M, 3))
covered = sum(killed[r] for r in relevant)
total = len(relevant)
live = total - covered

by9 = {}
for cls in (1, 4, 7):
    rs = range(cls, M, 9)
    t = sum(1 for _ in rs)
    c = sum(killed[r] for r in range(cls, M, 9))
    by9[cls] = (c, t, t-c)

print("Q", Q)
print("FIRST_CONTRACTION_CERTIFICATES", len(certs))
print("NONREDUNDANT_CERTIFICATES", len(selected))
print("HARD_ENDPOINT_DOMAIN", "y_mod_3_eq_1")
print("COVERED_RELEVANT_RESIDUES", covered)
print("TOTAL_RELEVANT_RESIDUES", total)
print("LIVE_RELEVANT_RESIDUES", live)
print("COVERAGE_FRACTION", f"{covered}/{total}", f"{covered/total:.12f}")
for cls,(c,t,l) in by9.items():
    print("MOD9_CLASS", cls, "COVERED", c, "TOTAL", t, "LIVE", l,
          "FRACTION", f"{c/t:.12f}")

assert (covered, total, live) == (639176, 1594323, 955147)
assert by9[1] == (101918, 531441, 429523)
assert by9[4] == (531441, 531441, 0)
assert by9[7] == (5817, 531441, 525624)

print("DECISION Q14_FIRST_CONTRACTION_BANK_INCOMPLETE_ON_HARD_ENDPOINT_DOMAIN")
print("REJECTED universal_finish_by_reverse_bank_depth_alone")
print("GLOBAL_COLLATZ UNKNOWN")
