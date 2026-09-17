# ARC Robotics Developmental Transfer V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prospectively test whether an ARC-acquired residual→separator→representation-split operator reduces developmental cost in a structurally different active world, then promote the unchanged operator to MuJoCo only after the finite causal gate passes.

**Architecture:** A source module acquires and serializes a domain-independent developmental operator. A separate sealed target module creates physics-like worlds after freeze and exposes only observations/interventions. A five-arm evaluator measures causal developmental cost with restart, sham and exact dependency ablation; promotion code is isolated behind the Phase-B gate.

**Tech Stack:** Python 3.12 standard library for Phase A/B; GitHub Actions for sealed execution/evidence; optional MuJoCo Python package only for gated Phase C.

**Spec:** `docs/superpowers/specs/2026-09-18-arc-robotics-developmental-transfer-design.md`

## Global Constraints

- Source and target may not share latent labels, truth tables, observation encoding, or target rules.
- The transferred artifact contains only the developmental meta-operator, never target-specific features or answers.
- Target seeds/worlds are derived only after source capability and scoring semantics are frozen.
- Five arms are mandatory: COLD, WARM, RESTART, SHAM, ABLATION.
- Final correctness observations are identical across arms and excluded from developmental cost.
- MuJoCo Phase C is gated on an independently validated Phase-B pass.

---

### Task 1: Freeze prospective Phase-B contract and RED tests

**Files:**
- Create: `experiments/arc_robotics_developmental_transfer_v1/PRECOMMIT.md`
- Create: `experiments/arc_robotics_developmental_transfer_v1/__init__.py`
- Create: `experiments/arc_robotics_developmental_transfer_v1/test_source.py`
- Create: `experiments/arc_robotics_developmental_transfer_v1/test_target.py`
- Create: `experiments/arc_robotics_developmental_transfer_v1/test_pipeline.py`
- Create: `.github/workflows/arc-robotics-developmental-transfer-v1.yml`

**Interfaces:**
- Consumes: design spec only.
- Produces frozen tests for `acquire_developmental_operator()`, `run_target_arm()`, `run_experiment()`, `validate_packet()`, and `score_packet()`.

- [ ] Write tests asserting source acquisition returns only a domain-independent collision/separator/split policy and contains none of the frozen forbidden target tokens.
- [ ] Write target tests asserting the initial representation aliases at least one pair with incompatible consequences, the separator intervention distinguishes that pair, and hidden regime labels are never present in learner observations.
- [ ] Write five-arm tests requiring exact correctness, WARM<COLD/SHAM/ABLATION, RESTART==WARM, and ABLATION restores the cold frontier.
- [ ] Run `python -m unittest discover -s experiments/arc_robotics_developmental_transfer_v1 -p 'test_*.py' -v` and verify RED because production modules do not yet exist.
- [ ] Commit the frozen contract before implementation.

### Task 2: Implement source developmental-operator acquisition

**Files:**
- Create: `experiments/arc_robotics_developmental_transfer_v1/source.py`
- Test: `experiments/arc_robotics_developmental_transfer_v1/test_source.py`

**Interfaces:**
- Produces: `DevelopmentalOperator` serializable dataclass and `acquire_developmental_operator() -> DevelopmentalOperator`.
- Capability fields are limited to collision detection rule, intervention-selection objective, minimal split rule, version, and provenance.

- [ ] Run source tests and confirm failure against missing implementation.
- [ ] Implement a finite ARC-like active source environment whose initial quotient collides under verified consequences.
- [ ] Implement cold search over a frozen small family of developmental responses so the residual→separator→split operator is acquired rather than hard-coded as the source answer.
- [ ] Serialize/reload the capability and test equality of behavior after restart.
- [ ] Run source tests to GREEN and commit.

### Task 3: Implement structurally different sealed target world

**Files:**
- Create: `experiments/arc_robotics_developmental_transfer_v1/target.py`
- Test: `experiments/arc_robotics_developmental_transfer_v1/test_target.py`

**Interfaces:**
- Produces: `TargetWorld`, `Observation`, `Intervention`, `generate_worlds(seed, n)`, and learner-safe observation methods.
- Hidden regime is private oracle state used only by evaluator correctness checks.

