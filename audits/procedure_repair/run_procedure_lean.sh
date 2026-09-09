#!/usr/bin/env bash
set -euo pipefail
AUDIT="$GITHUB_WORKSPACE/audit/audits/procedure_repair"
CROSS="$GITHUB_WORKSPACE/audit/audits/cross_domain"
GENESIS="$GITHUB_WORKSPACE/audit/audits/certificate_genesis"
RECOVERED="$GITHUB_WORKSPACE/recovered"
EVIDENCE="$GITHUB_WORKSPACE/evidence"
BUILD="$PWD/.mathgraph-procedure"
mkdir -p "$EVIDENCE" "$BUILD"
test "$(git rev-parse HEAD)" = "$EXPECTED_REF"
git rev-parse HEAD > "$EVIDENCE/source-commit.txt"
cp lean-toolchain "$EVIDENCE/source-toolchain.txt"
cp lake-manifest.json "$EVIDENCE/source-manifest.json"
if [ "$TASK" = source ]; then
  test "$(git hash-object EulerBlowup/Elementary.lean)" = 5814b45a6fc141985c5bc59a7152ef98f8c0c6e6
else
  test "$(git hash-object NavierStokes/PolarCharts.lean)" = 93e1a3ed3b300512a4bb5a27c45b838e57e371b5
fi
if [ "$TASK" != soundness ]; then
  test -s "$RECOVERED/RecoveredProcedures.lean"
  test -s "$RECOVERED/HeldoutProcedure.lean"
  (cd "$RECOVERED" && sha256sum -c source.sha256)
  cp "$RECOVERED/RecoveredProcedures.lean" "$BUILD/RecoveredProcedures.lean"
  cp "$RECOVERED/HeldoutProcedure.lean" "$BUILD/HeldoutProcedure.lean"
  cp "$RECOVERED/certificate.json" "$EVIDENCE/certificate.json"
  sha256sum "$BUILD/RecoveredProcedures.lean" "$BUILD/HeldoutProcedure.lean" > "$EVIDENCE/generated-source-hash.txt"
fi
curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -o /tmp/elan-init.sh
sh /tmp/elan-init.sh -y --default-toolchain none
export PATH="$HOME/.elan/bin:$PATH"
elan toolchain install "$(cat lean-toolchain)"
elan default "$(cat lean-toolchain)"
lean --version | tee "$EVIDENCE/source-lean-version.txt"
if lake exe cache get > "$EVIDENCE/cache-first.log" 2>&1; then
  echo SOURCE_TOOLCHAIN_CACHE=PASS | tee "$EVIDENCE/cache-status.txt"
else
  grep -q 'Dependency Mathlib uses a different lean-toolchain' "$EVIDENCE/cache-first.log"
  test -f .lake/packages/mathlib/lean-toolchain
  git -C .lake/packages/mathlib rev-parse HEAD > "$EVIDENCE/mathlib-commit.txt"
  cp .lake/packages/mathlib/lean-toolchain lean-toolchain
  elan toolchain install "$(cat lean-toolchain)"
  elan default "$(cat lean-toolchain)"
  echo MATHLIB_CACHE_COMPATIBILITY_REPLAY | tee "$EVIDENCE/cache-status.txt"
  lake exe cache get > "$EVIDENCE/cache.log" 2>&1
