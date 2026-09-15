# A6 Hash-Cons Front Cache — Frozen Decision Rule

## Scientific residual

Current A6 Callgrind on frozen `perf/grind-ring-5`:

- `spine_snoc_hc`: 8.39% self instructions
- `mk_rigid_hc`: 5.76%
- `canonicalize_for_spine`: 3.99%
- `mk_unfold_hc`: 3.39%

The earlier earned-only intervention proved that these eager canonical/hash-cons
paths are causally valuable overall: removing or delaying them loses performance.

Therefore the current target is **lookup cost**, not semantics.

## Diagnostic

The front-cache locality diagnostic changes no production return value.

For each current exact hash-cons/canonical table:

- canonical representative cache
- spine hash-cons
- rigid hash-cons
- unfold hash-cons

it measures:

- current map hit rate;
- exact direct-mapped 1K locality;
- exact direct-mapped 4K locality.

The shadow arrays store full current keys. A diagnostic hit therefore means the
same key would have been answered exactly by that front entry. No hash-only
match is counted.

## Frozen promotion rule

A production front-cache candidate may be built only for a table satisfying:

```text
4K exact front hits / current map hits >= 0.70
AND
current map hits >= 10,000
```

on the aggregate frozen four-case development workload.

The 70% threshold is fixed before seeing locality output. It asks for a clearly
dominant bypass opportunity rather than tuning around small gains.

If multiple tables qualify, implement the highest-volume qualifying table first.
Do not stack tables before establishing its causal gain.

## Production safety rule

A production front entry must store:

```text
full exact key + authoritative cached result
```

A front result may be returned only on full exact key equality.

A front miss falls through unchanged to the current authoritative hash table.

Therefore collisions can only reduce front-cache hit rate; they cannot alter
semantic identity.

## Development performance rule

For the first promoted table:

1. A0, front-cache candidate, and same-front-lookup ablation.
2. Full 103-good / 58-bad external semantic oracle.
3. Arena-style PGO builds.
4. 30 paired repetitions on the frozen four-case development workload.
5. Candidate must beat the matched ablation with:
   - median paired CPU delta < 0;
   - at least 18 / 30 wins.
6. Candidate must also have median CPU below A0.

Only then escalate to the disjoint held-out workload and Mathlib.

No front-cache size or table selection may be changed after locality is observed
under this protocol.
