# LIVE STATUS — Triskelion × Lean Kernel Arena

## Purpose

Public execution mirror for the Lean Kernel Arena programme. This repo is intentionally narrower than the private `heathsanchez/triskelion` research repo.

## Current admitted frontier

A2 remains the current admitted frontier.

A2 reconstruction used here:
- upstream sokonanoda `9b4ea12f4cd437d00b6bcd0e34743065c58dea08`
- 4 threads
- session budget 2,621,440 bytes

## E0012 — symmetric universe-level equality cache

Public revalidation run: `31855875785`
Artifact: `9239017873`
Artifact SHA-256: `448c3c17713f21824e56e6a978634bb26741aca09282d4369e1aa197dd20e103`

Semantic result on immutable Arena artifact `8931227426` (161 cases):
- A2: 161/161, zero declines
- E0012: 161/161, zero declines

Paired 24-case proxy, 16 counterbalanced repetitions:
- A2 median: 0.917405 s
- E0012 median: 0.919181 s
- median paired fractional change `(E0012-A2)/A2`: +0.9939%

Decision for the public optimization stream: NOT ADMITTED. The original private exact-Mathlib decision remains formally open because those local fixtures/protocol were not pushed, but E0012 is not stacked into later candidates.

## E0013 — SPINE_LENGTH_FAST_REJECT

Public run: `31856147246`
Artifact: `9239099644`
Artifact SHA-256: `f2453a9fae8712039cb03ca53311e6c2f5d2ec5d6f5a66a6b2a4e7c0bf4aa023`

Semantic result on the same 161-case immutable corpus:
- A2: 161/161, zero declines
- E0013: 161/161, zero declines

Paired 24-case proxy, 16 counterbalanced repetitions:
- A2 median: 0.959417 s
- E0013 median: 0.977648 s
- median paired fractional change `(E0013-A2)/A2`: +2.0898%
- speed ratio A2/E0013: 0.981353

Decision: REJECT for the public optimization stream. The shortcut is semantically safe on this corpus but the resource signal is clearly negative. Do not stack it.

## Negative-law accumulation

Current public evidence adds:
- universe-level equality caching: no public proxy win on A2
- immediate spine-length mismatch reject: no public proxy win on A2

These are search-space deletions, not failures to preserve.

Important corpus correction: the public immutable artifact used here contains 161 cases, not the later 178-file corpus.

## Execution rules

- Continue from A2.
- One intervention at a time.
- Same-runner A2 control for every public performance comparison.
- Do not stack negative or unresolved candidates.
- Infrastructure failures are not scientific evidence.
- Any exact-Mathlib result must use a frozen reconstructed Mathlib fixture/protocol, not the 24-case proxy.

## Next gate

Fresh A2 profile before inventing another intervention.

Goal: re-measure the admitted A2 substrate rather than continuing to optimize historical A1 residuals. Produce:
1. per-case wall ranking over the immutable 161-case corpus;
2. fresh callgrind profile on `good/perf/grind-ring-5.ndjson` if the hosted runner supports it;
3. top optimized functions / instruction-cost regions;
4. re-rank candidate families only after this profile.
