# Yeast ExE V2 — source-grouped intervention discrimination: RESULT AND INDEPENDENT RECEIPT AUDIT

**Executed 2026-10-19 NZT. Scope:** authentic retrospective holdout of original Costanzo 2016 ExE (essential×essential temperature-sensitive yeast alleles) inside a precommitted, gene-disjoint protocol. This is not prospective wet-lab data, not a new biological law, and not a p-value-qualified genetic interaction result.

## Lineage and source authority
- Original 2016 archive SHA256 `53c69b7dc6e54aeff54afddfa84a24741b9e09c2fdc6bfd9fcbf0b73939ec30f` (source URL: https://thecellmap.org/yeast/costanzo2016/). Exact ExE CDT original member SHA256 `6ac9ad373846836ae3ac9800ca3843358ffe98d442ae66c17cea2bd66fe98180`.
- Metadata-only preflight [run 39224704675](https://github.com/heathsanchez/test/actions/runs/39224704675) exposed only source header, names and metadata: ExE has 792 TSA array columns, a native ORF row and strain labels. Numeric ExE outcomes remained unopened until the method was committed.
- Frozen scientific method [commit 15ee43b5092af1290d0bb950e4dcbb25f1254989](https://github.com/heathsanchez/test/commit/15ee43b5092af1290d0bb950e4dcbb25f1254989). First [CI run 39226218895](https://github.com/heathsanchez/test/actions/runs/39226218895) failed the SYNTHETIC preflight before ExE source access due `select.py` shadowing the Python standard library. Apparatus-only rename to `predict.py` was byte-identical, independently compared during [commit 704049cc](https://github.com/heathsanchez/test/commit/704049cc9ec57bedffae5ce5fa3010fae4d35ffa), before ExE outcomes. No scientific method or threshold was altered.
- [Full native green run #39226740802](https://github.com/heathsanchez/test/actions/runs/39226740802), job `117974751993`, [authentic artifact #12174480784](https://github.com/heathsanchez/test/actions/runs/39226740802/artifacts/12174480784); downloaded exact ZIP independently SHA256 `ab9314cfa9d3f7b0906ce21b398c156e8feb8253db6a96f0be0a64e7e4bbf205`. Pre-outcome SHA256 `d34095f4cf51a0c8b0088471e8b36bd7fdff1d42839795cfadc3792cab432f1b`. Independent decimal-native verifier (separate source file, no selector import) and synthetic causal target/reciprocal-data withdrawal tests green.

## Strict admission
- 557 calibration-gene ORFs and 239 heldout-gene ORFs; **zero intersecting gene identities** by exact systematic ORF. One representative allele per gene, 315 complete initial-panel calibration genes, 141 complete initial-panel holdout genes; 47 disjoint pairs (94 distinct heldout ORFs) satisfy 8-panel epsilon max gap <=0.08.
- Every one of 136 selected array backgrounds has a distinct gene ORF **from calibration only**, with none of the 239 target ORFs among them. No reciprocal available source cells are numerically used by the selector. Artificially replacing target-candidate and calibration-target reciprocal cells with invalid markers left **all synthetic predictions exactly unchanged**. The real selector then sealed predictions before the independent evaluator opened any protected ExE target-candidate outcomes.

## Frozen primary outcome (gap >= 0.16)
| Method | observed/47 | distinctions/47 |
| --- | ---: | ---: |
| contrast-mixture exploratory policy | 44 | **10** |
| matched KNN point estimate | 45 | 8 |
| KNN variance UCB | 44 | 10 |
| global marginal variance | 47 | **11** |
| Ridge(alpha=5) point prediction | 45 | 1 |
| seeded random choice | 44 | 4 |

Among 128 predeclared contexts per pair, **46/47** had a retrospectively measured separating candidate; this is an *oracle diagnostic*, never part of the selection algorithm. Primary contrast-mixture − matched KNN all-attempt success: +2/47 or +4.26 percentage points, descriptive pair bootstrap interval **[-10.64,+19.15] points**, spanning zero; no justified advantage. Global variance beats contrast-mixture 11 to 10 with no missing values; strong comparator must not be omitted. Within-pair overlap of success against KNN: 2 both, 8 only mixture, 6 only KNN, 31 neither. Against variance: 2 both, 8 only mixture, 9 only variance, 28 neither. Mixture chose the identical intervention to point KNN for only 2/47 pairs and to global variance for only 3/47: this was a genuinely different policy, not an identity clone.

**Post-hoc threshold sensitivity** (NOT preregistered and MUST NOT be used to claim advantage): at gap 0.12, mix/variance/point hits 18/16/11; at original 0.16, 10/11/8; at 0.20, 6/7/7; at 0.24, 3/6/5. No robustly leading policy. Recorded in the separately audited JSON report.

## Epistemic classification
- **WARRANTED_BOUNDED_REAL_SOURCE**: ExE input source verified by archive+member hash; exact source-native nonessential-vs-essential matrix identity respected; 47 original eight-panel-equivalent pairs, of which 46/47 had an extra measured score contrast >=0.16 on 128 candidates; gene-grouping and reciprocal access protocol passed; two-stage evidence and source-decimal 0.16 threshold passed; independent ZIP/receipt hash and per-pair count audit passed.
- **REJECTED / NOT WARRANTED**: no significant source-independent exploration advantage over strong conventional selectors; positive point KNN difference interval crosses zero, global variance beats the candidate. Don't interpret post-hoc threshold 0.12 as a successful new primary method. The original V1a flawed LCB remains a separate negative on NxN; it is not identical to this V2 policy.
- **UNKNOWN**: individual biological significance due absent per-measurement p-values in matrix, assay/allele replication, generalization outside the 2016 study, intervention cost/temperature dependence, causal mechanism, certified biological law, superior future discovery method, source-neutral inference beyond the fixed algorithm. Biological gene IDs may have unmodelled functional redundancy or alias uncertainty; dataset-specific sampling of measurable eight-panel pairs can change prevalence estimates.

## Most important residual
The 46/47 oracle coverage and 10/47 realized hit rate isolate a **distinguishing-intervention acquisition problem**: access to a separator is not the ability to predict or discover its identity efficiently. The existing finite Metalogic no-go already distinguishes representation invariance from information-bearing intervention; the yeast results do not create a stronger ontology. The next actual science experiment should use **a different study and acquisition modality with raw intervention outcomes, replicate statistics or p-values**, freeze a new method and complete strong active-learning baselines **before opening** that data. A separate lower-risk cross-domain demonstration can use MathGraph's existing selective claim-withdrawal core with real biological source-cell dependencies, but that tests evidence accounting, not new biological prediction.