# C144: frozen N7 head expressions are lexical binders and a projection under lambdas

**Status: WARRANTED_BOUNDED source-only identification; no new checker acceptance.**
Native [workflow run 43502627236](https://github.com/heathsanchez/test/actions/runs/43502627236), job `132152066128`, **completed successfully** (28/28 job steps successful), checked out remote source at `3f2c5f3bcd115bd3cd44b5a5bdc8b4f513d9a729`; its C144 step succeeded and printed the eight literal AST rows below. Artifact ID `14075925242`, ZIP SHA256 `52963cc346a105e85daaeea054f8d0f7b810130a836be8adb9d1a3b8fe9a1b28` (GitHub artifact metadata and native log agree). Frozen, unchanged original Arena `good/perf/magma-list-pair-n7.ndjson`, SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`, is checked byte-for-byte before source parsing. C144 read-only parser and unit tests do not alter the evaluator or verdict.

| Source ExprId | Original exported AST row | C143 high-budget head-loop visits | App-parent edges |
| --- | --- | ---: | ---: |
| 1 | `{"bvar":0,"ie":1}` | 1,095,156 | 688 |
| 6 | `{"bvar":1,"ie":6}` | 896,349 | 558 |
| 11 | `{"bvar":2,"ie":11}` | 504,189 | 451 |
| 7 | `{"app":{"arg":1,"fn":6},"ie":7}` | 196,070 | 5 |
| 345 | `{"const":{"name":89,"us":[]},"ie":345}` | 134,456 | 14 |
| 4677 | `{"ie":4677,"proj":{"idx":0,"struct":1,"typeName":88}}` | 134,456 | 0 |
| 4678 | `{"ie":4678,"lam":{"binderInfo":"default","body":4677,"name":34,"type":342}}` | 134,456 | 0 |
| 4679 | `{"ie":4679,"lam":{"binderInfo":"default","body":4678,"name":65,"type":204}}` | 134,456 | 0 |

App-parent edges count only `App.fn` and `App.arg` fields in the frozen export; lambda and projection parent links intentionally are **not** in this count. Name IDs 89, 88 and binder IDs 34, 65 are not yet decoded into text names; no claim about what named constructor these represent. The head-loop frequencies are C143 observations, not work charged to the Arena owner; C144 only resolves their source syntax.

**Synthesis:** identical `ExprId` repetition is not term equivalence. The high-budget evaluator has substantial repeated local lookups of de Bruijn variables across different immutable environments, plus a source projection under two lambdas. C105 previously showed simple BVar-terminal closure deduplication failed for two N21 recursor owners; this N7 source map does not overturn that negative. It also does **not** show which of BVar lookup, beta, projection, App-spine transport, delta, or other head actions dominate the full 12,761,384-loop high-budget producer.

**Next smallest discriminating test:** on the same exact `Expr8799@Env0@Levels[]` uncached source exposure, measure per-AST-constructor counts and outcomes of bound-variable lookup, new beta frames, projection demands and App-spine transitions at both low and high budgets. Separate exact frame provenance from syntax IDs, and compare instrumented on/off judgments and stdout. Only then consider a single semantics-preserving optimization or resumable continuation, never a cross-environment syntax cache or unproved shortcut.

Lineage: C141 exact cache provenance → C142 producer cost → C143 head revisit census → C144 source AST identity. Six original valid standard-budget UNKNOWNs and source-qualified full Mathlib acceptance remain OPEN; neither selected production checker nor protected forged regression was changed here.
