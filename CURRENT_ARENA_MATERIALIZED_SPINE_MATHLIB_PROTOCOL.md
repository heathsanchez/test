# Current Arena Materialized-Key Spine — Frozen Mathlib Protocol

This protocol is frozen before any current-baseline Mathlib candidate timing.

## Arena snapshot

Lean Kernel Arena commit:

```text
4543f486677a6cb56c7656767712cd017f8058ea
```

Current official sokonanoda pin:

```text
28c03d0103e004610e4d47a4828965efb2b70af9
```

Frozen Mathlib definition:

```text
url: https://github.com/leanprover-community/mathlib4
ref: v4.29.1
rev: 5e932f97dd25535344f80f9dd8da3aab83df0fe6
module: Mathlib
outcome: accept
compare-perf: true
```

## Candidate

Untouched current official sokonanoda plus only the exact materialized-key spine
representation:

```text
FxHashMap<(prev_pointer, elim_key), S>
->
HashTable<(prev_pointer, elim_key, S)>
```

No A6 patch is applied.

## Arms

1. `current` — untouched official current pin.
2. `raws` — S-only prehashed exact table.
3. `rawkey` — materialized-key exact table.

All arms use the exact official Arena-style PGO procedure trained on
`init-prelude`.

## Preconditions

Run this Mathlib gate only if the current-pin frozen transfer experiment reports:

```text
CURRENT_MATERIALIZED_PROCEED_MATHLIB
```

No candidate code changes are permitted between that verdict and this test.

## Correctness

Generate one exact Mathlib NDJSON and reuse it for all arms.

All arms must accept it.

If the untouched current baseline rejects, the test is invalid and no candidate
conclusion may be drawn.

## Performance

One warmup per arm.

Then 7 randomized-order paired repetitions.

Primary metric: child-process CPU seconds.

Candidate is verified only if:

```text
rawkey vs current:
    median paired CPU delta < 0
    AND wins >= 5 / 7

rawkey vs raws:
    median paired CPU delta < 0
    AND wins >= 5 / 7
```

Wall time is secondary only.

## Process rule

No pull request may be created without Heath first writing or explicitly
approving the PR description.
