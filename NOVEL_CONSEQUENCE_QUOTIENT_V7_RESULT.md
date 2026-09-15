# Novel Consequence Quotient V7 — Frozen Result

## Verdict

```text
VERIFIED_RECURRENCE_REUSE_NO_CAUSAL_GAIN
```

This is the preregistered categorical verdict because the candidate did not
reach the required 12 / 15 paired wins versus the recompute ablation.

Authoritative run: `34919098292`  
Job: `104222990675`  
Commit: `841de8813b29bae0e73e4451e4343541e12e85bb`  
Artifact: `10377601396`  
Artifact digest: `sha256:771234d69bb93bf58b046bfc963f2236865e5031f2a5ad528dc681448a10bc90`

## External semantic verifier

All arms preserved the complete frozen Arena oracle:

- A0: 103 / 103 good accepted, 58 / 58 bad rejected
- recurrence candidate: 103 / 103 good accepted, 58 / 58 bad rejected
- matched recompute ablation: 103 / 103 good accepted, 58 / 58 bad rejected

## Held-out economics

Median CPU on the same frozen 24-case held-out workload:

- A0: **0.249628 s**
- recurrence ablation: **0.248557 s**
- recurrence candidate: **0.246496 s**

Paired CPU:

- candidate vs A0: **−1.2391%**, wins **11 / 15**
- candidate vs recompute ablation: **−0.8447%**, wins **9 / 15**

## Interpretation

V7 is the first residual-derived candidate in this sequence whose median CPU is
lower than both A0 and its matched causal control.

It nevertheless fails the frozen admission threshold against the ablation
because paired wins are only 9 / 15.

Therefore the correct next move is **replication**, not another representation
change.

The mechanism is frozen unchanged for confirmation:

```text
recurrence
-> exact consequential comparison
-> require closed portable consequence
-> reuse consequence
-> rebind continuation to current operational state
```

A confirmatory experiment will:

1. repeat the original frozen held-out comparison with substantially more paired
   repetitions;
2. test an independently frozen disjoint held-out workload;
3. make no change to the V7 candidate, ablation, equality relation, cache size,
   closedness rule, or activation rule.

V7 is not yet admitted.
