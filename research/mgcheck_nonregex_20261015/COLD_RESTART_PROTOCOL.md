# Unchanged-method independent cold runner — 2026-10-15

Re-run the SAME frozen general non-regex method source and original pinned PR revisions under fresh GitHub-hosted runner instances; no new method operations, no source-specific probes, no test scope widening and no author test fixture imports. Compare semantically normalized results from the original [green exact-head run #38607065226](https://github.com/heathsanchez/test/actions/runs/38607065226).

Source-independent Go method source was frozen on branch before either original implementation patch was inspected. Core method blob SHA: `e48824b2db9c28130bc501a5e1508a505453f393`. The only changed branch file is this documentary restart trigger, not the method or Actions workflow.

Predeclared expected semantic observations (counts at tested input domain):
- shopspring/decimal original base `f658fbf1eb94abc869558633a0b9b239300899f4` → author head `1fc621e247bcaa551e84a3a49608515ef9cbf13e`: `NewFromString` 21 acceptance-status changes; minimal qualified witness `−0`; 1219 diagnostic-only differences excluded.
- Masterminds/semver original base `8b89c86cb53c57cfd5d07c13de12bc4d78954e99` → author head `c9706646b4e12416632860dd87d388c2eed07052`: `NewVersion` 3746 acceptance-status changes, minimal `\\t0`; `StrictNewVersion` 1495 changes, minimal `\\t0.0.0`; `NewConstraint` ZERO semantic changes, 2662 diagnostic-only differences excluded. Retain this negative/UNKNOWN; do not tailor grammar to known constraints from contributor tests.
- Old regexp method fails both as `REJECTED_NO_MATCHED_PATTERN_CHANGE`.
- Physical source-missing/wrong-SHA controls return UNKNOWN, generated-test removal prevents semantic observation.

Accepted comparison: same exact source/head pins, method blob hash, input counts, per-function status-transition counts, witnesses and physical-guard verdicts. Elapsed times, ZIP hashes, Go build paths and runner metadata may vary and must not be claimed identical.

This is BOUNDED source-derived method-program construction within a pre-authored grammar, NOT L7 new meta-method-language invention, independent blind defect discovery or measured reviewer benefit. Fully informed conventional differential testing can reproduce results.
