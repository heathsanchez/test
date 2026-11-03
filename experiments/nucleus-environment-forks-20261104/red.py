"""Expected RED: staged signature forks still copy the checked constants map."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent
OUT=Path('/tmp/nucleus-environment-fork-red')
OUT.mkdir(exist_ok=True)
source=Path('/tmp/envfork-baseline/metatron-kernel')
baseline=Path('/tmp/ac-qualified/candidate/source.patch')
assert hashlib.sha256(baseline.read_bytes()).hexdigest()=='c25db576b5b52ed6e76711b9e83e66731bd40c68b7aa6627d45ad751c769ba69'
test='environment::owned_append_tests::staged_branch_reuses_checked_constant_root_after_snapshot_drop'
command=['cargo','test','--manifest-path',str(source/'Cargo.toml'),'--lib',test,'--','--exact','--nocapture']
result=subprocess.run(command,capture_output=True,env=dict(os.environ,CARGO_TARGET_DIR='/tmp/envfork-red-target'),timeout=600)
(OUT/'stdout').write_bytes(result.stdout)
(OUT/'stderr').write_bytes(result.stderr)
log=result.stdout+result.stderr
expected=(result.returncode==101 and b'0 passed; 1 failed;'in log
    and b'staged signature fork should reuse the checked root'in log)
report=dict(status='EXPECTED_RED_CONFIRMED'if expected else 'APPARATUS_OR_HYPOTHESIS_FAILURE',
    baseline_source_patch_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
    environment_with_test_sha256=hashlib.sha256((source/'src/environment.rs').read_bytes()).hexdigest(),
    test_patch_sha256=hashlib.sha256((ROOT/'red-test.patch').read_bytes()).hexdigest(),
    test=test,rc=result.returncode,expected_red=expected,no_performance_claim=True)
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
assert expected,'Require actual assertion RED, not a compilation or fixture failure'
