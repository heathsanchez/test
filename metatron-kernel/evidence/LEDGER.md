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

- Status: RETAINED and externally sealed at
  `d7d7fd055634eaad17eff40f6ef3610790c656ce` by run `35657906764`, job
  `106525973850`, artifact `10665242896`, digest
  `sha256:185b26274ae7e19cfd64d13275420c8f105be24145a7ee284337b0b376e83052`.
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

- Status: RETAINED; the integrated G11 checkpoint is externally sealed at
  `d7d7fd055634eaad17eff40f6ef3610790c656ce`.
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

- Status: RETAINED and externally qualified at exact implementation head
  `b8a28332e48bb1d885d03cf670cd6f619bd730e5` by run `35663878360`, job
  `106545136635`, artifact `10668253045`, digest
  `sha256:9d1072f78a9b0eb718265b051a4f1fc56c6e07dde7254aab7a9a46c7031fd777`.
- Exact obstruction: tutorial 039 `good/039_andType.ndjson`, SHA-256
  `d81009480e131d451da9e625fe9a90fff92fbee08d324aefd6fde3c3b89979e1`,
  expects ACCEPT and the sealed G11 checker returns `UNKNOWN`.
- Retained capability: recognize only the exact built-in-shaped `And` envelope:
  two `Prop` parameters, one nonrecursive constructor whose two fields directly
  and in order correspond to those parameters, plus an independently derived
  recursor signature and rule. The existing opaque-signature transaction is
  reused unchanged.
- Falsifiers: parameter and field order, field type/count, result application,
  recursor metadata/type/rule, and owner perturbations reject. Indexed,
  recursive, unsafe, nested, and broader parameterized neighbors remain
  `UNKNOWN`. The exact sealed G11 bytes remain `UNKNOWN` on tutorial 039 while
  the G12 checker accepts those same bytes.
- Explicit exclusions: no general parameterized-inductive engine, positivity,
  iota, projections, or eta.
- Formal warrant: `IdealLean.ParameterizedInductivePromotion.
  promote_preserves_environment_validity` models a validated telescope and
  proves opaque signature promotion preserves environment validity. Its
  validity relations are abstract; it is not Rust refinement or whole-checker
  verification.
- Local qualification: tutorial 001–039 matches with zero incorrect; all
  Rust/Python/ledger/Clippy and portable Lean gates pass.
- Performance: deterministic operation counters are recorded for G11/G12.
  Callgrind is unavailable locally; retired instructions remain `UNKNOWN` and
  no performance promotion is claimed.

## G13-001 — Universe-polymorphic `Prod`

- Status: RETAINED and externally qualified at exact implementation head
  `bc0952e2263d55626514035a872004e173654ae7` by run `35668236889`, job
  `106558640628`, artifact `10670560654`, digest
  `sha256:4fed5032c513d7f996c150d88c9b20aa5ae04cb77ba0ef3e76bd39d26145b786`.
- Exact obstruction: tutorial 040 `good/040_prodType.ndjson`, SHA-256
  `a74e83890dce34014ef7dc8f1f6e7baf56d481df2a776d886462c789c529741d`,
  expects ACCEPT and the G12 checker returns `UNKNOWN`.
- Retained capability: a separate exact `Prod` classifier validates two
  ordered universe parameters, `Type u`/`Type v` parameter sorts, the computed
  `Type (max u v)` result, universe-instantiated constructor and recursor
  signatures, and the exported rule. It reuses the unchanged opaque-signature
  promotion transaction.
- Causal differential: the sealed G12 oracle and G13 candidate agree on all
  tutorial cases 001–039; case 040 is the sole permitted delta, from `UNKNOWN`
  to `ACCEPT`.
- Falsifiers: universe count/order, parameter levels, computed result level,
  constant universe instances, constructor result/order, recursor
  universe/telescope, minor/rule, owner and count perturbations reject.
  Indexed, recursive, unsafe, nested, dependent-parameter and broader shapes
  remain `UNKNOWN`.
- Explicit exclusions: no shared G12/G13 parameterized-inductive abstraction,
  general universe framework, positivity, iota, projections, or eta.
- Formal warrant: `IdealLean.ProdUniversePromotion.
  promote_preserves_environment_validity` proves the prior parameterized
  opaque-promotion law remains valid after the exact two-universe telescope
  and computed-level obligations are established. This is not Rust refinement.
