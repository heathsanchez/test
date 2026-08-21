# Korovin V10 — Finite Residual Completion

## Why V10 exists

V9 froze an arbitrary maximum of 8 residual-edge additions. On the first difficult transfer world inspected after that freeze, the same operator reaches global completeness in 10 additions. This classifies the V9 failure as a budget residual, not evidence for a new representation or law family.

V10 removes the arbitrary constant and replaces it with a bound derived from the finite residual itself.

This precommit is frozen before any V10 world is generated or inspected.

## Operator

The inherited V5 theory learner and V6 global certificate remain unchanged.

For a world whose inherited theory is not globally complete:

1. Compute the set F0 of semantically valid but underivable canonical state-generator edges.
2. Set the maximum number of completion rounds to |F0|. There is no hand-selected constant.
3. At each round, form one candidate law from every currently failed edge: `lhs = canonical_target`.
4. Independently require exact semantic equality of both sides.
5. Choose the minimum candidate under `(total side length, maximum side length, lhs, rhs)`.
6. Add that one law and recompute the certificate.
7. Stop immediately if all canonical edges certify.
8. After completion, run the existing V6 global redundancy pruning to fixed point.

Because adding a sound edge equality cannot make a previously derivable equality underivable, and the selected failed edge becomes directly derivable, the procedure is expected to terminate no later than |F0| rounds. V10 tests the executable realization of that finite-completion argument.

## New public transfer batch

Root phrase: `KOROVIN_V10_PUBLIC_COMPLETION_TRANSFER_2026-08-22`.

Exactly 12 indexed 4-point/two-generator worlds, indices 0..11, are generated using the unchanged V8 draw mechanism. Every draw is retained and reported. No seed may be replaced.

## Gates

- G0: exactly 12 indexed worlds reported.
- G1: every inherited rule set is semantically sound.
- G2: every residual-generated law is semantically sound.
- G3: every residual-bearing world reaches global completeness in at most its initial failed-edge count.
- G4: every baseline-complete world receives zero added law.
- G5: final bounded audits have zero false merges for every world.
- G6: after fixed-point global pruning, every retained generated law is individually causal for global completeness.
- G7: every final theory is globally complete.
- G8: at least one world is residual-bearing; otherwise the developmental operator is untested and the experiment fails.
- G9: for every residual-bearing nontrivial world, the number of retained generated laws is strictly less than the reachable semantic state count.

## Claim boundary

A pass establishes a finite, externally verified completion mechanism for these finite transformation worlds: theory incompleteness identifies exact missing transition laws and each retained repair is sound and causally necessary.

This is not historical mathematical novelty. The semantic oracle and finite canonical state graph remain available to the verifier.