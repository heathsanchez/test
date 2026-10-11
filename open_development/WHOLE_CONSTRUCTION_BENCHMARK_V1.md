# Whole-construction developmental benchmark V1 — frozen experimental contract

## Objective
Test total-lifecycle optimisation over a source-certified dependency graph, not cheapest-next-action selection. Use the real MDA v7 ProofCompositionAdapter, FiniteAdapter, EvidenceStore, independent verifier, source role transport, and exact executable-ledger replay. Flash-style incremental reclosure is a CANDIDATE to implement, not an already warranted result.

## Pinned baseline
Parent source `13325089c471996b8b68f46540fd4ad449df752c`, independently qualified CI `38043019010`. Retain the original test cases, all failures, verifier scopes and old run artifacts.

## Workload
Construct one joint development episode with at least:
- three-generation proof-program acquisition and two later role-requalified generations;
- 16 held-out dependent proof obligations plus the original finite-observation question acquisition and reuse;
- shared ancestors, independent siblings, source-body ablation, forged-source rejection, ancestor revocation, restart, and requalification;
- two independent active frontiers whose feasible candidate sets change when one warranted result is admitted or revoked.

Do not fabricate a cross-frontier dependency: source exact proof obligations and finite authority must remain separately typed. If no legitimate coupling exists, report NO_CROSS_FRONTIER_EDGE rather than force a positive Flash result.

## Four matched planners
A. Local greedy: choose lowest immediate cost eligible acquisition.
B. Whole-sequence: optimise entire sequential admissible acquisition path.
C. Whole-DAG: optimise total acquisition + verification + execution + storage/replay cost with shared capabilities.
D. Whole-DAG plus incremental warrant reclosure: update only affected dependency cones on admission/revocation.

All arms receive the same declared grammar, available certificates, source evidence, goals, verifier and budget. Include an exact executable-memory replay control (must tie in reach), and exhaustive small-subgraph oracle for checking optimiser decisions. Do not confuse a lower remaining acquisition cost with lower full-lifecycle cost.

## Authority and results
Every accepted proof/observation must pass the original independent adapter. No guessed verifier receipts. Source, contract, interpreter and task digests are pinned. Negative controls must remain negative. If no candidate is qualified, return UNKNOWN, not an invented completion.

Measure per arm: protected ACCEPT/UNKNOWN, proposal checks, independent verifier calls, total wall/CPU time, peak RSS, retained bytes, cold start/restart, reclosure touched nodes, ablation/revocation impact, complete total cost in declared units. Report Pareto frontier when costs cannot be legitimately converted into one scalar.

## Preregistered success boundary
WARRANTED only when exact source CI passes, full positive/negative parity holds, and the selected whole graph has a lower measured complete cost than local greedy. Strict advantage over a strong global oracle is not expected: tie is the correctness check. Flash adds value only if cross-frontier reclosure measurably reduces rework or reopens a genuinely dormant capability. Independent natural-domain transfer and autonomous constructor invention remain UNKNOWN.

## Cheapest decisive experiment
First instrument the existing MDA v7 source to emit a real dependency graph, verified receipt list and per-event costs with zero semantic changes. Compare its extracted graph against the original ledger. Only then add whole-DAG planning, followed by incremental reclosure, with source-exact protected checks after each stage.
