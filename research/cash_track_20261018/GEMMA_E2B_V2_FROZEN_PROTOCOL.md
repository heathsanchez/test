# Gemma 4 E2B CPU V2 — frozen truncation-separator protocol (18 October 2026)

## Lineage and falsifier

Original frozen V1 [protocol 4aec77a8](https://github.com/heathsanchez/test/commit/4aec77a860d3d6ff8c427ae9ae5ec173a5527bff) and independent [CI #39096545823](https://github.com/heathsanchez/test/actions/runs/39096545823) were executed on exact original Go source with GGUF SHA256 8e30dff3ac4c8434c49a7036fa15564bdbb6044e42bf04550bf1a096ad7e6a52. The one V1 model response had content="", reasoning_content nonempty, finish_reason="length", exactly 240 completion tokens (prompt 1931). V1 classification REJECTED_INVALID_JSON is retained. Original source independently ran 7/7 named tests with 6 PASS/1 FAIL as expected. Original downloaded artifact #12125006444 SHA256 6f8332f482b0a91aa7a9849ce9c4902ed35c000d000aee4a3f152480d2648722 independently rehashed and opened.

This is an **explicit second experiment**, not a disguised retry of the original fixed 240-token test.

## Precommitted V2 modification

- Preserve exactly the V1 model identifier/quantisation/digest, original Go base source commit, original source excerpt lines 244–336, task text, system instruction, seed 181026, temperature 0, llama.cpp tag b11433 (commit 50569eb87df530daff11afda229ceb9ab8e6cae8), CPU-only, 4096 context, one local inference request, frozen original seven Go tests and physical causal restoration.
- **Single changed inference factor:** `max_tokens = 1024` rather than 240. This is an *apparatus budget* correction to test whether the reasoning_content overflow prevented final output. No output repair, model re-prompt, patch rewriting or post-result grammar adjustments.
- CPU standard GitHub Actions on one separate workflow. Do not run the V1 workflow again; V2 is tagged as its own attempt and must report its actual model output.
- Required result categories: `REJECTED_INVALID_JSON` / source mismatch / native repair false / successful bounded one-patch native test / UNKNOWN_ENVIRONMENT. A model answer that is not JSON is scientific rejection, not a green patch.
- Equal-information strong model comparator remains NOT_RUN. A positive result is **one small previously public PR repair under frozen independent native oracle**, not prospective unknown bug discovery, G2, or overall coding-agent superiority.
- Archive prompt SHA, model response, separate reasoning_content vs final content, token usage, complete original and candidate native test logs, source identity, artifact SHA. If V2 content still empty, preserve its second negative and STOP; no V3 automatic rerun.

The original V1 is forever a separate negative in ROS and competition papers. The V2 successor can be promoted only inside its own declared budget. No Kaggle submission, commercial deployment, external code write or paid GPU.
