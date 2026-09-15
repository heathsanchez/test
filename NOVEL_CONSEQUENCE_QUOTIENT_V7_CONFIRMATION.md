# V7 Confirmatory Replication — Frozen Protocol

## Purpose

V7 produced the first candidate in the sequence with lower median CPU than both:

- A0: −1.2391%
- matched recompute ablation: −0.8447%

but its preregistered 15-pair win-count threshold was not met.

No V7 mechanism is changed for this confirmation.

## Frozen implementation

Candidate:
`scripts/patch_cq_pi_recurrence_seed.py`

Matched ablation:
`scripts/patch_cq_pi_recurrence_seed_ablation.py`

Pinned checker:
`9b4ea12f4cd437d00b6bcd0e34743065c58dea08`

Frozen Arena oracle:
`8931227426`

## Workloads

All workload selection is independent of V7 timing.

Remove the discovery case `grind-ring-5` from frozen good cases, then order by:

```text
descending file size, path tie-break
```

### Replication set A

First 24 cases.

This is exactly the workload used in V1–V7.

### Disjoint generalization set B

Next 24 cases, positions 25–48 in the same frozen ordering.

Set B is disjoint from discovery and set A.

## Semantic gate

A0, V7 candidate and V7 ablation must each:

- accept 103 / 103 frozen good cases;
- reject 58 / 58 frozen bad cases.

Any mismatch rejects the candidate immediately.

## Performance protocol

For each set independently:

- warm all three arms once;
- run **60 paired repetitions**;
- randomize arm order deterministically by repetition index;
- primary metric: CPU seconds;
- record wall time secondarily.

## Frozen confirmatory thresholds

For candidate versus ablation:

```text
median paired CPU delta < 0
AND
candidate wins >= 37 / 60
```

37 / 60 is the first one-sided sign threshold below 0.05 under p=0.5.

For candidate versus A0 the same threshold is used.

### Replicated gain

```text
VERIFIED_RECURRENCE_GATED_CONSEQUENCE_GAIN_REPLICATED
```

requires the semantic gate plus both causal and net thresholds on set A.

### Replicated and generalized gain

```text
VERIFIED_RECURRENCE_GATED_CONSEQUENCE_GAIN_GENERALIZED
```

requires the same thresholds on both A and disjoint set B.

### Otherwise

The directional V7 result is retained but not admitted.

## No post-hoc mechanism changes

The confirmation may not change:

- recurrence activation;
- cache size;
- environment equality;
- closedness requirement;
- consequence unit;
- candidate code;
- ablation code;
- workload membership;
- primary metric;
- thresholds.
