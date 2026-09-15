# Novel Consequence Quotient V1 — Frozen Result

## Verdict

```text
VERIFIED_FALSE_SPLIT_NO_CAUSAL_GAIN
```

Run: `34914068167`  
Job: `104207733237`  
Commit: `3ea90c0ac9dd975eafd52021462e7cf7d2670df1`  
Artifact: `10375687689`  
Artifact digest: `sha256:edc9cccc28ab582045f49efa8f2b41725f7d268d236c3e872ee86d410ed1a6df`

## RED witness

Authoritative RED run: `34913712534`

On the frozen `grind-ring-5` discovery workload, diagnostic-only A6 showed:

- cold projected-frame constructions: **369,613**
- frames whose selected slot vector changed under existing value canonicalization: **289,211**
- repeated canonical signatures: **222,499**
- raw-frame false splits inside one canonical signature: **5,317**

No candidate quotient was enabled in the RED run.

## GREEN closure

The minimal candidate canonicalized only values selected into projected frames before hashing/interning.

The original property closed:

```text
RED false splits:   5,317
GREEN false splits: 0
```

## External semantic verifier

All frozen Arena outcomes were preserved:

| Arm | Good accepted | Bad rejected |
| --- | ---: | ---: |
| A0 | 103 / 103 | 58 / 58 |
| quotient | 103 / 103 | 58 / 58 |
| same-cost ablation | 103 / 103 | 58 / 58 |

## Held-out economics

Discovery case was excluded. Primary metric was paired CPU time over the frozen 24-case held-out workload.

Median CPU:

- A0: **0.171499 s**
- same-cost ablation: **0.175248 s**
- quotient: **0.176155 s**

Paired result:

- quotient vs A0: **+1.6898%**, quotient wins **2 / 15**
- quotient vs same-cost ablation: **+0.8201%**, quotient wins **6 / 15**

Therefore the broad quotient is rejected.

## Scientific update

The experiment separates two questions that were previously conflated:

1. **Is the present representation too fine?** Yes. The 5,317 RED witnesses establish a real false split relative to the checker's already-admitted value canonicalization.
2. **Should that equivalence be acquired eagerly on every projected-frame construction?** No. The acquisition/application cost exceeds the held-out reuse gain.

The next residual is therefore not equivalence discovery. It is **activation economics**:

```text
apply a known-safe quotient only when its representative has already been earned
or when a cheap structural predicate predicts positive reuse value.
```

This negative result is retained as evidence and must not be silently stacked into later candidates.
