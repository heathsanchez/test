# Hex Digraph Residual-Guided Substrate Growth V3 — Frozen Protocol

## Question

When the currently available adapter substrate is exhaustively inadequate, can the residual identify a structural failure mode, authorize a bounded substrate expansion, and select a minimal repair whose removal restores the failure?

V2 showed that an anonymous three-role adapter can be selected from a supplied static grammar. V3 makes the developmental order explicit: begin with a substrate that cannot express the successful representation, certify inadequacy, inspect the residual, and only then expose a frozen set of lawful substrate-growth constructors.

## Prior external authority

Downstream exaptation authority is inherited only as a frozen reference from V2:

- V2 verdict: `VERIFIED_BOUNDED_ADAPTER_GENESIS`
- V2 workflow run: `34727765985`
- V2 head: `8e897d6571bf53a35980d8ff635a68652bf81173`
- V2 evidence artifact: `10309130239`
- V2 artifact SHA-256: `a384b953d8cf3236255cd104679a3079430ab8d8ce2bbd60a6e2fcc996f24891`

V3 does not re-run Hex. It tests the developmental transition that produced the adapter already kernel-checked downstream in V2.

## Source semantics and qualification world

Exactly as in V2:

- loopless directed graphs;
- all 64 graphs on 3 vertices;
- all 4,096 ordered pairs;
- exact source isomorphism under all vertex permutations;
- exact target colour-preserving isomorphism under independent permutations inside each target role.

## Initial substrate

The initial substrate permits at most two anonymous role copies per source vertex.

For each role count, it permits:

- every ordered role pair as the arc channel;
- every subset of identity couplings between distinct roles.

This means the initial substrate contains:

- the one-role direction-erasing family;
- every two-role tail/head split;
- the only possible two-role identity coupling.

No three-role representation exists initially.

## Inadequacy gate

Before any substrate growth, exhaust the complete initial substrate.

Growth is authorized only if:

1. no initial candidate has zero semantic disagreement;
2. the best two-role residual remains nonzero;
3. a concrete false-positive target isomorphism witness exists.

For the canonical two-role diagnostic candidate `arc 0->1 + identity coupling 0--1`, record the role-wise target permutations witnessing the first false positive.

Residual classification is predeclared:

- if the target witness uses different permutations in role 0 and role 1, classify `ROLE_PERMUTATION_DESYNCHRONIZATION`;
- otherwise classify `UNRESOLVED_TWO_ROLE_FAILURE`.

## Frozen growth constructors

Only after the inadequacy gate, evaluate these predeclared one-step substrate repairs:

1. `ADD_INERT_ROLE`
   - add role 2;
   - no identity coupling to it.

2. `ADD_PARTIAL_IDENTITY_CHANNEL_0`
   - add role 2;
   - couple role 0 to role 2 only.

3. `ADD_PARTIAL_IDENTITY_CHANNEL_1`
   - add role 2;
   - couple role 1 to role 2 only.

4. `ADD_FULL_IDENTITY_CHANNEL`
   - add role 2;
   - couple both role 0 and role 1 to role 2.

The directed arc channel remains `0 -> 1` in every repair. Thus the new role can only serve as additional representational substrate; it cannot directly carry source arcs.

## Selection and causality

Evaluate each repair over the complete 4,096-pair qualification world.

A pass requires:

- initial substrate exhaustively inadequate;
- diagnostic residual classified as role-permutation desynchronization;
- inert-role repair fails;
- both partial identity-channel repairs fail;
- full identity-channel repair reaches zero disagreement;
- removing either full repair coupling restores disagreement;
- the successful repair is exactly the adapter independently selected and Hex-checked in V2.

## Interpretation

The intended structural reading is:

> direction splitting creates independent role permutations; a two-role identity edge is semantically confounded with the arc channel because both inhabit the same colour-pair relation; a third role creates a distinct identity channel that forces the role permutations back into one source-vertex permutation.

## Claim boundary

A pass earns **bounded residual-guided substrate growth under a supplied constructor set**.

It does not establish autonomous invention of the growth constructors, open-ended grammar invention, or a universal theory of representation growth.
