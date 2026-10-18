# Cash-track Gemma 4 E2B V3 — separate frozen non-thinking CPU trial
Date: 2026-10-18 (Pacific/Auckland).

## Previous evidence, unchanged

- V1 frozen protocol [4aec77a8](https://github.com/heathsanchez/test/commit/4aec77a860d3d6ff8c427ae9ae5ec173a5527bff), [Actions 39096545823](https://github.com/heathsanchez/test/actions/runs/39096545823): actual Gemma E2B GGUF inference with 240 completion tokens; `message.content=""`, `finish_reason="length"`, 6/7 original Go tests, no model patch.
- V2 frozen protocol [5aa6c078](https://github.com/heathsanchez/test/commit/5aa6c078cb78b96e8b2b777fa6ce194b8399ce64), [Actions 39097185412](https://github.com/heathsanchez/test/actions/runs/39097185412): same exact model/issue/source/seed/temp/inference runtime, raised completion tokens to 1024; again final `message.content=""` and `finish_reason="length"` with 1024 generated thinking tokens; original Go 6/7.
- Preserve the user-requested V2 STOP: no V2 retry or changes to draft PR #126. The present V3 is a separately frozen experiment approved by the user. It is not a V2 pass or a third independent benchmark task.

## Fixed conditions / sole inference intervention

- Base from original V2 candidate commit [d92fc7d1](https://github.com/heathsanchez/test/commit/d92fc7d1811e9f79f5cc2ba71f9a247ca7be797d), isolated research branch `research/gemma4-e2b-nonthinking-v3-20261018`. No PR; a single push-only GitHub workflow guarded by an exact commit message. No `workflow_dispatch`, `pull_request`, cron or inherited path-driven model tasks.
- Model `ggml-org/gemma-4-E2B-it-GGUF` named `gemma-4-E2B-it-Q4_0.gguf`; SHA256 `8e30dff3ac4c8434c49a7036fa15564bdbb6044e42bf04550bf1a096ad7e6a52`; pin llama.cpp tag `b11433` resolving at `50569eb87df530daff11afda229ceb9ab8e6cae8`, compile CPU only, no paid hosted model calls.
- Preserve original model prompt text exactly: `run_gemma_e2b_v2_model.py` TASK, SYSTEM, source lines 244–336, seed 181026, temperature 0, max_tokens **1024**, context **4096**, 4 CPU threads, one inference call only. V2 prompt SHA256 `f7bf130560fe2ba7370e8c99ce45d4584b6f6a3d37e33a399a41fb2a255061d2` and source file SHA256 `976be45f6d65a8892e0fba94294fda0c68ac05be71b3cc6c73f31648aaad9ca2` are compulsory; assert before inference, otherwise UNKNOWN/RED.
- **Only experimental change:** launch the same llama-server command plus `--reasoning off` (native llama.cpp reasoning control, not `--reasoning-format none` which changes parsing only). Do not add another request-level thinking flag or change prompt/inference budget. Record full raw response JSON, reasoning_content presence/length, finish_reason, token count and effective server command without credentials.
- Before model test preserve original official Go source from `OllyInsurance/fern-platform@ee843f4babd4c05e819aa86701e409b58e328c66`, frozen `heldout_fern_outage_test.go` unchanged, seven *actual executed* named native tests with exactly six PASS/one protected FAIL; clean git tracked worktree and hash-checked single new test overlay.
- Parse generated JSON with exactly three string fields `old_regex,new_regex,claim`, prohibit unsupported changes, never repair invalid model output or use author patch. Run same exact seven native Go tests on generated patch if and only if exact source-bound replacement exists. Native candidate 7/7 PASS plus physical deletion/restore FAIL qualify a **single bounded native repair on a publicly disclosed bug**, not autonomous novel bug discovery or improved coding model quality. If unsupported, label REJECTED_MODEL_...; if environment/not-ready, UNKNOWN; if no final content, keep negative. No extra generation.
- Measure actual CPU inference seconds and all test timings; setup/download/build are separately charged in logs, not excluded from a claim of end-to-end cost. A single one-source native test is not a matched tool-using model comparator.

## Historical evidence / promotion and stopping rules

- V1 and V2 thought-only outputs are NOT erased. An accidental V1 PR synchronize rerun [39097185379](https://github.com/heathsanchez/test/actions/runs/39097185379) is an excluded nonindependent duplicate.
- V3 status: `WARRANTED_BOUNDED_ONE_MODEL_PATCH` ONLY if exact native Go patch successfully passes all seven, original failure physically restored, identities match. `WARRANTED_EXECUTED_MODEL_REJECTED_OUTPUT` if actual model call yields invalid/empty/unsupported answer; `UNKNOWN_ENVIRONMENT` if transport/compilation/download/oracle not executed. Never represent runner GREEN as model correctness.
- **One-shot STOP** after one V3 generation regardless of outcome; no automatic reruns. No Kaggle, no customer outreach, no RunPod, no paid inference, no source merge. Save GitHub Actions log, artifact, exact SHA/commit and ROS warrant.

## Fixed source evidence pointers

[Original Go native historical qualification](https://github.com/heathsanchez/test/actions/runs/39093369502) and [7/49 packet audit](https://github.com/heathsanchez/test/actions/runs/39095449385) remain separate boundaries. Rules for nonthinking are documented by [llama.cpp CLI](https://github.com/ggml-org/llama.cpp/blob/master/tools/cli/README.md) and [Gemma 4 llama.cpp discussion](https://github.com/ggml-org/llama.cpp/discussions/21338), with acknowledged template-version failure possibilities. A model tool error is not a scientific negative.
