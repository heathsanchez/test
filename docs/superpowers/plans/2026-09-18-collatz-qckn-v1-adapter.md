# Collatz QCKN V1 Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and qualify a thin QCKN V1 runtime around the existing exact Collatz engines, demonstrating bounded causal promotion, canonical restart, prospective zero-search reuse, matched controls, and causal ablation without changing the underlying Collatz mathematics.

**Architecture:** The implementation is a small Python package `collatz_qckn` whose typed records, authority, causal ledger, compiled present, adapter, policy, and qualification runner wrap the existing `experiments/` engines. Domain proposal and authority are separate; only independently verified promotion events enter the canonical CompiledPresent. The end-to-end qualification uses a small sealed training/future split and emits deterministic machine-readable evidence for COLD, WARM, RAW_HISTORY, SHAM, and ANCESTOR_ABLATION.

**Tech Stack:** Python 3 standard library; existing exact Collatz experiment modules; `unittest`; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-18-collatz-qckn-domain-adapter-design.md`

## Global Constraints

- Existing exact Collatz arithmetic engines remain authoritative and are not semantically rewritten.
- Proposal MUST NOT equal promotion.
- Promotion requires an independent replay verifier under an explicit contract.
- Active memory is separable from raw history.
- Canonical CompiledPresent restart must reproduce active semantics without replaying discovery.
- Revocation must survive restart and disable dependent capabilities.
- `UNKNOWN_SEARCH` must not be silently upgraded to `UNKNOWN_EXPRESSIVITY`.
- Same-identity conflicting active payloads must cause explicit compilation failure.
- Qualification claims are bounded developmental claims and MUST NOT claim a proof of Collatz.
- The mandatory causal-control pattern is COLD, WARM, RAW_HISTORY, SHAM, ANCESTOR_ABLATION.
- Test-first implementation; each implementation task begins with a failing test.

---

## File Structure

- `collatz_qckn/__init__.py` — public package surface.
- `collatz_qckn/types.py` — immutable typed outcomes, obligations, capabilities, evidence, costs, and ledger events.
- `collatz_qckn/authority.py` — independent exact replay verification and authority snapshot.
- `collatz_qckn/ledger.py` — immutable promotion/revocation history and deterministic active projection.
- `collatz_qckn/compiled_present.py` — canonical active serialization, parsing, digest, dependency validation.
- `collatz_qckn/adapter.py` — exact forward-descent macro proposal/replay adapter over existing Collatz engines.
- `collatz_qckn/mda.py` — typed intervention licensing and deterministic prospective selection.
- `collatz_qckn/runner.py` — bounded generation/control qualification harness.
- `tests/test_collatz_qckn_types.py` — typed-record and identity tests.
- `tests/test_collatz_qckn_authority.py` — proposal/verification/stale/invalid tests.
- `tests/test_collatz_qckn_ledger.py` — causal promotion/revocation/conflict/dependency tests.
- `tests/test_collatz_qckn_compiled_present.py` — canonical serialization/restart tests.
- `tests/test_collatz_qckn_adapter.py` — exact domain proposal/replay tests.
- `tests/test_collatz_qckn_mda.py` — typed routing and uncertainty tests.
- `tests/test_collatz_qckn_runner.py` — matched-control and end-to-end causal reuse tests.
- `.github/workflows/collatz-qckn-v1-qualification.yml` — deterministic CI qualification.
- `docs/collatz-qckn-v1-qualification.md` — claim boundary, evidence schema, and qualification interpretation.

### Task 1: Typed constitutional records and semantic identity

**Files:**
- Create: `collatz_qckn/__init__.py`
- Create: `collatz_qckn/types.py`
- Create: `tests/test_collatz_qckn_types.py`

**Interfaces:**
- Produces: `Outcome`, `Intervention`, `Obligation`, `Capability`, `VerificationEvidence`, `CostRecord`, `LedgerEvent`, `canonical_json()`, `digest_payload()`.

- [ ] **Step 1: Write failing tests** covering immutable records, deterministic canonical JSON, semantic capability identity, and conflicting payload distinction.

- [ ] **Step 2: Run** `python -m unittest tests.test_collatz_qckn_types -v` and verify import/definition failures.

- [ ] **Step 3: Implement minimal immutable dataclasses and enums.** Capability identity is derived from kind, anchors, affine parameters, guard digest, and contract digest; provenance and cost do not alter semantic identity.

- [ ] **Step 4: Re-run the test module and verify PASS.**

- [ ] **Step 5: Commit** with message `Add typed Collatz QCKN records`.

### Task 2: Independent authority and exact forward-macro verification

**Files:**
- Create: `collatz_qckn/authority.py`
- Create: `collatz_qckn/adapter.py`
- Create: `tests/test_collatz_qckn_authority.py`
- Create: `tests/test_collatz_qckn_adapter.py`

**Interfaces:**
- Consumes: typed records from Task 1 and existing `experiments/collatz_q0_coalescence_component_audit.py`, `experiments/collatz_q0_rigid_recharge_audit.py`.
- Produces: `CollatzAdapter.propose_forward_macro(...)`, `CollatzAdapter.apply_capability(...)`, `Authority.verify(...)`, `AuthoritySnapshot`.

- [ ] **Step 1: Write failing tests** showing a proposal is inactive/unverified, a valid exact episode macro verifies, an altered word fails replay, and a stale contract/authority digest fails.

- [ ] **Step 2: Run authority/adapter tests and verify FAIL.**

- [ ] **Step 3: Implement the adapter as a wrapper around existing exact episode replay.** It must calculate the claimed path minimum and common endpoint from the existing engines rather than trust proposal fields.

- [ ] **Step 4: Implement authority verification** returning `VerificationEvidence(valid=True,...)` only when scope, contract, guard, exact replay, and claimed protected consequence all match.

- [ ] **Step 5: Re-run tests and verify PASS.**

- [ ] **Step 6: Commit** `Add independent Collatz capability authority`.

### Task 3: Causal ledger, promotion, revocation, dependency semantics

**Files:**
- Create: `collatz_qckn/ledger.py`
- Create: `tests/test_collatz_qckn_ledger.py`

**Interfaces:**
- Consumes: `Capability`, `VerificationEvidence`, `LedgerEvent`.
- Produces: `CausalLedger.promote()`, `revoke()`, `active_capabilities()`, `events()`.

- [ ] **Step 1: Write failing tests** for proposal-not-active, verified promotion, invalid promotion rejection, causal revocation, dependency invalidation, same-ID conflicting payload refusal, and deterministic event ordering.

- [ ] **Step 2: Run ledger tests and verify FAIL.**

- [ ] **Step 3: Implement immutable content-addressed promotion/revocation events.** Promotion stores the verified payload digest; revocation names the observed promoted event(s); active projection excludes revoked capabilities and recursively excludes capabilities with inactive dependencies.

- [ ] **Step 4: Implement explicit `LedgerConflict` for same semantic identity/different active payload.**

- [ ] **Step 5: Re-run tests and verify PASS.**

- [ ] **Step 6: Commit** `Add causal Collatz capability ledger`.

### Task 4: Canonical CompiledPresent and exact restart

**Files:**
- Create: `collatz_qckn/compiled_present.py`
- Create: `tests/test_collatz_qckn_compiled_present.py`

**Interfaces:**
- Consumes: active capabilities from `CausalLedger`.
- Produces: `CompiledPresent.compile(ledger)`, `to_text()`, `from_text()`, `digest`, `capabilities`.

- [ ] **Step 1: Write failing tests** for insertion-order independence, parse/text roundtrip, stable digest, raw-history exclusion, dependency validation, and revoked capability absence after restart.

- [ ] **Step 2: Run tests and verify FAIL.**

- [ ] **Step 3: Implement canonical JSON serialization** with sorted capabilities/dependencies and explicit schema/version/contract/authority fields.

- [ ] **Step 4: Implement parser and deterministic digest.** Parsing validates identity, dependencies, duplicates, and conflicts before exposing active capabilities.

- [ ] **Step 5: Re-run tests and verify PASS.**

- [ ] **Step 6: Commit** `Add canonical Collatz CompiledPresent`.

### Task 5: Typed MDA routing and uncertainty preservation

**Files:**
- Create: `collatz_qckn/mda.py`
- Create: `tests/test_collatz_qckn_mda.py`

**Interfaces:**
- Produces: `licensed_interventions(outcome)`, `select_intervention(outcome, candidates)`.

- [ ] **Step 1: Write failing tests** asserting certified results license COMPILE, RIGID residual licenses CONSTRUCT/VERIFY/RESTRUCTURE, UNKNOWN_SEARCH does not license EXPAND, and UNKNOWN_EXPRESSIVITY licenses EXPAND only with a matching completeness certificate.

- [ ] **Step 2: Run tests and verify FAIL.**

- [ ] **Step 3: Implement the frozen Collatz admissibility map and deterministic prospective-cost selector.**

- [ ] **Step 4: Re-run tests and verify PASS.**

- [ ] **Step 5: Commit** `Add typed Collatz MDA routing`.

### Task 6: Bounded acquisition, minimization, promotion, and restart fixture

**Files:**
- Modify: `collatz_qckn/adapter.py`
- Create: `collatz_qckn/runner.py`
- Create: `tests/test_collatz_qckn_runner.py`

**Interfaces:**
- Produces: `discover_forward_macros(training_sources,...)`, `promote_verified(...)`, `run_arm(...)`, `QualificationResult`.

- [ ] **Step 1: Write a failing sealed-split test** using a small deterministic training/future source set. The test must assert at least one candidate is independently verified/promoted and the serialized restarted WARM present produces at least one authoritative future hit without invoking discovery.

- [ ] **Step 2: Run the runner test and verify FAIL.**

- [ ] **Step 3: Implement bounded discovery by extracting forward q0 descent macros from training sources using existing episode engines.** Deduplicate by semantic identity before authority verification.

- [ ] **Step 4: Implement promotion and compile/restart fixture.**

- [ ] **Step 5: Implement WARM application as active-capability matching/replay only; it must expose a `discovery_calls` counter that remains zero for capability hits.**

- [ ] **Step 6: Re-run tests and verify PASS.**

- [ ] **Step 7: Commit** `Compile and restart verified Collatz macros`.

### Task 7: Matched causal controls

**Files:**
- Modify: `collatz_qckn/runner.py`
- Modify: `tests/test_collatz_qckn_runner.py`

**Interfaces:**
- Produces arms `COLD`, `WARM`, `RAW_HISTORY`, `SHAM`, `ANCESTOR_ABLATION`.

- [ ] **Step 1: Add failing tests** requiring: WARM has at least one authoritative zero-search hit; RAW_HISTORY cannot use uncompiled candidates as active capabilities; SHAM has matched count/shape but zero authoritative hits; ANCESTOR_ABLATION removes the promoted family and reproduces the cold active-capability behavior.

- [ ] **Step 2: Run and verify FAIL.**

- [ ] **Step 3: Implement the five arms with identical future obligations and explicit cost counters.** SHAM mutates contract/guard digests while preserving record count and approximate payload shape.

- [ ] **Step 4: Implement targeted family revocation through the causal ledger, recompile, restart, and rerun the future obligations.**

- [ ] **Step 5: Re-run tests and verify PASS.**

- [ ] **Step 6: Commit** `Add causal controls for Collatz compounding`.

### Task 8: Deterministic evidence certificate and CI qualification

**Files:**
- Modify: `collatz_qckn/runner.py`
- Modify: `tests/test_collatz_qckn_runner.py`
- Create: `.github/workflows/collatz-qckn-v1-qualification.yml`
- Create: `docs/collatz-qckn-v1-qualification.md`

**Interfaces:**
- Produces: CLI `python -m collatz_qckn.runner --qualify` emitting canonical JSON plus a SHA-256 closure certificate.

- [ ] **Step 1: Write failing tests** asserting repeated qualification runs produce byte-identical evidence and identical certificate digests.

- [ ] **Step 2: Run full test suite and verify the deterministic-evidence test fails.**

- [ ] **Step 3: Implement canonical evidence output** containing contract digest, authority digest, training/future source digests, CompiledPresent digest, per-arm search/acquisition/verification/hit/residual metrics, revocation event digest, and bounded claim text.

- [ ] **Step 4: Add the GitHub Actions workflow** to run all unit tests, the qualification CLI twice, compare outputs, reject `sorry/admit`-style placeholders in the new runtime, and upload the evidence artifact.

- [ ] **Step 5: Add qualification documentation** stating exactly what a green run establishes and explicitly stating that Collatz remains unproved.

- [ ] **Step 6: Run `python -m unittest discover -s tests -p 'test_collatz_qckn_*.py' -v` and `python -m collatz_qckn.runner --qualify` locally/CI and verify PASS.**

- [ ] **Step 7: Commit** `Qualify Collatz QCKN V1 causal reuse`.

### Task 9: Release audit against the approved specification

**Files:**
- Modify only if audit discovers a concrete defect.

**Interfaces:**
- Consumes: all prior tasks.
- Produces: one green release evidence point or an exact named residual.

- [ ] **Step 1: Run the complete test suite and qualification workflow.**

- [ ] **Step 2: Audit every approved-spec requirement against code/tests:** proposal boundary, authority, typed outcomes, uncertainty, causal history, active/raw separation, restart, revocation, conflicts, dependencies, five controls, deterministic evidence, claim boundary.

- [ ] **Step 3: Run targeted negative controls:** corrupt one capability payload, stale one contract digest, revoke one ancestor, reorder ledger insertion, and verify the expected explicit failures/semantic invariance.

- [ ] **Step 4: If all gates pass, freeze the evidence digest and document the bounded verdict. If a gate fails, retain the smallest exact RED and do not weaken the contract.**

- [ ] **Step 5: Commit** `Close Collatz QCKN V1 qualification`.
