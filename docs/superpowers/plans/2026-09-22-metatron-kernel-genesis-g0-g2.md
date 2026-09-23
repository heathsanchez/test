# Metatron Kernel Genesis G0–G2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and externally qualify the first independent Metatron-guided Lean Arena checker substrate: format 3.1.0 parsing, sparse/out-of-order IDs, a minimal dependent type core, guarded beta/zeta/delta conversion, and fail-closed tri-state verdicts.

**Architecture:** A Rust crate under `metatron-kernel/` stores the exporter DAG without inheriting another checker's source, interprets terms with explicit immutable closures, and returns proven/refuted/unknown judgments. The plan admits only G0–G2 mechanisms; every later Lean feature remains an explicit residual.

**Tech Stack:** stable Rust 2024 edition; `serde_json`; Rust standard library; Python 3.12 standard library for evidence validation; GitHub Actions `ubuntu-24.04`; upstream Lean Kernel Arena format 3.1.0.

**Spec:** `docs/superpowers/specs/2026-09-22-metatron-kernel-genesis-design.md`

## Global Constraints

- The Flash control remains untouched at `metalogiclabs/mathgraph-lean-kernel@78c7502bac8a5ba000057b3f083bc0595ac65750`.
- The upstream Arena authority is pinned initially at `leanprover/lean-kernel-arena@f5e1bce6e2dc9c60479b3001b76e01722b403799`.
- No sokonanoda, MathGraph, nanoda, official-kernel, Tenet, con-leche, or lean4lean source is copied into the new checker.
- Unsupported semantic features return Arena exit 2.
- A supported semantic contradiction returns Arena exit 1.
- Malformed input or an internal invariant failure returns an error exit distinct from 0, 1, and 2.
- Search-budget exhaustion returns unknown, never reject.
- Only comparable measurements with identical metric, cohort, ordered case plan, and measurement contract may promote a candidate.
- Native wall time may reject a clear regression but may not promote a performance change.
- The primary optimization metric is retired instructions.
- Direct readable source is the product; patch scripts may only support experiments.
- Every runtime behavior starts with a failing test observed before implementation.

## Review Focus

1. A forward-referenced level ID must resolve without assuming dense or ascending indexes; a missing ID must be a malformed-input error.
2. An unbound de Bruijn index must reject a supported declaration rather than panic or decline.
3. An unsupported inductive record must decline the stream rather than be ignored or accepted.
4. Conversion fuel exhaustion and a cyclic delta path must return unknown rather than equality or inequality.
5. A cached/promoted judgment from an incompatible environment authority must never be reused.

---

### Task 1: Seed the crate, verdict boundary, and evidence schema

**Files:**
- Create: `metatron-kernel/Cargo.toml`
- Create: `metatron-kernel/src/lib.rs`
- Create: `metatron-kernel/src/main.rs`
- Create: `metatron-kernel/src/verdict.rs`
- Create: `metatron-kernel/tests/cli_verdict.rs`
- Create: `metatron-kernel/evidence/ledger.jsonl`
- Create: `metatron-kernel/evidence/LEDGER.md`
- Create: `metatron-kernel/evidence/schema.json`
- Create: `metatron-kernel/scripts/check_ledger.py`
- Create: `metatron-kernel/tests_py/test_ledger.py`

**Interfaces:**
- Produces: `Verdict::{Accept, Reject, Unknown, Error}` and `Verdict::exit_code() -> i32`.
- Produces: `run<R: BufRead>(reader: R) -> Verdict`, initially returning `Unknown` for every readable stream.
- Produces: ledger records with exact obstruction, falsifier, qualification, and performance fields.

- [ ] **Step 1: Write failing Rust verdict tests**

```rust
use metatron_kernel::verdict::Verdict;

#[test]
fn arena_exit_codes_preserve_unknown() {
    assert_eq!(Verdict::Accept.exit_code(), 0);
    assert_eq!(Verdict::Reject.exit_code(), 1);
    assert_eq!(Verdict::Unknown.exit_code(), 2);
    assert_eq!(Verdict::Error.exit_code(), 3);
}
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd metatron-kernel && cargo test --test cli_verdict`