- Local qualification: tutorial 001–040 has 40 matched and zero incorrect;
  differential result is 39 equal, one earned delta, zero mismatches. Rust,
  Python, ledger, Clippy and portable Lean gates pass.
- Performance: the deterministic case-040 counts are three promoted
  signatures, four type judgments and thirteen conversions. Retired
  instructions remain unqualified without a same-cohort control.

## G14-001 — `PProd` replication residual

- Status: RETAINED at implementation commit
  `ce19e8c9c4c5908c59cdf01996e3842fef9c38c4` and externally qualified at
  published head `d6542201fd3aa8fac3e401c3a75fa97fd344defc` by run
  `35673231544`, job `106574159278`, artifact `10671569298`, digest
  `sha256:13d74e8c0ef1f6dc65c9227d94ed402cc434f848af36874bdf028e7b95504a14`.
- Exact obstruction: tutorial 041 `good/041_pprodType.ndjson`, SHA-256
  `9f2f275784ba923bc3a050c5f1856ad0d18c83d31ff107a5cd663d4cceaec98a`,
  expects ACCEPT and sealed G13 `6b50ae9d...` returns `UNKNOWN`.
- Retained capability: a separate exact `PProd` classifier validates
  parameters in `Sort u` and `Sort v`, result sort `max 1 u v`, ordered
  universe instances, constructor and recursor signatures, and the rule. It
  reuses only the existing opaque-signature promotion transaction.
- Causal differential: G13 and G14 agree on tutorials 001–040; tutorial 041
  is the sole delta, from `UNKNOWN` to `ACCEPT`—40 equal, one earned delta,
  zero mismatches.
- Falsifiers: malformed Sort levels, universes, result level, constructor
  spine, recursor motive/minor/rule, ownership and counts reject. Dependent,
  indexed, recursive, nested, unsafe and broader shapes remain `UNKNOWN`.
- Formal warrant: `IdealLean.PProdSortPromotion.
  promote_preserves_environment_validity` proves the existing parameterized
  opaque-promotion law remains valid after the exact PProd Sort telescope and
  computed-sort obligations are validated. It is not Rust refinement.
- No generic parameterized-inductive abstraction was introduced during G14.
- Diagnostic counts are three promoted signatures, four type judgments and
  thirteen conversions. Callgrind is unavailable; retired instructions remain
  unqualified.

## G15-001 — Replicated-law promotion experiment

- Status: RETAINED as a zero-authority representation quotient.
- Obstruction: the independently earned And, Prod and PProd handlers now
  repeat a common two-parameter, one-constructor, one-recursor derivation
  spine after their distinct telescope/result-sort classifiers.
- Retained representation: the private `BinaryProductSortLaw` has exactly
  `And`, `Prod` and `PProd` variants. One `ExactBinaryProductDerivation`
  validates the common parameter telescope, constructor spine,
  motive/minor/rule skeleton, ownership/counts and opaque promotion. External
  name dispatch and unsupported-neighbor checks remain family-specific.
- The independently earned laws remain distinct: And uses Prop parameters and
  result; Prod uses `Type u`, `Type v`, `Type (max u v)`; PProd uses `Sort u`,
  `Sort v`, `Sort (max 1 u v)`.
- Causal ablation: sealed head `d128565e8de681a48cf962f77641696219d76a22`
  is the executable pre-quotient oracle. Exact-head run `35677667353`, job
  `106587470554`, produced 41 equal tutorial verdicts, zero deltas and zero
  mismatches. All G12-G14 exact and perturbation inputs were replayed directly
  against both binaries. A renamed fourth family and tutorial 042 remained
  `UNKNOWN` in both.
- Duplicated surface decreased: `checker.rs` fell from 2584 to 1990 lines.
- Formal status: no new semantic theorem was added or claimed. Existing
  G12-G14 family-specific environment-validity promotion theorems remain the
  semantic warrants. The Rust quotient is externally qualified, not formally
  refined to IdealLean and not whole-checker verification.
- Artifact `10673617458`, digest
  `sha256:e852835781b78936f34902228850d5c6d0c6f0aafadf37326712bdf4bb268b0f`.
- Retired instructions remain `UNKNOWN`: hosted PMU unavailable and there is
  no same-cohort control measurement.

## G16-001 — Exact nullary/singleton `PUnit` law

- Status: RETAINED and externally qualified.
- Frozen baseline: retained G15 head
  `f45b49a6989c09317635c790615ca63c617c84c7`, which returns `UNKNOWN`
  on exact tutorial 042.
