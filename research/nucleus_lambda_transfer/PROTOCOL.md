# Nucleus source-certified guarded lambda-argument transfer — prospective gate

Date 2026-10-12 NZDT. Experiment isolated from production and Arena submission.

## Frozen evidence and source
- Prior native full196 qualification: heathsanchez/test@684d761244e95b8bf0ea98fb4821b1d248f03d5d, [CI 38111316772](https://github.com/heathsanchez/test/actions/runs/38111316772), counts 118 ACCEPT/71 REJECT/7 UNKNOWN/0 incorrect; original Rust subtree SHA 311cf82ae95e5bdff55e4529892209da6d85e5bd.
- Original official Arena 196-case export: leanprover/lean-kernel-arena artifact #11272848230, source b1d6e91d6de351f9bcf21e6b039f4d51d6b9bb42. Protect all 71 invalid exports, original verdicts, special exact false-index negative (sha256 2a090edfcfa2a16191f17a433617aaf045fc9b11cd0e2a93405b705d8a899688) and malformed nested unused-parameter recursor.
- Native Nucleus stage16 diagnostic [CI 38200079646](https://github.com/heathsanchez/test/actions/runs/38200079646), source ad207417730ac2ec1264f630872be34345127b41, artifact #11724049727: six Init/Grind/Magma workloads under strict field-application route have Nat.succ/Free0 rigid counterpair, and remain refuted under every tested conversion policy; the separate [no-go qualifier 38231472810](https://github.com/heathsanchez/test/actions/runs/38231472810) rejects treating these as universally equal. Fueled-chain instead has two source-typed LAMBDA/LAMBDA actual arguments for which PreferredOnly converts to Refuted but full 8192-step GuardedSemanticFallback independently reports PROVEN, with explicit original closure/env identity and type information.
- Source field-application and contextual proof patch scripts are the exact previously qualified .github/scripts/nucleus_contextual_capability_patch_v1.py and nucleus_field_application_patch_v1.py. The new code will ONLY add an optional, source-typed fallback in checked_field_application_congruence at actual argument comparison, after existing exact field equality, Pi domains, argument inference and type checking.

## Primary question
Can reuse of an already independently proven guarded relational conversion WITNESS for two genuine source-LAMBDA arguments change the real Nucleus native fueled-chain export from UNKNOWN to ACCEPT, without any incorrect accepted bad sources or loss of prior proofs? This is NOT permission to equate Nat.succ and a free local or to rely on a theorem name/fixture fingerprint.

## Candidate
- Only when original PreferredOnly actual-argument conversion fails, both original argument syntax have expression type Expr::Lam, and source-checked argument types each convert to its independently checked dependent Pi domain.
- Invoke the existing native convert_with_policy_in_context at budget <=8192 with GuardedSemanticFallback and the same exact lexical context and depth. Admit ONLY if this independent converter returns Judgment::Proven. Preserve failure/refutation/UNKNOWN unchanged otherwise. The new option is feature-flagged and does not mutate saved theorem/field source or special case names.
- Retain existing non-reentrancy guard of checked_field_application_congruence. Do not regard the certificate label as external Lean kernel proof; full native regression and source model obligations remain necessary.

## Tests
1. Baseline binary built before source edits; candidate patch source bound and source hash evidence.
2. Run old + candidate feature OFF + candidate feature ON on all frozen 196 native exports, per-case verdicts and aggregate, with zero false acceptance/rejection, zero regressions. Assert original/off 118/71/7, zero wrong. Target at least one **new complete export ACCEPT** to promote. If none, return RED and preserve exact evidence, no success claim.
3. Record first-trace stage16 relation under ON vs OFF, number of new guarded-Lambda witnesses; counters prove existing Nat.succ/Free0 cases do not gain a false conversion. Avoid extra logging slowing benchmark claims.
4. Native false-index negative must not ACCEPT and malformed nested-recursion negative must REJECT. Rust unit tests and cargo lock/sources frozen. Exactly identify any positive and negative changes.
5. If ON gains a complete accept with negatives protected, run a separate independent source-check (pinned Lean 4.34.1 or source-signed Arena expected GOOD) and compare strong baseline; promote WARRANTED_BOUNDED_NATIVE_FAILURE_TO_SUCCESS on frozen corpus. This is NOT proof of full Mathlib or leaderboard number 1.
6. If ON fails to earn a complete accept, call it rejected as *that* transfer, not autonomous new grammar invention; next residual must be traced from the earliest unproved dependent path.

## Interpretations
The source of this reusable capability is an existing Nucleus guarded conversion algorithm, not the MSI Bundy proof critic or a newly invented theorem. This tests *cross-path internal source-certified capability reuse*, NOT true transfer from independently authored project. Therefore do NOT promote CROSS_PROJECT_GENERATIVE_IMPROVEMENT solely on this positive. The stronger cross-project goal still needs a source-independent verified target task and autonomous adapter.
