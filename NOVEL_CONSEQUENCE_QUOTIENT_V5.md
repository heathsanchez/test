# Novel Consequence Quotient V5 — Exact Direct-Mapped Pi-Domain Identity

## Residual from V4

V4 established that caching only the Pi domain while rebinding the current body
closure removes the clear stale-operational-state penalty, but its general
`Vec<usize>` consequential key remains too expensive.

Frozen V4 result:

```text
Q-domain vs A0:       +4.1753%, wins 1/15
Q-domain vs ablation: +0.0963%, wins 7/15
```

All semantic gates remained green.

Thus the remaining obstruction is key economics rather than the consequence
being reused.

## V5 representation

V5 preserves exactly the same semantic relation as V4 but compiles it into a
bounded direct-mapped cache.

The cache has **1024 entries**, matching the existing A6 prune direct-map scale.
This size is inherited from the present system rather than tuned from V5
performance.

For a Pi raw-pointer-cache miss:

1. compute a non-allocating hash over:
   - the projected environment mask;
   - level-substitution identity;
   - already-earned canonical representative pointers for selected slots;
2. combine it with the Pi expression identity to select one direct-map slot;
3. if an entry is present, require exact equality:
   - same Pi expression;
   - same level substitution;
   - same projected mask;
   - same slot count;
   - representative-by-representative pointer equality;
4. only then may the cached **domain** be reused;
5. rebuild the Pi body closure against the current raw environment.

No `Vec` key is allocated.

No frame is merged.

No previous body closure is reused.

No eager canonicalization occurs.

## Collision safety

The semantic hash only selects a candidate direct-map entry.

A hash match alone never authorizes reuse.

Full exact equality under already-earned representatives is checked before a
domain can be returned. Therefore a hash collision can only cause replacement
or a missed reuse opportunity; it cannot produce a wrong cache hit.

## Arms

### A0
Frozen A6.

### Q-DM
Direct-mapped exact consequential Pi-domain reuse.

### Q-DM-ablation
Runs the same hash, same slot selection, same exact equality test, same cache
storage, and the same `black_box` consumption of a cached-domain hit, but
deliberately recomputes the domain rather than using it.

Thus Q-DM versus Q-DM-ablation isolates only the causal value of domain reuse.

## External verifier

Frozen Lean Kernel Arena artifact `8931227426`.

Every arm must:

- accept 103 / 103 good cases;
- reject 58 / 58 bad cases.

## Held-out firewall

`grind-ring-5` remains excluded.

The performance workload is unchanged:

```text
24 largest frozen good cases by byte size,
path tie-break,
discovery case excluded.
```

## Frozen decision rule

Primary metric: paired CPU seconds over 15 randomized-order repetitions.

`VERIFIED_DIRECT_MAPPED_CONSEQUENTIAL_PI_GAIN` requires:

1. all semantic gates green;
2. Q-DM beats Q-DM-ablation in median paired CPU and wins at least 12/15;
3. Q-DM beats A0 in median paired CPU and wins at least 10/15.

If Q-DM beats the ablation but not A0:

```text
VERIFIED_DM_PI_REUSE_CAUSAL_BUT_NET_NEGATIVE
```

If Q-DM does not beat the ablation:

```text
VERIFIED_DM_PI_REUSE_NO_CAUSAL_GAIN
```

## Claim boundary

A positive result would support:

```text
keep operational state raw;
compile consequential identity into a cheap exact reuse index;
reuse only the consequence component;
rebind the continuation to the present.
```
