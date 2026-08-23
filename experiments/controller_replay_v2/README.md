# Controller Replay V2 — Two-axis research controller

V1 exposed two out-of-vocabulary transitions: infrastructure repair and transfer. V2 does not add them as more flat modes. It factorizes controller state into two questions:

1. **Lifecycle** — what stage of research are we in?
   - REPAIR
   - DISCOVER
   - VERIFY
   - TRANSFER
   - RETAIN

2. **Epistemic mode** — how should we reason at that stage?
   - EXPLOIT
   - INSPECT
   - MAP
   - REFRAME
   - DISCRIMINATE

A controller action is therefore a pair such as `(REPAIR, INSPECT)`, `(DISCOVER, MAP)`, `(TRANSFER, DISCRIMINATE)`, or `(RETAIN, DISCRIMINATE)`.

## Why this is better than V1

V1 mixed research lifecycle with epistemic altitude in one vocabulary. That made `REPAIR_INFRA` and `TRANSFER` look like missing reasoning modes. V2 treats them as orthogonal lifecycle states, while preserving the existing altitude logic.

`IMPORT` is explicitly an input channel, not a truth-bearing mode. An outside paper/comment/repo/analogy does not force a reframe merely by arriving. It can trigger REFRAME only when local evidence already justifies changing altitude (for V2: repeated local failures or an unsharp residual). This prevents novelty-by-retrieval.

## Evidence status

The replay is retrospective smoke evidence only. It is intentionally not a claim of autonomous research ability. The historical labels are interpretations of subsequent repo trajectories. The additional V133→V134, V149, and prospective RBS self-test episodes were not part of the V1 replay, but they are still known history, not protected held-out evidence.

The counterfactual factorization tests are more important than raw replay fit: they require the same lifecycle to combine with different epistemic modes and the same mode to combine with different lifecycle states. They also require IMPORT to be inert when it lacks a structural trigger.

## Next experiment — no more retrospective tuning

Do not add more historical cases to tune V2.

The next evidentiary step must be prospective and frozen before outcomes:

- same base model/tools/verifier/resource budget across arms;
- LOCAL baseline;
- RAW_HISTORY reconstruction baseline with the same historical evidence;
- V2 controller;
- V2 with mode-switch selection ablated/shuffled;
- optional V2+IMPORT arm where outside material is selected without protected-outcome access;
- score terminal verified success and decision-changing information under the same cost vector;
- record whether retained compiled state beats active reconstruction from raw history;
- preserve infrastructure nulls and negative outcomes.

The strongest claim available from a positive run is determined by the weakest control it beats. If RAW_HISTORY matches V2, call it a memory/retrieval result. If V2 beats RAW_HISTORY but not mode-switch ablation, structured retention may help but switching is not identified. If full V2 beats both under matched budgets, the switching policy has prospective causal evidence.
