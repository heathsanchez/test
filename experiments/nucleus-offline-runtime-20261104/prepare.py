"""Seal a portable pinned Rust runtime and public locked dependency cache."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

OUT=Path('/tmp/nucleus-offline-runtime');OUT.mkdir(exist_ok=True)
parent=Path('/tmp/qualified-stack');source=Path('/tmp/nucleus-runtime-source');source.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(parent/'candidate/source.tar.gz')=='43418750f5972fc8ffe4451c3f0b63270f01d7f00ff29ac1bd68f88261b99fff'
with tarfile.open(parent/'candidate/source.tar.gz')as a:a.extractall(source,filter='data')
kernel=source/'metatron-kernel'
for name,digest in json.loads((parent/'candidate/source-manifest.json').read_text()).items():assert sha(kernel/name)==digest
sysroot=Path(subprocess.check_output(['rustc','--print','sysroot'],text=True).strip())
stage=OUT/'bundle';(stage/'toolchain/bin').mkdir(parents=True)
for name in ['rustc','cargo','rustdoc']:shutil.copy2(sysroot/'bin'/name,stage/'toolchain/bin'/name)
shutil.copytree(sysroot/'lib',stage/'toolchain/lib',symlinks=True)
env={k:v for k,v in os.environ.items()if k not in('GH_TOKEN','GITHUB_TOKEN')and not k.startswith('NUCLEUS_')}
env.update(CARGO_HOME=str(stage/'cargo-home'),RUSTC=str(stage/'toolchain/bin/rustc'),RUSTDOC=str(stage/'toolchain/bin/rustdoc'),CARGO_TARGET_DIR='/tmp/nucleus-runtime-target')
env['PATH']=str(stage/'toolchain/bin')+os.pathsep+env['PATH']
fetch=subprocess.run([str(stage/'toolchain/bin/cargo'),'fetch','--locked','--manifest-path',str(kernel/'Cargo.toml')],cwd=kernel,env=env,capture_output=True,timeout=300)
(OUT/'fetch.log').write_bytes(fetch.stdout+fetch.stderr);assert fetch.returncode==0
build=subprocess.run([str(stage/'toolchain/bin/cargo'),'build','--release','--locked','--offline','--manifest-path',str(kernel/'Cargo.toml')],cwd=kernel,env=env,capture_output=True,timeout=600)
(OUT/'build.log').write_bytes(build.stdout+build.stderr);assert build.returncode==0
binary=Path(env['CARGO_TARGET_DIR'])/'release/metatron-kernel';expected='a1d903c6ddf1219a7202db87f14ac3de82a344383501251c928a2a19683e621f'
rows=[]
fixtures=Path(__file__).resolve().parent.parent/'nucleus-universe-reconcile-20261104/inputs'
configuration=json.loads((parent/'qualification.json').read_text())['candidate']['configuration']
for case in json.loads((fixtures/'manifest.json').read_text()):
    source_case=fixtures/case['file'];assert sha(source_case)==case['sha256']
    with source_case.open('rb')as stream:result=subprocess.run([str(binary)],stdin=stream,capture_output=True,env=configuration,timeout=30)
    assert result.returncode==0 if case['expect_reference']==0 else result.returncode in(1,2)
    rows.append(dict(case=case['case'],source_sha=case['sha256'],rc=result.returncode,expected=case['expect_reference']))
exact=sha(binary)==expected
included=lambda p:str(p.relative_to(stage)).startswith(('toolchain/','cargo-home/registry/'))
files={str(p.relative_to(stage)):sha(p)for p in stage.rglob('*')if p.is_file()and not p.is_symlink()and included(p)}
links={str(p.relative_to(stage)):os.readlink(p)for p in stage.rglob('*')if p.is_symlink()and included(p)}
for name,target in links.items():
 resolved=(stage/name).resolve();assert resolved.is_relative_to(stage.resolve()),(name,target)
manifest=dict(status='WARRANTED_EXACT_OFFLINE_REBUILD'if exact else'WARRANTED_OFFLINE_BUILD_AND_THREE_CONTROLS',exact_qualified_binary_match=exact,controls=rows,no_broad_kernel_qualification_without_exact_binary=not exact,rustc=subprocess.check_output([str(stage/'toolchain/bin/rustc'),'-Vv'],text=True,env=env),cargo=subprocess.check_output([str(stage/'toolchain/bin/cargo'),'-V'],text=True,env=env),qualified_source_run=41749654779,qualified_binary=expected,offline_rebuilt_binary=sha(binary),cargo_lock_sha=sha(kernel/'Cargo.lock'),files=files,symlinks=links)
(OUT/'runtime-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Only the toolchain and isolated public registry enter the portable bundle.
with tarfile.open(OUT/'rust-runtime.tar.gz','w:gz')as a:
 a.add(stage/'toolchain',arcname='toolchain');a.add(stage/'cargo-home/registry',arcname='cargo-home/registry')
assert(OUT/'rust-runtime.tar.gz').stat().st_size<500*1024*1024
print(json.dumps(dict(status=manifest['status'],runtime_archive_sha=sha(OUT/'rust-runtime.tar.gz'),bytes=(OUT/'rust-runtime.tar.gz').stat().st_size,qualified_binary=expected)))
