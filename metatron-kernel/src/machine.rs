use std::cell::{Cell, RefCell};
use std::collections::{HashMap, HashSet};
use std::rc::Rc;

use crate::environment::{BoolPrimitives, NatPrimitives, QuotPrimitives};
use crate::id::{ExprId, IdTable, LevelId, NameId};
use crate::judgment::Judgment;
use crate::level::instantiate_level;
use crate::syntax::{Expr, Level};
use crate::value::{
    Closure, EnvBinding, EnvFrame, FreeId, LevelSubstitution, Neutral, NeutralHead, Value,
};

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct AuthorityId(pub u64);

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum Transparency {
    Opaque,
    Reducible,
    Full,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TransitionWitness {
    Beta,
    Zeta,
    Delta,
    SingletonRecursor,
    ConstructorRecursor,
    NatExtension,
    Quotient,
    Rigid,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DefinitionBody {
    pub value: ExprId,
    pub preferred_for_reduction: bool,
    pub level_params: Vec<NameId>,
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub struct RecursorRule {
    pub constructor: NameId,
    pub constructor_level_params: Vec<NameId>,
    pub num_params: usize,
    pub num_fields: usize,
    pub rhs: ExprId,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ClosedNestedMinorReduction {
    pub constructor: NameId,
    pub constructor_levels: Vec<crate::level::LevelTerm>,
    pub constructor_parameters: Vec<(NameId,Vec<crate::level::LevelTerm>)>,
    pub num_fields: usize,
    pub rhs: ExprId,
    pub level_params: Vec<NameId>,
    pub prefix_len: usize,
    pub minor_argument: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct NullaryMinorReduction {
    pub constructor: NameId,
    pub level_arity: usize,
    pub prefix_len: usize,
    pub minor_argument: usize,
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub struct RecursorReduction {
    pub k: bool,
    pub num_params: usize,
    pub num_indices: usize,
    pub level_params: Vec<NameId>,
    pub rules: Vec<RecursorRule>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ProjectionFieldType {
    Parameter(usize),
    Derived(ExprId),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProjectionSpec {
    pub constructor: NameId,
    pub num_params: usize,
    pub field_types: Vec<ProjectionFieldType>,
    pub eta_expandable: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Exposure {
    pub value: Value,
    pub transitions: Vec<TransitionWitness>,
}

/// Only certified exposure results may be retained. Closure frames and the
/// declared authority are part of the key; budget is an exploration limit,
/// not a semantic hypothesis about the normalized value.
pub(crate) type ExposureCacheKey = (AuthorityId, Closure, Transparency, bool, Vec<Closure>);
// Retain the immutable registered-rule map while pointer identity is a key.
// An address alone could alias a later allocation after the old map drops.
#[derive(Clone)]
struct ImmutableMapWitness<T>(Rc<T>);
impl<T> PartialEq for ImmutableMapWitness<T> {fn eq(&self,other:&Self)->bool{Rc::ptr_eq(&self.0,&other.0)}}
impl<T> Eq for ImmutableMapWitness<T> {}
impl<T> std::hash::Hash for ImmutableMapWitness<T> {
    fn hash<H:std::hash::Hasher>(&self,state:&mut H){std::hash::Hash::hash(&(Rc::as_ptr(&self.0) as usize),state);}
}
#[derive(Clone,Eq,Hash,PartialEq)]
struct CompletedReplayKey {
    authority:AuthorityId,
    demand_major:bool,
    replay_projection_major:bool,
    replay_neutral_projection:bool,
    rules:ImmutableMapWitness<HashMap<NameId,RecursorReduction>>,
    definitions:ImmutableMapWitness<HashMap<NameId,DefinitionBody>>,
    projections:ImmutableMapWitness<HashMap<NameId,ProjectionSpec>>,
    singletons:ImmutableMapWitness<HashSet<NameId>>,
    nullary:ImmutableMapWitness<HashMap<NameId,Vec<NullaryMinorReduction>>>,
    nested:ImmutableMapWitness<HashMap<NameId,Vec<ClosedNestedMinorReduction>>>,
    certificate:RecursorReduction,
    name:NameId,
    levels:Vec<crate::level::LevelTerm>,
    spine:Vec<Closure>,
    nat:Option<NatPrimitives>,
    bools:Option<BoolPrimitives>,
    quot:Option<(NameId,NameId,NameId,NameId)>,
}
// A structural source hash is computed once. Hash buckets still compare
// the full certificate/configuration/closures under the replay work owner.
struct ReplayKey {
    exact: CompletedReplayKey,
    digest: u64,
}
impl ReplayKey {
    fn identity(key:&Rc<Self>)->usize {Rc::as_ptr(key) as usize}
}
// Share the exact key with the CLOCK ring. Its structural digest is computed
// once; pointer equality makes removal of an owned ring entry constant work.
struct CachedExposureKey { exact:ExposureCacheKey, digest:u64 }
impl CachedExposureKey {
    fn new(exact:ExposureCacheKey)->Self {
        use std::hash::{Hash,Hasher};
        let mut hash=std::collections::hash_map::DefaultHasher::new();exact.hash(&mut hash);
        Self{exact,digest:hash.finish()}
    }
}
impl PartialEq for CachedExposureKey {
    fn eq(&self,other:&Self)->bool {std::ptr::eq(self,other)||self.exact==other.exact}
}
impl Eq for CachedExposureKey {}
impl std::hash::Hash for CachedExposureKey {
    fn hash<H:std::hash::Hasher>(&self,state:&mut H){std::hash::Hash::hash(&self.digest,state)}
}
struct ClockExposure {value:Value,referenced:bool}
#[derive(Default)]
pub(crate) struct ExposureCacheStore {
    values: HashMap<Rc<CachedExposureKey>, ClockExposure>,
    exposure_clock:Vec<Rc<CachedExposureKey>>,
    exposure_hand:usize,
    bindings: HashMap<(AuthorityId, Closure, Closure), EnvFrame>,
    numeric_bindings: HashMap<(AuthorityId, ExprId, crate::nat::BigNat), EnvFrame>,
    completed_replays:HashMap<u64,Vec<(Rc<ReplayKey>,Value)>>,
    completed_replay_count:usize,
}
impl ExposureCacheStore {
    fn retain_exposure(&mut self,key:Rc<CachedExposureKey>,value:&Value,mut spend:impl FnMut()->bool) {
        const CAPACITY:usize=8192;
        if let Some(entry)=self.values.get_mut(&key) {entry.value=value.clone();entry.referenced=true;return}
        // A deliberate external test eviction may empty only the value map.
        if self.values.is_empty(){self.exposure_clock.clear();self.exposure_hand=0;}
        if self.values.len()<CAPACITY {
            self.exposure_clock.push(key.clone());
        } else {
            let mut victim=None;
            for _ in 0..CAPACITY*2 {
                if !spend(){return}
                let index=self.exposure_hand;
                self.exposure_hand=(index+1)%CAPACITY;
                let saved=&self.exposure_clock[index];
                if let Some(entry)=self.values.get_mut(saved) {
                    if entry.referenced {entry.referenced=false;continue}
                }
                victim=Some(index);break;
            }
            let Some(index)=victim else{return};
            self.values.remove(&self.exposure_clock[index]);
            self.exposure_clock[index]=key.clone();
        }
        self.values.insert(key,ClockExposure{value:value.clone(),referenced:false});
    }
}
pub(crate) type ExposureCache = Rc<RefCell<ExposureCacheStore>>;

pub(crate) fn new_exposure_cache() -> ExposureCache {
    Rc::new(RefCell::new(ExposureCacheStore::default()))
}

type VisitKey = (AuthorityId, ExprId, u64);
const INLINE_VISIT_CAPACITY: usize = 8;

struct VisitSet {
    inline: [Option<VisitKey>; INLINE_VISIT_CAPACITY],
    len: usize,
    overflow: Option<HashSet<VisitKey>>,
}

impl VisitSet {
    #[inline]
    fn new() -> Self {
        Self {
            inline: [None; INLINE_VISIT_CAPACITY],
            len: 0,
            overflow: None,
        }
    }

    #[inline]
    fn insert(&mut self, key: VisitKey) -> bool {
        if let Some(overflow) = self.overflow.as_mut() {
            return overflow.insert(key);
        }
        for slot in &self.inline[..self.len] {
            if *slot == Some(key) {
                return false;
            }
        }
        if self.len < INLINE_VISIT_CAPACITY {
            self.inline[self.len] = Some(key);
            self.len += 1;
            return true;
        }
        let mut overflow = HashSet::with_capacity(INLINE_VISIT_CAPACITY * 2);
        for slot in &self.inline[..self.len] {
            overflow.insert(slot.expect("initialized inline visit slot"));
        }
        let inserted = overflow.insert(key);
        self.overflow = Some(overflow);
        inserted
    }

    #[inline]
    fn clear(&mut self) {
        self.len = 0;
        self.overflow = None;
    }
    #[cfg(feature="diagnostics")]
    fn diagnostic_keys(&self)->Vec<(u64,u64,u64)> {
        let mut keys:Vec<_>=match &self.overflow {
            Some(overflow)=>overflow.iter().map(|(authority,expr,env)|
                (authority.0,expr.0,*env)).collect(),
            None=>self.inline[..self.len].iter().filter_map(|key|key.map(
                |(authority,expr,env)|(authority.0,expr.0,env))).collect(),
        };
        keys.sort_unstable();
        keys
    }
}

#[cfg(feature="diagnostics")]
static REPLAY_KEY_WORK:std::sync::atomic::AtomicUsize=std::sync::atomic::AtomicUsize::new(0);
#[cfg(feature="diagnostics")]
struct ReplayWorkTrace<'a>{fuel:&'a Cell<Option<usize>>,start:usize,key_start:usize,head:&'a NeutralHead}
#[cfg(feature="diagnostics")]
impl Drop for ReplayWorkTrace<'_>{fn drop(&mut self){
    use std::sync::atomic::{AtomicUsize,Ordering};
    static PRINTED:AtomicUsize=AtomicUsize::new(0);
    if PRINTED.fetch_add(1,Ordering::Relaxed)<32 {
        let remaining=self.fuel.get().unwrap_or(0);
        eprintln!("NUCLEUS_REPLAY_WORK:head={:?}:start={}:remaining={remaining}:consumed={}:key_work={}",self.head,self.start,self.start.saturating_sub(remaining),REPLAY_KEY_WORK.load(Ordering::Relaxed).saturating_sub(self.key_start));
    }
}}

// Read-only, owner-local phase receipts. This observer never creates a source
// value, a replay key or a type judgment; in particular a pending continuation
// is not a cacheable completed result.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C94PhaseCounts {
    entered: Cell<usize>, resumed: Cell<usize>, completed: Cell<usize>,
    local_hits: Cell<usize>, global_hits: Cell<usize>, max_depth: Cell<usize>,
    last_major_expr: Cell<u64>, last_major_frame: Cell<u64>, last_head: Cell<u64>,
    bvar_majors: Cell<usize>, bvar_repeats: Cell<usize>,
    bvar_bindings: RefCell<HashSet<(ExprId,u64)>>,
}
// C104 is a read-only ledger of exact captured major exposure requests.
// A previously Proven exposure need not be a completed constructor or even
// cacheable; a repeated Closure is not an exact replay-key equivalence.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C104MajorGroup {
    requests: usize,
    charged: usize,
    unresolved: usize,
    nested: usize,
    other_proven: usize,
    had_proven: bool,
}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C104MajorCounts {
    requests: usize,
    repeated: usize,
    prior_proven: usize,
    prior_unresolved: usize,
    unresolved: usize,
    nested: usize,
    other_proven: usize,
    repeat_spent: usize,
    unresolved_spent: usize,
    nested_spent: usize,
    other_proven_spent: usize,
    groups: HashMap<Closure,C104MajorGroup>,
}
#[cfg(feature="diagnostics")]
impl C104MajorCounts {
    fn record(&mut self,major:&Closure,spent:usize,proven:bool,nested:bool) {
        self.requests+=1;
        let group=self.groups.entry(major.clone()).or_default();
        if group.requests>0 {
            self.repeated+=1;
            self.repeat_spent+=spent;
            if group.had_proven {self.prior_proven+=1;}
            else {self.prior_unresolved+=1;}
        }
        group.requests+=1;
        group.charged+=spent;
        if !proven {
            self.unresolved+=1;
            self.unresolved_spent+=spent;
            group.unresolved+=1;
        } else if nested {
            self.nested+=1;
            self.nested_spent+=spent;
            group.nested+=1;
        } else {
            self.other_proven+=1;
            self.other_proven_spent+=spent;
            group.other_proven+=1;
        }
        group.had_proven|=proven;
    }
}
#[cfg(feature="diagnostics")]
struct C104MajorReceipt<'a> {
    counts:&'a RefCell<C104MajorCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
// A distinct C104 captured frame can resolve through a chain of immutable
// source BVar bindings. C105 records the exact *terminal closure*, not an
// inferred equality of different frames or an admissible proof cache key.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C105TerminalGroup {
    requests:usize,charged:usize,had_proven:bool,
}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C105TerminalCounts {
    requests:usize,terminal_repeated:usize,
    prior_proven:usize,prior_unresolved:usize,repeated_spent:usize,
    chain_steps:usize,max_chain:usize,chain_capped:usize,
    groups:HashMap<Closure,C105TerminalGroup>,
}
#[cfg(feature="diagnostics")]
impl C105TerminalCounts {
    fn record(&mut self,terminal:Closure,steps:usize,capped:bool,
              spent:usize,proven:bool) {
        self.requests+=1;
        self.chain_steps+=steps;
        self.max_chain=self.max_chain.max(steps);
        self.chain_capped+=usize::from(capped);
        let group=self.groups.entry(terminal).or_default();
        if group.requests>0 {
            self.terminal_repeated+=1;
            self.repeated_spent+=spent;
            if group.had_proven {self.prior_proven+=1;}
            else {self.prior_unresolved+=1;}
        }
        group.requests+=1;
        group.charged+=spent;
        group.had_proven|=proven;
    }
}
#[cfg(feature="diagnostics")]
struct C105TerminalReceipt<'a> {
    counts:&'a RefCell<C105TerminalCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
// C106 tests a smaller *candidate* support for the exact N21 source App
// ExprId(7219). Its eight-node DAG has only BVars 2 and 4; all other nodes
// are App or Const. Identity of those immutable lexical bindings, plus the
// complete level substitution, is measured without quotienting Values or
// importing a proof of contextual independence. Never use this as a cache.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C106SupportGroup {
    requests:usize,charged:usize,had_proven:bool,
}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C106SupportCounts {
    requests:usize,target:usize,complete:usize,missing:usize,
    pair_repeated:usize,node2_repeated:usize,node4_repeated:usize,
    prior_proven:usize,prior_unresolved:usize,repeated_spent:usize,
    pairs:HashMap<(u64,u64,LevelSubstitution),C106SupportGroup>,
    node2:HashSet<(u64,LevelSubstitution)>,
    node4:HashSet<(u64,LevelSubstitution)>,
}
#[cfg(feature="diagnostics")]
impl C106SupportCounts {
    fn record(&mut self,terminal:&Closure,spent:usize,proven:bool) {
        self.requests+=1;
        if terminal.expr!=ExprId(7219) {return;}
        self.target+=1;
        let (Some(node2),Some(node4))=(
            terminal.env.diagnostic_binding_node_id(2),
            terminal.env.diagnostic_binding_node_id(4),
        ) else {self.missing+=1;return;};
        self.complete+=1;
        let levels=terminal.levels.clone();
        if !self.node2.insert((node2,levels.clone())) {self.node2_repeated+=1;}
        if !self.node4.insert((node4,levels.clone())) {self.node4_repeated+=1;}
        let group=self.pairs.entry((node2,node4,levels)).or_default();
        if group.requests>0 {
            self.pair_repeated+=1;
            self.repeated_spent+=spent;
            if group.had_proven {self.prior_proven+=1;}
            else {self.prior_unresolved+=1;}
        }
        group.requests+=1;
        group.charged+=spent;
        group.had_proven|=proven;
    }
}
#[cfg(feature="diagnostics")]
struct C106SupportReceipt<'a> {
    counts:&'a RefCell<C106SupportCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
// C109 asks which *source function* is bound at BVar(2) in N21's
// ExprId(7219), after following actual immutable lexical BVar links.
// Grouping by source ExprId deliberately drops environment/levels: this is
// a program-shape census, emphatically not a semantic equivalence key.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C109FunctionGroup {requests:usize,associated_charge:usize}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C109FunctionCounts {
    requests:usize,target:usize,closure:usize,free:usize,
    neutral:usize,natlit:usize,missing:usize,
    chain_steps:usize,max_chain:usize,chain_capped:usize,
    source_repeated:usize,
    groups:HashMap<(ExprId,u8),C109FunctionGroup>,
}
#[cfg(feature="diagnostics")]
impl C109FunctionCounts {
    fn record(&mut self,terminal:&Closure,spent:usize,expressions:&IdTable<ExprId,Expr>) {
        self.requests+=1;
        if terminal.expr!=ExprId(7219) {return;}
        self.target+=1;
        let Some(mut binding)=terminal.env.lookup_binding_ref(2) else {
            self.missing+=1;return;
        };
        let mut steps=0;
        let mut value;
        loop {
            if let EnvBinding::Closure(c)=binding {
                value=c;
                if steps<16
                    && let Some(Expr::BVar(index))=expressions.get(value.expr)
                    && let Some(next)=value.env.lookup_binding_ref(*index) {
                    steps+=1;
                    binding=next;
                    continue;
                }
                if steps==16 && matches!(expressions.get(value.expr),Some(Expr::BVar(_))) {
                    self.chain_capped+=1;
                }
                self.closure+=1;
                let kind=match expressions.get(value.expr) {
                    Some(Expr::BVar(_))=>0,Some(Expr::App{..})=>1,
                    Some(Expr::Lam{..})=>2,Some(Expr::Let{..})=>3,
                    Some(Expr::Const{..})=>4,Some(Expr::Proj{..})=>5,
                    Some(Expr::NatLit(_))=>6,_=>7,
                };
                let group=self.groups.entry((value.expr,kind)).or_default();
                if group.requests>0 {self.source_repeated+=1;}
                group.requests+=1;
                group.associated_charge+=spent;
                break;
            }
            match binding {
                EnvBinding::Free(_)=>self.free+=1,
                EnvBinding::Neutral(_)=>self.neutral+=1,
                EnvBinding::NatLit(_)=>self.natlit+=1,
                EnvBinding::Closure(_)=>unreachable!(),
            }
            break;
        }
        self.chain_steps+=steps;
        self.max_chain=self.max_chain.max(steps);
    }
}
#[cfg(feature="diagnostics")]
struct C109FunctionReceipt<'a> {
    counts:&'a RefCell<C109FunctionCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
// C110 adds the *actual free lexical captures* of C109's two repeated
// source lambdas. These static support sets are pinned to the frozen N21
// input by the source-only probe. A captured node-identity pair and exact
// level substitution is an observational key, NOT a proved semantic key.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C110CaptureGroup {requests:usize,charged:usize}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C110CaptureCounts {
    requests:usize,target:usize,complete:usize,missing:usize,unsupported:usize,
    pair_repeated:usize,repeated_spent:usize,a_repeated:usize,b_repeated:usize,
    pairs:HashMap<(ExprId,u64,u64,LevelSubstitution),C110CaptureGroup>,
    node_a:HashSet<(ExprId,u64,LevelSubstitution)>,
    node_b:HashSet<(ExprId,u64,LevelSubstitution)>,
    single_repeats:HashMap<ExprId,(usize,usize)>,
}
#[cfg(feature="diagnostics")]
impl C110CaptureCounts {
    fn record(&mut self,terminal:&Closure,spent:usize,expressions:&IdTable<ExprId,Expr>) {
        self.requests+=1;
        if terminal.expr!=ExprId(7219) {return;}
        self.target+=1;
        let Some(mut binding)=terminal.env.lookup_binding_ref(2) else {
            self.missing+=1;return;
        };
        let mut steps=0;
        loop {
            if let EnvBinding::Closure(value)=binding {
                if steps<16
                    && let Some(Expr::BVar(index))=expressions.get(value.expr)
                    && let Some(next)=value.env.lookup_binding_ref(*index) {
                    steps+=1;
                    binding=next;
                    continue;
                }
                let (first,second)=match value.expr {
                    ExprId(7197)=>(1,3),
                    ExprId(6303)=>(0,2),
                    _=>{self.unsupported+=1;return;},
                };
                let (Some(node_a),Some(node_b))=(
                    value.env.diagnostic_binding_node_id(first),
                    value.env.diagnostic_binding_node_id(second),
                ) else {self.missing+=1;return;};
                self.complete+=1;
                let levels=value.levels.clone();
                let singles=self.single_repeats.entry(value.expr).or_default();
                if !self.node_a.insert((value.expr,node_a,levels.clone())) {
                    self.a_repeated+=1;
                    singles.0+=1;
                }
                if !self.node_b.insert((value.expr,node_b,levels.clone())) {
                    self.b_repeated+=1;
                    singles.1+=1;
                }
                let key=(value.expr,node_a,node_b,levels);
                let group=self.pairs.entry(key).or_default();
                if group.requests>0 {
                    self.pair_repeated+=1;
                    self.repeated_spent+=spent;
                }
                group.requests+=1;
                group.charged+=spent;
                return;
            }
            self.missing+=1;
            return;
        }
    }
}
#[cfg(feature="diagnostics")]
struct C110CaptureReceipt<'a> {
    counts:&'a RefCell<C110CaptureCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
// C111 attributes actual caller-charged major-exposure attempts to the
// checked recursor owner, result class and exact UNKNOWN residual. The
// 512 local allowance is tested as a *measurement*, never raised here.
#[cfg(feature="diagnostics")]
#[derive(Clone,Copy,Default)]
struct C111MajorGroup {
    requests:usize,charged:usize,constructor:usize,nested:usize,
    other:usize,unknown:usize,refuted:usize,
}
#[cfg(feature="diagnostics")]
impl C111MajorGroup {
    fn record(&mut self,spent:usize,kind:usize) {
        self.requests+=1;
        self.charged+=spent;
        match kind {
            0=>self.constructor+=1,1=>self.nested+=1,
            2=>self.other+=1,3=>self.unknown+=1,
            4=>self.refuted+=1,_=>unreachable!(),
        }
    }
}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C111MajorCounts {
    all:C111MajorGroup, at_least_512:usize,max_spent:usize,
    heads:HashMap<u64,C111MajorGroup>,
    buckets:[C111MajorGroup;6],
    reasons:HashMap<&'static str,C111MajorGroup>,
}
#[cfg(feature="diagnostics")]
impl C111MajorCounts {
    fn record(&mut self,head:u64,spent:usize,kind:usize,reason:Option<&'static str>) {
        self.all.record(spent,kind);
        self.at_least_512+=usize::from(spent>=512);
        self.max_spent=self.max_spent.max(spent);
        self.heads.entry(head).or_default().record(spent,kind);
        let bucket=match spent {0..=1=>0,2..=7=>1,8..=31=>2,
            32..=127=>3,128..=511=>4,_=>5};
        self.buckets[bucket].record(spent,kind);
        if let Some(reason)=reason {self.reasons.entry(reason).or_default().record(spent,kind);}
    }
}
#[cfg(feature="diagnostics")]
struct C111MajorReceipt<'a> {
    counts:&'a RefCell<C111MajorCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C111MajorReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let counts=self.counts.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || counts.all.requests<10
            || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        let all=&counts.all;
        eprintln!("NUCLEUS_C111_MAJOR_OWNER:start={}:spent={spent}:requests={}:charged={}:constructor={}:nested={}:other={}:unknown={}:refuted={}:at_least_512={}:max_spent={}",
            self.start,all.requests,all.charged,all.constructor,all.nested,all.other,
            all.unknown,all.refuted,counts.at_least_512,counts.max_spent);
        let mut heads:Vec<_>=counts.heads.iter().collect();
        heads.sort_by_key(|(head,_)|**head);
        for (head,g) in heads {
            eprintln!("NUCLEUS_C111_MAJOR_GROUP:start={}:head={head}:requests={}:charged={}:constructor={}:nested={}:other={}:unknown={}:refuted={}",
                self.start,g.requests,g.charged,g.constructor,g.nested,g.other,g.unknown,g.refuted);
        }
        for (bucket,g) in counts.buckets.iter().enumerate() {
            eprintln!("NUCLEUS_C111_MAJOR_BUCKET:start={}:bucket={bucket}:requests={}:charged={}:constructor={}:nested={}:other={}:unknown={}:refuted={}",
                self.start,g.requests,g.charged,g.constructor,g.nested,g.other,g.unknown,g.refuted);
        }
        let mut reasons:Vec<_>=counts.reasons.iter().collect();
        reasons.sort_by(|a,b|b.1.charged.cmp(&a.1.charged).then(a.0.cmp(b.0)));
        for (reason,g) in reasons {
            eprintln!("NUCLEUS_C111_MAJOR_REASON:start={}:reason={reason}:requests={}:charged={}",
                self.start,g.requests,g.charged);
        }
    }
}
// C112 follows only genuinely returned source-registered constructors from
// their caller-charged major exposure through the *actual* selected source
// rule and subsequent RHS result. Observation cannot select a constructor.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C112RuleGroup {
    requests:usize,charged:usize,high_count:usize,high_charged:usize,
    min_depth:usize,max_depth:usize,rhs_proven:usize,rhs_unknown:usize,rhs_nested:usize,
}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C112RuleCounts {
    constructor_results:usize,all:C112RuleGroup,
    groups:HashMap<(u64,u64,u64),C112RuleGroup>,
    high:Vec<(usize,u64,u64,u64,usize,usize,usize,bool,&'static str)>,
}
#[cfg(feature="diagnostics")]
impl C112RuleCounts {
    fn record(&mut self,recursor:u64,constructor:u64,rhs:u64,charge:usize,
        depth:usize,major_parents:usize,requested:bool,outcome:&'static str,
    ) {
        let high=charge>=512;
        for group in [&mut self.all,self.groups.entry((recursor,constructor,rhs)).or_default()] {
            if group.requests==0 {group.min_depth=depth;}
            group.requests+=1;
            group.charged+=charge;
            group.high_count+=usize::from(high);
            if high {group.high_charged+=charge;}
            group.min_depth=group.min_depth.min(depth);
            group.max_depth=group.max_depth.max(depth);
            group.rhs_proven+=usize::from(outcome!="unknown");
            group.rhs_unknown+=usize::from(outcome=="unknown");
            group.rhs_nested+=usize::from(outcome=="nested");
        }
        if high {self.high.push((self.all.requests,recursor,constructor,rhs,charge,
            depth,major_parents,requested,outcome));}
    }
}
#[cfg(feature="diagnostics")]
struct C112RuleReceipt<'a> {
    counts:&'a RefCell<C112RuleCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C112RuleReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let counts=self.counts.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || counts.all.requests<10
            || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        let all=&counts.all;
        eprintln!("NUCLEUS_C112_RULE_OWNER:start={}:constructor_results={}:selected={}:charged={}:high_count={}:high_charged={}:rhs_proven={}:rhs_unknown={}",
            self.start,counts.constructor_results,all.requests,all.charged,
            all.high_count,all.high_charged,all.rhs_proven,all.rhs_unknown);
        let mut groups:Vec<_>=counts.groups.iter().collect();
        groups.sort_by_key(|(key,_)|**key);
        for ((recursor,constructor,rhs),g) in groups {
            eprintln!("NUCLEUS_C112_RULE_GROUP:start={}:recursor={recursor}:constructor={constructor}:rhs={rhs}:requests={}:charged={}:high_count={}:high_charged={}:min_depth={}:max_depth={}:rhs_proven={}:rhs_unknown={}:rhs_nested={}",
                self.start,g.requests,g.charged,g.high_count,g.high_charged,
                g.min_depth,g.max_depth,g.rhs_proven,g.rhs_unknown,g.rhs_nested);
        }
        for (seq,recursor,constructor,rhs,charge,depth,major_parents,requested,outcome) in &counts.high {
            eprintln!("NUCLEUS_C112_RULE_HIGH:start={}:seq={seq}:recursor={recursor}:constructor={constructor}:rhs={rhs}:charge={charge}:depth={depth}:major_parents={major_parents}:requested={}:rhs_outcome={outcome}",
                self.start,usize::from(*requested));
        }
    }
}
// C113 measures subsequent source-RHS work for the same high-charge C112
// events, and marks an actual Continuation::Major pop. No inferred result
// or syntactic equivalence influences execution.
#[cfg(feature="diagnostics")]
struct C113HighEvent {
    recursor:u64,constructor:u64,rhs:u64,major:usize,
    telescope:usize,rhs_work:usize,depth:usize,major_parents:usize,resumed:bool,
}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C113HighCounts {events:Vec<C113HighEvent>}
#[cfg(feature="diagnostics")]
struct C113HighReceipt<'a> {
    counts:&'a RefCell<C113HighCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C113HighReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let events=&self.counts.borrow().events;
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || events.len()<10
            || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        eprintln!("NUCLEUS_C113_HIGH_OWNER:start={}:events={}:major_charge={}:telescope_charge={}:rhs_charge={}:resumed={}",
            self.start,events.len(),events.iter().map(|e|e.major).sum::<usize>(),
            events.iter().map(|e|e.telescope).sum::<usize>(),
            events.iter().map(|e|e.rhs_work).sum::<usize>(),
            events.iter().filter(|e|e.resumed).count());
        for (idx,e) in events.iter().enumerate() {
            eprintln!("NUCLEUS_C113_HIGH_EVENT:start={}:seq={}:recursor={}:constructor={}:rhs={}:major={}:telescope={}:rhs_work={}:depth={}:major_parents={}:resumed={}",
                self.start,idx+1,e.recursor,e.constructor,e.rhs,e.major,
                e.telescope,e.rhs_work,e.depth,e.major_parents,usize::from(e.resumed));
        }
    }
}
// C114 counts actual evaluator loop kinds while the original high-cost
// major request runs. Loop counts are not fuel units: only the independent
// inclusive major charge is conserved and compared against C113.
#[cfg(feature="diagnostics")]
struct C114HighEvent {
    major:usize,loops:usize,unique:usize,repeat:usize,kinds:[usize;8],
}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C114HighCounts { events:Vec<C114HighEvent> }
#[cfg(feature="diagnostics")]
struct C114HighReceipt<'a> {
    counts:&'a RefCell<C114HighCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C114HighReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let events=&self.counts.borrow().events;
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || events.len()<10
            || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        let total:usize=events.iter().map(|e|e.major).sum();
        let loops:usize=events.iter().map(|e|e.loops).sum();
        let unique:usize=events.iter().map(|e|e.unique).sum();
        let repeat:usize=events.iter().map(|e|e.repeat).sum();
        let kinds:[usize;8]=std::array::from_fn(|i|events.iter().map(|e|e.kinds[i]).sum());
        eprintln!("NUCLEUS_C114_HIGH_OWNER:start={}:events={}:major_charge={total}:loops={loops}:unique={unique}:repeat={repeat}:k0={}:k1={}:k2={}:k3={}:k4={}:k5={}:k6={}:k7={}",
            self.start,events.len(),kinds[0],kinds[1],kinds[2],kinds[3],kinds[4],kinds[5],kinds[6],kinds[7]);
        for (idx,e) in events.iter().enumerate() {
            let k=&e.kinds;
            eprintln!("NUCLEUS_C114_HIGH_EVENT:start={}:seq={}:major={}:loops={}:unique={}:repeat={}:k0={}:k1={}:k2={}:k3={}:k4={}:k5={}:k6={}:k7={}",
                self.start,idx+1,e.major,e.loops,e.unique,e.repeat,k[0],k[1],k[2],k[3],k[4],k[5],k[6],k[7]);
        }
    }
}
// C115: replay the *actual* BVar evaluator steps inside each C114 high-major
// exposure, keeping the entire live head/pending state and the exact captured
// lexical node separately. These identity censuses do not authorize reuse.
#[cfg(feature="diagnostics")]
struct C115BVarStep {
    state:(Closure,Vec<Closure>,Transparency,bool),
    node:Option<u64>,
    kind:usize,
    context:Option<C116BVarContext>,
    c118_invocation:Option<usize>,
    c118_fuel:Option<usize>,
    c118_terminal:Option<C118Terminal>,
    c119_context:Option<(usize,usize,Option<usize>)>,
}
#[cfg(feature="diagnostics")]
struct C118Terminal {
    result:Rc<Judgment<Exposure>>,
    tail_work:Option<usize>,
}
#[cfg(feature="diagnostics")]
struct C116BVarContext {
    budget:usize,
    fuel:Option<usize>,
    witnesses:bool,
    visits:Vec<(u64,u64,u64)>,
    target:Option<Closure>,
}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C115BVarHistogram {
    bvar:usize,full_unique:usize,full_repeat:usize,
    node_unique:usize,node_repeat:usize,node_missing:usize,
    kinds:[usize;5],
}
#[cfg(feature="diagnostics")]
impl C115BVarHistogram {
    fn from_steps(steps:&[C115BVarStep])->Self {
        let mut counts=Self::default();
        let mut full=HashSet::new();
        let mut nodes=HashSet::new();
        for step in steps {
            counts.bvar+=1;
            counts.kinds[step.kind]+=1;
            if full.insert(&step.state) {counts.full_unique+=1;} else {counts.full_repeat+=1;}
            if let Some(node)=step.node {
                if nodes.insert((step.state.0.expr.0,node)) {
                    counts.node_unique+=1;
                } else {counts.node_repeat+=1;}
            } else {counts.node_missing+=1;}
        }
        counts
    }
}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C115BoundCounts {
    events:Vec<C115BVarHistogram>,
    across_full_seen:HashSet<(Closure,Vec<Closure>,Transparency,bool)>,
    across_node_seen:HashSet<(u64,u64)>,
    across_full_repeat:usize,
    across_node_repeat:usize,
    across_node_missing:usize,
}
#[cfg(feature="diagnostics")]
impl C115BoundCounts {
    fn record(&mut self, steps:&[C115BVarStep]) {
        for step in steps {
            if !self.across_full_seen.insert(step.state.clone()) {
                self.across_full_repeat+=1;
            }
            if let Some(node)=step.node {
                if !self.across_node_seen.insert((step.state.0.expr.0,node)) {
                    self.across_node_repeat+=1;
                }
            } else {self.across_node_missing+=1;}
        }
        self.events.push(C115BVarHistogram::from_steps(steps));
    }
}
// A repeated head is not yet a repeated completed evaluation. C116 asks how
// many such heads still repeat when local limits, witness mode and exact
// active visited identities are added. Global shared fuel is a separate
// resource constraint, not an assertion of semantic inequality.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C116ContextCounts {
    events:usize,bvar:usize,full_repeat:usize,budget_repeat:usize,
    visit_repeat:usize,fuel_repeat:usize,target_mismatch:usize,
    witness_true:usize,witness_false:usize,visit_nontrivial:usize,
    full:HashMap<(Closure,Vec<Closure>,Transparency,bool),(usize,Option<Closure>)>,
    budget:HashSet<((Closure,Vec<Closure>,Transparency,bool),usize,bool)>,
    visits:HashSet<(((Closure,Vec<Closure>,Transparency,bool),usize,bool),Vec<(u64,u64,u64)>)>,
    fuels:HashSet<((((Closure,Vec<Closure>,Transparency,bool),usize,bool),Vec<(u64,u64,u64)>),Option<usize>)>,
}
#[cfg(feature="diagnostics")]
impl C116ContextCounts {
    fn record(&mut self,steps:&[C115BVarStep]) {
        self.events+=1;
        for step in steps {
            let ctx=step.context.as_ref().expect("C116 step carries source-native context");
            self.bvar+=1;
            if ctx.witnesses {self.witness_true+=1;} else {self.witness_false+=1;}
            if ctx.visits.len()>1 {self.visit_nontrivial+=1;}
            if let Some(prior)=self.full.get(&step.state) {
                self.full_repeat+=1;
                if *prior!=(step.kind,ctx.target.clone()) {self.target_mismatch+=1;}
            } else {self.full.insert(step.state.clone(),(step.kind,ctx.target.clone()));}
            let budget=(step.state.clone(),ctx.budget,ctx.witnesses);
            if !self.budget.insert(budget.clone()) {self.budget_repeat+=1;}
            let visit=(budget,ctx.visits.clone());
            if !self.visits.insert(visit.clone()) {self.visit_repeat+=1;}
            if !self.fuels.insert((visit,ctx.fuel)) {self.fuel_repeat+=1;}
        }
    }
}
#[cfg(feature="diagnostics")]
struct C116ContextReceipt<'a> {
    counts:&'a RefCell<C116ContextCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C116ContextReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let c=self.counts.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || c.events<10 || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        eprintln!("NUCLEUS_C116_CONTEXT_OWNER:start={}:events={}:bvar={}:full_repeat={}:budget_repeat={}:visit_repeat={}:fuel_repeat={}:target_mismatch={}:witness_true={}:witness_false={}:visit_nontrivial={}",
            self.start,c.events,c.bvar,c.full_repeat,c.budget_repeat,c.visit_repeat,
            c.fuel_repeat,c.target_mismatch,c.witness_true,c.witness_false,c.visit_nontrivial);
    }
}
// C117 tests an actual existing cache boundary: a completed exposure *call*
// is not the same thing as an intermediate BVar loop state. Keep the two
// identity sets separate until an exact source-qualified intersection exists.
#[cfg(feature="diagnostics")]
struct C117CompletedCall {
    state:(Closure,Vec<Closure>,Transparency,bool),
    eligible:Option<Value>,
    unknown:bool,refuted:bool,cached:bool,entry_bvar:bool,
}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C117CallCounts {
    events:usize,calls:usize,eligible:usize,unknown:usize,refuted:usize,
    cached_hits:usize,entry_bvar:usize,completed_repeated:usize,
    completed_value_conflicts:usize,bvar:usize,bvar_repeated:usize,
    completed:HashMap<(Closure,Vec<Closure>,Transparency,bool),Value>,
    bvar_seen:HashSet<(Closure,Vec<Closure>,Transparency,bool)>,
    bvar_states:Vec<(Closure,Vec<Closure>,Transparency,bool)>,
    repeated_bvar_states:Vec<(Closure,Vec<Closure>,Transparency,bool)>,
}
#[cfg(feature="diagnostics")]
impl C117CallCounts {
    fn record(&mut self,calls:&[C117CompletedCall],steps:&[C115BVarStep]) {
        self.events+=1;
        for call in calls {
            self.calls+=1;
            self.unknown+=usize::from(call.unknown);
            self.refuted+=usize::from(call.refuted);
            self.cached_hits+=usize::from(call.cached);
            self.entry_bvar+=usize::from(call.entry_bvar);
            if let Some(value)=&call.eligible {
                self.eligible+=1;
                if let Some(previous)=self.completed.get(&call.state) {
                    self.completed_repeated+=1;
                    if previous!=value {self.completed_value_conflicts+=1;}
                } else {self.completed.insert(call.state.clone(),value.clone());}
            }
        }
        for step in steps {
            self.bvar+=1;
            if !self.bvar_seen.insert(step.state.clone()) {
                self.bvar_repeated+=1;
                self.repeated_bvar_states.push(step.state.clone());
            }
            self.bvar_states.push(step.state.clone());
        }
    }
}
#[cfg(feature="diagnostics")]
struct C117CallReceipt<'a> {
    counts:&'a RefCell<C117CallCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C117CallReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let c=self.counts.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || c.events<10 || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        let bvar_entry_overlap=c.bvar_states.iter().filter(|s|c.completed.contains_key(*s)).count();
        let repeated_bvar_entry_overlap=c.repeated_bvar_states.iter().filter(|s|c.completed.contains_key(*s)).count();
        eprintln!("NUCLEUS_C117_CALL_OWNER:start={}:events={}:calls={}:eligible={}:unknown={}:refuted={}:cached_hits={}:entry_bvar={}:completed_repeated={}:completed_value_conflicts={}:bvar={}:bvar_repeated={}:bvar_entry_overlap={bvar_entry_overlap}:repeated_bvar_entry_overlap={repeated_bvar_entry_overlap}",
            self.start,c.events,c.calls,c.eligible,c.unknown,c.refuted,c.cached_hits,
            c.entry_bvar,c.completed_repeated,c.completed_value_conflicts,c.bvar,c.bvar_repeated);
    }
}
// C118: complete only *real* source evaluator invocations. Every observed
// intermediate BVar visit receives the actual terminal result and actual
// remaining shared-work charge from its original invocation, with no replay.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C118SegmentCounts {
    events:usize,bvar:usize,repeated:usize,
    terminal_proven:usize,terminal_unknown:usize,terminal_refuted:usize,terminal_missing:usize,
    repeat_same_result:usize,repeat_conflict:usize,
    repeat_same_tail:usize,repeat_tail_conflict:usize,
    repeat_tail_sum:usize,repeat_tail_min:usize,repeat_tail_max:usize,
    repeat_tail_positive:usize,repeat_tail_zero:usize,
    max_tail_source:u64,max_tail_node:u64,max_tail_pending:usize,
    seen:HashMap<((Closure,Vec<Closure>,Transparency,bool),usize,bool,Vec<(u64,u64,u64)>),
        (Option<Rc<Judgment<Exposure>>>,Option<usize>)>,
}
#[cfg(feature="diagnostics")]
impl C118SegmentCounts {
    fn record(&mut self,steps:&[C115BVarStep]) {
        self.events+=1;
        for step in steps {
            self.bvar+=1;
            let ctx=step.context.as_ref().expect("C118 requires exact captured local context");
            let key=(step.state.clone(),ctx.budget,ctx.witnesses,ctx.visits.clone());
            let current=step.c118_terminal.as_ref().map(|t|t.result.clone());
            let tail=step.c118_terminal.as_ref().and_then(|t|t.tail_work);
            match current.as_ref().map(|result|result.as_ref()) {
                Some(Judgment::Proven{..})=>self.terminal_proven+=1,
                Some(Judgment::Unknown{..})=>self.terminal_unknown+=1,
                Some(Judgment::Refuted{..})=>self.terminal_refuted+=1,
                None=>self.terminal_missing+=1,
            }
            if let Some((previous,prior_tail))=self.seen.get(&key) {
                self.repeated+=1;
                if previous==&current {self.repeat_same_result+=1;}
                else {self.repeat_conflict+=1;}
                if prior_tail==&tail {self.repeat_same_tail+=1;}
                else {self.repeat_tail_conflict+=1;}
                let charge=tail.unwrap_or(0);
                self.repeat_tail_sum+=charge;
                if self.repeated==1 {self.repeat_tail_min=charge;}
                else {self.repeat_tail_min=self.repeat_tail_min.min(charge);}
                if charge>0 {self.repeat_tail_positive+=1;}
                else {self.repeat_tail_zero+=1;}
                if charge>self.repeat_tail_max {
                    self.repeat_tail_max=charge;
                    self.max_tail_source=step.state.0.expr.0;
                    self.max_tail_node=step.node.unwrap_or(0);
                    self.max_tail_pending=step.state.1.len();
                }
            } else {self.seen.insert(key,(current,tail));}
        }
    }
}
#[cfg(feature="diagnostics")]
struct C118SegmentReceipt<'a> {
    counts:&'a RefCell<C118SegmentCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C118SegmentReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let c=self.counts.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || c.events<10 || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        eprintln!("NUCLEUS_C118_SEGMENT_OWNER:start={}:events={}:bvar={}:repeated={}:terminal_proven={}:terminal_unknown={}:terminal_refuted={}:terminal_missing={}:repeat_same_result={}:repeat_conflict={}:repeat_same_tail={}:repeat_tail_conflict={}:repeat_tail_sum={}:repeat_tail_min={}:repeat_tail_max={}:repeat_tail_positive={}:repeat_tail_zero={}:max_tail_source={}:max_tail_node={}:max_tail_pending={}",
            self.start,c.events,c.bvar,c.repeated,c.terminal_proven,c.terminal_unknown,
            c.terminal_refuted,c.terminal_missing,c.repeat_same_result,c.repeat_conflict,
            c.repeat_same_tail,c.repeat_tail_conflict,c.repeat_tail_sum,c.repeat_tail_min,
            c.repeat_tail_max,c.repeat_tail_positive,c.repeat_tail_zero,
            c.max_tail_source,c.max_tail_node,c.max_tail_pending);
    }
}
#[cfg(feature="diagnostics")]
struct C118InvocationScope<'a> {active:&'a Cell<Option<usize>>,previous:Option<usize>}
#[cfg(feature="diagnostics")]
impl Drop for C118InvocationScope<'_> {
    fn drop(&mut self) {self.active.set(self.previous);}
}
// C119: the C116 local-state key is not assumed to include every ambient
// evaluator guard. Compare the actual depth and owner work at repeat visits.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C119ContextCounts {
    events:usize,bvar:usize,repeated:usize,
    depth_equal:usize,depth_different:usize,
    projection_equal:usize,projection_different:usize,
    fuel_equal:usize,fuel_different:usize,
    max_depth:usize,near_limit:usize,
    witness_expr:u64,witness_depth_before:usize,witness_depth_after:usize,
    seen:HashMap<((Closure,Vec<Closure>,Transparency,bool),usize,bool,Vec<(u64,u64,u64)>),
        (usize,usize,Option<usize>)>,
}
#[cfg(feature="diagnostics")]
impl C119ContextCounts {
    fn record(&mut self,steps:&[C115BVarStep]) {
        self.events+=1;
        for step in steps {
            self.bvar+=1;
            let ctx=step.context.as_ref().expect("C119 requires exact captured local context");
            let current=step.c119_context.expect("C119 requires actual dynamic context");
            let key=(step.state.clone(),ctx.budget,ctx.witnesses,ctx.visits.clone());
            self.max_depth=self.max_depth.max(current.0);
            if current.0>=63 {self.near_limit+=1;}
            if let Some(previous)=self.seen.get(&key) {
                self.repeated+=1;
                if previous.0==current.0 {self.depth_equal+=1;}
                else {
                    self.depth_different+=1;
                    if self.depth_different==1 {
                        self.witness_expr=step.state.0.expr.0;
                        self.witness_depth_before=previous.0;
                        self.witness_depth_after=current.0;
                    }
                }
                if previous.1==current.1 {self.projection_equal+=1;}
                else {self.projection_different+=1;}
                if previous.2==current.2 {self.fuel_equal+=1;}
                else {self.fuel_different+=1;}
            } else {self.seen.insert(key,current);}
        }
    }
}
#[cfg(feature="diagnostics")]
struct C119ContextReceipt<'a> {
    counts:&'a RefCell<C119ContextCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C119ContextReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let c=self.counts.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || c.events<10 || PRINTED.fetch_add(1,Ordering::Relaxed)>=32{return;}
        eprintln!("NUCLEUS_C119_CONTEXT_OWNER:start={}:events={}:bvar={}:repeated={}:depth_equal={}:depth_different={}:projection_equal={}:projection_different={}:fuel_equal={}:fuel_different={}:max_depth={}:near_limit={}:witness_expr={}:witness_depth_before={}:witness_depth_after={}",
            self.start,c.events,c.bvar,c.repeated,c.depth_equal,c.depth_different,
            c.projection_equal,c.projection_different,c.fuel_equal,c.fuel_different,
            c.max_depth,c.near_limit,c.witness_expr,c.witness_depth_before,c.witness_depth_after);
    }
}
// C120: repeated interior tails share one monotonically decreasing owner
// allowance. Their summed lengths double-count overlapping charged work.
// Union actual [remaining, start) counter intervals within each owner.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C120SpanCounts {
    events:usize,bvar:usize,repeated:usize,span_positive:usize,span_zero:usize,
    sum:usize,spans:Vec<(usize,usize)>,
    seen:HashSet<((Closure,Vec<Closure>,Transparency,bool),usize,bool,Vec<(u64,u64,u64)>)>,
}
#[cfg(feature="diagnostics")]
impl C120SpanCounts {
    fn record(&mut self,steps:&[C115BVarStep]) {
        self.events+=1;
        for step in steps {
            self.bvar+=1;
            let context=step.context.as_ref().expect("C120 requires captured C116 context");
            let key=(step.state.clone(),context.budget,context.witnesses,context.visits.clone());
            if !self.seen.insert(key) {
                self.repeated+=1;
                let start=step.c118_fuel.expect("C120 requires C118 actual fuel");
                let charge=step.c118_terminal.as_ref()
                    .and_then(|end|end.tail_work)
                    .expect("C120 requires actual same-invocation terminal fuel");
                self.sum+=charge;
                if charge==0 {self.span_zero+=1;}
                else {
                    self.span_positive+=1;
                    let low=start.checked_sub(charge).expect("non-monotonic owner-fuel trace");
                    self.spans.push((low,start));
                }
            }
        }
    }
    fn union_and_components(&self)->(usize,usize) {
        let mut spans=self.spans.clone();
        spans.sort_unstable();
        let (mut total,mut components)=(0,0);
        let mut current:Option<(usize,usize)>=None;
        for (low,high) in spans {
            if let Some((old_low,old_high))=current {
                if low<=old_high {current=Some((old_low,old_high.max(high)));}
                else {
                    total+=old_high-old_low;
                    components+=1;
                    current=Some((low,high));
                }
            } else {current=Some((low,high));}
        }
        if let Some((low,high))=current {total+=high-low;components+=1;}
        (total,components)
    }
}
#[cfg(feature="diagnostics")]
struct C120SpanReceipt<'a> {
    counts:&'a RefCell<C120SpanCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C120SpanReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let c=self.counts.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || c.events<10 || PRINTED.fetch_add(1,Ordering::Relaxed)>=32{return;}
        let (union,components)=c.union_and_components();
        eprintln!("NUCLEUS_C120_SPAN_OWNER:start={}:events={}:bvar={}:repeated={}:span_positive={}:span_zero={}:sum={}:union={}:overlap={}:components={}",
            self.start,c.events,c.bvar,c.repeated,c.span_positive,c.span_zero,
            c.sum,union,c.sum.saturating_sub(union),components);
    }
}
// C121 observes the neglected 128..511-unit major requests, preserving the
// registered source result and exact evaluator-kind delta on each live call.
#[cfg(feature="diagnostics")]
struct C121MidEvent {
    recursor:u64,rhs:u64,constructor:u64,charge:usize,loops:usize,
    depth:usize,major_parents:usize,requested:usize,outcome:usize,kinds:[usize;8],
}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C121MidCounts {events:Vec<C121MidEvent>}
#[cfg(feature="diagnostics")]
struct C121MidReceipt<'a> {
    counts:&'a RefCell<C121MidCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C121MidReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let events=&self.counts.borrow().events;
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || events.len()<10 || PRINTED.fetch_add(1,Ordering::Relaxed)>=32{return;}
        let total:usize=events.iter().map(|e|e.charge).sum();
        let loops:usize=events.iter().map(|e|e.loops).sum();
        let kinds:[usize;8]=std::array::from_fn(|i|events.iter().map(|e|e.kinds[i]).sum());
        let outcomes:[usize;5]=std::array::from_fn(|i|events.iter().filter(|e|e.outcome==i).count());
        eprintln!("NUCLEUS_C121_MID_OWNER:start={}:events={}:major_charge={total}:loops={loops}:other_work={}:constructor={}:nested={}:other={}:unknown={}:refuted={}:k0={}:k1={}:k2={}:k3={}:k4={}:k5={}:k6={}:k7={}",
            self.start,events.len(),total.saturating_sub(loops),outcomes[0],outcomes[1],outcomes[2],
            outcomes[3],outcomes[4],kinds[0],kinds[1],kinds[2],kinds[3],
            kinds[4],kinds[5],kinds[6],kinds[7]);
        for (idx,e) in events.iter().enumerate() {
            let k=&e.kinds;
            eprintln!("NUCLEUS_C121_MID_EVENT:start={}:seq={}:recursor={}:rhs={}:constructor={}:charge={}:loops={}:depth={}:major_parents={}:requested={}:outcome={}:k0={}:k1={}:k2={}:k3={}:k4={}:k5={}:k6={}:k7={}",
                self.start,idx+1,e.recursor,e.rhs,e.constructor,e.charge,e.loops,
                e.depth,e.major_parents,e.requested,e.outcome,k[0],k[1],k[2],
                k[3],k[4],k[5],k[6],k[7]);
        }
    }
}
// C122 observes registered source closures on both sides of each successful
// nested-major transition. Frame/binding IDs are diagnostic identity only,
// never evidence of equality between meaning-bearing captured values.
#[cfg(feature="diagnostics")]
struct C122SourceEvent {
    seq:usize,recursor:u64,expr:u64,env:u64,expr_kind:usize,
    binding:u64,bound_expr:u64,bound_env:u64,next_head:u64,next_arity:usize,
    next_expr:u64,next_env:u64,next_expr_kind:usize,
    next_binding:u64,next_bound_expr:u64,next_bound_env:u64,
}
#[cfg(feature="diagnostics")]
struct C122SourceReceipt<'a> {
    events:&'a RefCell<Vec<C122SourceEvent>>,fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C122SourceReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let events=self.events.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || events.len()<10 || PRINTED.fetch_add(1,Ordering::Relaxed)>=32{return;}
        for e in events.iter() {
            eprintln!("NUCLEUS_C122_NESTED_TRANSITION:start={}:seq={}:recursor={}:expr={}:env={}:expr_kind={}:binding={}:bound_expr={}:bound_env={}:next_head={}:next_arity={}:next_expr={}:next_env={}:next_expr_kind={}:next_binding={}:next_bound_expr={}:next_bound_env={}",
                self.start,e.seq,e.recursor,e.expr,e.env,e.expr_kind,e.binding,
                e.bound_expr,e.bound_env,e.next_head,e.next_arity,e.next_expr,
                e.next_env,e.next_expr_kind,e.next_binding,e.next_bound_expr,
                e.next_bound_env);
        }
    }
}
// C123 follows only immutable lexical BVar-to-closure links. The walk is
// observational: it neither spends evaluator fuel nor proves a transport rule.
#[cfg(feature="diagnostics")]
struct C123BVarChainEvent {
    seq:usize,hops:usize,terminal_expr:u64,terminal_env:u64,
    terminal_kind:usize,terminal_bvar:u64,terminal_binding_kind:usize,
    capped:usize,levels:usize,
}
#[cfg(feature="diagnostics")]
struct C123BVarChainReceipt<'a> {
    events:&'a RefCell<Vec<C123BVarChainEvent>>,
    fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C123BVarChainReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let events=self.events.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || events.len()<10 || PRINTED.fetch_add(1,Ordering::Relaxed)>=32{return;}
        for e in events.iter() {
            eprintln!("NUCLEUS_C123_BVAR_CHAIN:start={}:seq={}:hops={}:terminal_expr={}:terminal_env={}:terminal_kind={}:terminal_bvar={}:terminal_binding_kind={}:capped={}:levels={}",
                self.start,e.seq,e.hops,e.terminal_expr,e.terminal_env,
                e.terminal_kind,e.terminal_bvar,e.terminal_binding_kind,
                e.capped,e.levels);
        }
    }
}
// C124 describes the exact application skeleton at C123's source terminal,
// and attributes only actually observed C97 App/Lam steps to each live major.
#[cfg(feature="diagnostics")]
struct C124AppProfileEvent {
    seq:usize,root:u64,env:u64,arity:usize,head:u64,head_kind:usize,
    head_binding:u64,head_bound_expr:u64,head_bound_env:u64,
    outer_arg:u64,inner_arg:u64,outer_kind:usize,inner_kind:usize,
    outer_body:u64,inner_body:u64,app:usize,lam:usize,root_app:usize,
    top_app:u64,top_app_count:usize,top_lam:u64,top_lam_count:usize,
}
#[cfg(feature="diagnostics")]
struct C124AppProfileReceipt<'a> {
    events:&'a RefCell<Vec<C124AppProfileEvent>>,
    fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C124AppProfileReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let events=self.events.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || events.len()<10 || PRINTED.fetch_add(1,Ordering::Relaxed)>=32{return;}
        for e in events.iter() {
            eprintln!("NUCLEUS_C124_APP_PROFILE:start={}:seq={}:root={}:env={}:arity={}:head={}:head_kind={}:head_binding={}:head_bound_expr={}:head_bound_env={}:outer_arg={}:inner_arg={}:outer_kind={}:inner_kind={}:outer_body={}:inner_body={}:app={}:lam={}:root_app={}:top_app={}:top_app_count={}:top_lam={}:top_lam_count={}",
                self.start,e.seq,e.root,e.env,e.arity,e.head,e.head_kind,
                e.head_binding,e.head_bound_expr,e.head_bound_env,e.outer_arg,
                e.inner_arg,e.outer_kind,e.inner_kind,e.outer_body,e.inner_body,
                e.app,e.lam,e.root_app,e.top_app,e.top_app_count,e.top_lam,e.top_lam_count);
        }
    }
}
#[cfg(feature="diagnostics")]
struct C115BoundReceipt<'a> {
    counts:&'a RefCell<C115BoundCounts>,fuel:&'a Cell<Option<usize>>,start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C115BoundReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let counts=self.counts.borrow();
        let events=&counts.events;
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || events.len()<10
            || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        let sum=|f:fn(&C115BVarHistogram)->usize|events.iter().map(f).sum::<usize>();
        let bvar=sum(|e|e.bvar);
        let full_unique=sum(|e|e.full_unique);
        let full_repeat=sum(|e|e.full_repeat);
        let node_unique=sum(|e|e.node_unique);
        let node_repeat=sum(|e|e.node_repeat);
        let node_missing=sum(|e|e.node_missing);
        let kinds:[usize;5]=std::array::from_fn(|i|events.iter().map(|e|e.kinds[i]).sum());
        let across_full_unique=counts.across_full_seen.len();
        let across_full_repeat=counts.across_full_repeat;
        let across_node_unique=counts.across_node_seen.len();
        let across_node_repeat=counts.across_node_repeat;
        let across_node_missing=counts.across_node_missing;
        let cross_event_full=across_full_repeat.saturating_sub(full_repeat);
        let cross_event_node=across_node_repeat.saturating_sub(node_repeat);
        eprintln!("NUCLEUS_C115_BOUND_OWNER:start={}:events={}:bvar={bvar}:full_unique={full_unique}:full_repeat={full_repeat}:node_unique={node_unique}:node_repeat={node_repeat}:node_missing={node_missing}:across_full_unique={across_full_unique}:across_full_repeat={across_full_repeat}:across_node_unique={across_node_unique}:across_node_repeat={across_node_repeat}:across_node_missing={across_node_missing}:cross_event_full={cross_event_full}:cross_event_node={cross_event_node}:b0={}:b1={}:b2={}:b3={}:b4={}",
            self.start,events.len(),kinds[0],kinds[1],kinds[2],kinds[3],kinds[4]);
        for (idx,e) in events.iter().enumerate() {
            eprintln!("NUCLEUS_C115_BOUND_EVENT:start={}:seq={}:bvar={}:full_unique={}:full_repeat={}:node_unique={}:node_repeat={}:node_missing={}:b0={}:b1={}:b2={}:b3={}:b4={}",
                self.start,idx+1,e.bvar,e.full_unique,e.full_repeat,e.node_unique,
                e.node_repeat,e.node_missing,e.kinds[0],e.kinds[1],e.kinds[2],e.kinds[3],e.kinds[4]);
        }
    }
}
#[cfg(feature="diagnostics")]
impl Drop for C110CaptureReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let counts=self.counts.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || counts.requests<10
            || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        eprintln!(
            "NUCLEUS_C110_CAPTURE_OWNER:start={}:spent={spent}:requests={}:target={}:complete={}:missing={}:unsupported={}:pair_unique={}:pair_repeated={}:repeated_spent={}:a_unique={}:a_repeated={}:b_unique={}:b_repeated={}",
            self.start,counts.requests,counts.target,counts.complete,counts.missing,
            counts.unsupported,counts.pairs.len(),counts.pair_repeated,counts.repeated_spent,
            counts.node_a.len(),counts.a_repeated,counts.node_b.len(),counts.b_repeated,
        );
        let mut sources:HashMap<ExprId,(usize,usize,usize,usize)>=HashMap::new();
        for ((source,_,_,_),group) in &counts.pairs {
            let row=sources.entry(*source).or_default();
            row.0+=group.requests;
            row.1+=1;
            row.2+=group.requests-1;
            row.3+=group.charged;
        }
        let mut groups:Vec<_>=sources.into_iter().collect();
        groups.sort_by_key(|(source,_)|*source);
        for (source,(requests,unique,repeated,charged)) in groups {
            let (a_repeated,b_repeated)=counts.single_repeats.get(&source).copied().unwrap_or_default();
            eprintln!(
                "NUCLEUS_C110_CAPTURE_GROUP:start={}:source={}:requests={requests}:unique={unique}:repeated={repeated}:charged={charged}:a_repeated={a_repeated}:b_repeated={b_repeated}",
                self.start,source.0,
            );
        }
    }
}
#[cfg(feature="diagnostics")]
impl Drop for C109FunctionReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let counts=self.counts.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || counts.requests<10
            || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        eprintln!(
            "NUCLEUS_C109_FUNCTION_OWNER:start={}:spent={spent}:requests={}:target={}:closure={}:free={}:neutral={}:natlit={}:missing={}:chain_steps={}:max_chain={}:chain_capped={}:source_unique={}:source_repeated={}",
            self.start,counts.requests,counts.target,counts.closure,counts.free,
            counts.neutral,counts.natlit,counts.missing,counts.chain_steps,
            counts.max_chain,counts.chain_capped,counts.groups.len(),counts.source_repeated,
        );
        let mut groups:Vec<_>=counts.groups.iter().collect();
        groups.sort_by(|a,b|b.1.requests.cmp(&a.1.requests).then(a.0.cmp(b.0)));
        for ((source,kind),group) in groups.into_iter().take(32) {
            eprintln!(
                "NUCLEUS_C109_FUNCTION_GROUP:start={}:source={}:kind={kind}:requests={}:charged={}",
                self.start,source.0,group.requests,group.associated_charge,
            );
        }
    }
}
#[cfg(feature="diagnostics")]
impl Drop for C106SupportReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let counts=self.counts.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || counts.requests<10
            || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        eprintln!(
            "NUCLEUS_C106_SUPPORT_OWNER:start={}:spent={spent}:requests={}:target={}:complete={}:missing={}:pair_unique={}:pair_repeated={}:node2_unique={}:node2_repeated={}:node4_unique={}:node4_repeated={}:prior_proven={}:prior_unresolved={}:repeated_spent={}",
            self.start,counts.requests,counts.target,counts.complete,counts.missing,
            counts.pairs.len(),counts.pair_repeated,counts.node2.len(),
            counts.node2_repeated,counts.node4.len(),counts.node4_repeated,
            counts.prior_proven,counts.prior_unresolved,counts.repeated_spent,
        );
        let mut groups:Vec<_>=counts.pairs.iter().collect();
        groups.sort_by(|a,b|b.1.charged.cmp(&a.1.charged));
        for ((node2,node4,_levels),group) in groups.into_iter().take(8) {
            eprintln!(
                "NUCLEUS_C106_SUPPORT_GROUP:start={}:node2={node2}:node4={node4}:requests={}:charged={}",
                self.start,group.requests,group.charged,
            );
        }
    }
}
#[cfg(feature="diagnostics")]
impl Drop for C105TerminalReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let counts=self.counts.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || counts.requests<10
            || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        eprintln!(
            "NUCLEUS_C105_TERMINAL_OWNER:start={}:spent={spent}:requests={}:terminal_unique={}:terminal_repeated={}:prior_proven={}:prior_unresolved={}:repeated_spent={}:chain_steps={}:max_chain={}:chain_capped={}",
            self.start,counts.requests,counts.groups.len(),counts.terminal_repeated,
            counts.prior_proven,counts.prior_unresolved,counts.repeated_spent,
            counts.chain_steps,counts.max_chain,counts.chain_capped,
        );
        let mut groups:Vec<_>=counts.groups.iter().collect();
        groups.sort_by(|a,b|b.1.charged.cmp(&a.1.charged));
        for (terminal,group) in groups.into_iter().take(8) {
            eprintln!(
                "NUCLEUS_C105_TERMINAL_GROUP:start={}:expr={}:frame={}:requests={}:charged={}",
                self.start,terminal.expr.0,terminal.env.id(),group.requests,group.charged,
            );
        }
    }
}
#[cfg(feature="diagnostics")]
impl Drop for C104MajorReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let counts=self.counts.borrow();
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || counts.requests<10
            || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        eprintln!(
            "NUCLEUS_C104_MAJOR_OWNER:start={}:spent={spent}:requests={}:unique={}:repeated={}:prior_proven={}:prior_unresolved={}:unresolved={}:nested={}:other_proven={}:repeat_spent={}:unresolved_spent={}:nested_spent={}:other_proven_spent={}",
            self.start,counts.requests,counts.groups.len(),counts.repeated,
            counts.prior_proven,counts.prior_unresolved,counts.unresolved,
            counts.nested,counts.other_proven,counts.repeat_spent,
            counts.unresolved_spent,counts.nested_spent,counts.other_proven_spent,
        );
        let mut groups:Vec<_>=counts.groups.iter().collect();
        groups.sort_by(|a,b|b.1.charged.cmp(&a.1.charged));
        for (major,group) in groups.into_iter().take(8) {
            eprintln!(
                "NUCLEUS_C104_MAJOR_GROUP:start={}:expr={}:frame={}:requests={}:charged={}:unresolved={}:nested={}:other_proven={}",
                self.start,major.expr.0,major.env.id(),group.requests,group.charged,
                group.unresolved,group.nested,group.other_proven,
            );
        }
    }
}
#[cfg(feature="diagnostics")]
struct C94PhaseReceipt<'a> {
    counts: &'a C94PhaseCounts, fuel: &'a Cell<Option<usize>>,
    start: usize, key_start: usize, head: &'a NeutralHead,
}
#[cfg(feature="diagnostics")]
impl Drop for C94PhaseReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED: AtomicUsize = AtomicUsize::new(0);
        // Restrict receipts to consequential owner calls, not tiny speculative
        // side probes. No decision depends on this output filter.
        if self.start < 8192 || self.counts.entered.get() == 0
            || PRINTED.fetch_add(1,Ordering::Relaxed) >= 32 { return; }
        let remaining = self.fuel.get().unwrap_or(0);
        let key_work=REPLAY_KEY_WORK.load(Ordering::Relaxed).saturating_sub(self.key_start);
        eprintln!(
            "NUCLEUS_C94_PHASE:head={:?}:start={}:remaining={remaining}:key_work={key_work}:entered={}:resumed={}:completed={}:local_hits={}:global_hits={}:max_depth={}:bvar_majors={}:bvar_repeats={}:last_head={}:last_major_expr={}:last_major_frame={}",
            self.head, self.start, self.counts.entered.get(),
            self.counts.resumed.get(), self.counts.completed.get(),
            self.counts.local_hits.get(), self.counts.global_hits.get(),
            self.counts.max_depth.get(),
            self.counts.bvar_majors.get(), self.counts.bvar_repeats.get(),
            self.counts.last_head.get(),
            self.counts.last_major_expr.get(), self.counts.last_major_frame.get(),
        );
    }
}

