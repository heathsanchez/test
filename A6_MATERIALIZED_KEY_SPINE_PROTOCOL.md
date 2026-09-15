# A6 Materialized-Key Raw Spine Interner — Frozen Protocol

## Residual entering this experiment

The exact S-only prehashed authoritative raw spine table is:

- strongly faster on heavy development workloads;
- semantically exact;
- slower on the disjoint small held-out workload.

The threshold-65 adaptive representation improved held-out transfer from
`+1.1567%` to `-0.7836%`, but missed the frozen 18/30 win gate at 17/30.

The threshold is not changed.

## Representation hypothesis

The current S-only raw table stores:

```text
S
```

and recovers the stored exact identity during every probe by dereferencing the
stored spine:

```text
S -> Spine::Snoc -> (prev pointer, elim key)
```

But that exact key was already known when the spine was interned.

The candidate therefore stores:

```text
(prev pointer, elim key, S)
```

directly in the authoritative raw table.

## Exactness

Query key remains exactly:

```text
(prev pointer, elim key)
```

Query hash remains the same frozen prehash used by the S-only raw table.

A hit is returned only if both stored key fields are exactly equal.

On miss:

1. construct the same spine;
2. apply the same canonical marking rule;
3. insert the exact key and authoritative S pointer.

No cache layer is added.
No equivalence relation changes.
No threshold or workload classifier is used.

## Frozen arms

1. A0 — original A6 `FxHashMap<(usize,u64),S>`.
2. S-only raw — prior exact prehashed `HashTable<S>`.
3. materialized-key raw — `HashTable<(usize,u64,S)>`.

All arms use identical Arena-style PGO.

## Frozen semantics

All three arms must pass:

- 103 / 103 good;
- 58 / 58 bad.

## Frozen development gate

Same four-case development workload.
30 paired randomized-order repetitions.

Materialized-key raw proceeds only if versus A0:

```text
median paired CPU delta < 0
wins >= 18 / 30
```

S-only raw is a mechanistic control, not an admission baseline.

## Frozen held-out gate

Same disjoint 24-case workload, unchanged.
30 paired randomized-order repetitions.

Materialized-key raw proceeds to Mathlib only if versus A0:

```text
median paired CPU delta < 0
wins >= 18 / 30
```

## Interpretation

If materializing the exact key preserves the heavy-workload gain and removes
the held-out penalty, the result supports a general representation principle:

```text
do not repeatedly reconstruct a consequential identity from the object
it names when that identity was already earned at construction time.
```

If it still fails held-out, the small-regime cost is elsewhere in the raw-table
probe/allocation representation and the candidate is rejected.
