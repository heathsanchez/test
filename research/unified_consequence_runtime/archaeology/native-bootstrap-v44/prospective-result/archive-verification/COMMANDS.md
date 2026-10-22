These are future operator commands, not executed actions. Run only after the actual ordered screening/science actors and independent audits finish; retain shortfalls/UNKNOWNs as outcomes. No workflow below replays native tests or invokes a model.

1. Review the publication input. The operator tree is the declared V44 source; do not pack CI-observer/download transport directories or ephemeral URL logs. Preserve excluded operational raw records locally and disclose any published sanitized summary/digest. Stop if the scientific packet itself cannot be published without violating source/evidence closure; do not silently drop refusals.

2. Package the complete stable operator tree with the original builder and a different original readback verifier, keeping outputs outside that tree:

```bash
export GIT_OPTIONAL_LOCKS=0
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/workspace/udm-v54
export UDM_REPO=/workspace/udm-v54
export UDM_CONTROLLER_PYTHON=/workspace/qualification/native-authority-v42-controller/bin/python
export UDM_OPERATOR=/workspace/qualification/native-frontier-v44-operator
export UDM_ARCHIVE_DRAFT=/workspace/qualification/native-bootstrap-v44-final-archive-preparation
export UDM_PUBLICATION=/workspace/qualification/native-bootstrap-v44-final-publication
mkdir -p "$UDM_PUBLICATION"
"$UDM_CONTROLLER_PYTHON" -B "$UDM_ARCHIVE_DRAFT/archive_evidence_v44.py" pack \
  --repo "$UDM_REPO" --source "$UDM_OPERATOR" \
  --archive "$UDM_PUBLICATION/RAW_EVIDENCE_CAS.tar.gz" \
  --manifest "$UDM_PUBLICATION/RAW_EVIDENCE_CAS.MANIFEST.json" \
  --readback "$UDM_PUBLICATION/RAW_EVIDENCE_CAS.READBACK.json" \
  --summary "$UDM_PUBLICATION/RAW_EVIDENCE_CAS.BUILD.json"
```

An independent actor should review/read back the resulting pack against the live original stable source. The original helper enforces its existing per-file <100 MB cap. If that fails, preserve the failure and use independently declared disjoint operator subtree packs plus an audited complete union coverage record; never omit a large case/common subtree. The draft checker accepts multiple existing-format packets but does not invent a coverage certificate.

3. Root installs only the reviewed new archival driver/workflow and the actual approved publication files under `research/unified_consequence_runtime/archaeology/native-bootstrap-v44/prospective-result/`. Do not touch native runtime, verifier, gate, original result or frozen protocol files. Required role files are `FINAL_RESULT.json`, actual `SCREENING_AUDIT.json` (which may honestly be UNKNOWN) and `RESEARCH_REPORT.md`. Preserve complete per-case refusals/costs, native evidence, scientific/comparator evidence if actually executed, source exposure and supersession/negative records. Copy actual independently audited gate result/audit records to their already bound canonical repository paths if not present.

4. Populate a final expectation from actual bytes. `ARCHIVE_EXPECTATION.DRAFT.json` cannot pass as supplied. The exact schema is:

```json
{
  "schema": "UDM_V44_FINAL_EVIDENCE_EXPECTATION_V1",
  "mode": "ARCHIVE_ONLY_NO_SCIENTIFIC_PROMOTION",
  "files": {"FINAL_RESULT.json": {"sha256": "ACTUAL", "bytes": 0}},
  "repository_records": {"research/unified_consequence_runtime/ACTUAL_RESULT_PATH.json": {"sha256": "ACTUAL", "bytes": 0}},
  "roles": {"final_result": "FINAL_RESULT.json", "independent_audit": "SCREENING_AUDIT.json", "report": "RESEARCH_REPORT.md"},
  "archives": [{"archive": "RAW_EVIDENCE_CAS.tar.gz", "manifest": "RAW_EVIDENCE_CAS.MANIFEST.json", "readback": "RAW_EVIDENCE_CAS.READBACK.json", "source_root": "/workspace/qualification/native-frontier-v44-operator"}],
  "qualified_gate_references": [{"kind": "bootstrap_v44", "descriptor": {}, "result_record": "research/unified_consequence_runtime/ACTUAL_RESULT_PATH.json"}],
  "retained_scientific_verdicts": {},
  "retained_independent_audit_status": "ACTUAL"
}
```

The example uses invalid placeholders, not actual authority. Pin every archive/manifest/readback/result/audit/report/driver/diagnostic file selected for publication in `files`. Pin all exact repository-relative source-gate/result/audit/protocol/index references in `repository_records`. Qualified gate references must include the preserved `environment_v42`, preserved `interface_v43`, and final corrected `bootstrap_v44`; additional superseded bounded native results may be retained separately without changing their original boundaries. Each descriptor has the actual seven gate fields; its result hash must match the pinned exact result file. The retained verdicts/status must equal the actual result and audit bytes, including UNKNOWNs, unstarted arms and ties. Do not generate a PASS audit to make archival green.

5. Set the workflow's `ARCHIVE_EXPECTATION_SHA256` to the actual expectation hash after independent review. Its expected-source input refers to the new final publication commit; the science/gate source commits remain their original pinned records. Commit/push only the isolated owned branch with an archival marker. Require a clean full source tree.

```bash
cd "$UDM_REPO"
UDM_RESULT=research/unified_consequence_runtime/archaeology/native-bootstrap-v44/prospective-result
cp "$UDM_ARCHIVE_DRAFT/archive_evidence_v44.py" "$UDM_RESULT/ARCHIVE_ONLY_CHECK.py"
cp "$UDM_ARCHIVE_DRAFT/udm-native-frontier-evidence-v44.yml" .github/workflows/udm-native-frontier-evidence-v44.yml
# Root copies the actual independently reviewed payload and fills exact expectation here.
# Root replaces only the workflow's deliberate expectation-hash placeholder.
# Do not execute until every placeholder is gone and every required real file is pinned.
git add "$UDM_RESULT" .github/workflows/udm-native-frontier-evidence-v44.yml
git commit -m "Archive complete V44 result and refusal evidence [archive-frontier-v44]"
git push origin HEAD
```

The marked push triggers the new archive-only workflow. Alternatively dispatch it on the exact same owned branch/commit:

```bash
gh workflow run udm-native-frontier-evidence-v44.yml \
  --ref research/udm-native-bootstrap-v44-20261022 \
  -f expected_source_commit="$(git rev-parse HEAD)"
```

Do not trigger both merely to repeat an archive headline. The workflow checks current source against exact Git blobs, preserves all 2,628 original files/modes, archives complete current source plus the three original component trees, verifies all raw evidence members and uploads data with no native/science/model execution. Its own scientific verdicts stay UNKNOWN. Read back the exact final Actions artifact ZIP/digest and every published member before reporting archival success. Actual native/G2/G4 conclusions remain solely in the separately audited original experiment, with their original costs, freezes and limitations.
