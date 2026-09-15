# Novel Consequence Quotient V2 — Already-Earned Slot Equivalence

## Residual inherited from V1

V1 established two facts under frozen external Lean Kernel Arena verification:

1. the A6 projected-frame representation contains a real false split under the checker's own existing value canonicalization;
2. eagerly acquiring that equivalence inside `prune_env_cold` is economically wrong.

V1 result:

```text
RED false splits: 5,317
GREEN false splits: 0
full semantic oracle: green
quotient vs A0 CPU: +1.6898%
quotient vs same-cost ablation CPU: +0.8201%
VERIFIED_FALSE_SPLIT_NO_CAUSAL_GAIN
```

The remaining question is activation economics.

## New hypothesis

Do not acquire canonical equivalence on the projection path.

Instead, compile it only when normal checker execution has **already earned** a
canonical representative.

For a selected projected slot `v`:

```text
if v is already canonical:
    use v
else if canon_cache already contains v -> c:
    use c
else:
    use v
```

No call to `canonicalize_for_spine` is introduced in the projection path.

## RED — frozen before implementation

Run: `34914346859`  
Job: `104208588362`  
Commit: `f961a4ce562851321f205ae997e07da795300975`

The diagnostic changed no projected frame and invoked no new canonicalization.

On frozen `grind-ring-5`:

- cold projected-frame constructions: **369,583**
- selected slots observed: **861,391**
- already-earned slot substitutions available: **503,464**
- frames changed by already-earned representatives: **264,426**
- repeated already-earned canonical signatures: **211,132**
- distinct raw representations inside one already-earned signature: **2,983**

RED assertion failed exactly because those **2,983** false splits are present in A6.

## Minimal GREEN repair

Use an already-earned representative for a selected projected slot when and only
when that representative is already available from normal execution.

No new equivalence relation is introduced.
No canonicalization is invoked.
No unselected value is inspected.

## Arms

### A0

Frozen A6 unchanged.

### Q-earned

Use already-earned canonical slot representatives before projected-frame
hashing/interning.

### Q-earned-abl

Perform the same `is_canonical` checks and `canon_cache` lookups, but discard
the representative and retain/hash the original raw slot.

Therefore Q-earned versus Q-earned-abl isolates the causal value of compiling the
already-earned equivalence into frame identity.

### GREEN

Q-earned plus the same diagnostic used in RED.

The RED property must close:

```text
already-earned false splits = 0
```

## Information firewall

Discovery case `grind-ring-5` is excluded from held-out performance.

The held-out workload is the same deterministic rule used in V1:

```text
24 largest frozen good Arena cases by byte size,
path tie-break,
discovery case excluded.
```

No performance result is used to select cases or alter the activation rule.

## External verifier

Frozen Lean Kernel Arena artifact `8931227426`.

A0, Q-earned and Q-earned-abl must each:

- accept all 103 frozen good cases;
- reject all 58 frozen bad cases.

Performance is interpreted only after semantics are green.

## Frozen decision rule

Primary metric: paired CPU time over 15 randomized-order repetitions.

`VERIFIED_NOVEL_EARNED_QUOTIENT_GAIN` requires:

1. GREEN false splits = 0;
2. all three arms pass the complete frozen semantic oracle;
3. Q-earned beats Q-earned-abl in median paired CPU and wins at least 12/15;
4. Q-earned beats A0 in median paired CPU and wins at least 10/15.

If Q-earned beats the ablation but not A0:

```text
VERIFIED_EARNED_QUOTIENT_CAUSAL_BUT_NET_NEGATIVE
```

If semantics and GREEN pass but Q-earned does not beat the ablation:

```text
VERIFIED_EARNED_FALSE_SPLIT_NO_CAUSAL_GAIN
```

Any semantic mismatch is `SEMANTIC_REJECTION`.

## Claim boundary

A positive result would show a novel residual-derived optimization in the pinned
checker: equivalence was first witnessed under diagnostic-only execution, the
broad eager implementation was rejected by held-out economics, and the
developmental loop then localized the lawful activation rule to equivalence
already earned elsewhere by consequence.
