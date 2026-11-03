import argparse,importlib.util,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('record_wave',ROOT.parent/'nucleus-parameter-telescope-20261104/runner.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R);t=R.t
BASE_BINARY='730f76f260437bcb01f567202a3af3765639582c94649988aaac6f36aa04e36d'
BASE_PATCH='8ad321253650a994511a9163b911af21f1dbfc08e1c347c07e71545ee4efab29'
def materialize(out,strict):
 k=R.materialize(out,True);assert t.digest(out/'source.patch')==BASE_PATCH
 for name in ['retain.patch']+(['compare.patch']if strict else []):
  patch=ROOT/name;r=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=out,capture_output=True,timeout=30);(out/(name+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0
  with(out/'source.patch').open('a')as f:f.write(patch.read_text())
 dst=k/'tests/fixtures/let-metadata';dst.mkdir(parents=True,exist_ok=True)
 for p in(ROOT.parent/'nucleus-let-metadata-audit-20261104/fixtures').glob('*.ndjson'):shutil.copy2(p,dst/p.name)
 shutil.copy2(ROOT/'let_metadata.rs',k/'tests/let_metadata.rs');return k
def controls(binary,env):
 rows=R.controls(binary,env);ref=json.loads(Path('/tmp/let-oracle/reference.json').read_text())
 assert ref['checker_sha']=='ae92c625e612fff1c90e329344d22e3c3c330383cb335ce28fd41435be3b3b94'and len(ref['rows'])==4
 for row in ref['rows']:
  expected=row['hypothesis'];assert row['parse']['rc']==0 and row['kernel']['rc']==expected
  p=ROOT.parent/'nucleus-let-metadata-audit-20261104/fixtures'/row['file'];assert t.digest(p)==row['sha256']
  with p.open('rb')as f:r=t.run_group([str(binary)],stdin=f,capture_output=True,env=env,timeout=60)
  rows.append(dict(file='let/'+row['file'],sha256=row['sha256'],expected=expected,rc=r.returncode,pass_=r.returncode==0 if expected==0 else r.returncode in(1,2)))
 return rows
def native_against_reused(candidate,baseline):
 key='let_metadata|test';assert key in candidate['targets']and key not in baseline['targets']
 added=candidate['targets'][key]
 if not added['complete']or added['failures']or added['counts']!=[4,0,0,0,0]:return False
 old=dict(candidate,targets={k:v for k,v in candidate['targets'].items()if k!=key})
 return R.N.Q.native_nonregression(old,baseline)
def qualify(out):
 shutil.copy2('/tmp/let-oracle/reference.json',out/'oracle-reference.json')
 prior=Path('/tmp/let-baseline');base=json.loads((prior/'qualification.json').read_text())['candidate']
 assert base['qualified']and base['binary_sha']==BASE_BINARY and base['source_patch_sha']==BASE_PATCH
 assert t.digest(prior/'candidate/nucleus')==BASE_BINARY and t.digest(prior/'candidate/source.patch')==BASE_PATCH
 run=R.N.runtime(True);assert {k:v for k,v in run.items()if k.startswith('NUCLEUS_')}==base['configuration']
 # Re-execute only the new target for RED. Old41-target receipts are reused.
 arm=out/'candidate';k=materialize(arm,False);binary,env=t.build(k,arm);assert binary is not None
 red=t.run_group(['cargo','test','--release','--locked','--manifest-path',str(k/'Cargo.toml'),'--test','let_metadata','--','--nocapture'],env=env|run,capture_output=True,timeout=600)
 raw=(red.stdout+red.stderr).decode(errors='replace');(out/'red.log').write_text(raw)
 assert red.returncode==101 and 'dependency_mismatches_cannot_grant_recursor_authority'in raw and '3 passed; 1 failed; 0 ignored'in raw,raw
 patch=ROOT/'compare.patch';r=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30);(arm/'compare.patch.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
 with(arm/'source.patch').open('a')as f:f.write(patch.read_text())
 binary,env=t.build(k,arm);assert binary is not None
 inputs=Path('/tmp/current208');extra=inputs/'inputs/good/perf/magma-list-pair-n21.ndjson';extra.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['zstd','-dq','-f',str(ROOT.parent/'nucleus-coverage-evidence-20261104/inputs/magma-list-pair-n21.ndjson.zst'),'-o',str(extra)],check=True);assert t.digest(extra)==base['extra']['input_sha']
 nr=t.native_suite(k,env|run|{'NUCLEUS_FROZEN196':str(inputs/'inputs')},arm)
 rows=t.replay(binary,json.loads((inputs/'inputs-manifest.json').read_text()),inputs,run,arm/'verdicts.json');old=json.loads((prior/'candidate/verdicts.json').read_text());assert len(rows)==len(old)==208;diff=[]
 for a,b in zip(old,rows):
  assert a['case']==b['case']and a['sha256']==b['sha256']
  if a['rc']!=b['rc']:diff.append(dict(case=a['case'],before=a['rc'],after=b['rc']))
 with extra.open('rb')as f:r=t.run_group([str(binary)],stdin=f,capture_output=True,env=run,timeout=180)
 extra_result=dict(case=base['extra']['case'],input_sha=t.digest(extra),rc=r.returncode,unchanged=r.returncode==base['extra']['rc'])
 cs=controls(binary,run);nonreg=native_against_reused(nr,base['native'])
 info=dict(binary_sha=t.digest(binary),source_patch_sha=t.digest(arm/'source.patch'),configuration=base['configuration'],native=nr,native_nonregression=nonreg,verdict_changes=diff,extra=extra_result,controls=cs,baseline_artifact=13258536280,baseline_evidence_reused=True,baseline_source_patch=BASE_PATCH,baseline_binary=BASE_BINARY,oracle_artifact=13261917242,harness=os.environ.get('GITHUB_SHA'))
 info['qualified']=nonreg and not diff and extra_result['unchanged']and len(cs)==61 and all(x['pass_']for x in cs)
 t.write_json(out/'qualification.json',dict(candidate=info));assert info['qualified'],info;shutil.rmtree(arm/'target',ignore_errors=True)
def full(out):
 prior=Path('/tmp/let-qualified');info=json.loads((prior/'qualification.json').read_text())['candidate'];assert info['qualified'];binary=prior/'candidate/nucleus';assert t.digest(binary)==info['binary_sha'];binary.chmod(0o755)
 source=Path('/tmp/mathlib.ndjson');assert t.digest(source)==t.INPUT_SHA;env=R.N.runtime(True);assert {k:v for k,v in env.items()if k.startswith('NUCLEUS_')}==info['configuration'];env['NUCLEUS_TRACE_DOWNSTREAM']='1'
 result=t.measure(binary,source,env,out/'full-input',timeout=5400,perf=False)
 import re
 trace=re.findall(r'NUCLEUS_DOWNSTREAM:name=(.*?):stage=',(out/'full-input/stderr').read_text());frontier=None
 if trace and not trace[-1].startswith('<'):
  p=out/'next-frontier.ndjson';frontier=R.E.extract(source,p,trace[-1]);subprocess.run(['zstd','-T0','-3',str(p)],check=True);p.unlink()
 summary=dict(binary_sha=t.digest(binary),source_patch_sha=info['source_patch_sha'],input_sha=t.INPUT_SHA,result=result,complete_mathlib_accept=result['rc']==0,next_frontier=frontier,qualified_binary_reused=True,configuration=info['configuration'],harness=os.environ.get('GITHUB_SHA'));t.write_json(out/'summary.json',summary);print(json.dumps(summary),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['qualify','full']);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);(qualify if a.phase=='qualify'else full)(out)
