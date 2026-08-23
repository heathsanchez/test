# UVRM Research Graph V3 — Representation Ablation Benchmark

## Question

Does typed research-graph structure improve next-experiment reasoning over the same chronological evidence presented as a transcript?

V1 selected from supplied candidate actions. V2 generated actions from graph evidence but still encoded hand-written generation motifs. V3 freezes a representation-ablation benchmark so the same model can be compared under matched evidence with different state representations.

## Arms

- `TRANSCRIPT`: chronological evidence text + compact UVRM instruction.
- `GRAPH`: same visible evidence and hypothesis text + typed scientific relations.
- `GRAPH_ABL`: same evidence, hypothesis text, and relation endpoints, but relation types are removed.
- `GRAPH_RULES`: GRAPH plus the hand-written generation motifs used by V2. This is an upper-bound/scaffold arm, not the target architecture.

The model, temperature, maximum output tokens, tool access, and number of attempts must be identical across arms. Run order should be randomized and answers stored before scoring.

## Cases

Three prequential cut points from the real E0031-E0034 Lean-kernel lineage:

1. after E0031 — should MAP projection-cost structure rather than jump to raw caching or representation invention;
2. after E0032 — should inspect shared-tail closure/composition rather than promote a heavyweight DAG;
3. after E0033 — should propose the parent-tail splice separator with baseline/ablation before quotient-index invention.

Only evidence at or before each cut point is rendered. Historical next moves and later outcomes are kept in the scorer-only benchmark file.

## Primary comparisons

1. `GRAPH > TRANSCRIPT`: typed persistent structure improves research action generation.
2. `GRAPH > GRAPH_ABL`: the gain comes from scientific relation types, not JSON formatting alone.
3. `GRAPH ~= GRAPH_RULES`: graph state is sufficient without hand-authored generation rules. If GRAPH_RULES remains substantially stronger, candidate-generation policy is still a scaffold.

Do not claim superiority from one lineage. V3 is a measurement-path and protocol test. The next valid escalation is to freeze this harness and add independent SAIR, Triskelion, and MathGraph cases without changing the scoring logic.

## Scoring

Each answer must provide current residual, diagnosis, live rivals, research mode, and smallest next experiment. The scorer checks mode, required mechanism concepts, prohibited premature promotions, and semantic keyword coverage of the frozen historical next move. Human review should additionally score whether the answer gives a genuinely discriminating experiment rather than merely parroting terms.

Report both pass rate and resource vector (model calls, input tokens, output tokens, wall time if available). Do not scalarize unless precommitted.

## Run

```bash
python experiments/uvrm_graph_v3/test_protocol.py
python experiments/uvrm_graph_v3/render_inputs.py
# Run the chosen model separately on rendered inputs and save answers.
python experiments/uvrm_graph_v3/evaluate.py after_E0033 path/to/answer.txt
```

## Claim boundary

This benchmark does not yet run an LLM autonomously in CI and therefore does not establish a graph advantage. It makes that comparison leakage-auditable and ready to execute. A positive result must survive cross-domain expansion and matched model/resource controls.