Expected: FAIL because the crate and `Verdict` do not exist.

- [ ] **Step 3: Add the minimal crate and verdict implementation**

`Cargo.toml` declares package `metatron-kernel`, binary `metatron-kernel`, and only `serde_json = "1"` as a product dependency. `src/main.rs` locks stdin, calls `run`, and exits with `Verdict::exit_code()`. `run` returns `Unknown` until Task 3 supplies parsing.

- [ ] **Step 4: Run Rust tests and verify GREEN**

Run: `cd metatron-kernel && cargo test --test cli_verdict`

Expected: 1 passed, 0 failed.

- [ ] **Step 5: Write failing Python ledger tests**

```python
def test_seed_ledger_is_valid(self):
    records = load_records(ROOT / "evidence/ledger.jsonl")
    self.assertEqual(validate_records(records), [])

def test_retained_entry_requires_obstruction_falsifier_and_run(self):
    record = seed_record(decision="retained")
    for field in ("obstruction", "falsifier", "qualification"):
        damaged = dict(record)
        damaged.pop(field)
        self.assertTrue(validate_records([damaged]))
```

- [ ] **Step 6: Run the ledger test and verify RED**

Run: `cd metatron-kernel && python -m unittest tests_py.test_ledger -v`

Expected: import failure for `scripts.check_ledger`.

- [ ] **Step 7: Implement the ledger validator and seed G0 residual**

The validator requires these literal keys on every record: `id`, `date`,
`arena_sha`, `baseline`, `obstruction`, `residual_class`, `capability`,
`competing_explanation`, `falsifier`, `ablation`, `protected_suite`,
`primary_metric`, `decision_rule`, `implementation_commit`, `qualification`,
`performance`, and `decision`. The seed `G0-000` decision is `open`, its
obstruction is the inability to parse one Arena 3.1.0 stream, and its
qualification is `null`.

- [ ] **Step 8: Verify, commit, and checkpoint**

Run:

```bash
cd metatron-kernel
cargo test
python -m unittest discover -s tests_py -p 'test_*.py' -v
python scripts/check_ledger.py
```

Expected: all commands exit 0. Commit message:
`feat(kernel): seed tri-state checker and evidence ledger`.

### Task 2: Sparse typed ID tables and lossless record model

**Files:**
- Create: `metatron-kernel/src/id.rs`
- Create: `metatron-kernel/src/syntax.rs`
- Create: `metatron-kernel/tests/id_table.rs`
- Modify: `metatron-kernel/src/lib.rs`

**Interfaces:**
- Produces: `NameId`, `LevelId`, `ExprId`, and `DeclId` newtypes over `u64`.
- Produces: `IdTable<I, T>::insert`, `get`, `contains`, and `len` without dense-index assumptions.
- Produces: immutable syntax enums `Level`, `Expr`, and `Declaration` matching the supported export records.

- [ ] **Step 1: Write a failing sparse-ID test**

```rust
#[test]
fn sparse_and_out_of_order_ids_are_independent() {
    let mut table = IdTable::<LevelId, &'static str>::default();
    table.insert(LevelId(2), "child").unwrap();
    table.insert(LevelId(1), "parent").unwrap();
    assert_eq!(table.get(LevelId(2)), Some(&"child"));
    assert_eq!(table.get(LevelId(1)), Some(&"parent"));
    assert_eq!(table.len(), 2);
}

#[test]
fn duplicate_id_is_rejected() {
    let mut table = IdTable::<ExprId, u8>::default();
    table.insert(ExprId(4), 1).unwrap();
    assert!(table.insert(ExprId(4), 2).is_err());
}
```

- [ ] **Step 2: Verify RED**

Run: `cd metatron-kernel && cargo test --test id_table`

Expected: FAIL because `id` does not exist.

- [ ] **Step 3: Implement IDs and `IdTable` with `HashMap<u64, T>`**

Do not add a dense vector optimization. Duplicate insertion returns a typed
`DuplicateId` error carrying the table kind and numeric ID.

- [ ] **Step 4: Add the supported syntax records**

