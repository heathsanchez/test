# Korovin Batch Transfer V8 — Frozen Precommit

This file is committed before any V8 validation world is generated or inspected.

## Motivation

V7's publicly precommitted single draw failed only its difficulty gate because the fixed seed produced identical primitive transformations and a 3-state object. All theory-formation and global-certification gates passed. V8 preserves that negative result and tests the world-distribution boundary without rejection sampling.

## Public batch seeds

Root phrase:

`KOROVIN_V8_PUBLIC_BATCH_2026-08-22`

For batch indices `0..7`, world `i` uses phrase:

`KOROVIN_V8_PUBLIC_BATCH_2026-08-22::<i>`

The seed integer is the unsigned big-endian integer represented by the first 8 bytes of SHA-256(the indexed phrase).

Every one of the eight draws must be generated, executed, and reported. No alternate index, replacement, regeneration, rejection sampling, or deletion is permitted.

## World distribution

For each index independently:

- carrier points: `{0,1,2,3}`;
- generator names: `a`, `b`;
- initialize Python `random.Random(seed_integer)`;
- for `a`, then `b`, draw four independent `randrange(4)` values;
- use left-to-right transformation composition exactly as in V5–V7.

## Preregistered complexity strata

The realized reachable state count is an outcome, not a selection criterion.

- **trivial draw:** fewer than 6 reachable states;
- **nontrivial draw:** at least 6 reachable states.

Both strata remain in the result. Theory soundness is required on every draw. Completeness-transfer claims are evaluated on every nontrivial draw.

## Frozen theory and certificate pipeline

For every draw:

- candidate equations: all semantically true distinct word pairs with each side length <= 5;
- training contextual universe: all words length <= 7;
- maximum greedy retained rules before global pruning: 10;
- same V5 rule-selection score and tie breaks;
- exact semantic oracle rejects false equations but does not suggest equations;
- BFS exact reachable-state enumeration and shortest canonical representatives;
- explicit V6 generator-edge derivation certificates with intermediate word length <= 9;
- global pruning deletes any learned equation unnecessary for the full global certificate;
- every final equation is individually ablated.

No hyperparameter may vary by world.

## Gates

G0. Exactly eight indexed worlds are generated and reported.
G1. Distribution adequacy: at least four of the eight worlds are nontrivial (>=6 states).
G2. Soundness: every final retained equation is semantically sound in every draw.
G3. No false merge: bounded theory formation creates zero semantically invalid identifications in every draw.
G4. Every nontrivial draw reaches exact bounded semantic congruence on words <=7.
G5. Every nontrivial draw obtains the initial global completeness certificate.
G6. Every nontrivial draw remains globally complete after global pruning.
G7. In every nontrivial draw, every final retained rule is causally necessary for global completeness.
G8. In every nontrivial draw, every canonical-state × generator edge has an explicit replayable derivation.
G9. Compactness: in every nontrivial draw, final rule count is strictly less than reachable state count.

## Reporting

The result must report all eight indexed phrases/seeds, primitive transformations, state counts, stratum labels, initial/final rules, all gates, and any failure. Aggregate success must never conceal a per-world failure.

## Claim boundary

A pass demonstrates distributional transfer of verified compact finite-object theory formation across a publicly precommitted batch of unlabeled synthetic transformation worlds, without seed replacement or favorable-world selection.

It does not establish historical mathematical novelty or usefulness to working mathematicians outside this finite formal setting.
