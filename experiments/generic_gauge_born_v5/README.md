# Generic gauge quotient → Born probability V5

## Pre-registered objective

The V1–V3 VeriTile sequence has already qualified one real-valued reusable
consequence: normalized ratios ignore a shared nonzero factor.

V5 tests the two highest-value remaining separators at once:

1. **scalar generality** — is the law really about `ℝ`, or does the same
   quotient exist at the smaller algebraic boundary `CommGroupWithZero`?
2. **domain transfer** — does the same capability survive outside GPU
   softmax/attention?

## Frozen external target

Before implementation, fix:

- repo: `rchain-community/quantum-logical-framework`
- revision: `888a4303846000ace1c7ef4c62a8d3e99110d979`
- file: `lean/QLF_StateSpace.lean`
- target theorem family: `bornProb_global_scale`

The target defines a rational Born probability from Gaussian-integer
amplitudes and proves invariance under a common Gaussian-integer amplitude
factor. This is mathematically a projective-ray normalization statement over
`ℚ`, not an attention kernel.

This experiment treats only that formal algebraic statement as evidence. It
does not adopt the repository's surrounding physical interpretations.

## Candidate capability

Generalize the quotient representation to any commutative group with zero:

```
RatioState K := (num, den)
GaugeEq p q := ∃ c ≠ 0, q = c · p
observe p := num / den
```

Prove `GaugeEq` is an equivalence relation and `observe` factors through
its quotient. Then append an independent target theorem that derives the
Born global-scale invariance through that generic quotient without invoking
the target's existing `bornProb_global_scale`.

## Qualification

The identical appended theorem must fail when the generic quotient module is
absent and pass when it is imported. The external repo and target source are
pinned exactly.
