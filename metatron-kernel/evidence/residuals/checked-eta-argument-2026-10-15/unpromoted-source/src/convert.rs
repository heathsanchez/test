use std::rc::Rc;
use std::collections::{HashMap, HashSet};

use crate::id::ExprId;
use crate::judgment::Judgment;
use crate::level::level_equal;
use crate::machine::Transparency;
use crate::syntax::Expr;
use crate::typecheck::{RuleKAttempt, TypeChecker, TypeValue};
use crate::value::{Closure, EnvBinding, FreeId, Neutral, NeutralHead, Value};

pub(crate) struct ProvenDomainPair<'a> {left:&'a Closure,right:&'a Closure,context:&'a [TypeValue],body_context:&'a Rc<Vec<TypeValue>>}
impl ProvenDomainPair<'_>{pub(crate) fn is_for(&self,left:&Closure,right:&Closure,context:&[TypeValue])->bool{std::ptr::eq(self.left,left)&&std::ptr::eq(self.right,right)&&std::ptr::eq(self.context,context)}
 pub(crate) fn completed_body_context(&self)->&Rc<Vec<TypeValue>>{self.body_context}
}
type ComparisonWork=(TypeValue,TypeValue,usize,Rc<Vec<TypeValue>>);
struct DomainContinuation {left_domain:Closure,right_domain:Closure,left_body:Closure,right_body:Closure,depth:usize,context:Rc<Vec<TypeValue>>,body_context:Rc<Vec<TypeValue>>,free:FreeId,audit:usize,parent_audit:Option<usize>}
struct FixedDomainContinuation {left_domain:Closure,right_domain:Closure,left_body:TypeValue,right_body:TypeValue,left_binder:FreeId,right_binder:FreeId,left_owner:crate::value::EnvFrame,right_owner:crate::value::EnvFrame,context:Rc<Vec<TypeValue>>,body_context:Rc<Vec<TypeValue>>,free:FreeId,depth:usize,audit:usize,parent_audit:Option<usize>}
struct AppProofFallback {left:Closure,right:Closure,context:Vec<TypeValue>,checkpoint:usize,audit:Option<usize>}
enum ConversionWork {Compare(ComparisonWork,Option<usize>),OpenPairedBinder(DomainContinuation),OpenFixedBinder(FixedDomainContinuation),FinishAppProof(usize)}
struct DomainAudit {parent:Option<usize>,incomplete_visit:bool}
struct ConversionWorkList {items:Vec<ConversionWork>,current_audit:Option<usize>,audits:Vec<DomainAudit>,app_proof_fallbacks:Vec<AppProofFallback>}
impl ConversionWorkList {
    fn new<C:Into<Rc<Vec<TypeValue>>>>(root:(TypeValue,TypeValue,usize,C))->Self{let(a,b,d,c)=root;let root=(a,b,d,c.into());Self{items:vec![ConversionWork::Compare(root,None)],current_audit:None,audits:Vec::new(),app_proof_fallbacks:Vec::new()}}
    fn defer_app_proof(&mut self,left:&Closure,right:&Closure,context:&[TypeValue]) {
        let id=self.app_proof_fallbacks.len();
        self.app_proof_fallbacks.push(AppProofFallback{left:left.clone(),right:right.clone(),context:context.to_vec(),checkpoint:self.items.len(),audit:self.current_audit});
        self.items.push(ConversionWork::FinishAppProof(id));
    }
    fn finish_app_proof(&mut self,id:usize){debug_assert_eq!(self.app_proof_fallbacks.len(),id+1);self.app_proof_fallbacks.truncate(id);}
    fn retry_app_proof(&mut self,checker:&TypeChecker<'_>,remaining:&mut usize)->bool {
        for id in (0..self.app_proof_fallbacks.len()).rev() {
            let saved=&self.app_proof_fallbacks[id];
            if checker.checked_owned_proof_source_pair(&saved.left,&saved.right,&saved.context,remaining) {
                let checkpoint=saved.checkpoint;let audit=saved.audit;
                self.items.truncate(checkpoint);self.app_proof_fallbacks.truncate(id);self.current_audit=audit;
                return true;
            }
        }
        false
    }
    fn push<C:Into<Rc<Vec<TypeValue>>>>(&mut self,work:(TypeValue,TypeValue,usize,C)){let(a,b,d,c)=work;let work=(a,b,d,c.into());self.items.push(ConversionWork::Compare(work,self.current_audit));}
 fn extend<C:Into<Rc<Vec<TypeValue>>>>(&mut self,work:impl IntoIterator<Item=(TypeValue,TypeValue,usize,C)>){for pair in work{self.push(pair);}}
 fn pop(&mut self)->Option<ConversionWork>{self.items.pop()}
 fn note_incomplete_visit(&mut self){let mut next=self.current_audit;while let Some(id)=next{self.audits[id].incomplete_visit=true;next=self.audits[id].parent;}}
 fn defer_domain(&mut self,mut c:DomainContinuation){let id=self.audits.len();self.audits.push(DomainAudit{parent:self.current_audit,incomplete_visit:false});c.audit=id;c.parent_audit=self.current_audit;let pair=(TypeValue::Term(c.left_domain.clone()),TypeValue::Term(c.right_domain.clone()),c.depth,c.context.clone());self.items.push(ConversionWork::OpenPairedBinder(c));self.items.push(ConversionWork::Compare(pair,Some(id)));}
 fn defer_fixed_domain(&mut self,mut c:FixedDomainContinuation){let id=self.audits.len();self.audits.push(DomainAudit{parent:self.current_audit,incomplete_visit:false});c.audit=id;c.parent_audit=self.current_audit;let pair=(TypeValue::Term(c.left_domain.clone()),TypeValue::Term(c.right_domain.clone()),c.depth,c.context.clone());self.items.push(ConversionWork::OpenFixedBinder(c));self.items.push(ConversionWork::Compare(pair,Some(id)));}
}

type ConversionVisitKey = (crate::machine::AuthorityId, TypeValue, TypeValue);
const INLINE_CONVERSION_VISIT_CAPACITY: usize = 8;
const CHEAP_PROJECTION_CONGRUENCE_BUDGET: usize = 64;

struct ConversionVisitSet {
    inline: [Option<ConversionVisitKey>; INLINE_CONVERSION_VISIT_CAPACITY],
    len: usize,
    overflow: Option<HashSet<ConversionVisitKey>>,
}

impl ConversionVisitSet {
    #[inline]
    fn new() -> Self {
        Self {
            inline: std::array::from_fn(|_| None),
            len: 0,
            overflow: None,
        }
    }

