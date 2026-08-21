# Korovin Distinction Synthesis V4 — Frozen Protocol

## Developmental inheritance

V3 established under causal ablation that syntax-only representation programs do not close the source residual and that the observation family is necessary. V4 treats only that result as an admitted law.

V4 does **not** inherit V3's chosen coordinates, state count, object order, algebraic laws, or multi-valued coordinate-split primitive.

## Question

Once evidence has justified moving into the observable-behavior carrier, can the system synthesize the **distinctions themselves** from a lower-level generic predicate language?

## Blind predicate grammar

The constructor receives raw finite observations and may build Boolean predicates only from:

- `obs[i] == constant`;
- `obs[i] == obs[j]`.

It receives no group/object names, axioms, expected order, coordinate pair, target state count, or post-hoc verifier result.

There is deliberately no `split_probe(i)` or other multi-valued coordinate split.

## Search

For each width from 0 upward, exhaustively enumerate predicate subsets. A representation is the Boolean signature induced by that subset.

Frozen lexicographic objective:

1. number of unresolved behavior collisions;
2. number of represented states;
3. number of predicates;
4. canonical predicate ordering.

Stop at the first width with zero collisions.

## Frozen source and controls

- source: opaque 4-point transformation world;
- independent transfer: opaque 3-point transformation world;
- negative control: 3-point world with a non-invertible generator;
- four independently relabeled source worlds.

Training programs: lengths 0..9.
Protected programs: lengths 10..13.
Syntax-memory baseline is frozen.

The order-3/5/7 breadth controls from V3 are not repeated: V4 tests a lower representational question, while V3 already established order transfer.

## Causal gate

Remove each predicate from the frozen source basis without re-search. Every removal must restore at least one unresolved behavior collision.

## Independent mathematical audit

Only after the Boolean representation is frozen may `verifier.py` test closure, identity, associativity, inverses, commutativity, and element orders.

The negative control must remain perfectly predictive while failing the post-hoc group bundle.

## Claim boundary

A pass supports residual-guided synthesis of a minimal Boolean distinction basis inside an evidence-justified carrier family.

It does not support ex nihilo concept invention. Equality predicates, Boolean signature semantics, and finite exhaustive search remain supplied machinery.
