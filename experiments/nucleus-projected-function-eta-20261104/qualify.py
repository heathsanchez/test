"""Qualify source-scoped telescope reuse and projected function eta."""
import importlib.util,json,re,shutil,subprocess,tarfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('performance_gates',ROOT.parent/'nucleus-performance-gates-20261104/gate.py')
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
C,Q,t=G.C,G.Q,G.t
BASE=Path('/tmp/quotient-metered-qualified')
OUT=Path('/tmp/nucleus-projected-function-eta')
BINARY='ec137270ead2aee950c8402b4baff87520ef3f2d176a4d2ce7e76ba54d9be997'
INT='231655af734415d00fcc7dc83cffe7d96f97406d1d3cd93554ff49aa6de8e521'

def main():
 OUT.mkdir(exist_ok=True);arm=OUT/'candidate';arm.mkdir()
 parent=json.loads((BASE/'qualification.json').read_text())['candidate']
 assert parent['qualified']and parent['binary_sha']==BINARY and t.digest(BASE/'candidate/nucleus')==BINARY
 assert t.digest(BASE/'candidate/source.tar.gz')=='2f268e78bcf2fbadefc1c4224753c2b51eaf2544d17c9e01c14d8659b12065de'
 assert t.digest(BASE/'candidate/source-manifest.json')=='c44e824a9ecb504cd57a744ac95153b240ac39659c54d65b41c44377bb19ca8e'
 with tarfile.open(BASE/'candidate/source.tar.gz')as archive:archive.extractall(arm,filter='data')
 kernel=arm/'metatron-kernel'
 for name,sha in json.loads((BASE/'candidate/source-manifest.json').read_text()).items():
  path=PurePosixPath(name);assert not path.is_absolute()and '..'not in path.parts;assert t.digest(kernel/name)==sha,name
 patch=ROOT/'projected-function-eta.patch'
 patched=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30)
 (arm/'patch.log').write_bytes(patched.stdout+patched.stderr);assert patched.returncode==0
 (arm/'source.patch').write_bytes((BASE/'candidate/source.patch').read_bytes()+patch.read_bytes())
 files=sorted(p for p in kernel.rglob('*')if p.is_file())
 t.write_json(arm/'source-manifest.json',{str(p.relative_to(kernel)):t.digest(p)for p in files})
 with tarfile.open(arm/'source.tar.gz','w:gz')as archive:
  for p in files:archive.add(p,arcname='metatron-kernel/'+str(p.relative_to(kernel)))
 binary,build_env=t.build(kernel,arm);assert binary is not None
 source=Path('/tmp/singleton-add-prefix.ndjson');assert t.digest(source)==INT
 cases=OUT/'native-inputs'
 subprocess.run(['python3',str(ROOT.parent/'nucleus-contextual-frontier-readback-20261104/frontier.py'),'--source','/tmp/mathlib.ndjson','--out',str(OUT/'foldlm-original'),'--target','List.foldlM_cons'],check=True)
 subprocess.run(['python3',str(ROOT.parent/'nucleus-contextual-frontier-readback-20261104/frontier.py'),'--source','/tmp/mathlib.ndjson','--out',str(OUT/'foldrm-original'),'--target','List.foldrM_cons'],check=True)
 subprocess.run(['python3',str(ROOT/'generate.py'),'--source',str(source),'--foldlm',str(OUT/'foldlm-original/next-frontier.ndjson'),'--foldrm',str(OUT/'foldrm-original/next-frontier.ndjson'),'--out',str(cases)],check=True)
 manifest=json.loads((cases/'manifest.json').read_text());manifest.insert(0,dict(case='authentic-original-singleton-add',file='dite.ndjson',sha256=INT,expect_reference=0));shutil.copyfile(source,cases/'dite.ndjson');assert len(manifest)==9
 native_cases=OUT/'native-inputs-prior'
 subprocess.run(['python3',str(ROOT.parent/'nucleus-native-completion-20261104/generate.py'),'--source','/tmp/int-ble-prefix.ndjson','--out',str(native_cases)],check=True)
 native_manifest=json.loads((native_cases/'manifest.json').read_text())
 contextual_cases=OUT/'contextual-inputs-prior'
 subprocess.run(['python3',str(ROOT.parent/'nucleus-contextual-proof-20261104/generate.py'),'--source','/tmp/dite-prefix.ndjson','--out',str(contextual_cases)],check=True)
 contextual_manifest=json.loads((contextual_cases/'manifest.json').read_text())
 shutil.copyfile('/tmp/dite-prefix.ndjson',contextual_cases/'dite.ndjson')
 contextual_manifest.insert(0,dict(case='authentic-dite-congr',file='dite.ndjson',sha256='53b48e5b9a4ee62f201d0e1f5eec26116446a1c511ca5d529767f64838fd22de',expect_reference=0))
 neutral_cases=OUT/'neutral-inputs-prior'
 subprocess.run(['python3',str(ROOT.parent/'nucleus-neutral-proof-20261104/generate.py'),'--source','/tmp/right-dite-prefix.ndjson','--out',str(neutral_cases)],check=True)
 neutral_manifest=json.loads((neutral_cases/'manifest.json').read_text())
 shutil.copyfile('/tmp/right-dite-prefix.ndjson',neutral_cases/'dite.ndjson')
 neutral_manifest.insert(0,dict(case='authentic-dite-eq-right',file='dite.ndjson',sha256='5937f7e74092f8c4adaf8268a2ef5c1e7dabfad096549a832c559e30b4f2dece',expect_reference=0))
 record_cases=OUT/'record-inputs-prior'
 subprocess.run(['python3',str(ROOT.parent/'nucleus-record-recursor-eta-20261104/generate_prod.py'),'--source','/tmp/product-lawful-prefix.ndjson','--out',str(record_cases)],check=True)
 record_manifest=json.loads((record_cases/'manifest.json').read_text())
 shutil.copyfile('/tmp/product-lawful-prefix.ndjson',record_cases/'product.ndjson')
 record_manifest.insert(0,dict(case='authentic-product-lawful',file='product.ndjson',sha256='75c66db3fcfded589778eac59ff31d7881df1420cd741c4c42c8d119321a9355',expect_reference=0))
 spine_cases=OUT/'spine-inputs-prior'
 subprocess.run(['python3',str(ROOT.parent/'nucleus-record-eta-spine-20261104/generate.py'),'--source','/tmp/linear-reverse-prefix.ndjson','--out',str(spine_cases)],check=True)
 spine_manifest=json.loads((spine_cases/'manifest.json').read_text())
 shutil.copyfile('/tmp/linear-reverse-prefix.ndjson',spine_cases/'linear.ndjson')
 spine_manifest.insert(0,dict(case='authentic-linear-poly-reverse',file='linear.ndjson',sha256='d6a69c3a7cf4bb71ada35baa6087c7cef2bca5609385a0a46de0378df74df156',expect_reference=0))
 projection_cases=OUT/'projection-inputs-prior'
 subprocess.run(['python3',str(ROOT.parent/'nucleus-record-eta-projection-20261104/generate.py'),'--source','/tmp/normpoly-prefix.ndjson','--out',str(projection_cases)],check=True)
 projection_manifest=json.loads((projection_cases/'manifest.json').read_text())
 template_cases=OUT/'template-inputs-prior'
 subprocess.run(['python3',str(ROOT.parent/'nucleus-source-projection-eta-20261104/generate.py'),'--source','/tmp/normpoly-prefix.ndjson','--out',str(template_cases)],check=True)
 template_manifest=json.loads((template_cases/'manifest.json').read_text())
 shutil.copyfile('/tmp/normpoly-prefix.ndjson',template_cases/'normpoly.ndjson')
 template_manifest.insert(0,dict(case='authentic-original-normpoly',file='normpoly.ndjson',sha256='6c8f1d48c9b556a63dafa333d0a4344b53b4fded1c0fab5e3aa5bb831a50734a',expect_reference=0))
 capture_cases=OUT/'capture-inputs-prior'
 subprocess.run(['python3',str(ROOT.parent/'nucleus-capture-reuse-20261104/generate.py'),'--source','/tmp/ringhom-prefix.ndjson','--out',str(capture_cases)],check=True)
 capture_manifest=json.loads((capture_cases/'manifest.json').read_text())
 shutil.copyfile('/tmp/ringhom-prefix.ndjson',capture_cases/'ringhom.ndjson')
 capture_manifest.insert(0,dict(case='authentic-original-ringhom',file='ringhom.ndjson',sha256='f9ab8c3cd617710b22862c5c4243c51bc57e1c7ca9ef7ffe7de816b25fca8e5c',expect_reference=0))
 prior_guard_cases=OUT/'guard-inputs-prior'
 subprocess.run(['python3',str(ROOT.parent/'nucleus-source-conversion-guard-20261104/generate.py'),'--source','/tmp/alghom-prefix.ndjson','--out',str(prior_guard_cases)],check=True)
 prior_guard_manifest=json.loads((prior_guard_cases/'manifest.json').read_text())
 shutil.copyfile('/tmp/alghom-prefix.ndjson',prior_guard_cases/'alghom.ndjson')
 prior_guard_manifest.insert(0,dict(case='authentic-original-alghom',file='alghom.ndjson',sha256='eb2ad18e41889f28f6e0e6e9d36690ff5b4ba5d2228ec6d831cce2c695e628b1',expect_reference=0))
 prior_quotient_cases=OUT/'quotient-inputs-prior'
 subprocess.run(['python3',str(ROOT.parent/'nucleus-quotient-metered-20261104/generate.py'),'--source','/tmp/multiset-nodup-prefix.ndjson','--out',str(prior_quotient_cases)],check=True)
 prior_quotient_manifest=json.loads((prior_quotient_cases/'manifest.json').read_text())
 shutil.copyfile('/tmp/multiset-nodup-prefix.ndjson',prior_quotient_cases/'nodup.ndjson')
 prior_quotient_manifest.insert(0,dict(case='authentic-original-nodup-singleton',file='nodup.ndjson',sha256='67f330e56e94c29578eb6375167b15483277c151edc0ee2dabae9898b4dc4318',expect_reference=0))
 role_cases=OUT/'role-inputs';role_cases.mkdir();role_manifest=[]
 for label,original in [('ordinary-lift-proof','authentic.ndjson'),('ordinary-lift-beta','indirect-beta.ndjson')]:
  rows=[json.loads(line)for line in(kernel/'tests/fixtures/quotient-reuse'/original).read_text().splitlines()]
  i=next(i for i,row in enumerate(rows)if row.get('quot',{}).get('kind')=='lift');d=rows[i]['quot'];rows[i]={'axiom':dict(name=d['name'],levelParams=d['levelParams'],type=d['type'],isUnsafe=False)}
  path=role_cases/(label+'.ndjson');path.write_text(''.join(json.dumps(row,separators=(',',':'))+'\n'for row in rows))
  role_manifest.append(dict(case=label,file=path.name,sha256=t.digest(path),expect_reference=0))
 def additional(binary,env):
  test=t.run_group(['cargo','test','--release','--locked','--manifest-path',str(kernel/'Cargo.toml'),'--lib','--','--include-ignored','--test-threads=1'],env=build_env|env|{'NUCLEUS_FROZEN196':'/tmp/current208/inputs'},capture_output=True,timeout=600)
  (OUT/'native-completion-tests.stdout').write_bytes(test.stdout);(OUT/'native-completion-tests.stderr').write_bytes(test.stderr)
  assert test.returncode==0 and b'180 passed; 0 failed; 0 ignored;'in test.stdout
  old=BASE/'candidate/nucleus';old.chmod(0o755)
  red=t.measure(old,source,env,OUT/'red-native',timeout=240,perf=False)
  assert red['rc']==2 and 'NUCLEUS_DOWNSTREAM:name=Multiset.singleton_add:stage=theorem.value:' in(OUT/'red-native/stderr').read_text()
  C.check_controls(binary,native_manifest,native_cases,env,'native_gate.json','native-differential')
  C.check_controls(binary,contextual_manifest,contextual_cases,env,'contextual_gate.json','contextual-differential')
  C.check_controls(binary,neutral_manifest,neutral_cases,env,'neutral_gate.json','neutral-differential')
  C.check_controls(binary,record_manifest,record_cases,env,'record_eta_gate.json','record-eta-differential')
  C.check_controls(binary,spine_manifest,spine_cases,env,'eta_spine_gate.json','eta-spine-differential')
  C.check_controls(binary,projection_manifest,projection_cases,env,'eta_projection_gate.json','eta-projection-differential')
  C.check_controls(binary,template_manifest,template_cases,env,'source_template_gate.json','source-template-differential')
  C.check_controls(binary,capture_manifest,capture_cases,env,'capture_reuse_gate.json','capture-reuse-differential')
  C.check_controls(binary,prior_guard_manifest,prior_guard_cases,env,'source_conversion_guard_gate.json','source-conversion-guard-differential')
  C.check_controls(binary,prior_quotient_manifest,prior_quotient_cases,env,'quotient_metered_gate.json','quotient-metered-differential')
  C.check_controls(binary,role_manifest,role_cases,env,'quotient_role_gate.json','quotient-role-reference-agreement')
  C.check_controls(binary,manifest,cases,env,'typed_prefix_gate.json','typed-prefix-differential',dict(red=red))
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
 q['boundary']='Same-formed-constant typed telescope prefix invariant plus evaluated projected function eta; full source capture freshness, exact head/universe gates, all actual receiver and prefix conversions mandatory under the actual extended context, shared source exposure owner and eta reservation debited from outer converter; independent source typing preserved, no new fuel, flags or authority'
 q['promotion_parent']=BINARY;q['native_nonregression_to_promotion_parent']=True
 t.write_json(OUT/'qualification.json',dict(candidate=q))
 report=dict(status='WARRANTED_BOUNDED_SEMANTIC_EXTENSION',qualified=True,binary_sha=q['binary_sha'],source_patch_sha=q['source_patch_sha'],parent_binary=BINARY,source_controls=113,protected_controls=61,native_targets=42,native_counts=totals,known_native_failures={k:v['failures']for k,v in q['native']['targets'].items()if v['failures']},singleton_add_prefix_sha=INT,singleton_add_prefix_accept=True,additional_verified_original_prefixes=dict(foldlm_cons='7a5a71599fb8240c88553967ae3d3146d1d26d176ef3cd2388608c25c4a2da29',foldrm_cons='8fbfa485711e12b989548753fb35fd077e7bb71c9a7b5d53a91e3c4db93d87d4'),full=full,no_performance_claim_different_frontier=True,no_official_rank_claim=True)
 t.write_json(OUT/'projected-function-eta.json',report);print('PROJECTED_FUNCTION_ETA_QUALIFIED',json.dumps(report),flush=True)
 shutil.rmtree(arm/'target',ignore_errors=True)
if __name__=='__main__':main()