// C95 counts charges while they are still owned by the original caller.
// Categories are disjoint for one worklist's instrumentation; key_work is
// separately reported as an inclusive counter and may overlap a stage when
// that stage recursively enters a different qualified recursor owner.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C95StageCounts {
    major: Cell<usize>, telescope: Cell<usize>, rhs: Cell<usize>, finish: Cell<usize>,
}
#[cfg(feature="diagnostics")]
struct C95StageCharge<'a> {
    fuel: &'a Cell<Option<usize>>, counter: &'a Cell<usize>, start: usize,
}
#[cfg(feature="diagnostics")]
impl<'a> C95StageCharge<'a> {
    fn new(fuel:&'a Cell<Option<usize>>,counter:&'a Cell<usize>)->Self {
        Self { fuel,counter,start:fuel.get().unwrap_or(0) }
    }
}
#[cfg(feature="diagnostics")]
impl Drop for C95StageCharge<'_> {
    fn drop(&mut self) {
        let charge=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        self.counter.set(self.counter.get().saturating_add(charge));
    }
}
#[cfg(feature="diagnostics")]
struct C95StageReceipt<'a> {
    counts:&'a C95StageCounts, fuel:&'a Cell<Option<usize>>,
    start:usize, key_start:usize, head:&'a NeutralHead,
}
#[cfg(feature="diagnostics")]
impl Drop for C95StageReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED: AtomicUsize=AtomicUsize::new(0);
        let remaining=self.fuel.get().unwrap_or(0);
        let spent=self.start.saturating_sub(remaining);
        if spent<8192 || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        let major_work=self.counts.major.get();
        let telescope_work=self.counts.telescope.get();
        let rhs_work=self.counts.rhs.get();
        let finish_work=self.counts.finish.get();
        let assigned=major_work.saturating_add(telescope_work)
            .saturating_add(rhs_work).saturating_add(finish_work);
        // If the assigned work exceeds spent, the Python conservation test
        // rejects the observer: overlapping charge scopes are not evidence.
        let other_work=spent.saturating_sub(assigned);
        let key_work=REPLAY_KEY_WORK.load(Ordering::Relaxed).saturating_sub(self.key_start);
        eprintln!("NUCLEUS_C95_PHASE:head={:?}:start={}:remaining={remaining}:major_work={major_work}:telescope_work={telescope_work}:rhs_work={rhs_work}:finish_work={finish_work}:other_work={other_work}:key_work={key_work}",self.head,self.start);
    }
}

// Source-capture histogram: an ExprId is a label for diagnosis, not an
// equivalence proof. Distinct EnvFrames are never merged by this observer.
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C96MajorGroup {
    count:usize,charged:usize,unknown:usize,nested:usize,
    chain_steps:usize,chain_max:usize,chain_capped:usize,
}
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C96MajorCounts {
    demands:Cell<usize>, charged:Cell<usize>,
    groups:RefCell<HashMap<(u64,u64,u64),C96MajorGroup>>,
}
#[cfg(feature="diagnostics")]
impl C96MajorCounts {
    fn record(&self,key:(u64,u64,u64),work:usize,unknown:bool,nested:bool,chain_steps:usize) {
        self.demands.set(self.demands.get()+1);
        self.charged.set(self.charged.get().saturating_add(work));
        let mut groups=self.groups.borrow_mut();
        let group=groups.entry(key).or_default();
        group.count+=1;group.charged=group.charged.saturating_add(work);
        group.unknown+=usize::from(unknown);group.nested+=usize::from(nested);
        group.chain_steps=group.chain_steps.saturating_add(chain_steps);
        group.chain_max=group.chain_max.max(chain_steps);
        group.chain_capped+=usize::from(chain_steps==4096);
    }
}
#[cfg(feature="diagnostics")]
struct C96MajorReceipt<'a> {
    counts:&'a C96MajorCounts,fuel:&'a Cell<Option<usize>>,
    start:usize,
}
#[cfg(feature="diagnostics")]
impl Drop for C96MajorReceipt<'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let spent=self.start.saturating_sub(self.fuel.get().unwrap_or(0));
        if spent<8192 || self.counts.demands.get()<10
            || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        let major_work=self.counts.charged.get();
        eprintln!("NUCLEUS_C96_OWNER:start={}:spent={spent}:major_work={major_work}:demands={}",self.start,self.counts.demands.get());
        let mut groups:Vec<_>=self.counts.groups.borrow().iter()
            .map(|(key,value)|(*key,value.count,value.charged,value.unknown,value.nested,
                value.chain_steps,value.chain_max,value.chain_capped)).collect();
        groups.sort_by(|a,b|b.2.cmp(&a.2));
        for ((recursor,kind,bound_expr),count,charged,unknown,nested,chain_steps,chain_max,chain_capped) in groups.into_iter().take(16) {
            eprintln!("NUCLEUS_C96_MAJOR:start={}:recursor={recursor}:kind={kind}:bound_expr={bound_expr}:count={count}:charged={charged}:unknown={unknown}:nested={nested}:chain_steps={chain_steps}:chain_max={chain_max}:chain_capped={chain_capped}",self.start);
        }
    }
}

