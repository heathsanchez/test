# UVRM Graph V6 — protected result and residual

## Protected run
Run: 32691619972
Job: 97326204161
Trigger commit: `d38055fd8790871ddfd4db7e082171d642bf2ede`

Validation passed and the full protected benchmark completed successfully. The unchanged V5 rubric and frozen wrong-label map were used.

## Frozen aggregate result

| Arm | invocations/case | token allowance | semantic pass | mean semantic score |
|---|---:|---:|---:|---:|
| RAW | 1 | 220 | 4/8 | 0.3333 |
| RECONSTRUCT_1 | 1 | 220 | 4/8 | 0.3750 |
| RECONSTRUCT_2 | 2 | 400 | 3/8 | 0.4167 |
| GRAPH | 1 | 220 | 7/8 | 0.7083 |
| GRAPH_PERMUTED | 1 | 220 | 4/8 | 0.5000 |

No arm produced a frozen forbidden consequence.

## Precommitted interpretation
Both primary mechanistic separators went in the predicted direction:

- `GRAPH > RECONSTRUCT_1` at matched one-call budget.
- `GRAPH > GRAPH_PERMUTED` with identical evidence, endpoints, formatting and graph size but corrupted relation semantics.

The deliberately more expensive two-call reconstruction arm did not catch GRAPH on this bounded benchmark.

This supports two bounded claims:

1. retained typed state provides a budget-relative next-move selection advantage over raw-history reconstruction under the tested model/resource boundary;
2. relation semantics carry causal information in at least part of the benchmark, because wrong labels reduce protected performance while topology/endpoints are preserved.

This is not a claim that reconstruction is impossible without the graph, nor that every relation label matters on every case.

## Sharp residual
The remaining question is now **sufficiency/minimality**:

> Which retained distinctions are actually necessary for lawful next-action selection, and which can be forgotten without changing protected behavior?

The full graph may still contain redundant state. The next deciding experiment should therefore keep evidence, model, budget, endpoints and evaluator fixed while exhaustively ablating relation subsets. Since every frozen V5 case contains exactly two typed relations, all four edge masks can be tested without search or post-result tuning: none, edge 1 only, edge 2 only, both.

This is a mechanistic quotient experiment, not a new transfer claim. Its purpose is to locate whether a smaller sufficient retained state exists before testing that compression on new held-out cases.
