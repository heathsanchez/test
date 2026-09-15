# A6 Materialized-Key Spine — Frozen Mathlib Protocol

This protocol is frozen after the candidate passed the frozen development and
disjoint held-out gates, but before any full Mathlib candidate performance is
observed.

## Authorized candidate

Exact script:

```text
scripts/patch_a6_materialized_key_spine.py
```

No hash function, table layout, entry layout, capacity, checker configuration,
or upstream pin may change before this test.

## Frozen external target

Lean Kernel Arena:

```text
4543f486677a6cb56c7656767712cd017f8058ea
```

Frozen `tests/mathlib.yaml`:

```text
url: https://github.com/leanprover-community/mathlib4
ref: v4.29.1
rev: 5e932f97dd25535344f80f9dd8da3aab83df0fe6
pre-build: lake exe cache get
module: Mathlib
outcome: accept
compare-perf: true
```

Mathlib was not used to discover the representation, select the entry layout,
or tune any threshold.

## Frozen checker arms

1. `a0` — reconstructed A6.
2. `raws` — exact S-only prehashed authoritative `HashTable<S>`.
3. `rawkey` — exact materialized-key authoritative
   `HashTable<(prev_pointer, elim_key, S)>`.

All arms use the same Arena-style PGO procedure and `init-prelude` training
export.

## Correctness

All three arms must accept the exact same full generated Mathlib NDJSON.

Any candidate rejection is a hard failure.

## Performance

Generate Mathlib once and reuse the exact export for every arm.

After one warmup per arm, run **7 randomized-order paired repetitions**.

Primary metric: child-process CPU seconds.

Secondary metric: wall seconds.

The materialized-key representation is verified on Mathlib only if:

```text
rawkey vs A0:
    median paired CPU delta < 0
    AND wins >= 5 / 7

rawkey vs S-only raw:
    median paired CPU delta < 0
    AND wins >= 5 / 7
```

No result may be rescued by wall time if the primary CPU gate fails.

## Claim if verified

A positive result supports:

```text
Exact global spine interning is faster when the already-earned exact identity
is stored directly with the interned consequence rather than reconstructed
from that consequence during future probes.
```

The claim is about this representation law, not about arbitrary hash tables or
all checker caches.
