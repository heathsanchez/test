# V2 cold admission seal, 2026-10-30

Exact algorithm/test source commit before cold target inspection: `2aeaa1c75ae46a29472f7df3c6981b768686dc1d`. Unit CI `40994057795` succeeded 6/6 AST fixtures, with deliberately RED preimplementation CI `40993868323`. Full native fixture CI `40994460894` succeeded 6/6 AST plus 3/3 native integration fixtures: constructor with time.Duration; context+unique source-defined default-config helper; generic zero-valued configuration compiled but failed at runtime and was correctly rejected. A prior bridge CI `40994364554` failed because safe-expression whitelist omitted Go struct literal braces; fix was confined to whitelist.

Cold target remains metadata rank 3 `dgraph-io/ristretto` @ `a56a38ebeec716a0da3d20a46b417ca2ab7c81f4`, Git-ref-only pin, no target source, README, issues, PRs or commit messages inspected before seal.

Admission contract:
- Run unmodified `constructor_planner.go`, `native_constructor_bridge.py`, unit and native fixtures. Verify equality against algorithm seal SHA.
- If planner says UNKNOWN, do not hand-write constructor adapter. If CANDIDATE, generate, compile and execute call at exact source SHA; nonzero exit or nil/error result is UNKNOWN_NATIVE_CONSTRUCTION.
- A successful constructor is a narrow **CANDIDATE -> WARRANTED_BOUNDED native constructibility** only for that source pin, not evidence of safety, novel operation grammar or unseen defect.
- A simple programmer with the same static type knowledge could use the same constructor; there is no G3 superiority or newly invented operator claim. Strict G3 UNKNOWN; seven gates 0/7.
