# Nucleus C45 high-budget and existing-grammar discriminator

Status: **WARRANTED BOUNDED observation** on unchanged originals; **REJECTED** as a standard-budget closure. No kernel proof rule or source was changed in this experiment.

## Baseline and authority

Executed the reconstructed C43 source + opt-in C44 binary with C44 **off**, the C39 selection's exact 24 experimental flags, `NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE=1`, on the original `good/perf/*.ndjson` files with immutable SHA-256 pins in `c44-evidence.md`. A separate `nucleus-diagnostic` executable differs from the production checker only by passing an explicit `Limits{judgment_steps:steps}` and printing the verdict. Higher budgets are **diagnostic only** and cannot qualify an Arena standard-budget ACCEPT.

## The smallest source budget experiment

Unchanged `magma-list-pair-n7`:

| Diagnostic steps | C44 off | C44 sparse on |
| ---: | --- | --- |
| 262,144 | UNKNOWN | UNKNOWN |
| 1,048,576 | UNKNOWN | not measured |
| 4,194,304 | UNKNOWN | not measured |
| 8,388,608 | UNKNOWN | not measured |
| 12,582,912 | UNKNOWN | not measured |
| 13,631,488 | UNKNOWN | UNKNOWN |
| 14,155,776 | ACCEPT | ACCEPT |
| 14,680,064 | ACCEPT | not measured |
| 16,777,216 | ACCEPT | not measured |

The measured acceptance threshold is in `(13,631,488, 14,155,776]` steps for both tested arms, **at least 52 times** the standard allowance. This proves the currently selected implementation can complete this unchanged proof at a larger allowance without adding inference rules. It does **not** prove that every earlier speculative conversion was necessary or that a different implementation cannot complete it inside the standard allowance.

The high-budget diagnostic run with `NUCLEUS_TRACE_REPLAY_CACHE=1` recorded repeated checked `NameId(66)` replay work items, with key-accounting charges like 23 of 27 local steps. However those 32 sampled worklist lines are not a global cost profile and cannot justify blaming replay key construction for the full 13+ million steps.

## Opposing controls

- With `NUCLEUS_DIAGNOSTIC_NO_REPLAY_KEYS=1`, exact n7 remains UNKNOWN at 262,144, 1,048,576, 4,194,304 and 8,388,608; ACCEPT at 14,155,776. Disabling completed replay keys does not produce the requisite order-of-magnitude reduction in this controlled boundary.
- With the selected 24 flags, removing each one *individually* while retaining the others and C38 observer produced 24/24 UNKNOWN at the standard 262,144 steps. Thus no one flag is the obvious obstruction, though joint ablations were not exhaustively searched.
- With 16,777,216 diagnostic steps, unchanged `magma-list-pair-n21`, `magma-list-deep-n21`, and `magma-list-deep-n36` remained UNKNOWN. `fueled-chain` hit a 75-second wall-time cap without a verdict and is inconclusive at that budget. Earlier qualified C34 evidence reported `grind-ring-5` ACCEPT at 16,777,216 and 82.84 seconds, not re-run here. Do not generalize n7's high-budget ACCEPT to all six.

## Causal interpretation and next action

The attached *Rigorous Breakthrough Stack* advocates closure-before-invention and plateau checks. This experiment explicitly tested the replay-key ablation, existing selected-mechanism single-flag ablations, and increased-budget reachability. The n7 bottleneck is **resource cost under the selected semantics**, not a proven missing Lean inference rule; still, at least 52x work reduction is needed. BVar forwarding and replay-key removal did not meet it. Repeating cache knob variants is now low-value.

For the next intervention, instrument the **entire** completed 14,155,776-step n7 derivation, not the first 32 replay traces, with per-class aggregate metered work at the first successful registered recursor/projection transition, and compare it with the standard-budget failure. The priority is to find a lawful structural quotient or source-certified demand-graph sharing that removes an entire repeated subproof family, rather than saving a few binder or replay-key operations. Require two rival discriminators and frozen forged controls before any step is promoted.

Trust boundary: production verdict unchanged; no new 403-case protected regression has been claimed; no ACCEPT under standard budget in C45.
