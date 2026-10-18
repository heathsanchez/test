# Prospective v3 controller: actual CLI runbook

This is an operator runbook, not a record of an executed frontier. No fresh metadata query, source fetch, screening or G2 run was performed while preparing it. The current controller is prepared only; the next independently qualified environment artifact must bind the final exact environment/bootstrap source before the query stage below. No prior frontier or environment protocol is modified.

The external record assembler alongside this file, `prepare_records.py`, performs local JSON assembly only. Its actual API has three subcommands: `prepare-screening`, `write-requests`, and `finalize-records`. It imports the real controller and uses its exact validation helpers. The independent screening audit is a required input; the assembler never creates an audit pass. `--help` was executed source-free. Full stage execution remains contingent on the qualified gate and future actual records.

## 1. Fixed paths and first environment gate

Use the same canonical prospective runner paths through screening, freeze and execution. The current controller binds canonical absolute external authority/meter paths and local interpreter identities; copying an arm to another host is not an executable portability claim.

```bash
cd /workspace/udm-v54
export PYTHONPATH=/workspace/udm-v54
export V3_RECORDS=research/unified_consequence_runtime/archaeology/native-environment-v3
export V3_ASSEMBLER=research/unified_consequence_runtime/archaeology/native-environment-v3/prepare_records.py
export V3_CURATION=/workspace/qualification/native-frontier-v3-curation
export V3_SCREEN_ROOT=/workspace/qualification/native-frontier-v3-independent-screening
export V3_REQUESTS=/workspace/qualification/native-frontier-v3-screen-requests
export V3_RUNTIME_PATHS=/workspace/qualification/env-selection-v3-runtime/LOCAL_RUNTIME_PATHS.json
export V3_FREEZE=/workspace/qualification/native-frontier-v3-FREEZE.json
export V3_RUN=/workspace/qualification/native-frontier-v3-prospective-run
```

`ENVIRONMENT_GATE.json` must be the independently checked, committed wrapper with **exactly** two keys:

```json
{
  "environment_gate": {
    "status": "ADMISSION_ONLY_QUALIFIED",
    "source_commit": "<40 hex qualified environment commit>",
    "run_id": 123,
    "artifact_id": 456,
    "artifact_sha256": "<64 hex downloaded artifact ZIP>",
    "qualification_result_sha256": "<64 hex exact archived RESULT.json bytes>",
    "result_path": "research/unified_consequence_runtime/archaeology/native-environment-v3/<new archived RESULT.json>"
  },
  "catalog": {
    "path": "research/unified_consequence_runtime/archaeology/native-environment-v3/ENVIRONMENT_CATALOG.json",
    "sha256": "<64 hex exact catalog bytes>"
  }
}
```

The downloaded artifact and archived result are real independently obtained evidence, not locally asserted fields. `require_environment_gate(wrapper)` checks actual qualifier/workflow names, exact bridge source, catalog, configuration and bootstrap source including `stdlib_cache.py`. It does not reuse the gate runner's absolute interpreter paths. Validate the real wrapper before any metadata query:

```bash
python -B - <<'PY'
import json
from research.unified_consequence_runtime import qualify_native_frontier_v3 as q
wrapper = json.loads((q.RECORDS/'ENVIRONMENT_GATE.json').read_text())
print(q.canonical(q.require_environment_gate(wrapper)))
PY
```

Create the fresh prospective runner runtime map using the **qualified** bootstrap before task source access. The map has every exact catalog profile ID and fresh absolute interpreter path. Current local paths are:

```json
{
  "cpython-3.12.14-pytest-8.4.1-linux-x86_64": "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python",
  "cpython-3.6.5-pytest-5.4.3-linux-x86_64": "/workspace/qualification/env-selection-v3-runtime/venv/bin/python"
}
```

This source-free CLI binds and validates both real runtime identities:

```bash
python -B -m research.unified_consequence_runtime.qualify_native_frontier_v3 \
  --write-runtime-inventory --catalog "$V3_RECORDS/ENVIRONMENT_CATALOG.json" \
  --runtimes "$V3_RUNTIME_PATHS" \
  --out /workspace/qualification/native-frontier-v3-RUNTIME_INVENTORY.json
```

This exact CLI was exercised previously against the local map; retained evidence is `ACTUAL_RUNTIME_INVENTORY.json` and `ACTUAL_RUNTIME_INVENTORY_CLI.log` beside this runbook. Recreate the inventory for the actual prospective run; an old smoke-test inventory is not admission evidence.

## 2. Commit prequery, then run only the fixed metadata curator

The curator file is `research/unified_consequence_runtime/archaeology/native-environment-v3/curate_frontier.py`. It is independently prepared by the metadata curator agent. Its actual CLI is:

