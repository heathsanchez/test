# Native authority v4: preparation for a later distinct frontier

Status: **SOURCE ARCHAEOLOGY AND PRE-OUTCOME DESIGN ONLY**. Reviewed against base
`95029db0d0b2122836bee7268299461bfbdb5a66` on 2026-10-16. This note names no new
repository universe or task. No fresh metadata query, target checkout, target
source/test inspection, admission screening, candidate search or native execution
was performed to prepare it. Existing v3 records and source are historical inputs,
not a frontier that can be made untouched again.

The next distinct frontier may be selected and frozen **only after independently
qualified v4 admission evidence binds the final exact v4 implementation**. This
document is neither that admission gate nor an executable v4 controller. The
v4 module and record names below describe required adapter seams, not APIs claimed
to exist at the reviewed base.

## 1. Reuse the existing mechanism and preserve its authority boundary

The current mechanism is already concrete: `qualify_native_frontier_v3.py`
provisions a source-selected environment; obtains a complete original native
collection certificate; probes an unrepaired baseline; generates candidates with
original V104; runs all original MSI orders; independently reconstructs profiles;
admits an original MSI/MDA policy; and opens the protected future only after that
policy is fixed. Its `isolated_binding()` reuses exact v2 function bytecode in a
private namespace. This is the small existing reuse seam.

The retained source pins are:

| Operator | Exact original source | Pin / scope |
| --- | --- | --- |
| V104 candidate generator | `heathsanchez/triskelion`, `experiments/METALOGIC_V104_GENERIC_CONSTRUCTOR_SYNTHESIS.py` | Commit `426c54f7c774560e0fabe7213c5ef333b1327c71`; SHA256 `d00301852efd278be8ac22b848e0c9e56ced7c574980753b2ebc2ef0a3b7cce9`; `h`, `nodes_for_selector`, `build_expr`, `program_candidates` and original supplied selector/builder assignments are extracted by `qualify_recursive_frontier.original_candidates`. |
| MSI ranking language | `heathsanchez/Minimal-Sufficient-Interface`, `experiments/policy_language_genesis_cross_domain_v10.py` | Commit `56cfd7b523e3592cae4eafa5468f437ccb94dbe9`; SHA256 `836b8f677f1f252fccad8bf1136f9a966a1f2b2330fa5057c616ee20ddb56608`; `decisive_native.policy_language` extracts only `policy_programs` and `pkey`. All 36 original policies and `COLD_V104_ORDER` remain in the carrier. |
| Prospective Pareto choice | `heathsanchez/test`, `experiments/verified_prospective_repair_selection_v1/run.py` | Commit `6031466188046f56b4660d772d13ad731ed4c0f2`; SHA256 `ef46969e2182a5ced64e3c80f5266c03f864d72dcd8133539e6b1a71c42a4b94`; only original `dominates` and `choose` are extracted by `developmental_choice`. |
| MSI repair and version space | `consequential_core.py`, `consequential_version_space.py` in the original MSI repo | Commit `5d448c0ecc82ff3945d009963064ebbb67d2f308`; SHA256 respectively `2c8be1f9fde571bfcdba6d1daf8a0e680a9636f697687fd4c128a8b214975ad8` and `1494620801a524fce54ae9b87a55ae12b79094875084e883fe2183c044e181f9`. Used through `native_meta_decision` and `consequence_selection.native_selectors`. |
| MDA assessment / repair / attachment | `heathsanchez/test`, `open_development/runtime.py` | Commit `13325089c471996b8b68f46540fd4ad449df752c`; SHA256 `48bc8efdbb289697c41d633773208dcbdb53bf39dbc8679127e58d0ed3e80703`; the existing Machine projects its one ledger into original `Developer`. |
| JPL finite observation basis | `heathsanchez/test`, `research/mathgraph_minimal_quotient/h11_quotient.py` | Commit `52eb1e7995bd877a2b698efe1883ae2b80a03737`; SHA256 `f9c5146748c324bc951b076b0db30d1a3e947eacc0d9095492d4a12e983d1f1a`; only `minimal_basis` is extracted, without executing the old h11 experiment. |

