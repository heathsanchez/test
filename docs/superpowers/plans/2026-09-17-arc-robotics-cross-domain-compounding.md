# ARC Robotics Cross-Domain Compounding V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and run an exact finite experiment testing whether a 3-bit relational operator discovered from ARC-like grids reduces later active-world calibration/search cost under a domain adapter, with sham, ablation, and restart controls.

**Architecture:** Exhaustively search all 256 three-input Boolean truth tables on passive source grids and retain the unique parity operator. In the target domain, expose raw sensor triples through paid probes and hide the target rule behind input/output polarity transformations. Compare COLD, WARM, SHAM, ABLATION, and RESTART using a frozen calibration stream and sealed after-commit target worlds.

**Tech Stack:** Python 3.12 standard library; GitHub Actions; JSON artifacts.

**Spec:** `docs/superpowers/specs/2026-09-17-arc-robotics-cross-domain-compounding-design.md`

## Global Constraints

- No MuJoCo dependency in V1.
- No LLM calls.
- Source operator library is exactly all 256 deterministic Boolean maps `{0,1}^3 -> {0,1}`.
- Source operator is selected only from source ARC-like examples.
- Target concrete sealed worlds are seeded from `GITHUB_SHA` and `GITHUB_RUN_ID` when available.
- WARM may reuse only the retained source truth table, not source answers or target labels.
- SHAM retains a same-type majority truth table and must be rejected by target calibration before cold fallback.
- Exact target correctness is required for every arm.

---

### Task 1: Freeze tests and CI RED state

**Files:**
- Create: `experiments/arc_robotics_cross_domain_v1/test_core.py`
- Create: `experiments/arc_robotics_cross_domain_v1/PRECOMMIT.md`
- Create: `.github/workflows/arc-robotics-cross-domain-v1.yml`

**Interfaces:**
- Consumes: none.
- Produces expected API from `core.py`: `source_examples()`, `discover_source_operator()`, `parity3_code()`, `majority3_code()`, `operator_orbit()`, `run_arm(arm, seed, n_worlds)`, `serialize_capability()`, `deserialize_capability()`.

- [ ] Write tests asserting unique source discovery, parity orbit size 2, WARM exactness and cost reduction, SHAM exact fallback, ABLATION cost restoration, and RESTART equality with WARM.
- [ ] Add workflow that runs `python -m unittest experiments.arc_robotics_cross_domain_v1.test_core -v`.
- [ ] Push and verify CI fails specifically because `core.py` does not yet exist.

### Task 2: Implement the exact source/target kernel

**Files:**
- Create: `experiments/arc_robotics_cross_domain_v1/__init__.py`
- Create: `experiments/arc_robotics_cross_domain_v1/core.py`

**Interfaces:**
- `source_examples() -> list[dict]`: eight ARC-like grid examples, one per 3-bit input.
- `discover_source_operator(examples) -> tuple[int, int]`: unique truth-table code and number of candidate evaluations.
- `operator_orbit(code: int) -> tuple[int, ...]`: distinct target truth tables induced by all input/output polarity flips.
- `run_arm(arm: str, seed: int, n_worlds: int = 64) -> dict`: exact metrics and per-world results.
- `serialize_capability(code: int) -> str`; `deserialize_capability(payload: str) -> int`.

- [ ] Implement truth-table encoding with index `(a << 2) | (b << 1) | c`.
- [ ] Implement source grid generation/extraction and exhaustive 256-table search.
- [ ] Implement polarity orbit construction.
- [ ] Implement target calibration: COLD/ABLATION search all 256 tables; WARM/RESTART search the transferred parity orbit and require one independent confirmation after uniqueness; SHAM searches majority orbit, rejects on mismatch, then reuses observations for cold fallback.
- [ ] Generate sealed target rule as parity or complement from the run seed and sealed worlds as random raw sensor triples after seed freeze.
- [ ] Count paid calibration interventions, operator evaluations, execution probes, total developmental cost, correctness, and UNKNOWN.
- [ ] Push and verify all Task 1 tests pass.

### Task 3: Add sealed runner, scorer, and validator

**Files:**
- Create: `experiments/arc_robotics_cross_domain_v1/run.py`
- Create: `experiments/arc_robotics_cross_domain_v1/score.py`
- Create: `experiments/arc_robotics_cross_domain_v1/validate.py`
- Modify: `.github/workflows/arc-robotics-cross-domain-v1.yml`

**Interfaces:**
- `run.py` writes `answers.json`, `run_metadata.json`, and `capability.json`.
- `score.py` reads `answers.json`, writes `scores.json`, and exits nonzero unless the frozen causal criteria hold.
- `validate.py` verifies source uniqueness, sealed seed provenance, arm exactness, and no warm-only access to target labels.

- [ ] Run all five arms with the same sealed seed and 64 target worlds.
- [ ] Score primary pass iff WARM cost < COLD, SHAM, ABLATION; RESTART cost == WARM; all arms exact; ABLATION cost == COLD.
- [ ] Upload all evidence files from CI even on failure.
- [ ] Push and inspect the authoritative workflow run and artifact metrics.

### Task 4: Verify branch evidence

**Files:** none unless a defect is found.

- [ ] Run full workflow again from final commit.
- [ ] Confirm test, validate, run, score, and artifact-upload steps are green.
- [ ] Record final commit SHA, workflow run URL, arm metrics, and exact claim boundary.
