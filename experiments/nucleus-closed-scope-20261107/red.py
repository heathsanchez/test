import os,subprocess,hashlib,json,pathlib,zipfile,tarfile,re
P=pathlib.Path
with open('base.zip','wb')as f:subprocess.run(['gh','api','repos/heathsanchez/test/actions/artifacts/13520537513/zip'],stdout=f,check=True)
assert hashlib.sha256(P('base.zip').read_bytes()).hexdigest()=='f8dc913015842af9a923c6b419f29d9b2fad14e269ea8bfbbbbcce9ffd7a9b0f'
with zipfile.ZipFile('base.zip')as z:assert z.testzip()is None;z.extractall('base')
with tarfile.open('base/candidate/source.tar.gz')as t:t.extractall('.',filter='data')
p=P('metatron-kernel/src/typecheck.rs');p.write_text(p.read_text()+'\n'+P('experiments/nucleus-closed-scope-20261107/controls.rs').read_text())
env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(json.loads(P('base/flags.json').read_text()));env.update(RUST_MIN_STACK='16777216',CARGO_BUILD_JOBS='2');P('reports').mkdir(exist_ok=True)
with open('reports/red.log','w')as f:r=subprocess.run(['cargo','test','--locked','--profile','inquiry','--features','diagnostics','--lib','captured_closed_scope_contract'],cwd='metatron-kernel',env=env,stdout=f,stderr=subprocess.STDOUT)
s=P('reports/red.log').read_text();assert r.returncode==101 and '2 passed; 2 failed' in s and 'captured-closed-context-change' in s and 'captured-closed-empty-context' in s
P('reports/receipt.json').write_text(json.dumps({'status':'EXPECTED_PARENT_RED','base':'018135224632f72ba06a2818132c3e857d67eaad','rc':r.returncode,'passed':2,'intended_failed':2,'boundary':'No implementation. Closed captured term/type scope replay is absent; open source, epoch/strict/borrowed/source/depth/zero guards pass.'},indent=2))
