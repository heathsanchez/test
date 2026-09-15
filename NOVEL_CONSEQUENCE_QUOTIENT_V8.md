# V8 — Recurrence-Gated Closed Type Consequence Reuse

## Discovery basis

The type-inference consequence-value atlas was shadow-only and preserved the
existing type cache.

Across 199,747 real type-cache misses it found:

- 253 dependency-complete repeated signatures;
- 1,359 recursive inference calls spent recomputing those repeats;
- mean 5.37 recursive inference calls per repeat;
- maximum 22;
- 253 / 253 repeated results closed.

Root expression classes:

- App: 191
- Pi: 62

Opportunity concentration:

- grind-ring-5: 142 repeats / 876 recursive inference calls;
- init-prelude: 110 repeats / 481 calls;
- all other 101 good cases: 1 repeat / 2 calls.

The conversion atlas was also run and rejected as economically negligible.

## V8 mechanism

Existing raw `type_cache` remains first and authoritative.

After a raw-cache miss, a 1024-entry expression-indexed seed table is consulted.
The size is inherited from the checker's existing 1024-entry direct-map scale.

A seed stores:

```text
expression
projected raw environment
local context
infer/check mode
universe-check scope
inferred result
```

A cached type result can be reused only if:

1. expression is identical;
2. infer/check mode is identical;
3. universe-check scope is identical;
4. projected environments are exactly equal under already-earned canonical
   representatives;
5. every context type addressable by the expression's loose variables is
   exactly equal under the same already-earned representatives;
6. the previously inferred result is closed.

No eager canonicalization is performed.

No environment or context is merged.

No open inferred value is reused.

On a valid hit, the ordinary raw `type_cache` is populated with the closed
result for the current raw key.

## Matched ablation

The ablation performs the same:

- seed indexing;
- expression/mode/scope tests;
- exact environment comparison;
- exact relevant-context comparison;
- closedness test;
- seed storage and replacement;
- black-box consumption of a valid cached result;

but deliberately recomputes inference instead of returning the cached result.

Candidate versus ablation therefore isolates reuse of the closed inference
consequence.

## Frozen semantic gate

Pinned checker:
`9b4ea12f4cd437d00b6bcd0e34743065c58dea08`

Frozen Arena artifact:
`8931227426`

A0, V8 candidate and V8 ablation must each:

- accept 103 / 103 good cases;
- reject 58 / 58 bad cases.

Any mismatch rejects V8.

## Development economics gate

Before paying for full Mathlib, benchmark only the two workloads where the
shadow atlas discovered material recurrence:

- `perf/grind-ring-5`
- `init-prelude`

These cases are **not held out**; this is only a development/economics gate.

For each case:

- 30 paired randomized-order repetitions;
- primary metric: CPU seconds.

Proceed to held-out Mathlib only if candidate has:

```text
median CPU delta vs ablation < 0
AND
wins >= 18 / 30
```

on both cases.

This gate authorizes only further testing, not a scientific performance claim.

## Held-out target if development gate passes

The full Arena Mathlib test:

- mathlib4 ref `v4.29.1`
- rev `5e932f97dd25535344f80f9dd8da3aab83df0fe6`
- module `Mathlib`

Mathlib was not included in the downloadable frozen 103-good/58-bad corpus and
was not used to discover or tune V8.

## Claim boundary

The developmental hypothesis is:

```text
recurrence
-> exact dependency-complete consequential identity
-> closed portable type consequence
-> reuse only when the avoided recursive inference work earns the mechanism
```
