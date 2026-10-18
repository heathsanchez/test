# When CI Is Green but the Claim Is Not: A Source-Scoped Developer-Agent Evidence Resource

**Gemma 4 Developer Agent Paper / Best New Resource candidate — NOT SUBMITTED.**  
Status as of 2026-10-18: **WARRANTED_BOUNDED_PACKET_CONSISTENCY + WARRANTED_BOUNDED_SOURCE_NATIVE_HELDOUT_GO_V2**. The latter is a prospective frozen *test protocol* applied retrospectively to a published upstream fix, not a hidden model generalization.  
**Not established:** independent model performance, novelty vs existing prior art, actual model-generated repairs, benchmark generalization, economic superiority, Gemma 4 use, prize eligibility.

## Abstract

Developer agents can describe a patch as "verified" even when its evidence belongs to another commit, an unrelated CI job, a different claim scope, or a test that was never executed. We present an initial source-scoped **evidence-admissibility evaluation resource** built from seven previously independently checked public research cases spanning Go application behavior, code review, formal transport proofs, and Python test admissions. A frozen benchmark constructor generated 49 deliberately invalid packets from seven admissible scoped historical packets. In native GitHub CI, an explicit typed-packet verifier admitted 7/7 originals and rejected 49/49 constructed falsifiers. By comparison, accepting any green CI admitted all 49 invalid packets; a source/run-only baseline admitted 35. These are *designed-control construction results*, not an estimated real-world error rate. A subsequent source-distinct external Go experiment executed an independently authored seven-subtest oracle on two pinned upstream revisions: original source 6 PASS / 1 FAIL and contributor-fixed source 7 PASS / 0 FAIL. Exact-source, altered-test and missing-test controls were qualified. No Gemma model, previously unseen model-generated patch or strong-agent comparator was executed; the next test must involve new developer-agent outputs and independent source-native oracles.

## Motivation and scientific question

A passing test is evidence of a **specific proposition**, at a specific source version, against a specific test obligation. It does not license arbitrary statements about correctness or safe deployment. Can a portable benchmark express this distinction in developer-agent terms, with negative cases that preserve plausible positive CI metadata but change only a consequential source, claim, phase, or revocation condition?

The candidate resource has an explicit machine-consumable packet and a precise *decline* outcome for unwarranted claims. It is designed as evaluation infrastructure that a coding agent could face after attempting to solve a task, not as a software-repair algorithm.

## Public original case authorities

