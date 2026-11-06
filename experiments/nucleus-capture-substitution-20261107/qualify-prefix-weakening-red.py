import pathlib,zipfile,tarfile,hashlib,subprocess,os,json,time
P=pathlib.Path;out=P('reports');out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
with open('base.zip','wb')as f:subprocess.run(['gh','api','repos/heathsanchez/test/actions/artifacts/13520537513/zip'],stdout=f,check=True)
assert sha('base.zip')=='f8dc913015842af9a923c6b419f29d9b2fad14e269ea8bfbbbbcce9ffd7a9b0f'
with zipfile.ZipFile('base.zip')as z:assert z.testzip()is None;z.extractall('base')
with tarfile.open('base/candidate/source.tar.gz')as t:t.extractall('.',filter='data')
source=P('metatron-kernel');tc=source/'src/typecheck.rs';controls=P('experiments/nucleus-capture-substitution-20261107/prefix-weakening-controls.rs');tc.write_text(tc.read_text()+'\n'+controls.read_text())
flags=json.loads(P('base/flags.json').read_text());env={**os.environ,**flags,'RUST_MIN_STACK':'16777216','CARGO_BUILD_JOBS':'2'};t=time.monotonic()
with open(out/'red.log','w')as f:r=subprocess.run(['cargo','test','--locked','--profile','inquiry','--features','diagnostics','--lib','exact_prefix_weakening_controls'],cwd=source,env=env,stdout=f,stderr=subprocess.STDOUT)
log=(out/'red.log').read_text()
assert r.returncode==101 and 'exact-prefix-paid-reuse'in log and 'prefix-dependent-paid-reuse'in log,log[-5000:]
assert 'test result: FAILED. 3 passed; 2 failed;'in log,log[-5000:]
(out/'receipt.json').write_text(json.dumps({'status':'EXPECTED_PARENT_RED','source_base':'018135224632f72ba06a2818132c3e857d67eaad','controls_sha256':sha(controls),'source_typecheck_sha256':sha(tc),'rc':r.returncode,'expected_passed':3,'expected_failed':2,'seconds':time.monotonic()-t,'boundary':'No implementation. Both cold derivations complete, then paid-one-step exact-prefix replays fail; dependent suffix/origin/epoch/borrowed scope controls included.'},indent=2))
