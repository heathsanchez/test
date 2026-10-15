# Canonical Attestation Ledger

_Last reconciled: 2026-08-14 NZST_

This is the authoritative evidence index for headline Triskelion / LOGOS claims. Top-level prose must not claim more than this ledger supports.

## Evidence classes

- **ATTESTED** — primary artifact and harness/predicate inspected; the exact allowed sentence is supported.
- **ATTESTED WITH QUALIFICATION** — the core behavioral predicate is supported, but an adjacent property such as sealing or independence is weaker than a gate name suggests.
- **BOUNDED PASS** — primary run/result lineage is pinned and the bounded verdict is supported; a fresh predicate-by-predicate audit has not necessarily been repeated in this reconciliation.
- **RESULT FILE / NO CI PROVENANCE LOCATED** — a committed result exists, but no corresponding Actions run was located in this repo.
- **NOT ATTESTED IN THIS REPO** — the claimed evidence is not present in this repository and must not be presented as repo-attested.
- **NEGATIVE / MIXED** — the scientific gate was reached and failed or produced a mixed result.
- **INCOMPLETE / HARNESS** — the intended mechanism was not reached because usable worlds or harness execution failed.

## Naming rule

Bare V-numbers are not unique identifiers. `V49`, `V50`, and `V51` are used by two unrelated lines. Use descriptive IDs such as `OPERATOR_INVENTION_V51` and `QUOTIENT_REFINEMENT_V51`.

## Headline developmental / model claims

| Canonical ID | Status | Primary evidence | Exact allowed wording |
|---|---|---|---|
| `TWO_GENERATION_COMPOUNDING_V54` | **BOUNDED PASS** | branch `v54-compounding-ratchet`; run `31761530951`; head `2dd5f41b6c7cec1004b8deaee4f976dd2a9ed21c` | Under the frozen one-new-generator protocol, O2 had zero cold survivors before O1, became discoverable after O1, and the final target required both. |
| `VERIFIER_MODEL_LAYER_V56C` | **BOUNDED PASS** | branch `v56-close-gaps`; suite run `31766446740`; head `14757f481d5873332c72a279c3337aec17d323ab` | On the frozen 12-case small-model task, explicit verifier-controlled applicability scored 12/12 vs 6/12 no-memory and 6/12 raw-memory. |
| `VERIFIER_INDUCED_INVOCATION_IKKF_V4B` | **BOUNDED PASS** | run `31763234925` | External verification refines a coarse admitted scope to the unique valid invocation in this bounded setting; ablation and later revocation pass. |
| `VERIFIED_ROUTING_IKKF_V2D` | **BOUNDED PASS** | run `31763593583` | On the exact V2c C/J worlds/modules, verifier-controlled routing/execution reached 100%/100% vs learned selector 50% routing and 0% joint execution. |
| `PORTABLE_CAPABILITY_IKKF_V1` | **ATTESTED WITH QUALIFICATION** | run `31759600559`; primary result/harness/protocol audited | Fresh capability compilation, a second fresh compilation call, uninstall and reload are separately executed. Do **not** claim stochastic independence: C1/C2 curves are bit-identical and the `independent_recompile` predicate does not test independence. |
| `ADAPTIVE_CONSOLIDATION_V18B` | **ATTESTED** | run `31740188434`; head `070dd7a14f288481c16c1cb33ca127a588da501f`; primary RESULT audited | Bounded protected consolidation preserves the measured ancestors/composites and reload persistence. |
| `SOURCE_DISTINCT_DISCOVERABILITY_V34` | **ATTESTED — BOUNDED** | run `31724783160`; head `9e89901b33c3de75923de0b5bfd1fad2cb2f609a`; artifact `metalogic-source-distinct-ratchet-v34`; digest `sha256:7cb14558b24f4a7894fa68e6ed5a2ec7d3fee56223af5901e2f38cf568e1256f`; harness audited | On fixed source-distinct Requests, Rich and Flask repositories under the supplied AST barrier vocabulary/frontier procedure, prior acquired operators change the next visible obstruction from cold `Try` to warm `Raise` and then `With`; ancestor ablations move the deepest frontier back accordingly. |
| `EXTERNAL_FRONTIER_V33` | **BOUNDED PASS precursor** | run `31724613985`; artifact `metalogic-external-frontier-v33`; digest `sha256:6f836e70f2f34e6cc99525c96ab73371bbb360d77053ab7014f8fe57ddaa6f4f` | Precursor external-frontier result; use V34 for the stronger source-distinct headline. |
| `SORRYDB_V77` | **NEGATIVE at current solver/budget** | repaired run `31761636184` | Exact-commit plumbing/official verifier/repo preparation works; five frozen solver arms solve 0/3 selected tasks. |

