# UVRM Graph V5 — frozen precommit

## Target
Test whether typed scientific relations improve protected next-move selection beyond the same facts presented chronologically or with relation labels ablated.

## Residual from V4
V4 produced a monotone concept-recall signal TRANSCRIPT < GRAPH_ABL < GRAPH, while the literal pass scorer was brittle to exact mode/phrase realization. V4 is preserved and not rescored.

## Frozen arms
- TRANSCRIPT: chronological evidence only.
- GRAPH_ABL: same evidence plus relation endpoints, edge labels removed.
- GRAPH: same evidence plus typed scientific relations.
- GRAPH_RULES: GRAPH plus the pre-existing generic controller scaffold.

## Protected cases
Eight new retrospective prequential cases, two each from Lean-kernel, SAIR, Triskelion, and MathGraph lineages. None is a V4 case.

## Model/resource boundary
Generation model `gpt-4.1-mini`; temperature 0; max 220 output tokens; one call per case×arm; 32 calls total; fixed shuffled call-order seed 2026082402. Same prompt prefix, model, token cap, and API path across arms.

## Frozen evaluation
Two outcomes are reported separately:
1. exact mode-label rate;
2. semantic next-move quality.

Semantic quality is deterministic and outcome-blind. Each case has three pre-frozen required consequence groups and at least two forbidden consequence groups. A group is satisfied if the response contains any pre-frozen realization in that group. Semantic score is required groups hit / 3. Semantic pass requires >=2/3 required groups and zero forbidden groups. Exact mode does not gate semantic pass.

This is deliberately not an LLM judge: the evaluator is reproducible and cannot adapt after outputs. Its remaining limitation is lexical realization within each consequence group; that limitation is to be attacked after the protected run, not tuned on these outputs.

## Live rivals
1. Typed relation labels carry decision-relevant state: GRAPH > both TRANSCRIPT and GRAPH_ABL on protected semantic quality.
2. Extra graph formatting/nouns, not typed relations, explain gains: GRAPH ≈ GRAPH_ABL.
3. Raw chronological history is sufficient: TRANSCRIPT ≈ GRAPH.
4. Hand-coded controller scaffold supplies the main advantage: GRAPH_RULES > GRAPH.
5. V4 ordering was small-sample noise: no stable ordering on V5.

## Decision rule
Primary relational-state support requires GRAPH > TRANSCRIPT and GRAPH > GRAPH_ABL on mean semantic score, with direction also checked by cases/domains rather than pooled mean alone. GRAPH_RULES − GRAPH measures remaining controller scaffold. Exact mode is diagnostic, not the primary endpoint.

No case, rubric, alias group, arm prompt, model setting, seed, or interpretation may be changed after the protected outputs are generated.
