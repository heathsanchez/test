# V4 Minimum Sufficient Native Authority — executed qualification

**Verdict: WARRANTED_BOUNDED source-role inference and generated-source native pytest smoke; generic external native admission and developmental G2–G6 UNKNOWN.**

## Evidence and frozen lineage

- Original V3 base: [95029db0](https://github.com/heathsanchez/test/commit/95029db0d0b2122836bee7268299461bfbdb5a66). The original RED [38877891483](https://github.com/heathsanchez/test/actions/runs/38877891483) (0/7 admissible and 0 protected calls) remains RED and was never replayed as prospective.
- Frozen V4 acceptance tests added before implementation at [13722d6e](https://github.com/heathsanchez/test/commit/13722d6eedbdf3fd1da834856ef1f25829dce0c5). The first expected RED at [38967644404](https://github.com/heathsanchez/test/actions/runs/38967644404) confirms they preceded the implementation.
- Final qualifying source [70bd4452](https://github.com/heathsanchez/test/commit/70bd44527d151e175831085af9a3692f48bc5e50).
- Static-contract qualification [38968231057](https://github.com/heathsanchez/test/actions/runs/38968231057): **17/17 original frozen tests passed** under Python 3.12, packaging 25.0. Previous diagnostic REDs are retained.
- Native generated-source qualification [38968634892](https://github.com/heathsanchez/test/actions/runs/38968634892), [artifact 12075573009](https://github.com/heathsanchez/test/actions/runs/38968634892/artifacts/12075573009), GitHub-reported ZIP SHA256 `d405b5632bc67e908de49c82241420ad37a44f3265688b975252e0a5dbadd3a1`. The same 17/17 static contracts remain green; direct original pytest 8.4.1 is exercised.

## Minimum warranted correction

The V3 selector parsed every `.py` blob while deriving environment constraints. Invalid fixture-as-data then prevented the process from reaching executable evidence.

V4 distinguishes source identity (all tracked bytes SHA256-bound) from static environment inference (explicitly recognized `tests/data/`, `tests/fixtures/`, `fixtures/`, `testdata/` data directories). Top-level actual `test_*.py`, `*_test.py`, `conftest.py`, `setup.py`, executable source modules and unrecognized locations do **not** receive that exemption. The candidate selector still grants **no execution warrant**. A fixture may be dynamically imported, so independent native full-suite collection, imports and protected assertions remain mandatory.

A second, bounded correction classifies **an exact pinned dependency version provably outside a declared requirement** as `INCOMPATIBLE_PINNED_DEPENDENCY`, not merely UNKNOWN. This enables a compatible legacy profile to be selected even with an impossible higher profile; absent dependency evidence still remains UNKNOWN. The original V3 selector bytes were not edited.

### Native execution controls

A generated, source-hashed project was executed under real pinned pytest 8.4.1 with plugin autoload disabled.

| Condition | Actual pytest exit | Interpretation |
| --- | ---: | --- |
| Invalid Python only as `tests/data/broken.py`; unrelated protected test | 0 | PASS, one real protected assertion executed |
| Original invalid fixture imported dynamically by a test | 1 | Real execution failed with `IndentationError` |
| Original invalid code placed into a collected `tests/test_invalid.py` | 2 | Real collection failed, as required |

Fixture-source hashes were checked unchanged across calls. Diagnostic adjustment was limited to accepting Python's actually reported `IndentationError` rather than assuming only `TabError`; prior failure run is retained [38968560985](https://github.com/heathsanchez/test/actions/runs/38968560985).

These controls are actual native executions **of our generated fixture**, not general independent author-test admission of unknown external source. They are not a proof of sandbox isolation, external-verifier soundness, or new autonomous method selection.

## What was deliberately not promoted

G0/G1 previous authority is preserved; [compare parent to qualified source](https://github.com/heathsanchez/test/compare/95029db0d0b2122836bee7268299461bfbdb5a66...70bd44527d151e175831085af9a3692f48bc5e50) shows four added-only implementation/test/workflow files. Original 246 ledger records, 76 CAS objects, and 70 inventory entries have not been edited in this branch. Historical Git-index cache audit limitation remains UNKNOWN.

The seven exposed V3 source tasks were not re-screened or changed into retrospective successes. Other V3 refusal classes (dynamic metadata 2, metadata grammar 2, interface 1 and compatible catalog profile 1) have no general native qualifications from this continuation. G2 prospective autonomous selection, G3 causal future-discoverability expansion, G4 charged economic advantage, G5 concrete refinement and G6 non-bypassable containment all remain **UNKNOWN**. Coding agent and ledger comparators were **NOT_RUN** because no independently admitted new prospective native obligation was available. Complete lifecycle and engineering costs remain UNKNOWN.

## Highest-leverage next independent gate

Integrate the V4 source-role candidate selection into an **explicitly versioned, independently authenticated native admission adapter**, without changing any original v1–v3 worker/verifier bytes. Preserve all original authority checks (source/import/environment/collection/selected order/assertions and falsification controls). Qualify against untouched external source with predeclared independent screening and budget. Only after that pass should a new pool be frozen and G2 pursued through the existing MSI/V104 policy machinery. Do not substitute this generated fixture for genuinely unknown source-native evidence.

**Machine-readable checkpoint:** [V4_MINIMUM_SUFFICIENT_AUTHORITY_RESULT.json](https://github.com/heathsanchez/test/blob/research/udm-minimum-sufficient-authority-v4-20261017/research/unified_consequence_runtime/V4_MINIMUM_SUFFICIENT_AUTHORITY_RESULT.json).