## V49–V51 sealed/operator line — fully reconciled

| Canonical ID | Status | Primary evidence | Exact allowed wording |
|---|---|---|---|
| `SEALED_TRANSFER_V49` | **ATTESTED WITH SEALING QUALIFICATION** | branch `v49-sealed-run`; audited run `31749682731`; head `79799fba8961645bcd20ba6f94bcf34011a8b629`; artifact `metalogic-v49-sealed`; digest `sha256:1079cae6f06085dc59bfa23cf548807d4219ecae811dd2d424dab5b9d3113a47` | The artifact records a unique learned lexical category, Requests cold FAIL → warm PASS → ablation FAIL, a unique later Django counterexample inside the category, and `REVOKE`. Behavioral predicates come from executable tests. Temporal sealing is supported by phase-separated workflow/code; the hard-coded `requests_absent_from_phase_a_code=True` flag is not itself sealing proof. |
| `OUTCOME_LABELED_V50` | **ATTESTED WITH SEALING QUALIFICATION** | original run `31749833138`; head `929461fe989592f40f2e15cb0105d81785281817`; artifact `metalogic-v50-outcome-labeled`; digest `sha256:6a97a3e5978d03c5f495f01ca11c0620c822b12e13c963f7df31e01a7cdebddd`; Phase A/B + harnesses audited | Under supplied episodes/tests and one widening mutation family, HELP/HARM is derived from executable before/after transitions, not supplied class labels: 2 HELP + 2 HARM induce one lexical relation; Requests gives cold FAIL → warm PASS → ablation FAIL; later in-relation Django HARM causes `REVOKE`. Temporal sealing is supported structurally, not by hard-coded unseen flags. |
| `OPERATOR_INVENTION_V51` | **ATTESTED WITH SEALING QUALIFICATION** | branch `v51-operator-invention`; run `31759857216`; head `f739be68af3cd6695a1674225938961f3b69f7b2`; artifact digest `sha256:e3c10a4ba1011876e5df7248de4f3cb468e90195f6c331e625c3bb5d6c2f93d0`; Phase A/B, workflow log and harnesses audited | Under the supplied generic token-emission substrate, two executable obstructions have the unique common repair `< -> <=`; that rewrite lies outside the frozen token-permutation closure; it causally repairs withheld Requests, ablation restores failure, and later contradictory Django evidence causes revocation. Do **not** claim invention outside all supplied meta-languages. |

The files `results/V49_EXTERNAL_QUOTIENT_REFINEMENT_RESULT.*`, `results/V50_EXTERNAL_QUOTIENT_REFINEMENT_RESULT.txt`, and `results/V51_RESULT.txt` belong to the separate quotient-refinement sequence and are not evidence for this operator line.

## Natural / constructor frontier

