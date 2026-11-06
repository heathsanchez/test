import os,subprocess,json,hashlib,zipfile,tarfile,pathlib,time,gzip,re,shutil
P=pathlib.Path;root=P.cwd();out=root/'reports';out.mkdir(exist_ok=True);scope=os.environ['SCOPE']
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def artifact(repo,id,name,digest):
 p=root/(name+'.zip')
 with p.open('wb')as f:subprocess.run(['gh','api',f'repos/{repo}/actions/artifacts/{id}/zip'],stdout=f,check=True)
 assert sha(p)==digest
 with zipfile.ZipFile(p)as z:assert z.testzip()is None;z.extractall(root/name)
artifact('heathsanchez/test',13520537513,'base','f8dc913015842af9a923c6b419f29d9b2fad14e269ea8bfbbbbcce9ffd7a9b0f')
artifact('leanprover/lean-kernel-arena',11272848230,'arena','f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2')
with tarfile.open('base/candidate/source.tar.gz')as t:t.extractall(root,filter='data')
with tarfile.open('arena/lean-arena-tests.tar.gz')as t:t.extractall(root/'original196',filter='data')
for line in P('base/reports/source.sha256').read_text().splitlines():
 digest,name=line.split(maxsplit=1);assert sha(name.strip())==digest
source=root/'metatron-kernel';exp=root/'experiments/nucleus-short-alias-20261107';flags=json.loads(P('base/flags.json').read_text());env={**os.environ,**flags,'RUST_MIN_STACK':'16777216','CARGO_BUILD_JOBS':'2'}
typecheck=source/'src/typecheck.rs';typecheck.write_text(typecheck.read_text()+'\n'+(exp/'tests.rs').read_text())
if scope=='arena':
 with(out/'alias-red.log').open('w')as f:r=subprocess.run(['cargo','test','--locked','--profile','inquiry','--features','diagnostics','--lib','a_completed_short_alias'],cwd=source,env=env,stdout=f,stderr=subprocess.STDOUT)
 assert r.returncode==101 and 'completed alias must reuse its own checked source derivation' in(out/'alias-red.log').read_text()
with(exp/'short-alias.patch').open()as f:subprocess.run(['patch','--fuzz=0','-p1'],cwd=source,stdin=f,check=True)
if scope=='arena':
 with(out/'native.log').open('w')as f:subprocess.run(['cargo','test','--locked','--profile','inquiry','--features','diagnostics'],cwd=source,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
with(out/'build.log').open('w')as f:subprocess.run(['cargo','build','--locked','--release','--features','diagnostics','--bin','metatron-kernel'],cwd=source,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
binary=source/'target/release/metatron-kernel';rows=[]
def run(path,label):
 t=time.monotonic()
 with path.open('rb')as f:r=subprocess.run([str(binary)],stdin=f,env={**env,'NUCLEUS_TRACE_DOWNSTREAM':'1'},stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=600)
 (out/(label+'.stderr')).write_bytes(r.stderr);(out/(label+'.stdout')).write_bytes(r.stdout)
 row={'case':label,'input_sha256':sha(path),'new':r.returncode,'seconds':time.monotonic()-t,'failure':[x for x in r.stderr.decode().splitlines()if x.startswith('NUCLEUS_DOWNSTREAM:name=')]};rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2));return row
if scope=='arena':
 artifact('heathsanchez/test',13276400289,'portable','a9582eadc0d9893cbe39e6bcfccd79bfaec2032838851b8a487c35df16096763')
 with tarfile.open('portable/lean-arena-tests.tar.gz')as t:t.extractall(root/'arena207',filter='data')
 old=json.loads(P('base/reports/ordinary-403.json').read_text());assert len(old)==403
 for e in old:
  path=root/e['case'];assert sha(path)==e['input_sha256'];r=run(path,e['case'].replace('/','__'))
  r.update(old=e['new'],expected=e['expected']);assert r['new']in[0,1,2]
  assert not(r['new']==0 and e['expected']!=0),r
  assert not(r['new']==1 and e['expected']!=1),r
  assert not(e['new']in[0,1]and r['new']!=e['new']),r
 (out/'rows.json').write_text(json.dumps(rows,indent=2))
else:
 artifact('heathsanchez/test',13507335517,'mathlib-source','f2446f88e13fa54e2d1a964d06bc0a4a5d35a151afbe42a1d2546a1a5a8ba879')
 raw=gzip.decompress(P('mathlib-source/reports/mathlib-through-LinearMap.ndjson.gz').read_bytes());assert hashlib.sha256(raw).hexdigest()=='295f995252c7d8924d4dc898d137021f5081dd6283bc86e40b260045d5b6b35d'
 declarations=0;lines=[];prefixes={}
 for line in raw.splitlines(keepends=True):
  lines.append(line)
  if set(json.loads(line))&{'axiom','def','thm','opaque','quot','inductive'}:
   declarations+=1
   if declarations in[4679,4680]:prefixes[declarations]=b''.join(lines)
 p=root/'protected4679.ndjson';p.write_bytes(prefixes[4679]);assert sha(p)=='cb1a3bee5ec54f9aa1af069a7ea804a566d627180e92e12e6237f4ad7f37c0e2';assert run(p,'protected4679')['new']==0
 full=(root/'original196/good/perf/fueled-chain.ndjson').read_bytes().splitlines(keepends=True)
 for n,label,h in[(8250,'chain6','16c9e3018e740505474ab8863017798241a5b6f07597520a0a0464aed7f6ee90'),(11792,'chain9','78dfd772d8a1e6b91484434718af521885fec1386c7a841b70a12e0a7c2f56a3')]:
  p=root/(label+'.ndjson');p.write_bytes(b''.join(full[:n]));assert sha(p)==h;r=run(p,label);assert r['new']in[0,2]
  if label=='chain6':assert r['new']==0
 p=root/'semiring4680.ndjson';p.write_bytes(prefixes[4680]);assert sha(p)=='36eeb5ec0ecd20b8d36865ebb27b9bd98b6b9b00bcd97f5c2f90463ce58d8e88';r=run(p,'semiring4680');assert r['new']in[0,2]
 if r['new']==0:
  p=root/'mathlib4852.ndjson';p.write_bytes(raw);assert run(p,'mathlib4852')['new']in[0,2]
P('candidate').mkdir(exist_ok=True);shutil.copy2(binary,'candidate/metatron-kernel');shutil.copy2('base/flags.json','flags.json')
with tarfile.open('candidate/source.tar.gz','w:gz')as t:t.add(source,arcname='metatron-kernel',filter=lambda i:None if '/target/'in i.name or i.name.endswith('/target')else i)
(out/'source.sha256').write_text(''.join(f'{sha(p)}  {p.relative_to(root)}\n'for p in sorted((source/'src').rglob('*.rs'))))
(out/'receipt.json').write_text(json.dumps({'scope':scope,'binary_sha256':sha(binary),'profile':'release','source_base':'018135224632f72ba06a2818132c3e857d67eaad','source_artifact':13520537513,'rows':rows,'boundary':'Short actual-closure aliases only, non-strict, no inherited witness view; existing memo key, context, flags, epoch and ownership gates unchanged; no budget increase or full Mathlib claim.'},indent=2))
