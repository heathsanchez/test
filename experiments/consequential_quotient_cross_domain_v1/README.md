# Consequential Quotient Cross-Domain V1

## Question

Can the V4 normalization result be lifted into a generic, reusable
`ConsequentialQuotient` layer and then instantiated without changing that layer
in genuinely unrelated verified domains?

The generic contract is deliberately tiny:

```
source state X
  -- certified invisible relation ~
  -> Quotient X/~ 
  -- protected observer
  -> Y
```

A relation is admissible only when it is an equivalence relation and the
protected observer is proved constant on its classes.

## Frozen external domains

1. **VeriTile** — `Lizn-zn/VeriTile@95a01f598e2cd1cac4052e5e5ff9145c658e18db`.
   Replays the warranted V4 normalization-gauge quotient as an instance of the
   generic compiler.
2. **QLF / Born probability** —
   `rchain-community/quantum-logical-framework@888a4303846000ace1c7ef4c62a8d3e99110d979`.
   Gaussian-integer amplitudes are mapped to rational norm weights; a global
   nonzero Gaussian factor becomes a common nonzero rational weight scale.
   The generic quotient is cross-checked against the source theorem
   `QLF.StateSpace.bornProb_global_scale`.
3. **Pythia / information ratio** —
   `athanor-ai/pythia@65404339b5c6fe8004d91fdd9c0c14ceb0bf7cd3`.
   Positive rescaling of active return and tracking error is compiled as a
   quotient and cross-checked against
   `Pythia.Finance.informationRatio_scale_invariant`.

The exact same generic module is compiled under each repository's own Lean /
Mathlib environment.

## Promotion rule

Green in all three independent jobs plus the final seal warrants only:
the generic quotient interface is portable across these three domains and the
declared protected observations factor through their certified-invisible
relations.

It does not establish automatic discovery of the right relation. That remains
the next residual.
