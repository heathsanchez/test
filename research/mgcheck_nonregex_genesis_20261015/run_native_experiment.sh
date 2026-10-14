#!/usr/bin/env bash
set -euo pipefail
BASE="${GITHUB_WORKSPACE:-$(pwd)}"
ROOT="$BASE/research/mgcheck_nonregex_genesis_20261015"
WORK="${RUNNER_TEMP:-/tmp}/mg_nonregex_20261015"
REPORT="$BASE/nonregex-native-evidence"
mkdir -p "$WORK" "$REPORT"
export GOFLAGS="-mod=mod"
PREVIOUS="$ROOT/prior_regex_incumbent.go"
LEARNER="$ROOT/nonregex_method_learner.go"
SUCCESS=0; TRANSFERS=0; CHALLENGES=0

stage() {
 local kind="$1" repo="$2" number="$3" base_sha="$4" head_sha="$5" mode="$6"
 local out="$WORK/$kind"
 mkdir -p "$out"
 git clone -q --no-checkout "https://github.com/$repo.git" "$out/upstream"
 git -C "$out/upstream" fetch -q origin "refs/pull/$number/head:refs/pull/$number/head"
 test "$(git -C "$out/upstream" rev-parse "refs/pull/$number/head")" = "$head_sha"
 git -C "$out/upstream" cat-file -e "${base_sha}^{commit}"
 git -C "$out/upstream" worktree add -q --detach "$out/old" "$base_sha"
 git -C "$out/upstream" worktree add -q --detach "$out/head" "$head_sha"
 test "$(git -C "$out/old" rev-parse HEAD)" = "$base_sha"
 test "$(git -C "$out/head" rev-parse HEAD)" = "$head_sha"
 echo "FROZEN_SUBJECT=$kind/$repo/$number base=$base_sha head=$head_sha"
 set +e
 go run "$PREVIOUS" -old "$out/old" -head "$out/head" -old-sha "$base_sha" -head-sha "$head_sha" -out "$out/legacy-regex.json" > "$out/legacy-regex.log" 2>&1
 local old_rc=$?
 set -e
 python - "$out/legacy-regex.json" "$kind" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
if not p.exists(): print("NO_OLD_METHOD_RESULT");sys.exit(1)
d=json.loads(p.read_text())
print("LEGACY_SCOPE",sys.argv[2],d.get("status"),"changed_unique_patterns",d.get("changed_unique_patterns"))
if d.get("changed_unique_patterns",0)!=0 or d.get("status") not in ("REJECTED_NO_MATCHED_PATTERN_CHANGE","UNKNOWN_NO_FINITE_WITNESS"):
 print("INCUMBENT_DID_NOT_REFUSE_NONREGEX_SOURCE")
 sys.exit(2)
PY
 local regex_gate=$?
 if [[ "$regex_gate" -ne 0 ]];then echo "$kind" >> "$REPORT/regex-scope-failure.txt";fi
 local extra=()
 if [[ "$mode" = "transfer" ]];then extra+=( -retained "$WORK/acquire/retained-plan.json" );fi
 set +e
 go run "$LEARNER" -mode "$mode" -old "$out/old" -head "$out/head" \
  -old-sha "$base_sha" -head-sha "$head_sha" \
  -out "$out/new-result.json" -plan "$out/retained-plan.json" \
  "${extra[@]}" > "$out/generator.log" 2>&1
 local native_exit=$?
 set -e
 if [[ -f "$out/new-result.json" ]];then
  python - "$out/new-result.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
p=d.get("AcquiredMethod") or d.get("RetainedMethod") or {}
w=d.get("NativeWitness") or {}
print("NATIVE_METHOD_STATUS",d.get("Stage"),d.get("Status"),
 "functions",d.get("FunctionCandidates"),"inputs",d.get("InputCount"),
 "differential_candidates",d.get("BaselineWitnessCount"),
 "operator",p.get("Operator"),"function",w.get("Function",{}).get("Name"),
 "input",w.get("Probe",{}).get("Input"),
 "total_ms",d.get("FullBudgetMillis"),"search_ms",d.get("SearchMillis"))
print("NATIVE_METHOD_SETUP_ERRORS",d.get("RunErrors",[])[:4])
PY
 else
  echo "NATIVE_METHOD_NO_REPORT[$kind]";tail -50 "$out/generator.log"||true
 fi
 # Physically supply wrong source identity: never promote.
 set +e
 go run "$LEARNER" -mode "$mode" -old "$out/old" -head "$out/head" \
  -old-sha "$base_sha" -head-sha "0000000000000000000000000000000000000000" \
  -out "$out/wrong-pin.json" -plan "$out/wrong-plan.json" \
  "${extra[@]}" > "$out/wrong-pin.log" 2>&1
 local wrong_exit=$?
 set -e
 if [[ "$wrong_exit" -eq 0 ]];then echo "ERROR_WRONG_SHA_ACCEPTED[$kind]";exit 17;fi
 python - "$out/wrong-pin.json" <<'PY'
import json,sys
assert json.load(open(sys.argv[1]))["Status"]=="UNKNOWN_SOURCE_IDENTITY"
print("ACTUAL_WRONG_SUBJECT_SHA_REJECTED")
PY
 if [[ "$mode" = "transfer" ]];then
  set +e
  go run "$LEARNER" -mode transfer -old "$out/old" -head "$out/head" \
    -old-sha "$base_sha" -head-sha "$head_sha" \
    -retained "$out/intentionally-absent-retained-plan.json" \
    -out "$out/no-plan.json" -plan "$out/no-plan-created.json" > "$out/no-plan.log" 2>&1
  local removed_exit=$?
  set -e
  test "$removed_exit" -ne 0
  python - "$out/no-plan.json" <<'PY'
import json,sys
assert json.load(open(sys.argv[1]))["Status"]=="UNKNOWN_RETAINED_METHOD_REMOVED"
print("ACTUAL_RETAINED_METHOD_REMOVAL_REOPENS_UNKNOWN")
PY
 fi
 mkdir -p "$REPORT/$kind"
 cp "$out/"*.json "$REPORT/$kind/" 2>/dev/null || true
 cp "$out/generator.log" "$REPORT/$kind/generator.log"
 cp "$out/legacy-regex.log" "$REPORT/$kind/regex.log"
 echo "STAGE_EXIT_$kind=$native_exit PREVIOUS_REGEX_EXIT=$old_rc"
 if [[ "$native_exit" -ne 0||"$regex_gate" -ne 0 ]];then return 1;fi
 return 0
}
if stage acquire spf13/cast 352 \
  6fd6afdc9df068c662e923a7c3ad04fda4647121 \
  9e3a7c487e18826a2482ad34ff29c58221a0c85b acquire; then SUCCESS=1;fi
