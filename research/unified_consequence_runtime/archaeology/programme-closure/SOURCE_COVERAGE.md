# Accessible research-source coverage — 2026-10-15

Frozen metadata universe: **26 API-visible repositories owned by `heathsanchez` or `metalogiclabs`**, including forks and archived repositories. Repository identity is deduplicated by id; the collaborator listing of `metalogiclabs/mathgraph-lean-kernel` under `heathsanchez` is counted once. The freeze is the explicitly recorded repository/ref objects observed during enumeration, not an atomic claim about every GitHub object at every instant.

This is a source-recovery and coverage report. It does not qualify a scientific claim from a keyword, branch name or green workflow. The existing E/D/V54 warrants are preserved; the coverage scanner ran no scientific experiment.

## Coverage achieved

- Metadata rows: **4,443 branches**, **82 tags**, **6,611 workflows**, **39,435 runs**, **30,176 artifacts**.
- Repository, branch, tag, workflow and artifact endpoints reached their pagination boundary for all 26 repositories. Four run histories stop at explicit authentication errors; they are not interpreted as empty or complete.
- Sixteen non-shallow source histories were explicitly fetched/cloned and searched over frozen local refs: **29,319 distinct reachable commits**, **39,634 source-extension blobs**, **326,197,543 bytes**. Commit subjects were searched; this does not mean every full commit diff was scientifically reviewed.
- **15,023 distinct source SHA256s** matched result signatures. These are discovery candidates, not unique warranted scientific results.
- **15 source blobs exceeded2 MB** and were explicitly skipped. Extensions and limits are frozen in `enumerate_sources.py` and `SOURCE_SCAN.json`.
- All API-enumerated branch/tag commit ids in the 16 scanned repositories occur in their scanned reachable commit sets. Exact reconciliation is in `REF_COVERAGE_RECONCILIATION.json`.
- Ten additional repositories received default-tree enumeration and **32** limited default-source inspections. Their other historical content remains uncovered.
- **16 distinct additional experiment families** absent from the previous 42-row index were inspected and source-pinned. **36 exact historical run records**, jobs and artifact metadata were queried. This scanner downloaded no candidate artifact payloads and did no native scientific replay.

## Repository coverage

| Repository | Historical source blobs searched | Branches | Tags | Runs metadata | Artifacts metadata |
|---|---:|---:|---:|---:|---:|
| `heathsanchez/equational-theories-lean-stage2` | 2052 | 83 | 1 | 3000 PARTIAL | 6622 |
| `heathsanchez/equational_theories` | Default tree/limited files only | 72 | 5 | 252 | 21 |
| `heathsanchez/FormalBook` | 727 | 34 | 0 | 0 | 0 |
| `heathsanchez/latent-coordinate-law-engine` | 83 | 1 | 0 | 0 | 0 |
| `heathsanchez/lean-kernel-arena` | 1477 | 77 | 0 | 2651 | 789 |
| `heathsanchez/lean4lean` | 885 | 3 | 0 | 0 | 0 |
| `heathsanchez/lima` | Default tree/limited files only | 5 | 0 | 0 | 0 |
| `heathsanchez/mathgraph` | 4586 | 59 | 0 | 637 | 21 |
| `heathsanchez/mathgraph-fork` | 2021 | 4 | 0 | 152 | 286 |
| `heathsanchez/mathgraph-igp24-continuation-engine` | 102 | 1 | 0 | 0 | 0 |
| `heathsanchez/Minimal-Sufficient-Interface` | 3065 | 340 | 1 | 1900 PARTIAL | 1616 |
| `heathsanchez/OpenGauss` | Default tree/limited files only | 1 | 0 | 0 | 0 |
| `heathsanchez/parameter-golf` | Default tree/limited files only | 1 | 0 | 0 | 0 |
| `heathsanchez/QuantumOptics.jl` | Default tree/limited files only | 12 | 63 | 0 | 0 |
| `heathsanchez/realitygraph` | 1284 | 163 | 0 | 1131 | 490 |
| `heathsanchez/specimen` | Default tree/limited files only | 134 | 10 | 903 | 413 |
| `heathsanchez/test` | 10957 | 1962 | 0 | 5500 PARTIAL | 11937 |
| `heathsanchez/triskelion` | 1537 | 239 | 0 | 887 | 956 |
| `heathsanchez/vericoding-benchmark` | 7879 | 2 | 0 | 0 | 0 |
| `metalogiclabs/mathgraph-lean-kernel` | 2276 | 613 | 0 | 8200 PARTIAL | 2719 |
| `metalogiclabs/go-ethereum` | Default tree/limited files only | 75 | 0 | 261 | 110 |
| `metalogiclabs/L4YAML` | Default tree/limited files only | 3 | 0 | 4 | 0 |
| `metalogiclabs/mathgraph` | 65 | 479 | 2 | 13519 | 3654 |
| `metalogiclabs/metatron` | 638 | 67 | 0 | 400 | 541 |
| `metalogiclabs/PropertyKindCalculus` | Default tree/limited files only | 7 | 0 | 37 | 0 |
| `metalogiclabs/Stockfish` | Default tree/limited files only | 6 | 0 | 1 | 1 |