```bash
python "$V3_RECORDS/curate_frontier.py" \
  --write-prequery "$V3_RECORDS/PREQUERY.json"
```

Root commits the final controller/environment/curator code, exact `PREQUERY.json`, gate wrapper and archived qualified result. The prepared plan keeps `state=PREQUERY_PREPARED_NO_QUERIES`; do not rewrite it to claim commitment. After that clean committed prequery and independently qualified gate, the following is the first metadata-query command:

```bash
python "$V3_RECORDS/curate_frontier.py" \
  --query-after-committed-prequery "$V3_RECORDS/PREQUERY.json" \
  --environment-gate "$V3_RECORDS/ENVIRONMENT_GATE.json" \
  --qualification-artifact /ABS/PATH/independently-downloaded-gate-artifact.zip \
  --out "$V3_CURATION"
```

The output directory may be empty; the three named output files must not preexist. Outputs are exactly `PREQUERY_EXECUTION.json`, `METADATA_CURATION.json`, and `FROZEN_POOL.json`. The receipt binds the plan, raw curator code and gate wrapper bytes at the actual prequery commit, zero prior target queries, archive SHA and fixed nine-repository universe. Pool selection uses only predeclared metadata, not native outcomes. Retain all metadata negatives; do not expand the universe after a shortfall.

## 3. Build and commit the screening authority before any target source

```bash
python -B "$V3_ASSEMBLER" prepare-screening \
  --environment-gate "$V3_RECORDS/ENVIRONMENT_GATE.json" \
  --curation "$V3_CURATION" --screen-root "$V3_SCREEN_ROOT"
```

This copies exact curation bytes, writes new `FRONTIER_PROTOCOL.json` in `PREPARED_NOT_FROZEN`, and writes `SCREENING_AUTHORITY.json`:

```json
{
  "schema": "UDM_NATIVE_CLI_AUTHORITY_V3",
  "operation": "screen",
  "repo": "/workspace/udm-v54",
  "environment_gate": "<the exact seven-field object, not a string>",
  "prequery": {"path": "<repo-relative PREQUERY_EXECUTION.json>", "sha256": "<exact bytes>"},
  "pool": {"path": "<repo-relative FROZEN_POOL.json>", "sha256": "<exact bytes>"},
  "output_root": "/workspace/qualification/native-frontier-v3-independent-screening"
}
```

Root reviews and commits all new records and prepared protocol, leaving a clean worktree. No source operation is authorized by an uncommitted ticket. Then create the exact ordered request files:

```bash
python -B "$V3_ASSEMBLER" write-requests \
  --authority "$V3_RECORDS/SCREENING_AUTHORITY.json" --requests "$V3_REQUESTS"
```

This executes real `cli_authority(...,'screen')`, `_committed_record` and `screening_request` checks without source access. Each request is exactly `{"pool_index": i, "spec": pool[i], "protocol_binding": SHA256(SCREENING_AUTHORITY.json bytes)}`. Current committed plan/code/wrapper bytes must equal their prequery committed bytes. The request's spec, index and binding cannot be substituted.

## 4. Independent admission-only screening: every pool member, in order

Run the screener in an independent fork/process with no learner/catalog/policy-candidate outcomes. Only baseline native admission is allowed. All fixed pool members must be screened and retained even after two eligible roles are found. Authentic complete `PASS_NATIVE` and `FAIL_NATIVE` are equally eligible; the public envelope masks that bit as `ADMITTED_NATIVE`. A training PASS cannot be replaced to obtain a failing task.

The following Python operator loop calls the **actual CLI**, supplies the externally pinned ticket SHA, stops on an interrupted/invalid envelope, and never skips a case:

```bash
python -B - <<'PY'
import json, os, subprocess, sys
from pathlib import Path
from research.unified_consequence_runtime import qualify_native_frontier_v3 as q
authority = (q.RECORDS/'SCREENING_AUTHORITY.json').resolve()
sha = q.digest(authority.read_bytes())  # independently record this before launch
ticket = json.loads(authority.read_text())
pool = q._committed_record(ticket['repo'], ticket['pool'])
requests = Path(os.environ['V3_REQUESTS'])
for index in range(len(pool['pool'])):
    subprocess.run([sys.executable, '-B', '-m', q.MODULE,
        '--screen-spec', str(requests/('request-'+format(index, '03d')+'.json')),
        '--authority', str(authority), '--authority-sha256', sha,
        '--runtimes', os.environ['V3_RUNTIME_PATHS'],
        '--out', str(Path(ticket['output_root'])/('case-'+format(index, '03d')))], check=True)
PY
```

