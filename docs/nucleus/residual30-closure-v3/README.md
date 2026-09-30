# Independent Nucleus: six of the thirty residuals closed

## Qualified boundary

- Semantic revision: `0329400bbab751eb6ea645c0a65b30f019e99bfd`.
- Baseline: `c362f35db5a2efe5c629e64c1a3b71e392b473fb`.
- Branch: `nucleus-residual30-closure-v3`.
- [Qualification run 36782281571](https://github.com/heathsanchez/test/actions/runs/36782281571): SUCCESS.
- [Artifact 11128736678](https://github.com/heathsanchez/test/actions/runs/36782281571/artifacts/11128736678), ZIP SHA-256 `9f4a09a917877d9aa9922a4e22fe137675f995f02fb4a62ad7837fda1b16ee7c`.
- Current Arena: `4c30c4ac4f14a3a899116beb3ea6131880e79a98`; input artifact `11090525747`. Frozen input artifact: `10712869614`.

| Corpus | Baseline A / R / U | Candidate A / R / U | Wrong | Errors | Lost decisions |
|---|---|---|---|---|---|
| Current, 194 | 105 / 59 / 30 | **110 / 60 / 24** | 0 | 0 | 0 |
| Frozen, 193 | 103 / 60 / 30 | **108 / 61 / 24** | 0 | 0 | 0 |

All 135 Rust tests pass. Exit 2 alone is UNKNOWN; every non-0/1/2 exit is an error. The six changes are identical on both corpora. All previously decisive answers are retained.

## Earned decisions and mechanisms

| Test | Change | Mechanism |
|---|---|---|
| `perf/church-numerals` | UNKNOWN → ACCEPT | Bounded judgment fuel increased from 16,384 to 65,536 |
| `perf/let-ladder` | UNKNOWN → ACCEPT | Same bounded fuel increase |
| `perf/unroll-versus-evaluate` | UNKNOWN → ACCEPT | Same bounded fuel increase |
| `tutorial/105_proofIrrelevanceBad` | UNKNOWN → REJECT | Scoped binder typing context proves that distinct locals of a rigid type variable in a successor universe cannot use proof irrelevance |
| `tutorial/099_ruleK` | UNKNOWN → ACCEPT | Exact admitted Eq enables constructor iota and K when both endpoints expose to identical values |
| `perf/app-lam` | UNKNOWN → ACCEPT | Reuse proven inference for the same expression and frame within one public judgment |

The inference cache is fresh for each public judgment; environment authority and level substitution remain fixed. Binder frames have distinct identities. UNKNOWN and refutations are never cached. A shared-syntax fixture was red before the change; a second fixture checks that shared BVar syntax retains its own binder type and does not validate the wrong argument.

Conversion work items now carry their own binder context. The rigid-local obstruction requires distinct bare locals with the same bare type variable whose type is known to be a successor sort. Prop proof irrelevance and identical data locals remain positive controls.

Eq computation is installed only after the existing exact declaration, constructor, recursor type, metadata, and computation rule have passed independent validation. K is not installed for ordinary recursors. Unequal endpoints and extra pending applications are covered by focused controls; `ruleKbad`, `ruleKAcc`, and `accRecNoEta` remain UNKNOWN in the corpus, never ACCEPT.

## Runtime boundary

The CLI supplies a 64 MiB checker thread stack. CI independently verifies both `app-lam` inputs under an **8 MiB launcher stack**, returning ACCEPT in approximately 1.3 seconds, with peak RSS about 299,000 KiB. Without the explicit checker stack, the local binary aborted on this test at an 8 MiB launcher limit. That failure is preserved in the lineage evidence and was not counted as UNKNOWN.

The baseline/candidate differential uses a 64 MiB launcher stack for both binaries. The candidate has 65,536 judgment steps. These are explicit qualification conditions. Current `unroll-versus-evaluate` takes **44.75 seconds** in the final CI replay. Instruction ranking and memory competitiveness have not been qualified.

The downloadable corpus omits exports larger than 10 MB. This result does not qualify full Mathlib 4.34.1, Init/Std, Navier–Stokes, Cedar, CSLib, or a competitive Arena submission.

## Remaining frontier: 24 UNKNOWNs

There are **13 expected ACCEPT and 11 expected REJECT** cases. Every remaining input was retraced on the exact candidate CLI. `frontier/frontier.json` records input and trace digests, expected verdicts, and first declaration boundaries; `frontier/logs/` preserves the full traces.

| First boundary | Cases | Consequence |
|---|---|---|
| `_private.Init.Prelude.0.noConfusion_of_Nat.aux._f` | `init-prelude`; all four magma tests | Five tests now share this valid-prefix boundary; `init-prelude` advanced from `eq_of_heq` without yet gaining a final decision |
| Performance conversion | `args-before-unfold`, both `folded-constant` tests, `shared-subterm`, `refute-cheap-first` | Four positive and one negative case still stop at differing neutral heads |
| Stuck projection in a valid matcher prefix | `proj-of-stuck-prop`, `proj-of-subst-prop`, `rec-missing-ih`, `rec-of-subst-prop` | Support the valid prefix before deriving the required negative verdict |
| Inductive admission | `fueled-chain` (Except), `grind-ring-5` (Char), `nested-unused-param` (T), `indexedUnitEta`, `indexedStructEta` | Exact admission obligations remain unresolved |
| Recursor / structure conversion | `RBTree.id_spec`, `structEta` | Direct constructor eta alone did not close the external structure test |
| Certified nonconversion | `ruleKbad`, `ruleKAcc`, `accRecNoEta` | K must remain inapplicable; a decisive negative conversion warrant is still needed |

**Priority remains residual closure.** The next shared target is the five-case Nat no-confusion prefix, with full 194/193 reclosure required after every candidate. No unsupported case may be forced to REJECT merely because the Arena labels it bad.

## Evidence and failed lineage

- `result.json`, `current-rows.json`, and `round1-rows.json`: final CI result and all 387 per-test observations, including input SHA-256 values. Row files are split and compacted from the artifact's `rows.json` without changing their data.
- `cli-stack.json`: the two CLI checks under the 8 MiB launcher stack.
- Original exact-baseline trace: diagnostic revision `d291113507e053741a41ff276447efe9a8ac658d`, [run 36777098878](https://github.com/heathsanchez/test/actions/runs/36777098878), artifact `11125309998`, SHA-256 `9eadbe01e3eb2a21c60d9eb2647e87d5c6f6f46559fe0d275a625d21e83e89cb`.
- Four-closure intermediate: `0a249f43b4f809dc75ca3221dc2b606d3fca595e`, [run 36780213533](https://github.com/heathsanchez/test/actions/runs/36780213533), artifact `11127113954`, digest `716ed8cfd95ea1ea77a46ff871d703e8b9bdde2e8621b01bc52d978a1999bdbb`.
- Five-closure intermediate: `527b6af44693404157eca654045e7bcb2d1452e3`, [run 36780898741](https://github.com/heathsanchez/test/actions/runs/36780898741), artifact `11127910920`, digest `dd8f31b5de4aa0fc65a7e19eb5d7b6f217ec1e6f1faf87615f1e9f22bae2c906`.
- `lineage/replays.json`: local experimental summaries, including the initial 8 MiB baseline abort. These are local experiments, separate from the CI qualification above.
- `lineage/rejected-elimination.patch`: computed-major reduction, neutral constant projections, and post-WHNF projection congruence, against c362. The first two stages changed obstructions without earning a case; the third regressed `proj-stuck-struct`. Excluded from the candidate.
- `lineage/unpromoted-structure-eta.patch`: direct, typed reconstruction from exact projections, against the five-closure source. Its focused positive/negative test passed, and both corpus counts were unchanged. It did not close `structEta`; excluded.
- `lineage/unpromoted-probes.patch`: diagnostic probes and a 4,096-step congruence probe experiment against the five-closure source. No gain on the six selected performance cases; no full qualification claimed. Excluded.

The parallel `f682fd87...` implementation remains a separate lineage. This candidate descends from the strict c362 qualification and does not inherit the parallel implementation's unresolved accounting or source-review findings.
