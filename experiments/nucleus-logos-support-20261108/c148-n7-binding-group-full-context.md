# C148: binding-group samples retain complete universe/pending context

**WARRANTED_BOUNDED sample, not certified reuse.** Exact source commit [`9c7dbabe0b62a0e6b7870c4da80bd114cceee9bf`](https://github.com/heathsanchez/test/commit/9c7dbabe0b62a0e6b7870c4da80bd114cceee9bf) and [native CI #43512160555](https://github.com/heathsanchez/test/actions/runs/43512160555) **SUCCESS**: C148 original source replay with conservation and silent-verdict parity, all earlier C126–C147 source steps, **340 Rust tests passed / 0 failed / 17 ignored across 40 suites**. Uploaded artifact `14078644302` ZIP SHA256 `165babed4b70982166497b592e91bbdb30a9f2df54e0836c787e0fa72e4903ac`; same-source C125 projection target [#43512160573](https://github.com/heathsanchez/test/actions/runs/43512160573) **SUCCESS**. Original unchanged Arena N7 export SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`. Still **C105-descendant surrogate, not recovered C124/C125b production**; standard-budget N7 UNKNOWN, high-budget N7 ACCEPT.

## Source-qualified experiment

At the exact C142/C143 captured N7 right-hand producer, source BVar1 and BVar2 are immutable expression IDs `6` and `11`. Their 1,400,538 high-budget visits are independently conserved against the C143 expression-ID census (`896,349 + 504,189`). Each visit first resolves its actually used immutable environment binding-node ID. A deterministic 1/16 predicate on `(ExprId, binding-node ID)` selects **complete projected classes**, unlike C146's sparse selection by full environment. Both compared keys retain complete `LevelSubstitution` and complete ordered pending `Vec<Closure>`:

* Full: `(Closure { ExprId, EnvFrame, LevelSubstitution }, complete pending spine)`.
* Used binding: `(ExprId, LevelSubstitution, immutable actual binding node ID, complete pending spine)`.

No value is cached, no proof witness is reused, and no verdict or budget semantics are modified. A 200,000-unique-key memory cap yields explicit UNKNOWN on saturation, not partial positive evidence. The source-qualified parser checks complete head census, target IDs, accounting, no missing bindings, and parity against an instrument-free checker execution.

| Captured exposure | Low first | Low second | High completed |
| --- | ---: | ---: | ---: |
| All evaluator heads | 63,908 | 60,444 | 12,761,384 |
| Source BVar1/2 visits | 7,577 | 7,037 | **1,400,538** |
| Entire binding-class sample visits | 349 | 227 | **68,666** |
| Sampled visits with nonempty pending | 122 | 85 | **16,036** |
| Full-context unique | 229 | 191 | **42,110** |
| Binding-projected full-context unique | 229 | 179 | **38,024** |
| Full-context repeated visits | 120 | 36 | **26,556** |
| Binding-projected full-context repeats | 120 | 48 | **30,642** |
| **Additional full-context collisions** | **0** | **12** | **4,086** |
| Missing bindings / overflow | 0 / false | 0 / false | 0 / false |

The sample is 68,666/1,400,538 (~4.9% of visit events); it is deterministic and class-complete, **not an unbiased statistical sample or a full-population upper bound**. The 4,086 extra collisions (~5.95% of selected visits) cannot be extrapolated directly to every source visit. By contrast, C147's full-population *weak* keys ignored levels and pending and measured 64,482 additional collapses; its repeat count is not proof-safe. C146 sampled full closures (not groups), saw only six additional matches among 9,262 and could miss nearly all projected aliases. C148 reconciles the mechanism without claiming a universal rate.

## Residual: transport the proven local binding, not arbitrary checker results

**C149 CANDIDATE**: formalize or otherwise independently certify this narrow local lemma: when two BVar sites have the same immutable bound-node identity, their one-step bound lookup resolves the same immutable `EnvBinding` regardless of unused enclosing frames. Retain the actual expression, authority, universe substitution, complete pending spine, transparency, projection policy and resource accounting at any larger evaluator boundary. Distinguish the local BVar step from replay of a **completed exposure**, which may depend on richer context, recursive state and budget. Before promoting a cache, require (a) a source/independent proof of the transport, (b) unchanged forged-proof negatives and complete regressions, and (c) a direct source-qualified reduction in standard-budget work or closure of a formerly UNKNOWN unchanged case. No diagnostic quotient is admitted as a production memoization key yet.

Lineage: C142–C145 source-work decomposition → C146 fully-contextual full-closure sample → C147 complete weak-key census → **C148 complete binding-group contextual sample** → C149 certified transport candidate. Six original valid standard-budget UNKNOWNs, full Mathlib source acceptance, and production C124/C125b recovery remain OPEN.