```rust
pub enum Level {
    Zero,
    Succ(LevelId),
    Max(LevelId, LevelId),
    IMax(LevelId, LevelId),
    Param(NameId),
}

pub enum Expr {
    BVar(u64),
    Sort(LevelId),
    Const { name: NameId, levels: Vec<LevelId> },
    App { fun: ExprId, arg: ExprId },
    Lam { domain: ExprId, body: ExprId },
    Pi { domain: ExprId, body: ExprId },
    Let { ty: ExprId, value: ExprId, body: ExprId },
}

pub enum Declaration {
    Axiom { name: NameId, level_params: Vec<NameId>, ty: ExprId },
    Definition {
        name: NameId,
        level_params: Vec<NameId>,
        ty: ExprId,
        value: ExprId,
        reducible: bool,
    },
    Unsupported { tag: String },
}
```

Binder names and binder-info fields are parsed but deliberately excluded from
these semantic nodes.

- [ ] **Step 5: Verify and commit**

Run: `cd metatron-kernel && cargo test`.

Expected: all tests pass. Commit message:
`feat(kernel): add sparse typed syntax stores`.

### Task 3: Arena 3.1.0 streaming parser and resolution gate

**Files:**
- Create: `metatron-kernel/src/parser.rs`
- Create: `metatron-kernel/tests/parser.rs`
- Create: `metatron-kernel/tests/fixtures/sparse-name-index.ndjson`
- Create: `metatron-kernel/tests/fixtures/level-index-out-of-order.ndjson`
- Create: `metatron-kernel/tests/fixtures/unsupported-inductive.ndjson`
- Modify: `metatron-kernel/src/lib.rs`
- Modify: `metatron-kernel/src/main.rs`

**Interfaces:**
- Produces: `ParsedExport { meta, names, levels, exprs, declarations }`.
- Produces: `parse<R: BufRead>(reader: R) -> Result<ParsedExport, ParseError>`.
- Produces: `ParsedExport::resolve() -> Result<ResolvedExport, ParseError>`.
- Consumes: syntax and IDs from Task 2.

- [ ] **Step 1: Copy the two exact upstream static fixtures**

Copy byte-for-byte from the pinned Arena SHA:

- `tests/other/sparse-name-index.ndjson`;
- `tests/other/level-index-out-of-order.ndjson`.

The files are external contract fixtures, not checker source.

- [ ] **Step 2: Write failing parser tests**

```rust
#[test]
fn parses_sparse_name_index() {
    let export = parse_fixture("sparse-name-index.ndjson").unwrap();
    assert!(export.names.contains(NameId(2)));
    assert!(!export.names.contains(NameId(1)));
}

#[test]
fn resolves_forward_referenced_levels() {
    let export = parse_fixture("level-index-out-of-order.ndjson")
        .unwrap()
        .resolve()
        .unwrap();
    assert_eq!(export.levels.len(), 3);
}

#[test]
fn missing_reference_is_malformed_not_unknown() {
    let err = parse_bytes(MISSING_LEVEL).unwrap().resolve().unwrap_err();
    assert!(matches!(err, ParseError::MissingLevel(LevelId(99))));
}
```

- [ ] **Step 3: Verify RED**

Run: `cd metatron-kernel && cargo test --test parser`

Expected: FAIL because `parser` does not exist.

- [ ] **Step 4: Implement line-by-line JSON parsing**

Parse one `serde_json::Value` per line. Require the first record to contain a
format-3.1.0-compatible `meta`. Recognize `in`, `il`, `ie`, `axiom`, and `def`
records needed by G0–G2. Preserve every other declaration tag as
`Declaration::Unsupported`; an unknown structural table record is malformed.
Resolution walks references after the stream is read, so level 1 may refer to
level 2 declared on the previous line without relying on numeric order.

- [ ] **Step 5: Make `run` distinguish parse error from semantic unknown**

`run` returns `Error` on `ParseError` and `Unknown` on a successfully resolved
export until Task 7 adds checking.

- [ ] **Step 6: Verify and commit**

Run:

```bash
cd metatron-kernel
cargo test
cargo run --quiet < tests/fixtures/sparse-name-index.ndjson
test $? -eq 2
```

