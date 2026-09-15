# A6 EARNED-ONLY APPLY — Frozen Development Protocol

## Residual

Current A6 Callgrind on the frozen dominant case `grind-ring-5` reports:

- `eval_no_cache`: **14.15%** of all retired instructions;
- `spine_snoc_hc`: **8.39%**;
- `mk_rigid_hc`: **5.76%**;
- `canonicalize_for_spine`: **3.99%**;
- `mk_unfold_hc`: **3.39%**;
- related hash-table growth/insert work adds several more percent.

Previous experiments already ruled out the obvious lower-level alternatives:

- parent-tail prune splice: **+1.71% CPU**;
- bit-directed prune: **+0.83% CPU**;
- removing frame interning: **+9.38% CPU**;
- type-consequence reuse: candidate slower than matched recompute ablation;
- already-earned quote/global-key consequence reuse: only microseconds of total work.

The largest coherent residual is therefore canonicalization and hash-consing in
general application.

## Hypothesis

Do not manufacture canonical identity merely because an application is being
constructed.

Preserve the canonical/hash-consed path only when identity has already been
earned:

```text
argument already canonical
OR
canon_cache already maps the raw argument to a canonical representative
```

Otherwise construct the spine and result directly without:

- `canonicalize_for_spine`;
- `spine_snoc_hc`;
- `mk_rigid_hc` / `mk_unfold_hc`.

This changes no mathematical reduction rule and does not merge values.

NatSucc and native Nat-reduction special paths remain frozen.

## Arms

### A0

Current reconstructed A6.

### earned

`scripts/patch_a6_earned_only_apply.py --mode earned`

Canonical/hash-consed construction is retained only for already-earned identity.

### raw ablation

`scripts/patch_a6_earned_only_apply.py --mode raw`

General Rigid/Unfold application always uses raw construction. Nat-special
paths are unchanged.

This is a causal ablation for the value of retaining already-earned identity.

## Build

All arms use the same Arena-style PGO procedure, trained on frozen
`init-prelude`, matching sokonanoda's Arena build strategy.

## Frozen semantic gate

Pinned checker:
`9b4ea12f4cd437d00b6bcd0e34743065c58dea08`

Frozen Arena artifact:
`8931227426`

A0 and `earned` must each:

- accept 103 / 103 good cases;
- reject 58 / 58 bad cases.

If `earned` differs on any verdict, reject the intervention.

The raw ablation is allowed to fail the oracle: such a failure is evidence that
some earned canonical identity is semantically necessary. If raw is oracle
green, it remains eligible as a performance ablation.

## Development workload

These cases are not held out and authorize no general performance claim:

- `perf/grind-ring-5`;
- `init-prelude`;
- `perf/app-lam`;
- `perf/beta-ladder`;
- `perf/let-ladder`.

All present cases are run as one combined development workload for 30 paired,
deterministically randomized repetitions.

Primary metric: paired CPU seconds.

Per-case timings are also recorded diagnostically.

## Frozen development decision

Proceed to a new disjoint held-out workload only if:

1. A0 and `earned` pass the full semantic oracle;
2. on the combined development workload, `earned` has:
   - median paired CPU delta versus A0 < 0;
   - at least 18 / 30 CPU wins;
3. on `grind-ring-5`, the median paired CPU direction versus A0 is < 0.

If raw is semantic-green, require additionally:

4. `earned` beats raw in combined median paired CPU with at least 18 / 30 wins.

If raw is semantic-invalid, requirement 4 is replaced by the semantic separator
itself.

## If the development gate passes

Freeze a disjoint held-out workload before inspecting its timing:

- remove all five development cases;
- order remaining frozen good cases by descending bytes, path tie-break;
- take the first 24.

Held-out protocol:

- warm A0 and `earned` once;
- 30 paired, deterministically randomized repetitions;
- primary metric: CPU seconds over the complete 24-case workload.

The held-out gate passes only if `earned` versus A0 has:

- median paired CPU delta < 0;
- at least 18 / 30 CPU wins.

If raw is semantic-green it is measured on held-out as a diagnostic, but the
held-out escalation decision remains candidate versus A0; the causal
candidate-versus-raw requirement was already frozen in the development gate.

Only after that held-out gate passes may full Arena Mathlib be built and run.

For Mathlib, use the Arena definition frozen at the time of this protocol:

- Arena repository commit: `4543f486677a6cb56c7656767712cd017f8058ea`;
- mathlib4 ref: `v4.29.1`;
- mathlib4 rev: `5e932f97dd25535344f80f9dd8da3aab83df0fe6`;
- module: `Mathlib`.

A Mathlib performance claim requires candidate acceptance plus a lower median
wall/CPU time than A0 under identical Arena-style PGO builds.

## Claim boundary

A positive result would support:

```text
canonical identity should be paid for only after consequence has earned it.
```

A negative result means the hot hash-consing work is buying enough future
structure to justify itself; no post-hoc value-kind classifier will be added
without a new separator.
