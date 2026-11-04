from pathlib import Path
import shutil,difflib,json,hashlib
R=Path(__file__).resolve().parent;src=R/'extracted/metatron-kernel';out=R/'trace/metatron-kernel';shutil.copytree(src,out,dirs_exist_ok=True)
p=out/'src/diagnostics.rs';s=p.read_text();s+='''
thread_local! { static RECEIVER_TARGET:Cell<bool>=const{Cell::new(false)}; static RECEIVER_EVENTS:Cell<usize>=const{Cell::new(0)}; }
pub(crate) fn receiver_target_active()->bool { RECEIVER_TARGET.get() }
pub(crate) fn receiver_target(active:bool){ RECEIVER_TARGET.set(active); RECEIVER_EVENTS.set(0); }
pub(crate) fn receiver_event(args:std::fmt::Arguments<'_>){ if RECEIVER_TARGET.get() && RECEIVER_EVENTS.get()<256 { RECEIVER_EVENTS.set(RECEIVER_EVENTS.get()+1); eprintln!("RECEIVER_BOUNDARY:{args}"); } }
''';p.write_text(s)
p=out/'src/checker.rs';s=p.read_text();needle='        let declaration = export.declarations[declaration_index].clone();';assert s.count(needle)==1;s=s.replace(needle,needle+'''
        #[cfg(feature="diagnostics")]
        crate::diagnostics::receiver_target(matches!(&declaration,Declaration::Theorem{name,..} if name.0==26089));
''');p.write_text(s)
p=out/'src/convert.rs';s=p.read_text();needle='''                if !argument_result.is_proven() {
''';assert s.count(needle)==1;s=s.replace(needle,needle+'''                    #[cfg(feature="diagnostics")]
                    crate::diagnostics::receiver_event(format_args!("argument:owner={left_type:?}:field={left_index}:depth={depth}:outer_budget={budget}:argument_budget={argument_budget}:left_expr={:?}:right_expr={:?}:left_env={}:right_env={}:result={argument_result:?}",lhs.expr,rhs.expr,lhs.env.id(),rhs.env.id()));
''')
needle='''                    return Judgment::unknown("source-binder-capture-or-support-unavailable");''';assert s.count(needle)==1;s=s.replace(needle,'''                    #[cfg(feature="diagnostics")]
                    crate::diagnostics::receiver_event(format_args!("opening:left_expr={:?}:right_expr={:?}:left_env={}:right_env={}:free={free:?}:allowance={allowance}:remaining={opening_budget}:depth={depth}",left_body.expr,right_body.expr,left_body.env.id(),right_body.env.id()));
'''+needle)
a=s.index('fn source_avoids_capture_uncached(');b=s.index('\n#[cfg(test)]',a);piece=s[a:b]
needle='''        let Some(support) = checker.complete_source_support(source.expr, budget) else { return false; };''';assert piece.count(needle)==1;piece=piece.replace(needle,'''        let Some(support) = checker.complete_source_support(source.expr, budget) else {
            #[cfg(feature="diagnostics")]
            crate::diagnostics::receiver_event(format_args!("support:root={:?}:env={}:virtual={virtual_slots}:free={free:?}:remaining={budget}",source.expr,source.env.id()));
            return false;
        };''')
needle='''                if *budget==0{return false;}*budget-=1;''';assert piece.count(needle)==1;piece=piece.replace(needle,'''                if *budget==0{
                    #[cfg(feature="diagnostics")]
                    crate::diagnostics::receiver_event(format_args!("environment-prefix:root={:?}:env={}:virtual={virtual_slots}:used_index={index}:traversed={traversed}:end={end}:free={free:?}",source.expr,source.env.id()));
                    return false;
                }*budget-=1;''')
s=s[:a]+piece+s[b:];p.write_text(s)
patch=''.join(''.join(difflib.unified_diff((src/rel).read_text().splitlines(True),(out/rel).read_text().splitlines(True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))for rel in [Path('src/diagnostics.rs'),Path('src/checker.rs'),Path('src/convert.rs')]);(R/'trace.patch').write_text(patch)
print(json.dumps(dict(patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),diagnostic_only=True,no_promotion=True)))