The native feature interpretation is the **already supplied** adapter in
`decisive_native.catalog`: `K` is distance from changed lines to the retained native
trace, `c` is at least one changed line, and `v` is changed-line variance. It does
not inherit the original scalar/orbital scientific meaning. Keep this meaning,
file ordering, candidate IDs, original generator order, cap 64 per production
file, MSI ordering and tie behavior unchanged when rebinding v4 admission.

Stronger pre-existing operators are recorded in
`archaeology/decisive-native/ORIGINAL_MECHANISM_RECOVERY.json`: V104's optional
allowed selector/builder support and its historical support-retention heuristic;
MSI V10's 12 statistic ASTs; V11 consequence-separated observation selection;
V12 recursive generated observation promotion; and V99 source-distinct probe
components/medoids. Their existence does not mean this driver runs them. V104
support scoring and V99 probe scoring still need a separately frozen generic
native semantics; the historical mains use supplied task worlds. The current
G2 path uses a supplied grammar and selects an existing ranking policy. Adding
statistics, learned constructor support or recursive observation promotion would
change the experimental scope and is not needed for this thin v4 binding.

## 2. The minimal v4 adapter seams

Add new versioned source/records only; preserve **every existing tracked byte**
from the reviewed base, including all v3 implementations, workflows, protocols,
logs, failed attempts and sealed evidence. Retain the earlier baseline-preservation
checks as well. No second ledger, registry, capability store or agent architecture
is required.

| Seam in the present implementation | Required v4 binding |
| --- | --- |
| `qualify_native_frontier_v3._guard`, `protocol`, `require_environment_gate`, `ENVIRONMENT_GATE_FILES` | A v4-owned exact-source guard and admission-gate validator, binding the final qualified v4 worker, AST/inventory/admission policy, environment bridge, bootstrap, catalog, protocol, workflow, result and archived provider evidence. An admission-only result leaves G2–G6 UNKNOWN. A v3 PASS is not a v4 gate. |
| v3 `isolated_binding()` and its wrappers for `native_probe`, `checked_record`, `bounded_catalog`, `search`, `reconstruct_profiles`, budgets and observation extraction | Preserve original algorithm bytecode and policy semantics; use a v4-owned private namespace with the v4 worker, paths, protocol, guards and accounting functions. Resolve every internal call through the intended v4 binding. Replacing a module attribute alone does not replace the globals already held by cloned functions. |
| v3 `_prepare()` | It has a local `from .native_runtime_v3 import NativeRuntimeV3`. It must explicitly instantiate the v4 runtime; changing `qualifier.worker` cannot change this local import. Preserve collection, independent recollection, baseline, prepared-parent and source-release obligations. |
| `native_runtime_v3`'s `_runtime_globals` and inherited v2 methods | A v4 runtime binds **both** the v4 verifier and v4 admission/AST authority, its own `__file__`, source descriptor hashes, checked source guard and explicit runtime version. Preserve Machine/CAS/Metatron/FLASH events and causal liveness. v3's namespace still contains `admission=native_admission_v2`; changing only `verifier` leaves stale AST identity in constructor/scope checks. The v2 `__class__` closures and `super()` path need explicit inspection when reusing methods. |
| v3 source freeze/check, CLI parent validation and source-release records | New paths/schemas must bind the actual v4 source file set, clean committed HEAD, complete historical preservation, exact qualified gate, fresh runner-local runtime inventory, screening meter and sealed manifest. Existing code hard-codes v3 source paths and schemas. Preserve typed `screen`, `catalog`, `agent` authorities and externally supplied expected hashes. |
| `native_meta_decision._checker_source` and `invoke_meta_policy` | Keep unchanged. Supply a genuine top-level importable v4 `reconstruct_profiles` entrypoint. The imported module attribute must be that function and `inspect.getsourcefile(function)` must equal the module's own file. A copied function with old `co_filename` or an edited registry entry is insufficient. |
| v3 curator `query()` and `prepare_records.py` | New wrappers bind the v4 gate/controller and new immutable v4 record paths; both currently import v3 directly. Keep the original scanner, classifications, metadata projections, commit/tree binding and record assembly semantics. Extend historical exclusions with the entire v3 frontier universe and records below. |
| `.github/workflows/udm-prospective-native-selection-v3.yml` | A distinct v4 workflow can reproduce an already committed v4 frontier with fresh canonical checkouts/runtimes and complete evidence retention. The current workflow imports qv3, binds old source and says reproduction explicitly. It does not select a new frontier or run a coding agent in CI. |