## Inaccessible sources and open boundaries

- `repos/metalogiclabs/mathgraph-lean-kernel/actions/runs?per_page=100&page=83`: gh: HTTP 503; observed `2026-10-15T08:19:48.752079+00:00`. No credential replacement or proxy bypass was attempted.
- `repos/heathsanchez/test/actions/runs?per_page=100&page=56`: gh: HTTP 503; observed `2026-10-15T08:19:07.632126+00:00`. No credential replacement or proxy bypass was attempted.
- `repos/heathsanchez/equational-theories-lean-stage2/actions/runs?per_page=100&page=31`: gh: Bad credentials (HTTP 401); observed `2026-10-15T08:17:09.386537+00:00`. No credential replacement or proxy bypass was attempted.
- `repos/heathsanchez/Minimal-Sufficient-Interface/actions/runs?per_page=100&page=20`: gh: Bad credentials (HTTP 401); observed `2026-10-15T08:17:09.227622+00:00`. No credential replacement or proxy bypass was attempted.

Private/deleted/unlisted repositories not returned to the configured identity are outside this frozen accessible universe. Full historical content for the ten default-tree-only repositories, source files outside the declared extensions, oversize blobs, inaccessible run-history pages, external storage and unprovided artifacts remain unclosed. Notion and paper coverage is recorded separately by the ROS recovery worker; inspection of those documents must never be inferred from GitHub coverage.

## Additional consequential families

| Family | Original scientific source | Historical record boundary |
|---|---|---|
| `verified-experiment-language-genesis-v1` | `795756a752a2d4857ef7f5ff5884920dc3c1432b` | Source+committed authority/results; run `34670317510`, job `103490329298`, artifact `10290558060`; payload not inspected by scanner |
| `verified-experiment-meta-substrate-genesis-v1` | `b1c56bc2ec4c1defed7060f8dfff81fdc6ae12f3` | Source+committed authority/results; run `34682784242`, job `103524385216`, artifact `10293399981`; payload not inspected by scanner |
| `verified-prospective-repair-selection-v1` | `6031466188046f56b4660d772d13ad731ed4c0f2` | Source+committed authority/results; run `34681030732`, job `103519580868`, artifact `10293778953`; payload not inspected by scanner |
| `verified-value-evidence-separator-genesis-v1` | `74a44981a766da23df87780496191014fcd41215` | Source+committed authority/results; run `34668270318`, job `103484544719`, artifact `10289800538`; payload not inspected by scanner |
| `verified-retention-policy-genesis-v1` | `f00bccabee25319bc0cc41ac9918c1d3a08108ad` | Source+committed authority/results; run `34648832202`, job `103425973195`, artifact `10282562232`; payload not inspected by scanner |
| `verified-semantic-certificate-causality-v1` | `2b8fd76354235c32b47a19b6bcac030a8cdbe1d7` | Source+committed authority/results; run `34606511715`, job `103286139441`, artifact `10266557272`; payload not inspected by scanner |
| `verified-cross-representation-compounding-v1` | `3a9a1e15be87063b52a11ae3fe234a7749062cc4` | Source+committed authority/results; run `34603467525`, job `103276154365`, artifact `10265436536`; payload not inspected by scanner |
| `verified-representation-genesis-v1` | `9e6ba7cac5eeb965e1e882ebe038424a87a69ea0` | Source+committed authority/results; run `34591859113`, job `103238734560`, artifact `10195947331`; payload not inspected by scanner |
| `verified-autonomous-adapter-genesis-v1` | `62d37a3bba2489fa82c10b8471dca637133c1a38` | Source+committed authority/results; run `34605772751`, job `103283707689`, artifact `10266545835`; payload not inspected by scanner |
| `emergent-persistence-geometry-v1` | `5ca51363d6559b8f9aef397579eb22695c5f58ed` | Source+committed authority/results; run `34641360659`, job `103401566856`, artifact `10280930082`; payload not inspected by scanner |
| `emergent-persistence-hierarchy-v1` | `5941cb3a00bc6d39b429c19885219c3b0e89048b` | Source+committed authority/results; run `34634249023`, job `103378179020`, artifact `10277547998`; payload not inspected by scanner |
| `verified-cross-domain-invariant-transfer-v1` | `1110cbcffbe23006707f5989451474bd8f0f697a` | Source+committed authority/results; run `34608265384`, job `103291984426`, artifact `10267845000`; payload not inspected by scanner |
| `verified-developmental-compounding-v1` | `67837d0154df1a9f75975d3ac735ce33392269d7` | Source+committed authority/results; run `34562463842`, job `103147825327`, artifact `10184798856`; payload not inspected by scanner |
| `verified-developmental-constructor-genesis-v1` | `3288a448071ebe60f55976a9b67149b8c370ae44` | Source+committed authority/results; run `34599025109`, job `103261533398`, artifact `10263413098`; payload not inspected by scanner |
| `verified-expressive-development-v1` | `213e932fcf11873dae7a037f7615cbcb0d3b980e` | Source+committed authority/results; run `34589130145`, job `103230116636`, artifact `10194868088`; payload not inspected by scanner |
| `verified-generator-construction-v1` | `bc20f766f84cbcf112d7d7cf6a27f87ffae7200d` | Source+committed authority/results; run `34590333207`, job `103233917529`, artifact `10195353862`; payload not inspected by scanner |