    #[inline]
    fn insert(&mut self, key: ConversionVisitKey) -> bool {
        if let Some(overflow) = self.overflow.as_mut() {
            return overflow.insert(key);
        }
        if self.inline[..self.len]
            .iter()
            .flatten()
            .any(|existing| existing == &key)
        {
            return false;
        }
        if self.len < INLINE_CONVERSION_VISIT_CAPACITY {
            self.inline[self.len] = Some(key);
            self.len += 1;
            return true;
        }

        let mut overflow = HashSet::with_capacity(INLINE_CONVERSION_VISIT_CAPACITY * 2);
        for slot in &mut self.inline[..self.len] {
            overflow.insert(slot.take().expect("initialized conversion visit slot"));
        }
        let inserted = overflow.insert(key);
        self.overflow = Some(overflow);
        inserted
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DeltaPolicy {
    PreferredOnly,
    GuardedSemanticFallback,
}

#[cfg(test)]
use std::cell::Cell;

#[cfg(test)]
thread_local! {
    static TRUSTED_CONVERSION_CALLS: Cell<u64> = const { Cell::new(0) };
}

pub fn convert(
    checker: &TypeChecker<'_>,
    left: &TypeValue,
    right: &TypeValue,
    budget: usize,
) -> Judgment<()> {
    convert_with_policy(
        checker,
        left,
        right,
        budget,
        DeltaPolicy::GuardedSemanticFallback,
    )
}

pub fn convert_with_policy(
    checker: &TypeChecker<'_>,
    left: &TypeValue,
    right: &TypeValue,
    budget: usize,
    delta_policy: DeltaPolicy,
) -> Judgment<()> {
    convert_with_policy_at_depth(checker, left, right, budget, delta_policy, 0)
}

pub(crate) fn convert_with_policy_at_depth(
    checker: &TypeChecker<'_>,
    left: &TypeValue,
    right: &TypeValue,
    budget: usize,
    delta_policy: DeltaPolicy,
    initial_depth: usize,
) -> Judgment<()> {
    convert_with_policy_in_context(
        checker,
        left,
        right,
        budget,
        delta_policy,
        initial_depth,
        &[],
    )
}

pub(crate) fn convert_with_policy_in_context(
    checker: &TypeChecker<'_>,
    left: &TypeValue,
    right: &TypeValue,
    budget: usize,
    delta_policy: DeltaPolicy,
    initial_depth: usize,
    context: &[TypeValue],
) -> Judgment<()> {
    let mut congruence_attempts = 32;
    convert_in_context_with_congruence(
        checker, left, right, budget, delta_policy, initial_depth, context, 0,
        &mut congruence_attempts,
    )
}

fn convert_in_context_with_congruence(
    checker: &TypeChecker<'_>,
    left: &TypeValue,
    right: &TypeValue,
    budget: usize,
    delta_policy: DeltaPolicy,
    initial_depth: usize,
    context: &[TypeValue],
    congruence_depth: usize,
    congruence_attempts: &mut usize,
) -> Judgment<()> {
    #[cfg(test)]
    TRUSTED_CONVERSION_CALLS.with(|calls| calls.set(calls.get() + 1));
    #[cfg(feature = "diagnostics")]
    crate::diagnostics::conversion();

    let mut remaining = budget;
    let mut work=ConversionWorkList::new((left.clone(),right.clone(),initial_depth,context.to_vec()));
    let mut visited = ConversionVisitSet::new();
    let mut unit_like_frees = HashMap::new();
    let mut proposition_frees:HashSet<FreeId> = HashSet::new();
    let mut proof_frees = HashMap::new();
    let mut proof_function_frees = HashMap::new();
    let mut lazy_head_delta_used = false;

    'conversion: while let Some(event) = work.pop() {
        macro_rules! failed_comparison {($result:expr)=>{{
            let result=$result;
            if work.retry_app_proof(checker,&mut remaining) {
                // Failed descendant visits completed no conversion judgment.
                visited=ConversionVisitSet::new();
                continue 'conversion;
            }
            return result;
        }};}

        let (left,right,depth,local_context)=match event {
            ConversionWork::FinishAppProof(id)=>{work.finish_app_proof(id);continue;},
            ConversionWork::Compare(pair,audit)=>{work.current_audit=audit;pair},
            ConversionWork::OpenPairedBinder(c)=>{
                work.current_audit=c.parent_audit;
                if remaining==0{failed_comparison!(Judgment::unknown("domain-continuation-budget"));}remaining-=1;
                if work.audits[c.audit].incomplete_visit{failed_comparison!(Judgment::unknown("domain-completion-unavailable"));}
                let proven=ProvenDomainPair{left:&c.left_domain,right:&c.right_domain,context:c.context.as_slice(),body_context:&c.body_context};
                let Some((left,right))=checker.checked_proven_domain_joint_opening(&proven,&c.left_domain,&c.right_domain,&c.left_body,&c.right_body,&c.context,c.free,&mut remaining)else{failed_comparison!(Judgment::unknown("domain-owned-opening-unavailable"));};
                work.push((TypeValue::Term(left),TypeValue::Term(right),c.depth.saturating_add(1),c.body_context));continue;
            },
            ConversionWork::OpenFixedBinder(c)=>{
                work.current_audit=c.parent_audit;
                if remaining==0{failed_comparison!(Judgment::unknown("fixed-domain-continuation-budget"));}remaining-=1;
                if work.audits[c.audit].incomplete_visit{failed_comparison!(Judgment::unknown("fixed-domain-completion-unavailable"));}
                let proven=ProvenDomainPair{left:&c.left_domain,right:&c.right_domain,context:c.context.as_slice(),body_context:&c.body_context};
                let Some((left,right))=checker.checked_fixed_pi_joint_bodies(&proven,&c.left_domain,&c.right_domain,&c.left_body,&c.right_body,c.left_binder,c.right_binder,&c.left_owner,&c.right_owner,&c.context,c.free,&mut remaining)else{failed_comparison!(Judgment::unknown("fixed-domain-owned-opening-unavailable"));};
                work.push((left,right,c.depth.saturating_add(1),c.body_context));continue;
            },
        };
        let context = local_context.as_slice();
        if left == right {
            continue;
        }
        if remaining == 0 {
            failed_comparison!(Judgment::unknown("conversion-budget-exhausted"));
        }
        remaining -= 1;
        if !visited.insert((checker.authority(),left.clone(),right.clone()))&&work.current_audit.is_none(){work.note_incomplete_visit();continue;}

        // A real captured substitution has an ordinary exposure step before
        // any optional proof classification. This paid eligibility lookup
        // grants no typing or equality authority; the saved original sources
        // still undergo strict proof checking if ordinary conversion fails.
        let defer_app_proof=depth==context.len()&&match (&left,&right) {
            (TypeValue::Term(lhs),TypeValue::Term(rhs))=>{
                let both_apps=matches!(checker.expression(lhs.expr),Some(Expr::App{..}))
                    &&matches!(checker.expression(rhs.expr),Some(Expr::App{..}));
                let mut captured_substitution=|source:&Closure| {
                    let Some(Expr::BVar(index))=checker.expression(source.expr)else{return false;};
                    let Some(cost)=index.checked_add(1).and_then(|cost|usize::try_from(cost).ok())else{return false;};
                    if remaining<cost{return false;}remaining-=cost;
                    matches!(source.env.lookup_binding_ref(*index),Some(EnvBinding::Closure(_)))
                };
                both_apps||captured_substitution(lhs)||captured_substitution(rhs)
            },
            _=>false,
        };
        if defer_app_proof && let (TypeValue::Term(lhs),TypeValue::Term(rhs))=(&left,&right) {
            work.defer_app_proof(lhs,rhs,context);
        }

        // Equal source syntax is sufficient only after every used capture
        // and universe is independently identical. Unused frame slots carry
        // no equality authority; incomplete support must decline this trial.
        if let (TypeValue::Term(lhs), TypeValue::Term(rhs)) = (&left, &right)
            && lhs.env != rhs.env
            // Root bound variables already have an ordinary actual-capture
            // exposure path. Avoid spending its allowance on an optional
            // transitive syntax/capture-identity trial before that exposure.
            && !matches!(checker.expression(lhs.expr),Some(crate::syntax::Expr::BVar(_)))
            && !matches!(checker.expression(rhs.expr),Some(crate::syntax::Expr::BVar(_)))
            && remaining > 8 && *congruence_attempts > 0
        {
            *congruence_attempts -= 1;
            let allowance = remaining.min(1024);
            let mut trial = allowance;
            let identical = checker.exact_source_capture_identity(lhs, rhs, &mut trial);
            remaining -= allowance.saturating_sub(trial);
            if identical { continue; }
        }

        // Residual-generated function eta capability.  This is deliberately
        // syntactic and contraction-only: (fun x => f x) may contract to f
        // exactly when the bound variable does not occur in f.  No unfolding,
        // structure eta authority is introduced here; proof irrelevance, when
        // available, is a separately guarded typed-binder consequence below.
        if let (TypeValue::Term(left_term), TypeValue::Term(right_term)) = (&left, &right) {
            if let Some(contracted) = eta_contract(checker, left_term, depth) {
                work.push((
                    TypeValue::Term(contracted),
                    TypeValue::Term(right_term.clone()),
                    depth,
                    local_context.clone(),
                ));
                continue;
            }
            if let Some(contracted) = eta_contract(checker, right_term, depth) {
                work.push((
                    TypeValue::Term(left_term.clone()),
                    TypeValue::Term(contracted),
                    depth,
                    local_context.clone(),
                ));
                continue;
            }
        }

        if let (TypeValue::Term(left_term), TypeValue::Term(right_term)) = (&left, &right)
            && checker.checked_transport_proof_pair(left_term, right_term, context, &mut remaining)
        {
            continue;
        }

        if let (TypeValue::Term(left_term), TypeValue::Term(right_term)) = (&left, &right)
            && false && checker.proof_terms_same_proposition(left_term, right_term, context, remaining)
        {
            continue;
        }

        if depth == context.len()
            && let (TypeValue::Term(lhs), TypeValue::Term(rhs)) = (&left, &right)
            && !defer_app_proof
            && checker.checked_owned_proof_source_pair(lhs, rhs, context, &mut remaining) {
            continue;
        }

        // Lean proof irrelevance after *independent* proposition formation
        // and exact type conversion. Unlike a FreeId shortcut this checks
        // the theorem application's argument before certifying a proof.
        if depth == context.len()
            && let (TypeValue::Term(lhs),TypeValue::Term(rhs))=(&left,&right)
            && false && checker.checked_proof_vs_local_in_context(lhs,rhs,context,remaining)
        {
            continue;
        }

        if let (TypeValue::Term(left_term), TypeValue::Term(right_term)) = (&left, &right)
            && unit_like_free_pair(checker, left_term, right_term, &unit_like_frees, remaining)
        {
            continue;
        }

        if depth == context.len()
            && let (TypeValue::Term(left_term), TypeValue::Term(right_term)) = (&left, &right)
            && matches!(checker.expression(left_term.expr),Some(Expr::BVar(_)))
            && matches!(checker.expression(right_term.expr),Some(Expr::BVar(_)))
            && checker.checked_unit_like_source_pair(left_term,right_term,context,&mut remaining)
        {
            continue;
        }

        if let (TypeValue::Term(left_term), TypeValue::Term(right_term)) = (&left, &right)
            && proof_free_pair(checker, left_term, right_term, &proof_frees, remaining)
        {
            continue;
        }

        if let (TypeValue::Term(left_term), TypeValue::Term(right_term)) = (&left, &right)
            && fixed_proof_function_application_pair(
                checker,
                left_term,
                right_term,
                &proof_function_frees,
                remaining,
            )
        {
            continue;
        }

        if depth == context.len()
            && distinct_rigid_local_terms(checker, &left, &right, context, remaining)
        {
            failed_comparison!(Judgment::refuted("distinct-rigid-local-terms"));
        }

        match (left, right) {
            (TypeValue::Sort(left), TypeValue::Sort(right)) => {
                match level_equal(left, right, remaining) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { obstruction } => {
                        failed_comparison!(Judgment::Refuted { obstruction });
                    }
                    Judgment::Unknown { residual } => failed_comparison!(Judgment::Unknown { residual }),
                }
            }
            (
                TypeValue::Pi {
                    domain: left_domain,
                    body: left_body,
                    binder: left_binder,
                 binder_owner: left_owner,},
                TypeValue::Pi {
                    domain: right_domain,
                    body: right_body,
                    binder: right_binder,
                 binder_owner: right_owner,},
            ) => {
                let Some(free) = fresh_local(depth) else {
                    failed_comparison!(Judgment::unknown("binder-depth-overflow"));
                };
                let (Some(left_owner),Some(right_owner),TypeValue::Term(left_domain),TypeValue::Term(right_domain))=(left_owner,right_owner,*left_domain,*right_domain)else{failed_comparison!(Judgment::unknown("fixed-pi-source-owner-unavailable"));};
                let mut body_context=local_context.as_ref().clone();if body_context.len()!=depth{failed_comparison!(Judgment::unknown("fixed-pi-source-context-unavailable"));}body_context.push(TypeValue::Term(left_domain.clone()));
                work.defer_fixed_domain(FixedDomainContinuation{left_domain,right_domain,left_body:*left_body,right_body:*right_body,left_binder,right_binder,left_owner,right_owner,context:local_context,body_context:Rc::new(body_context),free,depth,audit:0,parent_audit:None});
            }
            (TypeValue::Term(left), TypeValue::Term(right)) => {
                if delta_policy == DeltaPolicy::GuardedSemanticFallback
                    && let (Some(left_literal), Some(right_literal)) = (
                        checker.captured_string_literal(&left, remaining),
                        checker.captured_string_literal(&right, remaining),
                    )
                    && left_literal == right_literal
                {
                    continue;
                }
                let machine = checker.machine();
                let mut unfold_parent = false;
                // Positive congruence before unfolding. Failed premises only
                // decline this rule; all nested probes share an attempt limit.
                if congruence_depth < 16 && *congruence_attempts > 0 {
                    *congruence_attempts -= 1;
                    let probe_budget = remaining;
                    let opaque_left = machine.expose(left.clone(), Transparency::Opaque, probe_budget);
                    let opaque_right = machine.expose(right.clone(), Transparency::Opaque, probe_budget);
                    if let (Some(Value::Neutral(lhs)), Some(Value::Neutral(rhs))) =
                        (opaque_left.proven_value(), opaque_right.proven_value())
                        && let (
                            NeutralHead::Const { name: left_name, .. },
                            NeutralHead::Const { name: right_name, .. },
                        ) = (&lhs.head, &rhs.head)
                        && left_name == right_name
                        && definition_arguments_used(checker, *left_name, lhs.spine.len())
                        && !lhs.spine.is_empty()
                        && lhs.spine.len() == rhs.spine.len()
                        && compare_neutral_heads(checker, lhs, rhs, probe_budget, depth, context).is_proven()
                        && lhs.spine.iter().zip(&rhs.spine).rev().all(|(left_arg, right_arg)| {
                            convert_in_context_with_congruence(
                                checker,
                                &TypeValue::Term(left_arg.clone()),
                                &TypeValue::Term(right_arg.clone()),
                                probe_budget / lhs.spine.len(),
                                delta_policy,
                                depth,
                                context,
                                congruence_depth + 1,
                                congruence_attempts,
                            ).is_proven()
                        })
                    {
                        continue;
                    }
                }
                if delta_policy == DeltaPolicy::GuardedSemanticFallback
                    && let Some((rigid_head, congruence)) =
                        rigid_application_head_congruence(checker, &left, &right, remaining)
                {
                    if congruence.is_proven() {
                        continue;
                    }
                    // Unequal arguments are not an inequality proof for a
                    // reducible function. Compare its actual applications
                    // after delta instead of committing those argument goals.
                    unfold_parent = checker.definition_value(rigid_head).is_some();
                    if let Judgment::Refuted { obstruction } = &congruence
                        && checker.is_certified_constructor(rigid_head)
                    {
                        // Injectivity lets us transport a genuinely rigid
                        // argument inequivalence to the constructor result.
                        // A PreferredOnly mismatch alone is NOT such evidence:
                        // an argument may reduce under guarded/full delta or
                        // recursor iota. This previously misclassified two
                        // valid Nat.mod_lt exports as REJECT.
                        #[cfg(feature = "diagnostics")]
                        if std::env::var_os("NUCLEUS_TRACE_CONSTRUCTOR_MISMATCH").is_some() {
                            eprintln!(
                                "NUCLEUS_CONSTRUCTOR_MISMATCH:head={rigid_head:?}:depth={depth}:obstruction={obstruction:?}"
                            );
                        }
                        if matches!(
                            obstruction.0,
                            "distinct-canonical-universes"
                                | "distinct-Nat-literals"
                                | "rigid-value-constructor-mismatch"
                                | "distinct-opaque-proposition-types"
                        ) {
                            failed_comparison!(Judgment::refuted("certified-constructor-argument-mismatch"));
                        }
                        // This is not yet a mismatch, nor grounds for an
                        // early UNKNOWN. Continue to the ordinary guarded
                        // comparison below. In particular Full exposure may
                        // apply an already-certified Nat.rec iota rule when
                        // its captured major argument is canonical zero.
                        #[cfg(feature = "diagnostics")]
                        if std::env::var_os("NUCLEUS_TRACE_NATREC_MAJOR").is_some() {
                            eprintln!(
                                "NUCLEUS_CONSTRUCTOR_FALLTHROUGH:depth={depth}:head={rigid_head:?}:obstruction={obstruction:?}"
                            );
                        }
                    }
                    if !congruence.is_refuted()
                        && !lazy_head_delta_used
                        && remaining > INLINE_CONVERSION_VISIT_CAPACITY
                        && let (Some(left_delta), Some(right_delta)) = (
                            machine
                                .expose_head_delta_for_conversion(left.clone(), remaining.min(64)),
                            machine
                                .expose_head_delta_for_conversion(right.clone(), remaining.min(64)),
                        )
                    {
                        lazy_head_delta_used = true;
                        if std::env::var_os("NUCLEUS_TRACE_LAZY_DELTA").is_some() {
                            eprintln!(
                                "NUCLEUS_LAZY_HEAD_DELTA:left={:?}:right={:?}:budget={remaining}",
                                left.expr, right.expr
                            );
                        }
                        if let (Some(left_delta), Some(right_delta)) =
                            (left_delta.proven_value(), right_delta.proven_value())
                        {
                            match compare_values(
                                checker,
                                left_delta,
                                right_delta,
                                remaining.saturating_sub(1),
                                depth,
                                context,
                                &mut work,
                                &mut proof_function_frees,
                            ) {
                                Judgment::Proven { .. } => continue,
                                Judgment::Refuted { obstruction } => {
                                    failed_comparison!(Judgment::Refuted { obstruction });
                                }
                                Judgment::Unknown { residual } => {
                                    failed_comparison!(Judgment::Unknown { residual });
                                }
                            }
                        } else {
                            // This optional bounded shortcut established no
                            // value comparison. Pay both attempted exposures
                            // and continue the ordinary guarded derivation.
                            let spent = remaining.min(64).saturating_mul(2);
                            remaining = remaining.saturating_sub(spent);
                        }
                    }
                }
                let cheap_left =
                    machine.expose_for_conversion(left.clone(), if unfold_parent { Transparency::Full } else { Transparency::Reducible }, remaining);
                let cheap_right = machine.expose_for_conversion(
                    right.clone(),
                    if unfold_parent { Transparency::Full } else { Transparency::Reducible },
                    remaining,
                );
                let (Some(cheap_left), Some(cheap_right)) =
                    (cheap_left.proven_value(), cheap_right.proven_value())
                else {
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_LITERAL_CONVERSION").is_some() {
                        eprintln!("NUCLEUS_LITERAL_CONVERSION:left={left:?}:syntax={:?}:result={cheap_left:?}:right={right:?}:syntax={:?}:result={cheap_right:?}",checker.expression(left.expr),checker.expression(right.expr));
                    }
                    failed_comparison!(Judgment::unknown("conversion-exposure"));
                };
                if depth==context.len()&&let Some(relation)=checker.checked_source_structure_relation(&left,&right,cheap_left,cheap_right,context,&mut remaining){
                    if relation.is_proven(){continue;}failed_comparison!(relation);
                }
                if let Some(relation)=source_qualified_free_eta(checker,&left,&right,cheap_left,cheap_right,context,depth,&mut remaining){if relation.is_proven(){continue;}failed_comparison!(relation);}
                match compare_values(
                    checker,
                    cheap_left,
                    cheap_right,
                    remaining,
                    depth,
                    context,
                    &mut work,
                    &mut proof_function_frees,
                ) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { .. } | Judgment::Unknown { .. }
                        if delta_policy == DeltaPolicy::GuardedSemanticFallback =>
                    {
                        let full_left =
                            machine.expose_for_conversion(left.clone(), Transparency::Full, remaining);
                        let full_right =
                            machine.expose_for_conversion(right.clone(), Transparency::Full, remaining);
                        let (Some(full_left), Some(full_right)) =
                            (full_left.proven_value(), full_right.proven_value())
                        else {
                            failed_comparison!(Judgment::unknown("full-conversion-exposure"));
                        };
                if depth==context.len()&&let Some(relation)=checker.checked_source_structure_relation(&left,&right,full_left,full_right,context,&mut remaining){
                    if relation.is_proven(){continue;}failed_comparison!(relation);
                }
                        if let Some(relation)=source_qualified_free_eta(checker,&left,&right,full_left,full_right,context,depth,&mut remaining){if relation.is_proven(){continue;}failed_comparison!(relation);}
                        match compare_values(
                            checker,
                            full_left,
                            full_right,
                            remaining,
                            depth,
                            context,
                            &mut work,
                            &mut proof_function_frees,
                        ) {
                            Judgment::Proven { .. } => {}
                            Judgment::Refuted { obstruction } => {
                                failed_comparison!(Judgment::Refuted { obstruction });
                            }
                            Judgment::Unknown { residual } => {
                                failed_comparison!(Judgment::Unknown { residual });
                            }
                        }
                    }
                    Judgment::Refuted { obstruction } => {
                        failed_comparison!(Judgment::Refuted { obstruction });
                    }
                    Judgment::Unknown { residual } => failed_comparison!(Judgment::Unknown { residual }),
                }
            }
            (TypeValue::Term(term), other) | (other, TypeValue::Term(term)) => {
                let machine = checker.machine();
                let exposed = machine.expose(term.clone(), Transparency::Reducible, remaining);
                let exposed = if exposed.is_unknown() && depth == context.len()
                    && delta_policy == DeltaPolicy::GuardedSemanticFallback
                {
                    checked_source_type_value(checker, term.clone(), context, remaining)
                } else {
                    exposed
                };
                let Some(exposed) = exposed.proven_value() else {
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_RIGID_TYPE_MISMATCH").is_some() {
                        eprintln!("NUCLEUS_TYPE_EXPOSURE_UNKNOWN:term={term:?}:budget={remaining}:result={exposed:?}");
                    }
                    failed_comparison!(Judgment::unknown("conversion-exposure"));
                };
                let exposed = if let Some(exposed) = value_as_type(checker, exposed, &term, context, depth, &mut remaining) {
                    exposed
                } else if delta_policy == DeltaPolicy::GuardedSemanticFallback {
                    let full = machine.expose(term.clone(), Transparency::Full, remaining);
                    let Some(full) = full.proven_value() else {
                        failed_comparison!(Judgment::unknown("full-conversion-exposure"));
                    };
                    let recovered = if depth == context.len() && value_as_type(checker, full, &term, context, depth, &mut remaining).is_none() {
                        checked_source_type_value(checker, term.clone(), context, remaining)
                    } else {
                        Judgment::unknown("checked-source-type-recovery-not-needed")
                    };
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_SOURCE_TYPE_RECOVERY").is_some() {
                        eprintln!("NUCLEUS_SOURCE_TYPE_RECOVERY:term={:?}:result={recovered:?}",term.expr);
                    }
                    let full = recovered.proven_value().unwrap_or(full);
                    let Some(full) = value_as_type(checker, full, &term, context, depth, &mut remaining) else {
                        #[cfg(feature="diagnostics")]
                        if std::env::var_os("NUCLEUS_TRACE_RIGID_TYPE_MISMATCH").is_some() {
                            eprintln!("NUCLEUS_RIGID_TYPE_MISMATCH:depth={depth}:context={}:exposed={full:?}:expected={other:?}:budget={remaining}",context.len());
                            if let Value::Neutral(n)=full {
                                eprintln!("NUCLEUS_RIGID_TYPE_MAJOR:{}",checker.diagnostic_captured_recursor_major_chain(n,remaining));
                            }
                        }
                        failed_comparison!(Judgment::refuted("rigid-type-constructor-mismatch"));
                    };
                    full
                } else {
                    failed_comparison!(Judgment::refuted("rigid-type-constructor-mismatch"));
                };
                work.push((exposed, other, depth, local_context));
            }
            (TypeValue::Sort(_), TypeValue::Pi { .. })
            | (TypeValue::Pi { .. }, TypeValue::Sort(_)) => {
                failed_comparison!(Judgment::refuted("rigid-type-constructor-mismatch"));
            }
        }
    }

    Judgment::proven((), "guarded-relational-conversion")
}

