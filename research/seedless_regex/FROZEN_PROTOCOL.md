# Frozen source-only regex witness test — independent sixth repository

Frozen 2026-10-15 NZDT, BEFORE inspecting code diff, run logs, original test sources for ozzo candidate.

## Development calibration, already known
- [go-playground/validator original PR #1664](https://github.com/go-playground/validator/pull/1664), original base `df91dfdd9abdbb838739d13a70550efb7f730d3e`, original contributor head `a37c290428207fcaf419d295cde1fc432fa37c9e`. Prior experiment source-derived a new input by one-character mutation of original author's positive test `EK-01-A03-FK-01`; this does NOT qualify seedless generation. This source is calibration only.

## Newly frozen independent sixth-source transfer
- [go-ozzo/ozzo-validation PR #208](https://github.com/go-ozzo/ozzo-validation/pull/208), upstream Go validation library unrelated to validator; base SHA `dbba76d963f16ad2ea78fd8fb7d36564783cb3c4`, author's repaired PR head `48423ae967b5ed417f9076caa37e83f24b29dccd`. Selection uses original PR title/body only; code patch/test files NOT inspected at freeze.
- PR description says E.164 regex mistakenly allows missing `+`; a correct E.164 prefix requires `+`. Original example in author body is known; **MUST NOT copy that example, author tests, or any positive seed into generated witness**. This is a retrospective already-known defect, NOT an unknown new upstream bug.
- The *unchanged previous* Go AST+regex map/test-table generator may not understand ozzo's regex grammar; if so, report exact structural obstruction. Do not hand-edit it to fit ozzo and misrepresent transfer.

## Executable experiment frozen before implementation
1. One human-authored generic seedless Go regexp AST method, not a per-repo regex recognizer: mine before/after anchored literal regex declarations from source diffs, pair only if identity unambiguous, and synthesize bounded minimal candidate strings solely from AST operators (literal, char class, concatenation, alternation, repetitions and optional branches). Validate against actual compiled *original old/new regexp*; require old/new acceptance differs. Do not use upstream test samples, PR body example, original author input seed, LLM to author target-specific string or any source-file target offset.
2. Run same unchanged tool on validator **calibration** and ozzo **held-out transfer**, pinned exact original source SHAs, compare original regexp predicates by Go `regexp.MatchString` in native GitHub Actions. Classify witness direction and exact input. If source regexp cannot be paired, syntax unsupported, ambiguity unresolved or generated candidates fail to separate, return UNKNOWN with obstruction; do not swap target after seeing results.
3. Additional original native PROGRAM integration (if possible): automatically find original affected test operation/function from source location and run a generated test on original predecessor vs author head. Without a secure source-test bridge, report REGEXP_ONLY and do not claim observable library behavior.
4. Independent requirements oracle: original author’s E.164 contract is description only; old/new regex acceptance does not prove conformity to external telecom standards. Report semantic authority SOURCE_REGEXP_DELTA, not THIRD_PARTY_SPEC_VERIFIED.
5. Negative controls: identical old/new regex => UNKNOWN, swapped head => reversed direction, invalid source SHA => UNKNOWN, no reference => UNKNOWN, withdrawal => STALE, restart results equal excluding volatile durations. No false promotion or action/merge authorization.
6. Strong equal-information conventional baseline can do same regex/syntax witness test; no measured reviewer time/cost or first-party customer adoption. Method HUMAN_WRITTEN, not autonomous generator-of-generators/L7, no target-specific branching.

## Protected boundaries
Only own `heathsanchez/test` isolated branch and Actions. Third-party repos read-only, no GitHub App install in outside repos, no outreach, no Gmail, Render, ARIA submission, Cloudflare/MathGraph website/product deployment or merges.