All 16 original entrypoints are byte-identical between the original scientific commit and later documentary branch head; `SCIENTIFIC_SOURCE_RECONCILIATION.json` checks entrypoints only. Dependency closure or full runtime equivalence is not inferred. `INDEX_ADDITIONS.json` keeps installed=false at baseb8216cf and CANDIDATE separate from original documentary verdicts. The canonical merger may promote only with additional independent evidence.

## Negative and superseded evidence retained

- Retention-policy genesis is NEGATIVE/PARTIAL for superiority to the supplied geometry policy:104887 versus102558 charged reconstruction cost. Bounded policy construction/revision is a separate reusable result. Its earlier green hash-seed-dependent runs remain obsolete.
- Expressive-development lineage retains the invalid false green whose Lean import failure was masked by missing pipefail, plus subsequent elaboration failures. Generator/representation/adapter/semantic-certificate failures remain source-linked.
- Developmental-compounding accounting correction is linked to its superseded run without asserting that an unchanged scientific algorithm was newly discovered.
- Experiment-meta-substrate source really enumerates stateless observations and synthesizes a finite Moore separator, but original passive/selected future costs are literal constants. They are not measured native integrated-future execution.
- Current Go/SemVer, VDN V23–V26, IKKF routing and strong-ledger ties remain in the previous canonical index and negative records; this scanner did not rerun them.

## Deduplication, dependency and equivalence discipline

Repository ids, commit ids and source SHA256s are deduplicated independently. Shared bytes establish source identity only. Matching names, final closure sizes or primitive vocabulary never establish protected-behaviour equivalence. `CAPABILITY_RELATION_GRAPH.json` contains documented source-base/supersession relations and explicit UNKNOWN behavioural-equivalence obligations; it is not a new runtime causal authority. Actual runtime dependency admissions require their existing independent verifiers.

## Reproduction and retained evidence

```bash
python research/unified_consequence_runtime/archaeology/programme-closure/enumerate_sources.py freeze --max-run-pages 200
python research/unified_consequence_runtime/archaeology/programme-closure/enumerate_sources.py scan --repos-root /workspace/repos
python research/unified_consequence_runtime/archaeology/programme-closure/enumerate_sources.py default-trees
```

The freeze uses configured `gh api`, paginates100 rows, caches exact returned pages with SHA256, deduplicates repository identity, checkpoints each endpoint/repository, and preserves failed requests. Source scanning reads Git objects without checking out or changing upstream code. Repeating the scanner is research recovery, not scientific experiment replay.

Raw API pages, repo inventories, inspected-source snapshots and historical signature outputs are gitignored to avoid duplicating megabytes of evidence in source control. `RAW_EVIDENCE_MANIFEST.json` identifies the retained local archive; `RAW_FILE_MANIFEST.json.gz` supplies every raw file digest. This scanner did not upload that local archive externally. Compact summaries, exact source pins, manifests and the resumable enumerator are committed deliverables.

**Scientific-result recovery is not exhaustive.** Metadata coverage is fully stated above; semantic review and independent verification of every consequential result in the 15,023 signature-matching source objects remains an open obligation. No count of keyword matches is presented as complete programme closure.

A later canonical reconciliation phase independently reopened and hash-checked **15 unique original archives**, recorded in `PRIMARY_RECONCILIATION.json`. The scanner’s earlier zero-payload count is a phase-specific snapshot, not a statement that no worker inspected the original archives. No historical scientific experiment was rerun in either recovery phase.