// C97: read-only census of the *loop iterations* paid for while exposing
// actual source majors. An expression ID and frame ID describe the precise
// source closure; neither implies equivalence with another closure.
#[cfg(feature="diagnostics")]
#[derive(Default,Clone)]
struct C97Steps {
    major_work:usize,
    loops:usize,
    unique_head_pending:usize,
    repeat_head_pending:usize,
    kinds:HashMap<u8,usize>,
    heads:HashMap<(u8,u64),usize>,
    repeated_heads:HashMap<(u8,u64),usize>,
    node_env:HashMap<(u64,u64),usize>,
}
#[cfg(feature="diagnostics")]
struct C97MajorActivity<'a> {active:&'a Cell<usize>}
#[cfg(feature="diagnostics")]
impl Drop for C97MajorActivity<'_> {
    fn drop(&mut self) {self.active.set(self.active.get().saturating_sub(1));}
}
#[cfg(feature="diagnostics")]
struct C115MajorActivity<'a> {active:&'a Cell<usize>}
#[cfg(feature="diagnostics")]
impl Drop for C115MajorActivity<'_> {
    fn drop(&mut self) {self.active.set(self.active.get().saturating_sub(1));}
}
#[cfg(feature="diagnostics")]
struct C97Receipt<'m,'a> {
    machine:&'m Machine<'a>,start:usize,baseline:C97Steps,
}
#[cfg(feature="diagnostics")]
impl Drop for C97Receipt<'_,'_> {
    fn drop(&mut self) {
        use std::sync::atomic::{AtomicUsize,Ordering};
        static PRINTED:AtomicUsize=AtomicUsize::new(0);
        let current=self.machine.c97_steps.borrow();
        let spent=self.start.saturating_sub(self.machine.exposure_fuel.get().unwrap_or(0));
        let loops=current.loops.saturating_sub(self.baseline.loops);
        if spent<8192 || loops==0 || PRINTED.fetch_add(1,Ordering::Relaxed)>=32 {return;}
        let major_work=current.major_work.saturating_sub(self.baseline.major_work);
        let unique_head_pending=current.unique_head_pending.saturating_sub(self.baseline.unique_head_pending);
        let repeat_head_pending=current.repeat_head_pending.saturating_sub(self.baseline.repeat_head_pending);
        let node_env:Vec<_>=current.node_env.iter().filter_map(|(key,count)|{
            let delta=count.saturating_sub(*self.baseline.node_env.get(key).unwrap_or(&0));
            (delta>0).then_some(delta)
        }).collect();
        let repeat_node_env=node_env.iter().map(|count|count.saturating_sub(1)).sum::<usize>();
        // This projection intentionally omits pending arguments, universe
        // substitutions and reduction mode: it is *not* a sound cache key.
        eprintln!("NUCLEUS_C97_OWNER:start={}:spent={spent}:major_work={major_work}:loops={loops}:unique_node_env={}:repeat_node_env={repeat_node_env}:unique_head_pending={unique_head_pending}:repeat_head_pending={repeat_head_pending}",self.start,node_env.len());
        let mut kinds:Vec<_>=current.kinds.iter().filter_map(|(kind,count)|{
            let delta=count.saturating_sub(*self.baseline.kinds.get(kind).unwrap_or(&0));
            (delta>0).then_some((*kind,delta))
        }).collect();
        kinds.sort_by_key(|(kind,_)|*kind);
        for (kind,count) in kinds {
            eprintln!("NUCLEUS_C97_KIND:start={}:kind={kind}:count={count}",self.start);
        }
        let mut heads:Vec<_>=current.heads.iter().filter_map(|(key,count)|{
            let delta=count.saturating_sub(*self.baseline.heads.get(key).unwrap_or(&0));
            (delta>0).then_some((*key,delta))
        }).collect();
        heads.sort_by(|a,b|b.1.cmp(&a.1).then(a.0.cmp(&b.0)));
        for ((kind,source),count) in heads.into_iter().take(20) {
            eprintln!("NUCLEUS_C97_HEAD:start={}:kind={kind}:source={source}:count={count}",self.start);
        }
        // C108: the source ExprId(7219) carries a Nat.le.refl proof argument.
        // A syntactic proof occurrence does not establish that the actual
        // recursor-major evaluator forces it. Reuse C97's *already measured*
        // immutable-source histogram to record demand, without touching the
        // evaluator, work owner, captured binding or diagnostic counts.
        if std::env::var_os("NUCLEUS_C108_PROOF_ARGUMENT_DEMAND_TRACE").is_some() {
            let demand=|kind:u8,source:u64|current.heads.get(&(kind,source))
                .copied().unwrap_or(0).saturating_sub(
                    self.baseline.heads.get(&(kind,source)).copied().unwrap_or(0));
            eprintln!(
                "NUCLEUS_C108_PROOF_ARGUMENT_OWNER:start={}:spent={spent}:root={}:proof_app={}:succ_app={}:le_refl={}:nat_succ={}",
                self.start,demand(1,7219),demand(1,6509),demand(1,1585),
                demand(4,76),demand(4,64),
            );
        }
        let mut repeated:Vec<_>=current.repeated_heads.iter().filter_map(|(key,count)|{
            let delta=count.saturating_sub(*self.baseline.repeated_heads.get(key).unwrap_or(&0));
            (delta>0).then_some((*key,delta))
        }).collect();
        repeated.sort_by(|a,b|b.1.cmp(&a.1).then(a.0.cmp(&b.0)));
        for ((kind,source),count) in repeated.into_iter().take(20) {
            eprintln!("NUCLEUS_C97_REPEAT_HEAD:start={}:kind={kind}:source={source}:count={count}",self.start);
        }
    }
}

#[derive(Clone,Copy,Eq,PartialEq)]
enum CheckedReplayGoal { Completed, OneStep }

struct NeutralProjectionDepthScope<'a> { depth: &'a Cell<usize> }
impl Drop for NeutralProjectionDepthScope<'_> { fn drop(&mut self) {self.depth.set(self.depth.get().saturating_sub(1));} }

struct ConstructorFuelScope<'a> { fuel: &'a Cell<Option<usize>> }
impl Drop for ConstructorFuelScope<'_> { fn drop(&mut self) { self.fuel.set(None); } }

struct ExposureFuelScope<'a> { fuel: &'a Cell<Option<usize>>, depth: &'a Cell<usize>, owner: bool }
impl Drop for ExposureFuelScope<'_> {
    fn drop(&mut self) { self.depth.set(self.depth.get().saturating_sub(1)); if self.owner { self.fuel.set(None); } }
}

#[cfg(feature="diagnostics")]
#[derive(Default)]
struct C153NestedCounts {
    calls:usize, proven:usize, unknown:usize,
    leaf_calls:usize, leaf_proven:usize, leaf_potentially_cacheable:usize,
    leaf_head_work:usize, max_leaf_head_work:usize,
    // C154: nonleaf intervals overlap their descendants; do not sum them.
    nonleaf_calls:usize, nonleaf_proven:usize, nonleaf_max_head_work:usize,
    nonleaf_ge_64:usize, nonleaf_ge_1024:usize, nonleaf_ge_65536:usize,
    already_cached_hits:usize,
}

pub struct Machine<'a> {
    authority: AuthorityId,
    demand_major: bool,
    replay_projection_major: bool,
    replay_neutral_projection: bool,
    neutral_projection_depth: Cell<usize>,
    exposure_fuel: Cell<Option<usize>>,
    exposure_depth: Cell<usize>,
    #[cfg(feature="diagnostics")]
    c152_head_active:Cell<usize>,
    #[cfg(feature="diagnostics")]
    c152_head_kinds:RefCell<[usize;8]>,
    #[cfg(feature="diagnostics")]
    c153_producer_active:Cell<usize>,
    #[cfg(feature="diagnostics")]
    c153_entry_serial:Cell<usize>,
    #[cfg(feature="diagnostics")]
    c153_nested:RefCell<C153NestedCounts>,
    #[cfg(feature="diagnostics")]
    c97_major_active:Cell<usize>,
    #[cfg(feature="diagnostics")]
    c97_steps:RefCell<C97Steps>,
    #[cfg(feature="diagnostics")]
    c97_head_pending_seen:RefCell<HashSet<(Closure,Vec<Closure>,Transparency,bool)>>,
    #[cfg(feature="diagnostics")]
    c115_major_active:Cell<usize>,
    #[cfg(feature="diagnostics")]
    c115_bvar_steps:RefCell<Vec<C115BVarStep>>,
    #[cfg(feature="diagnostics")]
    c116_context_enabled:bool,
    #[cfg(feature="diagnostics")]
    c117_completed_entry_enabled:bool,
    #[cfg(feature="diagnostics")]
    c117_completed_calls:RefCell<Vec<C117CompletedCall>>,
    #[cfg(feature="diagnostics")]
    c118_interior_tail_enabled:bool,
    #[cfg(feature="diagnostics")]
    c118_current_invocation:Cell<Option<usize>>,
    #[cfg(feature="diagnostics")]
    c118_next_invocation:Cell<usize>,
    #[cfg(feature="diagnostics")]
    c119_dynamic_context_enabled:bool,
    #[cfg(feature="diagnostics")]
    c120_repeated_span_enabled:bool,
    #[cfg(test)]
    replay_key_builds: Cell<usize>,
    exposure_cache: Option<ExposureCache>,
    expressions: &'a IdTable<ExprId, Expr>,
    levels: &'a IdTable<LevelId, Level>,
    definitions: Rc<HashMap<NameId, DefinitionBody>>,
    singleton_recursor_reductions: Rc<HashSet<NameId>>,
    nullary_minor_reductions: Rc<HashMap<NameId, Vec<NullaryMinorReduction>>>,
    closed_nested_minor_reductions: Rc<HashMap<NameId,Vec<ClosedNestedMinorReduction>>>,
    recursor_reductions: Rc<HashMap<NameId, RecursorReduction>>,
    projection_specs: Rc<HashMap<NameId, ProjectionSpec>>,
    nat_primitives: Option<NatPrimitives>,
    bool_primitives: Option<BoolPrimitives>,
    quot_primitives: Option<QuotPrimitives>,
}

impl<'a> Machine<'a> {
    pub fn new(
        authority: AuthorityId,
        expressions: &'a IdTable<ExprId, Expr>,
        levels: &'a IdTable<LevelId, Level>,
        definitions: impl Into<Rc<HashMap<NameId, DefinitionBody>>>,
    ) -> Self {
        Self {
            authority,
            demand_major: std::env::var_os("NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR").is_some(),
            replay_projection_major: std::env::var_os("NUCLEUS_EXPERIMENTAL_REPLAY_PROJECTION_MAJOR").is_some(),
            replay_neutral_projection: std::env::var_os("NUCLEUS_EXPERIMENTAL_REPLAY_NEUTRAL_PROJECTION").is_some(),
            neutral_projection_depth: Cell::new(0),
            exposure_fuel: Cell::new(None),
            exposure_depth: Cell::new(0),
            #[cfg(feature="diagnostics")]
            c152_head_active:Cell::new(0),
            #[cfg(feature="diagnostics")]
            c152_head_kinds:RefCell::new([0;8]),
            #[cfg(feature="diagnostics")]
            c153_producer_active:Cell::new(0),
            #[cfg(feature="diagnostics")]
            c153_entry_serial:Cell::new(0),
            #[cfg(feature="diagnostics")]
            c153_nested:RefCell::new(C153NestedCounts::default()),
            #[cfg(feature="diagnostics")]
            c97_major_active:Cell::new(0),
            #[cfg(feature="diagnostics")]
            c97_steps:RefCell::new(C97Steps::default()),
            #[cfg(feature="diagnostics")]
            c97_head_pending_seen:RefCell::new(HashSet::new()),
            #[cfg(feature="diagnostics")]
            c115_major_active:Cell::new(0),
            #[cfg(feature="diagnostics")]
            c115_bvar_steps:RefCell::new(Vec::new()),
            #[cfg(feature="diagnostics")]
            c116_context_enabled:std::env::var_os("NUCLEUS_C116_BVAR_CONTEXT_TRACE").is_some()
                || std::env::var_os("NUCLEUS_C118_INTERIOR_TAIL_TRACE").is_some()
                || std::env::var_os("NUCLEUS_C119_DYNAMIC_CONTEXT_TRACE").is_some()
                || std::env::var_os("NUCLEUS_C120_REPEATED_SPAN_TRACE").is_some(),
            #[cfg(feature="diagnostics")]
            c117_completed_entry_enabled:std::env::var_os("NUCLEUS_C117_COMPLETED_ENTRY_TRACE").is_some(),
            #[cfg(feature="diagnostics")]
            c117_completed_calls:RefCell::new(Vec::new()),
            #[cfg(feature="diagnostics")]
            c118_interior_tail_enabled:std::env::var_os("NUCLEUS_C118_INTERIOR_TAIL_TRACE").is_some()
                || std::env::var_os("NUCLEUS_C120_REPEATED_SPAN_TRACE").is_some(),
            #[cfg(feature="diagnostics")]
            c118_current_invocation:Cell::new(None),
            #[cfg(feature="diagnostics")]
            c118_next_invocation:Cell::new(0),
            #[cfg(feature="diagnostics")]
            c119_dynamic_context_enabled:std::env::var_os("NUCLEUS_C119_DYNAMIC_CONTEXT_TRACE").is_some(),
            #[cfg(feature="diagnostics")]
            c120_repeated_span_enabled:std::env::var_os("NUCLEUS_C120_REPEATED_SPAN_TRACE").is_some(),
            #[cfg(test)]
            replay_key_builds: Cell::new(0),
            exposure_cache: None,
            expressions,
            levels,
            definitions: definitions.into(),
            singleton_recursor_reductions: Rc::new(HashSet::new()),
            nullary_minor_reductions: Rc::new(HashMap::new()),
            closed_nested_minor_reductions: Rc::new(HashMap::new()),
            recursor_reductions: Rc::new(HashMap::new()),
            projection_specs: Rc::new(HashMap::new()),
            nat_primitives: None,
            bool_primitives: None,
            quot_primitives: None,
        }
    }

    pub fn with_singleton_recursor_reductions(mut self, reductions: impl Into<Rc<HashSet<NameId>>>) -> Self {
        self.singleton_recursor_reductions = reductions.into();
        self
    }

    pub fn with_nullary_minor_reductions(mut self, reductions:impl Into<Rc<HashMap<NameId,Vec<NullaryMinorReduction>>>>)->Self {
        self.nullary_minor_reductions=reductions.into();
        self
    }

    pub fn with_closed_nested_minor_reductions(mut self,reductions:impl Into<Rc<HashMap<NameId,Vec<ClosedNestedMinorReduction>>>>)->Self {
        self.closed_nested_minor_reductions=reductions.into();
        self
    }

    pub fn with_recursor_reductions(
        mut self,
        reductions: impl Into<Rc<HashMap<NameId, RecursorReduction>>>,
    ) -> Self {
        self.recursor_reductions = reductions.into();
        self
    }

    pub fn with_projection_specs(mut self, specs: impl Into<Rc<HashMap<NameId, ProjectionSpec>>>) -> Self {
        self.projection_specs = specs.into();
        self
    }

    /// Share positive exposure evidence over one type-checker judgment.
    /// Unresolved / cyclic evaluations are intentionally never cached.
    pub(crate) fn with_exposure_cache(mut self, cache: ExposureCache) -> Self {
        self.exposure_cache = Some(cache);
        self
    }

    pub fn with_nat_primitives(mut self, primitives: Option<NatPrimitives>) -> Self {
        self.nat_primitives = primitives;
        self
    }

    pub fn with_bool_primitives(mut self, primitives: Option<BoolPrimitives>) -> Self {
        self.bool_primitives = primitives;
        self
    }

    pub fn with_quot_primitives(mut self, primitives: Option<QuotPrimitives>) -> Self {
        self.quot_primitives = primitives;
        self
    }

    pub fn expose(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
    ) -> Judgment<Value> {
        self.expose_internal(closure, transparency, budget, false, false)
            .map(|exposure| exposure.value)
    }

