# V7 Confirmatory Replication — Result

## Verdict

```text
DIRECTIONAL_V7_NOT_REPLICATED
```

Run: `34919339721`  
Job: `104223717405`  
Commit: `01c5a4daa11e9da93464763a6172abcce01962fb`  
Artifact: `10377855455`  
Artifact digest: `sha256:fa3b6b16a07df1a23005c456c5307068c8a8ec70b90976cae4f19b94841bbc56`

## External semantic verifier

All three arms again passed the complete frozen Arena oracle:

- A0: 103 / 103 good, 58 / 58 bad
- V7 candidate: 103 / 103 good, 58 / 58 bad
- V7 matched ablation: 103 / 103 good, 58 / 58 bad

## Confirmatory set A — original 24 held-out cases

60 paired repetitions.

- candidate vs A0 median CPU: **+0.4741%**
- candidate vs A0 wins: **27 / 60**
- candidate vs ablation median CPU: **+0.1008%**
- candidate vs ablation wins: **29 / 60**

The original directional gain did not replicate on set A.

## Disjoint set B — next 24 frozen cases

60 paired repetitions.

- candidate vs A0 median CPU: **−1.7269%**
- candidate vs A0 wins: **44 / 60**
- candidate vs ablation median CPU: **−0.4886%**
- candidate vs ablation wins: **36 / 60**

Net benefit versus A0 passed the frozen 37/60 sign threshold.

The causal candidate-vs-ablation comparison missed that threshold by one win
(36 / 60 versus required 37 / 60).

## Scientific update

The V7 mechanism is not a universal improvement over the frozen workload.

Performance differs materially between two independently frozen workload
regimes.

The next question is therefore not whether recurrence or equivalence exists.
It is:

```text
which portable consequences are valuable enough to reuse?
```

A diagnostic activation funnel and avoided-work experiment are retained to
identify the decision variable without tuning on timing outcomes.

V7 remains unadmitted.