fi
lean --version | tee "$EVIDENCE/runtime-lean-version.txt"
test "$(git rev-parse HEAD)" = "$EXPECTED_REF"
git -C .lake/packages/mathlib rev-parse HEAD | tee "$EVIDENCE/mathlib-commit.txt"
run_audit() {
  lake env bash -c 'export LEAN_PATH="$1:$LEAN_PATH"; shift; exec lean "$@"' bash "$BUILD" "$@"
}
cp "$AUDIT/ProcedureRules.lean" "$BUILD/ProcedureRules.lean"
run_audit -o "$BUILD/ProcedureRules.olean" "$BUILD/ProcedureRules.lean" > "$EVIDENCE/soundness.log" 2>&1
NAMES='CrossDomainResidual.ProcedureRules.coeffPoly_sound CrossDomainResidual.ProcedureRules.halfLineSquare_sound CrossDomainResidual.ProcedureRules.intervalAffine_sound CrossDomainResidual.ProcedureRules.sum_sound CrossDomainResidual.ProcedureRules.product_sound'
if [ "$TASK" != soundness ]; then
  run_audit -o "$BUILD/RecoveredProcedures.olean" "$BUILD/RecoveredProcedures.lean" > "$EVIDENCE/recovered.log" 2>&1
  run_audit -o "$BUILD/HeldoutProcedure.olean" "$BUILD/HeldoutProcedure.lean" > "$EVIDENCE/heldout.log" 2>&1
  NAMES="$NAMES CrossDomainResidual.ProcedureRepair.derivative_nonneg CrossDomainResidual.ProcedureRepair.recovered_lower CrossDomainResidual.ProcedureRepair.interval_nonneg"
  if [ "$TASK" = target ]; then
    lake build NavierStokes.PolarCharts > "$EVIDENCE/source-build.log" 2>&1
    cp "$CROSS/KnownUpper.lean" "$BUILD/KnownUpper.lean"
    cp "$GENESIS/IndependentTarget.lean" "$BUILD/IndependentTarget.lean"
    cp "$AUDIT/ProcedurePolarTransfer.lean" "$BUILD/ProcedurePolarTransfer.lean"
    run_audit -o "$BUILD/KnownUpper.olean" "$BUILD/KnownUpper.lean" > "$EVIDENCE/known-upper.log" 2>&1
    run_audit "$BUILD/IndependentTarget.lean" > "$EVIDENCE/independent-target.log" 2>&1
    run_audit "$BUILD/ProcedurePolarTransfer.lean" > "$EVIDENCE/lean.log" 2>&1
    NAMES="$NAMES CrossDomainResidual.IndependentTarget.angle_gt_seven_tenths CrossDomainResidual.ProcedurePolarTransfer.baseChart_angle_bounds CrossDomainResidual.ProcedurePolarTransfer.localChart_angle_bounds CrossDomainResidual.ProcedurePolarTransfer.recovered_angle_gt_seven_tenths"
  else
    lake build EulerBlowup.Elementary > "$EVIDENCE/source-build.log" 2>&1
    cp "$AUDIT/ProcedureSourceCheck.lean" "$BUILD/ProcedureSourceCheck.lean"
    run_audit "$BUILD/ProcedureSourceCheck.lean" > "$EVIDENCE/lean.log" 2>&1
    NAMES="$NAMES CrossDomainResidual.ProcedureSourceCheck.quadratic_stronger_on CrossDomainResidual.ProcedureSourceCheck.recovered_implies_source_on CrossDomainResidual.ProcedureSourceCheck.original_source_check CrossDomainResidual.ProcedureSourceCheck.strict_improvement_at_one"
  fi
fi
cat "$EVIDENCE/soundness.log"
for f in recovered.log heldout.log independent-target.log lean.log; do
  if [ -f "$EVIDENCE/$f" ]; then cat "$EVIDENCE/$f"; fi
done
NAMES="$NAMES" python - <<'PY'
import os,pathlib,re
root=pathlib.Path(os.environ['GITHUB_WORKSPACE'])/'evidence'
text='\n'.join(p.read_text() for p in root.glob('*.log') if p.name in ('soundness.log','recovered.log','heldout.log','independent-target.log','lean.log'))
allowed={'propext','Quot.sound','Classical.choice'}
records=[]
for actual,axioms in re.findall(r"'([^']+)' depends on axioms: \[([^\]]*)\]",text):
    records.append((actual,{x.strip() for x in axioms.split(',') if x.strip()}))
for actual in re.findall(r"'([^']+)' does not depend on any axioms",text):
    records.append((actual,set()))
for name in os.environ['NAMES'].split():
    matches=[(actual,axioms) for actual,axioms in records if actual==name]
    assert len(matches)==1,(name,matches)
    actual,axioms=matches[0]
    assert axioms<=allowed,(actual,axioms)
    print(actual,'AXIOMS_PASS')
print('PROCEDURE_REPAIR_LEAN_QUALIFICATION_PASS')
PY
