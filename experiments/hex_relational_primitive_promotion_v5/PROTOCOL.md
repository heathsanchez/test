# Hex Relational Primitive Promotion V5 — Frozen Protocol

## Question

Can a successful developmental program from one domain be promoted into a role-agnostic developmental primitive and reused on a structurally larger, held-out source domain, reducing future developmental search while preserving exhaustive semantics and downstream Hex verification?

V4 constructed the successful directed-graph repair compositionally from three low-level operations. V5 does not supply the successful higher-order primitive. It derives a macro schema from the sealed V4 authority and tests whether that learned schema transfers to a new source language with **two named directed binary relations**.

## Prior authority

Read, do not rewrite:

`experiments/hex_digraph_compositional_repair_genesis_v4/AUTHORITY.json`

Required prior verdict:

`VERIFIED_COMPOSITIONAL_REPAIR_GENESIS`

The V4 winning state had:

- two active roles in its source relation channel;
- one newly added role;
- an identity coupling from every active role to that new role.

## Macro induction rule

V5 may promote a macro only if the sealed V4 state satisfies this exact structural predicate:

1. exactly one fresh role was added relative to the two-role starting substrate;
2. every role appearing in the source arc channel is coupled to the fresh role;
3. the fresh role carries no source arc endpoint;
4. there are no other identity couplings.

If the predicate holds, emit the structural macro schema:

`ADD_ONE_FRESH_ROLE; COUPLE_EVERY_ACTIVE_RELATION_ROLE_TO_FRESH`

The macro is represented structurally in evidence; its name is descriptive only. The transfer implementation instantiates it over the active roles of the new source language.

## Transfer source language

Objects have one carrier and **two named loopless directed binary relations**, `R0` and `R1`.

Source isomorphism is one vertex permutation applied simultaneously to both relations.

The target pre-anchor representation uses four ordered target roles:

- two anonymous endpoint roles for `R0`;
- two anonymous endpoint roles for `R1`.

Thus the transfer problem has four active relation roles, not the two seen in V4.

## Complete qualification world

Carrier size: 3.

For each named relation, require exactly one loopless directed arc.

There are 6 choices for the `R0` arc and 6 choices for the `R1` arc, hence exactly **36 source objects** and **1,296 ordered pairs**.

This entire world is exhausted.

## Cold developmental baseline

The cold low-level basis contains only:

- add one fresh role;
- add an identity coupling from any existing active role to the fresh role.

After the fresh role is added, exhaust every subset of the four possible active-to-fresh couplings. This yields 16 unique post-growth states.

Depth is:

`1 + number_of_active_to_fresh_couplings`

The first successful depth and all semantic disagreement counts are recorded.

## Warm developmental route

Instantiate the promoted V4 macro on the four active roles:

- add one fresh role;
- couple all four active roles to it.

This is charged as **one retained macro invocation**.

## Semantic gate

For every cold state and for the warm macro state:

- compute exact source isomorphism under one common permutation;
- compute exact target colour-preserving isomorphism under independent within-role permutations;
- compare all 1,296 ordered pairs.

A transferred representation qualifies only with zero disagreement.

## Compounding gate

A pass requires:

- V4 macro induction predicate holds;
- no cold state before the full four-coupling state qualifies;
- the full four-coupling cold state has zero disagreement;
- the promoted macro instantiates exactly that state;
- warm candidate evaluations = 1;
- cold candidate evaluations through first success = 16;
- warm semantic pair comparisons = 1,296;
- cold semantic pair comparisons through first success = 20,736;
- removing any one of the four promoted couplings restores semantic disagreement.

## Held-out downstream Hex check

Only after qualification, generate unseen n=4 obligations with unrestricted multi-arc relations:

- positive: a two-relation structure and a nontrivial relabelling;
- negative: a structure differing in one named relation.

Compile the promoted macro representation and kernel-check both obligations with pinned HexGraphIso.

External capability freeze:

- `leanprover/hex-graph-iso` tag `v0.6.0`
- commit `f247c0898414ca29c502691e3a8ad0b3ce0b4f6a`
- Lean `v4.34.0-rc2`

## Claim boundary

A pass earns:

> bounded developmental primitive promotion and cross-language reuse: a higher-order repair schema is induced from a prior verified trajectory, instantiated on a larger active-role set, exhaustively qualified in a new relational language, and reused with lower future search cost.

It does not establish invention ex nihilo, autonomous choice of subject matter, or a universal developmental metalanguage.
