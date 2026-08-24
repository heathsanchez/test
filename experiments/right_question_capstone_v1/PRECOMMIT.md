# RIGHT QUESTION CAPSTONE V1 — PRECOMMIT

## Question
Can a frozen LLM choose the intervention that collapses uncertainty over a downstream target once the surviving possible worlds are explicit, and which instruction is causally useful?

## Frozen benchmark
Same 8 arbitrary add-mod-4 worlds and 4 ambiguity templates as Active Latent Disambiguation V1. Each task has 16 surviving hypotheses, 3 allowed extra queries, and a held-out target. Python enumerates the exact hypothesis set and computes the optimal target-information-gain query.

## Arms
1. GENERIC_EXPLICIT — explicit surviving worlds; choose the most useful next query.
2. RIVAL_EXPLICIT — explicit surviving worlds; choose the query that best separates live rivals relevant to the target.
3. TARGET_INFO_GAIN_EXPLICIT — explicit surviving worlds; choose the query minimizing expected entropy of the target action.
4. TARGET_INFO_GAIN_OBS_ONLY — same target-info-gain instruction but no explicit surviving-world table; tests whether the scaffold is necessary.
5. RANDOM_QUERY — deterministic random baseline.
6. OPTIMAL_QUERY — deterministic target-information-gain ceiling.

## External scoring
The LLM chooses only one of the three allowed queries. Python reveals the true answer, filters the exact hypothesis set, and predicts the target by survivor majority. No LLM judges outcomes.

Primary: TARGET_INFO_GAIN_EXPLICIT downstream accuracy > GENERIC_EXPLICIT and > RANDOM_QUERY.
Secondary: TARGET_INFO_GAIN_EXPLICIT optimal-query rate > GENERIC_EXPLICIT; TARGET_INFO_GAIN_EXPLICIT >= RIVAL_EXPLICIT; explicit > obs-only; compare target entropy after query and regret to deterministic optimum.

Success is about downstream future-action certainty, not recovering a unique world. All hypotheses, prompts, arms, scoring, model, and task set are frozen before protected execution.
