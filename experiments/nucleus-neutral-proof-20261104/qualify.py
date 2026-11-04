"""Qualify contextual proof conversion without a same-frontier speed claim."""
import importlib.util,json,re,shutil,subprocess,tarfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('performance_gates',ROOT.parent/'nucleus-performance-gates-20261104/gate.py')
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
C,Q,t=G.C,G.Q,G.t
BASE=Path('/tmp/native-qualified')
OUT=Path('/tmp/nucleus-neutral-proof')
BINARY='13acbe00d45fd50684b97afb30a6481c54fce9b796012be6444805c9a1fca545'
INT='5937f7e74092f8c4adaf8268a2ef5c1e7dabfad096549a832c559e30b4f2dece'

def main():
 OUT.mkdir(exist_ok=True);arm=OUT/'candidate';arm.mkdir()
 parent=json.loads((BASE/'qualification.json').read_text())['candidate']
 assert parent['qualified']and parent['binary_sha']==BINARY and t.digest(BASE/'candidate/nucleus')==BINARY
 assert t.digest(BASE/'candidate/source.tar.gz')=='871459360f33532eaa82e74dab50fe03db443714c9cc8951d5ff303356b94e30'
 assert t.digest(BASE/'candidate/source-manifest.json')=='341e8b7875c38f5fc8d3724c03361241a0ad323110f82762c73c1497022b94b4'
 with tarfile.open(BASE/'candidate/source.tar.gz')as archive:archive.extractall(arm,filter='data')
 kernel=arm/'metatron-kernel'
 for name,sha in json.loads((BASE/'candidate/source-manifest.json').read_text()).items():
  path=PurePosixPath(name);assert not path.is_absolute()and '..'not in path.parts;assert t.digest(kernel/name)==sha,name
 patch=ROOT/'combined-proof.patch'
 patched=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30)
 (arm/'patch.log').write_bytes(patched.stdout+patched.stderr);assert patched.returncode==0
 (arm/'source.patch').write_bytes((BASE/'candidate/source.patch').read_bytes()+patch.read_bytes())
 files=sorted(p for p in kernel.rglob('*')if p.is_file())
 t.write_json(arm/'source-manifest.json',{str(p.relative_to(kernel)):t.digest(p)for p in files})
 with tarfile.open(arm/'source.tar.gz','w:gz')as archive:
  for p in files:archive.add(p,arcname='metatron-kernel/'+str(p.relative_to(kernel)))
 binary,build_env=t.build(kernel,arm);assert binary is not None
 source=Path('/tmp/right-dite-prefix.ndjson');assert t.digest(source)==INT
 cases=OUT/'native-inputs'
 subprocess.run(['python3',str(ROOT/'generate.py'),'--source',str(source),'--out',str(cases)],check=True)
 manifest=json.loads((cases/'manifest.json').read_text());manifest.insert(0,dict(case='authentic-dite-eq-right',file='dite.ndjson',sha256=INT,expect_reference=0));shutil.copyfile(source,cases/'dite.ndjson');assert len(manifest)==6
 native_cases=OUT/'native-inputs-prior'
 subprocess.run(['python3',str(ROOT.parent/'nucleus-native-completion-20261104/generate.py'),'--source','/tmp/int-ble-prefix.ndjson','--out',str(native_cases)],check=True)
 native_manifest=json.loads((native_cases/'manifest.json').read_text())
 contextual_cases=OUT/'contextual-inputs-prior'
 subprocess.run(['python3',str(ROOT.parent/'nucleus-contextual-proof-20261104/generate.py'),'--source','/tmp/dite-prefix.ndjson','--out',str(contextual_cases)],check=True)
 contextual_manifest=json.loads((contextual_cases/'manifest.json').read_text())
 shutil.copyfile('/tmp/dite-prefix.ndjson',contextual_cases/'dite.ndjson')
 contextual_manifest.insert(0,dict(case='authentic-dite-congr',file='dite.ndjson',sha256='53b48e5b9a4ee62f201d0e1f5eec26116446a1c511ca5d529767f64838fd22de',expect_reference=0))
 def additional(binary,env):
  test=t.run_group(['cargo','test','--release','--locked','--manifest-path',str(kernel/'Cargo.toml'),'--lib','contextual_negation_proof_tests','--','--include-ignored','--test-threads=1'],env=build_env|env,capture_output=True,timeout=600)
  (OUT/'native-completion-tests.stdout').write_bytes(test.stdout);(OUT/'native-completion-tests.stderr').write_bytes(test.stderr)
  assert test.returncode==0 and b'10 passed; 0 failed; 0 ignored;'in test.stdout
  old=BASE/'candidate/nucleus';old.chmod(0o755)
  red=t.measure(old,source,env,OUT/'red-native',timeout=240,perf=False)
  assert red['rc']==2 and 'dite_congr' in(OUT/'red-native/stderr').read_text()
  C.check_controls(binary,native_manifest,native_cases,env,'native_gate.json','native-differential')
  C.check_controls(binary,contextual_manifest,contextual_cases,env,'contextual_gate.json','contextual-differential')
  C.check_controls(binary,manifest,cases,env,'neutral_gate.json','neutral-differential',dict(red=red))
 q,baseline=G.qualify_candidate((kernel,binary,build_env,arm),BASE,OUT,additional_gate=additional)
 assert q['qualified']and not q['verdict_changes']and q['extra_unchanged']and q['controls_unchanged']
 full=json.loads((OUT/'full.json').read_text());reference=Path('/tmp/k-reference/bundle/kernel');assert t.digest(reference)==C.REF_SHA
 assert full['source_sha']==t.INPUT_SHA and full['binary_sha']==q['binary_sha']
 assert full['result']['rc'] in(0,2),'Full Mathlib may neither reject nor crash/timeout'
 frontier=None
 if full['result']['rc']==2:
  assert full.get('next_frontier') and full.get('terminal'),'UNKNOWN needs an extracted concrete frontier'
  old_full=json.loads((BASE/'full.json').read_text())
  assert full['next_frontier']['record']>old_full['next_frontier']['record'],'Full-input coverage must advance beyond the parent frontier'
  frontier=OUT/'frontier-reference.ndjson'
  subprocess.run(['zstd','-dq',str(OUT/'next-frontier.ndjson.zst'),'-o',str(frontier)],check=True)
  assert t.digest(frontier)==full['next_frontier']['sha256']
  parse=C.captured([str(reference),'--parse-only',str(frontier)],OUT/'frontier-oracle/parse')
  ref=C.captured([str(reference),str(frontier)],OUT/'frontier-oracle/reference',timeout=240)
  assert parse==ref==0,'The first new decline must be official-valid'
  frontier.unlink()
  full['frontier_official_reference']=dict(binary_sha=C.REF_SHA,parse_rc=parse,rc=ref,source_sha=full['next_frontier']['sha256'])
  t.write_json(OUT/'full.json',full)
 else:
  assert full['complete_mathlib_accept'] is True
 totals=[sum(row['counts'][i]for row in q['native']['targets'].values())for i in range(5)]
 q['boundary']='Bounded independently checked constant-local and distinct-constant proof conversion; source inference, Prop formation, exact proposition conversion and scoped prerequisite admission preserved'
 q['promotion_parent']=BINARY;q['native_nonregression_to_promotion_parent']=True
 t.write_json(OUT/'qualification.json',dict(candidate=q))
 report=dict(status='WARRANTED_BOUNDED_SEMANTIC_EXTENSION',qualified=True,binary_sha=q['binary_sha'],source_patch_sha=q['source_patch_sha'],parent_binary=BINARY,source_controls=68,protected_controls=61,native_targets=42,native_counts=totals,known_native_failures={k:v['failures']for k,v in q['native']['targets'].items()if v['failures']},dite_eq_right_prefix_sha=INT,dite_eq_right_prefix_accept=True,full=full,no_performance_claim_different_frontier=True,no_official_rank_claim=True)
 t.write_json(OUT/'neutral-proof.json',report);print('NEUTRAL_PROOF_QUALIFIED',json.dumps(report),flush=True)
 shutil.rmtree(arm/'target',ignore_errors=True)
if __name__=='__main__':main()
