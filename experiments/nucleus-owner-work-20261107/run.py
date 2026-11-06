import os,subprocess,json,hashlib,zipfile,tarfile,pathlib,time,gzip
P=pathlib.Path;root=P.cwd();out=root/'reports';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def artifact(repo,id,name,digest):
 p=root/(name+'.zip')
 with p.open('wb')as f:subprocess.run(['gh','api',f'repos/{repo}/actions/artifacts/{id}/zip'],stdout=f,check=True)
 assert sha(p)==digest,(id,sha(p))
 with zipfile.ZipFile(p)as z:assert z.testzip()is None;z.extractall(root/name)
artifact('heathsanchez/test',13520537513,'base','f8dc913015842af9a923c6b419f29d9b2fad14e269ea8bfbbbbcce9ffd7a9b0f')
artifact('leanprover/lean-kernel-arena',11272848230,'arena','f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2')
with tarfile.open('base/candidate/source.tar.gz')as t:t.extractall(root,filter='data')
with tarfile.open('arena/lean-arena-tests.tar.gz')as t:t.extractall(root/'inputs',filter='data')
for line in P('base/reports/source.sha256').read_text().splitlines():
 digest,name=line.split(maxsplit=1);assert sha(name.strip())==digest
source=root/'metatron-kernel';exp=root/'experiments/nucleus-owner-work-20261107'
with (exp/'owner-work.patch').open()as f:subprocess.run(['patch','--fuzz=0','-p1'],cwd=source,stdin=f,check=True)
(source/'src/owner_work.rs').write_bytes((exp/'owner_work.rs').read_bytes())
flags=json.loads(P('base/flags.json').read_text());env={**os.environ,**flags,'RUST_MIN_STACK':'16777216','CARGO_BUILD_JOBS':'2'}
for label,args in [('native',['cargo','test','--locked','--profile','inquiry','--features','diagnostics']),('build',['cargo','build','--locked','--profile','inquiry','--features','diagnostics','--bin','metatron-kernel','--bin','nucleus-census'])]:
 with (out/(label+'.log')).open('w')as f:subprocess.run(args,cwd=source,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
binary=source/'target/inquiry/metatron-kernel';census=source/'target/inquiry/nucleus-census';baseline=root/'base/candidate/metatron-kernel';baseline.chmod(0o755)
full=root/'inputs/good/perf/fueled-chain.ndjson';data=full.read_bytes().splitlines(keepends=True)
assert hashlib.sha256(b''.join(data[:11792])).hexdigest()=='78dfd772d8a1e6b91484434718af521885fec1386c7a841b70a12e0a7c2f56a3'
prefix=root/'chain9.ndjson';prefix.write_bytes(b''.join(data[:11792]));rows=[]
artifact('heathsanchez/test',13507335517,'mathlib-source','f2446f88e13fa54e2d1a964d06bc0a4a5d35a151afbe42a1d2546a1a5a8ba879')
original=gzip.decompress(P('mathlib-source/reports/mathlib-through-LinearMap.ndjson.gz').read_bytes())
assert hashlib.sha256(original).hexdigest()=='295f995252c7d8924d4dc898d137021f5081dd6283bc86e40b260045d5b6b35d'
lines=[];count=0
for line in original.splitlines(keepends=True):
 lines.append(line)
 if set(json.loads(line))&{'axiom','def','thm','opaque','quot','inductive'}:
  count+=1
  if count==4680:break
assert count==4680
semiring=root/'semiring.ndjson';semiring.write_bytes(b''.join(lines))

for target,target_owner,target_input in [('chain9','chain9_datF',prefix),('semiring','AddMonoidAlgebra.semiring',semiring)]:
 target_rows=[]
 for label,exe,extra in [('parent',baseline,{}),('off',binary,{}),('on',binary,{'NUCLEUS_DIAGNOSTIC_WORK_OWNER':target_owner})]:
  t=time.monotonic()
  with target_input.open('rb')as f:r=subprocess.run([str(exe)],stdin=f,env={**env,**extra,'NUCLEUS_TRACE_DOWNSTREAM':'1'},stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=600)
  (out/(target+'-'+label+'.stderr')).write_bytes(r.stderr);(out/(target+'-'+label+'.stdout')).write_bytes(r.stdout)
  row={'target':target,'input_sha256':sha(target_input),'arm':label,'exit':r.returncode,'elapsed_seconds':time.monotonic()-t,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest()};rows.append(row);target_rows.append(row)
  assert r.returncode==2,(target,label,r.returncode)
  failed=[x for x in r.stderr.decode().splitlines()if x.startswith('NUCLEUS_DOWNSTREAM:name=')]
  assert len(failed)==1 and ('name='+target_owner+':stage=') in failed[0] and 'verdict=UNKNOWN:reason=application-function-type' in failed[0],(target,label,failed)
  if label=='on':
   reports=[json.loads(x.split(':',1)[1])for x in r.stderr.decode().splitlines()if x.startswith('NUCLEUS_OWNER_WORK:')];assert len(reports)==1 and reports[0]['owner']==target_owner and reports[0]['acceptance_authority']is False
   (out/(target+'-owner-work.json')).write_text(json.dumps(reports[0],indent=2))
 assert len({x['stdout_sha256']for x in target_rows})==1
 (out/'arms.json').write_text(json.dumps(rows,indent=2))
# Unchanged authoritative valid and malformed controls, with observer selected
# only for chain9, do not obtain diagnostic assumptions or a new verdict path.
controls=[]
for p in sorted((root/'inputs').rglob('*.ndjson')):
 if '/bad/'not in str(p)and '/tutorial/'not in str(p):continue
 for arm,exe in [('parent',baseline),('observer',binary)]:
  with p.open('rb')as f:r=subprocess.run([str(exe)],stdin=f,env={**env,'NUCLEUS_DIAGNOSTIC_WORK_OWNER':'chain9_datF'},stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120)
  controls.append({'case':str(p.relative_to(root/'inputs')),'arm':arm,'exit':r.returncode})
 assert controls[-2]['exit']==controls[-1]['exit']and controls[-1]['exit']in[0,1,2],str(p)
(out/'matched-controls.json').write_text(json.dumps(controls,indent=2));(out/'arms.json').write_text(json.dumps(rows,indent=2))
(out/'source.sha256').write_text(''.join(f'{sha(p)}  {p.relative_to(root)}\n'for p in sorted((source/'src').rglob('*.rs'))))
P('candidate').mkdir(exist_ok=True)
with tarfile.open('candidate/source.tar.gz','w:gz')as t:
 t.add(source,arcname='metatron-kernel',filter=lambda i:None if '/target/'in i.name or i.name.endswith('/target')else i)
import shutil
shutil.copy2(binary,'candidate/metatron-kernel');shutil.copy2(census,'candidate/nucleus-census');shutil.copy2('base/flags.json','flags.json')
(out/'receipt.json').write_text(json.dumps({'diagnostic_only':True,'acceptance_authority':False,'source_parent':'018135224632f72ba06a2818132c3e857d67eaad','source_artifact':13520537513,'input_sha256':{'chain9':sha(prefix),'semiring':sha(semiring)},'binary_sha256':sha(binary),'profile':'inquiry','matched_arms':rows,'controls':len(controls)//2,'source_scope':'ordinary original chain9 and semiring prefixes, standard262144; observer has no semantic output','interpretation':'row debits overlap; coarse source families do not establish scope equivalence; no efficiency or completion promotion'},indent=2))
