# LIVE STATUS — Triskelion × Lean Kernel Arena

## Purpose

Public execution mirror for the Lean Kernel Arena programme. This repo is intentionally narrower than the private `heathsanchez/triskelion` research repo.

## Durable handoff

From the prior Work session:

- E0010 (`preserve verified intermediate`) was rejected under the frozen resource protocol despite semantic safety.
- A2 is the current admitted local frontier.
- A2 was reported as upstream sokonanoda `9b4ea12f4cd437d00b6bcd0e34743065c58dea08` plus the admitted 4-thread/session-budget change (2.5 MiB per session under the tested setting).
- E0012 is the symmetric universe-level equality cache candidate.
- E0012 reportedly passed the 178-file downloadable semantic corpus with zero declines and is awaiting the paired exact-Mathlib resource decision.
- The exact local E0012 protocol commit (`d4402a3` in the Work session) was not pushed to GitHub under that SHA, so the public harness must re-establish the implementation and public-runner baseline before any new public result is promoted.

## Public workflows copied from the private experiment branches

- `lean-kernel-arena-latest-soko-gate.yml`
- `lean-kernel-arena-session-search.yml`
- `lean-kernel-arena-conv-level-cache.yml`

These preserve the committed experimental families and provenance but should not be confused with the later local A2/E0012 exact-Mathlib gate.

## Current rule

No public-runner timing is compared numerically against a private-runner timing baseline without a fresh same-runner baseline.

## Immediate next gate

1. Reconstruct A2 on the public runner.
2. Reconstruct E0012 on top of A2.
3. Require 178/178 semantic correctness and zero declines.
4. Establish paired public-runner performance evidence.
5. Only after that, reproduce the exact Mathlib gate when the immutable Mathlib exports/protocol are available in this repo.

No result is promoted from infrastructure failure or from stale/substrate-mismatched evidence.
