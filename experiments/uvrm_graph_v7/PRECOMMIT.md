# UVRM Graph V7 — frozen sufficient-state edge-mask census

## Target
Test whether the full retained typed graph contains redundant distinctions, or whether both frozen relations are required for protected next-move selection.

This is the direct residual from V6. It is a mechanistic sufficiency/minimality experiment, not a new independent generalization benchmark.

## Cases and evaluator
Reuse the eight V5/V6 cases and their already-frozen semantic rubrics without modification. Each case has exactly two typed scientific relations. No required/forbidden alias, case text, expected mode or scoring rule may change after this precommit.

## Frozen arms
For each case, preserve the same evidence nodes and test all four subsets of its two typed relations:

- `MASK_00`: no typed relations; evidence nodes only.
- `MASK_10`: relation 1 only.
- `MASK_01`: relation 2 only.
- `MASK_11`: both relations; full GRAPH condition.

Relation order is the frozen order in `experiments/uvrm_graph_v5/cases.json`. No relation is selected based on observed outputs.

## Resource boundary
`gpt-4.1-mini`; temperature 0; max 220 generated tokens; one model call per case×mask; 32 calls total; OpenAI chat-completions API; fixed shuffled order seed `2026082404`. Same prompt prefix and answer format across masks.

## Frozen evaluation
Reuse the V5 semantic evaluator exactly: semantic score = required consequence groups hit / 3; semantic pass = >=2/3 required groups and zero forbidden groups. Exact mode remains diagnostic only.

## Primary questions
1. **Redundancy:** Does either one-edge mask preserve full-graph behavior on a case?
2. **Necessity:** Does removing a particular edge reduce semantic score or flip a pass to fail?
3. **Synergy:** Are there cases where neither single edge is sufficient but both together are?
4. **Quotientability:** What is the smallest edge count per case that attains the same frozen semantic score as `MASK_11`?

## Frozen aggregate summaries
Report for each mask: pass rate and mean semantic score. Also report per case:
- full-graph score;
- best zero/one-edge score;
- minimum edge count attaining the full-graph score, if any;
- whether edge 1 and/or edge 2 is individually necessary relative to full graph;
- whether the case exhibits two-edge synergy.

## Interpretation
- If many cases preserve `MASK_11` behavior with one or zero edges, the retained graph is over-specified and admits quotienting.
- If different cases require different edges, sufficient state is context-dependent rather than a fixed global schema.
- If both edges are jointly required on some cases, relation composition itself carries decision-relevant state.
- If `MASK_00 ≈ MASK_11`, V6's apparent graph advantage is unstable on replay and should be downgraded.

No transfer claim is allowed from V7. Any minimal-state rule inferred from V7 must be frozen and tested on new held-out cases in a subsequent experiment.
