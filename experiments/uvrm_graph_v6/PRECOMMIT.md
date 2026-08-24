# UVRM Graph V6 — frozen mechanistic precommit

## Target
Attack the two live rivals left by V5:

1. **reconstruction rival** — a strong agent can cheaply reconstruct the decision-relevant structure from raw history, so persistent derived graph state adds no real capability;
2. **label-causality rival** — the V5 gain comes from graph endpoints/formatting rather than the meanings of typed scientific edge labels.

V5 is preserved unchanged. This is a post-V5 mechanistic separator, not a new independent generalization benchmark.

## Cases and evaluator
Reuse the eight V5 cases and their already-frozen semantic rubrics without modification. This prevents post-result rubric tuning. V6 changes only the information/compute condition.

## Frozen arms
- `RAW`: chronological evidence only; one model call.
- `RECONSTRUCT_1`: identical raw evidence plus a generic instruction to reconstruct whatever decision-relevant relations are needed before choosing the next move; one model call, same final-answer token cap as GRAPH.
- `RECONSTRUCT_2`: two-stage reconstruction. Stage A receives only raw evidence and must emit a compact relation graph. Stage B receives the same raw evidence plus Stage A's reconstruction and chooses the move. This arm is deliberately more expensive and measures whether extra inference can reconstruct retained state.
- `GRAPH`: the V5 retained typed graph state; one model call.
- `GRAPH_PERMUTED`: identical evidence, endpoints, formatting and graph size as GRAPH, but every edge type is transformed by a fixed precommitted wrong-label map. This attacks causal dependence on edge semantics while preserving graph topology and nouns.

Fixed wrong-label map:
`SUPPORTS→REFUTES`, `REFUTES→SUPPORTS`, `MOTIVATES→WEAKENS`, `WEAKENS→MOTIVATES`, `BLOCKS→SUPPORTS`, with any other label mapped to `REFUTES`.

## Reconstruction cost
The cost unit is model invocations plus generated-token allowance under the same model/API.

- RAW, RECONSTRUCT_1, GRAPH, GRAPH_PERMUTED: 1 invocation, max 220 generated tokens.
- RECONSTRUCT_2: Stage A 1 invocation max 180 tokens + Stage B 1 invocation max 220 tokens = 2 invocations and max 400 generated tokens.

Prompt characters and wall-clock seconds are recorded diagnostically but do not alter the frozen decision rule.

## Model/resource boundary
`gpt-4.1-mini`; temperature 0; OpenAI chat-completions API; fixed shuffled job-order seed `2026082403`. Stage-B scoring is deterministic using the unchanged V5 semantic rubric. No LLM judge.

## Live predictions
### Persistent-state hypothesis
At equal one-call budget, `GRAPH > RECONSTRUCT_1` on mean semantic score and/or pass rate. If `RECONSTRUCT_2` catches GRAPH only with its extra invocation, the supported claim is an efficiency/compression advantage, not an unavailable-capability claim.

### Cheap-reconstruction rival
If `RECONSTRUCT_1 ≈ GRAPH`, raw history is sufficient under the matched budget and persistent graph state is not needed for this benchmark. If `RECONSTRUCT_2 >= GRAPH`, reconstruction is reachable with additional inference; any remaining graph advantage is budget-relative.

### Typed-label causality
If edge semantics are causally useful, `GRAPH > GRAPH_PERMUTED`. If they are approximately equal, V5 does not establish that the labels themselves matter; topology/endpoints/content remain the better explanation.

## Interpretation ladder
1. `GRAPH > RECONSTRUCT_1` and `GRAPH > GRAPH_PERMUTED`: evidence for both persistent-state efficiency and typed-label causality.
2. `GRAPH > RECONSTRUCT_1`, but `RECONSTRUCT_2 ≈ GRAPH`: persistent state compresses inference; no reachability claim.
3. `RECONSTRUCT_1 ≈ GRAPH`: cheap reconstruction rival survives; developmental-state claim weakens.
4. `GRAPH ≈ GRAPH_PERMUTED`: typed labels are not shown causal; graph topology/endpoints are the residual mechanism.
5. Surprise outside these predictions becomes a new residual; do not repair the interpretation after seeing outputs.

No prompt, mapping, case, rubric, model setting, seed, budget or decision rule may be changed after protected outputs are generated.