| Canonical ID | Status | Evidence boundary |
|---|---|---|
| `HISTORICAL_COMPOUNDING_V55A` | **INCOMPLETE** | run `31764969750`; only two READY historical worlds, both Black; no unique O1; natural compounding not reached. |
| `CONSTRUCTOR_COMPOUNDING_V55B` | **NEGATIVE under tested substrate** | suite run `31764908603`; K0 obstruction reached; frozen insertion meta-substrate failed to synthesize K1. |
| `MODEL_CARD_V55C` | **MIXED / NEGATIVE** | same suite; 6/12 no-memory, 5/12 raw-memory, 5/12 verified-card; protected negatives fail. |
| `HISTORICAL_BLIND_EDIT_V56A` | **HARNESS FAILURE** | suite run `31766446740`; `IndexError`; no scientific verdict. |
| `CONSTRUCTOR_RETRY_V56B` | **HARNESS FAILURE** | same suite; malformed insertion caused `IndentationError`; no scientific verdict. |
| `META_CONSTRUCTOR_V36_V37` | **RESULT FILE / NO CI PROVENANCE LOCATED** | committed `results/V36_V37_META_CONSTRUCTOR.txt`; checkpoint commit `32f3f9e5e280e81d017e3e502faee4e6b6a8ecd6`; no Actions run located for that checkpoint | The committed summary reports bounded constructor-level discoverability under a supplied Python AST type lattice/LCA meta-substrate. Treat as result-file evidence, not CI-attested. |

## Scope / ontology progression

| Canonical ID | Status | Primary lineage |
|---|---|---|
| `SCOPE_CONSTRUCTION_V40` | **BOUNDED PASS** | run `31738858678`, head `94549744273b934ff4f7dbe659e9a0483a03fc72` |
| `RELATIONAL_SCOPE_V41` | **BOUNDED PASS** | fixed run `31741219608`, head `ce2d86201087aaea45ba9113deb6ae248ccc2aa5` |
| `OPAQUE_LABEL_AUDIT_V42` | **BOUNDED PASS** | run `31741542315`, head `fa66c3ffff654239c1eae8b33e8f5e179f222bff` |
| `CATEGORY_INDUCTION_V43` | **BOUNDED PASS** | run `31742025972`, head `e8316eaafa354f32e445b5cad1f85768df447ac5` |

These recovered lineages support bounded historical status; this reconciliation did not repeat a full predicate-by-predicate audit of every V40–V43 gate.

## Grammar / motif line

| Canonical ID | Status | Primary evidence / boundary |
|---|---|---|
| `MULTISCALE_MOTIFS_V70` | **BOUNDED PASS** | run `31741994569`; digest `26a1c4023211a21285b84a2233602e2ebb4b9271dfe02f9bd0724ab9358153fc`; manually normalized 51-event corpus only. |
| `SCALE_HOLDOUT_GRAMMAR_V71` | **BOUNDED PASS** | run `31742125256`; digest `4508a8510366f021cfcb98a719d4b629cfb8005a1d3bc3b63470013a0216462c`; whole-scale transfer positive under frozen corpus. |
| `MDL_MOTIF_BASIS_V72` | **BOUNDED PASS** | run `31742262476`; digest `ae432cc96822cdf05ebb4e14fc46d2aa371f496d0b0c991bade4c5829abdd21b`; exact MDL search: raw cost 142 → 120, 15.493% saving vs 5.632% shuffle mean. |
| `HIERARCHICAL_MOTIF_V73` | **NEGATIVE / MIXED** | run `31742496354`; digest `c7fb4014978d7d4aedf09f9918d0a47b971f3e66d54314502d274e337bf9c58b`; zero qualifying second-level motifs, all hierarchy gates fail. |
| `MATH_GRAMMAR_TRANSFER_V74` | **MIXED** | run `31743038770`; digest `6767cda6ec0e22f25301848d8d31129574283de586205fb6085005b5edc01d07`; primitive/operator order transfers strongly, but V72 macros do not establish incremental math value. |

## Earlier operator / composition line

These have primary successful Actions lineage and uploaded artifacts but were not all freshly predicate-audited in this reconciliation, so they remain bounded historical results.

