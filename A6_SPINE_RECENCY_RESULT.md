# A6 Spine Recency Locality — Result

## Verdict

```text
NO_RECENCY_K_QUALIFIES
```

Run: `34924526033`  
Job: `104239635207`  
Commit: `8717dc9effdb2c28ecd423c3ff50cfc9c7100c36`  
Artifact: `10379676319`  
Artifact digest: `sha256:3b57700cab0ac8945202712bb09ddbfa40d7a081244468ebdfbe5ccc2f838eda`

The diagnostic was read-only and the full frozen semantic replay was green.

## Aggregate exact temporal recurrence

Current `spine_hc` map hits: **2,290,628**

Capture of those hits by exact recent-key windows:

- last 1: **1.5924%**
- last 2: **5.9203%**
- last 4: **15.1020%**
- last 8: **29.5667%**
- last 16: **44.0791%**

Frozen promotion threshold:

```text
>= 45% of current map hits
```

The largest allowed recency window misses that threshold.

Therefore:

```text
selected_smallest_k = null
```

and no production recency-cache experiment may be triggered.

## Workload detail

### grind-ring-5
last-16 capture: **42.7006%**

### init-prelude
last-16 capture: **73.6862%**

### app-lam
last-16 capture: **94.9821%**

### shift-cascade
last-16 capture: **98.5915%**

The aggregate is dominated by `grind-ring-5`, where short temporal recurrence
is insufficient.

## Scientific update

Two cheaper secondary-index approaches have now been separated:

1. 4K exact hashed front:
   - 90.59% hit capture;
   - strong causal bypass value vs matched control;
   - net negative because activation/index overhead is too high.
2. tiny exact recency:
   - very cheap activation;
   - insufficient aggregate hit capture under the frozen threshold.

The next residual is therefore the authoritative `spine_hc` representation
itself.

The search should preserve exact global spine interning while lowering the cost
of its primary lookup/probe path, rather than stacking another secondary cache.

The parameterized recency production workflow remains intentionally untriggered.
