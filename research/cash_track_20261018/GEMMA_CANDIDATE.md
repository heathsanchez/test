# When CI Is Green but the Claim Is Not: A Source-Scoped Developer-Agent Evidence Resource

**Gemma 4 Developer Agent Paper / Best New Resource candidate — NOT SUBMITTED.**  
Status as of 2026-10-18: **WARRANTED_BOUNDED_PACKET_CONSISTENCY** on newly generated controls.  
**Not established:** independent model performance, novelty vs existing prior art, actual model-generated repairs, benchmark generalization, economic superiority, Gemma 4 use, prize eligibility.

## Abstract

Developer agents can describe a patch as "verified" even when its evidence belongs to another commit, an unrelated CI job, a different claim scope, or a test that was never executed. We present an initial source-scoped **evidence-admissibility evaluation resource** built from seven previously independently checked public research cases spanning Go application behavior, code review, formal transport proofs, and Python test admissions. A frozen benchmark constructor generated 49 deliberately invalid packets from seven admissible scoped historical packets. In native GitHub CI, an explicit typed-packet verifier admitted 7/7 originals and rejected 49/49 constructed falsifiers. By comparison, accepting any green CI admitted all 49 invalid packets; a source/run-only baseline admitted 35. These are *designed-control construction results*, not an estimated real-world error rate. No Gemma model, new upstream native test, previously unseen developer-agent output or strong-agent comparator was executed. The next test is independently acquired agent outputs with genuine source-native oracles.

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

## Comparison, limitations, next falsifier

A capable model or rule engine furnished with the same exact evidence schema may tie the typed verifier. A green-CI-only baseline is intentionally weak; it is not a matched frontier coding agent. The benchmark currently lacks source-distinct new agent traces, external adjudication, empirical reward signal, a genuine blind holdout, original raw artifact reauthentication inside the benchmark process, end-user decision measurement, and full-lifecycle time/cost. It is not a demonstration of autonomous method creation, cross-domain capability compounding, or general proof verification.

**Cheapest consequential next experiment:** freeze a source-distinct developer-agent task and its independent native test; run an unchanged agent baseline and the same agent with typed evidence admission, with equal information, tools, runtime and model budget. Include real changed-head and revoked-evidence controls. Only after an external difference is measured should a competitive claim be promoted.

## Prize-specific obligations remaining

- Gemma Kaggle Writeup must be submitted via the participant's account by **12 November 2026, 23:59 UTC**. Current draft is **not** a Kaggle Writeup.
- Best New Resource eligibility and originality relative to prior benchmarks require a real relevance check to Gemma 4 developer agents, actual user-facing resource usability and prior-art comparison.
- Public disclosure/commit rights of any *new* dataset/tool and the competition's applicable rules must be checked before publishing additional components.
- Other competitions (AIMO, ARC, Apart) require separate task-specific evidence; this bounded packet test should not be recycled as a supposedly novel result.

**Release boundary:** this file and the constructed benchmark are intended for research audit; do not infer official competitor scoring, prize entitlement, independent safety certification, or external endorsement.
