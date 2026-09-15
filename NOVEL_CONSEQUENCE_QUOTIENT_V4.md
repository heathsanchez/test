# Novel Consequence Quotient V4 — Reuse Pi Domain, Rebind Operational Closure

## Residual from V3

V3 separated consequential cache identity from raw environment identity, but
cached and returned the entire `Value::Pi`.

The frozen result was negative:

```text
Q-Pi vs A0 CPU:       +7.0169%, wins 0/15
Q-Pi vs ablation CPU: +1.7622%, wins 5/15
```

All 103 good and 58 bad frozen Arena cases remained correct, so this was an
economic/representation failure rather than a semantic failure.

## Why whole-Pi reuse is still too coarse

A `Value::Pi` contains:

```text
domain value
+
body Closure { env, body }
```

The V3 secondary cache is consulted only after the ordinary raw-environment
cache misses. Therefore every cross-identity whole-Pi hit can import a body
closure whose `env` belongs to the earlier raw operational state.

The reusable mathematical consequence and the operational continuation were
still bundled together.

## V4 hypothesis

Reuse only the Pi **domain** consequence.

On a raw pointer-cache miss for a Pi expression:

1. build the already-earned consequential environment key;
2. if the key has a cached domain, reuse that domain;
3. construct a fresh `Value::Pi`;
4. bind its body closure to the **current** raw projected environment.

No prior raw environment is imported through the cache.

No frame is merged.

No prune memo is shared.

No whole Pi value is shared.

No eager canonicalization is performed.

## Arms

### A0

Frozen A6 unchanged.

### Q-domain

Uses the consequential Pi key to cache/reuse only the evaluated Pi domain and
always reconstructs the Pi against the current operational environment.

### Q-domain-ablation

Builds the identical key, performs the identical map lookup, stores the same
domain values, and reconstructs Pi values identically, but deliberately ignores
secondary-cache hits and recomputes the domain.

Thus candidate vs ablation isolates **reuse of the domain consequence**.

## External verifier

Frozen Lean Kernel Arena artifact `8931227426`.

Every arm must:

- accept 103 / 103 good cases;
- reject 58 / 58 bad cases.

Any mismatch is `SEMANTIC_REJECTION`.

## Held-out firewall

Discovery case `grind-ring-5` remains excluded.

Performance workload remains frozen:

```text
24 largest frozen good cases by byte size,
path tie-break,
grind-ring-5 excluded.
```

## Frozen decision rule

Primary metric: paired CPU seconds over 15 randomized-order repetitions.

`VERIFIED_REBOUND_PI_DOMAIN_CACHE_GAIN` requires:

1. all arms pass the complete external semantic oracle;
2. Q-domain beats Q-domain-ablation in median paired CPU and wins at least 12/15;
3. Q-domain beats A0 in median paired CPU and wins at least 10/15.

If candidate beats the ablation but not A0:

```text
VERIFIED_PI_DOMAIN_REUSE_CAUSAL_BUT_NET_NEGATIVE
```

If it does not beat the ablation:

```text
VERIFIED_PI_DOMAIN_SHARING_NO_CAUSAL_GAIN
```

## Claim boundary

A positive result would support the more precise representation principle:

```text
reuse verified consequence,
rebind operational continuation.
```

It would not justify sharing arbitrary values, environments, closures, or
execution history.
