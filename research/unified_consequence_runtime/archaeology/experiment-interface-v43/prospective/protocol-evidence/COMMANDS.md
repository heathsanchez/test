These are operator commands for after independent whole-interface gate acceptance. None of the query, declaration, screening, freeze or agent commands below was run during readiness. Root owns every Git mutation. Replace audited external artifact/interpreter/model paths with the actual retained values; never manufacture PASS records or hash an editable child ticket to grant itself authority.

```bash
export GIT_OPTIONAL_LOCKS=0
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/workspace/udm-v54
export UDM_REPO=/workspace/udm-v54
export UDM_COMPONENTS=/workspace/components
export UDM_SOURCE_REPOS=/workspace/repos
export UDM_READINESS=/workspace/qualification/experiment-interface-v43-prospective-readiness
export UDM_RECORDS=$UDM_REPO/research/unified_consequence_runtime/archaeology/experiment-interface-v43/prospective
export UDM_OPERATOR=/workspace/qualification/native-frontier-v43-operator
: "${UDM_CONTROLLER_PYTHON:?actual isolated qualified controller interpreter}"
: "${UDM_RUNTIME_PATHS:?actual original two-profile RUNTIME_PATHS.json}"
: "${UDM_OLD_ENVIRONMENT_ARCHIVE:?audited original V42 environment ZIP}"
: "${UDM_INTERFACE_ARCHIVE:?audited complete whole V43 interface ZIP}"
UDM_CONTROLLER_PYTHON_SHA256=$(sha256sum "$UDM_CONTROLLER_PYTHON" | cut -d ' ' -f 1)
UDM_AGENT_MODEL_ARGS=()
if test -n "${UDM_AGENT_MODEL:-}"; then UDM_AGENT_MODEL_ARGS=(--model "$UDM_AGENT_MODEL"); fi
```

First, trusted root must place the independently audited `GATE_WRAPPER.json` at `UDM_RECORDS`, containing exactly `environment_gate`, `catalog`, `interface_gate`, `interface_archive_audit`. Its result/audit descriptors must point to ordinary committed repository files with the exact paths/digests chosen in the independent audit; changing an audited result path changes the descriptor and requires re-binding that audit. Preserve the old V42 gate result/status/counts and old ENVIRONMENT_GATE_FILES. The separate new interface descriptor uses the actual whole-mode driver schema/status and exact final interface hashes. Do not substitute a build-native-only result. Verify the wrapper without reading target names:

```bash
cd "$UDM_REPO"
"$UDM_CONTROLLER_PYTHON" -B - <<'PY'
import json, os
from pathlib import Path
from research.unified_consequence_runtime import qualify_native_frontier_v43 as q
records = Path(os.environ['UDM_RECORDS'])
wrapper = json.loads((records/'GATE_WRAPPER.json').read_text())
assert set(wrapper) == {'environment_gate','catalog','interface_gate','interface_archive_audit'}
q.require_environment_gate(wrapper)
for variable, key in (('UDM_OLD_ENVIRONMENT_ARCHIVE','environment_gate'),('UDM_INTERFACE_ARCHIVE','interface_gate')):
    assert q.digest(Path(os.environ[variable]).read_bytes()) == wrapper[key]['artifact_sha256']
PY
```

After root/reviewer accepts the outside drafts, install the two metadata helpers and compact prior record. Install the separate recovered original projection source and its literal-only V43 adapter using the adapter's exact sibling source filename; retain its source-free tests/evidence too. Install the operator watcher as a frozen protocol source. No original file is edited. Declare the already proposed identities only after gate acceptance, by copying `candidate_names` from `UNFROZEN_UNIVERSE_GRAMMAR_CHECK.json` into the canonical V43 declared-universe schema and exact three gate fields. This declaration is new-only and cannot be replaced after a shortfall.

