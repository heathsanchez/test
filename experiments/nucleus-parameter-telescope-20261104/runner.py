import argparse,importlib.util,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('nat_wave',ROOT.parent/'nucleus-nat-closure-20261104/runner.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N);t=N.t
spec=importlib.util.spec_from_file_location('source_extract',ROOT.parent/'nucleus-inductive-frontier-20261104/extract.py');E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
def materialize(out,candidate):
 k=N.materialize(out,True)
 if candidate:
  patch=ROOT/'record.patch';r=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=out,capture_output=True,timeout=30);(out/'record-patch.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
  with(out/'source.patch').open('a')as f:f.write(patch.read_text())
 dst=k/'tests/fixtures/parameter-telescope';dst.mkdir(parents=True,exist_ok=True)
 for p in Path('/tmp/record-fixtures').glob('*.ndjson'):
  if p.stem!='original':shutil.copy2(p,dst/p.name)
 shutil.copy2(ROOT/'parameter_telescope.rs',k/'tests/parameter_telescope.rs')
 for label in ['parameter-record','homogeneous-pair']:
  shutil.copy2(Path('/tmp/record-fixtures')/('canonical-'+label+'.ndjson'),k/'tests/fixtures'/('good-'+label+'.ndjson'))
 ENUM=ROOT.parent/'nucleus-nullary-enum-20261104'
 if candidate:
  patch=ENUM/'enum.patch';r=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=out,capture_output=True,timeout=30);(out/'enum-patch.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
  with(out/'source.patch').open('a')as f:f.write(patch.read_text())
 dst=k/'tests/fixtures/nullary-enum';dst.mkdir(parents=True,exist_ok=True)
 for p in Path('/tmp/enum-fixtures').glob('*.ndjson'):
  if p.stem!='original':shutil.copy2(p,dst/p.name)
 shutil.copy2(ENUM/'nullary_enum.rs',k/'tests/nullary_enum.rs')
 with(k/'src/checker.rs').open('a')as f:f.write((ENUM/'enum_reductions.rs').read_text())
 return k
def controls(binary,env):
 rows=[]
 for row in json.loads(Path('/tmp/record-fixtures/manifest.json').read_text()):
  p=Path('/tmp/record-fixtures')/row['file'];assert t.digest(p)==row['sha256']
  with p.open('rb')as f:r=t.run_group([str(binary)],stdin=f,capture_output=True,env=env,timeout=180)
  rows.append(dict(**row,rc=r.returncode,pass_=r.returncode==0 if row['expected']==0 else r.returncode in(1,2),stderr=r.stderr.decode(errors='replace')))
 for row in json.loads(Path('/tmp/enum-fixtures/manifest.json').read_text()):
  p=Path('/tmp/enum-fixtures')/row['file'];assert t.digest(p)==row['sha256']
  with p.open('rb')as f:r=t.run_group([str(binary)],stdin=f,capture_output=True,env=env,timeout=180)
  expected=row['native_expected'];passed=r.returncode==expected if expected in(0,2)else r.returncode in(1,2)
  rows.append(dict(**row,rc=r.returncode,pass_=passed,stderr=r.stderr.decode(errors='replace')))
 # Retain all existing Nat and final proof-spine explicit controls.
 for folder,manifest in [(Path('/tmp/nat-fixtures'),json.loads(Path('/tmp/nat-fixtures/manifest.json').read_text())),(N.FINAL/'controls',[dict(file=p.name,expected=0 if p.stem in {'same','proof_last','dependent_proof_last','long_prefix_valid'}else 1)for p in (N.FINAL/'controls').glob('*.ndjson')])]:
  for row in manifest:
   p=folder/row['file']
   with p.open('rb')as f:r=t.run_group([str(binary)],stdin=f,capture_output=True,env=env,timeout=180)
   rows.append(dict(case=str(p.name),rc=r.returncode,pass_=r.returncode==0 if row['expected']==0 else r.returncode in(1,2)))
 return rows
def qualify(out):
 inputs=Path('/tmp/current208');manifest=json.loads((inputs/'inputs-manifest.json').read_text());baseline=nr0=None;state={}
 # Keep the immutable 208 manifest; augment only the native external fixture root.
 extra=inputs/'inputs/good/perf/magma-list-pair-n21.ndjson';extra.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['zstd','-dq','-f',str(ROOT.parent/'nucleus-coverage-evidence-20261104/inputs/magma-list-pair-n21.ndjson.zst'),'-o',str(extra)],check=True)
 assert t.digest(extra)=='b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84'
 for name,candidate in [('baseline',False),('candidate',True)]:
  arm=out/name;k=materialize(arm,candidate);binary,env=t.build(k,arm);assert binary is not None;run=N.runtime(True)
  nr=t.native_suite(k,env|run|{'NUCLEUS_FROZEN196':str(inputs/'inputs')},arm);rows=t.replay(binary,manifest,inputs,run,arm/'verdicts.json')
  with extra.open('rb')as f:r=t.run_group([str(binary)],stdin=f,capture_output=True,env=run,timeout=180)
  extra_result=dict(case='perf/magma-list-pair-n21',input_sha=t.digest(extra),rc=r.returncode,pass_=r.returncode in(0,2))
  if not candidate:t.validate_baseline(rows);baseline=rows;nr0=nr
  regress=[dict(case=a['case'],before=a['rc'],after=b['rc'])for a,b in zip(baseline,rows)if b['rc']not in(b['expected'],2)or(a['rc']!=2 and a['rc']!=b['rc'])]
  info=dict(binary_sha=t.digest(binary),source_patch_sha=t.digest(arm/'source.patch'),configuration={k:v for k,v in run.items()if k.startswith('NUCLEUS_')},native=nr,native_nonregression=N.Q.native_nonregression(nr,nr0),regressions=regress,counts={str(rc):sum(x['rc']==rc for x in rows)for rc in(0,1,2)},extra=extra_result)
  if candidate:
   info['controls']=controls(binary,run);info['qualified']=not regress and info['native_nonregression']and extra_result['pass_']and all(x['pass_']for x in info['controls'])
  state[name]=info;t.write_json(out/'qualification.json',state);shutil.rmtree(arm/'target',ignore_errors=True)
 assert state['candidate']['qualified'],state['candidate']
def full(out):
 source=Path('/tmp/mathlib.ndjson');assert t.digest(source)==t.INPUT_SHA;k=materialize(out/'candidate',True);binary,_=t.build(k,out/'candidate');assert binary is not None
 env=N.runtime(True);env['NUCLEUS_TRACE_DOWNSTREAM']='1';perf=t.probe_perf(out);result=t.measure(binary,source,env,out/'full-input',timeout=5400,perf=perf)
 terminal=re.findall(r'NUCLEUS_DOWNSTREAM:name=(.*?):stage=',(out/'full-input/stderr').read_text());frontier=None
 if terminal and not terminal[-1].startswith('<'):
  path=out/'next-frontier.ndjson';frontier=E.extract(source,path,terminal[-1]);subprocess.run(['zstd','-T0','-3',str(path)],check=True);path.unlink()
 summary=dict(base=t.BASE,harness=os.environ.get('GITHUB_SHA'),binary_sha=t.digest(binary),source_patch_sha=t.digest(out/'candidate/source.patch'),input_sha=t.INPUT_SHA,result=result,complete_mathlib_accept=result['rc']==0,perf_available=perf,next_frontier=frontier,configuration={k:v for k,v in env.items()if k.startswith('NUCLEUS_')});t.write_json(out/'summary.json',summary);print(json.dumps(summary),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['qualify','full']);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);(qualify if a.phase=='qualify'else full)(out)