Expected: tests pass and the parser-only stream exits 2. Commit message:
`feat(kernel): parse and resolve Arena format 3.1.0`.

### Task 4: Minimal exact universe algebra

**Files:**
- Create: `metatron-kernel/src/level.rs`
- Create: `metatron-kernel/tests/level.rs`
- Modify: `metatron-kernel/src/lib.rs`

**Interfaces:**
- Produces: owned `LevelTerm::{Zero, Succ, Max, IMax, Param}`.
- Produces: `instantiate_level(LevelId, substitution) -> Result<LevelTerm, LevelError>`.
- Produces: `level_equal(lhs, rhs, budget) -> Judgment<()>`.
- Produces: `level_imax(lhs, rhs) -> LevelTerm` with only syntactically warranted simplifications.

- [ ] **Step 1: Write failing equality and unknown tests**

```rust
#[test]
fn max_is_commutative_and_idempotent() {
    let u = LevelTerm::param("u");
    let v = LevelTerm::param("v");
    assert!(level_equal(max(u.clone(), v.clone()), max(v, u), 64).is_proven());
    assert!(level_equal(max(u.clone(), u.clone()), u, 64).is_proven());
}

#[test]
fn unresolved_imax_does_not_guess() {
    let u = LevelTerm::param("u");
    let v = LevelTerm::param("v");
    assert!(level_equal(imax(u.clone(), v.clone()), max(u, v), 64).is_unknown());
}

#[test]
fn imax_with_successor_right_is_max() {
    let u = LevelTerm::param("u");
    let v1 = succ(LevelTerm::param("v"));
    assert!(level_equal(imax(u.clone(), v1.clone()), max(u, v1), 64).is_proven());
}
```

- [ ] **Step 2: Verify RED**

Run: `cd metatron-kernel && cargo test --test level`

Expected: FAIL because `level` does not exist.

- [ ] **Step 3: Implement canonical max/successor algebra**

Flatten `Max`, collect each parameter's greatest successor offset plus the
greatest constant, sort parameter names, and rebuild a canonical comparison
key. Reduce `IMax(_, Zero)` to `Zero` and `IMax(u, Succ(v))` to `Max(u,
Succ(v))`. Leave every other `IMax` as an unresolved guarded node and return
unknown when equality requires a case split not yet implemented.

- [ ] **Step 4: Add budget and 26-parameter non-explosion test**

Construct two equal max expressions over 26 parameters in reverse order and
require equality to finish under a 256-step budget. This catches accidental
Boolean enumeration.

- [ ] **Step 5: Verify and commit**

Run: `cd metatron-kernel && cargo test`.

Expected: all tests pass. Commit message:
`feat(kernel): add conservative universe equality`.

### Task 5: Explicit closure machine and guarded reduction

**Files:**
- Create: `metatron-kernel/src/value.rs`
- Create: `metatron-kernel/src/machine.rs`
- Create: `metatron-kernel/tests/machine.rs`
- Modify: `metatron-kernel/src/lib.rs`

**Interfaces:**
- Produces: `Closure { expr: ExprId, env: EnvFrame }`.
- Produces: immutable `EnvFrame::{Empty, Extend}`.
- Produces: `Value::{Sort, Pi, Lam, Neutral}` and neutral application spines.
- Produces: `Machine::expose(closure, transparency, budget) -> Judgment<Value>`.
- Produces: transition witnesses `Beta`, `Zeta`, `Delta`, and `Rigid`.

- [ ] **Step 1: Write failing beta, zeta, and cycle tests**

```rust
#[test]
fn beta_uses_explicit_environment_extension() {
    let fixture = Fixture::identity_application();
    let result = fixture.machine().expose(fixture.root(), Transparency::Reducible, 64);
    assert_eq!(result.proven_value(), Some(fixture.argument_value()));
}

#[test]
fn zeta_uses_let_value_without_substitution_copy() {
    let fixture = Fixture::let_identity();
    assert!(fixture.machine().expose(fixture.root(), Transparency::Reducible, 64).is_proven());
}

#[test]
fn cyclic_delta_returns_unknown() {
    let fixture = Fixture::cyclic_constants();
    assert!(fixture.machine().expose(fixture.root(), Transparency::Reducible, 16).is_unknown());
}
```