if stage transfer Masterminds/semver 303 \
  8b89c86cb53c57cfd5d07c13de12bc4d78954e99 \
  c9706646b4e12416632860dd87d388c2eed07052 transfer; then TRANSFERS=1;fi
if stage challenge shopspring/decimal 428 \
  f658fbf1eb94abc869558633a0b9b239300899f4 \
  1fc621e247bcaa551e84a3a49608515ef9cbf13e challenge;then CHALLENGES=1;fi
printf '{"acquired":%s,"transferred":%s,"orthogonal_challenge":%s}\n' "$SUCCESS" "$TRANSFERS" "$CHALLENGES" > "$REPORT/gates.json"
echo "FINAL_NATIVE_GATES=$(cat "$REPORT/gates.json")"
if [[ "$SUCCESS" -ne 1||"$TRANSFERS" -ne 1 ]];then
 echo "NOT_QUALIFIED_FOR_NEW_METHOD_TRANSFER"
 exit 23
fi
echo "WARRANTED_BOUNDED_FIXED_GRAMMAR_PLAN_CONSTRUCTION_AND_TRANSFER"
echo "L7_UNRESTRICTED_NEW_GRAMMAR=UNKNOWN"
echo "FULL_INFORMATION_BASELINE_ADVANTAGE=NOT_PROVEN"
