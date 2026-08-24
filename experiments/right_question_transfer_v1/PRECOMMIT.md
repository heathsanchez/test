# Right Question Transfer V1 — frozen protocol

## Question
Does the near-optimal observation-only right-question behavior from Right Question Capstone V1 transfer beyond the original add_mod4 world, or was it benchmark-specific?

## Frozen design
Generate protected tasks deterministically (seed 2026082507) from three previously untested additive latent families: mod 2, mod 3, and mod 5. Each family has 4 prefix coordinates and 3 suffix coordinates with gauge X=0. A world maps pair PS to (base[P]+offset[S]) mod m.

For each task, expose a partial verified observation set, a target pair whose value matters, and four allowed extra queries. Exact Python enumeration defines the surviving hypothesis set and the optimal one-step query by expected reduction in TARGET entropy.

Arms:
- RANDOM_QUERY: deterministic random allowed query.
- GENERIC_OBS_ONLY: LLM sees observations, target, query set, family; choose most useful query.
- TARGET_INFO_GAIN_OBS_ONLY: same information, explicitly choose query minimizing expected uncertainty of target value; no explicit possible-world list.
- OPTIMAL_QUERY: exact Python optimum.

No LLM receives explicit surviving worlds. Python reveals the chosen query outcome, filters hypotheses, and scores target prediction/entropy.

## Primary
TARGET_INFO_GAIN_OBS_ONLY must exceed RANDOM_QUERY in target accuracy and achieve >= 0.80 optimal-query rate pooled across protected tasks.

## Secondary
- TARGET_INFO_GAIN_OBS_ONLY >= GENERIC_OBS_ONLY in target accuracy.
- Mean target-entropy regret to OPTIMAL_QUERY is lower for TARGET_INFO_GAIN_OBS_ONLY than RANDOM_QUERY.
- Report each modulus separately to expose family-specific failure.

## Interpretation
Pass: observation-only target-directed query selection transfers across distinct latent alphabets/moduli and is not just an add_mod4 artifact.
Fail: preserve the residual; do not rescue by changing prompts or tasks after seeing outcomes.
