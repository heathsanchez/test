# Operational Physics Regrowth V33 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and execute three exact finite scaffold-deletion arenas that test regrowth of positivity, parallel product, and sequential operator structure.

**Architecture:** One dependency-free `core.py` exposes the three arena analyzers and exact helpers. `run.py` executes all arenas and writes a JSON certificate. `test_regrowth.py` freezes the scientific gates and ablations before implementation.

**Tech Stack:** Python 3 standard library; `fractions.Fraction`; `unittest`.

**Spec:** `docs/superpowers/specs/2026-09-17-operational-physics-regrowth-v33-design.md`

## Global Constraints
- Exact rational arithmetic decides all finite gates.
- No NumPy/SciPy/symbolic algebra dependency.
- No claim stronger than the declared finite grammar and obligations.
- Tests precede production implementation.

---

### Task 1: Freeze regrowth gates
**Files:** Create `experiments/operational_physics_regrowth_v33/test_regrowth.py`.
**Interfaces:** Tests consume `discover_positivity`, `discover_parallel_product`, `discover_sequential_algebra`, `run_all` from `core.py`.
- [ ] Write tests for exact composition attack, minimal positivity rule, unique product, Kronecker induction, order-sensitive sequential family, ablations, and aggregate verdict.
- [ ] Run `python -m unittest discover -s experiments/operational_physics_regrowth_v33 -v` and verify RED due to missing `core`.

### Task 2: Implement exact arenas
**Files:** Create `experiments/operational_physics_regrowth_v33/core.py`.
**Interfaces:** Produce the four functions frozen in Task 1, returning JSON-serializable dicts.
- [ ] Implement Fraction helpers and exact matrix/event calculations.
- [ ] Implement Arena P bounded witness search and rule selection.
- [ ] Implement Arena T biaffine enumeration and tensor induction.
- [ ] Implement Arena S family search over protected sequence signatures.
- [ ] Run the full test command and verify GREEN.

### Task 3: Runner and evidence
**Files:** Create `experiments/operational_physics_regrowth_v33/run.py`, `PROTOCOL.md`, `README.md`.
**Interfaces:** `python run.py --out evidence.json` writes the aggregate certificate and exits nonzero unless all declared gates pass.
- [ ] Add runner and documentation preserving claim boundaries.
- [ ] Run tests, then run the experiment twice and compare deterministic output.
- [ ] Record final exact counts and unforced frontier in the certificate.
