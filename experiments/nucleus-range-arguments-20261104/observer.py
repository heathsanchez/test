import difflib
from pathlib import Path
def apply(kernel,out):
 p=kernel/'src/checker.rs';before=p.read_text();s=before
 insert='''#[cfg(feature="diagnostics")]
std::thread_local!{static TRACE_DECL_ACTIVE:std::cell::Cell<bool>=std::cell::Cell::new(false);}
#[cfg(feature="diagnostics")]
pub(crate) fn diagnostic_scope_active()->bool{TRACE_DECL_ACTIVE.with(|value|value.get())}
'''
 s=insert+s
 needle='''        let declaration = export.declarations[declaration_index].clone();''';assert s.count(needle)==1
 s=s.replace(needle,needle+'''
        #[cfg(feature="diagnostics")]
        {
            let name=match &declaration {
                Declaration::Axiom{name,..}|Declaration::Definition{name,..}|Declaration::Theorem{name,..}|Declaration::Opaque{name,..}|Declaration::Quot{name,..}=>Some(*name),
                Declaration::Inductive(block)=>block.types.first().map(|ty|ty.name),
                _=>None,
            };
            let active=std::env::var("NUCLEUS_TRACE_ONLY_DECLARATION").ok().is_none_or(|target|name.is_some_and(|name|trace_name(&export,name)==target));
            TRACE_DECL_ACTIVE.with(|value|value.set(active));
        }
''');p.write_text(s);patch=''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile='a/metatron-kernel/src/checker.rs',tofile='b/metatron-kernel/src/checker.rs'))
 p=kernel/'src/typecheck.rs';before=p.read_text();s=before
 for flag in ['NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE','NUCLEUS_TRACE_DEPENDENCY_GAP']:
  needle='std::env::var_os("'+flag+'").is_some()';assert s.count(needle)==1;s=s.replace(needle,needle+' && crate::checker::diagnostic_scope_active()')
 needle='&& (context.len()==4 || context.len()==11)';assert s.count(needle)==1;s=s.replace(needle,'&& crate::checker::diagnostic_scope_active()')
 s=s.replace('for slot in 0..6u64','for slot in 0..9u64')
 anchor='                            if let (TypeValue::Term(inferred), TypeValue::Term(anticipated)) = (&value, expected) {\n                                for slot'
 probe=r'''                            if expression.0 == 108167 && let (TypeValue::Term(inferred), TypeValue::Term(anticipated)) = (&value, expected) {
                                use std::sync::atomic::{AtomicBool, Ordering};
                                static ONCE: AtomicBool = AtomicBool::new(false);
                                if !ONCE.swap(true, Ordering::Relaxed) {
                                    let raw_spine = |term: &Closure| {
                                        let mut head=term.clone(); let mut args=Vec::new();
                                        for _ in 0..16 {
                                            if let Some(Expr::App{fun,arg})=self.expressions.get(head.expr) {
                                                args.push(Closure::with_levels(*arg,head.env.clone(),head.levels.clone())); head.expr=*fun;
                                            } else {break}
                                        }
                                        args.reverse(); (head,args)
                                    };
                                    let (_,la)=raw_spine(inferred); let (_,ra)=raw_spine(anticipated);
                                    if let (Some(lb),Some(rb))=(la.get(1),ra.get(1)) {
                                        let (lh,ls)=raw_spine(lb); let (rh,rs)=raw_spine(rb);
                                        eprintln!("NUCLEUS_SAT_HEADS:left={lh:?}:left_shape={:?}:right={rh:?}:right_shape={:?}",self.expressions.get(lh.expr),self.expressions.get(rh.expr));
                                        for (slot,(l,r)) in ls.iter().zip(&rs).enumerate() {
                                            for transparency in [Transparency::Reducible,Transparency::Full] {
                                                let le=self.machine().expose_for_conversion(l.clone(),transparency,65536);
                                                let re=self.machine().expose_for_conversion(r.clone(),transparency,65536);
                                                eprintln!("NUCLEUS_SAT_ARG:slot={slot}:transparency={transparency:?}:left={l:?}:left_shape={:?}:right={r:?}:right_shape={:?}:left_whnf={le:?}:right_whnf={re:?}",self.expressions.get(l.expr),self.expressions.get(r.expr));
                                            }
                                            let cv=crate::convert::convert_with_policy_in_context(self,&TypeValue::Term(l.clone()),&TypeValue::Term(r.clone()),65536,crate::convert::DeltaPolicy::GuardedSemanticFallback,context.len(),context);
                                            eprintln!("NUCLEUS_SAT_ARG_CONVERSION:slot={slot}:verdict={cv:?}");
                                        }
                                    }
                                }
                            }
'''
 assert s.count(anchor)==1
 s=s.replace(anchor,probe+anchor)
 p.write_text(s);patch+=''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile='a/metatron-kernel/src/typecheck.rs',tofile='b/metatron-kernel/src/typecheck.rs'));(out/'observer.patch').write_text(patch)