```bash
cp "$UDM_READINESS/drafts/curate_frontier.py" "$UDM_RECORDS/curate_frontier.py"
cp "$UDM_READINESS/drafts/prepare_records.py" "$UDM_RECORDS/prepare_records.py"
cp "$UDM_READINESS/drafts/PRIOR_EXPOSURE.json" "$UDM_RECORDS/PRIOR_EXPOSURE.json"
cp "$UDM_READINESS/drafts/training_history_projection_v43.py" "$UDM_RECORDS/training_history_projection_v43.py"
cp -R "$UDM_READINESS/drafts/training-history-original" "$UDM_RECORDS/training-history-original"
cp "$UDM_READINESS/watch_actual_agent.py" "$UDM_RECORDS/watch_actual_agent.py"
"$UDM_CONTROLLER_PYTHON" -B - <<'PY'
import json, os
from pathlib import Path
from research.unified_consequence_runtime import qualify_native_frontier_v43 as q
records = Path(os.environ['UDM_RECORDS'])
wrapper = json.loads((records/'GATE_WRAPPER.json').read_text())
q.require_environment_gate(wrapper)
check = json.loads((Path(os.environ['UDM_READINESS'])/'UNFROZEN_UNIVERSE_GRAMMAR_CHECK.json').read_text())
assert check['frozen'] is False and check['network_queries'] == 0 and not check['overlap_prior_exposure']
universe = {'schema':'UDM_NATIVE_AUTHORITY_V43_DECLARED_UNIVERSE_V1','repositories':check['candidate_names'],
            **{key:wrapper[key] for key in ('environment_gate','interface_gate','interface_archive_audit')}}
with (records/'DECLARED_UNIVERSE.json').open('x') as stream:
    stream.write(q.canonical(universe)+'\n')
PY
"$UDM_CONTROLLER_PYTHON" -B "$UDM_RECORDS/curate_frontier.py" \
  --write-prequery "$UDM_RECORDS/PREQUERY.json" \
  --universe "$UDM_RECORDS/DECLARED_UNIVERSE.json" \
  --environment-gate "$UDM_RECORDS/GATE_WRAPPER.json" \
  --qualification-artifact "$UDM_OLD_ENVIRONMENT_ARCHIVE" \
  --interface-qualification-artifact "$UDM_INTERFACE_ARCHIVE"
```

Root now commits the complete new helpers/projection/watcher, declared universe, prequery, exact gate/result/audit/prior files. Verify a clean complete worktree. This is the prequery commitment; only then run the single metadata-query command. It retains all nine repository metadata dispositions and the resulting ordered pool, without source/test/patch contents or native outcomes.

```bash
"$UDM_CONTROLLER_PYTHON" -B "$UDM_RECORDS/curate_frontier.py" \
  --query-after-committed-prequery "$UDM_RECORDS/PREQUERY.json" \
  --universe "$UDM_RECORDS/DECLARED_UNIVERSE.json" \
  --environment-gate "$UDM_RECORDS/GATE_WRAPPER.json" \
  --qualification-artifact "$UDM_OLD_ENVIRONMENT_ARCHIVE" \
  --interface-qualification-artifact "$UDM_INTERFACE_ARCHIVE" --out "$UDM_RECORDS"
"$UDM_CONTROLLER_PYTHON" -B "$UDM_RECORDS/prepare_records.py" prepare-screening \
  --environment-gate "$UDM_RECORDS/GATE_WRAPPER.json" --curation "$UDM_RECORDS" \
  --screen-root "$UDM_OPERATOR/screening" --components "$UDM_COMPONENTS"
```

Root commits all three first-query outputs plus FRONTIER_PROTOCOL and SCREENING_AUTHORITY before any source admission. A zero-member pool is an immediate retained metadata shortfall; do not invent source-screening requests. Freeze/validate the original runtime identities, generate requests from this committed authority, and let the independent screener run every pool member once in order. The authority SHA below is computed by trusted parent/operator custody; it is passed as an independent pin to each source-reading CLI.

```bash
"$UDM_CONTROLLER_PYTHON" -B "$UDM_RECORDS/prepare_records.py" write-requests \
  --authority "$UDM_RECORDS/SCREENING_AUTHORITY.json" --requests "$UDM_OPERATOR/requests"
UDM_SCREEN_AUTHORITY_SHA256=$(sha256sum "$UDM_RECORDS/SCREENING_AUTHORITY.json" | cut -d ' ' -f 1)
shopt -s nullglob
for UDM_REQUEST in "$UDM_OPERATOR"/requests/request-*.json; do
  UDM_CASE_INDEX=${UDM_REQUEST##*/request-}
  UDM_CASE_INDEX=${UDM_CASE_INDEX%.json}
  "$UDM_CONTROLLER_PYTHON" -B -m research.unified_consequence_runtime.qualify_native_frontier_v43 \
    --screen-spec "$UDM_REQUEST" --authority "$UDM_RECORDS/SCREENING_AUTHORITY.json" \
    --authority-sha256 "$UDM_SCREEN_AUTHORITY_SHA256" --runtimes "$UDM_RUNTIME_PATHS" \
    --out "$UDM_OPERATOR/screening/case-$UDM_CASE_INDEX"
done
```

Do not retry an interrupted/failed case or add targets. An independent actor audits all raw cases, receipts, setup UNKNOWNs, sidecars and build/native/lifecycle charges, and supplies actual `SCREENING_AUDIT.json`. If fewer than two admit, archive a precise SCREENING_SHORTFALL with the complete cases/costs and stop; no task metadata/freeze/agent result is invented. Otherwise finalize the first two equal PASS/FAIL admissions:

