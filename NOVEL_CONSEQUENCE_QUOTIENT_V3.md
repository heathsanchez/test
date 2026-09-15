# Novel Consequence Quotient V3 — Separate Consequential Pi Cache

## Why V3 exists

V1 proved that projected A6 environments contain real false splits under the
checker's existing value canonicalization, but eagerly replacing raw frame slots
was net negative.

V2 proved that even using only already-earned representatives was net negative.
The same-lookup ablation was faster than the quotient, so the harm came from
changing the operational environment representation itself.

A follow-up prune diagnostic showed that quotienting raw frames increased
downstream work on the frozen held-out workload:

- total prune requests: **+17,488**
- Cons cold prunes: **+9,960**
- frame cold prunes: **+593**

A value-class diagnostic then showed the held-out false splits were entirely
structural:

- held-out false-split frames: **1,449**
- content-only false-split frames: **0**
- differing Rigid slots implicated: **2,026**

Therefore V3 separates semantic identity from operational state.

## Shadow separator — frozen before implementation

Run: `34915583025`  
Job: `104212363049`  
Commit: `d8e6a9604d212884f6d79313ca226cfe73a26bb8`

The shadow diagnostic left the real open-eval cache unchanged. On a real
pointer-key cache miss it computed the already-earned consequential environment
signature and asked whether that signature had been seen before. It never
returned a shadow-cached value.

### Discovery

```text
raw hits:    158,382
raw misses:  145,317
shadow hits:     687
```

All 687 shadow hits were `Pi` evaluations.

### Frozen held-out workload

```text
raw hits:     21,239
raw misses:   50,799
shadow hits:     602
```

Again, all **602 / 602** shadow hits were `Pi` evaluations:

- Pi: 602
- Proj: 0
- Let: 0
- all other observed open-eval forms: 0

Thus the smallest evidence-supported activation surface is `Pi` only.

## V3 repair

Keep all raw `Env` objects unchanged.

Keep the existing pointer-keyed `open_eval_cache` unchanged.

Only after that cache misses, and only when the expression is `Pi`, construct:

```text
(
  Pi expression identity,
  projected environment mask,
  level-substitution identity,
  already-earned canonical slot representatives
)
```

No call to `canonicalize_for_spine` is added.

No frame is merged or replaced.

No prune memo is shared.

The secondary consequential cache may answer the evaluation only when the full
exact key matches.

## Arms

### A0

Frozen A6 unchanged.

### Q-Pi

Pointer cache first. On a pointer miss for `Pi`, consult the consequential Pi
cache and return its value on a hit.

### Q-Pi-ablation

Construct the identical key, perform the identical secondary map lookup, and
populate the identical map after evaluation, but never return a secondary-cache
hit.

Therefore Q-Pi versus Q-Pi-ablation isolates the value of consequential cache
reuse while controlling key construction, hashing, lookup, allocation, storage,
and cache side effects.

## External semantic verifier

Frozen Lean Kernel Arena artifact `8931227426`.

Each arm must:

- accept all **103 / 103** frozen good cases;
- reject all **58 / 58** frozen bad cases.

Any mismatch is `SEMANTIC_REJECTION`.

## Held-out firewall

The discovery case `grind-ring-5` is excluded.

The held-out performance set remains the same deterministic rule used in V1/V2:

```text
24 largest frozen good Arena cases by byte size,
path tie-break,
discovery case excluded.
```

No performance outcome is used to choose the expression class, key, cases, or
decision rule.

## Frozen performance decision

Primary metric: paired CPU time over 15 randomized-order repetitions.

`VERIFIED_SEPARATE_CONSEQUENTIAL_PI_CACHE_GAIN` requires:

1. all three arms pass the complete external semantic oracle;
2. Q-Pi beats Q-Pi-ablation in median paired CPU and wins at least **12 / 15**;
3. Q-Pi beats A0 in median paired CPU and wins at least **10 / 15**.

If Q-Pi beats the ablation but not A0:

```text
VERIFIED_PI_CACHE_CAUSAL_BUT_NET_NEGATIVE
```

If semantics pass but Q-Pi does not beat the ablation:

```text
VERIFIED_PI_SHADOW_OPPORTUNITY_NO_CAUSAL_GAIN
```

## Claim boundary

A positive result would establish a new representation principle in this pinned
checker and frozen workload:

```text
semantic identity can profitably be coarser than operational state
when compiled as cache identity rather than state replacement.
```

It would not establish universal optimality or correctness outside the frozen
external verifier and held-out workload.