#[cfg(test)]
pub(crate) fn reset_test_conversion_calls() {
    TRUSTED_CONVERSION_CALLS.with(|calls| calls.set(0));
}

#[cfg(test)]
pub(crate) fn test_conversion_calls() -> u64 {
    TRUSTED_CONVERSION_CALLS.with(Cell::get)
}

fn distinct_rigid_local_terms(
    checker: &TypeChecker<'_>,
    left: &TypeValue,
    right: &TypeValue,
    context: &[TypeValue],
    budget: usize,
) -> bool {
    // Original source typing is unavailable at this evaluated-only site.
    false
}

fn opaque_free(checker: &TypeChecker<'_>, ty: &TypeValue, budget: usize) -> Option<FreeId> {
    let TypeValue::Term(closure) = ty else {
        return None;
    };
    let exposed = checker
        .machine()
        .expose(closure.clone(), Transparency::Opaque, budget.min(32));
    let Value::Neutral(neutral) = exposed.proven_value()? else {
        return None;
    };
    if !neutral.spine.is_empty() {
        return None;
    }
    let NeutralHead::Free(free, _) = neutral.head else {
        return None;
    };
    Some(free)
}

fn bare_free_type(checker: &TypeChecker<'_>, ty: &TypeValue, budget: usize) -> Option<FreeId> {
    let TypeValue::Term(closure) = ty else {
        return None;
    };
    let exposed = checker
        .machine()
        .expose(closure.clone(), Transparency::Reducible, budget);
    let Value::Neutral(neutral) = exposed.proven_value()? else {
        return None;
    };
    if !neutral.spine.is_empty() {
        return None;
    }
    let NeutralHead::Free(free, _) = neutral.head else {
        return None;
    };
    Some(free)
}

fn fixed_proof_function_application_pair(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    proof_functions: &HashMap<FreeId, (crate::id::NameId, Vec<crate::level::LevelTerm>)>,
    budget: usize,
) -> bool {
    // Original source typing is unavailable at this evaluated-only site.
    false
}

fn proof_free_pair(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    proof_frees: &HashMap<FreeId, FreeId>,
    budget: usize,
) -> bool {
    // Original source typing is unavailable at this evaluated-only site.
    false
}

fn unit_like_free_pair(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    unit_like_frees: &HashMap<FreeId, (crate::id::NameId, Vec<crate::level::LevelTerm>)>,
    budget: usize,
) -> bool {
    // Original source typing is unavailable at this evaluated-only site.
    false
}

fn eta_contract(checker: &TypeChecker<'_>, closure: &Closure, depth: usize) -> Option<Closure> {
    let closure = resolve_local_closure(checker, closure)?;
    let Expr::Lam { body, .. } = checker.expression(closure.expr)? else {
        return None;
    };
    if std::env::var_os("NUCLEUS_TRACE_ETA").is_some() {
        eprintln!(
            "NUCLEUS_ETA_BODY:closure={:?}:body={:?}:body_expr={:?}",
            closure,
            body,
            checker.expression(*body)
        );
    }
    let Expr::App { fun, arg } = checker.expression(*body)? else {
        return None;
    };
    if !matches!(checker.expression(*arg), Some(Expr::BVar(0))) {
        return None;
    }
    if expression_uses_bvar(checker, *fun, 0, 512) {
        return None;
    }
    let free = fresh_local(depth)?;
    Some(closure.sibling(*fun, closure.env.extend_free(free)))
}

// Evaluated function eta for a bare local function versus an explicit lambda.
// This is the semantic counterpart of eta_contract above: it is admitted only
// when evaluating the lambda body under a fresh local yields exactly f x, where
// f is the same bare local function and x is that fresh local.  The local's
// declared Pi domain is still compared through the ordinary conversion worklist.
pub(crate) fn source_qualified_free_eta(checker:&TypeChecker<'_>,left_source:&Closure,right_source:&Closure,left:&Value,right:&Value,context:&[TypeValue],depth:usize,remaining:&mut usize)->Option<Judgment<()>> {
    let (lambda_source,function_source,neutral,domain,body)=match (left,right) {
        (Value::Lam{domain,body},Value::Neutral(n))=>(left_source,right_source,n,domain,body),
        (Value::Neutral(n),Value::Lam{domain,body})=>(right_source,left_source,n,domain,body),_=>return None,
    };
    if !neutral.spine.is_empty()||!matches!(neutral.head,NeutralHead::Free(_,Some(_)))||depth!=context.len(){return None;}
    let Some(free)=fresh_local(depth)else{return None;};
    let Some(opened)=checker.checked_source_eta_opening(lambda_source,function_source,domain,body,context,free,remaining)else{return None;};
    let allowance=(*remaining).min(256);if allowance==0{return None;}*remaining-=allowance;
    let result=checker.machine().expose_for_conversion(opened.body().clone(),Transparency::Reducible,allowance);
    let Some(Value::Neutral(actual))=result.proven_value()else{return None;};
    if !actual.head.same_owned_free(&neutral.head)||actual.spine.len()!=1{return None;}
    let fresh=checker.eta_fresh_argument(&opened,remaining);
    let allowance=(*remaining).min(128);if allowance==0{return None;}*remaining-=allowance;
    if let Some(fresh)=fresh {
        let relation=crate::convert::convert_with_policy_in_context(checker,&TypeValue::Term(actual.spine[0].clone()),&TypeValue::Term(fresh),allowance,DeltaPolicy::GuardedSemanticFallback,opened.context().len(),opened.context());
        if relation.is_proven(){return Some(Judgment::proven((),"source-qualified-function-eta"));}
        if matches!(&relation,Judgment::Refuted{obstruction} if obstruction.0=="distinct-rigid-local-terms")&&checker.eta_body_result_is_rigid(&opened,remaining){return Some(relation);}
        return None;
    }
    let argument=checker.machine().expose_for_conversion(actual.spine[0].clone(),Transparency::Reducible,allowance);
    let Some(Value::Neutral(argument))=argument.proven_value()else{return None;};
    (argument.spine.is_empty()&&argument.head.same_owned_free(&NeutralHead::Free(free,Some(opened.body().env.clone())))).then(||Judgment::proven((),"source-qualified-function-eta"))
}

fn evaluated_free_eta(
    checker: &TypeChecker<'_>,
    neutral: &Neutral,
    lambda_domain: &Closure,
    lambda_body: &Closure,
    budget: usize,
    depth: usize,
    work: &mut ConversionWorkList,
    context: &[TypeValue],
) -> bool {
    // Original source typing is unavailable at this evaluated-only site.
    false
}

fn resolve_local_closure(checker: &TypeChecker<'_>, closure: &Closure) -> Option<Closure> {
    let mut current = closure.clone();
    for _ in 0..64 {
        match checker.expression(current.expr)? {
            Expr::BVar(index) => match current.env.lookup(*index)? {
                EnvBinding::Closure(bound) => current = bound,
                EnvBinding::Free(_) | EnvBinding::Neutral(_) | EnvBinding::NatLit(_) => return Some(current),
            },
            Expr::Let { value, body, .. } => {
                let value = current.sibling(*value, current.env.clone());
                current = current.sibling(*body, current.env.extend(value));
            }
            _ => return Some(current),
        }
    }
    None
}

// Skip speculative argument equality when direct beta reduction can erase an
// argument. This is only a cost gate; ordinary conversion remains authoritative.
fn definition_arguments_used(
    checker: &TypeChecker<'_>,
    name: crate::id::NameId,
    arity: usize,
) -> bool {
    let Some(mut expression) = checker.definition_value(name) else {
        return false;
    };
    for _ in 0..arity {
        let Some(Expr::Lam { body, .. }) = checker.expression(expression) else {
            return false;
        };
        if !expression_uses_bvar(checker, *body, 0, 64) {
            return false;
        }
        expression = *body;
    }
    true
}

fn expression_uses_bvar(
    checker: &TypeChecker<'_>,
    expression: ExprId,
    target: u64,
    budget: usize,
) -> bool {
    if budget == 0 {
        return true;
    }
    let Some(expression) = checker.expression(expression) else {
        return true;
    };
    let next = budget - 1;
    match expression {
        Expr::BVar(index) => *index == target,
        Expr::NatLit(_) | Expr::StrLit(_) | Expr::Sort(_) | Expr::Const { .. } => false,
        Expr::App { fun, arg } => {
            expression_uses_bvar(checker, *fun, target, next)
                || expression_uses_bvar(checker, *arg, target, next)
        }
        Expr::Lam { domain, body } | Expr::Pi { domain, body } => {
            expression_uses_bvar(checker, *domain, target, next)
                || expression_uses_bvar(checker, *body, target.saturating_add(1), next)
        }
        Expr::Let { ty, value, body } => {
            expression_uses_bvar(checker, *ty, target, next)
                || expression_uses_bvar(checker, *value, target, next)
                || expression_uses_bvar(checker, *body, target.saturating_add(1), next)
        }
        Expr::Proj { structure, .. } => expression_uses_bvar(checker, *structure, target, next),
    }
}