- Exact fixture: tutorial 042 `good/042_pUnitType.ndjson`, SHA-256
  `acc7a70c97888e02e2b92e583b370803db0bdac1ddc38f9ff036831459d3a891`.
- Least capability: one name-sealed `PUnit` law supplying a single universe
  parameter, zero term parameters/indices/fields, one nullary constructor,
  one motive/minor/rule recursor, and the level-polymorphic `Sort u` result
  law to the retained G15 `ExactBinaryProductDerivation` skeleton.
- No fourth independent derivation pipeline was introduced. Opaque promotion
  is reused unchanged; no iota, projections, eta, positivity, recursive,
  indexed, nested, unsafe, or general inductive authority is added.
- Falsifiers passed: wrong universe/result sort, missing/extra constructor,
  constructor owner/index/field perturbations, recursor level/minor/type/rule
  perturbations, and fabricated rule claims reject. Indexed, recursive,
  unsafe, and nested PUnit neighbors remain `UNKNOWN`; a renamed family also
  remains `UNKNOWN`.
- Exact oracle differential: tutorials 001–041 are equal to frozen G15;
  tutorial 042 is the sole earned delta, `UNKNOWN → ACCEPT`; zero mismatches.
- External qualification: candidate
  `865548098d16588db5aef79b9e094746933497d9`, run `35686513640`, job
  `106614391496`, artifact `10676299174`, digest
  `sha256:fbb4091c6674b6dfb5c6ff919a4219d531890a035e07d90f2fac7ef36ae05106`.
  The six-case contract and all 42 tutorial cases passed.
- Formal status: the existing generic opaque-promotion theorem still warrants
  the promotion transaction, but the exact Rust PUnit classifier/law is not
  refined to IdealLean and whole-checker verification is not claimed.
- Performance remains `UNKNOWN_NO_SAME_COHORT_HARDWARE_COUNTERS`: hosted
  `perf instructions:u` was unavailable, so no performance promotion is made.

## G17-001 — Exact indexed non-recursive `Eq` law

- Status: RETAINED and externally qualified.
- Frozen baseline: sealed G16 head
  `7b57cc7834b2f7eee34e762fbc23009cd65d6be7`, which returns `UNKNOWN`
  on exact tutorial 043.
- Exact fixture: tutorial 043 `good/043_eqType.ndjson`, SHA-256
  `d45ed54cc74be3d7d92aae6bacc040420ba33f23fa034b4497edb389e089afdc`.
- Least capability: one name-sealed `Eq` law adds exactly one index to the
  retained single-constructor derivation/promotion skeleton: one universe
  parameter, two parameters, one index, zero constructor fields, `Prop`
  result, `Eq.refl`, and the exact K-enabled motive/minor/rule recursor.
- No general indexed-inductive engine was added. Opaque signature promotion is
  reused unchanged; no iota, recursive, nested, unsafe, mutual, or arbitrary
  indexed authority is granted.
- Falsifiers passed: parameter/index counts, result sort, constructor
  owner/index/field count, recursor K bit, levels, index count, rule
  owner/field/body, and recursor type perturbations reject. Recursive,
  reflexive, unsafe, nested, and renamed Eq neighbours remain `UNKNOWN`.
- Exact oracle differential: tutorials 001–042 are equal to frozen G16;
  tutorial 043 is the sole earned `UNKNOWN → ACCEPT` delta; zero mismatches.
- External qualification: candidate
  `ebc901d24688d2aa672c38e4fd80e20d6a0e5b15`, run `35687371672`, job
  `106616975935`, artifact `10676794003`, digest
  `sha256:dc5a59be2174b604161e50ca855e0ecb9579e18ca77c76e128e976cf1da289d2`.
  The six-case contract, all 43 tutorial cases, and 50 end-to-end tests passed.
- Formal status: existing opaque-promotion validity/opacity warrants still
  apply to the staged transaction, but the exact Rust Eq/index law is not
  refined to IdealLean and whole-checker verification is not claimed.
- Performance remains `UNKNOWN_NO_SAME_COHORT_HARDWARE_COUNTERS`.

## G18-001 — Exact recursive `N` law

- Status: RETAINED and externally qualified.
- Frozen baseline: sealed G17 head
  `3a4bb85a06f6434bca27f72e82dc682570123c99`, which returns `REJECT`
  on the valid tutorial 044 Nat declaration.
