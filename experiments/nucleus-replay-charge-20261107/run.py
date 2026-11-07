import os,pathlib,subprocess,zipfile,tarfile,json,hashlib,gzip,time,re
P=pathlib.Path;root=P.cwd();out=root/'reports';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def artifact(repo,id,label,digest):
 p=root/(label+'.zip')
 with p.open('wb')as f:subprocess.run(['gh','api',f'repos/{repo}/actions/artifacts/{id}/zip'],stdout=f,check=True)
 assert sha(p)==digest
 with zipfile.ZipFile(p)as z:assert z.testzip()is None;z.extractall(root/label)
artifact('heathsanchez/test',13555074038,'base','42bfe782d0499049dc89512212e2f76170c4fbc1a233dcf7a8a77e886ec66840')
with tarfile.open('base/candidate/source.tar.gz')as t:t.extractall(root,filter='data')
source=root/'metatron-kernel'
flags=json.loads(P('base/reports/receipt.json').read_text())['flags'];assert len(flags)==24
env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(flags);env.update(RUST_MIN_STACK='16777216',CARGO_BUILD_JOBS='2')
exp=root/'experiments/nucleus-replay-charge-20261107'
patch=exp/'observer.patch'
assert sha(patch)=='bf27ab26137f5c576c740670dbcafb3a2f82944ffe7096ebd7d129f26c266a7e'
with patch.open()as f:subprocess.run(['patch','--fuzz=0','-p1'],stdin=f,cwd=source,check=True)
import shutil
shutil.copy2(exp/'charge_trace.rs',source/'src/charge_trace.rs')
for label,args in [('native',['cargo','test','--locked','--profile','inquiry','--features','diagnostics']),('plain',['cargo','check','--locked','--lib']),('build',['cargo','build','--locked','--release','--features','diagnostics','--bin','metatron-kernel'])]:
 with(out/(label+'.log')).open('w')as f:subprocess.run(args,cwd=source,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
artifact('leanprover/lean-kernel-arena',11272848230,'original','f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2')
with tarfile.open('original/lean-arena-tests.tar.gz')as t:t.extractall(root/'original196',filter='data')
data=P('original196/good/perf/fueled-chain.ndjson').read_bytes().splitlines(keepends=True);P('chain9.ndjson').write_bytes(b''.join(data[:11792]))
assert sha('chain9.ndjson')=='78dfd772d8a1e6b91484434718af521885fec1386c7a841b70a12e0a7c2f56a3'
binary=source/'target/release/metatron-kernel';rows=[]
pristine=root/'base/candidate/metatron-kernel';pristine.chmod(0o755)
for name in ['chain9']:
 pair=[]
 for enabled in ['pristine',False,True]:
  label=name+('-pristine'if enabled=='pristine'else'-on'if enabled else'-off');e={**env,'NUCLEUS_TRACE_DOWNSTREAM':'1'}
  if enabled is True:e['NUCLEUS_TRACE_CLOSED_ACTIVATION']='1'
  executable=pristine if enabled=='pristine'else binary
  t=time.monotonic()
  with P(name+'.ndjson').open('rb')as inp:r=subprocess.run([str(executable)],stdin=inp,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=e,timeout=300)
  (out/(label+'.stderr')).write_bytes(r.stderr);(out/(label+'.stdout')).write_bytes(r.stdout)
  lines=r.stderr.decode().splitlines()
  row={'name':name,'observer_on':enabled,'rc':r.returncode,'seconds':time.monotonic()-t,'input_sha256':sha(name+'.ndjson'),'first_failure':next((x for x in lines if x.startswith('NUCLEUS_DOWNSTREAM:')),None),'observations':[json.loads(x.split(':',1)[1])for x in lines if x.startswith('NUCLEUS_CLOSED_ACTIVATION:')]}
  assert r.returncode==2
  pair.append(row);rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2))
 assert pair[0]['first_failure']==pair[1]['first_failure']==pair[2]['first_failure']
 assert not pair[0]['observations']and not pair[1]['observations']and pair[2]['observations']
P('candidate').mkdir(exist_ok=True)
import shutil
shutil.copy2(binary,'candidate/metatron-kernel')
with tarfile.open('candidate/source.tar.gz','w:gz')as t:t.add(source,arcname='metatron-kernel',filter=lambda i:None if '/target/'in i.name or i.name.endswith('/target')else i)
counts=re.findall(r'test result: ok. (\d+) passed; \d+ failed; (\d+) ignored',(out/'native.log').read_text())
receipt={'status':'OBSERVATION_ONLY','pristine_binary_sha256':sha(pristine),'source_base_artifact':13555074038,'patch_sha256':sha(patch),'binary_sha256':sha(binary),'flags':flags,'judgment_steps':262144,'native_passed':sum(int(a)for a,b in counts),'native_ignored':sum(int(b)for a,b in counts),'rows':rows,'boundary':'Source61 only in actual failed chain9 owner. Pristine candidate/OFF/ON preserve owner/reason/verdict; independent32-unit sampled structural gate plus fixed<=4 parent metadata reads per operand; strict/inherited/current canonical flags are metadata. No semantic fuel/cache mutation or saved-work claim. No fresh whole corpus/protected-prefix qualification for observer.'}
observation = next(o for o in rows[-1]['observations'] if o['stage']=='theorem.value')

assert observation['root_debit']==262144
assert sum(observation['infer_class_debit'])==observation['root_debit']
assert observation['unclosed']==observation['anomalies']==0
assert sum(observation['exclusive_by_route'])==observation['root_debit']
receipt['boundary']='Exclusive attribution of C2 chain9 theorem.value root-counter decrements. Nested local counters are excluded unless debited by caller. Trace flags shared in pristine/OFF/ON parity. No runtime savings estimate.'
(out/'receipt.json').write_text(json.dumps(receipt,indent=2))
