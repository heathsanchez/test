# C95: exact-source charged recursor cost factorization (13 November 2026)

**Status: WARRANTED_BOUNDED diagnostic result; still UNKNOWN as a completeness
fix.** The original valid Arena magma-list-pair-n7 and n21 exports still
return UNKNOWN. No inference rule, recursor rule, source, constructor guess,
budget or cache eligibility was changed.

## Authority and controls

- Parent: [published C94 research tree](https://github.com/heathsanchez/test/tree/research/nucleus-c94-owner-phase-observer-20261113)
  `0440ae0f293dab634e1ed4c0f3e1c0f1ca1b55ee`.
  Code modifications in C95 are diagnostic-only; the C94 probe's optional
  observer-flag parameter is refactored without changing its default.
- Arena upstream `6c2d82164f1a2b1ac94aee62290fe78a3c3853fb`, generated
  original byte hashes: n7
  `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`,
  n21 `b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84`.
- Current C91-style qualification: default judgment allowance 65,536;
  flags `NUCLEUS_EXPERIMENTAL_RELEVANCE=1`,
  `NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA=1`, and
  `METATRON_KERNEL_DIAGNOSTICS=1`. Observer ON adds
  `NUCLEUS_C95_PHASE_TRACE=1`; observer OFF has no C95 flag.
- Build: `cargo build --locked --features diagnostics` (debug binary SHA-256
  `90a316894598b25b4e2fce771ab6af617b182e4a1a4cd2554e8339589ea5edba`).
  Reproduce with `python3 -B
  experiments/nucleus-logos-support-20261108/probe_c95_phase_cost.py
  metatron-kernel/target/debug/metatron-kernel
  /path/to/arena/_build/tests/perf/magma-list-pair-n7.ndjson`, likewise n21.
  Script checks source SHA, identical original `UNKNOWN` exit 2, exact
  operation-counter equality, nonnegative fuel, and **conservation** across
  charged phases. The test was RED against C94 lacking stage receipts;
  C95 is GREEN for both unchanged originals.
- The C94 observer also remains GREEN on n7 and n21 when run against the
  C95 diagnostic binary; its original phase receipts, shared source budget,
  `UNKNOWN` verdicts and operation-counter equality are preserved. This is a
  diagnostic compatibility check, not a new original ACCEPT.
- `NUCLEUS_EXPERIMENTAL_RELEVANCE=1
  NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA=1 cargo test --release --locked`
  completed with exit 0: all active library and integration tests PASS,
  ten existing library tests ignored. No protected 403-case whole-export
  replay was rerun here.

## Single budget-exhausting `Decidable.rec` owner per original

| Charged stage | n7 (start 65,055, remaining 0) | n21 (start 65,157, remaining 0) |
| --- | ---: | ---: |
| Actual major exposure | 36,970 (56.83%) | 41,441 (63.60%) |
| Checked rule RHS exposure | 10,360 (15.92%) | 8,749 (13.43%) |
| Completed-result cache and cloning | 1,152 (1.77%) | 708 (1.09%) |
| Rule RHS telescope binding | 919 (1.41%) | 589 (0.90%) |
| Other charged work, including replay keys | 15,654 (24.06%) | 13,670 (20.98%) |
| **Total, disjoint stages** | **65,055 (100%)** | **65,157 (100%)** |
| Replay-key charge, inclusive cross-check | 15,440 (23.73%) | 13,720 (21.06%) |

Replay-key charge is independently measured at its reservation site. It is
**not** a sixth disjoint stage: its inclusive measure can overlap nested
qualified recursor computations triggered by a major/RHS exposure. Adding it
to the disjoint total would double-count some work. The disjoint stage cost
is the shared owner's `Cell<Option<usize>>` decrease measured on entry/exit,
including all nested calls and failures. Each RAII scope charges even when
the wrapped branch returns UNKNOWN; exact conservation is tested on every
emitted receipt, not inferred from timing.

Observer OFF/ON operation counts were equal: n7 declarations276,
inductive-signatures89, type-judgments247, conversions45,551; n21
276/89/247/44,957. No acceptance improvement was observed.

## What this changes

For both charged originals, **actual major exposure** dominates the
owner-exhausting worklist. Completed-result retention accounts for only about
1–2% of charged fuel; rule telescope binding under 1.5%. This is evidence
against spending the next implementation cycle on global completed-result
cache capacity or binder-telescope micro-optimization as the leading lever.

It is not proof that major exposure is redundant: the C94 fresh
`ExprId(11) = BVar(2)` majors had 235/235 and 206/206 distinct immutable
binding-node identities; their environments may still be related only by a
stronger, unproved observational equivalence. The C89 frozen 262,144/24-flag
audit already rejected exact pending-closure and alias reuse. Do not duplicate
it here. The C29 association of `Nat.decidableBallLT` with the chain remains
**CANDIDATE**, not source-dynamic causal evidence.

## Cheapest decisive next experiment

Qualify the *actual* binding and source-call lineage for the expensive major
exposures in one failing owner. Record per-exposure source head, captured
binder-node ID, registered rule, work delta and exit reason with bounded
histograms (including UNKNOWN); compare n7 vs n21 scaling. If a repeated
source semantics is demonstrated, attempt one exact, source-authorized
evaluator algorithm (e.g., demand-driven unfolding with charged shared
subcomputations), with a synthetic wrong-owner/wrong-universe/wrong-branch
negative and exact original/forged replay at the **same** budget. An observed
constructor endpoint alone is not an iota warrant.

Six valid original UNKNOWNs and source-qualified whole Mathlib ACCEPT remain
**UNKNOWN**. A complete protected 403-case replay is not implied by C95's
diagnostic-only probes or by its release tests.
