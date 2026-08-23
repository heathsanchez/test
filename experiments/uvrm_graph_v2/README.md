# UVRM Research Graph V2

V1 showed that a typed graph could recover the historically useful E0034 action when candidate actions were already supplied. That left two serious loopholes: hindsight and action injection.

V2 closes both on the E0031-E0034 Lean-kernel lineage.

## Changes from V1

1. **Time-sliced evidence views.** Every evidence item and relation has an order. A controller choosing after E0031 cannot inspect E0032/E0033.
2. **Evidence-derived hypothesis state.** `SUPPORTED`, `REFUTED`, and `UNRESOLVED` are computed from typed relations, not stored as trusted labels.
3. **Action generation from graph motifs.** Candidate actions are not stored in the graph. The controller generates MAP / INSPECT_CLOSURE / DISCRIMINATE / REFRAME moves from the currently visible evidence pattern.
4. **Evidence ablations.** Removing the relation that supports tail reuse removes the tail-splice action. Removing a refutation restores uncertainty about the rejected branch.
5. **Perturbation test.** If E0033's exact reusable-tail opportunity is lowered below the frozen threshold, the splice separator is no longer generated.
6. **Closure before invention.** A quotient-index representation experiment remains available but is dominated while an evidence-supported same-frame composition test exists.

## Frozen historical checkpoints

- After E0031: generate `MAP_SCAN_COST`.
- After E0032: generate `MAP_TAIL_REUSE`.
- After E0033: generate `TEST_TAIL_SPLICE`.

These correspond to the recorded progression from late quotient discovery, to rejection of a heavyweight indexed environment, to inspection of shared-tail reuse, to the E0034 parent-tail splice separator.

## Claim boundary

This is still a deterministic reconstruction smoke test. It does **not** show that a general LLM can invent these action-generation motifs from scratch, nor that graph state beats a raw transcript under matched model budgets.

It establishes a narrower result: a typed evidence graph plus generic UVRM-style generation rules can recover three consecutive historical research-mode/action transitions without future evidence, and the final action disappears when its causal support is ablated.

## Next test

Run a matched prospective comparison:

- `TRANSCRIPT`: same model receives only the chronological raw research log.
- `GRAPH`: same model receives the typed evidence graph, but no narrative interpretation or supplied candidate actions.
- `GRAPH_ABLATED`: remove residual/REFUTES/SUPPORTS/RIVAL structure while preserving raw facts and token budget.

Freeze model, prompt, tool budget and target. Score: correct frontier reconstruction, repeated-dead-branch rate, live-rival recall, time/calls to a deciding experiment, and verified downstream research yield.
