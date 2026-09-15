# Current Arena env_hc Representation — Frozen Protocol

## Evidence entering this experiment

Current official sokonanoda pin:

```text
28c03d0103e004610e4d47a4828965efb2b70af9
```

Current `grind-ring-5` Callgrind:

- `env_extend`: **5.231%** self instructions
- exact rehash path for `RawTable<((usize, usize), Env)>`: **3.139%**

Visible combined structural cost: about **8.37%**.

The capacity-retention atlas rejected repeated session-reset regrowth as the
main cause. On `grind-ring-5`, `env_hc` grows to 917,504 capacity but is
discarded only once across nine session clears.

## Exact relation

Current authoritative map:

```text
(parent Env pointer, Value pointer) -> Env
```

The key is already fully earned at environment construction time.

## Frozen arms

1. `current`
   - untouched current `FxHashMap<(usize, usize), E>`.

2. `raws`
   - `HashTable<E>`;
   - query hash computed once from the exact pointer pair;
   - full equality reconstructs the pair from stored `Env::Cons`.

3. `rawkey`
   - `HashTable<(usize, usize, E)>`;
   - the exact pair is stored inline with the authoritative environment;
   - query returns only on full exact pair equality.

All arms preserve one exact environment per exact key.

## Hash

Both raw arms use the same frozen exact-key hash helper:

```text
crate::hash64!(parent_pointer, value_pointer)
```

No hash tuning is permitted after performance is observed.

## Session policy

All arms preserve the current session-clearing rule:

- if capacity exceeds `KEEP_CAP = 32768`, replace with a fresh empty table;
- otherwise clear entries while retaining capacity.

This experiment changes table representation only.

## Semantic gate

All three arms must pass the complete frozen oracle:

- 103 / 103 good accepted;
- 58 / 58 bad rejected.

## Development workload

Frozen four cases:

- `perf/grind-ring-5`
- `init-prelude`
- `perf/app-lam`
- `perf/shift-cascade`

Arena-style PGO.

30 randomized paired repetitions.

Proceed only if `rawkey` vs `current`:

```text
median paired CPU delta < 0
AND
wins >= 18 / 30
```

The S-only raw arm is mechanistic evidence. A useful materialization effect is:

```text
median CPU(rawkey vs raws) < 0
```

## Disjoint held-out

Use the same frozen 24-case held-out workload.

Proceed to Mathlib only if `rawkey` vs `current`:

```text
median paired CPU delta < 0
AND
wins >= 18 / 30
```

## Memory guard

On `perf/grind-ring-5`, record peak RSS for each arm with `/usr/bin/time -v`.

A candidate whose peak RSS exceeds current by more than **20%** is rejected even
if CPU improves.

## Claim boundary

A positive result would support only:

```text
For the current exact environment-extension interner, materializing the
already-earned pointer-pair identity in a prehashed authoritative table lowers
lookup/growth cost without changing checker semantics.
```

No pull request may be created without Heath first writing or explicitly
approving the PR description.
