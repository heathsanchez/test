import importlib.util,json,os,subprocess,shutil
from pathlib import Path
from observer import apply
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('let_wave',ROOT.parent/'nucleus-let-preservation-20261104/runner.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L);R=L.R;t=L.t
out=Path('/tmp/range-scoped');out.mkdir(exist_ok=True);prior=Path('/tmp/scoped-qualified');q=json.loads((prior/'qualification.json').read_text())['candidate'];assert q['qualified']
plain=prior/'candidate/nucleus';assert t.digest(plain)=='4cd1c0c95147ea5423b73af5ae7e8d1e265a7d5a7b799d0bcb10a1bc30483fb3';plain.chmod(0o755)
arm=out/'source';k=L.materialize(arm,True);patch=ROOT.parent/'nucleus-let-index-stack-20261104/owner-index.patch';r=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30);assert r.returncode==0
with(arm/'source.patch').open('a')as f:f.write(patch.read_text())
assert t.digest(arm/'source.patch')==q['source_patch_sha']=='9d55735a77d69febdfb0b3d02ee1d5d29bb98011c9e534c17e25ca0f661bbfaa'
source=Path('/tmp/range-prefix.ndjson');assert t.digest(source)=='d9d7b1fe7267a0806f65200abc64a9c7114fb8097a9da1f3687f2560a2568bb9'
run=R.N.runtime(True);run['NUCLEUS_TRACE_DOWNSTREAM']='1'
with source.open('rb')as f:r=t.run_group([str(plain)],stdin=f,capture_output=True,env=run,timeout=180)
(out/'plain.stderr').write_bytes(r.stderr);assert r.returncode==2
apply(k,out);env=dict(os.environ,CARGO_TARGET_DIR=str(arm/'target'));build=t.run_group(['cargo','build','--release','--locked','--features','diagnostics','--manifest-path',str(k/'Cargo.toml')],env=env,capture_output=True,timeout=600);(out/'build.log').write_bytes(build.stdout+build.stderr);assert build.returncode==0
binary=arm/'target/release/metatron-kernel';assert b'METATRON_KERNEL_DIAGNOSTICS'in binary.read_bytes()
flags={'METATRON_KERNEL_DIAGNOSTICS':'1','NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE':'1','NUCLEUS_TRACE_DEPENDENCY_GAP':'1','NUCLEUS_TRACE_DEPENDENCY_VALUES':'1','NUCLEUS_TRACE_APP_DOMAIN_OBLIGATION':'1','NUCLEUS_TRACE_ONLY_DECLARATION':"_private.Init.Data.List.Nat.Range.0.List.pairwise_lt_range'._proof_1_4"}
with source.open('rb')as f,(out/'trace.stdout').open('wb')as stdout,(out/'trace.stderr').open('wb')as stderr:r=t.run_group([str(binary)],stdin=f,stdout=stdout,stderr=stderr,env=run|flags,timeout=240)
lines=(out/'trace.stderr').read_text(errors='replace').splitlines();terminal=[x for x in lines if x.startswith('NUCLEUS_DOWNSTREAM:')];gaps=[x for x in lines if x.startswith('NUCLEUS_DEPENDENCY_GAP:')];summary=dict(source_sha=t.digest(source),production_binary=t.digest(plain),diagnostic_binary=t.digest(binary),source_patch_sha=q['source_patch_sha'],observer_patch_sha=t.digest(out/'observer.patch'),plain_rc=2,traced_rc=r.returncode,terminal=terminal[-1:],gaps=gaps,reference_reused=13264820032,scope='Current qualified indexed Bool-layout source; diagnostic observer only, no semantic promotion')
t.write_json(out/'summary.json',summary);print(json.dumps(summary),flush=True);assert r.returncode==2 and terminal and 'pairwise_lt_range' in terminal[-1];shutil.rmtree(arm/'target',ignore_errors=True)
