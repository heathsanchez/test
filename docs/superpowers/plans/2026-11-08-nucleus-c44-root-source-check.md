# Nucleus C44 Root Source Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) for tracking.

**Goal:** Isolate the necessary source-typed first proof argument of n7's final `And.intro`, without changing any proof rule or original input.

**Architecture:** Reconstruct exact C37-qualified source plus C38/C39 diagnostic patches. Observe the inferred and expected type at the source-checked `ExprId(8804)` argument to `And.intro`, then preserve the proof verdict and a separate artifact.

**Tech Stack:** Rust 1.99.1, Python 3, GitHub Actions.

**Spec:** `experiments/nucleus-logos-support-20261108/c40-c42-evidence.md` on `research/nucleus-c40-c42-source-major-20261108` (root failure also shown by C43).

## Global Constraints

- Exact original n7 SHA-256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`.
- Selected 24 flags and 262,144 judgment steps unchanged; no inferred equality from a diagnostic.
- Selected independent checker and protected forged-proof results remain untouched.

## Review Focus

- The observer is absent from the pristine binary (RED).
- Altered source bytes must fail closed.
- The record must identify expression 8804 in source context zero; another ID is not evidence.
- Missing inferred-type records cannot be mistaken for a successful type-check.
- No flag-on ACCEPT can be promoted without full 403 protected qualification.

### Task 1: Observe the precise type-check premise

**Files:** `probe_c44_root_argument.py`, `test_c44_root_argument.py`, `c44-root-source-check.patch`, `metatron-kernel/src/typecheck.rs` (research extraction only).

**Interface:** `parse_events(stderr: bytes) -> dict`, records `NUCLEUS_C44_INFERRED_ARG` and `NUCLEUS_C44_ROOT_CHECK`.

- [x] Write parser and source-hash gates.
- [x] Run Python tests (3/3 pass) and witness RED on existing C38 compiled binary (missing observer).
- [x] Implement two opt-in, observer-only records for expression 8804, context zero.
- [x] Zero-fuzz dry-run of C44 patch on exact C37+C38+C39 source succeeds.

### Task 2: Compile and verify hosted evidence

**Files:** `.github/workflows/nucleus-c44-root-source.yml`.

**Interface:** `reports/c44-root-n7.json` and optional research-branch source-checked receipt.

- [ ] Compile Rust all targets and run native proof/forged controls.
- [ ] Validate immutable original and pristine RED, then run C44 GREEN.
- [ ] Independently inspect outcome and first failed semantic premise.
- [ ] If a proof-rule repair follows, create a separate RED-first protected test and 403-case qualification.
