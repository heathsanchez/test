"""C82 observe whether an exactly owned FAILED recursor is retried later.

There are no acceptance/proof-rule/cache/fuel changes. Retain exact Rc
definition and registered-recursor table owners, exact neutral root with its
captured closures and universes, current authority, and replay goal. Only
failure sites already independently instrumented by C50 count as failures.
No digest, source syntactic match or diagnostic result licenses proof reuse.
"""
from pathlib import Path

p=Path("metatron-kernel/src/machine.rs")
src=p.read_text()
anchor="struct ClockExposure {value:Value,referenced:bool}"
assert src.count(anchor)==1,"C82 owner-key source anchor drift"
insert=r"""
#[cfg(feature="diagnostics")]
struct C82Key {
    authority: AuthorityId,
    definitions: Rc<HashMap<NameId,DefinitionBody>>,
    recursors: Rc<HashMap<NameId,RecursorReduction>>,
    goal: CheckedReplayGoal,
    root: Neutral,
    failed: bool,
}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C82State {
    seen:Vec<C82Key>,
    enters:u64,
    repeated:u64,
    failed_then_retried:u64,
    c50_failures:u64,
    overflow:u64,
}
#[cfg(feature="diagnostics")]
thread_local! {
    static C82_HISTORY: RefCell<C82State> = RefCell::new(C82State::default());
}
#[cfg(feature="diagnostics")]
pub(crate) fn c82_summary() {
    C82_HISTORY.with(|cell|{
        let state=cell.borrow();
        eprintln!("NUCLEUS_C82_SUMMARY:{}",serde_json::json!({
            "entries":state.enters,
            "distinct_stored":state.seen.len(),
            "exact_reentries":state.repeated,
            "exact_failed_then_retried":state.failed_then_retried,
            "c50_failure_site_events":state.c50_failures,
            "untracked_at_capacity":state.overflow,
            "continuation_resume_implemented":false,
            "kernel_accept_authority":"NONE",
        }));
    });
}
"""
src=src.replace(anchor,insert+"\n"+anchor)
p.write_text(src)

src=p.read_text()
marker="    fn qualified_recursor_result(\n"
assert src.count(marker)==1,"C82 recursor root anchor drift"
method=r"""    #[cfg(feature="diagnostics")]
    fn c82_enter_exact_source_root(&self,root:&Neutral,goal:CheckedReplayGoal) {
        if std::env::var_os("NUCLEUS_C82_EXACT_REPEAT").is_none()
            || !crate::typecheck::c56_source_root_active() {return}
        C82_HISTORY.with(|cell|{
            let mut state=cell.borrow_mut();
            state.enters=state.enters.saturating_add(1);
            let owner=self.definitions.clone();
            let rules=self.recursor_reductions.clone();
            let same=state.seen.iter().position(|entry|
                entry.authority==self.authority
                && entry.goal==goal
                && Rc::ptr_eq(&entry.definitions,&owner)
                && Rc::ptr_eq(&entry.recursors,&rules)
                && entry.root==*root);
            if let Some(index)=same {
                state.repeated=state.repeated.saturating_add(1);
                if state.seen[index].failed {
                    state.failed_then_retried=state.failed_then_retried.saturating_add(1);
                }
            } else if state.seen.len()<1024 {
                state.seen.push(C82Key {
                    authority:self.authority,definitions:owner,
                    recursors:rules,goal,root:root.clone(),failed:false,
                });
            } else {
                state.overflow=state.overflow.saturating_add(1);
            }
        });
    }

    #[cfg(feature="diagnostics")]
    fn c82_mark_exact_root_failure(&self,root:&Neutral,goal:CheckedReplayGoal){
        if std::env::var_os("NUCLEUS_C82_EXACT_REPEAT").is_none()
            || !crate::typecheck::c56_source_root_active(){return}
        C82_HISTORY.with(|cell|{
            let mut state=cell.borrow_mut();
            state.c50_failures=state.c50_failures.saturating_add(1);
            if let Some(entry)=state.seen.iter_mut().find(|entry|
                entry.authority==self.authority
                && entry.goal==goal
                && Rc::ptr_eq(&entry.definitions,&self.definitions)
                && Rc::ptr_eq(&entry.recursors,&self.recursor_reductions)
                && entry.root==*root){
                entry.failed=true;
            }
        });
    }

"""
src=src.replace(marker,method+marker)
start=src.index("    fn qualified_recursor_result(")
end=src.index("    fn ",start+9)
segment=src[start:end]
early="        if budget < 48 { return Judgment::unknown(\"nested-recursor-iota-budget\"); }"
assert segment.count(early)==1,"C82 root budget anchor drift"
segment=segment.replace(early,early+"""
        #[cfg(feature="diagnostics")]
        self.c82_enter_exact_source_root(neutral,goal);
        #[cfg(feature="diagnostics")]
        let c82_root=neutral.clone();
""")
needle="""        macro_rules! c50_loss {
            ($stage:expr) => {{"""
assert segment.count(needle)==1,("C82 C50 failure macro drift",segment.count(needle))
segment=segment.replace(needle,"""        macro_rules! c50_loss {
            ($stage:expr) => {{
                #[cfg(feature="diagnostics")]
                self.c82_mark_exact_root_failure(&c82_root,goal);""")
p.write_text(src[:start]+segment+src[end:])

p=Path("metatron-kernel/src/typecheck.rs")
s=p.read_text()
marker="""        if c47_profile {
            let (exposure,replay_key,recursor,conversion)=crate::diagnostics::c47_work_snapshot();"""
assert s.count(marker)==1,("C82 original C47 profile end drift",s.count(marker))
s=s.replace(marker,marker.replace("            let (exposure","            crate::machine::c82_summary();\n            let (exposure"))
p.write_text(s)
print("C82_EXACT_FAILED_RECURSOR_REENTRY_OBSERVER_APPLIED")