- [ ] **Step 2: Verify RED**

Run: `cd metatron-kernel && cargo test --test machine`

Expected: FAIL because the machine does not exist.

- [ ] **Step 3: Implement the least transition machine**

Use `Rc`-backed immutable environment frames and values for G2. Do not add a
custom arena, interner, read-set quotient, or cache. Record the transition kind
on each proven exposure. Track visited `(AuthorityId, ExprId, EnvFrameId)`
states and remaining steps. Cycles and exhausted steps return a residual.

- [ ] **Step 4: Verify and commit**

Run: `cd metatron-kernel && cargo test`.

Expected: all tests pass. Commit message:
`feat(kernel): add explicit guarded reduction machine`.

### Task 6: Bidirectional inference and relational conversion

**Files:**
- Create: `metatron-kernel/src/judgment.rs`
- Create: `metatron-kernel/src/environment.rs`
- Create: `metatron-kernel/src/typecheck.rs`
- Create: `metatron-kernel/src/convert.rs`
- Create: `metatron-kernel/tests/typecheck.rs`
- Create: `metatron-kernel/tests/convert.rs`
- Modify: `metatron-kernel/src/lib.rs`

**Interfaces:**
- Produces: `Judgment<T>` with warrant, obstruction, and residual IDs.
- Produces: immutable `Environment` with monotone `AuthorityId`.
- Produces: `TypeChecker::infer`, `check`, and `convert`.
- Consumes: Tasks 2, 4, and 5.

- [ ] **Step 1: Write failing inference tests**

Cover literal hand-built fixtures for:

- `Sort u : Sort (succ u)`;
- Pi sort is `imax` of domain and codomain sorts;
- annotated identity lambda inference;
- identity application checking;
- let inference;
- unbound `BVar(0)` is refuted.

Each expectation is a hand-written value, not computed by a helper that shares
the implementation logic.

- [ ] **Step 2: Verify inference RED**

Run: `cd metatron-kernel && cargo test --test typecheck`

Expected: FAIL because `TypeChecker` does not exist.

- [ ] **Step 3: Implement inference and checking for the G2 fragment**

Context entries carry both the fresh neutral value and its established type.
Application checking exposes the function type to Pi, infers the argument, and
calls conversion. Lambda and Pi extend the context with a fresh neutral.
Unsupported expression variants return unknown.

- [ ] **Step 4: Write failing conversion tests**

Cover syntactic identity, beta, zeta, reducible delta, rigid Pi comparison,
unequal sorts, and budget exhaustion. The unequal-sort test is refuted only
when `level_equal` establishes inequality inside the supported algebra;
unresolved `imax` remains unknown.

- [ ] **Step 5: Verify conversion RED**

Run: `cd metatron-kernel && cargo test --test convert`

Expected: FAIL because relational conversion does not exist.

- [ ] **Step 6: Implement guarded relational conversion**

Use a worklist of value pairs and a visited set keyed by authority, context
support, subjects, and transparency. Try syntactic/rigid comparison before
requesting reduction transitions. Never convert an unknown reduction result
into refutation.

- [ ] **Step 7: Verify and commit**

Run: `cd metatron-kernel && cargo test`.

Expected: all tests pass. Commit message:
`feat(kernel): check the minimal dependent core`.

### Task 7: Declaration checking and end-to-end Arena verdicts

**Files:**
- Create: `metatron-kernel/src/checker.rs`
- Create: `metatron-kernel/tests/end_to_end.rs`
- Create: `metatron-kernel/tests/fixtures/bad-unbound-axiom.ndjson`
- Create: `metatron-kernel/tests/fixtures/good-beta-definition.ndjson`
- Modify: `metatron-kernel/src/lib.rs`
- Modify: `metatron-kernel/src/main.rs`

**Interfaces:**
- Produces: `check_export(ResolvedExport, Limits) -> Verdict`.
- Produces: one sequential authority extension per established declaration.

