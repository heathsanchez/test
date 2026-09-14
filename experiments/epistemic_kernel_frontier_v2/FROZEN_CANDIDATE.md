# Epistemic Kernel Frontier V2 — EQ+DIST-Constrained Candidate

**Status:** FROZEN BEFORE V2 TEST  
**Date:** 2026-09-14

V1 showed:
- singleton possible-world sets recover exact kernels;
- robust kernel intersection overcommits in 32,752/32,767 world-sets;
- nonunique least-commitment frontiers occur;
- but 12 world-sets admitted a minimal frontier member that split a pair classified EQ in every compatible world.

V2 aligns the frontier with WCD's full trichotomy.

## 1. Pair statuses

For a nonempty compatible exact-kernel set `K_E`:

- EQ: every compatible kernel merges the pair;
- DIST: every compatible kernel separates the pair;
- UNKNOWN: otherwise.

## 2. Admissible representation

A representation partition `P` is admissible iff:

1. every EQ pair is merged in `P`;
2. every DIST pair is separated in `P`;
3. UNKNOWN pairs are unconstrained.

Thus current warrant constrains both signs of consequential difference.

## 3. Least-commitment frontier

Among admissible partitions retain all coarsest/minimal elements under refinement.

No admissible frontier member may preserve a distinction already warranted irrelevant (EQ).

## 4. Resolved-world reduction

For singleton `K_E={K}`, the unique admissible least-commitment representation is exactly `K`.

## 5. Robust intersection

`intersection K_E` remains admissible but can be strictly more committed because it separates UNKNOWN pairs whenever any compatible world separates them.

## 6. Falsifiers

V2 fails if:
1. any nonempty compatible-kernel set has no admissible partition;
2. any frontier member splits an EQ pair or merges a DIST pair;
3. any singleton world set fails to recover its exact kernel uniquely;
4. robust intersection ever violates EQ or DIST constraints;
5. robust intersection is always least-committed;
6. nonunique frontiers disappear entirely.
