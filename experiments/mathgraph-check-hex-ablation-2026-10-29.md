# MathGraph Check — Green-but-Wrong TestSuiteBench V0

**State:** CANDIDATE / BOUNDED POSITIVE. **Not:** a product-level or agent-vs-agent victory.

## Objective

Test the narrow hypothesis that boundary/interaction-directed probes catch failures missed by conventional example tests, holding test count (48) and the independent expected-output checker fixed.

## Frozen experiment

- Benchmark: ETH SRI TestSuiteBench, commit `583d2eb1ffa19f3aa0c04b7455fd13d846b4c8d9`.
- Task: `sitkevij__hex.61ae69b`; spec-only construction, no mutant/reference source inspected.
- Test generator: `scripts/mathgraph_testgen_ablation.py`.
- Runner commit: `af1904f30f60e8a7ac8216af642b2d151e18220a`.
- Official scored workflow: [40796353794](https://github.com/heathsanchez/test/actions/runs/40796353794).
- Artifact: [12863344738](https://github.com/heathsanchez/test/actions/runs/40796353794/artifacts/12863344738), sha256 `3665c4b47fa09c58b4e4e55e9369dadfd04d3016efca387482190357d0acb3df`.
- Both suites: 48 reference tests, 48/48 pass, no binary errors.

| Method | Mutants killed | Mutation score |
| --- | ---: | ---: |
| Conventional one-dimensional examples | 8 / 54 | 14.8% |
| Boundary/interaction probes | 10 / 54 | 18.5% |

Relative lift: (10 - 8) / 8 = 25%; absolute lift: 2 / 54 = 3.70 percentage points.

Exact mutant kill sets:

- Baseline: repo_16, repo_17, repo_18, repo_23, repo_29, repo_30, repo_32, repo_36.
- Boundary/interaction: repo_17, repo_18, repo_23, repo_28, repo_29, repo_30, repo_32, repo_33, repo_34, repo_36.
- Common: 7. Only signature: repo_28, repo_33, repo_34 (array modes and input boundaries). Only baseline: repo_16.
- Combined union: 11/54, derived from result vectors (not separately executed).

## Important failure in our own evaluator

Initial workflow [40796040523](https://github.com/heathsanchez/test/actions/runs/40796040523) had a green GitHub Actions status despite **0 recognized tests and 55 binary errors per suite** because `:task_patched` was absent. That evidence is **REJECTED** as a score, retained as the motivating false-green observation.

Follow-up commit `af1904f30f60e8a7ac8216af642b2d151e18220a` prepared the official image and added a fail-closed assertion: every suite must execute exactly 48 tests on the reference with no reference error. Corrected scored run passed this assertion.

## Boundary / residual

**WARRANTED:** This manually engineered, equal-count probe-selection ablation was reference-valid and killed 2 more mutants in this single task. It reveals complementary—not superseding—coverage; preserving existing tests is essential.

**UNKNOWN:** Out-of-sample repetition; statistically reliable gain; autonomous test generation capability; improvement over equally informed conventional coding agents; commercial demand; production incident reduction; concrete A-severity issue discovery.

**Cheapest decisive next experiment:** Blind, preregistered multi-task evaluation with identical model, input specification, token/time budget, and mutant-hiding conditions. Run standard agent prompt vs MathGraph Check residual/interaction prompt. Score ground-truth validity first, mutant kills second; preserve failures and cost. No upstream issue or PR should claim this result as a product benchmark.
