# Epistemic Kernel Frontier V1 — Frozen Candidate

**Status:** FROZEN BEFORE EXHAUSTIVE TEST  
**Date:** 2026-09-14

This candidate links:
- resolved-world State–Test Kernel V2;
- WCD V2's EQ / DIST / UNKNOWN discipline;
- the least-commitment frontier under epistemic uncertainty.

## 1. Possible resolved kernels

Let `K_E` be a nonempty set of compatible exact future-consequence kernels on state set `X`.

For a pair `x,y`:

- **EQ** if every `K in K_E` merges the pair;
- **DIST** if every `K in K_E` separates the pair;
- **UNKNOWN** otherwise.

If `K_E` is empty: inconsistent evidence / inadequate authority.

## 2. Warranted representation constraint

A current representation is semantically adequate for the current warranted consequence if it does not merge any pair classified DIST.

It may preserve additional distinctions.

The least-commitment frontier is the set of coarsest/minimal partitions satisfying all currently warranted DIST constraints.

EQ pairs should disappear under least commitment unless preserving them is forced indirectly by the global partition structure.

UNKNOWN pairs are not decided in advance.

## 3. Resolved-world reduction

If `K_E={K}` is a singleton, the least-commitment frontier should be exactly `{K}`.

Thus exact state–test quotienting is the resolved-world special case.

## 4. Robust-intersection warning

The intersection relation

```math
K_cap = \bigcap_{K\in K_E}K
```

preserves every distinction that *any* compatible world might need.

It is therefore a robust sufficient refinement, but it can preserve distinctions not currently warranted by **all** compatible worlds.

Claim:

> `K_cap` is generally more committed than the WCD least-commitment frontier and must not replace the epistemic frontier.

## 5. Falsifiers

V1 fails if:
1. a singleton compatible-kernel set does not recover its exact kernel as unique least-commitment representation;
2. the robust intersection ever violates a universally warranted DIST constraint;
3. the robust intersection is always least-committed, leaving no need for a frontier;
4. nonunique least-commitment frontiers never occur under compatible-kernel uncertainty;
5. EQ/DIST/UNKNOWN pair classification overlaps for any nonempty compatible-kernel set.
