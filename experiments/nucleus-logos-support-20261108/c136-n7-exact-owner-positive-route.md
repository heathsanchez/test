# C136 — first positive comparison is shared; deferred equality remains (WARRANTED_BOUNDED)

Native green [run #43492251622](https://github.com/heathsanchez/test/actions/runs/43492251622),
artifact `14070920387`, ZIP SHA256
`173f859590e27285512c488c663b6832ec23981ec998d0b124fd369e213b71f6`.
Frozen original N7 SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`;
C105-descendant surrogate, **not** exact C124/C125b. Diagnostic flags,
source, checker semantics, and budgets unchanged. Observer OFF/ON parity.

At the exact C133 **second** captured conversion owner, the first work item
is `Expr110@Env66182` vs `Expr1@Env66180` at depth zero.

| Initial budget | Owner budget | Shared first-pair events | Owner result |
|---|---:|---|---|
| 65,536 | 65,264 | `pop` → `cheap-exposure-attempted` (65,260) → `cheap-comparison-proven` (65,260) | UNKNOWN |
| 14,155,776 | 14,155,504 | `pop` → `cheap-exposure-attempted` (14,155,500) → `cheap-comparison-proven` (14,155,500) | PROVEN |

**Conclusion:** The first compared pair has an identically named positive
rule in both runs. This is **not a certificate for the whole conversion**:
`compare_values` can append additional equalities to the worklist. C135
correctly found a later recursor trial only in the standard route, while
the diagnostic route succeeded. The positive-rule search should now move to
the **first unresolved deferred work item**, not add an unconditional
shortcut for the original two source expressions or merge captured frames.

Next C137: observe each worklist pop and exact closure identities at this
owner, recording low/high divergence without changing any judgment or budget.
