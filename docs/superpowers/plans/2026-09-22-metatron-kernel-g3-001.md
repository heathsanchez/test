# G3-001 Guarded Semantic Delta Plan

> Execution follows the Metatron residual protocol frozen at
> `metatron-kernel/evidence/residuals/G3-001/protocol.json`.

**Goal:** Accept exact tutorial case 006 by making definition bodies
semantically available to conversion without turning exporter reducibility
hints into logical opacity or assuming normalization is total.

**Architecture:** Keep the current explicit closure machine and relational
conversion worklist. Rename the stored hint to describe its cost role. Add a
full semantic transparency request to the machine, but issue it only when the
cheap reducible comparison reaches a rigid mismatch. Every full-transparency
request retains authority-scoped cycle detection and the existing hard budget;
failure to expose remains `UNKNOWN`.

**Primary metric:** official Arena retired instructions. Correctness can retain
the semantic mechanism when the exact residual and protected suite pass, but
performance remains `UNKNOWN` without candidate and flash counts from the same
runner, metric, build, cohort, and order.

## Task 1: Freeze failing tests and the ablation seam

- Add an end-to-end regression using the byte-exact G3-001 fixture; it must
  fail before implementation.
- Add machine tests distinguishing preferred-hint transparency from full
  semantic transparency.
- Expose conversion policy only as a testable enabled/disabled option; the
  Arena checker uses enabled semantics.

## Task 2: Implement the least semantic capability

- Replace `reducible` booleans with `preferred_for_reduction` naming across
  syntax, environment, and machine representations.
- Add `Transparency::Full` to permit any definition body at the current
  authority while preserving polymorphic-instantiation, cycle, and budget
  residuals.
- In relational conversion, try preferred reduction first. Only after a rigid
  mismatch, retry the same relation using full transparency. Do not add global
  normalization, memoization, eta, proof irrelevance, or inductive behavior.

## Task 3: Qualify, ablate, and record

- Run the exact G3 residual and tutorial prefix 001–006.
- Run all Rust/Python tests, strict Clippy, formatting, ledger validation, and
  exact Lean 4.29.1 oracles.
- Record enabled/disabled verdicts, protected results, and retired-instruction
  availability. Retain only on zero semantic regression; otherwise reject and
  remove the mechanism.
- Commit and push a readable source checkpoint. Do not open an Arena PR.
