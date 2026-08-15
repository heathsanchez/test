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

The original private exact-Mathlib E0012 gate remains formally unresolved because the local immutable Mathlib fixtures/protocol were not pushed.

Public revalidation run: `31855875785`
Artifact: `9239017873`
Artifact SHA-256: `448c3c17713f21824e56e6a978634bb26741aca09282d4369e1aa197dd20e103`

The public runner completed end-to-end on the immutable Arena artifact `8931227426`.

Semantic result on the 161-case suite contained in that artifact:
- A2: 161/161, zero declines
- E0012: 161/161, zero declines

Paired 24-case proxy, 16 counterbalanced repetitions:
- A2 median: 0.917405 s
- E0012 median: 0.919181 s
- speed ratio A2/E0012: 0.998069
- median paired fractional change `(E0012-A2)/A2`: +0.9939%

Interpretation:
- semantic safety: supported on this 161-case public corpus
- public performance signal: negative
- admission: NO; E0012 is not stacked into the frontier
- exact private Mathlib decision: still formally open, but this public proxy does not motivate spending the next optimization branch on E0012

Important corpus correction: the public immutable artifact used here contains 161 cases, not the later 178-file corpus. Do not relabel this result as 178/178.

## Execution rules

- Continue from A2.
- One intervention at a time.
- Same-runner A2 control for every public performance comparison.
- Do not stack negative or unresolved candidates.
- Infrastructure failures are not scientific evidence.
- Any exact-Mathlib result must use a frozen reconstructed Mathlib fixture/protocol, not this 24-case proxy.

## Next gate

E0013: `SPINE_LENGTH_FAST_REJECT` on A2.

Hypothesis: after pointer identity has failed, unequal spine lengths can return false immediately rather than entering deeper spine comparison.

Protocol:
1. Reconstruct A2.
2. Add only the length-mismatch fast reject.
3. Require full correctness and zero declines on the same 161-case immutable corpus.
4. Compare A2 vs E0013 on the same counterbalanced 24-case public-runner proxy.
5. If positive, promote only after an appropriately stronger resource gate; if negative, freeze and re-profile A2.
