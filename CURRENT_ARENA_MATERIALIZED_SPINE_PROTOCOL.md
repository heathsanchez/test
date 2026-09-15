# Current Arena Materialized-Key Spine — Frozen Transfer Protocol

## Why this experiment exists

The materialized-key spine representation passed:

- 103 / 103 frozen good cases;
- 58 / 58 frozen bad cases;
- development: -10.1005% vs A0, 30 / 30 wins;
- disjoint held-out: -1.0432% vs A0, 20 / 30 wins.

The subsequent full-Mathlib experiment was invalid because its A0/A6 baseline
itself panicked on Mathlib before either candidate arm ran.

Therefore this transfer experiment moves only the representation law onto the
**current official Lean Kernel Arena sokonanoda pin**, which is already the
Arena baseline intended for current full-suite evaluation.

## Frozen official baseline

Repository:

```text
intgrah/sokonanoda
```

Official Arena pin observed before candidate execution:

```text
28c03d0103e004610e4d47a4828965efb2b70af9
```

At that pin, the authoritative spine interner remains:

```text
FxHashMap<(prev_pointer, elim_key), S>
```

and `spine_snoc_hc` uses the same exact key law as the earlier candidate.

## Candidate

Replace only that authoritative spine interner with:

```text
HashTable<(prev_pointer, elim_key, S)>
```

The exact identity is stored directly alongside the authoritative spine pointer.

The query key and exact equality remain:

```text
(prev pointer, elim key)
```

A hit returns only after full exact equality.

No A6 patch is applied.
No threshold is used.
No workload classifier is used.
No secondary cache is added.
No other current-upstream optimization is changed.

## Frozen arms

1. `current` — untouched official sokonanoda pin.
2. `raws` — S-only prehashed authoritative table, direct current-pin port.
3. `rawkey` — materialized-key authoritative table, direct current-pin port.

The S-only arm is mechanistic evidence; the admission baseline is `current`.

## Semantic gate

All three arms must:

- accept 103 / 103 frozen good cases;
- reject 58 / 58 frozen bad cases.

## Development gate

Same frozen four-case workload:

- perf/grind-ring-5
- init-prelude
- perf/app-lam
- perf/shift-cascade

Arena-style PGO, 30 randomized paired repetitions.

Proceed only if `rawkey` vs `current`:

```text
median paired CPU delta < 0
AND
wins >= 18 / 30
```

## Disjoint held-out gate

Use the same previously frozen 24-case held-out workload.

Proceed to current full Mathlib only if `rawkey` vs `current`:

```text
median paired CPU delta < 0
AND
wins >= 18 / 30
```

## Full Mathlib

If both gates pass, generate Mathlib using the then-frozen current Arena test
definition and compare the exact current baseline against the unchanged
materialized-key candidate.

No PR may be created without Heath first writing or approving the PR description.
