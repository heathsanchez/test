# Metatron Kernel Experiment Ledger

This is the readable projection of `ledger.jsonl`. The JSONL file is the
machine-readable authority. Rejected and unknown experiments remain recorded.

## G0-000 — Arena stream parser

- Status: RETAINED
- Arena authority: `f5e1bce6e2dc9c60479b3001b76e01722b403799`
- Implementation: `d8fa825da86b88c8c93ec409b8a4485e4228d298`
- Obstruction: no independent checker source tree can parse an Arena stream.
- Least capability: format 3.1.0 parsing with sparse, out-of-order typed IDs.
- Falsifier: duplicate or missing references pass, or the two static format
  fixtures require inherited checker source.
- Qualification: six parser tests, full Rust suite, strict Clippy, CLI exit 2,
  and byte equality against both pinned upstream fixtures passed.
- Protected behavior: malformed streams exit as `ERROR`; unsupported semantic
  declarations remain preserved and yield `UNKNOWN`.
- Primary metric: retired instructions after semantic qualification.
- Performance: deliberately unmeasured at this stage; parser-only correctness
  does not qualify an official retired-instruction comparison.

## G1-001 — Conservative universe equality

- Status: RETAINED
- Arena authority: `f5e1bce6e2dc9c60479b3001b76e01722b403799`
- Implementation: `2f222bf76e8852d748da1782768f29a64873192b`
- Obstruction: Sort inference needs universe equality, but symbolic `imax`
  cannot be collapsed to `max` without proving its right side nonzero.
- Least capability: canonical max/successor atoms, the two unconditional
  `imax` branches, and a bounded guarded node for every unresolved case.
- Falsifier: disagreement with Lean 4.29.1, guessing symbolic `imax`, or
  failure of the 26-parameter equality within 256 semantic steps.
- Qualification: the pinned Lean reference accepted the commutativity,
  idempotence, successor-right, and concrete zero-right obligations; all six
  Rust tests and the protected suite passed.
- Performance: the non-explosion test passed; official retired instructions
  remain deliberately unmeasured until an end-to-end checker qualifies.

## G1-002 — Explicit guarded reduction machine

- Status: RETAINED
- Arena authority: `f5e1bce6e2dc9c60479b3001b76e01722b403799`
- Implementation: `7582fe3d29aa9c3114d4c4fe0334c6dcc6cab216`
- Obstruction: application inference and conversion need beta/zeta/delta, but
  neither substitution copying nor global normalization is warranted.
- Least capability: lazy closures over immutable `Rc` environment frames,
  guarded WHNF transitions, authority-scoped delta-cycle detection, and a
  hard step budget.
- Falsifier: disagreement with Lean beta/zeta, unfolding through opaque
  transparency, proving a delta cycle, or rejecting shared syntax after beta.
- Qualification: six machine tests and the full protected Rust suite passed;
  Lean 4.29.1 accepted the beta and zeta reference obligations.
- Corrective experiment: a first global visited-set rule falsely classified
  `(fun x => x) (fun x => x)` as cyclic. The frozen regression forced visited
  state to reset at beta/zeta/environment boundaries while delta chains retain
  cycle detection.
- Performance: closures avoid expression copying by construction; official
  retired instructions remain unmeasured until end-to-end qualification.

## G1-003 — Bidirectional dependent core and relational conversion

- Status: RETAINED
- Arena authority: `f5e1bce6e2dc9c60479b3001b76e01722b403799`
- Implementation: `6c5d8941e91181644addb4e760004065f3998ee0`
- Obstruction: reduced terms still cannot earn a typing or conversion
  judgment, especially for application and dependent Pi instantiation.
- Least capability: syntax-directed inference plus a guarded worklist that
  tries rigid identity before requesting WHNF transitions.
- Falsifier: failure to instantiate a Pi body with its argument closure,
  proving unequal supported sorts, or guessing at unresolved `imax`, cycles,
  polymorphic delta, or budget exhaustion.
- Qualification: seven inference tests, six conversion tests, the full
  protected suite, and the exact Lean 4.29.1 dependent-core oracle passed.
- Semantic boundary: monomorphic core declarations are implemented;
  polymorphic delta remains `UNKNOWN` until explicit universe substitution is
  represented in closures.
- Cost boundary: environment extension currently clones a small `Rc`-backed
  map. That is an implementation selection, not part of semantic identity, and
  remains eligible for a later session/memory residual.
- Performance: official retired instructions remain unmeasured until the
  end-to-end Arena verdict layer qualifies.

## G2-000 — Sequential Arena verdict boundary

- Status: RETAINED
- Arena authority: `f5e1bce6e2dc9c60479b3001b76e01722b403799`
- Implementation: `d107a3eb1fdd9ac593b6a05cda1d5c7fbd8cc53d`
- Obstruction: internal judgments were not composed into official process
  verdicts or a monotone declaration session.
- Least capability: check a declaration against current authority, extend only
  after proof, and map proven/refuted/residual/malformed to exits 0/1/2/3.
- Falsifier: accepting a self-proof, guessing an inductive, or producing any
  wrong exit on the frozen six-case cohort.
- Qualification: release tests passed; sparse/out-of-order and beta cases exit
  0, unbound/self-proof cases exit 1, and unsupported inductive exits 2.
- Performance: intentionally unmeasured here. Only Task 9's exact external
  same-cohort retired-instruction run may promote performance claims.

## G2-001 — Promoted-judgment experiment