Keep the root-provided expected SHA independently; do not recompute it from editable ticket bytes inside an untrusted worker. The actual ticket bytes must also equal committed Git bytes. The controller locks `SCREENING_METER.json`, persists a pending launch before source access, requires sequential once-only indices, binds one screening source commit/runtime inventory, and retains every native launch delta on malformed reports. It refuses continued screening after invalid accounting. A crashed pending case is retained UNKNOWN; do not erase/reset the meter or replay it as untouched.

Budget: at most nine cases, two native executions per case, collection60s/call, execution600s/call,7200s total screening interval. Every case retains `SCREENING_CASE.json`, source/environment/collection/native artifacts and sealed `SCREENING_ENVELOPE.json`; native reexecution is charged. The learner receives only the sealed public envelopes, costs and metadata. Keep raw future baseline observations, source and receipt packets restricted to the independent screener/auditor.

## 5. Independent audit, final sealed manifest and first two roles

An independent auditor checks the genuine sealed raw reports and source/collection/native lineage, exact pool/receipt bytes, entire ordered meter, all admission negatives and costs, and actual information-exposure boundary. Native output requires complete authentic admission; outcome sign does not affect eligibility. The auditor can structurally validate existing worker receipts with `independent=False`; additional native reruns consume screening budget and must be predeclared/charged, not performed as free audit work.

The auditor writes a real audit JSON containing at least:

```json
{
  "status": "PASS_ADMISSION_ONLY_SCREENING_AUDIT",
  "pool_sha256": "<exact committed FROZEN_POOL.json bytes>",
  "reports_sha256": "<q.worker.fingerprint(ordered public envelopes)>",
  "eligibility_rule": "PASS_NATIVE_OR_FAIL_NATIVE_IDENTICAL",
  "all_screened_cases_and_costs_retained": true,
  "independent_screener": true,
  "search_or_policy_outcomes_accessed": false,
  "learner_future_source_accessed": false
}
```

These fields are attestations of actual reviewed conduct, not a template to mark PASS automatically. Preserve the auditor's checks/evidence and any refusal. With an actual passing audit:

```bash
python -B "$V3_ASSEMBLER" finalize-records \
  --authority "$V3_RECORDS/SCREENING_AUTHORITY.json" \
  --independent-audit /ABS/PATH/actual-independent-SCREENING_AUDIT.json
```

This copies only the public meter and real audit, constructs `SCREENING.json`, selects exactly first two distinct eligible sources in fixed order using `q.select_screened_roles(pool,reports,requested=2)`, writes `FRESH_TASK_METADATA.json`, and sets `FRONTIER_PROTOCOL.json` to `READY_TO_FREEZE_NO_LEARNER_SOURCE_ACCESS`. It calls real `require_screening_manifest` before returning. All pool reports and costs survive; no training-PASS or policy-tie replacement occurs. Insufficient eligible roles is a terminal shortfall for this pool.

The screening manifest's exact operative keys are `schema=UDM_ADMISSION_ONLY_SCREENING_V3`, `pool_sha256`, `prequery_sha256`, `environment_gate`, the three exposure booleans above, `reports` (sealed envelopes), `independent_audit` (repo-relative bound descriptor), `screening_authority` (absolute committed ticket descriptor), `screening_meter` (absolute descriptor to retained public meter), and `costs`. The controller independently checks every meter case and requires unchanged controller bytes since first screening source access. Root commits all final new records and leaves the worktree clean. Do not change controller/curator/gate bytes to repair a prospective result after screening.

## 6. Freeze the exact committed frontier; execute original MSI/V104

```bash
python -B -m research.unified_consequence_runtime.qualify_native_frontier_v3 \
  --write-freeze --repo /workspace/udm-v54 --runtimes "$V3_RUNTIME_PATHS" \
  --out "$V3_FREEZE"
```

`write_freeze(repo,out,runtime_paths)` requires the ready protocol, independent environment gate, entire sealed screening manifest, exact clean HEAD and unchanged original baseline files. It reconstructs the complete tracked source path set and fresh runtime identities. The freeze file stays outside the worktree so its creation does not dirty the execution commit. `check_freeze(repo,path)` rechecks committed bytes, complete file set, runtime identities and all bound records.

Prepare the actual coding-agent consumer **before** starting qualification, as described in stage7. Then:

```bash
python -B -m research.unified_consequence_runtime.qualify_native_frontier_v3 \
  --repo /workspace/udm-v54 --freeze "$V3_FREEZE" \
  --components /workspace/components --source-repos /workspace/repos \
  --out "$V3_RUN"
```

The run output directory must be new. `/workspace/components` and `/workspace/repos` must be the existing original authenticated MSI/V104/evaluator sources, not target-specific replacement methods. No direct `--catalog-spec` call is needed: the controller creates a typed immutable prepared-parent authority internally and the actual child catalog CLI authenticates it. Naked catalog/screen/agent CLI calls fail before dispatch.

