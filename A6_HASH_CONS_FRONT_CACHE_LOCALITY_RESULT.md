# A6 Hash-Cons Front-Cache Locality — Result

Run: `34923791015`  
Job: `104237369008`  
Commit: `e28b2f3df509c82c460b6e0276581f1df609655e`  
Artifact: `10378824160`  
Artifact digest: `sha256:8f358d602df5d2a858b51ca940692610348762a09959ebb4627d27db541bcaaa`

The diagnostic was shadow-only. Production hash tables remained authoritative.
The frozen semantic replay was fully green.

## Aggregate four-case locality

### Canonical representative cache

- calls: **1,025,169**
- current map hits: **718,343**
- map hit rate: **70.07%**
- exact 1K front capture: **97.37% of current hits**
- exact 4K front capture: **99.21% of current hits**

### Spine hash-cons

- calls: **3,426,827**
- current map hits: **2,290,111**
- map hit rate: **66.83%**
- exact 1K front capture: **83.77% of current hits**
- exact 4K front capture: **90.59% of current hits**

### Rigid hash-cons

- calls: **1,874,792**
- current map hits: **1,021,950**
- map hit rate: **54.51%**
- exact 1K front capture: **81.98% of current hits**
- exact 4K front capture: **90.13% of current hits**

### Unfold hash-cons

- calls: **1,347,844**
- current map hits: **926,041**
- map hit rate: **68.71%**
- exact 1K front capture: **78.54% of current hits**
- exact 4K front capture: **88.82% of current hits**

## Frozen promotion decision

All four tables exceed the preregistered rule:

```text
4K exact capture >= 70%
AND
current map hits >= 10,000
```

The highest-volume qualifying table is `spine_hc`.

Therefore only `spine_hc` is promoted to the first production front-cache
experiment.

Predicted exact bypasses on the four-case development workload:

```text
2,074,689 / 2,290,111 current spine_hc hits
= 90.59%
```

No rigid, unfold, or canonical front cache may be stacked before the spine-only
causal experiment is resolved.
