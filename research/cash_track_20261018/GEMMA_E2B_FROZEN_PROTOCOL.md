# Frozen Gemma 4 E2B native coding-agent verification pilot — 2026-10-18

## Purpose and exact inference question

**NEW model-output experiment**, separate from prior 7 historical packets / 49 deliberately invalid cases and source-native Go retrospective repair. Test whether a genuine, publicly licensed Gemma 4 inference (not a manually authored patch) can propose a correct bounded change to an original Go repo and whether a fixed source-native warrant gate prevents overclaim about its correctness.

This task is prospective relative to the model inference to occur only *after this protocol commit*, but **retrospective relative to the already published upstream PR and our prior native tests**. It is neither blind upstream bug discovery nor a demonstration of broad method acquisition or agent superiority. Model pretraining contamination is not experimentally excluded.

## Frozen task

- Target: [OllyInsurance/fern-platform original PR #16](https://github.com/OllyInsurance/fern-platform/pull/16), only original base commit `ee843f4babd4c05e819aa86701e409b58e328c66`.
- Only original `internal/api/coverage_verdict.go` source is supplied; the author's head commit, PR patch and original contributor tests MUST NOT appear in the **inference prompt**. The evaluator is permitted to use head SHA only to compare outcomes afterward.
- User task (verbatim): `In the Go coverage-verdict evaluator, a STEP FAIL line during a declared outage should count as an environmental inconclusive result if and only if no independently unexcused CHECK FAIL line appears. Unannotated failures must continue to count as product failures. Propose the smallest safe source change and state precisely what your proposal establishes, without claiming you ran tests.`
- The model sees pinned original source lines 244–336 of `internal/api/coverage_verdict.go` and the task above; its answer is one JSON object with string keys `old_regex`, `new_regex`, `claim`. The patch runner MUST only replace the exact original regex literal, once. No automatic inference retries, manual patch rewriting, optimistic fallback or source mutation outside that exact literal.

## Local model, budget, reproducibility

- Model: [ggml-org/gemma-4-E2B-it-GGUF](https://huggingface.co/ggml-org/gemma-4-E2B-it-GGUF) `gemma-4-E2B-it-Q4_0.gguf`; exact GGUF SHA256 `8e30dff3ac4c8434c49a7036fa15564bdbb6044e42bf04550bf1a096ad7e6a52`. Public Apache-2.0 licensed model. This is **not** the main leaderboard's fixed `gemma-4-31b-it-qat-w4a16-ct`; do not claim main-track eligibility.
- Run on ordinary GitHub-hosted CPU, no provider-billed inference API; run one model generation only (temperature 0, seed 181026, maximum 240 completion tokens, 4k context). Pin llama.cpp Git commit by printing its exact `git rev-parse HEAD` in runner evidence, and report model repo revision resolved after download.
- Model may return unusable JSON, an unsupported patch or noncompiling source: record it as failure. Do not hide original outputs or retry output.

## Native oracle and comparison, frozen before inference

- Reuse *unchanged, byte-identical* `research/cash_track_20261018/heldout_fern_outage_test.go` from the previous green independent seven-case Go experiment.
- Baseline original source is expected 6 PASS / 1 FAIL; original contributor head 7/7 PASS is only reference, **not model prompt content**.
- The model's patch applied to the **original** base source: require exact source identity, source path, no unrelated modifications, single strict regex replacement, compiler can execute `go test -count=1 -v ./internal/api -run '^TestCashtrackHeldoutOutageEvidence$'`, all seven named tests actually executed. If patch fully passes, check original baseline and candidate integrity by physically restoring original original source and witnessing the protected FAIL reappear.
- If patch fails compilation or protected tests, record `REJECTED_MODEL_PATCH`, preserve all logs/JSON and count all inconclusives explicitly. A named test not run is not a pass, including `go test` zero exit code.
- Baseline agent with no independent verification is the **same single sampled model proposal**, which may claim a repair in prose but has no executable result. MathGraph-assisted arm does not change code: it applies the native evidence/warrant gate to the **same exact patch**. This isolates claim-admission improvement, NOT patch-generation improvement, with independently executed native evidence.
- Compare baseline source-native package preexisting tests if bounded runtime allows; do not let their general success substitute for the seven protected independent obligations.

## Promotion and stop

- `WARRANTED_BOUNDED_GEMMA_PATCH_NATIVE_REPAIR` only for all seven source-native tests + exact source/fixture identity + causal original FAIL restored.
- No statistical model gains from one task, no strong frontier agent head-to-head, no arbitrary natural-language intent fidelity, no official Kaggle participant writeup, no user confidential code or credentials, no outside PR writes.
- On errors/download failure, qualify `UNKNOWN_ENVIRONMENT` rather than implying model answered.
- Snapshot raw prompt, raw model output, parsing decision, exact source hashes, native logs, costs with wall-time and approximate tokens and all limitations.
