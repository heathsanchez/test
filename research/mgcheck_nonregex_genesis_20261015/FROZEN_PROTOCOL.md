# PREREGISTRATION — MathGraph Check non-regex method acquisition, 2026-10-15

## Objective and failure gate
The live/qualified incumbent (source-bound Go regexp/syntax derivation, original source→native predicate bridge) works only where a changed regexp is found. On truly non-regex source, it must return typed UNKNOWN / NO_MATCHED_PATTERN_CHANGE, not invent a successful verdict.

A separate **fixed-before-source-inspection meta-searcher** must decide whether to construct a NEW executable verification *plan* (not a new human-programmed generator language) from its general predeclared AST/callable/observation primitives, instead of targeting a human-named operation or using author test examples. The plan must arise at runtime from evidence and be persisted, ablated, and reused. Do not alter the plan search algorithm, baseline corpus, ranking, native test emitter or extraction grammar after inspecting ANY target source, changed patch, native result or author test. Only an implementation/syntax/infrastructure bug that can be shown without per-target specialization may be corrected, but affected targets cease to be clean holdouts after it.

## External independent original targets — metadata ONLY examined before freeze
(1) Acquisition source: `spf13/cast` original PR #352, base `6fd6afdc9df068c662e923a7c3ad04fda4647121` → contributor head `9e3a7c487e18826a2482ad34ff29c58221a0c85b`, *closed unmerged*. Public PR title mentions surrounding spaces in string numeric casts.
(2) Pre-frozen transfer: `Masterminds/semver` original PR #303, base `8b89c86cb53c57cfd5d07c13de12bc4d78954e99` → contributor head `c9706646b4e12416632860dd87d388c2eed07052`, *closed unmerged*. Title mentions surrounding spaces in version/constraint parsing.
(3) Source-distinct orthogonal probe: `shopspring/decimal` original PR #428, base `f658fbf1eb94abc869558633a0b9b239300899f4` → author head `1fc621e247bcaa551e84a3a49608515ef9cbf13e`, *merged*. Title mentions Unicode minus.

**Contamination caveat:** the titles and source family selection make this retrospective/semi-informed, NOT a blind defect discovery. Original contributors supplied the patches and any existing tests. All external source is fetched read-only in owned GitHub Actions and no upstream fork/PR modified.

## Precommitted generative operation grammar
Before seeing code, implement one target-independent native Go AST planner with no target/repo/function/example/operation names in source. It may extract exported original Go functions with EXACTLY one `string` or `interface{}/any` parameter and exactly two returns, last `error`, plus a bounded set of other safe parse signatures. It must derive candidate interface inventory from *source* and optionally changed Go files, not from author tests, and emit one ordinary Go native test that logs typed return/error observation on deterministic generated input candidates under both exact original Go revisions. Module dependencies are loaded only on GitHub Actions runners. No author test source or pull-request body is eligible for generation.

The *human-written* available primitives are:
- finite type-safe seed production: digits `0,1,2,9`, alphanumerics, signs, decimal integer, two-/three-dot segments, optional prefix, ASCII/Golang escaped string/rune literals mined from production source only;
- transformations `IDENTITY`, `EDGE_SPACE` (prefix/suffix/both ordinary whitespace), `RUNE_SUBSTITUTION` (change a sign or character to a rune actually mined from source), `CASE_VARIANT`, and `CONCAT_SMALL`; expansion order fixed before execution;
- `OBSERVE_RETURN_ERROR`: compare success/error and stable typed result form from real native execution, never Python-host equality, never trust CI green alone;
- method synthesis as a *program record*: composition of `SOURCE_PUBLIC_PARSE_INTERFACE` → one or more of the above transformation operators → `EXECUTE_ORIGINAL_GO_API` → `COMPARE_TYPED_OBSERVATION`. Search chooses a plan based on actual verified source-variant observations, not a per-source manual operation manifest.

Zero-code adaptation and plan reuse on the second frozen source family required to claim bounded method transfer. If first selected plan fails transfer, classify UNKNOWN_TRANSFER rather than retune or substitute per-target branch. The third family is a separate protected challenge to acquisition of a different plan using the SAME fixed meta-searcher and vocabulary.

## Strong baseline and cost
For each target run the fully informed conventional native *differential enumeration* control given the SAME discovered APIs, old/head source, complete typed input set and Go compiler, without method selection. It must produce the same witnesses whenever the selected plan succeeds (otherwise the test is invalid); record actual candidate counts, Go build+run time and method selection cost, not declare novelty or superiority. A smarter conventional source-aware fuzzer could also generate equivalent programs, and no reviewer time benefit is measured. The strongest warranted win is causal *retention/reuse* of a discovered executable plan, if it genuinely saves future selection cost under the same inputs and verification boundary; no value claim absent full-lifecycle accounting.

## Required native and negative controls
- Fetch/validate full original SHA and head SHA; wrong identity refuses UNKNOWN.
- Actually execute prior source regexp method and confirm zero matched changed pattern before claiming a new method.
- Compile and run native tests against original source in isolation. If base observation differs from head and same frozen input reproduces this under independently generated single-witness tests, record exact result; do not count simple author test transplantation.
- Physical delete / disable synthesized method must return UNKNOWN (even if baseline finds a difference).
- Absent/withdrawn original evidence must refuse/stale.
- Reject no-call/nil-test false passes. Distinguish compilation/setup failures from behavioral mismatches.
- A missing or tied best plan is UNKNOWN; do not force a green test or reinterpret head as universally correct.
- No action authorization, automated patch or merge, cloud deployment, third-party writes, Gmail, Render, outreach, ARIA submission.

## Epistemic states and stop criteria
INTERESTING: source AST admits plausible new operation.
CANDIDATE: executable plan JSON generated with source identity and primitive sequence.
WARRANTED_BOUNDED: original native implementation differences on source-generated tests + full equality-informed baseline, artifact, controls, and frozen target results.
WARRANTED_BOUNDED_TRANSFER: same exact retained method selector/plan template genuinely transfers to second independent source, with no per-target human code.
REJECTED: unchanged or wrong behavior in protected source; keep failures.
UNKNOWN_L7: no self-authored new primitive, no independent stronger reviewer win or outside user adoption. Do not call a fixed human-designed plan grammar novel meta-language invention, even if a new combination is discovered.

## Frozen falsifier
The crucial falsifier is **a new, necessary operator not expressible by the above finite fixed grammar**, which the system must autonomously create rather than be hand-coded after seeing it. If any head's change requires such an operator and the procedure returns UNKNOWN, retain that evidence. This is a genuine test of the current capability boundary rather than a reason to extend the grammar afterward and claim the same holdout.

All original fatal runner failures, broad UNKNOWNs, comparator ties and negative evidence remain in ROS.
