#!/usr/bin/env bash
set -euo pipefail
AUDIT="$GITHUB_WORKSPACE/audit/audits/certificate_genesis"
FORM="$GITHUB_WORKSPACE/audit/audits/form_recovery"
CROSS="$GITHUB_WORKSPACE/audit/audits/cross_domain"
RECOVERED="$GITHUB_WORKSPACE/recovered"
EVIDENCE="$GITHUB_WORKSPACE/evidence"
AUDIT_BUILD="$PWD/.mathgraph-genesis"
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
# The exact artifact from the finite job is checked, never regenerated here.
test -s "$RECOVERED/RecoveredGenesis.lean"
(cd "$RECOVERED" && sha256sum -c source.sha256)
cp "$RECOVERED/RecoveredGenesis.lean" "$AUDIT_BUILD/RecoveredGenesis.lean"
cp "$RECOVERED/certificate.json" "$EVIDENCE/certificate.json"
sha256sum "$AUDIT_BUILD/RecoveredGenesis.lean" > "$EVIDENCE/generated-source-hash.txt"
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
run_audit -o "$AUDIT_BUILD/RecoveredGenesis.olean" "$AUDIT_BUILD/RecoveredGenesis.lean" > "$EVIDENCE/recovered.log" 2>&1
if [ "$TASK" = target ]; then
  lake build NavierStokes.PolarCharts > "$EVIDENCE/source-build.log" 2>&1
  cp "$CROSS/KnownUpper.lean" "$AUDIT_BUILD/KnownUpper.lean"
  cp "$AUDIT/GenesisPolarTransfer.lean" "$AUDIT_BUILD/GenesisPolarTransfer.lean"
  cp "$AUDIT/IndependentTarget.lean" "$AUDIT_BUILD/IndependentTarget.lean"
  run_audit -o "$AUDIT_BUILD/KnownUpper.olean" "$AUDIT_BUILD/KnownUpper.lean" > "$EVIDENCE/known-upper.log" 2>&1
  run_audit "$AUDIT_BUILD/IndependentTarget.lean" > "$EVIDENCE/independent-target.log" 2>&1
  run_audit "$AUDIT_BUILD/GenesisPolarTransfer.lean" > "$EVIDENCE/lean.log" 2>&1
  NAMES='CrossDomainResidual.CertificateGenesis.recovered_lower CrossDomainResidual.IndependentTarget.angle_gt_seven_tenths CrossDomainResidual.GenesisPolarTransfer.baseChart_angle_bounds CrossDomainResidual.GenesisPolarTransfer.localChart_angle_bounds CrossDomainResidual.GenesisPolarTransfer.recovered_angle_gt_seven_tenths'
else
  lake build EulerBlowup.Elementary > "$EVIDENCE/source-build.log" 2>&1
  PYTHONPATH="$AUDIT:$FORM:$CROSS" python "$AUDIT/source_compare.py" --certificate "$EVIDENCE/certificate.json" --output "$AUDIT_BUILD/GenesisSourceCheck.lean"
  run_audit "$AUDIT_BUILD/GenesisSourceCheck.lean" > "$EVIDENCE/lean.log" 2>&1
  NAMES='CrossDomainResidual.CertificateGenesis.recovered_lower CrossDomainResidual.GenesisSourceCheck.quadratic_stronger_on CrossDomainResidual.GenesisSourceCheck.recovered_implies_source_on CrossDomainResidual.GenesisSourceCheck.original_source_check CrossDomainResidual.GenesisSourceCheck.strict_improvement_at_one'
fi
cat "$EVIDENCE/recovered.log" "$EVIDENCE/lean.log"
if [ "$TASK" = target ]; then cat "$EVIDENCE/independent-target.log"; fi
NAMES="$NAMES" python - <<'PY'
import os,pathlib,re
root=pathlib.Path(os.environ['GITHUB_WORKSPACE'])/'evidence'
text='\n'.join(p.read_text() for p in (root/'recovered.log',root/'lean.log') if p.exists())
if (root/'independent-target.log').exists():text+='\n'+(root/'independent-target.log').read_text()
allowed={'propext','Quot.sound','Classical.choice'}
records=[]
for actual,axioms in re.findall(r"'([^']+)' depends on axioms: \[([^\]]*)\]",text):
    records.append((actual,{x.strip() for x in axioms.split(',') if x.strip()}))
for actual in re.findall(r"'([^']+)' does not depend on any axioms",text):records.append((actual,set()))
for name in os.environ['NAMES'].split():
    matches=[(actual,axioms) for actual,axioms in records if actual==name or actual.endswith('.'+name)]
    assert len(matches)==1,(name,matches)
    actual,axioms=matches[0]
    assert axioms<=allowed,(actual,axioms)
    print(actual,'AXIOMS_PASS')
print('CERTIFICATE_GENESIS_LEAN_QUALIFICATION_PASS')
PY
