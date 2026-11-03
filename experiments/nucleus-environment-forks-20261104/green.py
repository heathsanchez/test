"""Isolated environment module GREEN, restored from an exact source bundle."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parent
PRIOR=Path('/tmp/envfork-red')
OUT=Path('/tmp/nucleus-environment-fork-green')
OUT.mkdir(exist_ok=True)
report=json.loads((PRIOR/'report.json').read_text())
assert report['expected_red'] and report['rc']==101
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(PRIOR/'qualified-source.tar.gz')==report['source_bundle_sha256']=='71cf6f028111109cc6361cf44b1d91a3e5f26a098e0c9737c20b3ff3325d4c9d'
assert digest(PRIOR/'source-manifest.json')==report['source_manifest_sha256']
work=Path('/tmp/envfork-green-source')
with tarfile.open(PRIOR/'qualified-source.tar.gz')as archive:
    archive.extractall(work,filter='data')
kernel=work/'metatron-kernel'
manifest=json.loads((PRIOR/'source-manifest.json').read_text())
for name,sha in manifest.items():
    path=PurePosixPath(name)
    assert not path.is_absolute()and '..'not in path.parts
    assert digest(kernel/name)==sha,name
patched=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(ROOT/'forked-constants.patch')],cwd=work,capture_output=True,timeout=30)
(OUT/'patch.log').write_bytes(patched.stdout+patched.stderr)
assert patched.returncode==0,(patched.stdout,patched.stderr)
command=['cargo','test','--locked','--manifest-path',str(kernel/'Cargo.toml'),'--lib','environment::owned_append_tests','--','--nocapture']
result=subprocess.run(command,capture_output=True,env=dict(os.environ,CARGO_TARGET_DIR='/tmp/envfork-green-target'),timeout=600)
(OUT/'stdout').write_bytes(result.stdout)
(OUT/'stderr').write_bytes(result.stderr)
passed=result.returncode==0 and b'6 passed; 0 failed;'in result.stdout
output=dict(status='GREEN_ENVIRONMENT_MODULE_ONLY'if passed else 'REJECTED_OR_APPARATUS_FAILURE',
    baseline_binary='582dd0ac17d664202a39ee7daa69b640f33916374fc44dbefdc96a37e8bcb238',
    baseline_source_bundle=report['source_bundle_sha256'],patch_sha256=digest(ROOT/'forked-constants.patch'),
    rc=result.returncode,owned_environment_tests=6,full_kernel_qualification='NOT_RUN',performance='NOT_RUN')
(OUT/'report.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output),flush=True)
assert passed