#[allow(clippy::too_many_arguments)]
fn certified_structure_eta(
    checker: &TypeChecker<'_>,
    target: &Neutral,
    constructed: &Neutral,
    budget: usize,
    depth: usize,
    work: &mut ConversionWorkList,
    context: &[TypeValue],
) -> bool {
    // Original source typing is unavailable at this evaluated-only site.
    false
}

fn rigid_local_non_eta_constructor_mismatch(
    checker: &TypeChecker<'_>,
    target: &Neutral,
    constructed: &Neutral,
    context: &[TypeValue],
    budget: usize,
) -> bool {
    // Original source typing is unavailable at this evaluated-only site.
    false
}

fn distinct_non_eta_structure_locals(
    checker: &TypeChecker<'_>,
    left: &Neutral,
    right: &Neutral,
    context: &[TypeValue],
    budget: usize,
) -> bool {
    // Original source typing is unavailable at this evaluated-only site.
    false
}

fn compare_values(
    checker: &TypeChecker<'_>,
    left: &Value,
    right: &Value,
    budget: usize,
    depth: usize,
    context: &[TypeValue],
    work: &mut ConversionWorkList,
    proof_function_frees: &mut HashMap<FreeId, (crate::id::NameId, Vec<crate::level::LevelTerm>)>,
) -> Judgment<()> {
    let mut current_left = left.clone();
    let mut current_right = right.clone();
    let mut current_budget = budget;
    loop {
        if matches!(&current_left,Value::Neutral(Neutral{head:NeutralHead::Free(_,None),..}))
            ||matches!(&current_right,Value::Neutral(Neutral{head:NeutralHead::Free(_,None),..})) {
            return Judgment::unknown("unowned-neutral-free-scope-unavailable");
        }
        match (&current_left, &current_right) {
            (Value::NatLit(left), Value::NatLit(right)) => {
                if left != right {
                    return Judgment::refuted("distinct-Nat-literals");
                }
            }
            (Value::NatLit(literal), Value::Neutral(neutral)) => {
                return compare_nat_literal_neutral(
                    checker,
                    literal,
                    neutral,
                    current_budget,
                    depth,
                    context,
                    work,
                    proof_function_frees,
                );
            }
            (Value::Neutral(neutral), Value::NatLit(literal)) => {
                return compare_nat_literal_neutral(
                    checker,
                    literal,
                    neutral,
                    current_budget,
                    depth,
                    context,
                    work,
                    proof_function_frees,
                );
            }
            (Value::Sort(left), Value::Sort(right)) => {
                work.push((
                    TypeValue::Sort(left.clone()),
                    TypeValue::Sort(right.clone()),
                    depth,
                    context.to_vec(),
                ));
            }
            (
                Value::Pi {
                    domain: left_domain,
                    body: left_body,
                },
                Value::Pi {
                    domain: right_domain,
                    body: right_body,
                },
            )
            | (
                Value::Lam {
                    domain: left_domain,
                    body: left_body,
                },
                Value::Lam {
                    domain: right_domain,
                    body: right_body,
                },
            ) => {
                let Some(free) = fresh_local(depth) else {
                    return Judgment::unknown("binder-depth-overflow");
                };
                let allowance = current_budget.min(1024);
                let mut opening_budget = allowance;
                if !source_opening_avoids_capture(checker, left_body, free, &mut opening_budget)
                    || !source_opening_avoids_capture(checker, right_body, free, &mut opening_budget) {
                    return Judgment::unknown("source-binder-capture-or-support-unavailable");
                }
                current_budget -= allowance - opening_budget;
                let left_domain_type = TypeValue::Term(left_domain.clone());
                let right_domain_type = TypeValue::Term(right_domain.clone());
                if let (Some(left_key), Some(right_key)) = (
                    checker.fixed_proof_function_type_key(&left_domain_type, current_budget),
                    checker.fixed_proof_function_type_key(&right_domain_type, current_budget),
                ) && left_key == right_key
                {
                    proof_function_frees.insert(free, left_key);
                }
                let mut body_context = context.to_vec();
                if body_context.len() == depth {
                    body_context.push(left_domain_type);
                }
                if let Some((left_opened,right_opened))=checker.checked_atomic_joint_opening(left_domain,right_domain,left_body,right_body,context,free,&mut current_budget){
                    work.push((TypeValue::Term(left_opened),TypeValue::Term(right_opened),depth.saturating_add(1),body_context));
                }else{
                    work.defer_domain(DomainContinuation{left_domain:left_domain.clone(),right_domain:right_domain.clone(),left_body:left_body.clone(),right_body:right_body.clone(),context:Rc::new(context.to_vec()),body_context:Rc::new(body_context),free,depth,audit:0,parent_audit:None});
                }
            }
            (
                Value::StuckProjection {
                    type_name: left_type,
                    index: left_index,
                    structure: left_structure,
                    spine: left_spine,
                },
                Value::StuckProjection {
                    type_name: right_type,
                    index: right_index,
                    structure: right_structure,
                    spine: right_spine,
                },
            ) if left_type == right_type && left_index == right_index => {
                // A checked projection of one fixed field is congruent only
                // after proving the receiver and all applied arguments equal.
                // The existing source-level Nat computation never licenses
                // identifying unrelated binder environments or Nat indices.
                let probe = (current_budget / 2).min(128);
                if probe >= 8
                    && left_spine.len() == right_spine.len()
                    && convert_with_policy_in_context(
                        checker,
                        &TypeValue::Term(left_structure.clone()),
                        &TypeValue::Term(right_structure.clone()),
                        probe,
                        DeltaPolicy::PreferredOnly,
                        depth,
                        context,
                    ).is_proven()
                    && left_spine.iter().zip(right_spine).all(|(lhs, rhs)| {
                        convert_with_policy_in_context(
                            checker,
                            &TypeValue::Term(lhs.clone()),
                            &TypeValue::Term(rhs.clone()),
                            probe,
                            DeltaPolicy::PreferredOnly,
                            depth,
                            context,
                        ).is_proven()
                    })
                {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_PROJECTION_CONGRUENCE").is_some() {
                        eprintln!("NUCLEUS_PROJECTION_CONGRUENCE:earned-certified-operands");
                    }
                    return Judgment::proven((), "certified-projection-congruence");
                }
                // Experimental: preserve the actual checked lexical context
                // for projection receiver/spine congruence. The context-free
                // fast path remains the production baseline. The new path is
                // permitted only when the local context matches its binder depth
                // and each argument conversion is independently PROVEN.
                let contextual = std::env::var_os(
                    "NUCLEUS_EXPERIMENTAL_PROJECTION_CONTEXT",
                ).is_some()
                    && depth == context.len()
                    && same_rigid_application_congruence_in_context(
                        checker, left_structure, right_structure,
                        current_budget, depth, context, CHEAP_PROJECTION_CONGRUENCE_BUDGET,
                    )
                    && same_closure_spine_congruence_in_context(
                        checker, left_spine, right_spine,
                        current_budget, depth, context, CHEAP_PROJECTION_CONGRUENCE_BUDGET,
                    );
                if contextual {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_PROJECTION_CONTEXT").is_some() {
                        eprintln!(
                            "NUCLEUS_CONTEXTUAL_PROJECTION:PROVEN:depth={depth}:receiver={left_structure:?}:opponent={right_structure:?}",
                        );
                    }
                    return Judgment::proven((), "checked-contextual-projection-congruence");
                }
                // Narrow second-stage budget: only paired projections with
                // the same original receiver syntax and universe instance,
                // under an explicit lexical context of at most two binders.
                // Unlike shape-based shortcuts, every recursor argument is
                // still independently proved definitionally equal by the
                // guarded converter with a bounded local budget.
                let deep_contextual =
                    std::env::var_os("NUCLEUS_EXPERIMENTAL_PROJECTION_CROSSFRAME_512")
                        .is_some()
                    && depth == context.len()
                    && depth <= 2
                    && *left_index == 0
                    && current_budget >= 256
                    && left_structure.expr == right_structure.expr
                    && left_structure.levels == right_structure.levels
                    && same_rigid_application_congruence_in_context(
                        checker,left_structure,right_structure,
                        512,depth,context,512,
                    )
                    && same_closure_spine_congruence_in_context(
                        checker,left_spine,right_spine,
                        512,depth,context,512,
                    );
                if deep_contextual {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_PROJECTION_CROSSFRAME_512").is_some() {
                        eprintln!(
                            "NUCLEUS_CROSSFRAME_512_PROVEN:depth={depth}:receiver_left={left_structure:?}:receiver_right={right_structure:?}",
                        );
                    }
                    return Judgment::proven((), "source-verified-bounded-projection-congruence");
                }
                // The source-scoped warrant is only used for the receiver
                // when both closures are independently typed in the SAME
                // existing lexical context. This is not a shape-based shortcut.
                let typed_receiver =
                    std::env::var_os("NUCLEUS_EXPERIMENTAL_TYPED_RECEIVER").is_some()
                    && depth == context.len()
                    && context.len() <= 12
                    && current_budget >= 512
                    && checker.checked_source_conversion(
                        left_structure,right_structure,context,
                        current_budget.min(2048),
                    ).is_proven()
                    && same_closure_spine_congruence_in_context(
                        checker,left_spine,right_spine,
                        current_budget,depth,context,512,
                    );
                if typed_receiver {
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_TYPED_RECEIVER").is_some(){
                        eprintln!(
                            "NUCLEUS_TYPED_RECEIVER:PROVEN:depth={depth}:left={left_structure:?}:right={right_structure:?}",
                        );
                    }
                    return Judgment::proven((),"checked-source-typed-projection-congruence");
                }
                // Reuse the *existing* typed receiver warrant at the
                // actual source binder depth. This experimental path is
                // independent of syntactic identity and requires separately
                // checked equality for every pending application argument.
                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_TEN_METHODS").is_some()
                    && depth==context.len() && (7..=8).contains(&depth)
                {
                    use std::sync::atomic::{AtomicUsize,Ordering};
                    static COUNT:AtomicUsize=AtomicUsize::new(0);
                    if COUNT.fetch_add(1,Ordering::Relaxed)<24 {
                        let left_typed=checker.checked_source_conversion(
                            left_structure,left_structure,context,512,
                        );
                        let right_typed=checker.checked_source_conversion(
                            right_structure,right_structure,context,512,
                        );
                        let receivers=checker.checked_source_conversion(
                            left_structure,right_structure,context,2048,
                        );
                        let args=same_closure_spine_congruence_in_context(
                            checker,left_spine,right_spine,512,depth,context,512,
                        );
                        eprintln!(
                            "NUCLEUS_TEN_METHODS:depth={depth}:budget={current_budget}:left_typed={left_typed:?}:right_typed={right_typed:?}:receiver_equality={receivers:?}:spine_equality={args}:left_expr={:?}:right_expr={:?}:left_arity={}:right_arity={}",
                            left_structure.expr,right_structure.expr,
                            left_spine.len(),right_spine.len(),
                        );
                    }
                }
                let source_typed_pair =
                    std::env::var_os("NUCLEUS_EXPERIMENTAL_SOURCE_PAIR_DEPTH8").is_some()
                    && depth == context.len()
                    && (7..=8).contains(&depth)
                    && current_budget >= 2
                    && checker.checked_source_conversion(
                        left_structure,right_structure,context,
                        2048,
                    ).is_proven()
                    && same_closure_spine_congruence_in_context(
                        checker,left_spine,right_spine,
                        512,depth,context,512,
                    );
                if source_typed_pair {
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_SOURCE_PAIR_DEPTH8").is_some(){
                        eprintln!(
                            "NUCLEUS_SOURCE_PAIR_DEPTH8:PROVEN:depth={depth}:left={left_structure:?}:right={right_structure:?}",
                        );
                    }
                    return Judgment::proven((),"checked-source-paired-projection");
                }
                if same_rigid_application_congruence(
                    checker,
                    left_structure,
                    right_structure,
                    current_budget,
                ) && same_closure_spine_congruence(
                    checker,
                    left_spine,
                    right_spine,
                    current_budget,
                ) {
                    return Judgment::proven((), "stuck-projection-rigid-application-congruence");
                }
                let machine = checker.machine();
                let left_value = machine.projection_value_for_conversion(
                    left_structure.clone(),
                    *left_type,
                    *left_index,
                    left_spine,
                    current_budget,
                );
                let right_value = machine.projection_value_for_conversion(
                    right_structure.clone(),
                    *right_type,
                    *right_index,
                    right_spine,
                    current_budget,
                );
                let (Some(left_value), Some(right_value)) =
                    (left_value.proven_value(), right_value.proven_value())
                else {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_PROJECTION_LAST_FAILURE").is_some() {
                        eprintln!(
                            "NUCLEUS_POST_IOTA_PROJECTION_GAP:shape=pair:depth={depth}:budget={current_budget}:left_type={left_type:?}:left_index={left_index}:left_structure={left_structure:?}:left_exposed={left_value:?}:right_type={right_type:?}:right_index={right_index}:right_structure={right_structure:?}:right_exposed={right_value:?}"
                        );
                    }
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_TERMINAL_CAUSE").is_some()
                        && (6..=10).contains(&depth)
                    {
                        eprintln!(
                            "NUCLEUS_TERMINAL_CAUSE:shape=pair:depth={depth}:left_type={left_type:?}:left_index={left_index}:left_receiver={left_structure:?}:left_result={left_value:?}:right_type={right_type:?}:right_index={right_index}:right_receiver={right_structure:?}:right_result={right_value:?}"
                        );
                    }
                    return Judgment::unknown("lazy-projection-value-exposure");
                };
                if current_budget == 0 {
                    return Judgment::unknown("lazy-projection-budget-exhausted");
                }
                current_left = left_value.clone();
                current_right = right_value.clone();
                current_budget -= 1;
                continue;
            }
            (
                Value::StuckProjection {
                    type_name,
                    index,
                    structure,
                    spine,
                },
                _,
            ) => {
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_FIRST_TYPED_CONTINUATION").is_some()
                    && let Value::Neutral(other) = &current_right
                    && current_budget >= 16
                    && other.spine.len() == 5
                {
                    use std::sync::atomic::{AtomicUsize, Ordering};
                    static PRINTED: AtomicUsize = AtomicUsize::new(0);
                    if PRINTED.fetch_add(1, Ordering::Relaxed) < 16 {
                        // The "separator" is a failed *typing premise* in a
                        // candidate proof derivation, not a claim that two
                        // valid convertible Lean terms are inequivalent.
                        let first = checker.diagnostic_neutral_source_telescope(
                            other, context, current_budget,
                        );
                        let first: String = first.chars().take(2500).collect();
                        eprintln!(
                            "NUCLEUS_FIRST_TYPED_CONTINUATION:depth={depth}:scope={}:projection={type_name:?}:{index}:receiver={:?}:opposing_head={:?}:opposing_arity={}:first_premise={first}",
                            context.len(), structure.expr, other.head, other.spine.len(),
                        );
                    }
                }
                let exposed = checker.machine().projection_value_for_conversion(
                    structure.clone(),
                    *type_name,
                    *index,
                    spine,
                    current_budget,
                );
                let Some(exposed) = exposed.proven_value() else {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_PROJECTION_LAST_FAILURE").is_some() {
                        eprintln!(
                            "NUCLEUS_POST_IOTA_PROJECTION_GAP:shape=single:depth={depth}:budget={current_budget}:projection_type={type_name:?}:index={index}:structure={structure:?}:pending={spine:?}"
                        );
                    }
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_TERMINAL_CAUSE").is_some()
                        && (6..=10).contains(&depth)
                    {
                        use std::sync::atomic::{AtomicUsize,Ordering};
                        static COUNT:AtomicUsize=AtomicUsize::new(0);
                        if COUNT.fetch_add(1,Ordering::Relaxed)<48 {
                            let receiver=checker.machine().expose_for_conversion(
                                structure.clone(),Transparency::Full,512,
                            );
                            let field=checker.machine().projection_field_for_conversion(
                                structure.clone(),*type_name,*index,512,
                            );
                            eprintln!(
                                "NUCLEUS_TERMINAL_CAUSE:depth={depth}:type={type_name:?}:index={index}:receiver_expr={:?}:receiver_env={}:receiver={}:field={}:pending={}",
                                structure.expr,structure.env.id(),
                                format!("{receiver:?}").chars().take(1300).collect::<String>(),
                                format!("{field:?}").chars().take(1300).collect::<String>(),
                                spine.len(),
                            );
                        }
                    }
                    return Judgment::unknown("lazy-projection-value-exposure");
                };
                if current_budget == 0 {
                    return Judgment::unknown("lazy-projection-budget-exhausted");
                }
                current_left = exposed.clone();
                current_budget -= 1;
                continue;
            }
            (
                _,
                Value::StuckProjection {
                    type_name,
                    index,
                    structure,
                    spine,
                },
            ) => {
                let exposed = checker.machine().projection_value_for_conversion(
                    structure.clone(),
                    *type_name,
                    *index,
                    spine,
                    current_budget,
                );
                let Some(exposed) = exposed.proven_value() else {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_PROJECTION_LAST_FAILURE").is_some() {
                        eprintln!(
                            "NUCLEUS_POST_IOTA_PROJECTION_GAP:shape=single:depth={depth}:budget={current_budget}:projection_type={type_name:?}:index={index}:structure={structure:?}:pending={spine:?}"
                        );
                    }
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_TERMINAL_CAUSE").is_some()
                        && (6..=10).contains(&depth)
                    {
                        use std::sync::atomic::{AtomicUsize,Ordering};
                        static COUNT:AtomicUsize=AtomicUsize::new(0);
                        if COUNT.fetch_add(1,Ordering::Relaxed)<48 {
                            let receiver=checker.machine().expose_for_conversion(
                                structure.clone(),Transparency::Full,512,
                            );
                            let field=checker.machine().projection_field_for_conversion(
                                structure.clone(),*type_name,*index,512,
                            );
                            eprintln!(
                                "NUCLEUS_TERMINAL_CAUSE:depth={depth}:type={type_name:?}:index={index}:receiver_expr={:?}:receiver_env={}:receiver={}:field={}:pending={}",
                                structure.expr,structure.env.id(),
                                format!("{receiver:?}").chars().take(1300).collect::<String>(),
                                format!("{field:?}").chars().take(1300).collect::<String>(),
                                spine.len(),
                            );
                        }
                    }
                    return Judgment::unknown("lazy-projection-value-exposure");
                };
                if current_budget == 0 {
                    return Judgment::unknown("lazy-projection-budget-exhausted");
                }
                current_right = exposed.clone();
                current_budget -= 1;
                continue;
            }
            (Value::Neutral(left), Value::Neutral(right)) => {
                // A registered recursor with an actual constructor major is
                // reducible even when both applications retain the same head.
                // Replay source iota before treating its arguments as rigid.
                if left.head == right.head
                    && let NeutralHead::Const { name, .. } = &left.head
                    && checker.has_qualified_recursor(*name)
                    && left.spine != right.spine
                {
                    let mut available = current_budget;
                    let mut reduced = None;
                    for (is_left, candidate) in [(false, right), (true, left)] {
                        if available < 128 { break; }
                        let probe = available / 2;
                        available -= probe;
                        if let Judgment::Proven { value, .. } = checker.machine()
                            .qualified_one_step_recursor_result(candidate, probe)
                            && !matches!(&value, Value::Neutral(n) if n == candidate)
                        {
                            reduced = Some((is_left, value));
                            break;
                        }
                    }
                    if let Some((is_left, value)) = reduced {
                        if is_left { current_left = value; } else { current_right = value; }
                        current_budget = available.saturating_sub(1);
                        continue;
                    }
                    current_budget = available;
                }
                // Proof-carrying relevance signature: a proposition-valued
                // argument may differ ONLY after both applications' exact
                // dependent argument typing and data-argument congruence
                // are independently established. The source metadata is
                // the same authority used for ordinary application checks.
                if false && checker.certified_relevance_spine_congruence(
                    left,right,context,current_budget,depth,
                ) {
                    return Judgment::proven((), "checked-prop-spine-congruence");
                }
                // Lean proof irrelevance: two checked proof terms of the same
                // *independently verified* proposition are convertible.
                // Do not quotient their FreeId values or closure frames.
                if certified_local_proof_irrelevance(
                    checker, left, right, context, current_budget, depth,
                ) {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_LOCAL_PROOF_IRREL").is_some() {
                        eprintln!("NUCLEUS_LOCAL_PROOF_IRREL:proved:depth={depth}:left={:?}:right={:?}",left.head,right.head);
                    }
                    return Judgment::proven((), "checked-local-proof-irrelevance");
                }
                if certified_structure_eta(
                    checker,
                    left,
                    right,
                    current_budget,
                    depth,
                    work,
                    context,
                ) || certified_structure_eta(
                    checker,
                    right,
                    left,
                    current_budget,
                    depth,
                    work,
                    context,
                ) {
                    return Judgment::proven((), "certified-structure-eta");
                }
                if rigid_local_non_eta_constructor_mismatch(
                    checker,
                    left,
                    right,
                    context,
                    current_budget,
                ) || rigid_local_non_eta_constructor_mismatch(
                    checker,
                    right,
                    left,
                    context,
                    current_budget,
                ) {
                    return Judgment::refuted("non-eta-structure-mismatch");
                }
                if distinct_non_eta_structure_locals(checker, left, right, context, current_budget)
                {
                    return Judgment::refuted("non-eta-structure-mismatch");
                }
                match checker.rule_k_reduce_neutral(left, context, current_budget) {
                    RuleKAttempt::Reduced(closure) => {
                        let exposed = checker.machine().expose(
                            closure,
                            Transparency::Reducible,
                            current_budget.saturating_sub(1),
                        );
                        let Some(reduced) = exposed.proven_value() else {
                            return Judgment::unknown("rule-k-reduction-exposure");
                        };
                        let other = Value::Neutral(right.clone());
                        return compare_values(
                            checker,
                            reduced,
                            &other,
                            current_budget.saturating_sub(1),
                            depth,
                            context,
                            work,
                            proof_function_frees,
                        );
                    }
                    RuleKAttempt::DefiniteMismatch => {
                        return Judgment::refuted("rule-k-target-mismatch");
                    }
                    RuleKAttempt::NotApplicable => {}
                }
                match checker.rule_k_reduce_neutral(right, context, current_budget) {
                    RuleKAttempt::Reduced(closure) => {
                        let exposed = checker.machine().expose(
                            closure,
                            Transparency::Reducible,
                            current_budget.saturating_sub(1),
                        );
                        let Some(reduced) = exposed.proven_value() else {
                            return Judgment::unknown("rule-k-reduction-exposure");
                        };
                        let other = Value::Neutral(left.clone());
                        return compare_values(
                            checker,
                            &other,
                            reduced,
                            current_budget.saturating_sub(1),
                            depth,
                            context,
                            work,
                            proof_function_frees,
                        );
                    }
                    RuleKAttempt::DefiniteMismatch => {
                        return Judgment::refuted("rule-k-target-mismatch");
                    }
                    RuleKAttempt::NotApplicable => {}
                }
                if one_neutral_head_is_free(left, right)
                    && (checker.certified_stuck_nonproof_recursor_on_local(
                        left,
                        context,
                        current_budget,
                    ) || checker.certified_stuck_nonproof_recursor_on_local(
                        right,
                        context,
                        current_budget,
                    ))
                {
                    return Judgment::refuted("certified-stuck-recursor-mismatch");
                }
                // A Bool constructor cannot be equated with an unrelated
                // neutral. It may, however, match a registered recursor after
                // exact source-defined iota. The major can itself be a
                // Decidable/Bool recursor with a captured constructor major.
                // Never select the constructor from the expected Bool result.
                if current_budget >= 128 {
                    let candidate = |constructor: &Neutral, recursive: &Neutral| -> Option<Value> {
                        let NeutralHead::Const { name, levels } = &constructor.head else {
                            return None;
                        };
                        if !constructor.spine.is_empty()
                            || !levels.is_empty()
                            || !checker.is_certified_bool_constructor(*name)
                            || recursive.spine.len() != 5
                        {
                            return None;
                        }
                        checker.machine().qualified_nested_recursor_result(
                            recursive, current_budget,
                        ).proven_value().cloned()
                    };
                    if let Some(result) = candidate(left, right) {
                        if result != Value::Neutral(right.clone()) {
                            return compare_values(
                                checker, &Value::Neutral(left.clone()), &result,
                                current_budget.saturating_sub(1),
                                depth, context, work, proof_function_frees,
                            );
                        }
                    }
                    if let Some(result) = candidate(right, left) {
                        if result != Value::Neutral(left.clone()) {
                            return compare_values(
                                checker, &result, &Value::Neutral(right.clone()),
                                current_budget.saturating_sub(1),
                                depth, context, work, proof_function_frees,
                            );
                        }
                    }
                }
                match compare_neutral_heads(checker, left, right, current_budget, depth, context) {
                    Judgment::Proven { .. } => {}
                    other => {
                        // A retained registered recursor can still have an
                        // actual constructor major. Replay its checked rule,
                        // independently of the opposing head or desired value.
                        // Reserve both bounded probes from this comparison's
                        // allowance, and continue iteratively after real iota.
                        let mut available = current_budget;
                        let mut reduced = None;
                        if left.head != right.head {
                            for (is_left, candidate) in [(false, right), (true, left)] {
                                if !matches!(candidate.head, NeutralHead::Const { .. })
                                    || candidate.spine.is_empty() || available < 128 {
                                    continue;
                                }
                                let probe = available / 2;
                                available -= probe;
                                if let Judgment::Proven { value, .. } = checker.machine()
                                    .qualified_one_step_recursor_result(candidate, probe)
                                    && !matches!(&value, Value::Neutral(n) if n == candidate)
                                {
                                    reduced = Some((is_left, value));
                                    break;
                                }
                            }
                        }
                        if let Some((is_left, value)) = reduced {
                            if is_left { current_left = value; } else { current_right = value; }
                            current_budget = available.saturating_sub(1);
                            continue;
                        }
                        return other;
                    }
                }
                if left.spine.len() != right.spine.len() {
                    return Judgment::refuted("neutral-spine-length");
                }
                // Proof-irrelevant dependent application congruence. Source
                // traces have independently established the exact premise
                // in a 13-binder context: the predicate head is unchanged,
                // the first argument is convertible, and the second pair
                // consists of two checked proofs of the same proposition.
                //
                // Do NOT permute arguments or identify unrelated locals.
                if depth==context.len() && (4..=24).contains(&depth) && current_budget>=1024
                    && left.head==right.head
                    && matches!(&left.head,NeutralHead::Free(_, _))
                    && left.spine.len()==2
                    && convert_with_policy_in_context(
                        checker,
                        &TypeValue::Term(left.spine[0].clone()),
                        &TypeValue::Term(right.spine[0].clone()),
                        512,DeltaPolicy::PreferredOnly,depth,context,
                    ).is_proven()
                    && checker.checked_proof_pair_in_bounded_context(
                        &left.spine[1],&right.spine[1],context,current_budget,
                    )
                {
                    return Judgment::proven(
                        (),"certified-dependent-predicate-proof-irrelevance",
                    );
                }
                work.extend(left.spine.iter().zip(&right.spine).map(|(left, right)| {
                    (
                        TypeValue::Term(left.clone()),
                        TypeValue::Term(right.clone()),
                        depth,
                        context.to_vec(),
                    )
                }));
            }
            (Value::Neutral(neutral), Value::Lam { domain, body })
            | (Value::Lam { domain, body }, Value::Neutral(neutral))
                if evaluated_free_eta(
                    checker,
                    neutral,
                    domain,
                    body,
                    current_budget,
                    depth,
                    work,
                    context,
                ) => {}
            (Value::Lam{..},Value::Neutral(_))|(Value::Neutral(_),Value::Lam{..})=>{
                return Judgment::unknown("function-eta-source-authority-unavailable");
            },
            _ => {
                if std::env::var_os("NUCLEUS_TRACE_VALUE_MISMATCH").is_some() {
                    eprintln!(
                        "NUCLEUS_VALUE_MISMATCH:left={:?}:right={:?}:budget={}:depth={}",
                        current_left, current_right, current_budget, depth
                    );
                }
                return Judgment::refuted("rigid-value-constructor-mismatch");
            }
        }
        break;
    }
    Judgment::proven((), "rigid-value-comparison")
}

