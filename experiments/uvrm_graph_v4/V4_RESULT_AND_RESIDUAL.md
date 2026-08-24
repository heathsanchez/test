# UVRM Graph V4 — protected result and residual

Protected run: 32688131409 (job 97316827989), head `3f1e2e47ffcb3eb07d4b7251fad570548d943807`.

## Frozen result

The infrastructure path succeeded end-to-end: frozen benchmark validation passed, all 20 `gpt-4.1-mini` calls completed, the frozen scorer ran, and artifacts uploaded.

Frozen scorer summary:

| arm | n | pass rate | mean concept recall | avoid rate |
|---|---:|---:|---:|---:|
| TRANSCRIPT | 5 | 0.00 | 0.00 | 0.00 |
| GRAPH_ABL | 5 | 0.00 | 0.20 | 0.00 |
| GRAPH | 5 | 0.00 | 0.45 | 0.00 |
| GRAPH_RULES | 5 | 0.40 | 0.30 | 0.00 |

This result is preserved exactly. It is not rescored or retroactively relabelled.

## What the result supports

The strongest signal is not the pass-rate column. `GRAPH` produced the highest concept recall (0.45), above `GRAPH_ABL` (0.20) and `TRANSCRIPT` (0.00), while `GRAPH_RULES` was the only arm to receive frozen passes (2/5). This is consistent with typed relations carrying useful decision-relevant information and with hand-coded rules still supplying additional scaffold.

The sample is only five cases, so this is suggestive rather than decisive.

## Sharp residual

The frozen scorer is lexically brittle. `mode_ok` is implemented as literal normalized substring inclusion of one expected mode token, and expected move concepts are also literal normalized substring tests. Several generated answers are semantically close to the intended move while failing because they do not emit the exact label/phrase. Example: for `lean_e0032`, GRAPH_RULES says `MODE: INSPECT` and proposes inspecting shared-tail closure/reuse, while the case label is frozen as `MAP`; the scientific action is close but the mode token fails. This does not invalidate the protected result; it means pass rate is partly a measurement-object residual.

Classification: **bad-objective / measurement representation residual**, not model or graph failure.

## Live rivals

1. Typed graph relations improve next-move selection.
2. Graph formatting merely exposes more useful nouns/phrases to a lexical scorer.
3. GRAPH_RULES wins because supplied rules encode the historical answer scaffold.
4. The five-case sample is too small/noisy for a stable arm ordering.
5. The lifecycle/mode ontology or reconstructed labels are themselves imperfect.

## Next deciding experiment

Do not alter or rescore V4 as evidence. Freeze a V5 evaluator before collecting new protected outputs with:

- new held-out prequential cases not present in V4;
- the same four representation arms;
- exact same model and matched resource budget;
- a two-level outcome: (a) exact mode label and (b) outcome-blind semantic next-move rubric based on required/forbidden consequences rather than exact phrases;
- scorer-ablation reporting exact-label and semantic scores separately;
- enough cases to estimate arm ordering by domain, not only pooled mean;
- protected interpretation: GRAPH must beat both TRANSCRIPT and GRAPH_ABL on semantic next-move quality to support a relational-state claim; GRAPH_RULES > GRAPH measures remaining controller scaffold.

The V4 concept-recall ordering may motivate V5, but must not be used to tune V5 protected cases after outputs are seen.
