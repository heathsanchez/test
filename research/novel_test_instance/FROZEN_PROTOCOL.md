# Frozen candidate for a NEW native assertion instance — 15 October 2026 NZDT

## Fifth independently maintained source-family (pre-inspection registration)
Chosen from public PR title/description only: [go-playground/validator PR #1664](https://github.com/go-playground/validator/pull/1664), original base `df91dfdd9abdbb838739d13a70550efb7f730d3e` → contributor head `a37c290428207fcaf419d295cde1fc432fa37c9e`. The PR reports extending Nigeria postcodes from an older 6-digit-only format to a new 11-character segmented format. The author wrote the code and original tests. This historical known defect is **not a newly discovered upstream bug**.

## Intended new operation, frozen before patch inspection
Do NOT pass a target Test name, postcode example, operation tag, expected validity result, file offset, or test-specific source code in an implementation manifest. Use a single human-coded generic Go AST procedure:
1. Under exact source Git SHAs, parse the original Go test source changes and extract Go test functions newly added or old named test functions with newly appended input cases.
2. Generate at least one **new source-file test instance** not byte-identical to anything in the contributor's original test patch by automatically changing exactly one string literal input using a bounded substitution alphabet/number grammar, retaining the original Go assertion logic.
3. Use original author's tests as *semantic template and oracle*. This is **inherited authorship of assertions**, NOT novel assertion synthesis, no L7 generator. If an attempted mutation changes the expected output or breaks original semantic intent, native author head must FAIL and candidate is discarded.
4. Run resulting exact generated Go test on original unmodified implementation source with only test-file changes versus original author repaired source. Require **test-executed and t.Error/Fatal** (not compile/setup red) on base and identical generated test **pass** on head; record original fixed test vs newly generated test source digests and diff. The generated input may not be present in the author's test-file patch. Require source-level novelty and no direct source fixes.
5. Negative controls: choose generated mutations with head FAIL (reject them), remove new generated test function on pristine base (Go no-test green -> UNKNOWN), test-only removal/withdrawal -> STALE, wrong SHA -> refuse, restart same successful pipeline and compare typed stable results.
6. Strong equal-information conventional baseline gets the exact same author template, source and mutation budget: it can mutate the original tests too, so reviewer advantage/time savings NOT PROVEN unless actually measured. Record candidate-count, native process cost, acceptance rate, human-authored glue and source/correctness limitations.

## Outcome/stop conditions
If the original author edited only existing data without a movable Go native test wrapper, or generator needs per-target handwritten semantic logic or prefilled test names/input, status = UNKNOWN/FAILED; don't quietly change frozen target. If it produces a new source-distinct test instance and native RED(base)/GREEN(head), claim only bounded **generated witness-input/test-instance construction under an upstream-authored oracle**. Never call that autonomous invention of semantic test oracle or L7.

Only owned heathsanchez/test research branch/Actions modified. Third-party source fetched and compiled read-only. No new GitHub App install or outside-owned repo writes, no Gmail, Render, outreach, ARIA submissions or production changes.
