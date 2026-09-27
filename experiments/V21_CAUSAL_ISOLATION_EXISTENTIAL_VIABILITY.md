# V21 — Causal Isolation of Existential Viability

Frozen residual from V20:

`EXISTENTIAL_OBJECT_NOT_CAUSALLY_ISOLATED_FROM_COVER_SUMMARY`

## Target

Test whether the policy-relevant abstraction

`Inhabited(V_same(rho)) := exists verified w : Option[Theta_same]`

is causally necessary for unseen-mechanism transfer once all non-typed policy observables are matched.

## Precommit

Each positive episode is paired with a negative episode having the same opaque witness-presence vector and the same coarse COVER/CAUSAL/PRESERVE/RETENTION summaries plus nuisance bits. The pair differs only in the hidden codomain of the present verified witness (`Theta_same` versus `Theta_other`). Thus type erasure makes the pair observationally identical to the policy learner.

For each opaque witness mechanism, every positive occurrence of that mechanism is removed from training while its matched negative twins remain. The typed learner must synthesize a minimum compositional policy and transfer to the unseen positive mechanism. An exact finite evaluator independently CompleteCover-checks the action from the hidden witness carrier.

## Gates

1. all non-typed pair observables exactly matched;
2. minimum full policy is `exists_verified[Theta_same]`;
3. typed leave-one-positive-mechanism-out transfer = 100%;
4. every held-out typed action independently verified;
5. policy invariant to alpha-renaming/reordering of mechanism identifiers;
6. type erasure breaks unseen-mechanism transfer;
7. causal/preservation hostile controls rejected.

Boundary: finite manually constructed witness carrier and supplied type system/policy grammar. V21 does not claim automatic discovery of the type system or adequacy map.