- Exact fixture: tutorial 044 `good/044_natDef.ndjson`, SHA-256
  `95d33f871f126e234740e05d9291a1cedcc6a2d01522aedc3122b25aab17ab95`.
- Least capability: one name-sealed recursive `N` law deriving `N : Type`,
  `N.zero`, `N.succ : N → N`, the exact two-minor recursor, induction
  hypothesis position, and both exported recursor rules before reusing the
  existing staged opaque-signature promotion transaction.
- No general recursive-inductive engine, positivity search, iota evaluator,
  arbitrary recursion, mutual recursion, indexed recursion, nested recursion,
  or unsafe authority was added.
- Falsifiers passed: recursion flag, result sort, constructor indices,
  constructor field/type claims, recursor K bit, minor count, rule ownership,
  rule field counts/bodies, and recursor type perturbations reject.
  Parameterized, indexed, reflexive, unsafe, nested, and renamed Nat neighbours
  remain `UNKNOWN`.
- Exact oracle differential: tutorials 001–043 are equal to sealed G17;
  tutorial 044 is the sole earned `REJECT → ACCEPT` repair; zero mismatches.
- External qualification: candidate
  `bb7809104681852b46d71c688814f24692965b1b`, run `35704232366`, job
  `106669198325`, artifact `10682964232`, digest
  `sha256:f3f7ae1d4878848b7c00ffffd414e2a5e68410629d6576d4f2cc11f7c32c781b`.
  The six-case contract, all 44 tutorial cases, and 54 end-to-end tests passed.
- Formal status: generic staged opaque-promotion validity/opacity warrants still
  apply to the installation transaction, but the exact Rust recursive Nat law
  and its recursive-shape validation are not refined to IdealLean; whole-checker
  verification is not claimed.
- Performance remains `UNKNOWN_NO_SAME_COHORT_HARDWARE_COUNTERS`.

## G19-001 — Composed recursive indexed `RBTree` law

- Status: RETAINED and externally qualified.
- Frozen baseline: sealed G18 head
  `ce4c2f50ab649e60ee09a19c50f04c7769c5ad19`, which returns `UNKNOWN`
  on exact tutorial 045.
- Exact fixture: tutorial 045 `good/045_rbTreeDef.ndjson`, SHA-256
  `d9781f44fcb7e46ff06da1c8a273a4fec4ae989e4114d6668720bd5b87c20b79`.
- Least capability: a name-sealed composition of already-earned parameter,
  index, recursion, multi-constructor, and staged opaque-promotion laws, plus
  the constructor-specific dependent index equations forced by `RBTree`.
  The type, all three constructor signatures, the two-index motive, three
  minors, recursive hypotheses, recursor type, and all three exported rule
  bodies are derived before promotion.
- No general recursive-indexed inductive engine, positivity search, arbitrary
  indexed recursion, nested/mutual recursion, unsafe authority, or runtime
  iota computation was added.
- Falsifiers passed: altered recursor type, leaf/red/black rule RHS, K bit,
  minor count, renamed family, and unsafe/reflexive/nested neighbours are
  rejected or remain `UNKNOWN` at the declared boundary.
- Exact oracle differential: tutorials 001–044 are equal to sealed G18;
  tutorial 045 is the sole earned `UNKNOWN → ACCEPT` delta; zero mismatches.
- External qualification: candidate
  `60fde2527b7a57c14487b7930d6083451dd01aeb`, run `35707420135`, job
  `106679605077`, artifact `10684434897`, digest
  `sha256:1b69b0eff0d12c46cd0174af8f7d559782e12c0632779e22501a38622108e86a`.
  The six-case contract, all 45 tutorial cases, and 58 end-to-end tests passed.
- Formal status: generic staged opaque-promotion validity/opacity warrants
  still apply to installation, but the composed Rust recursive-indexed RBTree
  law is not refined to IdealLean and whole-checker or general-inductive
  verification is not claimed.
- Performance remains `UNKNOWN_NO_SAME_COHORT_HARDWARE_COUNTERS`.

## G20-001 — Rejection-only empty-inductive arity law

- Status: RETAINED and externally qualified.
- Frozen baseline: sealed G19 head
  `5c51781af6ede78e435b756b7aa75490d10d49c9`.
