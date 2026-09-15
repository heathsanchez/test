# A6 Spine Front Cache — Held-Out Mathlib Protocol

This protocol is frozen before the spine front-cache development result.

## Preconditions

Run Mathlib only if the frozen spine-front workflow reports:

```text
SPINE_FRONT_PROCEED_MATHLIB
```

No front-cache size, hash/index function, key equality, table selection, or
candidate code may be changed before this test.

## Frozen external target

Lean Kernel Arena repository:

```text
4543f486677a6cb56c7656767712cd017f8058ea
```

Arena `tests/mathlib.yaml` at that commit:

```text
url: https://github.com/leanprover-community/mathlib4
ref: v4.29.1
rev: 5e932f97dd25535344f80f9dd8da3aab83df0fe6
pre-build: lake exe cache get
module: Mathlib
outcome: accept
compare-perf: true
```

Mathlib was not used to select the spine table, front-cache size, index
function, or development decision thresholds.

## Frozen checker arms

1. A0 — exact reconstructed A6.
2. Front — exact 4K `spine_hc` front-cache candidate.
3. Ablation — identical front allocation/index/equality/update path, but front
   hits deliberately fall through to the authoritative hash map.

All arms use the same Arena-style PGO construction and configuration.

## Correctness

Every arm must accept the full generated Mathlib export.

Any rejection is a hard candidate failure.

## Performance

Primary metric is checker CPU time on the exact same generated Mathlib NDJSON.

Because Mathlib is a large single workload, use repeated executions of the
already-generated export; do not rebuild/export Mathlib between arms.

Run 7 randomized-order repetitions after one warmup per arm.

A held-out Mathlib gain requires:

```text
median paired CPU(front vs ablation) < 0
AND
front wins >= 5 / 7

median paired CPU(front vs A0) < 0
AND
front wins >= 5 / 7
```

Wall time and peak RSS are secondary diagnostics.

## Claim boundary

A positive Mathlib result plus the frozen corpus/development/held-out gates
supports a real Arena-facing optimization:

```text
most successful spine hash-cons lookups exhibit exact short-range locality;
an exact front index can preserve canonical reuse while bypassing the dominant
general hash-table lookup cost.
```

It does not authorize stacking rigid, unfold, or canonical front caches without
separate causal evidence.
