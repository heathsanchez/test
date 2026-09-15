# Novel Consequence Quotient V3 — Frozen Result

## Verdict

```text
VERIFIED_PI_SHADOW_OPPORTUNITY_NO_CAUSAL_GAIN
```

Run: `34915799812`  
Job: `104213011910`  
Commit: `114fb8a52909b811bebf5f470668375f66523236`  
Artifact: `10376640737`  
Artifact digest: `sha256:c4e6b369c157fc3074e6b4c4297c4a92898f829c5471f0c7736eebcf4a57e99f`

## Shadow evidence that motivated V3

Run `34915583025` showed, on the frozen held-out workload:

- raw pointer-cache misses: **50,799**
- consequential shadow hits among those misses: **602**
- Pi shadow hits: **602**
- Proj shadow hits: **0**
- Let shadow hits: **0**

## External semantic verifier

All three arms preserved the complete frozen Arena oracle:

- A0: 103/103 good, 58/58 bad
- Q-Pi: 103/103 good, 58/58 bad
- Q-Pi-ablation: 103/103 good, 58/58 bad

## Held-out economics

Median CPU:

- A0: **0.296664 s**
- Q-Pi-ablation: **0.314892 s**
- Q-Pi: **0.319253 s**

Paired CPU:

- Q-Pi vs A0: **+7.0169%**, wins **0 / 15**
- Q-Pi vs same-lookup ablation: **+1.7622%**, wins **5 / 15**

Thus the secondary key machinery itself is expensive, and returning the cached
whole Pi value adds further cost beyond that machinery.

## Exact residual

A cached `Value::Pi` contains both:

1. the reusable domain value; and
2. a body `Closure` whose `env` is the raw environment from the earlier evaluation.

Every V3 consequential-cache hit occurs after the ordinary raw-environment key
misses. Therefore a whole-Pi cache hit necessarily imports a Pi whose body
closure is tied to a different raw operational environment.

The next minimal experiment caches only the Pi domain and reconstructs the Pi
with the current raw environment. It tests whether the mathematical consequence
can be reused without importing the previous operational state.

V3 is rejected and is not stacked into V4.
