# Korovin Representation-Program Invention V3 — Frozen Protocol

## Upgrade over V2

V2 still possessed a privileged mechanism: states were created directly by equality of a chosen feature tuple.

V3 removes that mechanism from the blind constructor.

The system begins with one undifferentiated block containing all observed programs. It must synthesize a **representation-building program** from a generic DSL. Candidate programs may split a current partition by a generic feature, refine it by successor behavior, or attempt transition-profile coarsening. Only the resulting residuals decide whether a program is acceptable.

No algebraic law, target object name, expected order, or post-hoc verifier output may influence representation-program synthesis.

## Generic DSL

Allowed primitives:

- split by program length;
- split by first token;
- split by last token;
- split by token count;
- split by one opaque observation coordinate;
- refine by one-step successor block destinations;
- merge blocks with equal representative transition profiles.

Maximum program length: 4.

The constructor begins from exactly one state. There is no direct tuple-key constructor.

## Score

Frozen lexicographic objective:

1. predictive + transition conflicts;
2. number of resulting states;
3. representation-program length;
4. primitive description cost.

The search stops at the first program length containing an exact residual-closing representation.

## Protected evaluation

Train: all opaque programs of lengths 0..9.
Protected holdout: lengths 10..13.
Baseline: exact syntax memory.

Worlds:

- opaque 4-point source;
- independent opaque 3-point transfer;
- non-invertible negative control;
- opaque order 3/5/7 controls;
- four independently relabeled source controls.

## Independent verifier

Only after the representation program is frozen may a separate module audit closure, identity, associativity, inverses, commutativity, and element orders.

## Causal gates

- remove each operation from the synthesized source program; the residual must return;
- forbid the entire observation-splitting primitive family and rerun the same synthesis budget; no exact representation may remain;
- negative control must remain perfectly predictive while failing the post-hoc group bundle.

## Claim boundary

A pass supports **constrained abstraction-program synthesis**: residuals can force construction of a representation-building procedure that recovers a familiar finite mathematical object.

It does not show ex nihilo invention. The generic DSL still supplies split/refine/merge operations.
