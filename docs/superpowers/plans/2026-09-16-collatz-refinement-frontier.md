# Collatz Refinement Frontier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Quotient the normalized zero-ternary search across refinement `r` as well as boundary `b`, producing one exact global graph for all residual roots up to a chosen maximum refinement `R`.

**Architecture:** Write `w=v-r`. Then the normalized coefficient condition is `2^u 3^w <= 2^K`, independent of `r`; E leaves `w` fixed and each O decreases `w`; a path ending at `w` requires exactly `rho=max(0,-w)` refinement capacity. For fixed maximum `R`, enumerate only states with `w>=-R` and memoize for each `(u,w,D)` the nondominated Pareto frontier `(rho,bestD)`. A boundary `b` closes at refinement `r` iff its root frontier contains a point with `rho<=r` and `bestD<b`.

**Tech Stack:** C++20, unsigned `__int128`, GitHub Actions.

**Spec:** `experiments/collatz_zero_ternary_normalized.cpp` reference semantics and the already verified boundary-independent solver on branch `collatz-shared-normalized-capability-v1`.

## Global Constraints
- Preserve the reference DFS as an oracle.
- Do not assume cross-refinement equivalence; prove it by differential census before scaling.
- Generate an O-run of length `m` only when `w-m>=-R`; its resulting frontier requirement is at least `max(0,m-w)`.
- Lower-slope acceptance is a function of `(u,w,K)` only.
- Prune an E-run only when even spending all O capacity available at `R` cannot reach lower slope.
- Pareto dominance is exact: `(rho1,D1)` dominates `(rho2,D2)` iff `rho1<=rho2` and `D1<=D2`.
- No theorem claim from finite runs; no PR or merge.

### Task 1: Implement the global refinement frontier
- Create `experiments/collatz_zero_ternary_refinement_frontier.cpp`.
- Retain the old fixed-`r` DFS and residual builder.
- Implement `coef_le_w`, max-`R` finiteness pruning, `(u,w,D)` memoization, exact Pareto insertion, and boundary/refinement queries.
- Add `--verify K R` to compare every residual at every `r<=R` against the old DFS.

### Task 2: Differential CI
- Create `.github/workflows/collatz-refinement-frontier.yml` on `collatz-refinement-frontier-v1`.
- Compile with `-O3 -std=c++20 -Wall -Wextra -Werror`.
- First gate: `--verify 8 4` and require `VERIFIED_REFINEMENT_FRONTIER_EQUIVALENCE`.
- Second gate: `12 16` and require `VERIFIED_REFINEMENT_FRONTIER_SCOUT`.
- Record unique states, memo hits, frontier point count, maximum frontier width, closures by first required refinement, wall time, and memory.

### Task 3: Scale conditionally
- If both gates are green and resource use is small, run B12/R64.
- Compare result and cost with the per-`r` shared value-function solver.
- If B12/R64 remains unresolved, preserve the exact Pareto frontier of residuals as the next theorem object rather than extending brute force.
