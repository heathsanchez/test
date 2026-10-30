# Cold transfer T1 — preregistered before target source inspection

2026-10-30. Research branch `research/g3-blind-cache-operator-transfer-20261030`.

Target: second repository from the *same* frozen ten-result metadata search, `allegro/bigcache`, default `main`. Exact SHA obtained from Git reference object (no commit text): `6e72b805b2b3f6d7952ac172f6c8f7aefecfc00e`. No target code, README, tests, issues, PRs, history, or commit titles read before this preregistration.

No modifications whatsoever are permitted to `source_proposer.go`, `native_bridge.py`, `native_replay.go` or their tests between successful first-source CI #40983814078 and this transfer. The point is to price cold transfer, **not** repair a new target. The re-run may use a new workflow only, and must pin both the source SHA and research commit of the proposer.

Execute:
1. Clone exact target SHA, parse only non-test source AST with frozen proposer.
2. Save manifest. If `UNKNOWN_ADAPTER`, mark failure of native portability and do not supply target-specific manual constructor adapters.
3. If `CANDIDATE_SIGNATURE_BRIDGE` with clock, generate/run unchanged native probe and independent replayer; if build/runtime fails, record UNKNOWN rather than edit algorithm.
4. Baseline B0 and fair time-aware direct B1 from frozen probe remain in force; no superiority claim when B1 ties.
5. Independently retain prior failed first-source blind result, follow-up repair, and this transfer outcome.

Admission: source-adaptive syntax selection on this cold repository is not itself strict G3; only an independently demonstrated, genuinely *new* operation not covered by the human-coded clock template and fair baselines would be a G3 candidate. Report UNKNOWN otherwise. Never claim source defect from this test alone.