- [ ] Implement deterministic seed-derived worlds with visible kinematic state and a hidden interaction regime unrelated to the ARC source latent mechanism.
- [ ] Provide multiple allowed interventions, only some of which separate the aliased regimes.
- [ ] Ensure terminal action/controller choice depends on the discovered behavioural distinction.
- [ ] Test that learner-visible structures contain no hidden-regime field or oracle label.
- [ ] Run target tests to GREEN and commit.

### Task 4: Implement five-arm developmental evaluator

**Files:**
- Create: `experiments/arc_robotics_developmental_transfer_v1/evaluator.py`
- Test: `experiments/arc_robotics_developmental_transfer_v1/test_pipeline.py`

**Interfaces:**
- Produces: `ArmResult`, `run_target_arm(arm, capability, worlds)`, developmental metrics, and exact execution correctness.

- [ ] Implement COLD as search over the frozen developmental strategy family with paid interventions/evaluations.
- [ ] Implement WARM using only the serialized developmental operator to react to predictive collisions and select a separator.
- [ ] Implement RESTART by round-tripping only the serialized capability before target development.
- [ ] Implement SHAM with a matched irrelevant operator and identical resource accounting.
- [ ] Implement ABLATION by exact removal of collision→active-separator→split dependency while preserving generic compute/search resources.
- [ ] Run five-arm tests to GREEN and commit.

### Task 5: Seal, validate, score, hash, and publish Phase-B evidence

**Files:**
- Create: `experiments/arc_robotics_developmental_transfer_v1/run.py`
- Create: `experiments/arc_robotics_developmental_transfer_v1/validate.py`
- Create: `experiments/arc_robotics_developmental_transfer_v1/score.py`
- Modify: `.github/workflows/arc-robotics-developmental-transfer-v1.yml`

**Interfaces:**
- `run_experiment()` writes `capability.json`, `answers.json`, and `run_metadata.json`.
- `validate_packet()` independently replays observations and checks leakage/provenance.
- `score_packet()` emits `scores.json` and exits nonzero unless every frozen causal requirement passes.

- [ ] Derive sealed seed from commit SHA/run ID only after checkout of the frozen tree.
- [ ] Generate untouched target worlds and run all five arms.
- [ ] Independently validate target correctness, restart equivalence, transfer-artifact schema, absence of target leakage, and exact ablation semantics.
- [ ] Score only the precommitted ordering/causal criteria; do not tune thresholds to observed magnitude.
- [ ] Hash PRECOMMIT, source/target/evaluator/run/validate/score, capability, answers, metadata, and scores.
- [ ] Upload the evidence packet as a GitHub Actions artifact.
- [ ] Run the authoritative CI gate and inspect full logs before claiming a Phase-B result.

### Task 6: Gate and attempt MuJoCo Phase-C promotion

**Files:**
- Create only after Phase-B pass: `experiments/arc_robotics_developmental_transfer_v1/mujoco_target.py`
- Create only after Phase-B pass: `experiments/arc_robotics_developmental_transfer_v1/test_mujoco_target.py`
- Modify only after Phase-B pass: `.github/workflows/arc-robotics-developmental-transfer-v1.yml`

**Interfaces:**
- Consumes the exact serialized `DevelopmentalOperator` produced in Phase A.
- Produces a MuJoCo arm result with the same developmental metrics and epistemic boundary as Phase B.

- [ ] Check Phase-B `primary_pass` from independently generated `scores.json`; stop and report the smallest obstruction if false.
- [ ] Add a minimal MuJoCo environment with visually/kinematically aliased initial observations and a hidden physical property such as friction affecting intervention consequences.
- [ ] Expose no simulator parameter values to the learner.
- [ ] Run COLD/WARM/RESTART/SHAM/ABLATION with the unchanged developmental operator semantics.
- [ ] If MuJoCo installation/runtime is unavailable in CI, record that as infrastructure obstruction rather than weakening the experiment.
- [ ] If available, seal and upload a separate Phase-C evidence packet; report Phase B and Phase C as distinct claims.
