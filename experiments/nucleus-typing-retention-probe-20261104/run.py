from pathlib import Path
import json,hashlib,zipfile,tarfile,subprocess,os,shutil
R=Path('/tmp/nucleus-typing-retention-probe');R.mkdir();ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(Path('/tmp/retention-parent.zip'))=='9d0ffa1d7ef5c09121477e7543c5abf1b35ec56391dd53fc89d755d737e43e73'
with zipfile.ZipFile('/tmp/retention-parent.zip')as z:z.extractall(R/'parent')
P=R/'parent';q=json.loads((P/'qualification.json').read_text())['candidate'];assert q['qualified']and q['binary_sha']=='173ff543e6fe368d501fe2c0682e98673fd4b259a6ddc1745fcbee76ff99fb1e'
with tarfile.open(P/'candidate/source.tar.gz')as t:t.extractall(R/'source',filter='data')
source=R/'source/metatron-kernel'
for n,h in json.loads((P/'candidate/source-manifest.json').read_text()).items():assert sha(source/n)==h
subprocess.run(['zstd','-dq',str(P/'next-frontier.ndjson.zst'),'-o',str(R/'original.ndjson')],check=True)
subprocess.run(['python3',str(ROOT.parent/'nucleus-contextual-frontier-readback-20261104/frontier.py'),'--source',str(R/'original.ndjson'),'--out',str(R/'hot'),'--target','AddMonoidAlgebra.instAddCommMonoid._proof_1'],check=True)
input=R/'hot/next-frontier.ndjson';assert sha(input)=='8428d5d4282a608eb77e48ff62adace23212d9487ff9e86dc2e57af7c573d5f1'
probe='''
#[cfg(feature="diagnostics")]
pub(crate)mod retention_probe{
 use std::cell::Cell;
 thread_local!{static ACTIVE:Cell<bool>=const{Cell::new(false)};static COUNTS:Cell<[u64;12]>=const{Cell::new([0;12])};}
 pub(crate)fn count(i:usize){if ACTIVE.with(Cell::get){COUNTS.with(|x|{let mut v=x.get();v[i]+=1;x.set(v);});}}
 pub(crate)struct Scope{old:bool,active:bool}
 impl Scope{pub(crate)fn enter(active:bool)->Self{let old=ACTIVE.with(|x|x.replace(active));if active{COUNTS.with(|x|x.set([0;12]));}Self{old,active}}}
 impl Drop for Scope{fn drop(&mut self){if self.active{COUNTS.with(|x|eprintln!("TYPING_RETENTION_PROBE:{:?}",x.get()));}ACTIVE.with(|x|x.set(self.old));}}
}
'''
env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|q['configuration'];rows=[]
for mode,expected in [('term','f56e757b04e95ee1a15879c0d6ead563fb92fa24de622973a196f9903ab31984'),('rich','9aa706591c59b852afd7282d7ca17d8a9b549a3a1803b368c5a81140d46c032b')]:
 arm=R/mode;arm.mkdir();kernel=arm/'metatron-kernel';shutil.copytree(source,kernel);patch=ROOT/(mode+'.patch');assert sha(patch)==expected
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(patch.resolve())],cwd=arm,check=True)
 p=kernel/'src/typecheck.rs';s=p.read_text();s=s.replace('            let set=key.set();','            retention_probe::count(0);let set=key.set();',1)
 hit='retention_probe::count(1);'if mode=='term'else'retention_probe::count(match &fact.result{TypeValue::Term(_)=>1,TypeValue::Pi{..}=>2,TypeValue::Sort(_)=>3});'
 needle='                        return Some(';i=s.index(needle,s.index('let set=key.set()'));s=s[:i]+hit+'\n'+s[i:]
 s=s.replace('            let start=table.hand[set]as usize;','            retention_probe::count(9);let start=table.hand[set]as usize;',1)
 needle='                if table.slots[index].as_ref().is_none_or(ExactTypingFact::relinquishable){';assert s.count(needle)==1
 s=s.replace(needle,'''                if table.slots[index].is_some(){retention_probe::count(7);}
                let safe=table.slots[index].as_ref().is_none_or(ExactTypingFact::relinquishable);
                if !safe{retention_probe::count(8);}
                if safe{''')
 store='retention_probe::count(4);'if mode=='term'else'retention_probe::count(match value{TypeValue::Term(_)=>4,TypeValue::Pi{..}=>5,TypeValue::Sort(_)=>6});'
 s=s.replace('                    table.slots[index]=Some(',store+'\n                    table.slots[index]=Some(',1)
 a=s.index(' fn relinquishable(&self)->bool{');b=s.index('\n }\n',a)+4
 method=''' fn relinquishable(&self)->bool{
  let roots=ROOTS;
  let safe=roots.iter().all(|root|{
   let en=roots.iter().filter(|v|v.env.id()==root.env.id()).count();let lv=roots.iter().filter(|v|v.levels.identity()==root.levels.identity()).count();
   (root.env.id()==0||root.env.strong_owners()>en)&&(root.levels.is_empty_instance()||root.levels.strong_owners()>lv)
  });
  if !safe{
   let key_dead=std::iter::once(&self._source).chain(self.context.iter()).any(|root|{
    let en=roots.iter().filter(|v|v.env.id()==root.env.id()).count();let lv=roots.iter().filter(|v|v.levels.identity()==root.levels.identity()).count();
    (root.env.id()!=0&&root.env.strong_owners()<=en)||root.levels.strong_owners()<=lv
   });retention_probe::count(if key_dead{10}else{11});
  }safe
 }'''.replace('ROOTS','self.roots().collect::<Vec<_>>()'if mode=='term'else'self.roots()')
 s=s[:a]+method+s[b:]+probe;p.write_text(s)
 p=kernel/'src/checker.rs';s=p.read_text();needle='        let declaration = export.declarations[declaration_index].clone();';assert s.count(needle)==1;s=s.replace(needle,needle+'\n        #[cfg(feature="diagnostics")]\n        let _retention_scope=crate::typecheck::retention_probe::Scope::enter(matches!(&declaration,Declaration::Theorem{name,..}if *name==NameId(19346)));');p.write_text(s)
 paths=sorted(p for p in kernel.rglob('*')if p.is_file());(arm/'source-manifest.json').write_text(json.dumps({str(p.relative_to(kernel)):sha(p)for p in paths},indent=2))
 build_env=os.environ|dict(CARGO_TARGET_DIR=str(arm/'target'))
 with(arm/'build.log').open('wb')as f:r=subprocess.run(['cargo','build','--release','--locked','--manifest-path',str(kernel/'Cargo.toml'),'--features','diagnostics'],env=build_env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 assert r.returncode==0
 binary=arm/'target/release/metatron-kernel';shutil.copy2(binary,arm/'nucleus')
 with input.open('rb')as stream,(arm/'stdout').open('wb')as out,(arm/'stderr').open('wb')as err:r=subprocess.run([str(binary)],stdin=stream,stdout=out,stderr=err,env=env,timeout=900)
 assert r.returncode==0
 import re
 counts=re.findall(r'TYPING_RETENTION_PROBE:(\[[^\n]+\])',(arm/'stderr').read_text());assert len(counts)==1
 row=dict(mode=mode,binary_sha=sha(binary),input_sha=sha(input),rc=r.returncode,counts=json.loads(counts[0]));rows.append(row);shutil.rmtree(arm/'target');print('RETENTION_PROBE_ROW',json.dumps(row),flush=True)
 report=dict(status='COMPLETE'if len(rows)==2 else'RUNNING',diagnostic_only=True,no_speedup_claim=True,no_promotion=True,schema=['eligible_calls','term_hits','pi_hits','sort_hits','term_stores','pi_stores','sort_stores','occupied_eviction_probes','blocked_eviction_probes','retention_attempts','blocked_due_to_unqueryable_key_root','blocked_only_by_result_capture'],rows=rows);(R/'report.json').write_text(json.dumps(report,indent=2))
