"""C85 experimental exact-owned checked-recursor continuation.

This adds an opt-in, *non-authoritative* suspended evaluator state. A checkpoint
may only resume under exactly the same root Neutral (full captured closures,
levels and binder origins), registered immutable rule map owners, source tables,
primitive authority and replay goal. It is never an ACCEPT, cache value, or
constructor selection. The existing evaluation loop rechecks recursor iota.

The grant/owner charges and lifetime scope remain experimental and need
independent soundness/refinement qualification. Never enable on selected kernel.
"""
from pathlib import Path

p=Path("metatron-kernel/src/machine.rs")
s=p.read_text()
def change(old,new):
    global s
    assert s.count(old)==1,("C85 source anchor changed",s.count(old),old[:180])
    s=s.replace(old,new)

state_decl=r"""
// C85: exact worklist checkpoint is NOT a proof result. A suspended
// registered iota retains only computations that were actually performed.
#[derive(Clone)]
enum C85Frame {
    Finish(Option<Rc<ReplayKey>>),
    Major(Neutral,bool),
    ProjectedMajor {
        parent:Neutral, requested:bool, type_name:NameId,
        index:usize, spine:Vec<Closure>,
    },
}
#[derive(Clone,Eq,PartialEq)]
struct C85SourceKey {
    authority:AuthorityId,
    goal:CheckedReplayGoal,
    root:Neutral,
    expression_owner:usize,
    level_owner:usize,
    demand_major:bool,
    replay_projection_major:bool,
    replay_neutral_projection:bool,
    definitions:ImmutableMapWitness<HashMap<NameId,DefinitionBody>>,
    rules:ImmutableMapWitness<HashMap<NameId,RecursorReduction>>,
    projections:ImmutableMapWitness<HashMap<NameId,ProjectionSpec>>,
    singletons:ImmutableMapWitness<HashSet<NameId>>,
    nullary:ImmutableMapWitness<HashMap<NameId,Vec<NullaryMinorReduction>>>,
    nested:ImmutableMapWitness<HashMap<NameId,Vec<ClosedNestedMinorReduction>>>,
    nat:Option<NatPrimitives>,
    bools:Option<BoolPrimitives>,
    quot:Option<(NameId,NameId,NameId,NameId)>,
}
struct C85Checkpoint {
    current:Neutral,
    current_is_requested:bool,
    parents:Vec<C85Frame>,
    established_major:Option<Value>,
    active:HashSet<usize>,
    resolved:HashMap<usize,Value>,
    entered:HashMap<u64,Vec<Rc<ReplayKey>>>,
    current_already_entered:bool,
}
struct ClockExposure {value:Value,referenced:bool}
"""
change("struct ClockExposure {value:Value,referenced:bool}",state_decl)
change("    unfinished_prefixes:HashMap<ExposureProgressKey,ExposureProgress>,",
       "    unfinished_prefixes:HashMap<ExposureProgressKey,ExposureProgress>,\n    c85_suspended:Vec<(C85SourceKey,C85Checkpoint)>,")
needle="""    #[track_caller]
    fn qualified_recursor_result("""
method=r"""    fn c85_source_key(&self,neutral:&Neutral,goal:CheckedReplayGoal)->C85SourceKey {
        C85SourceKey {
            authority:self.authority,goal,root:neutral.clone(),
            expression_owner:self.expressions as *const _ as usize,
            level_owner:self.levels as *const _ as usize,
            demand_major:self.demand_major,
            replay_projection_major:self.replay_projection_major,
            replay_neutral_projection:self.replay_neutral_projection,
            definitions:ImmutableMapWitness(self.definitions.clone()),
            rules:ImmutableMapWitness(self.recursor_reductions.clone()),
            projections:ImmutableMapWitness(self.projection_specs.clone()),
            singletons:ImmutableMapWitness(self.singleton_recursor_reductions.clone()),
            nullary:ImmutableMapWitness(self.nullary_minor_reductions.clone()),
            nested:ImmutableMapWitness(self.closed_nested_minor_reductions.clone()),
            nat:self.nat_primitives.clone(),
            bools:self.bool_primitives.clone(),
            quot:self.quot_primitives.as_ref().map(|q|(q.type_name,q.mk,q.lift,q.ind)),
        }
    }

"""
change(needle,method+needle)

start=s.index("    fn qualified_recursor_result(")
end=s.index("    fn rule_constructor_application(",start)
body=s[start:end]
local_enum="""        enum Continuation {
            Finish(Option<Rc<ReplayKey>>),
            Major(Neutral,bool),
            // A projection is not a constructor. Retain the source-owned
            // projection while its actual receiver recursor is checked by
            // this same worklist and work owner.
            ProjectedMajor {
                parent:Neutral,
                requested:bool,
                type_name:NameId,
                index:usize,
                spine:Vec<Closure>,
            },
        }
"""
assert body.count(local_enum)==1,"C85 worklist frame origin changed"
body=body.replace(local_enum,"")
assert body.count("Continuation::")>=8,("unexpected frame use",body.count("Continuation::"))
body=body.replace("Continuation::","C85Frame::")