- Exact malformed corridor: tutorials 046–049. Sealed G19 returns `UNKNOWN`
  on 046, 047, and 049, while 048 is already `REJECT`.
- Least capability: inside the zero-constructor frontier only, universe
  parameters must be unique and the inductive arity must contain exactly
  `numParams + numIndices` Pi binders ending in `Sort`. This is
  rejection-only: it cannot install or accept any declaration.
- The first global version was causally rejected because it changed nine
  protected broader-neighbour verdicts from `UNKNOWN` to `REJECT`. Scoping
  the same law to the existing empty-inductive frontier restores every sealed
  G0–G19 boundary while retaining the desired malformed rejections.
- Exact oracle differential through tutorial 049: 46 equal, three earned
  `UNKNOWN → REJECT` deltas (046, 047, 049), and zero mismatches. Tutorial
  048 remains equal `REJECT`.
- External qualification: candidate
  `97ae436b2af00d563a5460d01d3839d97304b5b0`, run `35761375025`, job
  `106859961966`, artifact `10710223928`, digest
  `sha256:e210119080a776841d2df5bf563625ed6b2ee87c1768f8e52d532c98058f556b`.
  All 49 tutorial cases and 59 end-to-end tests passed.
- Diagnostic suffix atlas improved from 17/96 to 20/96 matches; the first
  remaining mismatch moves from tutorial 046 to tutorial 050.
- Formal status: no new promotion theorem is required because the law is
  rejection-only. Rust-to-IdealLean refinement and completeness of general
  inductive arity checking are not claimed.
- Performance remains `UNKNOWN_NO_SAME_COHORT_HARDWARE_COUNTERS`.

## G21-001 — Rejection-only constructor-result coherence law

- Status: RETAINED and externally qualified.
- Frozen baseline: sealed G20 head
  `80c99cfdce1e9a5349ef4b300f506c92677dc6ce`.
- Exact malformed corridor: tutorials 050–053. Sealed G20 returns `UNKNOWN`
  on all four.
- Least capability: on the otherwise unrecognized single-constructor frontier,
  validate only hard constructor-result invariants: owner/index metadata,
  declared universe order, parameter reuse/order, result arity, and absence
  of recursive occurrences inside indices. Parameter domain types are
  deliberately not compared, preserving conversion-sensitive tutorial 055.
- This is rejection-only: it cannot install or accept any declaration.
- Exact oracle differential through tutorial 053: 49 equal, four earned
  `UNKNOWN → REJECT` deltas (050–053), zero mismatches.
- External qualification: candidate
  `1423040508c602c628f92e845d4ccc3796f165ba`, run `35763602005`, job
  `106867429092`, artifact `10711556671`, digest
  `sha256:d80d8c82fe6838bbc9fab662a9281fd017c39d7ae51021badc9de5193ea92209`.
  All 53 tutorial cases and 61 end-to-end tests passed.
- Diagnostic suffix atlas improves to 25/96 matches; the first remaining
  mismatch moves to tutorial 054 (`indNeg`).
- Formal status: rejection-only structural law; no new promotion theorem is
  required. General positivity/completeness and conversion-sensitive
  constructor-domain validation are not claimed.
- Performance remains `UNKNOWN_NO_SAME_COHORT_HARDWARE_COUNTERS`.

## G22-001 — Definite-negative recursive-field rejection law

- Status: RETAINED and externally qualified.
- Frozen baseline: sealed G21 head
  `fc2e64a0e43676d283e202b7c9b1cbb262360e79`.
- Exact residual: tutorial 054 `indNeg`. Sealed G21 returns `UNKNOWN`.
- Least capability: a rejection-only polarity walk over constructor field
  domains. Pi-domain traversal flips polarity; the inductive constant is
  rejected only when it occurs in a definitely negative position.
- The law deliberately does not attempt general positivity proof, does not
  unfold arbitrary reducible constants, and grants no ACCEPT authority.
- Tutorial 055 is an explicit control and remains `UNKNOWN` in both arms.
- Exact oracle differential through tutorial 054: 53 equal, one earned
  `UNKNOWN → REJECT` delta, zero mismatches.
- External qualification: candidate
  `cc5063c372f72be4bbd8caffa25f5770b055462b`, run `35765424875`, job
  `106873615908`, artifact `10711439094`, digest
  `sha256:d7a17f265897ab3afb8e58134a70038addfb9b26d0803ccc8193d33a30db87f6`.
  All 54 tutorial cases and 63 end-to-end tests passed.
