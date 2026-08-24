# Separator Construction V1 — frozen precommit

## Question
Given the same correct latent abstraction and evidence, can a frozen LLM *construct* a rival + executable differential intervention, rather than merely choose from a supplied menu?

This follows Separator Selection V2, where all four arms chose the correct intervention 6/6 once a short candidate menu was supplied. The residual is therefore upstream of selection: candidate rival/intervention construction.

## Design
Six frozen historical lineages are represented as small executable experimental worlds. Each case supplies:
- evidence;
- the correct latent abstraction;
- a domain-specific intervention DSL vocabulary;
- two frozen possible worlds: TARGET and SIMPLE_RIVAL;
- a deterministic outcome function over valid DSL interventions.

No candidate interventions are shown.

The model must emit exactly:
`RIVAL: <one sentence>`
`TEST: <dsl expression>`

## Arms
1. `GENERIC` — construct the best next experiment.
2. `RIVAL_FIRST` — explicitly state the strongest simpler rival first, then construct the smallest test that makes target and rival disagree.
3. `COUNTERFACTUAL_WORLDS` — predict what would happen under both possible worlds and construct the cheapest intervention whose outcomes differ.
4. `VERIFIED_RESIDUAL` — use the verified-residual discipline: strongest live rival, closure-before-invention, smallest deciding intervention, frozen metric/boundary.

## Frozen model/resource boundary
- model: `gpt-4.1-mini` unless UVRM_MODEL overrides in workflow
- temperature: 0
- max_tokens: 220
- one call per case/arm
- 6 cases × 4 arms = 24 calls
- fixed shuffle seed 20260824
- no retrieval or tools

## Deterministic scoring
The scorer parses the DSL expression and executes it against both frozen worlds.

For each response:
- `valid`: expression parses and uses only allowed primitives;
- `separates`: TARGET outcome != SIMPLE_RIVAL outcome;
- `cost`: frozen additive intervention cost;
- `minimal_separator`: separates and has minimum possible cost for that case;
- `rival_hit`: output identifies the frozen simpler rival concept family.

Primary metric: mean `separator_utility = separates * (1 / cost)` with invalid=0.
Secondary: minimal-separator rate and rival-hit rate.

## Frozen predictions
Primary directional prediction:
`RIVAL_FIRST > GENERIC` on mean separator utility.

Secondary:
`COUNTERFACTUAL_WORLDS >= RIVAL_FIRST` if explicit possible-world simulation adds value.
`VERIFIED_RESIDUAL > RIVAL_FIRST` only if the full method adds value beyond the compressed rival-separator kernel.

## Interpretation
- If all arms ceiling: the DSL/worlds are too easy; do not infer equivalence of methods.
- If RIVAL_FIRST > GENERIC while VERIFIED_RESIDUAL ~= RIVAL_FIRST: evidence that the operational kernel compresses to explicit rival construction + separator.
- If VERIFIED_RESIDUAL > RIVAL_FIRST: evidence for additional value from the broader discipline.
- If no arm separates reliably: construction capability remains weak or the DSL carrier is inadequate.

This is a bounded construction benchmark, not evidence about human phenomenology or unrestricted scientific discovery.