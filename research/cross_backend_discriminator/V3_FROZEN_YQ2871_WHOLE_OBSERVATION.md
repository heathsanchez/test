# V3 whole-source-observation contract — frozen before validation patch inspection

Status at freeze, 14 October 2026 NZ: previous V2 original source builds succeeded but source test mining failed on both original revisions. [jaq #423](https://github.com/01mf02/jaq/pull/423) changed documentation examples, not Rust test files; [yq #2869](https://github.com/mikefarah/yq/pull/2869) added one complete Go test expression but the miner admitted a nested regex string as a standalone jq program. [Original V2 CI #38554850248](https://github.com/heathsanchez/test/actions/runs/38554850248), failing jaq #11889331352 and yq #11889016463 artifacts retained. Both cases are now DEVELOPMENT/CALIBRATION, not untouched validations.

## Fresh frozen original upstream source
[mikefarah/yq PR #2871](https://github.com/mikefarah/yq/pull/2871): feature adding jq-compatible if/then/elif/else/end conditionals. Original base ef305adbe5a703a994f431812e0521d81f5f8668, contributor head 88566f7676af10192bc5bd5bd3bdab13ca8956c6, merged 29 September 2026. Only PR title/body metadata have been read, not its code patch, tests or docs. Contributor disclosed Claude Code assistance; no original code authored by MathGraph. PR description includes example expressions and a caveat that missing-key/no-output behavior is not universally equivalent to jq, so the grammar and tested property must be constrained.

## NEW GENERATOR construction hypothesis (freeze before inspecting #2871 patch)
Use ONE HUMAN-WRITTEN generic observer-structure extractor that preserves a complete original source-authored observation:
- changed Go/Rust source TEST scenario fields (whole expression, source file, input, expected output); raw Go string literals should not be decomposed into partial regex strings;
- changed documentation/example code expressions with authored result where present;
- native C jq syntax/behaviour permitted as independent reference only when entire expression is supported, not because nested quoted fragments happen to be syntactically valid;
- compile original Go yq BASE and contributor HEAD exact immutable SHAs and execute the same source-derived whole expression with a small bounded canonical JSON input domain.
- If original predecessor rejects an expression but author HEAD and native jq agree, label a bounded NEW_SUPPORTED_OPERATION, NOT repaired value mismatch. Keep resource errors, grammar incompatibility, parse errors, stale source and missing evidence typed UNKNOWN.

## PREDECLARED decisive success
At least one whole if/then/else expression automatically extracted from an original added test/doc source line without hard-coding that operation string in generator or experiment. Compare original C jq and source-pinned HEAD yq behaviour equal on at least one bounded input; original prior yq must be observably unable to execute the operation or return a different value. If the algorithm must be changed after seeing original validation patch, declare FROZEN_VALIDATION_FAILED, and preserve that evidence; do not rerun same PR as a newly held-out win. If original source lacks eligible complete examples, return UNKNOWN, not positive.

Necessary negative controls: no source test/doc gives UNKNOWN, no independent reference gives UNKNOWN, source withdrawal gives STALE, wrong original SHAs rejected, exact source run and input evidence attached, no side effects or merge authority. A competent fully informed traditional reviewer sees original author examples too; no measured superior decision, speed or L7 autonomous generator invention claims.

## Limits
This is a different PR within already calibrated yq repo; not a fourth independent repo. One source-derived procedural success remains human-authored extractor and originally authored test. No outside-user product adoption. No Gmail/Render/outreach/ARIA submission. No writes to any external repository, production MathGraph App or Cloudflare.
