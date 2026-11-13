# C147: complete N7 BVar1/2 binding-identity revisit census

**Status: WARRANTED_BOUNDED diagnostic measurement; not a proof-reuse certificate.** Source commit [`74b0966bf693e926057d3f8cdbf02c80e0f73e2f`](https://github.com/heathsanchez/test/commit/74b0966bf693e926057d3f8cdbf02c80e0f73e2f), native [run #43510018126](https://github.com/heathsanchez/test/actions/runs/43510018126) **SUCCESS**, source and complete release Rust regression **340 passed, 0 failed, 17 ignored (40 suites)**. Frozen original N7 NDJSON SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`; **C105-descendant surrogate**, not recovered production C124/C125b. Native artifact `14078552270`, ZIP SHA256 `a7878f0dccec5549be327a037b19713a1b2fb8a9a7b1b9958ac55e06ed3e1bbb`.

The independent projection-target workflow on the same source [#43510018034](https://github.com/heathsanchez/test/actions/runs/43510018034) also passed. The original Arena standard-budget verdict remains `UNKNOWN`; the raised-budget verdict is `ACCEPT`. No original standard-budget UNKNOWN has closed.

## Complete read-only census

C147 visits every BVar1/2 evaluator head at the C143/C145 exact captured RHS producer, source expression IDs `6` and `11`. It records two deliberately optimistic equivalence classes:

* Full-environment **weak reference**: `(ExprId, EnvFrame ID)`.
* Actual used-binding **weak projection**: `(ExprId, immutable EnvBinding node ID at the BVar index)`.

Both erase the current closure's universe-level substitution and its complete pending argument spine, **only to observe possible repeat events**. These are not safe result-replay keys. The source machine distinguishes those dimensions elsewhere. The observed projected repeat-event count is a ceiling for any stricter key which retains binding identity, but neither the difference of distinct weak-key classes nor the repeat counts upper-bound *incremental safe-key cache savings, fuel savings or CPU savings*.

| Exact exposure | Low first | Low second | High completed |
| --- | ---: | ---: | ---: |
| Total evaluator head visits | 63,908 | 60,444 | 12,761,384 |
| Source BVar1/2 visits | 7,577 | 7,037 | **1,400,538** |
| Full-env weak unique | 4,193 | 3,910 | **831,910** |
| Used-binding weak unique | 3,873 | 3,605 | **767,428** |
| Full-env weak repeat events | 3,384 | 3,127 | **568,628** |
| Used-binding weak repeat events | 3,704 | 3,432 | **633,110** |
| **Additional weak-key collapse** | **320** | **305** | **64,482** |
| Missing bindings / overflow | 0 / false | 0 / false | 0 / false |

The exact high source count conserves C143's original source expression census: Expr6 `896,349` plus Expr11 `504,189` equals **1,400,538**. Silent and diagnostic executions have identical verdict exit/status and stdout. The C147 source manifest asserts original-byte SHA, source expression site, aligned head counts, no missing bindings, and an explicit `UNKNOWN_OVERFLOW` status on cap saturation. The native parser tests and full release test gate passed.

At the optimistic level, 633,110/1,400,538 (~45.2%) head visits repeat a bound-node identity, and 64,482 events (~4.6% of target visits) are additionally merged relative to the weak full-environment key. **This is a substantial revisit signal, not established reusable computation.** The C146 1/256 sample of complete context saw only six extra collisions, because selection based on full closure can miss other members of a projected class. These experiments are complementary rather than conflicting.

## Residual and cheapest decisive experiment

**C148 CANDIDATE**: sample *entire binding-node classes*, not isolated full closures, at a stable moderate rate and compare:

1. exact `(Closure { ExprId, EnvFrame, LevelSubstitution }, complete pending Vec<Closure>)`, versus
2. projected `(ExprId, LevelSubstitution, immutable used-binding node ID, complete pending Vec<Closure>)`.

This recovers C146's semantic distinctions while fixing its full-closure-based sampling bias. First inspect the pending-spine distribution, memory/overflow and proportion of projected repeated events that still collide with complete context. Mark sampling limitations, retain source parity and full Rust regressions. **No unchecked weak-key cache publication**. Even a positive exact-context sample would require a separate, proved/certified one-step binder transport before value/result reuse, and a measured standard-budget reduction before claiming Nucleus closure.

Lineage: C142 source work → C143 source ID census → C144 source AST → C145 action mix → C146 fully-distinguished 1/256 full-closure sample → C147 all-visit weak binding census → C148 proposed binding-class grouped exact-context sample. The six original valid UNKNOWNs and source-qualified full Mathlib remain OPEN.
