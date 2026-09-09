#!/usr/bin/env bash
set -euo pipefail
BASE="$GITHUB_WORKSPACE/audit/audits/procedure_repair/run_procedure_lean.sh"
PROGRAM="$GITHUB_WORKSPACE/audit/audits/procedure_composition/ProgramRules.lean"
test "$(git -C "$GITHUB_WORKSPACE/audit" hash-object audits/procedure_repair/run_procedure_lean.sh)" = aa6efd2913091710d4b383948596319f9c0328b3
python - "$BASE" "$PROGRAM" <<'PY'
import pathlib,sys
text=pathlib.Path(sys.argv[1]).read_text()
needle='run_audit -o "$BUILD/ProcedureRules.olean" "$BUILD/ProcedureRules.lean" > "$EVIDENCE/soundness.log" 2>&1'
addition='\ncp '+repr(sys.argv[2])+' "$BUILD/ProgramRules.lean"\nrun_audit -o "$BUILD/ProgramRules.olean" "$BUILD/ProgramRules.lean" > "$EVIDENCE/program-soundness.log" 2>&1'
assert text.count(needle)==1
text=text.replace(needle,needle+addition)
needle2='if [ "$TASK" != soundness ]; then\n  run_audit -o "$BUILD/RecoveredProcedures.olean"'
assert text.count(needle2)==1
text=text.replace(needle2,'NAMES="$NAMES CrossDomainResidual.ProgramRules.sound"\n'+needle2)
text=text.replace('cat "$EVIDENCE/soundness.log"','cat "$EVIDENCE/soundness.log"\ncat "$EVIDENCE/program-soundness.log"')
pathlib.Path('/tmp/mathgraph-transfer-run.sh').write_text(text)
PY
bash /tmp/mathgraph-transfer-run.sh