- Diagnostic suffix atlas: 27/96 matches; first remaining mismatch is tutorial
  055, the conversion-sensitive valid constructor-parameter case.
- Formal status: rejection-only structural polarity law; no promotion theorem
  is required. General positivity completeness is not claimed.
- Performance remains `UNKNOWN_NO_SAME_COHORT_HARDWARE_COUNTERS`.



## G23-001 — Conversion-lifted recursive constructor coherence

- Status: RETAINED and externally qualified.
- Frozen baseline: sealed G22 head
  `917566dd7c91fdda1f32e85aaf5ab65a19973923`, which returns `UNKNOWN`
  on tutorial 055 `good/055_reduceCtorParam.ndjson`.
- Least capability: inside the exact name-sealed one-parameter, one-field
  recursive family, validate constructor parameter coherence and recursive
  field coherence by the kernel's existing definitional-equality relation
  after staging the inductive type. This lifts the previously structural
  constructor-coherence law through conversion rather than requiring literal
  AST identity.
- The recursor motive/minor/rule remain structurally derived before opaque
  promotion. No general recursive-inductive engine, arbitrary positivity,
  indexed/reflexive/nested recursion, projection, eta, Rule-K computation, or
  unrestricted conversion authority is added.
- Falsifiers and retained controls passed: all prior G0–G22 end-to-end tests,
  exact tutorial prefix 001–054, malformed constructor/recursor controls, and
  the G21/G22 coherence/negativity boundaries.
- Exact oracle differential through tutorial 055: 54 equal, one earned
  `UNKNOWN → ACCEPT` delta at 055, zero mismatches. Tutorial qualification is
  55 matched, 0 incorrect.
- External qualification: candidate
  `7975697a23091ee72abbfe6e68042f0e079f8738`, run `35767458462`, job
  `106880494500`, artifact `10713170335`, digest
  `sha256:63ec11c759359046e0e2cb792a83c1a0528b42d975110f84c77fe5f3524e9055`.
  The Rust release suite passed 66/66.
- Diagnostic untouched suffix 046–141: 28/96 matched; first remaining
  mismatch is tutorial 058 `PredWithTypeField`.
- Formal status: existing staged opaque-promotion validity/opacity warrants
  still apply to installation, but the exact Rust conversion-lifted family is
  not refined to IdealLean and whole-checker verification is not claimed.
- Performance remains unknown for promotion: hosted retired-instruction
  measurement was unavailable and no same-cohort performance claim is made.


## G24-001 — Manifest constructor-field universe admissibility

- Status: RETAINED and externally qualified.
- Frozen baseline: sealed G23Q head
  `58b08a1b0fc3622a480ec2d72953ba77fdc86265`, which returns `UNKNOWN`
  on tutorials 058–061.
- Certified residual corridor:
  - 058 `PredWithTypeField`: valid Prop with a `Type` field.
  - 059 `TypeWithTypeField`: valid `Type 1` with a `Type` field.
  - 060 `TypeWithTypeFieldPoly`: valid universe-polymorphic
    `Type (u+1)` with a `Type u` field.
  - 061 `typeWithTooHighTypeField`: invalid `Type` whose `Type` field
    lives one universe too high.
- Least capability: within the safe zero-parameter, zero-index, nonrecursive,
  nonreflexive, nonnested, one-constructor/one-manifest-Sort-field envelope,
  derive field-universe admissibility from the existing universe algebra.
  `Prop` keeps its impredicative exception; otherwise the inferred sort of
  the field domain must be at most the inductive result sort. The corresponding
  one-motive/one-minor recursor and rule are structurally derived, then the
  existing staged opaque-promotion transaction is reused.
- Global reclosure against the exact G23Q oracle across tutorials 001–141:
  four and only four deltas, all earned — 058/059/060
  `UNKNOWN → ACCEPT`, 061 `UNKNOWN → REJECT`; zero mismatches.
  Counts: 4 earned deltas, 73 equal-correct, 64 equal-residual.
- Prior committed corpus replay at qualification time: 39/39 status-equivalent
  to G23Q. The exact four corridor fixtures are now retained separately under
  `evidence/residuals/G24-001/`.
- Qualification implementation `447632bbcc7724d17b63361326273ac4498dd07b`;
  qualification head `7439d79d7450d4d52fe1a9e05baf45d508ab8516`;
  run `35846178771`, job `107132797052`, artifact `10744010491`,
  digest
  `sha256:0068e41e35118b997dc3f136a6bf7b21bee4cc28e92912d3fb90839ca5132e88`.
