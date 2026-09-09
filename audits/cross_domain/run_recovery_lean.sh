#!/usr/bin/env bash
set -euo pipefail
AUDIT="$GITHUB_WORKSPACE/audit/audits/cross_domain"
EVIDENCE="$GITHUB_WORKSPACE/evidence"
AUDIT_BUILD="$PWD/.mathgraph-recovery"
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
# The generated source is the immutable finite-job artifact, not a new synthesis.
test -s "$GITHUB_WORKSPACE/recovered/RecoveredLower.lean"
cp "$GITHUB_WORKSPACE/recovered/RecoveredLower.lean" "$AUDIT_BUILD/RecoveredLower.lean"
cp "$GITHUB_WORKSPACE/recovered/certificate.json" "$EVIDENCE/certificate.json"
sha256sum "$AUDIT_BUILD/RecoveredLower.lean" > "$EVIDENCE/generated-source-hash.txt"
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
# The compiler requires source files inside the project root. Only the
# private audit module directory is added; Lake retains its dependency paths.
run_audit() {
  lake env bash -c 'export LEAN_PATH="$1:$LEAN_PATH"; shift; exec lean "$@"' bash "$AUDIT_BUILD" "$@"
}
run_audit -o "$AUDIT_BUILD/RecoveredLower.olean" "$AUDIT_BUILD/RecoveredLower.lean" > "$EVIDENCE/recovered-lower.log" 2>&1
if [ "$TASK" = target ]; then
  lake build NavierStokes.PolarCharts > "$EVIDENCE/source-build.log" 2>&1
  cp "$AUDIT/KnownUpper.lean" "$AUDIT_BUILD/KnownUpper.lean"
  cp "$AUDIT/RecoveredPolarTransfer.lean" "$AUDIT_BUILD/RecoveredPolarTransfer.lean"
  run_audit -o "$AUDIT_BUILD/KnownUpper.olean" "$AUDIT_BUILD/KnownUpper.lean" > "$EVIDENCE/known-upper.log" 2>&1
  run_audit "$AUDIT_BUILD/RecoveredPolarTransfer.lean" > "$EVIDENCE/lean.log" 2>&1
  NAMES='CrossDomainResidual.RecoveredLower.recovered_arctan_lower CrossDomainResidual.RecoveredPolarTransfer.baseChart_angle_bounds CrossDomainResidual.RecoveredPolarTransfer.localChart_angle_bounds'
else
  lake build EulerBlowup.Elementary > "$EVIDENCE/source-build.log" 2>&1
  cp "$AUDIT/RecoveredSourceCheck.lean" "$AUDIT_BUILD/RecoveredSourceCheck.lean"
  run_audit "$AUDIT_BUILD/RecoveredSourceCheck.lean" > "$EVIDENCE/lean.log" 2>&1
  NAMES='CrossDomainResidual.RecoveredLower.recovered_arctan_lower CrossDomainResidual.RecoveredSourceCheck.recovered_implies_source CrossDomainResidual.RecoveredSourceCheck.source_implies_recovered'
fi
cat "$EVIDENCE/recovered-lower.log" "$EVIDENCE/lean.log"
NAMES="$NAMES" python - <<'PY'
import os,pathlib,re
root=pathlib.Path(os.environ['GITHUB_WORKSPACE'])/'evidence'
text=(root/'recovered-lower.log').read_text()+'\n'+(root/'lean.log').read_text()
allowed={'propext','Quot.sound','Classical.choice'}
for name in os.environ['NAMES'].split():
    pattern=r"'"+re.escape(name)+r"' depends on axioms: \[([^\]]*)\]"
    match=re.search(pattern,text)
    if match:
        axioms={x.strip() for x in match.group(1).split(',') if x.strip()}
        assert axioms <= allowed,(name,axioms)
    else:
        assert re.search(r"'"+re.escape(name)+r"' does not depend on any axioms",text),name
    print(name,'AXIOMS_PASS')
print('RECOVERY_LEAN_QUALIFICATION_PASS')
PY
