# Active Latent Disambiguation V1 — frozen precommit

Goal: test whether active selection of a query that separates surviving latent models improves recovery of a held-out target compared with a matched random extra query.

World family: the same eight frozen arbitrary add-mod-4 worlds used in Law Induction V1d / Latent Coordinate Induction V1. The latent family is fixed and externally enumerable with gauge X=0.

For each world we create four frozen partial-observation scenarios. Each scenario begins with four verified observations, leaves one target pair held out, and offers exactly three possible one-step extra queries. The surviving hypothesis set is all add-mod-4 coordinate assignments consistent with the four initial observations.

Arms:
- NO_EXTRA: predict the target from the current surviving hypothesis set by majority vote.
- RANDOM_QUERY: spend exactly one extra query, chosen uniformly from the three candidates using frozen seed 2026082505; reveal its true verified answer; then majority-vote the target among survivors.
- INFO_GAIN_QUERY: spend exactly one extra query, chosen to maximize expected reduction in target-prediction entropy over the surviving hypothesis set; reveal its verified answer; then majority-vote the target.
- ORACLE_QUERY: choose the candidate that minimizes target entropy after seeing its outcome under the true world; ceiling/control only.

No LLM is used in this test. This isolates the causal value of active hypothesis separation itself from language-model generation quality.

Primary endpoint: exact held-out target accuracy over 32 world×scenario tasks.

Primary prediction: INFO_GAIN_QUERY > RANDOM_QUERY.
Secondary predictions: INFO_GAIN_QUERY > NO_EXTRA; ORACLE_QUERY defines the one-query ceiling. We also record mean surviving-hypothesis count and mean target entropy before and after the query.

Interpretation frozen before run:
- If INFO_GAIN_QUERY > RANDOM_QUERY, active selection of where surviving worlds disagree is causally useful beyond merely obtaining one more observation.
- If INFO_GAIN_QUERY = RANDOM_QUERY, the active-separator hypothesis is not supported on this family.
- If NO_EXTRA is already at ceiling, the scenarios are invalid for this purpose.