- The first remaining tutorial residual jumps from 061 to 072:
  `good/072_boolPropRec.ndjson`.
- Scope remains bounded: this is not a general inductive universe checker,
  arbitrary constructor telescope rule, positivity engine, or unrestricted
  recursor synthesis law.


## G25-001 — Prop-only binary enum recursor derivation

- Status: RETAINED and externally qualified.
- Frozen baseline: sealed G24 head
  `a3cb6b76fc6aa5d2117f891dda966940648ffaed`, which returns `UNKNOWN`
  on tutorial 072 `good/072_boolPropRec.ndjson`.
- Certified residual: `BoolProp : Prop` has two nullary constructors. Unlike
  the already retained Type-level Bool/Color binary-enum family, its generated
  recursor has no motive universe parameter and eliminates only into `Prop`.
- Least capability: extend the internally shared binary-enum derivation with a
  `Prop` elimination law while leaving the newly earned external family
  name-sealed to `BoolProp`. Constructor ownership/order, nullary shape,
  recursor metadata, motive, minors, target, result, and both computation rules
  are reconstructed before staged opaque promotion.
- Negative controls: wrong motive metadata rejects; adding an illicit recursor
  universe parameter rejects; adjacent tutorial 073 `BogusRecursor` remains
  `UNKNOWN`, so no malformed-recursor authority leaked across the boundary.
- Global reclosure against the exact G24 oracle across tutorials 001–141:
  exactly one earned delta, 072 `UNKNOWN → ACCEPT`; zero mismatches.
  Counts: 1 earned delta, 77 equal-correct, 63 equal-residual.
- Committed differential: 45 fixtures, with exactly the retained 072 fixture
  differing from G24 and no other delta.
- Qualified source `ee58e47f5c9b1fffc6f2587d13cfaf87b16b9af7`;
  implementation `3119496bc766d45bf3511505ef1a1424055d8d6c`;
  run `35847399187`, job `107136766368`, artifact `10744405022`,
  digest
  `sha256:677a76e3e93b4be3efc907bd40f0056b7e0fc47fd7260789ea28c84887af0636`.
- First remaining residual: tutorial 073
  `bad/073_BogusRecursor.ndjson`.
- Scope remains bounded: no general multi-constructor Prop recognizer, no
  arbitrary Prop elimination engine, and no general malformed-recursor checker
  is claimed.


## G26-001 — Definite recursor-metadata incoherence

- Status: RETAINED and externally qualified.
- Frozen baseline: sealed G25 head
  `4b257ea8442a7905af8b894144288864b16fb81a`.
- Primary residual: tutorial 073 `BogusRecursor` was `UNKNOWN` despite a
  supplied recursor whose structural metadata cannot belong to its inductive.
- Least capability: rejection-only structural coherence on the already
  unsupported safe single-constructor frontier. A recursor is definitely
  malformed when declaration-fixed metadata disagrees: ownership/all set,
  parameter/index counts, single-inductive motive count, minor/rule counts,
  rule constructor/field counts, or child `.rec` naming. Elimination
  universes, rule K, and positive inductive semantics remain outside the law.
- Global reclosure found three independent earned deltas with zero mismatches:
  tutorials 073, 136, and 137 all moved `UNKNOWN → REJECT`.
  This is the first direct cross-corpus evidence that the law is reusable
  rather than a patch for 073.
- Adjacent coherent unsupported tutorial 074 remains `UNKNOWN`.
- Qualification: source `aa8b1c2ea1803193f78502b76b961a51a6e51da1`;
  implementation `1537d4f580348e5a9828aae2c8f6df31001e449e`;
  run `35847835068`, job `107138168263`, artifact `10744570750`,
  digest
  `sha256:bcd3050ad8e410a2d7c78a55875f4ac7f5904a22a7359c49a0eda15082fa1826`.
- Tutorial reclosure counts: 3 earned deltas, 78 equal-correct,
  60 equal-residual, 0 mismatches. Committed corpus differs from G25 only on
  the retained 073 fixture.
- First remaining residual: tutorial 074 `good/074_existsRec.ndjson`.
- Scope remains bounded: this law can reject definite structural contradiction
  but cannot accept an unfamiliar inductive or infer its elimination universe.