- [ ] **Step 1: Write failing end-to-end verdict tests**

```rust
#[test]
fn sparse_name_axiom_is_accepted() {
    assert_eq!(run_fixture("sparse-name-index.ndjson"), Verdict::Accept);
}

#[test]
fn out_of_order_level_axiom_is_accepted() {
    assert_eq!(run_fixture("level-index-out-of-order.ndjson"), Verdict::Accept);
}

#[test]
fn unbound_axiom_type_is_rejected() {
    assert_eq!(run_fixture("bad-unbound-axiom.ndjson"), Verdict::Reject);
}

#[test]
fn unsupported_inductive_is_unknown() {
    assert_eq!(run_fixture("unsupported-inductive.ndjson"), Verdict::Unknown);
}
```

- [ ] **Step 2: Verify RED**

Run: `cd metatron-kernel && cargo test --test end_to_end`

Expected: FAIL because `check_export` does not exist.

- [ ] **Step 3: Implement sequential declaration checking**

For an axiom, establish that its type has a sort before extending authority.
For a definition, establish that the declared type has a sort, then check the
value against it before extension. Stop on first reject, unknown, or error.
Do not install a declaration before it is checked; this prevents self-proof.

- [ ] **Step 4: Verify CLI exit behavior**

Run each fixture through `cargo run --quiet --release` and assert exit 0, 1,
or 2 exactly. Capture stderr only for diagnostics; no test asserts diagnostic
wording.

- [ ] **Step 5: Verify and commit**

Run:

```bash
cd metatron-kernel
cargo test --release
python -m unittest discover -s tests_py -p 'test_*.py' -v
python scripts/check_ledger.py
```

Expected: all tests pass. Commit message:
`feat(kernel): qualify G2 end-to-end verdicts`.

### Task 8: Freeze residual G2-001 and add promoted-judgment experiment

**Files:**
- Create: `metatron-kernel/src/capability.rs`
- Create: `metatron-kernel/tests/capability.rs`
- Create: `metatron-kernel/evidence/residuals/G2-001/fixture.ndjson`
- Create: `metatron-kernel/evidence/residuals/G2-001/protocol.json`
- Modify: `metatron-kernel/evidence/ledger.jsonl`
- Modify: `metatron-kernel/evidence/LEDGER.md`

**Interfaces:**
- Produces: `JudgmentKey` including operation, authority, support, subjects,
  transparency, and semantic epoch.
- Produces: `CapabilityBank::lookup_proven` and `insert_proven`.
- Produces: replayable `ExpansionRecipe` over trusted operations.

- [ ] **Step 1: Measure before adding the bank**

Instrument trusted conversion calls on `good-beta-definition.ndjson`. Freeze
the exact repeated positive obligation as G2-001. If no positive obligation
repeats, record `UNKNOWN_NO_RECURRENCE`, skip capability implementation, and
advance to Task 9 with no bank.

- [ ] **Step 2: If recurrence exists, write failing authority tests**

```rust
#[test]
fn proven_obligation_reuses_under_exact_authority() { /* one trusted replay */ }

#[test]
fn different_authority_cannot_reuse_capability() { /* lookup misses */ }

#[test]
fn unknown_and_refuted_judgments_are_not_promoted() { /* bank stays empty */ }
```

- [ ] **Step 3: Verify RED**

Run: `cd metatron-kernel && cargo test --test capability`.

Expected: FAIL because the capability bank does not exist.

- [ ] **Step 4: Implement only positive exact-authority promotion**

Use `HashMap<JudgmentKey, ProvenCapability>`. Each value stores the result,
warrant, expansion recipe, dependencies, and qualification scope. Do not add
negative caching, cross-authority reuse, direct maps, or persistence.

- [ ] **Step 5: Run causal ablation**

Run the frozen fixture once with the bank enabled and once with lookup disabled
but all control flow preserved. Require identical verdicts and fewer trusted
conversion calls in the enabled arm. Otherwise reject the mechanism and keep
the code out of the retained head.

- [ ] **Step 6: Verify, record, and commit**

