# Real PR #958 — one consequential missing behavior test

Target: [goccy/go-yaml PR #958](https://github.com/goccy/go-yaml/pull/958), original source \`edee2f91616c6d73112a13e7c0dbde72ce938877\`, proposed head \`a34b94ecb553bb5a693296c30232a89026db79ca\`.

Frozen protocol commit: \`04b3d8c098841c8833f8055329e56048ad4d3d7c\`, **before looking at the contributor's patch**.

The human-authored Go native test compares standalone YAML block meaning against the same bytes-marshaler fragment embedded into 5 nesting contexts under 2 indentation settings across 13 source fragments (130 generated checks). The source-independent oracle uses the *unchanged* library's own parser on each stand-alone fragment and checks exact decoded structure. It includes folded, literal, chomping, explicit-indent, Unicode, plain/quoted controls.

A separate inherited-bug control checks 5 \`.nan\`/\`.inf\` string-typing cases known from prior work. It is **never** attributed to this PR if base and head both fail. Both original repository test suites are checked separately.

Decision contract: classify each check by base/head statuses; alert on an *introduced* semantic regression only when a baseline-pass becomes a new head-failure. Historical base-fail/head-pass are repairs. Both-fail are residuals, not PR-caused. No report may declare correctness of all YAML, automatic bug discovery by an LLM or newly generated self-improvement method. No upstream GitHub write, customer install, PR comment, public review or website action.

If an introduced regression appears, smallest resolution is **not yet established** until native red/green/ablation on the isolated patch; do not fabricate it.
