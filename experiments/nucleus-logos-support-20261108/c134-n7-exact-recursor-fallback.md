# C134 — N7 exact captured qualified-recursor fallback (WARRANTED_BOUNDED)

Native source: unchanged Arena `good/perf/magma-list-pair-n7.ndjson`, SHA256
`abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`,
recovered from frozen original-196 artifact `11272848230`, archive SHA256
`f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2`.

Green native diagnostic run:
https://github.com/heathsanchez/test/actions/runs/43490040767
Artifact `14069137265`; ZIP SHA256
`777dbc93b876912f7deaa6401363d276dad629fab8371d2e86dadabb3ccaa937`.
Branch: `research/nucleus-c125-c105-surrogate-ci-20261114`, C105-derived,
**not** recovered exact C124/C125b source. Configuration is the same at both
budgets: `NUCLEUS_EXPERIMENTAL_RELEVANCE=1` and
`NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR=1`.

The diagnostic owner is the second, **not the first**, C133 captured conversion:
`Term(Expr110,Env66182,levels=[(Name18,Succ(Zero))])` against
`Term(Expr1,Env66180,levels=[(Name2,Zero)])`, depth zero. C134 does not
identify these with the distinct previously successful Env45059/Env45057
captured pair.

* Standard 65,536: exact owner starts with budget **65,264**, outcome
  **UNKNOWN**. Within that owner the qualified-recursor mismatch occurs at
  budgets **507** and **65,250**.
* Diagnostic 14,155,776: exact owner starts with **14,155,504**, outcome
  **PROVEN**. The same mismatch occurs at budget **507**.
* Every observed mismatch in this receipt has left neutral constant
  `NameId(169)` with empty levels/spine; right neutral constant
  `NameId(147)` with level `Succ(Zero)` and spine length **5**; depth zero.
* Both native checker verdict and original stdout match with diagnostics
  enabled and disabled within each budget. The source is unchanged.

**Interpretation / restraint.** The repeated mismatch is not grounds for
equality, admissibility, or a sound caching rule. A low-budget fallback at
65,250 is absent from the high-budget owner's trace even though a smaller
507-budget fallback occurs in both. This is evidence of a budget-dependent
search/replay path, but does **not** yet identify which checked reduction
premise explains the divergent outcomes. C135 instruments that one-step
qualified recursor attempt without altering any checker decision.

**Residual.** Original N7 still UNKNOWN at the standard budget; five other
original valid UNKNOWNs remain. No production checker promotion is warranted.
