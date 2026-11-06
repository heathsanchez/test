import os,pathlib,subprocess,zipfile,tarfile,json,hashlib,gzip,time,re,concurrent.futures,shutil
P=pathlib.Path;root=P.cwd();out=root/'reports';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def artifact(repo,id,label,digest):
 p=root/(label+'.zip')
 with p.open('wb')as f:subprocess.run(['gh','api',f'repos/{repo}/actions/artifacts/{id}/zip'],stdout=f,check=True)
 assert sha(p)==digest
 with zipfile.ZipFile(p)as z:assert z.testzip()is None;z.extractall(root/label)
artifact('heathsanchez/test',13520537513,'base','f8dc913015842af9a923c6b419f29d9b2fad14e269ea8bfbbbbcce9ffd7a9b0f')
with tarfile.open('base/candidate/source.tar.gz')as t:t.extractall(root,filter='data')
source=root/'metatron-kernel'
for line in P('base/reports/source.sha256').read_text().splitlines():
 digest,name=line.split(maxsplit=1);assert sha(name.strip())==digest
exp=root/'experiments/nucleus-capture-substitution-20261107';patch=exp/'prefix-weakening-candidate.patch'
assert sha(patch)=='42cd038ffd414de23cb395a4aec79ece6f1e53f35a1cca88ce14a2afcf308dc6'
with patch.open()as f:subprocess.run(['patch','--fuzz=0','-p1'],stdin=f,cwd=source,check=True)
controls=exp/'prefix-weakening-controls.rs';assert sha(controls)=='cecc5c202605600a542881141fb5b746104e82eb3c1da8815004f6321a7b19a2'
tc=source/'src/typecheck.rs';tc.write_text(tc.read_text()+'\n'+controls.read_text())
flags=json.loads(P('base/flags.json').read_text());assert len(flags)==24
env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(flags);env.update(RUST_MIN_STACK='16777216',CARGO_BUILD_JOBS='2')
for label,args in [('controls',['cargo','test','--locked','--profile','inquiry','--features','diagnostics','--lib','exact_prefix_weakening_controls']),('native',['cargo','test','--locked','--profile','inquiry','--features','diagnostics']),('plain',['cargo','check','--locked','--lib']),('build',['cargo','build','--locked','--release','--features','diagnostics','--bin','metatron-kernel'])]:
 with(out/(label+'.log')).open('w')as f:subprocess.run(args,cwd=source,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
artifact('leanprover/lean-kernel-arena',11272848230,'original','f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2')
with tarfile.open('original/lean-arena-tests.tar.gz')as t:t.extractall(root/'original196',filter='data')
artifact('heathsanchez/test',13507335517,'mathlib','f2446f88e13fa54e2d1a964d06bc0a4a5d35a151afbe42a1d2546a1a5a8ba879')
P('mathlib4852.ndjson').write_bytes(gzip.decompress(P('mathlib/reports/mathlib-through-LinearMap.ndjson.gz').read_bytes()))
assert sha('mathlib4852.ndjson')=='295f995252c7d8924d4dc898d137021f5081dd6283bc86e40b260045d5b6b35d'
data=P('original196/good/perf/fueled-chain.ndjson').read_bytes().splitlines(keepends=True)
for n,label,h in[(8250,'chain6','16c9e3018e740505474ab8863017798241a5b6f07597520a0a0464aed7f6ee90'),(11792,'chain9','78dfd772d8a1e6b91484434718af521885fec1386c7a841b70a12e0a7c2f56a3')]:
 P(label+'.ndjson').write_bytes(b''.join(data[:n]));assert sha(label+'.ndjson')==h
count=0;lines=[]
for line in P('mathlib4852.ndjson').read_bytes().splitlines(keepends=True):
 lines.append(line)
 if set(json.loads(line))&{'axiom','def','thm','opaque','quot','inductive'}:
  count+=1
  if count in[4679,4680]:P('mathlib'+str(count)+'.ndjson').write_bytes(b''.join(lines))
assert sha('mathlib4679.ndjson')=='cb1a3bee5ec54f9aa1af069a7ea804a566d627180e92e12e6237f4ad7f37c0e2'
assert sha('mathlib4680.ndjson')=='36eeb5ec0ecd20b8d36865ebb27b9bd98b6b9b00bcd97f5c2f90463ce58d8e88'
binary=source/'target/release/metatron-kernel'
def run(label,path,trace=False):
 e=env.copy()
 if trace:e.update(NUCLEUS_TRACE_PREFIX_REUSE='1',NUCLEUS_TRACE_DOWNSTREAM='1')
 start=time.monotonic()
 with P(path).open('rb')as inp:r=subprocess.run([str(binary)],stdin=inp,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=e,timeout=300)
 (out/(label+'.stderr')).write_bytes(r.stderr);(out/(label+'.stdout')).write_bytes(r.stdout)
 lines=r.stderr.decode().splitlines()
 return {'name':label,'input_sha256':sha(path),'rc':r.returncode,'seconds':time.monotonic()-start,'diagnostics':trace,'first_failure':next((x for x in lines if x.startswith('NUCLEUS_DOWNSTREAM:')),None),'prefix_reuse':[json.loads(x.split(':',1)[1])for x in lines if x.startswith('NUCLEUS_PREFIX_REUSE:')]}
names=['magma-list-pair-n7','magma-list-pair-n21','magma-list-deep-n21','magma-list-deep-n36','fueled-chain','grind-ring-5']
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(lambda n:run(n,'original196/good/perf/'+n+'.ndjson'),names))
assert all(r['rc']in[0,2]for r in rows)
for label in['chain6','chain9','mathlib4679','mathlib4680','mathlib4852']:
 row=run(label,label+'.ndjson');rows.append(row);assert row['rc']in[0,2]
 if label in['chain6','mathlib4679']:assert row['rc']==0,row
