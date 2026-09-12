# Hex Digraph Exaptation V1 — Frozen Pilot Protocol

## Question

Can an independently developed verified graph-isomorphism capability (HexGraphIso / verified nauty semantics) be lawfully reused for a non-native finite directed-graph obligation through an adapter that is selected by finite semantic evidence, while a lossy adapter is rejected?

This is a first natural-domain transfer pilot. It is not a claim of learned adapter discovery, open-ended transfer, or general graph-reduction synthesis.

## External capability freeze

- Capability: `leanprover/hex-graph-iso`
- Release: `v0.6.0`
- Commit: `f247c0898414ca29c502691e3a8ad0b3ce0b4f6a`
- Lean toolchain: `leanprover/lean4:v4.34.0-rc2`

Hex is treated as an already-retained verified capability. The experiment tests the semantic transport into its input language, not Hex's internal correctness.

## Source domain

Finite loopless directed graphs on a fixed labelled carrier. Source isomorphism is exact: all vertex permutations are enumerated.

## Declared adapter substrate

Two adapters are admitted before the decisive test.

1. `ROLE_SPLIT_ANCHOR` (candidate semantic adapter)
   - For each source vertex `v`, create three target vertices: `out(v)`, `in(v)`, and `anchor(v)`.
   - Use three ordered Hex colours to preserve these roles.
   - Add `anchor(v)-out(v)` and `anchor(v)-in(v)`.
   - Encode each directed arc `u -> v` by `out(u)-in(v)`.

2. `SYMMETRIZE` (lossy control)
   - Forget direction and retain only the underlying undirected edge set.

The candidate substrate is fixed. No adapter is invented after seeing the held-out cases.

## Qualification world

Exhaust all 64 loopless directed graphs on 3 vertices and all 4096 ordered pairs.

For each pair:
- compute exact source directed-graph isomorphism by exhaustive permutation;
- compute exact target colour-preserving graph isomorphism for `ROLE_SPLIT_ANCHOR`;
- compute exact target graph isomorphism for `SYMMETRIZE`.

Precommitted semantic gate:
- `ROLE_SPLIT_ANCHOR` must have zero disagreement with the source oracle over the complete finite world;
- `SYMMETRIZE` must exhibit at least one disagreement.

## Held-out transfer

After qualification, test unseen 4-vertex source obligations through the selected adapter and Hex:

- positive pair: a directed path and a nontrivial relabelling;
- negative pair: two non-isomorphic orientations of the same undirected path;
- lossy-adapter control: the negative pair becomes isomorphic after symmetrization.

Hex must kernel-check:
- positive encoded pair is isomorphic;
- negative encoded pair is not isomorphic;
- lossy control pair is isomorphic after direction is erased.

## Interpretation

A pass supports only:

> finite exhaustive semantic qualification on the declared 3-vertex source world, followed by successful held-out 4-vertex exaptation into an independently developed verified Lean capability.

It does not establish a general theorem that the adapter is faithful for all finite sizes, autonomous discovery of the adapter, natural-domain breadth, or open-ended developmental transfer.
