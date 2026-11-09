"""C84 exact closure-identity census for already observed C47 hot source IDs.

Pure diagnostics: count ExprId plus immutable captured EnvFrame node identity
without treating it as a proof, semantic equality, cache key, or permission to
share across different pending spines/goals. Exact source proof and budgets
are unchanged. Values from differently allocated but extensionally equal
environments count as distinct, conservatively.
"""
from pathlib import Path

p=Path("metatron-kernel/src/diagnostics.rs")
s=p.read_text()
anchor="    static C47_EXPOSURE_SAMPLES: RefCell<HashMap<u64,u64>> = RefCell::new(HashMap::new());"
assert s.count(anchor)==1, "C84 diagnostic store anchor drift"
s=s.replace(anchor,anchor+"""
    // C84 observer only. Env IDs are node identities, not semantic equality.
    static C84_EXACT_CLOSURES: RefCell<HashMap<(u64,u64),u64>> = RefCell::new(HashMap::new());
    static C84_WATCH_TRANSITIONS: Cell<u64> = const { Cell::new(0) };
    static C84_EXACT_REPEATS: Cell<u64> = const { Cell::new(0) };
    static C84_OVERFLOW: Cell<u64> = const { Cell::new(0) };
""")
anchor="    C47_EXPOSURE_SAMPLES.with(|samples|samples.borrow_mut().clear());"
assert s.count(anchor)==1,"C84 reset anchor drift"
s=s.replace(anchor,anchor+"""
    C84_EXACT_CLOSURES.with(|samples|samples.borrow_mut().clear());
    C84_WATCH_TRANSITIONS.set(0);
    C84_EXACT_REPEATS.set(0);
    C84_OVERFLOW.set(0);
""")
anchor="pub(crate) fn c47_replay_reservation(count: usize) {"
assert s.count(anchor)==1,"C84 exposure observer anchor drift"
s=s.replace(anchor,r"""
// Only exact (ExprId, captured immutable environment node identity) counts.
// Pending application spines and proof goals are *not* included; a match is
// necessary for that class of conservative sharing, never sufficient.
pub(crate) fn c84_closure_transition(expression:u64,environment:u64) {
    if std::env::var_os("NUCLEUS_C84_EXACT_CLOSURE_CENSUS").is_none() {return}
    if !matches!(expression,1|6|11|7|345|4678|4677|6087|217|218|547|7277|6365) {return}
    C84_WATCH_TRANSITIONS.set(C84_WATCH_TRANSITIONS.get().saturating_add(1));
    C84_EXACT_CLOSURES.with(|samples|{
        let mut seen=samples.borrow_mut();
        if let Some(hits)=seen.get_mut(&(expression,environment)){
            *hits=hits.saturating_add(1);
            C84_EXACT_REPEATS.set(C84_EXACT_REPEATS.get().saturating_add(1));
        } else if seen.len()<65536 {
            seen.insert((expression,environment),1);
        } else {
            C84_OVERFLOW.set(C84_OVERFLOW.get().saturating_add(1));
        }
    });
}

pub(crate) fn c84_closure_summary()->serde_json::Value{
    C84_EXACT_CLOSURES.with(|samples|{
        let seen=samples.borrow();
        let mut grouped=HashMap::<u64,(u64,u64,u64)>::new();
        let mut top=Vec::<(u64,u64,u64)>::new();
        for (&(expr,env),&hits) in seen.iter(){
            let x=grouped.entry(expr).or_insert((0,0,0));
            x.0=x.0.saturating_add(hits);
            x.1=x.1.saturating_add(1);
            x.2=x.2.max(hits);
            top.push((expr,env,hits));
        }
        top.sort_unstable_by(|a,b|b.2.cmp(&a.2).then(a.0.cmp(&b.0)).then(a.1.cmp(&b.1)));
        top.truncate(16);
        let mut groups=grouped.into_iter().map(|(expr,(events,unique,max_hits))|
            (expr,events,unique,max_hits)).collect::<Vec<_>>();
        groups.sort_unstable_by(|a,b|b.1.cmp(&a.1).then(a.0.cmp(&b.0)));
        serde_json::json!({
            "watch_transitions":C84_WATCH_TRANSITIONS.get(),
            "unique_exact_expr_env_nodes":seen.len(),
            "exact_repeated_exposures":C84_EXACT_REPEATS.get(),
            "capacity_overflow":C84_OVERFLOW.get(),
            "monitored_expr_ids_only":true,
            "same_expr_env_does_not_imply_same_pending_spine_or_proof_goal":true,
            "groups":groups,
            "top_exact":top,
        })
    })
}

""" + anchor)
p.write_text(s)

p=Path("metatron-kernel/src/machine.rs")
s=p.read_text()
anchor="            crate::diagnostics::c47_exposure_transition(closure.expr.0);"
assert s.count(anchor)==1,"C84 machine hot-loop anchor drift"
s=s.replace(anchor,anchor+"\n            #[cfg(feature=\"diagnostics\")]\n            crate::diagnostics::c84_closure_transition(closure.expr.0,closure.env.id());")
p.write_text(s)

p=Path("metatron-kernel/src/typecheck.rs")
s=p.read_text()
anchor='''            eprintln!("NUCLEUS_C47_HOT_SOURCE:expr={expression:?}:samples_every_64={:?}",
                crate::diagnostics::c47_top_source_exposures());'''
assert s.count(anchor)==1,"C84 selected-root reporting anchor drift"
s=s.replace(anchor,anchor+'''
            if std::env::var_os("NUCLEUS_C84_EXACT_CLOSURE_CENSUS").is_some(){
                eprintln!("NUCLEUS_C84_CLOSURES:{}",
                    crate::diagnostics::c84_closure_summary());
            }''')
p.write_text(s)
print("C84_EXACT_CLOSURE_IDENTITY_OBSERVER_APPLIED")
