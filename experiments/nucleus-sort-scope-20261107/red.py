import os,subprocess,hashlib,json,pathlib,zipfile,tarfile,re
P=pathlib.Path
with open('base.zip','wb')as f:subprocess.run(['gh','api','repos/heathsanchez/test/actions/artifacts/13554703450/zip'],stdout=f,check=True)
assert hashlib.sha256(P('base.zip').read_bytes()).hexdigest()=='9f08545e95049636f1a689ec57bc859c1cef8594e2a78ba41c0442765e9d249b'
with zipfile.ZipFile('base.zip')as z:assert z.testzip()is None;z.extractall('base')
with tarfile.open('base/candidate/source.tar.gz')as t:t.extractall('.',filter='data')
p=P('metatron-kernel/src/typecheck.rs');p.write_text(p.read_text()+'\n'+P('experiments/nucleus-sort-scope-20261107/controls.rs').read_text())
env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(json.loads(P('base/reports/receipt.json').read_text())['flags']);env.update(RUST_MIN_STACK='16777216',CARGO_BUILD_JOBS='2');P('reports').mkdir(exist_ok=True)
with open('reports/red.log','w')as f:r=subprocess.run(['cargo','test','--locked','--profile','inquiry','--features','diagnostics','--lib','captured_sort_scope_controls'],cwd='metatron-kernel',env=env,stdout=f,stderr=subprocess.STDOUT)
s=P('reports/red.log').read_text();assert r.returncode==101 and '0 passed; 1 failed' in s and 'closed-sort-term-paid-reuse' in s
P('reports/receipt.json').write_text(json.dumps({'status':'EXPECTED_PARENT_RED','base':'de67a048a8704a507424b2aeadb9e9cfebbcd2c1','rc':r.returncode,'passed':0,'intended_failed':1,'boundary':'Current qualified candidate completes the captured application with a Sort-source Term type; paid scope replay fails before rule extension.'},indent=2))
