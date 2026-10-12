# Source-scoped residual closure implementation plan

**Goal:** Close all seven complete positive exports using independent Nucleus typing and definitional reduction.

**Architecture:** Check source lambdas bidirectionally against checked expected Pi types, preserving actual lexical captures and universe substitutions. Open explicit fixed Pi binders capture-safely. Reduce only admitted source definitions and registered recursor/projection rules; never infer a major from an expected result or treat distinct data operands as proof-irrelevant.

**Tech stack:** Rust, lean4export NDJSON 3.1.0, locked dependencies, local Rust 1.99.0 and independent Linux CI.

## Evidence and constraints

- Incumbent frozen artifact 11272848230: 118 ACCEPT, 71 REJECT, seven UNKNOWN, zero wrong/errors.
- Source before this work: 5eff23d. Whole-export gains remain zero.
- Fixed Pi alpha and neutral projection regression tests are bounded controls, not evidence that the seven exports are closed.
- Protect forged false-index SHA256 2a090edfcfa2a16191f17a433617aaf045fc9b11cd0e2a93405b705d8a899688 and malformed nested-recursion negatives.
- Preserve every incumbent ACCEPT and REJECT individually; UNKNOWN cannot be relabelled as REJECT or ACCEPT.
- No source-ID, test-name, theorem-name, fuel-only or external-checker acceptance bypass.

## Tasks

- [ ] Reproduce an expected-Pi lambda boundary and write positive/invalid-annotation/invalid-body/capture controls in `metatron-kernel/tests/typecheck.rs`.
- [ ] Generalize `check_expected_lambda_in` and its call in `check_in`, removing source-ID eligibility and reopening fixed codomains safely. Retain ordinary inference fallback when the optional rule cannot establish typing.
- [ ] Replay all seven and classify the first remaining complete-export obstruction from actual source contexts. Do not count local conversion wins as closure.
- [ ] If needed, reconstruct source-defined Pi exposure, exact beta substitutions and registered recursor/projection reductions, with a minimal counterexample and adversarial control before each semantic change.
- [ ] Requalify exact frozen196 in default and source-origin configurations, including per-case incumbent comparison, all Rust tests and protected mutants.
- [ ] Independently review and run Linux CI on an exact source commit for each complete-export gain.
- [ ] Qualify current Arena corpus and full Mathlib only after bounded semantic gates pass. Report remaining UNKNOWNs and instruction measurements separately.

## Implementation checkpoint

- Reconstructed conversion projections over source-reduced constant-headed neutrals.
- Generalized expected-lambda checking as an opt-in UNKNOWN fallback (eager checking was slower).
- Composed the independently qualified SourceInfo erased-field capability from source `02b30cf99530a3da31e60262132aff90dcb9afbd` with closed-field universe and RHS annotation checks.
- Derived generic closed direct-positive recursive contracts, including induction hypotheses and exact source recursor equations, independently of family names.
- Extended nonrecursive enums over closed and parametric field telescopes with independent field universe checks and rule annotation checks.
- Parsed and checked singleton safe opaque declarations, retaining only their checked signatures at runtime.
- Prototyped opt-in constructor demand with shared decreasing exposure fuel, bounded depth, and no caching of budget-stopped recursor heads.
- Added exact native predecessor bindings for certified Nat recursor iota when the source export lacks a predecessor literal; iota respects the caller's delta policy.
- Preserved dependent prior-field projections of typed constant-headed neutral receivers.
- Reviewer found a missing-rules index panic in the parametric enum path; checked access and a regression now prevent it.

**Whole-export status:** all seven remain UNKNOWN. Internal-prefix progress must not be counted as Arena gain. No official promotion or performance/rank claim.

The normal Rust suite requires the previously established `NUCLEUS_EXPERIMENTAL_RELEVANCE=1` configuration: 200 tests pass, 10 ignored (nine pre-existing bounded probes and the external-corpus seven-closure goal). The goal test remains RED and must be run explicitly when claiming complete closure.