| Case | Original externally executing evidence | Scope |
|---|---|---|
| ReviewBench Go PR #9 | [Native RED→candidate GREEN→restore RED, official container](https://github.com/heathsanchez/test/actions/runs/38634850681) | Exact historical SHA; not unique discovery/safe merge |
| go-ozzo/ozzo-validation E164 | [Original Go application predicate old/head](https://github.com/heathsanchez/test/actions/runs/38600969324) | Semantic difference, not independently correct policy |
| asaskevich/govalidator Email | [Separate Go matrix job on same run](https://github.com/heathsanchez/test/actions/runs/38600969324) | Semantic difference; contributor PR closed/unmerged |
| CLC → FLASH V3 | [Lean finite transport with actual FLASH admission](https://github.com/heathsanchez/realitygraph/actions/runs/39079945123) | Does **not** include durable certificate reauthentication |
| Nucleus | [Frozen196 verifier and malicious negatives](https://github.com/heathsanchez/test/actions/runs/39018141144) | Exact 196-case boundary, not full Mathlib |
| AnyIO | [Original source-protected failure admitted](https://github.com/heathsanchez/test/actions/runs/39077610372) | A native failing obligation, NOT new acquired method |
| Itsdangerous | [Original clean suite and inherited tests](https://github.com/heathsanchez/test/actions/runs/39075931136) | Admission and regression qualification; G2 not demonstrated |

These are **prior experiments** and are attributed rather than presented as newly run source-native tests. Their original proof/test limits travel with the dataset.

## Protocol, methods and reproducibility

Original protocol frozen in commit [bb33d34a](https://github.com/heathsanchez/test/commit/bb33d34a479d439cf4d38ce9601462c53b0beda1) before implementation. Authority descriptions fixed in [67915bd3](https://github.com/heathsanchez/test/commit/67915bd323e338edd9ca3e9d4db8e7e8b3faee1c). All seven historical original CI job statuses were checked again through GitHub's job records, with separate original Go matrix jobs preserved.

Each original packet identifies (1) source/corpus subject, (2) original CI run and job, (3) bounded claim, (4) named evidence phases, (5) status and (6) explicit revocation state. We generate seven falsifiers per packet:

1. mismatched subject identity;
2. mismatched CI run;
3. mismatched job, including a case sharing the real original run ID;
4. missing required observation phase;
5. extra forged assertion phase;
6. revoked source;
7. overbroad unsupported claim.

We compare five deterministic strategies: unconditional acceptance; green CI only; exact subject and green CI; exact subject/run and green CI; and exact typed source, CI job, scoped claim, phases and revocation.

The new tests are deliberately constructed and the typed verifier checks consistency with a frozen local manifest; it does **not** use a cryptographically authenticated independent CI oracle. The result is a quality gate for a future resource, not the resource's full security qualification.

## Results

Independent GitHub Actions [#39087453567](https://github.com/heathsanchez/test/actions/runs/39087453567) completed successfully at [source head 12b1119d](https://github.com/heathsanchez/test/commit/12b1119d73398e93957633dca272a13b3d8d858a). Workflow steps included independent process repeat with bytewise identical dataset and metrics, frozen protocol ancestry checks, and artifact upload. [Original archived resource #12121133774](https://github.com/heathsanchez/test/actions/runs/39087453567/artifacts/12121133774), GitHub upload-log ZIP digest `sha256:612f19b4aa0d5e3681f59efe7db936236d403d22c59f5648e746e0d5f5c171a6` (provider-reported, **not separately rehashed here**).

| Method | Positive admissions (of 7) | Invalid admissions (of 49) |
|---|---:|---:|
| Accept everything | 7 | 49 |
| Accept any green CI | 7 | 49 |
| Subject + green CI | 7 | 42 |
| Subject + run + green CI | 7 | 35 |
| Typed scoped packet | **7** | **0** |

The results measure **construction agreement** on deliberately generated falsifiers. Since the true labels are specified by the same protocol that designed the typed verifier, its perfect score is expected and **must not** be reported as evidence of scientific superiority. No independent model run or source-native fresh repair was performed in this step.

`python research/cash_track_20261018/runner.py --self-test --out research/cash_track_20261018/out` reproduces the candidate resource. Native Python 3.11 GitHub CI verifies deterministic replay.

## Source-distinct native validation — outside the original seven-packet construction

A first independent external repository was selected from public PR metadata **before reading its production patch**: [OllyInsurance/fern-platform PR #16](https://github.com/OllyInsurance/fern-platform/pull/16). The [source and outcome protocol](https://github.com/heathsanchez/test/blob/research/cashtrack-evidence-resource-20261018/research/cash_track_20261018/HELDOUT_FERN_PROTOCOL.md) was frozen in [commit 3ec172aa](https://github.com/heathsanchez/test/commit/3ec172aa162787d9acc0d7dad3aceeb994dfa6b5). The public PR author had already identified the defect: an original Go test stopped by a declared outage emitted `STEP FAIL`, not `CHECK FAIL`, and was wrongly treated as a product failure. The independent test cases were then human-authored **after inspecting only the production patch**, not the original contributor tests. The published upstream fix is not MathGraph's discovery.

Both actual original Go package source revisions were fetched by exact commit and received identical independently authored test bytes. Seven protected cases covered a declared-outage STEP failure, an ordinary STEP failure, an independently unexcused product CHECK failure despite an outage, the previously working CHECK annotation case, and additional mixed/note controls.

| Method/source on seven frozen subtests | Correct classifications | Incorrect |
|---|---:|---:|
| Naive: any outage string excuses the result | 3 | 4 |
| Naive: CHECK-only annotation recognizer | 5 | 2 |
| Original upstream base `ee843f4` native Go | 6 | 1 |
| Original contributor head `ddff2c8` native Go | **7** | **0** |

The [initial native Actions #39093122857](https://github.com/heathsanchez/test/actions/runs/39093122857) established exact source original 6/7 → contributor head 7/7 and physical delete-test `go test` exit 0 with zero named tests. The [V2 source-authority protocol](https://github.com/heathsanchez/test/blob/research/cashtrack-evidence-resource-20261018/research/cash_track_20261018/HELDOUT_V2_SOURCE_AUTHORITY_PROTOCOL.md) was frozen **before** the source-integrity fix: HEAD SHA alone does not prove a clean source tree. On [independent V2 CI #39093369502](https://github.com/heathsanchez/test/actions/runs/39093369502), the checker refused modified tracked Go source, modified frozen test bytes, and extra untracked Go source while the Git HEAD commit remained unchanged; restoring original bytes restored admission. Exact source identity and clean-tree conditions passed before and after native execution on both original revisions. The [archived V2 artifact #12123821495](https://github.com/heathsanchez/test/actions/runs/39093369502/artifacts/12123821495) was independently downloaded, SHA-256 verified as `65ab70a2f2a512d16f3ccecf6489cf3421abc160292a8895717a09b82e94dc87`, opened, and the original independent Go transcripts and manifest parsed.

**Interpretation:** this is an independently source-native **classification and source integrity** result, not a prospective blindly generated coding-agent repair, and not a claim that our verifier generalizes from one case. The human-written fixture and known author fix are part of the trust/execution boundary. The final source-bound claim is that `envFault` on these two exact original commits has the observed behavior. The complete system, hidden model generalization, correctly authorized deployment, and model-agent superiority remain UNKNOWN.

## Prior art and candidate distinct contribution

- **SWE-bench / SWE-bench Verified** test candidate patches using independently specified fail-to-pass and pass-to-pass tests; these are primarily *patch outcome* evaluations. OpenAI's [February 2026 critique](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/) demonstrates that benchmark tests themselves can be underspecified or contaminated. The present resource does not solve those problems but makes the **right to assert a claimed result** a separate explicit evaluation target.
- **SWE-bench Pro** ([Deng et al., 2025](https://arxiv.org/abs/2509.16941)) raises repository-level difficulty and controls contamination. We do not outperform it or use its hidden data.
- **RepoReason** ([Li, Su & Lyu, ACL 2026](https://aclanthology.org/2026.acl-long.399/)) already combines mutation-generated tasks and executable semantic oracles. Therefore source-backed mutations and executable scoring are **not new by themselves**. The narrower **CANDIDATE distinction** is binding each coding-agent *verification claim* to its exact subject, test/run identity, proof phases, claim scope, verified execution, source cleanliness, and withdrawal conditions.
- **Related source-qualified MathGraph work** was developed before this competition and must be attributed, not presented as new Gemma experimentation. The newly constructed packet controls and the source-distinct Go qualification are the concrete additions here.

### Why it matters for Gemma 4

A local coding agent cannot merely say a patch passed tests; it should return a *machine-checkable, source-bound assertion* describing the test actually executed. Our proposed resource would let a Gemma agent produce/inspect evidence packets and receive exact ACCEPT, REJECT or UNKNOWN outcomes without conflating `go test` process exit 0 with actual named-test execution. **No Gemma agent is yet connected to this interface**, so relevance to Gemma 4 remains a candidate rather than an empirical finding.

## Comparison, limitations, next falsifier

A capable model or rule engine furnished with the same exact evidence schema may tie the typed verifier. Green-CI-only and literal regex baselines are intentionally weak, not matched frontier coding agents. The extra native source case compares behavior of a contributor's known fix, not an automatically generated MathGraph repair. The benchmark currently lacks source-distinct new agent traces, external adjudication, empirical reward signal, a genuine blind holdout, original raw artifact reauthentication inside the benchmark process, end-user decision measurement, and full-lifecycle time/cost. It is not a demonstration of autonomous method creation, cross-domain capability compounding, or general proof verification.

**Cheapest consequential next experiment:** the source-distinct native *test-reproduction* gate is now complete on one new Go project; next freeze an **actually unseen model-produced coding-agent task/output** and its independent native oracle, then run an unchanged agent baseline versus the same agent with typed evidence admission, with equal information, tools, runtime and model budget. Include real changed-head and revoked-evidence controls. Only after an external difference is measured should a competitive claim be promoted.

## Prize-specific obligations remaining

- Gemma Kaggle Writeup must be submitted via the participant's account by **12 November 2026, 23:59 UTC**. Current draft is **not** a Kaggle Writeup.
- Best New Resource eligibility and originality relative to prior benchmarks require a real relevance check to Gemma 4 developer agents, actual user-facing resource usability and prior-art comparison.
- Public disclosure/commit rights of any *new* dataset/tool and the competition's applicable rules must be checked before publishing additional components.
- Other competitions (AIMO, ARC, Apart) require separate task-specific evidence; this bounded packet test should not be recycled as a supposedly novel result.

**Release boundary:** this file and the constructed benchmark are intended for research audit; do not infer official competitor scoring, prize entitlement, independent safety certification, or external endorsement.
