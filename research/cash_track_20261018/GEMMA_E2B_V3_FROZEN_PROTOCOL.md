# Gemma 4 E2B V3 — frozen non-thinking separator (2026-10-18)

## Lineage and independent question
V1 [39096545823](https://github.com/heathsanchez/test/actions/runs/39096545823): 240/240 reasoning tokens, no final content, REJECTED_INVALID_JSON.
V2 [39097185412](https://github.com/heathsanchez/test/actions/runs/39097185412): 1024/1024 reasoning tokens, no final content, REJECTED_INVALID_JSON.
V2 required STOP, with no V3 automatic rerun. This document explicitly authorizes **one new, separately frozen V3 inference**, and not a V2 retry.

Question: Under an explicit non-thinking chat template, can the identical Gemma 4 E2B inference produce an admissible one-regex JSON patch, and if so does it pass the same seven original Go-native protected tests?

## Locked controls
Reuse V2 exactly: ggml-org/gemma-4-E2B-it-GGUF gemma-4-E2B-it-Q4_0.gguf SHA256 8e30dff3ac4c8434c49a7036fa15564bdbb6044e42bf04550bf1a096ad7e6a52; llama.cpp tag b11433 SHA 50569eb87df530daff11afda229ceb9ab8e6cae8; target OllyInsurance/fern-platform base ee843f4babd4c05e819aa86701e409b58e328c66; exact V2 task, system instruction, original source excerpt 244–336; temp 0; seed 181026; max_tokens 1024; context 4096; original independent heldout_fern_outage_test.go fixture; patch only the one declared-outage regex; no upstream author patch in prompt. Only inference-mode factor changes: request chat_template_kwargs.enable_thinking=false and server --reasoning off. Neither is a parser-only alteration.

## Admission and evidence
Use exact unchanged V2 decode(), apply_exact(), native original baseline, 7/7 named native validation, source identity and physical original failure restoration logic. Preserve original full model_response.json, raw prompt, final and reasoning fields, finish_reason, usage and hashes. No output salvage, no retries, no alternate model, no manual edits, no paid inference, no Kaggle submission. A green Actions workflow is not a model success. If no admissible JSON, report REJECTED_INVALID_JSON/REJECTED_OUTPUT_SCHEMA or relevant refusal and do not test a fabricated patch. If native test fails, REJECTED_MODEL_PATCH_NATIVE. If runtime fails or nonthinking mechanism is unsupported, UNKNOWN_ENVIRONMENT. An accepted one-task repair is WARRANTED_BOUNDED_ONE_MODEL_PATCH, not general programming superiority or prospective G2. Preserve V1/V2 negatives and the lack of equal-information comparator. No V4 automatically.

## Trigger protection
Only the newly added V3 workflow may trigger from changes to its own workflow file on existing draft PR #126. Workflow has read-only permissions; archives logs; no workflow_dispatch, no push trigger, no retries.