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
 p.write_text(s);patch+=''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile='a/metatron-kernel/src/typecheck.rs',tofile='b/metatron-kernel/src/typecheck.rs'));(out/'observer.patch').write_text(patch)
