# Factor Witness Reclosure V6

## Objective

V5 qualified the generic quotient law itself. The remaining operational gap is
that every target adapter still hand-builds the quotient witness.

V6 compiles the repeated pattern into one reusable semantic object:

```
CommonFactorWitness p q :=
  factor c
  c ≠ 0
  q.num = c * p.num
  q.den = c * p.den
```

From that object, one generic constructor must produce:

```
GaugeEq p q
observe p = observe q
```

No target is allowed to repeat the cancellation proof.

## Reclosure targets

Use two unrelated, frozen external consequences at different scalar types:

1. **QLF Born probability** — `ℚ`, Gaussian-integer amplitude normalization.
   `rchain-community/quantum-logical-framework@888a4303846000ace1c7ef4c62a8d3e99110d979`.
2. **Pythia Sharpe ratio** — `ℝ`, risk-adjusted return scale invariance.
   `athanor-ai/pythia@65404339b5c6fe8004d91fdd9c0c14ceb0bf7cd3`.

The target-specific proof should do only:

- establish the two factor equalities;
- package `CommonFactorWitness`;
- invoke the compiled observation consequence.

This is the smallest operational test of “never pay twice” after V5.
