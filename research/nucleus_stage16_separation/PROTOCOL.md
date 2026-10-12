# Nucleus stage-16 source-qualified rigid-neutral separator (freeze before program)

Date 2026-10-12 NZDT. User objective: one native UNKNOWN→ACCEPT with no soundness regression. This specific experiment is a **falsifier of a proposed rule**, not an acceptance claim. We preserve the native 118/71/7, zero-wrong baseline.

## Immutable authorities
- Nucleus current prior three-arm qualification: heathsanchez/test@684d761244e95b8bf0ea98fb4821b1d248f03d5d; native [run 38111316772](https://github.com/heathsanchez/test/actions/runs/38111316772) at 118 ACCEPT / 71 REJECT / 7 UNKNOWN, zero wrong, with proof-irrelevance and field congruence off/on tie. The two later guarded-field retries [38200431470](https://github.com/heathsanchez/test/actions/runs/38200431470) and [38200547145](https://github.com/heathsanchez/test/actions/runs/38200547145) also gained zero complete ACCEPTs under protected native 196 verification.
- Frozen Arena export corpus artifact leanprover/lean-kernel-arena 11272848230, artifact ZIP SHA256 `f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2`, fixed Arena source commit b1d6e91d6de351f9bcf21e6b039f4d51d6b9bb42; includes native good inputs for six Init/Grind/Magma residuals and fueled-chain.
- Nucleus stage16 diagnostic evidence from heathsanchez/test [run #38200079646](https://github.com/heathsanchez/test/actions/runs/38200079646) artifact #11724049727, ZIP SHA256 `3282352b1ae86dd5e2e8cadd15009bc2e845a52ef54f6c51d34938139769e990`; original source commit ad207417730ac2ec1264f630872be34345127b41. This contains raw seven.json, report.json, source SHA and source-bound typed operand, environment, independent conversion/reducible-head probes.
- Target Lean version declared by artifact `4.34.1`, hash `5045d0056413266e57c625dcd7c365b10e377c52`. Original Lean trust source and native Nucleus checks are distinct.

## Frozen source-question and negative controls
Test six NON-fueled residual exports: `init-prelude`, `perf/grind-ring-5`, `perf/magma-list-pair-n7`, `perf/magma-list-pair-n21`, `perf/magma-list-deep-n21`, `perf/magma-list-deep-n36`. Independently decode the export-local constant IDs from NAME constructions in the **source file**, not hardcoded tables. Compare first two recorded WHNF pairs and source-bearing BVar/context; require the constant is `Nat.succ` and the counterpart is a free neutral `FreeId(0)`. Do not rely on name IDs recurring across files. Confirm `distinct-neutral-heads` remains the result across tested fallback policies. The first tested field-application premise is then **not a valid general definitional congruence route**.

Independently prove through pinned Lean 4.34.1 that the general equation `∀ (a b : Nat), Nat.succ a = b` is false (e.g. a=b=0); this is a countermodel to *universally* equating those term shapes. It **does not** prove the real Lean theorem cannot have a different conversion proof, or that no additional source-specific hypothesis could relate this particular pair. No source theorem name, benchmark fingerprint or numeric import IDs may authorize equality.

Adversarial: tamper with source SHA, misname NameId, or replace neutral Free0 with another head → parser/qualification fail closed. Fueled-chain has a DIFFERENT lambda/lambda shape and must not be grouped with the six.

## Promotion criteria
If source/original traces bind exactly, plus separate Lean native universal-rule countermodel proof checks, publish **WARRANTED_BOUNDED_REJECTED_FIELD_ARGUMENT_RULE**. Native full-case verdict remains UNKNOWN. Do not claim a new ACCEPT or any solver speed gain. Correct next search focuses on alternative K/iota/recursor/typed projection reduction path with *source-derived* obligations, not patching this known false premise. Prevent scope creep to broad Nat.succ≠free universal theorem: countermodel is to the general equality axiom only, not an inequality for every instantiation.

Source and qualification are isolated; no production changes.
