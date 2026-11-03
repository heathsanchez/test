import argparse,importlib.util,json,math,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('let_wave',ROOT.parent/'nucleus-let-preservation-20261104/runner.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L);R=L.R;t=L.t
def signatures(rows):return sorted(json.dumps({k:r.get(k)for k in ['file','case','sha256','expected','native_expected','rc']},sort_keys=True)for r in rows)
def main(out):
 prior=Path('/tmp/tagged-baseline');base=json.loads((prior/'qualification.json').read_text())['candidate'];assert base['qualified'];bb=prior/'candidate/nucleus';assert t.digest(bb)==base['binary_sha'];bb.chmod(0o755)
 assert t.digest(prior/'candidate/source.patch')==base['source_patch_sha']
 assert len(base['native']['targets'])==42 and len(base['controls'])==61 and all(x['complete']for x in base['native']['targets'].values())and all(x['pass_']for x in base['controls'])
 run=R.N.runtime(True);assert {k:v for k,v in run.items()if k.startswith('NUCLEUS_')}==base['configuration']
 arm=out/'candidate';k=L.materialize(arm,True)
 for label in ['owner-index.patch','tagged.patch']:
  if label=='tagged.patch':assert t.digest(arm/'source.patch')==base['source_patch_sha']
  patch=ROOT/label;r=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30);(arm/(label+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0
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
 cs=L.controls(binary,run);nonreg=R.N.Q.native_nonregression(nr,base['native']);same=signatures(cs)==signatures(base['controls'])
 q=dict(baseline_binary=base['binary_sha'],baseline_source_patch=base['source_patch_sha'],baseline_artifact=13264581883,baseline_evidence_reused=True,binary_sha=t.digest(binary),source_patch_sha=t.digest(arm/'source.patch'),native=nr,native_nonregression=nonreg,verdict_changes=diff,extra=extra_result,controls=cs,controls_unchanged=same,configuration=base['configuration'])
 q['qualified']=nonreg and not diff and extra_result['unchanged']and same and all(x['pass_']for x in cs);t.write_json(out/'qualification.json',dict(candidate=q));assert q['qualified'],q
 source=Path('/tmp/mathlib.ndjson');assert t.digest(source)==t.INPUT_SHA;run['NUCLEUS_TRACE_DOWNSTREAM']='1';pairs=[];expected=None
 for number,order in enumerate([('baseline','candidate'),('candidate','baseline'),('baseline','candidate')]):
  pair={}
  for name in order:
   b=bb if name=='baseline'else binary;directory=out/'matched'/f'{number}-{name}';m=t.measure(b,source,run,directory,timeout=600,perf=False)
   traces=[line for line in(directory/'stderr').read_text().splitlines()if line.startswith('NUCLEUS_DOWNSTREAM:')];terminal=traces[-1]if traces else None;assert m['rc']in(0,2),m
   if expected is None:expected=(m['rc'],terminal)
   assert(m['rc'],terminal)==expected,(name,m,terminal,expected)
   pair[name]=dict(result=m,terminal=terminal,binary_sha=t.digest(b));print('MATCHED',json.dumps(dict(pair=number,arm=name,**pair[name])),flush=True)
  pairs.append(pair);t.write_json(out/'matched.json',dict(pairs=pairs))
 ratios=[p['candidate']['result']['user']/p['baseline']['result']['user']for p in pairs];total=[(p['candidate']['result']['user']+p['candidate']['result']['system'])/(p['baseline']['result']['user']+p['baseline']['result']['system'])for p in pairs]
 report=dict(pairs=pairs,user_cpu_ratios=ratios,total_cpu_ratios=total,user_cpu_geomean=math.prod(ratios)**(1/3),total_cpu_geomean=math.prod(total)**(1/3),screen_won=all(x<1 for x in total)and math.prod(total)**(1/3)<=.98,input_sha=t.INPUT_SHA,complete_mathlib_accept=expected[0]==0,official_instructions_measured=False)
 t.write_json(out/'matched.json',report);print(json.dumps(report),flush=True);shutil.rmtree(arm/'target',ignore_errors=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);main(out)