| ID | Status | Run / digest |
|---|---|---|
| `PRIMITIVE_COMPOSITION_V15` | **BOUNDED PASS** | run `31684670614`; digest `3a9632a69dda4a70f1ef2f8abe93732451450c3ff1b14a3acfa9e4de26016927` |
| `VERIFIED_COMPOSER_V16` | **BOUNDED PASS** | run `31692092038` attempt 2; latest digest `59c7a143cde4c916a983394e25a049ee4b52953e5b3bce6a27e28765c049dad6` |
| `HIERARCHICAL_CHUNKING_V17` | **BOUNDED PASS** | run `31692435978`; digest `4568a3bcd30dfc5794bb674c225b7b446c7ce853cba6e32d66a013d0f1b30dbc` |
| `REUSABLE_WORDS_V19` | **BOUNDED PASS** | run `31693216278`; digest `f482d385cc51f2455aee87c6bd1f7a68d5c08c2942c0d13144399a7f87bc5318` |
| `OPERATOR_ORDER_V20` | **BOUNDED PASS** | run `31693479066`; digest `3c3c78d4e12f1d9f917cd280c8c891b96723baebb83d8286a8b3e3fb38b5fc7a` |
| `TYPED_IR_V21` | **BOUNDED PASS** | run `31701544954`; digest `64d18471430f7c34f6ee6daa99b95a1b1af24fe36f9b38a56baeea5a1e48db93` |
| `FOUR_STATE_IR_V22` | **RESULT/SCRIPT ONLY — NO CI RUN LOCATED** | commit `1c67e9df6e60b9067de7c77213294986a321663c`; no Actions run found for that commit. |
| `METAMATH_V23` | **BOUNDED PASS** | fixed rerun `31704158909`; digest `8ebb4d9e8f4e3349ced03b83d92c861e232d803ee3a6c4400bb24082a7d6c1a5` |

## External quotient / Lawbook line

| Canonical ID | Status | Evidence boundary |
|---|---|---|
| `QUOTIENT_REFINEMENT_V45_V66` | **BOUNDED RESULT LEDGER WITH PINNED PARENT ARTIFACT** | `results/V45_V66_LEDGER.txt`: parent artifact `9190497808`, digest `5e0af022d52fdc0a2d4262f1766ed4042f2e6803689b06cf2fa370314e095073`; 22 targets, 19 no-coarse-equivalence negatives, 3 reversible refinements (V54/V57/V66). Claim boundary: bounded external reversible equivalence, not autonomous separator invention. |
| `INCREMENTAL_LAWBOOK_V68` | **RESULT FILE / NO CI PROVENANCE LOCATED** | precommit `fb6e0880a8a71ef6eb093e2e4bae13aa1da7da84`; committed result reports 3→6 classes, reversible partition/provenance restoration and no fake capability gain at V66; no Actions run located for result commit `f3c7448d9421b258785f87fe8da67a1abba0079b`. |

## Evidence not contained in this repo

`EXCEPTION_FLOW_EXTERNAL_STREAM` — **NOT ATTESTED IN THIS REPO.** No commit, indexed file, or code-search hit containing `EXCEPTION_FLOW` was found in this repository. The reported ffmpeg→SHAP result may exist in prior Library/external artifacts, but a Triskelion repo ZIP does not substantiate it and top-level repo docs must not present it as repo-attested.

## Audit completion state

The **provenance audit is complete to the current repository**: every headline family above is now either (a) tied to a primary run/artifact, (b) explicitly result-only/no-CI, (c) explicitly negative/incomplete, or (d) explicitly not attested in this repo. There is no remaining silent `PASS` category whose evidence location is unknown.

This does **not** mean every historical result has been freshly predicate-audited. Only rows marked `ATTESTED` / `ATTESTED WITH QUALIFICATION` received that stronger treatment in this reconciliation. `BOUNDED PASS` remains deliberately weaker.

## Citation policy

A paper/demo/README headline may use only the exact bounded wording allowed here. A successful workflow is not by itself a scientific verdict; a gate name cannot claim more than its implemented predicate; declarative booleans are not empirical proof; and result-only/no-CI rows must retain that qualification.

## Remaining scientific capstones — not attestation debt

1. Natural heterogeneous V54-shaped development with solutions sealed.
2. Constructor-language development: `Constructible(K0) ⊊ Constructible(K1)` under an externally meaningful protocol.
3. Matched longitudinal economic/model A/B showing benefit per token/call/cost as developmental state accumulates.
