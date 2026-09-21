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

## G4-002 — Explicit semantic locals

- Status: RETAINED at `d94bd1dc51ab93b476f4a738feab9e1f964ac79c`.
- The first declaration of G4-001 changed from REJECT to proven when both open
  bodies were extended with the same depth-indexed `FreeId`. A dedicated test
  verifies that distinct `FreeId` values never alias.
- The full fixture then returned UNKNOWN rather than ACCEPT, exposing a second
  residual. This intermediate result is preserved rather than misreported as
  full qualification.

## G4-003 — Universe substitutions in closures

- Status: RETAINED at `d94bd1dc51ab93b476f4a738feab9e1f964ac79c`;
  performance UNKNOWN.
- Obstruction: after shared binders proved the dependent identity, the final
  declaration stopped at `pi-domain-sort` because occurrence-specific universe
  arguments were discarded.
- Least capability: immutable closure-local maps from declaration parameters
  to `LevelTerm`; constant inference and delta construct them explicitly, and
  evaluated sorts and neutral constants retain instantiated terms.
- Qualification: exact G4-001 ACCEPTS, tutorial cases 001–008 match, all Rust
  release tests and strict Clippy pass, and unresolved universe cases retain
  UNKNOWN. No eager AST substitution or global universe assignment was added.
- Retired-instruction counters and a same-cohort flash control remain absent,
  so no performance promotion is claimed.

## G5-001 — Preserve sort-judgment polarity

- Status: RETAINED at `817ed678589cd4b8a3e7c3847ed2e9f10960ad9c`.
- `sort_level` now returns a three-valued judgment. A rigid neutral nonsort is
  refuted, while failed exposure, cycles, and budgets remain UNKNOWN.
- Exact bad tutorial case 009 now REJECTS; cases 001–011 match and the complete
  protected suite passes. Performance remains UNKNOWN without counters.

## G6-001 — Theorem representation and proposition obligation

- Status: OPEN; no theorem mechanism implemented.
- Exact tutorial case 012, SHA-256
  `07c030b1e9ee321bb537f4f82f5238087cbed199f5e4f8673650c3190e54a33a`,
  should REJECT but returns UNKNOWN because `thm` is only preserved as an
  unsupported declaration.
- Least candidate capability: an explicit theorem node, a proof check before
  authority extension, and a separate proof-type-is-Prop obligation. Theorem
  bodies must remain unavailable to conversion.

## G9-001 — Derived empty-inductive authority

- Status: RETAINED by exact-head external qualification.
- Qualifying head: `78a53e3ed6e4f6d5f741c4869ae098cfdcda31bd`.
- Exact obstruction: tutorial 036, SHA-256
  `030852937308e66cb90de3b8de7cd336f3d825e81c87c5be5cc1fe33c6d54356`,
  returned `UNKNOWN` after cases 001–035 matched.
- Least capability: preserve the complete Arena block, but recognize only a
  singleton safe empty type in `Prop` or `Type`. Independently derive the
  unique eliminator signature, type-check it in the staged type authority,
  and atomically install opaque type and recursor signatures.
- Falsifiers: exact recursor-use case 062 accepts; `k` perturbation and
  fabricated extra/orphan empty recursors reject; empty placeholders and
  nonempty `Bool` remain `UNKNOWN`; recursors have no delta/iota body.
- Local qualification: release Rust suite, strict Clippy, Python tests, ledger
  validation, portable Lean skeleton, and exact tutorial prefix 001–036 pass.
- External qualification: run `35653364302`, job `106510875913`, artifact
  `10662982778`, digest
  `sha256:c8fc2be20ec01c957005cdf7047500fab4f37f453f588629587e84ed63e087e4`;
  tutorial 001–037 matched with zero incorrect.
- Formal status: exact external certificate. A portable formal
  empty-inductive rule and Rust-to-spec refinement theorem do not yet exist.
- Performance: `UNKNOWN_NO_PMU_OR_SAME_COHORT_CONTROL`; no wall-time claim.

## G10-001 — First nonempty inductive (`Bool`)