Do not implement this by mutating old module globals, a shared admission/runtime
registry, `_LOADED_*` hash fields, source pins or a worker's validity predicates.
The execution worker itself has `_controller_globals`; the runtime has
`_runtime_globals`; the qualifier has another layer of cloned v2 globals. All are
distinct bindings. Keep the original files and namespaces intact and expose new
versioned functions. Refusals must identify the actual missing binding instead of
turning a partial old authority into a v4 qualification.

## 3. Exact sequence for a later freeze

1. **Finish and qualify admission v4 first.** Freeze/commit the final generic v4
   policy and implementation against the exposed development diagnostics. Retain
   failed attempts, independent checks, exact provider run/artifact identities,
   downloaded artifact digest and member readback evidence. The independently
   audited gate must bind that final source and catalog. Do not choose or query a
   new repository while this gate is pending.
2. **Declare one new metadata universe after that gate.** In new v4 records,
   fix at most nine nonexcluded repositories in ascending full-name order,
   requested roles two (`TRAINING`, `PROTECTED_FUTURE_1`), all predicates,
   budgets and exposure rules below. This note intentionally supplies no names.
   Hash every accessible historical input and retain explicit missing-input
   records. Commit exact curator code, prepared prequery, gate wrapper and
   archived qualified result in a clean tree before any target query.
3. **Issue metadata-only queries once.** Write the prequery execution receipt
   before querying; it binds actual committed plan/code/gate bytes, source
   commit, zero earlier target queries, fixed universe and artifact SHA256.
   Keep all repository/PR negatives, API errors, coverage and elapsed costs.
   Choose the first qualifying PR per repository in returned order; preserve
   commit/tree binding failures without retargeting. Commit the complete fixed
   ordered pool before source screening. A shortfall never expands this pool.
4. **Commit screening authority before source access.** Bind exact prequery and
   pool descriptors, v4 gate and canonical output root in a typed external
   `screen` ticket. The expected ticket SHA256 comes from the parent authority.
   Create requests with exact pool index/spec/hash only after commitment. Use
   a new output root, committed controller and fresh runner-local inventory.
5. **Independently screen every pool member in order.** Baseline admission only:
   provision; collect; independently validate collection; run unrepaired native
   baseline; independently validate/reexecute it. No constructor catalog,
   candidate order, policy search or repaired production head is permitted.
   Persist pending launch before access, preserve each directory/report and all
   partial attempts, and refuse skipped indices, reset meters or crash replay.
6. **Audit sealed raw evidence; release only envelopes.** Genuine complete
   `PASS_NATIVE` and `FAIL_NATIVE` are **identically eligible**. Public status is
   `ADMITTED_NATIVE`; raw outcome sign, traces and future source remain sealed
   from the learner. The auditor checks exact source/authority/certificate/raw
   report lineage, entire ordered meter, exposure conduct and every cost. Extra
   audit native runs are predeclared and charged. The assembler must consume an
   actual audit, never manufacture one.
7. **Choose exactly the first two source-distinct admissions.** Use the existing
   equality rule and fixed pool order. Retain every screened case. A passing
   training baseline is not replaced: the later G2 run stops
   `UNKNOWN_NO_TRAINING_NATIVE_RESIDUAL`. Insufficient eligible sources ends this
   pool; do not turn the v3 pool into a fresh retry.
8. **Freeze the committed frontier before learner source release.** Final
   protocol state is `READY_TO_FREEZE_NO_LEARNER_SOURCE_ACCESS`; bind metadata,
   sealed screening manifest, actual independent audit, complete meter, gate,
   exact source-file set and fresh runtime inventory. Freeze stays outside the
   worktree. Check that all prior bytes are preserved and every working byte
   equals committed HEAD. Prepare the independent actual agent consumer before
   execution; do not delay it until outcomes are available.
