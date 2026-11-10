"""C85 diagnostics-only exact completed recursor census over frozen C84.

Apply strictly *after* C84. This is a source transform for the CI rebuild,
not a checked-recursion rule or a cache. Each finished continuation carries
the source-qualified CompletedReplayKey already built by the checker. The
same structural equality used by the real cache is used for the census.
Costs are consumed shared-fuel units from post-key entry to completion and
are inclusive of descendant evaluations (not net potential savings).
"""
from pathlib import Path


def replace_once(path, old, new):
    text = path.read_text()
    assert text.count(old) == 1, f"C85 patch anchor drift in {path}: {old[:80]}"
    path.write_text(text.replace(old, new))


def apply_c85(root=Path("metatron-kernel/src")):
    machine = root / "machine.rs"
    anchor = "enum CheckedReplayGoal { Completed, OneStep }"
    replace_once(machine, anchor, anchor + r"""

// C85: observation-only census. Exact key includes source closure, full
// argument spine, immutable registered interface, authority, and options.
// Separate goal classes: OneStep results are not counted as completions.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C85CompletionCensus {
    seen: HashMap<u64,Vec<(Rc<ReplayKey>,CheckedReplayGoal)>>,
    completed:u64,
    unique_exact:u64,
    repeated_exact:u64,
    repeated_inclusive_work:u64,
    completed_inclusive_work:u64,
    completed_goal:u64,
    one_step_goal:u64,
    one_step_exits:u64,
    cache_hits:u64,
    unkeyed_completions:u64,
    overflow:u64,
}
#[cfg(feature="diagnostics")]
thread_local! {
    static C85_COMPLETIONS: RefCell<C85CompletionCensus> = RefCell::new(C85CompletionCensus::default());
}
#[cfg(feature="diagnostics")]
pub(crate) fn c85_reset() {
    C85_COMPLETIONS.with(|cell|*cell.borrow_mut()=C85CompletionCensus::default());
}
#[cfg(feature="diagnostics")]
fn c85_completed(key:&Rc<ReplayKey>, goal:CheckedReplayGoal, inclusive_work:usize) {
    if std::env::var_os("NUCLEUS_C85_COMPLETION_CENSUS").is_none() {return;}
    C85_COMPLETIONS.with(|cell| {
        let mut c=cell.borrow_mut();
        c.completed=c.completed.saturating_add(1);
        c.completed_inclusive_work=c.completed_inclusive_work.saturating_add(inclusive_work as u64);
        match goal {
            CheckedReplayGoal::Completed=>c.completed_goal=c.completed_goal.saturating_add(1),
            CheckedReplayGoal::OneStep=>c.one_step_goal=c.one_step_goal.saturating_add(1),
        }
        // Hash buckets are not proof of identity. Compare complete source
        // keys before reporting exact repetition. Observer-only comparison
        // consumes no checker work allowance and cannot license acceptance.
        let exact=c.seen.get(&key.digest).is_some_and(|bucket|bucket.iter().any(|(saved,saved_goal)|
            *saved_goal==goal && saved.exact==key.exact));
        if exact {
            c.repeated_exact=c.repeated_exact.saturating_add(1);
            c.repeated_inclusive_work=c.repeated_inclusive_work.saturating_add(inclusive_work as u64);
        } else if c.unique_exact<8192 {
            c.seen.entry(key.digest).or_default().push((key.clone(),goal));
            c.unique_exact=c.unique_exact.saturating_add(1);
        } else {
            c.overflow=c.overflow.saturating_add(1);
        }
    });
}
#[cfg(feature="diagnostics")]
fn c85_cache_hit() {
    if std::env::var_os("NUCLEUS_C85_COMPLETION_CENSUS").is_none() {return;}
    C85_COMPLETIONS.with(|cell|{
        let mut c=cell.borrow_mut();
        c.cache_hits=c.cache_hits.saturating_add(1);
    });
}
#[cfg(feature="diagnostics")]
fn c85_unkeyed_completion() {
    if std::env::var_os("NUCLEUS_C85_COMPLETION_CENSUS").is_none() {return;}
    C85_COMPLETIONS.with(|cell|{
        let mut c=cell.borrow_mut();
        c.unkeyed_completions=c.unkeyed_completions.saturating_add(1);
    });
}
#[cfg(feature="diagnostics")]
fn c85_one_step_exit() {
    if std::env::var_os("NUCLEUS_C85_COMPLETION_CENSUS").is_none() {return;}
    C85_COMPLETIONS.with(|cell|{
        let mut c=cell.borrow_mut();
        c.one_step_exits=c.one_step_exits.saturating_add(1);
    });
}
#[cfg(feature="diagnostics")]
pub(crate) fn c85_completed_summary()->serde_json::Value {
    C85_COMPLETIONS.with(|cell|{
        let c=cell.borrow();
        serde_json::json!({
            "completed":c.completed,
            "unique_exact":c.unique_exact,
            "repeated_exact":c.repeated_exact,
            "repeated_inclusive_work":c.repeated_inclusive_work,
            "completed_inclusive_work":c.completed_inclusive_work,
            "goal_counts":{"Completed":c.completed_goal,"OneStep":c.one_step_goal},
            "one_step_exits":c.one_step_exits,
            "cache_hits":c.cache_hits,
            "unkeyed_completions":c.unkeyed_completions,
            "overflow":c.overflow,
            "limit":8192,
            "source_authority_preserved":true,
            "exact_structural_comparison":true,
            "completed_only":true,
            "inclusive_cost_not_realizable_savings":true,
        })
    })
}
""")

    anchor = "        let mut entered:HashMap<u64,Vec<Rc<ReplayKey>>>=HashMap::new();"
    replace_once(machine, anchor, anchor + "\n        #[cfg(feature=\"diagnostics\")]\n        let mut c85_started:HashMap<usize,usize>=HashMap::new();")

    # Exact C37 artifact includes a keyless option on some proof paths;
    # current local diagnostic source may not. Select the actual frozen
    # source shape, never assume that a missing key is an exact match.
    source = machine.read_text()
    if "Continuation::Finish(maybe_key) => {" in source:
        anchor = "                        Continuation::Finish(maybe_key) => {"
        replace_once(machine, anchor, anchor + """
                            #[cfg(feature="diagnostics")]
                            if maybe_key.is_none() {c85_unkeyed_completion();}""")
        anchor = "                            if let Some(key)=maybe_key {"
        replace_once(machine, anchor, anchor + """
                                #[cfg(feature="diagnostics")]
                                if let Some(start)=c85_started.remove(&ReplayKey::identity(&key)) {
                                    c85_completed(&key,goal,start.saturating_sub(self.exposure_fuel.get().unwrap_or(0)));
                                }""")
        anchor = "                parents.push(Continuation::Finish(Some(key)));"
    else:
        anchor = "                        Continuation::Finish(key) => {"
        replace_once(machine, anchor, anchor + """
                            #[cfg(feature="diagnostics")]
                            if let Some(start)=c85_started.remove(&ReplayKey::identity(&key)) {
                                c85_completed(&key,goal,start.saturating_sub(self.exposure_fuel.get().unwrap_or(0)));
                            }""")
        anchor = "                parents.push(Continuation::Finish(key));"
    replace_once(machine, anchor, """                #[cfg(feature="diagnostics")]
                c85_started.insert(identity,self.exposure_fuel.get().unwrap_or(0));
""" + anchor)

    anchor = """                        finish!('evaluate,value);
                    }
                    Judgment::Proven{value:None,..}=>{},"""
    replace_once(machine, anchor, """                        #[cfg(feature="diagnostics")]
                        c85_cache_hit();
                        finish!('evaluate,value);
                    }
                    Judgment::Proven{value:None,..}=>{},""")

    anchor = """            if goal==CheckedReplayGoal::OneStep && current_is_requested {
                return Judgment::proven(value,"checked-one-step-source-recursor-iota");"""
    replace_once(machine, anchor, """            if goal==CheckedReplayGoal::OneStep && current_is_requested {
                #[cfg(feature="diagnostics")]
                c85_one_step_exit();
                return Judgment::proven(value,"checked-one-step-source-recursor-iota");""")

    diagnostics = root / "diagnostics.rs"
    anchor = "    C84_EXACT_CLOSURES.with(|samples|samples.borrow_mut().clear());"
    replace_once(diagnostics, anchor, anchor + "\n    crate::machine::c85_reset();")

    typecheck = root / "typecheck.rs"
    anchor = """                    crate::diagnostics::c84_closure_summary());
            }"""
    replace_once(typecheck, anchor, anchor + """
            if std::env::var_os("NUCLEUS_C85_COMPLETION_CENSUS").is_some(){
                eprintln!("NUCLEUS_C85_COMPLETED:{}",
                    crate::machine::c85_completed_summary());
            }""")


if __name__ == "__main__":
    apply_c85()
    print("C85_EXACT_COMPLETED_RECURSOR_OBSERVER_APPLIED")