needle="""        let mut entered:HashMap<u64,Vec<Rc<ReplayKey>>>=HashMap::new();"""
assert body.count(needle)==1,"C85 original entered lookup drift"
insert=needle+r"""
        // A resumable checkpoint must never be interpreted as a value.
        // Scope the experiment to the registered Decidable.rec root observed
        // in the original n7 source; all other recursors are unchanged.
        let c85_enabled=std::env::var_os("NUCLEUS_C85_TYPED_CHECKPOINT").is_some()
            && matches!(&neutral.head,NeutralHead::Const{name,..} if name.0==147)
            && self.exposure_cache.is_some();
        let mut c85_key=None;
        let mut c85_already_entered=false;
        if c85_enabled {
            // Both lookup and checkpoint acquisition spend an explicit
            // bounded reservation from the current shared owner. C85 is
            // an experimental accounting model, not yet a refinement proof.
            let reservation=32usize;
            if self.exposure_fuel.get().is_some_and(|available|available>reservation+48) {
                for _ in 0..reservation {
                    if !spend(){break;}
                }
                let key=self.c85_source_key(neutral,goal);
                if let Some(cache)=self.exposure_cache.as_ref(){
                    let mut store=cache.borrow_mut();
                    if let Some(pos)=store.c85_suspended.iter().position(|(owned,_)|owned==&key){
                        let (_,saved)=store.c85_suspended.remove(pos);
                        current=saved.current;
                        current_is_requested=saved.current_is_requested;
                        parents=saved.parents;
                        established_major=saved.established_major;
                        active=saved.active;
                        resolved=saved.resolved;
                        entered=saved.entered;
                        c85_already_entered=saved.current_already_entered;
                        #[cfg(feature="diagnostics")]
                        eprintln!("NUCLEUS_C85:reused-exact-worklist:parents={}:resolved={}:entered={}:owner={}",
                            parents.len(),resolved.len(),entered.len(),self.exposure_fuel.get().unwrap_or(0));
                    }
                }
                c85_key=Some(key);
            }
        }
"""
body=body.replace(needle,insert)

# C50 c85_store must occur at failure site before the return, not at
# non-failure or before a constructor has been checked.
macro="""        macro_rules! c50_loss {
            ($stage:expr) => {{"""
assert body.count(macro)==1,"C85 C50 failure site drift"
store=r"""        macro_rules! c50_loss {
            ($stage:expr) => {{
                if c85_enabled && ($stage=="owner-exhausted" || $stage=="major-exposure")
                    && parents.len()<=96 && resolved.len()<=8192
                    && entered.len()<=8192 && active.len()<=8192
                {
                    if let (Some(key),Some(cache))=(c85_key.as_ref(),self.exposure_cache.as_ref()){
                        let snapshot=C85Checkpoint{
                            current:current.clone(),
                            current_is_requested,
                            parents:std::mem::take(&mut parents),
                            established_major:established_major.take(),
                            active:std::mem::take(&mut active),
                            resolved:std::mem::take(&mut resolved),
                            entered:std::mem::take(&mut entered),
                            current_already_entered:$stage=="major-exposure",
                        };
                        let mut store=cache.borrow_mut();
                        if store.c85_suspended.len()>=4{store.c85_suspended.remove(0);}
                        #[cfg(feature="diagnostics")]
                        eprintln!("NUCLEUS_C85:suspended:stage={}:parents={}:resolved={}:root={:?}",
                            $stage,snapshot.parents.len(),snapshot.resolved.len(),key.root.head);
                        store.c85_suspended.push((key.clone(),snapshot));
                    }
                }
"""
body=body.replace(macro,store)
# A checkpoint saved *after* source key admission includes a pending Finish
# and active node. The next call must not re-register that same in-progress
# node as a fresh recursor and misclassify it as a cycle.
before="""                if no_replay_keys {
"""
assert body.count(before)==1,"C85 replay entry changed"
body=body.replace(before, """                if c85_already_entered {
                    c85_already_entered=false;
                } else if no_replay_keys {
""")
# Preserve exact prior state for owner-exhausted *before* entering recursor.
# It does not have a current Finish frame, and key admission must still run.
s=s[:start]+body+s[end:]
p.write_text(s)
print("C85_SOURCE_EXACT_PENDING_RECURSOR_WORKLIST_CHECKPOINT_APPLIED")
