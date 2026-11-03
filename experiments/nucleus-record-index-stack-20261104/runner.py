import argparse,hashlib,importlib.util,json,math,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('record_wave',ROOT.parent/'nucleus-parameter-telescope-20261104/runner.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R);t=R.t
BASE_BINARY='63124411e01b109f85e1ffb9179f4668bb9a8c8b91b05b80370c2afb16560553'
BASE_PATCH='110cda043bb4ac98dafb443c3f043980f58416c12a45ff6cc8cdb12bc2755cc8'
def main(out):
 baseline_root=Path('/tmp/record-baseline');baseline=json.loads((baseline_root/'qualification.json').read_text())['candidate']
 assert baseline['qualified'] and baseline['native_nonregression'] and not baseline['regressions']
 bb=baseline_root/'candidate/nucleus';assert t.digest(bb)==BASE_BINARY and baseline['binary_sha']==BASE_BINARY
 assert t.digest(baseline_root/'candidate/source.patch')==BASE_PATCH and baseline['source_patch_sha']==BASE_PATCH
 os.chmod(bb,0o755);run=R.N.runtime(True)
 assert {k:v for k,v in run.items()if k.startswith('NUCLEUS_')}==baseline['configuration']
 assert len(baseline['native']['targets'])==40 and all(x['complete']for x in baseline['native']['targets'].values())
 assert len(baseline['controls'])==32 and all(x['pass_']for x in baseline['controls'])
 arm=out/'candidate';k=R.materialize(arm,True);assert t.digest(arm/'source.patch')==BASE_PATCH
 patch=ROOT/'owner-index.patch';r=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30);(arm/'index-patch.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
 with(arm/'source.patch').open('a')as f:f.write(patch.read_text())
 binary,env=t.build(k,arm);assert binary is not None
 inputs=Path('/tmp/current208');extra=inputs/'inputs/good/perf/magma-list-pair-n21.ndjson';extra.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['zstd','-dq','-f',str(ROOT.parent/'nucleus-coverage-evidence-20261104/inputs/magma-list-pair-n21.ndjson.zst'),'-o',str(extra)],check=True)
 assert t.digest(extra)==baseline['extra']['input_sha']
 nr=t.native_suite(k,env|run|{'NUCLEUS_FROZEN196':str(inputs/'inputs')},arm)
 manifest=json.loads((inputs/'inputs-manifest.json').read_text());rows=t.replay(binary,manifest,inputs,run,arm/'verdicts.json')
 old=json.loads((baseline_root/'candidate/verdicts.json').read_text());assert len(old)==len(rows)==208
 diffs=[]
 for a,b in zip(old,rows):
  assert a['case']==b['case'] and a['sha256']==b['sha256']
  if a['rc']!=b['rc']:diffs.append(dict(case=a['case'],before=a['rc'],after=b['rc']))
 with extra.open('rb')as f:r=t.run_group([str(binary)],stdin=f,capture_output=True,env=run,timeout=180)
 extra_result=dict(case=baseline['extra']['case'],input_sha=t.digest(extra),rc=r.returncode,unchanged=r.returncode==baseline['extra']['rc'])
 controls=R.controls(binary,run);nonreg=R.N.Q.native_nonregression(nr,baseline['native'])
 q=dict(baseline_artifact=13255951206,baseline_zip_sha='fb87e4188fc3a2cd027a8ef8ab5edad8d314716487a2e8dd904f627f1f5d557b',baseline_binary=BASE_BINARY,baseline_source_patch=BASE_PATCH,baseline_evidence_reused=True,candidate_binary=t.digest(binary),candidate_source_patch=t.digest(arm/'source.patch'),native=nr,native_nonregression=nonreg,verdict_changes=diffs,extra=extra_result,controls=controls,configuration=baseline['configuration'])
 q['qualified']=nonreg and not diffs and extra_result['unchanged'] and all(x['pass_']for x in controls)
 t.write_json(out/'qualification.json',q);assert q['qualified'],q
 source=Path('/tmp/mathlib.ndjson');assert t.digest(source)==t.INPUT_SHA;run['NUCLEUS_TRACE_DOWNSTREAM']='1'
 pairs=[];terminal_expected=None
 for number,order in enumerate([('baseline','candidate'),('candidate','baseline'),('baseline','candidate')]):
  pair={}
  for name in order:
   directory=out/'matched'/f'{number}-{name}';b=bb if name=='baseline'else binary
   result=t.measure(b,source,run,directory,timeout=5400,perf=False)
   traces=re.findall(r'NUCLEUS_DOWNSTREAM:name=(.*?):stage=(.*)',(directory/'stderr').read_text())
   terminal=traces[-1]if traces else None
   observed=dict(result=result,terminal=terminal,binary_sha=t.digest(b));pair[name]=observed
   if terminal_expected is None:terminal_expected=(result['rc'],terminal)
   assert (result['rc'],terminal)==terminal_expected,(name,observed,terminal_expected)
   print('MATCHED',json.dumps(dict(pair=number,arm=name,**observed)),flush=True)
  pairs.append(pair);t.write_json(out/'matched.json',dict(pairs=pairs))
 ratios=[p['candidate']['result']['user']/p['baseline']['result']['user']for p in pairs]
 total=[(p['candidate']['result']['user']+p['candidate']['result']['system'])/(p['baseline']['result']['user']+p['baseline']['result']['system'])for p in pairs]
 report=dict(pairs=pairs,user_cpu_ratios=ratios,total_cpu_ratios=total,user_cpu_geomean=math.prod(ratios)**(1/3),total_cpu_geomean=math.prod(total)**(1/3),screen_won=all(r<1 for r in total)and math.prod(total)**(1/3)<=0.98,input_sha=t.INPUT_SHA,complete_mathlib_accept=terminal_expected[0]==0,official_instructions_measured=False,baseline_evidence_reused=True)
 t.write_json(out/'matched.json',report);print(json.dumps(report),flush=True)
 shutil.rmtree(arm/'target',ignore_errors=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);main(out)
