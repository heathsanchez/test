# G11 and Shared Closed-Inductive Derivation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Qualify exact `TwoBool`, factor G9/G10/G11 through one internal derivation engine without changing their verdict frontier, prove the smallest portable promotion theorem, freeze tutorial 039, and add diagnostic-only operation measurement.

**Architecture:** Keep external admission as three explicit shape classifiers. Each classifier produces a deep `DerivedInductive` witness containing the exact type, constructor, recursor, and rule obligations; one shared validator checks and atomically compiles that witness to opaque runtime signatures. The pre-refactor handlers remain available under tests as an oracle until an exhaustive mutation corpus establishes verdict equivalence.

**Tech Stack:** Rust 2024, Lean 4.29.1, Python 3.12, Arena NDJSON 3.1, GitHub Actions, Valgrind/Callgrind when available.

**Spec:** User directive dated 2026-09-22 in the active task; governing architecture remains `docs/architecture/metatron-kernel-genesis-v1.md`.

## Global Constraints

- Arena authority is exactly `f5e1bce6e2dc9c60479b3001b76e01722b403799`.
- `UNKNOWN` is preserved for every shape outside G9/G10/G11 and for budget or unresolved semantic boundaries.
- G11 admits only one closed safe nonrecursive, nonindexed, nonparameterized `Type` structure with one constructor and exactly two fields.
- Constructors and recursors compile to opaque signatures only; no iota, projections, or eta.
- The shared engine must not broaden the accepted/rejected domain of the three sealed handlers.
- Formal results warrant only this promotion boundary, not the whole Rust checker.
- Performance claims require same-cohort retired instructions; deterministic counters and Callgrind are diagnostic only.
- No pull request to the official Arena repository.

## Review Focus

- A malformed constructor result that mentions the wrong inductive must reject.
- Reordered or duplicated fields/minors/rules must reject rather than gain authority.
- A failed block must publish none of its staged signatures.
- One-parameter, indexed, recursive, unsafe, nested, or mutual blocks must remain `UNKNOWN`.
- Refactoring must preserve every verdict in the exact fixtures plus the deterministic perturbation corpus.

---

### Task 1: Seal exact-head evidence and freeze G11

**Files:**
- Modify: `metatron-kernel/evidence/ledger.jsonl`
- Modify: `metatron-kernel/evidence/LEDGER.md`
- Create: `metatron-kernel/evidence/external/78a53e3e/qualification.json`
- Create: `metatron-kernel/evidence/residuals/G11-001/fixture.ndjson`
- Create: `metatron-kernel/evidence/residuals/G11-001/protocol.json`

**Interfaces:**
- Consumes: run `35653364302`, job `106510875913`, artifact `10662982778`, digest `sha256:c8fc2be20ec01c957005cdf7047500fab4f37f453f588629587e84ed63e087e4`.
- Produces: immutable G11 fixture hash `91a1f7379e22ebbec710ce6b43b7e0750be258ace8fc22d0b889fb76b57010de` and recorded 37/37 external qualification.

- [ ] Record exact-head run metadata and the `37 matched, 0 incorrect` assertion.
- [ ] Copy tutorial 038 bytes verbatim through `apply_patch` and verify the hash.
- [ ] Record the G11 obstruction, competing explanation, falsifier, ablation, protected suite, and performance status.
- [ ] Run `python scripts/check_ledger.py`; expect success.
- [ ] Commit evidence.

### Task 2: Exact TwoBool RED→GREEN

**Files:**
- Modify: `metatron-kernel/tests/end_to_end.rs`
- Modify: `metatron-kernel/src/checker.rs`
- Modify: `metatron-kernel/src/environment.rs`
- Modify: `metatron-kernel/scripts/qualify_tutorial.py`
- Modify: `.github/workflows/metatron-kernel-genesis-g2.yml`

**Interfaces:**
- Consumes: the frozen G11 block.
- Produces: a validated opaque type/constructor/recursor transaction for the exact one-constructor/two-field structure.

- [ ] Add failing exact-positive, constructor-owner/result/field-count/index, recursor motive/minor/rule/RHS, opacity, atomicity, and unsupported-shape tests.
- [ ] Run focused tests; expect exact positive `UNKNOWN` and supported-shape perturbations not yet `REJECT`.
- [ ] Implement the smallest exact structural derivation and staged semantic checks.
- [ ] Run focused tests; expect all pass and no iota/projection/eta capability.
- [ ] Extend direct tutorial qualification through 038 and run it locally; expect 38 matched.
- [ ] Run the full protected Rust/Python/Lean/Clippy/ledger suite.
- [ ] Commit G11 implementation.

