"""Expected RED: staged signature forks still copy the checked constants map."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import importlib.util
import tarfile

ROOT=Path(__file__).resolve().parent
OUT=Path('/tmp/nucleus-environment-fork-red')
OUT.mkdir(exist_ok=True)
baseline=Path('/tmp/ac-qualified/candidate/source.patch')
assert hashlib.sha256(baseline.read_bytes()).hexdigest()=='c25db576b5b52ed6e76711b9e83e66731bd40c68b7aa6627d45ad751c769ba69'
spec=importlib.util.spec_from_file_location('qualified_delta',ROOT.parent/'nucleus-beq-neutral-delta-20261104/qualify.py')
Q=importlib.util.module_from_spec(spec)
spec.loader.exec_module(Q)
Q.OUT=Path('/tmp/envfork-materialized')
Q.OUT.mkdir(exist_ok=True)
prior=json.loads(Path('/tmp/dense-qualified/qualification.json').read_text())['candidate']
original=Q.D.patch_source
def qualified_source(kernel,arm):
    original(kernel,arm)
    assert Q.t.digest(arm/'source.patch')=='a788f92fd0471f1dc20cce9f42f8c94f9e3309ea1becb1da1ecd88aa5a9b58a6'
    for patch in(ROOT.parent/'nucleus-k-canonical-20261104/k-canonical.patch',ROOT.parent/'nucleus-ac-sort-20261104/sort-carrier.patch'):
        result=Q.t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30)
        assert result.returncode==0,(result.stdout,result.stderr)
        with(arm/'source.patch').open('a')as stream:stream.write(patch.read_text())
Q.D.patch_source=qualified_source
try:
    source,binary,build_env,arm=Q.source_qualified_candidate(prior)
finally:
    Q.D.patch_source=original
assert Q.t.digest(arm/'source.patch')==Q.t.digest(baseline)
assert Q.t.digest(binary)=='582dd0ac17d664202a39ee7daa69b640f33916374fc44dbefdc96a37e8bcb238'
# Capture generated files and Cargo.lock as well as the recorded patches.
files=sorted(p for p in source.rglob('*')if p.is_file()and 'target'not in p.relative_to(source).parts)
manifest={str(p.relative_to(source)):Q.t.digest(p)for p in files}
(OUT/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with tarfile.open(OUT/'qualified-source.tar.gz','w:gz',dereference=True)as archive:
    for p in files:archive.add(p,arcname='metatron-kernel/'+str(p.relative_to(source)))
patched=Q.t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(ROOT/'red-test.patch')],cwd=arm,capture_output=True,timeout=30)
assert patched.returncode==0,(patched.stdout,patched.stderr)
test='environment::owned_append_tests::staged_branch_reuses_checked_constant_root_after_snapshot_drop'
command=['cargo','test','--manifest-path',str(source/'Cargo.toml'),'--lib',test,'--','--exact','--nocapture']
result=subprocess.run(command,capture_output=True,env=build_env,timeout=600)
(OUT/'stdout').write_bytes(result.stdout)
(OUT/'stderr').write_bytes(result.stderr)
log=result.stdout+result.stderr
expected=(result.returncode==101 and b'0 passed; 1 failed;'in log
    and b'staged signature fork should reuse the checked root'in log)
report=dict(status='EXPECTED_RED_CONFIRMED'if expected else 'APPARATUS_OR_HYPOTHESIS_FAILURE',
    baseline_source_patch_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
    reproduced_binary_sha256=Q.t.digest(binary),
    source_bundle_sha256=Q.t.digest(OUT/'qualified-source.tar.gz'),
    source_manifest_sha256=Q.t.digest(OUT/'source-manifest.json'),
    environment_with_test_sha256=hashlib.sha256((source/'src/environment.rs').read_bytes()).hexdigest(),
    test_patch_sha256=hashlib.sha256((ROOT/'red-test.patch').read_bytes()).hexdigest(),
    test=test,rc=result.returncode,expected_red=expected,no_performance_claim=True)
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
assert expected,'Require actual assertion RED, not a compilation or fixture failure'
