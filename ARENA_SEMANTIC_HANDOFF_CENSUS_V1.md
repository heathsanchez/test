# Lean Kernel Arena semantic-handoff census V1

## Objective

Test the current high-value hypothesis suggested by the retained kernel history:

> large gains are more likely when an unnecessary producer→consumer semantic boundary is eliminated than when the intermediate operation is merely made cheaper.

This is a diagnostic experiment only. It cannot admit an optimization.

## Frozen checker

The census profiles the Arena-pinned MathGraph V2 revision:

`metalogiclabs/mathgraph-lean-kernel@3d7585c21242f29fdaa48ae9a16e16c6afe42238`

The checker is run with the same 4-thread configuration used by the Arena checker definition. The frozen Arena corpus artifact remains `8931227426` for semantic sanity and discriminator selection.

## Competing causal worlds

- H1: environment projection / canonical identity remains the dominant removable boundary.
- H2: infer→apply/eval handoffs contain repeated work large enough for another beta-like fusion.
- H3: eval/force/unfold handoffs repeatedly reconstruct weak-head information already available to the producer.
- H4: conversion consumes freshly-created intermediates through a high-cost single-use boundary.
- H5: no single semantic handoff has enough removable mass; remaining cost is dispersed.

The experiment does not choose a winner in advance.

## Probe

Use Callgrind on the unchanged V2 binary and extract direct call-graph edges touching the semantic phase vocabulary:

`eval`, `infer`, `apply`, `force`, `unfold`, `whnf`, `conv`, `defeq`, `unify`, `key_env`, `prune_env`, `intern_frame`, `thunk`, `proj`, `iota`, `recursor`.

For each edge retain:

- caller;
- callee;
- call count;
- Callgrind instruction cost attributed to the edge;
- workload;
- normalized instruction fraction within the captured profile.

The primary ranking is **edge instruction mass**, not raw frequency. Frequency without removable cost is not actionable.

## Discriminators

At minimum:

1. `good/perf/grind-ring-5.ndjson`, the known dominant environment/canonicalization workload.
2. Up to two source-distinct available performance tests selected deterministically from the frozen artifact by lexicographic path order, excluding grind-ring-5.

No discriminator is removed after results are visible. If fewer than three performance tests exist, the run records that corpus limitation rather than substituting hand-picked cases.

## Semantic gate

Before profiling, the unchanged V2 checker must reproduce the expected good/bad verdict on the complete frozen corpus with zero declines. A semantic mismatch makes the census invalid.

## Decision rule

After aggregating across workloads:

- If one producer→consumer edge or tightly-related edge family carries a large instruction fraction across at least two source-distinct workloads, freeze the smallest fusion A/B around that boundary.
- If an edge is large only on grind-ring-5, classify it as an applicability residual and require a pre-result activation predicate before intervention.
- If environment projection remains large but no consumer edge concentrates its cost, continue the access/representation line rather than pretending fusion is supported.
- If no semantic edge family has substantial mass, reject the fusion-first hypothesis for the present frontier and return to whole-profile residual analysis.

## Required next experiment if a winner exists

A0: exact V2.

A1: eliminate exactly one intermediate semantic boundary while preserving verifier semantics.

A1-ablation: retain the A1 control flow but force reconstruction of the intermediate state, isolating the fusion mechanism.

Promotion requires semantic equivalence, deterministic instruction reduction, protected resource improvement, and causal loss under ablation.
