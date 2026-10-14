# ReviewBench × MathGraph Check — frozen first admission experiment (2026-10-15)

Goal: establish that a source-pinned reviewer adapter runs unmodified under the official ReviewBench contract, and separately test whether its *existing* verified source checks add genuine findings over a matched model baseline. This is NOT a claim of semantic-bug discovery, model superiority, or leaderboard score.

Authority: review-bench/ReviewBench source revision 5bba258937cc7d43577ce9a81a389a6550a20fa9; official public test indices **4, 5, 8, 9, 17, 18, 21** (four Python, three Go). Their repository/head SHAs are in the pinned corpus/test/test.json and must not be replaced ad hoc. Golden findings are never read by the reviewer. Only benchmark PR metadata, base/head Git objects, diff, and working source are permitted. No upstream review comments/later commits or web search. Fresh container per task.

Arms:
- baseline: same one-call model reviewer, only when separately configured with an explicit model and credential. Otherwise NOT_RUN_NO_MODEL_OR_CREDENTIAL, not zero-defect evidence.
- mathgraph: same model call and prompt plus deterministic source-anchored compiler regression checks. Candidate input is bounded to changed Python/Go files; a syntax finding is emitted only if exact base parses, exact head does not, and the error line is in/near the actual changed hunk. Failed source identity/visibility is an error, not success.

The compiler check is **not** the existing L7 autonomous semantics engine, and the two model arms do not share a frozen model response. Therefore any cross-arm difference from model stochasticity is not attributable to MathGraph. Bounded source differential checks are only a technical admission gate. Existing ROS stateful observer and repair modules are retained as externally validated predecessors, **not silently claimed as integrated** into this first adapter.

First execute four source-negative controls (base→head detection, repaired head, SHA mismatch, malformed output), then seven real ReviewBench tasks under the official try-agent.sh. Record container exit and JSON validity per task. Do not run a judge, access golden findings, submit to leaderboard, publish an image, alter production GitHub App/Cloudflare, or spend on a model unless explicitly configured. Persist log/artifact and exact run commit; a zero-finding output is only a valid interface, **not a proof of review quality**.

Promotion thresholds: WARRANTED_BOUNDED_ADAPTER requires 7/7 genuine contract executions plus source/negative controls; WARRANTED_REVIEWER_SUPERIORITY requires an independent blinded matched strong tool-using reviewer, attributable improvement on novel real cases, measured precision/recall/time/cost, and held-out repetition. Until then, superiority = UNKNOWN.
