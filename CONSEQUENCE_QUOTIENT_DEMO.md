# Consequence Quotient Demo

## Claim

This experiment tests one narrow causal claim:

> Repeated requests for the same projected evaluation-frame signature identify a candidate consequential equivalence. Compiling that equivalence into shared state should preserve Lean checking semantics and reduce protected evaluation cost. Removing only the sharing mechanism should remove the gain.

This is an end-to-end demonstration of:

```text
observe repeated consequence
-> predict an equivalence
-> compile the quotient
-> verify externally
-> hold out performance cases
-> ablate the quotient
```

It is **not** presented as a claim that frame interning itself is a novel Lean optimization.

## Frozen scientific base

- Repository branch base: `arc3-developmental-tonight`
- Base commit: `579c287780a48962ebe5b8b32ea910ea5d01eb20`
- sokonanoda source pin: `9b4ea12f4cd437d00b6bcd0e34743065c58dea08`
- Frozen Lean Kernel Arena corpus artifact: `8931227426`
- Existing A6 reconstruction: `scripts/patch_a6.py`

## Arms

### Discovery

A6 with quotient reuse disabled.

The arm retains one representative of each projected-frame signature only as a diagnostic index. When the same signature is requested again, it records the repeat but returns a fresh equal frame.

Therefore discovery can observe candidate equivalence without receiving the performance benefit of the quotient.

The signature is:

```text
(mask, ordered slot identities, level-substitution identity)
```

### Quotient

Unmodified A6 frame interning.

Repeated equal projected-frame signatures share the existing canonical frame.

### Ablation

A6 with the frame-intern reuse mechanism removed by `scripts/patch_a6_e0035_no_frame_intern.py`.

It preserves frame contents and projection semantics while allocating a fresh frame for every request.

## Information firewall

The discovery case is `grind-ring-5`.

The held-out performance workload is selected deterministically from frozen Arena good cases **after excluding the discovery case**.

The prediction is frozen before any quotient-vs-ablation timing is read:

```text
Repeated exact projected-frame signatures should be safe to merge.
If the merge is computationally useful beyond the discovery example,
the quotient arm should beat the ablation arm on held-out CPU while
both preserve the external semantic oracle.
```

## External verifier

Correctness is decided by the frozen external Lean Kernel Arena good/bad corpus, not by the developmental logic.

For both quotient and ablation:

- every frozen good case must be accepted;
- every frozen bad case must be rejected.

Performance is interpreted only after this semantic gate is green.

## Primary result

Primary resource metric: paired CPU time on the deterministic held-out workload.

Secondary: wall time.

A positive causal result requires:

1. nonzero repeated signatures in discovery;
2. complete semantic agreement with the frozen Arena oracle for quotient and ablation;
3. lower median held-out CPU for quotient than ablation;
4. quotient wins a majority of paired repetitions;
5. removing only reuse removes the gain.

## Interpretation

### VERIFIED_CAUSAL_QUOTIENT_GAIN

The system observed repeated consequential signatures before performance evaluation, predicted a merge, the external verifier accepted the compiled quotient, held-out cost fell, and ablation removed the gain.

### VERIFIED_EQUIVALENCE_NO_HELDOUT_GAIN

The quotient is semantically valid on the frozen corpus but does not improve the held-out resource metric. This is a valid negative result: equivalence alone did not justify compilation for this workload.

### SEMANTIC_REJECTION

The proposed quotient changes protected Lean outcomes and is rejected immediately.

## Scope

This demo establishes the experimental pattern required for stronger claims. The next step after a positive run is to apply the same protocol to a **novel residual-derived equivalence** rather than an already-existing interning mechanism.
