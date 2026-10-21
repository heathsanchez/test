# UDM V2 historical full-native qualification, 2026-10-21

VERDICT: WARRANTED_BOUNDED_SOURCE_ADMISSION_PROGRESS; G2–G6 UNKNOWN.

Candidate on isolated draft PR #153, original historical UDM reference 15e71683a19394fb00b5833c18a3e876c2645d54. The original signed/source-qualified V1 evidence remains bound to its old source bytes; V2 does not retroactively replace prior verifier authority.

- Full diagnostic [run #39573282754](https://github.com/heathsanchez/test/actions/runs/39573282754): SUCCESS, 116/116 protected contracts, artifact #12332689535, ZIP SHA256 dfeeb636d0d1efbf64ce94c6fec4b2aab9ac882286469b4de17dded4fa05fafb.
- Independent full [run #39573327378](https://github.com/heathsanchez/test/actions/runs/39573327378): SUCCESS, 116/116 protected contracts, artifact #12333176309, ZIP SHA256 2fd072ec0278f1aa581632544e3d5d7200cd75804ec07e9a957becfa33bdd682.
- Inspected original archived NATIVE_EVIDENCE.tar.gz / decisive/RESULT.json and three exact admission.json files from both full archives, not just CI badges.

Current machine status: UNKNOWN_NO_NATIVE_ACQUISITION_RESIDUAL. G0_G1=PRESERVED_EXACT_PRIOR_SOURCE_AUTHORITY; G2=G3=G4=G5=G6=UNKNOWN.

Frozen historical task outcomes:
1. more-itertools PR #1309: authentic tests/test_more.py blob b3a9351595a6fd7f1aa9c1e35978f08106e43df0, source admission PREPARED, native UNKNOWN_TIMEOUT at frozen 7-second horizon.
2. python-attrs/attrs PR #1513: authentic tests/test_validators.py blob 5ad2308eb89e6dfa8b0f6362969775b69c692fd6, admission PREPARED, native UNKNOWN_TIMEOUT at same frozen horizon.
3. python-attrs/cattrs PR #723: authentic tests/test_tuples.py blob c1a9562c3c25ae8e1002aeca00a1ffe34cd2bd24, admission UNKNOWN_CONTRACT because original pyproject declares pytest-benchmark plugin flags --benchmark-sort, --benchmark-warmup, --benchmark-warmup-iterations, and --benchmark-group-by; plugin source and authority not admitted by the no-autoload native verifier.

Additional authentic test-file diagnostic [CI 39573043195](https://github.com/heathsanchez/test/actions/runs/39573043195) checked exact author Git blob identities and statically parsed 616, 101 and 7 test nodes. Artifact #12332872260 SHA256 a666f0a0c04e8f15d15179ef659c6cbdfa362539d34ab04f392dd02c408696c5.

Candidate scope: recognizes specific --import-mode values, -l, and statically literal test-prefixed test data; refuses dynamic registration, unknown options and unsafe paths. No original frozen negative result is upgraded to prospective success. No new O1/O2, source-native capability genesis, causal continuation gain, fully charged advantage or production authority was established.

Next admissible gate: independently qualify a versioned source-authorized pytest suite authority including audited benchmark-plugin identity and realistic fixed complete-suite execution horizon before opening a newly frozen source-distinct trial. Preserve old history. Source-admission/verification and total acquisition/integration costs must be charged to both equally informed arms.
