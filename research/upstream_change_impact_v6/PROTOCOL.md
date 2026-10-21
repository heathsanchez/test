# V6 — prospective external-upstream change impact, frozen before source inspection

Date 2026-10-22. Source owner: **Pallets**, independent of Metalogic.
Exact official upstream repository: https://github.com/pallets/markupsafe
Immutable commit: 4e111271b1494995708a9e878a10829b5e10c7ba (2026-10-03).
No alternate upstream selection or post-exposure source-family tuning.

## Locked task
Select the first eligible Python return expression in the upstream **src/markupsafe/_native.py**, depth-first function order, whose AST expression has no named-expression/yield/await and whose function has no binding/reference to fixed temporary name `_mg_equivalent_result_v6`. Replace exactly `return EXPR` with `_mg_equivalent_result_v6 = EXPR; return _mg_equivalent_result_v6`. This is a control-flow-preserving *proposed* refactor, not a certified general Python equivalence: locals(), tracing, profiling and frame introspection can distinguish the result. Explicitly inspect for these risks and do not claim universal preservation; if eligible code cannot be safely located, STOP UNKNOWN. No changes to upstream tests or requirements. Do not submit a PR upstream.

## Baseline/test selection
Use actual upstream tests selected by default native pytest discovery, not invented tests. Frozen risk model treats any test that imports the package directly/indirectly, dynamically loads the source, or reads source text as possibly impacted and must KEEP. An omitted real test is admissible only if exact pinned source and test identity plus closed import/effects allow independence under a stated execution boundary. If all upstream tests depend on MarkupSafe, report ZERO safely skipped.
Strong conventional dependency-aware baseline: direct test-to-module imports and an independently executed coverage-based call/reference check (where available), with same target source and test suite; do not compare solely to naive filenames. The conventional selector is allowed to select all tests.
Mutation: inject into a temporary cloned test (not committed upstream) a dynamic import or source-introspection dependency on target; proposed skip MUST retract. Inject a semantic-changing implementation perturbation and require native behavior/regression failure. Exact source hash and diff must be recorded.

## Native execution
GitHub Actions checkout upstream at fixed commit into isolated directory. Install isolated package/test dependencies as supported by upstream pinned metadata; run original upstream suite and changed suite with the same test command and runner, record counts and timings. If upstream installation or native tests cannot execute reproducibly, return UNKNOWN_ENVIRONMENT rather than fabricate results. No synthetic pass substitution. Run a conventional equal-information selection and full baseline.
Any performance claim must include discovery, qualification, negative controls and native runs. Protected product release remains UNKNOWN unless whole-required regression and independent source authority admitted by real MathGraph release mechanisms. Do not claim universal Python-equivalence theorem, cross-kind Lean proof, or economic superiority.

The experiment is hosted in an owned research branch only. R7.2, CLC, MathGraph production verification/warrant modules remain unchanged.
