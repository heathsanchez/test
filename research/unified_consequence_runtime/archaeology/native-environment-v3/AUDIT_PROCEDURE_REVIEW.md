# Prospective admission-only screening audit procedure

Design review only, 2026-10-16. No fresh task metadata, task source, curation output, screening cases, or remote services were accessed. No worker was run. This procedure is for a separately authorized independent auditor after **every fixed pool member** has completed or refused. Keep all raw evidence sealed from the learner; release only admission envelopes and the audit verdict.

Reviewed contracts: `native_execution_v3.py`, `native_environment_v3.py`, `qualify_native_frontier_v3.py` and the pinned generic predecessor/controller definitions that v3 binds. References below are repository-relative under `research/unified_consequence_runtime/`.

## 1. Establish exact authority before inspecting cases

Verify external descriptors using raw-byte SHA256, canonical absolute paths, no symlinks, and exact retained bytes. Bind the prequery receipt, fixed ordered pool, screening CLI authority, environment gate, catalog, runner-local runtime inventory, committed controller sources, complete meter, case reports, and envelopes. Use SHA256 of bytes for descriptors; use `worker.fingerprint(value)` only where the contract specifies canonical JSON fingerprints.

Check the prequery/pool/authority relationships prescribed by `screening_request` (`qualify_native_frontier_v3.py:373`): exact pool member and index; authority `operation='screen'`; `request.protocol_binding=authority-descriptor.sha256`; prequery state, source commit, zero prequery task-query count, committed plan/code/gate descriptors, and exact gate/catalog linkage. Check the environment gate independently against its frozen source/artifact receipt. Do not treat self-declared `independent_screener`, no-search, or no-learner-source-access booleans as proof of process isolation; require the external run/access provenance supporting them.

Require `SCREENING_METER.json` schema `UDM_ORDERED_SCREENING_METER_V3`, the authority SHA256, source commit, and runtime-inventory fingerprint; `pending=null`; `accounting_complete=true`; one case for every pool member in fixed order, including refusals. Case index/spec fingerprint/report descriptor must match its pool member and exact sealed report. Never stop auditing after enough eligible roles exist. Independently verify the native limit 2/case, collection horizon 60 seconds/call, execution horizon 600 seconds/call, maximum cases, total screening wall budget, and first eligible repository-distinct role selection. PASS and FAIL are equally eligible.

## 2. API boundary: perform no additional native or collection execution

The safe retained-receipt entry point is:

```python
worker.validate_receipt(contract, {'replacements': []}, authority, certificate,
                        retained_receipt, policy=policy, independent=False)
```

Use it separately on producer and independent-baseline receipts. This validates retained packets, source/candidate/certificate/policy/runner binding, JUnit, status, and costs. It calls `_context`, which snapshots local Git and launches environment/plugin identity subprocesses; it creates temporary XML scratch files. It does **not** launch a native pytest collection or run. Charge/log any audit identity work separately.

**There is no public structural-only certificate validator.** `worker.validate_certificate(..., output_dir=None)` still creates a temporary directory and calls `_run(..., 'collect', ...)` (`native_execution_v2.py:299`). Do not call it. Also do not call `collect`, `verify`, `validate_receipt(independent=True)`, `_run`, provisioning, candidate search, or constructors during this audit.

The available non-pytest structural helpers are `worker._context(contract, authority, policy) -> (files, manifest, environment, plugins)`, `_binding(...)`, `_collection(data, authority, files)`, `_status(data, counts, certificate['collection'])`, `worker.original._junit(path)`, `worker.admission.validate_suite_contract(...)`, and `worker.fingerprint`/`sha256`/`canonical`. These are private, frozen implementation APIs; pin their source and mirror the existing checks explicitly where necessary. Snapshot `worker.attempt_snapshot()` immediately before/after audit structural calls and require zero deltas in `native_calls`, `collection_calls`, and `subprocess_attempts`; this counter excludes identity subprocesses.

If the original runner/environment is unavailable, `_context`/receipt validation cannot establish current executable identity from portable artifacts alone. Report that limitation; do not reconstruct an environment or rerun screening to obtain a PASS.

## 3. Exact retained successful-case layout and receipt bindings

Let `C = authority.output_root / ('case-' + format(index, '03d'))`. Require the report's `retained_raw_directory` to identify C when present. Successful screening produces:

| Relative path under C | Evidence / calls |
|---|---|
| `SCREENING_CASE.json`, `SCREENING_ENVELOPE.json` | Raw case and released envelope |
| `source-environment/{admission-v3.json,selection.json,metadata-source.tar.gz}` | Source-derived selection and independent base metadata snapshot |
| `source-environment/native/{admission.json,source-boundaries.json,native-suite-authority.json,contract.json,policy.json}` | Materialization, source/test boundary and worker inputs |
| `source-environment/native/{base-source.tar.gz,contract-source.tar.gz}` | Hashed raw Git-byte archives, not transformed checkouts |
| `source-environment/native/{environment.json,plugin-identity.json,native-wheel.json,wheels/*}` | Environment/plugin and base-wheel identity |
| `source-environment/{pinned-requirements.txt,pinned-package-files.json}` | Exact catalog artifact pins and retained pinned-file inventory |
| `collection/admission-certificate.json` and raw files in `collection/` | Initial collection, 1 collection |
| raw files in `independent-collection/` | Explicit independent certificate recollection, 1 collection |
| `baseline/receipt.json`, raw files in `baseline/independent-collection/`, `baseline/execution/` | Producer baseline, 1 collection + 1 native run |
| `independent-baseline/receipt.json`, raw files in `independent-baseline/independent-collection/`, `independent-baseline/execution/` | Independently repeated baseline, 1 collection + 1 native run |