fn same_closure_spine_congruence(
    checker: &TypeChecker<'_>,
    left: &[Closure],
    right: &[Closure],
    budget: usize,
) -> bool {
    let budget = budget.min(CHEAP_PROJECTION_CONGRUENCE_BUDGET);
    left.len() == right.len()
        && left.iter().zip(right).all(|(left, right)| {
            matches!(
                convert_with_policy(
                    checker,
                    &TypeValue::Term(left.clone()),
                    &TypeValue::Term(right.clone()),
                    budget.saturating_sub(1),
                    DeltaPolicy::PreferredOnly,
                ),
                Judgment::Proven { .. }
            )
        })
}

fn same_closure_spine_congruence_in_context(
    checker: &TypeChecker<'_>,
    left: &[Closure],
    right: &[Closure],
    budget: usize,
    depth: usize,
    context: &[TypeValue],
    max_budget: usize,
) -> bool {
    let budget = budget.min(max_budget);
    left.len() == right.len()
        && left.iter().zip(right).all(|(left,right)| {
            convert_with_policy_in_context(
                checker,
                &TypeValue::Term(left.clone()),
                &TypeValue::Term(right.clone()),
                budget.saturating_sub(1),
                DeltaPolicy::PreferredOnly, depth, context,
            ).is_proven()
        })
}

