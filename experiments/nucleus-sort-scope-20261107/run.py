import os,pathlib,subprocess,zipfile,tarfile,json,hashlib,gzip,time,re
P=pathlib.Path;root=P.cwd();out=root/'reports';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def artifact(repo,id,label,digest):
 p=root/(label+'.zip')
 with p.open('wb')as f:subprocess.run(['gh','api',f'repos/{repo}/actions/artifacts/{id}/zip'],stdout=f,check=True)
 assert sha(p)==digest
 with zipfile.ZipFile(p)as z:assert z.testzip()is None;z.extractall(root/label)
artifact('heathsanchez/test',13554703450,'base','9f08545e95049636f1a689ec57bc859c1cef8594e2a78ba41c0442765e9d249b')
with tarfile.open('base/candidate/source.tar.gz')as t:t.extractall(root,filter='data')
source=root/'metatron-kernel'
for line in P('base/reports/source.sha256').read_text().splitlines():
 digest,name=line.split(maxsplit=1);assert sha(name.strip())==digest
flags=json.loads(P('base/reports/receipt.json').read_text())['flags'];assert len(flags)==24
env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(flags);env.update(RUST_MIN_STACK='16777216',CARGO_BUILD_JOBS='2')
exp=root/'experiments/nucleus-sort-scope-20261107'
patch=exp/'candidate.patch'
assert sha(patch)=='37fb64406d8924dc174276116e1ed358ef0421148ea0fbcf98500df73fb5f666'
with patch.open()as f:subprocess.run(['patch','--fuzz=0','-p1'],stdin=f,cwd=source,check=True)
import shutil
tc=source/'src/typecheck.rs';tc.write_text(tc.read_text()+'\n'+(exp/'controls.rs').read_text())
for label,args in [('native',['cargo','test','--locked','--profile','inquiry','--features','diagnostics']),('plain',['cargo','check','--locked','--lib']),('build',['cargo','build','--locked','--release','--features','diagnostics','--bin','metatron-kernel'])]:
 with(out/(label+'.log')).open('w')as f:subprocess.run(args,cwd=source,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
artifact('leanprover/lean-kernel-arena',11272848230,'original','f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2')
with tarfile.open('original/lean-arena-tests.tar.gz')as t:t.extractall(root/'original196',filter='data')
data=P('original196/good/perf/fueled-chain.ndjson').read_bytes().splitlines(keepends=True);P('chain9.ndjson').write_bytes(b''.join(data[:11792]))
assert sha('chain9.ndjson')=='78dfd772d8a1e6b91484434718af521885fec1386c7a841b70a12e0a7c2f56a3'
artifact('heathsanchez/test',13507335517,'mathlib','f2446f88e13fa54e2d1a964d06bc0a4a5d35a151afbe42a1d2546a1a5a8ba879')
P('semiring.ndjson').write_bytes(gzip.decompress(P('mathlib/reports/mathlib-through-LinearMap.ndjson.gz').read_bytes()))
assert sha('semiring.ndjson')=='295f995252c7d8924d4dc898d137021f5081dd6283bc86e40b260045d5b6b35d'
binary=source/'target/release/metatron-kernel';pristine=root/'base/candidate/metatron-kernel';rows=[]
def run(path,label,expected=None):
 t=time.monotonic()
 with path.open('rb')as inp:r=subprocess.run([str(binary)],stdin=inp,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=600)
 (out/(label+'.stderr')).write_bytes(r.stderr);(out/(label+'.stdout')).write_bytes(r.stdout)
 row={'name':label,'input_sha256':sha(path),'rc':r.returncode,'seconds':time.monotonic()-t,'stdout_bytes':len(r.stdout),'stderr_bytes':len(r.stderr)};rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2));assert r.returncode in[0,1,2],row
 if expected is not None:assert r.returncode in expected,row
 return row
P('chain6.ndjson').write_bytes(b''.join(data[:8250]));assert sha('chain6.ndjson')=='16c9e3018e740505474ab8863017798241a5b6f07597520a0a0464aed7f6ee90'
lines=[];decls=0;prefix={}
for line in P('semiring.ndjson').read_bytes().splitlines(keepends=True):
 lines.append(line)
 if set(json.loads(line))&{'axiom','def','thm','opaque','quot','inductive'}:
  decls+=1
  if decls in[4679,4680]:prefix[decls]=b''.join(lines)