Each completed raw worker directory contains `stdout.log`, `stderr.log`, `report.json`, `checked-report.json`, `tracked-source-manifest.json`, and normally `native.xml`. The certificate requires all six packet files; execution packets allow missing XML structurally, but an eligible PASS/FAIL must satisfy the nonempty exact-suite JUnit/status checks. Decode every embedded packet with strict base64, verify `packet_sha256`, and compare decoded bytes with their corresponding retained files.

Require report schema `UDM_ADMISSION_ONLY_CASE_V3`, repository/spec fingerprint, exact `screening_mode='ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH'`, truthful status/eligibility, and exact agreement between embedded `setup`/`certificate`/`baseline` and saved JSON. The independent baseline receipt is **not embedded** in SCREENING_CASE; audit its disk receipt explicitly. Reject evidence of candidate catalogs, orders, policies, candidate replacements, or searches. Both execution receipts must bind `fingerprint({'replacements': []})`, the same contract/authority/certificate/policy/runner, and the screening authority's protocol binding.

For an eligible case require both receipt structural checks above, equal status and JUnit, and exact equality of the two `execution` objects after removing only their top-level `costs` field, reproducing `validate_receipt`'s independent agreement rule. Do not remove node order, test code hashes, imports, plugin manifests, or controller outcome fields to force agreement. The independent receipt need not have identical timing, XML bytes, output logs, or its own receipt hash.

## 4. Collection validation without recollection

Mirror the structural portion of `validate_certificate` (`native_execution_v2.py:271–298`) using the original context and retained bytes. Require certificate fields exactly `_binding(...)` plus `status`, `collection`, `packet`, `packet_sha256`, `costs`; schema `UDM_NATIVE_ADMISSION_CERTIFICATE_V3`, revision `3.1`, `status='ADMITTED_NATIVE_COLLECTION'`; exact source/authority/policy/runner/environment/plugin binding; six-file packet digest equality; original manifest; and correct cost/collect-mode checks.

For each of the four retained collection directories, compare the producer JSON with checked JSON after removing only controller keys `process_exit_code`, `timeout`, `source_mutations`, `unexpected_imports`, `costs`. Validate original source manifests and imported bytes. Require `_collection(checked, authority, files) == certificate['collection']`. This enforces successful nonempty original collection, unique nodes, exact selected/collected membership, no deselection/errors/source/import/plugin violations, original test source hashes, and protected assertion-prefix coverage. Validate finite nonnegative times and cost tuple `(native_calls=0, collection_calls=1, horizon_seconds=60)` separately for every collection. Compare each receipt's `independent_collection.output` and `costs` to its actual retained recollection directory/report, because structural receipt validation alone does not read that output path or authenticate those cost claims.

## 5. Original source, author-test and environment boundaries

Require source-selection receipt `status='PREPARED'`, inner native setup PREPARED, exact agreement between duplicated contract/authority/policy/boundary fields, and `source_metadata_identity == source_boundaries.base_identity`. Reconstruct selection from the independent raw base archive with `environment.selection.validate_selection(base_files, catalog, setup['selection'])`; the selected profile and runner runtime inventory must agree. Require policy exactly `environment.execution_policy(profile)` with 60/600 limits.

Validate base/augmented manifests against local immutable Git snapshots and raw archives: safe unique regular paths, modes 100644/100755, SHA256, Git blob IDs, complete path sets, file counts, tree identity, and canonical manifest fingerprint. Check archive descriptor SHA256/bytes/format and `export_subst=false`; do not execute or blindly extract archive contents. `metadata-source.tar.gz` has no explicit retained digest descriptor, so recompute its contents/manifest identity rather than inventing one.

Use the frozen pool spec to identify exact author test paths. Recheck each retained `author-test-N.log` JSON using boundary `transport_json`/`transport_sha256`, endpoint repository/path/head commit, decoded base64 bytes, length, Git blob hash, and SHA256. The augmented source must equal base source overlaid with exactly those test blobs; all other paths and modes remain original. Require immutable native configuration and independently reconstruct `worker.admission.validate_suite_contract(contract, authority)`. Require `head_production_fetched=false`, `production_preserved=true`, exact base/head/augmented identities, and no repaired-head source transport in retained command provenance. SCM tag/ancestry transport, when present, must satisfy the retained base-ancestry-only provenance and unchanged source checks.

