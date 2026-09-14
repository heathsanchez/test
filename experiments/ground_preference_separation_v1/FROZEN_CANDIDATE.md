# Ground–Preference Separation V1 — Frozen Candidate

**Status:** FROZEN BEFORE TEST  
**Date:** 2026-09-14

Candidate:

> Semantic ground/lawfulness is a hard admissibility layer and cannot, in
> general across unbounded domains, be replaced by one fixed finite scalar
> penalty mixed with ordinary developmental cost.

## Claim

For any fixed finite scalar penalty M in an objective

```math
score = M * violations + cost,
```

with lower score preferred and unbounded lawful cost, there exists a valid
candidate and an invalid candidate such that the scalar objective prefers the
invalid one.

Therefore universal correctness-first behavior requires either:
- a hard admissibility gate;
- a lexicographic order with violations first; or
- an equivalent non-Archimedean/typed construction.

Within the lawful set, ordinary cost/preference may still choose among
consequentially equivalent realizations.

## Falsifier

V1 fails if a fixed finite M can enforce correctness-first choice for all
nonnegative unbounded costs.
