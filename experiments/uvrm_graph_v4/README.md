# UVRM Research Graph V4 — cross-domain representation ablation

## Question
Does typed scientific graph structure improve next-research-move reasoning beyond the same evidence supplied chronologically or with relation labels ablated?

V4 freezes five retrospective/prequential cut points spanning Lean-kernel optimization, SAIR equational reasoning, Triskelion mechanism discovery, and MathGraph capability identity.

## Arms

- `TRANSCRIPT`: same evidence as chronological notes.
- `GRAPH_ABL`: same evidence and relation endpoints as GRAPH, but edge types withheld.
- `GRAPH`: typed relations such as SUPPORTS / REFUTES / WEAKENS / MOTIVATES / BLOCKS.
- `GRAPH_RULES`: GRAPH plus hand-authored UVRM routing motifs; an explicit scaffolded upper bound.

All arms receive the same compact UVRM instruction. Expected mode/move labels live only in `cases.json` for scoring and are not rendered into prompts.

## Frozen cases

1. Lean E0031: late canonical convergence vs naive raw caching -> map projection cost.
2. Lean E0032: shallow scan cost weakens heavy-DAG escalation -> inspect shared-tail reuse.
3. SAIR five-residual restart: restored budgets plus persistent residuals -> map inference/operator effects rather than merely spend more search.
4. Triskelion rapid phase sniff: square/reduce learnability vs weak squaremod -> matched composition/interface separator, not a performance claim.
5. MathGraph V4->V5: reusable repair law under changed DSL presentation -> transfer/behavioral identity test before treating syntax as capability identity.

## Evidence boundary
This benchmark is retrospective. Source commits existed before V4 was assembled. It tests whether a frozen representation/scorer can recover historically useful research moves across domains; it is not independent evidence that GRAPH causes better research.

The next admissible claim requires a prospective untouched case stream with matched model/version/settings and model-call/token/tool budgets.

## Primary comparisons

`GRAPH > GRAPH_ABL` isolates value of typed scientific relations.

`GRAPH > TRANSCRIPT` tests whether explicit relational state helps beyond chronological memory.

`GRAPH ~= GRAPH_RULES` would suggest the graph contains enough structure that hand-written routing motifs add little; a large GRAPH_RULES gap localizes the remaining scaffold to the action generator/controller.

## Run

```bash
python experiments/uvrm_graph_v4/validate.py
python experiments/uvrm_graph_v4/render.py
# Run the rendered prompts with one frozen model/config and save answers as JSON.
python experiments/uvrm_graph_v4/score.py answers.json
```

Do not tune cases, scorer, or prompt templates after inspecting arm outputs. Add future cases only under a new version/protocol.
