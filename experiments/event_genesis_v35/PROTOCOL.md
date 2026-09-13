# Consequence-Selected Eventization from an Undirected Cyclic Boundary V35 — Frozen Protocol

## Question

Can V34's supplied sequential event order be weakened so that neither event boundaries nor a distinguished origin/direction are given in advance?

V35 presents each encounter as a finite binary cycle. The same physical boundary is supplied under every rotation and reflection with the same consequence, so external array position and traversal direction cannot be authoritative.

The frozen kernel may hypothesize a view only through two generic ingredients:

1. an oriented binary motif that must occur exactly once on the cycle and therefore may define an origin and direction;
2. a chunk width used to partition the remaining oriented bits into anonymous symbols.

No challenge-specific variable, event label, semantic coordinate, history register, pair/tuple constructor, context tag, or fixed event boundary is supplied.

The hidden challenge pack is committed only after this scientific core is frozen.

## Candidate views

For each motif length m from 2 through 6, the kernel exhaustively enumerates every binary motif p in {0,1}^m.

For every chunk width w dividing the remaining cycle length, the parser tests whether p occurs in exactly one oriented traversal of every encountered cycle.

If so, p determines a candidate origin and direction. The remaining raw bits are traversed in that orientation and grouped into consecutive chunks of width w. Each chunk becomes an anonymous integer symbol.

Thus the kernel is not told where an event begins, how many raw bits constitute one event, or which direction is forward.

If no unique oriented motif exists, that candidate view is invalid.

## Consequence machine

For each valid view, the kernel constructs the exact residual machine over the resulting anonymous symbol sequence.

Equal future consequence functions are merged. A state whose entire remaining subtree has one consequence collapses immediately to a terminal.

The view therefore competes on the size of the consequence machine it induces.

## Frozen description-length ordering

Each valid view and machine is encoded with one fixed prefix-free-style bit accounting:

- Elias-gamma length of motif length, plus the motif bits;
- Elias-gamma length of chunk width;
- Elias-gamma length of machine-state count;
- root-state pointer;
- one tag bit per state;
- consequence-label bits for terminal states;
- Elias-gamma transition-count plus fixed-width symbol and state-pointer fields for transition states.

The exact implementation is frozen in kernel.py before the hidden pack.

The minimum encoded description is selected. All exact ties remain on the frontier.

This cost code is part of the supplied prior. V35 does not claim that description length is uniquely privileged or free of inductive bias.

## Expected qualitative tests after freeze

The hidden pack will include boundaries generated from latent payloads but supplied only as raw cycles and all their dihedral presentations.

The evaluator will test whether:

- constant consequence requires no parsing view at all;
- asymmetric consequence can select a unique oriented anchor;
- symmetric consequence preserves opposite orientations when both are equally economical;
- different consequences select different chunk widths, so event grain is consequence-relative rather than fixed;
- relational and conditional consequences induce larger exact residual machines;
- permutation of latent sources changes the selected eventization without changing the frozen kernel;
- consequence-label relabelling preserves the selected structural view and machine shape;
- incomplete dihedral authority remains UNKNOWN;
- verifier ablation authorizes no eventization.

## Frozen gates

E1. Scientific core remains byte-identical after the challenge pack is added.
E2. Every hidden world replays exactly under one frozen kernel.
E3. Constant consequence contracts to one terminal and no selected view.
E4. An asymmetric one-source task earns a unique orientation.
E5. A reversal-symmetric task preserves at least two opposite-orientation minimum views.
E6. Across the hidden suite, at least three distinct chunk widths are selected by consequence.
E7. At least one relational task selects a chunk width larger than one because its frozen description is shorter than the raw-bit alternative.
E8. A four-class relation yields four consequence terminals under the selected eventization.
E9. An eight-class relation yields eight consequence terminals.
E10. A conditional task is represented exactly with a nontrivial selected eventization.
E11. Permuting latent source order changes the selected eventization for multiple tasks.
E12. No external rotation or reflection is privileged: authority includes complete dihedral orbits.
E13. Consequence-label relabelling preserves selected motif/width up to equal-cost frontier symmetry and preserves machine graph shape.
E14. Incomplete dihedral authority remains UNKNOWN.
E15. Verifier ablation authorizes no parsing search.
E16. Challenge-axis names and latent-source identifiers are absent from the frozen executable kernel.

## Claim boundary

A pass would show a bounded form of eventization genesis, not presuppositionless perception.

V35 still supplies substantial structure:

- a binary raw boundary;
- cyclic adjacency;
- a generic motif-anchor hypothesis language;
- consecutive chunking as the allowed segmentation family;
- finite exhaustive search through motif length 6;
- an external consequence verifier;
- the frozen description-length code.

Therefore V35 cannot establish that event segmentation, adjacency, symbolization, or parsing grammar arise from nothing.

Its precise target is narrower:

> fixed event boundaries, fixed origin, fixed direction, and fixed event width are not required for these finite worlds; consequence can select them from a generic cyclic parsing language, and can preserve non-canonicity when consequence does not justify a unique choice.

If V35 passes, the next remaining handhold is the supplied parsing grammar itself: motif anchoring plus consecutive chunking.
