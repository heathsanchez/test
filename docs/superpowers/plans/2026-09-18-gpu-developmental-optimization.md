# GPU Developmental Optimization V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test prospectively whether verified optimization capabilities acquired on source kernel families reduce developmental search on untouched target kernels.

**Architecture:** Implement an exact finite kernel IR with reference evaluator, frozen transformation family, verifier and cost model. Acquire conditional transformations on source kernels, serialize them, then compare COLD/WARM/RESTART/SHAM/ABLATION on sealed target kernels. Hardware promotion is separate.

**Tech Stack:** Python 3.12 standard library; GitHub Actions; optional Triton/CUDA only after the finite gate.

**Spec:** `docs/superpowers/specs/2026-09-18-gpu-developmental-optimization-design.md`

## Global Constraints
- Target kernels are generated only after scorer/transformation family/capabilities freeze.
- Correctness is authoritative and independent of performance score.
- Retained capabilities contain no target IDs or answers.
- Five causal arms are mandatory.

---

### Task 1: Freeze RED contract
**Files:** Create `experiments/gpu_developmental_optimization_v1/PRECOMMIT.md`, `test_ir.py`, `test_transfer.py`, workflow.
**Interfaces:** Tests require `evaluate_reference`, `enumerate_transformations`, `acquire_capabilities`, `run_arm`, `score_packet`.
- [ ] Freeze source/target generators, transformation set, verifier, cost accounting and causal inequalities in PRECOMMIT.
- [ ] Write failing tests for semantic equivalence, capability applicability, restart, sham and exact ablation.
- [ ] Run unittest discovery and confirm RED from missing production modules.
- [ ] Commit frozen tests.

### Task 2: Exact kernel IR and verifier
**Files:** Create `ir.py`, `verify.py`.
**Interfaces:** `Kernel`, `evaluate_reference(kernel, inputs)`, `verify_equivalent(a,b,test_domain)`.
- [ ] Implement finite integer-array kernels with exact arithmetic and explicit operations.
- [ ] Implement exhaustive frozen input-domain equivalence checks.
- [ ] Implement structural execution-cost accounting independent from developmental search cost.
- [ ] Run IR tests GREEN and commit.

### Task 3: Transformation search and capability acquisition
**Files:** Create `optimize.py`, `capability.py`.
**Interfaces:** `Transformation`, `Capability`, `acquire_capabilities(source_kernels)`.
- [ ] Implement frozen transformations: fusion, intermediate elimination, safe reassociation, specialization and traversal/layout rewrite in IR terms.
- [ ] Search candidates, reject verifier failures, retain only strict cost improvements with applicability signatures.
- [ ] Serialize/reload capabilities and verify exact replay.
- [ ] Commit GREEN source acquisition.

### Task 4: Prospective five-arm target tournament
**Files:** Create `run.py`, `score.py`, `validate.py`; extend `test_transfer.py`.
**Interfaces:** `run_arm(name, capabilities, target_kernels) -> ArmResult`.
- [ ] Derive target seed from frozen commit/run provenance.
- [ ] Run COLD full search, WARM capability-first, RESTART serialized-only, matched SHAM, exact ABLATION.
- [ ] Require verifier-equivalent outputs in every arm.
- [ ] Independently replay metrics and causal dependencies.
- [ ] Score frozen inequalities and emit evidence hashes/artifact.
- [ ] Inspect authoritative CI logs before reporting.

### Task 5: Hardware promotion if finite gate passes
**Files:** Create only after pass: `triton_promotion.py`, `test_triton_promotion.py`.
- [ ] Detect available GPU/Triton runner without weakening Phase-B claim if absent.
- [ ] Compile applicable retained transformations to a small real kernel family.
- [ ] Compare numerical correctness and measured latency separately from IR cost.
- [ ] Seal hardware evidence as a distinct result or report exact infrastructure/transfer obstruction.