# Prospective source admission V2 — frozen before opening new sources

Prior V1 is INSUFFICIENT_SOURCE; do not revise it.

Candidate list, deterministic order, all mathlib4 tag v4.34.0:
1. Mathlib/Algebra/Order/BigOperators/Group/Finset.lean
2. Mathlib/Data/Finset/Card.lean
3. Mathlib/NumberTheory/Divisors.lean
4. Mathlib/Data/Nat/Choose/Sum.lean

Eligibility is metadata-only: at least eight source docstrings immediately adjacent to theorem/lemma declarations; do not inspect proof success or statement truth to choose.
Select first eligible file. If no file eligible, return INSUFFICIENT_POOL and STOP.
All selected theorems in textual order are the admitted task set; first eight for bounded evaluation. Preserve exact Git blob hashes, source commit, and parser code. Do not substitute based on result.
V1 mathematical-intent and comparator protocol unchanged; source documents themselves do not establish independent semantic ground truth.