    // Both inputs come from qualified Nat constructors and a source-checked
    // Nat local. Evaluate the actual RHS; no expected result selects iota.
    pub(crate) fn source_predecessor_equations(&self,zero_body:Closure,succ_body:Closure,
        free:FreeId,budget:usize)->bool {
        if self.nat_primitives.as_ref().is_none_or(|nat|nat.pred.is_some()) {return false;}
        let Some(nat)=self.nat_primitives.as_ref() else{return false;};
        let _owner=if self.exposure_fuel.get().is_none(){
            self.exposure_fuel.set(Some(budget));Some(ConstructorFuelScope{fuel:&self.exposure_fuel})
        }else{None};
        let zero=self.expose(zero_body,Transparency::Full,budget);
        let zero_matches=matches!(zero.proven_value(),Some(Value::NatLit(n)) if n.is_zero())
            ||matches!(zero.proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Const{name,levels},spine})) if *name==nat.zero&&levels.is_empty()&&spine.is_empty());
        if !zero_matches{
            #[cfg(feature="diagnostics")] if std::env::var_os("NUCLEUS_TRACE_PRED_SOURCE").is_some(){eprintln!("NUCLEUS_PRED_SOURCE_DECLINE:actual-zero:{zero:?}:fuel={:?}",self.exposure_fuel.get());}
            return false;
        }
        let succ=self.expose(succ_body,Transparency::Full,self.exposure_fuel.get().unwrap_or(0));
        #[cfg(feature="diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_PRED_SOURCE").is_some(){eprintln!("NUCLEUS_PRED_SOURCE_EQUATIONS:zero={zero:?}:succ={succ:?}:fuel={:?}",self.exposure_fuel.get());}
        matches!(succ.proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Free(actual),spine})) if *actual==free&&spine.is_empty())
    }

    pub fn expose_for_conversion(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
    ) -> Judgment<Value> {
        self.expose_internal(closure, transparency, budget, false, true)
            .map(|exposure| exposure.value)
    }

    /// Unfold exactly the definition at an application's head, then resume
    /// cheap conversion exposure with the original application spine.
    pub(crate) fn expose_head_delta_for_conversion(
        &self,
        mut closure: Closure,
        mut budget: usize,
    ) -> Option<Judgment<Value>> {
        let mut pending = Vec::new();
        let mut visited = VisitSet::new();
        loop {
            if budget == 0 || !visited.insert((self.authority, closure.expr, closure.env.id())) {
                return Some(Judgment::unknown("head-delta-exposure"));
            }
            budget -= 1;
            match self.expressions.get(closure.expr)? {
                Expr::BVar(index) => match closure.env.lookup(*index)? {
                    EnvBinding::Closure(bound) => closure = bound,
                    EnvBinding::Free(_) | EnvBinding::Neutral(_) | EnvBinding::NatLit(_) => return None,
                },
                Expr::Let { value, body, .. } => {
                    let value = closure.sibling(*value, closure.env.clone());
                    closure = closure.sibling(*body, self.bind_captured_argument(&closure,value));
                }
                Expr::App { fun, arg } => {
                    pending.push(closure.sibling(*arg, closure.env.clone()));
                    closure = closure.sibling(*fun, closure.env.clone());
                }
                Expr::Const { name, levels } => {
                    let definition = self.definitions.get(name)?;
                    if definition.level_params.len() != levels.len() {
                        return Some(Judgment::unknown("head-delta-level-arity"));
                    }
                    let mut substitution = Vec::with_capacity(levels.len());
                    for (parameter, level) in definition.level_params.iter().zip(levels) {
                        let Some(level) = self.resolve_level(*level, &closure, budget) else {
                            return Some(Judgment::unknown("head-delta-level-instantiation"));
                        };
                        substitution.push((*parameter, level));
                    }
                    let body = Closure::with_levels(
                        definition.value,
                        EnvFrame::empty(),
                        LevelSubstitution::new(substitution),
                    );
                    return Some(
                        self.expose_internal_with_pending(
                            body,
                            Transparency::Reducible,
                            budget,
                            false,
                            true,
                            pending,
                        )
                        .map(|exposure| exposure.value),
                    );
                }
                _ => return None,
            }
        }
    }

    pub fn expose_with_witnesses(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
    ) -> Judgment<Exposure> {
        self.expose_internal(closure, transparency, budget, true, false)
    }

    pub(crate) fn projection_field_for_conversion(
        &self,
        structure: Closure,
        type_name: NameId,
        index: usize,
        budget: usize,
    ) -> Judgment<Closure> {
        let Some(spec) = self.projection_specs.get(&type_name) else {
            return Judgment::unknown("unsupported-projection");
        };
        if index >= spec.field_types.len() {
            return Judgment::unknown("projection-index-out-of-range");
        }
        let exposed = self.expose_internal(
            structure.clone(),
            Transparency::Full,
            budget,
            false,
            false,
        );
        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_PROJECTION_FIELD_FAILURE").is_some() {
            static COUNT: std::sync::atomic::AtomicUsize =
                std::sync::atomic::AtomicUsize::new(0);
            if COUNT.fetch_add(1, std::sync::atomic::Ordering::Relaxed) < 96 {
                eprintln!(
                    "NUCLEUS_PROJECTION_FIELD_PROBE:type={type_name:?}:index={index}:constructor={:?}:structure={structure:?}:full_exposure={exposed:?}",
                    spec.constructor,
                );
            }
        }
        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_CERTIFIED_ARITHMETIC_FIELD").is_some() {
            use std::sync::atomic::{AtomicUsize,Ordering};
            static COUNT:AtomicUsize=AtomicUsize::new(0);
            if COUNT.fetch_add(1,Ordering::Relaxed)<48 {
                eprintln!(
                    "NUCLEUS_CERTIFIED_FIELD:type={type_name:?}:index={index}:structure={structure:?}:constructor={:?}:params={}:exposure={}",
                    spec.constructor,spec.num_params,
                    format!("{exposed:?}").chars().take(1600).collect::<String>(),
                );
            }
        }
        let replayed = if let Some(Value::Neutral(neutral)) = exposed.proven_value().map(|value| &value.value)
            && matches!(&neutral.head, NeutralHead::Const { name, .. }
                if *name != spec.constructor && self.recursor_reductions.contains_key(name))
        {
            self.qualified_nested_recursor_result(neutral, budget)
        } else {
            Judgment::unknown("projection-no-registered-replay")
        };
        let actual = replayed.proven_value().or_else(|| exposed.proven_value().map(|value| &value.value));
        let Some(Value::Neutral(neutral)) = actual else {
            return Judgment::unknown("projection-structure-stuck");
        };
        let NeutralHead::Const { name, .. } = neutral.head else {
            return Judgment::unknown("projection-structure-neutral");
        };
        if name != spec.constructor {
            return Judgment::unknown("projection-constructor-mismatch");
        }
        let field_offset = spec.num_params + index;
        let Some(field) = neutral.spine.get(field_offset).cloned() else {
            return Judgment::unknown("projection-constructor-arity");
        };
        #[cfg(feature="diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_SELECTED_FIELD").is_some() {
            use std::sync::atomic::{AtomicUsize,Ordering};
            static COUNT:AtomicUsize=AtomicUsize::new(0);
            if COUNT.fetch_add(1,Ordering::Relaxed)<64 {
                let value=self.expose_internal(
                    field.clone(),Transparency::Reducible,budget.min(512),false,false,
                );
                eprintln!(
                    "NUCLEUS_SELECTED_FIELD:type={type_name:?}:index={index}:constructor={:?}:selected={field:?}:value={}",
                    spec.constructor,format!("{value:?}").chars().take(1300).collect::<String>(),
                );
            }
        }
        Judgment::proven(field, "projection-selected-field")
    }

    pub(crate) fn projection_value_for_conversion(
        &self,
        structure: Closure,
        type_name: NameId,
        index: usize,
        spine: &[Closure],
        budget: usize,
    ) -> Judgment<Value> {
        let field = self.projection_field_for_conversion(structure.clone(), type_name, index, budget);
        let Some(field) = field.proven_value() else {
            let Some(spec) = self.projection_specs.get(&type_name) else {
                return Judgment::unknown("unsupported-projection");
            };
            if index >= spec.field_types.len() {
                return Judgment::unknown("projection-index-out-of-range");
            }
            // Full source delta/iota can stop at a legitimate neutral
            // recursor or opaque constant. Retain the projection itself;
            // do not select or synthesize a constructor field.
            let receiver = self.expose(structure, Transparency::Full, budget.saturating_sub(1));
            if let Some(Value::Neutral(neutral)) = receiver.proven_value()
                && !matches!(&neutral.head, NeutralHead::Const { name, .. } if *name == spec.constructor)
            {
                return Judgment::proven(Value::Neutral(Neutral {
                    head: NeutralHead::Projection {
                        type_name, index, structure: Box::new(neutral.clone()),
                    },
                    spine: spine.to_vec(),
                }), "source-reduced-neutral-projection");
            }
            return Judgment::unknown("lazy-projection-field-exposure");
        };
        // Do not eagerly normalize a fully applied projection field through
        // every recursive definition. A proven preferred reduction is enough
        // to establish a legitimate rigid comparison; Full is the fallback
        // only if this bounded first stage cannot produce any certified value.
        let pending: Vec<Closure> = spine.iter().rev().cloned().collect();
        let cheap = self.expose_internal_with_pending(
            field.clone(), Transparency::Reducible,
            budget.saturating_sub(1), false, true, pending.clone(),
        ).map(|exposure| exposure.value);
        if cheap.is_proven() {
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_PROJECTION_CHEAP").is_some() {
                eprintln!("NUCLEUS_PROJECTION_CHEAP:field={:?}:type={type_name:?}:index={index}", field.expr);
            }
            return cheap;
        }
        self.expose_internal_with_pending(
            field.clone(), Transparency::Full,
            budget.saturating_sub(1), false, true, pending,
        ).map(|exposure| exposure.value)
    }

    fn expose_internal(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
        record_witnesses: bool,
        preserve_stuck_projection: bool,
    ) -> Judgment<Exposure> {
        self.expose_internal_with_pending(
            closure,
            transparency,
            budget,
            record_witnesses,
            preserve_stuck_projection,
            Vec::new(),
        )
    }

    /// Memoize exact successful normal forms across exposure calls that
    /// share an environment/authority. Never treat a cached UNKNOWN as proof.
    fn expose_internal_with_pending(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
        record_witnesses: bool,
        preserve_stuck_projection: bool,
        pending: Vec<Closure>,
    ) -> Judgment<Exposure> {
        // C153 records *completed invocation intervals*, not matching head
        // revisits. Leaf intervals are disjoint, so their work is not counted
        // twice. This is an observer; it does not change or populate caches.
        #[cfg(feature="diagnostics")]
        let c153_entry=if self.c153_producer_active.get()>0 {
            let serial=self.c153_entry_serial.get()+1;
            self.c153_entry_serial.set(serial);
            let heads=self.c152_head_kinds.borrow().iter().sum::<usize>();
            Some((serial,heads))
        } else {None};
        #[cfg(feature="diagnostics")]
        let c117_call=(self.c117_completed_entry_enabled && self.c115_major_active.get()!=0)
            .then(||{
                let state=(closure.clone(),pending.clone(),transparency,preserve_stuck_projection);
                let cached=!record_witnesses && budget>0
                    && self.exposure_fuel.get()!=Some(0)
                    && (self.exposure_fuel.get().is_none() || self.exposure_depth.get()<64)
                    && self.exposure_cache.as_ref().is_some_and(|cache|
                        cache.borrow().values.contains_key(&Rc::new(CachedExposureKey::new((
                            self.authority,closure.clone(),transparency,
                            preserve_stuck_projection,pending.clone(),
                        )))));
                let entry_bvar=matches!(self.expressions.get(closure.expr),Some(Expr::BVar(_)));
                (state,cached,entry_bvar)
            });
        let result=self.expose_internal_with_pending_impl(
            closure,transparency,budget,record_witnesses,preserve_stuck_projection,pending);
        #[cfg(feature="diagnostics")]
        if let Some((serial,before))=c153_entry {
            let leaf=self.c153_entry_serial.get()==serial;
            let after=self.c152_head_kinds.borrow().iter().sum::<usize>();
            let eligible=!record_witnesses && result.proven_value().is_some_and(|e|{
                !(self.demand_major && matches!(&e.value,
                    Value::Neutral(Neutral{head:NeutralHead::Const{name,..},..})
                    if self.recursor_reductions.contains_key(name))
                    && !self.recursor_has_immutable_local_major(&e.value))
            });
            let mut counts=self.c153_nested.borrow_mut();
            counts.calls+=1;
            counts.proven+=usize::from(result.is_proven());
            counts.unknown+=usize::from(result.is_unknown());
            if leaf {
                let work=after.saturating_sub(before);
                counts.leaf_calls+=1;
                counts.leaf_proven+=usize::from(result.is_proven());
                counts.leaf_potentially_cacheable+=usize::from(eligible);
                counts.leaf_head_work+=work;
                counts.max_leaf_head_work=counts.max_leaf_head_work.max(work);
            } else {
                let work=after.saturating_sub(before);
                counts.nonleaf_calls+=1;
                counts.nonleaf_proven+=usize::from(result.is_proven());
                counts.nonleaf_max_head_work=counts.nonleaf_max_head_work.max(work);
                counts.nonleaf_ge_64+=usize::from(work>=64);
                counts.nonleaf_ge_1024+=usize::from(work>=1024);
                counts.nonleaf_ge_65536+=usize::from(work>=65536);
            }
        }
        #[cfg(feature="diagnostics")]
        if let Some((state,cached,entry_bvar))=c117_call {
            let eligible=if record_witnesses {None} else {
                result.proven_value().and_then(|exposure|{
                    let value=&exposure.value;
                    let unresolved=self.demand_major && matches!(value,
                        Value::Neutral(Neutral{head:NeutralHead::Const{name,..},..})
                            if self.recursor_reductions.contains_key(name))
                        && !self.recursor_has_immutable_local_major(value);
                    (!unresolved).then(||value.clone())
                })
            };
            self.c117_completed_calls.borrow_mut().push(C117CompletedCall{
                state,eligible,unknown:result.is_unknown(),refuted:result.is_refuted(),
                cached,entry_bvar,
            });
        }
        result
    }

    fn expose_internal_with_pending_impl(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
        record_witnesses: bool,
        preserve_stuck_projection: bool,
        pending: Vec<Closure>,
    ) -> Judgment<Exposure> {
        if self.exposure_fuel.get().is_some() && self.exposure_depth.get() >= 64 { return Judgment::unknown("constructor-demand-depth-exhausted"); }
        self.exposure_depth.set(self.exposure_depth.get() + 1);
        let _fuel_scope = ExposureFuelScope { fuel: &self.exposure_fuel, depth: &self.exposure_depth, owner: false };
        if budget == 0 || self.exposure_fuel.get() == Some(0) {
            return Judgment::unknown("reduction-budget-exhausted");
        }
        let Some(cache) = self.exposure_cache.as_ref().filter(|_| !record_witnesses) else {
            return self.expose_uncached_internal_with_pending(
                closure, transparency, budget, record_witnesses,
                preserve_stuck_projection, pending,
            );
        };
        let key = Rc::new(CachedExposureKey::new((
            self.authority, closure.clone(), transparency,
            preserve_stuck_projection, pending.clone(),
        )));
        // C151: recovered *C125b* source-only cache-provenance witness.
        // Observe the same frozen N7 closure as C141's surrogate probe, but
        // do not transfer its results or change any cache/budget semantics.
        #[cfg(feature="diagnostics")]
        let c151_exact = std::env::var_os("NUCLEUS_C151_EXACT_CACHE").is_some()
            && closure.expr.0==8799 && closure.env.id()==0
            && closure.levels.entries().next().is_none()
            && preserve_stuck_projection && pending.is_empty();
        #[cfg(feature="diagnostics")]
        let c151_event = |event:&str,value:Option<&Value>,retained:bool| {
            if !c151_exact{return;}
            let head=match value {
                Some(Value::Neutral(Neutral{head:NeutralHead::Const{name,..},spine})) =>
                    format!("Const{}A{}",name.0,spine.len()),
                Some(_) => "OtherValue".to_owned(),
                None => "None".to_owned(),
            };
            eprintln!("NUCLEUS_C151_CACHE:event={event}:source=8799:env=0:levels=0:authority={}:transparency={transparency:?}:pending=0:preserve=true:budget={budget}:fuel={}:head={head}:retained={retained}",
                self.authority.0,self.exposure_fuel.get().map_or_else(||"none".to_owned(),|v|v.to_string()));
        };
        let cached = cache.borrow_mut().values.get_mut(&key).map(|entry|{
            entry.referenced=true;entry.value.clone()
        });
        if let Some(value) = cached {
            #[cfg(feature="diagnostics")]
            if self.c153_producer_active.get()>0
                && std::env::var_os("NUCLEUS_C154_NONLEAF_COST").is_some()
            {
                self.c153_nested.borrow_mut().already_cached_hits+=1;
            }
            #[cfg(feature="diagnostics")]
            c151_event("lookup-hit",Some(&value),true);
            if let Some(fuel) = self.exposure_fuel.get() { self.exposure_fuel.set(Some(fuel.saturating_sub(1))); }
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_EXPOSURE_CACHE").is_some() {
                eprintln!("NUCLEUS_EXPOSURE_CACHE:hit:expression={:?}", closure.expr);
            }
            return Judgment::proven(
                Exposure { value, transitions: Vec::new() },
                "certified-cached-closure-exposure",
            );
        }
        #[cfg(feature="diagnostics")]
        c151_event("lookup-miss",None,false);
        #[cfg(feature="diagnostics")]
        let c152_exact=c151_exact
            && std::env::var_os("NUCLEUS_C152_EXACT_HEAD_COST").is_some();
        #[cfg(feature="diagnostics")]
        let c152_before=if c152_exact {
            self.c152_head_active.set(self.c152_head_active.get()+1);
            Some(*self.c152_head_kinds.borrow())
        } else {None};
        #[cfg(feature="diagnostics")]
        let c153_exact=c152_exact
            && self.c153_producer_active.get()==0
            && std::env::var_os("NUCLEUS_C153_NESTED_COMPLETIONS").is_some();
        #[cfg(feature="diagnostics")]
        if c153_exact {
            self.c153_producer_active.set(self.c153_producer_active.get()+1);
            self.c153_entry_serial.set(0);
            *self.c153_nested.borrow_mut()=C153NestedCounts::default();
        }
        let result = self.expose_uncached_internal_with_pending(
            closure, transparency, budget, false,
            preserve_stuck_projection, pending,
        );
        #[cfg(feature="diagnostics")]
        if c153_exact {
            self.c153_producer_active.set(self.c153_producer_active.get().saturating_sub(1));
            let c=self.c153_nested.borrow();
            eprintln!("NUCLEUS_C153_NESTED:source=8799:env=0:authority={}:budget={budget}:calls={}:proven={}:unknown={}:leaf_calls={}:leaf_proven={}:leaf_potentially_cacheable={}:leaf_head_work={}:max_leaf_head_work={}",
                self.authority.0,c.calls,c.proven,c.unknown,c.leaf_calls,c.leaf_proven,
                c.leaf_potentially_cacheable,c.leaf_head_work,c.max_leaf_head_work);
            if std::env::var_os("NUCLEUS_C154_NONLEAF_COST").is_some() {
                eprintln!("NUCLEUS_C154_NONLEAF:source=8799:env=0:authority={}:budget={budget}:nonleaf_calls={}:nonleaf_proven={}:nonleaf_max_head_work={}:ge64={}:ge1024={}:ge65536={}:already_cached_hits={}",
                    self.authority.0,c.nonleaf_calls,c.nonleaf_proven,c.nonleaf_max_head_work,
                    c.nonleaf_ge_64,c.nonleaf_ge_1024,c.nonleaf_ge_65536,c.already_cached_hits);
            }
        }
        #[cfg(feature="diagnostics")]
        if let Some(before)=c152_before {
            self.c152_head_active.set(self.c152_head_active.get().saturating_sub(1));
            let after=*self.c152_head_kinds.borrow();
            let kinds:[usize;8]=std::array::from_fn(|i|after[i].saturating_sub(before[i]));
            let total=kinds.iter().sum::<usize>();
            let outcome=if result.is_proven(){"PROVEN"}
                else if result.is_unknown(){"UNKNOWN"} else {"REFUTED"};
            let head=match result.proven_value().map(|e|&e.value) {
                Some(Value::Neutral(Neutral{head:NeutralHead::Const{name,..},spine})) =>
                    format!("Const{}A{}",name.0,spine.len()),
                Some(_)=>"OtherValue".to_owned(),
                None=>"None".to_owned(),
            };
            eprintln!("NUCLEUS_C152_HEADS:source=8799:env=0:authority={}:budget={budget}:outcome={outcome}:head={head}:total={total}:bvar={}:app={}:lam={}:const={}:proj={}:nat={}:let={}:other={}",
                self.authority.0,kinds[0],kinds[1],kinds[2],kinds[3],kinds[4],kinds[5],kinds[6],kinds[7]);
        }
        #[cfg(feature="diagnostics")]
        c151_event(if result.is_proven(){"uncached-proven"}
            else if result.is_unknown(){"uncached-unknown"}
            else {"uncached-refuted"},
            result.proven_value().map(|e|&e.value),false);
        #[cfg(feature="diagnostics")]
        let mut c151_eligible=false;
        if let Some(established) = result.proven_value()
            // A certified recursor stopped because its major did not expose.
            // This is not a budget-independent normal form; permit a later
            // constructor demand to evaluate the same exact lexical closure.
            && !(self.demand_major && matches!(&established.value,
                Value::Neutral(Neutral { head: NeutralHead::Const {name,..}, .. })
                    if self.recursor_reductions.contains_key(name))
                && !self.recursor_has_immutable_local_major(&established.value))
        {
            #[cfg(feature="diagnostics")]
            {c151_eligible=true;}
            let mut entries = cache.borrow_mut();
            #[cfg(feature="diagnostics")]
            let c151_exact_key=c151_exact.then(||key.clone());
            // Optional cache maintenance shares the existing owner when
            // present, and otherwise uses this call's finite local allowance.
            // Exhaustion declines publication; the proved result is retained.
            let mut local_work=budget;
            entries.retain_exposure(key,&established.value,||{
                if let Some(fuel)=self.exposure_fuel.get(){
                    if fuel==0{return false} self.exposure_fuel.set(Some(fuel-1));true
                } else if local_work>0 {local_work-=1;true} else {false}
            });
            #[cfg(feature="diagnostics")]
            if let Some(exact_key)=c151_exact_key {
                c151_event("publication",Some(&established.value),
                    entries.values.contains_key(&exact_key));
            }
        }
        #[cfg(feature="diagnostics")]
        if c151_exact && !c151_eligible {
            c151_event("publication-skipped",
                result.proven_value().map(|e|&e.value),false);
        }
        result
    }

    // Hash-cons only an exact source evaluator binding. This does not open
    // typed locals or create/transfer any checked typing witness.
    fn bind_captured_argument(&self, binder: &Closure, argument: Closure) -> EnvFrame {
        let Some(cache)=self.exposure_cache.as_ref() else {return binder.env.extend(argument);};
        if !matches!(self.expressions.get(binder.expr),Some(Expr::Lam{..}|Expr::Let{..})) {
            return binder.env.extend(argument);
        }
        let key=(self.authority,binder.clone(),argument.clone());
        if let Some(frame)=cache.borrow().bindings.get(&key).cloned() {return frame;}
        let frame=binder.env.extend(argument);
        let mut entries=cache.borrow_mut();
        // Retained source frames are keys of completed replay evidence.
        // Preserve them at capacity; overflow bindings remain ordinary fresh
        // evaluator frames, with no source or typing equality transferred.
        if entries.bindings.len()<8192 {entries.bindings.insert(key,frame.clone());}
        #[cfg(feature="diagnostics")]
        if entries.bindings.len()>=8192 && std::env::var_os("NUCLEUS_TRACE_REPLAY_CACHE").is_some() {
            use std::sync::atomic::{AtomicUsize,Ordering};
            static PRINTED:AtomicUsize=AtomicUsize::new(0);
            if PRINTED.fetch_add(1,Ordering::Relaxed)<32 {eprintln!("NUCLEUS_BETA_BINDING_CACHE:capacity:source={:?}",binder.expr);}
        }
        frame
    }

    // Reserve work before predecessor allocation and the interner's exact
    // key copying/hashing. Recursive demands charge their shared owner;
    // ordinary iota still respects the caller's local bound.
    fn native_nat_predecessor(&self, number: &crate::nat::BigNat, budget: usize) -> Option<Closure> {
        let cost=number.limb_count().checked_mul(8)?.checked_add(1)?;
        match self.exposure_fuel.get() {
            Some(remaining) => {
                let remaining=remaining.checked_sub(cost)?;
                self.exposure_fuel.set(Some(remaining));
            }
            None if budget<cost => return None,
            None => {}
        }
        self.native_nat_field(number.pred()?)
    }

    // A native numeral is closed mathematical data. Reuse only its exact
    // immutable value carrier under the same authority and verified source
    // BVar(0); typed local environments never enter this interner.
    fn native_nat_field(&self, number: crate::nat::BigNat) -> Option<Closure> {
        let variable=self.nat_primitives.as_ref()?.virtual_bvar_zero?;
        if !matches!(self.expressions.get(variable),Some(Expr::BVar(0))) { return None; }
        let Some(cache)=self.exposure_cache.as_ref() else {
            return Some(Closure::new(variable,EnvFrame::empty().extend_nat_literal(number)));
        };
        let key=(self.authority,variable,number.clone());
        if let Some(frame)=cache.borrow().numeric_bindings.get(&key).cloned() {
            return Some(Closure::new(variable,frame));
        }
        let frame=EnvFrame::empty().extend_nat_literal(number);
        let mut entries=cache.borrow_mut();
        if entries.numeric_bindings.len()>=8192 { entries.numeric_bindings.clear(); }
        entries.numeric_bindings.insert(key,frame.clone());
        Some(Closure::new(variable,frame))
    }

    fn reserve_replay_work(&self,cost:usize)->bool {
        let Some(remaining)=self.exposure_fuel.get().and_then(|f|f.checked_sub(cost)) else {return false;};
        self.exposure_fuel.set(Some(remaining));true
    }

    // Reserve traversal/clone/hash work before allocating a source key.
    // Only references enter this iterative walk, and every pushed node has
    // already paid for its bounded traversal and structural key operations.
    fn reserve_replay_levels(&self,level:&crate::level::LevelTerm)->bool {
        use crate::level::LevelTerm;
        if !self.reserve_replay_work(4) {return false;}
        let mut pending=vec![(level,0usize)];
        while let Some((node,depth))=pending.pop() {
            if depth>=256 {return false;}
            match node {
                LevelTerm::Zero=>{},
                LevelTerm::Param(name)=>if !self.reserve_replay_work(name.len().div_ceil(8)) {return false;},
                LevelTerm::Succ(child)=>{
                    if !self.reserve_replay_work(4) {return false;}
                    pending.push((child,depth+1));
                }
                LevelTerm::Max(left,right)|LevelTerm::IMax(left,right)=>{
                    if !self.reserve_replay_work(8) {return false;}
                    pending.push((left,depth+1));pending.push((right,depth+1));
                }
            }
        }
        true
    }

    fn reserve_replay_key(&self,levels:&[crate::level::LevelTerm],spine:&[Closure],certificate:&RecursorReduction)->bool {
        #[cfg(feature="diagnostics")]
        let before=self.exposure_fuel.get();
        let result=self.reserve_replay_key_inner(levels,spine,certificate);
        #[cfg(feature="diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_REPLAY_CACHE").is_some()
            || std::env::var_os("NUCLEUS_C94_PHASE_TRACE").is_some()
            || std::env::var_os("NUCLEUS_C95_PHASE_TRACE").is_some() {
            let used=before.unwrap_or(0).saturating_sub(self.exposure_fuel.get().unwrap_or(0));
            REPLAY_KEY_WORK.fetch_add(used,std::sync::atomic::Ordering::Relaxed);
        }
        result
    }
    fn reserve_replay_key_inner(&self,levels:&[crate::level::LevelTerm],spine:&[Closure],certificate:&RecursorReduction)->bool {
        let Some(base)=spine.len().checked_add(certificate.rules.len()).and_then(|n|n.checked_add(certificate.level_params.len())).and_then(|n|n.checked_add(4)) else {return false;};
        if !self.reserve_replay_work(base) {return false;}
        for rule in &certificate.rules {if !self.reserve_replay_work(rule.constructor_level_params.len()) {return false;}}
        for level in levels {if !self.reserve_replay_levels(level) {return false;}}
        for closure in spine {
            for (_,level) in closure.levels.entries() {
                if !self.reserve_replay_work(1)||!self.reserve_replay_levels(level) {return false;}
            }
        }
        true
    }

    fn reserve_replay_value_clone(&self,value:&Value)->bool {
        match value {
            Value::NatLit(number)=>number.limb_count().checked_mul(8).is_some_and(|cost|self.reserve_replay_work(cost)),
            Value::Sort(level)=>self.reserve_replay_levels(level),
            Value::Pi{..}|Value::Lam{..}=>self.reserve_replay_work(2),
            Value::StuckProjection{spine,..}=>self.reserve_replay_work(spine.len().saturating_add(1)),
            Value::Neutral(neutral)=>{
                let mut current=neutral;
                let mut depth=0usize;
                loop {
                    if depth>=256 {return false;}
                    if !self.reserve_replay_work(current.spine.len().saturating_add(1)) {return false;}
                    match &current.head {
                        NeutralHead::Const{levels,..}=>return levels.iter().all(|level|self.reserve_replay_levels(level)),
                        NeutralHead::Free(_)=>return true,
                        NeutralHead::Projection{structure,..}=>{depth+=1;current=structure;},
                    }
                }
            }
        }
    }

    fn completed_replay_key(&self,name:NameId,levels:&[crate::level::LevelTerm],spine:&[Closure])->Option<Rc<ReplayKey>> {
        let certificate=self.recursor_reductions.get(&name)?;
        let required=certificate.num_params.checked_add(1)?.checked_add(certificate.rules.len())?
            .checked_add(certificate.num_indices)?.checked_add(1)?;
        if certificate.level_params.len()!=levels.len() || spine.len()<required {return None;}
        if !self.reserve_replay_key(levels,spine,certificate) {return None;}
        #[cfg(test)]
        self.replay_key_builds.set(self.replay_key_builds.get()+1);
        let exact=CompletedReplayKey{authority:self.authority,demand_major:self.demand_major,replay_projection_major:self.replay_projection_major,replay_neutral_projection:self.replay_neutral_projection,
            rules:ImmutableMapWitness(self.recursor_reductions.clone()),
            definitions:ImmutableMapWitness(self.definitions.clone()),projections:ImmutableMapWitness(self.projection_specs.clone()),
            singletons:ImmutableMapWitness(self.singleton_recursor_reductions.clone()),nullary:ImmutableMapWitness(self.nullary_minor_reductions.clone()),
            nested:ImmutableMapWitness(self.closed_nested_minor_reductions.clone()),certificate:certificate.clone(),
            name,levels:levels.to_vec(),spine:spine.to_vec(),nat:self.nat_primitives.clone(),
            bools:self.bool_primitives.clone(),quot:self.quot_primitives.as_ref().map(|q|(q.type_name,q.mk,q.lift,q.ind))};
        use std::hash::{Hash,Hasher};
        let mut hash=std::collections::hash_map::DefaultHasher::new();
        exact.hash(&mut hash);
        Some(Rc::new(ReplayKey{exact,digest:hash.finish()}))
    }

    fn replay_keys_equal(&self,left:&Rc<ReplayKey>,right:&Rc<ReplayKey>)->Option<bool> {
        if Rc::ptr_eq(left,right) {return Some(true);}
        if left.digest!=right.digest {return Some(false);}
        let key=&left.exact;
        if !self.reserve_replay_key(&key.levels,&key.spine,&key.certificate) {return None;}
        Some(left.exact==right.exact)
    }

    fn lookup_completed_replay(&self,key:&Rc<ReplayKey>)->Judgment<Option<Value>> {
        let Some(cache)=self.exposure_cache.as_ref() else {return Judgment::proven(None,"no-completed-replay-cache");};
        let entries=cache.borrow();
        if let Some(bucket)=entries.completed_replays.get(&key.digest) {
            for (saved,value) in bucket {
                let Some(equal)=self.replay_keys_equal(key,saved) else {return Judgment::unknown("nested-replay-comparison-work");};
                if equal {
                    if !self.reserve_replay_value_clone(value) {return Judgment::unknown("nested-replay-cache-work");}
                    return Judgment::proven(Some(value.clone()),"exact-completed-replay");
                }
            }
        }
        Judgment::proven(None,"no-exact-completed-replay")
    }

    fn cache_completed_replay(&self,key:Rc<ReplayKey>,value:&Value) {
        let Some(cache)=self.exposure_cache.as_ref() else {return;};
        if matches!(value,Value::Neutral(Neutral{head:NeutralHead::Const{name,..},..})
            if self.recursor_reductions.contains_key(name)) {return;}
        {
            let entries=cache.borrow();
            if let Some(bucket)=entries.completed_replays.get(&key.digest) {
                for (saved,_) in bucket {
                    match self.replay_keys_equal(&key,saved) {Some(false)=>{},_=>return}
                }
            }
            if entries.completed_replay_count>=8192 {
                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_REPLAY_CACHE").is_some() {
                    use std::sync::atomic::{AtomicUsize,Ordering};
                    static PRINTED:AtomicUsize=AtomicUsize::new(0);
                    if PRINTED.fetch_add(1,Ordering::Relaxed)<32 {eprintln!("NUCLEUS_REPLAY_CACHE:capacity-skip:name={:?}:fuel={:?}",key.exact.name,self.exposure_fuel.get());}
                }
                return;
            }
        }
        if !self.reserve_replay_value_clone(value) {return;}
        let mut entries=cache.borrow_mut();
        entries.completed_replays.entry(key.digest).or_default().push((key,value.clone()));
        entries.completed_replay_count+=1;
    }

    // A captured lexical local cannot later become a constructor under the
    // same immutable environment and authority. Only direct binding chains
    // establish this; definitions and unresolved computations stay uncached.
    fn recursor_has_immutable_local_major(&self, value: &Value) -> bool {
        let Value::Neutral(Neutral { head: NeutralHead::Const { name, .. }, spine }) = value else {return false;};
        let Some(reduction) = self.recursor_reductions.get(name) else {return false;};
        let required = reduction.num_params.saturating_add(1)
            .saturating_add(reduction.rules.len()).saturating_add(reduction.num_indices).saturating_add(1);
        let Some(mut closure) = spine.get(required.saturating_sub(1)).cloned() else {return false;};
        for _ in 0..64 {
            let Some(Expr::BVar(index)) = self.expressions.get(closure.expr) else {return false;};
            match closure.env.lookup(*index) {
                Some(EnvBinding::Free(_)) => return true,
                Some(EnvBinding::Neutral(Neutral { head: NeutralHead::Free(_), .. })) => return true,
                Some(EnvBinding::Closure(bound)) => closure = bound,
                _ => return false,
            }
        }
        false
    }

    fn expose_uncached_internal_with_pending(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
        record_witnesses: bool,
        preserve_stuck_projection: bool,
        pending: Vec<Closure>,
    ) -> Judgment<Exposure> {
        #[cfg(feature="diagnostics")]
        let c118_scope=(self.c118_interior_tail_enabled && self.c115_major_active.get()!=0)
            .then(||{
                let id=self.c118_next_invocation.get();
                self.c118_next_invocation.set(id+1);
                let previous=self.c118_current_invocation.replace(Some(id));
                let start=self.c115_bvar_steps.borrow().len();
                (id,start,C118InvocationScope{active:&self.c118_current_invocation,previous})
            });
        let result=self.expose_uncached_internal_with_pending_impl(
            closure,transparency,budget,record_witnesses,preserve_stuck_projection,pending);
        #[cfg(feature="diagnostics")]
        if let Some((id,start,_scope))=c118_scope {
            let fuel_end=self.exposure_fuel.get();
            let terminal=Rc::new(result.clone());
            for step in self.c115_bvar_steps.borrow_mut()[start..].iter_mut() {
                if step.c118_invocation==Some(id) {
                    step.c118_terminal=Some(C118Terminal{
                        result:terminal.clone(),
                        tail_work:step.c118_fuel.zip(fuel_end).map(|(start,end)|
                            start.saturating_sub(end)),
                    });
                }
            }
        }
        result
    }

    fn expose_uncached_internal_with_pending_impl(
        &self,
        mut closure: Closure,
        transparency: Transparency,
        mut budget: usize,
        record_witnesses: bool,
        preserve_stuck_projection: bool,
        mut pending: Vec<Closure>,
    ) -> Judgment<Exposure> {
        let mut visited = VisitSet::new();
        let mut transitions = Vec::new();

        loop {
            if budget == 0 || self.exposure_fuel.get() == Some(0) {
                return Judgment::unknown("reduction-budget-exhausted");
            }
            budget -= 1;
            if let Some(fuel) = self.exposure_fuel.get() { self.exposure_fuel.set(Some(fuel - 1)); }
            #[cfg(feature="diagnostics")]
            if self.c152_head_active.get()>0 {
                let kind=match self.expressions.get(closure.expr) {
                    Some(Expr::BVar(_))=>0,
                    Some(Expr::App{..})=>1,
                    Some(Expr::Lam{..})=>2,
                    Some(Expr::Const{..})=>3,
                    Some(Expr::Proj{..})=>4,
                    Some(Expr::NatLit(_))=>5,
                    Some(Expr::Let{..})=>6,
                    _=>7,
                };
                self.c152_head_kinds.borrow_mut()[kind]+=1;
            }
            if !visited.insert((self.authority, closure.expr, closure.env.id())) {
                return Judgment::unknown("reduction-cycle");
            }

            let Some(expression) = self.expressions.get(closure.expr) else {
                return Judgment::unknown("missing-expression-during-reduction");
            };
            #[cfg(feature="diagnostics")]
            if self.c97_major_active.get()!=0 {
                let (kind,source)=match expression {
                    Expr::BVar(_)=>(0,closure.expr.0),
                    Expr::App{..}=>(1,closure.expr.0),
                    Expr::Lam{..}=>(2,closure.expr.0),
                    Expr::Let{..}=>(3,closure.expr.0),
                    Expr::Const{name,..}=>(4,name.0),
                    Expr::Proj{..}=>(5,closure.expr.0),
                    Expr::NatLit(_)=>(6,closure.expr.0),
                    _=>(7,closure.expr.0),
                };
                let mut steps=self.c97_steps.borrow_mut();
                steps.loops+=1;
                // This is the entire local evaluator head and pending spine,
                // not a proof that the enclosing worklist state is identical.
                if self.c97_head_pending_seen.borrow_mut().insert((
                    closure.clone(),pending.clone(),transparency,preserve_stuck_projection,
                )) {steps.unique_head_pending+=1;} else {
                    steps.repeat_head_pending+=1;
                    *steps.repeated_heads.entry((kind,source)).or_default()+=1;
                }
                *steps.kinds.entry(kind).or_default()+=1;
                *steps.heads.entry((kind,source)).or_default()+=1;
                *steps.node_env.entry((closure.expr.0,closure.env.id())).or_default()+=1;
            }
            match expression {
                Expr::BVar(index) => {
                    #[cfg(feature="diagnostics")]
                    if self.c115_major_active.get()!=0 {
                        let kind=match closure.env.lookup_binding_ref(*index) {
                            Some(EnvBinding::Closure(_))=>0,
                            Some(EnvBinding::Neutral(_))=>1,
                            Some(EnvBinding::Free(_))=>2,
                            Some(EnvBinding::NatLit(_))=>3,
                            None=>4,
                        };
                        self.c115_bvar_steps.borrow_mut().push(C115BVarStep{
                            state:(closure.clone(),pending.clone(),transparency,preserve_stuck_projection),
                            node:closure.env.diagnostic_binding_node_id(*index),
                            kind,
                            context:self.c116_context_enabled.then(||C116BVarContext{
                                budget,
                                fuel:self.exposure_fuel.get(),
                                witnesses:record_witnesses,
                                visits:visited.diagnostic_keys(),
                                target:match closure.env.lookup_binding_ref(*index) {
                                    Some(EnvBinding::Closure(bound))=>Some(bound.clone()),
                                    _=>None,
                                },
                            }),
                            c118_invocation:self.c118_interior_tail_enabled
                                .then(||self.c118_current_invocation.get()).flatten(),
                            c118_fuel:self.c118_interior_tail_enabled
                                .then(||self.exposure_fuel.get()).flatten(),
                            c118_terminal:None,
                            c119_context:self.c119_dynamic_context_enabled.then(||(
                                self.exposure_depth.get(),self.neutral_projection_depth.get(),
                                self.exposure_fuel.get())),
                        });
                    }
                    if let Some(bound) = closure.env.lookup(*index) {
                        match bound {
                            EnvBinding::Closure(bound) => {
                                visited.clear();
                                closure = bound;
                                continue;
                            }
                            EnvBinding::Free(free) => {
                                let mut spine = Vec::new();
                                append_pending(&mut spine, &mut pending);
                                record_transition(
                                    &mut transitions,
                                    record_witnesses,
                                    TransitionWitness::Rigid,
                                );
                                return exposed(
                                    Value::Neutral(Neutral {
                                        head: NeutralHead::Free(free),
                                        spine,
                                    }),
                                    transitions,
                                );
                            }
                            EnvBinding::NatLit(number) => {
                                if !pending.is_empty() { return Judgment::unknown("native-nat-literal-applied-as-function"); }
                                return exposed(Value::NatLit(number), transitions);
                            }
                            EnvBinding::Neutral(mut neutral) => {
                                append_pending(&mut neutral.spine, &mut pending);
                                record_transition(
                                    &mut transitions,
                                    record_witnesses,
                                    TransitionWitness::Rigid,
                                );
                                return exposed(Value::Neutral(neutral), transitions);
                            }
                        }
                    }
                    let mut spine = Vec::new();
                    append_pending(&mut spine, &mut pending);
                    record_transition(&mut transitions, record_witnesses, TransitionWitness::Rigid);
                    return exposed(
                        Value::Neutral(Neutral {
                            head: NeutralHead::Free(FreeId(*index)),
                            spine,
                        }),
                        transitions,
                    );
                }
                Expr::NatLit(value) if pending.is_empty() => {
                    record_transition(&mut transitions, record_witnesses, TransitionWitness::Rigid);
                    return exposed(Value::NatLit(value.clone()), transitions);
                }
                Expr::NatLit(_) => {
                    return Judgment::unknown("nat-literal-applied-as-function");
                }
                Expr::StrLit(_) => {
                    return Judgment::unknown("string-literal-reduction-not-qualified");
                }
                Expr::Sort(level) if pending.is_empty() => {
                    let Some(level) = self.resolve_level(*level, &closure, budget) else {
                        return Judgment::unknown("unresolved-sort-level-during-reduction");
                    };
                    record_transition(&mut transitions, record_witnesses, TransitionWitness::Rigid);
                    return exposed(Value::Sort(level), transitions);
                }
                Expr::Pi { domain, body } if pending.is_empty() => {
                    record_transition(&mut transitions, record_witnesses, TransitionWitness::Rigid);
                    return exposed(
                        Value::Pi {
                            domain: closure.sibling(*domain, closure.env.clone()),
                            body: closure.sibling(*body, closure.env.clone()),
                        },
                        transitions,
                    );
                }
                Expr::Lam { domain, body } => {
                    // Diagnostic-only, source-ID-pinned beta history for the
                    // four immutable Nat.modCoreGo_lt witnesses. These are
                    // syntax references, NOT production semantic rules.
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_SOURCE_PROOF_BETA").is_some()
                        && matches!(
                            (closure.expr.0, domain.0),
                            (7143,7074)|(6897,6828)|(5728,5659)|(5725,5656)|
                            (7091,5240)|(6845,4961)|(5676,3638)|(5673,3635)
                        )
                    {
                        use std::sync::atomic::{AtomicUsize,Ordering};
                        static COUNT:AtomicUsize=AtomicUsize::new(0);
                        if COUNT.fetch_add(1,Ordering::Relaxed)<200 {
                            eprintln!(
                                "NUCLEUS_SOURCE_BETA:lambda={:?}:domain={domain:?}:env={}:pending={}:actual={:?}:kind={}",
                                closure.expr,closure.env.id(),pending.len(),pending.last(),
                                if pending.is_empty() {"open-lambda"} else {"checked-argument-required"},
                            );
                        }
                    }
                    if let Some(argument) = pending.pop() {
                        record_transition(
                            &mut transitions,
                            record_witnesses,
                            TransitionWitness::Beta,
                        );
                        visited.clear();
                        closure = closure.sibling(*body, self.bind_captured_argument(&closure,argument));
                        continue;
                    }
                    record_transition(&mut transitions, record_witnesses, TransitionWitness::Rigid);
                    return exposed(
                        Value::Lam {
                            domain: closure.sibling(*domain, closure.env.clone()),
                            body: closure.sibling(*body, closure.env.clone()),
                        },
                        transitions,
                    );
                }
                Expr::Let { value, body, .. } => {
                    record_transition(&mut transitions, record_witnesses, TransitionWitness::Zeta);
                    visited.clear();
                    let value = closure.sibling(*value, closure.env.clone());
                    closure = closure.sibling(*body, self.bind_captured_argument(&closure,value));
                }
                Expr::App { fun, arg } => {
                    pending.push(closure.sibling(*arg, closure.env.clone()));
                    closure = closure.sibling(*fun, closure.env.clone());
                }
                Expr::Const { name, levels } => {
                    if let Some(arithmetic)=self.try_native_bounded_arithmetic(*name,levels,&mut pending,transparency,budget) {
                        return match arithmetic {
                            Judgment::Proven{value,..}=>{
                                record_transition(&mut transitions,record_witnesses,TransitionWitness::NatExtension);
                                exposed(value,transitions)
                            }
                            Judgment::Unknown{residual}=>Judgment::Unknown{residual},
                            Judgment::Refuted{obstruction}=>Judgment::Refuted{obstruction},
                        };
                    }
                    if let Some(native) = self.try_native_nat_reduction(
                        *name,
                        levels,
                        &mut pending,
                        transparency,
                        budget,
                    ) {
                        record_transition(
                            &mut transitions,
                            record_witnesses,
                            TransitionWitness::NatExtension,
                        );
                        return exposed(native, transitions);
                    }

                    if let Some(next) = self.try_quot_reduction(*name, levels, &mut pending) {
                        record_transition(
                            &mut transitions,
                            record_witnesses,
                            TransitionWitness::Quotient,
                        );
                        visited.clear();
                        closure = next;
                        continue;
                    }

                    let mut nullary_selected=false;
                    if let Some(rules)=self.nullary_minor_reductions.get(name) {
                        for rule in rules {
                            let required=rule.prefix_len+1;
                            if pending.len()<required || levels.len()!=rule.level_arity || rule.minor_argument>=rule.prefix_len {continue;}
                            let offset=pending.len()-required;
                            let args=pending[offset..].iter().rev().cloned().collect::<Vec<_>>();
                            let major=self.expose_internal(args[rule.prefix_len].clone(),Transparency::Opaque,budget.min(16),false,false);
                            if matches!(major.proven_value(),Some(Exposure {value:Value::Neutral(Neutral {head:NeutralHead::Const {name:ctor,levels},spine}),..})
                                if *ctor==rule.constructor && levels.is_empty() && spine.is_empty()) {
                                let selected=args[rule.minor_argument].clone();
                                pending.truncate(offset);
                                visited.clear();
                                closure=selected;
                                nullary_selected=true;
                                #[cfg(feature="diagnostics")]
                                if std::env::var_os("NUCLEUS_TRACE_NULLARY_MINOR").is_some() {eprintln!("NUCLEUS_NULLARY_IOTA:recursor={name:?}:constructor={:?}:minor={}",rule.constructor,rule.minor_argument);}
                                record_transition(&mut transitions,record_witnesses,TransitionWitness::ConstructorRecursor);
                                break;
                            }
                        }
                        // A selected source minor changes the current closure;
                        // resume evaluation with every surplus argument intact.
                        if nullary_selected {continue;}
                    }

                    let mut nested_selected=false;
                    if let Some(rules)=self.closed_nested_minor_reductions.get(name) {
                        for rule in rules {
                            let required=rule.prefix_len+1;
                            if pending.len()<required || levels.len()!=rule.level_params.len() {continue;}
                            let offset=pending.len()-required;
                            let args=pending[offset..].iter().rev().cloned().collect::<Vec<_>>();
                            let major=self.expose_internal(args[rule.prefix_len].clone(),transparency,budget.min(64),false,false);
                            let Some(Exposure{value:Value::Neutral(Neutral{head:NeutralHead::Const{name:ctor,levels:ctor_levels},spine}),..})=major.proven_value() else{continue;};
                            let p=rule.constructor_parameters.len();
                            if *ctor!=rule.constructor || *ctor_levels!=rule.constructor_levels || spine.len()!=p+rule.num_fields {continue;}
                            if !spine[..p].iter().zip(&rule.constructor_parameters).all(|(actual,(expected_name,expected_levels))| {
                                matches!(self.expose_internal(actual.clone(),Transparency::Opaque,budget.min(64),false,false).proven_value(),Some(Exposure{value:Value::Neutral(Neutral{head:NeutralHead::Const{name,levels},spine}),..})
                                    if name==expected_name && levels==expected_levels && spine.is_empty())
                            }) {continue;}
                            let mut substitution=closure.levels.to_map();
                            let mut valid=true;
                            for (parameter,level) in rule.level_params.iter().zip(levels) {
                                if let Some(actual)=self.resolve_level(*level,&closure,budget) {substitution.insert(*parameter,actual);} else {valid=false;break;}
                            }
                            if !valid {continue;}
                            let mut substitution=substitution.into_iter().collect::<Vec<_>>();substitution.sort_by_key(|(name,_)|name.0);
                            let mut actuals=args[..rule.prefix_len].to_vec();actuals.extend_from_slice(&spine[p..]);
                            pending.truncate(offset);
                            for actual in actuals.iter().rev() {pending.push(actual.clone());}
                            closure=Closure::with_levels(rule.rhs,EnvFrame::empty(),LevelSubstitution::new(substitution));
                            visited.clear();nested_selected=true;
                            record_transition(&mut transitions,record_witnesses,TransitionWitness::ConstructorRecursor);
                            #[cfg(feature="diagnostics")]
                            if std::env::var_os("NUCLEUS_TRACE_NULLARY_MINOR").is_some() {eprintln!("NUCLEUS_CLOSED_NESTED_IOTA:recursor={name:?}:constructor={:?}:fields={}",rule.constructor,rule.num_fields);}
                            break;
                        }
                    }
                    if nested_selected {continue;}

                    // G28: a separately qualified nullary-singleton recursor
                    // ignores its target and returns its sole minor.  This is
                    // kernel computation authority, not delta unfolding.
                    if self.singleton_recursor_reductions.contains(name) && pending.len() >= 3 {
                        let _motive = pending.pop().expect("length checked");
                        let minor = pending.pop().expect("length checked");
                        let _target = pending.pop().expect("length checked");
                        record_transition(
                            &mut transitions,
                            record_witnesses,
                            TransitionWitness::SingletonRecursor,
                        );
                        visited.clear();
                        closure = minor;
                        continue;
                    }
                    if let Some(reduction) = self.recursor_reductions.get(name) {
                        if std::env::var_os("NUCLEUS_TRACE_NAT_IOTA").is_some() && self.nat_primitives.as_ref().is_some_and(|nat| nat.recursor == *name) { eprintln!("NUCLEUS_NAT_REC:pending={}:transparency={transparency:?}:rules={}", pending.len(), reduction.rules.len()); }
                        let required = reduction.num_params
                            + 1
                            + reduction.rules.len()
                            + reduction.num_indices
                            + 1;
                        if pending.len() >= required && reduction.level_params.len() == levels.len()
                        {
                            let offset = pending.len() - required;
                            let arguments =
                                pending[offset..].iter().rev().cloned().collect::<Vec<_>>();
                            let target = arguments.last().expect("required includes target");
                            let prefix_len = reduction.num_params + 1 + reduction.rules.len();
                            if let Some((constructor, constructor_arguments)) =
                                self.rule_constructor_application(
                                    target,
                                    reduction,
                                    transparency,
                                    budget,
                                )
                                && let Some(rule) = reduction
                                    .rules
                                    .iter()
                                    .find(|rule| rule.constructor == constructor)
                                && constructor_arguments.len() == rule.num_params + rule.num_fields
                            {
                                let mut rule_arguments = arguments[..prefix_len].to_vec();
                                rule_arguments
                                    .extend_from_slice(&constructor_arguments[rule.num_params..]);

                                let mut level_substitution = closure.levels.to_map();
                                let mut levels_ok = true;
                                for (parameter, level) in reduction.level_params.iter().zip(levels)
                                {
                                    let Some(level) = self.resolve_level(*level, &closure, budget)
                                    else {
                                        levels_ok = false;
                                        break;
                                    };
                                    level_substitution.insert(*parameter, level);
                                }
                                if levels_ok {
                                    let mut level_substitution =
                                        level_substitution.into_iter().collect::<Vec<_>>();
                                    level_substitution.sort_by_key(|(name, _)| name.0);
                                    pending.truncate(offset);
                                    for argument in rule_arguments.iter().rev() {
                                        pending.push(argument.clone());
                                    }
                                    record_transition(
                                        &mut transitions,
                                        record_witnesses,
                                        TransitionWitness::ConstructorRecursor,
                                    );
                                    visited.clear();
                                    closure = Closure::with_levels(
                                        rule.rhs,
                                        EnvFrame::empty(),
                                        LevelSubstitution::new(level_substitution),
                                    );
                                    continue;
                                }
                            }
                        }
                    }
                    if let Some(definition) = self.definitions.get(name)
                        && permits_delta(transparency, definition.preferred_for_reduction)
                    {
                        if definition.level_params.len() != levels.len() {
                            return Judgment::unknown("polymorphic-delta-arity");
                        }
                        let mut substitution = Vec::with_capacity(levels.len());
                        for (parameter, level) in definition.level_params.iter().zip(levels) {
                            let Some(level) = self.resolve_level(*level, &closure, budget) else {
                                return Judgment::unknown("polymorphic-delta-instantiation");
                            };
                            substitution.push((*parameter, level));
                        }
                        record_transition(
                            &mut transitions,
                            record_witnesses,
                            TransitionWitness::Delta,
                        );
                        closure = Closure::with_levels(
                            definition.value,
                            EnvFrame::empty(),
                            LevelSubstitution::new(substitution),
                        );
                        continue;
                    }
                    let mut instantiated_levels = Vec::with_capacity(levels.len());
                    for level in levels {
                        let Some(level) = self.resolve_level(*level, &closure, budget) else {
                            return Judgment::unknown("neutral-level-instantiation");
                        };
                        instantiated_levels.push(level);
                    }
                    let mut spine = Vec::new();
                    append_pending(&mut spine, &mut pending);
                    record_transition(&mut transitions, record_witnesses, TransitionWitness::Rigid);
                    return exposed(
                        Value::Neutral(Neutral {
                            head: NeutralHead::Const {
                                name: *name,
                                levels: instantiated_levels,
                            },
                            spine,
                        }),
                        transitions,
                    );
                }
                Expr::Proj {
                    type_name,
                    index,
                    structure,
                } => {
                    let Some(spec) = self.projection_specs.get(type_name) else {
                        return Judgment::unknown("unsupported-projection");
                    };
                    let Ok(index) = usize::try_from(*index) else {
                        return Judgment::unknown("projection-index-overflow");
                    };
                    if index >= spec.field_types.len() {
                        return Judgment::unknown("projection-index-out-of-range");
                    }
                    let structure = closure.sibling(*structure, closure.env.clone());
                    let structure_transparency = if preserve_stuck_projection {
                        Transparency::Opaque
                    } else {
                        transparency
                    };
                    let exposed_structure = self.expose_internal(
                        structure.clone(),
                        structure_transparency,
                        budget,
                        false,
                        preserve_stuck_projection,
                    );
                    let Some(exposure) = exposed_structure.proven_value() else {
                        if preserve_stuck_projection {
                            let mut spine = Vec::new();
                            append_pending(&mut spine, &mut pending);
                            return exposed(
                                Value::StuckProjection {
                                    type_name: *type_name,
                                    index,
                                    structure,
                                    spine,
                                },
                                transitions,
                            );
                        }
                        return Judgment::unknown("projection-structure-stuck");
                    };
                    let Value::Neutral(neutral) = &exposure.value else {
                        if preserve_stuck_projection {
                            let mut spine = Vec::new();
                            append_pending(&mut spine, &mut pending);
                            return exposed(
                                Value::StuckProjection {
                                    type_name: *type_name,
                                    index,
                                    structure,
                                    spine,
                                },
                                transitions,
                            );
                        }
                        return Judgment::unknown("projection-structure-stuck");
                    };
                    match &neutral.head {
                        NeutralHead::Const { name, .. } if *name == spec.constructor => {
                            let field_offset = spec.num_params + index;
                            let Some(field) = neutral.spine.get(field_offset).cloned() else {
                                return Judgment::unknown("projection-constructor-arity");
                            };
                            visited.clear();
                            closure = field;
                            continue;
                        }
                        NeutralHead::Const { .. } => {
                            #[cfg(feature="diagnostics")]
                            if std::env::var_os("NUCLEUS_TRACE_PROJECTION_FIELD_FAILURE").is_some() {
                                eprintln!("NUCLEUS_PROJECTION_CONST_MISMATCH:type={type_name:?}:index={index}:expected={:?}:actual={neutral:?}:transparency={transparency:?}",spec.constructor);
                            }
                            if transparency == Transparency::Full && !preserve_stuck_projection
                                && matches!(&neutral.head, NeutralHead::Const { name, .. }
                                    if self.recursor_reductions.contains_key(name))
                                && let Some(field) = self.projection_field_for_conversion(
                                    structure.clone(), *type_name, index, budget.saturating_sub(1),
                                ).proven_value().cloned()
                            {
                                closure = field;
                                visited.clear();
                                continue;
                            }
                            if preserve_stuck_projection {
                                let mut spine = Vec::new();
                                append_pending(&mut spine, &mut pending);
                                return exposed(
                                    Value::StuckProjection {
                                        type_name: *type_name,
                                        index,
                                        structure,
                                        spine,
                                    },
                                    transitions,
                                );
                            }
                            return Judgment::unknown("projection-constructor-mismatch");
                        }
                        NeutralHead::Free(_) | NeutralHead::Projection { .. } => {
                            let mut spine = Vec::new();
                            append_pending(&mut spine, &mut pending);
                            record_transition(
                                &mut transitions,
                                record_witnesses,
                                TransitionWitness::Rigid,
                            );
                            return exposed(
                                Value::Neutral(Neutral {
                                    head: NeutralHead::Projection {
                                        type_name: *type_name,
                                        index,
                                        structure: Box::new(neutral.clone()),
                                    },
                                    spine,
                                }),
                                transitions,
                            );
                        }
                    }
                }
                Expr::Sort(_) | Expr::Pi { .. } => {
                    return Judgment::unknown("rigid-head-applied-as-function");
                }
            }
        }
    }

    fn try_quot_reduction(
        &self,
        name: NameId,
        levels: &[LevelId],
        pending: &mut Vec<Closure>,
    ) -> Option<Closure> {
        let primitives = self.quot_primitives.as_ref()?;

        let (required, target_index, function_index, level_arity) = if name == primitives.lift {
            (6usize, 5usize, 3usize, 2usize)
        } else if name == primitives.ind {
            (5usize, 4usize, 3usize, 1usize)
        } else {
            return None;
        };
        if levels.len() != level_arity || pending.len() < required {
            return None;
        }

        let offset = pending.len() - required;
        let arguments = pending[offset..].iter().rev().cloned().collect::<Vec<_>>();
        let target = arguments.get(target_index)?;
        let (constructor, constructor_arguments) = self.constructor_application(target)?;
        if constructor != primitives.mk || constructor_arguments.len() != 3 {
            return None;
        }

        let function = arguments.get(function_index)?.clone();
        let value = constructor_arguments[2].clone();
        pending.truncate(offset);
        pending.push(value);
        Some(function)
    }

    fn try_native_bounded_arithmetic(&self,name:NameId,levels:&[LevelId],pending:&mut Vec<Closure>,transparency:Transparency,budget:usize)->Option<Judgment<Value>> {
        let nat=self.nat_primitives.as_ref()?;
        let operation = if nat.pow==Some(name) {crate::environment::NatOperation::Pow}
            else if nat.mul==Some(name) {crate::environment::NatOperation::Mul}
            else if nat.land==Some(name) {crate::environment::NatOperation::Land}
            else if nat.shift_right==Some(name) {crate::environment::NatOperation::ShiftRight}
            else if nat.div==Some(name) {crate::environment::NatOperation::Div}
            else if nat.modulo==Some(name) {crate::environment::NatOperation::Mod}
            else {return None;};
        if !levels.is_empty() || pending.len()!=2 {return None;}
        // Native bit/division probes must not normalize large symbolic
        // operand programs just to discover that no numeral is available.
        let operand_budget = if matches!(operation,
            crate::environment::NatOperation::Land | crate::environment::NatOperation::ShiftRight
            | crate::environment::NatOperation::Div | crate::environment::NatOperation::Mod)
        { budget.saturating_sub(1).min(256) } else { budget.saturating_sub(1) };
        let left=self.expose_internal(pending[1].clone(),transparency,operand_budget,false,false);
        let right=self.expose_internal(pending[0].clone(),transparency,operand_budget,false,false);
        #[cfg(feature="diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_NATIVE_NAT_BITS").is_some()
            && matches!(operation,crate::environment::NatOperation::Land|crate::environment::NatOperation::ShiftRight)
        {
            eprintln!("NUCLEUS_NATIVE_NAT_BITS_OPERANDS:operation={operation:?}:left={left:?}:right={right:?}");
        }
        let (Some(Value::NatLit(left)),Some(Value::NatLit(right)))=(left.proven_value().map(|e|&e.value),right.proven_value().map(|e|&e.value)) else{return None;};
        let mut work=budget;
        let result=match operation {
            crate::environment::NatOperation::Pow=>left.pow_bounded(right,&mut work),
            crate::environment::NatOperation::Mul=>left.mul_bounded(right,&mut work),
            crate::environment::NatOperation::Land=>left.land_bounded(right,&mut work),
            crate::environment::NatOperation::ShiftRight=>left.shift_right_bounded(right,&mut work),
            crate::environment::NatOperation::Div=>left.div_mod_bounded(right,&mut work).map(|(quotient,_)|quotient),
            crate::environment::NatOperation::Mod=>left.div_mod_bounded(right,&mut work).map(|(_,remainder)|remainder),
            _=>return None,
        };
        Some(match result {
            Some(number)=>{pending.clear();Judgment::proven(Value::NatLit(number),"qualified-bounded-native-Nat-arithmetic")}
            None=>Judgment::unknown("native-Nat-arithmetic-budget"),
        })
    }

    fn try_native_nat_reduction(
        &self,
        name: NameId,
        levels: &[LevelId],
        pending: &mut Vec<Closure>,
        transparency: Transparency,
        budget: usize,
    ) -> Option<Value> {
        let primitives = self.nat_primitives.as_ref()?;
        enum Operation {
            Add,
            Sub,
            Pred,
            Ble,
            Beq,
        }
        let operation = if primitives.add == Some(name) {
            Operation::Add
        } else if primitives.sub == Some(name) {
            Operation::Sub
        } else if primitives.pred == Some(name) {
            Operation::Pred
        } else if primitives.ble == Some(name) {
            Operation::Ble
        } else if primitives.beq == Some(name) {
            Operation::Beq
        } else {
            return None;
        };
        // Nat.pred (Nat.succ n) reduces to n; on neutral n, preserve the
        // typed source application rather than forcing a recursively stuck
        // matcher. Full transparency may still inspect its definition.
        if matches!(operation, Operation::Pred) {
            if !levels.is_empty() || pending.len() != 1 {
                return None;
            }
            let argument = pending[0].clone();
            let exposed = self.expose_internal(
                argument.clone(), transparency, budget.saturating_sub(1), false, false,
            );
            if let Some(exposed) = exposed.proven_value() {
                match &exposed.value {
                    Value::NatLit(n) => {
                        pending.clear();
                        return Some(Value::NatLit(n.pred().unwrap_or_else(|| n.clone())));
                    }
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: ctor, levels },
                        spine,
                    }) if levels.is_empty() && *ctor == primitives.succ && spine.len() == 1 => {
                        let result = self.expose_internal(
                            spine[0].clone(), transparency, budget.saturating_sub(1),
                            false, false,
                        );
                        if let Some(value) = result.proven_value() {
                            pending.clear();
                            return Some(value.value.clone());
                        }
                    }
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: ctor, levels },
                        spine,
                    }) if levels.is_empty() && *ctor == primitives.zero && spine.is_empty() => {
                        pending.clear();
                        return Some(Value::Neutral(Neutral {
                            head: NeutralHead::Const { name: *ctor, levels: vec![] },
                            spine: vec![],
                        }));
                    }
                    _ => {}
                }
            }
            if transparency != Transparency::Full {
                pending.clear();
                return Some(Value::Neutral(Neutral {
                    head: NeutralHead::Const { name, levels: vec![] },
                    spine: vec![argument],
                }));
            }
            return None;
        }
        if !levels.is_empty() || pending.len() != 2 {
            return None;
        }

        // Applications are accumulated outside-in, so the last pending item
        // is the first source argument.
        let first = pending[pending.len() - 1].clone();
        let second = pending[pending.len() - 2].clone();

        if matches!(operation, Operation::Beq) {
            let bools = self.bool_primitives.as_ref()?;
            let first_value = self
                .expose_internal(
                    first.clone(),
                    transparency,
                    budget.saturating_sub(1),
                    false,
                    false,
                )
                .proven_value()?
                .value
                .clone();
            let second_value = self
                .expose_internal(
                    second.clone(),
                    transparency,
                    budget.saturating_sub(1),
                    false,
                    false,
                )
                .proven_value()?
                .value
                .clone();

            let bool_value = |truth: bool| {
                Value::Neutral(Neutral {
                    head: NeutralHead::Const {
                        name: if truth { bools.true_ctor } else { bools.false_ctor },
                        levels: Vec::new(),
                    },
                    spine: Vec::new(),
                })
            };

            // Nat literals already have exact native meaning.  Comparing two
            // literals is therefore the same definitional consequence as
            // recursively peeling their constructors.
            if let (Some(left), Some(right)) = (
                self.certified_nat_numeral(&first_value, transparency, budget.saturating_sub(1)),
                self.certified_nat_numeral(&second_value, transparency, budget.saturating_sub(1)),
            ) {
                pending.clear();
                return Some(bool_value(left.compare(&right) == std::cmp::Ordering::Equal));
            }

            let constructor_view = |value: &Value| -> Option<(bool, Option<Closure>)> {
                match value {
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name, levels },
                        spine,
                    }) if levels.is_empty()
                        && *name == primitives.zero
                        && spine.is_empty() =>
                    {
                        Some((false, None))
                    }
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name, levels },
                        spine,
                    }) if levels.is_empty()
                        && *name == primitives.succ
                        && spine.len() == 1 =>
                    {
                        Some((true, Some(spine[0].clone())))
                    }
                    Value::NatLit(value) if value.is_zero() => Some((false, None)),
                    _ => None,
                }
            };

            let (first_succ, first_pred) = constructor_view(&first_value)?;
            let (second_succ, second_pred) = constructor_view(&second_value)?;
            pending.clear();
            return match (first_succ, second_succ) {
                (false, false) => Some(bool_value(true)),
                (false, true) | (true, false) => Some(bool_value(false)),
                (true, true) => Some(Value::Neutral(Neutral {
                    head: NeutralHead::Const {
                        name,
                        levels: Vec::new(),
                    },
                    spine: vec![first_pred?, second_pred?],
                })),
            };
        }

        // Nat.add n 0 = n and Nat.add n (succ 0) = succ n.
        // These are the exact constructor equations of the checked Prelude
        // definition, and work for any already well-typed symbolic n.
        // This contraction does not infer any recursor major or proof index.
        if matches!(operation, Operation::Add) {
            let right = self.expose_internal(
                second.clone(), transparency, budget.saturating_sub(1), false, false,
            );
            if let Some(v) = right.proven_value().map(|x| &x.value) {
                let zero = |v: &Value| matches!(v,
                    Value::NatLit(n) if n.is_zero())
                    || matches!(v,
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: ctor, levels },
                        spine,
                    }) if *ctor==primitives.zero && levels.is_empty() && spine.is_empty());
                let one = matches!(v,
                    Value::NatLit(n) if n.pred().is_some_and(|pre| pre.is_zero()))
                    || matches!(v,
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: ctor, levels },
                        spine,
                    }) if *ctor == primitives.succ && levels.is_empty() && spine.len()==1
                        && self.expose_internal(
                            spine[0].clone(), transparency, budget.saturating_sub(1),
                            false, false,
                        ).proven_value().is_some_and(|x| zero(&x.value)));
                if zero(v) {
                    let first_value = self.expose_internal(
                        first.clone(), transparency, budget.saturating_sub(1),
                        false, false,
                    );
                    if let Some(value)=first_value.proven_value() {
                        pending.clear();
                        #[cfg(feature="diagnostics")]
                        if std::env::var_os("NUCLEUS_TRACE_NAT_ADDONE").is_some() {
                            eprintln!("NUCLEUS_NAT_ADDONE:checked-zero");
                        }
                        return Some(value.value.clone());
                    }
                }
                if one {
                    pending.clear();
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_NAT_ADDONE").is_some() {
                        eprintln!("NUCLEUS_NAT_ADDONE:checked-one");
                    }
                    return Some(Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: primitives.succ, levels: vec![] },
                        spine: vec![first],
                    }));
                }
            }
        }

        // Pinned Lean v4.34.1 Init.Prelude defines:
        //   Nat.ble zero _ = true
        //   Nat.ble (succ _) zero = false
        //   Nat.ble (succ n) (succ m) = Nat.ble n m
        // The existing native extension only handled two numerals. Preserve
        // this exact source-defined one-step symbolic computation without
        // claiming the predecessor variables or proof indices are equal.
        if matches!(operation, Operation::Ble) {
            let bools = self.bool_primitives.as_ref()?;
            let as_constructor = |v: &Value| -> Option<(bool, Option<Closure>)> {
                match v {
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name, levels },
                        spine,
                    }) if levels.is_empty()
                        && *name == primitives.zero
                        && spine.is_empty() => Some((false, None)),
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name, levels },
                        spine,
                    }) if levels.is_empty()
                        && *name == primitives.succ
                        && spine.len() == 1 => Some((true, Some(spine[0].clone()))),
                    Value::NatLit(n) if n.is_zero() => Some((false, None)),
                    _ => None,
                }
            };
            let boolean = |truth: bool| Value::Neutral(Neutral {
                head: NeutralHead::Const {
                    name: if truth { bools.true_ctor } else { bools.false_ctor },
                    levels: Vec::new(),
                },
                spine: Vec::new(),
            });
            let left = self.expose_internal(
                first.clone(), transparency, budget.saturating_sub(1), false, false,
            ).proven_value()?.value.clone();
            if let Some((false, None)) = as_constructor(&left) {
                pending.clear();
                return Some(boolean(true));
            }
            let right = self.expose_internal(
                second.clone(), transparency, budget.saturating_sub(1), false, false,
            ).proven_value()?.value.clone();
            if let (Some(n), Some(m)) = (
                self.certified_nat_numeral(&left,transparency,budget.saturating_sub(1)),
                self.certified_nat_numeral(&right,transparency,budget.saturating_sub(1)),
            ) {
                pending.clear();
                return Some(boolean(n.compare(&m) != std::cmp::Ordering::Greater));
            }
            match (as_constructor(&left), as_constructor(&right)) {
                (Some((true, Some(_))), Some((false, None))) => {
                    pending.clear();
                    return Some(boolean(false));
                }
                (Some((true, Some(n))), Some((true, Some(m)))) => {
                    pending.clear();
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_BLE_SYMBOLIC").is_some() {
                        eprintln!("NUCLEUS_BLE_SYMBOLIC:succ-succ:head={name:?}");
                    }
                    return Some(Value::Neutral(Neutral {
                        head: NeutralHead::Const { name, levels: Vec::new() },
                        spine: vec![n, m],
                    }));
                }
                _ => {}
            }
            return None;
        }

        // Verified source equation (Lean v4.34.1 Init.Prelude):
        // Nat.sub a 0 = a, including an arbitrary symbolic a.
        // No predecessor is synthesized and no unsupported succ rule is
        // inferred. The receiver's established WHNF is reused directly.
        if matches!(operation, Operation::Sub) {
            let second_value = self.expose_internal(
                second.clone(), transparency, budget.saturating_sub(1), false, false,
            );
            let zero_major = matches!(second_value.proven_value().map(|e| &e.value), Some(Value::NatLit(n)) if n.is_zero())
                || matches!(second_value.proven_value().map(|e| &e.value),
                    Some(Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: ctor, levels },
                        spine,
                    })) if *ctor == primitives.zero && levels.is_empty() && spine.is_empty());
            if zero_major {
                if let Some(first_value) = self.expose_internal(
                    first.clone(), transparency, budget.saturating_sub(1), false, false,
                ).proven_value().map(|e| e.value.clone()) {
                    pending.clear();
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_NAT_SUBZERO").is_some() {
                        eprintln!("NUCLEUS_NAT_SUBZERO:certified-zero-right");
                    }
                    return Some(first_value);
                }
            }
            // Nat.sub (succ a) (succ zero) = a, obtained by two
            // checked Nat.sub clauses and Nat.pred (succ a) = a.
            // Both constructor witnesses are required. A symbolic second
            // predecessor is deliberately NOT eliminated.
            if primitives.pred.is_some()
                && let Some(Value::Neutral(Neutral {
                    head: NeutralHead::Const { name: second_ctor, levels: second_levels },
                    spine: second_spine,
                })) = second_value.proven_value().map(|e| &e.value)
                && *second_ctor == primitives.succ
                && second_levels.is_empty()
                && second_spine.len() == 1
            {
                let predecessor = self.expose_internal(
                    second_spine[0].clone(), transparency,
                    budget.saturating_sub(1), false, false,
                );
                let is_zero = matches!(predecessor.proven_value().map(|e| &e.value),
                    Some(Value::NatLit(n)) if n.is_zero())
                    || matches!(predecessor.proven_value().map(|e| &e.value),
                        Some(Value::Neutral(Neutral {
                            head: NeutralHead::Const { name: zero, levels },
                            spine,
                        })) if *zero == primitives.zero && levels.is_empty() && spine.is_empty());
                if is_zero {
                    let first_value = self.expose_internal(
                        first.clone(), transparency, budget.saturating_sub(1), false, false,
                    );
                    if let Some(Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: first_ctor, levels: first_levels },
                        spine: first_spine,
                    })) = first_value.proven_value().map(|e| &e.value)
                        && *first_ctor == primitives.succ
                        && first_levels.is_empty()
                        && first_spine.len() == 1
                    {
                        let result = self.expose_internal(
                            first_spine[0].clone(), transparency,
                            budget.saturating_sub(1), false, false,
                        );
                        if let Some(established) = result.proven_value() {
                            pending.clear();
                            #[cfg(feature = "diagnostics")]
                            if std::env::var_os("NUCLEUS_TRACE_NAT_SUBSUCC_ZERO").is_some() {
                                eprintln!("NUCLEUS_NAT_SUBSUCC_ZERO:certified-double-constructor");
                            }
                            return Some(established.value.clone());
                        }
                    }
                }
            }

            // Exact Lean v4.34.1 Nat.sub definition:
            //   Nat.sub a (Nat.succ b) = Nat.pred (Nat.sub a b).
            // Retain both source argument closures; a new opaque binder
            // holds the already-evaluated, typed inner native application.
            // It never equates two different b values or indexes.
            if let Some(Value::Neutral(Neutral {
                head: NeutralHead::Const { name: ctor, levels },
                spine,
            })) = second_value.proven_value().map(|e| &e.value)
                && *ctor == primitives.succ && levels.is_empty() && spine.len() == 1
                && let (Some(pred), Some(bvar0)) =
                    (primitives.pred, primitives.virtual_bvar_zero)
            {
                let sub_thunk = Closure::new(
                    bvar0,
                    EnvFrame::empty().extend_neutral(Neutral {
                        head: NeutralHead::Const { name, levels: vec![] },
                        spine: vec![first.clone(), spine[0].clone()],
                    }),
                );
                pending.clear();
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_NAT_SUBSUCC").is_some() {
                    eprintln!("NUCLEUS_NAT_SUBSUCC:checked-source-successor:pred={:?}", pred);
                }
                return Some(Value::Neutral(Neutral {
                    head: NeutralHead::Const { name: pred, levels: vec![] },
                    spine: vec![sub_thunk],
                }));
            }
            // No constructor evidence for the major: keep the expression
            // neutral on the cheap path; Full transparency retains the
            // definitional fallback. No equality is asserted here.
            if transparency != Transparency::Full
                && !matches!(second_value.proven_value().map(|e| &e.value), Some(Value::NatLit(_)))
            {
                pending.clear();
                return Some(Value::Neutral(Neutral {
                    head: NeutralHead::Const { name, levels: vec![] },
                    spine: vec![first, second],
                }));
            }
        }

        let first_value = self
            .expose_internal(first, transparency, budget.saturating_sub(1), false, false)
            .proven_value()?
            .value
            .clone();
        let second_value = self
            .expose_internal(second, transparency, budget.saturating_sub(1), false, false)
            .proven_value()?
            .value
            .clone();
        let (Value::NatLit(first), Value::NatLit(second)) = (first_value, second_value) else {
            return None;
        };
        pending.clear();
        Some(match operation {
            Operation::Pred => unreachable!("unary Nat.pred handled above"),
            Operation::Add => Value::NatLit(first.add(&second)),
            Operation::Sub => Value::NatLit(first.sub_trunc(&second)),
            Operation::Ble => {
                let bools = self.bool_primitives.as_ref()?;
                let ctor = if first.compare(&second) != std::cmp::Ordering::Greater {
                    bools.true_ctor
                } else {
                    bools.false_ctor
                };
                Value::Neutral(Neutral {
                    head: NeutralHead::Const {
                        name: ctor,
                        levels: Vec::new(),
                    },
                    spine: Vec::new(),
                })
            }
            Operation::Beq => unreachable!("Nat.beq handled before literal-only operations"),
        })
    }

    /// Read an exact certified zero/successor chain ending in a numeral.
    /// Cached constructor WHNFs remain valid inputs; no neutral predecessor
    /// or desired comparison result is interpreted as numeral evidence.
    fn certified_nat_numeral(&self,value:&Value,transparency:Transparency,mut budget:usize)->Option<crate::nat::BigNat> {
        let nat=self.nat_primitives.as_ref()?;
        let mut current=value.clone();let mut successors=crate::nat::BigNat::zero();
        let one=crate::nat::BigNat::parse_decimal("1")?;
        loop {
            if budget==0 {return None;}budget-=1;
            match current {
                Value::NatLit(number)=>return Some(number.add(&successors)),
                Value::Neutral(Neutral{head:NeutralHead::Const{name,levels},spine}) if levels.is_empty() && name==nat.zero && spine.is_empty()=>return Some(successors),
                Value::Neutral(Neutral{head:NeutralHead::Const{name,levels},spine}) if levels.is_empty() && name==nat.succ && spine.len()==1=>{
                    successors=successors.add(&one);
                    current=self.expose_internal(spine[0].clone(),transparency,budget,false,false).proven_value()?.value.clone();
                }
                _=>return None,
            }
        }
    }

    fn constructor_application(&self, target: &Closure) -> Option<(NameId, Vec<Closure>)> {
        let mut closure = target.clone();
        let mut arguments = Vec::new();
        loop {
            match self.expressions.get(closure.expr)? {
                Expr::App { fun, arg } => {
                    arguments.push(closure.sibling(*arg, closure.env.clone()));
                    closure = closure.sibling(*fun, closure.env.clone());
                }
                Expr::BVar(index) => match closure.env.lookup(*index)? {
                    EnvBinding::Closure(bound) => {
                        closure = bound;
                    }
                    EnvBinding::Free(_) | EnvBinding::Neutral(_) | EnvBinding::NatLit(_) => return None,
                },
                Expr::Const { name, .. } => {
                    arguments.reverse();
                    return Some((*name, arguments));
                }
                _ => return None,
            }
        }
    }

    /// Reproduce one *existing* certified Nat.rec iota rule on an already
    /// evaluated neutral application. The expression evaluator normally
    /// performs this earlier, but type conversion can retain a rigid
    /// neutral because its cheap exposure precedes Full unfolding.
    ///
    /// No equality is guessed: only the installed recursor metadata,
    /// literal zero major, original minor arguments, RHS syntax and
    /// universe substitution are allowed to produce the reduct.
    pub(crate) fn qualified_nat_zero_recursor_result(
        &self,
        neutral: &Neutral,
        budget: usize,
    ) -> Judgment<Value> {
        if budget < 32 {
            return Judgment::unknown("natrec-zero-iota-small-budget");
        }
        let NeutralHead::Const { name, levels } = &neutral.head else {
            return Judgment::unknown("natrec-zero-iota-nonconst");
        };
        let (Some(nat), Some(reduction)) = (
            self.nat_primitives.as_ref(),
            self.recursor_reductions.get(name),
        ) else {
            return Judgment::unknown("natrec-zero-iota-missing-authority");
        };
        if *name != nat.recursor
            || reduction.num_params != 0
            || reduction.num_indices != 0
            || reduction.rules.len() != 2
            || reduction.level_params.len() != levels.len()
            || !reduction.rules.iter().any(|r| {
                r.constructor == nat.succ && r.num_fields == 1 && r.num_params == 0
            })
        {
            return Judgment::unknown("natrec-zero-iota-interface");
        }
        let required = reduction.num_params + 1
            + reduction.rules.len() + reduction.num_indices + 1;
        if neutral.spine.len() != required {
            return Judgment::unknown("natrec-zero-iota-arity");
        }
        let Some(rule) = reduction.rules.iter().find(|r| {
            r.constructor == nat.zero && r.num_fields == 0 && r.num_params == 0
        }) else {
            return Judgment::unknown("natrec-zero-iota-zero-rule");
        };
        let Some(major) = neutral.spine.last() else {
            return Judgment::unknown("natrec-zero-iota-major-missing");
        };
        let major_exposed = self.expose(
            major.clone(), Transparency::Full, budget.saturating_sub(1).min(256),
        );
        if !matches!(
            major_exposed.proven_value(),
            Some(Value::NatLit(n)) if n.is_zero()
        ) {
            return Judgment::unknown("natrec-zero-iota-major-not-canonical");
        }

        let substitution = reduction.level_params.iter().copied()
            .zip(levels.iter().cloned()).collect::<Vec<_>>();
        let mut result = Closure::with_levels(
            rule.rhs, EnvFrame::empty(), LevelSubstitution::new(substitution),
        );
        let prefix_len = reduction.num_params + 1 + reduction.rules.len();
        for arg in neutral.spine.iter().take(prefix_len) {
            let mut lets = 0usize;
            loop {
                match self.expressions.get(result.expr) {
                    Some(Expr::Lam { body, .. }) => {
                        result = result.sibling(*body, self.bind_captured_argument(&result,arg.clone()));
                        break;
                    }
                    Some(Expr::Let { value, body, .. }) if lets < 32 => {
                        let value = result.sibling(*value, result.env.clone());
                        result = result.sibling(*body, self.bind_captured_argument(&result,value));
                        lets += 1;
                    }
                    _ => return Judgment::unknown("natrec-zero-iota-rhs-telescope"),
                }
            }
        }
        self.expose(
            result, Transparency::Full, budget.saturating_sub(1).min(512),
        )
    }

    /// Evaluate only a source-registered recursor's constructor iota rule.
    ///
    /// This handles *evaluated neutrals* retained during conversion, rather
    /// than guessing a constructor from the desired output. The major may be
    /// another independently registered recursor: descend only while the
    /// major is backed by an exact checked rule, then replay the chosen
    /// rule's actual RHS through its lambda telescope.
    ///
    /// A neutral major without a constructor witness remains UNKNOWN.
    /// Return the actual source RHS after the requested checked iota.
    /// Nested majors still require constructor evidence; partial RHS values
    /// never enter the completed replay memo.
    pub(crate) fn qualified_one_step_recursor_result(&self,neutral:&Neutral,budget:usize)->Judgment<Value> {
        self.qualified_recursor_result(neutral,budget,CheckedReplayGoal::OneStep)
    }

    pub(crate) fn qualified_nested_recursor_result(&self,neutral:&Neutral,budget:usize)->Judgment<Value> {
        self.qualified_recursor_result(neutral,budget,CheckedReplayGoal::Completed)
    }

    fn checked_neutral_projection_result(&self,neutral:&Neutral,budget:usize)->Judgment<Value>{
        // This operation selects only an actual field of the actual result
        // of an independently registered source recursor. Neither a desired
        // constructor nor the surrounding equality chooses a branch.
        let NeutralHead::Projection{type_name,index,structure}=&neutral.head else {
            return Judgment::unknown("neutral-projection-head");
        };
        let Some(spec)=self.projection_specs.get(type_name)else{
            return Judgment::unknown("neutral-projection-owner");
        };
        if *index>=spec.field_types.len(){return Judgment::unknown("neutral-projection-index");}
        if !matches!(&structure.head,NeutralHead::Const{name,..}if self.recursor_reductions.contains_key(name)){
            return Judgment::unknown("neutral-projection-receiver-not-qualified-recursor");
        }
        if self.neutral_projection_depth.get()>=8{return Judgment::unknown("neutral-projection-depth");}
        let Some(fuel)=self.exposure_fuel.get()else{return Judgment::unknown("neutral-projection-no-work-owner");};
        if fuel==0{return Judgment::unknown("neutral-projection-budget");}
        self.exposure_fuel.set(Some(fuel-1));
        self.neutral_projection_depth.set(self.neutral_projection_depth.get()+1);
        let _scope=NeutralProjectionDepthScope{depth:&self.neutral_projection_depth};
        // Qualified replay checks source rule, universe instances and actual
        // constructor arity. It shares this same work allowance recursively.
        let replay=self.qualified_nested_recursor_result(structure,budget.min(fuel-1));
        let Some(Value::Neutral(actual))=replay.proven_value()else{return Judgment::unknown("neutral-projection-receiver-replay");};
        let NeutralHead::Const{name,..}=&actual.head else{return Judgment::unknown("neutral-projection-receiver-nonconstructor");};
        if *name!=spec.constructor || actual.spine.len()!=spec.num_params+spec.field_types.len(){
            return Judgment::unknown("neutral-projection-receiver-owner-or-arity");
        }
        let field=actual.spine[spec.num_params+*index].clone();
        let pending:Vec<Closure>=neutral.spine.iter().rev().cloned().collect();
        let allowance=self.exposure_fuel.get().unwrap_or(0).min(budget);
        let cheap=self.expose_internal_with_pending(field.clone(),Transparency::Reducible,allowance,false,true,pending.clone()).map(|x|x.value);
        if cheap.is_proven(){return cheap}
        self.expose_internal_with_pending(field,Transparency::Full,self.exposure_fuel.get().unwrap_or(0).min(budget),false,true,pending).map(|x|x.value)
    }

    fn qualified_recursor_result(
        &self,neutral:&Neutral,budget:usize,goal:CheckedReplayGoal,
    ) -> Judgment<Value> {
        // Exposure and replay consume the same owner's work allowance. A
        // child never receives a fresh budget, and this scope does not reset
        // an allowance already owned by a surrounding constructor demand.
        if budget < 48 { return Judgment::unknown("nested-recursor-iota-budget"); }
        let _fuel_scope = if self.exposure_fuel.get().is_none() {
            self.exposure_fuel.set(Some(budget));
            Some(ConstructorFuelScope { fuel: &self.exposure_fuel })
        } else { None };
        #[cfg(feature="diagnostics")]
        let _work_trace=std::env::var_os("NUCLEUS_TRACE_REPLAY_CACHE").map(|_|ReplayWorkTrace{
            fuel:&self.exposure_fuel,start:self.exposure_fuel.get().unwrap_or(0),
            key_start:REPLAY_KEY_WORK.load(std::sync::atomic::Ordering::Relaxed),head:&neutral.head,
        });
        #[cfg(feature="diagnostics")]
        let c94_counts=C94PhaseCounts::default();
        #[cfg(feature="diagnostics")]
        let c104_counts=RefCell::new(C104MajorCounts::default());
        #[cfg(feature="diagnostics")]
        let _c104_receipt=std::env::var_os("NUCLEUS_C104_MAJOR_EXPOSURE_TRACE").map(|_|C104MajorReceipt{
            counts:&c104_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c105_counts=RefCell::new(C105TerminalCounts::default());
        #[cfg(feature="diagnostics")]
        let _c105_receipt=std::env::var_os("NUCLEUS_C105_TERMINAL_BINDING_TRACE").map(|_|C105TerminalReceipt{
            counts:&c105_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c106_counts=RefCell::new(C106SupportCounts::default());
        #[cfg(feature="diagnostics")]
        let _c106_receipt=std::env::var_os("NUCLEUS_C106_RELEVANT_BINDINGS_TRACE").map(|_|C106SupportReceipt{
            counts:&c106_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c109_counts=RefCell::new(C109FunctionCounts::default());
        #[cfg(feature="diagnostics")]
        let _c109_receipt=std::env::var_os("NUCLEUS_C109_FUNCTION_BINDING_TRACE").map(|_|C109FunctionReceipt{
            counts:&c109_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c110_counts=RefCell::new(C110CaptureCounts::default());
        #[cfg(feature="diagnostics")]
        let _c110_receipt=std::env::var_os("NUCLEUS_C110_FUNCTION_CAPTURE_TRACE").map(|_|C110CaptureReceipt{
            counts:&c110_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c111_counts=RefCell::new(C111MajorCounts::default());
        #[cfg(feature="diagnostics")]
        let _c111_receipt=std::env::var_os("NUCLEUS_C111_CHARGED_MAJOR_OUTCOMES_TRACE").map(|_|C111MajorReceipt{
            counts:&c111_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c112_counts=RefCell::new(C112RuleCounts::default());
        #[cfg(feature="diagnostics")]
        let _c112_receipt=std::env::var_os("NUCLEUS_C112_MAJOR_RULE_FRONTIER_TRACE").map(|_|C112RuleReceipt{
            counts:&c112_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c113_counts=RefCell::new(C113HighCounts::default());
        #[cfg(feature="diagnostics")]
        let _c113_receipt=std::env::var_os("NUCLEUS_C113_POST_MAJOR_RHS_COST_TRACE").map(|_|C113HighReceipt{
            counts:&c113_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c114_counts=RefCell::new(C114HighCounts::default());
        #[cfg(feature="diagnostics")]
        let _c114_receipt=std::env::var_os("NUCLEUS_C114_HIGH_MAJOR_STEP_TRACE").map(|_|C114HighReceipt{
            counts:&c114_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c115_counts=RefCell::new(C115BoundCounts::default());
        #[cfg(feature="diagnostics")]
        let _c115_receipt=std::env::var_os("NUCLEUS_C115_BOUND_TRANSITION_IDENTITY_TRACE").map(|_|C115BoundReceipt{
            counts:&c115_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c116_counts=RefCell::new(C116ContextCounts::default());
        #[cfg(feature="diagnostics")]
        let _c116_receipt=self.c116_context_enabled.then(||C116ContextReceipt{
            counts:&c116_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c117_counts=RefCell::new(C117CallCounts::default());
        #[cfg(feature="diagnostics")]
        let _c117_receipt=self.c117_completed_entry_enabled.then(||C117CallReceipt{
            counts:&c117_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c118_counts=RefCell::new(C118SegmentCounts::default());
        #[cfg(feature="diagnostics")]
        let _c118_receipt=self.c118_interior_tail_enabled.then(||C118SegmentReceipt{
            counts:&c118_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c119_counts=RefCell::new(C119ContextCounts::default());
        #[cfg(feature="diagnostics")]
        let _c119_receipt=self.c119_dynamic_context_enabled.then(||C119ContextReceipt{
            counts:&c119_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c120_counts=RefCell::new(C120SpanCounts::default());
        #[cfg(feature="diagnostics")]
        let _c120_receipt=self.c120_repeated_span_enabled.then(||C120SpanReceipt{
            counts:&c120_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c121_counts=RefCell::new(C121MidCounts::default());
        #[cfg(feature="diagnostics")]
        let _c121_receipt=std::env::var_os("NUCLEUS_C121_MID_MAJOR_FRONTIER_TRACE").map(|_|C121MidReceipt{
            counts:&c121_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c122_events=RefCell::new(Vec::<C122SourceEvent>::new());
        #[cfg(feature="diagnostics")]
        let _c122_receipt=std::env::var_os("NUCLEUS_C122_NESTED_SOURCE_TRANSITION_TRACE").map(|_|C122SourceReceipt{
            events:&c122_events,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c123_events=RefCell::new(Vec::<C123BVarChainEvent>::new());
        #[cfg(feature="diagnostics")]
        let _c123_receipt=std::env::var_os("NUCLEUS_C123_BVAR_CHAIN_TERMINAL_TRACE").map(|_|C123BVarChainReceipt{
            events:&c123_events,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let c124_events=RefCell::new(Vec::<C124AppProfileEvent>::new());
        #[cfg(feature="diagnostics")]
        let _c124_receipt=std::env::var_os("NUCLEUS_C124_TERMINAL_APP_PROFILE").map(|_|C124AppProfileReceipt{
            events:&c124_events,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let _c94_receipt=std::env::var_os("NUCLEUS_C94_PHASE_TRACE").map(|_|C94PhaseReceipt{
            counts:&c94_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
            key_start:REPLAY_KEY_WORK.load(std::sync::atomic::Ordering::Relaxed),
            head:&neutral.head,
        });
        #[cfg(feature="diagnostics")]
        let c95_counts=C95StageCounts::default();
        #[cfg(feature="diagnostics")]
        let _c95_receipt=std::env::var_os("NUCLEUS_C95_PHASE_TRACE").map(|_|C95StageReceipt{
            counts:&c95_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
            key_start:REPLAY_KEY_WORK.load(std::sync::atomic::Ordering::Relaxed),
            head:&neutral.head,
        });
        #[cfg(feature="diagnostics")]
        let c96_counts=C96MajorCounts::default();
        #[cfg(feature="diagnostics")]
        let _c96_receipt=std::env::var_os("NUCLEUS_C96_MAJOR_TRACE").map(|_|C96MajorReceipt{
            counts:&c96_counts,fuel:&self.exposure_fuel,
            start:self.exposure_fuel.get().unwrap_or(0),
        });
        #[cfg(feature="diagnostics")]
        let _c97_receipt=std::env::var_os("NUCLEUS_C97_MAJOR_STEP_TRACE").map(|_|C97Receipt{
            machine:self,start:self.exposure_fuel.get().unwrap_or(0),
            baseline:self.c97_steps.borrow().clone(),
        });
        let spend = || {
            let Some(fuel)=self.exposure_fuel.get() else { return false; };
            if fuel == 0 { return false; }
            self.exposure_fuel.set(Some(fuel-1));
            true
        };
        let mut current=neutral.clone();
        let mut current_is_requested=true;
        enum Continuation { Finish(Rc<ReplayKey>), Major(Neutral,bool) }
        let mut parents=Vec::new();
        #[cfg(feature="diagnostics")]
        let mut c113_awaiting_resume:Option<usize>=None;
        let mut established_major=None;
        let mut active=HashSet::new();
        let mut resolved:HashMap<usize,Value>=HashMap::new();
        // Retain all local keys so pointer identities cannot be recycled.
        // Exact structural comparison occurs only while interning a node.
        let mut entered:HashMap<u64,Vec<Rc<ReplayKey>>>=HashMap::new();
        // Finish both a selected rule and any result recursors before
        // memoizing. Exact source closures, universes, and arguments form
        // the key; no desired result or unrelated frame licenses reuse.
        macro_rules! finish {
            ($target:lifetime, $value:expr) => {{
                let value=$value;
                while let Some(continuation)=parents.pop() {
                    match continuation {
                        Continuation::Finish(key) => {
                            #[cfg(feature="diagnostics")]
                            let _c95_finish=_c95_receipt.as_ref().map(|_|C95StageCharge::new(
                                &self.exposure_fuel,&c95_counts.finish));
                            #[cfg(feature="diagnostics")]
                            if _c94_receipt.is_some(){c94_counts.completed.set(c94_counts.completed.get()+1);}
                            active.remove(&ReplayKey::identity(&key));
                            self.cache_completed_replay(key.clone(),&value);
                            if self.reserve_replay_value_clone(&value) {resolved.insert(ReplayKey::identity(&key),value.clone());}
                        }
                        Continuation::Major(parent,requested) => {
                            #[cfg(feature="diagnostics")]
                            if _c94_receipt.is_some(){c94_counts.resumed.set(c94_counts.resumed.get()+1);}
                            #[cfg(feature="diagnostics")]
                            if let Some(index)=c113_awaiting_resume.take() {
                                if let Some(event)=c113_counts.borrow_mut().events.get_mut(index) {
                                    event.resumed=true;
                                }
                            }
                            current=parent;
                            current_is_requested=requested;
                            established_major=Some(value);
                            continue $target;
                        }
                    }
                }
                return Judgment::proven(value,"checked-source-recursor-worklist");
            }}
        }
        'evaluate: loop {
            if !spend() { return Judgment::unknown("nested-recursor-iota-budget"); }
            #[cfg(feature="diagnostics")]
            if _c94_receipt.is_some(){c94_counts.max_depth.set(c94_counts.max_depth.get().max(parents.len()));}
            let neutral=&current;
            #[cfg(feature="diagnostics")]
            let depth=parents.len();
            let NeutralHead::Const { name, levels } = &neutral.head else {
                return Judgment::unknown("nested-recursor-iota-nonconst");
            };
            let Some(reduction) = self.recursor_reductions.get(name) else {
                return Judgment::unknown("nested-recursor-iota-no-qualified-rule");
            };
            if reduction.level_params.len() != levels.len() {
                return Judgment::unknown("nested-recursor-iota-levels");
            }
            let required = reduction.num_params.saturating_add(1)
                .saturating_add(reduction.rules.len())
                .saturating_add(reduction.num_indices)
                .saturating_add(1);
            if neutral.spine.len() < required {
                return Judgment::unknown("nested-recursor-iota-arity");
            }
            #[cfg(feature="diagnostics")]
            if _c94_receipt.is_some() {
                let major=&neutral.spine[required-1];
                c94_counts.last_head.set(name.0);
                c94_counts.last_major_expr.set(major.expr.0);
                c94_counts.last_major_frame.set(major.env.id());
                // A resumed parent already owns its established major; it is
                // not a second demand for the source binding.
                if established_major.is_none()
                    && let Some(Expr::BVar(index))=self.expressions.get(major.expr)
                    && let Some(binding)=major.env.diagnostic_binding_node_id(*index) {
                    c94_counts.bvar_majors.set(c94_counts.bvar_majors.get()+1);
                    if !c94_counts.bvar_bindings.borrow_mut().insert((major.expr,binding)) {
                        c94_counts.bvar_repeats.set(c94_counts.bvar_repeats.get()+1);
                    }
                }
            }
            #[cfg(feature="diagnostics")]
            let mut c112_pending=None;
            let mut major_value=if let Some(value)=established_major.take() { value } else {
                let Some(candidate)=self.completed_replay_key(*name,levels,&neutral.spine) else {return Judgment::unknown("nested-replay-key-work");};
                let mut key=candidate;
                if let Some(bucket)=entered.get(&key.digest) {
                    for saved in bucket {
                        let Some(equal)=self.replay_keys_equal(&key,saved) else {return Judgment::unknown("nested-replay-comparison-work");};
                        if equal {key=saved.clone();break;}
                    }
                }
                let identity=ReplayKey::identity(&key);
                if let Some(value)=resolved.remove(&identity) {
                    #[cfg(feature="diagnostics")]
                    if _c94_receipt.is_some(){c94_counts.local_hits.set(c94_counts.local_hits.get()+1);}
                    finish!('evaluate,value);
                }
                // Interface checks above precede every lookup. A completed
                // value is actual source RHS, never a desired constructor.
                match self.lookup_completed_replay(&key) {
                    Judgment::Proven{value:Some(value),..}=>{
                        #[cfg(feature="diagnostics")]
                        if _c94_receipt.is_some(){c94_counts.global_hits.set(c94_counts.global_hits.get()+1);}
                        #[cfg(feature="diagnostics")]
                        if std::env::var_os("NUCLEUS_TRACE_REPLAY_CACHE").is_some() {
                            use std::sync::atomic::{AtomicUsize,Ordering};
                            static PRINTED:AtomicUsize=AtomicUsize::new(0);
                            if PRINTED.fetch_add(1,Ordering::Relaxed)<32 {eprintln!("NUCLEUS_REPLAY_CACHE:hit:name={name:?}:fuel={:?}",self.exposure_fuel.get());}
                        }
                        finish!('evaluate,value);
                    }
                    Judgment::Proven{value:None,..}=>{},
                    failure=>return failure.map(|_|unreachable!()),
                }
                if !active.insert(identity) {return Judgment::unknown("nested-recursor-iota-cycle");}
                #[cfg(feature="diagnostics")]
                if _c94_receipt.is_some(){c94_counts.entered.set(c94_counts.entered.get()+1);}
                entered.entry(key.digest).or_default().push(key.clone());
                parents.push(Continuation::Finish(key));
                #[cfg(feature="diagnostics")]
                let c96_key=if _c96_receipt.is_some() {
                    let major=&neutral.spine[required-1];
                    let (kind,bound_expr)=match self.expressions.get(major.expr) {
                        Some(Expr::BVar(index))=>match major.env.lookup_binding_ref(*index) {
                            Some(EnvBinding::Closure(bound))=>(0,bound.expr.0),
                            Some(EnvBinding::Neutral(Neutral{head:NeutralHead::Const{name,..},..}))=>(1,name.0),
                            Some(EnvBinding::Neutral(_))=>(2,0),
                            Some(EnvBinding::Free(free))=>(3,free.0),
                            Some(EnvBinding::NatLit(_))=>(4,0),
                            None=>(5,major.expr.0),
                        },
                        _=>(6,major.expr.0),
                    };
                    // Read-only source BVar-to-closure walk: the closure chain
                    // may be shared but has no inferred semantic equality.
                    // Hard cap keeps an adversarial cyclic source bounded.
                    let mut link=major;
                    let mut chain_steps=0;
                    while chain_steps<4096 {
                        let Some(Expr::BVar(index))=self.expressions.get(link.expr) else {break};
                        let Some(EnvBinding::Closure(next))=link.env.lookup_binding_ref(*index) else {break};
                        link=next;
                        chain_steps+=1;
                    }
                    Some(((name.0,kind,bound_expr),chain_steps))
                }else{None};
                #[cfg(feature="diagnostics")]
                let c96_before=self.exposure_fuel.get().unwrap_or(0);
                #[cfg(feature="diagnostics")]
                let c114_before=_c114_receipt.as_ref().map(|_|{
                    let stats=self.c97_steps.borrow();
                    (stats.loops,stats.unique_head_pending,stats.repeat_head_pending,
                     std::array::from_fn::<_,8,_>(|i|
                         stats.kinds.get(&(i as u8)).copied().unwrap_or(0)))
                });
                #[cfg(feature="diagnostics")]
                let c121_before=_c121_receipt.as_ref().map(|_|{
                    let stats=self.c97_steps.borrow();
                    (stats.loops,std::array::from_fn::<_,8,_>(|i|
                        stats.kinds.get(&(i as u8)).copied().unwrap_or(0)))
                });
                #[cfg(feature="diagnostics")]
                let c122_source=_c122_receipt.as_ref()
                    .map(|_|neutral.spine[required-1].clone());
                #[cfg(feature="diagnostics")]
                let c124_heads_before=_c124_receipt.as_ref().map(|_|self.c97_steps.borrow().heads.clone());
                #[cfg(feature="diagnostics")]
                let c115_before=(_c115_receipt.is_some() || _c116_receipt.is_some() || _c117_receipt.is_some() || _c118_receipt.is_some() || _c119_receipt.is_some() || _c120_receipt.is_some())
                    .then(||self.c115_bvar_steps.borrow().len());
                #[cfg(feature="diagnostics")]
                let c117_before=_c117_receipt.as_ref().map(|_|self.c117_completed_calls.borrow().len());
                let major_result={
                    #[cfg(feature="diagnostics")]
                    let _c95_major=_c95_receipt.as_ref().map(|_|C95StageCharge::new(
                        &self.exposure_fuel,&c95_counts.major));
                    #[cfg(feature="diagnostics")]
                    let _c97_activity=(_c97_receipt.is_some() || _c114_receipt.is_some() || _c121_receipt.is_some()).then(||{
                        self.c97_major_active.set(self.c97_major_active.get()+1);
                        C97MajorActivity{active:&self.c97_major_active}
                    });
                    #[cfg(feature="diagnostics")]
                    let _c115_activity=(_c115_receipt.is_some() || _c116_receipt.is_some() || _c117_receipt.is_some() || _c118_receipt.is_some() || _c119_receipt.is_some() || _c120_receipt.is_some()).then(||{
                        self.c115_major_active.set(self.c115_major_active.get()+1);
                        C115MajorActivity{active:&self.c115_major_active}
                    });
                    if self.replay_projection_major {
                        self.expose_for_conversion(neutral.spine[required-1].clone(),
                            Transparency::Full,self.exposure_fuel.get().unwrap_or(0).min(512))
                    } else {
                        self.expose(neutral.spine[required-1].clone(),
                            Transparency::Full,self.exposure_fuel.get().unwrap_or(0).min(512))
                    }
                };
                #[cfg(feature="diagnostics")]
                if let Some((before_loops,before_unique,before_repeat,before_kinds))=c114_before {
                    let charged=c96_before.saturating_sub(self.exposure_fuel.get().unwrap_or(0));
                    if charged>=512 && matches!(&major_result,Judgment::Proven{value:Value::Neutral(n),..}
                        if matches!(&n.head,NeutralHead::Const{name,..}
                            if reduction.rules.iter().any(|r|r.constructor==*name
                                && n.spine.len()==r.num_params+r.num_fields))) {
                        let stats=self.c97_steps.borrow();
                        let kinds=std::array::from_fn(|i|stats.kinds.get(&(i as u8))
                            .copied().unwrap_or(0).saturating_sub(before_kinds[i]));
                        c114_counts.borrow_mut().events.push(C114HighEvent{
                            major:charged,
                            loops:stats.loops.saturating_sub(before_loops),
                            unique:stats.unique_head_pending.saturating_sub(before_unique),
                            repeat:stats.repeat_head_pending.saturating_sub(before_repeat),
                            kinds,
                        });
                    }
                }
                #[cfg(feature="diagnostics")]
                if let Some((before_loops,before_kinds))=c121_before {
                    let charged=c96_before.saturating_sub(self.exposure_fuel.get().unwrap_or(0));
                    if (128..512).contains(&charged) {
                        let (outcome,constructor,rhs)=match &major_result {
                            Judgment::Unknown{..}=>(3,0,0),
                            Judgment::Refuted{..}=>(4,0,0),
                            Judgment::Proven{value:Value::Neutral(n),..}=>{
                                let source=match &n.head {NeutralHead::Const{name,..}=>Some(*name),_=>None};
                                if source.is_some_and(|candidate|self.recursor_reductions.contains_key(&candidate)) {
                                    (1,0,0)
                                } else if let Some((actual,rule))=source.and_then(|actual|
                                    reduction.rules.iter().find(|r|r.constructor==actual &&
                                        n.spine.len()==r.num_params+r.num_fields).map(|r|(actual,r))) {
                                    (0,actual.0,rule.rhs.0)
                                } else {(2,0,0)}
                            }
                            Judgment::Proven{..}=>(2,0,0),
                        };
                        let stats=self.c97_steps.borrow();
                        let kinds=std::array::from_fn(|i|stats.kinds.get(&(i as u8))
                            .copied().unwrap_or(0).saturating_sub(before_kinds[i]));
                        c121_counts.borrow_mut().events.push(C121MidEvent{
                            recursor:name.0,rhs,constructor,charge:charged,
                            loops:stats.loops.saturating_sub(before_loops),
                            depth,major_parents:parents.iter().filter(|p|
                                matches!(p,Continuation::Major(..))).count(),
                            requested:usize::from(current_is_requested),outcome,kinds,
                        });
                    }
                }
                #[cfg(feature="diagnostics")]
                if let Some(source)=c122_source {
                    let charged=c96_before.saturating_sub(self.exposure_fuel.get().unwrap_or(0));
                    if (128..512).contains(&charged)
                        && let Judgment::Proven{value:Value::Neutral(nested),..}=&major_result
                        && let NeutralHead::Const{name:next_name,..}=&nested.head
                        && let Some(next_reduction)=self.recursor_reductions.get(next_name) {
                        let next_required=next_reduction.num_params.saturating_add(1)
                            .saturating_add(next_reduction.rules.len())
                            .saturating_add(next_reduction.num_indices)
                            .saturating_add(1);
                        let inspect=|closure:&Closure| {
                            let (kind,index)=match self.expressions.get(closure.expr) {
                                Some(Expr::BVar(i))=>(0,Some(*i)),
                                Some(Expr::Const{..})=>(1,None),
                                Some(Expr::App{..})=>(2,None),
                                Some(Expr::Lam{..})=>(3,None),
                                Some(Expr::Pi{..})=>(4,None),
                                Some(Expr::Let{..})=>(5,None),
                                Some(Expr::Proj{..})=>(6,None),
                                Some(Expr::Sort(..))=>(7,None),
                                Some(Expr::NatLit(..))=>(8,None),
                                Some(Expr::StrLit(..))=>(9,None),
                                None=>(10,None),
                            };
                            let binding=index.and_then(|i|
                                closure.env.diagnostic_binding_node_id(i)).unwrap_or(0);
                            let (bound_expr,bound_env)=index.and_then(|i|
                                closure.env.lookup_binding_ref(i)).and_then(|v|
                                    match v {EnvBinding::Closure(c)=>Some((c.expr.0,c.env.id())),_=>None})
                                .unwrap_or((0,0));
                            (closure.expr.0,closure.env.id(),kind,binding,bound_expr,bound_env)
                        };
                        let (expr,env,expr_kind,binding,bound_expr,bound_env)=inspect(&source);
                        let next_major=nested.spine.get(next_required.saturating_sub(1));
                        let (next_expr,next_env,next_expr_kind,next_binding,next_bound_expr,next_bound_env)=
                            next_major.map(&inspect).unwrap_or((0,0,10,0,0,0));
                        c122_events.borrow_mut().push(C122SourceEvent{
                            seq:c121_counts.borrow().events.len(),recursor:name.0,
                            expr,env,expr_kind,binding,bound_expr,bound_env,
                            next_head:next_name.0,next_arity:usize::from(next_major.is_some()),
                            next_expr,next_env,next_expr_kind,next_binding,
                            next_bound_expr,next_bound_env,
                        });
                        if _c123_receipt.is_some() {
                            let mut link=&source;
                            let mut hops=0usize;
                            while hops<4096 {
                                let Some(Expr::BVar(index))=self.expressions.get(link.expr) else {break};
                                let Some(EnvBinding::Closure(next))=link.env.lookup_binding_ref(*index) else {break};
                                link=next;
                                hops+=1;
                            }
                            let (terminal_expr,terminal_env,terminal_kind,_,_,_)=inspect(link);
                            let (terminal_bvar,terminal_binding_kind)=
                                if let Some(Expr::BVar(index))=self.expressions.get(link.expr) {
                                    let kind=if hops==4096 {6} else {
                                        match link.env.lookup_binding_ref(*index) {
                                            Some(EnvBinding::Closure(_))=>0,
                                            Some(EnvBinding::Free(_))=>1,
                                            Some(EnvBinding::Neutral(_))=>2,
                                            Some(EnvBinding::NatLit(_))=>3,
                                            None=>4,
                                        }
                                    };
                                    (*index,kind)
                                } else {(0,5)};
                            c123_events.borrow_mut().push(C123BVarChainEvent{
                                seq:c121_counts.borrow().events.len(),hops,
                                terminal_expr,terminal_env,terminal_kind,
                                terminal_bvar,terminal_binding_kind,
                                capped:usize::from(hops==4096),
                                levels:link.levels.entries().count(),
                            });
                        }
                        if let Some(before)=c124_heads_before.as_ref() {
                            // Traverse original immutable AST edges only; these
                            // are not beta reductions or a rewritten closure.
                            let mut link=&source;
                            for _ in 0..4096 {
                                let Some(Expr::BVar(index))=self.expressions.get(link.expr) else {break};
                                let Some(EnvBinding::Closure(next))=link.env.lookup_binding_ref(*index) else {break};
                                link=next;
                            }
                            let mut head_expr=link.expr;
                            let mut args=Vec::new();
                            while args.len()<128 {
                                let Some(Expr::App{fun,arg})=self.expressions.get(head_expr) else {break};
                                args.push(*arg);
                                head_expr=*fun;
                            }
                            let (_,_,head_kind,head_binding,head_bound_expr,head_bound_env)=
                                inspect(&link.sibling(head_expr,link.env.clone()));
                            let arg_info=|idx:usize|{
                                let Some(expr)=args.get(idx).copied() else{return (0,10,0)};
                                let (_,_,kind,_,_,_)=inspect(&link.sibling(expr,link.env.clone()));
                                let body=match self.expressions.get(expr) {
                                    Some(Expr::Lam{body,..})=>body.0,
                                    _=>0,
                                };
                                (expr.0,kind,body)
                            };
                            let (outer_arg,outer_kind,outer_body)=arg_info(0);
                            let (inner_arg,inner_kind,inner_body)=arg_info(1);
                            let stats=self.c97_steps.borrow();
                            let (mut app,mut lam,mut top_app,mut top_lam)=(0,0,(0,0),(0,0));
                            for (&(kind,expr),&count) in stats.heads.iter() {
                                if kind!=1 && kind!=2 {continue;}
                                let delta=count.saturating_sub(before.get(&(kind,expr)).copied().unwrap_or(0));
                                let (total,top)=if kind==1 {(&mut app,&mut top_app)} else {(&mut lam,&mut top_lam)};
                                *total+=delta;
                                if delta>top.1 || (delta==top.1 && expr<top.0) {*top=(expr,delta);}
                            }
                            let root_app=stats.heads.get(&(1,link.expr.0)).copied().unwrap_or(0)
                                .saturating_sub(before.get(&(1,link.expr.0)).copied().unwrap_or(0));
                            c124_events.borrow_mut().push(C124AppProfileEvent{
                                seq:c121_counts.borrow().events.len(),root:link.expr.0,env:link.env.id(),
                                arity:args.len(),head:head_expr.0,head_kind,
                                head_binding,head_bound_expr,head_bound_env,
                                outer_arg,inner_arg,outer_kind,inner_kind,outer_body,inner_body,
                                app,lam,root_app,top_app:top_app.0,top_app_count:top_app.1,
                                top_lam:top_lam.0,top_lam_count:top_lam.1,
                            });
                        }
                    }
                }
                #[cfg(feature="diagnostics")]
                if let Some(before)=c115_before {
                    let charged=c96_before.saturating_sub(self.exposure_fuel.get().unwrap_or(0));
                    if charged>=512 && matches!(&major_result,Judgment::Proven{value:Value::Neutral(n),..}
                        if matches!(&n.head,NeutralHead::Const{name,..}
                            if reduction.rules.iter().any(|r|r.constructor==*name
                                && n.spine.len()==r.num_params+r.num_fields))) {
                        let steps=self.c115_bvar_steps.borrow();
                        if _c115_receipt.is_some() {c115_counts.borrow_mut().record(&steps[before..]);}
                        if _c116_receipt.is_some() {c116_counts.borrow_mut().record(&steps[before..]);}
                        if let Some(start)=c117_before {
                            let calls=self.c117_completed_calls.borrow();
                            c117_counts.borrow_mut().record(&calls[start..],&steps[before..]);
                        }
                        if _c118_receipt.is_some() {
                            c118_counts.borrow_mut().record(&steps[before..]);
                        }
                        if _c119_receipt.is_some() {
                            c119_counts.borrow_mut().record(&steps[before..]);
                        }
                        if _c120_receipt.is_some() {
                            c120_counts.borrow_mut().record(&steps[before..]);
                        }
                    }
                    // Retain nested major observations for their parent's inclusive
                    // slice, but release the complete stream at its outer boundary.
                    if self.c115_major_active.get()==0 {
                        self.c115_bvar_steps.borrow_mut().clear();
                        if _c117_receipt.is_some() {self.c117_completed_calls.borrow_mut().clear();}
                    }
                }
                #[cfg(feature="diagnostics")]
                if let Some((key,chain_steps))=c96_key {
                    let spent=c96_before.saturating_sub(self.exposure_fuel.get().unwrap_or(0));
                    let nested=matches!(major_result.proven_value(),
                        Some(Value::Neutral(n)) if matches!(&n.head,
                        NeutralHead::Const{name,..}if self.recursor_reductions.contains_key(name)));
                    c96_counts.record(key,spent,major_result.is_unknown(),nested,chain_steps);
                }
                #[cfg(feature="diagnostics")]
                if _c104_receipt.is_some() {
                    let spent=c96_before.saturating_sub(self.exposure_fuel.get().unwrap_or(0));
                    let result=major_result.proven_value();
                    let nested=matches!(result,
                        Some(Value::Neutral(n)) if matches!(&n.head,
                            NeutralHead::Const{name,..} if self.recursor_reductions.contains_key(name)));
                    c104_counts.borrow_mut().record(&neutral.spine[required-1],
                        spent,result.is_some(),nested);
                }
                #[cfg(feature="diagnostics")]
                if _c111_receipt.is_some() {
                    let spent=c96_before.saturating_sub(self.exposure_fuel.get().unwrap_or(0));
                    let (kind,reason)=match &major_result {
                        Judgment::Unknown{residual}=>(3,Some(residual.0)),
                        Judgment::Refuted{obstruction}=>(4,Some(obstruction.0)),
                        Judgment::Proven{value:Value::Neutral(n),..}
                            if matches!(&n.head,NeutralHead::Const{name,..}
                                if self.recursor_reductions.contains_key(name))=>(1,None),
                        Judgment::Proven{value:Value::Neutral(n),..}
                            if matches!(&n.head,NeutralHead::Const{name,..}
                                if reduction.rules.iter().any(|r|
                                    r.constructor==*name && n.spine.len()==r.num_params+r.num_fields))=>(0,None),
                        Judgment::Proven{..}=>(2,None),
                    };
                    c111_counts.borrow_mut().record(name.0,spent,kind,reason);
                }
                #[cfg(feature="diagnostics")]
                if (_c112_receipt.is_some() || _c113_receipt.is_some())
                    && matches!(&major_result,Judgment::Proven{value:Value::Neutral(n),..}
                        if matches!(&n.head,NeutralHead::Const{name,..}
                            if reduction.rules.iter().any(|r|r.constructor==*name
                                && n.spine.len()==r.num_params+r.num_fields))) {
                    if _c112_receipt.is_some() {
                        c112_counts.borrow_mut().constructor_results+=1;
                    }
                    c112_pending=Some((
                        c96_before.saturating_sub(self.exposure_fuel.get().unwrap_or(0)),
                        depth,parents.iter().filter(|p|matches!(p,Continuation::Major(..))).count(),
                        current_is_requested,
                    ));
                }
                #[cfg(feature="diagnostics")]
                if _c105_receipt.is_some() || _c106_receipt.is_some() || _c109_receipt.is_some() || _c110_receipt.is_some() {
                    // The same real immutable BVar closure chain audited by
                    // C96. This read-only walk neither exposes a value nor
                    // changes any source constructor/replay/fuel decision.
                    let mut terminal=neutral.spine[required-1].clone();
                    let mut steps=0usize;
                    while steps<16 {
                        let Some(Expr::BVar(index))=self.expressions.get(terminal.expr) else {break};
                        let Some(EnvBinding::Closure(next))=terminal.env.lookup_binding_ref(*index) else {break};
                        terminal=next.clone();
                        steps+=1;
                    }
                    let spent=c96_before.saturating_sub(self.exposure_fuel.get().unwrap_or(0));
                    let proven=major_result.proven_value().is_some();
                    if _c105_receipt.is_some() {
                        c105_counts.borrow_mut().record(terminal.clone(),steps,steps==16,
                            spent,proven);
                    }
                    if _c106_receipt.is_some() {
                        c106_counts.borrow_mut().record(&terminal,spent,proven);
                    }
                    if _c109_receipt.is_some() {
                        c109_counts.borrow_mut().record(&terminal,spent,self.expressions);
                    }
                    if _c110_receipt.is_some() {
                        c110_counts.borrow_mut().record(&terminal,spent,self.expressions);
                    }
                }
                #[cfg(feature="diagnostics")]
                if _c97_receipt.is_some() {
                    let spent=c96_before.saturating_sub(self.exposure_fuel.get().unwrap_or(0));
                    self.c97_steps.borrow_mut().major_work+=spent;
                }
                let Some(value)=major_result.proven_value() else {
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_NESTED_RECURSOR_IOTA_FAILURE").is_some() {
                        eprintln!("NUCLEUS_NESTED_REPLAY_FAILURE:depth={depth}:head={name:?}:major={major_result:?}:fuel={:?}",self.exposure_fuel.get());
                    }
                    return Judgment::unknown("nested-recursor-iota-major-exposure");
                };
                if let Value::Neutral(nested)=value
                    && matches!(&nested.head,NeutralHead::Const{name,..} if self.recursor_reductions.contains_key(name))
                {
                    parents.push(Continuation::Major(current.clone(),current_is_requested));
                    current=nested.clone();current_is_requested=false;
                    continue;
                }
                value.clone()
            };
            if self.replay_projection_major {
                // Preserve the actual source projection while demanding a
                // constructor. Select only a registered field of the actual
                // source constructor; no desired result chooses a rule.
                // Recursive exposures and replays share this work owner's fuel.
                for _ in 0..16 {
                    if !spend(){return Judgment::unknown("projection-major-replay-budget");}
                    let next=match &major_value {
                        Value::StuckProjection{type_name,index,structure,spine}=>{
                            self.projection_value_for_conversion(
                                structure.clone(),*type_name,*index,spine,
                                self.exposure_fuel.get().unwrap_or(0),
                            )
                        }
                        Value::Neutral(nested) if self.replay_neutral_projection && matches!(&nested.head,NeutralHead::Projection{..})=>{
                            self.checked_neutral_projection_result(nested,self.exposure_fuel.get().unwrap_or(0))
                        }
                        Value::Neutral(nested) if matches!(&nested.head,
                            NeutralHead::Const{name,..}if self.recursor_reductions.contains_key(name))=>{
                            parents.push(Continuation::Major(current.clone(),current_is_requested));
                            current=nested.clone();current_is_requested=false;
                            continue 'evaluate;
                        }
                        _=>break,
                    };
                    let Some(value)=next.proven_value()else {
                        return Judgment::unknown("projection-major-source-field-unavailable");
                    };
                    if value==&major_value {
                        return Judgment::unknown("projection-major-source-nonprogress");
                    }
                    major_value=value.clone();
                }
            }
            let (constructor, constructor_levels, constructor_args) = match major_value {
                Value::Neutral(Neutral { head: NeutralHead::Const { name, levels }, spine }) => (name,levels,spine),
                Value::NatLit(number) => {
                    let Some(nat) = self.nat_primitives.as_ref() else {return Judgment::unknown("nested-Nat-iota-no-authority")};
                    if *name != nat.recursor || reduction.k || reduction.num_params != 0 || reduction.num_indices != 0
                        || reduction.level_params.len() != 1 || reduction.rules.len() != 2
                        || !reduction.rules.iter().any(|r|r.constructor==nat.zero && r.num_params==0 && r.num_fields==0 && r.constructor_level_params.is_empty())
                        || !reduction.rules.iter().any(|r|r.constructor==nat.succ && r.num_params==0 && r.num_fields==1 && r.constructor_level_params.is_empty())
                    {return Judgment::unknown("nested-Nat-iota-interface");}
                    if number.is_zero() {(nat.zero,vec![],vec![])} else {
                        let Some(field)=self.native_nat_predecessor(&number,self.exposure_fuel.get().unwrap_or(0)) else {return Judgment::unknown("nested-Nat-iota-predecessor-work-or-carrier");};
                        (nat.succ,vec![],vec![field])
                    }
                }
                _=>return Judgment::unknown("nested-recursor-iota-no-constructor"),
            };
            let Some(rule) = reduction.rules.iter().find(|rule| {
                rule.constructor == constructor
                    && constructor_args.len() == rule.num_params + rule.num_fields
            }) else {
                return Judgment::unknown("nested-recursor-iota-unmatched-rule");
            };
            // Check the actual constructor's universe instantiation against
            // the rule declared in the same certified recursor interface.
            if rule.constructor_level_params.len() != constructor_levels.len() {
                return Judgment::unknown("nested-recursor-iota-constructor-level-arity");
            }
            for (parameter, actual) in rule.constructor_level_params.iter().zip(&constructor_levels) {
                let Some(index) = reduction.level_params.iter().position(|name| name == parameter) else {
                    return Judgment::unknown("nested-recursor-iota-constructor-level-map");
                };
                if levels[index] != *actual {
                    return Judgment::unknown("nested-recursor-iota-constructor-level-mismatch");
                }
            }
            let substitution = reduction.level_params.iter().copied()
                .zip(levels.iter().cloned()).collect::<Vec<_>>();
            let mut result = Closure::with_levels(
                rule.rhs, EnvFrame::empty(), LevelSubstitution::new(substitution),
            );
            let prefix_len = reduction.num_params + 1 + reduction.rules.len();
            let mut arguments = neutral.spine[..prefix_len].to_vec();
            arguments.extend(constructor_args[rule.num_params..].iter().cloned());

            // The RHS is the independently checked recursor rule. Consume
            // exactly its declared binders. Unknown shapes do not grant iota.
            #[cfg(feature="diagnostics")]
            let _c95_telescope=_c95_receipt.as_ref().map(|_|C95StageCharge::new(
                &self.exposure_fuel,&c95_counts.telescope));
            #[cfg(feature="diagnostics")]
            let c113_telescope_before=self.exposure_fuel.get().unwrap_or(0);
            for arg in arguments {
                if !spend() { return Judgment::unknown("nested-recursor-iota-budget"); }
                let mut lets = 0usize;
                loop {
                    match self.expressions.get(result.expr) {
                        Some(Expr::Lam { body, .. }) => {
                            result = result.sibling(*body, self.bind_captured_argument(&result,arg.clone()));
                            break;
                        }
                        Some(Expr::Let { value, body, .. }) if lets < 16 => {
                            if !spend() { return Judgment::unknown("nested-recursor-iota-budget"); }
                            let value = result.sibling(*value, result.env.clone());
                            result = result.sibling(*body, self.bind_captured_argument(&result,value));
                            lets += 1;
                        }
                        _ => return Judgment::unknown("nested-recursor-iota-rhs-telescope"),
                    }
                }
            }
            #[cfg(feature="diagnostics")]
            drop(_c95_telescope);
            #[cfg(feature="diagnostics")]
            let c113_rhs_before=self.exposure_fuel.get().unwrap_or(0);
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_NESTED_RECURSOR_IOTA").is_some() {
                use std::sync::atomic::{AtomicUsize, Ordering};
                static PRINTED: AtomicUsize = AtomicUsize::new(0);
                if PRINTED.fetch_add(1, Ordering::Relaxed) < 32 {
                    eprintln!(
                        "NUCLEUS_NESTED_RECURSOR_IOTA:depth={depth}:recursor={name:?}:constructor={constructor:?}:rule_fields={}:source_rhs={:?}",
                        rule.num_fields,rule.rhs
                    );
                }
            }
            let exposed={
                #[cfg(feature="diagnostics")]
                let _c95_rhs=_c95_receipt.as_ref().map(|_|C95StageCharge::new(
                    &self.exposure_fuel,&c95_counts.rhs));
                self.expose_internal_with_pending(
                    result, Transparency::Full, self.exposure_fuel.get().unwrap_or(0).min(512),
                    false, true, neutral.spine[required..].iter().rev().cloned().collect(),
                ).map(|exposure| exposure.value)
            };
            #[cfg(feature="diagnostics")]
            if let Some((charge,major_depth,major_parents,requested))=c112_pending.take() {
                let outcome=match &exposed {
                    Judgment::Proven{value:Value::Neutral(n),..}
                        if matches!(&n.head,NeutralHead::Const{name,..}
                            if self.recursor_reductions.contains_key(name))=>"nested",
                    Judgment::Proven{value:Value::Neutral(n),..}
                        if matches!(&n.head,NeutralHead::Const{..})=>"constructor",
                    Judgment::Proven{..}=>"other",
                    _=>"unknown",
                };
                if _c112_receipt.is_some() {
                    c112_counts.borrow_mut().record(name.0,constructor.0,rule.rhs.0,
                        charge,major_depth,major_parents,requested,outcome);
                }
                if _c113_receipt.is_some() && charge>=512 {
                    let mut counts=c113_counts.borrow_mut();
                    let index=counts.events.len();
                    counts.events.push(C113HighEvent{
                        recursor:name.0,constructor:constructor.0,rhs:rule.rhs.0,
                        major:charge,
                        telescope:c113_telescope_before.saturating_sub(c113_rhs_before),
                        rhs_work:c113_rhs_before.saturating_sub(self.exposure_fuel.get().unwrap_or(0)),
                        depth:major_depth,major_parents,resumed:false,
                    });
                    if outcome=="constructor" && !requested && major_parents>0 {
                        c113_awaiting_resume=Some(index);
                    }
                }
            }
            let value=match exposed {
                Judgment::Proven{value,..}=>value,
                failure=>{
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_NESTED_RECURSOR_IOTA_FAILURE").is_some() {
                        eprintln!("NUCLEUS_NESTED_REPLAY_FAILURE:depth={depth}:head={name:?}:rhs={failure:?}:fuel={:?}",self.exposure_fuel.get());
                    }
                    return failure;
                }
            };
            // Only the requested term may stop after its actual checked iota.
            // A child needed to establish its major must still finish to a
            // constructor. Partial results bypass every completed memo.
            if goal==CheckedReplayGoal::OneStep && current_is_requested {
                return Judgment::proven(value,"checked-one-step-source-recursor-iota");
            }
            // A selected rule may return another captured registered recursor.
            // Establish that result before using it as a parent's constructor.
            if let Value::Neutral(nested)=&value
                && matches!(&nested.head,NeutralHead::Const{name,..} if self.recursor_reductions.contains_key(name))
            {
                current=nested.clone();current_is_requested=false;
                continue;
            }
            finish!('evaluate,value);
        }
    }

    fn rule_constructor_application(
        &self,
        target: &Closure,
        reduction: &RecursorReduction,
        transparency: Transparency,
        budget: usize,
    ) -> Option<(NameId, Vec<Closure>)> {
        let matches_rule = |constructor: NameId, arity: usize| {
            reduction.rules.iter().any(|rule| {
                rule.constructor == constructor
                    && arity == rule.num_params + rule.num_fields
            })
        };
        if let Some((constructor, arguments)) = self.constructor_application(target)
            && matches_rule(constructor, arguments.len())
        {
            return Some((constructor, arguments));
        }
        // Only a new constructor demand owns shared fuel. Ordinary beta
        // exposure keeps its established budget semantics; recursive major
        // demands share and decrease this exact owner's budget.
        let _constructor_fuel = if self.demand_major && self.exposure_fuel.get().is_none() {
            self.exposure_fuel.set(Some(budget));
            Some(ConstructorFuelScope { fuel: &self.exposure_fuel })
        } else { None };
        // Iota is independent of delta transparency. Expose the exact major
        // using the caller's policy, so native literals and beta/zeta majors
        // can select checked rules even when definition unfolding is opaque.
        // A checked Bool recursor may receive its computed major through
        // captured beta/zeta bindings. The bounded probe must still expose
        // the exact registered constructor; syntax shape selects no branch.
        let bool_rules = self.bool_primitives.as_ref().is_some_and(|bools| {
            reduction.rules.len() == 2
                && reduction.rules.iter().any(|r| r.constructor == bools.false_ctor)
                && reduction.rules.iter().any(|r| r.constructor == bools.true_ctor)
        });
        let certified_nat_rec = self.nat_primitives.as_ref().is_some_and(|nat| {
            reduction.rules.len() == 2
                && matches_rule(nat.zero, 0)
                && matches_rule(nat.succ, 1)
        });
        let major_cap = if bool_rules {
            256
        } else if certified_nat_rec {
            128
        } else {
            128
        };
        let exposed = self
            .expose_internal(
                target.clone(),
                transparency,
                if self.demand_major { budget.saturating_sub(1) } else { budget.saturating_sub(1).min(major_cap) },
                false,
                false,
            )
            .proven_value()?
            .value
            .clone();
        match exposed {
            Value::Neutral(Neutral {
                head: NeutralHead::Const { name, .. },
                spine,
            }) if matches_rule(name, spine.len()) => Some((name, spine)),
            // Lean's trusted Nat numeral representation is definitionally
            // constructor-shaped. A recursor with independently installed
            // Nat.zero/Nat.succ iota rules may inspect that exact numeral.
            // Carry the exact native predecessor through a verified source
            // carrier without scanning the export for a matching numeral.
            Value::NatLit(number) => {
                let nat = self.nat_primitives.as_ref()?;
                if std::env::var_os("NUCLEUS_TRACE_NAT_IOTA").is_some() { eprintln!("NUCLEUS_NAT_LITERAL_IOTA:major={number:?}:zero_rule={}:succ_rule={}", matches_rule(nat.zero,0), matches_rule(nat.succ,1)); }
                if number.is_zero() && matches_rule(nat.zero, 0) {
                    return Some((nat.zero, Vec::new()));
                }
                if !matches_rule(nat.succ, 1) {
                    return None;
                }
                let predecessor_closure=self.native_nat_predecessor(&number,budget)?;
                Some((nat.succ, vec![predecessor_closure]))
            }
            _ => None,
        }
    }

    fn resolve_level(
        &self,
        level: LevelId,
        closure: &Closure,
        budget: usize,
    ) -> Option<crate::level::LevelTerm> {
        instantiate_level(self.levels, level, &closure.levels, budget).ok()
    }
}

fn permits_delta(transparency: Transparency, preferred_for_reduction: bool) -> bool {
    match transparency {
        Transparency::Opaque => false,
        Transparency::Reducible => preferred_for_reduction,
        Transparency::Full => true,
    }
}

fn append_pending(spine: &mut Vec<Closure>, pending: &mut Vec<Closure>) {
    while let Some(argument) = pending.pop() {
        spine.push(argument);
    }
}

#[inline]
fn record_transition(
    transitions: &mut Vec<TransitionWitness>,
    enabled: bool,
    witness: TransitionWitness,
) {
    if enabled {
        transitions.push(witness);
    }
}

fn exposed(value: Value, transitions: Vec<TransitionWitness>) -> Judgment<Exposure> {
    Judgment::proven(Exposure { value, transitions }, "explicit-closure-machine")
}

#[cfg(test)]
mod neutral_projection_tests {
    use super::*;

    #[test]
    fn projection_conversion_preserves_a_constant_neutral_receiver() {
        let mut expressions = IdTable::default();
        let levels = IdTable::default();
        expressions.insert(ExprId(0), Expr::Const { name: NameId(3), levels: vec![] }).unwrap();
        expressions.insert(ExprId(1), Expr::BVar(0)).unwrap();
        let machine = Machine::new(AuthorityId(1), &expressions, &levels, HashMap::new())
            .with_projection_specs(HashMap::from([(NameId(1), ProjectionSpec {
                constructor: NameId(2), num_params: 0,
                field_types: vec![ProjectionFieldType::Derived(ExprId(1))],
                eta_expandable: false,
            })]));
        let receiver = Closure::new(ExprId(0), EnvFrame::empty());
        let argument = Closure::new(ExprId(1), EnvFrame::empty().extend_free(FreeId(0)));
        let result = machine.projection_value_for_conversion(receiver.clone(), NameId(1), 0, &[argument.clone()], 128);
        let Some(Value::Neutral(Neutral { head: NeutralHead::Projection { type_name, index, structure }, spine })) = result.proven_value() else {
            panic!("legitimate neutral receiver projection was discarded: {result:?}");
        };
        assert_eq!((*type_name, *index), (NameId(1), 0));
        assert_eq!(structure.head, NeutralHead::Const { name: NameId(3), levels: vec![] });
        assert_eq!(spine, &[argument]);
        assert!(machine.projection_value_for_conversion(receiver.clone(), NameId(1), 1, &[], 128).is_unknown());
        assert!(machine.projection_value_for_conversion(receiver, NameId(9), 0, &[], 128).is_unknown());
    }
}

#[cfg(test)]
mod checked_one_step_replay_tests {
    use super::*;
    use crate::{parser::parse,syntax::Declaration,level::LevelTerm};
    use std::io::Cursor;
    #[test]
    fn actual_field_enum_iota_can_return_a_symbolic_registered_recursor_without_completing_it() {
        let fixture=include_bytes!("../tests/fixtures/good-closed-field-enum.ndjson");
        assert_eq!(crate::run(Cursor::new(fixture)),crate::verdict::Verdict::Accept);
        let mut export=parse(Cursor::new(fixture)).unwrap().resolve().unwrap();
        let blocks=export.declarations.iter().filter_map(|d|if let Declaration::Inductive(b)=d{Some(b.clone())}else{None}).collect::<Vec<_>>();
        let nat=&blocks[0];let enumeration=&blocks[1];let natrec=&nat.recursors[0];let enumrec=&enumeration.recursors[0];
        let mut rules=HashMap::new();
        for block in &blocks {for rec in &block.recursors {
            rules.insert(rec.name,RecursorReduction{k:rec.k,num_params:rec.num_params as usize,num_indices:rec.num_indices as usize,
                level_params:rec.level_params.clone(),rules:rec.rules.iter().map(|r|{
                    let constructor=block.constructors.iter().find(|c|c.name==r.constructor).unwrap();
                    RecursorRule{constructor:r.constructor,constructor_level_params:constructor.level_params.clone(),num_params:constructor.num_params as usize,num_fields:r.num_fields as usize,rhs:r.rhs}
                }).collect()});
        }}
        let nat_type=export.exprs.iter_raw().find_map(|(id,e)|matches!(e,Expr::Const{name,levels} if *name==nat.types[0].name && levels.is_empty()).then_some(ExprId(id))).unwrap();
        let enum_type=export.exprs.iter_raw().find_map(|(id,e)|matches!(e,Expr::Const{name,levels} if *name==enumeration.types[0].name && levels.is_empty()).then_some(ExprId(id))).unwrap();
        let zero_level=export.levels.iter_raw().find_map(|(id,l)|matches!(l,Level::Zero).then_some(LevelId(id))).unwrap();
        let level=LevelId(1000);export.levels.insert(level,Level::Succ(zero_level)).unwrap();
        let mut insert=|id,e|{export.exprs.insert(ExprId(id),e).unwrap();ExprId(id)};
        let variable=insert(1000,Expr::BVar(0));
        let motive=insert(1001,Expr::Lam{domain:nat_type,body:nat_type});
        let zero=insert(1002,Expr::Const{name:nat.constructors[0].name,levels:vec![]});
        let step_inner=insert(1003,Expr::Lam{domain:nat_type,body:variable});
        let step=insert(1004,Expr::Lam{domain:nat_type,body:step_inner});
        let head=insert(1005,Expr::Const{name:natrec.name,levels:vec![level]});
        let first=insert(1006,Expr::App{fun:head,arg:motive});
        let second=insert(1007,Expr::App{fun:first,arg:zero});
        let third=insert(1008,Expr::App{fun:second,arg:step});
        let body=insert(1009,Expr::App{fun:third,arg:variable});
        let minor=insert(1010,Expr::Lam{domain:nat_type,body});
        let constructor=insert(1011,Expr::Const{name:enumeration.constructors[0].name,levels:vec![]});
        let major=insert(1012,Expr::App{fun:constructor,arg:variable});
        let enum_motive=insert(1013,Expr::Lam{domain:enum_type,body:nat_type});
        let child_body=insert(1100,Expr::App{fun:constructor,arg:variable});
        let child_minor=insert(1101,Expr::Lam{domain:nat_type,body:child_body});
        let previous=insert(1102,Expr::BVar(1));
        let child_two_body=insert(1103,Expr::App{fun:constructor,arg:previous});
        let child_inner=insert(1104,Expr::Lam{domain:nat_type,body:child_two_body});
        let child_two=insert(1105,Expr::Lam{domain:nat_type,body:child_inner});
        let child_motive=insert(1106,Expr::Lam{domain:enum_type,body:enum_type});
        let cache=new_exposure_cache();
        let machine=Machine::new(AuthorityId(1),&export.exprs,&export.levels,HashMap::new()).with_recursor_reductions(rules.clone()).with_exposure_cache(cache.clone());
        let closed=|id|Closure::new(id,EnvFrame::empty());
        let input=Neutral{head:NeutralHead::Const{name:enumrec.name,levels:vec![crate::level::succ(LevelTerm::Zero)]},
            spine:vec![closed(enum_motive),closed(minor),closed(step),Closure::new(major,EnvFrame::empty().extend_free(FreeId(0)))]};
        assert!(machine.qualified_nested_recursor_result(&input,512).is_unknown());
        let actual=machine.qualified_one_step_recursor_result(&input,512);
        assert!(matches!(actual.proven_value(),Some(Value::Neutral(n)) if matches!(&n.head,NeutralHead::Const{name,..} if *name==natrec.name) && n.spine.len()==4),"valid source iota was lost while completing its symbolic result: {actual:?}");
        let Some(Value::Neutral(returned))=actual.proven_value() else {panic!("expected actual retained source recursor")};
        assert!(matches!(machine.expose(returned.spine[3].clone(),Transparency::Full,128).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Free(FreeId(0)),..}))));
        let mut unknown=input.clone();
        unknown.spine[3]=Closure::new(variable,EnvFrame::empty().extend_free(FreeId(99)));
        assert!(machine.qualified_one_step_recursor_result(&unknown,512).is_unknown());
        let mut missing_field=input.clone();missing_field.spine[3]=closed(constructor);
        assert!(machine.qualified_one_step_recursor_result(&missing_field,512).is_unknown());
        let mut wrong_levels=input.clone();
        wrong_levels.head=NeutralHead::Const{name:enumrec.name,levels:vec![LevelTerm::Zero,LevelTerm::Zero]};
        assert!(machine.qualified_one_step_recursor_result(&wrong_levels,512).is_unknown());
        let mut wrong_ctor_levels=input.clone();
        wrong_ctor_levels.spine[3]=Closure::new(variable,EnvFrame::empty().extend_neutral(Neutral{head:NeutralHead::Const{name:enumeration.constructors[0].name,levels:vec![LevelTerm::Zero]},spine:vec![closed(zero)]}));
        assert!(machine.qualified_one_step_recursor_result(&wrong_ctor_levels,512).is_unknown());
        let mut malformed_rules=rules.clone();malformed_rules.get_mut(&enumrec.name).unwrap().rules[0].rhs=zero;
        let malformed=Machine::new(AuthorityId(1),&export.exprs,&export.levels,HashMap::new()).with_recursor_reductions(malformed_rules).with_exposure_cache(cache.clone());
        assert!(malformed.qualified_one_step_recursor_result(&input,512).is_unknown());
        assert!(machine.qualified_one_step_recursor_result(&input,12).is_unknown());
        machine.exposure_fuel.set(Some(8));
        assert!(machine.qualified_one_step_recursor_result(&input,512).is_unknown());
        assert!(machine.exposure_fuel.get().is_some_and(|remaining|remaining<8),"the public allowance must not reset an existing owner");machine.exposure_fuel.set(None);
        assert_eq!(cache.borrow().completed_replay_count,0,"a partial registered result cannot become a completed memo");
        // A nested major is completed before the requested term may stop.
        let mut child=input.clone();child.spine[0]=closed(child_motive);child.spine[1]=closed(child_minor);child.spine[2]=closed(child_two);
        let mut outer=input.clone();outer.spine[3]=Closure::new(variable,EnvFrame::empty().extend_neutral(child));
        let nested=machine.qualified_one_step_recursor_result(&outer,512);
        assert!(matches!(nested.proven_value(),Some(Value::Neutral(n)) if matches!(&n.head,NeutralHead::Const{name,..} if *name==natrec.name)),"child completion lost the requested rewrite marker: {nested:?}");
        let mut unresolved_parent=input.clone();unresolved_parent.spine[3]=Closure::new(variable,EnvFrame::empty().extend_neutral(input.clone()));
        assert!(machine.qualified_one_step_recursor_result(&unresolved_parent,512).is_unknown(),"a stuck child cannot establish the parent's constructor");
    }
}

#[cfg(test)]
mod captured_recursor_spine_tests {
    use super::*;
    #[test]
    fn checked_neutral_iota_retains_surplus_arguments_and_actual_major_position() {
        let mut expressions=IdTable::default();
        let mut levels=IdTable::default();levels.insert(LevelId(0),Level::Zero).unwrap();
        for (id,expr) in [
            (0,Expr::Sort(LevelId(0))), (1,Expr::BVar(0)),
            (2,Expr::Lam {domain:ExprId(0),body:ExprId(1)}),
            (3,Expr::Lam {domain:ExprId(0),body:ExprId(2)}),
            (4,Expr::Const {name:NameId(2),levels:vec![]}),
            (5,Expr::Const {name:NameId(99),levels:vec![]}),
        ] {expressions.insert(ExprId(id),expr).unwrap();}
        let machine=Machine::new(AuthorityId(1),&expressions,&levels,HashMap::new())
            .with_recursor_reductions(HashMap::from([(NameId(1),RecursorReduction {
                k:false,num_params:0,num_indices:0,level_params:vec![],rules:vec![RecursorRule {
                    constructor:NameId(2),constructor_level_params:vec![],num_params:0,num_fields:0,rhs:ExprId(3),
                }],
            })]));
        let closure=|id|Closure::new(ExprId(id),EnvFrame::empty());
        let neutral=Neutral {head:NeutralHead::Const {name:NameId(1),levels:vec![]},spine:vec![closure(0),closure(2),closure(4),closure(5)]};
        let one_step=machine.qualified_one_step_recursor_result(&neutral,512);
        assert!(matches!(one_step.proven_value(),Some(Value::Neutral(n)) if n.head==NeutralHead::Const {name:NameId(99),levels:vec![]} && n.spine.is_empty()));
        let mut surplus_one_step=neutral.clone();surplus_one_step.spine.push(closure(0));
        assert!(matches!(machine.qualified_one_step_recursor_result(&surplus_one_step,512).proven_value(),Some(Value::Neutral(n)) if n.spine==[closure(0)]));
        let result=machine.qualified_nested_recursor_result(&neutral,512);
        assert!(matches!(result.proven_value(),Some(Value::Neutral(n)) if n.head==NeutralHead::Const {name:NameId(99),levels:vec![]} && n.spine.is_empty()),"{result:?}");
        let mut wrong=neutral.clone();wrong.spine[2]=closure(5);
        assert!(machine.qualified_nested_recursor_result(&wrong,512).is_unknown());
        let mut short=neutral.clone();short.spine.truncate(2);
        assert!(machine.qualified_nested_recursor_result(&short,512).is_unknown());
        assert!(machine.qualified_nested_recursor_result(&neutral,12).is_unknown());
        let mut surplus=neutral.clone();surplus.spine.push(closure(0));
        assert!(matches!(machine.qualified_nested_recursor_result(&surplus,512).proven_value(),Some(Value::Neutral(n)) if n.spine==[closure(0)]));
    }
}

#[cfg(test)]
mod bounded_checked_replay_tests {
    use super::*;

    fn assert_no_completed_replay(machine:&Machine<'_>,neutral:&Neutral) {
        machine.exposure_fuel.set(Some(4096));
        let NeutralHead::Const{name,levels}=&neutral.head else {panic!("test requires source recursor")};
        if let Some(key)=machine.completed_replay_key(*name,levels,&neutral.spine) {
            assert!(matches!(machine.lookup_completed_replay(&key).proven_value(),Some(None)),"changed source/configuration reused a completed result");
        }
        machine.exposure_fuel.set(None);
    }

    #[test]
    fn checked_replay_reuses_a_resolved_major_returned_again_by_the_rule_rhs() {
        let mut expressions=IdTable::default();
        let mut levels=IdTable::default();levels.insert(LevelId(0),Level::Zero).unwrap();
        for (id,expr) in [(0,Expr::Sort(LevelId(0))),(1,Expr::BVar(0)),
            (2,Expr::Const{name:NameId(2),levels:vec![]}),
            (3,Expr::Lam{domain:ExprId(0),body:ExprId(1)}),
            (4,Expr::Lam{domain:ExprId(0),body:ExprId(3)})]
        { expressions.insert(ExprId(id),expr).unwrap(); }
        let machine=Machine::new(AuthorityId(1),&expressions,&levels,HashMap::new())
            .with_recursor_reductions(HashMap::from([(NameId(1),RecursorReduction{
                k:false,num_params:0,num_indices:0,level_params:vec![],rules:vec![RecursorRule{
                    constructor:NameId(2),constructor_level_params:vec![],num_params:0,num_fields:0,rhs:ExprId(4),
                }],
            })]));
        let closed=|id|Closure::new(ExprId(id),EnvFrame::empty());
        let inner=Neutral{head:NeutralHead::Const{name:NameId(1),levels:vec![]},spine:vec![closed(0),closed(2),closed(2)]};
        let shared=Closure::new(ExprId(1),EnvFrame::empty().extend_neutral(inner));
        let outer=Neutral{head:NeutralHead::Const{name:NameId(1),levels:vec![]},spine:vec![closed(0),shared.clone(),shared]};
        assert_eq!(machine.qualified_nested_recursor_result(&outer,512).proven_value(),
            Some(&Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(2),levels:vec![]},spine:vec![]})));
    }

    #[test]
    fn completed_replay_constructs_one_source_key_and_shares_it_through_finish() {
        let mut expressions=IdTable::default();let levels=IdTable::default();
        for (id,expr) in [(0,Expr::BVar(0)),(1,Expr::Const{name:NameId(2),levels:vec![]}),
            (2,Expr::Lam{domain:ExprId(0),body:ExprId(1)}),
            (3,Expr::Lam{domain:ExprId(0),body:ExprId(2)})] {
            expressions.insert(ExprId(id),expr).unwrap();
        }
        let cache=new_exposure_cache();
        let machine=Machine::new(AuthorityId(1),&expressions,&levels,HashMap::new())
            .with_exposure_cache(cache.clone()).with_recursor_reductions(HashMap::from([(NameId(1),RecursorReduction{
                k:false,num_params:0,num_indices:0,level_params:vec![],rules:vec![RecursorRule{
                    constructor:NameId(2),constructor_level_params:vec![],num_params:0,num_fields:0,rhs:ExprId(3),
                }],
            })]));
        let closed=Closure::new(ExprId(1),EnvFrame::empty());
        let inner=Neutral{head:NeutralHead::Const{name:NameId(1),levels:vec![]},spine:vec![closed.clone(),closed.clone(),closed]};
        assert!(machine.qualified_nested_recursor_result(&inner,128).is_proven());
        assert_eq!(cache.borrow().completed_replay_count,1);
        assert_eq!(machine.replay_key_builds.get(),1,"entry and Finish must retain one exact source key");
        // A digest is an index, never equality evidence. Force a collision
        // and check that full source comparison is both exact and charged.
        let digest=*cache.borrow().completed_replays.keys().next().unwrap();
        let mut different=inner.clone();different.spine[0]=Closure::new(ExprId(0),EnvFrame::empty());
        machine.exposure_fuel.set(Some(512));
        let candidate=machine.completed_replay_key(NameId(1),&[],&different.spine).unwrap();
        let mut candidate=Rc::try_unwrap(candidate).ok().unwrap();candidate.digest=digest;
        let candidate=Rc::new(candidate);
        assert!(matches!(machine.lookup_completed_replay(&candidate).proven_value(),Some(None)));
        machine.exposure_fuel.set(Some(1));
        assert!(machine.lookup_completed_replay(&candidate).is_unknown(),"collision equality must not traverse an uncharged source key");
        machine.exposure_fuel.set(None);
    }

    #[test]
    fn checked_replay_refuses_a_constructor_at_a_different_declared_universe() {
        let mut expressions=IdTable::default();
        let mut levels=IdTable::default();levels.insert(LevelId(0),Level::Zero).unwrap();
        expressions.insert(ExprId(0),Expr::Sort(LevelId(0))).unwrap();
        expressions.insert(ExprId(1),Expr::BVar(0)).unwrap();
        let machine=Machine::new(AuthorityId(1),&expressions,&levels,HashMap::new())
            .with_recursor_reductions(HashMap::from([(NameId(1),RecursorReduction{
                k:false,num_params:0,num_indices:0,level_params:vec![NameId(10)],rules:vec![RecursorRule{
                    constructor:NameId(2),constructor_level_params:vec![NameId(10)],num_params:0,num_fields:0,rhs:ExprId(0),
                }],
            })]));
        let actual_constructor=Neutral{head:NeutralHead::Const{name:NameId(2),levels:vec![crate::level::succ(crate::level::LevelTerm::Zero)]},spine:vec![]};
        let major=Closure::new(ExprId(1),EnvFrame::empty().extend_neutral(actual_constructor));
        let closed=Closure::new(ExprId(0),EnvFrame::empty());
        let neutral=Neutral{head:NeutralHead::Const{name:NameId(1),levels:vec![crate::level::LevelTerm::Zero]},spine:vec![closed.clone(),closed,major]};
        assert!(machine.qualified_nested_recursor_result(&neutral,512).is_unknown());
    }

    #[test]
    fn completed_inner_replay_survives_outer_exhaustion_without_caching_the_outer() {
        let mut expressions=IdTable::default();let mut levels=IdTable::default();
        levels.insert(LevelId(0),Level::Zero).unwrap();
        for (id,expr) in [(0,Expr::Sort(LevelId(0))),(1,Expr::BVar(0)),
            (2,Expr::Const{name:NameId(2),levels:vec![]}),
            (3,Expr::Const{name:NameId(3),levels:vec![]})]
        {expressions.insert(ExprId(id),expr).unwrap();}
        let mut body=ExprId(3);
        for id in 10..32 {expressions.insert(ExprId(id),Expr::Let{ty:ExprId(0),value:ExprId(3),body}).unwrap();body=ExprId(id);}
        let mut cheap=ExprId(3);let mut expensive=body;
        for id in 50..60 {expressions.insert(ExprId(id),Expr::Let{ty:ExprId(0),value:ExprId(3),body:cheap}).unwrap();cheap=ExprId(id);}
        for id in 110..113 {expressions.insert(ExprId(id),Expr::Lam{domain:ExprId(0),body:cheap}).unwrap();cheap=ExprId(id);}
        for id in 113..116 {expressions.insert(ExprId(id),Expr::Lam{domain:ExprId(0),body:expensive}).unwrap();expensive=ExprId(id);}
        let reduction=RecursorReduction{k:false,num_params:0,num_indices:0,level_params:vec![],rules:vec![
            RecursorRule{constructor:NameId(2),constructor_level_params:vec![],num_params:0,num_fields:0,rhs:cheap},
            RecursorRule{constructor:NameId(3),constructor_level_params:vec![],num_params:0,num_fields:0,rhs:expensive},
        ]};
        let rules=Rc::new(HashMap::from([(NameId(1),reduction)]));let cache=new_exposure_cache();
        let machine=Machine::new(AuthorityId(1),&expressions,&levels,HashMap::new())
            .with_recursor_reductions(rules.clone()).with_exposure_cache(cache.clone());
        let closed=|id|Closure::new(ExprId(id),EnvFrame::empty());
        let inner=Neutral{head:NeutralHead::Const{name:NameId(1),levels:vec![]},spine:vec![closed(0),closed(0),closed(0),closed(2)]};
        let captured=Closure::new(ExprId(1),EnvFrame::empty().extend_neutral(inner.clone()));
        let mut outer=inner.clone();outer.spine[3]=captured;
        assert!(machine.qualified_nested_recursor_result(&outer,64).is_unknown());
        assert_no_completed_replay(&machine,&outer);
        machine.exposure_fuel.set(Some(32));
        let retry=machine.qualified_nested_recursor_result(&inner,48);
        machine.exposure_fuel.set(None);
        assert_eq!(retry.proven_value(),Some(&Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(3),levels:vec![]},spine:vec![]})),"completed inner iota was lost: {retry:?}");
        machine.exposure_fuel.set(Some(24));
        assert!(machine.qualified_nested_recursor_result(&outer,48).is_unknown());
        machine.exposure_fuel.set(None);
        assert_eq!(machine.qualified_nested_recursor_result(&outer,64).proven_value(),
            Some(&Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(3),levels:vec![]},spine:vec![]})),
            "same outer allowance should finish after completed inner proof survives");
        for variant in [0,1,2,3] {
            let mut different=inner.clone();
            match variant {
                0=>different.spine[1]=closed(3),
                1=>different.spine[3]=Closure::new(ExprId(1),EnvFrame::empty().extend(closed(2))),
                2=>different.head=NeutralHead::Const{name:NameId(1),levels:vec![crate::level::LevelTerm::Zero]},
                _=>different.spine.truncate(3),
            }
            assert_no_completed_replay(&machine,&different);
            machine.exposure_fuel.set(Some(12));
            assert!(machine.qualified_nested_recursor_result(&different,48).is_unknown());
            machine.exposure_fuel.set(None);
        }
        // Saturation keeps previously completed progress instead of
        // clearing the table and repeating the first expensive component.
        for index in 0..8193 {
            let mut distinct=inner.clone();
            distinct.spine[0]=Closure::new(ExprId(0),EnvFrame::empty().extend_free(FreeId(1000+index)));
            assert!(machine.qualified_nested_recursor_result(&distinct,64).is_proven());
        }
        machine.exposure_fuel.set(Some(32));
        assert!(machine.qualified_nested_recursor_result(&inner,48).is_proven());
        machine.exposure_fuel.set(None);
        let mut large_rules=(*rules).clone();large_rules.get_mut(&NameId(1)).unwrap().level_params=vec![NameId(10)];
        let large_key_machine=Machine::new(AuthorityId(1),&expressions,&levels,HashMap::new()).with_recursor_reductions(large_rules).with_exposure_cache(cache.clone());
        let mut large_key=inner.clone();large_key.head=NeutralHead::Const{name:NameId(1),levels:vec![crate::level::LevelTerm::Param("u".repeat(4096))]};
        assert!(large_key_machine.qualified_nested_recursor_result(&large_key,128).is_unknown(),"source key traversal must reserve bounded work before cloning/hashing");
        let fork=|authority|Machine::new(authority,&expressions,&levels,machine.definitions.clone())
            .with_recursor_reductions(rules.clone()).with_projection_specs(machine.projection_specs.clone())
            .with_singleton_recursor_reductions(machine.singleton_recursor_reductions.clone())
            .with_nullary_minor_reductions(machine.nullary_minor_reductions.clone())
            .with_closed_nested_minor_reductions(machine.closed_nested_minor_reductions.clone()).with_exposure_cache(cache.clone());
        let other=fork(AuthorityId(2));
        assert_no_completed_replay(&other,&inner);
        other.exposure_fuel.set(Some(12));assert!(other.qualified_nested_recursor_result(&inner,48).is_unknown());other.exposure_fuel.set(None);
        let mut forged=(*rules).clone();forged.get_mut(&NameId(1)).unwrap().rules[0].rhs=expensive;
        let changed=fork(AuthorityId(1)).with_recursor_reductions(forged);
        assert_no_completed_replay(&changed,&inner);
        changed.exposure_fuel.set(Some(12));assert!(changed.qualified_nested_recursor_result(&inner,48).is_unknown());changed.exposure_fuel.set(None);
        let mut different_mode=fork(AuthorityId(1));
        different_mode.demand_major=!machine.demand_major;
        assert_no_completed_replay(&different_mode,&inner);
        different_mode.exposure_fuel.set(Some(12));assert!(different_mode.qualified_nested_recursor_result(&inner,48).is_unknown());different_mode.exposure_fuel.set(None);
    }

    #[test]
    fn completed_replay_clone_declines_deep_projection_heads_before_recursive_copy() {
        let expressions=IdTable::default();let levels=IdTable::default();
        let machine=Machine::new(AuthorityId(1),&expressions,&levels,HashMap::new());
        let mut head=Neutral{head:NeutralHead::Free(FreeId(0)),spine:vec![]};
        for _ in 0..257 {head=Neutral{head:NeutralHead::Projection{type_name:NameId(1),index:0,structure:Box::new(head)},spine:vec![]};}
        let value=Value::Neutral(head);
        machine.exposure_fuel.set(Some(64));assert!(!machine.reserve_replay_value_clone(&value));
        machine.exposure_fuel.set(Some(1024));assert!(!machine.reserve_replay_value_clone(&value));
        machine.exposure_fuel.set(None);
    }

    // Reintroducing a fixed five-major depth bound loses valid source iota.
    #[test]
    fn checked_replay_resolves_eight_captured_majors_without_guessing_a_branch() {
        let mut expressions=IdTable::default();
        let mut levels=IdTable::default();
        levels.insert(LevelId(0),Level::Zero).unwrap();
        for (id,expr) in [
            (0,Expr::Sort(LevelId(0))), (1,Expr::BVar(0)),
            (2,Expr::Const{name:NameId(2),levels:vec![]}),
            (3,Expr::Lam{domain:ExprId(0),body:ExprId(2)}),
            (4,Expr::Lam{domain:ExprId(0),body:ExprId(3)}),
        ] { expressions.insert(ExprId(id),expr).unwrap(); }
        let machine=Machine::new(AuthorityId(1),&expressions,&levels,HashMap::new())
            .with_recursor_reductions(HashMap::from([(NameId(1),RecursorReduction{
                k:false,num_params:0,num_indices:0,level_params:vec![],rules:vec![RecursorRule{
                    constructor:NameId(2),constructor_level_params:vec![],num_params:0,num_fields:0,rhs:ExprId(4),
                }],
            })]));
        let closed=|id|Closure::new(ExprId(id),EnvFrame::empty());
        let mut chain=Neutral{head:NeutralHead::Const{name:NameId(2),levels:vec![]},spine:vec![]};
        for _ in 0..8 {
            let major=Closure::new(ExprId(1),EnvFrame::empty().extend_neutral(chain));
            chain=Neutral{head:NeutralHead::Const{name:NameId(1),levels:vec![]},spine:vec![closed(0),closed(0),major]};
        }
        assert_eq!(machine.qualified_nested_recursor_result(&chain,2048).proven_value(),
            Some(&Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(2),levels:vec![]},spine:vec![]})));
        assert!(machine.qualified_nested_recursor_result(&chain,12).is_unknown());
        let mut free=chain.clone();free.spine[2]=Closure::new(ExprId(1),EnvFrame::empty().extend_free(FreeId(9)));
        assert!(machine.qualified_nested_recursor_result(&free,2048).is_unknown());
        let mut short=chain.clone();short.spine.truncate(2);
        assert!(machine.qualified_nested_recursor_result(&short,2048).is_unknown());
        let mut wrong_constructor=chain.clone();
        wrong_constructor.spine[2]=Closure::new(ExprId(1),EnvFrame::empty().extend_neutral(
            Neutral{head:NeutralHead::Const{name:NameId(2),levels:vec![crate::level::LevelTerm::Zero]},spine:vec![]}));
        assert!(machine.qualified_nested_recursor_result(&wrong_constructor,2048).is_unknown());
        wrong_constructor.spine[2]=Closure::new(ExprId(1),EnvFrame::empty().extend_neutral(
            Neutral{head:NeutralHead::Const{name:NameId(2),levels:vec![]},spine:vec![closed(0)]}));
        assert!(machine.qualified_nested_recursor_result(&wrong_constructor,2048).is_unknown());
        let mut wrong_levels=chain;wrong_levels.head=NeutralHead::Const{name:NameId(1),levels:vec![crate::level::LevelTerm::Zero]};
        assert!(machine.qualified_nested_recursor_result(&wrong_levels,2048).is_unknown());
    }
}

#[cfg(test)]
mod captured_native_nat_replay_tests {
    use super::*;
    use crate::parser::parse;
    use crate::syntax::Declaration;
    use crate::nat::BigNat;
    use std::io::Cursor;

    #[test]
    fn native_nat_successor_reuses_its_exact_numeric_field_carrier() {
        let mut export=parse(Cursor::new(include_bytes!("../tests/fixtures/good-parameter-tree.ndjson"))).unwrap().resolve().unwrap();
        let Declaration::Inductive(block)=export.declarations[0].clone() else {panic!("Nat block")};
        let rec=&block.recursors[0];
        export.exprs.insert(ExprId(1000),Expr::NatLit(BigNat::parse_decimal("16").unwrap())).unwrap();
        let reduction=RecursorReduction{k:false,num_params:0,num_indices:0,level_params:rec.level_params.clone(),rules:rec.rules.iter().map(|r|RecursorRule{constructor:r.constructor,constructor_level_params:vec![],num_params:0,num_fields:r.num_fields as usize,rhs:r.rhs}).collect()};
        let nat=NatPrimitives{type_name:block.types[0].name,type_expr:ExprId(1),zero:block.constructors[0].name,succ:block.constructors[1].name,recursor:rec.name,add:None,mul:None,pow:None,land:None,shift_right:None,div:None,modulo:None,sub:None,pred:None,virtual_bvar_zero:Some(ExprId(5)),ble:None,beq:None};
        let cache=new_exposure_cache();
        let machine=Machine::new(AuthorityId(1),&export.exprs,&export.levels,HashMap::new())
            .with_nat_primitives(Some(nat.clone())).with_exposure_cache(cache.clone());
        let major=Closure::new(ExprId(1000),EnvFrame::empty());
        let first=machine.rule_constructor_application(&major,&reduction,Transparency::Opaque,128).unwrap();
        let second=machine.rule_constructor_application(&major,&reduction,Transparency::Opaque,128).unwrap();
        assert_eq!(first,second,"same certified numerical field must preserve evaluator sharing");
        assert_eq!(first.0,nat.succ);
        assert_eq!(machine.expose(first.1[0].clone(),Transparency::Opaque,16).proven_value(),
            Some(&Value::NatLit(BigNat::parse_decimal("15").unwrap())));
        cache.borrow_mut().values.clear();
        let third=machine.rule_constructor_application(&major,&reduction,Transparency::Opaque,128).unwrap();
        assert_eq!(first,third,"exposure result eviction must not invalidate numeric bindings");
        let different=machine.native_nat_field(BigNat::parse_decimal("16").unwrap()).unwrap();
        assert_ne!(first.1[0],different,"different exact numbers retain distinct carriers");
        let other_authority=Machine::new(AuthorityId(2),&export.exprs,&export.levels,HashMap::new())
            .with_nat_primitives(Some(nat.clone())).with_exposure_cache(cache.clone());
        assert_ne!(first.1[0],other_authority.native_nat_field(BigNat::parse_decimal("15").unwrap()).unwrap());
        cache.borrow_mut().numeric_bindings.clear();
        let evicted=machine.native_nat_field(BigNat::parse_decimal("15").unwrap()).unwrap();
        assert_eq!(machine.expose(evicted,Transparency::Opaque,16).proven_value(),
            Some(&Value::NatLit(BigNat::parse_decimal("15").unwrap())));
        assert_eq!(machine.expose(first.1[0].clone(),Transparency::Opaque,16).proven_value(),
            Some(&Value::NatLit(BigNat::parse_decimal("15").unwrap())));
        let absent=Machine::new(AuthorityId(1),&export.exprs,&export.levels,HashMap::new());
        assert!(absent.rule_constructor_application(&major,&reduction,Transparency::Opaque,128).is_none());
        let mut wrong=nat;wrong.virtual_bvar_zero=Some(ExprId(1));
        let invalid=Machine::new(AuthorityId(1),&export.exprs,&export.levels,HashMap::new()).with_nat_primitives(Some(wrong));
        assert!(invalid.rule_constructor_application(&major,&reduction,Transparency::Opaque,128).is_none());
        let zero=Closure::new(ExprId(5),EnvFrame::empty().extend_nat_literal(BigNat::zero()));
        assert_eq!(invalid.rule_constructor_application(&zero,&reduction,Transparency::Opaque,128),
            Some((block.constructors[0].name,vec![])),"zero has no predecessor field or carrier demand");
        assert!(absent.rule_constructor_application(&zero,&reduction,Transparency::Opaque,128).is_none());
    }

    #[test]
    fn qualified_nat_replay_uses_exact_literal_major_and_predecessor() {
        let mut export=parse(Cursor::new(include_bytes!("../tests/fixtures/good-parameter-tree.ndjson"))).unwrap().resolve().unwrap();
        let Declaration::Inductive(block)=export.declarations[0].clone() else {panic!("Nat block")};
        let rec=&block.recursors[0];
        for (id,value) in [(1000,"0"),(1002,"7"),(1007,"99")] {export.exprs.insert(ExprId(id),Expr::NatLit(BigNat::parse_decimal(value).unwrap())).unwrap();}
        let large=BigNat::parse_decimal(&"9".repeat(900)).unwrap();
        export.exprs.insert(ExprId(1008),Expr::NatLit(large.clone())).unwrap();
        export.exprs.insert(ExprId(1003),Expr::BVar(1)).unwrap();
        export.exprs.insert(ExprId(1004),Expr::Lam{domain:ExprId(1),body:ExprId(1003)}).unwrap();
        export.exprs.insert(ExprId(1005),Expr::Lam{domain:ExprId(1),body:ExprId(1004)}).unwrap();
        export.exprs.insert(ExprId(1006),Expr::Lam{domain:ExprId(1),body:ExprId(1)}).unwrap();
        let reduction=RecursorReduction{k:false,num_params:0,num_indices:0,level_params:rec.level_params.clone(),rules:rec.rules.iter().map(|r|RecursorRule{constructor:r.constructor,constructor_level_params:vec![],num_params:0,num_fields:r.num_fields as usize,rhs:r.rhs}).collect()};
        let nat=NatPrimitives{type_name:block.types[0].name,type_expr:ExprId(1),zero:block.constructors[0].name,succ:block.constructors[1].name,recursor:rec.name,add:None,mul:None,pow:None,land:None,shift_right:None,div:None,modulo:None,sub:None,pred:None,virtual_bvar_zero:Some(ExprId(5)),ble:None,beq:None};
        let rules=Rc::new(HashMap::from([(rec.name,reduction.clone())]));
        let cache=new_exposure_cache();
        let machine=Machine::new(AuthorityId(1),&export.exprs,&export.levels,HashMap::new()).with_recursor_reductions(rules.clone()).with_nat_primitives(Some(nat)).with_exposure_cache(cache.clone());
        let closure=|id|Closure::new(ExprId(id),EnvFrame::empty());
        let mut neutral=Neutral{head:NeutralHead::Const{name:rec.name,levels:vec![crate::level::succ(crate::level::LevelTerm::Zero)]},spine:vec![closure(1006),closure(1007),closure(1005),closure(1002)]};
        assert_eq!(machine.qualified_nested_recursor_result(&neutral,512).proven_value(),Some(&Value::NatLit(BigNat::parse_decimal("6").unwrap())));
        neutral.spine[3]=closure(1000);
        assert_eq!(machine.qualified_nested_recursor_result(&neutral,512).proven_value(),Some(&Value::NatLit(BigNat::parse_decimal("99").unwrap())));
        assert!(machine.qualified_nested_recursor_result(&neutral,20).is_unknown());
        neutral.spine[3]=Closure::new(ExprId(5),EnvFrame::empty().extend_free(FreeId(99)));
        assert!(machine.qualified_nested_recursor_result(&neutral,512).is_unknown());
        neutral.spine[3]=closure(1002);
        // Even identical registered rules and authority cannot transfer a
        // native literal replay into a machine without its Nat witness.
        let no_nat=Machine::new(AuthorityId(1),&export.exprs,&export.levels,machine.definitions.clone())
            .with_recursor_reductions(rules).with_singleton_recursor_reductions(machine.singleton_recursor_reductions.clone())
            .with_nullary_minor_reductions(machine.nullary_minor_reductions.clone())
            .with_closed_nested_minor_reductions(machine.closed_nested_minor_reductions.clone())
            .with_projection_specs(machine.projection_specs.clone()).with_exposure_cache(cache);
        assert!(no_nat.qualified_nested_recursor_result(&neutral,512).is_unknown());
        // Seven source-registered Nat iotas each select the actual successor
        // rule and its exact predecessor, even through delayed value bindings.
        let mut delayed=neutral;
        for _ in 0..6 {
            let major=Closure::new(ExprId(5),EnvFrame::empty().extend_neutral(delayed.clone()));
            delayed.spine[3]=major;
        }
        assert_eq!(machine.qualified_nested_recursor_result(&delayed,4096).proven_value(),
            Some(&Value::NatLit(BigNat::parse_decimal("0").unwrap())));
        assert!(no_nat.qualified_nested_recursor_result(&delayed,4096).is_unknown());
        delayed.spine[3]=closure(1008);
        assert!(machine.qualified_nested_recursor_result(&delayed,128).is_unknown(),"large predecessor/carrier work must spend limb-scaled fuel");
        assert!(machine.rule_constructor_application(&closure(1008),&reduction,Transparency::Opaque,128).is_none());
        assert_eq!(machine.qualified_nested_recursor_result(&delayed,8192).proven_value(),Some(&Value::NatLit(large.pred().unwrap())));
    }
}

#[cfg(test)]
mod captured_nat_projection_tests {
    use super::*;
    use crate::parser::parse;
    use crate::syntax::Declaration;
    use crate::nat::BigNat;
    use std::io::Cursor;

    #[test]
    fn projection_replays_a_cached_nat_recursor_on_its_actual_numeric_major() {
        let mut export=parse(Cursor::new(include_bytes!("../tests/fixtures/good-parameter-tree.ndjson"))).unwrap().resolve().unwrap();
        let Declaration::Inductive(block)=export.declarations[0].clone() else {panic!("Nat block")};
        let rec=&block.recursors[0];
        for (id,expr) in [
            (1000,Expr::NatLit(BigNat::parse_decimal("7").unwrap())),
            (1001,Expr::NatLit(BigNat::zero())),
            (1002,Expr::Const{name:NameId(100),levels:vec![]}),
            (1003,Expr::Const{name:NameId(101),levels:vec![]}),
            (1004,Expr::BVar(1)),
            (1005,Expr::App{fun:ExprId(1002),arg:ExprId(1004)}),
            (1006,Expr::Lam{domain:ExprId(1003),body:ExprId(1005)}),
            (1007,Expr::Lam{domain:ExprId(1),body:ExprId(1006)}),
            (1008,Expr::Lam{domain:ExprId(1),body:ExprId(1003)}),
            (1009,Expr::App{fun:ExprId(1002),arg:ExprId(1001)}),
            (1010,Expr::Const{name:rec.name,levels:vec![LevelId(1)]}),
        ] {export.exprs.insert(ExprId(id),expr).unwrap();}
        let mut definitions=HashMap::new();
        let mut previous=ExprId(1000);
        for i in 0..200u64 {
            let name=NameId(2000+i);let id=ExprId(2000+i);
            export.exprs.insert(id,Expr::Const{name,levels:vec![]}).unwrap();
            definitions.insert(name,DefinitionBody{value:previous,level_params:vec![],preferred_for_reduction:true});previous=id;
        }
        let mut call=ExprId(1010);
        for (i,arg) in [ExprId(1008),ExprId(1009),ExprId(1007),previous].into_iter().enumerate() {
            let id=ExprId(3000+i as u64);export.exprs.insert(id,Expr::App{fun:call,arg}).unwrap();call=id;
        }
        export.exprs.insert(ExprId(3010),Expr::Proj{type_name:NameId(101),index:0,structure:call}).unwrap();
        let nat=NatPrimitives{type_name:block.types[0].name,type_expr:ExprId(1),zero:block.constructors[0].name,succ:block.constructors[1].name,recursor:rec.name,add:None,mul:None,pow:None,land:None,shift_right:None,div:None,modulo:None,sub:None,pred:None,virtual_bvar_zero:Some(ExprId(5)),ble:None,beq:None};
        let reduction=RecursorReduction{k:false,num_params:0,num_indices:0,level_params:rec.level_params.clone(),rules:rec.rules.iter().map(|r|RecursorRule{constructor:r.constructor,constructor_level_params:vec![],num_params:0,num_fields:r.num_fields as usize,rhs:r.rhs}).collect()};
        let machine=Machine::new(AuthorityId(1),&export.exprs,&export.levels,definitions).with_nat_primitives(Some(nat)).with_recursor_reductions(HashMap::from([(rec.name,reduction)])).with_projection_specs(HashMap::from([(NameId(101),ProjectionSpec{constructor:NameId(100),num_params:0,field_types:vec![ProjectionFieldType::Derived(ExprId(1))],eta_expandable:false})])).with_exposure_cache(new_exposure_cache());
        let receiver=Closure::new(call,EnvFrame::empty());
        if !machine.demand_major {
            assert!(matches!(machine.expose(receiver.clone(),Transparency::Full,1024).proven_value(),Some(Value::Neutral(n)) if n.head==NeutralHead::Const{name:rec.name,levels:vec![crate::level::succ(crate::level::LevelTerm::Zero)]}));
        }
        assert!(machine.projection_field_for_conversion(receiver.clone(),NameId(101),1,1024).is_unknown());
        assert!(machine.projection_field_for_conversion(receiver.clone(),NameId(999),0,1024).is_unknown());
        assert!(machine.projection_field_for_conversion(receiver.clone(),NameId(101),0,1).is_unknown());
        let projected=machine.expose(Closure::new(ExprId(3010),EnvFrame::empty()),Transparency::Full,1024);
        assert_eq!(projected.proven_value(),Some(&Value::NatLit(BigNat::parse_decimal("6").unwrap())),"{projected:?}");
    }
}

#[cfg(test)]
mod symbolic_major_cache_tests {
    use super::*;
    use crate::nat::BigNat;

    #[test]
    fn demand_reuses_a_normal_form_blocked_on_an_immutable_local() {
        let mut expressions=IdTable::default();
        let mut levels=IdTable::default();levels.insert(LevelId(0),Level::Zero).unwrap();
        for (id,expr) in [
            (0,Expr::BVar(0)), (1,Expr::Sort(LevelId(0))),
            (2,Expr::Const{name:NameId(1),levels:vec![]}),
            (3,Expr::NatLit(BigNat::parse_decimal("9").unwrap())),
            (4,Expr::App{fun:ExprId(2),arg:ExprId(1)}),
            (5,Expr::App{fun:ExprId(4),arg:ExprId(3)}),
            (6,Expr::App{fun:ExprId(5),arg:ExprId(0)}),
            (7,Expr::Const{name:NameId(2),levels:vec![]}),
            (8,Expr::Lam{domain:ExprId(1),body:ExprId(0)}),
            (9,Expr::Lam{domain:ExprId(1),body:ExprId(8)}),
        ] {expressions.insert(ExprId(id),expr).unwrap();}
        let mut definitions=HashMap::new();let mut previous=ExprId(7);
        for i in 0..200u64 {
            let id=ExprId(1000+i);let name=NameId(1000+i);
            expressions.insert(id,Expr::Const{name,levels:vec![]}).unwrap();
            definitions.insert(name,DefinitionBody{value:previous,preferred_for_reduction:true,level_params:vec![]});previous=id;
        }
        let mut machine=Machine::new(AuthorityId(1),&expressions,&levels,definitions)
            .with_recursor_reductions(HashMap::from([(NameId(1),RecursorReduction{
                k:false,num_params:0,num_indices:0,level_params:vec![],rules:vec![RecursorRule{
                    constructor:NameId(2),constructor_level_params:vec![],num_params:0,num_fields:0,rhs:ExprId(9),
                }],
            })])).with_exposure_cache(new_exposure_cache());
        machine.demand_major=true;
        let local=Closure::new(ExprId(6),EnvFrame::empty().extend_free(FreeId(73)));
        let first=machine.expose(local.clone(),Transparency::Full,256);
        let Some(Value::Neutral(n))=first.proven_value() else {panic!("{first:?}")};
        assert_eq!(n.head,NeutralHead::Const{name:NameId(1),levels:vec![]});
        let reused=machine.expose(local.clone(),Transparency::Full,1);
        assert_eq!(reused.proven_value(),first.proven_value(),"stable symbolic result was recomputed: {reused:?}");
        machine.authority=AuthorityId(2);
        assert!(machine.expose(local,Transparency::Full,1).is_unknown());
        machine.authority=AuthorityId(1);
        // An unresolved constructor demand is not a stable symbolic major.
        let delayed=Closure::new(ExprId(6),EnvFrame::empty().extend(Closure::new(previous,EnvFrame::empty())));
        assert!(matches!(machine.expose(delayed.clone(),Transparency::Full,64).proven_value(),Some(Value::Neutral(_))));
        assert!(machine.expose(delayed.clone(),Transparency::Full,1).is_unknown());
        assert_eq!(machine.expose(delayed,Transparency::Full,1024).proven_value(),Some(&Value::NatLit(BigNat::parse_decimal("9").unwrap())));
    }
}

#[cfg(test)]
mod captured_beta_frame_tests {
    use super::*;
    use crate::nat::BigNat;

    #[test]
    fn completed_replay_still_matches_after_beta_binding_saturation() {
        let mut expressions=IdTable::default();let mut levels=IdTable::default();
        levels.insert(LevelId(0),Level::Zero).unwrap();
        for (id,expr) in [(0,Expr::Sort(LevelId(0))),(1,Expr::BVar(0)),
            (2,Expr::Const{name:NameId(2),levels:vec![]}),
            (3,Expr::Lam{domain:ExprId(0),body:ExprId(2)}),
            (4,Expr::Lam{domain:ExprId(0),body:ExprId(3)}),
            (5,Expr::Lam{domain:ExprId(0),body:ExprId(1)})]
        {expressions.insert(ExprId(id),expr).unwrap();}
        let machine=Machine::new(AuthorityId(1),&expressions,&levels,HashMap::new())
            .with_recursor_reductions(HashMap::from([(NameId(1),RecursorReduction{
                k:false,num_params:0,num_indices:0,level_params:vec![],rules:vec![RecursorRule{
                    constructor:NameId(2),constructor_level_params:vec![],num_params:0,num_fields:0,rhs:ExprId(4),
                }],
            })])).with_exposure_cache(new_exposure_cache());
        let closed=|id|Closure::new(ExprId(id),EnvFrame::empty());
        let binder=closed(5);let argument=closed(2);
        let first_frame=machine.bind_captured_argument(&binder,argument.clone());
        let mut inner=Neutral{head:NeutralHead::Const{name:NameId(1),levels:vec![]},
            spine:vec![closed(0),closed(0),Closure::new(ExprId(1),first_frame)]};
        assert!(machine.qualified_nested_recursor_result(&inner,128).is_proven());
        for index in 0..8193 {
            let distinct=Closure::new(ExprId(2),EnvFrame::empty().extend_free(FreeId(1000+index)));
            machine.bind_captured_argument(&binder,distinct);
        }
        let retried_frame=machine.bind_captured_argument(&binder,argument);
        inner.spine[2]=Closure::new(ExprId(1),retried_frame);
        machine.exposure_fuel.set(Some(20));
        let retried=machine.qualified_nested_recursor_result(&inner,48);
        machine.exposure_fuel.set(None);
        assert!(retried.is_proven(),"binding purge made a completed exact replay unreachable: {retried:?}");
    }

    #[test]
    fn beta_binding_saturation_preserves_existing_exact_captures_and_leaves_new_ones_fresh() {
        use crate::level::LevelTerm;
        use crate::value::LevelSubstitution;
        let mut expressions=IdTable::default();let levels=IdTable::default();
        expressions.insert(ExprId(0),Expr::BVar(0)).unwrap();
        expressions.insert(ExprId(1),Expr::Lam{domain:ExprId(0),body:ExprId(0)}).unwrap();
        expressions.insert(ExprId(2),Expr::NatLit(BigNat::parse_decimal("9").unwrap())).unwrap();
        let cache=new_exposure_cache();
        let machine=Machine::new(AuthorityId(1),&expressions,&levels,HashMap::new()).with_exposure_cache(cache.clone());
        let binder=Closure::new(ExprId(1),EnvFrame::empty());
        let argument=Closure::new(ExprId(2),EnvFrame::empty());
        let first=machine.bind_captured_argument(&binder,argument.clone());
        assert_eq!(first.id(),machine.bind_captured_argument(&binder,argument.clone()).id());
        let changed_levels=LevelSubstitution::new(vec![(NameId(77),LevelTerm::Zero)]);
        let changed_binder=Closure::with_levels(binder.expr,binder.env.clone(),changed_levels.clone());
        assert_ne!(first.id(),machine.bind_captured_argument(&changed_binder,argument.clone()).id());
        let changed_argument=Closure::with_levels(argument.expr,argument.env.clone(),changed_levels);
        assert_ne!(first.id(),machine.bind_captured_argument(&binder,changed_argument).id());
        for i in 0..8192 {
            let distinct=Closure::new(argument.expr,EnvFrame::empty().extend_free(FreeId(i)));
            machine.bind_captured_argument(&binder,distinct);
        }
        let after_eviction=machine.bind_captured_argument(&binder,argument.clone());
        assert_eq!(first.id(),after_eviction.id(),"saturation must preserve existing source binding identities");
        let overflow=Closure::new(argument.expr,EnvFrame::empty().extend_free(FreeId(u64::MAX)));
        let fresh=machine.bind_captured_argument(&binder,overflow.clone());
        let fresh_again=machine.bind_captured_argument(&binder,overflow);
        assert_ne!(fresh.id(),fresh_again.id(),"new overflow bindings remain uncached fresh frames");
        let expected=Some(&Value::NatLit(BigNat::parse_decimal("9").unwrap()));
        assert_eq!(machine.expose(Closure::new(ExprId(0),first),Transparency::Full,32).proven_value(),expected);
        assert_eq!(machine.expose(Closure::new(ExprId(0),after_eviction),Transparency::Full,32).proven_value(),expected);
        assert_eq!(machine.expose(Closure::new(ExprId(0),fresh),Transparency::Full,32).proven_value(),expected);
        assert_eq!(machine.expose(Closure::new(ExprId(0),fresh_again),Transparency::Full,32).proven_value(),expected);
    }

    #[test]
    fn repeated_exact_beta_capture_reuses_its_dependent_domain_evidence() {
        let mut expressions=IdTable::default();let levels=IdTable::default();
        for (id,expr) in [
            (0,Expr::BVar(0)),
            (1,Expr::Const{name:NameId(7),levels:vec![]}),
            (2,Expr::Const{name:NameId(2),levels:vec![]}),
            (3,Expr::App{fun:ExprId(2),arg:ExprId(0)}),
            (4,Expr::Lam{domain:ExprId(3),body:ExprId(0)}),
            (5,Expr::Lam{domain:ExprId(1),body:ExprId(4)}),
            (6,Expr::NatLit(BigNat::parse_decimal("9").unwrap())),
            (7,Expr::NatLit(BigNat::parse_decimal("10").unwrap())),
            (8,Expr::App{fun:ExprId(5),arg:ExprId(6)}),
            (9,Expr::App{fun:ExprId(5),arg:ExprId(7)}),
            (10,Expr::Lam{domain:ExprId(1),body:ExprId(4)}),
            (11,Expr::App{fun:ExprId(10),arg:ExprId(6)}),
        ] {expressions.insert(ExprId(id),expr).unwrap();}
        let mut machine=Machine::new(AuthorityId(1),&expressions,&levels,HashMap::new())
            .with_exposure_cache(new_exposure_cache());
        let closure=|id|Closure::new(ExprId(id),EnvFrame::empty());
        let domain=|value:Judgment<Value>|match value {Judgment::Proven{value:Value::Lam{domain,..},..}=>domain,_=>panic!("expected captured lambda")};
        let first=domain(machine.expose(closure(8),Transparency::Full,128));
        let established=machine.expose(first,Transparency::Full,128);
        assert!(established.is_proven());
        let repeated=domain(machine.expose(closure(8),Transparency::Reducible,128));
        assert_eq!(machine.expose(repeated,Transparency::Full,1).proven_value(),established.proven_value(),"identical source beta capture lost its domain evidence");
        let other_argument=domain(machine.expose(closure(9),Transparency::Full,128));
        assert!(machine.expose(other_argument.clone(),Transparency::Full,1).is_unknown());
        let Some(Value::Neutral(n))=machine.expose(other_argument,Transparency::Full,128).proven_value().cloned() else {panic!("P ten")};
        assert_eq!(machine.expose(n.spine[0].clone(),Transparency::Full,128).proven_value(),Some(&Value::NatLit(BigNat::parse_decimal("10").unwrap())));
        let other_binder=domain(machine.expose(closure(11),Transparency::Full,128));
        assert!(machine.expose(other_binder,Transparency::Full,1).is_unknown());
        let other_parent=domain(machine.expose(Closure::new(ExprId(8),EnvFrame::empty().extend_free(FreeId(99))),Transparency::Full,128));
        assert!(machine.expose(other_parent,Transparency::Full,1).is_unknown());
        machine.authority=AuthorityId(2);
        let other_authority=domain(machine.expose(closure(8),Transparency::Full,128));
        assert!(machine.expose(other_authority,Transparency::Full,1).is_unknown());
    }
}

#[cfg(test)]
mod exposure_clock_tests {
    use super::*;
    #[test]
    fn depth_limit_is_an_ambient_dependency_outside_a_captured_bvar_head() {
        let mut expressions=IdTable::default();
        expressions.insert(ExprId(0),Expr::BVar(0)).unwrap();
        let levels=IdTable::default();
        let machine=Machine::new(AuthorityId(1),&expressions,&levels,HashMap::new());
        let closure=Closure::new(ExprId(0),EnvFrame::empty().extend_free(FreeId(12)));
        // Same source/closure, pending spine, transparency, local allowance,
        // projection mode, and global fuel. Only ambient evaluator depth varies.
        machine.exposure_fuel.set(Some(128));
        machine.exposure_depth.set(63);
        let permitted=machine.expose(closure.clone(),Transparency::Full,128);
        assert!(permitted.is_proven(),"63-level call should reach the captured BVar");
        machine.exposure_fuel.set(Some(128));
        machine.exposure_depth.set(64);
        let limited=machine.expose(closure,Transparency::Full,128);
        assert!(matches!(limited,Judgment::Unknown{..}),
            "identical exposure request must respect the ambient depth guard");
        machine.exposure_depth.set(0);
        machine.exposure_fuel.set(None);
    }
    #[test]
    fn clock_keys_preserve_capture_authority_and_exposure_modes() {
        let mut exprs=IdTable::default();exprs.insert(ExprId(0),Expr::BVar(0)).unwrap();
        let levels=IdTable::default();let cache=new_exposure_cache();
        let machine=Machine::new(AuthorityId(1),&exprs,&levels,HashMap::new()).with_exposure_cache(cache.clone());
        let a=Closure::new(ExprId(0),EnvFrame::empty().extend_free(FreeId(1)));
        let b=Closure::new(ExprId(0),EnvFrame::empty().extend_free(FreeId(2)));
        assert!(matches!(machine.expose(a.clone(),Transparency::Full,16).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Free(FreeId(1)),..}))));
        assert!(matches!(machine.expose(b.clone(),Transparency::Full,16).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Free(FreeId(2)),..}))));
        let count=cache.borrow().values.len();
        assert!(machine.expose(a.clone(),Transparency::Opaque,16).is_proven());
        assert!(cache.borrow().values.len()>count);
        let count=cache.borrow().values.len();
        assert!(machine.expose_internal_with_pending(a.clone(),Transparency::Full,16,false,true,vec![]).is_proven());
        assert!(cache.borrow().values.len()>count);
        let other=Machine::new(AuthorityId(2),&exprs,&levels,HashMap::new()).with_exposure_cache(cache.clone());
        let count=cache.borrow().values.len();assert!(other.expose(a.clone(),Transparency::Full,16).is_proven());
        assert!(cache.borrow().values.len()>count);
        let count=cache.borrow().values.len();
        assert!(machine.expose(a,Transparency::Full,0).is_unknown());
        assert!(machine.expose(Closure::new(ExprId(99),EnvFrame::empty()),Transparency::Full,16).is_unknown());
        assert_eq!(cache.borrow().values.len(),count);
        // A cached digest is only an index; exact source equality remains required.
        let left=CachedExposureKey{exact:(AuthorityId(1),b.clone(),Transparency::Full,false,vec![]),digest:1};
        let right=CachedExposureKey{exact:(AuthorityId(2),b,Transparency::Full,false,vec![]),digest:1};
        assert!(left!=right);
    }
    #[test]
    fn exhausted_clock_bookkeeping_declines_only_optional_publication() {
        let mut store=ExposureCacheStore::default();
        let key=Rc::new(CachedExposureKey::new((AuthorityId(1),Closure::new(ExprId(0),EnvFrame::empty()),Transparency::Full,false,vec![])));
        let value=Value::Neutral(Neutral{head:NeutralHead::Free(FreeId(0)),spine:vec![]});
        for i in 0..8192 {store.retain_exposure(Rc::new(CachedExposureKey::new((AuthorityId(1),Closure::new(ExprId(i+1),EnvFrame::empty()),Transparency::Full,false,vec![]))),&value,||true);}
        store.retain_exposure(key.clone(),&value,||false);
        assert_eq!(store.values.len(),8192);assert!(!store.values.contains_key(&key));
        for entry in store.values.values_mut(){entry.referenced=true;}
        let mut allowance=3;store.retain_exposure(key.clone(),&value,||{if allowance==0{false}else{allowance-=1;true}});
        assert_eq!(allowance,0);assert_eq!(store.values.len(),8192);assert!(!store.values.contains_key(&key));
        let mut visits=0;store.retain_exposure(key.clone(),&value,||{visits+=1;true});
        assert!(visits<=8192*2);assert_eq!(store.values.len(),8192);assert!(store.values.contains_key(&key));
        let mut exprs=IdTable::default();exprs.insert(ExprId(0),Expr::Const{name:NameId(0),levels:vec![]}).unwrap();
        let levels=IdTable::default();let cache=new_exposure_cache();
        let machine=Machine::new(AuthorityId(1),&exprs,&levels,HashMap::new()).with_exposure_cache(cache.clone());
        machine.exposure_fuel.set(Some(1));
        let result=machine.expose(Closure::new(ExprId(0),EnvFrame::empty()),Transparency::Full,32);
        assert!(result.is_proven(),"optional eviction cannot lose an established result: {result:?}");
        // Unsaturated insertion is the existing exposure publication path;
        // only the newly introduced CLOCK sweep needs extra maintenance work.
        assert_eq!(cache.borrow().values.len(),1);assert_eq!(machine.exposure_fuel.get(),Some(0));
    }
    #[test]
    fn hot_certified_exposure_survives_cold_churn_at_the_same_capacity() {
        let mut exprs=IdTable::default();let levels=IdTable::default();
        for i in 0..8320 {exprs.insert(ExprId(i),Expr::Const{name:NameId(i),levels:vec![]}).unwrap();}
        let cache=new_exposure_cache();
        let machine=Machine::new(AuthorityId(1),&exprs,&levels,HashMap::new()).with_exposure_cache(cache.clone());
        let term=|i|Closure::new(ExprId(i),EnvFrame::empty());
        for i in 0..8192 {assert!(machine.expose(term(i),Transparency::Full,8).is_proven());}
        for i in 8192..8320 {
            assert!(machine.expose(term(0),Transparency::Full,1).is_proven());
            assert!(machine.expose(term(i),Transparency::Full,8).is_proven());
            assert_eq!(cache.borrow().values.len(),8192);
            assert!(cache.borrow().values.keys().any(|k|k.exact.1==term(0)),"a hot source proof was discarded by cold churn");
        }
    }
}
