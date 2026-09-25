# Normalization gauge quotient V4

## Objective

V1–V3 independently converged on the same protected consequence:

a numerator/denominator pair may change by a shared nonzero scale without
changing the normalized observation.

Rather than collecting another attention example, V4 asks whether the common
capability is best represented as a **consequence-relative quotient**.

## Candidate representation

For a real pair `p = (N,D)` define

```
p ~ q  iff  ∃ c ≠ 0, q = c · p
observe(p) = N / D
```

The candidate law is:

```
p ~ q  =>  observe(p) = observe(q)
```

and therefore `observe` factors through the quotient by `~`.

The implementation must reuse the already-qualified V2/V3 capability
`MathGraphGaugeCapability.common_factor_ratio`; it must not independently
reprove scale cancellation.

## External factorization probes

Against frozen `Lizn-zn/VeriTile@95a01f598e2cd1cac4052e5e5ff9145c658e18db`,
the same quotient representation is instantiated on three independently
qualified target families:

1. `softmax_reducev` — natural-exp weighted quotient;
2. `mixed_sparse_attention` — WithBot/base-2 sparse FA2 fold;
3. `block_sparse_attn` — CSR-gathered causal streaming attention.

Each target keeps its own domain-specific equalities establishing the shared
factor. V4 tests only whether those equalities mechanically induce the same
`GaugeEq` class and therefore the same protected normalized observation.

## Promotion rule

Green hosted qualification warrants only:

- `GaugeEq` is an equivalence relation on real numerator/denominator pairs;
- normalized observation factors through its quotient;
- the three frozen target families instantiate that same quotient boundary.

It does not claim arbitrary-field generality, GPU performance, IEEE/PTX
correctness, or that target-local recurrence proofs are redundant.
