# Environmental biological distinction V3 — pre-outcome protocol

**Date**: 2026-10-20 (NZT). **Scientific state**: CANDIDATE until source-native held-out evaluation and separate audit complete.

## Authority / new physical source

Costanzo et al., *Environmental robustness of the global yeast genetic interaction network* (2021), DOI 10.5061/dryad.3r2280gfd. Source archive is a distinct environmental-intervention experiment, albeit the same research programme/organism as the 2016 prior, so **not full cross-species independence**. Original Zenodo archive record 4560674:

- `Costanzo_et_al_Data_File_1_Conditions_Strains_Fitness.xlsx` MD5 `feec6ee93cbdc6c29d1989b05bb15390`, SHA256 `02d97bf2c57397c781e4c7792430f89938c92da823df58836b53185cb62b4655`.
- `Costanzo_et_al_Data_File_3_Raw_interaction_dataset.xlsx` MD5 `f81a8123a8113b795a00e8e154fa072d`, SHA256 `b4e242087e554df1adc648aefb890144d397a1eb303a55509a90ae08e912c488`.

The metadata-only [run #39346448982](https://github.com/heathsanchez/test/actions/runs/39346448982) verified these bytes and sheet schemas without opening biological outcomes. Use the `Diagnostic array_complete` sheet (363201 data rows, 25 source-declared fields) and `Conditions` sheet metadata. The published experiment contains two biological replicates of environmental differential interaction, native P values, baseline reference and corrected differential interaction scores.

## Hypothesis, observation and tests

A *genetic-pair state* is `(query ORF, array ORF)`. The untreated reference is the comparator. The four **lexically first treatment labels** after excluding the independently source-declared `Reference condition + solvent` row from the source's 15-label conditions table are an initial observation interface, and the remaining ten are candidate new interventions. Labels/order determined solely from source metadata, never response values. Source-to-intervention meaning is relative to the independent 2021 paper; no novel physical law follows from contextual response.

**Prospective source holdout**: source genes assigned *globally*, deterministically with SHA-256(seed+systematic ORF) to calibration (<70%) or target (>=70%), independent of all outcomes. Only pairs whose two genes belong to the same group can enter that group; cross-group records are dropped. Thus the exact same systematic gene ORF cannot occur anywhere in both calibration and target, including reversed query/array orientation. No duplicates or missingness from protected target candidate interventions can affect eligibility. The target's known four environmental scores and untreated reference score are admitted as observations. Require all four known environments nonresponding by the paper-defined criterion. Select the first 200 eligible target genetic pairs in a deterministic *metadata and permitted-observation only* hash order; stop UNKNOWN if <40 targets or <1000 calibration pairs. Training may read all calibration responses.

**Primary target event**: at the method-selected previously unseen intervention, published per-condition `differential_p_value < 0.05` **and** `abs(mean_differential_epsilon) > 0.08`. This is the author's intermediate within-source criterion, *not* a direct experimental contrast test between two different genes, and does not imply familywide FWER/FDR control across all scanned interactions.

**Stricter secondary event**: `p < 0.005`, `abs(ε_differential) > 0.08`, and both biological replicates have nonzero sign concordant with the mean. This is a conservative multiplicity-aware proxy for selecting among ten options, not a proof of exact familywide type-I error rate or replicate independence.

**One intervention only per target pair**. If selected response is missing, report missing and count as no successful observed discovery, not as biological evidence of no effect. Post-hoc upper bound is whether *any measured* of the ten candidates meets the primary endpoint, evaluated strictly after the selector seal. Do not select on protected target candidate outcomes or their missingness.

## Frozen human-authored methods, complete matched input

All methods see only identical four initial observed response effects plus 2021 untreated reference effect for every target pair, and all candidate measurements for calibration pairs. All target candidates are prohibited and absent from the prediction process. Features fit on calibration only; common StandardScaler.

1. **Contrast exploration (candidate)**: `0.50*KNN(p_hit) + 0.25*sqrt(KNN(p_hit)*(1-KNN(p_hit))) + 0.25*global_hit_rate`; maximize. This source-neutral human-authored combination is an **unproven heuristic**; not certified confidence or autonomous operation discovery.
2. **Matched KNN (primary comparator)**: maximize inverse-distance weighted `KNN(p_hit)` with k=31 and distance weight `(d+0.05)^-1`.
3. **KNN expected effect**: maximize `abs(KNN mean differential epsilon)`.
4. **Logistic regression**: separate per-context `LogisticRegression(C=1, max_iter=500)` calibrated on source training labels.
5. **Random Forest**: separate per-context `RandomForestClassifier(n_estimators=100,min_samples_leaf=12,max_features='sqrt',seed=20261020+j)`.
6. **Global prevalence**: maximize training frequency of significant differential interaction by context.
7. **Seeded random**: uniform over ten contexts per target genetic pair, seed keyed to pair ID.

No method uses biology-specific annotations or query/array identifiers for numerical prediction. Same calibration and feature costs for everyone. Calibration score comparisons must include missingness, no selective target exclusions, the full 200/eligible attempts, and a query-gene-cluster bootstrap (4000 predeclared replicates) for method-difference uncertainty. Scientific status: WARRANTED only for exact scoped source-native outcome and evidence method; claim of advantage **only if** candidate beats matched KNN **and** all other strong baselines, positive cluster-bootstrap lower bound, and survives restrictive replicated endpoint and error controls. Otherwise TIE/REJECTED/UNKNOWN, never universal law.

## Isolation, source fidelity and adversarial failure controls

Three physical jobs: `source-steward` obtains and SHA256 pins workbook, reads source but **does not interpret or materialize target candidate numeric values**, then emits an allowlisted `allowed.json` with calibration measurements and target known features ONLY. `predictor` runs in a separate clean job, downloads *only* `allowed.json`, checks fields and gene overlap, computes method choices, writes and SHA256 seals `sealed_predictions.json`. `independent evaluator` runs only after the predictor job and independently reacquires+hashes the full original workbook before reading target candidate outcomes; it imports no predictor functions and rechecks all target known scores. Recompute report, strict and source-precise criteria; retain per-target evidence and raw digests.

Synthetic control must show altering all target hidden outcomes (including missingness) leaves allowed input and choices unchanged, and blocked target-query/array reciprocal channels do not leak to calibration; intentionally invalid schema/hash/split must fail closed. A publication-faithful claim must use actual source `differential_p_value`, not substitute `condition_p_value`, and preserve replication uncertainty. An implementation RED before opening protected outcomes is apparatus failure and never a negative biological result. Source must never be changed after seeing held-out outcomes except under independently preregistered new experiment; preserve lineage, negatives and supersession.

## Disqualifying limitations

P values may already be unadjusted for thousands of genes/interventions; even the stricter endpoint is not a formal cross-study multiple-testing correction. The 2021 data is observationally retrospective and produced by a related laboratory, not a new randomly assigned experiment or cross-species prospective discovery. Shared query-level lab batches induce dependence: bootstrap by query gene. Input data are published source-produced summary statistics, not independent raw colony image reprocessing. Positive results require future external experiment and strong active-design competitors, not a mere difference from random.
