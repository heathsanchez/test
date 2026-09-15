# A6 Prune Residual — Recovered Evidence Synthesis

The A6 prune path already has a complete experimental sequence. This note
recovers the actual completed run evidence to prevent duplicate search.

## E0031 — prune access diagnostic

Run `31894982350`.

On `grind-ring-5`:

- cold prune calls: **369,293**
- raw (environment,mask) repeats: **5,256** (**1.42%**)
- frame hits: **219,367** (**59.40%**)
- frame misses: **149,926**
- selected slots: **860,720**
- slot work that ended in a frame hit: **47.04%**
- mean selected slots / hit: **1.85**
- mean selected slots / miss: **3.04**

This showed substantial projection work before frame rediscovery, but almost no
raw-pair recurrence.

## E0032 — scan diagnostic

Run `31895136323`.

- cold calls: **372,450**
- cons cells scanned: **889,027**
- selected: **480,371**
- skipped: **408,656**
- framed calls: **190,202**
- selected slots: **867,197**
- max cons scan: **64**

## E0033 — parent tail memo diagnostic

Run `31895457005`.

- cons steps: **890,755**
- nonzero tails: **707,979**
- parent memo matches: **137,548**
- parent memo results: **137,548**
- parent framed: **176,342**
- parent cons: **531,637**

The apparent reuse opportunity was real and large enough to justify a causal
intervention.

## E0034 — parent-tail splice

Run `31910955956`.

All arms preserved 103 / 103 good and 58 / 58 bad.

Compared with A6:

- parent-tail splice median CPU delta: **+1.7109%**
- matched disabled ablation: **+0.2324%**

The seemingly obvious tail reuse was net negative.

## E0035 — frame-intern ablation

Run `31911212530`.

Semantic oracle remained green.

Removing frame interning changed median CPU by:

```text
+9.3764%
```

Therefore frame interning is strongly causally valuable and must remain.

## E0036 — bit-directed prune

Run `31911411104`.

Semantic oracle remained green.

Replacing sequential prune scan with bit-directed lookup changed median CPU by:

```text
+0.8328%
```

So direct selected-bit lookup was also net negative.

## Current conclusion

The prune residual has already been explored in the obvious directions:

- raw recurrence is too low;
- parent-tail recurrence exists but exploiting it costs more than it saves;
- frame interning is essential;
- bit-directed lookup is slower.

Do not reopen these variants without a new separator.

The next move is instruction-level profiling of current A6.
