# Novel Consequence Quotient V7 — Recurrence-Gated Closed Pi Consequence Reuse

## Residual from V6

V6 was the first candidate to show the correct causal direction:

```text
Q-closed vs recompute ablation: -0.4332% median CPU
wins: 9 / 15
Q-closed vs A0: +0.9106%
```

All 103 / 103 good cases and 58 / 58 bad cases passed.

The remaining problem is activation cost.

A recurrence diagnostic on the same frozen held-out workload found:

```text
Pi pointer-cache misses: 50,428
first encounter of Pi expression: 30,268
repeat encounter: 20,160
```

So about 60% of Pi pointer misses cannot possibly produce cross-environment reuse:
there is no previous occurrence of that Pi expression to reuse from.

## V7 hypothesis

Do not compute consequential environment identity on a first Pi-expression encounter.

Maintain a bounded 1024-entry expression-indexed seed table.

For a Pi pointer-cache miss:

### First / nonmatching seed

Evaluate normally and remember:

```text
(expression, raw projected environment, evaluated domain)
```

No consequential environment comparison is performed.

### Repeated same expression

Only now compare the current raw projected environment with the remembered one
using exact consequential equality under already-earned canonical representatives.

Reuse the remembered domain only if:

1. expressions are identical;
2. projected environments are exactly consequence-equivalent under the frozen relation;
3. the remembered domain is closed.

The Pi body closure is always rebuilt against the current raw environment.

## Why this is the smallest current mechanism

V7 does not:

- merge environments;
- merge frames;
- share prune memo state;
- reuse a prior Pi closure;
- canonicalize eagerly;
- allocate a general consequential key;
- test environment equivalence before recurrence makes reuse possible.

The only new question paid for is:

```text
same Pi appeared again — is its previously earned closed domain portable here?
```

## Arms

### A0

Frozen A6.

### Q-recurrence

1024-entry Pi-expression seed table. Exact consequential comparison only on
same-expression recurrence. Reuse only an exact, closed domain.

### Q-recurrence-ablation

Performs the same seed lookup, exact environment comparison, closedness test,
black-box barriers and seed replacement, but deliberately recomputes the domain
even when reuse is valid.

Candidate versus ablation isolates only the value of recurrence-gated closed
consequence reuse.

## External verifier

Frozen Lean Kernel Arena artifact `8931227426`.

All arms must:

- accept 103 / 103 good cases;
- reject 58 / 58 bad cases.

Any mismatch is `SEMANTIC_REJECTION`.

## Held-out firewall

The discovery case `grind-ring-5` remains excluded.

The held-out workload is unchanged:

```text
24 largest frozen good Arena cases by byte size,
path tie-break,
discovery case excluded.
```

No V7 timing is used to choose the recurrence trigger, cache size, equality
relation, closedness condition, or workload.

## Frozen decision rule

Primary metric: paired CPU seconds over 15 randomized-order repetitions.

`VERIFIED_RECURRENCE_GATED_CONSEQUENCE_GAIN` requires:

1. full semantic oracle green;
2. candidate beats ablation in median paired CPU and wins at least 12 / 15;
3. candidate beats A0 in median paired CPU and wins at least 10 / 15.

If candidate beats ablation but not A0:

```text
VERIFIED_RECURRENCE_REUSE_CAUSAL_BUT_NET_NEGATIVE
```

Otherwise:

```text
VERIFIED_RECURRENCE_REUSE_NO_CAUSAL_GAIN
```

## Research claim boundary

A positive result would support the developmental rule:

```text
do not pay to ask whether two histories share a portable consequence
until recurrence creates a possible reuse action.
```