9. **Execute once under the preserved policy.** Release training; reconstruct
   all original profiles; require a unique original policy; only then release
   the protected future and its source-bound catalog. Preserve all stops and
   UNKNOWN results. Reproductions may check committed evidence but never restore
   untouchedness or create a second first run.

Metadata policy retained from the current curator: latest at most 100 closed PRs
per repository (`page=1`, `per_page=100`, `sort=updated`, descending); merged;
case-insensitive title starts `fix` or a label contains `bug`; at least one
production `.py` and one test `.py`; production deletions inclusive 1–4;
production additions at most six; all production `.py` changes are `modified`;
no changed file renamed or removed. Use the original test classifier and file
pagination through closure, rejecting an unclosed 3000-file ceiling. Only projected
PR/file metadata and Git commit/tree metadata may cross the process boundary.
No contents/blob/raw endpoint, patch, body, CI result or commit-message output;
no clone/fetch or native execution in this phase. Metadata ceiling is 900 seconds.

Screening ceiling retained: at most nine cases; at most two native executions
per case including independent verification; collection 60 seconds per call;
native execution 600 seconds per call; 7200 seconds for the ordered interval.
Retain collection attempts separately, including initial collection, independent
recollection and the recollection performed by native verify/reverify. A complete
ordinary case can therefore contain two native and four collection launches;
collections are not free or mislabeled native calls. Missing exact attempt
accounting, malformed reports, budget overrun or environment ambiguity cannot
become an admission.

## 4. Costs and comparator commitments

Preserve search budget eight per episode, catalog cap 64 per production file,
catalog horizon 45 seconds, training unique-producer ceiling 128, reserve 64
future native calls, and aggregate acquisition ceilings **512 native calls and
3600 wall seconds independently per arm**. Per-search time does not override
the aggregate deadline. The collection/execution limits remain 60/600 seconds.

Charge unrepaired baselines, common preparation and learning, failed prefixes,
every native producer and independent reexecution, profile reconstruction,
policy admission/revalidation, actual informed-training-ledger run, future cold,
warm and informed-ledger runs, operation deletion/rematerialization, final native
admit twice and execute once, and agent native verification. Native collections,
metadata, environment/package/bootstrap subprocesses, pure catalog regeneration,
Machine initialization, model deliberation, tools, tokens, engineering and total
lifecycle time must be retained in their appropriate cost records. The present
driver meters native/collection worker launches and wall time; it does not
automatically measure every model/tool/engineering cost. Unmeasured costs stay
UNKNOWN, never zero. Nested inclusive wall times and envelope costs are not
summed again as independent work.

Screening costs are the entire fixed pool, retained separately from acquisition
arms and included in any total-lifecycle report. Each matched arm starts with
the same common acquisition history and native cost, including learning and
baseline verification. The informed ledger receives the same original grammar,
all original orders, admissible source/native observations/history and selected
order; it may tie the warm arm. That tie prevents a superiority claim.

The actual coding-agent arm has its own immutable parent/authority, catalog
membership check, locked persistent meter, at most eight actual proposals, and
the same 512-call/3600-second total including common learning and independent
checks. Its clock starts at publication and includes common elapsed acquisition
time plus later deliberation. Do not reset or republish after seeing outcomes.
Preserve actual prompt/transcript, model identity, release/proposal timestamps,
token/tool/native costs, failed launches and evidence. A prepared arm, simulated
transcript or replay of another arm's winner remains `PENDING_ACTUAL_EXECUTION`.

## 5. Concrete supported claim and stops

The current driver's strongest positive G2 endpoint is
`WARRANTED_BOUNDED_PROSPECTIVE_NATIVE_POLICY_SELECTION`, not a larger-language or
comparative claim. It requires all of the following actual evidence: failed
training native baseline; complete original-policy profiles and a unique
original choice; fixed policy before future release; authentic complete cold
failure for the future prefix of eight; selected warm success within eight with
the retained policy dependency; independent fresh receipt checks; actual physical
deletion of the policy program in cloned state followed by source-identical
rematerialization and cold-eight failure; and fresh native admission plus
execution success, with original ledger prefix retained and all costs in budget.

