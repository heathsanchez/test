# Hex Meta-Language Substrate Genesis V8 — Frozen Protocol

## Question

V7 still supplied the selector atom `TRUE`, which directly denotes "select every named relation."

V8 removes that atom.

Can certified inadequacy of the old selector language authorize a generic finite Boolean-function substrate, from which the missing meta-language primitive is synthesized, retained, and reused on a larger unseen relational language?

## Prior authority

V7 must read:

`VERIFIED_META_RULE_GENESIS_AND_TRANSFER`

from:

`experiments/hex_meta_selector_genesis_v7/AUTHORITY.json`

The prior selected behavior is used only as protected consequence. V8 does not receive `TRUE` as an available selector constructor.

## Initial meta-language

Atoms:

- `FIRST`: relation index is first.
- `LAST`: relation index is last.

Constructor:

- pointwise Boolean `OR`.

The full semantic closure of these atoms under OR is exhausted before growth. Because OR is associative, commutative, and idempotent, the only nonempty denotations are:

- `FIRST`
- `LAST`
- `FIRST OR LAST`

No additional syntax is treated as a distinct capability once it has the same selector denotation.

## Protected consequence worlds

The old language is judged against three frozen worlds.

### World 1 — one named relation

- carrier size 3;
- all 64 loopless directed graphs;
- all 4,096 ordered pairs.

### World 2 — two named relations

- carrier size 3;
- exactly one loopless arc per relation;
- 36 objects;
- all 1,296 ordered pairs.

### World 3 — three named relations

- carrier size 2;
- exactly one loopless arc per relation;
- 8 objects;
- all 64 ordered pairs.

For every selector, source isomorphism uses one common carrier permutation. Target isomorphism permits independent permutations inside role colours. A named relation is identity-anchored only when the selector chooses that relation.

Growth is authorized only if every denotation in the complete OR-closure has nonzero semantic disagreement on the protected worlds.

## Generic growth substrate

After old-language inadequacy is certified, expose a **generic binary Boolean truth-table substrate**.

A candidate is one of all 16 functions:

[
f : \{0,1\}^2 \to \{0,1\}.
]

The two inputs are the existing `FIRST` and `LAST` observations at a relation position.

No truth table is named `TRUE`, `AND`, `XOR`, etc. Candidates are represented only by their four output bits in input order:

`00, 01, 10, 11`.

All 16 are exhaustively evaluated over all three protected consequence worlds.

A truth table qualifies only if it has zero semantic disagreement everywhere.

## Promotion and causal controls

A pass requires:

- the initial OR-closure is completely exhausted and inadequate;
- exactly one of the 16 truth tables qualifies;
- its output bits are `1111`;
- ablating the synthesized table restores old-language inadequacy;
- the synthesized selector reproduces the V7 selected behavior without using a supplied `TRUE` atom.

The table is then retained as a new primitive selector denotation.

## Prospective transfer / compounding

Use a new four-relation qualification world:

- carrier size 2;
- exactly one directed arc per named relation;
- 16 objects;
- all 256 ordered pairs.

Compare:

- **cold**: exhaust all 16 truth tables, replaying the three protected worlds plus the new four-relation world until the first fully qualified candidate;
- **warm**: use the retained synthesized table and replay the same protected + new worlds.

Because candidates are enumerated from `0000` to `1111`, the retained table is the 16th cold candidate.

The precommitted developmental comparison is therefore candidate-state count and semantic pair-comparison count under identical replay obligations.

## Held-out downstream Hex check

Only after the four-relation transfer qualifies, generate an unseen carrier-size-3 problem with four named relations and multiple arcs per relation.

Compile the retained truth-table selector into the identity-channel representation and kernel-check:

- one positive isomorphic pair;
- one negative non-isomorphic pair.

Pinned external capability:

- `leanprover/hex-graph-iso` tag `v0.6.0`
- commit `f247c0898414ca29c502691e3a8ad0b3ce0b4f6a`
- Lean `v4.34.0-rc2`

## Claim boundary

A pass earns bounded **meta-language primitive genesis from a generic finite Boolean-function substrate**, causal old-language inadequacy, retention, and prospective cross-scale reuse.

It does not establish genesis of the generic truth-table substrate itself, autonomous subject selection, or verifier genesis.
