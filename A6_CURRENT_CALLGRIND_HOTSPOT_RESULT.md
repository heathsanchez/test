# Current A6 Callgrind Hotspot — Result

Run: `34922243847`  
Job: `104232730438`  
Commit: `12736e0ea2e67be2cbcf9e05c2d865757a99a816`  
Artifact: `10378462967`  
Artifact digest: `sha256:8e8c4c4d67b5fd16bf619b719617814a8a33a88f794b71fc6cb8adf320fa6b4c`

The exact reconstructed A6 passed the frozen semantic replay before profiling.

Profile case: frozen `perf/grind-ring-5`.

Total Callgrind instructions:

```text
2,696,238,925
```

## Dominant self-costs

- `eval_no_cache`: **14.15%**
- `spine_snoc_hc`: **8.39%**
- `eval`: **7.95%**
- memset: **6.47%**
- `mk_rigid_hc`: **5.76%**
- `canonicalize_for_spine`: **3.99%**
- `apply`: **3.46%**
- `mk_unfold_hc`: **3.39%**
- `infer_value`: **3.22%**
- secondary `eval_no_cache` instance: **2.57%**
- `prune_env_cold`: **2.40%**
- secondary `eval`: **2.11%**
- `apply_many`: **2.01%**
- `spine_apps`: **1.99%**

Related hash-table insertion/rehash functions contribute several additional
percent.

## Key residual

The largest coherent avoidable cluster is the canonicalization/hash-consing path
inside general application:

```text
canonicalize_for_spine
-> spine_snoc_hc
-> mk_rigid_hc / mk_unfold_hc
-> hash-table maintenance
```

The direct named components alone account for more than 20% of instructions.

Callgrind also shows millions of calls into this path from `apply`, so this is
not a rare micro-optimization opportunity.

## Next intervention

Test whether canonical identity should be manufactured eagerly on every general
Rigid/Unfold application.

Frozen candidate:

```text
if identity already earned:
    preserve canonical/hash-consed path
else:
    construct raw spine/value
```

Matched raw ablation removes the canonical/hash-consed path entirely for those
general application branches.

This intervention is implemented by
`scripts/patch_a6_earned_only_apply.py` and governed by
`A6_EARNED_ONLY_APPLY.md`.
