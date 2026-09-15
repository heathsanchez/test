# Novel Consequence Quotient V6 — Closed Consequence Reuse

## Residual from V5

V5 made consequential identity cheap and exact, but reusing every matched Pi
domain remained harmful:

```text
Q-DM vs A0:       +1.8086%, wins 1/15
Q-DM vs ablation: +2.4910%, wins 2/15
```

All semantic gates remained green.

A diagnostic of exact direct-map hits then classified the cached domain values.

Run: `34916666736`

Frozen held-out totals:

```text
exact direct-map hits: 370
closed domains:        130  (35.1%)
canonical domains:     102  (27.6%)

domain kinds:
Rigid   181
Pi       99
Sort     53
Unfold   37
```

Thus most reusable-looking domains are still open structural values.

## V6 hypothesis

Only a **closed** cached domain is operationally self-contained enough to reuse
across raw environment identity.

The V5 exact direct-map key and exact equality test remain unchanged.

On an exact hit:

- if cached domain is closed: reuse it;
- if cached domain is open: recompute it.

The resulting Pi is always rebuilt with the current raw environment in its body
closure.

## Arms

### A0
Frozen A6.

### Q-closed
Exact direct-map consequential identity; reuse only closed cached domains.

### Q-closed-ablation
Performs the identical exact direct-map lookup, identical `is_closed` test,
identical `black_box` barriers, and identical storage, but recomputes even
closed hits.

Candidate versus ablation therefore isolates closed-domain reuse.

## External verifier

Frozen Lean Kernel Arena artifact `8931227426`.

Each arm must accept all 103 good cases and reject all 58 bad cases.

## Held-out firewall

The same 24 frozen good cases are used, selected by size/path with
`grind-ring-5` excluded.

## Frozen decision rule

Primary metric: paired CPU seconds over 15 randomized-order repetitions.

`VERIFIED_CLOSED_CONSEQUENCE_REUSE_GAIN` requires:

1. all semantic gates green;
2. Q-closed beats ablation in median paired CPU and wins at least 12/15;
3. Q-closed beats A0 in median paired CPU and wins at least 10/15.

If candidate beats ablation but not A0:

```text
VERIFIED_CLOSED_REUSE_CAUSAL_BUT_NET_NEGATIVE
```

Otherwise:

```text
VERIFIED_CLOSED_REUSE_NO_CAUSAL_GAIN
```

## Claim boundary

A positive result would support the developmental rule:

```text
cross-state reuse requires a consequence to be both
semantically matched and operationally closed.
```