- Status: UNKNOWN_NO_RECURRENCE
- Arena authority: `f5e1bce6e2dc9c60479b3001b76e01722b403799`
- Frozen fixture: `evidence/residuals/G2-001/fixture.ndjson`, SHA-256
  `3ab79d5676f0e70523b67c083e35c8a2322d1f5b476c081069d2a039f0e0023d`.
- Measurement: the exact good-beta path made one trusted conversion call and
  therefore repeated zero positive calls at the promotion boundary.
- Decision: no capability bank, cache, persistence, or direct map was added.
  Residuals earn generators; a non-recurring obligation has earned none.
- Performance: no ablation or retired-instruction claim is meaningful because
  enabled and disabled programs would be identical.

## G2-002 — Exact-head external qualification

- Status: RETAINED for correctness qualification; performance UNKNOWN.
- Candidate: `47aff936001f88204f2bf05a9fad9abe4eda9a9c` at Arena authority
  `f5e1bce6e2dc9c60479b3001b76e01722b403799`.
- External evidence: GitHub Actions run `35620658852`, job `106402590918`,
  artifact `10648885370`, digest
  `sha256:c100e632fef5e952b7fabee07fbb0f1a7358a7634441a43a86f99095a4d39176`.
- Qualification: all six ordered cases matched; zero cases were incomplete,
  incorrect, or errored. Verdict totals were three ACCEPT, two REJECT, and one
  preserved UNKNOWN.
- Falsifier: any authority mismatch, fixture or verdict drift, or presenting
  unavailable hardware counters as a performance improvement.
- Performance: GitHub's runner exposed no usable `perf instructions:u`
  counter, and no same-cohort flash control count exists. Retired-instruction
  performance is therefore `UNKNOWN_NO_PMU_OR_CONTROL`; wall time is not a
  substitute and no promotion is claimed.

## G3-001 — Opaque-hint delta at conversion mismatch

- Status: OPEN; no semantic mechanism implemented.
- Arena authority: `f5e1bce6e2dc9c60479b3001b76e01722b403799`;
  exact tutorial case `good/006_betaReduction.ndjson`, SHA-256
  `3320f6f67cd55b2bae9112ea9b0d002f231e88ec4fb3c3f3c8fd4e750b13ce78`.
- Ordered result: cases 001–005 matched their expected exits. Case 006 should
  ACCEPT but the baseline checker REJECTS, so execution stopped there.
- Primary class: conversion. The expected type needs delta and beta through
  the earlier `constType` definition, whose body was incorrectly made
  semantically inaccessible because its exporter hint is `opaque`.
- Deciding experiment: changing only that first hint to `regular` made the
  unchanged checker ACCEPT. This falsifies an independent application or
  dependent-instantiation failure for this fixture.
- Least candidate capability: keep definition bodies semantically available;
  let hints select cheap work, then permit guarded full-transparency delta only
  after rigid comparison stalls. Cycles, budgets, and absent evidence retain
  `UNKNOWN`.
- Causal ablation: enabled versus disabled post-mismatch delta on identical
  code and authority; only case 006 may change on the protected prefix.
- Performance plan: official retired instructions on the identical ordered
  tutorial prefix plus G2 cohort against pinned flash, same runner and build.
  Missing PMU or control evidence remains UNKNOWN and cannot be replaced by
  wall time.

## G3-002 — Guarded semantic-delta experiment

- Status: RETAINED for semantics at implementation
  `6c61a895c8055a3da16ba2a38a716e4995b5c467`; no performance promotion.
- Representation correction: `preferred_for_reduction` now records a cost
  preference, while `Transparency::Full` expresses semantic availability.
  The distinction is explicit in syntax, environment, and machine state.
- Execution remains shallow: relational conversion first uses preferred
  bodies, then requests full transparency only after a rigid mismatch. It does
  not construct a global normal form or assume confluence or termination.
- Exact ablation: `PreferredOnly` REJECTS G3-001; the guarded semantic fallback
  ACCEPTS it. The same build matches tutorial cases 001–006 and the complete
  protected Rust/Python suite.
- UNKNOWN protection: nonpreferred full-transparency delta cycles and exhausted
  budgets remain UNKNOWN; polymorphic delta remains unsupported rather than
  guessed.
- Performance: the local environment has no `perf` executable, so candidate
  and flash retired-instruction totals are absent. Status is
  `UNKNOWN_NO_COUNTERS`; semantic retention is not a performance claim.

## G4-001 — Dependent conversion under a shared binder

- Status: OPEN; no mechanism implemented.
- Exact residual: pinned tutorial `good/008_forallSortWhnf.ndjson`, SHA-256
  `b4af42800421f4ac5ec7e699a706bdd82f9f1324a5d2d49769fb340bf36e6a48`.
  Cases 001–007 match; case 008 should ACCEPT but REJECTS.
- Localization: the first 14 lines—the dependent identity declaration alone—
  already reject with `distinct-neutral-heads`. The later sort-WHNF declaration
  is not reached.
- Separator: concretizing the universe and removing its level parameter still
  rejects the dependent identity. Universe substitution is therefore not the
  primary residual.
- Least candidate capability: compare dependent Pi bodies after extending both
  original environments with the same explicit fresh neutral at a shared
  binder depth. No substitution copying or global normalization is warranted.
- Falsifier: witness aliasing, any protected verdict drift, or loss of UNKNOWN
  at cycle/budget edges. Retired-instruction comparison remains planned under
  the same-identity measurement law.
