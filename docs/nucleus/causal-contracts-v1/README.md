# Nucleus causal contract paths v1

## Qualified current authority

Head `b7d7baebf8485122fe02afe2e8d910189551cfe2`, branch `nucleus-causal-contracts-v1`; [run36819395684](https://github.com/heathsanchez/test/actions/runs/36819395684) SUCCESS. Artifact11142848175 (54186bytes), downloaded and SHA256 verified: `d90f37ba8642bf936a460a715f1bc0dfd048963cebf68adc386cc6de38104676`.

- 179 normal Rust tests and181 diagnostics Rust tests pass; 16 Python planner/report/capture checks pass in CI. Capture was also checked to fail on the uninstrumented base.
- All387 pinned verdicts agree across base, normal and diagnostic builds. Current110A/60R/24U; frozen108A/61R/24U; zero wrong/errors/regressions/changes.
- All24 terminal declaration scopes captured, none truncated or preflight-incomplete.
- **3 composed candidate paths**: Option in two files and Except in one. Their actual existing recursor-shape check passes.
- **2 representation/applicability residuals**: both SourceInfo files fail that check at stage14, the constructor/minor field-type comparison. The pinned source identifies `optParam Bool false` versus `Bool`.
- **12 typed conversion residuals**, including both masked application-function-type errors; **7 other inductive admission residuals**.
- Total planner output:3 CANDIDATE_PATH,21 NO_REGISTERED_PATH. No new semantic authority or Arena decision is earned.

The direct-reuse test falsified a tempting five-way collapse and found the extra adapter obligation. This is the consequential result of applying the diagnostic Crystal move.

## Initial shape-only result and boundary

Diagnostic restoration, not a semantic promotion. The executable semantic base is `0659bc671a4ef536ed4a096deacd0c61b1ca927e`. Candidate verdict changes: zero. No complete-checker backstop, official submission or merge.

First replay: `b2c0c08a87e458aaca7c44e9ac82fb1347188d36`, run [36818178960](https://github.com/heathsanchez/test/actions/runs/36818178960), artifact `11142407451`, downloaded ZIP SHA-256 `6e6455248407f99a81e1f5aed3d581de6eaf5854b06d724afe53dcdb371724e4`.

Current194: **110 ACCEPT / 60 REJECT / 24 UNKNOWN**. Frozen193: **108 ACCEPT / 61 REJECT / 24 UNKNOWN**. Exact base, normal candidate and diagnostic candidate agree on every test. Zero wrong verdicts, errors and regressions. Both app-lam controls pass under an 8 MiB launcher stack.

## What the instrument establishes

- Five residual occurrences have a measured admission-route miss and a shared observed nonrecursive multi-constructor envelope. They map to one **CANDIDATE** sum/telescope derivation path. This does not establish a valid generalized admission law.
- Twelve terminal declarations contain failed typed comparisons. In two, an application inference wrapper masks `distinct-neutral-heads`: `RBTree.id_spec` and `structEta`.
- Seven other residuals stop at inductive admission, with no registered path.
- All24 terminal scopes in the measured artifact are present; no trace-limit or detail truncation occurs.

The first failed Bool-matcher check is `Eq.refl` at expression7407 in the pinned pair-n7 input; inferred type expression110 is compared with expected expression7398, in four local binders, under GuardedSemanticFallback with budget65475. This is a replay locator, not a diagnosis that reflexivity is unsound or needs a new rule. Expression/frame identifiers are local to the pinned export/execution. Frame debug values are identities, not standalone environment serialization.

## Qualified measured frontier

| Test | Terminal observation | Planner status |
|---|---|---|
| `init-prelude` | Sum: field annotation mismatch | NO_REGISTERED_PATH |
| `perf/args-before-unfold` | Typed conversion | NO_REGISTERED_PATH |
| `perf/folded-constant-first` | Typed conversion | NO_REGISTERED_PATH |
| `perf/folded-constant-last` | Typed conversion | NO_REGISTERED_PATH |
| `perf/fueled-chain` | Sum: existing recursor shape passes | CANDIDATE_PATH |
| `perf/grind-ring-5` | Sum: field annotation mismatch | NO_REGISTERED_PATH |
| `perf/magma-list-deep-n21` | Sum: existing recursor shape passes | CANDIDATE_PATH |
| `perf/magma-list-deep-n36` | Sum: existing recursor shape passes | CANDIDATE_PATH |
| `perf/magma-list-pair-n21` | Typed conversion | NO_REGISTERED_PATH |
| `perf/magma-list-pair-n7` | Typed conversion | NO_REGISTERED_PATH |
| `perf/shared-subterm` | Typed conversion | NO_REGISTERED_PATH |
| `tutorial/082_RBTree.id_spec` | Typed conversion; application mask | NO_REGISTERED_PATH |
| `tutorial/112_structEta` | Typed conversion; application mask | NO_REGISTERED_PATH |
| `bugs/nested-unused-param` | Other inductive admission | NO_REGISTERED_PATH |
| `bugs/proj-of-stuck-prop` | Other inductive admission | NO_REGISTERED_PATH |
| `bugs/proj-of-subst-prop` | Other inductive admission | NO_REGISTERED_PATH |
| `bugs/rec-missing-ih` | Other inductive admission | NO_REGISTERED_PATH |
| `bugs/rec-of-subst-prop` | Other inductive admission | NO_REGISTERED_PATH |
| `perf/refute-cheap-first` | Typed conversion | NO_REGISTERED_PATH |
| `tutorial/100_ruleKbad` | Typed conversion | NO_REGISTERED_PATH |
| `tutorial/101_ruleKAcc` | Typed conversion | NO_REGISTERED_PATH |
| `tutorial/111_indexedUnitEta` | Other inductive admission | NO_REGISTERED_PATH |
| `tutorial/113_indexedStructEta` | Other inductive admission | NO_REGISTERED_PATH |
| `tutorial/125_accRecNoEta` | Typed conversion | NO_REGISTERED_PATH |

## Warrant and limitations

The offline registry binds the measured existing recursor syntax check and three recent qualified capabilities (Iff function-proof singleton, closed three-field record, bounded proof-type conversion). The adapter does not manufacture validated-premise witnesses from observed shapes. Consequently **NO_REGISTERED_PATH is relative to this registry and adapter**, not evidence of global capability saturation, an impossible composition, or a genuinely absent semantic law. No zero-cost applicable composition has been demonstrated by this experiment.

The sum path requires both observed nonrecursive shape and an actual route-miss event. Option/Except reach the binary-enum name/schema gate; SourceInfo reaches unsupported constructor cardinality. The preserved declaration records retain differing parameter/universe/constructor telescopes. Sharing a path ID does not erase those obligations.

Comparison traces preserve expression IDs, inferred/expected types, local type context, frame IDs, level substitutions, policy, budget and conversion outcome at the failure point. The report explicitly does not equate every speculative failed comparison with a minimal root cause. It retains input SHA256 and terminal declaration identity for replay.

## Historical lineage and correction

Historical graph `6fa0fe1245bdc08c1520acf22461689ce6fff0b4` / run35981575301 established a16-occurrence/one-path diagnostic collapse on an older193 frontier, granting no semantic authority. It was absent at0659. Its planner mixed derived interfaces into the seed set, permitting a downstream warranted edge to lose an upstream candidate dependency. The new offline planner retains subset-minimal support sets, counts shared dependencies once, excludes cross-observation contracts, and reports bounded search as UNKNOWN.

The rejected coarse fixed-point grammar (run36343465543: unknown_multiset/depth_language/event_language) is not revived. Current grouping requires evidence from the actual failure sites.

## Review and verification

Fresh read-only review found one Important issue: a suppressed terminal boundary could attach prior declarations to the final object. Commit4c368dcb6b770f7165b5722d92c5175bdb60d8c3 separates unattributed events and preserves incomplete status. Regression test observed RED then GREEN. The two coverage comments were addressed: report tests gate CI and the capture test requires a comparison in the terminal scope.

The normal Rust suite and diagnostics suite run in CI. Python planner/report tests run locally; the real-corpus capture test runs RED on base and GREEN on candidate in CI. No local Rust SDK was available.

## Refinement after the initial shape grouping

The blanket direct-reuse hypothesis failed at commit `36949b396aa706083870d8b8c4054ec56819948b`, run36819075234: the existing recursor-shape probe returned false for at least one of the three families. The failed capture assertion is preserved; it was an experimental hypothesis failure, not a wrong kernel verdict.

Direct inspection of the pinned `init-prelude` export identifies a structural separator in `Lean.SourceInfo.synthetic`: the third constructor-field annotation is `optParam Bool false` (expression8060), while the corresponding minor-field annotation is `Bool` (expression879). The existing validator uses syntactic equality with bound-variable shifts at that seam. The final hosted trace confirms the mismatch at stage14 in both SourceInfo files. This suggests reusing checked type conversion on field annotations, not inventing a new equality axiom. No such adapter is yet qualified.

The diagnostic probe now has conservative metadata bounds, a4096-expression-occurrence work cap and depth64 preflight; literal payloads are excluded. It records incomplete evidence instead of invoking the recursive validator beyond these bounds.

## Smallest consequential next experiment

First test the checked field-type conversion adapter exposed by SourceInfo, then compose it with the already measured recursor check and a bounded, safe, nonrecursive, nonindexed Type-valued sum admission envelope across Option/Except/Lean.SourceInfo. Independently validate parameter and field telescopes, uniform constructor returns, universe bounds, motive/minor telescopes, rule binder annotations and field order, metadata and runtime iota premises. Validate real dependency slices and malformed neighbors, then require full194/193 zero-wrong reclosure. Do not count prerequisite gains as final Arena verdict gains. The12 conversion obligations remain separate pending exact replay and applicability diagnosis.
