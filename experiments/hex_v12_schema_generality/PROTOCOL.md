# Hex V12 Repair-Schema Generality Selection — Frozen Protocol

## Question

V11 inferred a generic repair schema using a supplied anti-unification procedure.

V12 removes that anti-unifier. Instead, it generates a finite family of repair schemas from a small generic schema-description grammar and asks whether prior fit plus independently frozen future consequence selects the correct level of generality.

## Prior authorities

Use:

- V10: VERIFIED_SPARSE_META_OPERATOR_GENESIS_AND_TRANSFER
- V11: VERIFIED_REPAIR_SCHEMA_ANTI_UNIFICATION_AND_TRANSFER

The workflow downloads and verifies the exact sealed V11 artifact so the transfer trace is not reconstructed from prose.

## Schema-description grammar

Generate the cross product of two independent dimensions.

Key scope:

- PRIOR_INTEGER_KEY: schema accepts only integer keys like V10;
- ANY_KEY: schema accepts any finite key representation.

Batch scope:

- OBSERVED_BATCH_SIZE: schema accepts only batch sizes observed in V10, namely 1 or 2;
- ANY_NONEMPTY_BATCH: schema accepts any nonempty finite residual batch.

All four generated schemas preserve existing bindings, forbid overwrite, require added keys to equal the typed residual, and require verifier-clean value selection.

No preferred schema is named.

## Qualification by consequence

Stage A — V10 fit:
all four schema candidates must explain the V10 developmental trajectory.

Stage B — frozen V11 transfer:
the exact V11 transfer uses categorical string keys. This must eliminate the PRIOR_INTEGER_KEY candidates while leaving both ANY_KEY candidates.

Stage C — new residual:
a new selector representation uses tuple-like categorical keys of the form POSITION|TAG.

The first target world has three named relations and exposes three fresh keys simultaneously. Therefore residual batch size is 3.

This must eliminate ANY_KEY + OBSERVED_BATCH_SIZE and leave only ANY_KEY + ANY_NONEMPTY_BATCH.

## New transfer representation

For relation index i among m named relations define:

POSITION:
- LEFT for i = 0;
- RIGHT for i = m-1;
- INTERIOR otherwise.

TAG:
- i mod 3.

The repair-map key is POSITION|TAG.

Transfer worlds:

1. m=3, carrier size 2, exactly one arc per relation:
   8 objects, 64 ordered pairs.
   First residual batch size: 3.

2. m=4, carrier size 2, exactly one arc per relation:
   16 objects, 256 ordered pairs.

3. m=5, carrier size 2, exactly one arc per relation:
   32 objects, 1,024 ordered pairs.

At each stage, the selected schema may extend only the currently missing residual keys. Boolean candidate values are selected by exact semantic consequence.

## Controls

- every losing schema must have a concrete applicability failure stage;
- attempted overwrite of an existing key must be rejected;
- changing any retained key from 1 to 0 must cause semantic disagreement on the stage where that key was earned;
- final policy must agree extensionally with the V11 all-relation selector on relation counts 3 through 8.

## Held-out continuation

Instantiate the selected schema-derived policy on eight named directed relations over a two-vertex carrier.

Generate one positive and one negative held-out source pair, compile through pinned HexGraphIso, and kernel-check both.

## Pass

A pass requires:

- all four grammar-generated schemas fit V10;
- V11 consequence removes exactly the integer-key schemas;
- the new batch-3 residual removes the observed-batch-size schema;
- one schema remains: ANY_KEY + ANY_NONEMPTY_BATCH;
- that schema matches V11's independently inferred generality;
- target transfer constructs a verifier-clean policy with all controls;
- held-out eight-relation Hex verification passes.

## Claim boundary

This replaces the supplied anti-unification algorithm with consequence-driven selection inside a supplied schema-description grammar. The schema grammar itself remains designed.
