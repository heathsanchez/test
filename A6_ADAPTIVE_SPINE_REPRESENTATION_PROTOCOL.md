# A6 Adaptive Spine Representation — Frozen Scale Protocol

## Evidence entering this experiment

The exact prehashed authoritative spine interner is:

- semantically exact on 103 good / 58 bad;
- strongly positive on the frozen development aggregate;
- strongly positive on `grind-ring-5`;
- positive on `init-prelude`;
- neutral on `app-lam` and `shift-cascade`;
- negative on the disjoint 24-case held-out aggregate.

Therefore a universal representation replacement is rejected.

## Hypothesis

The prehashed raw table earns its lower probe cost only after the authoritative
spine interner becomes sufficiently large.

The candidate switching feature is frozen before the scale diagnostic:

```text
peak number of exact entries in baseline spine_hc within one checker process
```

No call count, hit rate, problem name, elapsed time, or semantic category may
replace this feature after scale output is seen.

## Development labels

Positive representation cases, fixed from prior paired CPU evidence:

- `perf/grind-ring-5.ndjson`
- `init-prelude.ndjson`

Control representation cases:

- `perf/app-lam.ndjson`
- `perf/shift-cascade.ndjson`

## Threshold rule

Let:

```text
P = peak spine_hc sizes of the two positive cases
C = peak spine_hc sizes of the two control cases
```

A hybrid experiment is permitted only if:

```text
min(P) > max(C)
```

If so, freeze:

```text
THRESHOLD = max(C) + 1
```

This is the smallest integer threshold that separates the prior positive and
control development cases.

If not, close the peak-size switching direction.

The 24 held-out cases may be measured by the diagnostic, but their scale values
may not alter `THRESHOLD`.

## Hybrid representation if permitted

Each fresh spine-interner session begins with the existing A0
`FxHashMap<(prev_pointer, elim_key), S>`.

When its exact entry count reaches `THRESHOLD`:

1. allocate the exact prehashed `HashTable<S>`;
2. migrate every existing exact entry;
3. verify migration by full exact spine key;
4. clear the old map;
5. use only the raw table for the rest of that session.

On `clear_session`, both representations clear and the next session starts in
A0 mode again.

No entry may be dropped and no equivalence relation changes.

## Frozen hybrid gates

- Arena-style PGO.
- Full 103-good / 58-bad external semantics.
- Same four-case development workload, 30 paired repetitions.
- Same disjoint 24-case held-out workload, 30 paired repetitions.

Proceed from development only if hybrid vs A0:

```text
median paired CPU < 0
wins >= 18 / 30
```

Proceed from held-out only if hybrid vs A0:

```text
median paired CPU < 0
wins >= 18 / 30
```

The already-frozen Mathlib benchmark is allowed only after both gates pass.
