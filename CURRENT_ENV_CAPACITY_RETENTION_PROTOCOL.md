# Current Arena Environment Capacity Retention — Frozen Diagnostic Protocol

## Residual

Current official sokonanoda pin:

```text
28c03d0103e004610e4d47a4828965efb2b70af9
```

Frozen `grind-ring-5` Callgrind shows these exact environment-table rehash
paths as major self-instruction costs:

1. `wide_prune: (usize, ExprPtr) -> Env`: **3.303%**
2. `env_hc: (usize, usize) -> Env`: **3.139%**
3. `frames: HashTable<Env>`: **1.401%**

Together: **7.843%**.

The same profile also shows `memset` at **9.123%**.

Current `clear_session` behavior discards capacity above:

```text
KEEP_CAP = 1 << 15 = 32768
```

For ordinary maps, `shrink_map` replaces an oversized table with a fresh
default table. For `frames`, oversized capacity is similarly replaced with a
new empty `HashTable`.

## Hypothesis

A heavy workload may repeatedly learn that these environment tables need large
capacity, then discard that learned capacity at a session reset, forcing future
sessions to pay the same growth/rehash cost again.

## Diagnostic

No production result changes.

Measure for each of:

- `wide_prune`
- `env_hc`
- `frames`

across one checker process:

- insertion calls;
- capacity growth events;
- maximum observed capacity;
- session-clear count;
- session boundaries where capacity exceeded `KEEP_CAP` and would be
  discarded by current policy;
- maximum capacity discarded.

Run on the same frozen four development cases.

## Frozen promotion rule

Use prior Callgrind cost ordering:

```text
wide_prune > env_hc > frames
```

A table qualifies for a first retention experiment only if, on
`perf/grind-ring-5`:

```text
discard_count >= 2
```

Select the **highest Callgrind-cost qualifying table only**.

If no table qualifies, close session-capacity retention as the explanation for
the current rehash hotspot.

## Candidate if qualified

For the selected table only:

- keep the existing exact entries/lookup representation;
- at session clear, remove all entries but retain allocated capacity;
- make no other cache or evaluation change.

A0 remains current official behavior.

Primary performance metric: paired CPU.
Secondary safety metric: peak RSS.

The candidate is not admissible if it produces an unacceptable memory increase,
even if CPU improves.

## Process rule

No pull request may be created without Heath first writing or explicitly
approving the PR description.
