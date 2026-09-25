# Consequential Quotient Recovery V2

## ROS correction

The relation-discovery residual was already substantially solved in the durable
programme state.

Pinned prior authority:

- `heathsanchez/Minimal-Sufficient-Interface@5d448c0ecc82ff3945d009963064ebbb67d2f308`
  proves that all-reachable-futures behavioural equivalence is the greatest
  observation-compatible invariant relation, and proves finite separator-driven
  recovery of the exact quotient.
- `metalogiclabs/mathgraph@e80fed62b6e58d2f4b62e2ceb012646c60dd1e28`
  proves `FutureEq` is the greatest future-sufficient relation and that one
  witnessed separator forces a split. Its real kernel census compresses 141 tests
  to a minimum two-test basis preserving the exact behavioural quotient.

So V2 does **not** invent another quotient-discovery algorithm.

## New question

Were the hand-written scale relations used in the cross-domain V1 merely safe
subrelations, or are they actually the maximal/coarsest protected-observation
quotients on the domains where the observations are semantically admissible?

We restrict only by the load-bearing nondegeneracy premises already present in
the source semantics:

- VeriTile ratio state: denominator nonzero;
- QLF normalized weight state: total weight nonzero;
- Pythia information-ratio state: tracking error positive.

Then we prove in each external domain:

```
hand_written_scale_relation  <->  equality_of_protected_observation
```

and therefore, by the already-known MSI universal property, the relation is the
greatest safe relation / coarsest safe representation on that admissible domain.

This closes the prior `minimum_quotient_optimality = UNKNOWN` boundary for
these three specific instances. It does not claim automatic symbolic synthesis
for arbitrary infinite domains. For finite continuation families, that recovery
mechanism is already the MSI finite-recovery theorem.
