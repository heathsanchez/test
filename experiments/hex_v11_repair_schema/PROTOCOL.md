# Hex V11 Repair-Schema Anti-Unification and Transfer

## Question

Can the generic fresh-binding repair operation used in V10 be inferred mechanically from V10's sealed developmental trajectory, rather than supplied directly, and then transferred to a new selector-key representation?

## Prior authority

The workflow must download the exact sealed V10 artifact:

- run 34733374359
- artifact 10310401999
- ZIP SHA-256 96059633cf1a53b94e5d631d1a4822413e2cab7b361cef50e8d3a05ed98c8f87

Required V10 verdict:

VERIFIED_SPARSE_META_OPERATOR_GENESIS_AND_TRANSFER

## Schema induction

Read the V10 stage trace from final_evidence.json.

For every developmental transition, compute:

- bindings preserved from the previous state;
- newly added bindings;
- deleted bindings;
- changed existing bindings;
- the typed undefined-pattern residual that preceded the transition.

Infer a repair schema only if all observed transitions satisfy the same structural law:

1. all old bindings are preserved;
2. no old binding is deleted or overwritten;
3. every added key was named by the immediately preceding undefined-pattern residual;
4. no key outside that residual is added;
5. the retained added values are exactly those selected by verifier-clean candidate search.

The inferred schema is serialized from the trace. No fresh-binding repair schema is hard-coded into the transfer experiment.

## New key representation

Transfer to a categorical positional selector with keys:

- SINGLE
- LEFT
- RIGHT
- INTERIOR

This is intentionally not the V10 integer truth-table key representation.

The semantic meaning is still which named directed relations receive the identity-channel coupling.

## Transfer stages

Stage 0: one named relation.
Only SINGLE occurs.
Use all 64 loopless directed graphs on 3 vertices and all 4,096 ordered pairs.

Stage 1: two named relations.
New keys LEFT and RIGHT occur.
Use the complete 36-object, 1,296-pair one-arc-per-relation world.

Stage 2: three named relations.
New key INTERIOR occurs.
Use the complete 8-object, 64-pair two-vertex world.

At each stage the inferred schema may extend the partial map only at residual-named fresh keys. Candidate Boolean values are selected by exact semantic consequence. Prior bindings must remain immutable.

## Controls

- disabling the inferred schema must leave the first unknown key unresolved;
- changing any retained value to 0 must cause nonzero disagreement on the stage that earned that key;
- any attempted overwrite of a prior binding is rejected by the inferred preservation invariant;
- the final categorical policy must select every relation and agree extensionally with V10/V9/V8.

## Held-out continuation

Instantiate the learned categorical policy on seven named directed relations over a two-vertex carrier.

Generate a positive and a negative held-out source pair, compile through pinned HexGraphIso, and kernel-check both.

## Pass

A pass requires successful schema induction from the sealed V10 trace, successful cross-representation transfer to categorical keys, all preservation and ablation controls, exact final semantics, and successful held-out Hex verification.

## Claim boundary

This establishes bounded repair-schema induction by structural anti-unification over a prior verified developmental trajectory. The anti-unification procedure itself remains supplied.
