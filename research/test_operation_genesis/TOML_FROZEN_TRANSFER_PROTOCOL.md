# Freeze — source-derived Go test operation transfer to BurntSushi/toml, October 14 2026

## Previous source-qualified algorithm (unchanged semantics)
Generic Go AST original-source test selector at [commit `54e45529`](https://github.com/heathsanchez/test/commit/54e455290e5781c66235f6e8558dc4b9f0f9263e), originally qualified on goccy/go-json PR #697, automatically selected newly added original Test function and applied only original test-file patch to predecessor. Do not change generic detection or per-target manually specify target test function names.

## NEW fourth, independent original source (frozen BEFORE reading patch)
[BurntSushi/toml PR #488](https://github.com/BurntSushi/toml/pull/488), original source base `277ecb0abd5e5945cf4c0a5cf3668759a27aa7fd` and contributor head `24ca3d8dcb474537da393351a75ccaa42c65cae4`. Chosen using original PR metadata only, which reports a local TOML date/time round-trip bug under non-UTC environments. The original author says a new round-trip test was added. **Do not inspect test name, file paths or diff until this protocol is committed.** Original author wrote the repair/test; not an unknown new upstream discovery.

## Frozen transfer gates
1. GENERALIZE ONLY source repository and exact frozen SHA parameters of the previously qualified selector; do not change Go AST test operation extraction logic or new-test requirement. Replace hard-coded goccy commit constants with CLI-provided pins and pass those pins in workflow. Preserve the existing go-json case on source-specific old workflow. Any per-target test-name whitelist/semantic helper is forbidden.
2. Retrieve only original git source at the two immutable commits; programmatically extract newly added original Go Test functions in a changed `_test.go` file, and exact original test-only patch (no implementation code changes), source hash-check.
3. On original predecessor source plus identical contributor-authored test require real `t.Error`/`t.Fatal` assertion fail (not compilation/set-up) and original contributor head with same test pass. If newly authored test is only part of an old test function, the unchanged extractor must return `UNKNOWN_NO_NEW_NATIVE_TEST_OPERATION` and this is a **transfer FAIL**, not a case to retrofit and reselect.
4. Local dates/times depend on timezone; set an explicitly declared controlled non-UTC native environment `TZ=America/New_York` for both base and head, report environment; do not adjust code/test names to force success after seeing result. A UTC-only match is not evidence against the defect.
5. Physical causal ablation: untouched old source without author test = `go test` not executing the selected operation, must yield UNKNOWN. Evidence withdrawal = STALE, zero action authorization.
6. Fully informed git diff + Go native test conventional reviewer could get same conclusion. No claim of measured review-time/cost advantage, no autonomous creation of novel tests, no Go semantics theorem or L7 generator self-invention.

## Scope
Only own research branch and GitHub Actions, original third-party source checkout READ-ONLY, no upstream changes, comments or installation; no Gmail, Render, external outreach, ARIA submission, production MathGraph or Cloudflare modifications.