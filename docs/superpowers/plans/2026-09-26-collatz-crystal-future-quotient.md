# Collatz Crystal Future-Quotient Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic separator-driven Collatz residual quotient compiler that emits either a checkable decreasing-rank certificate or an exact recurrent obstruction without conflating bounded closure with universal Collatz closure.

**Architecture:** Reuse the existing Final Proof Kernel, finite certificate interface, source-product semantics, and historical stateful-future algorithms. Keep discovery in Python and authority in exact replay + generated Lean certificate. Quotient identity is protected-future-relative and grows only by witnessed separators.

**Tech Stack:** Python 3.11 exact integers, Lean 4 pinned core, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-26-collatz-crystal-future-quotient-design.md`

## Global Constraints
- Work on `collatz-universal-source-product-v1`.
- Global Collatz status remains UNKNOWN unless universal normalization/progress and rank are independently certified.
- Do not revive rejected scalar ranks or finite-residue SCC claims.
- Do not use raw depth/rung/Q3/occurrence identity unless a future separator earns it.
- No `sorry/admit/axiom/unsafe` in generated/formal Collatz proof files.
- Deterministic evidence with explicit lineage and separator provenance.

## Review Focus
- Same protected future under different presentation coordinates must merge.
- Same coarse state with different protected futures must be split by a witnessed separator.
- A sampled empty kernel must remain labeled bounded when universal coverage is absent.
- A recurrent cell with no earned separator must be emitted, never hidden by synthetic identity.
- Generated rank must be checked against every emitted residual edge.

---

### Task 1: Exact protected-future quotient core

**Files:**
- Create: `experiments/collatz_crystal_future_quotient_v1.py`
- Create: `experiments/test_collatz_crystal_future_quotient_v1.py`

**Interfaces:**
- Produces `refine_future_quotient(nodes, succ, exits)`, `greatest_kernel(nodes, succ)`, `rank_if_acyclic(kernel_nodes, succ)`, and deterministic canonical serialization.

- [ ] Write failing tests for presentation-coordinate merge, exit distinction, recurrent-cycle detection, and rank validation on an acyclic residual graph.
- [ ] Run the focused unittest file and verify the new API is missing/failing for the intended reason.
- [ ] Implement the minimal quotient/kernel/rank functions with exact deterministic ordering.
- [ ] Run focused tests; then run the existing stateful-future unit tests as regression.
- [ ] Commit the independently testable quotient core.

### Task 2: Separator-driven refinement with provenance

**Files:**
- Modify: `experiments/collatz_crystal_future_quotient_v1.py`
- Modify: `experiments/test_collatz_crystal_future_quotient_v1.py`

**Interfaces:**
- Consumes the Task 1 graph API.
- Produces `compile_with_separators(occurrences, base_signature, separator_bank)` and a trace recording admitted/rejected separators and surviving SCC witnesses.

- [ ] Write failing tests where a coarse recurrent kernel is killed by a genuine future separator, and where an irrelevant coordinate is rejected.
- [ ] Verify RED.
- [ ] Implement smallest-separator admission: a coordinate is admitted only if it separates currently merged states with different protected successor/exit signatures.
- [ ] Add a failing test proving an unsplit recurrent cell is emitted as UNKNOWN rather than assigned occurrence identity.
- [ ] Implement obstruction emission and deterministic provenance.
- [ ] Run focused + stateful-future regressions and commit.

### Task 3: Bind the canonical Collatz residual adapter

**Files:**
- Modify: `experiments/collatz_crystal_future_quotient_v1.py`
- Modify: `experiments/test_collatz_crystal_future_quotient_v1.py`
- Read/reuse: `experiments/collatz_stateful_future_kernel_v0.py` semantics from its qualified branch and current `SourceProduct` definitions.

**Interfaces:**
- Produces a canonical occurrence schema containing source/end affine semantics, genuine exit flags, lawful successor identity, and earned separator coordinates (V3/V23/resource/source-endpoint fields) with provenance.

- [ ] Write a failing regression fixture reproducing the historical coarse CONTROL recurrence and V3/V23 kernel collapse from frozen evidence.
- [ ] Verify RED against the new adapter.
- [ ] Implement the adapter without copying presentation-only coordinates into base identity.
- [ ] Add negative tests ensuring depth/rung/occurrence id do not split otherwise identical futures.
- [ ] Run focused tests and compare the historical bounded verdict/certificate fields against the pinned evidence boundary; commit.

### Task 4: Emit and independently replay finite rank/cycle certificates

**Files:**
- Create: `formal/Collatz/CrystalFutureCertificate.lean`
- Create: `experiments/collatz_crystal_future_certificate_v1.py`
- Modify tests.

**Interfaces:**
- Python emits a finite model compatible with `CollatzFinal.FiniteResidualModel`, plus rank or recurrent cycle witness.
- Lean imports `Collatz.Certificate` and checks generated rank tables.

- [ ] Write failing Python tests for malformed rank, missing edge, and cycle-vs-rank disagreement.
- [ ] Verify RED.
- [ ] Implement deterministic certificate emission and independent Python replay.
- [ ] Add a tiny generated Lean fixture and compile it; ensure a deliberately invalid rank fails before restoring the valid fixture.
- [ ] Run Python tests + pinned Lean build + axiom/sorry audit; commit.

### Task 5: Universal-boundary manifest and hosted qualification

**Files:**
- Create: `evidence/collatz-crystal-future-quotient-v1/result.json`
- Create: `docs/collatz_crystal_future_quotient_v1.md`
- Create: `.github/workflows/collatz-crystal-future-quotient-v1.yml`
- Modify: `experiments/collatz_crystal_campaign_state_v1.json`

**Interfaces:**
- Emits one of `BOUNDED_EMPTY_KERNEL`, `EXACT_RECURRENT_OBSTRUCTION`, or `UNIVERSAL_RANK_CERTIFIED`; the last requires explicit normalization/progress proof references.

- [ ] Write the workflow gate so bounded empty-kernel evidence cannot be serialized as universal without nonempty verified normalization/progress authorities.
- [ ] Run the full Python suite relevant to the compiler and all formal Collatz builds used by the gate.
- [ ] Run the compiler on the canonical residual corpus and prospective holdout(s); persist exact rank or obstruction.
- [ ] Push and require hosted GitHub Actions success; inspect logs/artifact rather than trusting workflow status alone.
- [ ] Reconcile the material result to ROS with exact commit/run/artifact and epistemic state.
