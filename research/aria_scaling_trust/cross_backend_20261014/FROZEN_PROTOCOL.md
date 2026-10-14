# Frozen cross-implementation consequence experiment — 2026-10-14

**Freeze precedence:** This protocol is committed **before fetching the held-out HowlFrame PR patch, native test content, or source-code changes**. Target selected using public repository/PR metadata and title/description only. No upstream writes or contact.

## Historical training/control source

- Original OPA differential failure: `open-policy-agent/opa` [PR #9216](https://github.com/open-policy-agent/opa/pull/9216), original base `37030a09d6088821a473f486fd75dd81ef394b74`, author head `d231b0381efd880597db736efdd74e6681000b54`.
- The preceding frozen [OPA protocol](https://github.com/heathsanchez/test/blob/aria-mathgraph-check-opa-9216-heldout-20261014/research/aria_scaling_trust/opa_9216/FROZEN_PROTOCOL.md) and [native run #38548773394](https://github.com/heathsanchez/test/actions/runs/38548773394) already qualified two bounded Go interpreter-vs-Wasm disagreements on original base and their removal on author head.
- Original MathGraph Check analyzer remained `BEHAVIORAL_SCOPE_UNKNOWN`, detected **0/2** named OPA issues; no self-discovery or review advantage was qualified.

## Sealed held-out new source family

- Independently owned external repo `howlcipher/howlframe`, [PR #75](https://github.com/howlcipher/howlframe/pull/75) merged in October 2026; **original base SHA `21efc6cb4742d7ae101288dfc67819bb549c1307`**, contributor PR head `151a033119a6f1acd3c7adce2524ce0768178be9`.
- Distinct from OPA: original numeric contract across multiple execution backends (interpreter, VM, Go, JavaScript), rather than Wasm string-replace order/termination.
- Public PR text already describes the intended fixes. **This is NOT blinded mathematical discovery of an unknown defect.** No claim the PR is unsafe or that its current published branch remains broken.
- Before first held-out patch read: only the repo and PR identity, base/head, broad language/backend family, and publicly disclosed author problem description are known. New/changed test identifiers, file paths, input literals and exact source modification logic have NOT been observed or selected.

## Predeclared proposed transferable operation

Find a **source-derived executable differential consequence**: detect relevant native test entry points from the *original contributor's added/modified test declarations*, replay exactly the same test behavior on the untouched base source and author head, and—where the source provides runnable backend parameterization—identify an input for which two independently executed backends disagree on base but agree on head.

The operator may use ONE generic Go test-discovery/execution mechanism across repositories; it must **not contain per-target imports, HowlFrame file names, semantic literals, patch-line rules, or a hard-coded list of expected failed tests**. If the source cannot be mined/executed without human glue, report `UNKNOWN_ADAPTER_NEEDED` rather than a transfer success. If the original tests cannot run on base due missing dependencies/APIs, report `UNKNOWN_ORIGINAL_BASE_TEST_NOT_RUNNABLE`, not a repaired bug.

An explicitly separate *diagnostic evaluator* may assess any provided pinned CLI/native witness, but **supplying a target-specific command manually does NOT qualify autonomous generation**. Explicitly count human operator configuration, native build+test time, checks, restarts, and control inputs.

## Frozen gates and strong equal-information baseline

1. **Original source:** exact Git commits, toolchain, source file blobs, and new regression-test selection must be reproducible. Do not silently use repository `main` head or user-provided verdicts.
2. **Observable native counterfactual:** old base + original new test RED, original author PR head + same test GREEN, independent native runner, and unchanged prior baseline tests GREEN, or explicitly `UNKNOWN` with failing stage. Distinguish build/setup failure from semantic rejection.
3. **Cross-backend distinction:** name and reproduce the two backend outcomes when the original test program permits, including bounded timeouts. A whole-suite red/green **alone** does not establish backend-specific disagreement.
4. **Protected controls:** test deletion/ablation removes the detection; tampered source commit/test bytes fail pin; duplicate/reordered original tests don't manufacture another capability; retained exact evidence survives independent cold restart. No execution of untrusted PR scripts on an authorized production host; only ephemeral CI sandbox.
5. **Equal-information baseline:** conventional reviewer/source-aware stateless baseline sees **entire original title/body/diff, contributor tests, exact GitHub CI, same native executable oracle and equal compute/time budget**. Since author disclosure already names issues, do not claim reviewer-discovery advantage unless matched prospective results actually support it. Count time/cost including candidate selection and infrastructure.
6. **Outcome types:** `WARRANTED_BOUNDED_GENERAL_OPERATOR_TRANSFER` only after original OPA and held-out HowlFrame source-native independent executed backend outcomes and the *same unmodified* generic extractor pass the frozen gates; `WARRANTED_BOUNDED_TEST_REPLAY_ONLY` if merely author test RED→GREEN; `REJECTED_TRANSFER` for failed held-out selector; `UNKNOWN` for setup/artifact limits.
7. **No semantic cheat:** no literals for numeric conversion, wasm replacements, parity bug names, expected values, custom per-case rewriting; no L7/self-generated grammar claim for any **human-authored** generator. No outside-owner MathGraph Check installation, no new upstream fix, no product adoption or economic superiority without evidence.

## Procedure/lineage

- Branch: `research/cross-backend-witness-heldout-20261014`; build only after this freeze is stored in GitHub.
- Historical original OPA and already-qualified independent Go method-IR experiments remain immutable controls; do not edit their frozen outputs.
- Preserve first red attempt and all future genuine failure logs and complete command/source digest receipts; annotate status rather than cherry-pick.
- Run in `heathsanchez/test` owned sandboxed CI. No unsolicited external PR comments, GitHub Checks POST, Render, Gmail, outreach or production MathGraph changes.