### Task 3: Shared closed-nonrecursive derivation engine

**Files:**
- Create: `metatron-kernel/src/inductive.rs`
- Modify: `metatron-kernel/src/lib.rs`
- Modify: `metatron-kernel/src/checker.rs`
- Create: `metatron-kernel/tests/inductive_equivalence.rs`

**Interfaces:**
- Consumes: G9/G10/G11 classifiers and opaque `ConstantDecl` constructors.
- Produces: `derive_supported_closed_block(...) -> Judgment<DerivedInductive>` and `validate_and_install_derived(...) -> Result<Environment, Verdict>`.

- [ ] Freeze the legacy handlers behind a test-only oracle.
- [ ] Add a failing causal-equivalence test over exact cases, all named falsifiers, single-field mutations, truncations, and unsupported neighboring shapes.
- [ ] Move shared metadata derivation, signature validation, staging, and installation into `inductive.rs`; keep three explicit external shape classifiers.
- [ ] Run the equivalence corpus; require identical `Accept/Reject/Unknown/Error` vectors.
- [ ] Remove production duplication only after equivalence passes.
- [ ] Run the full protected suite and commit the refactor.

### Task 4: IdealLean promotion warrant

**Files:**
- Modify: `metatron-kernel/formal/IdealLean/Semantics.lean`
- Modify: `metatron-kernel/formal/IdealLeanTests.lean`
- Modify: `metatron-kernel/formal/README.md`

**Interfaces:**
- Consumes: a portable `DerivedInductiveChecks` premise independent of Rust representation.
- Produces: theorem that appending opaque validated type/constructor/recursor declarations preserves an abstract environment-validity invariant and exposes no bodies.

- [ ] Add failing `#check` declarations for opaque-body and validity-preservation theorems.
- [ ] Define portable inductive signature candidates and promotion checks without mentioning Rust APIs.
- [ ] Prove every promoted declaration has no body and sequential installation preserves validity from the supplied validation premises.
- [ ] Run `lake build`; expect success.
- [ ] Record the theorem names as a narrow G9/G10/G11 warrant and commit.

### Task 5: Freeze tutorial 039

**Files:**
- Create: `metatron-kernel/evidence/residuals/G12-001/fixture.ndjson`
- Create: `metatron-kernel/evidence/residuals/G12-001/protocol.json`
- Modify: `metatron-kernel/evidence/ledger.jsonl`
- Modify: `metatron-kernel/evidence/LEDGER.md`

**Interfaces:**
- Consumes: ordered exact scan after the sealed 001–038 prefix.
- Produces: the exact first residual at tutorial 039; no parameter support.

- [ ] Run the ordered scan and require 001–038 exact.
- [ ] Freeze case 039 bytes/hash and record the obstruction before choosing a mechanism.
- [ ] Verify any parameterized neighboring shape remains `UNKNOWN`.
- [ ] Commit the residual.

### Task 6: Diagnostic operation counters and Callgrind baseline

**Files:**
- Create: `metatron-kernel/src/diagnostics.rs`
- Modify: `metatron-kernel/src/lib.rs`
- Create: `metatron-kernel/scripts/diagnose_operations.py`
- Create: `metatron-kernel/evidence/performance/g11-sealed/README.md`
- Modify: `metatron-kernel/evidence/ledger.jsonl`

**Interfaces:**
- Consumes: sealed checker and exact frozen cohort.
- Produces: deterministic diagnostic counters and optional Callgrind output, never semantic cache authority.

- [ ] Add failing tests that diagnostic mode leaves verdicts byte-for-byte unchanged and counters deterministic across repeated runs.
- [ ] Implement feature-gated/thread-local counters outside semantic decisions.
- [ ] Run the exact cohort twice and compare counter JSON exactly.
- [ ] If `valgrind` exists, capture an identical-build Callgrind baseline; otherwise record `UNAVAILABLE`.
- [ ] Record performance decision `UNKNOWN_NO_SAME_COHORT_RETIRED_INSTRUCTIONS` and commit.

### Task 7: External qualification and final review

**Files:**
- Modify: G9/G10/G11 ledger records with the new run only after success.

**Interfaces:**
- Consumes: pushed exact source head.
- Produces: external run/job/artifact/digest for the 001–038 prefix and formal build.

- [ ] Re-run complete local verification and inspect every result.
- [ ] Push the branch checkpoint without opening an Arena PR.
- [ ] Capture exact-head CI and artifact metadata.
- [ ] Update warrants and performance status without overclaiming.
- [ ] Perform a whole-branch review focused on authority broadening, transaction atomicity, de Bruijn derivation, and theorem scope.
