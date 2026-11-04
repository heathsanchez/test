from pathlib import Path
import shutil,subprocess,difflib,json,hashlib
R=Path(__file__).resolve().parent;B=R/'extracted/metatron-kernel';S=R/'capture-goals/metatron-kernel';shutil.copytree(B,S,dirs_exist_ok=True);subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(R/'trace.patch')],cwd=S,check=True);(S/'src/convert.rs').write_text((R/'skip-convert.rs').read_text())
p=S/'src/typecheck.rs';s=p.read_text();needle='    pub(crate) fn has_source_opening_proof(&self,body:&Closure,free:FreeId)->bool {';assert s.count(needle)==1;s=s.replace(needle,'''    #[cfg(feature="diagnostics")]
    pub(crate)fn diagnostic_capture_value_goals(&self,left:&Closure,right:&Closure,context:&[TypeValue])->String{
        let source_probe=TypeChecker::with_level_substitution(self.expressions,self.levels,self.environment,self.level_substitution.clone());
        let mut work=65536;let support=source_probe.complete_source_support(left.expr,&mut work);let mut levels_work=65536;let levels_equal=Self::exact_source_levels(&left.levels,&right.levels,&mut levels_work);
        let mut rows=vec![format!("expr={:?}:same_expr={}:depth={}:full_universe_maps_equal={levels_equal}:support={support:?}:isolated=true:binder_ledger_snapshot=true",left.expr,left.expr==right.expr,context.len())];
        let Some(support)=support else{return rows.join(" || ")};
        for index in support{
            match(left.env.lookup_binding_ref(index),right.env.lookup_binding_ref(index)){
                (Some(EnvBinding::Closure(a)),Some(EnvBinding::Closure(b)))=>{
                    for budget in[128,512]{
                        let mut probe=TypeChecker::with_level_substitution(self.expressions,self.levels,self.environment,self.level_substitution.clone()).with_delta_policy(self.delta_policy);
                        probe.checked_binding_lineage=Rc::new(RefCell::new(self.checked_binding_lineage.borrow().clone()));probe.strict_origin_probe=self.strict_origin_probe;
                        let result=crate::convert::convert_with_policy_in_context(&probe,&TypeValue::Term(a.clone()),&TypeValue::Term(b.clone()),budget,crate::convert::DeltaPolicy::GuardedSemanticFallback,context.len(),context);
                        rows.push(format!("index={index}:lhs_expr={:?}:rhs_expr={:?}:lhs_env={}:rhs_env={}:lhs_syntax={:?}:rhs_syntax={:?}:budget={budget}:value_conversion={result:?}",a.expr,b.expr,a.env.id(),b.env.id(),self.expressions.get(a.expr),self.expressions.get(b.expr)));
                    }
                }
                (Some(EnvBinding::Free(a)),Some(EnvBinding::Free(b)))=>rows.push(format!("index={index}:free_left={a:?}:free_right={b:?}:same_in_real_scope={}",a==b&&a.0<(context.len()as u64))),
                (Some(a),Some(b))=>rows.push(format!("index={index}:other_left={:?}:other_right={:?}",std::mem::discriminant(a),std::mem::discriminant(b))),
                _=>rows.push(format!("index={index}:missing-actual-capture")),
            }
        }
        rows.join(" || ")
    }

'''+needle);p.write_text(s)
p=S/'src/convert.rs';s=p.read_text();needle='''                if !argument_result.is_proven() {''';assert s.count(needle)==1;s=s.replace(needle,needle+'''
                    #[cfg(feature="diagnostics")]
                    if crate::diagnostics::receiver_target_active() && lhs.expr==ExprId(690) && rhs.expr==ExprId(690) && argument_budget>=128{
                        use std::sync::atomic::{AtomicUsize,Ordering};static GOALS:AtomicUsize=AtomicUsize::new(0);
                        if GOALS.fetch_add(1,Ordering::Relaxed)<4{eprintln!("CAPTURE_VALUE_GOALS:{}",checker.diagnostic_capture_value_goals(lhs,rhs,context));}
                    }''');p.write_text(s)
patch=''.join(''.join(difflib.unified_diff((B/rel).read_text().splitlines(True),(S/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))for rel in ['src/checker.rs','src/convert.rs','src/diagnostics.rs','src/typecheck.rs']);(R/'capture-goals.patch').write_text(patch)
s=(R/'run-envelope.py').read_text().replace("D=R/'envelope-replay'","D=R/'capture-goals-replay'").replace("source=R/'envelope/metatron-kernel'","source=R/'capture-goals/metatron-kernel'").replace("target=R/'target'","target=R/'capture-goals-target'").replace("x.startswith('ENVELOPE_FEASIBILITY:')","x.startswith('CAPTURE_VALUE_GOALS:')");s=s.replace("binary=target/'release/metatron-kernel';","binary=target/'release/metatron-kernel';assert b'CAPTURE_VALUE_GOALS:' in binary.read_bytes();");(R/'run-capture-goals.py').write_text(s);print(json.dumps(dict(patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),diagnostic_only=True)))
