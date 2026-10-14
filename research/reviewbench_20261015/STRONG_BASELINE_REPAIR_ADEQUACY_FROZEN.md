# Strong-reviewer-informed repair adequacy gate — frozen before new native test code

Date: 2026-10-15 NZDT. **This is a retrospective, fully-informed adversarial follow-up, not a fresh detection or a live matched model comparison.** Original prior [PR #9 native SHA-freshness qualification](https://github.com/heathsanchez/test/actions/runs/38630767862) is warranted only on its four specified tests. Do not supersede that by a broader claim.

## Baseline authority

- External original: review-bench/k1LoW_gh-copilot-review original PR #9 source at exact Git SHA `f98281938e63acd1d2df9b89d6af98dcf58c9fa8`.
- Original known proposed source-to-contract repair: our previously human-coded `NEW_FUNCTION` in `research/reviewbench_20261015/replay_semantic.py`; do NOT rewrite this patch in the first experiment.
- Credible comparator: [ReviewBench published golden](https://github.com/review-bench/ReviewBench/blob/5bba258937cc7d43577ce9a81a389a6550a20fa9/golden/k1LoW_gh-copilot-review_9-f9828193.json) Git blob `4c49ff2fb925df6bcfecf30472e82f5b01fee4a0` evaluated AFTER the original native result. Strong Claude Sonnet 4.6 correctly calls out **(A) commit pagination beyond 30**, **(B) review pagination beyond 30**, and **(C) timestamp-vs-commit identity**; Opus 4.7 separately noted contract/implementation mismatch. The published golden also contains false positives. It is not a new invocation with the same tool/time budget. Model cost NOT MEASURED.
- Benchmark golden is **not injected into official ReviewBench adapter** and no leaderboard score is computed. It is an explicit fully-informed outside evaluator for *repair adequacy*, not for measuring live model discovery.

## Decisive question

Does the **already qualified** subject-identity patch close the strong reviewer's additional consequential concerns, or did our four-case green test silently become an unsupported "verified resolution" claim? Freeze two genuinely separate **real GitHub pagination** obligations:
1. 31 commits, review attached to true current 31st commit, only 30 commits in REST first page, Link next. PR freshness should return true under authoritative current-head review; comparing to first page's 30th commit is wrong.
2. 31 reviews, Copilot's matching-current-head review on the next page; first page contains 30 non-Copilot reviews, Link next. Freshness should return true, not false.

Both are externally published strong-reviewer TPs and NOT new MathGraph discoveries. The native Go test uses original mocked HTTP RoundTripper, sets pagination Link headers and provides an actual next-page response. If original and candidate fail two scenarios while candidate still passes the prior four SHA/clock cases, the correct conclusion is `PARTIAL_RESOLUTION`, NOT `MERGE_SAFE` or `COMPLETE`. If Go client already paginates automatically, refute the strong-model concern on this source and retain negative result rather than forcing expected failure.

## Verification and stop rules

- Fresh clone original ReviewBench mirror exact source SHA; check immutable source Git head; no upstream writes.
- Native run on exact **unmodified original**, **previous original candidate**, then physically **restore original bytes**. Execute both original four-case suite and new two-case pagination suite as separate named test functions; exit and individual test names must match expected. Record raw native logs and SHA hashes.
- Expected: original identity suite FAIL, candidate identity PASS, removal identity FAIL; first source and candidate pagination test FAIL if strong reviewer pagination concern is executable. Negative control: with **one page** both original patch and published source should retain ordinary behavior.
- Generate one reproducible fully-typed `reviewer_resolution.json` with bounded evidence, comparator result, unclosed residual, source/patch identities, and honest `unknown` for full repo, user time, novel defect, generic L7 and reviewer superiority.
- No grant of merge authority, external GitHub PR comments, review requests, installed App changes, CodeRabbit/Copilot write, Cloudflare/Render/Vercel deployment, Gmail or other outreach. Existing 14/14 ReviewBench adapter gate and live Cloudflare receipt remain separate.

## Promotion

`WARRANTED_BOUNDED_PARTIAL_RESOLUTION_ASSESSMENT` if original tests prove the first repair and independent native paging tests show it still leaves published TP concerns unresolved. This is an **evidence-backed rejection of false generalization**, which may be useful to maintainers. It is not an advantage over a strong model already naming the same issues. For genuine commercial differentiation, next measure reviewer attention/cost on a prospective, strong equally informed trial with actual model execution and users.
