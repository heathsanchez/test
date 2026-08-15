# Triskelion × Lean Kernel Arena — Public Execution Harness

Public GitHub Actions harness for the Lean Kernel Arena optimization/development programme.

This repository intentionally contains only the execution-facing subset needed to reproduce and continue benchmark experiments. The broader Triskelion research repository remains separate.

## Current execution objective

Preserve complete Lean Kernel Arena semantic correctness while reducing resource cost. New interventions are admitted only after protected semantic and paired resource gates.

## Immediate frontier

The private research ledger reports A2 as the current admitted local frontier and E0012 (symmetric level-equality cache) as semantically clean on the 178-file downloadable corpus, pending paired Mathlib resource validation. Because the exact local E0012 commit was not pushed, this public harness reconstructs the relevant committed experiment families from the existing Triskelion branches and reruns them on public GitHub-hosted runners before promotion.

## Provenance

Source experiment history: `heathsanchez/triskelion` (private research repo).
External checker/world: Lean Kernel Arena and upstream sokonanoda.

No result in this public repository should be treated as admitted unless the workflow artifact and status ledger say so.
