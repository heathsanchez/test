#!/usr/bin/env python3
"""Qualify original source arithmetic replay with source constructor demand."""
import argparse,importlib.util,json,os,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FRONTIER=ROOT.parent/'nucleus-nat-frontier-20261104'
FINAL=ROOT.parent/'nucleus-final-proof-spine-20261104'
QSPEC=importlib.util.spec_from_file_location('quotient_wave',ROOT.parent/'nucleus-quotient-reuse-20261104/runner.py')
Q=importlib.util.module_from_spec(QSPEC);QSPEC.loader.exec_module(Q);t=Q.t

def runtime(semantic):
 env=t.run_env()
 if semantic:env['NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR']='1'
 return env

def materialize(out,semantic):
 k=Q.materialize(out,True)
 if semantic:
  patch=FRONTIER/'complete-replay.patch';r=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=out,capture_output=True,timeout=30)
  (out/'native-patch.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
  with(out/'source.patch').open('a')as f:f.write(patch.read_text())
 tests=FRONTIER/('captured_native_tests.rs'if semantic else'captured_native_tests_initial.rs')
 with(k/'src/machine.rs').open('a')as f:f.write(tests.read_text())
 (k/'tests/native_source_replay.rs').write_text((ROOT/'native_source_replay.rs').read_text())
 fixture=k/'tests/fixtures/native-source-replay';fixture.mkdir(parents=True,exist_ok=True)
 for p in Path('/tmp/nat-fixtures').glob('*.ndjson'):shutil.copy2(p,fixture/p.name)
 assert t.digest(fixture/'nat-original.ndjson')=='7767e7f90b3e24b30ecb5324f1117d6858b5f40653b31011ad1948eed747e8ea'
 return k

def qualify(out):
 inputs=Path('/tmp/current208');manifest=json.loads((inputs/'inputs-manifest.json').read_text());state={};baseline=nr0=None
 for name,semantic in [('baseline',False),('candidate',True)]:
  arm=out/name;k=materialize(arm,semantic);binary,env=t.build(k,arm);assert binary is not None
  run=runtime(semantic);native_env=env|run|{'NUCLEUS_FROZEN196':str(inputs/'inputs')}
  nr=t.native_suite(k,native_env,arm);rows=t.replay(binary,manifest,inputs,run,arm/'verdicts.json')
  if not semantic:t.validate_baseline(rows);baseline=rows;nr0=nr
  regress=[dict(case=a['case'],before=a['rc'],after=b['rc'])for a,b in zip(baseline,rows)if b['rc']not in(b['expected'],2)or(a['rc']!=2 and a['rc']!=b['rc'])]
  info=dict(binary_sha=t.digest(binary),source_patch_sha=t.digest(arm/'source.patch'),configuration={k:v for k,v in run.items()if k.startswith('NUCLEUS_')},native=nr,native_nonregression=Q.native_nonregression(nr,nr0),regressions=regress,counts={str(rc):sum(x['rc']==rc for x in rows)for rc in(0,1,2)})
  if semantic:
   controls=[]
   for p in sorted((FINAL/'controls').glob('*.ndjson')):
    with p.open('rb')as f:r=t.run_group([str(binary)],stdin=f,capture_output=True,env=run,timeout=60)
    good=p.stem in{'same','proof_last','dependent_proof_last','long_prefix_valid'}
    controls.append(dict(case=p.stem,rc=r.returncode,pass_=r.returncode==0 if good else r.returncode in(1,2)))
   for row in json.loads(Path('/tmp/nat-fixtures/manifest.json').read_text()):
    p=Path('/tmp/nat-fixtures')/row['file'];assert t.digest(p)==row['sha256']
    with p.open('rb')as f:r=t.run_group([str(binary)],stdin=f,capture_output=True,env=run,timeout=180)
    controls.append(dict(case=row['file'],sha=row['sha256'],rc=r.returncode,pass_=r.returncode==0 if row['expected']==0 else r.returncode in(1,2),stderr=r.stderr.decode(errors='replace')))
   info['controls']=controls;info['qualified']=not regress and info['native_nonregression']and all(c['pass_']for c in controls)
  state[name]=info;t.write_json(out/'qualification.json',state);shutil.rmtree(arm/'target',ignore_errors=True)
 assert state['candidate']['qualified'],state['candidate']

def full(out):
 source=Path('/tmp/mathlib.ndjson');assert t.digest(source)==t.INPUT_SHA
 k=materialize(out/'candidate',True);binary,_=t.build(k,out/'candidate');assert binary is not None
 env=runtime(True);env['NUCLEUS_TRACE_DOWNSTREAM']='1';perf=t.probe_perf(out);result=t.measure(binary,source,env,out/'full-input',timeout=5400,perf=perf)
 import re
 terminal=re.findall(r'NUCLEUS_DOWNSTREAM:name=(.*?):stage=',(out/'full-input/stderr').read_text())
 frontier=Q.extract_frontier(source,out/'next-frontier.ndjson',terminal[-1])if terminal and not terminal[-1].startswith('<')else None
 summary=dict(base=t.BASE,harness=os.environ.get('GITHUB_SHA'),binary_sha=t.digest(binary),source_patch_sha=t.digest(out/'candidate/source.patch'),input_sha=t.INPUT_SHA,result=result,complete_mathlib_accept=result['rc']==0,perf_available=perf,next_frontier=frontier,configuration={k:v for k,v in env.items()if k.startswith('NUCLEUS_')});t.write_json(out/'summary.json',summary);print(json.dumps(summary),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['qualify','full']);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);(qualify if a.phase=='qualify'else full)(out)
