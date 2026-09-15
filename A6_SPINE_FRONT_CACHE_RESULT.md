# A6 Spine Front Cache — Development Result

## Verdict

```text
SPINE_FRONT_STOP_DEVELOPMENT
```

Run: `34924111339`  
Job: `104238357461`  
Commit: `74342e897e14b969ce8733901648780c8a50db4b`  
Artifact: `10379685595`  
Artifact digest: `sha256:05ac569958a8ec1f58731eda0d2b9aade0aeba92ac99bbcf736c021ef02c8663`

## Frozen semantic oracle

All three arms were exact:

- A0: 103 / 103 good accepted, 58 / 58 bad rejected
- 4K spine front cache: 103 / 103 good accepted, 58 / 58 bad rejected
- matched front-lookup ablation: 103 / 103 good accepted, 58 / 58 bad rejected

## Development economics

Arena-style PGO builds and 30 paired repetitions over the frozen four-case
development workload.

Median CPU:

- A0: **0.708665 s**
- front-cache ablation: **0.734119 s**
- front cache: **0.719695 s**

Front versus matched ablation:

- median paired CPU delta: **−2.0205%**
- wins: **28 / 30**

Front versus A0:

- median paired CPU delta: **+1.3579%**
- wins: **3 / 30**

The development gate therefore failed and the disjoint held-out workload was
correctly not run.

## Interpretation

The exact front-cache reuse mechanism is **causally valuable** once its
activation machinery is already paid for.

The failure is activation/index cost:

```text
A0
< front
< same front machinery with reuse disabled
```

So the current general hash-table lookup is expensive enough that bypassing it
recovers about 2% versus the matched control, but a 4K direct-mapped front check
on every `spine_snoc_hc` call costs more than it saves overall.

This sharply localizes the next residual:

```text
preserve exact spine reuse
while making the front eligibility/lookup substantially cheaper.
```

The next diagnostic measures exact temporal recurrence at last-1/2/4/8/16
spine calls. If a very small recency cache captures a large fraction of current
map hits, it can eliminate both the general hash lookup and the 4K index/table
overhead.

The 4K production candidate is rejected and not admitted.