```bash
"$UDM_CONTROLLER_PYTHON" -B "$UDM_RECORDS/prepare_records.py" finalize-records \
  --authority "$UDM_RECORDS/SCREENING_AUTHORITY.json" \
  --independent-audit "$UDM_OPERATOR/independent-audit/SCREENING_AUDIT.json"
```

Root commits the final protocol, metadata, sealed envelopes/meter and independent audit, keeping raw future source/evidence sealed outside learner input. Freeze exact clean source and runtime inventory before learner source access. Source-repos must contain the exact original MSI/Triskelion implementation objects required by the original constructor and policy selection; do not fetch target repair heads. The original component/evaluator pins remain mandatory.

```bash
"$UDM_CONTROLLER_PYTHON" -B -m research.unified_consequence_runtime.qualify_native_frontier_v43 \
  --write-freeze --repo "$UDM_REPO" --runtimes "$UDM_RUNTIME_PATHS" --out "$UDM_OPERATOR/FREEZE.json"
```

Start the trusted parent watcher before the main run so agent publication is observed immediately. It reads no RESULT contents, projects exact training evidence using the recovered original algorithm, records parent authority pins, then invokes the CLI with remaining matched budget. The lexical venv interpreter path is preserved; its resolved binary is only separately recorded and checked against the trusted parent SHA pin. The optional model argument is omitted unless a model was explicitly chosen; CLI defaults remain unresolved until actual event evidence identifies the served model. The CLI uses `--skip-git-repo-check --ephemeral` for the outside workspace without changing CLI configuration, HOME or CODEX_HOME. The watcher exits UNKNOWN if the controller finishes without publishing an arm; publication or a failed CLI process alone is never an executed-agent claim.

```bash
"$UDM_CONTROLLER_PYTHON" -B "$UDM_RECORDS/watch_actual_agent.py" \
  --repo "$UDM_REPO" --run "$UDM_OPERATOR/run" --agent-dir "$UDM_OPERATOR/actual-agent" \
  --python "$UDM_CONTROLLER_PYTHON" --source-repos "$UDM_SOURCE_REPOS" \
  --python-sha256 "$UDM_CONTROLLER_PYTHON_SHA256" \
  --metadata "$UDM_RECORDS/FRESH_TASK_METADATA.json" \
  --history-helper "$UDM_RECORDS/training_history_projection_v43.py" \
  "${UDM_AGENT_MODEL_ARGS[@]}" > "$UDM_OPERATOR/agent-watcher.stdout" 2> "$UDM_OPERATOR/agent-watcher.stderr" &
UDM_AGENT_WATCHER_PID=$!
"$UDM_CONTROLLER_PYTHON" -B -m research.unified_consequence_runtime.qualify_native_frontier_v43 \
  --repo "$UDM_REPO" --freeze "$UDM_OPERATOR/FREEZE.json" --components "$UDM_COMPONENTS" \
  --source-repos "$UDM_SOURCE_REPOS" --out "$UDM_OPERATOR/run" \
  > "$UDM_OPERATOR/native-selection.stdout" 2> "$UDM_OPERATOR/native-selection.stderr"
UDM_NATIVE_EXIT_CODE=$?
printf '%s\n' "$UDM_NATIVE_EXIT_CODE" > "$UDM_OPERATOR/NATIVE_EXIT_CODE.txt"
wait "$UDM_AGENT_WATCHER_PID"
UDM_AGENT_WATCHER_EXIT_CODE=$?
printf '%s\n' "$UDM_AGENT_WATCHER_EXIT_CODE" > "$UDM_OPERATOR/AGENT_WATCHER_EXIT_CODE.txt"
```

Retain raw process exit codes and both logs even when either process fails. Final independent assessment must audit the actual agent transcript for equal information, all failed proposals, original catalog membership, persistent meter, native independent evidence and complete measured costs. Preserve UNKNOWN for unavailable model/tool/engineering charges, scientific ties/obstructions, refinement and non-bypassability. Metadata/admission/interface qualification does not establish G2, G3 or G4.

If the CLI is unavailable or fails, preserve its complete failure packet. Once that process and any native child attempt have finished and the original meter lock is free, trusted root may invoke an actual collaboration agent using `collaboration.spawn_agent` with `fork_turns="none"`. Supply the exact already frozen PROMPT.md, authority descriptor/hash, projected training-history descriptor/hash, lexical interpreter/binary pin, exact ARM and current remaining time/proposals/calls. The fallback receives only this arm's prior failed attempts and allowed training/current-release inputs. Retain its agent ID, invocation timestamps, actual transcript/tool calls and native evidence as an explicit second transport in the same comparator. Do not republish ARM, change/reset ARM_METER, restart the common acquisition clock, replace the candidate catalog, or erase CLI costs. If the same original deadline is exhausted, stop UNKNOWN. The fallback is an actual agent invocation, never a shell-script proposal or a manufactured completion; native candidate execution still requires a new positive native launch in the persistent meter.
