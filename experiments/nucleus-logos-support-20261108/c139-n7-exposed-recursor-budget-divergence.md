# C139: exact deferred comparison exposes a stuck recursor at standard fuel

Status: **WARRANTED_BOUNDED** on C105-derived diagnostic surrogate. No change to checker judgments, fuel or semantic authority; **six original standard-budget valid UNKNOWNs remain**.

Native green [run 43495827090](https://github.com/heathsanchez/test/actions/runs/43495827090), artifact ID `14070914792`, artifact ZIP SHA256 `e48561e1bd3d83f4f92adc88aecc5de831db475e22752f8946c876c7e1e4f192`. Frozen unchanged original source `good/perf/magma-list-pair-n7.ndjson` SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`. Source-qualified observer ON/OFF emitted identical verdict and stdout at both 65,536 standard and 14,155,776 high diagnostic budgets. Fifteen parser tests passed; Rust native build and prior C126–C138 steps green.

The exact second deferred worklist equality has unchanged source identities: `Expr1@Env66182@Levels[(NameId18,Succ(Zero))]` versus `Expr8799@Env0@Levels[]` at depth 0. Both operands' ordinary `expose_for_conversion` return PROVEN value judgments at each budget, **but not the same value shape**:

| Exact `compare_values` entry | Standard budget | High diagnostic budget |
| --- | --- | --- |
| Budget at entry | 65,250 | 14,155,490 |
| Left exposed value | Neutral Const NameId169, 0 levels, 0 args | Neutral Const NameId169, 0 levels, 0 args |
| Right exposed value | Neutral Const NameId147, 1 level, 5 args (qualified recursor) | Neutral Const NameId169, 0 levels, 0 args |
| Neutral heads | UNKNOWN | PROVEN |
| Fallback one-step probe | 32,625, UNKNOWN | not invoked |
| Outcome | UNKNOWN | PROVEN; both spines empty |

**Correction to an easy overinterpretation of C138:** both exposures return a `PROVEN Value`, but that does **not** establish fully normal forms or equality. At low budget the right value is still a source-qualified recursor neutral; at high budget it has reduced to the same constructor-like constant as the left. The high checker does not gain its proof from completing the low one-step recursor fallback trial. The different values arise **inside exposure**, prior to comparing heads. No permission to equate the unmatched neutral heads follows.

**Engineering residual:** determine the source-owned reduction path for `Expr8799@Env0@Levels[]` and which certified recursor evaluation step is repeated, truncated or budget-exhausted at standard fuel. The smallest next experiment is to trace `expose_for_conversion` for only that exact closure, including source-qualified normal-form status and budget/major-work counters. If a sound resumable continuation or completed exact subproblem can be retained without identifying unrelated captured frames, test it as an optimizer; require unchanged 71 forged, protected 403/403, all original 196, and eventually complete Mathlib qualification before promotion.

Lineage C133→C134→C135→C136→C137→C138→C139. The historical unpushed C124/C125b checker commit `d8be1443f2f1352634aaf333a282f32e7ec8a719` is not in this workspace or GitHub, so no C139 claim transfers automatically to that checker.
