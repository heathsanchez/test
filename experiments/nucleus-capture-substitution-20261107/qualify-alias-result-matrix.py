import hashlib,json,os,pathlib,subprocess,tarfile,time,zipfile
root=pathlib.Path.cwd();out=root/'reports';out.mkdir(exist_ok=True);exp=root/'experiments/nucleus-capture-substitution-20261107'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
pins={'C':('parent.zip','f8dc913015842af9a923c6b419f29d9b2fad14e269ea8bfbbbbcce9ffd7a9b0f','base'),'A':('alias.zip','03bc26dc31884c5c34eb4ac5ea08c8c2bbc0e953916dd88280579f882702b6bf','base-A'),'B':('results.zip','cab9b94683aa78adb23a5f72621d042d355909a2f97001e1fa6b844a050884a5','base-B')}
sources={}
for tag,(archive,digest,dest)in pins.items():
 assert sha(archive)==digest
 with zipfile.ZipFile(archive)as z:assert z.testzip()is None;z.extractall(dest)
 directory=root/'variants'/tag
 with tarfile.open(root/dest/'candidate/source.tar.gz')as t:t.extractall(directory,filter='data')
 sources[tag]=directory/'metatron-kernel'
# Combined source starts from frozen B, independently qualified A is a control arm.
directory=root/'variants/AB'
with tarfile.open(root/'base-B/candidate/source.tar.gz')as t:t.extractall(directory,filter='data')
sources['AB']=directory/'metatron-kernel'
with(exp/'alias-result-combined-v2.patch').open()as f:subprocess.run(['patch','--fuzz=0','-p1','-d',str(sources['AB'])],stdin=f,check=True)
p=sources['AB']/'src/typecheck.rs';p.write_text(p.read_text()+'\n'+(exp/'short-alias-controls.rs').read_text())
interaction=(exp/'alias-pi-interaction-tests.rs').read_text()
flags=json.load(open('base/flags.json'));env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(flags);env['RUST_MIN_STACK']='16777216';env['CARGO_BUILD_JOBS']='2'
matrix=[]
for tag,source in sources.items():
 p=source/'src/typecheck.rs';p.write_text(p.read_text()+'\n'+interaction)
 local={**env,'CARGO_TARGET_DIR':str(root/'target-arms'/tag)};start=time.monotonic()
 with(out/('interaction-'+tag+'.log')).open('wb')as log:
  r=subprocess.run(['cargo','test','--locked','--features','diagnostics','--manifest-path',str(source/'Cargo.toml'),'alias_pi_interaction_controls'],stdout=log,stderr=subprocess.STDOUT,env=local,timeout=1200)
 text=(out/('interaction-'+tag+'.log')).read_text()
 if tag!='AB':
  assert r.returncode==101,(tag,r.returncode)
  assert 'short_alias_to_dependent_function_reuses_completed_pi ... FAILED'in text,tag
 else:assert r.returncode==0
 assert 'changed_capture_zero_work_and_unadmitted_aliases_never_reuse_pi ... ok'in text,tag
 matrix.append({'arm':tag,'rc':r.returncode,'source_typecheck_sha256':sha(p),'seconds':time.monotonic()-start})
(out/'interaction-matrix.json').write_text(json.dumps(matrix,indent=2));print('INTERACTION',json.dumps(matrix),flush=True)
source=sources['AB'];local={**env,'CARGO_TARGET_DIR':str(root/'target-arms/AB')}
with(out/'native.log').open('wb')as log:subprocess.run(['cargo','test','--locked','--features','diagnostics','--manifest-path',str(source/'Cargo.toml')],stdout=log,stderr=subprocess.STDOUT,env=local,timeout=1200,check=True)
with(out/'plain-build.log').open('wb')as log:subprocess.run(['cargo','check','--locked','--all-targets','--manifest-path',str(source/'Cargo.toml')],stdout=log,stderr=subprocess.STDOUT,env=local,timeout=1200,check=True)
subprocess.run(['cargo','build','--locked','--release','--features','diagnostics','--manifest-path',str(source/'Cargo.toml')],env=local,check=True,timeout=1200)
candidate=root/'candidate';candidate.mkdir(exist_ok=True)
binary=candidate/'metatron-kernel';binary.write_bytes((root/'target-arms/AB/release/metatron-kernel').read_bytes());binary.chmod(0o755)
with tarfile.open(candidate/'source.tar.gz','w:gz')as t:t.add(source,arcname='metatron-kernel',filter=lambda m:None if'/target/'in m.name else m)
(out/'combined-source.json').write_text(json.dumps({'base':'018135224632f72ba06a2818132c3e857d67eaad','A':'15e6dfc9caedbffcdd9c58d8a4a5f6cda2bd4e05','B':'763e7cdb7841aff1fbcfca62a538eacf99142301','binary_sha256':sha(binary),'flags':flags,'source_files':{str(p.relative_to(source)):sha(p)for p in(source/'src').rglob('*.rs')}},indent=2))
