#!/usr/bin/env bash
set -euo pipefail
AUDIT="$GITHUB_WORKSPACE/audit/audits/cross_domain"
EVIDENCE="$GITHUB_WORKSPACE/evidence"
mkdir -p "$EVIDENCE"
test "$(git rev-parse HEAD)" = "$EXPECTED_REF"
git rev-parse HEAD > "$EVIDENCE/source-commit.txt"
cp lean-toolchain "$EVIDENCE/source-toolchain.txt"
cp lake-manifest.json "$EVIDENCE/source-manifest.json"
case "$TASK" in
  minimum|polar-transfer)
    if [ "$SOURCE" = openai ]; then
      test "$(git hash-object NavierStokes/PolarCharts.lean)" = 93e1a3ed3b300512a4bb5a27c45b838e57e371b5
    fi ;;
  source-check)
    test "$(git hash-object EulerBlowup/Elementary.lean)" = 5814b45a6fc141985c5bc59a7152ef98f8c0c6e6 ;;
esac
curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -o /tmp/elan-init.sh
sh /tmp/elan-init.sh -y --default-toolchain none
export PATH="$HOME/.elan/bin:$PATH"
elan toolchain install "$(cat lean-toolchain)"
elan default "$(cat lean-toolchain)"
lean --version | tee "$EVIDENCE/source-lean-version.txt"
if lake exe cache get > "$EVIDENCE/cache-first.log" 2>&1; then
  echo SOURCE_TOOLCHAIN_CACHE=PASS | tee "$EVIDENCE/cache-status.txt"
else
  cat "$EVIDENCE/cache-first.log"
  grep -q 'Dependency Mathlib uses a different lean-toolchain' "$EVIDENCE/cache-first.log"
  test -f .lake/packages/mathlib/lean-toolchain
  git -C .lake/packages/mathlib rev-parse HEAD | tee "$EVIDENCE/mathlib-commit.txt"
  cp .lake/packages/mathlib/lean-toolchain "$EVIDENCE/runtime-toolchain.txt"
  cp .lake/packages/mathlib/lean-toolchain lean-toolchain
  elan toolchain install "$(cat lean-toolchain)"
  elan default "$(cat lean-toolchain)"
  echo MATHLIB_CACHE_COMPATIBILITY_REPLAY | tee "$EVIDENCE/cache-status.txt"
  lake exe cache get > "$EVIDENCE/cache.log" 2>&1
fi
lean --version | tee "$EVIDENCE/runtime-lean-version.txt"
test "$(git rev-parse HEAD)" = "$EXPECTED_REF"
git -C .lake/packages/mathlib rev-parse HEAD | tee "$EVIDENCE/mathlib-commit.txt"

# Lake supplies the upstream dependency paths; the additional directory
# contains only independently compiled MathGraph audit modules.
run_audit() {
  lake env bash -c 'export LEAN_PATH="$1:$LEAN_PATH"; shift; exec lean "$@"' bash "$AUDIT" "$@"
}

case "$TASK" in
  minimum)
    run_audit -o "$AUDIT/RankOneStress.olean" "$AUDIT/RankOneStress.lean" > "$EVIDENCE/rank-one.log" 2>&1
    run_audit "$AUDIT/Minimum.lean" > "$EVIDENCE/lean.log" 2>&1
    NAMES='CrossDomainResidual.Minimum.minimum_two' ;;
  source-check)
    lake build EulerBlowup.Elementary > "$EVIDENCE/source-build.log" 2>&1
    run_audit -o "$AUDIT/ABAngleBounds.olean" "$AUDIT/ABAngleBounds.lean" > "$EVIDENCE/extraction.log" 2>&1
    run_audit "$AUDIT/SourceCapabilityCheck.lean" > "$EVIDENCE/lean.log" 2>&1
    NAMES='CrossDomainResidual.SourceCapabilityCheck.source_tilt_replay CrossDomainResidual.SourceCapabilityCheck.extracted_tilt_replay' ;;
  polar-transfer)
    lake build NavierStokes.PolarCharts > "$EVIDENCE/source-build.log" 2>&1
    run_audit -o "$AUDIT/ABAngleBounds.olean" "$AUDIT/ABAngleBounds.lean" > "$EVIDENCE/extraction.log" 2>&1
    run_audit "$AUDIT/PolarChartTransfer.lean" > "$EVIDENCE/lean.log" 2>&1
    NAMES='CrossDomainResidual.PolarChartTransfer.baseChart_angle_bounds CrossDomainResidual.PolarChartTransfer.localChart_angle_bounds' ;;
  *) echo "Unknown task: $TASK" >&2; exit 2 ;;
esac
cat "$EVIDENCE/lean.log"
NAMES="$NAMES" python - <<'PY'
import os, pathlib, re
text=(pathlib.Path(os.environ['GITHUB_WORKSPACE'])/'evidence/lean.log').read_text()
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
print('LEAN_QUALIFICATION_PASS')
PY
sha256sum "$AUDIT/RankOneStress.lean" "$AUDIT/Minimum.lean" "$AUDIT/ABAngleBounds.lean" "$AUDIT/PolarChartTransfer.lean" "$AUDIT/SourceCapabilityCheck.lean" > "$EVIDENCE/audit-source-hashes.txt"
