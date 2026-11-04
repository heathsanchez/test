from pathlib import Path
import shutil,difflib,hashlib
R=Path(__file__).resolve().parent;B=Path('/tmp/nucleus-nested-projection-normalized/source');S=R/'source';shutil.copytree(B,S)
p=S/'src/diagnostics.rs';s=p.read_text()+'''
thread_local!{static RECEIVER_SNAPSHOT_TARGET:Cell<bool>=const{Cell::new(false)};}
pub(crate)fn receiver_snapshot_target(active:bool){RECEIVER_SNAPSHOT_TARGET.set(active)}
pub(crate)fn receiver_snapshot_target_active()->bool{RECEIVER_SNAPSHOT_TARGET.get()}
''';p.write_text(s)
p=S/'src/checker.rs';s=p.read_text();n='        let declaration = export.declarations[declaration_index].clone();';assert s.count(n)==1;s=s.replace(n,n+'\n        #[cfg(feature="diagnostics")]\n        crate::diagnostics::receiver_snapshot_target(matches!(&declaration,Declaration::Theorem{name,..}if name.0==26089));');p.write_text(s)
p=S/'src/nat.rs';s=p.read_text();n='impl BigNat {';assert s.count(n)==1;s=s.replace(n,n+'\n    #[cfg(feature="diagnostics")]\n    pub(crate) fn diagnostic_limbs(&self)->&[u32]{&self.0}\n');p.write_text(s)
p=S/'src/typecheck.rs';s=p.read_text();n='    pub(crate) fn machine(&self) -> Machine';assert s.count(n)==1;s=s.replace(n,(R/'snapshot-method.rs').read_text()+'\n'+n)
n='''                #[cfg(feature = "diagnostics")]
                if crate::run_flags::present(crate::run_flags::Flag::TraceFailedReceiverConversion)''';assert s.count(n)==1;s=s.replace(n,'''                #[cfg(feature="diagnostics")]
                if crate::diagnostics::receiver_snapshot_target_active() && expected_formed
                    && *remaining>100000 && (4..=16).contains(&context.len()){
                    if let Judgment::Unknown{residual}=&conversion{
                        self.diagnostic_receiver_snapshot(&value,expected,context,expression,frame.id(),*remaining,residual.0);
                    }
                }
'''+n);p.write_text(s)
patch=''.join(''.join(difflib.unified_diff((B/rel).read_text().splitlines(True),(S/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))for rel in['src/checker.rs','src/typecheck.rs','src/nat.rs','src/diagnostics.rs']);(R/'snapshot.patch').write_text(patch)
s=Path('/tmp/nucleus-projection-residual-probe/run.py').read_text().replace('PROJECTION_RESIDUAL:','RECEIVER_SNAPSHOT:');(R/'run.py').write_text(s);print(hashlib.sha256(patch.encode()).hexdigest())