**Production-scope limitation:** complete base/augmented source preservation outside the author-test overlay is reconstructable from manifests and archives. The original requested changed-production-file list in `spec.files` is not stored in the case/setup receipt; only `spec_sha256` is retained. Reconstruct that target scope from the exact frozen pool spec and the generic test classifier (non-test `.py` paths), or mark it unavailable. Execution imports describe the loaded subset, not all production paths.

Check environment JSON fingerprint against `contract.environment_sha256`, and equal environment/plugin objects throughout certificate and both receipts. On the original runner, `_context` verifies actual executable, original stdlib bytes, installed distribution inventory digest, pytest import/version, and licensed plugin identities. `environment.validate_runtime(profile, runtime_record, interpreter=contract['interpreter'])` and `installed_package_identity(...)` can recheck original runtime/pinned files without pytest execution; compare the retained `pinned-package-files.json` fingerprint and exact `package_requirements(profile)`. Check native-wheel bytes/hash/base identity and no synthetic version. Full distribution file rows are represented by a digest, not retained wholesale in environment JSON; artifact-only review cannot recover them from that digest. Original tests/plugins remain trusted Python; receipts expressly retain `UNKNOWN_NONBYPASSABILITY`.

## 6. Reconcile complete costs and refusal artifacts

Inventory every retained file and hash it into a sealed audit manifest, including all setup/transport/install/build logs, wheels, archives, partial reports, malformed outputs, refusal reasons, and failure-time pip freeze. Do not delete or replace failed cases. Recursively compare every actual `checked-report.json` with `partial_native_reports` path/SHA256/valid/cost data; independently parse and type-check costs. Classify files by their actual worker path, since recursive discovery may also encounter a source/package fixture with that basename. Extra or duplicated cost-bearing paths must not silently masquerade as worker executions.

For normal eligible cases the six worker checked reports total **2 native + 4 collection = 6 launches**. SCREENING_CASE `costs` contains only baseline receipt costs and independent-baseline receipt costs (2 native + 2 collection); it omits initial collection and explicit independent recollection. Setup costs remain in `setup.costs` (including inner setup costs); duplicated nested receipts are not extra charges. Wall intervals are nested/nonadditive.

Reproduce `screening_envelope`: sum counts over all `partial_native_reports`, then take the componentwise maximum with `controller_attempts` for native and collection counts. Require envelope exact fields/schema `UDM_SEALED_ADMISSION_ENVELOPE_V3`, exact sealed report descriptor/raw SHA256, wall value and derived costs. Independently also reconcile actual worker report counts with private launch deltas and meter case costs; any recovered worker counts exceeding private deltas are an accounting discrepancy, not an authorized extra execution. Counts must be nonnegative integers (not booleans), `subprocess_attempts=native_calls+collection_calls`, each case <=2 native attempts, and aggregate meter counters must equal case private deltas. A failed Popen is charged even when no checked report exists. Missing raw evidence cannot be converted to zero calls. `accounting_complete=true` means private snapshots/deltas were valid; it does not by itself establish successful evidence or budget eligibility.

Refusals may lack a contract, certificate, final receipt, or `retained_raw_directory`, especially in the outer interrupted-screening fallback. Audit what exists at fixed C, preserve refusal status/eligible=false, account every private attempt and partial file, and identify gaps explicitly. Never require success-only artifacts to exist in a refusal; never promote it to eligible by inference from a leftover PASS/FAIL receipt. A malformed checked report must remain faithfully retained and admission-ineligible UNKNOWN; it does not by itself fail the all-pool audit when every failure, artifact, cost and exposure is retained and private launch deltas are exact. Fail the all-pool audit when complete retention, cost provenance/accounting, budget compliance, or exposure boundaries cannot be established.

Native counters exclude provisioning, builds, installs, metadata fetches, identity subprocesses, audit overhead, and model/tool/engineering work. Retain their available durations/logs and identify unmeasured quantities as UNKNOWN. Current receipts do not supply an exhaustive process ledger or prove absence of unrecorded external actions. Frozen controller/run/artifact provenance and the declared cost boundary are necessary; do not claim total lifecycle cost is fully measured.

## 7. Verdict and information release

Produce a sealed detailed audit record binding every input and raw-evidence digest, per-case checks/refusals/cost discrepancies, native/collection audit delta zero, and explicit limitations. The learner-facing audit must bind `pool_sha256`, `reports_sha256=worker.fingerprint(ordered_envelopes)`, `eligibility_rule='PASS_NATIVE_OR_FAIL_NATIVE_IDENTICAL'`, and `all_screened_cases_and_costs_retained=true`; set `status='PASS_ADMISSION_ONLY_SCREENING_AUDIT'` only when the declared independent boundary, all-case retention, bindings, evidence checks, and accounting checks pass. Eligibility may still be false for faithfully retained UNKNOWN/refusal cases. Release no source, native PASS-versus-FAIL observations, traces, catalog/search information, or detailed future-case audit evidence through the envelope.

Hashes and structural agreement demonstrate consistency with committed trusted-controller evidence; they are not independent execution attestations by themselves. The retained second run is the screening-time independent execution. This audit must not spend a third native run to compensate for missing provenance.