Update G2-001 with the exact result and decision. Commit message on retention:
`feat(kernel): promote recurring proven judgments`; on rejection:
`evidence(kernel): reject G2 judgment promotion`.

### Task 9: Current-Arena qualification workflow and checkpoint

**Files:**
- Create: `.github/workflows/metatron-kernel-genesis-g2.yml`
- Create: `metatron-kernel/scripts/qualify_arena.py`
- Create: `metatron-kernel/tests_py/test_qualify_arena.py`
- Create: `metatron-kernel/evidence/runs/README.md`
- Modify: `metatron-kernel/evidence/ledger.jsonl`
- Modify: `metatron-kernel/evidence/LEDGER.md`

**Interfaces:**
- Produces: deterministic JSON qualification summary keyed by exact candidate
  and Arena SHAs.
- Consumes: the two pinned upstream static NDJSON fixtures plus local good,
  bad, and unsupported fixtures.

- [ ] **Step 1: Write failing qualification-summary tests**

The parser must classify process exits as accept/reject/unknown/error, compare
them to expected outcomes, reject missing cases, and emit ordered JSON. Include
a test proving that an unknown on a required-good case is incomplete rather
than incorrect.

- [ ] **Step 2: Verify RED**

Run: `cd metatron-kernel && python -m unittest tests_py.test_qualify_arena -v`.

Expected: import failure for `scripts.qualify_arena`.

- [ ] **Step 3: Implement the qualification driver**

The driver accepts `--checker`, `--arena`, `--candidate-sha`, and
`--arena-sha`. It runs only the declared G2 suite, writes counts and each exact
case result, and exits nonzero on any incorrect or error result.

- [ ] **Step 4: Add GitHub Actions qualification**

The workflow checks out the candidate, installs stable Rust, runs formatting,
Clippy with warnings denied, release tests, ledger tests, clones upstream Arena
at the pinned SHA, checks fixture byte hashes, runs the G2 suite, writes a JSON
attestation, and uploads it as an artifact. It does not open or update an Arena
PR.

- [ ] **Step 5: Push and inspect the exact-head run**

Push the commit to `metatron-kernel-genesis-v1`. Record the workflow run ID,
job ID, candidate SHA, Arena SHA, artifact ID, verdict counts, and result in the
ledger. A green earlier SHA does not qualify a later evidence-only commit.

- [ ] **Step 6: Run final local checks and commit evidence closure**

Run:

```bash
cd metatron-kernel
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test --release
python -m unittest discover -s tests_py -p 'test_*.py' -v
python scripts/check_ledger.py
```

Expected: every command exits 0. Commit message:
`evidence(kernel): record G2 external qualification`.

### Task 10: Freeze the first post-G2 Arena residual

**Files:**
- Create: `metatron-kernel/evidence/residuals/G3-001/fixture.ndjson`
- Create: `metatron-kernel/evidence/residuals/G3-001/protocol.json`
- Modify: `metatron-kernel/evidence/ledger.jsonl`
- Modify: `metatron-kernel/evidence/LEDGER.md`

**Interfaces:**
- Produces: the exact next residual; produces no new semantic mechanism.

- [ ] **Step 1: Run the next upstream tests in tutorial order**

Use the Arena tutorial ordering. Stop at the first case whose result is unknown
or wrong after G2. Preserve its exact NDJSON bytes and upstream provenance.

- [ ] **Step 2: Classify the residual**

Choose exactly one primary class: parser/format, application inference,
conversion, universe equality, environment representation, proof irrelevance,
eta, inductive, recursor, projection, quotient, literal, session/memory, or
resource.

- [ ] **Step 3: Freeze a deciding protocol before implementation**

The protocol names the least candidate capability, strongest competing
explanation, semantic falsifier, causal ablation, protected suite, and retired
instruction measurement plan. If multiple least repairs remain tied and no
small separator resolves them, record `UNKNOWN_CHOICE` and stop for the
architectural decision.

- [ ] **Step 4: Commit and checkpoint**

Commit message: `evidence(kernel): freeze first post-G2 residual`.

The next implementation plan is written from this residual. No G3 production
code is added in this plan.
