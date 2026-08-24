# Verified Quotient Synthesis V1 — frozen precommit

## Target
Test whether exact verifier counterexamples can turn failed one-shot representation construction into a usable future-relative quotient that changes downstream reachable action.

## Frozen world
Three held-out modular latent families m∈{2,3,5}; additive hidden law `value=(base[prefix]+offset[suffix]) mod m`, gauge X=0. 12 protected tasks per family (36 total), generated deterministically with seed 2026082509. Each task has raw verified observations, one target, and four allowed extra queries.

## Representation language
A candidate quotient is a JSON mapping from each allowed query q and each possible observed query value a to the *set of target values still possible* after observing q=a. No latent coordinates are retained. This is the smallest target-relative support partition needed by the controller in these tasks.

## Arms
- RAW_DIRECT: choose a query directly from raw observations.
- ONE_SHOT_SYNTHESIS: construct the quotient once from raw observations; Python derives the query from the proposed quotient.
- VERIFIED_SYNTHESIS: construct a quotient, receive exact verifier counterexamples (missing/spurious target values for incorrect cells), revise for at most 4 total proposals; Python derives the query from the final proposal.
- HAND_QUOTIENT: exact externally generated target quotient.
- OPTIMAL_QUERY: deterministic exact expected-target-entropy selector.

All LLM arms use the same frozen model, temperature 0. Python is the external verifier and scorer.

## Primary
`VERIFIED_SYNTHESIS` must beat `ONE_SHOT_SYNTHESIS` on (1) exact quotient rate and (2) downstream target accuracy.

## Strong success
- VERIFIED_SYNTHESIS exact quotient rate >= 0.75;
- downstream target accuracy >= 0.90;
- VERIFIED_SYNTHESIS downstream accuracy > RAW_DIRECT;
- HAND_QUOTIENT accuracy >= 0.95.

## Interpretation
If exact counterexamples improve verified quotient construction and downstream action, retain a bounded law: representation construction can be turned into verifier-guided synthesis. If not, preserve `QUOTIENT_CONSTRUCTION_NOT_REPAIRED_BY_LOCAL_COUNTEREXAMPLES` and do not claim the developmental bridge is closed.
