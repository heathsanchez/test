from pathlib import Path
import shutil,subprocess,difflib,json,hashlib
R=Path(__file__).resolve().parent;B=R/'extracted/metatron-kernel';S=R/'identity-frontier/metatron-kernel';shutil.copytree(B,S,dirs_exist_ok=True);subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(R/'trace.patch')],cwd=S,check=True);(S/'src/convert.rs').write_text((R/'skip-convert.rs').read_text())
p=S/'src/typecheck.rs';s=p.read_text();needle='''            if !Self::exact_source_levels(&a.levels, &b.levels, remaining) { return false }''';assert s.count(needle)==1;s=s.replace(needle,'''            if !Self::exact_source_levels(&a.levels,&b.levels,remaining){
                #[cfg(feature="diagnostics")]
                if crate::diagnostics::receiver_target_active() && matches!(left.expr.0,690|8){
                    use std::sync::atomic::{AtomicUsize,Ordering};static LEVELS:AtomicUsize=AtomicUsize::new(0);
                    if LEVELS.fetch_add(1,Ordering::Relaxed)<32{let mut generous=65536;let semantic=Self::exact_source_levels(&a.levels,&b.levels,&mut generous);eprintln!("IDENTITY_FRONTIER:reason=levels:root={:?}:left_expr={:?}:right_expr={:?}:remaining={remaining}:generous_exact={semantic}:left_levels={:?}:right_levels={:?}:diagnostic_only=true",left.expr,a.expr,b.expr,a.levels.entries().take(8).collect::<Vec<_>>(),b.levels.entries().take(8).collect::<Vec<_>>());}
                }
                return false;
            }''')
needle='''            let Some(support) = self.complete_paired_source_support(a.expr, b.expr, remaining) else { return false };''';assert s.count(needle)==1;s=s.replace(needle,'''            let Some(support)=self.complete_paired_source_support(a.expr,b.expr,remaining)else{
                #[cfg(feature="diagnostics")]
                if crate::diagnostics::receiver_target_active() && matches!(left.expr.0,690|8){
                    use std::sync::atomic::{AtomicUsize,Ordering};static SYNTAX:AtomicUsize=AtomicUsize::new(0);
                    if SYNTAX.fetch_add(1,Ordering::Relaxed)<32{
                        let isolated=TypeChecker::new(self.expressions,self.levels,self.environment);let mut generous=65536;let complete=isolated.complete_paired_source_support(a.expr,b.expr,&mut generous);
                        eprintln!("IDENTITY_FRONTIER:reason=source-shape:root={:?}:left_expr={:?}:right_expr={:?}:remaining={remaining}:generous_support={complete:?}:left_syntax={:?}:right_syntax={:?}:diagnostic_only=true",left.expr,a.expr,b.expr,self.expressions.get(a.expr),self.expressions.get(b.expr));
                    }
                }
                return false;
            };''');p.write_text(s)
patch=''.join(''.join(difflib.unified_diff((B/rel).read_text().splitlines(True),(S/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))for rel in ['src/checker.rs','src/convert.rs','src/diagnostics.rs','src/typecheck.rs']);(R/'identity-frontier.patch').write_text(patch)
s=(R/'run-capture-goals.py').read_text().replace('capture-goals','identity-frontier').replace("b'CAPTURE_VALUE_GOALS:'","b'IDENTITY_FRONTIER:'").replace("x.startswith('CAPTURE_VALUE_GOALS:')","x.startswith('IDENTITY_FRONTIER:')");(R/'run-identity-frontier.py').write_text(s);print(json.dumps(dict(patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),diagnostic_only=True)))
