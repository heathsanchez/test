from pathlib import Path
import importlib.util,json,hashlib,subprocess,tarfile,statistics
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'nucleus-quotient-result-projection-20261104/qualify.py'
s=OLD.read_text().replace('/tmp/nucleus-quotient-result-projection','/tmp/nucleus-universe-parametric-source').replace("b'183 passed; 0 failed; 0 ignored;'","b'210 passed; 0 failed; 0 ignored;'")
s=s.replace("q['promotion_parent']=BINARY;","q['promotion_parent']='26244e47fb94c1ffa47a09531bc8fb9d8205bba176c459bcf31d431e9f4aea89';")
start=s.index(" q['boundary']=");end=s.index('\n',start)
s=s[:start]+" q['boundary']='Completed Term inference reuse under exact source/frame/universe/full-Term-context, captured configuration, strictness and revocable binding epoch; fixed8192 slots and four probes, bounded context64, source root step charged once, constructor/host metadata boundary separate from unchanged semantic caps, borrowed fixed-point destruction certificate:66roots/326records/64nontrivialallocation-entry-level nodes/4096parameterbytes; count released parent and Closure payload edges; unsupportedownedpayloads decline; no Pi/Sort/Unknown retention. Separate instantiated-source VALUE congruence uses completed context-free syntax templates with all binder-relative captures and Sort-Const universe obligations, each actual universe substitution rechecked by borrowed metered traversal; literal capture equality remains mandatory. Strict identity contract and proofcache namespace unchanged; broad results local-only. Templatecache8192, each capture-level set128; missing-cyclic-exhausted casesdecline. Converter falls back only within original sharedtrialallowance, no newfuel-flags'"+s[end:]
s=s.replace("q['native_nonregression_to_promotion_parent']=True","q['native_nonregression_to_promotion_parent']=False")
s=s.replace("if __name__=='__main__':main()",'')
module=type(__import__('sys'))('bounded_qualification');module.__file__=str(OLD)
exec(compile(s,str(OLD),'exec'),module.__dict__)
t=module.t;original_build=t.build

def build(kernel,arm,profile='standard'):
 patch=ROOT/'universe-parametric-source.patch';r=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30);(arm/'typing-memo-patch.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
 with(arm/'source.patch').open('ab')as f:f.write(patch.read_bytes())
 files=sorted(p for p in kernel.rglob('*')if p.is_file())
 t.write_json(arm/'source-manifest.json',{str(p.relative_to(kernel)):t.digest(p)for p in files})
 with tarfile.open(arm/'source.tar.gz','w:gz')as archive:
  for p in files:archive.add(p,arcname='metatron-kernel/'+str(p.relative_to(kernel)))
 return original_build(kernel,arm,profile)
t.build=build

def main():
 module.main();R=module.OUT;report=json.loads((R/'quotient-result-projection.json').read_text());full=report['full'];default=Path('/tmp/bounded-default')
 parent=json.loads((default/'bounded-capture-reclaim.json').read_text());assert parent['qualified']and parent['binary_sha']=='26244e47fb94c1ffa47a09531bc8fb9d8205bba176c459bcf31d431e9f4aea89'
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
 for i,arm in enumerate(['candidate','parent','parent','candidate']):
  bin=new if arm=='candidate'else old;r=t.measure(bin,source,env,R/'timing'/f'{i}-{arm}',timeout=900,perf=False);assert r['rc']==0
  rows.append(dict(arm=arm,binary_sha=t.digest(bin),input_sha=t.digest(source),**r));t.write_json(R/'timing.json',dict(status='RUNNING',rows=rows));print('BOUNDED_TIMING_ARM',json.dumps(rows[-1]),flush=True)
 a=[r['user']+r['system']for r in rows if r['arm']=='parent'];b=[r['user']+r['system']for r in rows if r['arm']=='candidate'];win=max(b)<min(a)*.99
 timing=dict(status='COMPLETE',rows=rows,preset='every candidate CPU sample beats every parent sample by more than1percent',speed_win=win,median_cpu_ratio=statistics.median(b)/statistics.median(a),no_rank_claim=True);t.write_json(R/'timing.json',timing)
 report.update(status='PROMOTABLE_UNIVERSE_PARAMETRIC_SOURCE'if win else'QUALIFIED_NO_ESTABLISHED_SPEED_WIN',qualified=win,source_qualified=True,parent_binary=parent['binary_sha'],source_parent_binary=module.BINARY,timing=timing,complete_mathlib_accept=full['complete_mathlib_accept'],no_official_rank_claim=True)
 t.write_json(R/'universe-parametric-source.json',report);print('BOUNDED_TYPING_MEMO_RESULT',json.dumps(report),flush=True)
if __name__=='__main__':main()
