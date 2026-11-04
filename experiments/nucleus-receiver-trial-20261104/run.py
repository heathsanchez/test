from pathlib import Path
import json,hashlib,zipfile,tarfile,subprocess,os,shutil
ROOT=Path(__file__).resolve().parent;R=Path('/tmp/nucleus-receiver-trials');R.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(Path('/tmp/receiver-parent.zip'))=='9d0ffa1d7ef5c09121477e7543c5abf1b35ec56391dd53fc89d755d737e43e73'
with zipfile.ZipFile('/tmp/receiver-parent.zip')as z:z.extractall(R/'parent')
P=R/'parent';q=json.loads((P/'qualification.json').read_text())['candidate'];assert q['qualified']and q['binary_sha']=='173ff543e6fe368d501fe2c0682e98673fd4b259a6ddc1745fcbee76ff99fb1e'
with tarfile.open(P/'candidate/source.tar.gz')as t:t.extractall(R/'source',filter='data')
source=R/'source/metatron-kernel'
for n,h in json.loads((P/'candidate/source-manifest.json').read_text()).items():assert sha(source/n)==h
subprocess.run(['zstd','-dq',str(P/'next-frontier.ndjson.zst'),'-o',str(R/'original.ndjson')],check=True)
subprocess.run(['python3',str(ROOT.parent/'nucleus-contextual-frontier-readback-20261104/frontier.py'),'--source',str(R/'original.ndjson'),'--out',str(R/'goal'),'--target','AddMonoidAlgebra.nonUnitalNonAssocSemiring._proof_1'],check=True)
input=R/'goal/signature-diagnostic.ndjson';assert sha(input)=='1022e5dc308231b91a2d8833a26006d1d082339785d61a09fc7427b30d8c0bdf'
env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|q['configuration']|dict(NUCLEUS_TRACE_DOWNSTREAM='1');rows=[]
for mode in ['parent','quarter','skip']:
 arm=R/mode;arm.mkdir()
 if mode=='parent':binary=P/'candidate/nucleus';binary.chmod(0o755)
 else:
  kernel=arm/'metatron-kernel';shutil.copytree(source,kernel)
  p=kernel/'src/checker.rs';s=p.read_text();n='        let declaration = export.declarations[declaration_index].clone();';assert s.count(n)==1;s=s.replace(n,n+'\n        #[cfg(feature="diagnostics")]\n        let _receiver_scope=crate::convert::receiver_trial::Scope::enter(matches!(&declaration,Declaration::Theorem{name,..}if *name==NameId(26089)));');p.write_text(s)
  p=kernel/'src/convert.rs';s=p.read_text();a=s.index('fn compare_neutral_heads(');n='''            let mut source_work = budget.saturating_sub(1);
            if exact_neutral_source_congruence(checker, left_structure, right_structure, &mut source_work) {
                return Judgment::proven((), "exact-source-neutral-receiver-congruence");
            }''';assert s[a:].count(n)==1
  grant='(source_work/4).min(1024)'if mode=='quarter'else'0'
  v='''            let mut source_work=budget.saturating_sub(1);
            let allowance=if receiver_trial::active(){GRANT}else{source_work};
            let mut trial=allowance;
            let proved=allowance>0&&exact_neutral_source_congruence(checker,left_structure,right_structure,&mut trial);
            source_work-=allowance-trial;
            if proved{return Judgment::proven((),"exact-source-neutral-receiver-congruence");}'''.replace('GRANT',grant)
  s=s[:a]+s[a:].replace(n,v,1);s+='''
#[cfg(feature="diagnostics")]
pub(crate)mod receiver_trial{
 use std::cell::Cell;thread_local!{static ACTIVE:Cell<bool>=const{Cell::new(false)};}
 pub(crate)struct Scope(bool);impl Scope{pub(crate)fn enter(active:bool)->Self{Self(ACTIVE.with(|x|x.replace(active)))}}
 impl Drop for Scope{fn drop(&mut self){ACTIVE.with(|x|x.set(self.0));}}
 pub(super)fn active()->bool{ACTIVE.with(Cell::get)}
}
''';p.write_text(s)
  files=sorted(p for p in kernel.rglob('*')if p.is_file());(arm/'source-manifest.json').write_text(json.dumps({str(p.relative_to(kernel)):sha(p)for p in files},indent=2))
  build_env=os.environ|dict(CARGO_TARGET_DIR=str(arm/'target'))
  with(arm/'build.log').open('wb')as f:r=subprocess.run(['cargo','build','--release','--locked','--manifest-path',str(kernel/'Cargo.toml'),'--features','diagnostics'],env=build_env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
  assert r.returncode==0
  binary=arm/'target/release/metatron-kernel';shutil.copy2(binary,arm/'nucleus')
 with input.open('rb')as i,(arm/'stdout').open('wb')as out,(arm/'stderr').open('wb')as err:r=subprocess.run([str(binary)],stdin=i,stdout=out,stderr=err,env=env,timeout=900)
 assert r.returncode in(0,2)
 row=dict(mode=mode,rc=r.returncode,binary_sha=sha(binary),input_sha=sha(input),terminal=(arm/'stderr').read_text()[-3000:]);rows.append(row);print('RECEIVER_TRIAL_ROW',json.dumps(row),flush=True)
 if mode!='parent':shutil.rmtree(arm/'target')
 (R/'report.json').write_text(json.dumps(dict(status='COMPLETE'if len(rows)==3 else'RUNNING',diagnostic_only=True,target_scoped_counterfactual=True,no_promotion=True,no_speed_claim=True,rows=rows),indent=2))
