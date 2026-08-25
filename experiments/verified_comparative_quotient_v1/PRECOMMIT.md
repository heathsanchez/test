# Verified Comparative Quotient V1 — frozen precommit

## Target
Test whether externally verified *comparative* repair across all candidate future queries improves action selection more reliably than repairing a single decision certificate.

## Frozen benchmark
- Model: `gpt-4.1-mini`, temperature 0.
- Families: additive latent worlds modulo 2, 3, and 5 with gauge `offset[X]=0`.
- 16 protected tasks per family; 48 total.
- Each task has raw verified observations, one target, and four allowed extra queries.
- Tasks are retained only when the exact optimal query makes target entropy zero and candidate queries have materially different target information value.
- Python exactly enumerates all latent worlds consistent with the observations and is the external verifier.

## Arms
1. `RAW_DIRECT`: choose one query directly from raw observations.
2. `ONE_SHOT_COMPARATIVE`: construct a compact comparison over all candidate queries once, then choose its top-ranked query.
3. `VERIFIED_COMPARATIVE`: start from the same one-shot comparison and receive up to three external ranking counterexamples. A counterexample states that the current top-ranked query is not optimal and supplies its exact expected target entropy together with one strictly better rival's exact expected target entropy. The model must repair the ranking/comparison.
4. `HAND_COMPARATIVE`: exact Python target-entropy ranking.
5. `OPTIMAL_QUERY`: exact deterministic optimum.

No arm is given the full latent-world list or full target quotient.

## Primary hypotheses
Before protected results are observed:
- `VERIFIED_COMPARATIVE` downstream target accuracy > `ONE_SHOT_COMPARATIVE`.
- `VERIFIED_COMPARATIVE` exact-optimal-query rate > `ONE_SHOT_COMPARATIVE`.

## Strong success thresholds
- Verified comparative target accuracy >= 0.90.
- Verified comparative exact-optimal-query rate >= 0.80.
- Hand comparative target accuracy >= 0.95.

## Interpretation
- If verified comparative beats one-shot and approaches the strong thresholds, retain the hypothesis that the useful minimal representation is comparative structure over candidate futures rather than a complete quotient or isolated certificate.
- If ranking fidelity improves without downstream action, preserve that as a new residual.
- If verification hurts, reject the comparative-repair hypothesis under this boundary.
