"""C70 source-owned continuation. Opt-in experimental instrumentation only.

Never reuse an UNKNOWN or invent a constructor. B retains only genuine
beta/zeta/application source progress. C additionally shares completed
Nat literals / sorts using a strict owner-qualified key.
"""
from pathlib import Path

ROOT=Path("metatron-kernel")
p=ROOT/"src/machine.rs"
s=p.read_text()

def change(old,new):
    global s
    n=s.count(old)
    if n!=1:raise AssertionError(("source anchor drift",n,old[:110]))
    s=s.replace(old,new)

change("struct ClockExposure {value:Value,referenced:bool}",r"""
#[derive(Clone,Eq,Hash,PartialEq)]
struct C70Key {
    source:ExposureCacheKey,
    expression_owner:usize,
    level_owner:usize,
    demand_major:bool,
    replay_projection_major:bool,
    replay_neutral_projection:bool,
    definitions:ImmutableMapWitness<HashMap<NameId,DefinitionBody>>,
    recursors:ImmutableMapWitness<HashMap<NameId,RecursorReduction>>,
    projections:ImmutableMapWitness<HashMap<NameId,ProjectionSpec>>,
    singletons:ImmutableMapWitness<HashSet<NameId>>,
    nullary:ImmutableMapWitness<HashMap<NameId,Vec<NullaryMinorReduction>>>,
    nested:ImmutableMapWitness<HashMap<NameId,Vec<ClosedNestedMinorReduction>>>,
    nat:Option<NatPrimitives>,
    bools:Option<BoolPrimitives>,
    quot:Option<(NameId,NameId,NameId,NameId)>,
}
#[derive(Clone)]
struct C70Prefix {
    closure:Closure,
    pending:Vec<Closure>,
    visited:VisitSet,
}
struct ClockExposure {value:Value,referenced:bool}""")

change("    completed_replay_count:usize,",
       "    completed_replay_count:usize,\n    c70_prefixes:HashMap<C70Key,C70Prefix>,\n    c70_completed:HashMap<C70Key,Value>,")
change("struct VisitSet {\n","#[derive(Clone)]\nstruct VisitSet {\n")

change("    // Hash-cons only an exact source evaluator binding.",r"""    fn c70_key(&self,closure:&Closure,transparency:Transparency,
        preserve_stuck_projection:bool,pending:&[Closure])->C70Key {
        C70Key {
            source:(self.authority,closure.clone(),transparency,
                preserve_stuck_projection,pending.to_vec()),
            expression_owner:self.expressions as *const _ as usize,
            level_owner:self.levels as *const _ as usize,
            demand_major:self.demand_major,
            replay_projection_major:self.replay_projection_major,
            replay_neutral_projection:self.replay_neutral_projection,
            definitions:ImmutableMapWitness(self.definitions.clone()),
            recursors:ImmutableMapWitness(self.recursor_reductions.clone()),
            projections:ImmutableMapWitness(self.projection_specs.clone()),
            singletons:ImmutableMapWitness(self.singleton_recursor_reductions.clone()),
            nullary:ImmutableMapWitness(self.nullary_minor_reductions.clone()),
            nested:ImmutableMapWitness(self.closed_nested_minor_reductions.clone()),
            nat:self.nat_primitives.clone(),bools:self.bool_primitives.clone(),
            quot:self.quot_primitives.as_ref().map(|q|(q.type_name,q.mk,q.lift,q.ind)),
        }
    }

    // Hash-cons only an exact source evaluator binding.""")

# Locate the first exact reducer invocation under its function name;
# prior C38/C64 diagnostics changed surrounding lines, not its API role.
first=s.index("return self.expose_uncached_internal_with_pending(")
last=s.index(");",first)
oldcall=s[first:last+2]
assert oldcall.count("pending")==1 and "VisitSet::new()" not in oldcall,oldcall
s=s[:first]+oldcall[:-2]+" VisitSet::new(),\n            );"+s[last+2:]

