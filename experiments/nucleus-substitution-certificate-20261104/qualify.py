from pathlib import Path
import importlib.util,json,hashlib,subprocess,tarfile,statistics
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'nucleus-quotient-result-projection-20261104/qualify.py'
s=OLD.read_text().replace('/tmp/nucleus-quotient-result-projection','/tmp/nucleus-substitution-certificate').replace("b'183 passed; 0 failed; 0 ignored;'","b'246 passed; 0 failed; 0 ignored;'")
s=s.replace("q['promotion_parent']=BINARY;","q['promotion_parent']='82ebbce2278e54f82667e4d12793034acdf72f329b989e4605cf65473c9de715';")
start=s.index(" q['boundary']=");end=s.index('\n',start)
s=s[:start]+" q['boundary']='Bounded composition of already-completed same-expression substitution support with literal actual-universe-map equality, identical primitive captures or completed owning child VALUE equalities. No cold support construction, closure-alias chasing, inference or exposure. All validation shares the existing quarter/min1024 allowance with legacy discovery; recursive search32 unchanged. Includes independently tested nested receiver resumption, metered universe normalization, strict-broad completed-fact separation, original-alias retention and forward application congruence. No preallocation arm, no new cache capacity, semantic numeric limits or flags.'"+s[end:]
s=s.replace("q['native_nonregression_to_promotion_parent']=True","q['native_nonregression_to_promotion_parent']=False")
s=s.replace("if __name__=='__main__':main()",'')
module=type(__import__('sys'))('bounded_qualification');module.__file__=str(OLD)
exec(compile(s,str(OLD),'exec'),module.__dict__)
t=module.t;original_build=t.build

