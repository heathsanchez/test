# Novel Consequence Quotient V2 — Frozen Result

## Verdict

```text
VERIFIED_EARNED_FALSE_SPLIT_NO_CAUSAL_GAIN
```

Run: `34914599429`  
Job: `104209367784`  
Commit: `518524eddb7932042240cb7a3cd2ffc13108d507`  
Artifact: `10375258420`  
Artifact digest: `sha256:f47488a4435fc94c36ddbe03e09f8d68fc7fcd86e7296a0ab309ae8991ac7afe`

## RED witness

Authoritative RED run: `34914346859`

Without invoking any new canonicalization:

- cold projected-frame constructions: **369,583**
- selected slots: **861,391**
- already-earned slot substitutions available: **503,464**
- frames affected by those representatives: **264,426**
- repeated already-earned signatures: **211,132**
- raw-frame false splits available from already-earned representatives: **2,983**

## GREEN closure

```text
RED false splits:   2,983
GREEN false splits: 0
```

## External semantic verifier

All arms preserved the complete frozen oracle:

- A0: 103/103 good, 58/58 bad
- quotient: 103/103 good, 58/58 bad
- same-lookup ablation: 103/103 good, 58/58 bad

## Held-out economics

Median CPU:

- A0: **0.225314 s**
- same-lookup ablation: **0.224459 s**
- quotient: **0.233560 s**

Paired CPU:

- quotient vs A0: **+2.5124%**, quotient wins **0 / 15**
- quotient vs same-lookup ablation: **+3.5286%**, quotient wins **1 / 15**

The lookup/acquisition explanation is therefore rejected: the same lookup path
without compiling the representative is faster. The cost is caused by changing
the shared frame representation itself.

## New residual

Projected frames contain both:

1. **semantic identity** — mask, slots, level substitution; and
2. **mutable operational history** — the single-entry per-frame `prune` memo.

Merging semantically equivalent frames therefore also merges mutable memo state.
The next separator tests whether the negative quotient effect is mediated by
increased prune-memo interference/cold recomputation.

No V1 or V2 candidate is admitted.