candidate=r"""        let resume=std::env::var_os("NUCLEUS_C70_RESUME_PREFIX").is_some();
        let share=resume && std::env::var_os("NUCLEUS_C70_SHARE_COMPLETED").is_some();
        let mut prefix=C70Prefix{closure,pending,visited:VisitSet::new()};
        let mut remaining=budget;
        let mut retained_key=None;
        if resume && remaining>8 && prefix.pending.len()<=32
            && prefix.closure.levels.entries().count()<=16
        {
            let charge=4usize.saturating_add(prefix.pending.len())
                .saturating_add(prefix.closure.levels.entries().count());
            if remaining>charge+2 && self.exposure_fuel.get().is_none_or(|f|f>charge+2) {
                remaining-=charge;
                if let Some(f)=self.exposure_fuel.get(){self.exposure_fuel.set(Some(f-charge));}
                let scope=self.c70_key(&prefix.closure,transparency,
                    preserve_stuck_projection,&prefix.pending);
                if share {
                    let reusable=cache.borrow().c70_completed.get(&scope).cloned();
                    if let Some(value)=reusable {
                        if remaining>1 && self.exposure_fuel.get().is_none_or(|f|f>1) {
                            if let Some(f)=self.exposure_fuel.get(){self.exposure_fuel.set(Some(f-1));}
                            #[cfg(feature="diagnostics")]
                            crate::diagnostics::c70_count(2);
                            return Judgment::proven(Exposure{value,transitions:Vec::new()},
                                "c70-exact-owned-completed-literal");
                        }
                    }
                }
                if let Some(previous)=cache.borrow_mut().c70_prefixes.remove(&scope) {
                    prefix=previous;
                    #[cfg(feature="diagnostics")]
                    crate::diagnostics::c70_count(0);
                }
                let mut advanced=false;
                while remaining>2 && self.exposure_fuel.get().is_none_or(|f|f>2) {
                    let Some(expr)=self.expressions.get(prefix.closure.expr)else{break};
                    let pure=match expr {
                        Expr::Let{..}|Expr::App{..}=>true,
                        Expr::Lam{..}=>!prefix.pending.is_empty(),
                        Expr::BVar(i)=>matches!(prefix.closure.env.lookup(*i),Some(EnvBinding::Closure(_))),
                        _=>false,
                    };
                    if !pure{break}
                    if !prefix.visited.insert((self.authority,prefix.closure.expr,prefix.closure.env.id())) {
                        return Judgment::unknown("reduction-cycle");
                    }
                    match expr {
                        Expr::Let{value,body,..}=>{
                            prefix.visited.clear();
                            let val=prefix.closure.sibling(*value,prefix.closure.env.clone());
                            prefix.closure=prefix.closure.sibling(*body,self.bind_captured_argument(&prefix.closure,val));
                        }
                        Expr::App{fun,arg}=>{
                            prefix.pending.push(prefix.closure.sibling(*arg,prefix.closure.env.clone()));
                            prefix.closure=prefix.closure.sibling(*fun,prefix.closure.env.clone());
                        }
                        Expr::Lam{body,..}=>{
                            let arg=prefix.pending.pop().expect("pure lambda has argument");
                            prefix.visited.clear();
                            prefix.closure=prefix.closure.sibling(*body,self.bind_captured_argument(&prefix.closure,arg));
                        }
                        Expr::BVar(i)=>{
                            let Some(EnvBinding::Closure(bound))=prefix.closure.env.lookup(*i)else{unreachable!("pure binding")};
                            prefix.visited.clear();
                            prefix.closure=bound;
                        }
                        _=>unreachable!("pure step"),
                    }
                    advanced=true;
                    remaining-=1;
                    if let Some(f)=self.exposure_fuel.get(){self.exposure_fuel.set(Some(f-1));}
                    #[cfg(feature="diagnostics")]
                    crate::diagnostics::c70_count(1);
                }
                if advanced && prefix.pending.len()<=32 && prefix.visited.overflow.is_none() {
                    let mut values=cache.borrow_mut();
                    if values.c70_prefixes.len()<256 {
                        values.c70_prefixes.insert(scope.clone(),prefix.clone());
                    }
                }
                retained_key=Some(scope);
            }
        }
        let result=self.expose_uncached_internal_with_pending(
            prefix.closure,transparency,remaining,false,
            preserve_stuck_projection,prefix.pending,prefix.visited,
        );
        if share {
            if let (Some(key),Some(established))=(retained_key.as_ref(),result.proven_value()) {
                // Never share unfinished recursors, projections, or neutrals.
                if matches!(&established.value,Value::NatLit(_)|Value::Sort(_)) {
                    let mut entries=cache.borrow_mut();
                    if entries.c70_completed.len()<256 {
                        entries.c70_completed.insert(key.clone(),established.value.clone());
                        #[cfg(feature="diagnostics")]
                        crate::diagnostics::c70_count(3);
                    }
                }
            }
        }"""
second=s.index("let result = self.expose_uncached_internal_with_pending(")
tail=s.index(");",second)
oldcall=s[second:tail+2]
assert "closure" in oldcall and "pending" in oldcall,oldcall
s=s[:second]+candidate+s[tail+2:]
change("        mut pending: Vec<Closure>,\n    ) -> Judgment<Exposure> {\n        let mut visited = VisitSet::new();",
       "        mut pending: Vec<Closure>,\n        mut visited: VisitSet,\n    ) -> Judgment<Exposure> {")
p.write_text(s)

p=ROOT/"src/diagnostics.rs"
d=p.read_text()
assert "pub fn c70_report()" not in d
d+=r"""
// C70 thread-local diagnostic counters, never semantic inputs.
thread_local! {
    static C70: std::cell::RefCell<[u64;4]> = const {std::cell::RefCell::new([0;4])};
}
pub fn c70_count(i:usize) {
    if std::env::var_os("NUCLEUS_C70_RESUME_PREFIX").is_none(){return}
    C70.with(|x|{let mut a=x.borrow_mut();a[i]=a[i].saturating_add(1)});
}
pub fn c70_report(){
    C70.with(|x|{
        let a=x.borrow();
        eprintln!("NUCLEUS_C70_COUNTS:{{\"resume_hits\":{},\"pure_steps\":{},\"completed_hits\":{},\"completed_insertions\":{}}}",
            a[0],a[1],a[2],a[3]);
    });
}
"""
p.write_text(d)
p=ROOT/"src/bin/nucleus-diagnostic.rs"
d=p.read_text()
old="metatron_kernel::diagnostics::c69_report();"
assert d.count(old)==1,"authenticated C69 binary report hook absent"
p.write_text(d.replace(old,old+"\n metatron_kernel::diagnostics::c70_report();"))
print("C70_EXACT_SOURCE_COMPUTATION_ONLY_PATCH_APPLIED")
