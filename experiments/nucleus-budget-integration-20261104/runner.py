import argparse,importlib.util,json,math,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('let_wave',ROOT.parent/'nucleus-let-preservation-20261104/runner.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L);R=L.R;t=L.t
def signatures(rows):return sorted(json.dumps({k:r.get(k)for k in ['file','case','sha256','expected','native_expected','rc']},sort_keys=True)for r in rows)
def reference(path,expected,directory):
 directory.mkdir(parents=True,exist_ok=True);binary=Path('/tmp/budget-reference/bundle/kernel');assert t.digest(binary)=='ae92c625e612fff1c90e329344d22e3c3c330383cb335ce28fd41435be3b3b94';binary.chmod(0o755)
 for mode,args,want in [('parse',['--parse-only',str(path)],0),('kernel',[str(path)],expected)]:
  r=t.run_group([str(binary),*args],capture_output=True,timeout=180);(directory/(mode+'.stdout')).write_bytes(r.stdout);(directory/(mode+'.stderr')).write_bytes(r.stderr);assert r.returncode==want,(path,mode,r.returncode,want)
 return dict(input_sha=t.digest(path),parse_rc=0,kernel_rc=expected,binary_sha=t.digest(binary),artifact=13267462207)
def main(out):
 prior=Path('/tmp/budget-baseline');base=json.loads((prior/'qualification.json').read_text())['candidate'];assert base['qualified'];bb=prior/'candidate/nucleus';assert t.digest(bb)==base['binary_sha'];bb.chmod(0o755)
 assert t.digest(prior/'candidate/source.patch')==base['source_patch_sha']
 assert len(base['native']['targets'])==42 and len(base['controls'])==61 and all(x['complete']for x in base['native']['targets'].values())and all(x['pass_']for x in base['controls'])
 run=R.N.runtime(True);assert {k:v for k,v in run.items()if k.startswith('NUCLEUS_')}==base['configuration']
 arm=out/'candidate';k=L.materialize(arm,True)
 for label in ['owner-index.patch','tagged.patch','dense.patch','budget.patch']:
  if label=='budget.patch':assert t.digest(arm/'source.patch')==base['source_patch_sha']
  patch=(ROOT/label if label=='budget.patch' else ROOT.parent/'nucleus-dense-composition-20261104'/label if label=='dense.patch' else ROOT.parent/'nucleus-tagged-let-20261104'/label);r=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30);(arm/(label+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0
  with(arm/'source.patch').open('a')as f:f.write(patch.read_text())
 binary,env=t.build(k,arm);assert binary is not None
 inputs=Path('/tmp/current208');extra=inputs/'inputs/good/perf/magma-list-pair-n21.ndjson';extra.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['zstd','-dq','-f',str(ROOT.parent/'nucleus-coverage-evidence-20261104/inputs/magma-list-pair-n21.ndjson.zst'),'-o',str(extra)],check=True);assert t.digest(extra)==base['extra']['input_sha']
 nr=t.native_suite(k,env|run|{'NUCLEUS_FROZEN196':str(inputs/'inputs')},arm)
 rows=t.replay(binary,json.loads((inputs/'inputs-manifest.json').read_text()),inputs,run,arm/'verdicts.json');old=json.loads((prior/'candidate/verdicts.json').read_text());assert len(rows)==len(old)==208;diff=[]
 for a,b in zip(old,rows):
  assert a['case']==b['case']and a['sha256']==b['sha256']and a['expected']==b['expected']
  if a['rc']!=b['rc']:
   valid=a['rc']==2 and b['rc']==b['expected'] and b['rc']in(0,1)
   entry=dict(case=a['case'],before=a['rc'],after=b['rc'],permitted=valid)
   if valid:
    path=inputs/'inputs'/('good'if b['expected']==0 else'bad')/(b['case']+'.ndjson');assert t.digest(path)==b['sha256']
    entry['reference']=reference(path,b['rc'],arm/('changed-'+str(len(diff))))
   diff.append(entry)
 with extra.open('rb')as f:r=t.run_group([str(binary)],stdin=f,capture_output=True,env=run,timeout=180)
 extra_result=dict(case=base['extra']['case'],input_sha=t.digest(extra),rc=r.returncode,unchanged=r.returncode==base['extra']['rc'])
 if not extra_result['unchanged']:
  extra_result['permitted']=base['extra']['rc']==2 and r.returncode==0
  if extra_result['permitted']:extra_result['reference']=reference(extra,0,arm/'changed-extra')
 captured=out/'captured-controls';subprocess.run(['python3',str(ROOT.parent/'nucleus-captured-tidy-probes-20261104/generate.py'),'--source','/tmp/range-prefix.ndjson','--out',str(captured)],check=True);captured_rows=[]
 for case in json.loads((captured/'inputs.json').read_text()):
  path=captured/case['file'];assert t.digest(path)==case['sha256'];reference(path,case['expected_reference_rc'],captured/(case['case']+'-reference'))
  with path.open('rb')as f:c=t.run_group([str(binary)],stdin=f,capture_output=True,env=run,timeout=240)
  (captured/(case['case']+'.stderr')).write_bytes(c.stderr);captured_rows.append(dict(case=case['case'],sha256=t.digest(path),rc=c.returncode,expected=case['expected_reference_rc'],pass_=c.returncode==case['expected_reference_rc']))
 t.write_json(out/'captured-controls.json',captured_rows)
 cs=L.controls(binary,run);nonreg=R.N.Q.native_nonregression(nr,base['native']);same=signatures(cs)==signatures(base['controls'])
 q=dict(baseline_binary=base['binary_sha'],baseline_source_patch=base['source_patch_sha'],baseline_artifact=13268111683,baseline_evidence_reused=True,binary_sha=t.digest(binary),source_patch_sha=t.digest(arm/'source.patch'),native=nr,native_nonregression=nonreg,captured_controls=captured_rows,verdict_changes=diff,extra=extra_result,controls=cs,controls_unchanged=same,configuration=base['configuration'])
 q['protected_qualified']=nonreg and len(captured_rows)==3 and all(x['pass_']for x in captured_rows)and all(x['permitted']for x in diff)and (extra_result['unchanged']or extra_result.get('permitted',False))and same and all(x['pass_']for x in cs);q['qualified']=False;t.write_json(out/'qualification.json',dict(candidate=q));assert q['protected_qualified'],q
 # Exact original source, independently accepted, must now close on the integrated binary.
 prefix=Path('/tmp/range-prefix.ndjson');assert t.digest(prefix)=='d9d7b1fe7267a0806f65200abc64a9c7114fb8097a9da1f3687f2560a2568bb9'
 reference(prefix,0,out/'range-reference')
 with prefix.open('rb')as f:replay=t.run_group([str(binary)],stdin=f,capture_output=True,env=run,timeout=240)
 (out/'range-prefix.stderr').write_bytes(replay.stderr);q['range_prefix']=dict(input_sha=t.digest(prefix),rc=replay.returncode,reference_rc=0);q['qualified']=q['protected_qualified']and replay.returncode==0
 t.write_json(out/'qualification.json',dict(candidate=q));assert q['qualified'],q;shutil.rmtree(arm/'target',ignore_errors=True)
 # Reuse the just-qualified binary without recompiling. New frontier differs by design;
 # this phase is completion evidence, not a speed comparison against an earlier exit.
 source=Path('/tmp/mathlib.ndjson');assert t.digest(source)==t.INPUT_SHA;run['NUCLEUS_TRACE_DOWNSTREAM']='1'
 result=t.measure(binary,source,run,out/'full-input',timeout=5400,perf=False)
 import re
 trace=re.findall(r'NUCLEUS_DOWNSTREAM:name=(.*?):stage=',(out/'full-input/stderr').read_text());frontier=None
 if trace and not trace[-1].startswith('<'):
  p=out/'next-frontier.ndjson';frontier=R.E.extract(source,p,trace[-1]);subprocess.run(['zstd','-T0','-3',str(p)],check=True);p.unlink()
 summary=dict(binary_sha=t.digest(binary),source_patch_sha=q['source_patch_sha'],input_sha=t.INPUT_SHA,result=result,complete_mathlib_accept=result['rc']==0,next_frontier=frontier,qualified_binary_reused=True,configuration=q['configuration'],harness=os.environ.get('GITHUB_SHA'))
 t.write_json(out/'summary.json',summary);print(json.dumps(summary),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);main(out)
