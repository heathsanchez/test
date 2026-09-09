#!/usr/bin/env bash
set -euo pipefail
AUDIT="$GITHUB_WORKSPACE/audit/audits/form_recovery"
CROSS="$GITHUB_WORKSPACE/audit/audits/cross_domain"
RECOVERED="$GITHUB_WORKSPACE/recovered"
EVIDENCE="$GITHUB_WORKSPACE/evidence"
AUDIT_BUILD="$PWD/.mathgraph-form"
mkdir -p "$EVIDENCE" "$AUDIT_BUILD"
test "$(git rev-parse HEAD)" = "$EXPECTED_REF"
git rev-parse HEAD > "$EVIDENCE/source-commit.txt"
cp lean-toolchain "$EVIDENCE/source-toolchain.txt"
cp lake-manifest.json "$EVIDENCE/source-manifest.json"
if [ "$TASK" = target ]; then
  test "$(git hash-object NavierStokes/PolarCharts.lean)" = 93e1a3ed3b300512a4bb5a27c45b838e57e371b5
else
  test "$(git hash-object EulerBlowup/Elementary.lean)" = 5814b45a6fc141985c5bc59a7152ef98f8c0c6e6
fi
# Do not synthesize again. Verify the exact finite-job artifact.
test -s "$RECOVERED/RecoveredForm.lean"
(cd "$RECOVERED" && sha256sum -c source.sha256)
cp "$RECOVERED/RecoveredForm.lean" "$AUDIT_BUILD/RecoveredForm.lean"
cp "$RECOVERED/certificate.json" "$EVIDENCE/certificate.json"
sha256sum "$AUDIT_BUILD/RecoveredForm.lean" > "$EVIDENCE/generated-source-hash.txt"
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
  lake env bash -c 'export LEAN_PATH="$1:$LEAN_PATH"; shift; exec lean "$@"' bash "$AUDIT_BUILD" "$@"
}
run_audit -o "$AUDIT_BUILD/RecoveredForm.olean" "$AUDIT_BUILD/RecoveredForm.lean" > "$EVIDENCE/recovered-form.log" 2>&1
if [ "$TASK" = target ]; then
  lake build NavierStokes.PolarCharts > "$EVIDENCE/source-build.log" 2>&1
  cp "$CROSS/KnownUpper.lean" "$AUDIT_BUILD/KnownUpper.lean"
  cp "$AUDIT/FormPolarTransfer.lean" "$AUDIT_BUILD/FormPolarTransfer.lean"
  run_audit -o "$AUDIT_BUILD/KnownUpper.olean" "$AUDIT_BUILD/KnownUpper.lean" > "$EVIDENCE/known-upper.log" 2>&1
  run_audit "$AUDIT_BUILD/FormPolarTransfer.lean" > "$EVIDENCE/lean.log" 2>&1
  NAMES='CrossDomainResidual.FormRecovered.recovered_lower CrossDomainResidual.FormPolarTransfer.baseChart_angle_bounds CrossDomainResidual.FormPolarTransfer.localChart_angle_bounds'
else
  lake build EulerBlowup.Elementary > "$EVIDENCE/source-build.log" 2>&1
  PYTHONPATH="$AUDIT:$CROSS" python "$AUDIT/source_compare.py" --certificate "$EVIDENCE/certificate.json" --output "$AUDIT_BUILD/FormSourceCheck.lean"
  run_audit "$AUDIT_BUILD/FormSourceCheck.lean" > "$EVIDENCE/lean.log" 2>&1
  NAMES='CrossDomainResidual.FormRecovered.recovered_lower CrossDomainResidual.FormSourceCheck.expression_agreement CrossDomainResidual.FormSourceCheck.recovered_implies_source CrossDomainResidual.FormSourceCheck.source_implies_recovered'
fi
cat "$EVIDENCE/recovered-form.log" "$EVIDENCE/lean.log"
NAMES="$NAMES" python - <<'PY'
import os,pathlib,re
root=pathlib.Path(os.environ['GITHUB_WORKSPACE'])/'evidence'
text=(root/'recovered-form.log').read_text()+'\n'+(root/'lean.log').read_text()
allowed={'propext','Quot.sound','Classical.choice'}
records=[]
for actual,axioms in re.findall(r"'([^']+)' depends on axioms: \[([^\]]*)\]",text):
    records.append((actual,{x.strip() for x in axioms.split(',') if x.strip()}))
for actual in re.findall(r"'([^']+)' does not depend on any axioms",text):
    records.append((actual,set()))
for name in os.environ['NAMES'].split():
    # Lean elaborates private theorem names with a file-specific prefix.
    matches=[(actual,axioms) for actual,axioms in records
             if actual==name or actual.endswith('.'+name)]
    assert len(matches)==1,(name,matches)
    actual,axioms=matches[0]
    assert axioms <= allowed,(actual,axioms)
    print(actual,'AXIOMS_PASS')
print('FORM_RECOVERY_LEAN_QUALIFICATION_PASS')
PY
