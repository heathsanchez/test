from pathlib import Path
import shutil,difflib,hashlib,json
R=Path(__file__).resolve().parent;B=Path('/tmp/nucleus-universe-parametric-source/source');S=R/'source';shutil.copytree(B,S)
p=S/'src/diagnostics.rs';s=p.read_text()+'''
thread_local!{static PROJECTION_RESIDUAL_TARGET:Cell<bool>=const{Cell::new(false)};}
pub(crate)fn projection_residual_target(active:bool){PROJECTION_RESIDUAL_TARGET.set(active)}
pub(crate)fn projection_residual_target_active()->bool{PROJECTION_RESIDUAL_TARGET.get()}
pub(crate)fn projection_residual_verdict<T>(j:&crate::judgment::Judgment<T>)->&'static str{
 match j{crate::judgment::Judgment::Proven{..}=>"PROVEN",crate::judgment::Judgment::Unknown{residual}=>residual.0,crate::judgment::Judgment::Refuted{obstruction}=>obstruction.0}
}
''';p.write_text(s)
p=S/'src/checker.rs';s=p.read_text();n='        let declaration = export.declarations[declaration_index].clone();';assert s.count(n)==1;s=s.replace(n,n+'\n        #[cfg(feature="diagnostics")]\n        crate::diagnostics::projection_residual_target(matches!(&declaration,Declaration::Theorem{name,..}if name.0==26089));');p.write_text(s)
p=S/'src/convert.rs';s=p.read_text();n='''                    return Judgment::unknown("lazy-projection-value-exposure");''';assert s.count(n)==3
pair='''                    #[cfg(feature="diagnostics")]
                    if crate::diagnostics::projection_residual_target_active(){use std::sync::atomic::{AtomicUsize,Ordering};static PAIRS:AtomicUsize=AtomicUsize::new(0);if PAIRS.fetch_add(1,Ordering::Relaxed)<32{eprintln!("PROJECTION_RESIDUAL:shape=pair:depth={depth}:scope={}:budget={current_budget}:left_type={left_type:?}:left_index={left_index}:left_expr={:?}:left_env={}:left_result={}:right_type={right_type:?}:right_index={right_index}:right_expr={:?}:right_env={}:right_result={}",context.len(),left_structure.expr,left_structure.env.id(),crate::diagnostics::projection_residual_verdict(&left_value),right_structure.expr,right_structure.env.id(),crate::diagnostics::projection_residual_verdict(&right_value));}}
'''
single='''                    #[cfg(feature="diagnostics")]
                    if crate::diagnostics::projection_residual_target_active(){use std::sync::atomic::{AtomicUsize,Ordering};static SINGLES:AtomicUsize=AtomicUsize::new(0);if SINGLES.fetch_add(1,Ordering::Relaxed)<32{eprintln!("PROJECTION_RESIDUAL:shape=single:depth={depth}:scope={}:budget={current_budget}:owner={type_name:?}:index={index}:expr={:?}:env={}:pending={}:result={}",context.len(),structure.expr,structure.env.id(),spine.len(),crate::diagnostics::projection_residual_verdict(&exposed));}}
'''
pieces=s.split(n);s=pieces[0]+pair+n+pieces[1]+single+n+pieces[2]+single+n+pieces[3];p.write_text(s)
patch=''.join(''.join(difflib.unified_diff((B/rel).read_text().splitlines(True),(S/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))for rel in ['src/checker.rs','src/convert.rs','src/diagnostics.rs']);(R/'projection-residual.patch').write_text(patch)
s=Path('/tmp/nucleus-universe-parametric-source/run-frontier.py').read_text().replace("D=R/'frontier-diagnostic'","D=R/'replay'").replace("source=R/'diagnostic-source'","source=R/'source'").replace("target=R/'diagnostic-target'","target=R/'target'").replace('PARAMETRIC_FRONTIER:','PROJECTION_RESIDUAL:');(R/'run.py').write_text(s);print(hashlib.sha256(patch.encode()).hexdigest())
