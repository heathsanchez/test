# Collatz Shared Normalized Capability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace repeated boundary-specific normalized zero-ternary DFS with an exact shared value-function graph, while differentially verifying identical closure decisions against the existing DFS before scaling.

**Architecture:** For fixed `(K,r)`, the normalized transition graph is independent of boundary `b`; `b` appears only in the success test `D < b`. Define `bestD(state)` as the minimum positive intercept `D'` reachable at any state satisfying `coef_le`. Then a boundary closes exactly when `bestD(root)` exists and `bestD(root) < b`. Memoize `bestD` globally for all residual roots at a fixed `(K,r)`, keep the old DFS as a reference oracle, and process `r` outermost so unresolved families share one memo.

**Tech Stack:** C++20, Boost-free fixed `unsigned __int128`, GitHub Actions, Python aggregation.

**Spec:** Existing normalized solver `experiments/collatz_zero_ternary_normalized.cpp` at commit `cc5d71145235ea7ca061bc472061df36569639df` plus run `35056988382`.

## Global Constraints

- Preserve exact normalized transition semantics and all overflow guards.
- `D == 0` remains non-closing and is not expanded, matching the reference DFS.
- A current state is a candidate only when `coef_le(u,v,K,r)` holds; pure intermediate E states inside the E-loop are not independently accepted.
- Continue searching descendants even if a current candidate exists, because the value function must compute the minimum reachable candidate.
- Keep `r` fixed in each memo. Do not quotient states across `r` until a separate equivalence proof exists.
- No Collatz theorem claim follows from finite verification.
- No PR or merge in this plan.

---

### Task 1: Add exact shared value-function solver and differential oracle

**Files:**
- Create: `experiments/collatz_zero_ternary_normalized_shared.cpp`

**Interfaces:**
- Consumes: existing `coef_le`, `future_coef_possible`, residual builder, and reference `ndfs` semantics.
- Produces: `bestD(u,v,D,k,r,memo,stats)` returning `{reachable,best}` and `shared_closes(...)` defined by `best < b`.

- [ ] **Step 1: Preserve the existing DFS unchanged as `reference_ndfs` and add a `--verify` execution mode.**
- [ ] **Step 2: Implement a collision-safe `unordered_map<NKey, BestResult, NKeyHash>`; equality always includes `(u,v,D)` so hash collisions cannot affect correctness.**
- [ ] **Step 3: Implement `bestD`: reject `D==0`; memo lookup; set current `D` as candidate iff `coef_le`; if `v<=0` return candidate; enumerate exactly the same E/O transitions and pruning as the reference; minimize over child results; memoize the exact result.**
- [ ] **Step 4: Reorder the census loop to `r` outermost. Maintain a vector of unresolved residual indices; one memo is reused for every root at that `r`; record first-closing `r` exactly as the old loop does.**
- [ ] **Step 5: In verify mode, for every tested residual and every `r<=R`, compute both the old boolean DFS and `(bestD(root)<b)` and exit nonzero on any disagreement with a full state/boundary diagnostic.**
- [ ] **Step 6: Emit telemetry for unique states, memo hits, transitions, prunes, peak memo size, and per-r closure counts.**

### Task 2: Add bounded CI equivalence gate

**Files:**
- Create: `.github/workflows/collatz-shared-normalized-verify.yml`

**Interfaces:**
- Consumes: shared solver from Task 1.
- Produces: a push-triggered green/red equivalence result isolated to branch `collatz-shared-normalized-capability-v1`.

- [ ] **Step 1: Compile with `g++ -O3 -std=c++20 -Wall -Wextra -Werror`.**
- [ ] **Step 2: Run `--verify 8 4` first; require marker `VERIFIED_SHARED_EQUIVALENCE`.**
- [ ] **Step 3: Run shared-only `12 8` as a bounded performance/scaling probe; require `VERIFIED_SHARED_NORMALIZED_SCOUT`.**
- [ ] **Step 4: Upload census/time-memory artifacts with `if: always()` so failures remain diagnosable.**

### Task 3: Scale only after the differential gate is green

**Files:**
- Modify: `.github/workflows/collatz-shared-normalized-verify.yml`

**Interfaces:**
- Consumes: verified solver and measured K12/R8 state curve.
- Produces: K12/R64 result if resource use is acceptable; otherwise an exact residual/state profile for the next normalization step.

- [ ] **Step 1: Inspect equivalence output and state/time telemetry. Do not scale on a mismatch.**
- [ ] **Step 2: If bounded telemetry is healthy, add a separate K12/R64 job with a 60-minute cap.**
- [ ] **Step 3: Record whether all 144 B12 residual boundaries close, the maximum required `r`, unique-state count, memo-hit count, wall time, and memory.**
- [ ] **Step 4: If K12/R64 still exhausts compute, retain the exact state profile and derive the next quotient/witness grammar from observed repeated states rather than increasing brute-force limits.**

## Self-review

- Spec coverage: preserves original semantics, removes `b` from memoized computation, shares work across boundaries, and verifies equivalence before scaling.
- No cross-`r` equivalence is assumed.
- No synthetic residual set substitutes for the repository's qualified baseline builder.
- Every optimization is guarded by differential comparison against the fixed reference implementation.