Native PASS at training/future baseline, policy ties, absent residuals, incomplete
episodes, setup/import/collection errors, missing accounting and exhausted
budgets remain the exact appropriate UNKNOWN stop. In particular, screening
eligibility does not promise a failing residual, a unique policy or reachable
repair. No post-outcome change to grammar, scoring, task, role, test suite,
environment catalog or budget is an allowed repair of the first experiment.

G3 constructor growth, second generation, withdrawal/restoration and cold restart
are not implemented by this policy-order experiment. Deleting an acquired policy
for its G2 control does not establish all those claims. G4 remains UNKNOWN without
the independently assessed actual matched-agent and lifecycle comparison; the
current CI explicitly runs no coding agent. Formal Python refinement and
non-bypassable external-effect containment remain unqualified (G5/G6 UNKNOWN).

## 6. Full historical exclusion review

The current v3 curator's original scanner consumes these 21 historical inputs:
`capability_index.json`, `sources.json`, `developmental_sources.json`,
`native_policy.json`; decisive-native `FRESH_TASK_METADATA.json`,
`CODING_AGENT_FREEZE.json`, `QUALIFICATION_FREEZE.json`, `PROTOCOL.json`,
`AUTHOR_TEST_BLOBS.json`; v54-continuation `PROSPECTIVE_FRONTIER_FROZEN.json`,
`SOURCE_MANIFEST.json`; recursive-frontier `GREEN_MAINTENANCE_FREEZE.json`;
programme-closure `REPOSITORIES.json`, `FROZEN_UNIVERSE.json`,
`DISCOVERED_CANDIDATES.json`, `CROSS_FRONTIER_SOURCE_INDEX.json`; external_pr_v1
`FROZEN_PROTOCOL.json`, `admission_policy.json`; native_semantic_genesis_v1,
native_unbounded_v1 and typed_semantic_method_v1 `FROZEN_PROTOCOL.json`.
It adds native-frontier-v2 `PREQUERY.json` and `FRESH_TASK_METADATA.json`, plus
the explicit `go-chi/chi` native-domain exclusion. At the reviewed base this
reconstructs 53 conservative identifiers. None of these inputs was missing.

For v4, add the **entire** nine-repository v3 universe, including queried
repositories that never produced a selected/admitted case. Bind at least the
following exact additional metadata records and review any later exposure
record before the new prequery commit:

| Historical v3 record (under `archaeology/native-environment-v3/`) | SHA256 at reviewed base |
| --- | --- |
| `PREQUERY.json` | `5c7e141f6b8915b48bf0f64d662ac443f41c9791190441c3ffc5b8ade8d5a718` |
| `PREQUERY_EXECUTION.json` | `dd9851f7d81a0ccba31fc715af050f5a372a7d80bab86703ec6e2f78682c21e8` |
| `METADATA_CURATION.json` | `8da692cc958a6db81f9b9bdd1e25a10af56587be81cb65332a862177eb698837` |
| `FROZEN_POOL.json` | `e99dbf7ed11554561f3584cbe7216cf7f847b78364ef1cac70841bec97c08bb3` |
| `SCREENING_ENVELOPES.json` | `ab2e633be00ef452456bd5efc59c29ae288057f1d2f999c5136ea67ef888aaa1` |
| `SCREENING_AUTHORITY.json` | `e91f8b231add3f4cf595e10c36359f7a5499cb2b11a61e40987f6361ed214a67` |
| `SCREENING_METER.json` | `f1984c506fdb8322938a486db03efd1470e11247cf42bcd39b8f3a6fa8365141` |
| `SCREENING_SHORTFALL.json` | `f1c07a9958bd7b2130a1f2007bbe85551091a29ebfcbb4c4d29828f8b952c111` |

The resulting conservative exclusion set is the following **62 identifiers**,
normalized to lowercase. Eight inherited scanner artifacts (`licenses/*`,
`repos/*`, `users/*`) are retained rather than silently pruned. The remaining
54 entries name repository-like historical exposures. This is an accessible
record exclusion check, not proof of universal model/human unfamiliarity.