fn same_rigid_application_congruence_in_context(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    budget: usize,
    depth: usize,
    context: &[TypeValue],
    max_budget: usize,
) -> bool {
    rigid_application_head_congruence_in_context(
        checker, left, right, budget, depth, context, max_budget,
    ).is_some_and(|(_, judgment)| judgment.is_proven())
}

fn same_rigid_application_congruence(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    budget: usize,
) -> bool {
    rigid_application_head_congruence(checker, left, right, budget)
        .is_some_and(|(_, judgment)| judgment.is_proven())
}

fn rigid_application_head_congruence(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    budget: usize,
) -> Option<(crate::id::NameId, Judgment<()>)> {
    rigid_application_head_congruence_in_context(
        checker, left, right, budget, 0, &[], CHEAP_PROJECTION_CONGRUENCE_BUDGET,
    )
}

fn rigid_application_head_congruence_in_context(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    budget: usize,
    depth: usize,
    context: &[TypeValue],
    max_budget: usize,
) -> Option<(crate::id::NameId, Judgment<()>)> {
    let budget = budget.min(max_budget);
    if budget == 0 {
        return None;
    }

    fn rigid_application_spine(
        checker: &TypeChecker<'_>,
        closure: &Closure,
    ) -> Option<(Closure, Vec<Closure>)> {
        let mut current = resolve_local_closure(checker, closure)?;
        let mut arguments = Vec::new();
        loop {
            match checker.expression(current.expr)? {
                Expr::App { fun, arg } => {
                    arguments.push(current.sibling(*arg, current.env.clone()));
                    current = current.sibling(*fun, current.env.clone());
                    current = resolve_local_closure(checker, &current)?;
                }
                Expr::Const { .. } => {
                    arguments.reverse();
                    return Some((current, arguments));
                }
                _ => return None,
            }
        }
    }

    let Some((left_head, left_args)) = rigid_application_spine(checker, left) else {
        return None;
    };
    let Some((right_head, right_args)) = rigid_application_spine(checker, right) else {
        return None;
    };
    if left_args.is_empty()
        || left_args.len() != right_args.len()
        || left_head.expr != right_head.expr
        || left_head.levels != right_head.levels
    {
        return None;
    }
    let Expr::Const {
        name: rigid_head, ..
    } = checker.expression(left_head.expr)?
    else {
        return None;
    };

    for (left, right) in left_args.iter().zip(&right_args) {
        match convert_with_policy_in_context(
            checker,
            &TypeValue::Term(left.clone()),
            &TypeValue::Term(right.clone()),
            budget.saturating_sub(1),
            DeltaPolicy::PreferredOnly, depth, context,
        ) {
            Judgment::Proven { .. } => {}
            Judgment::Refuted { obstruction } => {
                return Some((*rigid_head, Judgment::Refuted { obstruction }));
            }
            Judgment::Unknown { residual } => {
                return Some((*rigid_head, Judgment::Unknown { residual }));
            }
        }
    }
    Some((
        *rigid_head,
        Judgment::proven((), "same-rigid-application-congruence"),
    ))
}

fn compare_nat_literal_neutral(
    checker: &TypeChecker<'_>,
    literal: &crate::nat::BigNat,
    neutral: &Neutral,
    budget: usize,
    depth: usize,
    context: &[TypeValue],
    work: &mut ConversionWorkList,
    proof_function_frees: &mut HashMap<FreeId, (crate::id::NameId, Vec<crate::level::LevelTerm>)>,
) -> Judgment<()> {
    let Some(primitives) = checker.nat_primitives() else {
        return Judgment::unknown("Nat-literal-conversion-without-authority");
    };
    let NeutralHead::Const { name, levels } = &neutral.head else {
        return Judgment::refuted("Nat-literal-neutral-head");
    };
    if literal.is_zero() && *name == primitives.recursor && budget >= 32 {
        let result = checker.machine().qualified_nat_zero_recursor_result(
            neutral, budget,
        );
        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_NATREC_MAJOR").is_some() {
            eprintln!(
                "NUCLEUS_ZERO_IOTA_REPLAY:depth={depth}:budget={budget}:result={result:?}"
            );
        }
        return match result {
            Judgment::Proven { value, .. } => {
                if value == Value::Neutral(neutral.clone()) {
                    Judgment::unknown("natrec-zero-iota-nonprogress")
                } else {
                    compare_values(
                        checker, &Value::NatLit(literal.clone()), &value,
                        budget.saturating_sub(1), depth, context,
                        work, proof_function_frees,
                    )
                }
            }
            Judgment::Refuted { .. } | Judgment::Unknown { .. } => {
                // A polymorphic Nat.rec is not a Nat constructor. Failure
                // to reduce it cannot establish numeral inequality.
                Judgment::unknown("natrec-zero-iota-unresolved")
            }
        };
    }
    if !levels.is_empty() {
        // A polymorphic recursor is not the constructor for zero. A
        // source-certified iota step requires first identifying its exact
        // recursor table AND inspecting its major argument.
        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_NATREC_MAJOR").is_some()
            && neutral.spine.len() == 4
        {
            use std::sync::atomic::{AtomicUsize, Ordering};
            static MAJOR_PROBES: AtomicUsize = AtomicUsize::new(0);
            if MAJOR_PROBES.fetch_add(1, Ordering::Relaxed) < 12 {
                eprintln!(
                    "NUCLEUS_NATREC_MAJOR_AUTHORITY:depth={depth}:literal={literal:?}:{}",
                    checker.diagnostic_natrec_major_authority(neutral, budget)
                );
            }
        }
        return Judgment::refuted("Nat-literal-constructor-levels");
    }
    if *name == primitives.zero {
        return if neutral.spine.is_empty() && literal.is_zero() {
            Judgment::proven((), "Nat-literal-zero")
        } else {
            Judgment::refuted("Nat-literal-zero-mismatch")
        };
    }
    if *name == primitives.succ {
        if neutral.spine.len() != 1 {
            return Judgment::refuted("Nat-literal-succ-arity");
        }
        let Some(pred) = literal.pred() else {
            return Judgment::refuted("Nat-zero-is-not-succ");
        };
        let exposed =
            checker
                .machine()
                .expose(neutral.spine[0].clone(), Transparency::Reducible, budget);
        let Some(argument) = exposed.proven_value() else {
            return Judgment::unknown("Nat-literal-succ-argument");
        };
        return compare_values(
            checker,
            &Value::NatLit(pred),
            argument,
            budget.saturating_sub(1),
            depth,
            context,
            work,
            proof_function_frees,
        );
    }
    Judgment::refuted("Nat-literal-non-Nat-head")
}

// A sufficient source equality proof for an entire neutral receiver. Every
// child uses the same remaining allowance; no normalization or typing
// witness is borrowed from another receiver or context.
fn exact_neutral_source_congruence(
    checker: &TypeChecker<'_>, left: &Neutral, right: &Neutral, remaining: &mut usize,
) -> bool {
    use crate::level::LevelTerm;
    let mut pending = vec![(left, right)];
    while let Some((left, right)) = pending.pop() {
        if *remaining == 0 { return false; }
        *remaining -= 1;
        match (&left.head, &right.head) {
            (NeutralHead::Free(_, _), NeutralHead::Free(_, _)) if left.head.same_owned_free(&right.head) => {}
            (NeutralHead::Const { name: a, levels: x }, NeutralHead::Const { name: b, levels: y }) if a == b && x.len() == y.len() => {
                if *remaining < x.len() { return false; }
                *remaining -= x.len();
                let mut levels: Vec<_> = x.iter().zip(y).collect();
                while let Some((a, b)) = levels.pop() {
                    if *remaining == 0 { return false; }
                    *remaining -= 1;
                    match (a, b) {
                        (LevelTerm::Zero, LevelTerm::Zero) => {}
                        (LevelTerm::Param(x), LevelTerm::Param(y)) => {
                            let cost = x.len().max(y.len());
                            if *remaining < cost { return false; }
                            *remaining -= cost;
                            if x != y { return false; }
                        }
                        (LevelTerm::Succ(x), LevelTerm::Succ(y)) => {
                            if *remaining == 0 { return false; }
                            *remaining -= 1;
                            levels.push((x, y));
                        }
                        (LevelTerm::Max(x, u), LevelTerm::Max(y, v))
                        | (LevelTerm::IMax(x, u), LevelTerm::IMax(y, v)) => {
                            if *remaining < 2 { return false; }
                            *remaining -= 2;
                            levels.push((x, y)); levels.push((u, v));
                        }
                        _ => return false,
                    }
                }
            }
            (NeutralHead::Projection { type_name: a, index: i, structure: x },
             NeutralHead::Projection { type_name: b, index: j, structure: y }) if a == b && i == j => {
                if *remaining == 0 { return false; }
                *remaining -= 1;
                pending.push((x.as_ref(), y.as_ref()));
            }
            _ => return false,
        }
        if left.spine.len() != right.spine.len() { return false; }
        for (a, b) in left.spine.iter().zip(&right.spine) {
            if *remaining == 0 { return false; }
            *remaining -= 1;
            if a.expr == b.expr && a.env == b.env && a.levels.identity() == b.levels.identity() {
                continue;
            }
            if !checker.exact_source_capture_identity(a, b, remaining) { return false; }
        }
    }
    true
}

