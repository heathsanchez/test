# Korovin Public Synthetic Unnamed Object V7 — Frozen Precommit

This file is committed before the public validation world is generated or inspected.

## Objective

Test whether the V5/V6 compact-theory and global-certification machinery transfers to a deterministic synthetic finite transformation object that was not selected for a familiar algebraic identity or for a favorable result.

## Public validation seed

Seed phrase:

`KOROVIN_V7_PUBLIC_VALIDATION_2026-08-22`

The seed integer is the unsigned big-endian integer represented by the first 8 bytes of SHA-256(seed phrase).

No alternate seed, rejection sampling, regeneration, or world replacement is permitted after generation.

## World generator

- carrier points: `{0,1,2,3}`;
- generator names: `a`, `b`;
- initialize Python `random.Random(seed_integer)`;
- for `a`, then `b`, draw four independent `randrange(4)` values to define each transformation tuple;
- program semantics is left-to-right transformation composition exactly as in V5/V6.

## Frozen theory search

- candidate equations: all semantically true distinct word pairs with each side length <= 5;
- training contextual universe: all words length <= 7;
- maximum greedy retained rules before global pruning: 10;
- rule-selection score: maximum additional sound quotient compression, then lower total side length, then lower max side length, then canonical lexical tie-break;
- exact semantic oracle may reject false equations but does not suggest equations.

## Global certification

- enumerate all reachable exact semantic states by BFS from the empty word;
- choose one shortest canonical word per state;
- for every canonical state and generator, require an explicit checked derivation from `r_q a` to `r_delta(q,a)` using retained equations;
- derivation-witness search permits intermediate words of length <= 9;
- semantically verify every retained relation;
- apply the V6 induction theorem to certify generated congruence = exact semantic equivalence for every finite word.

## Global pruning and ablation

Repeatedly delete any learned equation whose removal preserves the full global certificate. Freeze the result. Then remove each final rule independently; every removal must destroy global completeness.

## Gates

G0. Generated world is nontrivial: at least 6 reachable states.
G1. At least one primitive generator is non-invertible on the four-point carrier.
G2. Bounded theory formation reaches exact semantic congruence on words <= 7 with zero false merges.
G3. Initial learned theory obtains the V6 global completeness certificate.
G4. Globally pruned theory remains globally complete.
G5. Every final retained relation is causally necessary for global completeness.
G6. Compactness: final relation count is strictly less than reachable state count.
G7. All retained equations are semantically sound.
G8. Every canonical-state × generator edge has an explicit independently replayable derivation.

## Claim boundary

A pass demonstrates transfer of residual-guided compact object theory formation to a fresh, publicly precommitted, unlabeled synthetic finite transformation object.

It does not establish historical mathematical novelty or usefulness to working mathematicians beyond this formal finite setting.
