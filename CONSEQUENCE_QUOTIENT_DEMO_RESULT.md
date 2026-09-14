# Consequence Quotient Demo — Verified Result

## Verdict

```text
VERIFIED_CAUSAL_QUOTIENT_GAIN
```

The first frozen run completed successfully without post-result tuning.

## Immutable evidence

- Workflow run: `34886408343`
- Workflow job: `104118049554`
- Branch: `consequence-quotient-demo-v1`
- Commit: `a2f3876911bc0f0c53182afccfcaf2b6906ddb7a`
- Evidence artifact: `10365260826`
- Artifact digest: `sha256:47d86f80f7466ca09f3897f77c130df883bdfb586076a7a668a0c379aebafda2`
- Frozen Arena oracle artifact: `8931227426`
- sokonanoda source pin: `9b4ea12f4cd437d00b6bcd0e34743065c58dea08`

## Discovery before performance

Discovery ran with quotient reuse deliberately disabled.

On the frozen discovery case `arena-tests/good/perf/grind-ring-5.ndjson`:

- projected-frame requests: **534,097**
- new signatures: **176,432**
- repeated signatures: **357,665**
- repeated-signature fraction: **66.9663%**
- quotient/ablation performance observed before prediction: **false**

The frozen predicted equivalence was:

```text
same(mask, ordered slot identities, level-substitution identity)
    => share one canonical projected frame
```

The held-out workload explicitly excluded the discovery case.

## External semantic verifier

Both the compiled quotient and the causal ablation were evaluated against the complete frozen Lean Kernel Arena good/bad oracle:

| Arm | Good accepted | Bad rejected |
| --- | ---: | ---: |
| quotient | 103 / 103 | 58 / 58 |
| ablation | 103 / 103 | 58 / 58 |

No performance result was interpreted until this gate passed.

## Held-out causal result

Primary metric: paired CPU time.

The held-out workload was frozen deterministically as the 24 largest good Arena cases by byte size after excluding the discovery case. No quotient/ablation timings were used in workload selection.

Across 15 paired repetitions:

- quotient CPU wins: **15 / 15**
- median paired CPU delta, quotient vs ablation: **-6.0722%**
- median CPU: quotient **0.252314 s**, ablation **0.268123 s**
- median wall: quotient **0.183936 s**, ablation **0.190069 s**

The preregistered positive-result rule required:

1. the full semantic oracle to pass;
2. negative median paired CPU delta; and
3. at least 12 / 15 quotient CPU wins.

All three conditions passed.

## What this establishes

This run demonstrates the complete causal protocol:

```text
observe repeated consequential signatures
-> freeze a merge prediction
-> compile the quotient
-> verify semantics externally
-> test on held-out workloads
-> remove only the quotient reuse
-> observe the gain disappear
```

The experiment therefore supports the operational claim:

> A consequential equivalence can be identified before performance evaluation, compiled into shared state, and externally verified to preserve Lean checking behavior while reducing held-out evaluation cost.

## Claim boundary

This is a proof of the **developmental protocol**, not a claim that frame interning itself is a novel Lean optimization. The quotient mechanism already exists in the pinned checker lineage.

The next stronger experiment is to use this exact protocol on a **novel residual-derived equivalence** that is not already implemented upstream.
