# Frozen external PR evaluation protocol — 2026-10-14 NZDT

## Selection (frozen BEFORE viewing the patch, CI traces or running MathGraph)
- Independent repository: `open-policy-agent/opa` (policy engine, Go and Wasm execution).
- Target: [original external PR #9216](https://github.com/open-policy-agent/opa/pull/9216), author head `d231b0381efd880597db736efdd74e6681000b54`, merged 2026-09-17. Title/description metadata may be known to a conventional reviewer before analysis; patch/test run is not yet inspected by us at freeze.
- Reason for preselection: the returned metadata describes a cross-runtime semantic discrepancy (Wasm vs native topdown) and a termination edge case, matching the *trustworthiness of a downstream decision across implementations*. Not selected from any earlier MathGraph example (the prior 8 original PRs all from IEANTN or Go YAML). May fail for practical CI reasons; no substitution permitted without a new registered protocol.
- No upstream PR edits, comments, requests for app installs, outreach or email.

## Comparators and information fairness
A. **Actual existing MathGraph Check** shared `analysis.mjs` without modifications, over exact historical GitHub PR metadata/diff and exact-head GitHub Actions API. Run as read-only shadow in OUR GitHub Actions. Do not claim a MathGraph App Check was posted to OPA.
B. **Conventional fully informed reviewer baseline**: access to the SAME PR title/description/diff, existing upstream CI, and any source tests, plus running original author tests when feasible. The reviewer is a documented manual-evidence pathway, **not a measured human subject**. Do not call it a blinded human experiment. The PR description itself already discloses the semantic bug and fix; do not conceal it from baseline.
C. **Original author native regression oracle**: identify tests added in original patch without implementing target-specific fixes. If practical, execute the original tests on original predecessor and exact author head; otherwise report NATIVE_REPLAY_UNKNOWN and explain. Native pass/fail does not imply general correctness.

## Frozen outcome gates
1. MathGraph meaningful finding must *independently* identify a difference in what can be relied upon across two policy-evaluation engines or specifically identify an untested behaviour. A generic `BEHAVIORAL_SCOPE_UNKNOWN` is not a substantive discovery and counts as NOT_DETECTED, even if it is a safe conclusion.
2. Baseline reviewer has full original PR description, which explicitly identifies `strings.replace_n`, overlapping pattern priority, single-pass and empty-key termination. This is legitimate baseline evidence; the user does not benefit if an assistant merely repeats it.
3. Scope of available CI must be represented honestly: no CI at exact head means CI_UNKNOWN; a green suite before the added regressions does not prove parity; differences in revisions require exact source identities.
4. On verified native red(base)–green(head), claim only a bounded regression established by **upstream-authored test/fix**, never MathGraph-generated repair or source/requirements equivalence.
5. Quantitative metrics: exact correct residuals named, false authority promotions, missing findings; tool CPU execution times and source retrievals if measured. Human review time and improvement **NOT_MEASURED**. Any fake second independent operator/reviewer is forbidden.
6. If A produces no source-specific finding, conclude **MathGraph Check v0 did not match fully informed conventional baseline on this held-out source**, even if the system remains safely neutral. This is a useful negative, not a reason to insert fitted AST code post hoc and call it held-out.
7. External App installation/adoption, cloud deployment, funding or PR merge must never be inferred. `action_authorization=NONE`.

## Protected non-effects
Work entirely under `heathsanchez/test` research branch; GitHub Actions reads third-party original source but posts NOTHING to third-party GitHub. Existing MathGraph PR #167, mathgraph.org, Cloudflare and app secrets must not be modified. No Gmail, Render, outreach, no ARIA submission.
