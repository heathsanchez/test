# Hex V13 Residual-Guided Scope-Predicate Growth — Frozen Protocol

## Question

V12 selected the correct repair-schema generality from a supplied four-member schema family.

V13 removes that schema family.

Instead, begin with the empirical scope restrictions actually exhibited by the V10 trajectory, represent them as independent applicability predicates, and allow only one generic developmental action:

`DROP_ONE_FAILED_SCOPE_PREDICATE`

A scope predicate may be removed only when a typed applicability residual proves that predicate blocks an otherwise admissible verified developmental transition.

## Exact prior evidence

The workflow downloads and verifies the sealed artifacts from:

- V10 run 34733374359, artifact 10310401999;
- V11 run 34733923706, artifact 10309829989;
- V12 run 34734314335, artifact 10310427933.

## Initial scope predicates

Induce the most literal finite scope description from V10's residual trace:

1. KEY_TYPE_IS_INT
   - every V10 residual key is an integer.

2. BATCH_SIZE_IN_OBSERVED_SET
   - V10 residual batch sizes are exactly from the set {1,2}.

These scope predicates sit on top of the retained constitutional invariants:

- preserve all existing bindings;
- forbid overwrite;
- add exactly the keys named by the typed residual;
- proposed values require verifier-clean semantic consequence.

The constitutional invariants are not candidates for deletion in this experiment.

## Growth by typed applicability residual

### Consequence 1 — exact V11 transfer

Replay V11's exact categorical-key residuals.

If the current schema cannot admit them, identify which scope predicate is falsified.

Test every one-predicate deletion.

A lawful repair must:

- remove a predicate actually falsified by the residual;
- make the blocked V11 transition admissible;
- preserve all previously admitted V10 transitions.

Exactly one minimum deletion must succeed.

### Consequence 2 — exact V12 batch-3 residual

Replay V12's first new transfer residual.

Again identify the falsified predicate and test every remaining one-predicate deletion.

Exactly one minimum deletion must succeed while preserving all earlier consequences.

## New transfer after scope growth

After both certified repairs, use a new key representation:

`(POSITION, TAG)`

where TAG is relation index mod 5.

Start with four named directed relations, so the first residual contains four fresh structured keys at once — outside V10's observed batch-size set and outside V10's integer key type.

Transfer worlds:

- m=4, carrier 2, one arc per relation: 16 objects / 256 ordered pairs;
- m=5, carrier 2, one arc per relation: 32 objects / 1,024 ordered pairs;
- m=6, carrier 2, one arc per relation: 64 objects / 4,096 ordered pairs.

At each stage, extend only residual-named fresh keys and select Boolean values by exact semantic consequence.

## Controls

- deleting the wrong scope predicate must not resolve each typed blockage;
- after each deletion, all prior admitted residuals must remain admissible;
- restoring KEY_TYPE_IS_INT must re-block V11/new structured keys;
- restoring BATCH_SIZE_IN_OBSERVED_SET must re-block the new batch-4 residual;
- attempted overwrite remains rejected;
- changing any retained value to 0 must restore semantic disagreement at its earning stage.

## Held-out continuation

Use the completed policy on held-out multi-arc six-relation objects over two vertices and kernel-check positive and negative obligations through pinned HexGraphIso.

## Pass

A pass requires two uniquely licensed one-predicate scope relaxations, exact preservation replay, successful structured-key/batch-4 transfer, all causal controls, and held-out Hex verification.

## Claim boundary

This removes the pre-enumerated schema family. The remaining designed meta-operation is the generic ability to delete one scope predicate that a typed residual has specifically falsified.
