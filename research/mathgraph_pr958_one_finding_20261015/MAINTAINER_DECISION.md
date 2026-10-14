# One consequential maintainer decision — Go YAML PR #958

**Verdict:** PR #958 passes its original native test suite and repairs **69/130** independently generated nested-YAML semantic checks, with **zero** introduced regressions in that matrix. Twenty additional tests fail on both base and head.

**One finding:** All 20 surviving cases are `|+` / `>+` YAML keep-chomping trailing blank-line losses, already reported in [upstream issue #872](https://github.com/goccy/go-yaml/issues/872). The contributor explicitly scoped #958 to indentation, not this older concern.

**Action for maintainer:** Do **not** block PR #958 solely on issue #872. Evaluate the small, separate `ast/ast.go` [patch](./issue872_preserve_chomp.patch) and its native evidence independently.

**Causal qualification:** Original PR head **20/130 fail**; scoped one-file repair **130/130 pass**; repair removed **20/130 fail** again. Existing Go test suite remains green. Five inherited NaN/infinity string controls are unchanged. [Native repair run #38560167831](https://github.com/heathsanchez/test/actions/runs/38560167831), [artifact #11891373353](https://github.com/heathsanchez/test/actions/runs/38560167831/artifacts/11891373353).

**No misleading authority:** This is a human-designed source-specific repair after source-independent regression tests. Neither autonomous verification-method invention, a novel issue, universal YAML correctness, formal proof of merge safety, nor external adoption has been established. We made no changes to the original repository or its PR.
