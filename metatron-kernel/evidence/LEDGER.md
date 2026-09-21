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