fn compare_neutral_heads(
    checker: &TypeChecker<'_>,
    left: &Neutral,
    right: &Neutral,
    budget: usize,
    depth: usize,
    context: &[TypeValue],
) -> Judgment<()> {
    match (&left.head, &right.head) {
        (NeutralHead::Free(_, _), NeutralHead::Free(_, _)) if left.head.same_owned_free(&right.head) => {
            Judgment::proven((), "same-free-variable")
        }
        (NeutralHead::Free(_, _),NeutralHead::Free(_, _))=>
            Judgment::unknown("neutral-free-scope-authority-unavailable"),
        (NeutralHead::Free(_,None),_)|(_,NeutralHead::Free(_,None))=>
            Judgment::unknown("unowned-neutral-free-scope-unavailable"),
        (
            NeutralHead::Projection {
                type_name: left_type,
                index: left_index,
                structure: left_structure,
            },
            NeutralHead::Projection {
                type_name: right_type,
                index: right_index,
                structure: right_structure,
            },
        ) if left_type == right_type
            && left_index == right_index
            && left_structure == right_structure =>
        {
            Judgment::proven((), "same-neutral-projection")
        }
        (
            NeutralHead::Projection {
                type_name: left_type,
                index: left_index,
                structure: left_structure,
            },
            NeutralHead::Projection {
                type_name: right_type,
                index: right_index,
                structure: right_structure,
            },
        ) if left_type == right_type && left_index == right_index
            && depth == context.len() =>
        {
            // Congruence requires equal receiver values, not identical
            // capture-frame allocations. This is only a sufficient equality
            // rule: failure does not prove unequal selected fields.
            if budget < 8 || left_structure.spine.len() != right_structure.spine.len() {
                return Judgment::unknown("neutral-projection-receiver-congruence");
            }
            let mut source_work = budget.saturating_sub(1);
            if exact_neutral_source_congruence(checker, left_structure, right_structure, &mut source_work) {
                return Judgment::proven((), "exact-source-neutral-receiver-congruence");
            }
            let budget = source_work;
            let probe = budget.saturating_sub(1) / 2;
            if !compare_neutral_heads(
                checker, left_structure, right_structure, probe, depth, context,
            ).is_proven() {
                return Judgment::unknown("neutral-projection-receiver-congruence");
            }
            let argument_budget = probe / left_structure.spine.len().max(1);
            for (lhs, rhs) in left_structure.spine.iter().zip(&right_structure.spine) {
                let argument_result = convert_with_policy_in_context(
                    checker, &TypeValue::Term(lhs.clone()), &TypeValue::Term(rhs.clone()),
                    argument_budget, DeltaPolicy::GuardedSemanticFallback, depth, context,
                );
                if !argument_result.is_proven() {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_FAILED_RECEIVER_CAPTURES").is_some()
                        && matches!(lhs.expr.0, 600 | 1214)
                        && lhs.expr == rhs.expr && argument_budget >= 2048
                    {
                        use std::sync::atomic::{AtomicUsize, Ordering};
                        static CAPTURES: AtomicUsize = AtomicUsize::new(0);
                        // Count before probing typed captures so recursive
                        // diagnostic conversion cannot start another trace.
                        if CAPTURES.fetch_add(1, Ordering::Relaxed) == 0 {
                            eprintln!("NUCLEUS_FAILED_RECEIVER_CAPTURES:owner={left_type:?}:field={left_index}:depth={depth}:budget={budget}:argument_budget={argument_budget}:result={argument_result:?}:{}",
                                checker.diagnostic_receiver_capture_pair(lhs, rhs, context, 128));
                        }
                    }
                    return Judgment::unknown("neutral-projection-receiver-congruence");
                }
            }
            Judgment::proven((), "neutral-projection-receiver-congruence")
        }
        (
            NeutralHead::Const {
                name: left_name,
                levels: left_levels,
            },
            NeutralHead::Const {
                name: right_name,
                levels: right_levels,
            },
        ) if left_levels.is_empty()
            && right_levels.is_empty()
            && checker.distinct_bool_constructors(*left_name, *right_name) =>
        {
            Judgment::refuted("rigid-value-constructor-mismatch")
        }
        (
            NeutralHead::Const {
                name: left_name,
                levels: left_levels,
            },
            NeutralHead::Const {
                name: right_name,
                levels: right_levels,
            },
        ) if left.spine.is_empty()
            && right.spine.is_empty()
            && checker.distinct_opaque_closed_proposition_types(
                *left_name,
                left_levels,
                *right_name,
                right_levels,
                budget,
            ) =>
        {
            Judgment::refuted("distinct-opaque-proposition-types")
        }
        (
            NeutralHead::Const {
                name: left_name,
                levels: left_levels,
            },
            NeutralHead::Const {
                name: right_name,
                levels: right_levels,
            },
        ) if left_name == right_name && left_levels.len() == right_levels.len() => {
            for (left, right) in left_levels.iter().zip(right_levels) {
                match level_equal(left.clone(), right.clone(), budget) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                }
            }
            Judgment::proven((), "same-rigid-constant")
        }
        _ => {
            if std::env::var_os("NUCLEUS_TRACE_NEUTRAL_HEADS").is_some() {
                eprintln!(
                    "NUCLEUS_NEUTRAL_HEAD_MISMATCH:depth={depth}:context_len={}:left={:?}:left_spine={:?}:right={:?}:right_spine={:?}:budget={}",
                    context.len(),left.head,left.spine,right.head,right.spine,budget,
                );
                let l=format!("{:?}",left.head);
                let r=format!("{:?}",right.head);
                if ((l=="Free(FreeId(6))" && r=="Free(FreeId(5))") ||
                    (l=="Free(FreeId(5))" && r=="Free(FreeId(6))"))
                {
                    let a=context.get(6);
                    let b=context.get(5);
                    let prop=|ty:Option<&TypeValue>| {
                        if let Some(TypeValue::Term(c))=ty {
                            Some(checker.is_proposition_in_context(
                                c.expr,context,&c.env,budget.min(1024),
                            ))
                        }else{None}
                    };
                    let relation=match(a,b){
                        (Some(x),Some(y))=>Some(convert_with_policy_in_context(
                            checker,x,y,budget.min(256),
                            DeltaPolicy::GuardedSemanticFallback,depth,context,
                        )),
                        _=>None,
                    };
                    eprintln!(
                        "NUCLEUS_FIN_LOCAL_PAIR:depth={depth}:context_len={}:free6_type={a:?}:free5_type={b:?}:prop6={:?}:prop5={:?}:type_relation={relation:?}",
                        context.len(),prop(a),prop(b),
                    );
                }
            }
            if std::env::var_os("NUCLEUS_TRACE_RECURSOR_MAJOR").is_some() { eprintln!("NUCLEUS_RECURSOR_MAJOR:left={:?}:right={:?}", left.spine.last(), right.spine.last()); if let Some(c) = right.spine.last() { eprintln!("NUCLEUS_RECURSOR_MAJOR_VALUE:{:?}", checker.machine().expose(c.clone(), Transparency::Full, budget.min(64))); } }
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_CHECKED_MAJOR_CHAIN").is_some() && left.spine.len()>=4 && context.len()<=24 {
                eprintln!("NUCLEUS_CHECKED_MAJOR_CHAIN:{}",checker.diagnostic_captured_recursor_major_chain(left,budget));
            }
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_CHECKED_MAJOR_CHAIN").is_some() && context.len() <= 24 {
                for value in [left, right] {
                    if value.spine.len() >= 4 {
                        eprintln!("NUCLEUS_EITHER_MAJOR_CHAIN:{}",checker.diagnostic_captured_recursor_major_chain(value,budget));
                    }
                    if let NeutralHead::Projection { structure, .. } = &value.head {
                        eprintln!("NUCLEUS_PROJECTION_MAJOR_CHAIN:{}",checker.diagnostic_captured_recursor_major_chain(structure,budget));
                    }
                }
            }
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_LEFT_DECIDABLE_MAJOR_CHAIN").is_some()
                && left.spine.len()==5 && context.len()==3
            {
                eprintln!("NUCLEUS_LEFT_DECIDABLE_MAJOR_CHAIN:{}",checker.diagnostic_captured_recursor_major_chain(left,budget));
            }
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_DECIDABLE_MAJOR_CHAIN").is_some()
                && matches!(&right.head, NeutralHead::Const { .. })
                && right.spine.len() == 5
            {
                use std::sync::atomic::{AtomicUsize, Ordering};
                static PRINTED: AtomicUsize = AtomicUsize::new(0);
                if PRINTED.fetch_add(1, Ordering::Relaxed) < 8 {
                    eprintln!(
                        "NUCLEUS_DECIDABLE_MAJOR_CHAIN:{}",
                        checker.diagnostic_captured_recursor_major_chain(right, budget),
                    );
                }
            }
            Judgment::refuted("distinct-neutral-heads")
        }
    }
}

/// Proof irrelevance is permitted only after checking BOTH proposition
/// judgments and checking conversion of their exact dependent types in
/// the current binder context. The local identifiers themselves are
/// explicitly *not* assumed interchangeable.
fn certified_local_proof_irrelevance(
    checker: &TypeChecker<'_>,
    left: &Neutral,
    right: &Neutral,
    context: &[TypeValue],
    budget: usize,
    depth: usize,
) -> bool {
    // Original source typing is unavailable at this evaluated-only site.
    false
}

fn one_neutral_head_is_free(left: &Neutral, right: &Neutral) -> bool {
    matches!(left.head, NeutralHead::Free(_, _)) ^ matches!(right.head, NeutralHead::Free(_, _))
}

pub(crate) fn checked_source_type_value(
    checker: &TypeChecker<'_>,
    term: Closure,
    context: &[TypeValue],
    budget: usize,
) -> Judgment<Value> {
    if budget < 128 {
        return Judgment::unknown("checked-transport-projection-budget");
    }
    let machine = checker.machine();
    let preserved = machine.expose_for_conversion(term, Transparency::Full, budget);
    #[cfg(feature="diagnostics")]
    if std::env::var_os("NUCLEUS_TRACE_SOURCE_TYPE_RECOVERY").is_some() {
        eprintln!("NUCLEUS_SOURCE_TYPE_PRESERVED:{preserved:?}");
    }
    let preserved = if let Some(Value::Neutral(neutral)) = preserved.proven_value() {
        machine.qualified_nested_recursor_result(neutral, budget)
    } else {
        preserved
    };
    let Some(Value::StuckProjection { type_name, index, structure, spine }) = preserved.proven_value() else {
        return preserved;
    };
    let receiver = machine.expose(structure.clone(), Transparency::Full, budget / 2);
    let Some(Value::Neutral(neutral)) = receiver.proven_value() else {
        return Judgment::unknown("checked-transport-projection-receiver");
    };
    let RuleKAttempt::Reduced(reduced) = checker.rule_k_reduce_neutral(neutral, context, budget / 2) else {
        return Judgment::unknown("checked-transport-projection-premise");
    };
    // Select only a field of the actual source-registered constructor after
    // the existing typed K premise succeeds; retain all projection arguments.
    machine.projection_value_for_conversion(reduced, *type_name, *index, spine, budget / 2)
}

fn value_as_type(checker: &TypeChecker<'_>, value: &Value, source: &Closure, context: &[TypeValue], depth: usize, remaining: &mut usize) -> Option<TypeValue> {
    match value {
        Value::Sort(level) => Some(TypeValue::Sort(level.clone())),
        Value::Pi { domain, body } => {
            let free = fresh_local(depth)?;
            let allowance = (*remaining).min(1024);
            let mut opening_budget = allowance;
            let safe = source_opening_avoids_capture(checker, body, free, &mut opening_budget);
            *remaining -= allowance - opening_budget;
            if !safe { return None; }
            let opened = body.under_free(free);
            checker.certify_conversion_pi_opening(source, domain, &opened, context, remaining);
            Some(TypeValue::Pi {
                domain: Box::new(TypeValue::Term(domain.clone())),
                body: Box::new(TypeValue::Term(opened.clone())),
                binder: free,
             binder_owner: Some(opened.env),})
        }
        Value::NatLit(_)
        | Value::Lam { .. }
        | Value::Neutral(_)
        | Value::StuckProjection { .. } => None,
    }
}

fn fresh_local(depth: usize) -> Option<FreeId> {
    u64::try_from(depth).ok().map(FreeId)
}

// A source body still has its leading de Bruijn binder, so drop that
// virtual slot before inspecting actual captures. Only complete source
// support can justify opening it with an ID used by the checked context.
pub(crate) fn source_opening_avoids_capture(
    checker: &TypeChecker<'_>, body: &Closure, free: FreeId, budget: &mut usize,
) -> bool {
    // The exact lookup consumes the existing initial source-node step.
    // A miss carries that prepaid node into the original traversal once.
    if *budget==0{return false;}
    *budget-=1;
    if checker.has_source_opening_proof(body,free){return true;}
    let started=*budget;
    let safe=source_opening_avoids_capture_uncached(checker,body,free,budget);
    #[cfg(feature="diagnostics")]
    if !safe&&std::env::var_os("NUCLEUS_TRACE_OPENING_FAILURE").is_some() {
        use std::sync::atomic::{AtomicUsize,Ordering};static FAILED:AtomicUsize=AtomicUsize::new(0);
        if FAILED.fetch_add(1,Ordering::Relaxed)<64 {eprintln!("SOURCE_OPENING_FAILURE:body={body:?}:free={free:?}:start={started}:remaining={budget}");}
    }
    if safe{checker.retain_source_opening_proof(body,free);}
    safe
}

fn source_opening_avoids_capture_uncached(
    checker:&TypeChecker<'_>,body:&Closure,free:FreeId,budget:&mut usize,
)->bool {
    let mut active=HashSet::new();
    complete_actual_capture_frees(checker,body,1,budget,&mut active,0,true)
        .is_some_and(|frees|!frees.contains(&free))
}