(out/'native-rows.json').write_text(json.dumps(rows,indent=2))
gain=any(row['rc']==0 and row['name']not in['chain6','mathlib4679']for row in rows)
for label in['chain9','mathlib4680']:
 observed=run(label+'-trace',label+'.ndjson',True);plain=next(r for r in rows if r['name']==label);assert observed['rc']==plain['rc'],(plain,observed);rows.append(observed)
counts=re.findall(r'test result: ok. (\d+) passed; \d+ failed; (\d+) ignored',(out/'native.log').read_text())
receipt={'status':'CANDIDATE'if gain else'REJECTED_AS_SUFFICIENT','source_base':'018135224632f72ba06a2818132c3e857d67eaad','base_artifact':13520537513,'patch_sha256':sha(patch),'controls_sha256':sha(controls),'binary_sha256':sha(binary),'flags':flags,'judgment_steps':262144,'new_native_reach':gain,'native_passed':sum(int(a)for a,b in counts),'native_ignored':sum(int(b)for a,b in counts),'rows':rows,'boundary':'Term-only exact-handle prefix extension. No Gamma source-equivalence quotient, contraction, result-retention expansion or budget increase; inherited extension excluded. Canonical primary replay has diagnostics absent.'}
P('candidate').mkdir(exist_ok=True);shutil.copy2(binary,'candidate/metatron-kernel')
with tarfile.open('candidate/source.tar.gz','w:gz')as t:t.add(source,arcname='metatron-kernel',filter=lambda i:None if '/target/'in i.name or i.name.endswith('/target')else i)
(out/'source.sha256').write_text(''.join(f'{sha(p)}  {p.relative_to(root)}\n'for p in sorted(source.rglob('*.rs'))if 'target'not in p.parts))
(out/'receipt.json').write_text(json.dumps(receipt,indent=2))
if gain:
 artifact('heathsanchez/test',13276400289,'portable','a9582eadc0d9893cbe39e6bcfccd79bfaec2032838851b8a487c35df16096763')
 with tarfile.open('portable/lean-arena-tests.tar.gz')as t:t.extractall(root/'arena207',filter='data')
 old=json.loads(P('base/reports/ordinary-403.json').read_text());assert len(old)==403
 def check(e):
  path=P(e['case']);assert sha(path)==e['input_sha256'];r=run('corpus-'+e['case'].replace('/','__'),path);r.update(parent=e['new'],expected=e['expected'],case=e['case'])
  assert r['rc']in[0,1,2]and(r['rc']not in[0,1]or r['rc']==e['expected']),r
  assert e['new']==2 or r['rc']==e['new'],r
  return r
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:corpus=list(pool.map(check,old))
 (out/'ordinary-403.json').write_text(json.dumps(corpus,indent=2));receipt['status']='WARRANTED_BOUNDED_NATIVE_GAIN';receipt['corpus_cases']=len(corpus)
else:receipt['corpus_cases']=0
(out/'receipt.json').write_text(json.dumps(receipt,indent=2))