P('protected4679.ndjson').write_bytes(prefix[4679]);assert sha('protected4679.ndjson')=='cb1a3bee5ec54f9aa1af069a7ea804a566d627180e92e12e6237f4ad7f37c0e2'
P('semiring4680.ndjson').write_bytes(prefix[4680]);assert sha('semiring4680.ndjson')=='36eeb5ec0ecd20b8d36865ebb27b9bd98b6b9b00bcd97f5c2f90463ce58d8e88'
run(root/'chain6.ndjson','chain6',[0]);run(root/'protected4679.ndjson','protected4679',[0])
new_reach=False
for name in ['magma-list-pair-n7','magma-list-pair-n21','magma-list-deep-n21','magma-list-deep-n36','fueled-chain','grind-ring-5']:
 row=run(root/('original196/good/perf/'+name+'.ndjson'),name,[0,2]);new_reach|=row['rc']==0
for path,name in [(root/'chain9.ndjson','chain9'),(root/'semiring4680.ndjson','semiring4680')]:
 row=run(path,name,[0,2]);new_reach|=row['rc']==0
if rows[-1]['rc']==0:run(root/'semiring.ndjson','mathlib4852',[0,2])
replayed403=False
if new_reach:
 artifact('heathsanchez/test',13276400289,'portable','a9582eadc0d9893cbe39e6bcfccd79bfaec2032838851b8a487c35df16096763')
 with tarfile.open('portable/lean-arena-tests.tar.gz')as t:t.extractall(root/'arena207',filter='data')
 artifact('heathsanchez/test',13520537513,'authority','f8dc913015842af9a923c6b419f29d9b2fad14e269ea8bfbbbbcce9ffd7a9b0f')
 assert flags==json.loads(P('authority/flags.json').read_text())
 old=json.loads(P('authority/reports/ordinary-403.json').read_text());assert len(old)==403
 for previous in old:
  path=root/previous['case'];assert sha(path)==previous['input_sha256'];row=run(path,previous['case'].replace('/','__'));row.update(old=previous['new'],expected=previous['expected'])
  assert not(row['rc']==0 and row['expected']!=0),row
  assert not(row['rc']==1 and row['expected']!=1),row
  assert not(previous['new']in[0,1]and row['rc']!=previous['new']),row
 replayed403=True
(out/'rows.json').write_text(json.dumps(rows,indent=2))
P('candidate').mkdir(exist_ok=True)
import shutil
shutil.copy2(binary,'candidate/metatron-kernel')
with tarfile.open('candidate/source.tar.gz','w:gz')as t:t.add(source,arcname='metatron-kernel',filter=lambda i:None if '/target/'in i.name or i.name.endswith('/target')else i)
counts=re.findall(r'test result: ok. (\d+) passed; \d+ failed; (\d+) ignored',(out/'native.log').read_text())
receipt={'status':'BOUNDED_NATIVE_GAIN'if new_reach else'REJECTED_AS_SUFFICIENT','new_native_reach':new_reach,'replayed_403':replayed403,'pristine_binary_sha256':sha(pristine),'source_base_artifact':13554703450,'corpus_authority_source':'018135224632f72ba06a2818132c3e857d67eaad','patch_sha256':sha(patch),'binary_sha256':sha(binary),'flags':flags,'judgment_steps':262144,'native_passed':sum(int(a)for a,b in counts),'native_ignored':sum(int(b)for a,b in counts),'rows':rows,'boundary':'Primary original-source canonical24 flags/262144 with all diagnostic environment flags absent. Direct captured-Const App eligibility is not typing; only native empty-context completed Term(Const or Sort) results obtain scope-free bit. Existing source/env/actual-levels/flags/epoch/ordinary-view/root/reclamation guards preserved; no scope extension for other result shapes. Full403 qualification only if replayed_403 true. No global soundness/fullMathlib or performance claim.'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2))


(out/'source.sha256').write_text(''.join(f'{sha(p)}  {p.relative_to(root)}\n'for p in sorted((source/'src').rglob('*.rs'))))
