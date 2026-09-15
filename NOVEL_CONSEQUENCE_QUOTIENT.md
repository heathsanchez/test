# Novel Consequence Quotient — Canonical Projected Slots

## Objective

Test whether the developmental protocol can discover and compile a **novel equivalence not already implemented by the pinned checker**.

The target is the projected environment-frame representation used by A6.

Current A6 interns frames using:

```text
(mask, level-substitution identity, raw slot Value pointers)
```

The checker already contains a semantics-preserving value canonicalizer,
`canonicalize_for_spine`, but projected environment slots are not passed
through it before frame hashing/interning.

The predicted false split is therefore:

```text
different raw slot pointers
but
same existing canonical Value representatives
=> unnecessarily distinct projected frames
```

## Rejected candidate before experiment

A possible quotient over `LevelSub` pointer identities was rejected by source inspection before spending a run.

Every `LevelSub` is constructed through `intern_level_sub(ks, vs)`, and the
`LevelsPtr` components are themselves interned. Therefore the pointer is
already a canonical proxy for the structural substitution within a session.

## RED — frozen before implementation

Run: `34913712534`  
Job: `104206631589`  
Commit: `515cc4a5abc316ab0526d1f2f77ad37264112a36`

The RED arm reconstructed A6 and added diagnostic instrumentation only.
Actual projected frames still used raw slot pointers; no candidate quotient was enabled.

Frozen discovery workload:

```text
arena-tests/good/perf/grind-ring-5.ndjson
```

Observed:

- cold projected-frame constructions: **369,613**
- slot vectors changed by existing value canonicalization: **289,211**
- repeated canonical slot signatures: **222,499**
- distinct raw representations inside one canonical signature: **5,317**

The RED property was:

> Current A6 already shares every projected frame that is equal under its own existing value canonicalization.

It failed specifically because **5,317 canonical-slot false splits** were found.

This is the witness that permits the representation change.

## Minimal GREEN repair

When a value is selected into a projected frame, pass only that selected value
through `canonicalize_for_spine` before:

1. writing it into the projected slot vector;
2. hashing the projected slots; and
3. calling the existing frame interner.

No new equality algorithm is introduced.

No unselected environment value is canonicalized.

No global environment representation is changed.

This is composition of two already-supported mechanisms:

```text
existing value canonicalization
+
existing projected-frame interning
```

## Arms

### A0 — baseline

Reconstructed A6 unchanged.

### Q — canonical-slot quotient

Canonicalize selected projected slots and retain those canonical
representatives in the frame.

### Q-abl — same-cost causal ablation

Execute the same `canonicalize_for_spine` calls, preserving their cache side
effects and computational cost, but discard the returned representative and
store/hash the original raw slot.

Thus Q versus Q-abl isolates whether **compiling the discovered equivalence into
the projected-frame representation** has causal value.

### GREEN diagnostic

Q plus the same RED diagnostic.

The original failing property must become true:

```text
canonical-slot false splits = 0
```

on the frozen discovery workload.

## Information firewall

The discovery case `grind-ring-5` is excluded from the performance workload.

The held-out workload is selected deterministically from frozen Arena good cases
using file size and path only. No Q/A0/Q-abl performance result is consulted.

## External semantic verifier

The complete frozen Lean Kernel Arena oracle artifact `8931227426` decides semantics.

For A0, Q and Q-abl:

- every frozen good case must be accepted;
- every frozen bad case must be rejected.

Performance is interpreted only after this gate is green.

## Frozen decision rule

Primary metric: paired CPU time.

A **VERIFIED_NOVEL_QUOTIENT_GAIN** requires all of:

1. GREEN diagnostic reports zero canonical-slot false splits;
2. A0, Q and Q-abl pass the complete frozen semantic oracle;
3. Q beats Q-abl in median paired CPU and wins at least 12/15 paired repetitions;
4. Q beats A0 in median paired CPU and wins at least 10/15 paired repetitions.

If Q beats Q-abl but not A0:

```text
VERIFIED_CAUSAL_QUOTIENT_BUT_NET_NEGATIVE
```

The equivalence has causal computational value, but acquisition/maintenance cost
exceeds the gain.

If semantics remain green but Q does not beat Q-abl:

```text
VERIFIED_FALSE_SPLIT_NO_CAUSAL_GAIN
```

The representation was finer than necessary, but compiling the quotient is not
useful under the protected workload.

Any semantic mismatch is:

```text
SEMANTIC_REJECTION
```

## Claim boundary

A positive result would be stronger than the earlier consequence-quotient demo:
this equivalence is **not** already implemented by the pinned checker. It was
identified from a residual in the present representation, witnessed before
implementation, then compiled using existing lawful mechanisms.
