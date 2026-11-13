# C138: second deferred equality exposes both values but cannot compare at standard fuel

Status: **WARRANTED_BOUNDED** for the C105-derived diagnostic surrogate only. No original standard-budget UNKNOWN is closed and no rule changed.

Native green [run 43494578491](https://github.com/heathsanchez/test/actions/runs/43494578491), artifact ID `14070783914`, artifact ZIP SHA256 `8e329fce6f82c98d0af2fd55717303d92408c58d6f926c147441b93c51b95600`. Source frozen original unchanged N7 SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`; 65,536 standard versus 14,155,776 high diagnostic steps; same two experimental relevance and demand-major flags in each arm. 14/14 local parser tests and native CI pass. Instrumentation gated by exact C137 root captured source owner and the **second** popped deferred equality, retaining term, environment, universe substitution and binder depth. Observer OFF/ON verdict and stdout exactly match at each budget.

The source-captured owner initially compares `Expr110@Env66182` versus `Expr1@Env66180` and pushes three deferred equalities. The first blocking one is **pop 2:** `Expr1@Env66182@Levels[(18, Succ(Zero))]` versus `Expr8799@Env0@Levels[]`, depth zero, pending one.

| Event for exact pop 2 | Standard budget | High diagnostic budget |
| --- | --- | --- |
| Pop / before work | 65,255 | 14,155,495 |
| Cheap-exposure attempt | 65,250 | 14,155,490 |
| Left/right exposure | **PROVEN / PROVEN** | **PROVEN / PROVEN** |
| `compare_values` outcome | **UNKNOWN** | **PROVEN** |
| Whole owner | UNKNOWN | PROVEN |

**REJECTED as an explanation:** either side's initial cheap exposure fails at standard fuel. **Remaining residual:** determine the `compare_values` branch and the checked sub-obligation inside this exact captured, fully exposed pair. An initial positive root compare and independently successful operand exposures must not be promoted to equality; a source-qualified complete proof remains required. The next cheapest experiment is to instrument only this `compare_values` invocation, including value constructors, neutral head checks and any qualified recursor fallback, without changing checker semantics.

Lineage: C133 distinct captured conversions → C134 fallback present at both budgets → C135 high does not finish an expensive one-step trial → C136 initial positive rule creates deferred work → C137 second deferred pair first remaining UNKNOWN → C138 both exposures PROVEN, nested value compare UNKNOWN. C125b exact source unavailable, full protected 403/403 plus 71 forged and six original valid UNKNOWNs remain future promotion gates.
