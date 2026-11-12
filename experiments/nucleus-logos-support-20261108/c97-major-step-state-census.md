# C97: charged major-step and source-state census (13 November 2026)

**State: WARRANTED_BOUNDED diagnosis; original proof still UNKNOWN.** This
branch changes only `#[cfg(feature="diagnostics")]` accounting, not kernel
logic, constructor eligibility, source authority, cache admission or budget.
It does not resolve any of the six frozen standard-budget UNKNOWNs.

## Authority and reproduction

- Parent: published C96 commit `da31717166d2b8be5b7e3e4415256c1d8e08b0bc`
  (tree `92399a26a7ee4c41efc673bc899fda58e7f4d7b8`).
- Same untouched Arena source at upstream
  `6c2d82164f1a2b1ac94aee62290fe78a3c3853fb`, fixture
  `magma-list-pair-n21.ndjson`; SHA256
  `b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84`.
  Original exporter `lean4export 3.1.0`, Lean `4.34.1`.
- Diagnostic binary (Rust dev, `--locked --features diagnostics`) SHA256
  `250a4690b6a5bb34cd176af52279ac67471ce71d92d6b3f02d6a1565a70da295`.
- Run `python3 -B
  experiments/nucleus-logos-support-20261108/probe_c97_major_steps.py
  metatron-kernel/target/debug/metatron-kernel
  /path/to/magma-list-pair-n21.ndjson`. The probe enforces the unchanged
  original source digest, `UNKNOWN` (exit 2) in both arms, byte-identical
  operation counters and additive histogram conservation. Before C97, this
  probe was RED because no C97 receipts existed.
- Runtime flags in both arms:
  `NUCLEUS_EXPERIMENTAL_RELEVANCE=1`,
  `NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA=1`,
  `METATRON_KERNEL_DIAGNOSTICS=1`. Observer adds only
  `NUCLEUS_C97_MAJOR_STEP_TRACE=1`.
- The qualified production regression
  `NUCLEUS_EXPERIMENTAL_RELEVANCE=1
  NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA=1 cargo test --release --locked`
  returned exit 0 across enabled unit and integration suites; existing
  source-scoped ignores remain ignored. No full external 403-case forgery
  corpus was replayed in this restored session.

## First exhausting owner (65,157 available work units)

Unchanged N21 `UNKNOWN` with `276` declarations, `247` type judgments,
`44,957` conversions and `89` inductive signatures. These counters are
identical with the read-only observer disabled and enabled.

| Disjoint per-loop source action | Count |
| --- | ---: |
| `Expr::App` traversal | 13,364 |
| `Expr::BVar` lookup | 11,792 |
| `Expr::Lam` handling | 9,609 |
| `Expr::Const` exposure | 3,298 |
| `Expr::Proj` handling | 703 |
| `Expr::NatLit` handling | 173 |
| **Total observed major-exposure evaluator loop iterations** | **38,939** |

The 38,939 iterations are **93.9%** of 41,452 owner-charged units measured
during major exposure. The remaining 2,513 units are non-loop charges such
as keyed replay work and nested helpers; the histogram does not claim to
attribute these to individual expression heads. The independently recorded
C96/C95 result (41,441 major units in its separately observed arm) is not
silently substituted for this C97 measurement.

### Distinguish repeated source expression from an identical reduction state

| Read-only key | Unique observations | Repeated observations |
| --- | ---: | ---: |
| `(ExprId, EnvFrameId)` *only* | 26,812 | 12,127 |
| `(Closure, pending arguments, transparency, stuck-projection mode)` | 32,964 | 5,975 |

The first projection drops universe substitutions and pending arguments; it
is **not a cache key**. The second key includes actual captured environment,
source expression, universe substitution, ordered pending spine and mode,
and was compared structurally (no hash-only equality). Even the second
does **not** capture all visited-cycle state, remaining fuel, proof-completion
status or enclosing recursor worklist; repeats cannot yet be promoted to
reusable proofs or rule selections.

Of 5,975 repeated local head+pending states, the largest repeated sources
are `BVar` `ExprId(6)` (3,231), `BVar` `ExprId(1)` (684), and `BVar`
`ExprId(11)` (379). Repeated short capture lookups are real, but 5,975 is
only the **number of repeated observation sites**, not an estimated saving:
no completed intermediate result or full-worklist equivalence has been
established. `Expr::Const` NameId(66), which the pinned source maps to
`Nat.rec`, was encountered 317 times inside these exposures, but this
count does not make its delta or iota work the dominant cost.

## Second sampled owner (32,578 units)

The second owner measured 16,536 evaluator iterations out of 17,455
major-exposure charge (94.7%); 5,264 BVar, 5,532 App, 3,861 Lam, 1,473
Const, 320 Proj, 86 NatLit. Its structurally complete *local* reduction-key
ledger recorded 14,126 new states and 2,410 repeats. The `HashSet` is
machine-local and persists across sampled owners, so this second repeat
count includes possible matches to earlier owners. It is not an isolated
second-owner cache-hit rate.

## What changed and the next decisive test

C96 established the captured BVar closure chain was at most four links.
C97 now establishes that the *charge inside major exposure* is mostly
App/BVar/Lam traversal. Counting only source ExprIds exaggerated reuse by
roughly a factor of two; adding actual lexical environments, universes and
pending arguments preserved only 5,975 repeats in the first owner.

**Next candidate, not implemented here:** attach a *diagnostic-only
completion witness* to repeated local exposure states, measuring whether a
previous pass actually completed to a stable source-certified value, or
ended neutral/UNKNOWN. If an eligible repeated state exists, test one
bounded internal positive-result cache keyed by full semantic reduction
context, sharing the same owner budget and excluding unresolved recursors,
projections, missing authority and partial continuations. Re-run the exact
originals and forged-proof controls before admitting any source acceptance.
An intermediate-state hit alone never licenses a result.

The `magma-list-pair-n7` unchanged source was not reconstructed in this
fresh executor session; this new C97 histogram is **N21-only**. The earlier
source-pinned C96 N7 evidence remains unchanged. There is no new Mathlib
acceptance or full protected 403-case regression claim.