def build(kernel,arm,profile='standard'):
 patch=ROOT/'substitution-certificate.patch';r=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30);(arm/'typing-memo-patch.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
 with(arm/'source.patch').open('ab')as f:f.write(patch.read_bytes())
 files=sorted(p for p in kernel.rglob('*')if p.is_file())
 t.write_json(arm/'source-manifest.json',{str(p.relative_to(kernel)):t.digest(p)for p in files})
 with tarfile.open(arm/'source.tar.gz','w:gz')as archive:
  for p in files:archive.add(p,arcname='metatron-kernel/'+str(p.relative_to(kernel)))
 return original_build(kernel,arm,profile)
t.build=build

def main():
 module.main();R=module.OUT;report=json.loads((R/'quotient-result-projection.json').read_text());full=report['full'];default=Path('/tmp/bounded-default')
 parent=json.loads((default/'universe-parametric-source.json').read_text());assert parent['qualified']and parent['binary_sha']=='82ebbce2278e54f82667e4d12793034acdf72f329b989e4605cf65473c9de715'
 q=json.loads((R/'qualification.json').read_text())['candidate'];parent_q=json.loads((default/'qualification.json').read_text())['candidate']
 assert q['configuration']==parent_q['configuration'],'Exact actual-default capability configuration'
 assert set(q['native']['targets'])==set(parent_q['native']['targets'])
 for name,old_row in parent_q['native']['targets'].items():
  new_row=q['native']['targets'][name]
  assert new_row['complete']and old_row['complete']
  assert new_row['counts'][0]>=old_row['counts'][0]and new_row['counts'][1:]==old_row['counts'][1:],('actual-default-native-counts',name)
  assert sorted(new_row['failures'])==sorted(old_row['failures']),('actual-default-native-failures',name)
 current_rows=json.loads((R/'candidate/verdicts.json').read_text());parent_rows=json.loads((default/'candidate/verdicts.json').read_text())
 signature=lambda rows:[(r['case'],r['expected'],r['rc'],r['sha256'])for r in rows]
 assert len(current_rows)==len(parent_rows)==208 and signature(current_rows)==signature(parent_rows),'Direct frozen208 verdict/input identity with actual default'
 q['native_nonregression_to_promotion_parent']=True;q['native_promotion_parent_binary']=parent['binary_sha'];t.write_json(R/'qualification.json',dict(candidate=q))
 old=default/'candidate/nucleus';old.chmod(0o755);assert t.digest(old)==parent['binary_sha']
 if full['result']['rc']==2:
  assert full['next_frontier']['record']>=parent['full']['next_frontier']['record'],'No coverage regression from the actual research default'
  if full['next_frontier']['record']==parent['full']['next_frontier']['record']:assert full['next_frontier']['sha256']==parent['full']['next_frontier']['sha256']
 subprocess.run(['python3',str(ROOT.parent/'nucleus-contextual-frontier-readback-20261104/frontier.py'),'--source','/tmp/coe-foldr-prefix.ndjson','--out',str(R/'hot'),'--target','AddMonoidAlgebra.instAddCommMonoid._proof_1'],check=True)
 source=R/'hot/next-frontier.ndjson';assert t.digest(source)=='8428d5d4282a608eb77e48ff62adace23212d9487ff9e86dc2e57af7c573d5f1'
 ref=Path('/tmp/k-reference/bundle/kernel');C=module.C
 assert C.captured([str(ref),'--parse-only',str(source)],R/'hot-oracle/parse')==0
 assert C.captured([str(ref),str(source)],R/'hot-oracle/reference',timeout=240)==0
 q=json.loads((R/'qualification.json').read_text())['candidate'];env={k:v for k,v in __import__('os').environ.items()if not k.startswith('NUCLEUS_')}|q['configuration'];new=R/'candidate/nucleus';rows=[]
 subprocess.run(['python3',str(ROOT.parent/'nucleus-contextual-frontier-readback-20261104/frontier.py'),'--source','/tmp/mathlib.ndjson','--out',str(R/'original-first-frontier'),'--target','AddMonoidAlgebra.nonUnitalNonAssocSemiring._proof_1'],check=True)
 original=R/'original-first-frontier/next-frontier.ndjson';assert t.digest(original)=='ca6ba58a99ca074dc45d975ab982fd119193fa05a6d12e20f08c53cb7dd786f2'
 fixture=ROOT.parent/'nucleus-source-qualification-readbacks-20261104/receiver-comparison-regression/valid-data-congruence.ndjson.xz';assert t.digest(fixture)=='80073229ac55790b1d1afaf3d9d6e219706644110a6c1f090f5a8fa554939f41'
 compact=R/'compact-regression.ndjson';compact.write_bytes(__import__('lzma').decompress(fixture.read_bytes()));assert t.digest(compact)=='ef5df79ed54b93ec8597131304c9ed76358dd4a60c5bf7275fb0033a9fe9e431'
 matched=[]
 for label,case in [('original-first-frontier',original),('compact-substitution-regression',compact)]:
  assert C.captured([str(ref),'--parse-only',str(case)],R/'matched-oracle'/label/'parse')==0
  assert C.captured([str(ref),str(case)],R/'matched-oracle'/label/'reference',timeout=240)==0
  red=t.measure(old,case,env,R/'matched-red'/label,timeout=900,perf=False);green=t.measure(new,case,env,R/'matched-green'/label,timeout=900,perf=False)
  assert red['rc']==2 and green['rc']==0,(label,red,green)
  matched.append(dict(case=label,input_sha=t.digest(case),parent_binary=t.digest(old),candidate_binary=t.digest(new),red=red,green=green))
 t.write_json(R/'matched-regressions.json',dict(status='COMPLETE',rows=matched,no_speed_claim=True))
 coverage_win=full['complete_mathlib_accept']or(full['result']['rc']==2 and full['next_frontier']['record']>parent['full']['next_frontier']['record']);assert coverage_win,'Actual-default original coverage must advance'

 for i,arm in enumerate(['candidate','parent','parent','candidate']):
  bin=new if arm=='candidate'else old;r=t.measure(bin,source,env,R/'timing'/f'{i}-{arm}',timeout=900,perf=False);assert r['rc']==0
  rows.append(dict(arm=arm,binary_sha=t.digest(bin),input_sha=t.digest(source),**r));t.write_json(R/'timing.json',dict(status='RUNNING',rows=rows));print('BOUNDED_TIMING_ARM',json.dumps(rows[-1]),flush=True)
 a=[r['user']+r['system']for r in rows if r['arm']=='parent'];b=[r['user']+r['system']for r in rows if r['arm']=='candidate'];win=max(b)<min(a)*.99
 timing=dict(status='COMPLETE',rows=rows,preset='every candidate CPU sample beats every parent sample by more than1percent',speed_win=win,median_cpu_ratio=statistics.median(b)/statistics.median(a),no_rank_claim=True);t.write_json(R/'timing.json',timing)
 report.update(status='PROMOTABLE_SUBSTITUTION_CERTIFICATE_COVERAGE',qualified=coverage_win,source_qualified=True,coverage_win=coverage_win,matched_regressions=matched,promotion_basis='actual-default original coverage gain; speed warrant separate',parent_binary=parent['binary_sha'],source_parent_binary=module.BINARY,timing=timing,complete_mathlib_accept=full['complete_mathlib_accept'],no_official_rank_claim=True)
 t.write_json(R/'substitution-certificate.json',report);print('BOUNDED_TYPING_MEMO_RESULT',json.dumps(report),flush=True)
if __name__=='__main__':main()
