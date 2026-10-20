# 2021 environmental yeast V3c — independent source and warrant audit

**Audit freeze:** 2026-10-20, after the V3c holdout outcomes were already opened. This is a **post-hoc** source-exact qualification, not a prospective biological test or a second independent experiment.

## Fixed authority and code separation
- Immutable original study source: `Costanzo_et_al_Data_File_3_Raw_interaction_dataset.xlsx`, Zenodo record `4560674`, SHA-256 `b4e242087e554df1adc648aefb890144d397a1eb303a55509a90ae08e912c488`, MD5 `f81a8123a8113b795a00e8e154fa072d`.
- Original V3c complete native CI: `heathsanchez/test` run `39349577864` at commit `f006d3f3e90c0b542c1becc44b75df53df67f3dd`.
- GitHub Actions artifacts from original run: 12232069578 (allowlisted only), 12233125123 (sealed predictions), 12233420071 (native evaluator).
- Require each raw JSON payload byte SHA-256 to match frozen author receipts and original workbook digest before doing any analysis.
- New audit script does not import, call, or alter original source steward, predictor or evaluator. It independently obtains raw source, matches source allele-coded rows to target identities, checks the original four known controls, then reads all ten protected candidate contexts.

## Protection and statistical boundary
1. Recompute all original 200 target/method outcome records from source `mean_differential_epsilon`, `differential_p_value`, both signed biological replicates and untreated reference. Reject any disagreement with saved immutable outcomes.
2. Primary source-published event: reported `p < 0.05` and absolute mean differential interaction `> 0.08`. Stricter *prespecified original secondary*: `p < 0.005`, `abs(effect) > 0.08`, and both biological replicates sign-concordant with effect.
3. Recompute exact method counts, missingness, oracle, and original query-cluster bootstrap; only eight distinct target query genes exist, so 200 tested pairs are not 200 independent biological replications.
4. Exploratory *post-hoc* multiplicity diagnostic: BH across all 2000 preselected target×10-context source P-values (missing treated as 1), and Bonferroni familywise threshold `0.05/2000`. Also BH separately across each method's 200 selected targets; the method-only selection changes the family and is NOT a precommitted statistical authority. These do not replace the source's full study-wide multiplicity correction, independent experimental validation, or source P-value assumptions.
5. No method advantage is warranted unless the original preregistered positive cluster-bootstrap lower bound and strong baselines pass; the original interval already includes zero.

## Consequence/authority withdrawal falsifier
- Fix exactly one selected authentic strong-positive target/source cell from the *already exposed* original V3c archive, indexed by its full allele pair and named environment.
- Bind each selected method-cell event to a source-workbook digest, literal cell token and threshold-policy token. Revoke only this single cell's evidence token, recompute which claims and method hit counts lose warrant, assert unrelated method counts remain exactly unchanged, then restore the same original cell evidence and require all original counts.
- A separate total-source authority withdrawal must make every source-dependent cell claim `UNKNOWN`, not `FALSE` or `EQ`. Alternative support is not claimed if no independent original measurement was provided.
- This is a finite audit of the QCK/CLC/Flash semantics, not a formal proof of complete mediation, not a Lean theorem and not a new biological prediction.

**Promotion:** `WARRANTED_BOUNDED` only for source-exact replay and the tested finite provenance rules. Preserve failures, apparatus errors, post-hoc distinctions, and UNKNOWNs. No revised method receives prospective credit for an already opened holdout.