- Status: RETAINED at qualifying head
  `78a53e3ed6e4f6d5f741c4869ae098cfdcda31bd`.
- Exact obstruction: tutorial 037, SHA-256
  `02053d077abf5a63594d1025f9ef2f90dfff65f331503aa3b7486bbbb997b3e8`,
  should accept but remains `UNKNOWN` after the protected 001–036 prefix.
- Retained capability: derive both nullary constructor signatures, eliminator
  signature, and exported rule bodies before atomically installing opaque
  signatures. No iota behavior is installed.
- Falsifiers: constructor-index and rule-RHS perturbations reject; the first
  field-bearing structure remains `UNKNOWN`.
- External qualification: the same run/job/artifact above directly replayed
  tutorial 001–037 with zero incorrect.
- Rejected shortcut: merely type-checking and installing constructors and
  recursors as axioms would grant unearned authority.
- Performance remains `UNKNOWN_NO_SAME_COHORT_RETIRED_INSTRUCTIONS`.

## G11-001 — Exact `TwoBool` structure

- Status: RETAINED locally at source commit
  `174ba4dc80b095308c9aed9286d5d871d6e8a4b1`; exact-head external
  qualification of the new head remains pending.
- Exact obstruction: tutorial 038, SHA-256
  `91a1f7379e22ebbec710ce6b43b7e0750be258ace8fc22d0b889fb76b57010de`,
  should accept but returns `UNKNOWN` after 001–037 match.
- Retained capability: exactly one closed safe `TwoBool : Type`, one
  nonrecursive `TwoBool.mk` constructor with two `Bool` fields, and the
  independently derived `TwoBool.rec` signature and rule claim. The promoted
  runtime authority is signature-only and opaque.
- Falsifiers: constructor index/owner/field count/result, recursor identity,
  minor count/type, rule owner/field count/body, and recursor type perturbations
  reject; indexed, recursive, and unsafe neighboring shapes remain `UNKNOWN`;
  a rejected block cannot partially extend authority.
- Explicit exclusions: parameters, indices, recursion, nesting, mutuality,
  unsafe declarations, iota, projections, and eta.
- Local qualification: exact tutorial 001–038, all Rust/Python/ledger/Clippy
  gates, and the portable Lean build pass.
- Performance: diagnostic counters are recorded. Callgrind is unavailable in
  the local environment and retired instructions remain
  `UNKNOWN_NO_SAME_COHORT_HARDWARE_COUNTERS`; no promotion is claimed.

## G9/G10/G11 shared closed-inductive promotion

- Status: RETAINED locally at `871c8f76691a46694a05599f296c1f9a88bfd845`.
- Family finding: the three retained handlers share one structural action after
  their distinct exact classifiers derive claims: validate signatures in
  dependency order and stage opaque type, constructor, and recursor authority.
- Refactor: `ClosedNonrecursiveDerivation` performs that transaction. The exact
  G9, G10, and named `TwoBool` gates remain outside it, so the accepted external
  frontier is not broadened.
- Causal equivalence: a sealed ten-case G9/G10/G11 vector preserves ACCEPT,
  REJECT, and UNKNOWN outcomes, and the original semantic/structural rule order
  is unchanged.
- Formal warrant: `IdealLean.InductivePromotion.
  promote_preserves_environment_validity` proves the generic sequential
  promotion law, and `promoted_signatures_are_opaque` proves the installed
  representatives have no body. The signature-validity premises are abstract;
  this is not a Rust-refinement theorem and not whole-checker verification.

## G12-001 — Parameterized `And`

- Status: OPEN; deliberately not implemented.
- Exact obstruction: tutorial 039 `good/039_andType.ndjson`, SHA-256
  `d81009480e131d451da9e625fe9a90fff92fbee08d324aefd6fde3c3b89979e1`,
  expects ACCEPT and the sealed G11 checker returns `UNKNOWN`.
- Boundary: this is the first parameterized inductive (`And` with two `Prop`
  parameters). No parameter mechanism is selected until a deciding experiment
  and falsifier are specified.
