# Representation-Change V2 — frozen precommit

## Residual
Representation-Change V1 saturated at 6/6 in every arm. The later problems were too locally decodable from the raw verified outcome and surface language, so V1 could not test whether retained derived structure changes later capability.

## Target
Test whether a retained verified abstraction transfers to a surface-disjoint later decision under a tight one-call budget, beyond what can be recovered from an opaque episode outcome alone.

## Cases
Six frozen source→future pairs spanning Lean-kernel, SAIR, Triskelion, MathGraph, and equational-theory mechanisms. Future problems intentionally rename objects and remove source-domain lexical cues. The correct later action is fixed before model calls.

## Arms
- RAW_OUTCOME: only an opaque factual episode record (intervention/control IDs and outcome), with no reusable abstraction named.
- PROSE_MEMORY: same raw episode record plus a concise natural-language lesson.
- STRUCTURED_STATE: same raw episode record plus a typed relation/action rule.
- STRUCTURED_ABLATION: same raw episode record and endpoints/scope, but the decision-relevant relation/action is weakened or removed.

## Model / budget
- model: gpt-4.1-mini
- temperature: 0
- one call per case/arm
- max_tokens: 80
- 24 calls total
- fixed shuffle seed: 2026082406

## Endpoint
Exact A/B/C/D choice on the surface-disjoint later problem.

## Primary protected prediction
1. STRUCTURED_STATE accuracy > RAW_OUTCOME accuracy.
2. STRUCTURED_STATE accuracy > STRUCTURED_ABLATION accuracy.

Primary pass requires both.

## Secondary
- PROSE_MEMORY > RAW_OUTCOME tests whether explicit semantic retention transfers.
- STRUCTURED_STATE > PROSE_MEMORY tests added value of typed organization; this is not required for the primary claim.
- Per-case arm pattern will be retained without post-hoc rescoring.

## Interpretation boundaries
A positive result is evidence for budget-relative transfer of retained derived state on this frozen benchmark, not unrestricted developmental intelligence. A ceiling or equality is a measurement residual. No rerun or rubric repair after seeing scientific outcomes.