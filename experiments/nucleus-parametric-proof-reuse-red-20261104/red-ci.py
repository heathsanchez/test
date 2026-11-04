from pathlib import Path
import hashlib,tarfile,zipfile,io,json,os,subprocess
R=Path(__file__).resolve().parent;D=Path('/tmp/parametric-proof-reuse-red');D.mkdir();Z=Path('/tmp/parent.zip');sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(Z.read_bytes())=='79a49583b5e9c4742c4280075b41cdd89ba44f2d96b402af8f90ef4750897e8d'
with zipfile.ZipFile(Z)as z:
 data=z.read('candidate/source.tar.gz');assert sha(data)=='4203d0e41e00b52ec8ff4acc7182407b6658b4b9d556c8056000228e208f2318'
 manifest=json.loads(z.read('candidate/source-manifest.json'));config=json.loads(z.read('qualification.json'))['candidate']['configuration']
 with tarfile.open(fileobj=io.BytesIO(data))as t:t.extractall(D,filter='data')
S=D/'metatron-kernel';inventory=lambda:{str(p.relative_to(S)):sha(p.read_bytes())for p in S.rglob('*')if p.is_file()};assert inventory()==manifest
r=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(R/'controls.patch')],cwd=S,capture_output=True);assert r.returncode==0,(r.stdout+r.stderr).decode()
env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|config|dict(CARGO_TARGET_DIR='/tmp/parametric-proof-reuse-red-target',CARGO_BUILD_JOBS='1')
with(D/'test.stdout').open('wb')as o,(D/'test.stderr').open('wb')as e:r=subprocess.run(['cargo','test','--release','--locked','--manifest-path',str(S/'Cargo.toml'),'--lib','universe_parametric_source_controls','--','--include-ignored'],env=env,stdout=o,stderr=e,timeout=900)
text=(D/'test.stdout').read_text();expected=['completed_parametric_fact_reuses_with_one_paid_root_step','broad_completed_fact_never_grants_strict_identity_until_strictly_reproved','failed_or_exhausted_parametric_obligations_never_become_reusable'];red=r.returncode!=0 and '10 passed; 3 failed;'in text and all(('::'+n+' ... FAILED')in text for n in expected)
report=dict(status='RED_CONFIRMED'if red else'UNEXPECTED',rc=r.returncode,parent_artifact_sha256=sha(Z.read_bytes()),controls_sha256=sha((R/'controls.patch').read_bytes()),parent_binary='82ebbce2278e54f82667e4d12793034acdf72f329b989e4605cf65473c9de715',configuration=config,expected_failed=expected,no_production_change=True,no_promotion=True)
(D/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert red,text[-4000:]
