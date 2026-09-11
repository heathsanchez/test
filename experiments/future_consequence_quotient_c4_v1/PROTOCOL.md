# Future Consequence Quotient C4 V1 Protocol

## Status and question

C4 was exposed by Verified Developmental Compounding V1. This is therefore a frozen-target repair qualification, not a fresh prospective evaluation. The mechanism is frozen before this rerun and must later survive a new held-out task before any prospective-transfer claim.

The question is whether replacing immediate prefix credit with continuation-major candidate comparison repairs the exact C4 failure while charging every verifier evaluation.

## Fixed inputs

- Parent evidence freeze: `379846668d040cfeaabc304413d1307db49a85fe`.
- C4 task, examples, operation order, verifier, and maximum depth are unchanged.
- No new operation is introduced. This tests behavioural continuation discovery inside the existing generated monoid, not generator genesis.
- Deterministic seed: 20260911.

## Frozen conditions

- `COLD_IMMEDIATE`: original depth-first prefix-major enumeration.
- `FUTURE_QUOTIENT`: at each depth enumerate continuation suffixes first and compare every possible leading candidate under the same suffix. This operationally groups leading candidates by their bounded continuation profiles. Stop at the first verifier-accepted member; untested equivalences remain UNKNOWN.
- `SEPARATOR_ABLATION`: remove the first successful separating continuation from the future-major schedule and replay unchanged.
- `OPERATOR_ABLATION`: remove continuation-major ordering entirely, restoring cold enumeration.
- `SHAM`: retain an inert profile record of matched size but use cold enumeration.
- `ANSWER_MEMORY`: expose prior answer provenance to a non-causal channel that the controller cannot read; use cold enumeration.

Every unique program evaluation is charged once. No probe cost is hidden. Correctness is exact equality over the unchanged frozen examples.

## Precommitted gates

1. All conditions remain correct.
2. Future quotient cost is below 80 percent of cold cost.
3. Exact separator ablation removes at least 20 verifier calls of the gain.
4. Operator ablation restores cold cost.
5. Sham and answer-memory controls equal cold cost.
6. Immediate one-step credit collides across all four leading candidates.
7. A later continuation separates that collision and occurs on the accepted path.
8. The formal generic action-quotient theorems compile without `sorry`.

Passing establishes bounded, post-failure causal repair by continuation-sensitive candidate comparison. It does not establish prospective transfer, complete quotient construction, or expressive generator genesis.
