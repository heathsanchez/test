import importlib.util,json,os,shutil,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('let_wave',ROOT.parent/'nucleus-let-preservation-20261104/runner.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L);R=L.R;t=L.t
out=Path('/tmp/range-cache');out.mkdir(exist_ok=True)
prior=Path('/tmp/scoped-qualified');q=json.loads((prior/'qualification.json').read_text())['candidate'];assert q['qualified'];plain=prior/'candidate/nucleus';assert t.digest(plain)=='4cd1c0c95147ea5423b73af5ae7e8d1e265a7d5a7b799d0bcb10a1bc30483fb3';plain.chmod(0o755)
arm=out/'base-source';k=L.materialize(arm,True);patch=ROOT.parent/'nucleus-let-index-stack-20261104/owner-index.patch';r=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30);assert r.returncode==0
with(arm/'source.patch').open('a')as f:f.write(patch.read_text())
assert t.digest(arm/'source.patch')==q['source_patch_sha']=='9d55735a77d69febdfb0b3d02ee1d5d29bb98011c9e534c17e25ca0f661bbfaa'
source=Path('/tmp/range-prefix.ndjson');assert t.digest(source)=='d9d7b1fe7267a0806f65200abc64a9c7114fb8097a9da1f3687f2560a2568bb9'
run=R.N.runtime(True);run['NUCLEUS_TRACE_DOWNSTREAM']='1';reports=[]
def observe(label,binary):
 directory=out/label;directory.mkdir(exist_ok=True);m=t.measure(binary,source,run,directory,timeout=240,perf=False)
 lines=(directory/'stderr').read_text(errors='replace').splitlines();terminal=[x for x in lines if x.startswith('NUCLEUS_DOWNSTREAM:')];return dict(result=m,terminal=terminal[-1:],binary_sha=t.digest(binary))
reports.append(dict(arm='baseline',**observe('baseline',plain)));assert reports[-1]['result']['rc']==2
# Hypothesis: a suspended projection is retained as completed exposure/replay,
# preventing a later constructor demand. Cache omission grants no new rule.
for label,exposure,replay,budget in [('exposure',True,False,65536),('replay',False,True,65536),('both',True,True,65536),('budget4x',False,False,262144)]:
 directory=out/label;directory.mkdir(exist_ok=True);kernel=directory/'metatron-kernel';shutil.copytree(k,kernel);patches=[]
 for path in ['src/machine.rs','src/checker.rs']:
  p=kernel/path;before=p.read_text();s=before
  if path=='src/machine.rs':
   if exposure:
    needle='    fn unfinished_native_capture(&self,value:&Value)->bool {';assert s.count(needle)==1;s=s.replace(needle,needle+'\n        if matches!(value,Value::StuckProjection{..}) {return true;}')
   if replay:
    needle='    fn cache_completed_replay(&self,key:Rc<ReplayKey>,value:&Value) {';assert s.count(needle)==1;s=s.replace(needle,needle+'\n        if matches!(value,Value::StuckProjection{..}) {return;}')
  elif budget!=65536:
   needle='judgment_steps: 65_536,';assert s.count(needle)==1;s=s.replace(needle,'judgment_steps: 262_144,')
  p.write_text(s);patches.append(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile='a/metatron-kernel/'+path,tofile='b/metatron-kernel/'+path)))
 (directory/'candidate.patch').write_text(''.join(patches));(directory/'source.patch').write_text((arm/'source.patch').read_text()+''.join(patches))
 env=dict(os.environ,CARGO_TARGET_DIR=str(out/'shared-target'));b=t.run_group(['cargo','build','--release','--locked','--features','diagnostics','--manifest-path',str(kernel/'Cargo.toml')],env=env,capture_output=True,timeout=600);(directory/'build.log').write_bytes(b.stdout+b.stderr)
 if b.returncode!=0:
  reports.append(dict(arm=label,build_rc=b.returncode));t.write_json(out/'screen.json',reports);continue
 binary=directory/'nucleus';shutil.copy2(out/'shared-target/release/metatron-kernel',binary)
 native=t.run_group(['cargo','test','--release','--locked','--lib','--manifest-path',str(kernel/'Cargo.toml')],env=env|run,capture_output=True,timeout=240);(directory/'native-lib.log').write_bytes(native.stdout+native.stderr)
 report=dict(arm=label,native_lib_rc=native.returncode,source_patch_sha=t.digest(directory/'source.patch'),**observe(label,binary));reports.append(report);t.write_json(out/'screen.json',dict(arms=reports,reference_reused=13264820032,source_sha=t.digest(source),scope='Causal source-prefix screen only; fresh complete qualification required before any promotion'))
 print(json.dumps(report),flush=True)
shutil.rmtree(out/'shared-target',ignore_errors=True)