```text
dateutil/dateutil
davidhalter/parso
go-chi/chi
grahamdumpleton/wrapt
grantjenks/python-sortedcontainers
heathsanchez/equational-theories-lean-stage2
heathsanchez/equational_theories
heathsanchez/formalbook
heathsanchez/latent-coordinate-law-engine
heathsanchez/lean-kernel-arena
heathsanchez/lean4lean
heathsanchez/lima
heathsanchez/mathgraph
heathsanchez/mathgraph-fork
heathsanchez/mathgraph-igp24-continuation-engine
heathsanchez/minimal-sufficient-interface
heathsanchez/opengauss
heathsanchez/parameter-golf
heathsanchez/quantumoptics.jl
heathsanchez/realitygraph
heathsanchez/specimen
heathsanchez/test
heathsanchez/triskelion
heathsanchez/vericoding-benchmark
jab/bidict
jd/tenacity
keleshev/schema
leanprover/cslib
licenses/apache-2.0
licenses/gpl-3.0
licenses/lgpl-3.0
licenses/mit
mahmoud/boltons
metalogiclabs/go-ethereum
metalogiclabs/l4yaml
metalogiclabs/mathgraph
metalogiclabs/mathgraph-lean-kernel
metalogiclabs/metatron
metalogiclabs/propertykindcalculus
metalogiclabs/stockfish
more-itertools/more-itertools
mverleg/pyjson_tricks
nasa-jpl/l4yaml
pallets/blinker
pallets/click
pallets/itsdangerous
pallets/markupsafe
psf/requests
pypa/packaging
python-attrs/attrs
python-attrs/cattrs
python-humanize/humanize
python-hyper/h11
repos/heathsanchez
repos/metalogiclabs
servicenow/webarena-verified
tartley/colorama
teorth/ieantn
tkem/cachetools
urllib3/urllib3
users/heathsanchez
users/metalogiclabs
```

## 7. Reviewed source receipts

These hashes identify the current machinery that this note proposes to preserve;
they do not qualify its future v4 binding.

| File, relative to `research/unified_consequence_runtime/` unless stated | SHA256 |
| --- | --- |
| `qualify_native_frontier_v3.py` | `d40d188be3565ed5127e06b033dd9cbf8fa32d60977d27ec47b5ae6698189418` |
| `qualify_native_frontier_v2.py` | `e06c148bc8fe701d703615186143f64545b26f1c338f775b87b5c0621473b9e2` |
| `native_runtime_v3.py` | `0d5c01f702fed063e11a0e4e9e011972947bf67b1c5c7c306cd7a79782e1b553` |
| `native_runtime_v2.py` | `0707f9938d74c358fd8c21f9881c18a51c4e2062a7fcc79eee48b3a8499573bb` |
| `native_execution_v3.py` | `fead622b61319dc21af1ef302a98b42203090bcc997838fc078c71ddc4ea6cd9` |
| `decisive_native.py` | `1c4143ea4f136298cca2885a5ff63d4ad83c85eeb64f2f1d1b3d7ba701e82b04` |
| `native_meta_decision.py` | `d1791b40a254d0a74dea2ec336cfb6c6893fa871b2458b16718bd37c1e8ea585` |
| `developmental_choice.py` | `47e356c5742fc7ccfdb4a0c7488faa1c314e531e2793da847ba7f27d7b20ca48` |
| `consequence_selection.py` | `e39f10c5671df25761c4e2bc18c46eccbb14dfd6180834f1befc560e13a4bcaa` |
| `archaeology/native-environment-v3/curate_frontier.py` | `44455d61c8144261e2db2ce2a6de8b6b2671d9ca504353e03bb9dcd487fa3c14` |
| `archaeology/native-environment-v3/prepare_records.py` | `7ab47d2339641a09d5ab2c6e417ed148298477e83bf19f8580b56a9655c6ce5a` |
| `archaeology/native-environment-v3/PROSPECTIVE_RUNBOOK.md` | `382407bce0b749af36451ad63ac0c89875ad26f0308bcb81d4a3beeadcd26e11` |
| repository `.github/workflows/udm-prospective-native-selection-v3.yml` | `f459863bbbc905f9f820603f41609509f0dd3da5f3d2aeed6d05b8fefbc15b4d` |
