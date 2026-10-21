# Gen3 native acquisition result — 2026-10-21

## Bounded native witness (new result)

Native Actions run [#39540011181](https://github.com/heathsanchez/test/actions/runs/39540011181) finished its source-native test step SUCCESS on frozen original `go-ini/ini@e2db55b0e088fa4ee0c128aa4ade263cdc1d7f08`.

Fixed precommitted bounded search reported:
```
GEN3 searched=12 witness="plain\\" -> "plain"
```
This states that one candidate ending with a literal backslash did not preserve the decoded value under the implemented repeated serialization process. The test is diagnostic and reports the witness while returning success: the CI green status does not mean the preservation property passed for all candidates.

Evidence artifact [#12318996307](https://github.com/heathsanchez/test/actions/runs/39540011181/artifacts/12318996307), SHA-256 `29efb4f56abde27a7dbfb5d28f48775637b6b6bd07e6f9db2833cc59e9c5feb1`.

## Epistemic boundary

- **WARRANTED_BOUNDED_NATIVE_OBSERVATION**: the fixed candidate search produced the above witness on the pinned source, as printed by actual native Go execution. Independent implementation/replay of this particular witness not yet established.
- **NOT WARRANTED**: novel upstream defect, general INI-string fidelity, discovered new method language, advantageous retention, or net lifecycle cost. This was a HUMAN_SUPPLIED fixed mutation grammar.
- Strong equal-information comparator can use the exact same grammar and fixtures; no actually-run competing acquisition trajectory, removal/restoration or restart cost measurement exists.
- Earlier Gen1 and Gen2 pass reports covered nine supplied fixture strings; the Gen3 witness is an additional generated candidate and is not a contradiction of those scoped passes.

## Decisive next control
Re-run the pinned witness in a separately implemented native reproducer with exact intermediate encoded bytes, add a negative-control string, and ensure baseline search is actually executed with the same grammar/tooling. Then compare acquisition cost inclusive of human design, adaptations, verifier calls, and cold restart. Do not imply the current result proves compounding.