// Complete pure support of the ACTUAL immutable capture graph. Syntax support
// alone never certifies freshness: every used stored closure is followed and
// every actual local is retained. Only complete graphs are published, pinned
// by their full source closure and intrinsic-slot count.
fn complete_actual_capture_frees(
    checker:&TypeChecker<'_>,source:&Closure,virtual_slots:u64,budget:&mut usize,
    active:&mut HashSet<(crate::id::ExprId,u64,usize,u64)>,depth:usize,prepaid:bool,
)->Option<std::rc::Rc<Vec<FreeId>>> {
    if depth>256{return None;}
    if !prepaid {if *budget==0{return None;}*budget-=1;}
    if let Some(frees)=checker.cached_actual_capture_frees(source,virtual_slots,budget){return Some(frees);}
    let key=(source.expr,source.env.id(),source.levels.identity(),virtual_slots);
    if !active.insert(key){return None;}
    let mut frees=std::collections::BTreeSet::new();
    let mut children=Vec::new();
    let mut inspect_binding=|binding:&EnvBinding|->Option<()> {
        match binding {
            EnvBinding::Free(actual)=>{frees.insert(actual.0);}
            EnvBinding::Closure(captured)=>children.push(captured.clone()),
            EnvBinding::NatLit(_)=>{},
            EnvBinding::Neutral(Neutral{head:NeutralHead::Free(actual,Some(owner)),spine}) if spine.is_empty()=>{
                if !matches!(owner.lookup_binding_ref(0),Some(EnvBinding::Free(original)) if original==actual){return None;}
                frees.insert(actual.0);
            },
            // An unowned or applied neutral cannot acquire source authority.
            EnvBinding::Neutral(_)=>return None,
        }
        Some(())
    };
    match checker.expression(source.expr)? {
        crate::syntax::Expr::BVar(index)=>{
            if *index>=virtual_slots {
                let offset=*index-virtual_slots;
                if offset==0 {
                    // This exact source-node visit has already been paid.
                    // Its actual current-node payload is a direct immutable
                    // field read; absence still declines before publication.
                    inspect_binding(source.env.lookup_binding_ref(0)?)?;
                } else {
                    let owner=checker.source_capture_owner(&source.env,offset,budget)?;
                    inspect_binding(owner.lookup_binding_ref(0)?)?;
                }
            }
        }
        crate::syntax::Expr::Const{..}|crate::syntax::Expr::Sort(_)
        |crate::syntax::Expr::NatLit(_)|crate::syntax::Expr::StrLit(_)=>{},
        _=>{
            let support=checker.complete_source_support(source.expr,budget)?;
            for index in support {
                if index<virtual_slots{continue;}
                let owner=checker.source_capture_owner(&source.env,index-virtual_slots,budget)?;
                inspect_binding(owner.lookup_binding_ref(0)?)?;
            }
        }
    }
    // All used bindings were validated above. With no local Free and one
    // actual child, the complete result is exactly that child's immutable set.
    // Forwarding copies only an Rc handle and creates no per-Free union work.
    if frees.is_empty()&&children.len()==1 {
        let child=children.pop()?;
        let child_frees=complete_actual_capture_frees(checker,&child,0,budget,active,depth+1,false)?;
        active.remove(&key);
        checker.retain_actual_capture_frees(source,virtual_slots,child_frees.clone());
        return Some(child_frees);
    }
    for child in children {
        let child_frees=complete_actual_capture_frees(checker,&child,0,budget,active,depth+1,false)?;
        if *budget<child_frees.len(){return None;}*budget-=child_frees.len();
        frees.extend(child_frees.iter().map(|free|free.0));
        if frees.len()>128{return None;}
    }
    active.remove(&key);
    let frees:std::rc::Rc<Vec<FreeId>>=std::rc::Rc::new(frees.into_iter().map(FreeId).collect());
    checker.retain_actual_capture_frees(source,virtual_slots,frees.clone());
    Some(frees)
}

#[cfg(test)]
mod owned_free_head_scope_tests {
 use super::*;
 use crate::id::{ExprId,IdTable,NameId};
 use crate::syntax::Expr;
 use crate::environment::{Environment,ConstantDecl};
 use crate::value::EnvFrame;
 #[test]
 fn same_number_without_joint_scope_is_unknown_not_refuted() {
  let mut expressions=IdTable::default();expressions.insert(ExprId(0),Expr::Sort(crate::id::LevelId(1))).unwrap();expressions.insert(ExprId(1),Expr::Const{name:NameId(1),levels:vec![]}).unwrap();
  let mut levels=IdTable::default();levels.insert(crate::id::LevelId(0),crate::syntax::Level::Zero).unwrap();levels.insert(crate::id::LevelId(1),crate::syntax::Level::Succ(crate::id::LevelId(0))).unwrap();
  let environment=Environment::empty().extend(NameId(1),ConstantDecl::axiom(vec![],ExprId(0))).unwrap();
  let checker=TypeChecker::new(&expressions,&levels,&environment);
  let gamma=vec![TypeValue::Term(Closure::new(ExprId(1),EnvFrame::empty()))];
  let owner=EnvFrame::empty().extend_free(FreeId(0));let unrelated=EnvFrame::empty().extend_free(FreeId(0));
  let a=Neutral{head:NeutralHead::Free(FreeId(0),Some(owner.clone())),spine:vec![]};
  let b=Neutral{head:NeutralHead::Free(FreeId(0),Some(unrelated)),spine:vec![]};
  let unknown=Neutral{head:NeutralHead::Free(FreeId(0),None),spine:vec![]};
  assert!(compare_neutral_heads(&checker,&a,&a,128,1,&gamma).is_proven());
  assert!(compare_neutral_heads(&checker,&a,&b,128,1,&gamma).is_unknown());
  assert!(compare_neutral_heads(&checker,&a,&unknown,128,1,&gamma).is_unknown());
  assert!(compare_neutral_heads(&checker,&unknown,&unknown,128,1,&gamma).is_unknown());
 }
}

#[cfg(test)]
mod deferred_application_proof_tests {
 use super::*;
 use crate::id::{IdTable,LevelId,NameId};
 use crate::syntax::Level;
 use crate::environment::{Environment,ConstantDecl};
 use crate::value::EnvFrame;
 fn fixture()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment) {
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(id,node)in[(0,Expr::Sort(LevelId(0))),(1,Expr::Sort(LevelId(1))),(2,Expr::Const{name:NameId(1),levels:vec![]}),(3,Expr::Const{name:NameId(2),levels:vec![]}),(4,Expr::BVar(0)),(5,Expr::Lam{domain:ExprId(2),body:ExprId(4)}),(6,Expr::BVar(0)),(7,Expr::Lam{domain:ExprId(2),body:ExprId(6)}),(8,Expr::Const{name:NameId(7),levels:vec![]}),(9,Expr::App{fun:ExprId(5),arg:ExprId(8)}),(10,Expr::App{fun:ExprId(7),arg:ExprId(8)}),(11,Expr::Pi{domain:ExprId(2),body:ExprId(3)}),(12,Expr::Const{name:NameId(3),levels:vec![]}),(13,Expr::Const{name:NameId(4),levels:vec![]}),(14,Expr::App{fun:ExprId(12),arg:ExprId(8)}),(15,Expr::App{fun:ExprId(13),arg:ExprId(8)}),(16,Expr::Pi{domain:ExprId(2),body:ExprId(2)}),(17,Expr::Const{name:NameId(5),levels:vec![]}),(18,Expr::Const{name:NameId(6),levels:vec![]}),(19,Expr::App{fun:ExprId(17),arg:ExprId(8)}),(20,Expr::App{fun:ExprId(18),arg:ExprId(8)})]{e.insert(ExprId(id),node).unwrap();}
  let env=Environment::empty().extend(NameId(1),ConstantDecl::axiom(vec![],ExprId(1))).unwrap().extend(NameId(2),ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(3),ConstantDecl::axiom(vec![],ExprId(11))).unwrap().extend(NameId(4),ConstantDecl::axiom(vec![],ExprId(11))).unwrap().extend(NameId(5),ConstantDecl::axiom(vec![],ExprId(16))).unwrap().extend(NameId(6),ConstantDecl::axiom(vec![],ExprId(16))).unwrap().extend(NameId(7),ConstantDecl::axiom(vec![],ExprId(2))).unwrap();(e,l,env)
 }
 fn term(id:u64)->TypeValue{TypeValue::Term(Closure::new(ExprId(id),EnvFrame::empty()))}
 #[test]
 fn productive_captured_substitution_keeps_ordinary_exposure_allowance(){
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);
  let captured=TypeValue::Term(Closure::new(ExprId(4),EnvFrame::empty().extend(Closure::new(ExprId(19),EnvFrame::empty()))));
  for budget in 16..384 {let result=convert(&c,&captured,&term(19),budget);assert!(result.is_proven(),"actual captured substitution must expose before optional proof typing at {budget}: {result:?}");}
  assert!(convert(&c,&captured,&term(19),0).is_unknown());
 }
 #[test]
 fn deferred_captured_proof_rechecks_whole_original_sources(){
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);
  let capture=|id|TypeValue::Term(Closure::new(ExprId(4),EnvFrame::empty().extend(Closure::new(ExprId(id),EnvFrame::empty()))));
  assert!(convert(&c,&capture(14),&term(15),4096).is_proven());
  assert!(!convert(&c,&capture(19),&term(20),4096).is_proven());
  assert!(!convert(&c,&TypeValue::Term(Closure::new(ExprId(4),EnvFrame::empty())),&term(10),4096).is_proven());
 }
 #[test]
 fn productive_beta_applications_use_ordinary_comparison_before_proof_typing(){
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);let result=convert(&c,&term(9),&term(10),16);assert!(result.is_proven(),"productive ordinary beta should retain its allowance: {result:?}");
 }
 #[test]
 fn failed_proof_application_heads_retry_the_original_whole_source(){
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);let proof=convert(&c,&term(14),&term(15),4096);assert!(proof.is_proven(),"different proof functions still produce proofs of the same checked proposition: {proof:?}");
  assert!(!convert(&c,&term(19),&term(20),4096).is_proven(),"same Nat data type must not authorize proof irrelevance");
 }
 #[test]
 fn deferred_source_fallback_finishes_after_children_and_keeps_the_parent_checkpoint(){
  let c=Closure::new(ExprId(1),EnvFrame::empty());let pair=(TypeValue::Term(c.clone()),TypeValue::Term(c.clone()),0,vec![]);let mut work=ConversionWorkList::new(pair.clone());work.defer_app_proof(&c,&c,&[]);work.push(pair.clone());
  assert!(matches!(work.pop(),Some(ConversionWork::Compare(..))));let Some(ConversionWork::FinishAppProof(id))=work.pop()else{panic!("parent proof source stays alive below its ordinary descendants")};work.finish_app_proof(id);assert!(work.app_proof_fallbacks.is_empty());assert!(matches!(work.pop(),Some(ConversionWork::Compare(..))));
 }
 #[test]
 fn original_proof_parent_can_resolve_failed_data_children_but_requires_both_typed_apps(){
  let(mut e,l,env)=fixture();e.insert(ExprId(21),Expr::Const{name:NameId(8),levels:vec![]}).unwrap();e.insert(ExprId(22),Expr::App{fun:ExprId(12),arg:ExprId(21)}).unwrap();e.insert(ExprId(23),Expr::App{fun:ExprId(13),arg:ExprId(3)}).unwrap();
  let env=env.extend(NameId(8),ConstantDecl::axiom(vec![],ExprId(2))).unwrap();let c=TypeChecker::new(&e,&l,&env);
  assert!(!convert(&c,&term(8),&term(21),4096).is_proven());assert!(convert(&c,&term(14),&term(22),4096).is_proven(),"whole original proof apps resolve the failed data argument comparison");assert!(!convert(&c,&term(14),&term(23),4096).is_proven(),"the second actual ill-typed argument cannot borrow the first proof type");
 }
}

#[cfg(test)]
pub(crate) fn with_completed_domain_pair_for_test<R>(
 checker:&TypeChecker<'_>,left:&Closure,right:&Closure,context:&Rc<Vec<TypeValue>>,
 f:impl FnOnce(&ProvenDomainPair<'_>)->R,
)->R {
 assert!(convert_with_policy_in_context(checker,&TypeValue::Term(left.clone()),&TypeValue::Term(right.clone()),4096,DeltaPolicy::GuardedSemanticFallback,0,context).is_proven());
 let mut body=(**context).clone();body.push(TypeValue::Term(left.clone()));let body=Rc::new(body);
 let pair=ProvenDomainPair{left,right,context,body_context:&body};f(&pair)
}
#[cfg(test)]
mod carried_context_identity_review_tests {
 use super::*;
 use crate::id::{IdTable,LevelId,NameId};
 use crate::syntax::Level;
 use crate::environment::{Environment,ConstantDecl};
 use crate::value::{EnvFrame,LevelSubstitution};
 use crate::level::LevelTerm;
 #[test]
 fn completed_pair_pins_actual_source_and_context_namespace(){
  let mut e=IdTable::default();e.insert(ExprId(0),Expr::Sort(LevelId(0))).unwrap();e.insert(ExprId(1),Expr::Const{name:NameId(1),levels:vec![]}).unwrap();
  let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();let env=Environment::empty().extend(NameId(1),ConstantDecl::axiom(vec![],ExprId(0))).unwrap();let c=TypeChecker::new(&e,&l,&env);
  let left=Closure::new(ExprId(1),EnvFrame::empty());let right=left.clone();let gamma=Rc::new(vec![TypeValue::Term(left.clone())]);
  with_completed_domain_pair_for_test(&c,&left,&right,&gamma,|proof|{
   assert!(proof.is_for(&left,&right,&gamma));
   let left_clone=left.clone();assert!(!proof.is_for(&left_clone,&right,&gamma),"equal syntax cannot replace the completed source reference");
   let separate_gamma=(*gamma).clone();assert!(!proof.is_for(&left,&right,&separate_gamma),"equal-length/equal-type context in a separate namespace is not the original proof context");
   let changed=Closure::with_levels(left.expr,left.env.clone(),LevelSubstitution::new(vec![(NameId(90),LevelTerm::Zero)]));assert!(!proof.is_for(&changed,&right,&gamma));
   let changed_owner=Closure::new(left.expr,left.env.extend_free(FreeId(9)));assert!(!proof.is_for(&changed_owner,&right,&gamma));
   let pin=proof.completed_body_context().clone();assert!(Rc::ptr_eq(&pin,proof.completed_body_context()));assert_eq!(pin.len(),gamma.len()+1);assert_eq!(pin.last(),Some(&TypeValue::Term(left.clone())));
  });
 }
}
