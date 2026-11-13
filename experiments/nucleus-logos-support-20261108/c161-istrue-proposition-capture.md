# C161: the 407 `Decidable.isTrue` heads retain 407 distinct exact proposition closures

**WARRANTED_BOUNDED, observational only.** The tempting shortcut after C160—quotient all 407 completed expensive `Decidable.isTrue` results by their constructor head or their source proposition expression—is **rejected**. In the frozen high-budget `magma-list-pair-n7` replay, all 407 results have distinct *full exact proposition closures*, distinct proof closures, and distinct ordered proposition/proof closure pairs. Yet those 407 proposition closures originate from only two source expression IDs (350 from `ExprId(7218)`, 57 from `ExprId(9)`). This is an especially strong example of the difference between shared source shape and shared captured meaning; neither equality nor inequivalence of the evaluated propositions has been established.

## Immutable evidence and lineage

- Exact independent C125b checker source `d8be1443f2f1352634aaf333a282f32e7ec8a719` with the isolated read-only diagnostics patch [C161 source `fd72e051`](https://github.com/heathsanchez/test/commit/fd72e051b7b6f157b4f0df3bb350b0bc96693cff), branch `research/nucleus-c161-istrue-proposition-bindings-20261114`.
- Frozen original Arena N7 `good/perf/magma-list-pair-n7.ndjson`, SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`; original 196-case source ZIP SHA256 `f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2`.
- [C161 native Action #43526113427](https://github.com/heathsanchez/test/actions/runs/43526113427) **SUCCESS**, job `132232166971`, artifact `nucleus-c161-istrue-field-distinction-receipt` ID `14085346818`, GitHub artifact digest `sha256:21d5300966e91259a1594955340e3e552195d0a5c8cff60f52cefe745f850638`.
- C159 [captured-binding regression](https://github.com/heathsanchez/test/commit/4656be1c6d12fa2415d657f27a0bd9b0838f5c1b) and C160 [same-constructor-head observation](https://github.com/heathsanchez/test/commit/bb99235227922083d86d07b9a8360f3ce8df1de6) are preserved, not superseded. The failed earlier C160 workflow gate `#43524753049` was a receipt multiplicity parser issue and remains recorded separately.

The source export independently identifies `NameId(144)` as `Decidable`, `NameId(146)` as its `isTrue` constructor and shows **one inductive parameter and one constructor field**. For **this N7 source**, the registered recursor `NameId(147)` has `isTrue` RHS `ExprId(531)`; do not transplant RHS expression IDs from a separately frozen N21 export. The two argument slots in each `isTrue` neutral value are accordingly classified as the proposition parameter and proof field. `ExprId(9)` is `BVar(3)`; `ExprId(7218)` is a `forallE` proposition with nested binder context. These are source *syntax* facts, not normalized proposition equalities.

## Exact native counts

| Measure on completed expensive producer `ExprId(8799) @ Env0` | Original standard budget 65,536 | Diagnostic budget 14,155,776 |
| --- | ---: | ---: |
| N7 verdict/exit | `UNKNOWN` / 2 | `ACCEPT` / 0 |
| Full exact-key-distinct expensive completed results | 0 | **407** |
| Actual `Decidable.isTrue` with zero universe levels/two arguments | 0 | **407** |
| Unexpected head/arity | 0 | 0 |
| Distinct exact proposition closures | 0 | **407** |
| Repeated exact proposition-closure groups | 0 | **0** |
| Largest exact proposition-closure group | 0 | **1** |
| Distinct proposition *source expression* IDs | 0 | **2** |
| Distinct `(source ExprId, level substitution)` shapes | 0 | **2** |
| Largest source-expression group | 0 | **350** |
| Distinct exact proof closures | 0 | **407** |
| Distinct exact proposition/proof pairs | 0 | **407** |

The 350-source group is `ExprId(7218)` and the 57-source group is `ExprId(9)`. The original low-budget four attempts granted 507, 507, 65,055, 65,055 evaluator steps, with no completed expensive result. The original high-budget three attempts granted 507, 507, 14,155,295 steps; the final attempt produced 407. These are not 407 different globally replayed proofs; they are 407 distinct completed internal expensive calls in one unchanged N7 replay.

The native gate checked C161 enabled/disabled **byte-identical non-observer stderr, stdout, and verdict**, frozen original N7 low UNKNOWN/high ACCEPT, the pinned three adversarial outcomes **1/2/1 (none ACCEPT)**, repeated C151–C160 observational/protected gates, and the native Rust diagnostics tests with **0 failures**. It did **not** replay the full frozen original 196 cases, 403 protected corpus, all Mathlib, or the other five standard-budget UNKNOWNs. No production evaluator behavior or cache lookup was changed.

## Decision and smallest useful next experiment

- **PROMOTE C161 to WARRANTED_BOUNDED:** all 407 completed expensive constructor values have exact proposition and proof closures distinct under their full captured environments, despite only two proposition source expressions.
- **REJECT head-only proof reuse**, source-ExprId-only memoization, and source-plus-level-substitution-only caching as unsafe without additional checked preconditions. C159 gives a concrete captured-binder counterexample to the general principle.
- **Do not infer 407 distinct *mathematical propositions*.** Exact closure inequality is weaker than semantic inequivalence. Nor may proof irrelevance erase the proposition parameter: proof irrelevance concerns checked proof terms of a *fixed* proposition.
- **C162 CANDIDATE (cheap and read-only):** for `ExprId(7218)` and `ExprId(9)`, compute their *source-syntax free-de-Bruijn-variable support under binders*, and classify the 407 proposition closures by an exact projection onto **only required captured bindings**, retaining universe levels. First determine whether any projected groups truly coincide. If yes, prove a source-checked environment-restriction lemma before trial caching; if no, reject projected closure quotient and pursue a constructor-specific typed reduction/induction. In both cases preserve no-ACCEPT adversarial controls and original standard-budget N7 verdict until a separately qualified semantic patch succeeds.

**Status:** the six original valid 65,536-step UNKNOWNs, unqualified whole-Mathlib replay, and independent soundness obligations remain OPEN. This result narrows a possible optimization; it does not claim to finish Nucleus.
