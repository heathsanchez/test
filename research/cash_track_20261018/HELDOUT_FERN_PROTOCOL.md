# Frozen prospective source-native transfer — declared-outage STEP FAIL (2026-10-18)

## Selection / provenance
Chosen before opening source diffs or original test files from [OllyInsurance/fern-platform PR #16](https://github.com/OllyInsurance/fern-platform/pull/16). Selection basis is **only PR metadata and natural-language contract** available on 18 Oct NZ: Go PR merged, two files changed, goal states a STEP FAIL *during a separately declared outage* is inconclusive, but a neighboring product CHECK FAIL must keep the result failed. The earlier MathGraph seven-case benchmark, its implementation and GREEN CI are frozen and do not contain this new repository.

Pin the original upstream base `ee843f4babd4c05e819aa86701e409b58e328c66` and author head `ddff2c82b9a0124ccec83d079cf9877f4479e914`. Treat source identity from `git rev-parse HEAD` as necessary. Do not use later commits or adapt input labels post hoc to make a pass. No external upstream writes.

## Independent causal experiment / exact obligations
- Use an independently authored **same fixed regression test file** on actual original Go package source, at both pinned base and author head.
- Protected positive: a result consisting of `STEP FAIL ... DURING DECLARED OUTAGE` (without CHECK FAIL) is classified **INCONCLUSIVE** at the **original scope**. A genuinely isolated, named outage should not be counted as product failure.
- Protected negative A: same result with `STEP FAIL` but **no declared outage evidence** remains **FAIL**.
- Protected negative B: `STEP FAIL ... DURING DECLARED OUTAGE` **plus an independent, unexcused `CHECK FAIL`** remains **FAIL**. A legitimate outage cannot launder a real product check failure.
- Protected negative C: an unrelated or forged outage name does NOT excuse an unbound CHECK FAIL.
- Source guard: exactly pinned base and head git identities, same test bytes, successful Go build, actual invocation of named tests and output; mere Go exit 0 without executed named test is NOT evidence.
- Expected difference (candidate, subject to native execution): base misclassifies positive while head classifies it inconclusive; controls A–C should remain failed on both.
- Negative source controls: incorrect source SHA, physically removed test file, corrupt independent source reference must fail closed.
- Comparison: unchanged native base-vs-head behavior; an equally informed **policy** baseline using only `any_outage_annotation` must be executed as a nontrivial comparison. Agent/model baseline NOT_RUN without independent model execution.
- Preserve all observed failure outcomes and if any protected negative flips, reject instead of counting a positive.

## Execution and promotion
Freeze this file as its own Git commit before fetching source patch, and before creating test implementation. Then inspect actual original PR diff only to find the narrow API/fixture source entrypoint without using original tests as templates. Any human-coded bridge is reported as such (no model-generated method or autonomous novel bug discovery). The author had already publicly disclosed the defect.

Success qualifies **WARRANTED_BOUNDED prospective independent *native test* transposition** for this source-distinct PR (if all native and negative gates pass), NOT a new upstream discovery, not strong agent advantage, not a blind unseen-model benchmark, nor an ordinary 7-case packet expansion.

The pre-existing resource has 7 historical packets; adding this only after native success yields exactly one independently reproduced new class, not a new general algorithm. Stop with UNKNOWN_NATIVE if original dependencies/source/toolchain cannot be independently built. Never claim competitive Kaggle submission.
