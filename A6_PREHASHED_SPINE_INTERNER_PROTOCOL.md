# A6 Prehashed Spine Interner — Frozen Protocol

## Residual

Three experiments now agree:

1. Existing eager spine hash-consing is causally valuable.
2. A 4K exact front cache bypasses 90.59% of current successful `spine_hc`
   lookups and is strongly causal versus a same-front-lookup ablation:
   **−2.0205% CPU, 28/30 wins**.
3. That front is net negative versus A0 because the additional activation/index
   layer costs more than the bypass saves.
4. Exact last-16 recency captures only **44.0791%** of current map hits, below
   the frozen 45% promotion threshold.

The next target is therefore the authoritative lookup representation itself.

## Candidate

Replace:

```text
FxHashMap<(prev_pointer, elim_key), S>
```

with:

```text
hashbrown::HashTable<S>
```

The exact spine key remains:

```text
(prev pointer, elim_key)
```

A cheap 64-bit hash of that exact key is computed once per lookup.

The raw table:

1. probes by that precomputed hash;
2. checks full exact key equality against the stored `Spine::Snoc`;
3. returns the already-interned `S` on exact hit;
4. on miss constructs exactly the same spine, applies exactly the same canonical
   marking rule, and inserts it with the same exact-key hash.

No secondary cache is added.

No equivalence relation changes.

No duplicate exact key is permitted.

## Why this is scientifically distinct

The 4K front experiment showed that avoiding the current authoritative map probe
is valuable, but adding a second lookup layer is not.

This experiment asks whether the same benefit can be obtained by making the
authoritative interner itself cheaper.

## Control

A0 is the natural representation control: identical A6 semantics and exact
spine-interning law using the existing `FxHashMap`.

A lightweight prehash-cost control may compute and black-box the candidate's
64-bit prehash before executing the unchanged A0 `FxHashMap` lookup. This
separates any cost of the new hash computation from the table substitution.

## Frozen semantic gate

All arms must pass the complete external frozen corpus:

- 103 / 103 good accepted;
- 58 / 58 bad rejected.

## Frozen development workload

Same four cases used to discover the hotspot:

- perf/grind-ring-5
- init-prelude
- perf/app-lam
- perf/shift-cascade

All arms use Arena-style PGO.

30 paired randomized-order repetitions.

## Promotion rule

Proceed to disjoint held-out only if the prehashed authoritative table:

```text
median paired CPU delta vs A0 < 0
AND
wins >= 18 / 30
```

and also beats the prehash-cost control in median CPU.

## Mechanistic gate

On frozen grind-ring-5 Callgrind, the candidate must reduce the instruction
count attributable to `spine_snoc_hc` / its lookup path relative to A0.

This is diagnostic support, not a substitute for the paired CPU gate.

## Escalation

Only after development and disjoint held-out gates pass may the already-frozen
Mathlib benchmark be run.

No rigid/unfold/canonical table conversion may be stacked before the spine-only
authoritative-table experiment is resolved.
