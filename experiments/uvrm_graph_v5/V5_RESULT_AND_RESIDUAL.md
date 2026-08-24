# UVRM Graph V5 — protected result and residual

Protected run: 32689624406 (job 97320857441), head `ad1ce710b04f508497d308b8322d6807cbf2781e`.

## Frozen result

The run completed successfully end-to-end: validation passed for 8 protected cases spanning Lean kernel, SAIR, Triskelion, and MathGraph; all 32 `gpt-4.1-mini` calls completed; the frozen deterministic scorer ran; and artifacts uploaded.

| arm | n | exact mode rate | semantic pass rate | mean semantic score | forbidden rate |
|---|---:|---:|---:|---:|---:|
| TRANSCRIPT | 8 | 0.000 | 0.375 | 0.4167 | 0.000 |
| GRAPH_ABL | 8 | 0.000 | 0.750 | 0.6250 | 0.000 |
| GRAPH | 8 | 0.000 | 1.000 | 0.7083 | 0.000 |
| GRAPH_RULES | 8 | 0.375 | 0.750 | 0.7083 | 0.000 |

The precommitted primary endpoint is satisfied on pooled mean semantic score:

`GRAPH (0.7083) > TRANSCRIPT (0.4167)` and `GRAPH (0.7083) > GRAPH_ABL (0.6250)`.

GRAPH also achieved 8/8 semantic passes, compared with 6/8 for GRAPH_ABL and 3/8 for TRANSCRIPT.

## Domain/case direction check

Mean semantic score by domain (two protected cases each):

| domain | TRANSCRIPT | GRAPH_ABL | GRAPH | GRAPH_RULES |
|---|---:|---:|---:|---:|
| Lean kernel | 0.333 | 0.333 | 0.667 | 0.833 |
| SAIR | 0.333 | 0.667 | 0.667 | 0.667 |
| Triskelion | 0.500 | 0.833 | 0.833 | 1.000 |
| MathGraph | 0.500 | 0.667 | 0.667 | 0.333 |

GRAPH is above TRANSCRIPT in all four domains. Relative to GRAPH_ABL, GRAPH is higher in Lean and tied in the other three domains; it is never lower. Thus the pooled typed-relation gain is real under the frozen scorer, but most of the graph-vs-transcript gain is already obtained by graph structure/endpoints before relation labels are restored.

## What this supports

1. A structured graph representation materially improves protected next-move selection over chronological evidence in this bounded benchmark.
2. Typed relation labels add a smaller incremental gain beyond graph structure/endpoints, concentrated here in the Lean cases.
3. The hand-coded controller scaffold is not the main source of semantic advantage: GRAPH_RULES ties GRAPH on mean semantic score and has lower semantic pass rate (6/8 vs 8/8), although it improves exact mode-label emission.
4. V4's monotone direction was not pure small-sample noise: V5 independently preserves TRANSCRIPT < GRAPH_ABL < GRAPH on the primary pooled semantic score.

## Sharp residual

The strongest remaining rival is no longer `raw chronological history is sufficient`. It is:

**Graph structure / explicit relational endpoints may supply most of the advantage, while typed edge labels contribute only a modest incremental benefit.**

A second residual is reconstruction: a strong system given the same raw history may be able to reconstruct an equivalent graph/state within budget, in which case the advantage is representation convenience rather than persistent developmental state.

## Next deciding experiment

Do not alter or rescore V5. The next protected separator should target the two live residuals directly:

1. **Relation-label necessity ablation.** Use more held-out cases selected specifically where the edge type changes the scientific interpretation while endpoints/facts stay fixed. Compare correct typed labels vs labels withheld vs labels permuted/wrong-direction, under the same graph topology and text budget.
2. **Raw-history reconstruction baseline.** Give a matched agent the same raw chronological evidence plus generic graph-construction tools and a frozen reconstruction budget, but not the retained derived graph. Score both reconstruction cost and downstream next-move quality. This separates persistent-state advantage from memory/reformatting advantage.

The developmental claim should ratchet only if retained graph state beats a raw-history reconstruction system under a pre-frozen matched budget, and if relation-label ablation/permutation causally degrades protected decisions where edge semantics are genuinely decision-relevant.
