from pathlib import Path
import os,json,subprocess,shutil
r=Path('/workspace/scratch/38cabe96376f');a=r/'nucleus-tournaments/capture-pair-probe';s=a/'source/metatron-kernel';shutil.copytree(r/'nucleus-tournaments/parameter-record-eta/source/metatron-kernel',s,ignore=shutil.ignore_patterns('target'),dirs_exist_ok=True)
p=s/'src/typecheck.rs';x=p.read_text();field='''    capture_pair_probe:RefCell<HashMap<(ExprId,u64,usize,ExprId,u64,usize),(Closure,Closure)>>,
''';x=x.replace('    source_opening_proofs: RefCell<HashMap',field+'    source_opening_proofs: RefCell<HashMap',1)
import re
x,n=re.subn(r'(\s*source_opening_proofs:\s*RefCell::new\(HashMap::new\(\)\),)',r'\1\n            capture_pair_probe:RefCell::new(HashMap::new()),',x);assert n==5,n
needle='''            if finish { active.remove(&pair); complete.insert(pair); retained.push((a, b)); continue }'''
repl='''            if finish { active.remove(&pair); complete.insert(pair);
                if self.capture_pair_probe.borrow().len()<8192{self.capture_pair_probe.borrow_mut().insert(pair,(a.clone(),b.clone()));}
                retained.push((a, b)); continue }
            if self.capture_pair_probe.borrow().contains_key(&pair){
                use std::sync::atomic::{AtomicUsize,Ordering};static COUNT:AtomicUsize=AtomicUsize::new(0);
                let count=COUNT.fetch_add(1,Ordering::Relaxed);
                if count<48 || count%10000==0{eprintln!("CAPTURE_PAIR_REPLAY:count={count}:authority={:?}:left={a:?}:right={b:?}:remaining={remaining}",self.authority());}
            }'''
assert needle in x;x=x.replace(needle,repl);p.write_text(x)
tool=r/'rust-runtime/toolchain/bin';env=os.environ|dict(PATH=str(tool)+':'+os.environ['PATH'],RUSTC=str(tool/'rustc'),RUSTDOC=str(tool/'rustdoc'),CARGO_HOME=str(r/'rust-runtime/cargo-home'),CARGO_TARGET_DIR=str(a/'target'))
with(a/'build.stdout').open('wb')as out,(a/'build.stderr').open('wb')as err:q=subprocess.run(['cargo','build','--release','--locked','--offline','--manifest-path',str(s/'Cargo.toml')],env=env,stdout=out,stderr=err)
print('build',q.returncode,flush=True)
if q.returncode:raise SystemExit(q.returncode)
env={k:v for k,v in env.items()if not k.startswith('NUCLEUS_')};env.update(json.loads((r/'nucleus-tournaments/receipts/stack-qualified/qualification.json').read_text())['candidate']['configuration']);env['NUCLEUS_TRACE_DOWNSTREAM']='1'
source=r/'nucleus-tournaments/source-projection-eta/next/next-frontier.ndjson'
with source.open('rb')as inp,(a/'original.stdout').open('wb')as out,(a/'original.stderr').open('wb')as err:q=subprocess.run([str(a/'target/release/metatron-kernel')],env=env,stdin=inp,stdout=out,stderr=err,timeout=180)
print('original',q.returncode,flush=True)