The unchanged original 36-policy MSI carrier plus cold order can tie. Then `UNKNOWN_META_CHOICE` is the result, future source remains sealed, and the real training unchanged cold episode, profiles, actual informed-training-ledger episode, common costs, and pending training agent arm remain available. One future is legal to original `choose_meta_decision`; no third role is consumed. A training native PASS remains an honest no-residual outcome with a baseline-only pending agent arm.

G2 requires a unique original policy before future release; future cold prefix8 authentic FAIL; selected warm prefix within8 authentic PASS with retained policy dependency; independent fresh lineage checks; physical deletion of the acquired program in cloned machine state and actual rematerialized cold8 failure; fresh admit2+execute native PASS. Learning, failed prefixes, all native rechecks and removal costs consume the same512-native/3600s arm budgets. Failed accounting or an insufficient budget yields UNKNOWN. The informed ledger may tie the warm order; this G2 is a bounded noncomparative policy-order claim. G3 constructor/restoration remains UNKNOWN, and preparing an agent arm does not establish agent execution or G4.

## 7. Execute the actual coding-agent arm at publication

Set up an independent actual coding agent ready to receive the published arm before qualification starts. The arm clock starts at `agent_arm(...)` publication and includes common acquisition time plus subsequent deliberation; waiting for all later comparator searches to finish can exhaust its3600s budget. Do not reset the timer or republish a cheaper arm after seeing results.

The controller publishes, on a warranted shared context or native-failing training selection stop:

* `AGENT_ARM.json`: exact source contract, original allowed catalog and orders, original native baseline, common history/costs, release time and fixed meter path.
* `AGENT_PARENT_RECEIPT.json`: exact freeze/controller/prepared-context/entire arm hashes, common cost binding, release and start time.
* `AGENT_AUTHORITY.json`: typed operation `agent`, repo, freeze descriptor and immutable parent receipt descriptor.
* `ARM_METER.json`: initialized at handoff; not initialized lazily on first proposal.

When these files appear, root records the authority SHA independently and hands the independent agent the arm, source/baseline and lawful shared training history. Do not give it `RESULT.json` future outcomes, warm/cold candidate outcomes, counterfactual results, hidden author repair, new operators or extra target tests. For training UNKNOWN_CHOICE the agent stays on training; future remains sealed. It must actually reason and choose original catalog members, not replay a selected winner from another arm.

Each actual agent proposal is a `CANDIDATE.json` equal to one exact `candidate_catalog[i]['candidate']` object. The evaluator hashes the full candidate against frozen catalog membership. Root/agent invokes the actual CLI:

```bash
python -B -m research.unified_consequence_runtime.qualify_native_frontier_v3 \
  --agent-spec "$V3_RUN/AGENT_ARM.json" \
  --authority "$V3_RUN/AGENT_AUTHORITY.json" \
  --authority-sha256 ROOT_RECORDED_EXACT_AUTHORITY_SHA256 \
  --candidate /ABS/PATH/actual-agent-proposal-001.json \
  --out /ABS/PATH/new-actual-agent-evidence-001
```

The enriched `result['agent_comparator']['execute_command_argv']` contains this concrete authority/arm command and two placeholders for candidate/output. It can be used after result publication only if the meter still has time. The immutable ARM.json itself includes the same generic command shape; no source-reading child may self-authorize using editable arm fields.

At most8 proposals are admitted, native budget512 and wall3600 including common learning and independent reexecution. All launches, failures, invalid reports and interrupted attempts consume the locked persistent meter; an invalid accounting flag or final overrun cannot become PASS. Preserve actual agent prompt/transcript, model identity, timestamps, token/tool/native costs and raw evidence. If no actual agent ran, report `PENDING_ACTUAL_EXECUTION`. Unknown model/tool/engineering costs remain UNKNOWN. G4 stays UNKNOWN until the complete declared actual matched comparison and lifecycle evidence is independently assessed; no simulated transcript or prepared ticket is an agent result.

## Prepared-state validation evidence

Controller source SHA at final preparation: `d40d188be3565ed5127e06b033dd9cbf8fa32d60977d27ec47b5ae6698189418`. Own32 source-free tests pass including JSON syntax errors, nonobject `[]`/`null`, nonmapping costs, private launch-delta persistence, strict CLI authority, actual Git blob identity, pool binding, once-only meter and exact source-file-set checks. Combined74 controller/original meta/decisive tests passed after the final static bootstrap path addition (`FINAL_74_REGRESSIONS.log`). Logs retain prior RED and GREEN runs beside this file. These controls establish prepared implementation behavior, not a native frontier outcome.
