#[path="typed_lineage.rs"]
mod typed_lineage;
use typed_lineage::CheckedLineage;
use std::cell::RefCell;
use std::collections::{hash_map::Entry, HashMap};
use std::rc::Rc;
use crate::machine::{ExposureCache, new_exposure_cache};

use crate::environment::Environment;
use crate::id::{ExprId, IdTable, LevelId, NameId};
use crate::judgment::Judgment;
use crate::level::{LevelTerm, imax, instantiate_level, succ};
use crate::machine::{Machine, ProjectionFieldType, Transparency};
use crate::syntax::{Expr, Level};
use crate::value::{
    Closure, EnvBinding, EnvFrame, FreeId, LevelSubstitution, Neutral, NeutralHead, Value,
};

thread_local! {static SOURCE_STRUCTURE_RELATION_ACTIVE:std::cell::Cell<bool>=const{std::cell::Cell::new(false)};}
struct SourceStructureRelationOwner;
impl SourceStructureRelationOwner {fn enter()->Option<Self>{SOURCE_STRUCTURE_RELATION_ACTIVE.with(|flag|if flag.get(){None}else{flag.set(true);Some(Self)})}}
impl Drop for SourceStructureRelationOwner {fn drop(&mut self){SOURCE_STRUCTURE_RELATION_ACTIVE.with(|flag|flag.set(false));}}
thread_local! {static GENERAL_DOMAIN_FORMATION_ACTIVE:std::cell::Cell<bool>=const{std::cell::Cell::new(false)};}
struct GeneralDomainFormationOwner;
impl GeneralDomainFormationOwner{fn enter()->Self{GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.set(true));Self}}
impl Drop for GeneralDomainFormationOwner{fn drop(&mut self){GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.set(false));}}
thread_local! {static STRUCTURAL_PI_FORMATION_ACTIVE:std::cell::Cell<bool>=const{std::cell::Cell::new(false)};}
struct StructuralPiFormationOwner;
impl StructuralPiFormationOwner{fn enter()->Option<Self>{STRUCTURAL_PI_FORMATION_ACTIVE.with(|f|{if f.get(){None}else{f.set(true);Some(Self)}})}}
impl Drop for StructuralPiFormationOwner{fn drop(&mut self){STRUCTURAL_PI_FORMATION_ACTIVE.with(|f|f.set(false));}}

thread_local! {static STRUCTURAL_APP_FORMATION_ACTIVE:std::cell::Cell<bool>=const{std::cell::Cell::new(false)};}
struct StructuralAppFormationOwner;
impl StructuralAppFormationOwner{fn enter()->Option<Self>{STRUCTURAL_APP_FORMATION_ACTIVE.with(|f|{if f.get(){None}else{f.set(true);Some(Self)}})}}
impl Drop for StructuralAppFormationOwner{fn drop(&mut self){STRUCTURAL_APP_FORMATION_ACTIVE.with(|f|f.set(false));}}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub enum TypeValue {
    Sort(LevelTerm),
    Term(Closure),
    Pi {
        domain: Box<TypeValue>,
        body: Box<TypeValue>,
        /// The lexical local opened when checking the lambda body.
        binder: FreeId,
        /// Original nominal introduction; never typing authority by itself.
        binder_owner: Option<EnvFrame>,
    },
}

/// A binder admitted after the source-domain type and substituted value
/// were checked. Both the immutable node and the protected source scope
/// must match before the certified type can be reused.
#[derive(Clone, Debug, Eq, PartialEq)]
struct CheckedBinderWitness {
    domain: TypeValue,
    protected_prefix: Rc<Vec<TypeValue>>,
}

// A completed argument check; consuming it still validates original scope.
#[derive(Clone)]
struct CheckedArgumentJudgment { function:Closure,domain:TypeValue,context:Rc<Vec<TypeValue>> }

#[derive(Clone)]
struct CheckedLambdaScope {frame:EnvFrame,witness:CheckedBinderWitness}
#[derive(Clone)]
struct SharedExpectedOpening {actual:CheckedLambdaScope,source:Closure,opened:EnvFrame}
#[derive(Clone)]
struct SourcePiOpening {source:Closure,opened:Closure,context:Vec<TypeValue>,domain:TypeValue}
#[derive(Clone)]
struct OwnedGoalDependency {
    free: Option<FreeId>, node: u64, index: u64, owner: EnvFrame,
    witness: CheckedBinderWitness, domain: TypeValue,
}
#[derive(Clone, Eq, Hash, PartialEq)]
enum CaptureFingerprint {
    Term(ExprId,LevelSubstitution,Vec<(u64,CaptureFingerprint)>),
    Free(FreeId,u64,LevelSubstitution),
    Nat(crate::nat::BigNat,LevelSubstitution),
    Bound(u64,Box<CaptureFingerprint>),
}
#[derive(Clone)]
struct OwnedLambdaGoal { source: Closure, expected: Closure, dependencies: Vec<OwnedGoalDependency> }
#[derive(Clone)]
struct ProofBinderTransport {frame:EnvFrame,original:CheckedBinderWitness,target:Vec<TypeValue>,output:TypeValue,opening:SourcePiOpening}
#[cfg(feature="diagnostics")]
thread_local!{static TRANSPORT_ARGUMENT_POST:RefCell<Option<(TypeValue,TypeValue,Vec<TypeValue>)>>=const{RefCell::new(None)};}
thread_local!{static TRANSPORT_PROOF_ACTIVE:std::cell::Cell<bool>=const{std::cell::Cell::new(false)};}
thread_local! { static OWNED_PROOF_SOURCE_ACTIVE: std::cell::Cell<bool> = const { std::cell::Cell::new(false) }; }
struct OwnedProofSourceOwner;
impl OwnedProofSourceOwner { fn enter() -> Self { OWNED_PROOF_SOURCE_ACTIVE.with(|flag| flag.set(true)); Self } }
impl Drop for OwnedProofSourceOwner { fn drop(&mut self) { OWNED_PROOF_SOURCE_ACTIVE.with(|flag| flag.set(false)); } }
struct TransportProofOwner;
impl TransportProofOwner{fn enter()->Self{TRANSPORT_PROOF_ACTIVE.with(|flag|flag.set(true));Self}}
impl Drop for TransportProofOwner{fn drop(&mut self){TRANSPORT_PROOF_ACTIVE.with(|flag|flag.set(false));}}

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
enum CheckedFrameRole { InferPi, InferLambda, ExpectedLambda, ExpectedPiOpening, LambdaIntro, LiteralBeta, Let, ExactPiSubstitution }

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
enum CheckedFrameBinding { Free(FreeId), Actual(Closure) }

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
struct CheckedFrameKey {
    source: ExprId,
    role: CheckedFrameRole,
    parent: u64,
    domain: TypeValue,
    protected_context: Rc<Vec<TypeValue>>,
    binding: CheckedFrameBinding,
    captured_codomain: Option<Closure>,
    substitution_lineage_enabled: bool,
    lineage_enabled: bool,
    strict_origin: bool,
}

#[cfg(feature = "diagnostics")]
thread_local! {
    static CAPTURE_SOURCE_FAILURE: RefCell<Option<Option<String>>> = const { RefCell::new(None) };
}
#[cfg(feature = "diagnostics")]
struct CaptureSourceFailureScope(Option<Option<String>>);
#[cfg(feature = "diagnostics")]
impl CaptureSourceFailureScope {
    fn enter() -> Self { Self(CAPTURE_SOURCE_FAILURE.with(|failure| failure.replace(Some(None)))) }
    fn first() -> Option<String> {
        CAPTURE_SOURCE_FAILURE.with(|failure| failure.borrow().as_ref().and_then(Clone::clone))
    }
}
#[cfg(feature = "diagnostics")]
impl Drop for CaptureSourceFailureScope {
    fn drop(&mut self) { CAPTURE_SOURCE_FAILURE.with(|failure| { failure.replace(self.0.take()); }); }
}

#[derive(Clone, Default)]
struct LambdaTrialState {
    quota: usize,
    active: usize,
    started: usize,
    proven: usize,
    declined: usize,
    spent: usize,
    nested_direct: usize,
    skipped: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum RuleKAttempt {
    NotApplicable,
    Reduced(Closure),
    DefiniteMismatch,
}

pub struct TypeChecker<'a> {
    expressions: &'a IdTable<ExprId, Expr>,
    levels: &'a IdTable<LevelId, Level>,
    environment: &'a Environment,
    level_substitution: HashMap<NameId, LevelTerm>,
    delta_policy: crate::convert::DeltaPolicy,
    exposure_cache: ExposureCache,
    // Eligibility is structural; typing proofs stay in the per-judgment cache.
    closed_spine_eligibility: RefCell<HashMap<ExprId, bool>>,
    completed_pi_lifts: Rc<RefCell<std::collections::HashSet<(ExprId,ExprId)>>>,
    source_support: Rc<RefCell<HashMap<ExprId, Vec<u64>>>>,
    source_capture_bindings: RefCell<HashMap<(u64,u64),(EnvFrame,EnvFrame)>>,
    owned_lambda_goals: RefCell<HashMap<ExprId,Vec<OwnedLambdaGoal>>>,
    lambda_shape_ids: RefCell<HashMap<ExprId,u64>>,
    lambda_shape_nodes: RefCell<HashMap<(u8,u64,u64,u64,u64),u64>>,
    owned_lambda_shapes: RefCell<HashMap<(ExprId,Option<ExprId>,u64),Vec<OwnedLambdaGoal>>>,
    owned_lambda_shape_domains: RefCell<HashMap<(ExprId,Option<ExprId>),Vec<u64>>>,
    paired_lambda_hint_facts: RefCell<HashMap<(ExprId,ExprId),bool>>,
    repeated_completed_apps: RefCell<HashMap<(ExprId,ExprId),u8>>,
    owned_application_patterns: RefCell<HashMap<(u64,ExprId),Vec<OwnedLambdaGoal>>>,
    source_syntax_patterns: RefCell<HashMap<ExprId,(u64,Vec<u64>)>>,
    source_syntax_pattern_nodes: RefCell<HashMap<((u8,u64,u64,u64,u64),Vec<Vec<u64>>),u64>>,
    formed_lambda_goals: RefCell<HashMap<(ExprId,u64,TypeValue,Vec<TypeValue>),Vec<OwnedGoalDependency>>>,
    paired_source_support: RefCell<HashMap<(ExprId, ExprId), Vec<(u64, u64)>>>,
    checked_frames: RefCell<HashMap<CheckedFrameKey, EnvFrame>>,
    lambda_intro_scopes:Rc<RefCell<HashMap<u64,CheckedLambdaScope>>>,
    shared_expected_openings:Rc<RefCell<HashMap<(u64,ExprId,u64,usize),SharedExpectedOpening>>>,
    source_pi_openings:Rc<RefCell<HashMap<u64,SourcePiOpening>>>,
    proof_binder_transports:Rc<RefCell<HashMap<u64,Vec<ProofBinderTransport>>>>,
    proof_transport_context_keys:Rc<RefCell<std::collections::HashSet<(usize,ExprId,u64,usize)>>>,
    // Completed pure source-freshness proofs, local to these borrowed immutable
    // source tables. Retained closures pin frame and level allocation identity.
    source_opening_proofs: RefCell<HashMap<(ExprId,u64,usize,FreeId),Closure>>,
    source_capture_free_support: Rc<RefCell<HashMap<(ExprId,u64,usize,u64),(Closure,Rc<Vec<FreeId>>)>>>,
    // Closed source types admitted by this checker's actual formation judgment.
    formed_expected: RefCell<std::collections::HashSet<Closure>>,
    lambda_trials: RefCell<LambdaTrialState>,
    checked_binding_lineage: Rc<CheckedLineage>,
    checked_arguments: Rc<RefCell<HashMap<Closure,Vec<CheckedArgumentJudgment>>>>,
    binding_checks_active: Rc<RefCell<std::collections::HashSet<u64>>>,
    // Diagnostic-only strictness: a FreeId is typed solely by its checked
    // immutable binder node under the identical protected source scope.
    strict_origin_probe: bool,
}

pub(crate) struct CheckedEtaBody { body:Closure, context:Rc<Vec<TypeValue>> }
impl CheckedEtaBody {
 pub(crate) fn body(&self)->&Closure{&self.body}
 pub(crate) fn context(&self)->&[TypeValue]{&self.context}
}

impl<'a> TypeChecker<'a> {
    fn reset_lambda_trials(&self, budget: usize) {
        *self.lambda_trials.borrow_mut() = LambdaTrialState {
            quota: budget.min(4096), ..LambdaTrialState::default()
        };
    }

    fn begin_lambda_trial(&self, remaining: usize) -> Option<usize> {
        let mut trials = self.lambda_trials.borrow_mut();
        if trials.active != 0 || trials.quota == 0 || remaining == 0 {
            trials.skipped += 1;
            return None;
        }
        let budget = remaining.min(4096).min(trials.quota);
        trials.quota -= budget;
        trials.started += 1;
        trials.active += 1;
        Some(budget)
    }

    fn finish_lambda_trial(&self, budget: usize, remaining: usize, proven: bool) {
        let mut trials = self.lambda_trials.borrow_mut();
        trials.active -= 1;
        let spent = budget.saturating_sub(remaining);
        trials.spent += spent;
        trials.quota += remaining.min(budget);
        if proven { trials.proven += 1; } else { trials.declined += 1; }
    }
    pub fn new(
        expressions: &'a IdTable<ExprId, Expr>,
        levels: &'a IdTable<LevelId, Level>,
        environment: &'a Environment,
    ) -> Self {
        Self {
            expressions,
            levels,
            environment,
            level_substitution: HashMap::new(),
            delta_policy: crate::convert::DeltaPolicy::GuardedSemanticFallback,
            exposure_cache: new_exposure_cache(),
            closed_spine_eligibility: RefCell::new(HashMap::new()),
            completed_pi_lifts: Rc::new(RefCell::new(std::collections::HashSet::new())),
            source_support: Rc::new(RefCell::new(HashMap::new())),
            source_capture_bindings: RefCell::new(HashMap::new()),
            owned_lambda_goals: RefCell::new(HashMap::new()),
            lambda_shape_ids: RefCell::new(HashMap::new()),
            lambda_shape_nodes: RefCell::new(HashMap::new()),
            owned_lambda_shapes: RefCell::new(HashMap::new()),
            paired_lambda_hint_facts: RefCell::new(HashMap::new()),
            owned_lambda_shape_domains: RefCell::new(HashMap::new()),
            repeated_completed_apps: RefCell::new(HashMap::new()),
            owned_application_patterns: RefCell::new(HashMap::new()),
            source_syntax_patterns: RefCell::new(HashMap::new()),
            source_syntax_pattern_nodes: RefCell::new(HashMap::new()),
            formed_lambda_goals: RefCell::new(HashMap::new()),
            paired_source_support: RefCell::new(HashMap::new()),
            checked_frames: RefCell::new(HashMap::new()),
            lambda_intro_scopes:Rc::new(RefCell::new(HashMap::new())),
            shared_expected_openings:Rc::new(RefCell::new(HashMap::new())),
            source_pi_openings:Rc::new(RefCell::new(HashMap::new())),
            proof_binder_transports:Rc::new(RefCell::new(HashMap::new())),
            proof_transport_context_keys:Rc::new(RefCell::new(std::collections::HashSet::new())),
            source_opening_proofs:RefCell::new(HashMap::new()),
            source_capture_free_support:Rc::new(RefCell::new(HashMap::new())),
            formed_expected: RefCell::new(std::collections::HashSet::new()),
            lambda_trials: RefCell::new(LambdaTrialState::default()),
            checked_binding_lineage: Rc::new(CheckedLineage::new(HashMap::new())),
            checked_arguments: Rc::new(RefCell::new(HashMap::new())),
            binding_checks_active: Rc::new(RefCell::new(std::collections::HashSet::new())),
            strict_origin_probe: false,
        }
    }

    pub fn with_level_substitution(
        expressions: &'a IdTable<ExprId, Expr>,
        levels: &'a IdTable<LevelId, Level>,
        environment: &'a Environment,
        level_substitution: HashMap<NameId, LevelTerm>,
    ) -> Self {
        Self {
            expressions,
            levels,
            environment,
            level_substitution,
            delta_policy: crate::convert::DeltaPolicy::GuardedSemanticFallback,
            exposure_cache: new_exposure_cache(),
            closed_spine_eligibility: RefCell::new(HashMap::new()),
            completed_pi_lifts: Rc::new(RefCell::new(std::collections::HashSet::new())),
            source_support: Rc::new(RefCell::new(HashMap::new())),
            source_capture_bindings: RefCell::new(HashMap::new()),
            owned_lambda_goals: RefCell::new(HashMap::new()),
            lambda_shape_ids: RefCell::new(HashMap::new()),
            lambda_shape_nodes: RefCell::new(HashMap::new()),
            owned_lambda_shapes: RefCell::new(HashMap::new()),
            paired_lambda_hint_facts: RefCell::new(HashMap::new()),
            owned_lambda_shape_domains: RefCell::new(HashMap::new()),
            repeated_completed_apps: RefCell::new(HashMap::new()),
            owned_application_patterns: RefCell::new(HashMap::new()),
            source_syntax_patterns: RefCell::new(HashMap::new()),
            source_syntax_pattern_nodes: RefCell::new(HashMap::new()),
            formed_lambda_goals: RefCell::new(HashMap::new()),
            paired_source_support: RefCell::new(HashMap::new()),
            checked_frames: RefCell::new(HashMap::new()),
            lambda_intro_scopes:Rc::new(RefCell::new(HashMap::new())),
            shared_expected_openings:Rc::new(RefCell::new(HashMap::new())),
            source_pi_openings:Rc::new(RefCell::new(HashMap::new())),
            proof_binder_transports:Rc::new(RefCell::new(HashMap::new())),
            proof_transport_context_keys:Rc::new(RefCell::new(std::collections::HashSet::new())),
            source_opening_proofs:RefCell::new(HashMap::new()),
            source_capture_free_support:Rc::new(RefCell::new(HashMap::new())),
            formed_expected: RefCell::new(std::collections::HashSet::new()),
            lambda_trials: RefCell::new(LambdaTrialState::default()),
            checked_binding_lineage: Rc::new(CheckedLineage::new(HashMap::new())),
            checked_arguments: Rc::new(RefCell::new(HashMap::new())),
            binding_checks_active: Rc::new(RefCell::new(std::collections::HashSet::new())),
            strict_origin_probe: false,
        }
    }

    pub fn with_delta_policy(mut self, policy: crate::convert::DeltaPolicy) -> Self {
        self.formed_expected.borrow_mut().clear();
        self.delta_policy = policy;
        self
    }

    /// Retain a scope-indexed type judgment only AFTER the binder's source
    /// domain was certified (Pi/Lam) or its substituted argument was checked
    /// against that domain (Let / exact beta spine). This is the substitution
    /// lemma as an explicit, local premise rather than a context-index guess.
    fn retain_checked_binding(
        &self,
        frame: &EnvFrame,
        domain: TypeValue,
        protected_context: &[TypeValue],
    ) {
        if std::env::var_os("NUCLEUS_EXPERIMENTAL_TYPED_LINEAGE").is_none()
            && !self.strict_origin_probe
        {
            return;
        }
        self.retain_shared_checked_binding(frame,domain,Rc::new(protected_context.to_vec()));
    }

    fn retain_shared_checked_binding(&self,frame:&EnvFrame,domain:TypeValue,protected_prefix:Rc<Vec<TypeValue>>) {
        if std::env::var_os("NUCLEUS_EXPERIMENTAL_TYPED_LINEAGE").is_none() && !self.strict_origin_probe{return;}
        let node=frame.id();
        let witness=CheckedBinderWitness {
            domain,
            protected_prefix,
        };
        let mut ledger=self.checked_binding_lineage.borrow_mut();
        match ledger.get(&node) {
            None=>{ledger.insert(node,Some(witness));},
            Some(old) if old.as_ref()!=Some(&witness)=>{ledger.insert(node,None);},
            _=>{},
        }
    }

    /// Called only after domain formation and, for actual substitutions,
    /// argument typing. Exact source and full Γ equality preserve the scope
    /// of each retained witness; no local or context quotient is involved.
    fn checked_source_frame(
        &self, source: ExprId, role: CheckedFrameRole, parent: &EnvFrame,
        domain: TypeValue, protected_context: &[TypeValue], binding: CheckedFrameBinding,
    ) -> EnvFrame {
        self.checked_source_frame_with_codomain(source, role, parent, domain,
            protected_context, binding, None)
    }

    fn checked_captured_pi_frame(
        &self, codomain: &Closure, argument: &Closure, domain: TypeValue,
        protected_context: &[TypeValue],
    ) -> EnvFrame {
        self.checked_source_frame_with_codomain(codomain.expr,
            CheckedFrameRole::ExactPiSubstitution, &codomain.env, domain,
            protected_context, CheckedFrameBinding::Actual(argument.clone()),
            Some(codomain.clone()))
    }

    fn checked_source_frame_with_codomain(
        &self, source: ExprId, role: CheckedFrameRole, parent: &EnvFrame,
        domain: TypeValue, protected_context: &[TypeValue], binding: CheckedFrameBinding,
        captured_codomain: Option<Closure>,
    ) -> EnvFrame {
        let substitution_lineage_enabled =
            std::env::var_os("NUCLEUS_EXPERIMENTAL_SUBSTITUTION_RECLOSURE").is_some();
        let lineage_enabled = self.strict_origin_probe
            || std::env::var_os("NUCLEUS_EXPERIMENTAL_TYPED_LINEAGE").is_some();
        let shared_context=Rc::new(protected_context.to_vec());
        let retain = |frame: &EnvFrame, domain| {
            if role == CheckedFrameRole::ExactPiSubstitution {
                self.retain_checked_elimination(frame, domain, protected_context);
            } else {
                self.retain_shared_checked_binding(frame, domain, shared_context.clone());
            }
        };
        // Avoid recursive fixed-Pi hashing and bound retained scope vectors.
        let eligible = protected_context.len() <= 128
            && !matches!(&domain, TypeValue::Pi { .. })
            && protected_context.iter().all(|ty| !matches!(ty, TypeValue::Pi { .. }));
        // Both lambda routes independently prove the source annotation's
        // formation before reaching this constructor. They introduce the
        // same annotated domain and fresh local under the exact full Γ.
        // Only that certified Free introduction has a shared cache role.
        let cache_role=if matches!(role,CheckedFrameRole::InferLambda|CheckedFrameRole::ExpectedLambda)
            && captured_codomain.is_none()
            && protected_context.last()==Some(&domain)
            && matches!(&binding,CheckedFrameBinding::Free(free) if !protected_context.is_empty() && fresh_local(protected_context.len()-1)==Some(*free))
            && matches!((self.expressions.get(source),&domain),
                (Some(Expr::Lam{domain:annotation,..}),TypeValue::Term(term))
                    if term.expr==*annotation && term.env.id()==parent.id())
        {CheckedFrameRole::LambdaIntro}else{role};
        let remember_intro=|frame:&EnvFrame| {
            if cache_role==CheckedFrameRole::LambdaIntro
                && let Some(Some(witness))=self.checked_binding_lineage.borrow().get(&frame.id()) {
                let mut scopes=self.lambda_intro_scopes.borrow_mut();
                if scopes.len()<8192 || scopes.contains_key(&frame.id()) {
                    scopes.entry(frame.id()).or_insert_with(||CheckedLambdaScope{frame:frame.clone(),witness:witness.clone()});
                }
            }
        };
        let key = eligible.then(|| CheckedFrameKey {
            source, role:cache_role, parent: parent.id(), domain: domain.clone(),
            protected_context: shared_context.clone(), binding: binding.clone(),
            captured_codomain, substitution_lineage_enabled,
            lineage_enabled, strict_origin: self.strict_origin_probe,
        });
        if let Some(key) = &key {
            let existing = self.checked_frames.borrow().get(key).cloned();
            if let Some(frame) = existing {
                let reusable = match self.checked_binding_lineage.borrow().get(&frame.id()) {
                    Some(Some(witness)) => witness.domain == domain
                        && witness.protected_prefix.as_slice() == protected_context,
                    Some(None) => false,
                    None => !lineage_enabled || (role == CheckedFrameRole::ExactPiSubstitution
                        && !substitution_lineage_enabled),
                };
                if reusable {
                    retain(&frame, domain);
                    remember_intro(&frame);
                    return frame;
                }
            }
        }
        let frame = match binding {
            CheckedFrameBinding::Free(free) => parent.extend_free(free),
            CheckedFrameBinding::Actual(actual) => parent.extend(actual),
        };
        retain(&frame, domain);
        remember_intro(&frame);
        if let Some(key) = key {
            let mut frames = self.checked_frames.borrow_mut();
            // Saturation preserves existing immutable proofs and falls back
            // to ordinary fresh allocation for new source tuples.
            if frames.len() < 8192 || frames.contains_key(&key) {
                frames.insert(key, frame.clone());
            }
        }
        frame
    }

    fn checked_lambda_scope(&self,frame:&EnvFrame)->Option<CheckedLambdaScope> {
        let token=self.lambda_intro_scopes.borrow().get(&frame.id())?.clone();
        let ledger=self.checked_binding_lineage.borrow();let current=ledger.get(&frame.id())?.as_ref()?;
        (current.domain==token.witness.domain && Rc::ptr_eq(&current.protected_prefix,&token.witness.protected_prefix)).then_some(token)
    }

    // Only the actual checked lambda introduction can supply this scope.
    // The caller has already formed the expected Pi and actual annotation,
    // converted their domains, and completed the source freshness guards.
    fn shared_expected_pi_frame(&self,source:&Closure,actual:&CheckedLambdaScope,free:FreeId,remaining:&mut usize)->Option<EnvFrame> {
        if !take_step(remaining){return None;}
        let known=self.lambda_intro_scopes.borrow().get(&actual.frame.id())?.clone();
        if known.frame!=actual.frame || known.witness.domain!=actual.witness.domain
            || !Rc::ptr_eq(&known.witness.protected_prefix,&actual.witness.protected_prefix){return None;}
        let current=self.checked_binding_lineage.borrow().get(&actual.frame.id())?.as_ref()?.clone();
        if current.domain!=known.witness.domain
            || !Rc::ptr_eq(&current.protected_prefix,&known.witness.protected_prefix)
            || current.protected_prefix.last()!=Some(&current.domain)
            || fresh_local(current.protected_prefix.len().checked_sub(1)?)!=Some(free)
            || !matches!(actual.frame.lookup_binding_ref(0),Some(EnvBinding::Free(value)) if *value==free){return None;}
        let key=(actual.frame.id(),source.expr,source.env.id(),source.levels.identity());
        if let Some(prior)=self.shared_expected_openings.borrow().get(&key).cloned() {
            if prior.actual.frame!=actual.frame || prior.source!=*source
                || !Rc::ptr_eq(&prior.actual.witness.protected_prefix,&current.protected_prefix)
                || prior.actual.witness.domain!=current.domain{return None;}
            let witness=self.checked_binding_lineage.borrow().get(&prior.opened.id())?.as_ref()?.clone();
            if witness.domain!=current.domain || !Rc::ptr_eq(&witness.protected_prefix,&current.protected_prefix)
                || !matches!(prior.opened.lookup_binding_ref(0),Some(EnvBinding::Neutral(Neutral{head:NeutralHead::Free(value,Some(owner)),spine})) if *value==free && owner==&actual.frame && spine.is_empty()){return None;}
            return Some(prior.opened);
        }
        // The two bodies refer to ONE introduced nominal variable. The
        // expected wrapper keeps its original captured parent while its
        // binder value carries the actual checked lambda owner's identity.
        let opened=source.env.extend_neutral_paid(Neutral{
            head:NeutralHead::Free(free,Some(actual.frame.clone())),spine:Vec::new(),
        },remaining)?;
        if !take_step(remaining){return None;}
        self.retain_shared_checked_binding(&opened,current.domain.clone(),current.protected_prefix.clone());
        let certificate=SharedExpectedOpening{actual:known,source:source.clone(),opened:opened.clone()};
        let mut openings=self.shared_expected_openings.borrow_mut();
        if openings.len()<8192{openings.insert(key,certificate);}
        Some(opened)
    }

    fn retain_checked_elimination(
        &self,
        frame:&EnvFrame,
        domain:TypeValue,
        protected_context:&[TypeValue],
    ){
        // This stronger substitution lineage is A/B guarded independently
        // of the already qualified local binder-introduction ledger.
        if std::env::var_os("NUCLEUS_EXPERIMENTAL_SUBSTITUTION_RECLOSURE").is_some(){
            self.retain_checked_binding(frame,domain,protected_context);
            #[cfg(feature="diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_SUBSTITUTION_RECLOSURE").is_some(){
                use std::sync::atomic::{AtomicUsize,Ordering};
                static SEEN:AtomicUsize=AtomicUsize::new(0);
                if self.checked_binding_lineage.borrow().get(&frame.id())
                    .is_some_and(|w|w.is_some())
                    && SEEN.fetch_add(1,Ordering::Relaxed)<80
                {
                    eprintln!(
                        "NUCLEUS_TYPED_SUBSTITUTION_RECLOSURE:frame={}:checked_prefix={}:registered=true",
                        frame.id(),protected_context.len()
                    );
                }
            }
        }
    }

    #[cfg(feature="diagnostics")]
    fn proof_transport_trace(stage:&str,detail:impl std::fmt::Debug){
        if std::env::var_os("NUCLEUS_TRACE_PROOF_TRANSPORT").is_none(){return;}
        use std::sync::atomic::{AtomicUsize,Ordering};static COUNT:AtomicUsize=AtomicUsize::new(0);
        if COUNT.fetch_add(1,Ordering::Relaxed)<96{eprintln!("PROOF_TRANSPORT:{stage}:{detail:?}");}
    }

    fn strict_certificate_probe(&self)->Self {
        let mut probe=Self::with_level_substitution(self.expressions,self.levels,self.environment,self.level_substitution.clone());
        // Completed lexical support is independent of the typing policy,
        // real Gamma and universe substitution. This probe uses the exact
        // same immutable expression table, so retain its paid syntax facts.
        probe.completed_pi_lifts=self.completed_pi_lifts.clone();
        probe.source_support=self.source_support.clone();
        probe.source_capture_free_support=self.source_capture_free_support.clone();
        probe.checked_binding_lineage=self.checked_binding_lineage.clone();
        probe.checked_arguments=self.checked_arguments.clone();
        probe.binding_checks_active=self.binding_checks_active.clone();
        probe.shared_expected_openings=self.shared_expected_openings.clone();
        probe.lambda_intro_scopes=self.lambda_intro_scopes.clone();
        probe.source_pi_openings=self.source_pi_openings.clone();
        probe.proof_binder_transports=self.proof_binder_transports.clone();
        probe.proof_transport_context_keys=self.proof_transport_context_keys.clone();
        probe.strict_origin_probe=true;probe
    }

    // A checked monomorphic global whose declared type is a literal Sort
    // supplies a formed type in every local context. Both original domain
    // operands must independently be that global with its exact zero arity.
    // This licenses only domain formation/reflexivity, never any local pair.
    fn checked_domain_source_alias(&self,source:&Closure,remaining:&mut usize)->Option<Closure> {
        let mut actual=source.clone();
        let mut seen=std::collections::HashSet::new();
        loop {
            if !take_step(remaining){return None;}
            if !seen.insert((actual.expr,actual.env.id(),actual.levels.identity())){return None;}
            match self.expressions.get(actual.expr)? {
                Expr::BVar(index)=>{
                    let owner=self.source_capture_owner(&actual.env,*index,remaining)?;
                    if !take_step(remaining){return None;}
                    let EnvBinding::Closure(payload)=owner.lookup_binding_ref(0)? else{return None;};
                    // Source substitution uses the stored value's own levels,
                    // not the unrelated level map on the BVar occurrence.
                    actual=payload.clone();
                },
                Expr::Const{..}|Expr::Sort(_)=>return Some(actual),
                _=>return None,
            }
        }
    }

    pub(crate) fn checked_closed_atomic_domain_pair(
        &self, left: &Closure, right: &Closure, remaining: &mut usize,
    ) -> bool {
        let Some(left)=self.checked_domain_source_alias(left,remaining) else{return false;};
        let Some(right)=self.checked_domain_source_alias(right,remaining) else{return false;};
        if !take_step(remaining) { return false; }
        if let Some(Expr::Sort(left_level))=self.expressions.get(left.expr) {
            if !take_step(remaining){return false;}
            let Some(Expr::Sort(right_level))=self.expressions.get(right.expr) else{return false;};
            // Each Sort is formed only from its own original universe graph
            // and own substitution. Failure/cycles/missing substitutions deny
            // admission before any shared binder is constructed.
            let Ok(left_level)=crate::level::instantiate_level_with_remaining(self.levels,*left_level,&left.levels,remaining) else{return false;};
            let Ok(right_level)=crate::level::instantiate_level_with_remaining(self.levels,*right_level,&right.levels,remaining) else{return false;};
            return crate::level::level_equal_with_remaining(left_level,right_level,remaining).is_proven();
        }
        let Some(Expr::Const{name:left_name,levels:left_levels})=self.expressions.get(left.expr) else { return false; };
        if !left_levels.is_empty() { return false; }
        if !take_step(remaining) { return false; }
        let Some(Expr::Const{name:right_name,levels:right_levels})=self.expressions.get(right.expr) else { return false; };
        if !right_levels.is_empty() || left_name!=right_name { return false; }
        if !take_step(remaining) { return false; }
        let Some(decl)=self.environment.get(*left_name) else { return false; };
        if !decl.level_params.is_empty() { return false; }
        if !take_step(remaining) { return false; }
        matches!(self.expressions.get(decl.ty),Some(Expr::Sort(_)))
    }

    /// One nominal introduction shared by two original source bodies.
    /// Only the already-checked closed atomic domain rule supplies formation
    /// and domain equality. The right capture is an owned alias of the one
    /// actual left local, not a same-number independent introduction.
    pub(crate) fn checked_source_eta_opening(&self,lambda_source:&Closure,function_source:&Closure,domain:&Closure,body:&Closure,context:&[TypeValue],free:FreeId,remaining:&mut usize)->Option<CheckedEtaBody> {
        if usize::try_from(free.0).ok()!=Some(context.len()){return None;}
        if !self.source_used_capture_authority_available(lambda_source,remaining)||!self.source_used_capture_authority_available(function_source,remaining){return None;}
        let probe=self.strict_certificate_probe();
        let lambda_type=probe.infer_exact_closure_in_context(lambda_source,context,remaining,0)?;
        let function_type=probe.infer_exact_closure_in_context(function_source,context,remaining,0)?;
        let allowance=(*remaining).min(256);if allowance==0{return None;}*remaining-=allowance;
        if !crate::convert::convert_with_policy_in_context(&probe,&lambda_type,&function_type,allowance,crate::convert::DeltaPolicy::GuardedSemanticFallback,context.len(),context).is_proven(){return None;}
        probe.shared_strict_source_sort(domain,context,remaining)?;
        if !crate::convert::source_opening_avoids_capture(self,body,free,remaining){return None;}
        let cost=context.len().checked_add(1)?;if *remaining<cost{return None;}*remaining-=cost;
        let ty=TypeValue::Term(domain.clone());let mut extended=context.to_vec();extended.push(ty.clone());
        let owner=body.env.extend_free_paid(free,remaining)?;if !take_step(remaining){return None;}
        let context=Rc::new(extended);probe.retain_shared_checked_binding(&owner,ty,context.clone());Some(CheckedEtaBody{body:body.sibling(body.expr,owner),context})
    }
    pub(crate) fn eta_fresh_argument(&self,opened:&CheckedEtaBody,remaining:&mut usize)->Option<Closure> {
        let mut pending=vec![opened.body.expr];let mut seen=std::collections::HashSet::new();
        for _ in 0..64 {
            let id=pending.pop()?;if !take_step(remaining){return None;}if !seen.insert(id){continue;}
            match self.expressions.get(id)? {
                Expr::BVar(0)=>return Some(opened.body.sibling(id,opened.body.env.clone())),
                Expr::App{fun,arg}=>{pending.push(*fun);pending.push(*arg);},
                Expr::Lam{domain,body}|Expr::Pi{domain,body}=>{pending.push(*domain);pending.push(*body);},
                Expr::Let{ty,value,body}=>{pending.push(*ty);pending.push(*value);pending.push(*body);},
                Expr::Proj{structure,..}=>pending.push(*structure),_=>{},
            }
        }None
    }

    pub(crate) fn eta_body_result_is_rigid(&self,opened:&CheckedEtaBody,remaining:&mut usize)->bool {
        if !self.source_used_capture_authority_available(opened.body(),remaining){return false;}
        let probe=self.strict_certificate_probe();let Some(ty)=probe.infer_exact_closure_in_context(opened.body(),opened.context(),remaining,0)else{return false;};
        let Some(sort)=probe.owned_inferred_type_formation_sort(&ty,opened.context(),remaining,0)else{return false;};
        if !crate::level::level_equal_with_remaining(sort,LevelTerm::Zero,remaining).is_refuted(){return false;}
        let TypeValue::Term(source)=ty else{return matches!(ty,TypeValue::Sort(_));};
        let allowance=(*remaining).min(128);if allowance==0{return false;}*remaining-=allowance;
        match probe.machine().expose(source,Transparency::Reducible,allowance).proven_value(){
            Some(Value::Sort(_))=>true,
            Some(Value::Neutral(Neutral{head:NeutralHead::Free(free,Some(owner)),spine})) if spine.is_empty()=>{
                if !matches!(owner.lookup_binding_ref(0),Some(EnvBinding::Free(actual)) if actual==free){return false;}
                let ledger=probe.checked_binding_lineage.borrow();let Some(Some(w))=ledger.get(&owner.id())else{return false;};
                fresh_local(w.protected_prefix.len().saturating_sub(1))==Some(*free)&&!w.protected_prefix.is_empty()&&opened.context().starts_with(&w.protected_prefix)
            },_=>false,
        }
    }

    // Read the TYPE of an actual source binding, not the type of that TYPE.
    // The existing checked witness validates original/current ownership and
    // its exact protected Gamma. Only a literal Sort is sufficient here;
    // this path never starts recursive inference under an active formation.
    fn checked_bound_literal_sort(&self,source:&Closure,context:&[TypeValue],remaining:&mut usize)->Option<LevelTerm> {
        if !self.source_used_capture_authority_available(source,remaining){return None;}
        let probe=self.strict_certificate_probe();let mut actual=source.clone();let mut seen=std::collections::HashSet::new();
        loop {
            if !take_step(remaining)||!seen.insert(actual.clone()){return None;}
            let Expr::BVar(index)=self.expressions.get(actual.expr)? else{return None;};
            let owner=self.source_capture_owner(&actual.env,*index,remaining)?;
            if !take_step(remaining){return None;}
            if let Some(ty)=probe.checked_type_of_bound_source(&actual.env,*index,context){
                return match ty {
                    TypeValue::Sort(level)=>Some(level),
                    TypeValue::Term(sort)=>{
                        if !self.source_used_capture_authority_available(&sort,remaining)||!take_step(remaining){return None;}
                        if let Some(Expr::Sort(level))=self.expressions.get(sort.expr){
                            return crate::level::instantiate_level_with_remaining(self.levels,*level,&sort.levels,remaining).ok();
                        }
                        // The checked binding records this ORIGINAL formed
                        // TYPE. During active formation it may transparently
                        // expose a Sort; never infer the type of that TYPE.
                        if !GENERAL_DOMAIN_FORMATION_ACTIVE.with(|flag|flag.get()){return None;}
                        let allowance=(*remaining).min(32);if allowance==0{return None;}*remaining-=allowance;
                        match probe.machine().expose_for_conversion(sort,Transparency::Reducible,allowance).proven_value(){
                            Some(Value::Sort(level))=>Some(level.clone()),_=>None,
                        }
                    },TypeValue::Pi{..}=>None,
                };
            }
            // An unowned beta cell may carry an actual captured type variable;
            // every wrapper was checked above and its original source value
            // keeps its own universes. Arbitrary App/lambda values decline.
            let EnvBinding::Closure(value)=owner.lookup_binding_ref(0)? else{return None;};
            actual=value.clone();
        }
    }
    // This bounded structural trial forms only an actual literal source Pi.
    // It leaves the outer domain-formation guard active and shares the caller's
    // allowance; a recursive structural trial conservatively declines.
    fn checked_active_source_sort(&self,source:&Closure,context:&[TypeValue],remaining:&mut usize)->Option<LevelTerm> {
        if matches!(self.expressions.get(source.expr),Some(Expr::BVar(_))){if let Some(sort)=self.checked_bound_literal_sort(source,context,remaining){return Some(sort);}}
        // This derives the TYPE of the original application under actual Gamma.
        // It keeps the outer formation guard and one shared work owner active;
        // a recursive application-formation trial cannot supply a certificate.
        if GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.get())&&matches!(self.expressions.get(source.expr),Some(Expr::App{..})) {
            let _application=StructuralAppFormationOwner::enter()?;
            if !self.source_used_capture_authority_available(source,remaining){return None;}
            return self.strict_certificate_probe().shared_strict_source_sort(source,context,remaining);
        }
        if !GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.get())||!matches!(self.expressions.get(source.expr),Some(Expr::Pi{..})){return None;}
        let _structural=StructuralPiFormationOwner::enter()?;
        if !self.source_used_capture_authority_available(source,remaining){return None;}
        let probe=self.strict_certificate_probe();
        probe.shared_strict_source_sort(source,context,remaining)
    }
    fn shared_strict_source_sort(&self,source:&Closure,context:&[TypeValue],remaining:&mut usize)->Option<LevelTerm> {
        let ty=self.infer_exact_closure_in_context(source,context,remaining,0)?;
        match ty {
            TypeValue::Sort(level)=>Some(level),
            TypeValue::Term(actual_type)=>{
                if !take_step(remaining){return None;}
                if let Some(Expr::Sort(level))=self.expressions.get(actual_type.expr){crate::level::instantiate_level_with_remaining(self.levels,*level,&actual_type.levels,remaining).ok()}
                else{let allowance=(*remaining).min(32);if allowance==0{return None;}*remaining-=allowance;self.sort_level(Judgment::proven(TypeValue::Term(actual_type),"actual-inferred-domain-type"),allowance).proven_value().cloned()}
            },TypeValue::Pi{..}=>None,
        }
    }
    pub(crate) fn checked_proven_domain_joint_opening(&self,proven:&crate::convert::ProvenDomainPair<'_>,left_domain:&Closure,right_domain:&Closure,left_body:&Closure,right_body:&Closure,context:&[TypeValue],free:FreeId,remaining:&mut usize)->Option<(Closure,Closure)> {
        if !proven.is_for(left_domain,right_domain,context){return None;}
        let bound=self.checked_active_source_sort(left_domain,context,remaining).is_some()&&self.checked_active_source_sort(right_domain,context,remaining).is_some();
        let _owner=if bound{None}else{if GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.get()){return None;}Some(GeneralDomainFormationOwner::enter())};
        if !bound{let probe=self.strict_certificate_probe();probe.shared_strict_source_sort(left_domain,context,remaining)?;probe.shared_strict_source_sort(right_domain,context,remaining)?;}
        self.checked_formed_joint_opening_with_prefix(left_domain,left_body,right_body,context,free,proven.completed_body_context(),remaining)
    }
    pub(crate) fn checked_fixed_pi_joint_bodies(&self,proven:&crate::convert::ProvenDomainPair<'_>,left_domain:&Closure,right_domain:&Closure,left_body:&TypeValue,right_body:&TypeValue,left_binder:FreeId,right_binder:FreeId,left_owner:&EnvFrame,right_owner:&EnvFrame,context:&[TypeValue],free:FreeId,remaining:&mut usize)->Option<(TypeValue,TypeValue)> {
        if !proven.is_for(left_domain,right_domain,context)||usize::try_from(free.0).ok()!=Some(context.len()){return None;}
        if !matches!(left_owner.lookup_binding_ref(0),Some(EnvBinding::Free(f)) if *f==left_binder)||!matches!(right_owner.lookup_binding_ref(0),Some(EnvBinding::Free(f)) if *f==right_binder){return None;}
        let ledger=self.checked_binding_lineage.borrow();if ledger.get(&left_owner.id()).is_some_and(Option::is_none)||ledger.get(&right_owner.id()).is_some_and(Option::is_none){return None;}drop(ledger);
        // Atomic formation uses only each original closed declaration/Sort;
        // it cannot recurse into another typing judgment or clear the outer
        // formation guard. Both actual owners were checked above.
        if !self.source_used_capture_authority_available(left_domain,remaining)||!self.source_used_capture_authority_available(right_domain,remaining){return None;}
        // This is the actual checked inferred binder, not an owner minted
        // by converting an exposed Pi. Its full original body Gamma and
        // source domain must be exactly the current completed continuation.
        let existing=if left_binder==free&&left_owner.parent_id()==Some(left_domain.env.id()){
            if !take_step(remaining){return None;}
            self.checked_binding_lineage.borrow().get(&left_owner.id()).cloned().flatten()
        }else{None};
        let reuse=if let Some(witness)=existing{
            let cost=proven.completed_body_context().len().checked_add(1)?;
            if *remaining<cost{return None;}*remaining-=cost;
            witness.domain==TypeValue::Term(left_domain.clone())
                &&witness.protected_prefix.as_slice()==proven.completed_body_context().as_slice()
        }else{false};
        if reuse {
            // The original witness certifies only LEFT domain formation.
            // A beta-erased ill-typed RIGHT domain is independently refused.
            let probe=self.strict_certificate_probe();
            let right_atomic=probe.checked_closed_atomic_domain_pair(right_domain,right_domain,remaining);
            if !right_atomic&&probe.checked_active_source_sort(right_domain,context,remaining).is_none(){
                if GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.get()){return None;}
                let _formation=GeneralDomainFormationOwner::enter();
                probe.shared_strict_source_sort(right_domain,context,remaining)?;
            }
            // Retain all original/current USED body quarantine premises even
            // though no substitution of the left body is now necessary.
            if !self.owned_pi_reclosure_capture_valid(left_body,remaining){return None;}
            let right=self.reopen_fixed_pi_body_owned(right_body,right_binder,right_owner,left_owner,remaining)?;
            #[cfg(feature="diagnostics")] if std::env::var_os("TRACE_FIXED_ORIGINAL_REUSED").is_some(){eprintln!("FIXED_ORIGINAL_REUSED gamma={} owner={} right_owner={} remaining={remaining}",context.len(),left_owner.id(),right_owner.id());}
            return Some((left_body.clone(),right));
        }
        let atomic=self.checked_closed_atomic_domain_pair(left_domain,right_domain,remaining);
        let bound=!atomic&&GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.get())&&self.checked_active_source_sort(left_domain,context,remaining).is_some()&&self.checked_active_source_sort(right_domain,context,remaining).is_some();
        let formed=atomic||bound;
        let _owner=if formed{None}else{
            if GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.get()){return None;}
            Some(GeneralDomainFormationOwner::enter())
        };
        let probe=self.strict_certificate_probe();
        if !formed{probe.shared_strict_source_sort(left_domain,context,remaining)?;probe.shared_strict_source_sort(right_domain,context,remaining)?;}
        let domain=TypeValue::Term(left_domain.clone());
        let target=left_owner.parent_frame()?.extend_free_paid(free,remaining)?;if !take_step(remaining){return None;}
        probe.retain_shared_checked_binding(&target,domain,proven.completed_body_context().clone());
        let left=self.reopen_fixed_pi_body_owned(left_body,left_binder,left_owner,&target,remaining);
        let left=left?;
        let right=self.reopen_fixed_pi_body_owned(right_body,right_binder,right_owner,&target,remaining);
        Some((left,right?))
    }
    pub(crate) fn checked_atomic_joint_opening(
        &self,left_domain:&Closure,right_domain:&Closure,left_body:&Closure,right_body:&Closure,
        context:&[TypeValue],free:FreeId,remaining:&mut usize,
    )->Option<(Closure,Closure)> {
        if usize::try_from(free.0).ok()!=Some(context.len()){return None;}
        if !self.checked_closed_atomic_domain_pair(left_domain,right_domain,remaining){return None;}
        self.checked_formed_joint_opening(left_domain,left_body,right_body,context,free,remaining)
    }
    fn checked_formed_joint_opening(&self,left_domain:&Closure,left_body:&Closure,right_body:&Closure,context:&[TypeValue],free:FreeId,remaining:&mut usize)->Option<(Closure,Closure)> {
        let cost=context.len().checked_add(1)?;
        if *remaining<cost{return None;}*remaining-=cost;
        let domain=TypeValue::Term(left_domain.clone());
        let mut extended=context.to_vec();extended.push(domain);
        self.checked_formed_joint_opening_with_prefix(left_domain,left_body,right_body,context,free,&Rc::new(extended),remaining)
    }
    // This private continuation consumes the exact immutable body Gamma built
    // for these domains before their completed comparison. Formation and domain
    // equality are still mandatory; only a second allocation/copy is avoided.
    // The original opening path constructs its own prefix above.
    fn checked_formed_joint_opening_with_prefix(&self,left_domain:&Closure,left_body:&Closure,right_body:&Closure,context:&[TypeValue],free:FreeId,extended:&Rc<Vec<TypeValue>>,remaining:&mut usize)->Option<(Closure,Closure)> {
        if usize::try_from(free.0).ok()!=Some(context.len()){return None;}
        if !take_step(remaining)||!self.has_source_opening_proof(left_body,free){return None;}
        if !take_step(remaining)||!self.has_source_opening_proof(right_body,free){return None;}
        let domain=TypeValue::Term(left_domain.clone());
        let original=left_body.env.extend_free_paid(free,remaining)?;
        if !take_step(remaining){return None;}
        self.retain_shared_checked_binding(&original,domain.clone(),extended.clone());
        let wrapper=right_body.env.extend_neutral_paid(Neutral{head:NeutralHead::Free(free,Some(original.clone())),spine:vec![]},remaining)?;
        if !take_step(remaining){return None;}
        self.retain_shared_checked_binding(&wrapper,domain.clone(),extended.clone());
        if !matches!(self.checked_binding_lineage.borrow().get(&original.id()),Some(Some(w)) if w.domain==domain && w.protected_prefix==*extended){return None;}
        if !matches!(self.checked_binding_lineage.borrow().get(&wrapper.id()),Some(Some(w)) if w.domain==domain && w.protected_prefix==*extended){return None;}
        Some((left_body.sibling(left_body.expr,original),right_body.sibling(right_body.expr,wrapper)))
    }

    /// Check every USED capture and its original declared domain for revocation.
    /// Closed source syntax does not depend on unused ambient cells.
    pub(crate) fn source_used_capture_authority_available(
        &self, source: &Closure, remaining: &mut usize,
    ) -> bool {
        let mut pending = vec![TypeValue::Term(source.clone())];
        let mut seen = std::collections::HashSet::new();
        while let Some(ty) = pending.pop() {
            if !take_step(remaining) { return false; }
            match ty {
                TypeValue::Sort(_) => {},
                TypeValue::Pi { domain, body, .. } => {
                    pending.push(*domain); pending.push(*body);
                },
                TypeValue::Term(term) => {
                    if self.checked_binding_lineage.borrow().get(&term.env.id())
                        .is_some_and(Option::is_none) { return false; }
                    if !seen.insert((term.expr, term.env.id(), term.levels.identity())) {
                        continue;
                    }
                    let Some(support) = self.complete_source_support(term.expr, remaining)
                        else { return false; };
                    for index in support {
                        // The immutable frame has binary ancestor links. Pay
                        // the existing exact owner lookup and its physical hops.
                        let Some(frame) = self.source_capture_owner(&term.env,index,remaining)
                            else { return false; };
                        let witness = self.checked_binding_lineage.borrow().get(&frame.id()).cloned();
                        match witness {
                            Some(None) => return false,
                            Some(Some(w)) => pending.push(w.domain),
                            None => {},
                        }
                        let Some(binding) = frame.lookup(0) else { return false; };
                        match binding {
                            EnvBinding::Closure(value) => pending.push(TypeValue::Term(value)),
                            EnvBinding::Free(_) | EnvBinding::NatLit(_) => {},
                            EnvBinding::Neutral(neutral) => {
                                let mut neutrals = vec![neutral];
                                while let Some(neutral) = neutrals.pop() {
                                    if !take_step(remaining) { return false; }
                                    pending.extend(neutral.spine.into_iter().map(TypeValue::Term));
                                    match neutral.head {
                                        NeutralHead::Free(_, None) => return false,
                                        NeutralHead::Free(free, Some(owner)) => {
                                            if !matches!(owner.lookup_binding_ref(0), Some(EnvBinding::Free(actual)) if *actual == free) {
                                                return false;
                                            }
                                            match self.checked_binding_lineage.borrow().get(&owner.id()).cloned() {
                                                Some(None) => return false,
                                                Some(Some(w)) => pending.push(w.domain),
                                                None => {},
                                            }
                                        },
                                        NeutralHead::Projection { structure, .. } => neutrals.push(*structure),
                                        NeutralHead::Const { .. } => {},
                                    }
                                }
                            },
                        }
                    }
                },
            }
        }
        true
    }

    fn collect_substitution_type_authority(&self,ty:&TypeValue,remaining:&mut usize,observations:&mut HashMap<u64,typed_lineage::Observation>)->bool {
        let mut pending=vec![ty];
        while let Some(ty)=pending.pop(){
            if !take_step(remaining){return false;}
            match ty {
                TypeValue::Sort(_)=>{},
                TypeValue::Term(source)=>if !self.collect_substitution_authority(source,remaining,observations){return false;},
                TypeValue::Pi{domain,body,binder_owner,..}=>{
                    let Some(owner)=binder_owner else{return false;};
                    let state=self.checked_binding_lineage.borrow().get(&owner.id()).cloned();
                    if state.as_ref().is_some_and(Option::is_none){return false;}
                    observations.insert(owner.id(),(owner.clone(),state));pending.push(domain);pending.push(body);
                }
            }
        }
        true
    }

    fn collect_substitution_authority(
        &self, source: &Closure, remaining: &mut usize, observations:&mut HashMap<u64,typed_lineage::Observation>,
    ) -> bool {
        let mut pending = vec![TypeValue::Term(source.clone())];
        let mut seen = std::collections::HashSet::new();
        while let Some(ty) = pending.pop() {
            if !take_step(remaining) { return false; }
            match ty {
                TypeValue::Sort(_) => {},
                TypeValue::Pi { domain, body, binder_owner, .. } => {
                    if let Some(owner)=binder_owner {let state=self.checked_binding_lineage.borrow().get(&owner.id()).cloned();observations.insert(owner.id(),(owner,state.clone()));if state.is_some_and(|v|v.is_none()){return false;}}
                    pending.push(*domain); pending.push(*body);
                },
                TypeValue::Term(term) => {
                    let state=self.checked_binding_lineage.borrow().get(&term.env.id()).cloned();
                    observations.insert(term.env.id(),(term.env.clone(),state.clone()));
                    if state.is_some_and(|v|v.is_none()) { return false; }
                    if !seen.insert((term.expr, term.env.id(), term.levels.identity())) {
                        continue;
                    }
                    let Some(support) = self.complete_source_support(term.expr, remaining)
                        else { return false; };
                    for index in support {
                        // The immutable frame has binary ancestor links. Pay
                        // the existing exact owner lookup and its physical hops.
                        let Some(frame) = self.source_capture_owner(&term.env,index,remaining)
                            else { return false; };
                        let witness = self.checked_binding_lineage.borrow().get(&frame.id()).cloned();
                        observations.insert(frame.id(),(frame.clone(),witness.clone()));
                        match witness {
                            Some(None) => return false,
                            Some(Some(w)) => pending.push(w.domain),
                            None => {},
                        }
                        let Some(binding) = frame.lookup(0) else { return false; };
                        match binding {
                            EnvBinding::Closure(value) => pending.push(TypeValue::Term(value)),
                            EnvBinding::Free(_) | EnvBinding::NatLit(_) => {},
                            EnvBinding::Neutral(neutral) => {
                                let mut neutrals = vec![neutral];
                                while let Some(neutral) = neutrals.pop() {
                                    if !take_step(remaining) { return false; }
                                    pending.extend(neutral.spine.into_iter().map(TypeValue::Term));
                                    match neutral.head {
                                        NeutralHead::Free(_, None) => return false,
                                        NeutralHead::Free(free, Some(owner)) => {
                                            if !matches!(owner.lookup_binding_ref(0), Some(EnvBinding::Free(actual)) if *actual == free) {
                                                return false;
                                            }
                                            let state=self.checked_binding_lineage.borrow().get(&owner.id()).cloned();
                                            observations.insert(owner.id(),(owner.clone(),state.clone()));
                                            match state {
                                                Some(None) => return false,
                                                Some(Some(w)) => pending.push(w.domain),
                                                None => {},
                                            }
                                        },
                                        NeutralHead::Projection { structure, .. } => neutrals.push(*structure),
                                        NeutralHead::Const { .. } => {},
                                    }
                                }
                            },
                        }
                    }
                },
            }
        }
        true
    }

    /// Form the actual inferred type, rather than infer its type a second
    /// time and confuse a proof with a type. An inferred Pi retains its
    /// original checked introduction; the owner tag alone supplies no scope.
    fn owned_inferred_type_formation_sort(&self,ty:&TypeValue,context:&[TypeValue],remaining:&mut usize,depth:usize)->Option<LevelTerm> {
        if depth>=48 || !take_step(remaining){return None;}
        match ty {
            TypeValue::Term(source)=>{
                if !self.source_used_capture_authority_available(source,remaining){return None;}
                self.shared_strict_source_sort(source,context,remaining)
            },
            TypeValue::Sort(level)=>{
                fn copy(level:&LevelTerm,remaining:&mut usize,depth:usize)->Option<LevelTerm> {
                    if depth>=128 || !take_step(remaining){return None;}
                    Some(match level {
                        LevelTerm::Zero=>LevelTerm::Zero,
                        LevelTerm::Succ(a)=>succ(copy(a,remaining,depth+1)?),
                        LevelTerm::Max(a,b)=>LevelTerm::Max(Box::new(copy(a,remaining,depth+1)?),Box::new(copy(b,remaining,depth+1)?)),
                        LevelTerm::IMax(a,b)=>LevelTerm::IMax(Box::new(copy(a,remaining,depth+1)?),Box::new(copy(b,remaining,depth+1)?)),
                        LevelTerm::Param(name)=>{if *remaining<name.len(){return None;}*remaining-=name.len();LevelTerm::Param(name.clone())},
                    })
                }
                Some(succ(copy(level,remaining,0)?))
            },
            TypeValue::Pi{domain,body,binder,binder_owner}=>{
                let owner=binder_owner.as_ref()?;
                if fresh_local(context.len())!=Some(*binder) || !take_step(remaining)
                    || !matches!(owner.lookup_binding_ref(0),Some(EnvBinding::Free(actual)) if actual==binder){return None;}
                if !take_step(remaining){return None;}
                let witness=self.checked_binding_lineage.borrow().get(&owner.id()).cloned().flatten()?;
                if witness.domain!=**domain{return None;}
                let domain_sort=self.owned_inferred_type_formation_sort(domain,context,remaining,depth+1)?;
                let cost=context.len().checked_add(1)?;if *remaining<cost{return None;}*remaining-=cost;
                let mut extended=context.to_vec();extended.push((**domain).clone());
                if witness.protected_prefix.as_slice()!=extended.as_slice(){return None;}
                // Every Term in this recursive formation uses its own source
                // environment/levels and strict actual Gamma lookup, including
                // original and current captured-wrapper quarantine checks.
                let body_sort=self.owned_inferred_type_formation_sort(body,&extended,remaining,depth+1)?;
                if !take_step(remaining){return None;}
                Some(imax(domain_sort,body_sort))
            },
        }
    }

    /// Original source typing, not a conversion-wide numeric kind hint, is
    /// the authority for proof irrelevance. Each side must form a proof TYPE.
    pub(crate) fn checked_owned_proof_source_pair(
        &self, left: &Closure, right: &Closure, context: &[TypeValue],
        remaining: &mut usize,
    ) -> bool {
        // Pi/Sort expressions are type syntax, not proof subjects. This
        // optional candidate veto does not certify conversion or formation.
        if matches!(self.expressions.get(left.expr),Some(Expr::Pi{..}|Expr::Sort(_)))
            || matches!(self.expressions.get(right.expr),Some(Expr::Pi{..}|Expr::Sort(_))) {
            return false;
        }
        if OWNED_PROOF_SOURCE_ACTIVE.with(|flag| flag.get()) || *remaining < 256 {
            return false;
        }
        // An actual binding whose checked TYPE is a literal Sort is itself
        // a type expression, never a proof subject. This paid source witness
        // keeps original/current ownership, Gamma and quarantine checks.
        for source in [left,right] {
            if matches!(self.expressions.get(source.expr),Some(Expr::BVar(_)))
                && self.checked_bound_literal_sort(source,context,remaining).is_some() {
                return false;
            }
        }
        if *remaining<256{return false;}
        *remaining -= 256;
        let _owner = OwnedProofSourceOwner::enter();
        let probe = self.strict_certificate_probe();
        let mut work = 256;
        if !self.source_used_capture_authority_available(left, &mut work)
            || !self.source_used_capture_authority_available(right, &mut work) {
            return false;
        }
        let Some(left_type) = probe.infer_exact_closure_in_context(left, context, &mut work, 0)
            else { return false; };
        let Some(right_type) = probe.infer_exact_closure_in_context(right, context, &mut work, 0)
            else { return false; };
        for ty in [&left_type, &right_type] {
            match ty {
                TypeValue::Term(source) => {
                    if !self.source_used_capture_authority_available(source, &mut work) { return false; }
                    let Some(formed) = probe.infer_exact_closure_in_context(source, context, &mut work, 0)
                        else { return false; };
                    let level = match formed {
                        TypeValue::Sort(level) => Some(level),
                        other => {
                            let allowance = work.min(32); work -= allowance;
                            probe.sort_level(Judgment::proven(other, "owned-proof-type-formation"), allowance)
                                .proven_value().cloned()
                        },
                    };
                    let Some(level)=level else{return false;};
                    if !crate::level::level_equal_with_remaining(level,LevelTerm::Zero,&mut work).is_proven(){return false;}
                },
                TypeValue::Pi { .. } => {
                    let Some(level) = probe.owned_inferred_type_formation_sort(ty, context, &mut work, 0)
                        else { return false; };
                    if !crate::level::level_equal_with_remaining(level, LevelTerm::Zero, &mut work).is_proven() {
                        return false;
                    }
                },
                TypeValue::Sort(_) => return false,
            }
        }
        let result=crate::convert::convert_with_policy_in_context(&probe, &left_type, &right_type, work,
            crate::convert::DeltaPolicy::GuardedSemanticFallback, context.len(), context);
        result.is_proven()
    }

    fn paid_strict_source_sort(&self,source:&Closure,context:&[TypeValue],remaining:&mut usize)->Option<LevelTerm> {
        if *remaining<160{return None;}*remaining-=160;
        let mut fuel=128;
        let ty=self.infer_exact_closure_in_context(source,context,&mut fuel,0)?;
        self.sort_level(Judgment::proven(ty,"original-source-formation"),32).proven_value().cloned()
    }

    pub(crate) fn certify_conversion_pi_opening(&self,source:&Closure,domain:&Closure,opened:&Closure,context:&[TypeValue],remaining:&mut usize)->bool {
        if context.len()>128 || context.iter().any(|ty|!matches!(ty,TypeValue::Term(_))){return false;}
        let literal=matches!(self.expressions.get(source.expr),Some(Expr::Pi{domain:declared,body}) if domain.expr==*declared && domain.env.id()==source.env.id() && domain.levels==source.levels && opened.expr==*body && opened.levels==source.levels && opened.env.parent_id()==Some(source.env.id()));
        if !literal {
            fn actual_pi_matches(value:&Value,domain:&Closure,opened:&Closure)->bool {
                matches!(value,Value::Pi{domain:actual_domain,body} if actual_domain==domain && body.expr==opened.expr && body.levels==opened.levels && opened.env.parent_id()==Some(body.env.id()))
            }
            if *remaining<512{return false;}*remaining-=512;
            let machine=self.machine();let exposed=machine.expose(source.clone(),Transparency::Reducible,512);
            #[cfg(feature="diagnostics")]
            if source.expr==ExprId(235){Self::proof_transport_trace("source-pi-exposure",(source,domain,opened,&exposed,*remaining));}
            if !exposed.proven_value().is_some_and(|v|actual_pi_matches(v,domain,opened)) {
                if *remaining<1024{return false;}*remaining-=1024;
                let exposed=machine.expose(source.clone(),Transparency::Full,1024);
                if !exposed.proven_value().is_some_and(|v|actual_pi_matches(v,domain,opened)){return false;}
            }
        }
        let Some(free)=fresh_local(context.len())else{return false;};
        if !matches!(opened.env.lookup_with_node_id(0),Some((id,EnvBinding::Free(actual))) if id==opened.env.id() && actual==free){return false;}
        let probe=self.strict_certificate_probe();
        // Proof-domain transport is the capability needed by this converter.
        // Independently reject a data domain before the full enclosing Pi
        // formation trial; ordinary lambda introductions retain data typing.
        let domain_sort=probe.shared_strict_source_sort(domain,context,remaining);
        if domain_sort!=Some(LevelTerm::Zero){return false;}
        let source_sort=probe.shared_strict_source_sort(source,context,remaining);
        if source_sort.is_none(){return false;}
        let cost=context.len()+4;if *remaining<cost{return false;}*remaining-=cost;
        let domain=TypeValue::Term(domain.clone());let mut extended=context.to_vec();extended.push(domain.clone());
        if self.checked_binding_lineage.borrow().get(&opened.env.id()).is_some_and(Option::is_none){return false;}
        self.retain_checked_binding(&opened.env,domain.clone(),&extended);
        if !matches!(self.checked_binding_lineage.borrow().get(&opened.env.id()),Some(Some(w)) if w.domain==domain && w.protected_prefix.as_slice()==extended){return false;}
        let mut openings=self.source_pi_openings.borrow_mut();
        if openings.len()<8192 {
            openings.insert(opened.env.id(),SourcePiOpening{source:source.clone(),opened:opened.clone(),context:context.to_vec(),domain});
            #[cfg(feature="diagnostics")]
            if source.expr==ExprId(235){Self::proof_transport_trace("opening-certified",(opened.env.id(),context.len(),*remaining));}
            true
        }else{false}
    }

    fn actual_binder_nodes(&self,body:&TypeValue,free:FreeId,remaining:&mut usize)->Vec<EnvFrame>{
        let TypeValue::Term(body)=body else{return vec![]};
        let mut pending=vec![body.clone()];let mut seen=std::collections::HashSet::new();let mut result=Vec::new();
        while let Some(source)=pending.pop(){
            if !take_step(remaining){return vec![];}
            if !seen.insert((source.expr,source.env.id(),source.levels.identity())){continue;}
            let Some(support)=self.complete_source_support(source.expr,remaining)else{return vec![]};
            for index in support {
                let Some(cost)=usize::try_from(index).ok().and_then(|i|i.checked_add(1))else{return vec![]};
                if *remaining<cost{return vec![];}*remaining-=cost;
                let Some(binding)=source.env.lookup_binding_ref(index)else{return vec![]};
                match binding {
                    EnvBinding::Free(actual) if *actual==free=>{if result.len()<8 {result.push(source.env.clone());}else{return vec![];}}
                    EnvBinding::Closure(c)=>pending.push(c.clone()),
                    EnvBinding::Neutral(Neutral{head:NeutralHead::Free(actual, _),spine})if *actual==free&&spine.is_empty()=>{if result.len()<8{result.push(source.env.clone());}else{return vec![];}}
                    _=>{}
                }
            }
        }result
    }

    pub(crate) fn transport_conversion_proof_binder(&self,left:&TypeValue,right:&TypeValue,old:&TypeValue,new:&TypeValue,context:&[TypeValue],remaining:&mut usize)->bool {
        let (TypeValue::Term(left),TypeValue::Term(old_source),TypeValue::Term(new_source))=(left,old,new)else{return false;};
        let opening=self.source_pi_openings.borrow().get(&left.env.id()).cloned();
        #[cfg(feature="diagnostics")]
        if matches!(old,TypeValue::Term(c)if c.expr==ExprId(68300)){Self::proof_transport_trace("transport-opening",(left.env.id(),opening.is_some(),old,new,context.len(),*remaining));}
        let Some(opening)=opening else{return false;};
        if opening.context!=context || opening.domain!=*new || opening.opened!=*left{return false;}
        let mut target=context.to_vec();target.push(new.clone());
        let opener_witness=self.checked_binding_lineage.borrow().get(&left.env.id()).cloned().flatten();
        if !matches!(&opener_witness,Some(w) if w.domain==*new && w.protected_prefix.as_slice()==target){return false;}
        let probe=self.strict_certificate_probe();
        if probe.paid_strict_source_sort(old_source,context,remaining)!=Some(LevelTerm::Zero)
            || probe.paid_strict_source_sort(new_source,context,remaining)!=Some(LevelTerm::Zero){return false;}
        if old!=new {
            if *remaining<1024{return false;}*remaining-=1024;
            let relation=crate::convert::convert_with_policy_in_context(&probe,old,new,1024,crate::convert::DeltaPolicy::GuardedSemanticFallback,context.len(),context);
            #[cfg(feature="diagnostics")]
            if old_source.expr==ExprId(68300){Self::proof_transport_trace("domain-relation",(&relation,*remaining));}
            if !relation.is_proven(){return false;}
        }
        let Some(free)=fresh_local(context.len())else{return false;};
        if *remaining<512{return false;}*remaining-=512;let mut discovery=512;
        let right_nodes=self.actual_binder_nodes(right,free,&mut discovery);
        #[cfg(feature="diagnostics")]
        if old_source.expr==ExprId(68300){Self::proof_transport_trace("right-node-discovery",(right_nodes.len(),discovery,*remaining));}
        let mut records=Vec::new();
        let mut old_scope=context.to_vec();old_scope.push(old.clone());
        for frame in right_nodes {
            for index in 0..=context.len() {
                let cost=index+1;if *remaining<cost{return false;}*remaining-=cost;
                if !matches!(frame.lookup_binding_ref(index as u64),Some(EnvBinding::Free(actual))if *actual==free){continue;}
                let Some((node,_))=frame.lookup_with_node_id(index as u64)else{continue;};
                let ledger=self.checked_binding_lineage.borrow();let Some(Some(w))=ledger.get(&node)else{continue;};
                if w.domain==*old && w.protected_prefix.as_slice()==old_scope {
                    if *remaining<old_scope.len()+2{return false;}*remaining-=old_scope.len()+2;
                    records.push((frame.clone(),node,w.clone()));
                }
            }
        }
        let cost=records.len().saturating_mul(target.len()+old_scope.len()+6);if *remaining<cost{return false;}*remaining-=cost;
        #[cfg(feature="diagnostics")]
        if old_source.expr==ExprId(68300){Self::proof_transport_trace("transport-records",(records.len(),*remaining));}
        let mut transports=self.proof_binder_transports.borrow_mut();
        for(frame,node,original)in records.into_iter().take(9) {
            if transports.len()>=8192&&!transports.contains_key(&node){continue;}
            let list=transports.entry(node).or_default();if list.len()<8{
                list.push(ProofBinderTransport{frame,original,target:target.clone(),output:old.clone(),opening:opening.clone()});
                if let Some(TypeValue::Term(last))=target.last(){self.proof_transport_context_keys.borrow_mut().insert((target.len(),last.expr,last.env.id(),last.levels.identity()));}
            }
        }true
    }

    fn transported_bound_type(&self,node:u64,original:&CheckedBinderWitness,context:&[TypeValue])->Option<TypeValue>{
        for record in self.proof_binder_transports.borrow().get(&node)? {
            if &record.original!=original || !context.starts_with(&record.target){continue;}
            let _owner=&record.frame;let opening=&record.opening;
            if !matches!(self.checked_binding_lineage.borrow().get(&opening.opened.env.id()),Some(Some(w)) if w.domain==opening.domain && w.protected_prefix.len()==opening.context.len()+1 && w.protected_prefix[..opening.context.len()]==opening.context[..] && w.protected_prefix.last()==Some(&opening.domain)){continue;}
            let _source_authority=&opening.source;return Some(record.output.clone());
        }None
    }

    pub(crate) fn checked_transport_proof_pair(&self,left:&Closure,right:&Closure,context:&[TypeValue],remaining:&mut usize)->bool {
        fn anchored(checker:&TypeChecker<'_>,term:&Closure,context:&[TypeValue],remaining:&mut usize)->bool {
            let Some(index)=context.len().checked_sub(1)else{return false;};let Some(free)=fresh_local(index)else{return false;};
            if *remaining<512{return false;}*remaining-=512;let mut work=512;
            let nodes=checker.actual_binder_nodes(&TypeValue::Term(term.clone()),free,&mut work);
            for frame in nodes {
                for slot in 0..=context.len(){
                    if !take_step(remaining){return false;}
                    if !matches!(frame.lookup_binding_ref(slot as u64),Some(EnvBinding::Free(actual))if *actual==free){continue;}
                    let Some((node,_))=frame.lookup_with_node_id(slot as u64)else{continue;};
                    let ledger=checker.checked_binding_lineage.borrow();let Some(Some(w))=ledger.get(&node)else{continue;};
                    if checker.transported_bound_type(node,w,context).is_some(){return true;}
                }
            }false
        }
        if TRANSPORT_PROOF_ACTIVE.with(|flag|flag.get()){return false;}
        let Some(TypeValue::Term(last))=context.last()else{return false;};
        if !self.proof_transport_context_keys.borrow().contains(&(context.len(),last.expr,last.env.id(),last.levels.identity())){return false;}
        // The scalar index is a cost gate only. Retained records pin its level
        // identity; actual node, original ledger and FULL target Gamma are
        // checked again before any proof judgment can be reused.
        if !take_step(remaining){return false;}
        let anchor=anchored(self,left,context,remaining)||anchored(self,right,context,remaining);
        #[cfg(feature="diagnostics")]
        if left.expr==ExprId(66500)||right.expr==ExprId(66500){Self::proof_transport_trace("proof-anchor",(anchor,left,right,context.len(),*remaining));}
        if !anchor{return false;}
        if *remaining<2880{return false;}*remaining-=2880;
        let _owner=TransportProofOwner::enter();let probe=self.strict_certificate_probe();
        #[cfg(feature="diagnostics")]
        let _left_failure=CaptureSourceFailureScope::enter();
        let mut a=1536;let left_ty=probe.infer_exact_closure_in_context(left,context,&mut a,0);
        #[cfg(feature="diagnostics")]
        if left.expr==ExprId(66500)||right.expr==ExprId(66500){Self::proof_transport_trace("proof-left-type",(&left_ty,a,CaptureSourceFailureScope::first()));}
        let Some(left_ty)=left_ty else{return false;};
        #[cfg(feature="diagnostics")]
        let _right_failure=CaptureSourceFailureScope::enter();
        let mut b=512;let right_ty=probe.infer_exact_closure_in_context(right,context,&mut b,0);
        #[cfg(feature="diagnostics")]
        if left.expr==ExprId(66500)||right.expr==ExprId(66500){Self::proof_transport_trace("proof-right-type",(&right_ty,b,CaptureSourceFailureScope::first()));}
        let Some(right_ty)=right_ty else{return false;};
        for ty in [&left_ty,&right_ty] {
            let TypeValue::Term(ty)=ty else{return false;};let mut form=160;
            if probe.paid_strict_source_sort(ty,context,&mut form)!=Some(LevelTerm::Zero){return false;}
        }
        crate::convert::convert_with_policy_in_context(&probe,&left_ty,&right_ty,512,crate::convert::DeltaPolicy::GuardedSemanticFallback,context.len(),context).is_proven()
    }

    fn checked_type_of_bound_source(
        &self,
        frame:&EnvFrame,
        index:u64,
        context:&[TypeValue],
    ) -> Option<TypeValue> {
        if std::env::var_os("NUCLEUS_EXPERIMENTAL_TYPED_LINEAGE").is_none()
            && !self.strict_origin_probe
        {
            return None;
        }
        let (wrapper_id,binding)=frame.lookup_with_node_id(index)?;
        let node_id=match &binding {
            EnvBinding::Neutral(Neutral{head:NeutralHead::Free(free,Some(owner)),spine}) if spine.is_empty()=>{
                if !matches!(owner.lookup_binding_ref(0),Some(EnvBinding::Free(actual)) if actual==free){return None;}
                owner.id()
            },
            EnvBinding::Neutral(Neutral{head:NeutralHead::Free(_,None),..})=>return None,
            _=>wrapper_id,
        };
        let proof=self.checked_binding_lineage.borrow()
            .get(&node_id)?.as_ref()?.clone();
        if wrapper_id!=node_id {
            let ledger=self.checked_binding_lineage.borrow();
            match ledger.get(&wrapper_id) {
                Some(None)=>return None,
                Some(Some(w)) if w.domain!=proof.domain || !context.starts_with(&w.protected_prefix)=>return None,
                _=>{},
            }
        }
        if let Some(transported)=self.transported_bound_type(node_id,&proof,context){return Some(transported);}
        if !context.starts_with(&proof.protected_prefix) {return None;}
        #[cfg(feature="diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_TYPED_LINEAGE").is_some(){
            use std::sync::atomic::{AtomicUsize,Ordering};
            static RECORDED:AtomicUsize=AtomicUsize::new(0);
            if RECORDED.fetch_add(1,Ordering::Relaxed)<64 {
                eprintln!(
                    "NUCLEUS_TYPED_LINEAGE_REUSE:frame={}:node={node_id}:index={index}:context={}:protected={}:type={:?}",
                    frame.id(),context.len(),proof.protected_prefix.len(),proof.domain
                );
            }
        }
        Some(proof.domain)
    }

    pub fn infer(&self, expression: ExprId, budget: usize) -> Judgment<TypeValue> {
        self.reset_lambda_trials(budget);
        let mut remaining = budget;
        self.infer_in(
            expression,
            &[],
            &EnvFrame::empty(),
            &mut remaining,
            &mut HashMap::new(),
        )
    }

    pub fn check(&self, expression: ExprId, expected: &TypeValue, budget: usize) -> Judgment<()> {
        self.reset_lambda_trials(budget);
        let mut remaining = budget;
        self.check_in(
            expression,
            expected,
            &[],
            &EnvFrame::empty(),
            &mut remaining,
            self.delta_policy == crate::convert::DeltaPolicy::GuardedSemanticFallback,
            &mut HashMap::new(),
        )
    }

    /// Check against an exact closed source type previously proved formed by
    /// `is_type` or `is_proposition` on this checker. A Pi shape is no warrant.
    pub fn check_formed(&self, expression: ExprId, expected: &TypeValue, budget: usize) -> Judgment<()> {
        self.reset_lambda_trials(budget);
        let TypeValue::Term(expected_source) = expected else {
            return Judgment::unknown("formed-expected-source-missing");
        };
        if !self.formed_expected.borrow().contains(expected_source) {
            return Judgment::unknown("expected-type-formation-warrant-missing");
        }
        let mut remaining = budget;
        let result = self.check_with_formation(expression, expected, &[], &EnvFrame::empty(),
            &mut remaining, self.delta_policy == crate::convert::DeltaPolicy::GuardedSemanticFallback,
            &mut HashMap::new(), true);
        #[cfg(feature="diagnostics")]
        if std::env::var_os("NUCLEUS_POST_TRANSPORT_ARGUMENT").is_some(){
            if let Some((lhs,rhs,ctx))=TRANSPORT_ARGUMENT_POST.with(|slot|slot.borrow_mut().take()) {
                eprintln!("TRANSPORT_ARGUMENT_ORIGINAL_VERDICT:{result:?}");
                for fuel in [512,1024,2048,4096,8192] {
                    let probe=self.strict_certificate_probe();let _owner=TransportProofOwner::enter();
                    let equality=crate::convert::convert_with_policy_in_context(&probe,&lhs,&rhs,fuel,crate::convert::DeltaPolicy::GuardedSemanticFallback,ctx.len(),&ctx);
                    let norm=|ty:&TypeValue|match ty{TypeValue::Term(c)=>Some(probe.machine().expose_for_conversion(c.clone(),Transparency::Full,fuel)),_=>None};
                    eprintln!("TRANSPORT_ARGUMENT_POST:fuel={fuel}:equality={equality:?}:lhs={:?}:rhs={:?}",norm(&lhs),norm(&rhs));
                }
            }
        }

        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_LAMBDA_TRIAL_WORK").is_some() {
            let trials = self.lambda_trials.borrow();
            eprintln!("lambda-trial-work expression={expression:?} budget={budget} remaining={remaining} started={} proven={} declined={} spent={} nested_direct={} skipped={} quota={}",
                trials.started, trials.proven, trials.declined, trials.spent,
                trials.nested_direct, trials.skipped, trials.quota);
        }
        result
    }

    fn retain_formed_expected(&self, expression: ExprId) {
        let mut formed = self.formed_expected.borrow_mut();
        if formed.len() < 128 {
            formed.insert(self.closure(expression, EnvFrame::empty()));
        }
    }

    pub fn is_type(&self, expression: ExprId, budget: usize) -> Judgment<()> {
        #[cfg(feature = "diagnostics")]
        crate::diagnostics::type_judgment();
        let result = match self.infer(expression, budget) {
            Judgment::Proven {
                value: TypeValue::Sort(_),
                ..
            } => Judgment::proven((), "type-has-sort"),
            Judgment::Proven {
                value: TypeValue::Term(closure),
                ..
            } => match self
                .machine()
                .expose(closure, Transparency::Reducible, budget)
            {
                Judgment::Proven {
                    value: Value::Sort(_),
                    ..
                } => Judgment::proven((), "type-reduces-to-sort"),
                Judgment::Proven { .. } => Judgment::refuted("term-is-not-a-type"),
                Judgment::Refuted { obstruction } => Judgment::Refuted { obstruction },
                Judgment::Unknown { residual } => Judgment::Unknown { residual },
            },
            Judgment::Proven {
                value: TypeValue::Pi { .. },
                ..
            } => Judgment::refuted("term-is-not-a-type"),
            Judgment::Refuted { obstruction } => Judgment::Refuted { obstruction },
            Judgment::Unknown { residual } => Judgment::Unknown { residual },
        };
        if result.is_proven() { self.retain_formed_expected(expression); }
        result
    }

    /// Establish that `expression` itself inhabits `Prop` (`Sort 0`).
    ///
    /// This remains three-valued: unresolved universe equality or reduction
    /// is not a refutation.
    pub fn is_proposition(&self, expression: ExprId, budget: usize) -> Judgment<()> {
        self.reset_lambda_trials(budget);
        let mut remaining = budget;
        let result = self.check_in(
            expression,
            &TypeValue::Sort(LevelTerm::Zero),
            &[],
            &EnvFrame::empty(),
            &mut remaining,
            false,
            &mut HashMap::new(),
        );
        if result.is_proven() { self.retain_formed_expected(expression); }
        result
    }

    /// Independently reconstruct the type of a two-argument relation in its
    /// captured lexical environment. A raw Pi telescope/codomain alone is
    /// NOT a proposition certificate: both arguments must be checked.
    ///
    /// This deliberately does not trust equivalence of expression IDs or
    /// equality of evaluation frames. Every bvar follows its actual closure
    /// binding, and every application checks its argument against the
    /// instantiated dependent domain. Unsupported cases stay UNKNOWN.
    pub fn certify_applied_proposition_in_context(
        &self,
        expression: &Closure,
        context: &[TypeValue],
        budget: usize,
    ) -> Judgment<()> {
        let mut remaining = budget.min(2048);
        let exposed = self.machine().expose(
            expression.clone(), Transparency::Reducible, remaining.min(1024),
        );
        let is_relation = matches!(
            exposed.proven_value(),
            Some(Value::Neutral(Neutral {
                head: NeutralHead::Const { .. },
                spine,
            })) if spine.len() == 2
        );
        if !is_relation {
            return Judgment::unknown("typed-telescope-not-two-argument-relation");
        }
        let Some(inferred) =
            self.infer_exact_closure_in_context(expression, context, &mut remaining, 0)
        else {
            return Judgment::unknown("typed-telescope-argument-obligation");
        };
        match self.sort_level(
            Judgment::proven(inferred, "typed-telescope-argument-checks"),
            remaining,
        ) {
            Judgment::Proven { value: LevelTerm::Zero, .. } => {
                Judgment::proven((), "checked-dependent-relation-proposition")
            }
            Judgment::Proven { .. } => {
                Judgment::unknown("typed-telescope-codomain-not-certified-Prop")
            }
            Judgment::Refuted { .. } | Judgment::Unknown { .. } => {
                Judgment::unknown("typed-telescope-codomain-obligation")
            }
        }
    }

    #[cfg(feature = "diagnostics")]
    fn record_capture_source_failure(&self, term: &Closure, context: &[TypeValue], remaining: usize, depth: usize, reason: &str) {
        CAPTURE_SOURCE_FAILURE.with(|failure| {
            let mut failure = failure.borrow_mut();
            if let Some(first @ None) = failure.as_mut() {
                *first = Some(format!("reason={reason}:source={term:?}:syntax={:?}:context_len={}:depth={depth}:remaining={remaining}", self.expressions.get(term.expr), context.len()));
            }
        });
    }

    /// A deliberately partial *typing derivation* for evaluated closures.
    /// In contrast to inferring just the normalized neutral head, this
    /// reconstructs the original expression's typing through its capture
    /// environment. In particular, beta reduction of an ill-typed App
    /// cannot serve as a substitute for checking the argument.
    // Private continuation ONLY for TYPEs obtained by the checked application
    // premises below. Actual argument typing derives `left`; actual function
    // typing and Pi elimination derive formation of `right`. Conversion alone
    // cannot manufacture this premise for arbitrary beta-erased source terms.
    fn compare_derived_fixed_pi_types(&self,left:&TypeValue,right:&TypeValue,context:&[TypeValue],remaining:&mut usize,depth:usize)->Option<Judgment<()>> {
        if !self.strict_origin_probe{return None;}
        let TypeValue::Pi{domain:left_domain,body:left_body,binder,binder_owner:Some(owner)}=left else{return None;};
        let TypeValue::Term(right_source)=right else{return None;};
        let Expr::Pi{domain:right_domain,body:right_body}=self.expressions.get(right_source.expr)? else{return None;};
        let TypeValue::Term(left_source)=left_domain.as_ref() else{return None;};
        if depth>=48||fresh_local(context.len())!=Some(*binder)||owner.parent_id()!=Some(left_source.env.id()) {return None;}
        if !matches!(owner.lookup_binding_ref(0),Some(EnvBinding::Free(free)) if free==binder){return None;}
        let witness=self.checked_binding_lineage.borrow().get(&owner.id()).cloned().flatten()?;
        if witness.domain!=**left_domain||witness.protected_prefix.len()!=context.len()+1||witness.protected_prefix[..context.len()]!=*context||witness.protected_prefix.last()!=Some(left_domain.as_ref()){return None;}
        if !take_step(remaining){return None;}
        let required=right_source.sibling(*right_domain,right_source.env.clone());
        let goal=right_source.sibling(*right_body,right_source.env.clone());
        if !self.source_used_capture_authority_available(left_source,remaining)||!self.source_used_capture_authority_available(&required,remaining){return None;}
        let relation=crate::convert::convert_with_policy_in_context_remaining(self,left_domain,&TypeValue::Term(required),crate::convert::DeltaPolicy::PreferredOnly,context.len(),context,remaining);
        if !relation.is_proven(){return Some(relation);}
        if !crate::convert::source_opening_avoids_capture(self,&goal,*binder,remaining){return None;}
        // Equality of the two formed domains licenses the SAME actual local
        // in the right codomain. Preserve the original right lexical parent
        // and universe substitution; do not identify independent FreeIds.
        let extended=witness.protected_prefix.clone();
        let frame=goal.env.extend_neutral_paid(Neutral{head:NeutralHead::Free(*binder,Some(owner.clone())),spine:vec![]},remaining)?;
        if !take_step(remaining){return None;}
        self.retain_shared_checked_binding(&frame,(**left_domain).clone(),extended.clone());
        if !self.source_used_type_value_authority_available(left_body,remaining){return None;}
        let goal=TypeValue::Term(goal.sibling(goal.expr,frame));
        if let Some(result)=self.compare_derived_fixed_pi_types(left_body,&goal,extended.as_slice(),remaining,depth+1){return Some(result);}
        Some(crate::convert::convert_with_policy_in_context_remaining(self,left_body,&goal,crate::convert::DeltaPolicy::PreferredOnly,extended.len(),extended.as_slice(),remaining))
    }

    fn source_used_type_value_authority_available(&self,value:&TypeValue,remaining:&mut usize)->bool {
        match value {
            TypeValue::Term(source)=>self.source_used_capture_authority_available(source,remaining),
            TypeValue::Sort(_)=>true,
            TypeValue::Pi{domain,body,..}=>self.source_used_type_value_authority_available(domain,remaining)&&self.source_used_type_value_authority_available(body,remaining),
        }
    }

    fn retain_checked_argument(&self,function:Closure,argument:Closure,domain:TypeValue,context:&[TypeValue],remaining:&mut usize){
        if !self.strict_origin_probe && std::env::var_os("NUCLEUS_EXPERIMENTAL_TYPED_LINEAGE").is_none(){return;}
        let cost=context.len()+1;if context.len()>128 || *remaining<cost{return;}
        let mut entries=self.checked_arguments.borrow_mut();if entries.len()>=4096 && !entries.contains_key(&argument){return;}
        let variants=entries.entry(argument).or_default();if variants.len()>=4 || variants.iter().any(|p|p.context.as_slice()==context&&p.domain==domain){return;}
        *remaining-=cost;variants.push(CheckedArgumentJudgment{function,domain,context:Rc::new(context.to_vec())});
    }

    fn certify_evaluated_binding(&self,frame:&EnvFrame,context:&[TypeValue],remaining:&mut usize,depth:usize)->Option<()>{
        let (binder,argument)=crate::machine::actual_binding_origin(self.environment.authority(),frame)?;
        if frame.parent_frame().as_ref()!=Some(&binder.env)
            || !matches!(frame.lookup_binding_ref(0),Some(EnvBinding::Closure(actual)) if actual==&argument){return None;}
        if let Some(Some(w))=self.checked_binding_lineage.borrow().get(&frame.id())
            && self.checked_binding_lineage.source_context(frame.id()).is_some()
            && context.starts_with(&w.protected_prefix){return Some(());}
        if !self.binding_checks_active.borrow_mut().insert(frame.id()){return None;}
        let result=(||{
            if !take_step(remaining) || context.len()>128{return None;}
            let annotation=match self.expressions.get(binder.expr)? {
                Expr::Lam{domain,..}=>*domain,
                Expr::Let{ty,value,..} if argument==binder.sibling(*value,binder.env.clone())=>*ty,
                _=>return None,
            };
            let domain=binder.sibling(annotation,binder.env.clone());
            let formation=self.infer_exact_closure_in_context(&domain,context,remaining,depth+1)?;
            let formed=match formation {
                TypeValue::Sort(_)=>true,
                TypeValue::Term(ref ty) if matches!(self.expressions.get(ty.expr),Some(Expr::Sort(_)))=>{
                    let Some(Expr::Sort(level))=self.expressions.get(ty.expr) else{unreachable!()};
                    crate::level::instantiate_level_with_remaining(self.levels,*level,&ty.levels,remaining).is_ok()
                },
                other=>{let allowance=(*remaining).min(512);if allowance==0{return None;}*remaining-=allowance;self.sort_level(Judgment::proven(other,"actual-evaluator-binding-annotation"),allowance).is_proven()},
            };
            if !formed{return None;}
            let proof=self.checked_arguments.borrow().get(&argument).and_then(|ps|ps.iter().find(|p|p.context.as_slice()==context)).cloned();
            let mut observations=HashMap::new();
            let known=proof.as_ref().filter(|p|self.owned_goal_dependencies(&p.function,&argument,context,remaining).is_some()
                && self.collect_substitution_authority(&p.function,remaining,&mut observations)
                && self.collect_substitution_type_authority(&p.domain,remaining,&mut observations)).map(|p|p.domain.clone());
            let actual_type=match known {Some(ty)=>ty,None=>self.infer_exact_closure_in_context(&argument,context,remaining,depth+1)?};
            let expected=TypeValue::Term(domain.clone());
            let mut allowance=(*remaining).min(512);let before=allowance;
            let relation=match self.compare_derived_fixed_pi_types(&actual_type,&expected,context,&mut allowance,0){
                Some(result)=>result,
                None=>crate::convert::convert_with_policy_in_context_remaining(self,&actual_type,&expected,self.delta_policy,context.len(),context,&mut allowance),
            };*remaining-=before-allowance;
            if !relation.is_proven(){return None;}
            if self.owned_goal_dependencies(&argument,&domain,context,remaining).is_none()
                || !self.collect_substitution_authority(&argument,remaining,&mut observations)
                || !self.collect_substitution_authority(&domain,remaining,&mut observations)
                || !self.collect_substitution_type_authority(&actual_type,remaining,&mut observations){return None;}
            for ty in context {if !self.collect_substitution_type_authority(ty,remaining,&mut observations){return None;}}
            if observations.len()>128 || *remaining<observations.len()+context.len()+1{return None;}
            *remaining-=observations.len()+context.len()+1;
            if self.checked_binding_lineage.borrow().get(&frame.id()).is_some_and(|w|w.as_ref().is_none_or(|w|w.domain!=expected||w.protected_prefix.as_slice()!=context)){return None;}
            let gamma=Rc::new(context.to_vec());
            self.checked_binding_lineage.derive(frame.id(),observations.into_values().collect(),binder.env.clone(),gamma.clone());
            self.retain_shared_checked_binding(frame,expected,gamma);
            #[cfg(feature="diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_CHECKED_BETA").is_some(){eprintln!("CHECKED_BETA_BINDING frame={} source={:?} gamma={} remaining={remaining}",frame.id(),binder.expr,context.len());}
            self.checked_binding_lineage.borrow().get(&frame.id()).is_some_and(Option::is_some).then_some(())
        })();
        self.binding_checks_active.borrow_mut().remove(&frame.id());result
    }

    fn infer_exact_closure_in_context(
        &self,
        term: &Closure,
        context: &[TypeValue],
        remaining: &mut usize,
        depth: usize,
    ) -> Option<TypeValue> {
        if depth >= 48 {
            #[cfg(feature = "diagnostics")]
            self.record_capture_source_failure(term, context, *remaining, depth, "source-depth-limit");
            return None;
        }
        if !take_step(remaining) {
            #[cfg(feature = "diagnostics")]
            self.record_capture_source_failure(term, context, *remaining, depth, "source-fuel-exhausted");
            return None;
        }
        if self.checked_binding_lineage.borrow().get(&term.env.id()).is_some_and(Option::is_none) {
            return None;
        }
        match self.expressions.get(term.expr)? {
            Expr::BVar(index) => {
                let Some(owner) = term.env.binding_frame(*index) else { return None; };
                if self.checked_binding_lineage.borrow().get(&owner.id()).is_some_and(Option::is_none) {
                    return None;
                }

                if self.strict_origin_probe && owner.evaluated_binding_origin().is_some(){
                    self.certify_evaluated_binding(&owner,context,remaining,depth+1)?;
                }

                // Only a source-checked binder or dependent elimination can
                // supply this immutable binding-node typing witness. Reuse
                // its type at the exact protected scope before recursively
                // inferring a value in a possibly different context.
                if (self.strict_origin_probe ||
                    std::env::var_os("NUCLEUS_EXPERIMENTAL_TYPED_VALUE_NORMALIZATION").is_some())
                    && let Some(checked) =
                        self.checked_type_of_bound_source(&term.env, *index, context)
                {
                    return Some(checked);
                }
                // This diagnostic probe cannot convert numeric FreeId
                // coincidence into an origin-type certificate. An immutable
                // checked binder witness with EXACT protected scope is needed.
                if self.strict_origin_probe {
                    match term.env.lookup(*index)? {
                        EnvBinding::Free(_) => {
                            #[cfg(feature = "diagnostics")]
                            self.record_capture_source_failure(term, context, *remaining, depth, "strict-free-witness-unavailable");
                            return None;
                        }
                        EnvBinding::Neutral(Neutral {
                            head: NeutralHead::Free(_, _), spine,
                        }) if spine.is_empty() => {
                            #[cfg(feature = "diagnostics")]
                            self.record_capture_source_failure(term, context, *remaining, depth, "strict-neutral-free-witness-unavailable");
                            return None;
                        }
                        _ => {}
                    }
                }
                match term.env.lookup(*index)? {
                    EnvBinding::Free(free) =>
                        context.get(usize::try_from(free.0).ok()?).cloned(),
                    EnvBinding::Neutral(Neutral {
                        head: NeutralHead::Free(free, _), spine,
                    }) if spine.is_empty() =>
                        context.get(usize::try_from(free.0).ok()?).cloned(),
                    EnvBinding::Closure(value) =>
                        self.infer_exact_closure_in_context(
                            &value, context, remaining, depth + 1,
                        ),
                    EnvBinding::Neutral(_) => None,
                    EnvBinding::NatLit(_) => self.environment.nat_primitives().map(|nat|TypeValue::Term(self.closure(nat.type_expr,EnvFrame::empty()))),
                }
            },
            Expr::Sort(level) => Some(TypeValue::Sort(succ(
                instantiate_level(self.levels, *level, &term.levels, *remaining).ok()?,
            ))),
            Expr::Const { name, levels } => {
                let declaration = self.environment.get(*name)?;
                if declaration.level_params.len() != levels.len() {
                    return None;
                }
                let mut substitution = Vec::with_capacity(levels.len());
                for (param, level) in declaration.level_params.iter().zip(levels) {
                    let value = instantiate_level(
                        self.levels, *level, &term.levels, *remaining,
                    ).ok()?;
                    substitution.push((*param, value));
                }
                Some(TypeValue::Term(Closure::with_levels(
                    declaration.ty, EnvFrame::empty(),
                    LevelSubstitution::new(substitution),
                )))
            }
            Expr::App { fun, arg } => {
                let function = term.sibling(*fun, term.env.clone());
                let argument = term.sibling(*arg, term.env.clone());
                let function_ty = self.infer_exact_closure_in_context(
                    &function, context, remaining, depth + 1,
                )?;
                let Some((domain, body)) = self.pi_view(
                    Judgment::proven(function_ty, "exact-captured-function-type"),
                    (*remaining).min(512),
                ) else {
                    #[cfg(feature = "diagnostics")]
                    self.record_capture_source_failure(term, context, *remaining, depth, "function-Pi-view-unavailable");
                    return None;
                };
                let argument_ty = self.infer_exact_closure_in_context(
                    &argument, context, remaining, depth + 1,
                )?;
                let mut domain_allowance=(*remaining).min(512);
                let mut domain_check=match self.compare_derived_fixed_pi_types(&argument_ty,&domain,context,&mut domain_allowance,0) {
                    Some(result)=>result,
                    None=>crate::convert::convert_with_policy_in_context_remaining(self,&argument_ty,&domain,crate::convert::DeltaPolicy::PreferredOnly,context.len(),context,&mut domain_allowance),
                };
                // This stronger conversion is available only inside the
                // independently typed transported-proof rule. The argument
                // was inferred above; both actual types must separately form
                // a sort before retrying their domain relation. The proof
                // subject itself still independently has a Prop type; no
                // data-context binding is transported by this retry.
                if !domain_check.is_proven() && self.strict_origin_probe
                    && TRANSPORT_PROOF_ACTIVE.with(|flag|flag.get())
                    && let (TypeValue::Term(actual_type),TypeValue::Term(expected_type))=(&argument_ty,&domain)
                    && self.paid_strict_source_sort(actual_type,context,remaining).is_some()
                    && self.paid_strict_source_sort(expected_type,context,remaining).is_some()
                    && *remaining>=1024
                {
                    *remaining-=1024;
                    domain_check=crate::convert::convert_with_policy_in_context(
                        self,&argument_ty,&domain,1024,crate::convert::DeltaPolicy::GuardedSemanticFallback,context.len(),context,
                    );
                    #[cfg(feature="diagnostics")]
                    Self::proof_transport_trace("guarded-proof-argument-domain",(term.expr,&argument_ty,&domain,&domain_check,*remaining));
                    #[cfg(feature="diagnostics")]
                    if term.expr==ExprId(66500) && !domain_check.is_proven() && std::env::var_os("NUCLEUS_POST_TRANSPORT_ARGUMENT").is_some(){TRANSPORT_ARGUMENT_POST.with(|slot|*slot.borrow_mut()=Some((argument_ty.clone(),domain.clone(),context.to_vec())));}

                }
                if !domain_check.is_proven() {
                    #[cfg(feature = "diagnostics")]
                    self.record_capture_source_failure(term, context, *remaining, depth, &format!("argument-domain-relation:{domain_check:?}"));
                    return None;
                }
                self.retain_checked_argument(function.clone(),argument.clone(),domain.clone(),context,remaining);
                if !take_step(remaining) {
                    #[cfg(feature = "diagnostics")]
                    self.record_capture_source_failure(term, context, *remaining, depth, "argument-substitution-fuel-exhausted");
                    return None;
                }
                match body {
                    PiBody::Fixed(binder, inferred_body, owner) => {
                        self.instantiate_checked_fixed_pi_body(
                            &inferred_body, binder, owner.as_ref(), &domain, &argument, context, &term.env, remaining,
                        )
                    }
                    PiBody::Closure(body) => {
                        // A literal Sort contains no term variable. Preserve
                        // its original closure/Theta after checking the argument.
                        if matches!(self.expressions.get(body.expr),Some(Expr::Sort(_))) {
                            return Some(TypeValue::Term(body));
                        }
                        // Reuse only the complete captured codomain, actual
                        // argument, checked domain and actual Gamma tuple.
                        // Both argument premises were established above;
                        // elimination lineage is retained on every cache hit.
                        let extended = self.checked_captured_pi_frame(
                            &body, &argument, domain, context,
                        );
                        Some(TypeValue::Term(Closure::with_levels(
                            body.expr,extended,body.levels,
                        )))
                    },
                }
            }
            Expr::NatLit(_) => self.infer_in(
                term.expr, context, &term.env, remaining,
                &mut HashMap::new(),
            ).proven_value().cloned(),
            Expr::Let { ty, value, body } => {
                let declared = term.sibling(*ty, term.env.clone());
                let declared_sort = self.infer_exact_closure_in_context(
                    &declared, context, remaining, depth + 1,
                )?;
                if !self.sort_level(
                    Judgment::proven(declared_sort, "captured-let-annotation"),
                    (*remaining).min(512),
                ).is_proven() {
                    return None;
                }
                let value = term.sibling(*value, term.env.clone());
                let value_ty = self.infer_exact_closure_in_context(
                    &value, context, remaining, depth + 1,
                )?;
                if !crate::convert::convert_with_policy_in_context(
                    self, &value_ty, &TypeValue::Term(declared.clone()),
                    (*remaining).min(512),
                    crate::convert::DeltaPolicy::PreferredOnly,
                    context.len(), context,
                ).is_proven() {
                    return None;
                }
                let extended=term.env.extend(value);
                self.retain_checked_elimination(
                    &extended,TypeValue::Term(declared.clone()),context,
                );
                if self.strict_origin_probe {
                    self.retain_checked_binding(&extended,TypeValue::Term(declared),context);
                }
                let body=term.sibling(*body,extended);
                self.infer_exact_closure_in_context(
                    &body,context,remaining,depth+1,
                )
            }
            Expr::Pi { domain, body } | Expr::Lam { domain, body } => {
                let is_pi = matches!(
                    self.expressions.get(term.expr), Some(Expr::Pi { .. })
                );
                let domain = term.sibling(*domain, term.env.clone());
                let domain_ty = self.infer_exact_closure_in_context(
                    &domain, context, remaining, depth + 1,
                )?;
                let domain_sort_result = self.sort_level(
                    Judgment::proven(domain_ty, "captured-binder-domain"),
                    (*remaining).min(512),
                );
                let Some(domain_sort) = domain_sort_result.proven_value().cloned() else {
                    #[cfg(feature = "diagnostics")]
                    self.record_capture_source_failure(term, context, *remaining, depth, &format!("binder-domain-formation:{domain_sort_result:?}"));
                    return None;
                };
                let binder = FreeId(u64::try_from(context.len()).ok()?);
                let source_body = term.sibling(*body, term.env.clone());
                // Freshness is a required premise of this original captured
                // lambda/Pi derivation. Finish it using the same finite caller
                // allowance; a separate local cap must not discard work while
                // this derivation can still pay the actual used-source proof.
                let safe = crate::convert::source_opening_avoids_capture(
                    self, &source_body, binder, remaining,
                );
                if !safe { return None; }
                let mut extended = context.to_vec();
                extended.push(TypeValue::Term(domain.clone()));
                let body_frame=term.env.extend_free(binder);
                self.retain_checked_elimination(
                    &body_frame,TypeValue::Term(domain.clone()),&extended,
                );
                if self.strict_origin_probe {
                    self.retain_checked_binding(&body_frame,TypeValue::Term(domain.clone()),&extended);
                }
                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_SOURCE_PROOF_BETA").is_some()
                    && matches!((term.expr.0,domain.expr.0),
                        (7143,7074)|(6897,6828)|(5728,5659)|(5725,5656))
                {
                    eprintln!(
                        "NUCLEUS_SOURCE_BINDER_INTRO:route=exact-infer:lambda={:?}:ctx={}:free={binder:?}:binding_node={}:source_frame={}:domain={:?}",
                        term.expr,context.len(),body_frame.id(),term.env.id(),domain,
                    );
                }
                if self.strict_origin_probe{self.retain_shared_checked_binding(&body_frame,TypeValue::Term(domain.clone()),Rc::new(extended.clone()));}
                let body=term.sibling(*body,body_frame);
                let body_ty=self.infer_exact_closure_in_context(
                    &body,&extended,remaining,depth+1,
                )?;
                if is_pi {
                    let body_sort = self.sort_level(
                        Judgment::proven(body_ty, "captured-pi-body"),
                        (*remaining).min(512),
                    ).proven_value()?.clone();
                    Some(TypeValue::Sort(imax(domain_sort, body_sort)))
                } else {
                    Some(TypeValue::Pi {
                        domain: Box::new(TypeValue::Term(domain)),
                        body: Box::new(body_ty),
                        binder,
                     binder_owner: Some(body.env.clone()),})
                }
            }
            Expr::Proj {
                type_name,
                index,
                structure,
            } => {
                // Captured-expression counterpart of infer_uncached's checked
                // projection telescope. Do not type a projection by merely
                // reducing the field: infer its receiver in the ACTUAL
                // captured environment and validate the inductive family.
                //
                // The field metadata was admitted by the source-checked
                // inductive validator; unknown recursors, an unmatched
                // family, absent parameters, or unresolved earlier fields
                // must remain UNKNOWN. In particular, a syntactically
                // identical BVar in two captured frames is not equal.
                let spec = self.environment.projection_specs().get(type_name)?.clone();
                let index = usize::try_from(*index).ok()?;
                let field_type = spec.field_types.get(index)?.clone();
                let receiver = term.sibling(*structure, term.env.clone());
                let TypeValue::Term(receiver_type) = self.infer_exact_closure_in_context(
                    &receiver, context, remaining, depth + 1,
                )? else { return None };
                let type_exposed = self.machine().expose(
                    receiver_type, Transparency::Reducible, (*remaining).min(4096),
                );
                let Value::Neutral(receiver_type_value) =
                    type_exposed.proven_value()?.clone()
                else { return None };
                let NeutralHead::Const { name, levels } = receiver_type_value.head else {
                    return None;
                };
                if name != *type_name || receiver_type_value.spine.len() < spec.num_params {
                    return None;
                }
                let result = match field_type {
                    ProjectionFieldType::Parameter(parameter_index) => {
                        receiver_type_value.spine.get(parameter_index).cloned()?
                    }
                    ProjectionFieldType::Derived(field_expression) => {
                        let inductive_decl = self.environment.get(*type_name)?;
                        if inductive_decl.level_params.len() != levels.len() {
                            return None;
                        }
                        let mut frame = EnvFrame::empty();
                        for param in receiver_type_value.spine.iter().take(spec.num_params) {
                            frame = frame.extend(param.clone());
                        }
                        if index > 0 {
                            let value_exposed = self.machine().expose(
                                receiver, Transparency::Reducible, (*remaining).min(4096),
                            );
                            let Value::Neutral(receiver_value) =
                                value_exposed.proven_value()?.clone()
                            else { return None };
                            for field in 0..index {
                                match &receiver_value.head {
                                    NeutralHead::Const { name, .. } if *name == spec.constructor => {
                                        let offset = spec.num_params.checked_add(field)?;
                                        frame = frame.extend(receiver_value.spine.get(offset)?.clone());
                                    }
                                    NeutralHead::Const { .. } => return None,
                                    NeutralHead::Free(_, _) | NeutralHead::Projection { .. } => {
                                        frame = frame.extend_neutral(Neutral {
                                            head: NeutralHead::Projection {
                                                type_name: *type_name,
                                                index: field,
                                                structure: Box::new(receiver_value.clone()),
                                            },
                                            spine: Vec::new(),
                                        });
                                    }
                                }
                            }
                        }
                        let substitution = LevelSubstitution::new(
                            inductive_decl.level_params.iter().copied()
                                .zip(levels).collect(),
                        );
                        Closure::with_levels(field_expression, frame, substitution)
                    }
                };
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_EXACT_PROJECTION").is_some() {
                    use std::sync::atomic::{AtomicUsize, Ordering};
                    static CERTIFIED: AtomicUsize = AtomicUsize::new(0);
                    if CERTIFIED.fetch_add(1, Ordering::Relaxed) < 36 {
                        eprintln!(
                            "NUCLEUS_EXACT_PROJECTION:expr={:?}:type={type_name:?}:index={index}:context={}:frame={}:field_type={result:?}",
                            term.expr,context.len(),term.env.id()
                        );
                    }
                }
                Some(TypeValue::Term(result))
            }
            Expr::StrLit(_) => self.environment.string_literal_type().map(|ty|TypeValue::Term(self.closure(ty,EnvFrame::empty()))),
        }
    }

    /// Diagnostic-only: distinguish a qualified Nat recursor stuck on its
    /// actual major from an unrelated polymorphic constructor. No verdict is
    /// derived from the apparent four-argument shape.
    #[cfg(feature = "diagnostics")]
    pub(crate) fn diagnostic_natrec_major_authority(
        &self,
        neutral: &Neutral,
        budget: usize,
    ) -> String {
        let NeutralHead::Const { name, levels } = &neutral.head else {
            return "not-constant-head".into();
        };
        let Some(reduction) = self.environment.recursor_reduction(*name) else {
            return format!("head={name:?}:qualified_recursor=false");
        };
        let required = reduction.num_params
            .saturating_add(1)
            .saturating_add(reduction.rules.len())
            .saturating_add(reduction.num_indices)
            .saturating_add(1);
        let nat_rules = self.environment.nat_primitives().is_some_and(|nat| {
            reduction.rules.len() == 2
                && reduction.rules.iter().any(|r| r.constructor == nat.zero)
                && reduction.rules.iter().any(|r| r.constructor == nat.succ)
        });
        let exact_interface = neutral.spine.len() == required
            && reduction.level_params.len() == levels.len();
        let Some(major) = neutral.spine.get(required.saturating_sub(1)) else {
            return format!(
                "head={name:?}:levels={levels:?}:qualified_recursor=true:nat_rules={nat_rules}:required={required}:actual={}:major=missing",
                neutral.spine.len()
            );
        };
        let syntax = self.expressions.get(major.expr);
        let binding = match syntax {
            Some(Expr::BVar(index)) => major.env.lookup(*index),
            _ => None,
        };
        let whnf = self.machine().expose(
            major.clone(), Transparency::Reducible, budget.min(256),
        );
        let full = self.machine().expose(
            major.clone(), Transparency::Full, budget.min(256),
        );
        format!(
            "head={name:?}:levels={levels:?}:qualified_recursor=true:nat_rules={nat_rules}:exact_interface={exact_interface}:params={}:indices={}:rules={}:required={required}:actual={}:major={major:?}:syntax={syntax:?}:binding={binding:?}:major_whnf={whnf:?}:major_full={full:?}",
            reduction.num_params, reduction.num_indices, reduction.rules.len(),
            neutral.spine.len()
        )
    }

    /// Read-only recursor certificate and captured major chain. Never changes
    /// a conversion verdict; no application shape is itself a reduction rule.
    #[cfg(feature = "diagnostics")]
    #[cfg(feature = "diagnostics")]
    pub(crate) fn diagnostic_receiver_capture_pair(
        &self, left: &Closure, right: &Closure, context: &[TypeValue], budget: usize,
    ) -> String {
        fn chain(checker: &TypeChecker<'_>, closure: Closure, limit: usize) -> String {
            let mut pending = vec![(closure, 0u64)];
            let mut seen = std::collections::HashSet::new();
            let mut lines = Vec::new();
            for _ in 0..limit.min(128) {
                let Some((term, local_depth)) = pending.pop() else { break };
                if !seen.insert((term.clone(), local_depth)) { continue }
                let syntax = checker.expressions.get(term.expr);
                lines.push(format!("source={term:?}:local_depth={local_depth}:syntax={syntax:?}"));
                match syntax {
                    Some(Expr::BVar(index)) if *index >= local_depth => {
                        let binding = term.env.lookup_with_node_id(*index - local_depth);
                        lines.push(format!("external_index={}:binding={binding:?}", *index - local_depth));
                        if let Some((_, EnvBinding::Closure(captured))) = binding {
                            pending.push((captured, 0));
                        }
                    }
                    Some(Expr::App { fun, arg }) => {
                        pending.push((Closure::with_levels(*arg, term.env.clone(), term.levels.clone()), local_depth));
                        pending.push((Closure::with_levels(*fun, term.env, term.levels), local_depth));
                    }
                    Some(Expr::Lam { domain, body }) | Some(Expr::Pi { domain, body }) => {
                        pending.push((Closure::with_levels(*body, term.env.clone(), term.levels.clone()), local_depth + 1));
                        pending.push((Closure::with_levels(*domain, term.env, term.levels), local_depth));
                    }
                    Some(Expr::Let { ty, value, body }) => {
                        pending.push((Closure::with_levels(*body, term.env.clone(), term.levels.clone()), local_depth + 1));
                        pending.push((Closure::with_levels(*value, term.env.clone(), term.levels.clone()), local_depth));
                        pending.push((Closure::with_levels(*ty, term.env, term.levels), local_depth));
                    }
                    Some(Expr::Proj { structure, .. }) =>
                        pending.push((Closure::with_levels(*structure, term.env, term.levels), local_depth)),
                    _ => {}
                }
            }
            lines.push(format!("unfinished_nodes={}", pending.len()));
            lines.join(" | ")
        }
        let mut output = vec![format!("left={left:?}:right={right:?}:context={context:?}")];
        for index in [4, 1] {
            let lhs = left.env.lookup_with_node_id(index);
            let rhs = right.env.lookup_with_node_id(index);
            output.push(format!("capture_index={index}:left_binding={lhs:?}:right_binding={rhs:?}"));
            match (lhs, rhs) {
                (Some((_, EnvBinding::Closure(a))), Some((_, EnvBinding::Closure(b)))) => {
                    output.push(format!("left_chain={}", chain(self, a.clone(), budget)));
                    output.push(format!("right_chain={}", chain(self, b.clone(), budget)));
                    let _scope = CaptureSourceFailureScope::enter();
                    let relation = self.checked_source_conversion(&a, &b, context, budget.min(128));
                    output.push(format!("independently_typed_capture_relation={relation:?}:first_source_failure={:?}", CaptureSourceFailureScope::first()));
                }
                _ => output.push("typed_capture_relation=unavailable-nonclosure-binding".to_string()),
            }
        }
        output.join(" || ")
    }

    pub(crate) fn diagnostic_captured_recursor_major_chain(
        &self, neutral: &Neutral, budget: usize,
    ) -> String {
        let NeutralHead::Const { name, levels } = &neutral.head else {
            return "non-constant-head".to_string();
        };
        let reduction = self.environment.recursor_reduction(*name);
        let rules = reduction.map(|r| {
            r.rules.iter().map(|c| {
                format!("ctor={:?}:params={}:fields={}", c.constructor, c.num_params, c.num_fields)
            }).collect::<Vec<_>>()
        });
        let mut chain = Vec::new();
        let major_of=|n:&Neutral| {
            let NeutralHead::Const{name,..}=&n.head else{return None;};
            let r=self.environment.recursor_reduction(*name)?;
            n.spine.get(r.num_params+1+r.rules.len()+r.num_indices).cloned()
        };
        let mut current = major_of(neutral);
        let machine = self.machine();
        for step in 0..64 {
            let Some(closure) = current.take() else { break };
            let syntax = self.expressions.get(closure.expr);
            let binding = match syntax {
                Some(Expr::BVar(n)) => closure.env.lookup(*n),
                _ => None,
            };
            let whnf = machine.expose(
                closure.clone(), Transparency::Full, budget.min(256),
            );
            let value = whnf.proven_value();
            let classifier = match value {
                Some(Value::Neutral(Neutral { head: NeutralHead::Const { name: head, .. }, spine })) => {
                    if let Some(r) = reduction {
                        format!(
                            "neutral={head:?}:arity={}:constructor_rule={}:same_recursor={}",
                            spine.len(), r.rules.iter().any(|rule| rule.constructor == *head),
                            *head == *name,
                        )
                    } else {
                        format!("neutral={head:?}:arity={}:no_recursor_authority",spine.len())
                    }
                }
                Some(Value::Neutral(n)) => format!("other_neutral={:?}",n.head),
                Some(Value::NatLit(n)) => format!("nat={n:?}"),
                Some(Value::Sort(l)) => format!("sort={l:?}"),
                Some(Value::Lam { .. }) => "lambda".to_string(),
                Some(Value::Pi { .. }) => "pi".to_string(),
                Some(Value::StuckProjection { .. }) => "stuck_projection".to_string(),
                None => format!("unknown_or_refuted={whnf:?}"),
            };
            chain.push(format!(
                "step={step}:expr={:?}:frame={}:syntax={syntax:?}:binding={binding:?}:classifier={classifier}",
                closure.expr,closure.env.id(),
            ));
            current = match value {
                Some(Value::Neutral(inner)) if major_of(inner).is_some()=>major_of(inner),
                _ => match binding {
                    Some(crate::value::EnvBinding::Closure(inner))=>Some(inner),
                    _=>None,
                },
            };
            if current.as_ref() == Some(&closure) {
                chain.push("cyclic-major-closure".to_string());
                break;
            }
        }
        format!(
            "head={name:?}:levels={levels:?}:arity={}:qualified={}:rules={rules:?}:major_chain={chain:?}",
            neutral.spine.len(), reduction.is_some()
        )
    }

    /// Diagnostic only: instantiate a declaration's dependent Pi telescope
    /// with the actual application closures, never authorizing acceptance.
    #[cfg(feature = "diagnostics")]
    pub(crate) fn diagnostic_applied_telescope(
        &self,
        name: NameId,
        args: &[Closure],
        budget: usize,
    ) -> String {
        let Some(decl) = self.environment.get(name) else {
            return "missing-declaration".into();
        };
        let mut current = Closure::new(decl.ty, EnvFrame::empty());
        let mut steps = Vec::new();
        for (i, arg) in args.iter().enumerate() {
            let exposed = self.machine().expose(
                current.clone(), Transparency::Reducible, budget,
            );
            match exposed.proven_value() {
                Some(Value::Pi { domain, body }) => {
                    steps.push(format!("arg={i}:domain={domain:?}:actual={arg:?}"));
                    current = Closure::with_levels(
                        body.expr, body.env.extend(arg.clone()), body.levels.clone(),
                    );
                }
                other => {
                    steps.push(format!("arg={i}:non-pi={other:?}"));
                    return format!("{steps:?}");
                }
            }
        }
        let codomain = self.machine().expose(
            current, Transparency::Reducible, budget,
        );
        format!("steps={steps:?}:instantiated_codomain={codomain:?}")
    }

    pub(crate) fn is_proposition_in_context(
        &self,
        expression: ExprId,
        context: &[TypeValue],
        frame: &EnvFrame,
        budget: usize,
    ) -> Judgment<()> {
        let mut remaining = budget;
        self.check_in(
            expression,
            &TypeValue::Sort(LevelTerm::Zero),
            context,
            frame,
            &mut remaining,
            false,
            &mut HashMap::new(),
        )
    }

    /// Proof-type formation through the exact captured closure. Unlike
    /// checking bare ExprId against Sort 0, this preserves both its lexical
    /// frame AND the universe-level substitution that produced the type.
    /// It is valid only as a side-condition for ordinary proof irrelevance:
    /// this judgment alone cannot identify any two proof terms.
    pub(crate) fn checked_captured_prop_type_in_context(
        &self,
        proposition: &Closure,
        context: &[TypeValue],
        budget: usize,
    ) -> Judgment<()> {
        let mut remaining = budget.min(2048);
        let Some(formation)=self.infer_exact_closure_in_context(
            proposition, context, &mut remaining, 0,
        ) else {
            return Judgment::unknown("captured-proposition-formation-obligation");
        };
        match self.sort_level(
            Judgment::proven(formation, "exact-captured-proposition-formation"),
            remaining.min(1024),
        ) {
            Judgment::Proven {value:LevelTerm::Zero,..} =>
                Judgment::proven((), "checked-captured-proposition-Sort0"),
            Judgment::Proven {..} =>
                Judgment::refuted("captured-proposition-sort-not-Prop"),
            Judgment::Refuted {obstruction} => Judgment::Refuted {obstruction},
            Judgment::Unknown {residual} => Judgment::Unknown {residual},
        }
    }

    /// A reusable source-scoped conversion warrant. Both terms must first
    /// typecheck in the SAME real context; equality of their types is not
    /// confused with equality of their values. No unchecked strengthening.
    pub(crate) fn checked_source_conversion(
        &self,
        left: &Closure,
        right: &Closure,
        context: &[TypeValue],
        budget: usize,
    ) -> Judgment<()> {
        let mut left_fuel=budget.min(4096);
        let Some(left_type)=self.infer_exact_closure_in_context(
            left,context,&mut left_fuel,0,
        ) else { return Judgment::unknown("source-left-type-unavailable") };
        let mut right_fuel=budget.min(4096);
        let Some(right_type)=self.infer_exact_closure_in_context(
            right,context,&mut right_fuel,0,
        ) else { return Judgment::unknown("source-right-type-unavailable") };
        let types=crate::convert::convert_with_policy_in_context(
            self,&left_type,&right_type,budget.min(2048),
            crate::convert::DeltaPolicy::PreferredOnly,
            context.len(),context,
        );
        if !types.is_proven() { return types }
        crate::convert::convert_with_policy_in_context(
            self,&TypeValue::Term(left.clone()),&TypeValue::Term(right.clone()),
            budget.min(4096),crate::convert::DeltaPolicy::PreferredOnly,
            context.len(),context,
        )
    }

    // The converter has paid index+1 for this actual immutable binding read.
    // Eligibility is retained separately so a revoked payload does not move
    // the original strict proof fallback ahead of ordinary computation.
    pub(crate) fn paid_source_substitution_payload(&self,source:&Closure,index:u64)->(bool,Option<Closure>){
        if !matches!(self.expressions.get(source.expr),Some(Expr::BVar(actual)) if *actual==index){return(false,None);}
        let Some(owner)=source.env.binding_frame(index)else{return(false,None);};
        let Some(EnvBinding::Closure(actual))=owner.lookup_binding_ref(0)else{return(false,None);};
        if [source.env.id(),owner.id(),actual.env.id()].iter().any(|id|self.checked_binding_lineage.borrow().get(id).is_some_and(Option::is_none)){return(true,None);}
        (true,Some(actual.clone()))
    }
    pub(crate) fn same_monomorphic_source_constant(&self,left:&Closure,right:&Closure,remaining:&mut usize)->bool{
        let (Some(Expr::Const{name:a,levels:la}),Some(Expr::Const{name:b,levels:lb}))=(self.expressions.get(left.expr),self.expressions.get(right.expr))else{return false;};
        if a!=b||!la.is_empty()||!lb.is_empty()||!take_step(remaining){return false;}
        if [left.env.id(),right.env.id()].iter().any(|id|self.checked_binding_lineage.borrow().get(id).is_some_and(Option::is_none)){return false;}
        self.environment.get(*a).is_some_and(|decl|decl.level_params.is_empty())
    }

    // A completed source AST theorem: body = lift(domain, 1, cutoff 0).
    // It contains no Gamma, universe substitution, value or typing judgment.
    fn discover_completed_pi_lift(&self,domain:ExprId,body:ExprId,domain_support:&[u64],body_support:&[u64],remaining:&mut usize){
        if domain_support.len()!=body_support.len(){return;}
        let (Some(left),Some(right))=(self.expressions.get(domain),self.expressions.get(body))else{return;};
        if std::mem::discriminant(left)!=std::mem::discriminant(right)
            ||matches!(left,Expr::BVar(_)|Expr::Const{..}|Expr::Sort(_)|Expr::NatLit(_)|Expr::StrLit(_)){return;}
        if !take_step(remaining)||self.completed_pi_lifts.borrow().contains(&(domain,body)){return;}
        if self.completed_pi_lifts.borrow().len()>=4096{return;}
        for (a,b) in domain_support.iter().zip(body_support){if !take_step(remaining)||a.checked_add(1)!=Some(*b){return;}}
        let allowance=(*remaining).min(64);let mut trial=allowance;
        let complete=self.complete_ast_lift(domain,body,&mut trial);
        *remaining-=allowance-trial;
        if complete {self.completed_pi_lifts.borrow_mut().insert((domain,body));
            #[cfg(feature="diagnostics")] if std::env::var_os("TRACE_SOURCE_PI_LIFT").is_some(){eprintln!("SOURCE_PI_LIFT_PUBLISHED domain={} body={} remaining={remaining}",domain.0,body.0);}
        }
    }
    fn complete_ast_lift(&self,domain:ExprId,body:ExprId,remaining:&mut usize)->bool {
        let mut pending=vec![(domain,body,0u64,false)];let mut active=std::collections::HashSet::new();let mut done=std::collections::HashSet::new();
        while let Some((a,b,cutoff,finish))=pending.pop(){
            if !take_step(remaining){return false;}
            let key=(a,b,cutoff);
            if finish {active.remove(&key);done.insert(key);continue;}
            if done.contains(&key){continue;}if !active.insert(key){return false;}
            let (Some(left),Some(right))=(self.expressions.get(a),self.expressions.get(b))else{return false;};
            pending.push((a,b,cutoff,true));
            match (left,right) {
                (Expr::BVar(x),Expr::BVar(y))=>{let wanted=if *x<cutoff{Some(*x)}else{x.checked_add(1)};if wanted!=Some(*y){return false;}},
                (Expr::Const{..},Expr::Const{..})|(Expr::Sort(_),Expr::Sort(_))|(Expr::NatLit(_),Expr::NatLit(_))|(Expr::StrLit(_),Expr::StrLit(_))=>{if a!=b{return false;}},
                (Expr::App{fun:x,arg:u},Expr::App{fun:y,arg:v})=>{pending.push((*u,*v,cutoff,false));pending.push((*x,*y,cutoff,false));},
                (Expr::Lam{domain:x,body:u},Expr::Lam{domain:y,body:v})|(Expr::Pi{domain:x,body:u},Expr::Pi{domain:y,body:v})=>{let Some(next)=cutoff.checked_add(1)else{return false;};pending.push((*u,*v,next,false));pending.push((*x,*y,cutoff,false));},
                (Expr::Let{ty:x,value:u,body:p},Expr::Let{ty:y,value:v,body:q})=>{let Some(next)=cutoff.checked_add(1)else{return false;};pending.push((*p,*q,next,false));pending.push((*u,*v,cutoff,false));pending.push((*x,*y,cutoff,false));},
                (Expr::Proj{type_name:x,index:i,structure:u},Expr::Proj{type_name:y,index:j,structure:v}) if x==y&&i==j=>pending.push((*u,*v,cutoff,false)),
                _=>return false,
            }
        }
        true
    }
    pub(crate) fn completed_pi_lift_for_source(&self,domain:&Closure,body:&Closure,remaining:&mut usize)->bool{
        if domain.env!=body.env||domain.levels.identity()!=body.levels.identity(){return false;}
        let (Some(left),Some(right))=(self.expressions.get(domain.expr),self.expressions.get(body.expr))else{return false;};
        if std::mem::discriminant(left)!=std::mem::discriminant(right)||!take_step(remaining){return false;}
        self.completed_pi_lifts.borrow().contains(&(domain.expr,body.expr))
    }

    // A complete structural support certificate carries no typing authority.
    pub(crate) fn complete_source_support(&self, expression: ExprId, remaining: &mut usize) -> Option<Vec<u64>> {
        let mut pending = vec![(expression, false)];
        let mut active = std::collections::HashSet::new();
        let mut complete = HashMap::<ExprId, Vec<u64>>::new();
        while let Some((id, finish)) = pending.pop() {
            if !finish {
                if !take_step(remaining) { return None }
                if complete.contains_key(&id) { continue }
                if let Some(support) = self.source_support.borrow().get(&id).cloned() {
                    complete.insert(id, support);
                    continue;
                }
                if !active.insert(id) { return None } // no cyclic coinduction
                pending.push((id, true));
                match self.expressions.get(id)? {
                    Expr::App { fun, arg } => {
                        pending.push((*arg, false)); pending.push((*fun, false));
                    }
                    Expr::Lam { domain, body } | Expr::Pi { domain, body } => {
                        pending.push((*body, false)); pending.push((*domain, false));
                    }
                    Expr::Let { ty, value, body } => {
                        pending.push((*body, false)); pending.push((*value, false)); pending.push((*ty, false));
                    }
                    Expr::Proj { structure, .. } => pending.push((*structure, false)),
                    Expr::BVar(_) | Expr::Const { .. } | Expr::Sort(_)
                    | Expr::NatLit(_) | Expr::StrLit(_) => {}
                }
            } else {
                let mut support = std::collections::BTreeSet::new();
                let mut add = |child: ExprId, under_binder: bool| -> Option<()> {
                    for index in complete.get(&child)? {
                        if !take_step(remaining) { return None }
                        if !under_binder || *index > 0 {
                            support.insert(if under_binder { index - 1 } else { *index });
                            if support.len() > 128 { return None }
                        }
                    }
                    Some(())
                };
                match self.expressions.get(id)? {
                    Expr::BVar(index) => { support.insert(*index); }
                    Expr::App { fun, arg } => { add(*fun, false)?; add(*arg, false)?; }
                    Expr::Lam { domain, body } | Expr::Pi { domain, body } => {
                        add(*domain, false)?; add(*body, true)?;
                    }
                    Expr::Let { ty, value, body } => {
                        add(*ty, false)?; add(*value, false)?; add(*body, true)?;
                    }
                    Expr::Proj { structure, .. } => { add(*structure, false)?; }
                    Expr::Const { .. } | Expr::Sort(_) | Expr::NatLit(_) | Expr::StrLit(_) => {}
                }
                active.remove(&id);
                let support: Vec<_> = support.into_iter().collect();
                if let Some(Expr::Pi{domain,body})=self.expressions.get(id){self.discover_completed_pi_lift(*domain,*body,complete.get(domain)?,complete.get(body)?,remaining);}
                if self.source_support.borrow().len() < 8192 {
                    self.source_support.borrow_mut().insert(id, support.clone());
                }
                complete.insert(id, support);
            }
        }
        let support = complete.remove(&expression)?;
        if *remaining < support.len() { return None }
        *remaining -= support.len();
        Some(support)
    }

    // Intrinsic alpha support: indices are relative to the paired source roots.
    // The memo records syntax only, never a captured value or typing witness.
    fn complete_paired_source_support(&self, left: ExprId, right: ExprId, remaining: &mut usize) -> Option<Vec<(u64, u64)>> {
        if left == right {
            return self.complete_source_support(left, remaining).map(|indices| indices.into_iter().map(|i| (i, i)).collect());
        }
        let lexical_pair={let patterns=self.source_syntax_patterns.borrow();
            match (patterns.get(&left),patterns.get(&right)) {
                (Some((a,x)),Some((b,y))) if a==b && x.len()==y.len()=>Some(x.iter().copied().zip(y.iter().copied()).collect::<Vec<_>>()),
                _=>None,
            }};
        if let Some(support)=lexical_pair {
            if !take_step(remaining)||*remaining<support.len(){return None;}
            *remaining-=support.len();return Some(support);
        }
        let root = (left, right);
        let mut pending = vec![(root, false)];
        let mut active = std::collections::HashSet::new();
        let mut complete = HashMap::<(ExprId, ExprId), Vec<(u64, u64)>>::new();
        while let Some((pair @ (a, b), finish)) = pending.pop() {
            if !finish {
                if !take_step(remaining) { return None }
                if complete.contains_key(&pair) { continue }
                if let Some(support) = self.paired_source_support.borrow().get(&pair).cloned() {
                    complete.insert(pair, support); continue;
                }
                if a == b {
                    let support = self.complete_source_support(a, remaining)?;
                    complete.insert(pair, support.into_iter().map(|i| (i, i)).collect());
                    continue;
                }
                if !active.insert(pair) { return None }
                pending.push((pair, true));
                match (self.expressions.get(a)?, self.expressions.get(b)?) {
                    (Expr::BVar(_), Expr::BVar(_)) => {}
                    (Expr::Const { name: x, levels: u }, Expr::Const { name: y, levels: v }) => {
                        if x != y || u.len() != v.len() || *remaining < u.len() { return None }
                        *remaining -= u.len();
                        if u != v { return None }
                    }
                    (Expr::Sort(x), Expr::Sort(y)) if x == y => {}
                    (Expr::NatLit(x), Expr::NatLit(y)) => {
                        let cost = x.limb_count().max(y.limb_count());
                        if *remaining < cost { return None }
                        *remaining -= cost;
                        if x != y { return None }
                    }
                    (Expr::StrLit(x), Expr::StrLit(y)) => {
                        let cost = x.len().max(y.len());
                        if *remaining < cost { return None }
                        *remaining -= cost;
                        if x != y { return None }
                    }
                    (Expr::App { fun: x, arg: u }, Expr::App { fun: y, arg: v }) => {
                        pending.push(((*u, *v), false)); pending.push(((*x, *y), false));
                    }
                    (Expr::Lam { domain: x, body: u }, Expr::Lam { domain: y, body: v })
                    | (Expr::Pi { domain: x, body: u }, Expr::Pi { domain: y, body: v }) => {
                        pending.push(((*u, *v), false)); pending.push(((*x, *y), false));
                    }
                    (Expr::Let { ty: x, value: u, body: m }, Expr::Let { ty: y, value: v, body: n }) => {
                        pending.push(((*m, *n), false)); pending.push(((*u, *v), false)); pending.push(((*x, *y), false));
                    }
                    (Expr::Proj { type_name: x, index: i, structure: u }, Expr::Proj { type_name: y, index: j, structure: v }) if x == y && i == j => {
                        pending.push(((*u, *v), false));
                    }
                    _ => return None,
                }
            } else {
                let mut support = std::collections::BTreeSet::new();
                let mut add = |child: (ExprId, ExprId), binder: bool| -> Option<()> {
                    for (x, y) in complete.get(&child)? {
                        if !take_step(remaining) { return None }
                        if binder {
                            match (*x, *y) {
                                (0, 0) => continue,
                                (0, _) | (_, 0) => return None,
                                _ => { support.insert((x - 1, y - 1)); }
                            }
                        } else { support.insert((*x, *y)); }
                        if support.len() > 128 { return None }
                    }
                    Some(())
                };
                match (self.expressions.get(a)?, self.expressions.get(b)?) {
                    (Expr::BVar(x), Expr::BVar(y)) => { support.insert((*x, *y)); }
                    (Expr::App { fun: x, arg: u }, Expr::App { fun: y, arg: v }) => { add((*x, *y), false)?; add((*u, *v), false)?; }
                    (Expr::Lam { domain: x, body: u }, Expr::Lam { domain: y, body: v })
                    | (Expr::Pi { domain: x, body: u }, Expr::Pi { domain: y, body: v }) => { add((*x, *y), false)?; add((*u, *v), true)?; }
                    (Expr::Let { ty: x, value: u, body: m }, Expr::Let { ty: y, value: v, body: n }) => { add((*x, *y), false)?; add((*u, *v), false)?; add((*m, *n), true)?; }
                    (Expr::Proj { structure: x, .. }, Expr::Proj { structure: y, .. }) => { add((*x, *y), false)?; }
                    _ => {}
                }
                active.remove(&pair);
                let support: Vec<_> = support.into_iter().collect();
                if self.paired_source_support.borrow().len() < 8192 {
                    self.paired_source_support.borrow_mut().insert(pair, support.clone());
                }
                complete.insert(pair, support);
            }
        }
        let support = complete.remove(&root)?;
        if *remaining < support.len() { return None }
        *remaining -= support.len();
        Some(support)
    }

    fn capture_fingerprint(&self, root:&Closure, remaining:&mut usize)->Option<CaptureFingerprint> {
        fn visit(checker:&TypeChecker<'_>,term:&Closure,remaining:&mut usize,depth:usize,
            active:&mut std::collections::HashSet<Closure>,
            complete:&mut HashMap<Closure,CaptureFingerprint>)->Option<CaptureFingerprint> {
            if depth>=64 || !take_step(remaining){return None;}
            if let Some(key)=complete.get(term){return Some(key.clone());}
            if !active.insert(term.clone()){return None;}
            let key=if let Some(Expr::BVar(index))=checker.expressions.get(term.expr) {
                let cost=usize::try_from(*index).ok()?.checked_add(1)?;
                if *remaining<cost{return None;}*remaining-=cost;
                let (node,binding)=term.env.lookup_with_node_id(*index)?;
                match binding {
                    EnvBinding::Closure(actual)=>CaptureFingerprint::Bound(node,Box::new(visit(checker,&actual,remaining,depth+1,active,complete)?)),
                    EnvBinding::Free(free)=>CaptureFingerprint::Free(free,node,term.levels.clone()),
                    EnvBinding::NatLit(number)=>{
                        if *remaining<number.limb_count(){return None;}*remaining-=number.limb_count();
                        CaptureFingerprint::Bound(node,Box::new(CaptureFingerprint::Nat(number,term.levels.clone())))
                    },
                    EnvBinding::Neutral(_)=>return None,
                }
            } else {
                let support=checker.complete_source_support(term.expr,remaining)?;
                let mut captures=Vec::new();
                for index in support {
                    let cost=usize::try_from(index).ok()?.checked_add(1)?;
                    if *remaining<cost{return None;}*remaining-=cost;
                    let (node,binding)=term.env.lookup_with_node_id(index)?;
                    let key=match binding {
                        EnvBinding::Closure(actual)=>CaptureFingerprint::Bound(node,Box::new(visit(checker,&actual,remaining,depth+1,active,complete)?)),
                        EnvBinding::Free(free)=>CaptureFingerprint::Free(free,node,term.levels.clone()),
                        EnvBinding::NatLit(number)=>{
                            if *remaining<number.limb_count(){return None;}*remaining-=number.limb_count();
                            CaptureFingerprint::Bound(node,Box::new(CaptureFingerprint::Nat(number,term.levels.clone())))
                        },
                        EnvBinding::Neutral(_)=>return None,
                    };
                    captures.push((index,key));
                }
                CaptureFingerprint::Term(term.expr,term.levels.clone(),captures)
            };
            active.remove(term);complete.insert(term.clone(),key.clone());Some(key)
        }
        visit(self,root,remaining,0,&mut std::collections::HashSet::new(),&mut HashMap::new())
    }

    fn retained_goal_dependencies_valid(&self, dependencies:&[OwnedGoalDependency], remaining:&mut usize)->bool {
        for dep in dependencies {
            if !take_step(remaining){return false;}
            if !matches!(dep.owner.lookup_with_node_id(dep.index),Some((node,_)) if node==dep.node)
                ||self.checked_binding_lineage.borrow().get(&dep.node)!=Some(&Some(dep.witness.clone())){return false;}
        }
        true
    }

    // A completed immutable environment lookup supplies the actual captured
    // value and its owning node, never a type or a context correspondence.
    // Retaining the frame pins every node used by this structural certificate.
    pub(crate) fn same_checked_bvar_origin(&self,left:&Closure,right:&Closure,context:&[TypeValue],remaining:&mut usize)->bool {
        fn domain_available(c:&TypeChecker<'_>,owner:&EnvFrame,remaining:&mut usize)->bool {
            let witness=c.checked_binding_lineage.borrow().get(&owner.id()).cloned();
            match witness {
                Some(None)=>false,None=>true,
                Some(Some(w))=>match &w.domain {
                    TypeValue::Sort(_)=>true,
                    TypeValue::Term(domain)=>{
                        if c.checked_binding_lineage.borrow().get(&domain.env.id()).is_some_and(Option::is_none){return false;}
                        matches!(c.expressions.get(domain.expr),Some(Expr::Sort(_)|Expr::Const{..}))||c.source_used_capture_authority_available(domain,remaining)
                    },TypeValue::Pi{..}=>false,
                },
            }
        }
        fn resolve(c:&TypeChecker<'_>,root:&Closure,remaining:&mut usize)->Option<(EnvFrame,FreeId)> {
            let mut source=root.clone();let mut seen=std::collections::HashSet::new();
            for _ in 0..48 {
                if !take_step(remaining)||!seen.insert(source.clone()){return None;}
                if !domain_available(c,&source.env,remaining){return None;}
                let Expr::BVar(index)=c.expressions.get(source.expr)? else{return None;};
                let owner=if *index==0 {source.env.clone()}else{c.source_capture_owner(&source.env,*index,remaining)?};
                if owner!=source.env&&!domain_available(c,&owner,remaining){return None;}
                match owner.lookup_binding_ref(0)? {
                    EnvBinding::Closure(value)=>source=value.clone(),
                    EnvBinding::Free(free)=>return Some((owner.clone(),*free)),
                    EnvBinding::Neutral(Neutral{head:NeutralHead::Free(free,Some(original)),spine}) if spine.is_empty()=>{
                        if !matches!(original.lookup_binding_ref(0),Some(EnvBinding::Free(actual)) if actual==free){return None;}
                        return Some((original.clone(),*free));
                    },_=>return None,
                }
            }None
        }
        if !matches!(self.expressions.get(left.expr),Some(Expr::BVar(_)))||!matches!(self.expressions.get(right.expr),Some(Expr::BVar(_))){return false;}
        let Some((a,x))=resolve(self,left,remaining)else{return false;};let Some((b,y))=resolve(self,right,remaining)else{return false;};
        if a!=b||x!=y{return false;}
        let ledger=self.checked_binding_lineage.borrow();let Some(Some(w))=ledger.get(&a.id())else{return false;};
        if !matches!(&w.domain,TypeValue::Sort(_))&&!matches!(&w.domain,TypeValue::Term(t) if matches!(self.expressions.get(t.expr),Some(Expr::Sort(_)))){return false;}
        let Some(last)=w.protected_prefix.len().checked_sub(1)else{return false;};
        if fresh_local(last)!=Some(x)||context.len()<w.protected_prefix.len()||w.protected_prefix.last()!=Some(&w.domain){return false;}
        for(actual,protected)in context.iter().zip(w.protected_prefix.iter()) {
            if !take_step(remaining)||actual!=protected{return false;}
        }
        match &w.domain {
            TypeValue::Sort(_)=>{},
            TypeValue::Term(domain)=>{
                if self.checked_binding_lineage.borrow().get(&domain.env.id()).is_some_and(Option::is_none){return false;}
                // These syntax forms have no captured term variables. Other
                // declared domains retain the existing complete USED check.
                if !matches!(self.expressions.get(domain.expr),Some(Expr::Sort(_)|Expr::Const{..}))&&!self.source_used_capture_authority_available(domain,remaining){return false;}
            },TypeValue::Pi{..}=>return false,
        }
        true
    }

    /// Validate declaration parameter annotations in the one actual typed
    /// telescope. Each introduction follows complete domain formation and
    /// comparison of every original annotation under its own universes.
    fn checked_parameter_telescope(
        &self, expected:&[ExprId], alternatives:&[&[ExprId]], remaining:&mut usize,
    )->Option<(EnvFrame,Vec<TypeValue>)> {
        if alternatives.iter().any(|a|a.len()!=expected.len()){return None;}
        let checker=self.strict_certificate_probe();
        let mut frame=EnvFrame::empty();let mut context=Vec::new();
        for (index,expression) in expected.iter().enumerate() {
            let source=checker.closure(*expression,frame.clone());
            if !checker.source_used_capture_authority_available(&source,remaining)
                ||checker.shared_strict_source_sort(&source,&context,remaining).is_none(){return None;}
            let domain=TypeValue::Term(source);
            let mut completed=std::collections::HashSet::new();completed.insert(*expression);
            for annotations in alternatives {
                let actual=annotations[index];if !completed.insert(actual){continue;}
                let actual=checker.closure(actual,frame.clone());
                if !checker.source_used_capture_authority_available(&actual,remaining)
                    ||checker.shared_strict_source_sort(&actual,&context,remaining).is_none(){return None;}
                if !crate::convert::convert_with_policy_in_context_remaining(&checker,&domain,&TypeValue::Term(actual),checker.delta_policy,context.len(),&context,remaining).is_proven(){return None;}
            }
            let Some(free)=fresh_local(context.len())else{return None;};
            let Some(next)=frame.extend_free_paid(free,remaining)else{return None;};
            if !take_step(remaining){return None;}context.push(domain.clone());
            checker.retain_checked_binding(&next,domain,&context);frame=next;
        }
        Some((frame,context))
    }

    pub(crate) fn checked_parameter_telescope_equivalence(
        &self, expected:&[ExprId], alternatives:&[&[ExprId]], remaining:&mut usize,
    )->bool {
        self.checked_parameter_telescope(expected,alternatives,remaining).is_some()
    }

    /// Form each original field as a proposition in the actual checked
    /// constructor telescope. The private context is carried from parameter
    /// formation, and proof fields introduce their own checked local once.
    pub(crate) fn checked_prop_field_telescope(
        &self, expected:&[ExprId], actual:&[ExprId], fields:&[ExprId],
        remaining:&mut usize,
    )->bool {
        let Some((mut frame,mut context))=self.checked_parameter_telescope(expected,&[actual],remaining)else{return false;};
        let checker=self.strict_certificate_probe();
        for expression in fields {
            let source=checker.closure(*expression,frame.clone());
            if !checker.source_used_capture_authority_available(&source,remaining){return false;}
            let Some(level)=checker.shared_strict_source_sort(&source,&context,remaining)else{return false;};
            if !crate::level::level_equal_with_remaining(level,LevelTerm::Zero,remaining).is_proven(){return false;}
            let Some(free)=fresh_local(context.len())else{return false;};
            let Some(next)=frame.extend_free_paid(free,remaining)else{return false;};
            if !take_step(remaining){return false;}
            let domain=TypeValue::Term(source);context.push(domain.clone());
            checker.retain_checked_binding(&next,domain,&context);frame=next;
        }
        true
    }

    pub(crate) fn source_capture_owner(&self,frame:&EnvFrame,index:u64,remaining:&mut usize)->Option<EnvFrame> {
        if !take_step(remaining){return None;}
        if let Some((_,owner))=self.source_capture_bindings.borrow().get(&(frame.id(),index)) {
            return Some(owner.clone());
        }
        // The lookup step prepays inspection of the current physical node.
        // Binary ancestor links perform one actual immutable hop per set bit.
        let cost=usize::try_from(index.count_ones()).ok()?;
        if *remaining<cost{return None;}*remaining-=cost;
        let owner=frame.binding_frame(index)?;
        if self.source_capture_bindings.borrow().len()<16384 {
            self.source_capture_bindings.borrow_mut().insert((frame.id(),index),(frame.clone(),owner.clone()));
        }
        Some(owner)
    }

    fn source_capture_binding(&self,frame:&EnvFrame,index:u64,remaining:&mut usize)->Option<(u64,EnvBinding)> {
        let owner=self.source_capture_owner(frame,index,remaining)?;
        let binding=owner.lookup_binding_ref(0)?;
        match binding {
            EnvBinding::NatLit(value)=>{
                if *remaining<value.limb_count(){return None;}*remaining-=value.limb_count();
            },
            EnvBinding::Neutral(_)=>return None,
            _=>{},
        }
        Some((owner.id(),binding.clone()))
    }

    // Gather all actual capture dependencies, then recursively their checked
    // source domains. Numeric Free IDs alone supply no typing authority.
    fn owned_goal_dependencies(&self, source: &Closure, expected: &Closure,
        context: &[TypeValue], remaining: &mut usize) -> Option<Vec<OwnedGoalDependency>> {
        let mut pending=vec![(source.clone(),false),(expected.clone(),false)];
        let mut active=std::collections::HashSet::new();
        let mut complete=std::collections::HashSet::new();
        let mut nodes=std::collections::HashSet::new();
        let mut dependencies=Vec::new();
        while let Some((term,finish))=pending.pop() {
            if finish {active.remove(&term);complete.insert(term);continue;}
            if !take_step(remaining){return None;}
            if complete.contains(&term){continue;}
            if !active.insert(term.clone()){return None;}
            let support=self.complete_source_support(term.expr,remaining)?;
            pending.push((term.clone(),true));
            for index in support {
                let (node,binding)=self.source_capture_binding(&term.env,index,remaining)?;
                let free=match &binding {EnvBinding::Free(free)=>Some(*free),_=>None};
                // Any captured source binder may supply its checked declared
                // domain during the completed derivation, including a stored
                // value closure. Retain that premise and recursively its scope.
                let witness=self.checked_binding_lineage.borrow().get(&node)?.as_ref()?.clone();
                let domain=self.checked_type_of_bound_source(&term.env,index,context)?;
                if nodes.insert(node) {
                    if dependencies.len()>=128{return None;}
                    match &domain {
                        TypeValue::Term(value)=>pending.push((value.clone(),false)),
                        TypeValue::Sort(_)=>{},
                        TypeValue::Pi{..}=>return None,
                    }
                    dependencies.push(OwnedGoalDependency{free,node,index,owner:term.env.clone(),witness,domain});
                }
                match binding {
                    EnvBinding::Closure(value)=>pending.push((value,false)),
                    EnvBinding::NatLit(value)=>{
                        if *remaining<value.limb_count(){return None;}*remaining-=value.limb_count();
                    },
                    EnvBinding::Free(_)=>{},
                    EnvBinding::Neutral(_)=>return None,
                }
            }
        }
        Some(dependencies)
    }

    // Rename a completed checking judgment with one injective correspondence
    // shared by its subject, expected type, and every used declared domain.
    // This rule supplies no conversion equality between distinct actual Frees.
    fn joint_owned_goal_transport(&self, previous:&OwnedLambdaGoal, source:&Closure,
        expected:&Closure, current:&[OwnedGoalDependency], remaining:&mut usize)->bool {
        let old:HashMap<_,_>=previous.dependencies.iter().map(|d|(d.node,d)).collect();
        let new:HashMap<_,_>=current.iter().map(|d|(d.node,d)).collect();
        let mut owners=HashMap::new();let mut reverse_owners=HashMap::new();
        let mut frees=HashMap::new();let mut reverse_frees=HashMap::new();
        let mut pending=vec![(previous.source.clone(),source.clone()),(previous.expected.clone(),expected.clone())];
        let mut complete=std::collections::HashSet::new();
        while let Some((a,b))=pending.pop() {
            if !take_step(remaining){return false;}
            if !complete.insert((a.clone(),b.clone())){continue;}
            if !Self::exact_source_levels(&a.levels,&b.levels,remaining){return false;}
            let Some(support)=self.complete_paired_source_support(a.expr,b.expr,remaining)else{return false;};
            for (x,y) in support {
                let Some((on,ob))=self.source_capture_binding(&a.env,x,remaining)else{return false;};
                let Some((nn,nb))=self.source_capture_binding(&b.env,y,remaining)else{return false;};
                let (Some(od),Some(nd))=(old.get(&on),new.get(&nn))else{return false;};
                if owners.get(&on).is_some_and(|n|*n!=nn)||reverse_owners.get(&nn).is_some_and(|n|*n!=on){return false;}
                if owners.insert(on,nn).is_none(){
                    reverse_owners.insert(nn,on);
                    if self.checked_binding_lineage.borrow().get(&on)!=Some(&Some(od.witness.clone()))
                        ||self.checked_binding_lineage.borrow().get(&nn)!=Some(&Some(nd.witness.clone())){return false;}
                    match (&od.domain,&nd.domain) {
                        (TypeValue::Term(u),TypeValue::Term(v))=>pending.push((u.clone(),v.clone())),
                        (TypeValue::Sort(u),TypeValue::Sort(v)) if u==v=>{},
                        _=>return false,
                    }
                }
                match (ob,nb) {
                    (EnvBinding::Closure(u),EnvBinding::Closure(v))=>pending.push((u,v)),
                    (EnvBinding::Free(u),EnvBinding::Free(v))=>{
                        if od.free!=Some(u)||nd.free!=Some(v){return false;}
                        if frees.get(&u).is_some_and(|f|*f!=v)||reverse_frees.get(&v).is_some_and(|f|*f!=u){return false;}
                        frees.insert(u,v);reverse_frees.insert(v,u);
                    },
                    (EnvBinding::NatLit(u),EnvBinding::NatLit(v))=>{
                        let cost=u.limb_count().max(v.limb_count());
                        if *remaining<cost{return false;}*remaining-=cost;
                        if u!=v{return false;}
                    },
                    _=>return false,
                }
            }
        }
        owners.len()==old.len()&&reverse_owners.len()==new.len()
    }

    // Pure complete AST shapes select candidates only. External and intrinsic
    // BVar indices intentionally share a hint; the subsequent full paired
    // source derivation checks offsets, actual captures, and binder positions.
    // One paid acyclic postorder produces a complete canonical shape and
    // exact lexical support. It produces no occurrence pattern, captured
    // owner correspondence, universe formation or typing judgment.
    fn complete_lambda_shape_only(&self,expression:ExprId,remaining:&mut usize)->Option<u64>{
        let mut pending=vec![(expression,false)];let mut active=std::collections::HashSet::new();
        let mut complete=HashMap::new();let mut supports=HashMap::<ExprId,Vec<u64>>::new();
        while let Some((id,finish))=pending.pop(){
            if !take_step(remaining){return None;}
            if !finish {
                if let Some(shape)=self.lambda_shape_ids.borrow().get(&id).copied()
                    && let Some(support)=self.source_support.borrow().get(&id).cloned(){
                    complete.insert(id,shape);supports.insert(id,support);continue;
                }
                if complete.contains_key(&id){continue;}if !active.insert(id){return None;}
                pending.push((id,true));
                match self.expressions.get(id)? {
                    Expr::App{fun,arg}=>{pending.push((*arg,false));pending.push((*fun,false));},
                    Expr::Lam{domain,body}|Expr::Pi{domain,body}=>{pending.push((*body,false));pending.push((*domain,false));},
                    Expr::Let{ty,value,body}=>{pending.push((*body,false));pending.push((*value,false));pending.push((*ty,false));},
                    Expr::Proj{structure,..}=>pending.push((*structure,false)),_=>{},
                }
            }else{
                let node=self.expressions.get(id)?;
                let key=match node {
                    Expr::BVar(_)=>(0,0,0,0,0),Expr::Const{..}=>(1,id.0,0,0,0),Expr::Sort(_)=>(2,id.0,0,0,0),Expr::NatLit(_)=>(3,id.0,0,0,0),Expr::StrLit(_)=>(4,id.0,0,0,0),
                    Expr::App{fun,arg}=>(5,*complete.get(fun)?,*complete.get(arg)?,0,0),Expr::Lam{domain,body}=>(6,*complete.get(domain)?,*complete.get(body)?,0,0),Expr::Pi{domain,body}=>(7,*complete.get(domain)?,*complete.get(body)?,0,0),Expr::Let{ty,value,body}=>(8,*complete.get(ty)?,*complete.get(value)?,*complete.get(body)?,0),Expr::Proj{type_name,index,structure}=>(9,type_name.0,*index,*complete.get(structure)?,0),
                };
                let cached_support=self.source_support.borrow().get(&id).cloned();
                let support=if let Some(support)=cached_support{support}else{
                    let mut support=std::collections::BTreeSet::new();
                    let mut add=|child:ExprId,binder:bool|->Option<()> {
                        for index in supports.get(&child)? {
                            // Keep the existing exact-support union/shift charge.
                            if !take_step(remaining){return None;}
                            if !binder || *index>0 {
                                support.insert(if binder{index-1}else{*index});
                                if support.len()>128{return None;}
                            }
                        }
                        Some(())
                    };
                    match node {
                        Expr::BVar(index)=>{support.insert(*index);},
                        Expr::App{fun,arg}=>{add(*fun,false)?;add(*arg,false)?;},
                        Expr::Lam{domain,body}|Expr::Pi{domain,body}=>{add(*domain,false)?;add(*body,true)?;},
                        Expr::Let{ty,value,body}=>{add(*ty,false)?;add(*value,false)?;add(*body,true)?;},
                        Expr::Proj{structure,..}=>{add(*structure,false)?;},
                        Expr::Const{..}|Expr::Sort(_)|Expr::NatLit(_)|Expr::StrLit(_)=>{},
                    }
                    support.into_iter().collect::<Vec<_>>()
                };
                if let Some(Expr::Pi{domain,body})=self.expressions.get(id){self.discover_completed_pi_lift(*domain,*body,supports.get(domain)?,supports.get(body)?,remaining);}
                let known=self.lambda_shape_nodes.borrow().get(&key).copied();
                let shape=if let Some(shape)=known{shape}else{if !take_step(remaining){return None;}let mut nodes=self.lambda_shape_nodes.borrow_mut();if nodes.len()>=32768{return None;}let shape=nodes.len()as u64;nodes.insert(key,shape);shape};
                if !take_step(remaining){return None;}
                if self.lambda_shape_ids.borrow().len()<32768{self.lambda_shape_ids.borrow_mut().insert(id,shape);}
                if self.source_support.borrow().len()<8192{self.source_support.borrow_mut().insert(id,support.clone());}
                active.remove(&id);complete.insert(id,shape);supports.insert(id,support);
            }
        }
        complete.remove(&expression)
    }
    fn lambda_candidate_hint(&self,expression:ExprId,remaining:&mut usize)->Option<u64> {
        let mut pending=vec![(expression,false)];let mut active=std::collections::HashSet::new();
        let mut complete=HashMap::new();
        let mut supports=HashMap::<ExprId,Vec<u64>>::new();
        let mut patterns=HashMap::<ExprId,u64>::new();
        while let Some((id,finish))=pending.pop() {
            if !take_step(remaining){return None;}
            if !finish {
                if let Some(shape)=self.lambda_shape_ids.borrow().get(&id).copied()
                    && let Some((pattern,support))=self.source_syntax_patterns.borrow().get(&id).cloned(){
                    complete.insert(id,shape);supports.insert(id,support);patterns.insert(id,pattern);continue;
                }
                if complete.contains_key(&id){continue;}
                if !active.insert(id){return None;}
                pending.push((id,true));
                match self.expressions.get(id)? {
                    Expr::App{fun,arg}=>{pending.push((*arg,false));pending.push((*fun,false));},
                    Expr::Lam{domain,body}|Expr::Pi{domain,body}=>{pending.push((*body,false));pending.push((*domain,false));},
                    Expr::Let{ty,value,body}=>{pending.push((*body,false));pending.push((*value,false));pending.push((*ty,false));},
                    Expr::Proj{structure,..}=>pending.push((*structure,false)),
                    _=>{},
                }
            }else{
                let key=match self.expressions.get(id)? {
                    Expr::BVar(_)=>(0,0,0,0,0),
                    Expr::Const{..}=>(1,id.0,0,0,0),
                    Expr::Sort(_)=>(2,id.0,0,0,0),
                    Expr::NatLit(_)=>(3,id.0,0,0,0),
                    Expr::StrLit(_)=>(4,id.0,0,0,0),
                    Expr::App{fun,arg}=>(5,*complete.get(fun)?,*complete.get(arg)?,0,0),
                    Expr::Lam{domain,body}=>(6,*complete.get(domain)?,*complete.get(body)?,0,0),
                    Expr::Pi{domain,body}=>(7,*complete.get(domain)?,*complete.get(body)?,0,0),
                    Expr::Let{ty,value,body}=>(8,*complete.get(ty)?,*complete.get(value)?,*complete.get(body)?,0),
                    Expr::Proj{type_name,index,structure}=>(9,type_name.0,*index,*complete.get(structure)?,0),
                };
                // The same paid complete syntax traversal also establishes
                // exact lexical support. Binder offsets and each support union
                // retain their original finite charge; shape IDs alone never
                // stand in for support or actual captured ownership.
                let cached_support=self.source_support.borrow().get(&id).cloned();
                let charge_slots=cached_support.is_some();
                let support=if let Some(support)=cached_support {support}else{
                let mut support=std::collections::BTreeSet::new();
                let mut add=|child:ExprId,binder:bool|->Option<()> {
                    for index in supports.get(&child)? {
                        if !take_step(remaining){return None;}
                        if !binder || *index>0 {
                            support.insert(if binder{index-1}else{*index});
                            if support.len()>128{return None;}
                        }
                    }
                    Some(())
                };
                match self.expressions.get(id)? {
                    Expr::BVar(index)=>{support.insert(*index);},
                    Expr::App{fun,arg}=>{add(*fun,false)?;add(*arg,false)?;},
                    Expr::Lam{domain,body}|Expr::Pi{domain,body}=>{add(*domain,false)?;add(*body,true)?;},
                    Expr::Let{ty,value,body}=>{add(*ty,false)?;add(*value,false)?;add(*body,true)?;},
                    Expr::Proj{structure,..}=>{add(*structure,false)?;},
                    Expr::Const{..}|Expr::Sort(_)|Expr::NatLit(_)|Expr::StrLit(_)=>{},
                }
                support.into_iter().collect::<Vec<_>>()
                };
                if self.source_support.borrow().len()<8192{self.source_support.borrow_mut().insert(id,support.clone());}
                // A compositional lexical pattern retains every occurrence
                // map. Slot zero is reserved for the newly introduced binder;
                // external slots are one plus their ordered parent support rank.
                let mut slots=|child:ExprId,binder:bool|->Option<Vec<u64>> {
                    supports.get(&child)?.iter().map(|index|{
                        // Cold support unions already paid each child entry.
                        // A cached support does not prepay a new occurrence map.
                        if charge_slots && !take_step(remaining){return None;}
                        if binder && *index==0 {Some(0)}else{
                            let parent_index=if binder{index-1}else{*index};
                            support.binary_search(&parent_index).ok().map(|rank|rank as u64+1)
                        }
                    }).collect()
                };
                let pattern_key=match self.expressions.get(id)? {
                    Expr::BVar(_)=>((0,0,0,0,0),vec![]),
                    Expr::Const{..}=>((1,id.0,0,0,0),vec![]),
                    Expr::Sort(_)=>((2,id.0,0,0,0),vec![]),
                    Expr::NatLit(_)=>((3,id.0,0,0,0),vec![]),
                    Expr::StrLit(_)=>((4,id.0,0,0,0),vec![]),
                    Expr::App{fun,arg}=>((5,*patterns.get(fun)?,*patterns.get(arg)?,0,0),vec![slots(*fun,false)?,slots(*arg,false)?]),
                    Expr::Lam{domain,body}=>((6,*patterns.get(domain)?,*patterns.get(body)?,0,0),vec![slots(*domain,false)?,slots(*body,true)?]),
                    Expr::Pi{domain,body}=>((7,*patterns.get(domain)?,*patterns.get(body)?,0,0),vec![slots(*domain,false)?,slots(*body,true)?]),
                    Expr::Let{ty,value,body}=>((8,*patterns.get(ty)?,*patterns.get(value)?,*patterns.get(body)?,0),vec![slots(*ty,false)?,slots(*value,false)?,slots(*body,true)?]),
                    Expr::Proj{type_name,index,structure}=>((9,type_name.0,*index,*patterns.get(structure)?,0),vec![slots(*structure,false)?]),
                };
                if let Some(Expr::Pi{domain,body})=self.expressions.get(id){self.discover_completed_pi_lift(*domain,*body,supports.get(domain)?,supports.get(body)?,remaining);}
                let pattern_known=self.source_syntax_pattern_nodes.borrow().get(&pattern_key).copied();
                let pattern=if let Some(pattern)=pattern_known {pattern}else{
                    let mut nodes=self.source_syntax_pattern_nodes.borrow_mut();
                    if nodes.len()>=32768{return None;}
                    let pattern=nodes.len() as u64;nodes.insert(pattern_key,pattern);pattern
                };
                if self.source_syntax_patterns.borrow().len()<32768 {
                    self.source_syntax_patterns.borrow_mut().insert(id,(pattern,support.clone()));
                }
                supports.insert(id,support);patterns.insert(id,pattern);
                let known=self.lambda_shape_nodes.borrow().get(&key).copied();
                let shape=if let Some(shape)=known{shape}else{
                    let mut nodes=self.lambda_shape_nodes.borrow_mut();
                    if nodes.len()>=32768{return None;}
                    let shape=nodes.len() as u64;nodes.insert(key,shape);shape
                };
                if self.lambda_shape_ids.borrow().len()<32768 {self.lambda_shape_ids.borrow_mut().insert(id,shape);}
                active.remove(&id);complete.insert(id,shape);
            }
        }
        complete.remove(&expression)
    }

    // Candidate-only: complete facts of one borrowed immutable expression table.
    fn paired_lambda_hint(&self,left:ExprId,right:ExprId,remaining:&mut usize)->bool {
        const COMPLETE_HINT_CAP:usize=4096;
        if !take_step(remaining){return false;}
        if let Some(completed)=self.paired_lambda_hint_facts.borrow().get(&(left,right)).copied(){return completed;}
        type Pair=(ExprId,ExprId);
        let mut frames:Vec<(Pair,Vec<Pair>,usize)>=Vec::new();
        let mut active=std::collections::HashSet::new();
        let mut pair=(left,right);
        loop {
            if !take_step(remaining){return false;}
            let cached=self.paired_lambda_hint_facts.borrow().get(&pair).copied();
            let mut result=if let Some(fact)=cached {Some(fact)} else if pair.0==pair.1 {Some(true)} else {
                if !active.insert(pair){return false;}
                let children=match(self.expressions.get(pair.0),self.expressions.get(pair.1)) {
                    (Some(Expr::BVar(_)),Some(Expr::BVar(_)))=>Some(vec![]),
                    (Some(Expr::App{fun:x,arg:y}),Some(Expr::App{fun:u,arg:v}))=>Some(vec![(*x,*u),(*y,*v)]),
                    (Some(Expr::Lam{domain:x,body:y}),Some(Expr::Lam{domain:u,body:v}))|
                    (Some(Expr::Pi{domain:x,body:y}),Some(Expr::Pi{domain:u,body:v}))=>Some(vec![(*x,*u),(*y,*v)]),
                    (Some(Expr::Let{ty:x,value:y,body:z}),Some(Expr::Let{ty:u,value:v,body:w}))=>Some(vec![(*x,*u),(*y,*v),(*z,*w)]),
                    (Some(Expr::Proj{type_name:x,index:y,structure:z}),Some(Expr::Proj{type_name:u,index:v,structure:w}))if x==u&&y==v=>Some(vec![(*z,*w)]),
                    _=>None,
                };
                match children {
                    None=>Some(false),
                    Some(children)if children.is_empty()=>Some(true),
                    Some(children)=>{let next=children[0];frames.push((pair,children,1));pair=next;continue;},
                }
            };
            loop {
                let completed=result.take().expect("finished pure syntax child");
                active.remove(&pair);
                if pair.0!=pair.1 {
                    let mut facts=self.paired_lambda_hint_facts.borrow_mut();
                    if facts.len()<COMPLETE_HINT_CAP {facts.insert(pair,completed);}
                }
                let Some((parent,children,next))=frames.pop()else{return completed;};
                if completed&&next<children.len() {
                    let child=children[next];frames.push((parent,children,next+1));pair=child;break;
                }
                pair=parent;result=Some(completed);
            }
        }
    }

    fn reuse_owned_lambda_goal(&self, expression: ExprId, source: &Closure,
        expected: &Closure, context: &[TypeValue], remaining: &mut usize) -> bool {
        let mut retained=self.owned_lambda_goals.borrow().get(&expression).cloned().unwrap_or_default();
        if matches!(self.expressions.get(expression),Some(Expr::App{..}))
            && let Some((pattern,_))=self.source_syntax_patterns.borrow().get(&expression)
            && let Some(candidates)=self.owned_application_patterns.borrow().get(&(*pattern,expected.expr)) {
            for proof in candidates {if proof.source.expr!=expression {retained.push(proof.clone());}}
        }
        if !self.owned_lambda_shape_domains.borrow().is_empty()
            && let Some(Expr::Lam{domain,..})=self.expressions.get(expression) {
            let bound_goal=matches!(self.expressions.get(expected.expr),Some(Expr::BVar(_)));
            // The coarse availability gate avoids compiling an unused shape.
            let goals=[Some(expected.expr),None];
            let available=self.owned_lambda_shape_domains.borrow();
            let mut has_candidate=false;
            for goal in goals {if goal.is_none()&&!bound_goal{continue;}if !take_step(remaining){return false;}if available.contains_key(&(*domain,goal)){has_candidate=true;break;}}
            drop(available);
            if has_candidate && let Some(shape)=self.complete_lambda_shape_only(expression,remaining){
                let shapes=self.owned_lambda_shapes.borrow();
                for goal in goals {
                    if goal.is_none()&&!bound_goal{continue;}
                    if !take_step(remaining){return false;}
                    if let Some(proofs)=shapes.get(&(*domain,goal,shape)) {
                        for proof in proofs {
                            if !take_step(remaining){return false;}
                            if !retained.iter().any(|old|old.source==proof.source&&old.expected==proof.expected){retained.push(proof.clone());}
                        }
                    }
                }
            }
        }
        #[cfg(feature="diagnostics")]
        if expression.0>=6900 && std::env::var_os("NUCLEUS_TRACE_LAST_LAMBDAS").is_some(){eprintln!("LAST_LAMBDA_CANDIDATES:expr={expression:?}:target={:?}:context={}:remaining={remaining}:candidates={:?}",expected.expr,context.len(),retained.iter().map(|p|p.source.expr).collect::<Vec<_>>());}
        #[cfg(feature="diagnostics")]
        if retained.is_empty() && expression.0>=6900 && std::env::var_os("NUCLEUS_TRACE_LAST_LAMBDAS").is_some() {
            if let Some(hint)=self.lambda_shape_ids.borrow().get(&expression).copied() {
                let missed:Vec<_>=self.owned_lambda_shapes.borrow().iter().filter(|((_,goal,shape),_)|*goal==Some(expected.expr)&&*shape==hint).flat_map(|((domain,_,_),ps)|ps.iter().map(|p|(*domain,p.source.expr))).collect();
                eprintln!("LAST_LAMBDA_OTHER_DOMAINS:expr={expression:?}:target={:?}:missed={missed:?}",expected.expr);
            }
        }
        if retained.is_empty(){return false;}
        let initial=*remaining;
        let Some(current)=self.owned_goal_dependencies(source,expected,context,remaining)else{return false;};
        let after_dependencies=*remaining;
        for previous in retained {
            if self.joint_owned_goal_transport(&previous,source,expected,&current,remaining){
                if context.len()<=128&&context.iter().all(|ty|matches!(ty,TypeValue::Term(_)))
                    &&self.formed_lambda_goals.borrow().len()<8192 {
                    let mut dependencies=current.clone();dependencies.extend(previous.dependencies.clone());
                    self.formed_lambda_goals.borrow_mut().insert((expression,source.env.id(),TypeValue::Term(expected.clone()),context.to_vec()),dependencies);
                }
                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_OWNED_GOALS").is_some(){eprintln!("OWNED_GOAL_JOINT_HIT:expr={expression:?}:previous={:?}:target={:?}:ctx={}:remaining={remaining}:dependencies={}:dependency_cost={}:joint_cost={}",previous.source.expr,expected.expr,context.len(),current.len(),initial-after_dependencies,after_dependencies-*remaining);}
                return true;
            }
        }
        #[cfg(feature="diagnostics")]
        if expression.0>=6900 && std::env::var_os("NUCLEUS_TRACE_LAST_LAMBDAS").is_some(){eprintln!("LAST_LAMBDA_MATCH_FAILED:expr={expression:?}:target={:?}:remaining={remaining}:cost={}",expected.expr,initial-*remaining);}
        false
    }

    fn exact_source_levels(left: &LevelSubstitution, right: &LevelSubstitution, remaining: &mut usize) -> bool {
        let mut left_entries = left.entries();
        let mut right_entries = right.entries();
        loop {
            let pair = (left_entries.next(), right_entries.next());
            match pair {
                (None, None) => return true,
                (Some((a, x)), Some((b, y))) if a == b => {
                    let mut pending = vec![(x, y)];
                    while let Some((x, y)) = pending.pop() {
                        if !take_step(remaining) { return false }
                        match (x, y) {
                            (LevelTerm::Zero, LevelTerm::Zero) => {}
                            (LevelTerm::Param(a), LevelTerm::Param(b)) => {
                                let cost = a.len().max(b.len());
                                if *remaining < cost { return false }
                                *remaining -= cost;
                                if a != b { return false }
                            }
                            (LevelTerm::Succ(a), LevelTerm::Succ(b)) => pending.push((a, b)),
                            (LevelTerm::Max(a, b), LevelTerm::Max(c, d))
                            | (LevelTerm::IMax(a, b), LevelTerm::IMax(c, d)) => {
                                pending.push((b, d)); pending.push((a, c));
                            }
                            _ => return false,
                        }
                    }
                }
                _ => return false,
            }
        }
    }

    pub(crate) fn exact_source_capture_identity(
        &self, left: &Closure, right: &Closure, remaining: &mut usize,
    ) -> bool {
        enum Capture { Free(FreeId,u64), Closure(Closure), Nat(crate::nat::BigNat) }
        fn resolve(checker: &TypeChecker<'_>, term: &Closure, index: u64, remaining: &mut usize) -> Option<Capture> {
            let mut frame = term.env.clone();
            let mut index = index;
            let mut seen = std::collections::HashSet::new();
            loop {
                let cost = usize::try_from(index).ok()?.checked_add(1)?;
                if *remaining < cost { return None }
                *remaining -= cost;
                if !seen.insert((frame.id(), index)) { return None }
                let owner=frame.binding_frame(index)?;
                match owner.lookup_binding_ref(0)? {
                    EnvBinding::Free(free) => return Some(Capture::Free(*free,owner.id())),
                    EnvBinding::Neutral(Neutral { head: NeutralHead::Free(free, Some(original)), spine }) if spine.is_empty() => {
                        if !matches!(original.lookup_binding_ref(0),Some(EnvBinding::Free(actual)) if actual==free){return None;}
                        return Some(Capture::Free(*free,original.id()));
                    },
                    EnvBinding::Neutral(_) => return None,
                    EnvBinding::NatLit(number) => {
                        if *remaining < number.limb_count() { return None }
                        *remaining -= number.limb_count();
                        return Some(Capture::Nat(number.clone()));
                    }
                    EnvBinding::Closure(value) => {
                        let next = value.clone();
                        match checker.expressions.get(next.expr)? {
                            Expr::BVar(next_index) => { frame = next.env; index = *next_index; }
                            _ => return Some(Capture::Closure(next)),
                        }
                    }
                }
            }
        }
        // Root BVars refer to actual stored values, outside any virtual
        // AST binder. Their stored closures own both scope and universes.
        // Intrinsic paired AST BVars remain untouched by this normalization.
        fn root_source(checker: &TypeChecker<'_>, mut source: Closure, remaining: &mut usize) -> Option<Closure> {
            let mut seen = std::collections::HashSet::new();
            let mut retained = Vec::new();
            while let Expr::BVar(index) = checker.expressions.get(source.expr)? {
                if !take_step(remaining) { return None; }
                let cost = usize::try_from(*index).ok()?.checked_add(1)?;
                if *remaining < cost { return None; }
                *remaining -= cost;
                let key = (source.expr, source.env.id(), source.levels.identity());
                if !seen.insert(key) { return None; }
                let next = match source.env.lookup_binding_ref(*index)? {
                    EnvBinding::Closure(actual) => actual.clone(),
                    EnvBinding::Neutral(Neutral { head: NeutralHead::Free(_, _), spine }) if spine.is_empty() => break,
                    EnvBinding::Neutral(_) => return None,
                    EnvBinding::Free(_) | EnvBinding::NatLit(_) => break,
                };
                retained.push(source);
                source = next;
            }
            Some(source)
        }

        // Level allocation identities are retained by the owning Closure
        // pairs; no recursive LevelTerm hashing or dangling pointer keys.
        let key = |a: &Closure, b: &Closure| (a.expr, a.env.id(), a.levels.identity(), b.expr, b.env.id(), b.levels.identity());
        let mut pending = vec![(left.clone(), right.clone(), false)];
        let mut active = std::collections::HashSet::new();
        let mut complete = std::collections::HashSet::new();
        let mut retained = Vec::new();
        while let Some((a, b, finish)) = pending.pop() {
            #[cfg(feature = "diagnostics")]
            if !finish && std::env::var("NUCLEUS_TRACE_SOURCE_CAPTURE_TARGET").ok()
                .and_then(|value| value.parse::<u64>().ok()) == Some(a.expr.0)
            {
                use std::sync::atomic::{AtomicUsize, Ordering};
                static TARGETS: AtomicUsize = AtomicUsize::new(0);
                if TARGETS.fetch_add(1, Ordering::Relaxed) < 16 {
                    eprintln!("NUCLEUS_SOURCE_CAPTURE_TARGET:left={a:?}:right={b:?}:remaining={remaining}:support_cached={}", self.source_support.borrow().contains_key(&a.expr));
                }
            }
            let (a, b) = if finish { (a, b) } else {
                let Some(a) = root_source(self, a, remaining) else { return false; };
                let Some(b) = root_source(self, b, remaining) else { return false; };
                (a, b)
            };
            let pair = key(&a, &b);
            if finish { active.remove(&pair); complete.insert(pair); retained.push((a, b)); continue }
            if !take_step(remaining)
                || !Self::exact_source_levels(&a.levels, &b.levels, remaining) { return false }
            if complete.contains(&pair) { continue }
            if !active.insert(pair) { return false }
            let Some(support) = self.complete_paired_source_support(a.expr, b.expr, remaining) else { return false };
            pending.push((a.clone(), b.clone(), true));
            for (left_index, right_index) in support {
                let Some(lhs) = resolve(self, &a, left_index, remaining) else { return false };
                let Some(rhs) = resolve(self, &b, right_index, remaining) else { return false };
                match (lhs, rhs) {
                    // Exact capture identity is independent of contextual alpha
                    // conversion. A lexical Free needs its same immutable
                    // owner; equal numeric IDs do not pair independent scopes.
                    (Capture::Free(x,owner_x), Capture::Free(y,owner_y))
                        if x==y&&owner_x==owner_y=>{},
                    (Capture::Nat(x), Capture::Nat(y)) => {
                        let cost = x.limb_count().max(y.limb_count());
                        if *remaining < cost { return false }
                        *remaining -= cost;
                        if x != y { return false }
                    }
                    (Capture::Closure(x), Capture::Closure(y)) => pending.push((x, y, false)),
                    _ => return false,
                }
            }
        }
        true
    }

    pub fn convert(&self, left: &TypeValue, right: &TypeValue, budget: usize) -> Judgment<()> {
        crate::convert::convert_with_policy_at_depth(
            self,
            left,
            right,
            budget,
            self.delta_policy,
            0,
        )
    }

    pub fn convert_with_policy(
        &self,
        left: &TypeValue,
        right: &TypeValue,
        budget: usize,
        policy: crate::convert::DeltaPolicy,
    ) -> Judgment<()> {
        crate::convert::convert_with_policy(self, left, right, budget, policy)
    }

    /// Prove a narrow grammar of ambient-independent expression subjects.
    /// Incomplete traversals retain only individually established child facts.
    fn closed_spine_eligible(&self, expression: ExprId, mut budget: usize) -> Option<bool> {
        let mut facts = self.closed_spine_eligibility.borrow_mut();
        if let Some(answer) = facts.get(&expression) {
            return Some(*answer);
        }
        let mut stack = vec![(expression, false)];
        let mut active = std::collections::HashSet::new();
        while let Some((current, returning)) = stack.pop() {
            if facts.contains_key(&current) {
                continue;
            }
            if !take_step(&mut budget) {
                return None;
            }
            let node = self.expressions.get(current)?;
            if returning {
                let Expr::App { fun, arg } = node else { return None };
                let eligible = *facts.get(fun)? && *facts.get(arg)?;
                facts.insert(current, eligible);
                active.remove(&current);
            } else {
                match node {
                    Expr::Const { .. } | Expr::Sort(_) | Expr::NatLit(_) | Expr::StrLit(_) => {
                        facts.insert(current, true);
                    }
                    Expr::App { fun, arg } => {
                        if !active.insert(current) {
                            return None;
                        }
                        stack.push((current, true));
                        stack.push((*arg, false));
                        stack.push((*fun, false));
                    }
                    Expr::BVar(_) | Expr::Lam { .. } | Expr::Pi { .. }
                        | Expr::Let { .. } | Expr::Proj { .. } => {
                        facts.insert(current, false);
                    }
                }
            }
        }
        facts.get(&expression).copied()
    }

    fn infer_in(
        &self,
        expression: ExprId,
        context: &[TypeValue],
        frame: &EnvFrame,
        remaining: &mut usize,
        cache: &mut HashMap<(ExprId, u64), TypeValue>,
    ) -> Judgment<TypeValue> {
        // Closed spines are checked under empty Γ, so their elimination
        // witnesses protect the empty prefix and admit arbitrary extension.
        // Open subjects retain their exact source frame.
        let canonical = self.closed_spine_eligible(expression, (*remaining).min(4096)) == Some(true);
        let empty_frame = EnvFrame::empty();
        let (context, frame) = if canonical { (&[][..], &empty_frame) } else { (context, frame) };
        let key = (expression, frame.id());
        if let Some(value) = cache.get(&key) {
            if canonical && matches!(value, TypeValue::Pi { .. }) {
                return Judgment::unknown("closed-spine-returned-fixed-pi");
            }
            return if take_step(remaining) {
                Judgment::proven(value.clone(), "shared-expression-inference")
            } else {
                Judgment::unknown("type-inference-budget")
            };
        }
        let result = self.infer_uncached(expression, context, frame, remaining, cache);
        // This grammar cannot synthesize an opened lambda Pi. Do not extend
        // cross-scope reuse to that representation if a future rule adds it.
        if canonical && matches!(&result, Judgment::Proven { value: TypeValue::Pi { .. }, .. }) {
            return Judgment::unknown("closed-spine-returned-fixed-pi");
        }
        if let Judgment::Proven { value, .. } = &result {
            cache.insert(key, value.clone());
        }
        result
    }

    #[inline(never)]
    fn infer_uncached(
        &self,
        expression: ExprId,
        context: &[TypeValue],
        frame: &EnvFrame,
        remaining: &mut usize,
        cache: &mut HashMap<(ExprId, u64), TypeValue>,
    ) -> Judgment<TypeValue> {
        if !take_step(remaining) {
            return Judgment::unknown("type-inference-budget");
        }
        let Some(expression_node) = self.expressions.get(expression) else {
            return Judgment::unknown("missing-expression-during-inference");
        };
        match expression_node {
            Expr::Lam{domain,body} => self.infer_lambda_source(expression,domain,body,context,frame,remaining,cache),
            Expr::App{fun,arg} => self.infer_application_source(expression,fun,arg,context,frame,remaining,cache),
            _ => self.infer_other_uncached(expression,expression_node,context,frame,remaining,cache),
        }
    }

    #[inline(never)]
    fn infer_other_uncached(
        &self,
        expression: ExprId,
        expression_node: &Expr,
        context: &[TypeValue],
        frame: &EnvFrame,
        remaining: &mut usize,
        cache: &mut HashMap<(ExprId, u64), TypeValue>,
    ) -> Judgment<TypeValue> {
        match expression_node {
            Expr::Lam{domain,body} => self.infer_lambda_source(expression,domain,body,context,frame,remaining,cache),
            Expr::App{fun,arg} => self.infer_application_source(expression,fun,arg,context,frame,remaining,cache),
            Expr::NatLit(_) => {
                let Some(primitives) = self.environment.nat_primitives() else {
                    return Judgment::unknown("nat-literal-without-qualified-Nat");
                };
                Judgment::proven(
                    TypeValue::Term(self.closure(primitives.type_expr, frame.clone())),
                    "qualified-Nat-literal-type",
                )
            }
            Expr::StrLit(_) => match self.environment.string_literal_type() {
                Some(ty)=>Judgment::proven(TypeValue::Term(self.closure(ty,EnvFrame::empty())),"qualified-native-String-literal-type"),
                None=>Judgment::unknown("string-literal-type-not-qualified"),
            },
            Expr::BVar(index) => {
                if let Some(EnvBinding::NatLit(_)) = frame.lookup(*index) {
                    let Some(nat) = self.environment.nat_primitives() else { return Judgment::unknown("native-nat-binding-without-qualified-Nat"); };
                    return Judgment::proven(TypeValue::Term(self.closure(nat.type_expr,EnvFrame::empty())),"qualified-native-Nat-binding-type");
                }
                let Some(offset) = usize::try_from(*index).ok() else {
                    return Judgment::refuted("unbound-bvar");
                };
                if let Some(checked)=self.checked_type_of_bound_source(
                    frame,*index,context,
                ){
                    return Judgment::proven(checked,"source-checked-lexical-binding");
                }
                if matches!(frame.lookup_binding_ref(*index),Some(EnvBinding::Neutral(Neutral{head:NeutralHead::Free(_,Some(_)),..}))) {
                    return Judgment::unknown("owned-neutral-source-typing-witness-unavailable");
                }
                // Canonical binder transport with an explicit source witness.
                // The checker creates lexical FreeId(k) exactly when opening
                // context entry k. If the captured frame exposes one of these
                // canonical locals, its type is context[k], not necessarily
                // the type of the most recent binder at de Bruijn position k.
                //
                // Crucially, noncanonical source-derived/synthetic IDs still
                // use the original type-inference procedure. Those frames
                // have NOT supplied this exact binder correspondence. This
                // is not an equality between FreeIds or between data terms.
                if std::env::var_os("NUCLEUS_EXPERIMENTAL_CONTEXT_BINDER").is_some()
                    && let Some(EnvBinding::Free(free)) = frame.lookup(*index)
                    && let Ok(canonical_index) = usize::try_from(free.0)
                    && let Some(qualified_type) = context.get(canonical_index)
                {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_CONTEXT_BINDER").is_some() {
                        if context.len().checked_sub(offset + 1) != Some(canonical_index) {
                            use std::sync::atomic::{AtomicUsize, Ordering};
                            static WITNESSES: AtomicUsize = AtomicUsize::new(0);
                            if WITNESSES.fetch_add(1, Ordering::Relaxed) < 80 {
                                eprintln!(
                                    "NUCLEUS_CONTEXT_BINDER_TRANSPORT:expr={expression:?}:bvar={index}:free={free:?}:context={}:frame={}:source_type={qualified_type:?}",
                                    context.len(),frame.id(),
                                );
                            }
                        }
                    }
                    Judgment::proven(qualified_type.clone(), "source-captured-canonical-binder-type")
                } else {
                    context.iter().rev().nth(offset).cloned()
                        .map(|value| Judgment::proven(value, "context-lookup"))
                        .unwrap_or_else(|| Judgment::refuted("unbound-bvar"))
                }
            }
            Expr::Sort(level) => match self.instantiate(*level, *remaining) {
                Ok(level) => Judgment::proven(TypeValue::Sort(succ(level)), "sort-inference"),
                Err(()) => Judgment::unknown("unresolved-sort-level"),
            },
            Expr::Const { name, levels } => {
                let Some(declaration) = self.environment.get(*name) else {
                    return Judgment::refuted("unknown-constant");
                };
                if levels.len() != declaration.level_params.len() {
                    return Judgment::refuted("constant-level-arity");
                }
                let mut substitution = Vec::with_capacity(levels.len());
                for (parameter, level) in declaration.level_params.iter().zip(levels) {
                    let Ok(level) = self.instantiate(*level, *remaining) else {
                        return Judgment::unknown("polymorphic-constant-instantiation");
                    };
                    substitution.push((*parameter, level));
                }
                Judgment::proven(
                    TypeValue::Term(Closure::with_levels(
                        declaration.ty,
                        EnvFrame::empty(),
                        LevelSubstitution::new(substitution),
                    )),
                    "constant-type",
                )
            }
            Expr::Pi { domain, body } => {
                let domain_type = self.infer_in(*domain, context, frame, remaining, cache);
                let domain_sort = match self.sort_level(domain_type, *remaining) {
                    Judgment::Proven { value, .. } => value,
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                };
                let domain_value = TypeValue::Term(self.closure(*domain, frame.clone()));
                let mut extended = context.to_vec();
                extended.push(domain_value);
                let Some(free) = fresh_local(context.len()) else {
                    return Judgment::unknown("binder-depth-overflow");
                };
                let body_frame = self.checked_source_frame(
                    expression, CheckedFrameRole::InferPi, frame,
                    TypeValue::Term(self.closure(*domain,frame.clone())), &extended,
                    CheckedFrameBinding::Free(free),
                );
                let body_type = self.infer_in(*body, &extended, &body_frame, remaining, cache);
                let body_sort = match self.sort_level(body_type, *remaining) {
                    Judgment::Proven { value, .. } => value,
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                };
                Judgment::proven(
                    TypeValue::Sort(imax(domain_sort, body_sort)),
                    "pi-sort-inference",
                )
            }
            Expr::Proj {
                type_name,
                index,
                structure,
            } => {
                let specs = self.environment.projection_specs();
                let Some(spec) = specs.get(type_name) else {
                    return Judgment::unknown("unsupported-projection");
                };
                let Ok(index) = usize::try_from(*index) else {
                    return Judgment::refuted("projection-index-overflow");
                };
                let Some(field_type) = spec.field_types.get(index).cloned() else {
                    return Judgment::refuted("projection-index-out-of-range");
                };
                let structure_type =
                    match self.infer_in(*structure, context, frame, remaining, cache) {
                        Judgment::Proven { value, .. } => value,
                        Judgment::Refuted { obstruction } => {
                            return Judgment::Refuted { obstruction };
                        }
                        Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                    };
                let TypeValue::Term(structure_type) = structure_type else {
                    return Judgment::refuted("projection-not-structure");
                };
                let exposed =
                    self.machine()
                        .expose(structure_type, Transparency::Reducible, *remaining);
                let neutral = match exposed {
                    Judgment::Proven {
                        value: Value::Neutral(neutral),
                        ..
                    } => neutral,
                    Judgment::Proven { .. } => {
                        return Judgment::refuted("projection-not-structure");
                    }
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                };
                let NeutralHead::Const { name, levels } = neutral.head else {
                    return Judgment::refuted("projection-not-structure");
                };
                if name != *type_name {
                    return Judgment::refuted("projection-type-name-mismatch");
                }

                let field_type = match field_type {
                    ProjectionFieldType::Parameter(parameter_index) => {
                        let Some(field_type) = neutral.spine.get(parameter_index).cloned() else {
                            return Judgment::refuted("projection-parameter-arity");
                        };
                        field_type
                    }
                    ProjectionFieldType::Derived(field_expression) => {
                        if neutral.spine.len() < spec.num_params {
                            return Judgment::refuted("projection-parameter-arity");
                        }
                        let Some(declaration) = self.environment.get(*type_name) else {
                            return Judgment::unknown("projection-missing-type-authority");
                        };
                        if declaration.level_params.len() != levels.len() {
                            return Judgment::refuted("projection-level-arity");
                        }

                        // Constructor field types are scoped over parameters
                        // followed by all earlier fields.  Instantiate that
                        // exact telescope.  Earlier fields of a neutral
                        // structure stay neutral projections rather than
                        // becoming UNKNOWN.
                        // Receiver-free field-zero type inference: no prior
                        // fields exist, so certified declaration + parameters
                        // already determine this type.
                        let structure_value = if index == 0 {
                            None
                        } else {
                            let exposed = self.machine().expose(
                                self.closure(*structure, frame.clone()),
                                Transparency::Reducible,
                                *remaining,
                            );
                            let Some(Value::Neutral(receiver)) = exposed.proven_value() else {
                                return Judgment::unknown("projection-dependent-structure-value");
                            };
                            Some(receiver.clone())
                        };

                        let mut field_frame = EnvFrame::empty();
                        for parameter in neutral.spine.iter().take(spec.num_params) {
                            field_frame = field_frame.extend(parameter.clone());
                        }
                        for prior_index in 0..index {
                            let Some(structure_value) = structure_value.as_ref() else {
                                return Judgment::unknown("projection-prior-field-receiver");
                            };
                            match &structure_value.head {
                                NeutralHead::Const { name, .. } if *name == spec.constructor => {
                                    let field_offset = spec.num_params + prior_index;
                                    let Some(prior_field) =
                                        structure_value.spine.get(field_offset).cloned()
                                    else {
                                        return Judgment::unknown(
                                            "projection-dependent-constructor-arity",
                                        );
                                    };
                                    field_frame = field_frame.extend(prior_field);
                                }
                                // The receiver's type has already matched
                                // the declared structure above. A constant-
                                // headed neutral has the same dependent
                                // projection telescope as any other neutral.
                                NeutralHead::Const { .. } | NeutralHead::Free(_, _) | NeutralHead::Projection { .. } => {
                                    field_frame = field_frame.extend_neutral(Neutral {
                                        head: NeutralHead::Projection {
                                            type_name: *type_name,
                                            index: prior_index,
                                            structure: Box::new(structure_value.clone()),
                                        },
                                        spine: Vec::new(),
                                    });
                                }
                            }
                        }

                        let level_substitution = LevelSubstitution::new(
                            declaration
                                .level_params
                                .iter()
                                .copied()
                                .zip(levels)
                                .collect(),
                        );
                        Closure::with_levels(field_expression, field_frame, level_substitution)
                    }
                };
                Judgment::proven(
                    TypeValue::Term(field_type),
                    "qualified-structure-projection",
                )
            }
            Expr::Let { ty, value, body } => {
                let annotation_type = self.infer_in(*ty, context, frame, remaining, cache);
                match self.sort_level(annotation_type, *remaining) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                }
                let established = TypeValue::Term(self.closure(*ty, frame.clone()));
                // Annotation formation was independently proved above.
                match self.check_with_formation(*value, &established, context, frame, remaining, true, cache, true) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                }
                let mut extended = context.to_vec();
                extended.push(established.clone());
                let extended_frame = self.checked_source_frame(
                    expression, CheckedFrameRole::Let, frame, established, &extended,
                    CheckedFrameBinding::Actual(self.closure(*value, frame.clone())),
                );
                self.infer_in(*body, &extended, &extended_frame, remaining, cache)
            }
        }
    }

    #[inline(never)]
    fn infer_lambda_source(
        &self,
        expression: ExprId,
        domain: &ExprId,
        body: &ExprId,
        context: &[TypeValue], frame: &EnvFrame,
        remaining: &mut usize,
        cache: &mut HashMap<(ExprId, u64), TypeValue>,
    ) -> Judgment<TypeValue> {
                let domain_type = self.infer_in(*domain, context, frame, remaining, cache);
                match self.sort_level(domain_type, *remaining) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                }
                let domain_type = TypeValue::Term(self.closure(*domain, frame.clone()));
                let mut extended = context.to_vec();
                extended.push(domain_type.clone());
                let Some(free) = fresh_local(context.len()) else {
                    return Judgment::unknown("binder-depth-overflow");
                };
                let body_frame = self.checked_source_frame(
                    expression, CheckedFrameRole::InferLambda, frame, domain_type.clone(),
                    &extended, CheckedFrameBinding::Free(free),
                );
                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_SOURCE_PROOF_BETA").is_some()
                    && matches!((expression.0,domain.0),
                        (7143,7074)|(6897,6828)|(5728,5659)|(5725,5656))
                {
                    eprintln!(
                        "NUCLEUS_SOURCE_BINDER_INTRO:route=infer:lambda={expression:?}:ctx={}:free={free:?}:binding_node={}:source_frame={}:domain={domain:?}",
                        context.len(),body_frame.id(),frame.id(),
                    );
                }
                self.strict_certificate_probe().retain_shared_checked_binding(&body_frame,domain_type.clone(),Rc::new(extended.clone()));
                self.infer_in(*body, &extended, &body_frame, remaining, cache)
                    .map(|body_type| TypeValue::Pi {
                        domain: Box::new(domain_type),
                        body: Box::new(body_type),
                        binder: free,
                     binder_owner: Some(body_frame.clone()),})

    }

    #[inline(never)]
    fn infer_application_source(
        &self,
        expression: ExprId,
        fun: &ExprId,
        arg: &ExprId,
        context: &[TypeValue], frame: &EnvFrame,
        remaining: &mut usize,
        cache: &mut HashMap<(ExprId, u64), TypeValue>,
    ) -> Judgment<TypeValue> {
                let function_type = self.infer_in(*fun, context, frame, remaining, cache);
                if let Judgment::Refuted { obstruction } = &function_type {
                    return Judgment::Refuted {
                        obstruction: *obstruction,
                    };
                }
                let ordinary_view = self.pi_view(function_type.clone(), *remaining);
                let checked_view = ordinary_view.or_else(|| {
                    if self.delta_policy != crate::convert::DeltaPolicy::GuardedSemanticFallback {
                        return None;
                    }
                    let TypeValue::Term(term) = function_type.proven_value()? else { return None };
                    let reduced = crate::convert::checked_source_type_value(
                        self, term.clone(), context, *remaining,
                    );
                    let Value::Pi { domain, body } = reduced.proven_value()? else { return None };
                    Some((TypeValue::Term(domain.clone()), PiBody::Closure(body.clone())))
                });
                let Some((domain, body)) = checked_view else {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE").is_some() {
                        let mut reducible = None;
                        let mut full = None;
                        if let Judgment::Proven {
                            value: TypeValue::Term(closure),
                            ..
                        } = &function_type
                        {
                            reducible = Some(
                                self.machine()
                                    .expose(
                                        closure.clone(),
                                        Transparency::Reducible,
                                        (*remaining).min(4096),
                                    ),
                            );
                            full = Some(
                                self.machine()
                                    .expose(
                                        closure.clone(),
                                        Transparency::Full,
                                        (*remaining).min(4096),
                                    ),
                            );
                        }
                        eprintln!(
                            "NUCLEUS_APPLICATION_FUNCTION_TYPE:application={:?}:function={:?}:argument={:?}:context_len={}:frame={}:remaining={}:function_type={:?}:reducible={:?}:full={:?}",
                            expression,
                            fun,
                            arg,
                            context.len(),
                            frame.id(),
                            *remaining,
                            function_type,
                            reducible,
                            full,
                        );
                    }
                    #[cfg(feature="diagnostics")] if std::env::var_os("NUCLEUS_TRACE_SHAPE_FRONTIER").is_some(){eprintln!("SHAPE_APP_UNKNOWN app={} fun={} arg={} gamma={} frame={} remaining={} type={function_type:?}",expression.0,fun.0,arg.0,context.len(),frame.id(),*remaining);}
                    return Judgment::unknown("application-function-type");
                };
                // Proven function inference in the checked caller Γ yields
                // a formed Pi domain; pi_view only exposes that proved type.
                let argument_judgment=self.check_with_formation(
                    *arg, &domain, context, frame, remaining, true, cache, true,
                );
                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_APP_DOMAIN_OBLIGATION").is_some()
                    && matches!(argument_judgment,Judgment::Unknown {..})
                    && (context.len()==4 || context.len()==11)
                {
                    use std::sync::atomic::{AtomicUsize,Ordering};
                    static TRACED:AtomicUsize=AtomicUsize::new(0);
                    if TRACED.fetch_add(1,Ordering::Relaxed)<24 {
                        let binding=match self.expressions.get(*arg){
                            Some(Expr::BVar(i))=>frame.lookup_with_node_id(*i),
                            _=>None,
                        };
                        eprintln!(
                            "NUCLEUS_APP_DOMAIN_OBLIGATION:application={expression:?}:function={fun:?}:argument={arg:?}:argument_shape={:?}:argument_binding={binding:?}:expected_domain={domain:?}:judgment={argument_judgment:?}:context_depth={}:frame={}:remaining={}:source_head={:?}",
                            self.expressions.get(*arg),context.len(),frame.id(),
                            *remaining,self.expressions.get(*fun),
                        );
                    }
                }
                match argument_judgment {
                    Judgment::Proven { .. } => {
                        self.retain_checked_argument(self.closure(*fun,frame.clone()),self.closure(*arg,frame.clone()),domain.clone(),context,remaining);

                        // Function inference and the argument-domain check
                        // establish elimination. Substitute the certified lexical
                        // binder in its inferred type, preserving capture guards.
                        let result = match body {
                            PiBody::Fixed(binder, inferred_body, owner) => {
                                let actual = self.closure(*arg, frame.clone());
                                let Some(type_value) = self.instantiate_checked_fixed_pi_body(
                                    &inferred_body, binder, owner.as_ref(), &domain, &actual, context, frame, remaining,
                                ) else {
                                    return Judgment::unknown("fixed-pi-binder-substitution");
                                };
                                type_value
                            }
                            PiBody::Closure(body) => {
                                let actual=self.closure(*arg,frame.clone());
                                let typed_frame=body.env.extend(actual);
                                self.retain_checked_elimination(
                                    &typed_frame,domain.clone(),context,
                                );
                                TypeValue::Term(Closure::with_levels(
                                    body.expr,typed_frame,body.levels,
                                ))
                            },
                        };
                        Judgment::proven(result, "application-type-instantiation")
                    }
                    Judgment::Refuted { obstruction } => Judgment::Refuted { obstruction },
                    Judgment::Unknown { residual } => Judgment::Unknown { residual },
                }

    }
    // Experimental bidirectional lambda rule: given a previously checked
    // expected dependent Pi, prove the annotation's domain formation,
    // compare domains definitionally, and then check the lambda body under
    // its genuinely introduced binder against the instantiated Pi codomain.
    // This derives typing; it does not infer equality from a lambda shape.
    fn check_expected_lambda_in(
        &self,
        expression: ExprId,
        expected: &TypeValue,
        context: &[TypeValue],
        frame: &EnvFrame,
        remaining: &mut usize,
        conversion_refutation_is_unknown: bool,
        cache: &mut HashMap<(ExprId,u64),TypeValue>,
        expected_formed: bool,
    ) -> Judgment<()> {
        if !take_step(remaining) {
            return Judgment::unknown("bidir-lambda-budget");
        }
        let Some(Expr::Lam {domain,body})=self.expressions.get(expression) else {
            return Judgment::unknown("bidir-lambda-not-lambda");
        };
        let Some((required_domain, codomain))=self.pi_view(
            Judgment::proven(expected.clone(),"checked-expected-Pi"),
            (*remaining).min(2048),
        ) else {
            return Judgment::unknown("bidir-lambda-expected-not-Pi");
        };
        let domain_formation=self.infer_in(
            *domain,context,frame,remaining,cache,
        );
        match self.sort_level(domain_formation,(*remaining).min(1024)) {
            Judgment::Proven {..} => {},
            Judgment::Unknown {residual}=>return Judgment::Unknown {residual},
            Judgment::Refuted {obstruction}=>return Judgment::Refuted {obstruction},
        };
        let annotated=TypeValue::Term(self.closure(*domain,frame.clone()));
        let relation=crate::convert::convert_with_policy_in_context(
            self,&annotated,&required_domain,(*remaining).min(2048),
            self.delta_policy,context.len(),context,
        );
        if !relation.is_proven(){return relation}
        let Some(free)=fresh_local(context.len()) else{
            return Judgment::unknown("bidir-lambda-fresh-binder-overflow")
        };
        let mut extended=context.to_vec();
        extended.push(annotated.clone());
        let body_frame=self.checked_source_frame(
            expression,CheckedFrameRole::ExpectedLambda,frame,annotated.clone(),&extended,CheckedFrameBinding::Free(free),
        );
        self.strict_certificate_probe().retain_shared_checked_binding(&body_frame,annotated.clone(),Rc::new(extended.clone()));
        let target=match codomain {
            PiBody::Closure(expected_body) => {
                let allowance = (*remaining).min(1024);
                let mut opening_budget = allowance;
                let safe = crate::convert::source_opening_avoids_capture(
                    self, &expected_body, free, &mut opening_budget,
                );
                *remaining -= allowance - opening_budget;
                if !safe {
                    return Judgment::unknown("bidir-lambda-source-binder-capture-or-support-unavailable");
                }
                let opened_frame=if expected_body.env==*frame && required_domain==annotated {
                    // Both source bodies have the same parent and proved domain;
                    // they are opened by this one checked lambda introduction.
                    body_frame.clone()
                }else{
                    if let Some(scope)=self.checked_lambda_scope(&body_frame) {
                        let Some(opened)=self.shared_expected_pi_frame(&expected_body,&scope,free,remaining) else {
                            return Judgment::unknown("expected-pi-opening-budget-or-quarantine");
                        };
                        opened
                    } else {
                        // Capability-off/fixed contexts retain the original
                        // independently materialized scope construction.
                        let scope_cost=extended.len()+4;
                        if *remaining<scope_cost{return Judgment::unknown("expected-pi-opening-budget");}*remaining-=scope_cost;
                        self.checked_source_frame_with_codomain(
                            expected_body.expr,CheckedFrameRole::ExpectedPiOpening,&expected_body.env,
                            annotated.clone(),&extended,CheckedFrameBinding::Free(free),Some(expected_body.clone()),
                        )
                    }
                };
                TypeValue::Term(Closure::with_levels(expected_body.expr,opened_frame,expected_body.levels))
            },
            PiBody::Fixed(binder,value, owner) => {
                let reopened=match owner {Some(owner)=>self.reopen_fixed_pi_body_owned(&value,binder,&owner,&body_frame,remaining),None=>None};
                let Some(reopened) = reopened else {
                    return Judgment::unknown("bidir-lambda-fixed-binder-not-aligned");
                };
                reopened
            },
        };
        // A formed expected Pi and the proved annotation-domain equality
        // establish its instantiated codomain under this checked fresh binder.
        self.check_with_formation(
            *body,&target,&extended,&body_frame,remaining,
            conversion_refutation_is_unknown,cache,expected_formed,
        )
    }

    fn check_in(
        &self,
        expression: ExprId,
        expected: &TypeValue,
        context: &[TypeValue],
        frame: &EnvFrame,
        remaining: &mut usize,
        conversion_refutation_is_unknown: bool,
        cache: &mut HashMap<(ExprId, u64), TypeValue>,
    ) -> Judgment<()> {
        self.check_with_formation(expression, expected, context, frame, remaining,
            conversion_refutation_is_unknown, cache, false)
    }

    fn check_with_formation(
        &self,
        expression: ExprId,
        expected: &TypeValue,
        context: &[TypeValue],
        frame: &EnvFrame,
        remaining: &mut usize,
        conversion_refutation_is_unknown: bool,
        cache: &mut HashMap<(ExprId, u64), TypeValue>,
        expected_formed: bool,
    ) -> Judgment<()> {
        let app_check_started=*remaining;
        let owned_application_goal=expected_formed
            && std::env::var_os("NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA").is_some()
            && context.len()<=128 && context.iter().all(|ty|matches!(ty,TypeValue::Term(_)))
            && matches!(self.expressions.get(expression),Some(Expr::App{..}))
            // Ordinary inference will already reuse this complete source type.
            // Transporting a separate checking certificate cannot save work.
            && !cache.contains_key(&(expression,if self.closed_spine_eligibility.borrow().get(&expression)==Some(&true){EnvFrame::empty().id()}else{frame.id()}));
        if owned_application_goal && let TypeValue::Term(target)=expected {
            #[cfg(feature="diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_MISSED_APP_PATTERNS").is_some()
                && let Some((pattern,_))=self.source_syntax_patterns.borrow().get(&expression).cloned() {
                let patterns=self.source_syntax_patterns.borrow();
                let proofs=self.owned_lambda_goals.borrow();
                let matches:Vec<_>=proofs.iter().filter(|(id,_)|**id!=expression&&matches!(self.expressions.get(**id),Some(Expr::App{..}))&&patterns.get(id).is_some_and(|(old,_)|*old==pattern))
                    .flat_map(|(id,entries)|entries.iter().filter(|entry|entry.expected.expr==target.expr).map(|_|*id)).collect();
                if !matches.is_empty(){eprintln!("MISSED_APP_PATTERN:expr={expression:?}:target={:?}:ctx={}:remaining={remaining}:old={matches:?}",target.expr,context.len());}
            }
            let source=self.closure(expression,frame.clone());
            if self.reuse_owned_lambda_goal(expression,&source,target,context,remaining){
                return Judgment::proven((),"completed-application-check-with-owned-typed-capture-transport");
            }
        }
        // Let elimination preserves the established goal. Its value is
        // checked against a formed annotation before the actual substitution
        // enters the lexical frame; no generic lambda is beta-checked here.
        if expected_formed
            && std::env::var_os("NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA").is_some()
            && let TypeValue::Term(target)=expected
            && let Some(Expr::Let{ty,value,body})=self.expressions.get(expression)
        {
            let fresh=fresh_local(context.len());
            let weakening=self.capture_fingerprint(target,remaining);
            fn contains_free(key:&CaptureFingerprint,free:FreeId)->bool {
                match key {
                    CaptureFingerprint::Free(f,..)=>*f==free,
                    CaptureFingerprint::Term(_,_,captures)=>captures.iter().any(|(_,k)|contains_free(k,free)),
                    CaptureFingerprint::Nat(..)=>false,
                    CaptureFingerprint::Bound(_,capture)=>contains_free(capture,free),
                }
            }
            if let (Some(fresh),Some(weakening))=(fresh,weakening) {
                if !contains_free(&weakening,fresh) {
                    if !take_step(remaining){return Judgment::unknown("formed-let-budget");}
                    let annotation_sort=self.infer_in(*ty,context,frame,remaining,cache);
                    match self.sort_level(annotation_sort,*remaining) {
                        Judgment::Proven{..}=>{},
                        Judgment::Unknown{residual}=>return Judgment::Unknown{residual},
                        Judgment::Refuted{obstruction}=>return Judgment::Refuted{obstruction},
                    }
                    let annotation=TypeValue::Term(self.closure(*ty,frame.clone()));
                    match self.check_with_formation(*value,&annotation,context,frame,remaining,
                        conversion_refutation_is_unknown,cache,true) {
                        Judgment::Proven{..}=>{},
                        Judgment::Unknown{residual}=>return Judgment::Unknown{residual},
                        Judgment::Refuted{obstruction}=>return Judgment::Refuted{obstruction},
                    }
                    let mut extended=context.to_vec();extended.push(annotation.clone());
                    let body_frame=self.checked_source_frame(expression,CheckedFrameRole::Let,
                        frame,annotation,&extended,
                        CheckedFrameBinding::Actual(self.closure(*value,frame.clone())));
                    return self.check_with_formation(*body,expected,&extended,&body_frame,remaining,
                        conversion_refutation_is_unknown,cache,true);
                }
            }
        }
        // An independently completed literal codomain support certificate
        // can show that this Pi is an arrow. Ordinary inference and actual
        // conversion then run first; this certificate proves no typing goal.
        let inference_first_arrow=if expected_formed
            && std::env::var_os("NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA").is_some()
            && matches!(self.expressions.get(expression),Some(Expr::Lam{..})) {
            if let TypeValue::Term(source)=expected
                && let Some(Expr::Pi{body,..})=self.expressions.get(source.expr) {
                let allowance=(*remaining).min(256);let mut work=allowance;
                let entire_support=self.complete_source_support(source.expr,&mut work);
                let independent=entire_support.is_some_and(|indices|indices.is_empty())
                    && self.complete_source_support(*body,&mut work).is_some_and(|indices|!indices.contains(&0));
                *remaining-=allowance-work;
                independent
            }else{false}
        }else{false};
        // A formed expected dependent Pi is the primary goal for a lambda.
        // Keep its dependent codomain throughout the checked derivation.
        if expected_formed && !inference_first_arrow
            && std::env::var_os("NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA").is_some()
            && matches!(self.expressions.get(expression), Some(Expr::Lam { .. }))
        {
            if self.pi_view(Judgment::proven(expected.clone(),"formed-goal"), *remaining).is_some() {
                let goal = (context.len() <= 128
                    && context.iter().all(|ty| matches!(ty,TypeValue::Term(_)))
                    && matches!(expected,TypeValue::Term(_)))
                    .then(||(expression,frame.id(),expected.clone(),context.to_vec()));
                let retained=goal.as_ref().and_then(|key|self.formed_lambda_goals.borrow().get(key).cloned());
                if let Some(dependencies)=retained {
                    if take_step(remaining)&&self.retained_goal_dependencies_valid(&dependencies,remaining) {
                        return Judgment::proven((),"retained-formed-lambda-goal");
                    }
                }
                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_CACHED_LAMBDA_CHECKS").is_some() && cache.contains_key(&(expression,frame.id())) {
                    eprintln!("CACHED_LAMBDA_CHECK:expr={expression:?}:ctx={}:remaining={remaining}",context.len());
                }
                let source=self.closure(expression,frame.clone());
                if context.len()<=128 && let TypeValue::Term(target)=expected {
                    if self.reuse_owned_lambda_goal(expression,&source,target,context,remaining){
                        return Judgment::proven((),"completed-lambda-goal-with-owned-typed-capture-transport");
                    }
                }
                let result = self.check_expected_lambda_in(expression, expected, context, frame,
                    remaining, conversion_refutation_is_unknown, cache, true);
                if result.is_proven() && context.len()<=128 && let TypeValue::Term(target)=expected {
                    let allowance=(*remaining).min(512);
                    let mut discovery=allowance;
                    let dependencies=self.owned_goal_dependencies(&source,target,context,&mut discovery);
                    *remaining-=allowance-discovery;
                    if let Some(dependencies)=dependencies {
                        if let Some(goal)=goal.clone() {
                            if self.formed_lambda_goals.borrow().len()<8192 {
                                self.formed_lambda_goals.borrow_mut().insert(goal,dependencies.clone());
                            }
                        }
                        if let Some(Expr::Lam{domain,..})=self.expressions.get(expression)
                            && let Some(hint)=self.lambda_candidate_hint(expression,remaining) {
                            let bound_goal=matches!(self.expressions.get(target.expr),Some(Expr::BVar(_)));
                            let mut shapes=self.owned_lambda_shapes.borrow_mut();
                            for goal in [Some(target.expr),None] {
                                if goal.is_none()&&!bound_goal {continue;}
                                if shapes.len()>=2048 {break;}
                                let candidates=shapes.entry((*domain,goal,hint)).or_default();
                                if candidates.len()<4 && !candidates.iter().any(|proof|proof.source.expr==expression) {
                                    candidates.push(OwnedLambdaGoal{source:source.clone(),expected:target.clone(),dependencies:dependencies.clone()});
                                    let mut buckets=self.owned_lambda_shape_domains.borrow_mut();let hints=buckets.entry((*domain,goal)).or_default();if !hints.contains(&hint){hints.push(hint);}
                                }
                            }
                        }
                        let mut proofs=self.owned_lambda_goals.borrow_mut();
                        if proofs.len()<2048 {
                            let variants=proofs.entry(expression).or_default();
                            if variants.len()<4 {variants.push(OwnedLambdaGoal{source,expected:target.clone(),dependencies});}
                        }
                    }
                }
                return result;
            }
        }
        let inferred = self.infer_in(expression, context, frame, remaining, cache);
        #[cfg(feature="diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_BIDIR_BODY_GAP").is_some()
            && context.len()==5
            && matches!(expression.0,11147|11146|7584|7250|5306)
        {
            eprintln!(
                "NUCLEUS_BIDIR_BODY_INFER:expr={expression:?}:context={}:frame={}:shape={:?}:inferred={inferred:?}:expected={expected:?}:remaining={}",
                context.len(),frame.id(),self.expressions.get(expression),*remaining,
            );
        }
        let ordinary = match inferred {
            Judgment::Proven { value, .. } => {
                let conversion = crate::convert::convert_with_policy_in_context(
                    self,
                    &value,
                    expected,
                    *remaining,
                    self.delta_policy,
                    context.len(),
                    context,
                );
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_FAILED_RECEIVER_CONVERSION").is_some()
                    && matches!(&conversion, Judgment::Unknown { residual }
                        if residual.0 == "neutral-projection-receiver-congruence")
                {
                    let machine = self.machine();
                    let expose = |ty: &TypeValue| match ty {
                        TypeValue::Term(term) => Some(machine.expose_for_conversion(
                            term.clone(), Transparency::Full, (*remaining).min(2048))),
                        _ => None,
                    };
                    eprintln!("NUCLEUS_FAILED_RECEIVER_CONVERSION:expression={expression:?}:context_len={}:source_frame={}:remaining={}:actual={value:?}:expected={expected:?}:context={context:?}:actual_exposed={:?}:expected_exposed={:?}",
                        context.len(), frame.id(), *remaining, expose(&value), expose(expected));
                }
                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_BIDIR_BODY_GAP").is_some()
                    && context.len()==5
                    && matches!(expression.0,11147|11146|7584|7250|5306)
                {
                    eprintln!(
                        "NUCLEUS_BIDIR_BODY_CONVERT:expr={expression:?}:actual={value:?}:expected={expected:?}:relation={conversion:?}",
                    );
                }
                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_FINAL_CODOMAIN").is_some()
                    && matches!((context.len(),expression.0),
                        (8,7581)|(8,7247)|(7,11145)|(7,11144))
                {
                    let machine=self.machine();
                    let actual_exposed=match &value {
                        TypeValue::Term(t)=>Some(machine.expose_for_conversion(
                            t.clone(),Transparency::Full,(*remaining).min(2048),
                        )),
                        _=>None,
                    };
                    let expected_exposed=match expected {
                        TypeValue::Term(t)=>Some(machine.expose_for_conversion(
                            t.clone(),Transparency::Full,(*remaining).min(2048),
                        )),
                        _=>None,
                    };
                    let alternate=crate::convert::convert_with_policy_in_context(
                        self,&value,expected,(*remaining).min(2048),
                        crate::convert::DeltaPolicy::PreferredOnly,
                        context.len(),context,
                    );
                    let pair_results={
                        let left=actual_exposed.as_ref().and_then(|v|v.proven_value());
                        let right=expected_exposed.as_ref().and_then(|v|v.proven_value());
                        let compare_pair=|a:&Closure,b:&Closure| {
                            [128usize,512,2048].into_iter().map(|fuel|{
                                (fuel,crate::convert::convert_with_policy_in_context(
                                    self,&TypeValue::Term(a.clone()),
                                    &TypeValue::Term(b.clone()),fuel,
                                    crate::convert::DeltaPolicy::PreferredOnly,
                                    context.len(),context,
                                ))
                            }).collect::<Vec<_>>()
                        };
                        let inspect=|label:&str,a:&Closure,b:&Closure| {
                            let mut afuel=2048;
                            let a_ty=self.infer_exact_closure_in_context(
                                a,context,&mut afuel,0,
                            );
                            let mut bfuel=2048;
                            let b_ty=self.infer_exact_closure_in_context(
                                b,context,&mut bfuel,0,
                            );
                            let kind=|ty:&Option<TypeValue>|{
                                if let Some(TypeValue::Term(c))=ty {
                                    let mut fuel=1024;
                                    self.infer_exact_closure_in_context(
                                        c,context,&mut fuel,0,
                                    ).map(|x|self.sort_level(
                                        Judgment::proven(x,"source-operand-kind"),
                                        fuel.min(512),
                                    ))
                                }else{None}
                            };
                            let same_type=match (&a_ty,&b_ty) {
                                (Some(left),Some(right))=>Some(
                                    crate::convert::convert_with_policy_in_context(
                                        self,left,right,2048,
                                        crate::convert::DeltaPolicy::PreferredOnly,
                                        context.len(),context,
                                    )),
                                _=>None,
                            };
                            let a_value=self.machine().expose_for_conversion(
                                a.clone(),Transparency::Reducible,512,
                            );
                            let b_value=self.machine().expose_for_conversion(
                                b.clone(),Transparency::Reducible,512,
                            );
                            #[cfg(feature="diagnostics")]
                            if std::env::var_os("NUCLEUS_TRACE_ARITHMETIC_INSTANCE").is_some()
                                && label != "arg0" && context.len()>=7
                            {
                                let lv=self.machine().expose_for_conversion(
                                    a.clone(),Transparency::Full,1024,
                                );
                                let rv=self.machine().expose_for_conversion(
                                    b.clone(),Transparency::Full,1024,
                                );
                                let classify=|value:&Judgment<Value>|->String {
                                    let Some(Value::StuckProjection{
                                        type_name,index,structure,spine,
                                    })=value.proven_value() else {
                                        return format!("not-stuck:{}",format!("{value:?}").chars().take(1200).collect::<String>())
                                    };
                                    let struct_source=match self.expressions.get(structure.expr) {
                                        Some(Expr::BVar(i))=>structure.env.lookup_with_node_id(*i),
                                        _=>None,
                                    };
                                    let receiver=self.machine().expose_for_conversion(
                                        structure.clone(),Transparency::Full,1024,
                                    );
                                    let original_args=spine.iter().map(|arg|{
                                        let v=self.machine().expose_for_conversion(
                                            arg.clone(),Transparency::Full,512,
                                        );
                                        format!("{:?}={}",arg.expr,
                                            format!("{v:?}").chars().take(550).collect::<String>())
                                    }).collect::<Vec<_>>();
                                    format!(
                                        "project={type_name:?}:{index}:struct={structure:?}:source={struct_source:?}:receiver={}:args={original_args:?}",
                                        format!("{receiver:?}").chars().take(1700).collect::<String>(),
                                    )
                                };
                                eprintln!(
                                    "NUCLEUS_ARITHMETIC_INSTANCE:label={label}:context={}:left={}:right={}",
                                    context.len(),classify(&lv),classify(&rv),
                                );
                            }
                            // Diagnostic only: compare exact source-backed
                            // constructor fields UNDER THE ORIGINAL CONTEXT.
                            // The raw fields may not be equal and pending
                            // application arguments remain independent
                            // obligations. This report grants no verdict.
                            if label=="arg1"
                                && std::env::var_os("NUCLEUS_TRACE_FIELD_PAIR").is_some()
                                && let (
                                    Some(Value::StuckProjection{
                                        type_name:ln,index:li,structure:ls,spine:la,
                                    }),
                                    Some(Value::StuckProjection{
                                        type_name:rn,index:ri,structure:rs,spine:ra,
                                    }),
                                )=(a_value.proven_value(),b_value.proven_value())
                            {
                                use std::sync::atomic::{AtomicUsize,Ordering};
                                static FIELD_PAIRS:AtomicUsize=AtomicUsize::new(0);
                                if FIELD_PAIRS.fetch_add(1,Ordering::Relaxed)<16 {
                                    let machine=self.machine();
                                    let left_field=machine.projection_field_for_conversion(
                                        ls.clone(),*ln,*li,2048,
                                    );
                                    let right_field=machine.projection_field_for_conversion(
                                        rs.clone(),*rn,*ri,2048,
                                    );
                                    let field_eq=match (
                                        left_field.proven_value(),
                                        right_field.proven_value(),
                                    ) {
                                        (Some(x),Some(y))=>Some(
                                            crate::convert::convert_with_policy_in_context(
                                                self,&TypeValue::Term(x.clone()),
                                                &TypeValue::Term(y.clone()),2048,
                                                crate::convert::DeltaPolicy::PreferredOnly,
                                                context.len(),context,
                                            ),
                                        ),
                                        _=>None,
                                    };
                                    let spine_eq=la.len()==ra.len() && la.iter().zip(ra)
                                        .all(|(x,y)|crate::convert::convert_with_policy_in_context(
                                            self,&TypeValue::Term(x.clone()),
                                            &TypeValue::Term(y.clone()),2048,
                                            crate::convert::DeltaPolicy::PreferredOnly,
                                            context.len(),context,
                                        ).is_proven());
                                    eprintln!(
                                        "NUCLEUS_FIELD_PAIR:context={}:lhs_type={ln:?}:rhs_type={rn:?}:lhs_field={left_field:?}:rhs_field={right_field:?}:field_eq={field_eq:?}:lhs_applied={}:rhs_applied={}:spine_eq={spine_eq}:NO_SEMANTIC_ADMISSION",
                                        context.len(),la.len(),ra.len(),
                                    );
                                }
                            }
                            format!(
                                "{label}:a={a:?}:b={b:?}:atype={a_ty:?}:btype={b_ty:?}:akind={:?}:bkind={:?}:type_relation={same_type:?}:value_a={}:value_b={}:checked_proof_pair={}",
                                kind(&a_ty),kind(&b_ty),
                                format!("{a_value:?}").chars().take(1500).collect::<String>(),
                                format!("{b_value:?}").chars().take(1500).collect::<String>(),
                                self.checked_proof_pair_in_bounded_context(a,b,context,2048),
                            )
                        };
                        match (left,right) {
                            (Some(Value::StuckProjection{
                                type_name:ln,index:li,structure:ls,spine:la,
                            }),Some(Value::StuckProjection{
                                type_name:rn,index:ri,structure:rs,spine:ra,
                            })) if ln==rn && li==ri && la.len()==ra.len() => {
                                let receiver=compare_pair(ls,rs);
                                let args=la.iter().zip(ra.iter()).enumerate()
                                    .map(|(i,(a,b))|format!("arg{i}:{:?}:{}",compare_pair(a,b),inspect(&format!("arg{i}"),a,b)))
                                    .collect::<Vec<_>>();
                                format!("same_projection={ln:?}:{li}:receiver={receiver:?}:arguments={args:?}")
                            }
                            (Some(Value::Neutral(l)),Some(Value::Neutral(r)))
                                if l.head==r.head && l.spine.len()==r.spine.len() => {
                                let args=l.spine.iter().zip(r.spine.iter()).enumerate()
                                    .map(|(i,(a,b))|format!("arg{i}:{:?}:{}",compare_pair(a,b),inspect(&format!("arg{i}"),a,b)))
                                    .collect::<Vec<_>>();
                                format!("same_neutral_head={:?}:arguments={args:?}",l.head)
                            }
                            _=>format!("nonmatched-shapes:left={left:?}:right={right:?}"),
                        }
                    };
                    eprintln!(
                        "NUCLEUS_CODOMAIN_PAIRS:expression={expression:?}:depth={}:premises={pair_results}",
                        context.len(),
                    );
                    eprintln!(
                        "NUCLEUS_FINAL_CODOMAIN:expression={expression:?}:scope={}:body={:?}:actual={value:?}:expected={expected:?}:guarded={conversion:?}:preferred={alternate:?}:actual_exposed={actual_exposed:?}:expected_exposed={expected_exposed:?}",
                        context.len(),self.expressions.get(expression),
                    );
                }
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_DEPENDENCY_GAP").is_some() {
                    if let Judgment::Unknown { residual } = &conversion {
                        use std::sync::atomic::{AtomicUsize, Ordering};
                        static GAPS: AtomicUsize = AtomicUsize::new(0);
                        if GAPS.fetch_add(1, Ordering::Relaxed) < 48 {
                            eprintln!(
                                "NUCLEUS_DEPENDENCY_GAP:expr={expression:?}:context={}:frame={}:residual={:?}:inferred_type={:?}:expected_type={:?}",
                                context.len(), frame.id(), residual, value, expected
                            );
                            if std::env::var_os("NUCLEUS_TRACE_DEPENDENCY_VALUES").is_some()
                                && let (TypeValue::Term(inferred), TypeValue::Term(anticipated)) = (&value, expected)
                            {
                                let machine = self.machine();
                                for transparency in [Transparency::Reducible, Transparency::Full] {
                                    let left = machine.expose_for_conversion(
                                        inferred.clone(), transparency, (*remaining).min(4096),
                                    );
                                    let right = machine.expose_for_conversion(
                                        anticipated.clone(), transparency, (*remaining).min(4096),
                                    );
                                    eprintln!("NUCLEUS_DEP_VALUES:expr={expression:?}:transparency={transparency:?}:left={left:?}:right={right:?}");
                                }
                            }
                            if let (TypeValue::Term(inferred), TypeValue::Term(anticipated)) = (&value, expected) {
                                for slot in 0..6u64 {
                                    eprintln!(
                                        "NUCLEUS_SUBLE_BINDING:expr={expression:?}:slot={slot}:actual={:?}:expected={:?}",
                                        inferred.env.lookup(slot), anticipated.env.lookup(slot)
                                    );
                                }
                            }
                        }
                    }
                }
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_REFUTATION_AS_UNKNOWN").is_some()
                    && context.len() == 7
                    && let Judgment::Refuted { obstruction } = &conversion
                    && conversion_refutation_is_unknown
                    && !definite_conversion_obstruction(obstruction.0)
                {
                    use std::sync::atomic::{AtomicUsize, Ordering};
                    static PRINTED: AtomicUsize = AtomicUsize::new(0);
                    if PRINTED.fetch_add(1, Ordering::Relaxed) < 40 {
                        let source_normal = match &value {
                            TypeValue::Term(term) => Some(self.machine().expose(
                                term.clone(), Transparency::Full, (*remaining).min(256),
                            )),
                            _ => None,
                        };
                        let expected_normal = match expected {
                            TypeValue::Term(term) => Some(self.machine().expose(
                                term.clone(), Transparency::Full, (*remaining).min(256),
                            )),
                            _ => None,
                        };
                        eprintln!(
                            "NUCLEUS_REFUTATION_AS_UNKNOWN:expr={expression:?}:context_len={}:frame={}:remaining={}:reason={obstruction:?}:actual={value:?}:expected={expected:?}:actual_whnf={source_normal:?}:expected_whnf={expected_normal:?}",
                            context.len(),frame.id(),remaining,
                        );
                    }
                }
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_FIRST_PI_DOMAIN").is_some()
                    && context.len() == 7
                    && let Judgment::Refuted { obstruction } = &conversion
                    && !definite_conversion_obstruction(obstruction.0)
                    && let (
                        TypeValue::Pi { domain: actual_domain, body: actual_body, binder , binder_owner,},
                        TypeValue::Term(expected_term),
                    ) = (&value, expected)
                {
                    use std::sync::atomic::{AtomicUsize, Ordering};
                    static PRINTED: AtomicUsize = AtomicUsize::new(0);
                    if PRINTED.fetch_add(1, Ordering::Relaxed) < 8 {
                        let expected_exposed = self.machine().expose(
                            expected_term.clone(), Transparency::Full, (*remaining).min(1024),
                        );
                        let mut domain_result = None;
                        let mut body_result = None;
                        let mut first_actual_normal = None;
                        let mut first_expected_normal = None;
                        if let Some(Value::Pi { domain: anticipated_domain, body: anticipated_body })
                            = expected_exposed.proven_value()
                        {
                            let check = crate::convert::convert_with_policy_in_context(
                                self,
                                actual_domain,
                                &TypeValue::Term(anticipated_domain.clone()),
                                (*remaining).min(512),
                                crate::convert::DeltaPolicy::GuardedSemanticFallback,
                                context.len(),
                                context,
                            );
                            domain_result = Some(check.clone());
                            first_actual_normal = match actual_domain.as_ref() {
                                TypeValue::Term(c) => Some(self.machine().expose(
                                    c.clone(), Transparency::Full, 512,
                                )),
                                _ => None,
                            };
                            first_expected_normal = Some(self.machine().expose(
                                anticipated_domain.clone(), Transparency::Full, 512,
                            ));
                            let mut diagnostic_opening_budget = 512;
                            if check.is_proven()
                                && *binder == FreeId(context.len() as u64)
                                && crate::convert::source_opening_avoids_capture(
                                    self, anticipated_body, *binder, &mut diagnostic_opening_budget,
                                )
                            {
                                let mut ext = context.to_vec();
                                ext.push(actual_domain.as_ref().clone());
                                body_result = Some(
                                    crate::convert::convert_with_policy_in_context(
                                        self,
                                        actual_body.as_ref(),
                                        &TypeValue::Term(anticipated_body.under_free(*binder)),
                                        (*remaining).min(512),
                                        crate::convert::DeltaPolicy::GuardedSemanticFallback,
                                        ext.len(),
                                        &ext,
                                    ),
                                );
                                let next_expected = anticipated_body.under_free(*binder);
                                let next_expected_whnf = self.machine().expose(
                                    next_expected, Transparency::Full, (*remaining).min(1024),
                                );
                                if let (
                                    TypeValue::Pi {
                                        domain: inner_actual_domain,
                                        body: inner_actual_body,
                                        binder: inner_binder,
                                     binder_owner,},
                                    Some(Value::Pi {
                                        domain: inner_expected_domain,
                                        body: inner_expected_body,
                                    }),
                                ) = (actual_body.as_ref(), next_expected_whnf.proven_value())
                                {
                                    let inner_domain_relation =
                                        crate::convert::convert_with_policy_in_context(
                                            self,
                                            inner_actual_domain,
                                            &TypeValue::Term(inner_expected_domain.clone()),
                                            (*remaining).min(512),
                                            crate::convert::DeltaPolicy::GuardedSemanticFallback,
                                            ext.len(),
                                            &ext,
                                        );
                                    let mut last_relation = None;
                                    let mut actual_final_whnf = None;
                                    let mut expected_final_whnf = None;
                                    let mut diagnostic_inner_opening_budget = 512;
                                    if inner_domain_relation.is_proven()
                                        && *inner_binder == FreeId(ext.len() as u64)
                                        && crate::convert::source_opening_avoids_capture(
                                            self, inner_expected_body, *inner_binder,
                                            &mut diagnostic_inner_opening_budget,
                                        )
                                    {
                                        let mut inner_context = ext.clone();
                                        inner_context.push(inner_actual_domain.as_ref().clone());
                                        let expected_final = inner_expected_body.under_free(*inner_binder);
                                        last_relation = Some(
                                            crate::convert::convert_with_policy_in_context(
                                                self,
                                                inner_actual_body.as_ref(),
                                                &TypeValue::Term(expected_final.clone()),
                                                (*remaining).min(512),
                                                crate::convert::DeltaPolicy::GuardedSemanticFallback,
                                                inner_context.len(),
                                                &inner_context,
                                            ),
                                        );
                                        actual_final_whnf = match inner_actual_body.as_ref() {
                                            TypeValue::Term(c) => Some(self.machine().expose(
                                                c.clone(), Transparency::Full, 512,
                                            )),
                                            _ => None,
                                        };
                                        expected_final_whnf = Some(self.machine().expose(
                                            expected_final, Transparency::Full, 512,
                                        ));
                                        if let (
                                            Some(Value::Neutral(actual_neutral)),
                                            Some(Value::Neutral(expected_neutral)),
                                        ) = (
                                            actual_final_whnf.as_ref().and_then(|j| j.proven_value()),
                                            expected_final_whnf.as_ref().and_then(|j| j.proven_value()),
                                        ) {
                                            if actual_neutral.head == expected_neutral.head
                                                && actual_neutral.spine.len() == 2
                                                && expected_neutral.spine.len() == 2
                                            {
                                                for actual_index in 0..2 {
                                                    for expected_index in 0..2 {
                                                        let actual = &actual_neutral.spine[actual_index];
                                                        let anticipated = &expected_neutral.spine[expected_index];
                                                        let preferred = crate::convert::convert_with_policy_in_context(
                                                            self,
                                                            &TypeValue::Term(actual.clone()),
                                                            &TypeValue::Term(anticipated.clone()),
                                                            (*remaining).min(512),
                                                            crate::convert::DeltaPolicy::PreferredOnly,
                                                            inner_context.len(),
                                                            &inner_context,
                                                        );
                                                        let guarded = if preferred.is_proven() {
                                                            preferred.clone()
                                                        } else {
                                                            crate::convert::convert_with_policy_in_context(
                                                                self,
                                                                &TypeValue::Term(actual.clone()),
                                                                &TypeValue::Term(anticipated.clone()),
                                                                (*remaining).min(512),
                                                                crate::convert::DeltaPolicy::GuardedSemanticFallback,
                                                                inner_context.len(),
                                                                &inner_context,
                                                            )
                                                        };
                                                        let actual_whnf = self.machine().expose(
                                                            actual.clone(), Transparency::Full, 512,
                                                        );
                                                        let expected_whnf = self.machine().expose(
                                                            anticipated.clone(), Transparency::Full, 512,
                                                        );
                                                        eprintln!(
                                                            "NUCLEUS_FINAL_SPINE_ARG:expr={expression:?}:depth={}:actual_index={actual_index}:expected_index={expected_index}:actual={actual:?}:expected={anticipated:?}:actual_whnf={actual_whnf:?}:expected_whnf={expected_whnf:?}:preferred={preferred:?}:guarded={guarded:?}",
                                                            inner_context.len(),
                                                        );
                                                        if actual_index == 1 && expected_index == 1
                                                            && std::env::var_os("NUCLEUS_TRACE_PROOF_ARGUMENT_TYPES").is_some()
                                                        {
                                                            let mut fuel_left=2048;
                                                            let mut fuel_right=2048;
                                                            let actual_type=self.infer_exact_closure_in_context(
                                                                actual, &inner_context, &mut fuel_left, 0,
                                                            );
                                                            let expected_type=self.infer_exact_closure_in_context(
                                                                anticipated, &inner_context, &mut fuel_right, 0,
                                                            );
                                                            let mut type_conversion=None;
                                                            let mut left_prop=None;
                                                            let mut right_prop=None;
                                                            if let Some(ty)=actual_type.as_ref() {
                                                                if let TypeValue::Term(type_closure)=ty {
                                                                    let mut fuel=2048;
                                                                    let inferred_type=self.infer_exact_closure_in_context(
                                                                        type_closure, &inner_context, &mut fuel, 0,
                                                                    );
                                                                    left_prop=inferred_type.map(|v|
                                                                        self.sort_level(
                                                                            Judgment::proven(v,"checked-proof-argument-type"),
                                                                            fuel.min(1024)
                                                                        )
                                                                    );
                                                                }
                                                            }
                                                            if let Some(ty)=expected_type.as_ref() {
                                                                if let TypeValue::Term(type_closure)=ty {
                                                                    let mut fuel=2048;
                                                                    let inferred_type=self.infer_exact_closure_in_context(
                                                                        type_closure, &inner_context, &mut fuel, 0,
                                                                    );
                                                                    right_prop=inferred_type.map(|v|
                                                                        self.sort_level(
                                                                            Judgment::proven(v,"checked-local-proof-type"),
                                                                            fuel.min(1024)
                                                                        )
                                                                    );
                                                                }
                                                            }
                                                            if let (Some(a),Some(b))=(&actual_type,&expected_type) {
                                                                type_conversion=Some(
                                                                    crate::convert::convert_with_policy_in_context(
                                                                        self,a,b,2048,
                                                                        crate::convert::DeltaPolicy::GuardedSemanticFallback,
                                                                        inner_context.len(), &inner_context,
                                                                    )
                                                                );
                                                            }
                                                            eprintln!(
                                                                "NUCLEUS_PROOF_ARGUMENT_TYPES:expr={expression:?}:context_len={}:actual_type={actual_type:?}:expected_type={expected_type:?}:type_conversion={type_conversion:?}:actual_type_sort={left_prop:?}:expected_type_sort={right_prop:?}:old_proof_relation={}",
                                                                inner_context.len(),
                                                                self.proof_terms_same_proposition(
                                                                    actual,anticipated,&inner_context,2048
                                                                ),
                                                            );
                                                        }

                                                    }
                                                }
                                            }
                                        }

                                    }
                                    eprintln!(
                                        "NUCLEUS_SECOND_PI_DOMAIN:expr={expression:?}:domain={inner_actual_domain:?}:expected_domain={inner_expected_domain:?}:domain_relation={inner_domain_relation:?}:last_relation={last_relation:?}:actual_final_whnf={actual_final_whnf:?}:expected_final_whnf={expected_final_whnf:?}",
                                    );
                                }

                            }
                        }
                        eprintln!(
                            "NUCLEUS_FIRST_PI_DOMAIN:expr={expression:?}:context_len={}:reason={obstruction:?}:actual_domain={actual_domain:?}:expected_pi={expected_exposed:?}:domain_relation={domain_result:?}:body_relation={body_result:?}:actual_domain_whnf={first_actual_normal:?}:expected_domain_whnf={first_expected_normal:?}",
                            context.len(),
                        );
                    }
                }
                match conversion {
                    Judgment::Refuted { obstruction }
                        if conversion_refutation_is_unknown
                            && !definite_conversion_obstruction(obstruction.0) =>
                    {
                        Judgment::unknown(obstruction.0)
                    }
                    other => other,
                }
            }
            Judgment::Refuted { obstruction } => Judgment::Refuted { obstruction },
            Judgment::Unknown { residual } => Judgment::Unknown { residual },
        };
        // A source lambda may be checked against an already established Pi
        // at any lexical depth. Eligibility depends on syntax and typing,
        // never an expression ID, theorem name or benchmark family.
        if ordinary.is_unknown() && std::env::var_os("NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA").is_some()
            && matches!(self.expressions.get(expression),Some(Expr::Lam {..}))
            && self.lambda_trials.borrow().active == 0
        {
            let Some(budget) = self.begin_lambda_trial(*remaining) else { return ordinary };
            let mut local_budget=budget;
            let candidate=self.check_expected_lambda_in(
                expression,expected,context,frame,&mut local_budget,
                conversion_refutation_is_unknown,cache,expected_formed,
            );
            self.finish_lambda_trial(budget, local_budget, candidate.is_proven());
            #[cfg(feature="diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_EXPECTED_LAMBDA").is_some() {
                use std::sync::atomic::{AtomicUsize,Ordering};
                static COUNT:AtomicUsize=AtomicUsize::new(0);
                if COUNT.fetch_add(1,Ordering::Relaxed)<40 {
                    eprintln!(
                        "NUCLEUS_EXPECTED_LAMBDA:expr={expression:?}:context={}:result={candidate:?}:remaining={local_budget}:expected={expected:?}",
                        context.len(),
                    );
                }
            }
            if candidate.is_proven() {
                *remaining = remaining.saturating_sub(budget - local_budget);
                return Judgment::proven((),"certified-expected-dependent-lambda");
            }
        }
        #[cfg(feature="diagnostics")]
        if matches!(self.expressions.get(expression),Some(Expr::App{..}))&&std::env::var_os("NUCLEUS_TRACE_CHECKED_APPS").is_some(){eprintln!("CHECKED_APP:expr={expression:?}:expected={:?}:formed={expected_formed}:ctx={}:start={app_check_started}:remaining={remaining}:proven={}",match expected{TypeValue::Term(t)=>Some(t.expr),_=>None},context.len(),ordinary.is_proven());}
        // Publish only a fully completed checking judgment. Reusing this
        // source application supplies no inferred output type and never
        // replaces typing of the original function by its beta normal form.
        if owned_application_goal && ordinary.is_proven()
            && app_check_started.saturating_sub(*remaining)>=32
            && let TypeValue::Term(target)=expected {
            // Occurrence counts select candidates only; they carry no typing
            // authority. Avoid collecting dependencies for one-off applications.
            if !take_step(remaining){return ordinary;}
            let repeated={let mut seen=self.repeated_completed_apps.borrow_mut();
                if seen.len()>=2048 && !seen.contains_key(&(expression,target.expr)){false}else{
                    let count=seen.entry((expression,target.expr)).or_default();
                    *count=(*count+1).min(2);*count==2
                }};
            if !repeated{return ordinary;}
            let source=self.closure(expression,frame.clone());
            let allowance=(*remaining).min(512);let mut discovery=allowance;
            let dependencies=self.owned_goal_dependencies(&source,target,context,&mut discovery);
            *remaining-=allowance-discovery;
            if let Some(dependencies)=dependencies {
                // Only an already completed lexical pattern may select a
                // different original application. It supplies no typing;
                // the full joint source/goal/domain derivation still follows.
                if let Some((pattern,_))=self.source_syntax_patterns.borrow().get(&expression) {
                    let mut buckets=self.owned_application_patterns.borrow_mut();
                    if buckets.len()<2048 {
                        let entries=buckets.entry((*pattern,target.expr)).or_default();
                        if entries.len()<4 && !entries.iter().any(|proof|proof.source.expr==expression) {
                            entries.push(OwnedLambdaGoal{source:source.clone(),expected:target.clone(),dependencies:dependencies.clone()});
                        }
                    }
                }
                let mut proofs=self.owned_lambda_goals.borrow_mut();
                if proofs.len()<2048 {
                    let variants=proofs.entry(expression).or_default();
                    if variants.len()<4 {variants.push(OwnedLambdaGoal{source,expected:target.clone(),dependencies});}
                }
            }
        }
        ordinary
    }

    // Whole-function inference has already succeeded. Reconstruct the
    // literal lambda telescope, checking each supplied argument in the caller
    // context while retaining each actual argument in the lexical environment.
    fn infer_literal_beta_spine(
        &self,
        expression: ExprId,
        context: &[TypeValue],
        frame: &EnvFrame,
        remaining: &mut usize,
        cache: &mut HashMap<(ExprId, u64), TypeValue>,
    ) -> Option<Judgment<TypeValue>> {
        let mut eligibility_remaining = *remaining;
        let mut head = expression;
        let mut arguments = Vec::new();
        while let Some(Expr::App { fun, arg }) = self.expressions.get(head) {
            if !take_step(&mut eligibility_remaining) {
                return None;
            }
            arguments.push(*arg);
            head = *fun;
        }
        if !matches!(self.expressions.get(head), Some(Expr::Lam { .. })) {
            return None;
        }
        // This bounded rule consumes only directly nested literal binders.
        // General returned-function representation remains a separate obligation.
        let mut probe = head;
        for _ in &arguments {
            if !take_step(&mut eligibility_remaining) {
                return None;
            }
            let Some(Expr::Lam { body, .. }) = self.expressions.get(probe) else {
                return None;
            };
            probe = *body;
        }
        // Declining eligibility preserves the caller's remaining budget.
        *remaining = eligibility_remaining;
        let mut lexical_context = context.to_vec();
        let mut lexical_frame = frame.clone();
        for arg in arguments.into_iter().rev() {
            let Some(Expr::Lam { domain, body }) = self.expressions.get(head) else {
                return None;
            };
            let domain_type =
                self.infer_in(*domain, &lexical_context, &lexical_frame, remaining, cache);
            match self.sort_level(domain_type, *remaining) {
                Judgment::Proven { .. } => {}
                Judgment::Refuted { obstruction } => {
                    return Some(Judgment::Refuted { obstruction });
                }
                Judgment::Unknown { residual } => return Some(Judgment::Unknown { residual }),
            }
            let domain = TypeValue::Term(self.closure(*domain, lexical_frame.clone()));
            // This exact lexical annotation was proved to have a sort above.
            match self.check_with_formation(arg, &domain, context, frame, remaining, true, cache, true) {
                Judgment::Proven { .. } => {}
                Judgment::Refuted { obstruction } => {
                    return Some(Judgment::Refuted { obstruction });
                }
                Judgment::Unknown { residual } => return Some(Judgment::Unknown { residual }),
            }
            lexical_context.push(domain.clone());
            lexical_frame = self.checked_source_frame(
                head, CheckedFrameRole::LiteralBeta, &lexical_frame, domain,
                &lexical_context, CheckedFrameBinding::Actual(self.closure(arg, frame.clone())),
            );
            head = *body;
        }
        Some(self.infer_in(head, &lexical_context, &lexical_frame, remaining, cache))
    }

    /// Unlike a fixed codomain, the body of an inferred lambda Pi may refer
    /// to its opened lexical local even when an outer Let hides the lambda
    /// syntactically. Instantiate only that local, within immutable closures.
    /// Unknown substitution shapes or exhausted fuel never justify acceptance.
    fn owned_pi_reclosure_capture_valid(&self,body:&TypeValue,remaining:&mut usize)->bool {
        let mut types=vec![body.clone()];let mut closures=Vec::new();let mut neutrals=Vec::new();
        let mut seen_types=std::collections::HashSet::new();let mut seen_closures=std::collections::HashSet::new();let mut seen_nodes=std::collections::HashSet::new();
        loop {
            if let Some(ty)=types.pop(){
                if !take_step(remaining){return false;}if !seen_types.insert(ty.clone()){continue;}
                match ty {
                    TypeValue::Sort(_)=>{},TypeValue::Term(c)=>closures.push(c),
                    TypeValue::Pi{domain,body,binder,binder_owner}=>{
                        if let Some(owner)=binder_owner {
                            if !matches!(owner.lookup_binding_ref(0),Some(EnvBinding::Free(f)) if *f==binder)
                                ||self.checked_binding_lineage.borrow().get(&owner.id()).is_some_and(Option::is_none){return false;}
                        }
                        types.push(*domain);types.push(*body);
                    },
                }continue;
            }
            if let Some(n)=neutrals.pop(){
                if !take_step(remaining){return false;}let n:Neutral=n;
                match n.head {
                    NeutralHead::Free(f,Some(owner))=>{
                        if !matches!(owner.lookup_binding_ref(0),Some(EnvBinding::Free(actual)) if *actual==f)
                            ||self.checked_binding_lineage.borrow().get(&owner.id()).is_some_and(Option::is_none){return false;}
                    },
                    NeutralHead::Free(_,None)=>return false,
                    NeutralHead::Projection{structure,..}=>neutrals.push(*structure),
                    NeutralHead::Const{..}=>{},
                }
                closures.extend(n.spine);continue;
            }
            let Some(c)=closures.pop() else{return true;};
            if !take_step(remaining){return false;}if !seen_closures.insert(c.clone()){continue;}
            let Some(support)=self.complete_source_support(c.expr,remaining) else{return false;};
            for index in support {
                let Some(owner)=self.source_capture_owner(&c.env,index,remaining) else{return false;};
                if !take_step(remaining){return false;}
                let witness=self.checked_binding_lineage.borrow().get(&owner.id()).cloned();
                if witness.as_ref().is_some_and(Option::is_none){return false;}
                if seen_nodes.insert(owner.id()) {if let Some(Some(w))=witness{types.push(w.domain);}}
                match owner.lookup_binding_ref(0) {
                    Some(EnvBinding::Closure(c))=>closures.push(c.clone()),
                    Some(EnvBinding::Neutral(n))=>neutrals.push(n.clone()),
                    Some(EnvBinding::Free(_)|EnvBinding::NatLit(_))=>{},None=>return false,
                }
            }
        }
    }
    pub(crate) fn reopen_fixed_pi_body_owned(&self,body:&TypeValue,binder:FreeId,original:&EnvFrame,target:&EnvFrame,remaining:&mut usize)->Option<TypeValue> {
        if !matches!(original.lookup_binding_ref(0),Some(EnvBinding::Free(f)) if *f==binder){return None;}
        let ledger=self.checked_binding_lineage.borrow();
        if ledger.get(&original.id()).is_some_and(Option::is_none)||ledger.get(&target.id()).is_some_and(Option::is_none){return None;}drop(ledger);
        if let Some(bvar)=self.expressions.iter_raw().find_map(|(id,e)|matches!(e,Expr::BVar(0)).then_some(ExprId(id))) {
            return self.instantiate_fixed_pi_body_owned(body,binder,original,&Closure::new(bvar,target.clone()),remaining);
        }
        // No replacement syntax is necessary for an independently checked
        // capture-independent body. A dependent body still declines.
        if !self.owned_pi_reclosure_capture_valid(body,remaining){return None;}
        (self.type_depends_on_free_paid(body,binder,remaining)==Some(false)).then(||body.clone())
    }
    fn instantiate_fixed_pi_body_owned(&self,body:&TypeValue,binder:FreeId,original:&EnvFrame,actual:&Closure,remaining:&mut usize)->Option<TypeValue> {
        if !matches!(original.lookup_binding_ref(0),Some(EnvBinding::Free(f)) if *f==binder)
            ||self.checked_binding_lineage.borrow().get(&original.id()).is_some_and(Option::is_none)
            ||!self.owned_pi_reclosure_capture_valid(body,remaining){return None;}
        if self.type_depends_on_free_paid(body,binder,remaining)==Some(false){return Some(body.clone());}
        if !take_step(remaining){return None;}
        match body {
            TypeValue::Sort(level)=>Some(TypeValue::Sort(level.clone())),
            TypeValue::Term(term)=>Some(TypeValue::Term(term.substitute_local_free_from_owner(binder,original,actual,remaining)?)),
            TypeValue::Pi{domain,body,binder:inner,binder_owner}=>{
                if *inner!=binder&&self.type_depends_on_free_paid(&TypeValue::Term(actual.clone()),*inner,remaining)!=Some(false){return None;}
                let domain=self.instantiate_fixed_pi_body_owned(domain,binder,original,actual,remaining)?;
                let body=if binder_owner.as_ref()==Some(original){(**body).clone()}else{self.instantiate_fixed_pi_body_owned(body,binder,original,actual,remaining)?};
                Some(TypeValue::Pi{domain:Box::new(domain),body:Box::new(body),binder:*inner,binder_owner:binder_owner.clone()})
            },
        }
    }
    // Both callers have just inferred the actual function and checked its
    // actual argument against this domain. This is typed substitution, not
    // a conversion or a context reconstruction from numeric variable ids.
    fn instantiate_checked_fixed_pi_body(&self,body:&TypeValue,binder:FreeId,owner:Option<&EnvFrame>,domain:&TypeValue,actual:&Closure,context:&[TypeValue],caller_frame:&EnvFrame,remaining:&mut usize)->Option<TypeValue>{
        fn transform(c:&TypeChecker<'_>,ty:&TypeValue,source:&[TypeValue],target:&[TypeValue],target_frame:&EnvFrame,session:&mut crate::value::OwnedTypeSubstitution,records:&mut Vec<(EnvFrame,CheckedBinderWitness,EnvFrame,Rc<Vec<TypeValue>>)>,remaining:&mut usize)->Option<TypeValue>{
            if !take_step(remaining){return None;}
            match ty {
                TypeValue::Sort(level)=>Some(TypeValue::Sort(level.clone())),
                TypeValue::Term(term)=>Some(TypeValue::Term(session.closure(term,remaining)?)),
                TypeValue::Pi{domain,body,binder,binder_owner}=>{
                    let original=binder_owner.as_ref()?;
                    if fresh_local(source.len())!=Some(*binder) || !matches!(original.lookup_binding_ref(0),Some(EnvBinding::Free(f)) if f==binder){return None;}
                    let witness=c.checked_binding_lineage.borrow().get(&original.id()).cloned().flatten()?;
                    let mut old_extended=source.to_vec();old_extended.push((**domain).clone());
                    if witness.domain!=**domain || witness.protected_prefix.as_slice()!=old_extended.as_slice(){return None;}
                    let new_domain=transform(c,domain,source,target,target_frame,session,records,remaining)?;
                    let new_free=fresh_local(target.len())?;
                    let parent=session.frame(&original.parent_frame()?,remaining)?;
                    let new_owner=parent.extend_free_paid(new_free,remaining)?;
                    session.bind(original,new_owner.clone())?;
                    let mut new_extended=target.to_vec();new_extended.push(new_domain.clone());
                    let new_body=transform(c,body,&old_extended,&new_extended,&new_owner,session,records,remaining)?;
                    records.push((new_owner.clone(),CheckedBinderWitness{domain:new_domain.clone(),protected_prefix:Rc::new(new_extended)},target_frame.clone(),Rc::new(target.to_vec())));
                    Some(TypeValue::Pi{domain:Box::new(new_domain),body:Box::new(new_body),binder:new_free,binder_owner:Some(new_owner)})
                }
            }
        }
        let enhanced=(||{
            if !self.strict_origin_probe && std::env::var_os("NUCLEUS_EXPERIMENTAL_TYPED_LINEAGE").is_none(){return None;}
            if !matches!(body,TypeValue::Pi{..}){return None;}
            let original=owner?;
            if !matches!(original.lookup_binding_ref(0),Some(EnvBinding::Free(f)) if *f==binder){return None;}
            let witness=self.checked_binding_lineage.borrow().get(&original.id()).cloned().flatten()?;
            let n=witness.protected_prefix.len().checked_sub(1)?;
            if witness.domain!=*domain || witness.protected_prefix.last()!=Some(domain)
                || fresh_local(n)!=Some(binder) || context!=&witness.protected_prefix[..n]{return None;}
            let frame_matches=match self.checked_binding_lineage.source_context(original.id()) {
                Some((source_frame,source_context))=>source_frame==*caller_frame && source_context.as_slice()==context,
                None=>original.parent_frame().as_ref()==Some(caller_frame),
            };
            if !frame_matches || !self.owned_pi_reclosure_capture_valid(body,remaining){return None;}
            if self.owned_goal_dependencies(actual,actual,context,remaining).is_none(){return None;}
            let mut observations=HashMap::new();
            if !self.collect_substitution_authority(actual,remaining,&mut observations)
                || !self.collect_substitution_type_authority(body,remaining,&mut observations)
                || !self.collect_substitution_type_authority(domain,remaining,&mut observations){return None;}
            for ty in witness.protected_prefix.iter(){if !self.collect_substitution_type_authority(ty,remaining,&mut observations){return None;}}
            let (mut session,replacement)=crate::value::OwnedTypeSubstitution::new(original,actual,remaining)?;
            let mut records=vec![(replacement,CheckedBinderWitness{domain:domain.clone(),protected_prefix:Rc::new(context.to_vec())},caller_frame.clone(),Rc::new(context.to_vec()))];
            let result=transform(self,body,&witness.protected_prefix,context,caller_frame,&mut session,&mut records,remaining)?;
            // Preserve every original wrapper/owner state before publishing.
            // No partial reclosure manufactures a checked binder witness.
            for frame in session.observed {
                if !take_step(remaining){return None;}
                let state=self.checked_binding_lineage.borrow().get(&frame.id()).cloned();
                if state.as_ref().is_some_and(Option::is_none){return None;}
                observations.insert(frame.id(),(frame,state));
            }
            let observations:Vec<_>=observations.into_values().collect();
            if observations.len()>128 || records.len()>128{return None;}
            let cost=records.len().checked_mul(observations.len()+context.len()+1)?;
            if *remaining<cost{return None;}*remaining-=cost;
            for (frame,_,source_frame,source_context) in &records {self.checked_binding_lineage.derive(frame.id(),observations.clone(),source_frame.clone(),source_context.clone());}
            for (frame,witness,_,_) in records {self.retain_shared_checked_binding(&frame,witness.domain,witness.protected_prefix);}
            #[cfg(feature="diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_TYPED_SUBSTITUTION").is_some(){eprintln!("CHECKED_TYPE_SUBSTITUTION original={} caller={} source={} remaining={remaining}",original.id(),context.len(),n);}
            Some(result)
        })();
        enhanced.or_else(||self.instantiate_fixed_pi_body_carried(body,binder,owner,actual,remaining))
    }

    fn instantiate_fixed_pi_body_carried(&self,body:&TypeValue,binder:FreeId,owner:Option<&EnvFrame>,actual:&Closure,remaining:&mut usize)->Option<TypeValue> {
        match owner {Some(owner)=>self.instantiate_fixed_pi_body_owned(body,binder,owner,actual,remaining),None=>None}
    }
    pub(crate) fn reopen_fixed_pi_body(
        &self,
        body: &TypeValue,
        binder: FreeId,
        fresh: FreeId,
        remaining: &mut usize,
    ) -> Option<TypeValue> {
        if binder == fresh {
            return Some(body.clone());
        }
        fn target_binder_present(ty: &TypeValue, target: FreeId, fuel: &mut usize) -> Option<bool> {
            if !take_step(fuel) {
                return None;
            }
            match ty {
                TypeValue::Pi { domain, body, binder , binder_owner,} => Some(
                    *binder == target
                        || target_binder_present(domain, target, fuel)?
                        || target_binder_present(body, target, fuel)?,
                ),
                TypeValue::Sort(_) | TypeValue::Term(_) => Some(false),
            }
        }
        if target_binder_present(body, fresh, remaining)? {
            return None;
        }
        // Do not capture an unrelated local or an inner binder already
        // using the target identity. An unproved absence stays UNKNOWN.
        if self.type_depends_on_free(body, fresh, (*remaining).min(4096)) != Some(false) {
            return None;
        }
        let bvar = self.expressions.iter_raw().find_map(|(id, expression)| {
            matches!(expression, Expr::BVar(0)).then_some(ExprId(id))
        })?;
        let actual = Closure::new(bvar, EnvFrame::empty().extend_free(fresh));
        self.instantiate_fixed_pi_body(body, binder, &actual, remaining)
    }

    // A numeric inferred binder is usable only when its actually USED
    // source captures identify one coherent original introduction.
    fn unique_used_free_origin(&self,term:&Closure,source:FreeId,remaining:&mut usize)->Option<Option<EnvFrame>> {
        let mut pending=vec![term.clone()];let mut seen=std::collections::HashSet::new();
        let mut target:Option<EnvFrame>=None;
        while let Some(term)=pending.pop() {
            if !take_step(remaining){return None;}
            if !seen.insert(term.clone()){continue;}
            for index in self.complete_source_support(term.expr,remaining)? {
                let wrapper=self.source_capture_owner(&term.env,index,remaining)?;
                let original=match wrapper.lookup_binding_ref(0)? {
                    EnvBinding::Free(free) if *free==source=>Some(wrapper.clone()),
                    EnvBinding::Neutral(Neutral{head:NeutralHead::Free(free,Some(owner)),spine}) if *free==source&&spine.is_empty()=>{
                        if !matches!(owner.lookup_binding_ref(0),Some(EnvBinding::Free(actual)) if *actual==source){return None;}
                        Some(owner.clone())
                    },
                    EnvBinding::Closure(c)=>{pending.push(c.clone());None},
                    EnvBinding::Neutral(Neutral{head:NeutralHead::Free(free,None),..}) if *free==source=>return None,
                    EnvBinding::Neutral(n) if !n.spine.is_empty()=>return None,
                    _=>None,
                };
                if let Some(original)=original {
                    let ledger=self.checked_binding_lineage.borrow();
                    if ledger.get(&wrapper.id()).is_some_and(Option::is_none)
                        ||ledger.get(&original.id()).is_some_and(Option::is_none){return None;}
                    if target.as_ref().is_some_and(|t|t!=&original){return None;}
                    target=Some(original);
                }
            }
        }Some(target)
    }

    fn instantiate_fixed_pi_body(
        &self,
        body: &TypeValue,
        binder: FreeId,
        actual: &Closure,
        remaining: &mut usize,
    ) -> Option<TypeValue> {
        // A checked, bounded support result allows a literal transport.
        // In particular, closed codomains of very deep beta ladders must
        // not pay to rebuild irrelevant lexical environments.
        if self.type_depends_on_free(body, binder, (*remaining).min(4096)) == Some(false) {
            return Some(body.clone());
        }
        if *remaining == 0 {
            return None;
        }
        *remaining -= 1;
        match body {
            TypeValue::Sort(level) => Some(TypeValue::Sort(level.clone())),
            TypeValue::Term(term) => {
                let Some(owner)=self.unique_used_free_origin(term,binder,remaining)? else{return Some(body.clone());};
                Some(TypeValue::Term(term.substitute_local_free_from_owner(binder,&owner,actual,remaining)?))
            },
            TypeValue::Pi { domain, body, binder: inner , binder_owner,} => {
                // A stored function may retain a binder from a shallower
                // scope. Its identity must not capture a free local in the
                // caller's actual argument. Unknown support declines reuse.
                if *inner != binder
                    && self.type_depends_on_free(
                        &TypeValue::Term(actual.clone()), *inner, (*remaining).min(4096),
                    ) != Some(false)
                {
                    return None;
                }
                let domain = self.instantiate_fixed_pi_body(
                    domain, binder, actual, remaining,
                )?;
                // An inner binder of the same identity shadows this one in
                // its body. In Nucleus's level-indexed locals, such an alias
                // is unusual but must not cause capture.
                let body = if *inner == binder {
                    (**body).clone()
                } else {
                    self.instantiate_fixed_pi_body(body, binder, actual, remaining)?
                };
                Some(TypeValue::Pi {
                    domain: Box::new(domain),
                    body: Box::new(body),
                    binder: *inner,
                 binder_owner: binder_owner.clone(),})
            }
        }
    }

    // Syntactic support of an inferred type, through its actual closures.
    // Only a proved absence skips substitution. Exhaustion remains conservative.
    fn type_depends_on_free(&self,ty:&TypeValue,free:FreeId,budget:usize)->Option<bool>{let mut remaining=budget;self.type_depends_on_free_paid(ty,free,&mut remaining)}
    fn type_depends_on_free_paid(&self, ty: &TypeValue, free: FreeId, remaining: &mut usize) -> Option<bool> {
        let budget=(*remaining).min(4096);
        struct Support<'a, 'b> {
            checker: &'a TypeChecker<'b>,
            free: FreeId,
            remaining: usize,
            cache: HashMap<(ExprId, u64, usize), bool>,
        }
        impl Support<'_, '_> {
            fn tick(&mut self) -> Option<()> {
                if self.remaining == 0 {
                    return None;
                }
                self.remaining -= 1;
                Some(())
            }
            fn ty(&mut self, ty: &TypeValue) -> Option<bool> {
                self.tick()?;
                match ty {
                    TypeValue::Sort(_) => Some(false),
                    TypeValue::Term(c) => self.closure(c),
                    TypeValue::Pi { domain, body, .. } => Some(self.ty(domain)? || self.ty(body)?),
                }
            }
            fn closure(&mut self, c: &Closure) -> Option<bool> {
                self.expr(c.expr, &c.env, 0)
            }
            fn neutral(&mut self, n: &Neutral) -> Option<bool> {
                self.tick()?;
                let head = match &n.head {
                    NeutralHead::Free(f, _) => *f == self.free,
                    NeutralHead::Const { .. } => false,
                    NeutralHead::Projection { structure, .. } => self.neutral(structure)?,
                };
                if head {
                    return Some(true);
                }
                for a in &n.spine {
                    if self.closure(a)? {
                        return Some(true);
                    }
                }
                Some(false)
            }
            fn expr(&mut self, e: ExprId, frame: &EnvFrame, depth: usize) -> Option<bool> {
                self.tick()?;
                let key = (e, frame.id(), depth);
                if let Some(answer) = self.cache.get(&key) {
                    return Some(*answer);
                }
                let found = match self.checker.expressions.get(e)? {
                    Expr::Sort(_) | Expr::Const { .. } | Expr::NatLit(_) | Expr::StrLit(_) => false,
                    Expr::BVar(k) => {
                        let k = usize::try_from(*k).ok()?;
                        if k < depth {
                            false
                        } else {
                            match frame.lookup(u64::try_from(k - depth).ok()?)? {
                                EnvBinding::Free(f) => f == self.free,
                                EnvBinding::NatLit(_) => false,
                                EnvBinding::Closure(c) => self.closure(&c)?,
                                EnvBinding::Neutral(n) => self.neutral(&n)?,
                            }
                        }
                    }
                    Expr::App { fun, arg } => {
                        self.expr(*fun, frame, depth)? || self.expr(*arg, frame, depth)?
                    }
                    Expr::Lam { domain, body } | Expr::Pi { domain, body } => {
                        self.expr(*domain, frame, depth)?
                            || self.expr(*body, frame, depth.checked_add(1)?)?
                    }
                    Expr::Let { ty, value, body } => {
                        self.expr(*ty, frame, depth)?
                            || self.expr(*value, frame, depth)?
                            || self.expr(*body, frame, depth.checked_add(1)?)?
                    }
                    Expr::Proj { structure, .. } => self.expr(*structure, frame, depth)?,
                };
                self.cache.insert(key, found);
                Some(found)
            }
        }
        let mut support=Support {checker:self,free,remaining:budget,cache:HashMap::new()};
        let result=support.ty(ty);*remaining-=budget-support.remaining;result
    }

    /// Infer the universe of a type in an already validated telescope.
    pub(crate) fn infer_sort_in_context(
        &self,
        expression: ExprId,
        context: &[TypeValue],
        frame: &EnvFrame,
        budget: usize,
    ) -> Judgment<LevelTerm> {
        let mut remaining = budget;
        let inferred = self.infer_in(
            expression,
            context,
            frame,
            &mut remaining,
            &mut HashMap::new(),
        );
        self.sort_level(inferred, remaining)
    }

    fn sort_level(&self, ty: Judgment<TypeValue>, budget: usize) -> Judgment<LevelTerm> {
        let ty = match ty {
            Judgment::Proven { value, .. } => value,
            Judgment::Refuted { obstruction } => return Judgment::Refuted { obstruction },
            Judgment::Unknown { residual } => return Judgment::Unknown { residual },
        };
        match ty {
            TypeValue::Sort(level) => Judgment::proven(level, "known-sort-level"),
            TypeValue::Term(closure) => {
                let machine = self.machine();
                let exposed = machine.expose(closure, Transparency::Reducible, budget);
                match exposed {
                    Judgment::Proven {
                        value: Value::Sort(level),
                        ..
                    } => Judgment::proven(level, "term-type-reduces-to-sort"),
                    Judgment::Proven { .. } => Judgment::refuted("term-type-is-rigid-nonsort"),
                    Judgment::Refuted { obstruction } => Judgment::Refuted { obstruction },
                    Judgment::Unknown { residual } => Judgment::Unknown { residual },
                }
            }
            TypeValue::Pi { .. } => Judgment::refuted("pi-value-is-not-a-sort"),
        }
    }

    fn pi_view(&self, ty: Judgment<TypeValue>, budget: usize) -> Option<(TypeValue, PiBody)> {
        let ty = ty.proven_value()?.clone();
        match ty {
            TypeValue::Pi { domain, body, binder , binder_owner,} => Some((*domain, PiBody::Fixed(binder, *body, binder_owner))),
            TypeValue::Term(closure) => {
                let machine = self.machine();
                let exposed = machine.expose(closure, Transparency::Reducible, budget);
                match exposed.proven_value()? {
                    Value::Pi { domain, body } => Some((
                        TypeValue::Term(domain.clone()),
                        PiBody::Closure(body.clone()),
                    )),
                    Value::NatLit(_)
                    | Value::Sort(_)
                    | Value::Lam { .. }
                    | Value::Neutral(_)
                    | Value::StuckProjection { .. } => None,
                }
            }
            TypeValue::Sort(_) => None,
        }
    }

    pub(crate) fn expression(&self, expression: ExprId) -> Option<&Expr> {
        self.expressions.get(expression)
    }

    pub(crate) fn captured_string_literal(&self, term: &Closure, budget: usize) -> Option<String> {
        self.environment.string_literal_type()?;
        let mut term = term.clone();
        for _ in 0..budget.min(64) {
            match self.expression(term.expr)? {
                Expr::StrLit(value) => return Some(value.clone()),
                Expr::BVar(index) => match term.env.lookup(*index)? {
                    EnvBinding::Closure(bound) => term = bound,
                    _ => return None,
                },
                Expr::Let { value, body, .. } => {
                    let value = term.sibling(*value, term.env.clone());
                    term = term.sibling(*body, term.env.extend(value));
                }
                Expr::Const { name, levels } if levels.is_empty() => {
                    let declaration = self.environment.get(*name)?;
                    if !declaration.level_params.is_empty() { return None; }
                    term = self.closure(declaration.value?, EnvFrame::empty());
                }
                _ => return None,
            }
        }
        None
    }

    /// Kernel proof irrelevance for a source-checked theorem application
    /// versus a lexical proof variable. This is a very small constructor of
    /// proof evidence, NOT a syntactic equation or identifier quotient.
    ///
    /// Both proof terms are independently typechecked in the SAME captured
    /// context, their actual dependent types must be definitionally
    /// convertible, and each type must independently be checked as Prop.
    ///
    /// The current verified residual uses nine open binders. Restricting
    /// to that context depth and one-argument theorem applications prevents
    /// needless speculative proof searches on unrelated large workloads.
    /// Independently typed proof irrelevance for the second argument of
    /// a source-certified dependent predicate application under a
    /// bounded lexical context. This method never assumes any two captured terms equal:
    /// each is typechecked in the same lexical context; each resulting
    /// type must independently be shown to inhabit Sort 0; and their
    /// dependent types must convert with the kernel-backed algorithm.
    ///
    /// Calls are made only after the SAME rigid predicate and its preceding
    /// argument have already been proved equal. If a premise is UNKNOWN,
    /// no new conversion is licensed.
    pub(crate) fn checked_proof_pair_in_bounded_context(
        &self,
        left: &Closure,
        right: &Closure,
        context: &[TypeValue],
        budget: usize,
    ) -> bool {
        if !(4..=24).contains(&context.len()) || budget < 1024 {
            return false;
        }
        let mut lf=2048;
        let Some(left_type)=self.infer_exact_closure_in_context(
            left,context,&mut lf,0
        ) else {return false};
        let mut rf=2048;
        let Some(right_type)=self.infer_exact_closure_in_context(
            right,context,&mut rf,0
        ) else {return false};
        let type_is_prop=|ty:&TypeValue|->bool{
            let TypeValue::Term(closure)=ty else {return false};
            let mut fuel=2048;
            let Some(formation)=self.infer_exact_closure_in_context(
                closure,context,&mut fuel,0
            ) else {return false};
            matches!(
                self.sort_level(
                    Judgment::proven(formation,"captured-proof-proposition-formation"),
                    fuel.min(1024),
                ),
                Judgment::Proven { value: LevelTerm::Zero, .. }
            )
        };
        if !type_is_prop(&left_type) || !type_is_prop(&right_type) {
            return false;
        }
        // The nested converter gets at most 512 steps. The qualifying rule
        // itself requires >=1024, preventing recursive self-licensing.
        let relation=crate::convert::convert_with_policy_in_context(
            self,&left_type,&right_type,512,
            crate::convert::DeltaPolicy::GuardedSemanticFallback,
            context.len(),context,
        );
        if !relation.is_proven() {
            return false;
        }
        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_CONTEXTUAL_PROOF_SPINE").is_some() {
            use std::sync::atomic::{AtomicUsize, Ordering};
            static COUNT: AtomicUsize=AtomicUsize::new(0);
            if COUNT.fetch_add(1,Ordering::Relaxed)<20 {
                eprintln!(
                    "NUCLEUS_CONTEXTUAL_PROOF_SPINE:checked:context={}:left_type={left_type:?}:right_type={right_type:?}:type_relation={relation:?}",
                    context.len(),
                );
            }
        }
        true
    }

    pub(crate) fn checked_proof_vs_local_in_context(
        &self,
        left: &Closure,
        right: &Closure,
        context: &[TypeValue],
        budget: usize,
    ) -> bool {
        if context.len() != 9 || budget < 256 {
            return false;
        }
        let probe=budget.min(2048);
        let left_value=self.machine().expose_for_conversion(
            left.clone(),Transparency::Reducible,probe.min(512),
        );
        let right_value=self.machine().expose_for_conversion(
            right.clone(),Transparency::Reducible,probe.min(512),
        );
        let (Some(Value::Neutral(left_neutral)),Some(Value::Neutral(right_neutral)))=
            (left_value.proven_value(),right_value.proven_value())
        else { return false };
        let theorem_local_shape =
            |theorem:&Neutral,local:&Neutral| -> bool {
                matches!(
                    &theorem.head,
                    NeutralHead::Const { levels, .. } if levels.is_empty()
                ) && theorem.spine.len()==1
                && matches!(&local.head,NeutralHead::Free(_, _))
                && local.spine.is_empty()
            };
        if !theorem_local_shape(left_neutral,right_neutral)
            && !theorem_local_shape(right_neutral,left_neutral)
        {
            return false;
        }
        let mut left_fuel=probe;
        let Some(left_type)=self.infer_exact_closure_in_context(
            left,context,&mut left_fuel,0
        ) else { return false };
        let mut right_fuel=probe;
        let Some(right_type)=self.infer_exact_closure_in_context(
            right,context,&mut right_fuel,0
        ) else { return false };
        let is_checked_prop = |ty:&TypeValue| -> bool {
            let TypeValue::Term(closure)=ty else {return false};
            let mut fuel=probe;
            let Some(type_type)=self.infer_exact_closure_in_context(
                closure,context,&mut fuel,0
            ) else {return false};
            matches!(
                self.sort_level(
                    Judgment::proven(type_type,"checked-proof-type-sort"),
                    fuel.min(1024)
                ),
                Judgment::Proven { value: LevelTerm::Zero, .. }
            )
        };
        if !is_checked_prop(&left_type) || !is_checked_prop(&right_type) {
            return false;
        }
        let converted=crate::convert::convert_with_policy_in_context(
            self,&left_type,&right_type,probe,
            crate::convert::DeltaPolicy::GuardedSemanticFallback,
            context.len(),context,
        );
        if !converted.is_proven() {
            return false;
        }
        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_CERTIFIED_PROOF_VS_LOCAL").is_some() {
            use std::sync::atomic::{AtomicUsize, Ordering};
            static PRINTED: AtomicUsize = AtomicUsize::new(0);
            if PRINTED.fetch_add(1,Ordering::Relaxed)<24 {
                eprintln!(
                    "NUCLEUS_CERTIFIED_PROOF_VS_LOCAL:proved:context=9:left_type={left_type:?}:right_type={right_type:?}:type_relation={converted:?}"
                );
            }
        }
        true
    }

    /// A conservatively checked counterpart of Flash's proof-relevance
    /// signature. A proof-valued constant argument can be erased from an
    /// equality obligation only when BOTH applications have independently
    /// typechecked arguments at convertible proposition domains.
    ///
    /// This deliberately validates the dependent Pi telescope on BOTH
    /// sides and checks every data argument. It never assumes that
    /// convertible *types* imply equality of non-proof data terms. Unknown
    /// premises return false, leaving the original conversion authoritative.
    pub(crate) fn certified_relevance_spine_congruence(
        &self,
        left: &Neutral,
        right: &Neutral,
        context: &[TypeValue],
        budget: usize,
        depth: usize,
    ) -> bool {
        if std::env::var_os("NUCLEUS_EXPERIMENTAL_RELEVANCE").is_none()
            || depth != context.len() || budget < 512
            || left.spine.is_empty() || left.spine.len() > 6
            || left.spine.len() != right.spine.len()
        {
            return false;
        }
        // No potential saving exists if every captured argument closure is
        // already byte-identical, so avoid expensive dependent inference.
        if left.spine.iter().zip(&right.spine).all(|(a,b)|a==b) {
            return false;
        }
        let (
            NeutralHead::Const { name: lname, levels: llevels },
            NeutralHead::Const { name: rname, levels: rlevels },
        ) = (&left.head, &right.head) else { return false };
        if lname != rname || llevels.len() != rlevels.len() {
            return false;
        }
        if !llevels.iter().zip(rlevels).all(|(a,b)|
            crate::level::level_equal(a.clone(), b.clone(), budget.min(256)).is_proven()
        ) { return false; }
        let Some(decl) = self.environment.get(*lname) else { return false };
        if decl.level_params.len() != llevels.len() { return false; }
        let ty_for = |levels: &Vec<LevelTerm>| TypeValue::Term(
            Closure::with_levels(
                decl.ty, EnvFrame::empty(), LevelSubstitution::new(
                    decl.level_params.iter().copied().zip(levels.iter().cloned()).collect()
                )
            )
        );
        let mut lhs_type=ty_for(llevels);
        let mut rhs_type=ty_for(rlevels);
        let probe=budget.min(2048);
        let mut skipped_proof=false;
        for (larg,rarg) in left.spine.iter().zip(&right.spine) {
            let Some((ldom,lbody))=self.pi_view(
                Judgment::proven(lhs_type,"relevance-typed-function"),probe,
            ) else { return false };
            let Some((rdom,rbody))=self.pi_view(
                Judgment::proven(rhs_type,"relevance-typed-function"),probe,
            ) else { return false };
            if !crate::convert::convert_with_policy_in_context(
                self,&ldom,&rdom,probe.min(512),
                crate::convert::DeltaPolicy::PreferredOnly,depth,context,
            ).is_proven() {return false}
            let mut lf=probe;
            let Some(larg_ty)=self.infer_exact_closure_in_context(
                larg,context,&mut lf,0,
            ) else {return false};
            let mut rf=probe;
            let Some(rarg_ty)=self.infer_exact_closure_in_context(
                rarg,context,&mut rf,0,
            ) else {return false};
            let check_ty=|actual:&TypeValue,expected:&TypeValue| {
                crate::convert::convert_with_policy_in_context(
                    self,actual,expected,probe.min(512),
                    crate::convert::DeltaPolicy::PreferredOnly,depth,context,
                ).is_proven()
            };
            if !check_ty(&larg_ty,&ldom) || !check_ty(&rarg_ty,&rdom) {
                return false;
            }
            let prop_domain=|dom:&TypeValue| {
                let TypeValue::Term(c)=dom else {return false};
                let mut f=probe;
                let Some(ty)=self.infer_exact_closure_in_context(c,context,&mut f,0)
                else {return false};
                matches!(
                    self.sort_level(
                        Judgment::proven(ty,"checked-relevance-domain"),f.min(1024)
                    ),
                    Judgment::Proven {value:LevelTerm::Zero,..}
                )
            };
            if prop_domain(&ldom) && prop_domain(&rdom) {
                skipped_proof=true;
            } else if !crate::convert::convert_with_policy_in_context(
                self,
                &TypeValue::Term(larg.clone()),
                &TypeValue::Term(rarg.clone()),
                probe.min(512),
                crate::convert::DeltaPolicy::PreferredOnly,
                depth,context,
            ).is_proven() {
                return false;
            }
            let next = |body:PiBody,arg:&Closure| -> Option<TypeValue> {
                match body {
                    PiBody::Fixed(binder,ty, owner) => {
                        let mut f=probe;
                        self.instantiate_fixed_pi_body_carried(&ty,binder,owner.as_ref(),arg,&mut f)
                    }
                    PiBody::Closure(body) => Some(TypeValue::Term(
                        Closure::with_levels(body.expr,body.env.extend(arg.clone()),body.levels)
                    )),
                }
            };
            let Some(lty)=next(lbody,larg) else {return false};
            let Some(rty)=next(rbody,rarg) else {return false};
            lhs_type=lty;
            rhs_type=rty;
        }
        if skipped_proof {
            #[cfg(feature="diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_CHECKED_RELEVANCE").is_some() {
                use std::sync::atomic::{AtomicUsize, Ordering};
                static EARNED:AtomicUsize=AtomicUsize::new(0);
                if EARNED.fetch_add(1,Ordering::Relaxed)<40 {
                    eprintln!(
                        "NUCLEUS_CHECKED_RELEVANCE:head={lname:?}:spine={}:depth={depth}:budget={budget}:verified_proof_erasures=true",
                        left.spine.len()
                    );
                }
            }
        }
        skipped_proof
    }

    pub(crate) fn proof_terms_same_proposition(
        &self,
        left: &Closure,
        right: &Closure,
        context: &[TypeValue],
        budget: usize,
    ) -> bool {
        let Some(left_value) = self
            .machine()
            .expose_for_conversion(left.clone(), Transparency::Reducible, budget)
            .proven_value()
            .cloned()
        else {
            return false;
        };
        let Some(right_value) = self
            .machine()
            .expose_for_conversion(right.clone(), Transparency::Reducible, budget)
            .proven_value()
            .cloned()
        else {
            return false;
        };
        let (Value::Neutral(left_neutral), Value::Neutral(right_neutral)) =
            (&left_value, &right_value)
        else {
            return false;
        };

        let Some(left_ty) = self.neutral_result_type(left_neutral, context, budget) else {
            return false;
        };
        let Some(right_ty) = self.neutral_result_type(right_neutral, context, budget) else {
            return false;
        };
        let Some(left_normal) = self.normalize_type_value(&left_ty, budget) else {
            return false;
        };
        let Some(right_normal) = self.normalize_type_value(&right_ty, budget) else {
            return false;
        };
        left_normal == right_normal
            && self.normalized_type_is_proposition(&left_normal, context, budget, 0)
    }

    fn normalize_type_value(&self, ty: &TypeValue, budget: usize) -> Option<Value> {
        match ty {
            TypeValue::Sort(level) => Some(Value::Sort(level.clone())),
            TypeValue::Term(closure) => self
                .machine()
                .expose(closure.clone(), Transparency::Reducible, budget)
                .proven_value()
                .cloned(),
            TypeValue::Pi { .. } => None,
        }
    }

    fn normalized_type_is_proposition(
        &self,
        value: &Value,
        context: &[TypeValue],
        budget: usize,
        depth: usize,
    ) -> bool {
        if depth >= 16 || budget == 0 {
            return false;
        }
        let Value::Neutral(neutral) = value else {
            return false;
        };
        let Some(ty) = self.neutral_result_type(neutral, context, budget - 1) else {
            return false;
        };
        let Some(normal) = self.normalize_type_value(&ty, budget - 1) else {
            return false;
        };
        match normal {
            Value::Sort(LevelTerm::Zero) => true,
            Value::Neutral(_) if normal != *value => {
                self.normalized_type_is_proposition(&normal, context, budget - 1, depth + 1)
            }
            _ => false,
        }
    }

    fn normalized_type_is_definitely_nonproposition(
        &self,
        value: &Value,
        context: &[TypeValue],
        budget: usize,
        depth: usize,
    ) -> bool {
        if depth >= 16 || budget == 0 {
            return false;
        }
        let Value::Neutral(neutral) = value else {
            return false;
        };
        let Some(ty) = self.neutral_result_type(neutral, context, budget - 1) else {
            return false;
        };
        let Some(normal) = self.normalize_type_value(&ty, budget - 1) else {
            return false;
        };
        match normal {
            Value::Sort(LevelTerm::Succ(_)) => true,
            Value::Neutral(_) if normal != *value => self
                .normalized_type_is_definitely_nonproposition(
                    &normal,
                    context,
                    budget - 1,
                    depth + 1,
                ),
            _ => false,
        }
    }

    fn neutral_result_type(
        &self,
        neutral: &crate::value::Neutral,
        context: &[TypeValue],
        budget: usize,
    ) -> Option<TypeValue> {
        let mut current = match &neutral.head {
            NeutralHead::Free(free, _) => {
                let index = usize::try_from(free.0).ok()?;
                context.get(index)?.clone()
            }
            NeutralHead::Const { name, levels } => {
                let declaration = self.environment.get(*name)?;
                if declaration.level_params.len() != levels.len() {
                    return None;
                }
                let substitution = declaration
                    .level_params
                    .iter()
                    .copied()
                    .zip(levels.iter().cloned())
                    .collect::<Vec<_>>();
                TypeValue::Term(Closure::with_levels(
                    declaration.ty,
                    EnvFrame::empty(),
                    LevelSubstitution::new(substitution),
                ))
            }
            NeutralHead::Projection { .. } => return None,
        };

        for argument in &neutral.spine {
            let (domain, body) =
                self.pi_view(Judgment::proven(current, "proof-type-spine"), budget)?;
            let _ = domain;
            current = match body {
                PiBody::Fixed(binder, body, owner) => {
                    let mut fuel = budget;
                    self.instantiate_fixed_pi_body_carried(&body, binder, owner.as_ref(), argument, &mut fuel)?
                },
                PiBody::Closure(body) => TypeValue::Term(Closure::with_levels(
                    body.expr,
                    body.env.extend(argument.clone()),
                    body.levels,
                )),
            };
        }
        Some(current)
    }

    /// Diagnostic-only proof-obligation separator. Unlike simply looking at
    /// the instantiated result type, this walks a neutral's actual source
    /// telescope and checks *every* captured argument against its dependent
    /// Pi domain. This can identify the earliest missing typing witness
    /// without allowing observational similarity to become kernel equality.
    ///
    /// This emits evidence only. No caller may use the resulting string to
    /// authorize ACCEPT/REJECT.
    /// An exact source-origin replay of a neutral's dependent telescope.
    /// A preserved binder witness carries its original checked context.
    /// Replay occurs under THAT context, not a synthetic empty caller scope.
    /// No derived result is installed in the production checker.
    #[cfg(feature = "diagnostics")]
    fn diagnostic_one_source_lambda_body(
        &self,
        lambda: &Closure,
        context: &[TypeValue],
        budget: usize,
    ) -> String {
        let Some(Expr::Lam { domain, body })=self.expressions.get(lambda.expr)
        else {return "not-source-lambda".into()};
        // Diagnostic-only: the captured source may have introduced FreeId(6)
        // before this lambda was opened. Reusing the caller's six-binder
        // context and assigning FreeId(6) again conflates TWO DIFFERENT
        // immutable binder nodes. Instead recover the deepest compatible,
        // source-checked prefix from actual captured Free bindings.
        // Never invent a type from its numeric FreeId or expected Pi domain.
        let caller_depth=context.len();
        let mut recovered_context=context.to_vec();
        let mut recovered_node=None;
        for index in 0..64u64 {
            let Some((node,binding))=lambda.env.lookup_with_node_id(index)
                else {break};
            if !matches!(binding,EnvBinding::Free(_)) {continue}
            let record=self.checked_binding_lineage.borrow()
                .get(&node).cloned().flatten();
            let Some(record)=record else {continue};
            if record.protected_prefix.len()<=context.len() {continue}
            if !record.protected_prefix.starts_with(context) {
                return format!(
                    "source-lambda-captured-prefix-conflict:node={node}:depth={}",
                    record.protected_prefix.len(),
                );
            }
            if record.protected_prefix.len()>recovered_context.len() {
                if !record.protected_prefix.starts_with(&recovered_context) {
                    return format!("source-lambda-incompatible-captured-prefixes:node={node}");
                }
                recovered_context=record.protected_prefix.as_ref().clone();
                recovered_node=Some(node);
            } else if !recovered_context.starts_with(&record.protected_prefix) {
                return format!("source-lambda-incompatible-captured-prefixes:node={node}");
            }
        }
        let context=recovered_context.as_slice();
        let checked_domain=lambda.sibling(*domain,lambda.env.clone());
        let mut remaining=budget.min(512);
        let Some(dty)=self.infer_exact_closure_in_context(
            &checked_domain,context,&mut remaining,0,
        ) else{return "lambda-source-domain-type-UNKNOWN".into()};
        if !self.sort_level(
            Judgment::proven(dty,"source-checked-captured-lambda"),
            remaining.min(256),
        ).is_proven(){return "lambda-source-domain-sort-UNKNOWN".into()}
        let Some(fresh)=u64::try_from(context.len()).ok().map(FreeId)
        else{return "lambda-source-binder-overflow".into()};
        let mut extended=context.to_vec();
        extended.push(TypeValue::Term(checked_domain.clone()));
        let frame=lambda.env.extend_free(fresh);
        self.retain_checked_elimination(
            &frame,TypeValue::Term(checked_domain),&extended,
        );
        let body_source=lambda.sibling(*body,frame);
        let exposed=self.machine().expose(
            body_source.clone(),Transparency::Opaque,remaining.min(512),
        );
        // Separate the source-bound *proof/data* classification from the
        // η binder introduced after it. A FreeId in a proof argument is
        // not licensed for erasure until the enclosing proposition and any
        // replacement proof are checked in the same source scope.
        let extra=FreeId(u64::try_from(caller_depth).unwrap_or(u64::MAX));
        let extra_domain_kind=context.get(caller_depth).and_then(|ty| {
            let TypeValue::Term(closure)=ty else {return None};
            let mut fuel=512;
            let kind=self.infer_exact_closure_in_context(
                closure,&context[..caller_depth],&mut fuel,0,
            )?;
            Some(self.sort_level(Judgment::proven(kind,"source-binder-domain-kind"),512))
        });
        let detail=match exposed.proven_value() {
            Some(Value::Neutral(n)) => {
                let argument_census=n.spine.iter().enumerate().take(8)
                    .map(|(position,arg)| {
                        let support=self.type_depends_on_free(
                            &TypeValue::Term(arg.clone()),extra,1024,
                        );
                        let mut fuel=1024;
                        let actual_ty=self.infer_exact_closure_in_context(
                            arg,&extended,&mut fuel,0,
                        );
                        let argument_type_sort=actual_ty.as_ref().and_then(|ty| {
                            let TypeValue::Term(t)=ty else {return None};
                            let mut inner_fuel=512;
                            let kind=self.infer_exact_closure_in_context(
                                t,&extended,&mut inner_fuel,0,
                            )?;
                            Some(self.sort_level(Judgment::proven(kind,"exact-argument-kind"),512))
                        });
                        format!("{position}:depends-on-source={support:?}:type-kind={argument_type_sort:?}")
                    }).collect::<Vec<_>>();
                let telescope=self.diagnostic_neutral_source_telescope_inner(
                    n,&extended,remaining.min(512),false,
                );
                format!("source-argument-census={argument_census:?}:telescope={telescope}")
            }
            other=>format!("source-body-not-neutral:{other:?}"),
        };
        format!("source-lambda-domain-formed:body={:?}:source-context={}:opened-context={}:source-node={recovered_node:?}:extra-domain-kind={extra_domain_kind:?}:source-obligation={detail}",
            body_source.expr,context.len(),extended.len())
    }

    #[cfg(feature = "diagnostics")]
    fn diagnostic_lambda_source_premises(
        &self,
        lambda: &Closure,
        context: &[TypeValue],
        expected_type: &TypeValue,
        budget: usize,
    ) -> String {
        let Some(Expr::Lam { domain, body }) = self.expressions.get(lambda.expr)
        else { return "not-source-lambda".into() };
        let mut remaining=budget.min(512);
        let domain= lambda.sibling(*domain, lambda.env.clone());
        let Some(domain_type)=self.infer_exact_closure_in_context(
            &domain,context,&mut remaining,0,
        ) else {
            return format!("lambda-domain-untyped:source={:?}:frame={}",
                domain.expr,domain.env.id());
        };
        let domain_sort=self.sort_level(
            Judgment::proven(domain_type,"source-lambda-domain"),
            remaining.min(256),
        );
        if !domain_sort.is_proven() {
            return format!("lambda-domain-not-established-sort:source={:?}:sort={domain_sort:?}",
                domain.expr);
        }
        let Some(free_id)=u64::try_from(context.len()).ok().map(FreeId)
        else {return "lambda-binder-depth-overflow".into()};
        let mut body_context=context.to_vec();
        body_context.push(TypeValue::Term(domain.clone()));
        let body_frame=lambda.env.extend_free(free_id);
        self.retain_checked_elimination(
            &body_frame,TypeValue::Term(domain.clone()),&body_context,
        );
        let body_term=lambda.sibling(*body,body_frame);
        let mut body_budget=remaining.min(512);
        let body_type=self.infer_exact_closure_in_context(
            &body_term,&body_context,&mut body_budget,0,
        );
        let failing_app=if body_type.is_none() {
            if let Some(Expr::App { fun, arg }) =
                self.expressions.get(body_term.expr)
            {
                let f=body_term.sibling(*fun,body_term.env.clone());
                let a=body_term.sibling(*arg,body_term.env.clone());
                let mut fbudget=256;
                let fty=self.infer_exact_closure_in_context(
                    &f,&body_context,&mut fbudget,0,
                );
                let mut abudget=256;
                let aty=self.infer_exact_closure_in_context(
                    &a,&body_context,&mut abudget,0,
                );
                let fview=fty.as_ref().and_then(|ty| self.pi_view(
                    Judgment::proven(ty.clone(),"checked-source-lambda-function"),
                    fbudget.min(256),
                ));
                let binding = if let Some(Expr::BVar(index)) =
                    self.expressions.get(f.expr)
                {
                    let source=f.env.lookup_with_node_id(*index);
                    let certificate=self.checked_type_of_bound_source(
                        &f.env,*index,&body_context,
                    );
                    format!("function-bvar={index}:source={source:?}:certificate={certificate:?}")
                } else {
                    format!("function-source={:?}",self.expressions.get(f.expr))
                };
                let source_chain = if fty.is_none() {
                    let mut cursor=f.clone();
                    let mut seen=std::collections::HashSet::new();
                    let mut chain=Vec::new();
                    for _ in 0..12 {
                        if !seen.insert((cursor.expr,cursor.env.id())) {
                            chain.push("cycle".to_owned()); break;
                        }
                        match self.expressions.get(cursor.expr) {
                            Some(Expr::BVar(index)) => {
                                let bound=cursor.env.lookup_with_node_id(*index);
                                let (node,entry)=match bound {
                                    Some(pair)=>pair,
                                    None=>{
                                        chain.push(format!("unbound:{index}")); break;
                                    }
                                };
                                let record=self.checked_binding_lineage.borrow()
                                    .get(&node).cloned().flatten();
                                let scope=record.as_ref().map(|w|
                                    (w.protected_prefix.len(),
                                     body_context.starts_with(&w.protected_prefix))
                                );
                                chain.push(format!("BVar({index})@{}:node={node}:scope={scope:?}:value={entry:?}",
                                    cursor.env.id()));
                                if let EnvBinding::Closure(next)=entry {
                                    cursor=next;
                                } else {break}
                            }
                            other=>{
                                chain.push(format!("first-source-leaf:{:?}:shape={other:?}",cursor.expr));
                                break;
                            }
                        }
                    }
                    chain.join(" -> ").chars().take(2600).collect::<String>()
                } else {
                    "function-type-certified".into()
                };
                // Candidate η transport: the function behind body BVar1
                // comes from the OUTER capture, before the new lambda binder.
                // Verify its actual type under the same origin, then compare
                // it to the declared dependent minor-argument type. Neither
                // a source eta shape nor the recursor's expected type is by
                // itself a typing certificate.
                let eta_type_probe = if matches!(
                    self.expressions.get(*arg),Some(Expr::BVar(0))
                ) && matches!(
                    self.expressions.get(*fun),Some(Expr::BVar(1))
                ) {
                    let mut captured=f.clone();
                    let mut valid=true;
                    for _ in 0..16 {
                        let Some(Expr::BVar(idx))=self.expressions.get(captured.expr)
                        else {break};
                        match captured.env.lookup(*idx) {
                            Some(EnvBinding::Closure(next))=>captured=next,
                            _=>{valid=false;break}
                        }
                    }
                    if valid {
                        // The captured function retains a distinct, source-checked
                        // local after the six-binder caller prefix. Reconstruct
                        // the original context for typing; never compare terms
                        // under a guessed FreeId-equivalent scope.
                        let mut source_context=context.to_vec();
                        let mut origin_nodes=Vec::new();
                        let mut compatible=true;
                        for index in 0..64u64 {
                            let Some((node,binding))=captured.env.lookup_with_node_id(index)
                                else {break};
                            if !matches!(binding,EnvBinding::Free(_)) {continue}
                            let record=self.checked_binding_lineage.borrow()
                                .get(&node).cloned().flatten();
                            let Some(record)=record else {continue};
                            if record.protected_prefix.len()<=context.len() {continue}
                            if !record.protected_prefix.starts_with(context) {
                                compatible=false;break
                            }
                            if record.protected_prefix.len()>source_context.len() {
                                if !record.protected_prefix.starts_with(&source_context) {
                                    compatible=false;break
                                }
                                source_context=record.protected_prefix.as_ref().clone();
                            } else if !source_context.starts_with(&record.protected_prefix) {
                                compatible=false;break
                            }
                            origin_nodes.push(node);
                        }
                        let mut budget=2048;
                        let source_ty=if compatible {
                            self.infer_exact_closure_in_context(
                                &captured,&source_context,&mut budget,0,
                            )
                        } else { None };
                        // Comparison in the extended source scope is only a
                        // DIAGNOSTIC. Even if proven, shrinking back to the
                        // six-binder caller requires source-term strengthening
                        // or an independently checked substitution witness.
                        let relation=source_ty.as_ref().map(|ty|
                            crate::convert::convert_with_policy_in_context(
                                self,ty,expected_type,budget.min(512),
                                crate::convert::DeltaPolicy::PreferredOnly,
                                source_context.len(),&source_context,
                            )
                        );
                        // η works relative to the *fresh* binder opened
                        // by this minor lambda. It need not eliminate a
                        // different, earlier captured binder. Keep the latter
                        // in the source context and test the actual typed η
                        // premise there, without authorizing caller-scope reuse.
                        let eta_free=FreeId(u64::try_from(source_context.len()).unwrap_or(u64::MAX));
                        let eta_fresh_absent=self.type_depends_on_free(
                            &TypeValue::Term(captured.clone()),eta_free,2048,
                        );
                        let mut eta_fuel=2048;
                        let eta_minor_ty=if compatible {
                            self.infer_exact_closure_in_context(
                                lambda,&source_context,&mut eta_fuel,0,
                            )
                        } else {None};
                        let eta_type_relation=match (&eta_minor_ty,&source_ty) {
                            (Some(left),Some(right))=>Some(
                                crate::convert::convert_with_policy_in_context(
                                    self,left,right,eta_fuel.min(512),
                                    crate::convert::DeltaPolicy::PreferredOnly,
                                    source_context.len(),&source_context,
                                )),
                            _=>None,
                        };
                        let eta_term_relation=if compatible &&
                            eta_fresh_absent==Some(false) &&
                            eta_minor_ty.is_some() && source_ty.is_some()
                        {
                            Some(crate::convert::convert_with_policy_in_context(
                                self,&TypeValue::Term(lambda.clone()),
                                &TypeValue::Term(captured.clone()),512,
                                crate::convert::DeltaPolicy::PreferredOnly,
                                source_context.len(),&source_context,
                            ))
                        } else {None};
                        // Source-bound proof h : P may be eliminated only by
                        // an actually available checked proof of P at the
                        // six-binder caller, never by fabricating one.
                        let source_proposition=source_context.get(context.len());
                        let mut caller_proof_candidates=Vec::new();
                        if let Some(proposition)=source_proposition {
                            for (i,caller_ty) in context.iter().enumerate() {
                                let eq=crate::convert::convert_with_policy_in_context(
                                    self,caller_ty,proposition,512,
                                    crate::convert::DeltaPolicy::PreferredOnly,
                                    context.len(),context,
                                );
                                if eq.is_proven() {
                                    caller_proof_candidates.push(format!("FreeId({i}):type-equal"));
                                }
                            }
                        }
                        let mut captured_proof_candidates=Vec::new();
                        if let Some(proposition)=source_proposition {
                            for (label,frame) in [
                                ("minor", &lambda.env),("captured-function", &captured.env),
                            ] {
                                for index in 0..32u64 {
                                    let Some((node,binding))=frame.lookup_with_node_id(index)
                                        else {break};
                                    if node == 0 {continue}
                                    let candidate_ty=match binding {
                                        EnvBinding::Free(id) if id.0 < context.len() as u64 =>
                                            self.checked_type_of_bound_source(frame,index,context)
                                                .or_else(||context.get(id.0 as usize).cloned()),
                                        EnvBinding::Closure(value) => {
                                            let mut fuel=512;
                                            self.infer_exact_closure_in_context(
                                                &value,context,&mut fuel,0,
                                            )
                                        },
                                        _=>None,
                                    };
                                    if let Some(candidate_ty)=candidate_ty {
                                        let eq=crate::convert::convert_with_policy_in_context(
                                            self,&candidate_ty,proposition,256,
                                            crate::convert::DeltaPolicy::PreferredOnly,
                                            context.len(),context,
                                        );
                                        if eq.is_proven() {
                                            captured_proof_candidates.push(
                                                format!("{label}:index={index}:node={node}:same-P")
                                            );
                                        }
                                    }
                                }
                            }
                        }
                        // Decisive proof-parametricity separator. Hypothetically
                        // open a SECOND proof binder h' : P after the original
                        // checked source h : P; both contexts are well-formed
                        // only when P : Prop independently checks at the
                        // original six-binder prefix. Replacing h by h' must
                        // preserve typing, and comparison must be established
                        // by conversion, never by merely classifying arguments.
                        let proof_parametricity=(|| -> String {
                            if !compatible || source_context.len()!=context.len()+1 {
                                return "source-context-incompatible".into()
                            }
                            let Some(prop)=source_proposition.cloned() else {
                                return "source-proposition-not-found".into()
                            };
                            let TypeValue::Term(p_term)=&prop else {
                                return "source-proposition-not-term".into()
                            };
                            let mut sort_fuel=1024;
                            let Some(ptype)=self.infer_exact_closure_in_context(
                                p_term,context,&mut sort_fuel,0,
                            ) else{return "source-proposition-not-formed".into()};
                            let psort=self.sort_level(
                                Judgment::proven(ptype,"parametricity-source-proposition"),
                                sort_fuel.min(512),
                            );
                            if !matches!(psort,Judgment::Proven {value:LevelTerm::Zero,..}) {
                                return format!("source-proposition-not-Prop:{psort:?}")
                            }
                            let Some((raw,_))=self.expressions.iter_raw()
                                .find(|(_,e)|matches!(e,Expr::BVar(0))) else {
                                return "no-bvar-zero-expression".into()
                            };
                            let source_h=FreeId(context.len() as u64);
                            let second_h=FreeId(source_context.len() as u64);
                            let replacement_frame=EnvFrame::empty().extend_free(second_h);
                            let replacement=Closure::new(ExprId(raw),replacement_frame.clone());
                            let mut double_proof_context=source_context.clone();
                            double_proof_context.push(prop.clone());
                            self.retain_checked_elimination(
                                &replacement_frame,prop.clone(),&double_proof_context,
                            );
                            let mut subst_fuel=8192;
                            let Some(instantiated)=captured.substitute_local_free(
                                source_h,&replacement,&mut subst_fuel,
                            ) else{return "capture-safe-substitution-unknown".into()};
                            let mut original_fuel=2048;
                            let original_ty=self.infer_exact_closure_in_context(
                                &captured,&double_proof_context,&mut original_fuel,0,
                            );
                            let mut substituted_fuel=2048;
                            let substituted_ty=self.infer_exact_closure_in_context(
                                &instantiated,&double_proof_context,&mut substituted_fuel,0,
                            );
                            let type_equal=match (&original_ty,&substituted_ty) {
                                (Some(l),Some(r))=>Some(
                                    crate::convert::convert_with_policy_in_context(
                                        self,l,r,512,crate::convert::DeltaPolicy::PreferredOnly,
                                        double_proof_context.len(),&double_proof_context,
                                    )),
                                _=>None,
                            };
                            let term_equal=if type_equal.as_ref().is_some_and(|j|j.is_proven()) {
                                Some(crate::convert::convert_with_policy_in_context(
                                    self,&TypeValue::Term(captured.clone()),
                                    &TypeValue::Term(instantiated.clone()),2048,
                                    crate::convert::DeltaPolicy::PreferredOnly,
                                    double_proof_context.len(),&double_proof_context,
                                ))
                            } else {None};
                            format!(
                                "ctx={}:h={source_h:?}:h2={second_h:?}:subst-remaining={subst_fuel}:original-type={}:replaced-type={}:types-convert={type_equal:?}:terms-convert={term_equal:?}",
                                double_proof_context.len(),original_ty.is_some(),
                                substituted_ty.is_some(),
                            )
                        })();
                        let extra=FreeId(u64::try_from(context.len()).unwrap_or(u64::MAX));
                        let source_uses_extra=self.type_depends_on_free(
                            &TypeValue::Term(captured.clone()),extra,2048,
                        );
                        let source_type_uses_extra=source_ty.as_ref().and_then(|ty|
                            self.type_depends_on_free(ty,extra,2048)
                        );
                        let expected_uses_extra=self.type_depends_on_free(
                            expected_type,extra,2048,
                        );
                        let first_source_body=self.diagnostic_one_source_lambda_body(
                            &captured,context,remaining.min(512),
                        );
                        format!("eta-source={:?}:source-scope={}:origin-nodes={origin_nodes:?}:compatible={compatible}:source-type={source_ty:?}:source-vs-expected-in-source={relation:?}:eta-fresh={eta_free:?}:eta-fresh-absent={eta_fresh_absent:?}:eta-minor-type={eta_minor_ty:?}:eta-types-convert={eta_type_relation:?}:eta-terms-convert={eta_term_relation:?}:caller-proof-candidates={caller_proof_candidates:?}:captured-proof-candidates={captured_proof_candidates:?}:proof-parametricity={proof_parametricity}:extra-free={extra:?}:source-term-dep={source_uses_extra:?}:source-type-dep={source_type_uses_extra:?}:expected-type-dep={expected_uses_extra:?}:remaining={budget}:next={first_source_body}",
                            captured.expr,source_context.len())
                    } else {"eta-source-binding-unavailable".into()}
                } else {"not-eta-source-shape".into()};
                format!("lambda-body-app:fun={:?}:fun_type={fty:?}:arg={:?}:arg_type={aty:?}:pi_view_present={}:{}:source_chain={source_chain}:eta_obligation={eta_type_probe}",
                    f.expr,a.expr,fview.is_some(),binding)
            } else { "lambda-body-not-app".to_owned() }
        } else { "lambda-body-typed".to_owned() };
        format!(
            "lambda-domain-sort=PROVEN:ctx={}:opened={free_id:?}:body_expr={:?}:body_shape={:?}:body_type={body_type:?}:remaining={body_budget}:subjudgment={failing_app}",
            context.len(),body_term.expr,self.expressions.get(body_term.expr),
        )
    }

    /// Same exact origin witness can also be used to *diagnose* the complete
    /// enclosing recursor telescope. The origin is selected by an actual
    /// source-bound Free node inside the leaf, not by matching recursor names.
    /// This does not create a transport from the source scope to the caller.
    #[cfg(feature = "diagnostics")]
    fn diagnostic_outer_telescope_at_leaf_origin(
        &self,
        outer: &Neutral,
        leaf: &Neutral,
        caller_context: &[TypeValue],
        budget: usize,
    ) -> String {
        let mut origin: Option<Vec<TypeValue>> = None;
        for arg in &leaf.spine {
            let Some(Expr::BVar(index)) = self.expressions.get(arg.expr) else {
                continue;
            };
            let Some((node_id, EnvBinding::Free(_))) =
                arg.env.lookup_with_node_id(*index) else { continue };
            let witness = self.checked_binding_lineage.borrow()
                .get(&node_id).cloned().flatten();
            let Some(witness) = witness else { continue };
            let prefix = witness.protected_prefix;
            if !prefix.starts_with(caller_context) {
                return format!("origin-context-not-a-caller-extension:node={node_id}");
            }
            if let Some(prior) = &origin {
                if !(prior.starts_with(&prefix) || prefix.starts_with(prior)) {
                    return format!("multiple-incompatible-checked-origins:node={node_id}");
                }
            }
            if origin.as_ref().is_none_or(|v| prefix.len()>v.len()) {
                origin=Some(prefix.as_ref().clone());
            }
        }
        let Some(origin) = origin else { return "origin-not-certified".into() };
        if origin.len()<=caller_context.len() {
            return "origin-not-a-strict-extension".into();
        }
        let isolated=Self {
            expressions:self.expressions,
            levels:self.levels,
            environment:self.environment,
            level_substitution:self.level_substitution.clone(),
            delta_policy:self.delta_policy,
            exposure_cache:new_exposure_cache(),
            closed_spine_eligibility: RefCell::new(HashMap::new()),
            completed_pi_lifts: Rc::new(RefCell::new(std::collections::HashSet::new())),
            source_support: Rc::new(RefCell::new(HashMap::new())),
            source_capture_bindings: RefCell::new(HashMap::new()),
            owned_lambda_goals: RefCell::new(HashMap::new()),
            lambda_shape_ids: RefCell::new(HashMap::new()),
            lambda_shape_nodes: RefCell::new(HashMap::new()),
            owned_lambda_shapes: RefCell::new(HashMap::new()),
            paired_lambda_hint_facts: RefCell::new(HashMap::new()),
            owned_lambda_shape_domains: RefCell::new(HashMap::new()),
            repeated_completed_apps: RefCell::new(HashMap::new()),
            owned_application_patterns: RefCell::new(HashMap::new()),
            source_syntax_patterns: RefCell::new(HashMap::new()),
            source_syntax_pattern_nodes: RefCell::new(HashMap::new()),
            formed_lambda_goals: RefCell::new(HashMap::new()),
            paired_source_support: RefCell::new(HashMap::new()),
            checked_frames: RefCell::new(HashMap::new()),
            lambda_intro_scopes:Rc::new(RefCell::new(HashMap::new())),
            shared_expected_openings:Rc::new(RefCell::new(HashMap::new())),
            source_pi_openings:Rc::new(RefCell::new(HashMap::new())),
            proof_binder_transports:Rc::new(RefCell::new(HashMap::new())),
            proof_transport_context_keys:Rc::new(RefCell::new(std::collections::HashSet::new())),
            source_opening_proofs:RefCell::new(HashMap::new()),
            source_capture_free_support:Rc::new(RefCell::new(HashMap::new())),
            formed_expected: RefCell::new(std::collections::HashSet::new()),
            lambda_trials: RefCell::new(LambdaTrialState::default()),
            checked_binding_lineage:Rc::new(self.checked_binding_lineage.cloned()),
            checked_arguments: Rc::new(RefCell::new(HashMap::new())),
            binding_checks_active: Rc::new(RefCell::new(std::collections::HashSet::new())),
            strict_origin_probe:true,
        };
        // The directly visible leaf determines a checked six-binder
        // prefix. The fourth outer recursor argument is a lambda that closes
        // over a function; follow its ACTUAL BVar bindings to find an
        // additional source-checked proof binder. This is a context JOIN,
        // never permission to manufacture a missing proof or to identify
        // different local variables. This entire replay remains diagnostic.
        let mut joined=origin.clone();
        let mut join_trace=Vec::new();
        if let Some(minor)=outer.spine.get(3) {
            if let Some(Expr::Lam {body,..})=self.expressions.get(minor.expr) {
                if let Some(Expr::App {fun,..})=self.expressions.get(*body) {
                    let mut cursor=minor.sibling(
                        *fun,minor.env.extend_free(FreeId(u64::MAX)),
                    );
                    for _ in 0..16 {
                        if let Some(Expr::BVar(index))=self.expressions.get(cursor.expr) {
                            let Some((node,binding))=cursor.env.lookup_with_node_id(*index)
                                else {join_trace.push("unbound-capture".to_owned());break};
                            join_trace.push(format!("capture-node={node}"));
                            if let EnvBinding::Closure(next)=binding {
                                cursor=next;
                                continue
                            }
                            join_trace.push("nonclosure-capture".to_owned());
                            break
                        }
                        if !matches!(self.expressions.get(cursor.expr),Some(Expr::Lam {..})) {
                            join_trace.push("captured-function-not-source-lambda".to_owned());
                            break
                        }
                        join_trace.push(format!("source-function={:?}",cursor.expr));
                        for index in 0..64u64 {
                            let Some((node,binding))=cursor.env.lookup_with_node_id(index)
                                else {break};
                            if !matches!(binding,EnvBinding::Free(_)){continue}
                            let record=self.checked_binding_lineage.borrow()
                                .get(&node).cloned().flatten();
                            let Some(record)=record else {continue};
                            let prefix=record.protected_prefix;
                            if prefix.len()>joined.len() {
                                if !prefix.starts_with(&joined) {
                                    join_trace.push(format!("incompatible-source-node={node}"));
                                    return format!("source_origin_depth={}:result={result}:joined-source-scope-CONFLICT",
                                        origin.len(),result=isolated.diagnostic_neutral_source_telescope_inner(
                                            outer,&origin,budget.min(1024),false,
                                        ));
                                }
                                join_trace.push(format!("joined-node={node}:depth={}",prefix.len()));
                                joined=prefix.as_ref().clone();
                            } else if !joined.starts_with(&prefix) {
                                return "joined-source-prefix-CONFLICT".into()
                            }
                        }
                        break
                    }
                }
            }
        }
        let joined_replay=if joined.len()>origin.len() {
            Some(isolated.diagnostic_neutral_source_telescope_inner(
                outer,&joined,budget.min(1024),false,
            ))
        } else {None};
        // Once every dependent recursor argument is source-typed, inspect
        // the ACTUAL major and existing certified recursor-iota interface.
        // This is a decisive separator: source typing alone cannot license
        // a constructor iota reduction on an unknown major.
        let qualified_major = if joined_replay.as_ref().is_some_and(|s|
            s.starts_with("all-source-arguments-checked"))
        {
            let certified=match &outer.head {
                NeutralHead::Const{name,..} =>
                    isolated.environment.recursor_reduction(*name).is_some(),
                _=>false,
            };
            let major=outer.spine.last().map(|c|
                isolated.machine().expose(
                    c.clone(),Transparency::Full,512,
                ));
            let iota=isolated.machine().qualified_nested_recursor_result(
                outer,512,
            );
            format!("certified={certified}:major={}:registered-iota={}",
                format!("{major:?}").chars().take(1800).collect::<String>(),
                format!("{iota:?}").chars().take(1000).collect::<String>())
        } else {"recursor-not-fully-source-typed".into()};
        let result=isolated.diagnostic_neutral_source_telescope_inner(
            outer,&origin,budget.min(1024),false,
        );
        format!(
            "joined_source_depth={}:joined_telescope={joined_replay:?}:major_obligation={qualified_major}:join_trace={join_trace:?}:source_origin_depth={}:outer_arity={}:result={result}",
            joined.len(),origin.len(),outer.spine.len(),
        )
    }

    #[cfg(feature = "diagnostics")]
    fn diagnostic_neutral_origin_replay(
        &self,
        neutral: &Neutral,
        caller_context: &[TypeValue],
        budget: usize,
    ) -> String {
        let mut candidate: Option<Vec<TypeValue>> = None;
        for arg in &neutral.spine {
            let Some(Expr::BVar(index)) = self.expressions.get(arg.expr) else {
                continue;
            };
            let Some((node_id, EnvBinding::Free(_))) =
                arg.env.lookup_with_node_id(*index)
            else {
                continue;
            };
            let record = self.checked_binding_lineage.borrow()
                .get(&node_id).cloned().flatten();
            let Some(record) = record else { continue };
            // The candidate is from the exact immutable binder node.
            // It must extend (not replace) the caller's already checked
            // prefix. Conflicting origin contexts cannot be spliced.
            if !record.protected_prefix.starts_with(caller_context) {
                return format!("origin-prefix-conflict:node={node_id}");
            }
            if let Some(prior) = &candidate {
                if prior.len() > record.protected_prefix.len()
                    && !prior.starts_with(&record.protected_prefix)
                {
                    return format!("incompatible-origin-scopes:node={node_id}");
                }
                if record.protected_prefix.len() > prior.len()
                    && !record.protected_prefix.starts_with(prior)
                {
                    return format!("incompatible-origin-scopes:node={node_id}");
                }
            }
            if candidate.as_ref()
                .is_none_or(|p| record.protected_prefix.len() > p.len())
            {
                candidate = Some(record.protected_prefix.as_ref().clone());
            }
        }
        let Some(origin) = candidate else {
            return "no-source-checked-origin-prefix".into();
        };
        if origin.len() <= caller_context.len() {
            return "source-origin-does-not-extend-caller".into();
        }
        let isolated = Self {
            expressions: self.expressions,
            levels: self.levels,
            environment: self.environment,
            level_substitution: self.level_substitution.clone(),
            delta_policy: self.delta_policy,
            exposure_cache: new_exposure_cache(),
            closed_spine_eligibility: RefCell::new(HashMap::new()),
            completed_pi_lifts: Rc::new(RefCell::new(std::collections::HashSet::new())),
            source_support: Rc::new(RefCell::new(HashMap::new())),
            source_capture_bindings: RefCell::new(HashMap::new()),
            owned_lambda_goals: RefCell::new(HashMap::new()),
            lambda_shape_ids: RefCell::new(HashMap::new()),
            lambda_shape_nodes: RefCell::new(HashMap::new()),
            owned_lambda_shapes: RefCell::new(HashMap::new()),
            paired_lambda_hint_facts: RefCell::new(HashMap::new()),
            owned_lambda_shape_domains: RefCell::new(HashMap::new()),
            repeated_completed_apps: RefCell::new(HashMap::new()),
            owned_application_patterns: RefCell::new(HashMap::new()),
            source_syntax_patterns: RefCell::new(HashMap::new()),
            source_syntax_pattern_nodes: RefCell::new(HashMap::new()),
            formed_lambda_goals: RefCell::new(HashMap::new()),
            paired_source_support: RefCell::new(HashMap::new()),
            checked_frames: RefCell::new(HashMap::new()),
            lambda_intro_scopes:Rc::new(RefCell::new(HashMap::new())),
            shared_expected_openings:Rc::new(RefCell::new(HashMap::new())),
            source_pi_openings:Rc::new(RefCell::new(HashMap::new())),
            proof_binder_transports:Rc::new(RefCell::new(HashMap::new())),
            proof_transport_context_keys:Rc::new(RefCell::new(std::collections::HashSet::new())),
            source_opening_proofs:RefCell::new(HashMap::new()),
            source_capture_free_support:Rc::new(RefCell::new(HashMap::new())),
            formed_expected: RefCell::new(std::collections::HashSet::new()),
            lambda_trials: RefCell::new(LambdaTrialState::default()),
            checked_binding_lineage: Rc::new(self.checked_binding_lineage.cloned()),
            checked_arguments: Rc::new(RefCell::new(HashMap::new())),
            binding_checks_active: Rc::new(RefCell::new(std::collections::HashSet::new())),
            strict_origin_probe: true,
        };
        let replay = isolated.diagnostic_neutral_source_telescope_inner(
            neutral, &origin, budget.min(1024), false,
        );
        format!("source_origin_depth={}:typed_replay={}", origin.len(), replay)
    }

    #[cfg(feature = "diagnostics")]
    pub(crate) fn diagnostic_neutral_source_telescope(
        &self,
        neutral: &Neutral,
        context: &[TypeValue],
        budget: usize,
    ) -> String {
        self.diagnostic_neutral_source_telescope_inner(
            neutral, context, budget, true,
        )
    }

    #[cfg(feature = "diagnostics")]
    fn diagnostic_neutral_source_telescope_inner(
        &self,
        neutral: &Neutral,
        context: &[TypeValue],
        budget: usize,
        follow_source_leaf: bool,
    ) -> String {
        // Diagnostic evaluation must not mutate the live checker's typed
        // binding ledger or reduction cache. Start from the same checked
        // witness snapshot in an isolated checker, then discard all new
        // synthetic diagnostic certificates with that snapshot.
        let probe = Self {
            expressions: self.expressions,
            levels: self.levels,
            environment: self.environment,
            level_substitution: self.level_substitution.clone(),
            delta_policy: self.delta_policy,
            exposure_cache: new_exposure_cache(),
            closed_spine_eligibility: RefCell::new(HashMap::new()),
            completed_pi_lifts: Rc::new(RefCell::new(std::collections::HashSet::new())),
            source_support: Rc::new(RefCell::new(HashMap::new())),
            source_capture_bindings: RefCell::new(HashMap::new()),
            owned_lambda_goals: RefCell::new(HashMap::new()),
            lambda_shape_ids: RefCell::new(HashMap::new()),
            lambda_shape_nodes: RefCell::new(HashMap::new()),
            owned_lambda_shapes: RefCell::new(HashMap::new()),
            paired_lambda_hint_facts: RefCell::new(HashMap::new()),
            owned_lambda_shape_domains: RefCell::new(HashMap::new()),
            repeated_completed_apps: RefCell::new(HashMap::new()),
            owned_application_patterns: RefCell::new(HashMap::new()),
            source_syntax_patterns: RefCell::new(HashMap::new()),
            source_syntax_pattern_nodes: RefCell::new(HashMap::new()),
            formed_lambda_goals: RefCell::new(HashMap::new()),
            paired_source_support: RefCell::new(HashMap::new()),
            checked_frames: RefCell::new(HashMap::new()),
            lambda_intro_scopes:Rc::new(RefCell::new(HashMap::new())),
            shared_expected_openings:Rc::new(RefCell::new(HashMap::new())),
            source_pi_openings:Rc::new(RefCell::new(HashMap::new())),
            proof_binder_transports:Rc::new(RefCell::new(HashMap::new())),
            proof_transport_context_keys:Rc::new(RefCell::new(std::collections::HashSet::new())),
            source_opening_proofs:RefCell::new(HashMap::new()),
            source_capture_free_support:Rc::new(RefCell::new(HashMap::new())),
            formed_expected: RefCell::new(std::collections::HashSet::new()),
            lambda_trials: RefCell::new(LambdaTrialState::default()),
            checked_binding_lineage: Rc::new(self.checked_binding_lineage.cloned()),
            checked_arguments: Rc::new(RefCell::new(HashMap::new())),
            binding_checks_active: Rc::new(RefCell::new(std::collections::HashSet::new())),
            strict_origin_probe: self.strict_origin_probe,
        };
        let mut remaining = budget.min(1024);
        let mut current = match &neutral.head {
            NeutralHead::Const { name, levels } => {
                let Some(decl) = probe.environment.get(*name) else {
                    return format!("missing-declaration:head={name:?}");
                };
                if decl.level_params.len() != levels.len() {
                    return format!("universe-arity:head={name:?}");
                }
                TypeValue::Term(Closure::with_levels(
                    decl.ty,
                    EnvFrame::empty(),
                    LevelSubstitution::new(
                        decl.level_params.iter().copied()
                            .zip(levels.iter().cloned()).collect(),
                    ),
                ))
            }
            NeutralHead::Free(free, _) => {
                let Some(ty) = usize::try_from(free.0).ok()
                    .and_then(|i| context.get(i)).cloned()
                else {
                    return format!("missing-typed-local:free={free:?}");
                };
                ty
            }
            NeutralHead::Projection { .. } => {
                return "neutral-projection-telescope-not-yet-qualified".into();
            }
        };
        for (position, actual_arg) in neutral.spine.iter().enumerate() {
            let Some((domain, body)) = probe.pi_view(
                Judgment::proven(current.clone(), "source-typed-telescope"),
                remaining.min(512),
            ) else {
                return format!(
                    "first-missing-pi:argument={position}:function_type={current:?}"
                );
            };
            let Some(actual_type) = probe.infer_exact_closure_in_context(
                actual_arg, context, &mut remaining, 0,
            ) else {
                // Chase only the *actual* captured BVar bindings, never
                // equate de Bruijn indices across separately captured frames.
                // A first incomplete typing judgment is not a refutation.
                let mut cursor = actual_arg.clone();
                let mut seen = std::collections::HashSet::new();
                let mut stages = Vec::new();
                let warrant_status = |node: u64| -> String {
                    let ledger = probe.checked_binding_lineage.borrow();
                    match ledger.get(&node) {
                        None => "absent".to_owned(),
                        Some(None) => "conflicting".to_owned(),
                        Some(Some(w)) if context.starts_with(&w.protected_prefix) =>
                            format!("matched:prefix={}", w.protected_prefix.len()),
                        Some(Some(w)) =>
                            format!("scope-mismatch:expected-prefix={}:actual={}",
                                w.protected_prefix.len(), context.len()),
                    }
                };
                for _ in 0..12 {
                    if !seen.insert((cursor.expr, cursor.env.id())) {
                        stages.push("binding-cycle".to_owned());
                        break;
                    }
                    match probe.expressions.get(cursor.expr) {
                        Some(Expr::BVar(index)) => {
                            let known_type = probe.checked_type_of_bound_source(
                                &cursor.env, *index, context,
                            );
                            match cursor.env.lookup_with_node_id(*index) {
                                Some((node, EnvBinding::Closure(next))) => {
                                    stages.push(format!(
                                        "BVar({index}):node={node}:cert={}:warrant={}:next={:?}@{}",
                                        known_type.is_some(), warrant_status(node),
                                        next.expr, next.env.id(),
                                    ));
                                    cursor = next;
                                }
                                Some((node, binding)) => {
                                    stages.push(format!(
                                        "BVar({index}):node={node}:cert={}:warrant={}:terminal={binding:?}",
                                        known_type.is_some(), warrant_status(node),
                                    ));
                                    break;
                                }
                                None => {
                                    stages.push(format!("BVar({index}):unbound"));
                                    break;
                                }
                            }
                        }
                        other => {
                            let app_obligation = if let Some(Expr::App { fun, arg }) = other {
                                let f = cursor.sibling(*fun, cursor.env.clone());
                                let a = cursor.sibling(*arg, cursor.env.clone());
                                let mut fuel = 256;
                                let fty = probe.infer_exact_closure_in_context(
                                    &f, context, &mut fuel, 0,
                                );
                                match fty {
                                    None => "first_app_function_type=UNKNOWN".to_owned(),
                                    Some(function_type) => {
                                        match probe.pi_view(
                                            Judgment::proven(
                                                function_type, "diagnostic-typed-function",
                                            ),
                                            fuel.min(256),
                                        ) {
                                            None => "first_app_pi_view=UNKNOWN".to_owned(),
                                            Some((domain, _)) => {
                                                let aty = probe.infer_exact_closure_in_context(
                                                    &a, context, &mut fuel, 0,
                                                );
                                                match aty {
                                                    None => {
                                                        let origin=match probe.expressions.get(a.expr) {
                                                            Some(Expr::BVar(index))=>{
                                                                let binding=a.env.lookup_with_node_id(*index);
                                                                let checked=probe.checked_type_of_bound_source(
                                                                    &a.env,*index,context,
                                                                );
                                                                let scope=binding.as_ref().and_then(|(node,_)|
                                                                    probe.checked_binding_lineage.borrow()
                                                                        .get(node).cloned()
                                                                ).flatten().map(|w| {
                                                                    let first_difference=(0..w.protected_prefix.len().min(context.len()))
                                                                        .find(|&i|context[i]!=w.protected_prefix[i]);
                                                                    let conversion=first_difference.map(|idx| {
                                                                        let relation=crate::convert::convert_with_policy_in_context(
                                                                            &probe,
                                                                            &context[idx],&w.protected_prefix[idx],
                                                                            256,
                                                                            crate::convert::DeltaPolicy::GuardedSemanticFallback,
                                                                            idx,&context[..idx],
                                                                        );
                                                                        format!("position={idx}:relation={relation:?}:new={:?}:source={:?}",
                                                                            context[idx],w.protected_prefix[idx])
                                                                    });
                                                                    if std::env::var_os("NUCLEUS_TRACE_ORIGIN_REPLAY").is_some() {
                                                                        use std::sync::atomic::{AtomicUsize, Ordering};
                                                                        static SCOPE:AtomicUsize=AtomicUsize::new(0);
                                                                        if SCOPE.fetch_add(1,Ordering::Relaxed)<24 {
                                                                            eprintln!(
                                                                                "NUCLEUS_SOURCE_SCOPE_SEPARATOR:arg={:?}:original_depth={}:candidate_depth={}:first_difference={first_difference:?}:conversion={conversion:?}",
                                                                                a.expr,w.protected_prefix.len(),context.len(),
                                                                            );
                                                                        }
                                                                    }
                                                                    (w.protected_prefix.len(),
                                                                    context.starts_with(&w.protected_prefix),
                                                                    first_difference,conversion)
                                                                });
                                                                format!("BVar({index}):binding={binding:?}:checked_type={checked:?}:scope={scope:?}")
                                                            }
                                                            other=>format!("source={other:?}"),
                                                        };
                                                        format!("first_app_argument_type=UNKNOWN:arg={:?}:required_domain={domain:?}:origin={origin}",a.expr)
                                                    }
                                                    Some(actual) => {
                                                        let judgment =
                                                            crate::convert::convert_with_policy_in_context(
                                                                &probe, &actual, &domain,
                                                                fuel.min(256),
                                                                crate::convert::DeltaPolicy::PreferredOnly,
                                                                context.len(), context,
                                                            );
                                                        format!(
                                                            "first_app_argument_domain={judgment:?}:actual={actual:?}:domain={domain:?}"
                                                        )
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            } else if matches!(other, Some(Expr::Lam { .. })) {
                                probe.diagnostic_lambda_source_premises(
                                    &cursor, context, &domain, remaining.min(512),
                                )
                            } else {
                                "non-application-source-leaf".to_owned()
                            };
                            let neutral_probe = probe.machine().expose(
                                cursor.clone(), Transparency::Opaque, 256,
                            );
                            let neutral_premise = if follow_source_leaf {
                                match neutral_probe.proven_value() {
                                    Some(Value::Neutral(value)) => {
                                        // One additional source telescope is
                                        // allowed, but cannot recursively call
                                        // itself on another untyped leaf.
                                        let ordinary =
                                            probe.diagnostic_neutral_source_telescope_inner(
                                                value, context, 512, false,
                                            );
                                        let original =
                                            probe.diagnostic_neutral_origin_replay(
                                                value, context, 512,
                                            );
                                        let enclosing =
                                            probe.diagnostic_outer_telescope_at_leaf_origin(
                                                neutral, value, context, 1024,
                                            );
                                        #[cfg(feature = "diagnostics")]
                                        if std::env::var_os("NUCLEUS_TRACE_ORIGIN_REPLAY").is_some()
                                        {
                                            use std::sync::atomic::{AtomicUsize, Ordering};
                                            static ORIGIN_COUNT: AtomicUsize = AtomicUsize::new(0);
                                            if ORIGIN_COUNT.fetch_add(1, Ordering::Relaxed) < 48 {
                                                eprintln!(
                                                    "NUCLEUS_ORIGIN_REPLAY:head={:?}:arity={}:caller_depth={}:result={}",
                                                    value.head, value.spine.len(), context.len(), original
                                                );
                                                eprintln!(
                                                    "NUCLEUS_OUTER_ORIGIN_REPLAY:head={:?}:arity={}:caller_depth={}:result={}",
                                                    neutral.head, neutral.spine.len(), context.len(), enclosing
                                                );
                                            }
                                        }
                                        format!("caller={ordinary}:origin={original}:enclosing={enclosing}")
                                    }
                                    other => format!("no-opaque-neutral={other:?}"),
                                }
                            } else {
                                "nested-source-probe-disabled".to_owned()
                            };
                            let neutral_premise: String =
                                neutral_premise.chars().take(1300).collect();
                            stages.push(format!(
                                "source_leaf={:?}@{}:shape={other:?}:typing={app_obligation}:opaque_telescope={neutral_premise}",
                                cursor.expr, cursor.env.id(),
                            ));
                            break;
                        }
                    }
                }
                let origin = stages.join(" -> ");
                return format!(
                    "first-untyped-argument:argument={position}:closure={actual_arg:?}:expected_domain={domain:?}:context_depth={}:origin={origin}",
                    context.len(),
                );
            };
            let relation = crate::convert::convert_with_policy_in_context(
                &probe, &actual_type, &domain,
                remaining.min(256),
                crate::convert::DeltaPolicy::PreferredOnly,
                context.len(), context,
            );
            if !relation.is_proven() {
                return format!(
                    "first-undischarged-domain:argument={position}:actual={actual_type:?}:required={domain:?}:relation={relation:?}:context_depth={}",
                    context.len(),
                );
            }
            current = match body {
                PiBody::Fixed(free, body_type, owner) => {
                    let Some(instantiated) = probe.instantiate_fixed_pi_body_carried(
                        &body_type, free, owner.as_ref(), actual_arg, &mut remaining,
                    ) else {
                        return format!(
                            "first-unresolved-dependent-substitution:argument={position}:binder={free:?}:body={body_type:?}"
                        );
                    };
                    instantiated
                }
                PiBody::Closure(body_closure) => {
                    TypeValue::Term(Closure::with_levels(
                        body_closure.expr,
                        body_closure.env.extend(actual_arg.clone()),
                        body_closure.levels,
                    ))
                }
            };
        }
        let result_kind = probe.sort_level(
            Judgment::proven(current.clone(), "checked-neutral-telescope"),
            remaining.min(256),
        );
        format!(
            "all-source-arguments-checked:arity={}:result_type={current:?}:result_sort={result_kind:?}",
            neutral.spine.len(),
        )
    }

    pub(crate) fn rule_k_reduce_neutral(
        &self,
        neutral: &Neutral,
        context: &[TypeValue],
        budget: usize,
    ) -> RuleKAttempt {
        if budget < 8 {
            return RuleKAttempt::NotApplicable;
        }
        let NeutralHead::Const { name, levels } = &neutral.head else {
            return RuleKAttempt::NotApplicable;
        };
        let Some(reduction) = self.environment.recursor_reduction(*name) else {
            if std::env::var_os("NUCLEUS_TRACE_RULE_K").is_some() {
                eprintln!("NUCLEUS_RULE_K:head={}:stage=no-reduction", name.0);
            }
            return RuleKAttempt::NotApplicable;
        };
        if std::env::var_os("NUCLEUS_TRACE_RULE_K").is_some() {
            eprintln!(
                "NUCLEUS_RULE_K:head={}:stage=found:k={}:rules={}:spine={}:params={}:indices={}",
                name.0,
                reduction.k,
                reduction.rules.len(),
                neutral.spine.len(),
                reduction.num_params,
                reduction.num_indices
            );
        }
        let [rule] = reduction.rules.as_slice() else {
            return RuleKAttempt::NotApplicable;
        };
        if std::env::var_os("NUCLEUS_TRACE_RULE_K").is_some() {
            eprintln!(
                "NUCLEUS_RULE_K:head={}:stage=rule:fields={}:rule_params={}:level_params={}:head_levels={}",
                name.0,
                rule.num_fields,
                rule.num_params,
                reduction.level_params.len(),
                levels.len()
            );
        }
        if !reduction.k
            || rule.num_fields != 0
            || rule.num_params != reduction.num_params
            || reduction.level_params.len() != levels.len()
        {
            if std::env::var_os("NUCLEUS_TRACE_RULE_K").is_some() {
                eprintln!("NUCLEUS_RULE_K:head={}:stage=guard-failed", name.0);
            }
            return RuleKAttempt::NotApplicable;
        }

        let required = reduction
            .num_params
            .saturating_add(1)
            .saturating_add(reduction.rules.len())
            .saturating_add(reduction.num_indices)
            .saturating_add(1);
        if neutral.spine.len() != required {
            return RuleKAttempt::NotApplicable;
        }

        // Rule K is licensed by the certified recursor interface itself:
        // after applying every recursor argument except the final major, the
        // remaining Pi domain is the exact type that a replacement constructor
        // must inhabit. This avoids reconstructing a local variable's type from
        // incidental FreeId numbering.
        let declaration = match self.environment.get(*name) {
            Some(declaration) if declaration.level_params.len() == levels.len() => declaration,
            _ => return RuleKAttempt::NotApplicable,
        };
        let substitutions = declaration
            .level_params
            .iter()
            .copied()
            .zip(levels.iter().cloned())
            .collect::<Vec<_>>();
        let mut current = TypeValue::Term(Closure::with_levels(
            declaration.ty,
            EnvFrame::empty(),
            LevelSubstitution::new(substitutions),
        ));
        for argument in &neutral.spine[..neutral.spine.len().saturating_sub(1)] {
            let Some((_domain, body)) = self.pi_view(
                Judgment::proven(current, "rule-k-recursor-spine"),
                budget / 4,
            ) else {
                if std::env::var_os("NUCLEUS_TRACE_RULE_K").is_some() {
                    eprintln!(
                        "NUCLEUS_RULE_K:head={}:stage=recursor-spine-type-missing",
                        name.0
                    );
                }
                return RuleKAttempt::NotApplicable;
            };
            current = match body {
                PiBody::Fixed(binder, body, owner) => {
                    let mut fuel = budget;
                    let Some(instantiated) = self.instantiate_fixed_pi_body_carried(
                        &body, binder, owner.as_ref(), argument, &mut fuel,
                    ) else {
                        return RuleKAttempt::NotApplicable;
                    };
                    instantiated
                },
                PiBody::Closure(body) => TypeValue::Term(Closure::with_levels(
                    body.expr,
                    body.env.extend(argument.clone()),
                    body.levels,
                )),
            };
        }
        let Some((target_domain, _body)) =
            self.pi_view(Judgment::proven(current, "rule-k-final-domain"), budget / 4)
        else {
            if std::env::var_os("NUCLEUS_TRACE_RULE_K").is_some() {
                eprintln!("NUCLEUS_RULE_K:head={}:stage=target-domain-missing", name.0);
            }
            return RuleKAttempt::NotApplicable;
        };
        if std::env::var_os("NUCLEUS_TRACE_RULE_K").is_some() {
            eprintln!("NUCLEUS_RULE_K:head={}:stage=target-domain-ok", name.0);
        }

        let mut constructor_levels = Vec::with_capacity(rule.constructor_level_params.len());
        for parameter in &rule.constructor_level_params {
            let Some(index) = reduction
                .level_params
                .iter()
                .position(|candidate| candidate == parameter)
            else {
                if std::env::var_os("NUCLEUS_TRACE_RULE_K").is_some() {
                    eprintln!(
                        "NUCLEUS_RULE_K:head={}:stage=constructor-level-map-missing:param={}",
                        name.0, parameter.0
                    );
                }
                return RuleKAttempt::NotApplicable;
            };
            constructor_levels.push(levels[index].clone());
        }
        let constructor = Neutral {
            head: NeutralHead::Const {
                name: rule.constructor,
                levels: constructor_levels,
            },
            spine: neutral.spine[..rule.num_params].to_vec(),
        };
        let Some(constructor_type) = self.neutral_result_type(&constructor, context, budget / 4)
        else {
            if std::env::var_os("NUCLEUS_TRACE_RULE_K").is_some() {
                eprintln!(
                    "NUCLEUS_RULE_K:head={}:stage=constructor-type-missing",
                    name.0
                );
            }
            return RuleKAttempt::NotApplicable;
        };
        if std::env::var_os("NUCLEUS_TRACE_RULE_K").is_some() {
            eprintln!("NUCLEUS_RULE_K:head={}:stage=constructor-type-ok", name.0);
        }

        let compatibility = crate::convert::convert_with_policy_in_context(
            self,
            &target_domain,
            &constructor_type,
            budget / 2,
            crate::convert::DeltaPolicy::GuardedSemanticFallback,
            context.len(),
            context,
        );
        if std::env::var_os("NUCLEUS_TRACE_RULE_K").is_some() {
            eprintln!(
                "NUCLEUS_RULE_K:head={}:stage=compatibility:result={compatibility:?}",
                name.0
            );
        }
        match compatibility {
            Judgment::Proven { .. } => {
                let substitutions = reduction
                    .level_params
                    .iter()
                    .copied()
                    .zip(levels.iter().cloned())
                    .collect::<Vec<_>>();
                let mut result = Closure::with_levels(
                    rule.rhs,
                    EnvFrame::empty(),
                    LevelSubstitution::new(substitutions),
                );
                let prefix_len = reduction.num_params + 1 + reduction.rules.len();
                for argument in &neutral.spine[..prefix_len] {
                    loop {
                        match self.expression(result.expr) {
                            Some(Expr::Lam { body, .. }) => {
                                result = result.sibling(*body, result.env.extend(argument.clone()));
                                break;
                            }
                            Some(Expr::Let { value, body, .. }) => {
                                let value = result.sibling(*value, result.env.clone());
                                result = result.sibling(*body, result.env.extend(value));
                            }
                            _ => return RuleKAttempt::NotApplicable,
                        }
                    }
                }
                if std::env::var_os("NUCLEUS_TRACE_RULE_K").is_some() {
                    eprintln!("NUCLEUS_RULE_K:head={}:stage=reduced", name.0);
                }
                RuleKAttempt::Reduced(result)
            }
            Judgment::Refuted { obstruction }
                if matches!(
                    obstruction.0,
                    "distinct-canonical-universes"
                        | "distinct-Nat-literals"
                        | "distinct-qualified-Nat-locals"
                        | "rigid-value-constructor-mismatch"
                ) =>
            {
                RuleKAttempt::DefiniteMismatch
            }
            Judgment::Refuted { .. } | Judgment::Unknown { .. } => RuleKAttempt::NotApplicable,
        }
    }

    pub(crate) fn certified_stuck_nonproof_recursor_on_local(
        &self,
        neutral: &Neutral,
        context: &[TypeValue],
        budget: usize,
    ) -> bool {
        let NeutralHead::Const { name, levels } = &neutral.head else {
            return false;
        };
        let Some(reduction) = self.environment.recursor_reduction(*name) else {
            return false;
        };
        if reduction.k || reduction.level_params.len() != levels.len() {
            return false;
        }
        let required = reduction
            .num_params
            .saturating_add(1)
            .saturating_add(reduction.rules.len())
            .saturating_add(reduction.num_indices)
            .saturating_add(1);
        if neutral.spine.len() != required {
            return false;
        }
        if !neutral
            .spine
            .last()
            .is_some_and(|target| self.closure_resolves_to_free(target, budget.min(4096)))
        {
            return false;
        }
        let Some(result_type) = self.neutral_result_type(neutral, context, budget) else {
            return false;
        };
        self.normalize_type_value(&result_type, budget)
            .is_some_and(|normalized| {
                self.normalized_type_is_definitely_nonproposition(&normalized, context, budget, 0)
            })
    }

    fn closure_resolves_to_free(&self, closure: &Closure, budget: usize) -> bool {
        let mut current = closure.clone();
        for _ in 0..budget {
            match self.expression(current.expr) {
                Some(Expr::BVar(index)) => match current.env.lookup(*index) {
                    Some(EnvBinding::Closure(bound)) => current = bound,
                    Some(EnvBinding::Free(_)) => return true,
                    Some(EnvBinding::Neutral(Neutral {
                        head: NeutralHead::Free(_, _),
                        spine,
                    })) => return spine.is_empty(),
                    Some(EnvBinding::Neutral(_)) | Some(EnvBinding::NatLit(_)) | None => return false,
                },
                Some(Expr::Let { value, body, .. }) => {
                    let value = current.sibling(*value, current.env.clone());
                    current = current.sibling(*body, current.env.extend(value));
                }
                _ => return false,
            }
        }
        false
    }

    pub(crate) fn is_certified_constructor(&self, name: NameId) -> bool {
        self.environment.is_certified_constructor(name)
    }

    pub(crate) fn has_qualified_recursor(&self, name: NameId) -> bool {
        self.environment.recursor_reduction(name).is_some()
    }

    /// Eta and rigid non-eta cases retain BOTH original typing sources.
    /// Evaluated heads select this trial; they supply no typing authority.
    pub(crate) fn checked_source_structure_relation(&self,left:&Closure,right:&Closure,left_value:&Value,right_value:&Value,context:&[TypeValue],remaining:&mut usize)->Option<Judgment<()>> {
        let (Value::Neutral(a),Value::Neutral(b))=(left_value,right_value) else{return None;};
        let nominal=|n:&Neutral|matches!(n.head,NeutralHead::Free(_,Some(_)))&&n.spine.is_empty();
        let rigid_spines=matches!(a.head,NeutralHead::Free(_,Some(_)))&&matches!(b.head,NeutralHead::Free(_,Some(_)))&&(!a.spine.is_empty()||!b.spine.is_empty())&&!a.head.same_owned_free(&b.head);
        let constructor=|n:&Neutral|match n.head {NeutralHead::Const{name,..}=>self.eta_projection_spec_for_constructor(name).is_some()||self.non_eta_structure_for_constructor(name).is_some(),_=>false};
        if !rigid_spines&&!((nominal(a)&&constructor(b))||(nominal(b)&&constructor(a))||(nominal(a)&&nominal(b))){return None;}
        if nominal(a)&&nominal(b) {
            if a.head.same_owned_free(&b.head){return None;}
            // Eligibility only: a literal registered structure in an original
            // retained domain avoids a strict typing trial for ordinary locals.
            let possible=|n:&Neutral|->bool{
                let NeutralHead::Free(_,Some(owner))=&n.head else{return false;};
                let ledger=self.checked_binding_lineage.borrow();let Some(Some(w))=ledger.get(&owner.id()) else{return false;};
                let TypeValue::Term(domain)=&w.domain else{return false;};let mut id=domain.expr;
                for _ in 0..16 {match self.expressions.get(id){Some(Expr::App{fun,..})=>id=*fun,Some(Expr::Const{name,..})=>return self.environment.shared_projection_specs().contains_key(name)||self.nat_primitives().is_some_and(|nat|nat.type_name==*name),Some(Expr::BVar(_))=>return true,_=>return false,}}
                false
            };
            if !possible(a)||!possible(b){return None;}
        }
        let _guard=SourceStructureRelationOwner::enter()?;
        if !self.source_used_capture_authority_available(left,remaining)||!self.source_used_capture_authority_available(right,remaining){return None;}
        let probe=self.strict_certificate_probe();
        let left_type=probe.infer_exact_closure_in_context(left,context,remaining,0)?;
        let right_type=probe.infer_exact_closure_in_context(right,context,remaining,0)?;
        let (TypeValue::Term(left_type_source),TypeValue::Term(right_type_source))=(&left_type,&right_type) else{return None;};
        // Proof irrelevance is not a rigid data inequality. Form both actual
        // types, with each closure's own captured universe substitution.
        let left_sort=probe.shared_strict_source_sort(left_type_source,context,remaining)?;
        let right_sort=probe.shared_strict_source_sort(right_type_source,context,remaining)?;
        // Raw substituted levels can hide zero (e.g. imax 1 0). Neither
        // normalized zero nor unresolved zero classification is DATA authority.
        if !crate::level::level_equal_with_remaining(left_sort,LevelTerm::Zero,remaining).is_refuted()
            ||!crate::level::level_equal_with_remaining(right_sort,LevelTerm::Zero,remaining).is_refuted(){return None;}
        #[cfg(feature="diagnostics")] if std::env::var_os("TRACE_ETA_ARGUMENT").is_some(){eprintln!("ETA_ARG_TYPES:left={left_type:?}:right={right_type:?}:remaining={remaining}:rigid_spines={rigid_spines}");}
        let checked_same_type=left_type==right_type||self.same_checked_bvar_origin(left_type_source,right_type_source,context,remaining);
        if !checked_same_type {
            let allowance=(*remaining).min(512);if allowance==0{return None;}*remaining-=allowance;
            if !crate::convert::convert_with_policy_in_context(&probe,&left_type,&right_type,allowance,crate::convert::DeltaPolicy::GuardedSemanticFallback,context.len(),context).is_proven(){return None;}
        }
        let allowance=(*remaining).min(256);if allowance==0{return None;}*remaining-=allowance;
        let actual_type=self.machine().expose(left_type_source.clone(),Transparency::Reducible,allowance);
        let Value::Neutral(type_head)=actual_type.proven_value()? else{return None;};
        // A nominal is rigid only when its ORIGINAL introduction is certified
        // in this actual Gamma; unrelated same-number owners are not unequal.
        let certified_nominal=|n:&Neutral|->Option<FreeId>{
            if !n.spine.is_empty(){return None;}
            let NeutralHead::Free(free,Some(owner))=&n.head else{return None;};
            if !matches!(owner.lookup_binding_ref(0),Some(EnvBinding::Free(actual)) if actual==free){return None;}
            let ledger=self.checked_binding_lineage.borrow();let witness=ledger.get(&owner.id())?.as_ref()?;
            if !context.starts_with(&witness.protected_prefix)||fresh_local(witness.protected_prefix.len().checked_sub(1)?)!=Some(*free){return None;}
            Some(*free)
        };
        if rigid_spines&&nominal(type_head) {
            certified_nominal(type_head)?;
            let certify_head=|n:&Neutral|->Option<FreeId>{let bare=Neutral{head:n.head.clone(),spine:vec![]};certified_nominal(&bare)};
            let (x,y)=(certify_head(a)?,certify_head(b)?);
            if x!=y{return Some(Judgment::refuted("distinct-rigid-local-terms"));}return None;
        }
        if rigid_spines{return None;}
        if nominal(a)&&nominal(b)&&nominal(type_head) {
            // An abstract, independently formed DATA type cannot unfold to a
            // proof or an eta-expandable record. All three original binders
            // must be certified in this actual Gamma; numbers alone confer
            // neither identity nor inequality.
            certified_nominal(type_head)?;
            let (x,y)=(certified_nominal(a)?,certified_nominal(b)?);
            if x!=y{return Some(Judgment::refuted("distinct-rigid-local-terms"));}
            return None;
        }
        let NeutralHead::Const{name:type_name,..}=&type_head.head else{return None;};
        if nominal(a)&&nominal(b) {
            let (x,y)=(certified_nominal(a)?,certified_nominal(b)?);
            if x!=y&&self.is_non_eta_structure_type(*type_name){return Some(Judgment::refuted("non-eta-structure-mismatch"));}
            // Both ORIGINAL terms and their common actual data TYPE were
            // independently checked above. The certified monomorphic Nat
            // interface has no record eta rule or proof irrelevance.
            if x!=y&&type_head.spine.is_empty()
                &&matches!(&type_head.head,NeutralHead::Const{levels,..} if levels.is_empty())
                &&self.nat_primitives().is_some_and(|nat|nat.type_name==*type_name){
                return Some(Judgment::refuted("distinct-qualified-Nat-locals"));
            }
            return None;
        }
        let (target,constructed)=if nominal(a){(a,b)}else{(b,a)};
        certified_nominal(target)?;
        let NeutralHead::Const{name:ctor,..}=&constructed.head else{return None;};
        if let Some((actual_type,arity))=self.non_eta_structure_for_constructor(*ctor) {
            if actual_type==*type_name&&constructed.spine.len()==arity{return Some(Judgment::refuted("non-eta-structure-mismatch"));}
            return None;
        }
        let (actual_type,params,fields)=self.eta_projection_spec_for_constructor(*ctor)?;
        if actual_type!=*type_name||constructed.spine.len()!=params.checked_add(fields)?{return None;}
        for(index,field)in constructed.spine[params..].iter().enumerate(){
            let allowance=(*remaining).min(256);if allowance==0{return None;}*remaining-=allowance;
            if !self.certified_eta_projection_field(field,*type_name,index,target,params,allowance){return None;}
        }
        Some(Judgment::proven((),"source-certified-structure-eta"))
    }

    pub(crate) fn eta_projection_spec_for_constructor(
        &self,
        constructor: NameId,
    ) -> Option<(NameId, usize, usize)> {
        let specs = self.environment.projection_specs();
        let mut matches = specs
            .into_iter()
            .filter(|(_, spec)| spec.eta_expandable && spec.constructor == constructor);
        let (type_name, spec) = matches.next()?;
        if matches.next().is_some() {
            return None;
        }
        Some((type_name, spec.num_params, spec.field_types.len()))
    }

    pub(crate) fn non_eta_structure_for_constructor(
        &self,
        constructor: NameId,
    ) -> Option<(NameId, usize)> {
        let specs = self.environment.projection_specs();
        let mut matches = specs
            .into_iter()
            .filter(|(_, spec)| !spec.eta_expandable && spec.constructor == constructor);
        let (type_name, spec) = matches.next()?;
        if matches.next().is_some() {
            return None;
        }
        Some((type_name, spec.num_params + spec.field_types.len()))
    }

    pub(crate) fn is_non_eta_structure_type(&self, type_name: NameId) -> bool {
        self.environment
            .projection_specs()
            .get(&type_name)
            .is_some_and(|spec| !spec.eta_expandable)
    }

    pub(crate) fn certified_eta_projection_field(
        &self,
        field: &Closure,
        type_name: NameId,
        index: usize,
        target: &crate::value::Neutral,
        num_params: usize,
        budget: usize,
    ) -> bool {
        let mut remaining=budget;
        let mut seen=std::collections::HashSet::new();
        let mut closure = field.clone();
        let mut arguments = Vec::new();
        let (projection, levels) = loop {
            if !take_step(&mut remaining)||!seen.insert((closure.expr,closure.env.id(),closure.levels.identity())){return false;}
            let Some(expression) = self.expressions.get(closure.expr) else {
                return false;
            };
            match expression {
                Expr::App { fun, arg } => {
                    arguments.push(closure.sibling(*arg, closure.env.clone()));
                    closure = closure.sibling(*fun, closure.env.clone());
                }
                Expr::BVar(bvar) => {
                    let Some(binding) = closure.env.lookup(*bvar) else {
                        return false;
                    };
                    match binding {
                        crate::value::EnvBinding::Closure(bound) => closure = bound,
                        crate::value::EnvBinding::Free(_)
                        | crate::value::EnvBinding::Neutral(_)
                        | crate::value::EnvBinding::NatLit(_) => return false,
                    }
                }
                Expr::Const { name, levels } => break (*name, levels.clone()),
                _ => return false,
            }
        };
        arguments.reverse();
        if arguments.len() != num_params + 1 {
            return false;
        }

        let Some(declaration) = self.environment.get(projection) else {
            return false;
        };
        let Some(mut body) = declaration.value else {
            return false;
        };
        if !declaration.preferred_for_reduction || declaration.level_params.len() != levels.len() {
            return false;
        }
        for _ in 0..=num_params {
            if !take_step(&mut remaining){return false;}
            let Some(Expr::Lam { body: next, .. }) = self.expressions.get(body) else {
                return false;
            };
            body = *next;
        }
        let Some(Expr::Proj {
            type_name: projected_type,
            index: projected_index,
            structure,
        }) = self.expressions.get(body)
        else {
            return false;
        };
        if *projected_type != type_name || usize::try_from(*projected_index).ok() != Some(index) {
            return false;
        }
        if !matches!(self.expressions.get(*structure), Some(Expr::BVar(0))) {
            return false;
        }

        let Some(target_argument) = arguments.last().cloned() else {
            return false;
        };
        let exposed = self
            .machine()
            .expose(target_argument, Transparency::Reducible, remaining);
        matches!(exposed.proven_value(), Some(Value::Neutral(actual)) if actual == target)
    }

    pub(crate) fn checked_unit_like_source_pair(&self,left:&Closure,right:&Closure,context:&[TypeValue],remaining:&mut usize)->bool {
        // Candidate metadata selects only immediate actual binding owners
        // with a literal singleton domain hint. The retained domain is not
        // accepted as typing authority here; both original operands are
        // independently checked below under the actual Gamma and quarantine.
        let possible=|source:&Closure| {
            let Some(Expr::BVar(index))=self.expressions.get(source.expr) else{return false;};
            let Some(owner)=source.env.binding_frame(*index) else{return false;};
            let ledger=self.checked_binding_lineage.borrow();
            let Some(Some(witness))=ledger.get(&owner.id()) else{return false;};
            let TypeValue::Term(domain)=&witness.domain else{return false;};
            let mut candidate=domain.clone();
            for _ in 0..16 {
                match self.expressions.get(candidate.expr) {
                    Some(Expr::Const{name,..})=>{
                        if self.environment.is_unit_like_type(*name){return true;}
                        let Some(next)=self.environment.get(*name).and_then(|decl|decl.value) else{return false;};
                        candidate=candidate.sibling(next,EnvFrame::empty());
                    },
                    Some(Expr::BVar(index))=>{
                        let Some(frame)=candidate.env.binding_frame(*index) else{return false;};
                        let Some(EnvBinding::Closure(value))=frame.lookup(0) else{return false;};
                        candidate=value;
                    },
                    _=>return false,
                }
            }
            false
        };
        if !possible(left)||!possible(right){return false;}
        if !self.source_used_capture_authority_available(left,remaining)||!self.source_used_capture_authority_available(right,remaining){return false;}
        fn bare_source_free(checker:&TypeChecker<'_>,source:&Closure,remaining:&mut usize)->Option<FreeId> {
            let mut current=source.clone();
            for _ in 0..48 {
                if !take_step(remaining){return None;}
                let Expr::BVar(index)=checker.expressions.get(current.expr)? else{return None;};
                let owner=checker.source_capture_owner(&current.env,*index,remaining)?;
                match owner.lookup(0)? {
                    EnvBinding::Free(free)=>return Some(free),
                    EnvBinding::Neutral(Neutral{head:NeutralHead::Free(free,Some(owner)),spine}) if spine.is_empty() && matches!(owner.lookup_binding_ref(0),Some(EnvBinding::Free(actual)) if *actual==free)=>return Some(free),
                    EnvBinding::Closure(value)=>current=value,
                    _=>return None,
                }
            }
            None
        }
        let Some(lhs)=bare_source_free(self,left,remaining) else{return false;};
        let Some(rhs)=bare_source_free(self,right,remaining) else{return false;};
        if lhs==rhs{return false;}
        // The original source operands must each have an actual checked
        // owner/domain witness in the real Gamma. Numeric IDs and Gamma
        // positions never supply this singleton typing premise.
        let probe=self.strict_certificate_probe();
        let Some(left_type)=probe.infer_exact_closure_in_context(left,context,remaining,0) else{return false;};
        let Some(right_type)=probe.infer_exact_closure_in_context(right,context,remaining,0) else{return false;};
        if *remaining<64{return false;}*remaining-=64;
        self.unit_like_type_key(&left_type,32).zip(self.unit_like_type_key(&right_type,32))
            .is_some_and(|(left_key,right_key)|left_key==right_key)
    }

    pub(crate) fn unit_like_type_key(
        &self,
        ty: &TypeValue,
        budget: usize,
    ) -> Option<(NameId, Vec<LevelTerm>)> {
        let TypeValue::Term(closure) = ty else {
            return None;
        };
        let exposed = self
            .machine()
            .expose(closure.clone(), Transparency::Reducible, budget);
        let Value::Neutral(neutral) = exposed.proven_value()? else {
            return None;
        };
        if !neutral.spine.is_empty() {
            return None;
        }
        let NeutralHead::Const { name, levels } = &neutral.head else {
            return None;
        };
        self.environment
            .is_unit_like_type(*name)
            .then(|| (*name, levels.clone()))
    }

    pub(crate) fn type_value_is_prop_sort(&self, ty: &TypeValue, budget: usize) -> bool {
        let TypeValue::Term(closure) = ty else {
            return false;
        };
        let exposed = self
            .machine()
            .expose(closure.clone(), Transparency::Reducible, budget);
        matches!(exposed.proven_value(), Some(Value::Sort(LevelTerm::Zero)))
    }

    pub(crate) fn fixed_proof_function_type_key(
        &self,
        ty: &TypeValue,
        budget: usize,
    ) -> Option<(NameId, Vec<LevelTerm>)> {
        let TypeValue::Term(closure) = ty else {
            return None;
        };
        let machine = self.machine();
        let exposed = machine.expose(closure.clone(), Transparency::Reducible, budget);
        let Value::Pi { body, .. } = exposed.proven_value()? else {
            return None;
        };

        // A distinguished free witness detects dependence on the function
        // argument. Only a fixed proposition codomain is admitted here.
        // Its identity must also be absent from every actual used capture.
        let allowance = budget.min(1024);
        let mut opening_budget = allowance;
        let safe = crate::convert::source_opening_avoids_capture(
            self, body, FreeId(u64::MAX), &mut opening_budget,
        );
        let budget = budget - (allowance - opening_budget);
        if !safe { return None; }
        let codomain = machine.expose(
            body.under_free(FreeId(u64::MAX)),
            Transparency::Reducible,
            budget,
        );
        let Value::Neutral(neutral) = codomain.proven_value()? else {
            return None;
        };
        if !neutral.spine.is_empty() {
            return None;
        }
        let NeutralHead::Const { name, levels } = &neutral.head else {
            return None;
        };
        let declaration = self.environment.get(*name)?;
        if declaration.level_params.len() != levels.len() {
            return None;
        }
        let substitutions = declaration
            .level_params
            .iter()
            .copied()
            .zip(levels.iter().cloned())
            .collect::<Vec<_>>();
        let proposition_type = Closure::with_levels(
            declaration.ty,
            EnvFrame::empty(),
            LevelSubstitution::new(substitutions),
        );
        let proposition_type = machine.expose(proposition_type, Transparency::Reducible, budget);
        matches!(
            proposition_type.proven_value(),
            Some(Value::Sort(LevelTerm::Zero))
        )
        .then(|| (*name, levels.clone()))
    }

    pub(crate) fn derived_predecessor_equations(&self,name:NameId,value:ExprId,budget:usize)->bool {
        let Some(nat)=self.environment.nat_primitives() else{return false;};
        if nat.pred.is_some(){return false;}
        let Some(carrier)=nat.virtual_bvar_zero else{return false;};
        if !matches!(self.expressions.get(carrier),Some(Expr::BVar(0))){return false;}
        let Some(Expr::Lam{domain,body})=self.expressions.get(value) else{return false;};
        if !matches!(self.expressions.get(*domain),Some(Expr::Const{name,levels}) if *name==nat.type_name&&levels.is_empty()){return false;}
        let mut probe=Self::new(self.expressions,self.levels,self.environment);
        probe.strict_origin_probe=true;
        let mut work=budget;
        if probe.complete_source_support(value,&mut work).is_none_or(|support|!support.is_empty()){return false;}
        // The immutable environment contains only established declarations.
        // Use that completed original body judgment, rather than rechecking it
        // under a different strict probe configuration.
        let Some(declaration)=self.environment.get(name) else{return false;};
        if declaration.value!=Some(value)||!declaration.level_params.is_empty(){return false;}
        let Some(Expr::Pi { domain: declared_domain, body: result }) = self.expressions.get(declaration.ty) else { return false; };
        if ![*declared_domain, *result].into_iter().all(|expr|
            matches!(self.expressions.get(expr),Some(Expr::Const{name,levels}) if *name==nat.type_name&&levels.is_empty())) { return false; }

        let domain=Closure::new(*domain,EnvFrame::empty());
        let Some(formation)=probe.infer_exact_closure_in_context(&domain,&[],&mut work,0)else{return false;};
        if !probe.sort_level(Judgment::proven(formation,"source-Nat-domain-formation"),work).is_proven(){return false;}
        if work < 4 { return false; }
        work -= 4;
        let free=FreeId(0);let original_body=Closure::new(*body,EnvFrame::empty());
        if !crate::convert::source_opening_avoids_capture(&probe,&original_body,free,&mut work){return false;}
        let domain=TypeValue::Term(domain);let context=vec![domain.clone()];
        let frame=probe.checked_source_frame(value,CheckedFrameRole::InferLambda,&EnvFrame::empty(),domain.clone(),&context,CheckedFrameBinding::Free(free));
        if probe.checked_type_of_bound_source(&frame,0,&context)!=Some(domain){return false;}
        let variable=Closure::new(carrier,frame);
        // A certified Nat.succ applied to this actual typed source local is
        // a Nat in the same Γ. The neutral carrier asserts no new typing fact.
        let successor=Closure::new(carrier,EnvFrame::empty().extend_neutral(Neutral{
            head:NeutralHead::Const{name:nat.succ,levels:vec![]},spine:vec![variable],
        }));
        let zero_body=Closure::new(*body,EnvFrame::empty().extend_nat_literal(crate::nat::BigNat::zero()));
        let succ_body=Closure::new(*body,EnvFrame::empty().extend(successor));
        probe.machine().source_predecessor_equations(zero_body,succ_body,free,work)
    }

    pub(crate) fn machine(&self) -> Machine<'_> {
        Machine::new(
            self.environment.authority(),
            self.expressions,
            self.levels,
            self.environment.definition_bodies(),
        )
        .with_singleton_recursor_reductions(self.environment.shared_singleton_recursor_reductions())
        .with_nullary_minor_reductions(self.environment.nullary_minor_reductions())
        .with_closed_nested_minor_reductions(self.environment.closed_nested_minor_reductions())
        .with_recursor_reductions(self.environment.shared_recursor_reductions())
        .with_projection_specs(self.environment.shared_projection_specs())
        .with_nat_primitives(self.environment.nat_primitives().cloned())
        .with_bool_primitives(self.environment.bool_primitives().cloned())
        .with_quot_primitives(self.environment.quot_primitives().cloned())
        .with_exposure_cache(self.exposure_cache.clone())
    }

    pub(crate) fn instantiate(&self, level: LevelId, budget: usize) -> Result<LevelTerm, ()> {
        instantiate_level(self.levels, level, &self.level_substitution, budget).map_err(|_| ())
    }

    pub(crate) fn cached_actual_capture_frees(&self,source:&Closure,virtual_slots:u64,_remaining:&mut usize)->Option<Rc<Vec<FreeId>>> {
        let key=(source.expr,source.env.id(),source.levels.identity(),virtual_slots);
        let cache=self.source_capture_free_support.borrow();
        let (_,frees)=cache.get(&key)?;
        // The caller already paid this source-node/cache inspection.
        // Cloning the immutable handle copies no FreeId elements.
        Some(frees.clone())
    }

    pub(crate) fn retain_actual_capture_frees(&self,source:&Closure,virtual_slots:u64,frees:Rc<Vec<FreeId>>) {
        let key=(source.expr,source.env.id(),source.levels.identity(),virtual_slots);
        let mut cache=self.source_capture_free_support.borrow_mut();
        if cache.len()<8192 {cache.entry(key).or_insert_with(||(source.clone(),frees));}
    }

    pub(crate) fn has_source_opening_proof(&self,body:&Closure,free:FreeId)->bool {
        self.source_opening_proofs.borrow().contains_key(&(body.expr,body.env.id(),body.levels.identity(),free))
    }

    pub(crate) fn retain_source_opening_proof(&self,body:&Closure,free:FreeId) {
        let mut proofs=self.source_opening_proofs.borrow_mut();
        if proofs.len()<8192 {
            proofs.entry((body.expr,body.env.id(),body.levels.identity(),free)).or_insert_with(||body.clone());
        }
    }

    pub(crate) fn authority(&self) -> crate::machine::AuthorityId {
        self.environment.authority()
    }

    pub(crate) fn nat_primitives(&self) -> Option<&crate::environment::NatPrimitives> {
        self.environment.nat_primitives()
    }

    pub(crate) fn definition_value(&self, name: NameId) -> Option<ExprId> {
        self.environment.get(name)?.value
    }

    pub(crate) fn is_certified_bool_constructor(&self, name: NameId) -> bool {
        self.environment
            .bool_primitives()
            .is_some_and(|primitives| name == primitives.false_ctor || name == primitives.true_ctor)
    }

    pub(crate) fn distinct_bool_constructors(&self, left: NameId, right: NameId) -> bool {
        if left == right {
            return false;
        }
        self.environment
            .bool_primitives()
            .is_some_and(|primitives| {
                let is_bool = |name| name == primitives.false_ctor || name == primitives.true_ctor;
                is_bool(left) && is_bool(right)
            })
    }

    /// Two distinct opaque closed constants that themselves inhabit Prop
    /// are rigid proposition type constructors. They cannot be definitionally
    /// equal: neither side has a delta body, there are no universe arguments,
    /// and each constant's declared type reduces to Sort 0.
    pub(crate) fn distinct_opaque_closed_proposition_types(
        &self,
        left: NameId,
        left_levels: &[LevelTerm],
        right: NameId,
        right_levels: &[LevelTerm],
        budget: usize,
    ) -> bool {
        if left == right || !left_levels.is_empty() || !right_levels.is_empty() {
            return false;
        }

        let definitions = self.environment.definition_bodies();
        if definitions.contains_key(&left) || definitions.contains_key(&right) {
            return false;
        }

        let is_closed_prop_type = |name: NameId| {
            let Some(declaration) = self.environment.get(name) else {
                return false;
            };
            if !declaration.level_params.is_empty() {
                return false;
            }
            let ty = Closure::with_levels(
                declaration.ty,
                EnvFrame::empty(),
                LevelSubstitution::new(Vec::new()),
            );
            matches!(
                self.machine()
                    .expose(ty, Transparency::Reducible, budget)
                    .proven_value(),
                Some(Value::Sort(LevelTerm::Zero))
            )
        };

        is_closed_prop_type(left) && is_closed_prop_type(right)
    }

    pub(crate) fn closure(&self, expr: ExprId, env: EnvFrame) -> Closure {
        let mut entries: Vec<_> = self
            .level_substitution
            .iter()
            .map(|(name, level)| (*name, level.clone()))
            .collect();
        entries.sort_by_key(|(name, _)| name.0);
        Closure::with_levels(expr, env, LevelSubstitution::new(entries))
    }
}

fn definite_conversion_obstruction(obstruction: &str) -> bool {
    matches!(
        obstruction,
        "distinct-canonical-universes"
            | "distinct-Nat-literals"
            | "rigid-value-constructor-mismatch"
            | "distinct-opaque-proposition-types"
            | "distinct-rigid-local-terms"
            | "non-eta-structure-mismatch"
            | "rule-k-target-mismatch"
            | "certified-stuck-recursor-mismatch"
            | "certified-constructor-argument-mismatch"
    )
}

enum PiBody {
    Fixed(FreeId, TypeValue, Option<EnvFrame>),
    Closure(Closure),
}

fn take_step(remaining: &mut usize) -> bool {
    if *remaining == 0 {
        false
    } else {
        *remaining -= 1;
        true
    }
}

fn fresh_local(depth: usize) -> Option<FreeId> {
    u64::try_from(depth).ok().map(FreeId)
}

#[cfg(test)]
mod minimal_context_binder_tests {
    use super::*;

    fn infer_bvar(free: u64, source_index:u64) -> Judgment<TypeValue> {
        let mut expression=IdTable::default();
        let levels=IdTable::default();
        expression.insert(ExprId(0),Expr::BVar(source_index)).unwrap();
        let environment=Environment::empty();
        let checker=TypeChecker::new(&expression,&levels,&environment);
        let context=vec![
            TypeValue::Sort(LevelTerm::Zero),
            TypeValue::Sort(LevelTerm::Succ(Box::new(LevelTerm::Zero))),
        ];
        let frame=EnvFrame::empty().extend_free(FreeId(free));
        let mut fuel=128;
        checker.infer_in(ExprId(0),&context,&frame,&mut fuel,&mut HashMap::new())
    }

    #[test]
    #[ignore="explicit bounded binder-context transport A/B"]
    fn actual_source_captured_free_zero_overrules_unrelated_latest_context_entry(){
        let result=infer_bvar(0,0);
        assert!(matches!(
            result,Judgment::Proven{value:TypeValue::Sort(LevelTerm::Zero),..}
        ),"the source frame actually denotes FreeId0, with context[0] type: {result:?}");
    }

    #[test]
    #[ignore="explicit bounded binder-context transport A/B"]
    fn source_captured_free_one_retains_different_data_type(){
        let result=infer_bvar(1,0);
        assert!(matches!(
            result,Judgment::Proven{value:TypeValue::Sort(LevelTerm::Succ(_)),..}
        ),"FreeId1 must retain its distinct context[1] type: {result:?}");
    }

    #[test]
    #[ignore="explicit bounded binder-context transport A/B"]
    fn high_synthetic_free_id_does_not_claim_unproved_context_correspondence(){
        let result=infer_bvar(75_000,0);
        assert!(matches!(
            result,Judgment::Proven{value:TypeValue::Sort(LevelTerm::Succ(_)),..}
        ),"source validator synthetic FreeIds retain original inference: {result:?}");
    }

    #[test]
    #[ignore="explicit bounded binder-context transport A/B"]
    fn actual_missing_bvar_still_rejected(){
        let result=infer_bvar(0,2);
        assert!(!result.is_proven(),"missing source variable cannot be assigned a type: {result:?}");
    }
}

#[cfg(test)]
mod checked_binding_lineage_tests {
    use super::*;

    fn checker_fixture<'a>(
        e: &'a IdTable<ExprId,Expr>,
        l: &'a IdTable<LevelId,Level>,
        env: &'a Environment
    )->TypeChecker<'a>{
        TypeChecker::new(e,l,env)
    }

    #[test]
    fn strict_origin_requires_immutable_checked_binding_and_exact_context() {
        let mut expressions=IdTable::default();
        expressions.insert(ExprId(0),Expr::BVar(0)).unwrap();
        let levels=IdTable::default();
        let env=Environment::empty();
        let mut checker=TypeChecker::new(&expressions,&levels,&env);
        checker.strict_origin_probe=true;
        let prop=TypeValue::Sort(LevelTerm::Zero);
        let different=TypeValue::Sort(LevelTerm::Succ(Box::new(LevelTerm::Zero)));
        let origin=vec![prop.clone()];
        let frame=EnvFrame::empty().extend_free(FreeId(0));
        let term=Closure::new(ExprId(0),frame.clone());
        let mut fuel=32;
        assert!(checker.infer_exact_closure_in_context(
            &term,&origin,&mut fuel,0
        ).is_none(),"numeric FreeId alone is not source typing");
        // A deliberately source-registered binder node establishes one exact
        // local typing judgment; it does not license arbitrary context change.
        checker.retain_checked_binding(&frame,prop.clone(),&origin);
        let mut fuel=32;
        assert_eq!(checker.infer_exact_closure_in_context(
            &term,&origin,&mut fuel,0
        ),Some(prop.clone()));
        let mut fuel=32;
        assert!(checker.infer_exact_closure_in_context(
            &term,&[different],&mut fuel,0
        ).is_none(),"different protected type cannot inherit the witness");
        let mut fuel=32;
        assert!(checker.infer_exact_closure_in_context(
            &term,&[],&mut fuel,0
        ).is_none(),"the checked source scope must not disappear");
    }

    #[test]
    #[ignore="explicit source-scoped binding authority A/B only"]
    fn typed_binder_uses_its_witness_not_unrelated_latest_context_type(){
        let expressions=IdTable::default();
        let levels=IdTable::default();
        let env=Environment::empty();
        let checker=checker_fixture(&expressions,&levels,&env);
        let t0=TypeValue::Sort(LevelTerm::Zero);
        let t1=TypeValue::Sort(LevelTerm::Succ(Box::new(LevelTerm::Zero)));
        let f0=EnvFrame::empty().extend_free(FreeId(0));
        checker.retain_checked_binding(&f0,t0.clone(),&[t0.clone()]);
        let f1=f0.extend_free(FreeId(1));
        checker.retain_checked_binding(&f1,t1.clone(),&[t0.clone(),t1.clone()]);
        let prefix=vec![t0.clone(),t1.clone()];
        assert_eq!(
            checker.checked_type_of_bound_source(&f1,1,&prefix),
            Some(t0.clone()),
            "BVar1 uses the checked parent binder's type, not the newest context type"
        );
        assert_eq!(
            checker.checked_type_of_bound_source(&f1,0,&prefix),
            Some(t1),
            "BVar0 is the newest binder's distinct type"
        );
    }


    #[test]
    #[ignore="explicit checked source substitution reclosure A/B"]
    fn checked_pi_elimination_registers_its_actual_typed_substitution(){
        let mut expressions=IdTable::default();
        let mut levels=IdTable::default();
        levels.insert(LevelId(0),Level::Zero).unwrap();
        levels.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
        for (id,expr) in [
            (0,Expr::Sort(LevelId(1))),
            (1,Expr::Const{name:NameId(1),levels:vec![]}),
            (2,Expr::Pi{domain:ExprId(1),body:ExprId(1)}),
            (3,Expr::Const{name:NameId(2),levels:vec![]}),
            (4,Expr::Const{name:NameId(3),levels:vec![]}),
            (5,Expr::App{fun:ExprId(3),arg:ExprId(4)}),
            (6,Expr::Sort(LevelId(0))),
            (7,Expr::App{fun:ExprId(3),arg:ExprId(6)}),
        ]{expressions.insert(ExprId(id),expr).unwrap();}
        let env=Environment::empty()
            .extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap()
            .extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![],ExprId(2))).unwrap()
            .extend(NameId(3),crate::environment::ConstantDecl::axiom(vec![],ExprId(1))).unwrap();
        let checker=TypeChecker::new(&expressions,&levels,&env);
        let mut budget=4096;
        let proven=checker.infer_exact_closure_in_context(
            &Closure::new(ExprId(5),EnvFrame::empty()),&[],&mut budget,0,
        );
        let Some(TypeValue::Term(result))=proven else{
            panic!("checked application must infer a result type");
        };
        assert!(checker.checked_type_of_bound_source(&result.env,0,&[]).is_some(),
            "a fully checked Pi elimination must produce a retained typed substitution witness");

        let mut bad_budget=4096;
        let invalid=checker.infer_exact_closure_in_context(
            &Closure::new(ExprId(7),EnvFrame::empty()),&[],&mut bad_budget,0,
        );
        assert!(invalid.is_none(),"an ill-typed source argument cannot acquire a new warrant");
    }
    #[test]
    #[ignore="explicit checked value substitution witness A/B only"]
    fn captured_typed_substitution_uses_validated_source_domain_without_reinfer() {
        let mut expressions=IdTable::default();
        let mut levels=IdTable::default();
        levels.insert(LevelId(0),Level::Zero).unwrap();
        expressions.insert(ExprId(0),Expr::Sort(LevelId(0))).unwrap();
        expressions.insert(ExprId(1),Expr::BVar(0)).unwrap();
        let environment=Environment::empty();
        let checker=checker_fixture(&expressions,&levels,&environment);
        let actual=Closure::new(ExprId(0),EnvFrame::empty());
        let mut source_fuel=16;
        let checked_domain=checker.infer_exact_closure_in_context(
            &actual,&[],&mut source_fuel,0,
        ).expect("the source argument was independently typed");
        let frame=EnvFrame::empty().extend(actual.clone());
        checker.retain_checked_elimination(&frame,checked_domain.clone(),&[]);
        let mut single_step_fuel=1;
        let recovered=checker.infer_exact_closure_in_context(
            &Closure::new(ExprId(1),frame),&[],&mut single_step_fuel,0,
        );
        assert_eq!(recovered,Some(checked_domain),
            "checked substitution should reuse its proven type without re-inference");
        let unwarranted=EnvFrame::empty().extend(actual);
        let mut missing_fuel=1;
        assert!(checker.infer_exact_closure_in_context(
            &Closure::new(ExprId(1),unwarranted),&[],&mut missing_fuel,0
        ).is_none(),"a distinct uncertified frame cannot acquire typing authority");
    }

    #[test]
    #[ignore="explicit source-scoped binding authority A/B only"]
    fn a_different_typing_prefix_is_a_protected_future_separator(){
        let expressions=IdTable::default();
        let levels=IdTable::default();
        let env=Environment::empty();
        let checker=checker_fixture(&expressions,&levels,&env);
        let p=TypeValue::Sort(LevelTerm::Zero);
        let q=TypeValue::Sort(LevelTerm::Succ(Box::new(LevelTerm::Zero)));
        let frame=EnvFrame::empty().extend_free(FreeId(0));
        checker.retain_checked_binding(&frame,p.clone(),&[p.clone()]);
        assert!(checker.checked_type_of_bound_source(&frame,0,&[q]).is_none(),
            "same source binder frame cannot be replayed under a different Γ");
    }

    #[test]
    #[ignore="explicit source-scoped binding authority A/B only"]
    fn conflicting_or_absent_witnesses_do_not_grant_type_authority(){
        let expressions=IdTable::default();
        let levels=IdTable::default();
        let env=Environment::empty();
        let checker=checker_fixture(&expressions,&levels,&env);
        let p=TypeValue::Sort(LevelTerm::Zero);
        let q=TypeValue::Sort(LevelTerm::Succ(Box::new(LevelTerm::Zero)));
        let frame=EnvFrame::empty().extend_free(FreeId(0));
        assert!(checker.checked_type_of_bound_source(&frame,0,&[p.clone()]).is_none());
        checker.retain_checked_binding(&frame,p.clone(),&[p.clone()]);
        checker.retain_checked_binding(&frame,q.clone(),&[p.clone()]);
        assert!(checker.checked_type_of_bound_source(&frame,0,&[p]).is_none(),
            "conflicting purported types revoke the reusable judgment");
    }
}

#[cfg(test)]
mod fixed_pi_capture_tests {
    use super::*;

    #[test]
    fn fixed_pi_substitution_refuses_actual_captured_by_unrelated_inner_binder() {
        let mut expressions = IdTable::default();
        expressions.insert(ExprId(0), Expr::BVar(0)).unwrap();
        let levels = IdTable::default();
        let environment = Environment::empty();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        let source = TypeValue::Term(Closure::new(ExprId(0),
            EnvFrame::empty().extend_free(FreeId(0))));
        let stored = TypeValue::Pi {
            domain: Box::new(source.clone()), body: Box::new(source), binder: FreeId(1),
         binder_owner: None,};
        let actual = Closure::new(ExprId(0), EnvFrame::empty().extend_free(FreeId(1)));
        let mut fuel = 128;
        assert!(checker.instantiate_fixed_pi_body(&stored, FreeId(0), &actual, &mut fuel).is_none(),
            "a stored shallow function type cannot capture the caller's ambient local");
    }
    #[test]
    fn fixed_pi_substitution_preserves_shadowing_and_refuses_unsupported_or_low_fuel() {
        let mut expressions = IdTable::default();
        expressions.insert(ExprId(0), Expr::BVar(0)).unwrap();
        let levels = IdTable::default();
        let environment = Environment::empty();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        let source = TypeValue::Term(Closure::new(ExprId(0),
            EnvFrame::empty().extend_free(FreeId(0))));
        let actual = Closure::new(ExprId(0), EnvFrame::empty().extend_free(FreeId(1)));
        let shadowed = TypeValue::Pi { domain: Box::new(source.clone()),
            body: Box::new(source.clone()), binder: FreeId(0) , binder_owner: None,};
        let mut fuel = 128;
        let Some(TypeValue::Pi { domain, body, binder , binder_owner,}) = checker.instantiate_fixed_pi_body(
            &shadowed, FreeId(0), &actual, &mut fuel) else { panic!("shadowing must remain supported") };
        assert_eq!(binder, FreeId(0));
        assert_eq!(*body, source, "inner body shadows the source binder");
        assert_eq!(checker.type_depends_on_free(&domain, FreeId(1), 128), Some(true));
        let mut fuel = 0;
        assert!(checker.instantiate_fixed_pi_body(&source, FreeId(0), &actual, &mut fuel).is_none());
        let unsupported = TypeValue::Term(Closure::new(ExprId(0),
            EnvFrame::empty().extend_neutral(Neutral {
                head: NeutralHead::Free(FreeId(0), None), spine: vec![actual.clone()],
            })));
        let mut fuel = 128;
        assert!(checker.instantiate_fixed_pi_body(&unsupported, FreeId(0), &actual, &mut fuel).is_none());
    }

}

#[cfg(test)]
mod closed_spine_inference_tests {
    use super::*;

    fn fixture() -> (IdTable<ExprId, Expr>, IdTable<LevelId, Level>, Environment, ExprId) {
        let mut expressions = IdTable::default();
        let mut levels = IdTable::default();
        levels.insert(LevelId(0), Level::Zero).unwrap();
        for (id, expression) in [
            (0, Expr::Sort(LevelId(0))),
            (1, Expr::Const { name: NameId(1), levels: vec![] }), // A
            (2, Expr::Pi { domain: ExprId(1), body: ExprId(1) }),
            (3, Expr::Const { name: NameId(2), levels: vec![] }), // id : A -> A
            (4, Expr::Const { name: NameId(3), levels: vec![] }), // p : A
            (5, Expr::BVar(0)),
            (6, Expr::Const { name: NameId(4), levels: vec![] }), // B
            (7, Expr::App { fun: ExprId(3), arg: ExprId(1) }), // wrong closed argument
        ] { expressions.insert(ExprId(id), expression).unwrap(); }
        let mut spine = ExprId(4);
        for id in 8..24 {
            expressions.insert(ExprId(id), Expr::App { fun: ExprId(3), arg: spine }).unwrap();
            spine = ExprId(id);
        }
        let environment = Environment::empty()
            .extend(NameId(1), crate::environment::ConstantDecl::axiom(vec![], ExprId(0))).unwrap()
            .extend(NameId(2), crate::environment::ConstantDecl::axiom(vec![], ExprId(2))).unwrap()
            .extend(NameId(3), crate::environment::ConstantDecl::axiom(vec![], ExprId(1))).unwrap()
            .extend(NameId(4), crate::environment::ConstantDecl::axiom(vec![], ExprId(0))).unwrap();
        expressions.insert(ExprId(24), Expr::App { fun: ExprId(3), arg: ExprId(5) }).unwrap();
        (expressions, levels, environment, spine)
    }

    #[test]
    fn singleton_source_operands_require_actual_owned_domains_and_quarantine() {
        let(expressions,levels,environment,_)=fixture();
        let environment=environment.install_unit_like_type(NameId(1)).unwrap();
        let mut checker=TypeChecker::new(&expressions,&levels,&environment);checker.strict_origin_probe=true;
        let unit=TypeValue::Term(checker.closure(ExprId(1),EnvFrame::empty()));
        let other=TypeValue::Term(checker.closure(ExprId(6),EnvFrame::empty()));
        let gamma=vec![unit.clone(),unit.clone()];
        let left_frame=EnvFrame::empty().extend_free(FreeId(0));
        let right_frame=EnvFrame::empty().extend_free(FreeId(1));
        checker.retain_checked_binding(&left_frame,unit.clone(),&gamma);
        checker.retain_checked_binding(&right_frame,unit.clone(),&gamma);
        let left=checker.closure(ExprId(5),left_frame.clone());
        let right=checker.closure(ExprId(5),right_frame.clone());
        assert!(checker.checked_unit_like_source_pair(&left,&right,&gamma,&mut 256));
        assert!(!checker.checked_unit_like_source_pair(&left,&right,&gamma,&mut 0));
        assert!(!checker.checked_unit_like_source_pair(&left,&right,&[other.clone(),other.clone()],&mut 256));
        let raw=checker.closure(ExprId(5),EnvFrame::empty().extend_free(FreeId(1)));
        assert!(!checker.checked_unit_like_source_pair(&left,&raw,&gamma,&mut 256),"same numeric Free and context type are not ownership");
        checker.retain_checked_binding(&right_frame,other,&gamma);
        assert!(!checker.checked_unit_like_source_pair(&left,&right,&gamma,&mut 256),"quarantine must revoke singleton witness");
        let mut ordinary=TypeChecker::new(&expressions,&levels,&environment);ordinary.strict_origin_probe=true;
        let data=TypeValue::Term(ordinary.closure(ExprId(6),EnvFrame::empty()));
        let data_gamma=vec![data.clone(),data.clone()];
        ordinary.retain_checked_binding(&left_frame,data.clone(),&data_gamma);
        ordinary.retain_checked_binding(&right_frame,data,&data_gamma);
        assert!(!ordinary.checked_unit_like_source_pair(&left,&right,&data_gamma,&mut 256),"distinct non-singleton data remains distinct");
    }

    #[test]
    fn singleton_source_operands_do_not_merge_distinct_universes() {
        let(mut expressions,mut levels,_,_)=fixture();
        levels.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
        for(id,level)in[(70,LevelId(0)),(71,LevelId(1))]{expressions.insert(ExprId(id),Expr::Const{name:NameId(1),levels:vec![level]}).unwrap();}
        let environment=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![NameId(42)],ExprId(0))).unwrap().install_unit_like_type(NameId(1)).unwrap();
        let mut checker=TypeChecker::new(&expressions,&levels,&environment);checker.strict_origin_probe=true;
        assert!(checker.is_type(ExprId(70),256).is_proven());assert!(checker.is_type(ExprId(71),256).is_proven());
        let a=TypeValue::Term(checker.closure(ExprId(70),EnvFrame::empty()));let b=TypeValue::Term(checker.closure(ExprId(71),EnvFrame::empty()));
        let gamma=vec![a.clone(),b.clone()];let left=EnvFrame::empty().extend_free(FreeId(0));let right=EnvFrame::empty().extend_free(FreeId(1));
        checker.retain_checked_binding(&left,a,&gamma);checker.retain_checked_binding(&right,b,&gamma);
        assert!(!checker.checked_unit_like_source_pair(&checker.closure(ExprId(5),left),&checker.closure(ExprId(5),right),&gamma,&mut 256));
    }

    #[test]
    fn immutable_ancestor_lookup_pays_actual_hops_and_preserves_physical_owners() {
        let (expressions,levels,environment,_)=fixture();
        let checker=TypeChecker::new(&expressions,&levels,&environment);
        let mut frames=Vec::new();let mut root=EnvFrame::empty();
        for i in 0..256 {root=root.extend_free(FreeId(i%3));frames.push(root.clone());}
        let mut needed=4;
        let actual=checker.source_capture_owner(&root,7,&mut needed).expect("the measured index7 lookup should finish in three actual ancestor hops plus its lookup step");
        assert_eq!(actual.id(),frames[248].id());assert_eq!(needed,0);
        for index in 0..256u64 {
            let mut work=usize::try_from(index.count_ones()).unwrap()+1;
            let actual=checker.source_capture_owner(&root,index,&mut work).unwrap();
            assert_eq!(actual.id(),frames[255-index as usize].id());
            let a=actual.lookup_with_node_id(0).map(|(node,binding)|match binding{EnvBinding::Free(free)=>(node,free),_=>panic!("actual payload changed")});
            let b=root.lookup_with_node_id(index).map(|(node,binding)|match binding{EnvBinding::Free(free)=>(node,free),_=>panic!("original payload changed")});
            assert_eq!(a,b);
        }
        assert!(checker.source_capture_owner(&root,256,&mut 64).is_none());
        assert!(checker.source_capture_owner(&root,u64::MAX,&mut 128).is_none());
        let branch_a=root.extend_free(FreeId(1));let branch_b=root.extend_free(FreeId(1));
        assert_ne!(checker.source_capture_owner(&branch_a,0,&mut 1).unwrap().id(),checker.source_capture_owner(&branch_b,0,&mut 1).unwrap().id());
        let uncached=root.extend_free(FreeId(1));
        assert!(checker.source_capture_owner(&uncached,7,&mut 0).is_none());
        assert!(checker.source_capture_owner(&uncached,7,&mut 3).is_none());
    }

    #[test]
    fn immutable_capture_lookup_preserves_owner_and_unfinished_work() {
        let (expressions,levels,environment,_)=fixture();
        let checker=TypeChecker::new(&expressions,&levels,&environment);
        let binder=EnvFrame::empty().extend_free(FreeId(0));
        let source=binder.extend(checker.closure(ExprId(1),EnvFrame::empty()));
        let mut cold=2;
        let owner=checker.source_capture_owner(&source,1,&mut cold).unwrap();
        assert_eq!(owner.id(),binder.id());assert_eq!(cold,0);
        let mut hot=1;
        assert_eq!(checker.source_capture_owner(&source,1,&mut hot).unwrap().id(),binder.id());assert_eq!(hot,0);
        assert!(matches!(owner.lookup_binding_ref(0),Some(EnvBinding::Free(FreeId(0)))));
        let other_binder=EnvFrame::empty().extend_free(FreeId(1));
        let other=other_binder.extend(checker.closure(ExprId(1),EnvFrame::empty()));
        let before=checker.source_capture_bindings.borrow().len();
        assert!(checker.source_capture_owner(&other,1,&mut 1).is_none());
        assert_eq!(checker.source_capture_bindings.borrow().len(),before,"incomplete lookup has no certificate");
        assert_eq!(checker.source_capture_owner(&other,1,&mut 2).unwrap().id(),other_binder.id());
        let before=checker.source_capture_bindings.borrow().len();
        assert!(checker.source_capture_owner(&source,3,&mut 4).is_none());
        assert_eq!(checker.source_capture_bindings.borrow().len(),before);
        assert!(checker.source_capture_owner(&source,1,&mut 0).is_none());
    }

    #[test]
    fn completed_lambda_bucket_requires_full_paired_source_and_owned_shifted_domains() {
        let (mut expressions,levels,environment,_)=fixture();
        for (id,expr) in [(60,Expr::Lam{domain:ExprId(1),body:ExprId(61)}),
            (61,Expr::BVar(1)),(62,Expr::BVar(2)),
            (64,Expr::Lam{domain:ExprId(1),body:ExprId(62)}),
            (65,Expr::Lam{domain:ExprId(1),body:ExprId(5)}),
            (66,Expr::Lam{domain:ExprId(1),body:ExprId(61)})] {
            expressions.insert(ExprId(id),expr).unwrap();
        }
        let mut checker=TypeChecker::new(&expressions,&levels,&environment);checker.strict_origin_probe=true;
        let a=TypeValue::Term(checker.closure(ExprId(1),EnvFrame::empty()));
        let b=TypeValue::Term(checker.closure(ExprId(6),EnvFrame::empty()));
        let expected=checker.closure(ExprId(2),EnvFrame::empty());
        let mut absent_budget=1;
        assert!(!checker.reuse_owned_lambda_goal(ExprId(60),&checker.closure(ExprId(60),EnvFrame::empty()),&expected,&[],&mut absent_budget));
        assert_eq!(absent_budget,1,"absent completed candidates must not traverse the source AST");
        assert!(checker.is_type(ExprId(2),4096).is_proven());
        let old=EnvFrame::empty().extend_free(FreeId(0));checker.retain_checked_binding(&old,a.clone(),&[a.clone()]);
        assert!(checker.check_expected_lambda_in(ExprId(60),&TypeValue::Term(expected.clone()),&[a.clone()],&old,&mut 4096,true,&mut HashMap::new(),true).is_proven());
        let source=checker.closure(ExprId(60),old.clone());
        let dependencies=checker.owned_goal_dependencies(&source,&expected,&[a.clone()],&mut 1024).unwrap();
        let hint=checker.lambda_candidate_hint(ExprId(60),&mut 128).unwrap();
        assert_eq!(checker.complete_source_support(ExprId(60),&mut 2),Some(vec![0]));
        assert!(checker.lambda_candidate_hint(ExprId(64),&mut 128).is_some());
        assert_eq!(checker.complete_source_support(ExprId(64),&mut 2),Some(vec![1]));
        assert!(checker.lambda_candidate_hint(ExprId(65),&mut 128).is_some());
        assert_eq!(checker.complete_source_support(ExprId(65),&mut 1),Some(vec![]));
        checker.owned_lambda_shape_domains.borrow_mut().entry((ExprId(1),Some(ExprId(2)))).or_default().push(hint);
        checker.owned_lambda_shapes.borrow_mut().insert((ExprId(1),Some(ExprId(2)),hint),vec![OwnedLambdaGoal{source,expected:expected.clone(),dependencies}]);
        let renamed=EnvFrame::empty().extend_free(FreeId(1));
        checker.retain_checked_binding(&renamed,a.clone(),&[a.clone(),a.clone()]);
        let extended=renamed.extend_free(FreeId(2));
        checker.retain_checked_binding(&extended,b.clone(),&[a.clone(),a.clone(),b.clone()]);
        let gamma=[a.clone(),a.clone(),b.clone()];
        assert!(checker.reuse_owned_lambda_goal(ExprId(64),&checker.closure(ExprId(64),extended.clone()),&expected,&gamma,&mut 4096),"different source ExprId and external offset require the full completed judgment correspondence");
        assert!(!checker.reuse_owned_lambda_goal(ExprId(65),&checker.closure(ExprId(65),extended.clone()),&expected,&gamma,&mut 4096),"external capture cannot become a positional intrinsic binder from a bucket match");
        assert!(!checker.reuse_owned_lambda_goal(ExprId(66),&checker.closure(ExprId(66),extended),&expected,&gamma,&mut 4096),"same annotation and goal do not erase the used B declared domain");
        checker.retain_checked_binding(&old,b.clone(),&[b]);
        assert!(!checker.reuse_owned_lambda_goal(ExprId(64),&checker.closure(ExprId(64),renamed),&expected,&gamma,&mut 4096),"original quarantine revokes structural candidates too");
    }

    #[test]
    fn completed_lambda_transport_requires_owned_recursive_type_premises() {
        let (mut expressions,levels,environment,_)=fixture();
        expressions.insert(ExprId(60),Expr::Lam{domain:ExprId(1),body:ExprId(61)}).unwrap();
        expressions.insert(ExprId(61),Expr::BVar(1)).unwrap();
        let mut checker=TypeChecker::new(&expressions,&levels,&environment);
        checker.strict_origin_probe=true;
        let a=TypeValue::Term(checker.closure(ExprId(1),EnvFrame::empty()));
        let b=TypeValue::Term(checker.closure(ExprId(6),EnvFrame::empty()));
        assert!(checker.is_type(ExprId(2),4096).is_proven());
        let expected=checker.closure(ExprId(2),EnvFrame::empty());
        let old=EnvFrame::empty().extend_free(FreeId(0));
        checker.retain_checked_binding(&old,a.clone(),&[a.clone()]);
        assert!(checker.check_expected_lambda_in(ExprId(60),&TypeValue::Term(expected.clone()),
            &[a.clone()],&old,&mut 4096,true,&mut HashMap::new(),true).is_proven());
        let source=checker.closure(ExprId(60),old.clone());
        let dependencies=checker.owned_goal_dependencies(&source,&expected,&[a.clone()],&mut 512).unwrap();
        assert_eq!(dependencies.len(),1);
        checker.owned_lambda_goals.borrow_mut().insert(ExprId(60),vec![OwnedLambdaGoal{
            source,expected:expected.clone(),dependencies,
        }]);
        assert!(checker.reuse_owned_lambda_goal(ExprId(60),&checker.closure(ExprId(60),old.clone()),
            &expected,&[a.clone(),b.clone()],&mut 512),"actual source ownership survives unused context extension");
        let other=EnvFrame::empty().extend_free(FreeId(0));
        assert!(!checker.reuse_owned_lambda_goal(ExprId(60),&checker.closure(ExprId(60),other.clone()),
            &expected,&[a.clone()],&mut 512),"a numeric FreeID is not a source witness");
        checker.retain_checked_binding(&other,b.clone(),&[b.clone()]);
        assert!(!checker.reuse_owned_lambda_goal(ExprId(60),&checker.closure(ExprId(60),other.clone()),
            &expected,&[b.clone()],&mut 512),"owned local of a different actual domain must not reuse A typing");
        checker.retain_checked_binding(&other,a.clone(),&[a.clone()]);
        assert!(checker.checked_binding_lineage.borrow().get(&other.id()).is_some_and(Option::is_none));
        assert!(!checker.reuse_owned_lambda_goal(ExprId(60),&checker.closure(ExprId(60),other),
            &expected,&[a.clone()],&mut 512),"quarantine cannot be repaired by matching a domain");
        assert!(!checker.reuse_owned_lambda_goal(ExprId(60),&checker.closure(ExprId(60),old.clone()),
            &expected,&[a.clone()],&mut 0));
        checker.retain_checked_binding(&old,b.clone(),&[b]);
        assert!(!checker.reuse_owned_lambda_goal(ExprId(60),&checker.closure(ExprId(60),old),
            &expected,&[a],&mut 512),"quarantining original ownership revokes transport");
    }

    #[test]
    fn captured_original_lambda_freshness_uses_caller_and_never_erases_bad_body_or_collision() {
        let (mut expressions,levels,environment,_)=fixture();
        expressions.insert(ExprId(60),Expr::Lam{domain:ExprId(1),body:ExprId(61)}).unwrap();
        expressions.insert(ExprId(61),Expr::BVar(1)).unwrap();
        expressions.insert(ExprId(62),Expr::Lam{domain:ExprId(1),body:ExprId(7)}).unwrap();
        let mut checker=TypeChecker::new(&expressions,&levels,&environment);checker.strict_origin_probe=true;
        let a=TypeValue::Term(checker.closure(ExprId(1),EnvFrame::empty()));
        let source=checker.closure(ExprId(60),EnvFrame::empty().extend(checker.closure(ExprId(4),EnvFrame::empty())));
        assert!(checker.infer_exact_closure_in_context(&source,&[],&mut 1024,0).is_some());
        assert!(checker.infer_exact_closure_in_context(&source,&[],&mut 0,0).is_none());
        assert!(checker.infer_exact_closure_in_context(&source,&[],&mut 2,0).is_none());
        let colliding=EnvFrame::empty().extend_free(FreeId(0));
        checker.retain_checked_binding(&colliding,a.clone(),&[a]);
        assert!(checker.infer_exact_closure_in_context(&checker.closure(ExprId(60),colliding),&[],&mut 1024,0).is_none(),"an independently owned source local must not become the fresh intrinsic binder from a matching numeric ID");
        assert!(checker.infer_exact_closure_in_context(&checker.closure(ExprId(62),EnvFrame::empty()),&[],&mut 1024,0).is_none(),"complete freshness does not replace typing of the original body by a desired beta result");
    }

    #[test]
    fn bound_goal_candidates_require_actual_payload_scope_and_old_ownership() {
        let (mut expressions,levels,environment,_)=fixture();
        for (id,expr) in [
            (60,Expr::Lam{domain:ExprId(1),body:ExprId(5)}),
            (61,Expr::BVar(1)),
            (62,Expr::Lam{domain:ExprId(1),body:ExprId(5)}),
            (63,Expr::Pi{domain:ExprId(6),body:ExprId(6)}),
            (64,Expr::Pi{domain:ExprId(1),body:ExprId(5)}),
        ] {expressions.insert(ExprId(id),expr).unwrap();}
        let mut checker=TypeChecker::new(&expressions,&levels,&environment);
        checker.strict_origin_probe=true;
        let a=TypeValue::Term(checker.closure(ExprId(1),EnvFrame::empty()));
        let sort=TypeValue::Sort(LevelTerm::Zero);
        let old_type=checker.closure(ExprId(2),EnvFrame::empty());
        let different_type=checker.closure(ExprId(63),EnvFrame::empty());
        assert_eq!(checker.infer_exact_closure_in_context(&old_type,&[],&mut 4096,0),Some(sort.clone()));
        assert_eq!(checker.infer_exact_closure_in_context(&different_type,&[],&mut 4096,0),Some(sort.clone()));
        let old_gamma=[a.clone()];
        let old=EnvFrame::empty().extend(old_type);
        checker.retain_checked_binding(&old,sort.clone(),&old_gamma);
        let expected=checker.closure(ExprId(5),old.clone());
        assert!(checker.check_expected_lambda_in(ExprId(60),&TypeValue::Term(expected.clone()),
            &old_gamma,&old,&mut 4096,false,&mut HashMap::new(),true).is_proven());
        let source=checker.closure(ExprId(60),old.clone());
        let dependencies=checker.owned_goal_dependencies(&source,&expected,&old_gamma,&mut 512).unwrap();
        let hint=checker.lambda_candidate_hint(ExprId(60),&mut 128).unwrap();
        checker.owned_lambda_shape_domains.borrow_mut().entry((ExprId(1),None)).or_default().push(hint);
        checker.owned_lambda_shapes.borrow_mut().insert((ExprId(1),None,hint),vec![OwnedLambdaGoal{
            source,expected:expected.clone(),dependencies}]);
        let gamma=[a.clone(),a.clone()];
        let current_type=checker.closure(ExprId(2),EnvFrame::empty());
        let current=EnvFrame::empty().extend(current_type);
        checker.retain_checked_binding(&current,sort.clone(),&gamma);
        let current=current.extend(checker.closure(ExprId(1),EnvFrame::empty()));
        let target=checker.closure(ExprId(61),current.clone());
        assert!(checker.reuse_owned_lambda_goal(ExprId(62),&checker.closure(ExprId(62),current.clone()),
            &target,&gamma,&mut 4096),"BVar0 and BVar1 only select a candidate; the complete owned typing judgment must transport");
        let wrong=EnvFrame::empty().extend(different_type);
        checker.retain_checked_binding(&wrong,sort.clone(),&gamma);
        let wrong=wrong.extend(checker.closure(ExprId(1),EnvFrame::empty()));
        assert!(!checker.reuse_owned_lambda_goal(ExprId(62),&checker.closure(ExprId(62),wrong.clone()),
            &checker.closure(ExprId(61),wrong),&gamma,&mut 4096),"identical declared Sort0 does not equate different captured goal payloads");
        assert!(!checker.reuse_owned_lambda_goal(ExprId(62),&checker.closure(ExprId(62),current.clone()),
            &checker.closure(ExprId(64),current.clone()),&gamma,&mut 4096),"an intrinsic Pi-body local cannot replace an external captured goal");
        let unowned=EnvFrame::empty().extend(checker.closure(ExprId(2),EnvFrame::empty())).extend(checker.closure(ExprId(1),EnvFrame::empty()));
        assert!(!checker.reuse_owned_lambda_goal(ExprId(62),&checker.closure(ExprId(62),unowned.clone()),
            &checker.closure(ExprId(61),unowned),&gamma,&mut 4096));
        checker.retain_checked_binding(&old,a,&old_gamma);
        assert!(!checker.reuse_owned_lambda_goal(ExprId(62),&checker.closure(ExprId(62),current),
            &target,&gamma,&mut 4096),"quarantining the original completed goal revokes the candidate");
    }

    #[test]
    fn expected_opening_shares_only_the_same_checked_lambda_scope() {
        let(mut expressions,levels,environment,_)=fixture();
        expressions.insert(ExprId(60),Expr::Lam{domain:ExprId(1),body:ExprId(5)}).unwrap();
        expressions.insert(ExprId(61),Expr::Lam{domain:ExprId(1),body:ExprId(5)}).unwrap();
        let mut checker=TypeChecker::new(&expressions,&levels,&environment);checker.strict_origin_probe=true;
        assert!(checker.is_type(ExprId(1),128).is_proven());
        let domain=TypeValue::Term(checker.closure(ExprId(1),EnvFrame::empty()));let gamma=vec![domain.clone()];
        let actual=checker.checked_source_frame(ExprId(60),CheckedFrameRole::ExpectedLambda,&EnvFrame::empty(),domain.clone(),&gamma,CheckedFrameBinding::Free(FreeId(0)));
        let token=checker.checked_lambda_scope(&actual).unwrap();
        let source=checker.closure(ExprId(1),EnvFrame::empty().extend_free(FreeId(9)));
        let mut work=16;let opened=checker.shared_expected_pi_frame(&source,&token,FreeId(0),&mut work).expect("one existing complete Gamma must supply the second actual introduction without recopying its vector");
        let witness=checker.checked_binding_lineage.borrow()[&opened.id()].as_ref().unwrap().clone();
        assert!(Rc::ptr_eq(&token.witness.protected_prefix,&witness.protected_prefix));
        assert_eq!(opened.parent_id(),Some(source.env.id()));
        assert!(matches!(opened.lookup_binding_ref(0),Some(EnvBinding::Neutral(Neutral{head:NeutralHead::Free(FreeId(0),Some(owner)),spine})) if owner==&actual && spine.is_empty()));
        assert!(checker.exact_source_capture_identity(&checker.closure(ExprId(5),actual.clone()),&checker.closure(ExprId(5),opened.clone()),&mut 128),"the certificate is consumed as the same original owned local");
        assert_eq!(checker.shared_expected_pi_frame(&source,&token,FreeId(0),&mut 1).unwrap().id(),opened.id());
        assert!(checker.shared_expected_pi_frame(&source,&token,FreeId(0),&mut 0).is_none());
        let mut wrong=token.clone();wrong.witness.protected_prefix=Rc::new(vec![TypeValue::Sort(LevelTerm::Zero)]);
        assert!(checker.shared_expected_pi_frame(&source,&wrong,FreeId(0),&mut 16).is_none());
        wrong=token.clone();wrong.witness.domain=TypeValue::Sort(LevelTerm::Zero);
        assert!(checker.shared_expected_pi_frame(&source,&wrong,FreeId(0),&mut 16).is_none());
        assert!(checker.shared_expected_pi_frame(&source,&token,FreeId(1),&mut 16).is_none());
        let changed=Closure::with_levels(source.expr,source.env.clone(),LevelSubstitution::new(vec![(NameId(7),LevelTerm::Zero)]));
        assert_ne!(checker.shared_expected_pi_frame(&changed,&token,FreeId(0),&mut 16).unwrap().id(),opened.id(),"different expected own universes have a separate introduction");
        let other=checker.checked_source_frame(ExprId(61),CheckedFrameRole::ExpectedLambda,&EnvFrame::empty(),domain.clone(),&gamma,CheckedFrameBinding::Free(FreeId(0)));
        assert_ne!(checker.shared_expected_pi_frame(&source,&checker.checked_lambda_scope(&other).unwrap(),FreeId(0),&mut 16).unwrap().id(),opened.id(),"different actual lambda owners cannot borrow the old expected introduction");
        checker.retain_checked_binding(&opened,TypeValue::Sort(LevelTerm::Zero),&gamma);
        assert!(checker.shared_expected_pi_frame(&source,&token,FreeId(0),&mut 16).is_none(),"old expected quarantine revokes reuse");
        checker.retain_checked_binding(&actual,TypeValue::Sort(LevelTerm::Zero),&gamma);
        assert!(checker.shared_expected_pi_frame(&changed,&token,FreeId(0),&mut 16).is_none(),"original actual introduction quarantine revokes all aliases");
    }

    #[test]
    fn exact_capture_identity_requires_the_actual_free_owner_not_its_number() {
        let (mut expressions,mut levels,environment,_)=fixture();
        levels.insert(LevelId(70),Level::Succ(LevelId(0))).unwrap();
        for (id,node) in [(70,Expr::Sort(LevelId(70))),(71,Expr::Const{name:NameId(70),levels:vec![]}),(72,Expr::Pi{domain:ExprId(71),body:ExprId(71)}),(73,Expr::Const{name:NameId(71),levels:vec![]}),(74,Expr::BVar(0)),(75,Expr::App{fun:ExprId(73),arg:ExprId(74)})]{expressions.insert(ExprId(id),node).unwrap();}
        let environment=environment.extend(NameId(70),crate::environment::ConstantDecl::axiom(vec![],ExprId(70))).unwrap().extend(NameId(71),crate::environment::ConstantDecl::axiom(vec![],ExprId(72))).unwrap();
        let checker=TypeChecker::new(&expressions,&levels,&environment);
        assert!(checker.is_type(ExprId(71),128).is_proven());
        let nat=TypeValue::Term(checker.closure(ExprId(71),EnvFrame::empty()));let gamma=vec![nat.clone()];
        let left=EnvFrame::empty().extend_free(FreeId(0));let right=EnvFrame::empty().extend_free(FreeId(0));
        checker.retain_checked_binding(&left,nat.clone(),&gamma);checker.retain_checked_binding(&right,nat,&gamma);
        assert_ne!(left.id(),right.id());
        let a=checker.closure(ExprId(75),left.clone());let b=checker.closure(ExprId(75),right);
        assert!(checker.infer_exact_closure_in_context(&a,&gamma,&mut 512,0).is_some());
        assert!(checker.infer_exact_closure_in_context(&b,&gamma,&mut 512,0).is_some());
        assert!(!checker.exact_source_capture_identity(&a,&b,&mut 512),"independent checked Nat owners have no joint introduction witness merely because both payloads say Free0");
        // An actually used alias of the original owner remains identifiable.
        let alias=checker.closure(ExprId(74),a.env.clone());
        let via_alias=checker.closure(ExprId(75),EnvFrame::empty().extend(alias));
        assert!(checker.exact_source_capture_identity(&a,&via_alias,&mut 512));
    }

    #[test]
    fn root_bvar_alias_conversion_keeps_budget_for_actual_source_exposure() {
        let (mut expressions,levels,environment,_)=fixture();
        expressions.insert(ExprId(60),Expr::BVar(7)).unwrap();
        expressions.insert(ExprId(61),Expr::NatLit(crate::nat::BigNat::zero())).unwrap();
        let checker=TypeChecker::new(&expressions,&levels,&environment);
        let literal=checker.closure(ExprId(61),EnvFrame::empty());
        let mut left=EnvFrame::empty().extend(literal.clone());let mut right=EnvFrame::empty().extend(literal);
        for _ in 0..7{left=left.extend_free(FreeId(40));right=right.extend_free(FreeId(41));}
        let a=TypeValue::Term(checker.closure(ExprId(60),left));let b=TypeValue::Term(checker.closure(ExprId(60),right));
        assert!(crate::convert::convert_with_policy_in_context(&checker,&a,&b,12,crate::convert::DeltaPolicy::PreferredOnly,0,&[]).is_proven(),"ordinary literal exposure must not lose its allowance to an optional whole-capture identity attempt");
    }

    #[test]
    fn exact_bvar_support_fuses_paid_source_node_with_zero_offset_payload() {
        let (mut expressions,levels,environment,_)=fixture();
        for (id,index) in [(60,1),(61,0),(62,7)]{expressions.insert(ExprId(id),Expr::BVar(index)).unwrap();}
        expressions.insert(ExprId(63),Expr::App{fun:ExprId(63),arg:ExprId(1)}).unwrap();
        let checker=TypeChecker::new(&expressions,&levels,&environment);
        let mut chain=checker.closure(ExprId(61),EnvFrame::empty().extend_free(FreeId(0)));
        for _ in 0..12 {chain=checker.closure(ExprId(61),EnvFrame::empty().extend(chain));}
        let root=checker.closure(ExprId(60),EnvFrame::empty().extend(chain));
        assert!(crate::convert::source_opening_avoids_capture(&checker,&root,FreeId(8),&mut 16),"one paid exact BVar/current physical payload visit must avoid generic support-vector reconstruction");
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&root,FreeId(0),&mut 64));
        let dangling=checker.closure(ExprId(60),EnvFrame::empty().extend(checker.closure(ExprId(62),EnvFrame::empty())));
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&dangling,FreeId(7),&mut 64),"a missing used child binding cannot synthesize a safe Free7 absence");
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&dangling,FreeId(9),&mut 64));
        let partial=checker.closure(ExprId(60),EnvFrame::empty().extend(checker.closure(ExprId(61),EnvFrame::empty().extend_free(FreeId(2)))));
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&partial,FreeId(8),&mut 1));
        assert!(!checker.source_capture_free_support.borrow().contains_key(&(partial.expr,partial.env.id(),partial.levels.identity(),1)));
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&checker.closure(ExprId(63),EnvFrame::empty()),FreeId(8),&mut 64));
        let arbitrary=checker.closure(ExprId(60),EnvFrame::empty().extend_neutral(Neutral{head:NeutralHead::Free(FreeId(2), None),spine:vec![]}));
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&arbitrary,FreeId(8),&mut 64));
    }

    #[test]
    fn completed_single_child_alias_support_reuses_immutable_set_with_paid_bounds() {
        let (mut expressions,levels,environment,_)=fixture();
        expressions.insert(ExprId(60),Expr::BVar(1)).unwrap();
        expressions.insert(ExprId(61),Expr::BVar(0)).unwrap();
        let checker=TypeChecker::new(&expressions,&levels,&environment);
        let leaf=checker.closure(ExprId(61),EnvFrame::empty().extend_free(FreeId(0)));
        let warm=checker.closure(ExprId(60),EnvFrame::empty().extend(leaf.clone()));
        assert!(crate::convert::source_opening_avoids_capture(&checker,&warm,FreeId(9),&mut 64));
        let mut chain=leaf;
        for _ in 0..12 {chain=checker.closure(ExprId(61),EnvFrame::empty().extend(chain));}
        let root=checker.closure(ExprId(60),EnvFrame::empty().extend(chain));
        assert!(crate::convert::source_opening_avoids_capture(&checker,&root,FreeId(8),&mut 55),"validated single-child aliases must forward one immutable completed set without repeated element copies");
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&root,FreeId(0),&mut 64),"forwarding preserves actual collision");
        let malformed=checker.closure(ExprId(60),EnvFrame::empty());
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&malformed,FreeId(8),&mut 64));
        let partial=checker.closure(ExprId(60),EnvFrame::empty().extend(checker.closure(ExprId(61),EnvFrame::empty().extend_free(FreeId(2)))));
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&partial,FreeId(8),&mut 1));
        assert!(!checker.source_capture_free_support.borrow().contains_key(&(partial.expr,partial.env.id(),partial.levels.identity(),1)),"partial traversal publishes no root support certificate");
        let arbitrary=checker.closure(ExprId(60),EnvFrame::empty().extend_neutral(Neutral{head:NeutralHead::Free(FreeId(8), None),spine:vec![]}));
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&arbitrary,FreeId(9),&mut 64));
    }

    #[test]
    fn completed_actual_capture_support_is_pure_exact_and_not_fresh_id_authority() {
        let (mut expressions,levels,environment,_)=fixture();
        expressions.insert(ExprId(60),Expr::BVar(1)).unwrap();
        expressions.insert(ExprId(61),Expr::BVar(0)).unwrap();
        let checker=TypeChecker::new(&expressions,&levels,&environment);
        let leaf=checker.closure(ExprId(61),EnvFrame::empty().extend_free(FreeId(1)));
        let source=checker.closure(ExprId(60),EnvFrame::empty().extend(leaf));
        assert!(crate::convert::source_opening_avoids_capture(&checker,&source,FreeId(9),&mut 32));
        let probe=checker.strict_certificate_probe();
        assert!(Rc::ptr_eq(&checker.source_capture_free_support,&probe.source_capture_free_support));
        assert!(crate::convert::source_opening_avoids_capture(&probe,&source,FreeId(8),&mut 2),"complete actual support can prove a different fresh ID absent without replaying its graph");
        assert!(!crate::convert::source_opening_avoids_capture(&probe,&source,FreeId(1),&mut 2),"the certificate retains the actual captured local and denies its collision");
        assert!(!crate::convert::source_opening_avoids_capture(&probe,&source,FreeId(8),&mut 0));
        let changed=checker.closure(ExprId(60),EnvFrame::empty().extend_free(FreeId(8)));
        assert!(!crate::convert::source_opening_avoids_capture(&probe,&changed,FreeId(8),&mut 32));
        let other=TypeChecker::new(&expressions,&levels,&environment);
        assert!(!Rc::ptr_eq(&checker.source_capture_free_support,&other.source_capture_free_support));
    }

    #[test]
    fn strict_probe_reuses_only_complete_pure_support_and_rechecks_actual_capture() {
        let (mut expressions,levels,environment,_)=fixture();
        expressions.insert(ExprId(60),Expr::BVar(1)).unwrap();
        expressions.insert(ExprId(61),Expr::App{fun:ExprId(61),arg:ExprId(1)}).unwrap();
        let checker=TypeChecker::new(&expressions,&levels,&environment);
        assert_eq!(checker.complete_source_support(ExprId(60),&mut 64),Some(vec![1]));
        assert!(checker.complete_source_support(ExprId(61),&mut 16).is_none());
        let probe=checker.strict_certificate_probe();
        assert!(Rc::ptr_eq(&checker.source_support,&probe.source_support));
        assert_eq!(probe.complete_source_support(ExprId(60),&mut 2),Some(vec![1]));
        assert!(!probe.source_support.borrow().contains_key(&ExprId(61)));
        let source=checker.closure(ExprId(60),EnvFrame::empty().extend_free(FreeId(0)));
        assert!(crate::convert::source_opening_avoids_capture(&probe,&source,FreeId(2),&mut 16));
        let colliding=checker.closure(ExprId(60),EnvFrame::empty().extend_free(FreeId(2)));
        assert!(!crate::convert::source_opening_avoids_capture(&probe,&colliding,FreeId(2),&mut 16),"pure support carries no evidence that a different captured binding avoids the fresh local");
        let other=TypeChecker::new(&expressions,&levels,&environment);
        assert!(!Rc::ptr_eq(&checker.source_support,&other.source_support));
    }

    #[test]
    fn completed_lexical_patterns_preserve_occurrences_intrinsic_binders_and_let_scope() {
        let (mut expressions,levels,environment,_)=fixture();
        for (id,expr) in [
            (60,Expr::BVar(1)),(61,Expr::BVar(2)),
            (62,Expr::Lam{domain:ExprId(1),body:ExprId(60)}),
            (63,Expr::Lam{domain:ExprId(1),body:ExprId(61)}),
            (64,Expr::Lam{domain:ExprId(1),body:ExprId(5)}),
            (65,Expr::App{fun:ExprId(5),arg:ExprId(5)}),
            (66,Expr::App{fun:ExprId(5),arg:ExprId(60)}),
            (67,Expr::App{fun:ExprId(60),arg:ExprId(5)}),
            (68,Expr::Lam{domain:ExprId(5),body:ExprId(60)}),
            (69,Expr::Lam{domain:ExprId(5),body:ExprId(5)}),
            (70,Expr::Let{ty:ExprId(1),value:ExprId(5),body:ExprId(60)}),
            (71,Expr::Let{ty:ExprId(1),value:ExprId(60),body:ExprId(5)}),
            (72,Expr::Lam{domain:ExprId(1),body:ExprId(62)}),
            (73,Expr::Lam{domain:ExprId(1),body:ExprId(64)}),
        ]{expressions.insert(ExprId(id),expr).unwrap();}
        let checker=TypeChecker::new(&expressions,&levels,&environment);
        for id in 62..74 {assert!(checker.lambda_candidate_hint(ExprId(id),&mut 4096).is_some());}
        let pattern=|id|checker.source_syntax_patterns.borrow().get(&ExprId(id)).unwrap().0;
        assert_eq!(pattern(62),pattern(63));
        assert_eq!(checker.complete_paired_source_support(ExprId(62),ExprId(63),&mut 2),Some(vec![(0,1)]));
        for (a,b) in [(62,64),(65,66),(66,67),(68,69),(70,71),(72,73)] {
            assert_eq!(checker.lambda_shape_ids.borrow().get(&ExprId(a)),checker.lambda_shape_ids.borrow().get(&ExprId(b)),"coarse hint intentionally forgets occurrence and binder distinctions");
            assert_ne!(pattern(a),pattern(b),"completed pattern must retain each lexical distinction");
        }
        assert!(checker.complete_paired_source_support(ExprId(62),ExprId(64),&mut 64).is_none());
        assert!(checker.complete_paired_source_support(ExprId(72),ExprId(73),&mut 64).is_none());
        assert!(checker.complete_paired_source_support(ExprId(62),ExprId(63),&mut 0).is_none());
    }

    #[test]
    fn completed_application_pattern_requires_joint_actual_source_goal_and_domains() {
        let (mut expressions,levels,environment,_)=fixture();
        expressions.insert(ExprId(60),Expr::BVar(1)).unwrap();
        expressions.insert(ExprId(61),Expr::App{fun:ExprId(3),arg:ExprId(60)}).unwrap();
        expressions.insert(ExprId(62),Expr::App{fun:ExprId(3),arg:ExprId(5)}).unwrap();
        let mut checker=TypeChecker::new(&expressions,&levels,&environment);checker.strict_origin_probe=true;
        let a=TypeValue::Term(checker.closure(ExprId(1),EnvFrame::empty()));
        let b=TypeValue::Term(checker.closure(ExprId(6),EnvFrame::empty()));
        let expected=checker.closure(ExprId(1),EnvFrame::empty());
        let old=EnvFrame::empty().extend_free(FreeId(0));checker.retain_checked_binding(&old,a.clone(),&[a.clone()]);
        assert!(checker.check_with_formation(ExprId(24),&a,&[a.clone()],&old,&mut 4096,true,&mut HashMap::new(),true).is_proven());
        for id in [24,61,62]{assert!(checker.lambda_candidate_hint(ExprId(id),&mut 128).is_some());}
        let pattern=checker.source_syntax_patterns.borrow().get(&ExprId(24)).unwrap().0;
        assert_eq!(checker.source_syntax_patterns.borrow().get(&ExprId(61)).unwrap().0,pattern);
        let source=checker.closure(ExprId(24),old.clone());
        let dependencies=checker.owned_goal_dependencies(&source,&expected,&[a.clone()],&mut 1024).unwrap();
        checker.owned_application_patterns.borrow_mut().insert((pattern,expected.expr),vec![OwnedLambdaGoal{source,expected:expected.clone(),dependencies}]);
        let renamed=EnvFrame::empty().extend_free(FreeId(1));checker.retain_checked_binding(&renamed,a.clone(),&[a.clone(),a.clone()]);
        let extra=renamed.extend_free(FreeId(2));let gamma=[a.clone(),a.clone(),b.clone()];
        checker.retain_checked_binding(&extra,b.clone(),&gamma);
        assert!(checker.reuse_owned_lambda_goal(ExprId(61),&checker.closure(ExprId(61),extra.clone()),&expected,&gamma,&mut 1024));
        assert!(!checker.reuse_owned_lambda_goal(ExprId(62),&checker.closure(ExprId(62),extra.clone()),&expected,&gamma,&mut 1024),"equal pure source pattern does not replace a used B domain by A");
        let unowned=EnvFrame::empty().extend_free(FreeId(1)).extend_free(FreeId(2));
        assert!(!checker.reuse_owned_lambda_goal(ExprId(61),&checker.closure(ExprId(61),unowned),&expected,&gamma,&mut 1024));
        checker.retain_checked_binding(&old,b.clone(),&[b]);
        assert!(!checker.reuse_owned_lambda_goal(ExprId(61),&checker.closure(ExprId(61),extra),&expected,&gamma,&mut 1024),"original quarantine revokes cross-source App checks");
    }

    #[test]
    fn completed_application_check_retains_actual_domain_and_quarantine() {
        let (mut expressions,levels,environment,_)=fixture();
        let mut body=ExprId(5);
        for id in 70..94 {expressions.insert(ExprId(id),Expr::App{fun:ExprId(3),arg:body}).unwrap();body=ExprId(id);}
        let mut checker=TypeChecker::new(&expressions,&levels,&environment);checker.strict_origin_probe=true;
        let a=TypeValue::Term(checker.closure(ExprId(1),EnvFrame::empty()));
        let b=TypeValue::Term(checker.closure(ExprId(6),EnvFrame::empty()));
        let target=checker.closure(ExprId(1),EnvFrame::empty());
        let old=EnvFrame::empty().extend_free(FreeId(0));checker.retain_checked_binding(&old,a.clone(),&[a.clone()]);
        assert!(checker.check_with_formation(body,&a,&[a.clone()],&old,&mut 4096,true,&mut HashMap::new(),true).is_proven());
        // This complete source checking premise, rather than a guessed output
        // type or a beta-erased value, is the sole authority for transport.
        let source=checker.closure(body,old.clone());
        let deps=checker.owned_goal_dependencies(&source,&target,&[a.clone()],&mut 1024).unwrap();
        checker.owned_lambda_goals.borrow_mut().insert(body,vec![OwnedLambdaGoal{source,expected:target.clone(),dependencies:deps}]);
        let renamed=EnvFrame::empty().extend_free(FreeId(1));checker.retain_checked_binding(&renamed,a.clone(),&[a.clone(),a.clone()]);
        assert!(checker.reuse_owned_lambda_goal(body,&checker.closure(body,renamed),&target,&[a.clone(),a.clone()],&mut 1024));
        let wrong=EnvFrame::empty().extend_free(FreeId(1));checker.retain_checked_binding(&wrong,b.clone(),&[a.clone(),b.clone()]);
        assert!(!checker.reuse_owned_lambda_goal(body,&checker.closure(body,wrong),&target,&[a.clone(),b.clone()],&mut 1024));
        checker.retain_checked_binding(&old,b.clone(),&[b]);
        assert!(!checker.reuse_owned_lambda_goal(body,&checker.closure(body,old),&target,&[a],&mut 1024));
    }

    #[test]
    fn completed_checking_renames_owned_binders_jointly_and_injectively() {
        let (mut expressions,levels,environment,_)=fixture();
        expressions.insert(ExprId(60),Expr::Lam{domain:ExprId(1),body:ExprId(61)}).unwrap();
        expressions.insert(ExprId(61),Expr::BVar(1)).unwrap();
        expressions.insert(ExprId(62),Expr::BVar(0)).unwrap();
        expressions.insert(ExprId(63),Expr::App{fun:ExprId(62),arg:ExprId(61)}).unwrap();
        let mut checker=TypeChecker::new(&expressions,&levels,&environment);checker.strict_origin_probe=true;
        let a=TypeValue::Term(checker.closure(ExprId(1),EnvFrame::empty()));
        let b=TypeValue::Term(checker.closure(ExprId(6),EnvFrame::empty()));
        let expected=checker.closure(ExprId(2),EnvFrame::empty());
        let old=EnvFrame::empty().extend_free(FreeId(0));
        checker.retain_checked_binding(&old,a.clone(),&[a.clone()]);
        assert!(checker.check_expected_lambda_in(ExprId(60),&TypeValue::Term(expected.clone()),
            &[a.clone()],&old,&mut 4096,true,&mut HashMap::new(),true).is_proven());
        let source=checker.closure(ExprId(60),old.clone());
        let dependencies=checker.owned_goal_dependencies(&source,&expected,&[a.clone()],&mut 1024).unwrap();
        checker.owned_lambda_goals.borrow_mut().insert(ExprId(60),vec![OwnedLambdaGoal{source:source.clone(),expected:expected.clone(),dependencies}]);
        let renamed=EnvFrame::empty().extend_free(FreeId(1));
        checker.retain_checked_binding(&renamed,a.clone(),&[a.clone(),a.clone()]);
        assert!(checker.reuse_owned_lambda_goal(ExprId(60),&checker.closure(ExprId(60),renamed.clone()),&expected,
            &[a.clone(),a.clone()],&mut 2048),"completed checking admits an owned binder of the same actual domain");
        // A single original Free used by subject and target cannot map to
        // different target Frees even if their checked domains coincide.
        let old_target=checker.closure(ExprId(62),old.clone());
        let proof=OwnedLambdaGoal{source:source.clone(),expected:old_target.clone(),dependencies:
            checker.owned_goal_dependencies(&source,&old_target,&[a.clone()],&mut 1024).unwrap()};
        let split=EnvFrame::empty().extend_free(FreeId(2));
        checker.retain_checked_binding(&split,a.clone(),&[a.clone(),a.clone(),a.clone()]);
        let new_source=checker.closure(ExprId(60),renamed.clone());
        let new_target=checker.closure(ExprId(62),split);
        let deps=checker.owned_goal_dependencies(&new_source,&new_target,&[a.clone(),a.clone(),a.clone()],&mut 1024).unwrap();
        assert!(!checker.joint_owned_goal_transport(&proof,&new_source,&new_target,&deps,&mut 2048));
        // Two distinct actual locals cannot collapse to one Free.
        let old_two=old.extend_free(FreeId(1));checker.retain_checked_binding(&old_two,a.clone(),&[a.clone(),a.clone()]);
        let collapse0=EnvFrame::empty().extend_free(FreeId(2));checker.retain_checked_binding(&collapse0,a.clone(),&[a.clone(),a.clone(),a.clone()]);
        let collapse=collapse0.extend_free(FreeId(2));checker.retain_checked_binding(&collapse,a.clone(),&[a.clone(),a.clone(),a.clone()]);
        let os=checker.closure(ExprId(63),old_two);let ns=checker.closure(ExprId(63),collapse);
        let proof=OwnedLambdaGoal{source:os.clone(),expected:expected.clone(),dependencies:
            checker.owned_goal_dependencies(&os,&expected,&[a.clone(),a.clone()],&mut 1024).unwrap()};
        let deps=checker.owned_goal_dependencies(&ns,&expected,&[a.clone(),a.clone(),a.clone()],&mut 1024).unwrap();
        assert!(!checker.joint_owned_goal_transport(&proof,&ns,&expected,&deps,&mut 2048));
        // Actual captured Closure binders retain their declared-domain premise.
        let actual=checker.closure(ExprId(4),EnvFrame::empty());
        let stored=EnvFrame::empty().extend(actual);checker.retain_checked_binding(&stored,a.clone(),&[a.clone()]);
        let cs=checker.closure(ExprId(60),stored.clone());
        assert!(checker.check_expected_lambda_in(ExprId(60),&TypeValue::Term(expected.clone()),&[a.clone()],&stored,&mut 4096,true,&mut HashMap::new(),true).is_proven());
        let deps=checker.owned_goal_dependencies(&cs,&expected,&[a.clone()],&mut 1024).unwrap();
        assert_eq!(deps.len(),1);assert_eq!(deps[0].free,None);
        checker.owned_lambda_goals.borrow_mut().insert(ExprId(60),vec![OwnedLambdaGoal{source:cs.clone(),expected:expected.clone(),dependencies:deps}]);
        assert!(checker.reuse_owned_lambda_goal(ExprId(60),&cs,&expected,&[a.clone()],&mut 2048));
        let different_declared=EnvFrame::empty().extend(checker.closure(ExprId(4),EnvFrame::empty()));
        checker.retain_checked_binding(&different_declared,b.clone(),&[b.clone()]);
        assert!(!checker.reuse_owned_lambda_goal(ExprId(60),&checker.closure(ExprId(60),different_declared),
            &expected,&[b.clone()],&mut 2048),"same stored actual value cannot erase a different checked declared domain");
        checker.retain_checked_binding(&stored,b.clone(),&[b]);
        assert!(!checker.reuse_owned_lambda_goal(ExprId(60),&cs,&expected,&[a],&mut 2048),"Closure declared-domain quarantine revokes completed checking");
    }

    #[test]
    fn exact_captured_pi_substitution_reuses_only_completed_same_scope_bindings() {
        let (mut expressions, levels, environment, _) = fixture();
        expressions.insert(ExprId(60), Expr::Const { name: NameId(5), levels: vec![] }).unwrap();
        expressions.insert(ExprId(61), Expr::App { fun: ExprId(3), arg: ExprId(60) }).unwrap();
        let environment = environment.extend(NameId(5),
            crate::environment::ConstantDecl::axiom(vec![], ExprId(1))).unwrap();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        let source = |id| Closure::new(ExprId(id), EnvFrame::empty());
        let context_a = [TypeValue::Term(source(1))];
        let context_b = [TypeValue::Term(source(6))];
        let infer = |id, context: &[TypeValue], fuel| {
            checker.infer_exact_closure_in_context(&source(id), context, &mut {fuel}, 0)
        };
        let frame = |value: TypeValue| match value { TypeValue::Term(c) => c.env.id(), _ => panic!("expected captured codomain") };
        let first = frame(infer(8, &context_a, 256).expect("argument typing and domain relation"));
        let repeat = frame(infer(8, &context_a, 256).expect("same complete source judgment"));
        assert_eq!(first, repeat, "exact source substitution must stabilize downstream inference frame keys");
        assert_ne!(first, frame(infer(61, &context_a, 256).unwrap()), "different actual argument remains distinct");
        assert_ne!(first, frame(infer(8, &context_b, 256).unwrap()), "different actual Gamma remains distinct");
        let before = checker.checked_frames.borrow().len();
        assert!(infer(7, &context_a, 256).is_none(), "wrong argument fails before registering a substitution frame");
        assert!(infer(8, &context_a, 0).is_none());
        assert_eq!(before, checker.checked_frames.borrow().len());
    }

    #[test]
    fn captured_pi_frame_key_preserves_own_codomain_levels_domain_and_quarantine() {
        let (expressions, levels, environment, _) = fixture();
        let mut checker = TypeChecker::new(&expressions, &levels, &environment);
        checker.strict_origin_probe = true;
        assert!(checker.is_type(ExprId(1), 256).is_proven());
        assert!(checker.is_type(ExprId(6), 256).is_proven());
        assert!(checker.infer(ExprId(4), 256).is_proven());
        let parent = EnvFrame::empty();
        let source = |id| Closure::new(ExprId(id), parent.clone());
        let domain = TypeValue::Term(source(1));
        let argument = source(4);
        let codomain = source(1);
        let context = [domain.clone()];
        let first = checker.checked_captured_pi_frame(&codomain, &argument, domain.clone(), &context);
        assert_eq!(first.id(), checker.checked_captured_pi_frame(&codomain, &argument, domain.clone(), &context).id());
        let other_levels = Closure::with_levels(codomain.expr, parent.clone(),
            LevelSubstitution::new(vec![(NameId(7), LevelTerm::Succ(Box::new(LevelTerm::Zero)))]));
        assert_ne!(first.id(), checker.checked_captured_pi_frame(&other_levels, &argument, domain.clone(), &context).id(), "full captured codomain own universe map belongs to the key");
        assert_ne!(first.id(), checker.checked_captured_pi_frame(&source(6), &argument, domain.clone(), &context).id(), "codomain source is part of exact scope");
        let other_domain = TypeValue::Term(source(6));
        assert_ne!(first.id(), checker.checked_captured_pi_frame(&codomain, &argument, other_domain.clone(), &context).id(), "checked domain remains exact");
        let other_parent = EnvFrame::empty().extend_free(FreeId(9));
        let other_codomain = Closure::new(codomain.expr, other_parent);
        assert_ne!(first.id(), checker.checked_captured_pi_frame(&other_codomain, &argument, domain.clone(), &context).id(), "actual captured parent identity remains exact");
        // A sibling/source conflict must never revive an old cached witness,
        // even when the substitution lineage capability is disabled.
        checker.retain_checked_binding(&first, domain.clone(), &context);
        checker.retain_checked_binding(&first, other_domain, &context);
        assert!(checker.checked_binding_lineage.borrow().get(&first.id()).unwrap().is_none());
        let replacement = checker.checked_captured_pi_frame(&codomain, &argument, domain.clone(), &context);
        assert_ne!(first.id(), replacement.id());
        assert!(checker.checked_binding_lineage.borrow().get(&first.id()).unwrap().is_none());
        let fixed = TypeValue::Pi { domain: Box::new(domain.clone()), body: Box::new(domain.clone()), binder: FreeId(0) , binder_owner: None,};
        let before = checker.checked_frames.borrow().len();
        let a = checker.checked_captured_pi_frame(&codomain, &argument, fixed.clone(), &context);
        let b = checker.checked_captured_pi_frame(&codomain, &argument, fixed, &context);
        assert_ne!(a.id(), b.id(), "unsupported recursive fixed-Pi key shapes fall back fresh");
        assert_eq!(before, checker.checked_frames.borrow().len());
    }

    #[test]
    fn closed_spine_is_shared_across_distinct_lexical_binders_with_one_step() {
        let (expressions, levels, environment, spine) = fixture();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        let prop = TypeValue::Term(Closure::new(ExprId(0), EnvFrame::empty()));
        let first_frame = EnvFrame::empty().extend_free(FreeId(0));
        let second_frame = first_frame.extend_free(FreeId(1));
        let mut cache = HashMap::new();
        let mut budget = 1024;
        let first = checker.infer_in(spine, &[prop.clone()], &first_frame, &mut budget, &mut cache);
        assert!(first.is_proven(), "source closed spine must independently type: {first:?}");
        let mut one_step = 1;
        let second = checker.infer_in(spine, &[prop.clone(), prop], &second_frame, &mut one_step, &mut cache);
        assert!(second.is_proven(), "closed judgment reuse across binder scopes: {second:?}");
        assert_eq!(second.proven_value(), first.proven_value());
        assert_eq!(one_step, 0, "cached proof reuse still consumes a step");
        assert_eq!(EnvFrame::empty().id(), 0);
        let mut one_step = 1;
        assert!(checker.infer_in(spine, &[], &second_frame, &mut one_step, &mut cache).is_proven(),
            "closedness licenses empty Γ even with a nonempty caller frame");
        let mut exhausted = 0;
        assert!(!checker.infer_in(spine, &[], &EnvFrame::empty(), &mut exhausted, &mut cache).is_proven());
    }

    #[test]
    fn open_spines_keep_their_distinct_typed_binders_and_wrong_closed_arguments_fail() {
        let (expressions, levels, environment, _) = fixture();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        let a = TypeValue::Term(Closure::new(ExprId(1), EnvFrame::empty()));
        let b = TypeValue::Term(Closure::new(ExprId(6), EnvFrame::empty()));
        let mut cache = HashMap::new();
        let mut budget = 128;
        let first = checker.infer_in(ExprId(5), &[a.clone()], &EnvFrame::empty().extend_free(FreeId(0)),
            &mut budget, &mut cache);
        let second = checker.infer_in(ExprId(5), &[b.clone()], &EnvFrame::empty().extend_free(FreeId(0)),
            &mut budget, &mut cache);
        assert_eq!(first.proven_value(), Some(&a));
        assert_eq!(second.proven_value(), Some(&b));
        let mut budget = 1024;
        let first = checker.infer_in(ExprId(24), &[a], &EnvFrame::empty().extend_free(FreeId(0)),
            &mut budget, &mut cache);
        let second = checker.infer_in(ExprId(24), &[b], &EnvFrame::empty().extend_free(FreeId(0)),
            &mut budget, &mut cache);
        assert!(first.is_proven());
        assert!(!second.is_proven(), "an App containing BVar cannot reuse the other scope's proof");
        assert!(!checker.infer(ExprId(7), 128).is_proven(), "closed syntax is not a typing warrant");
    }

    #[test]
    fn closed_spine_eligibility_exhaustion_does_not_poison_a_later_proof() {
        let (expressions, levels, environment, spine) = fixture();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        assert_eq!(checker.closed_spine_eligible(spine, 1), None);
        assert!(!checker.closed_spine_eligibility.borrow().contains_key(&spine));
        assert_eq!(checker.closed_spine_eligible(spine, 1024), Some(true));
        assert_eq!(checker.closed_spine_eligible(ExprId(24), 1024), Some(false));
        assert_eq!(checker.closed_spine_eligible(ExprId(2), 1024), Some(false));
    }

    #[test]
    fn repeated_literal_beta_spine_reuses_only_its_exact_checked_source_frame() {
        let (mut expressions, levels, environment, _) = fixture();
        expressions.insert(ExprId(25), Expr::BVar(1)).unwrap();
        let mut body = ExprId(25);
        for id in 26..42 {
            expressions.insert(ExprId(id), Expr::App { fun: ExprId(3), arg: body }).unwrap();
            body = ExprId(id);
        }
        expressions.insert(ExprId(42), Expr::Lam { domain: ExprId(1), body }).unwrap();
        expressions.insert(ExprId(43), Expr::App { fun: ExprId(42), arg: ExprId(4) }).unwrap();
        expressions.insert(ExprId(44), Expr::App { fun: ExprId(42), arg: ExprId(1) }).unwrap();
        let mut checker = TypeChecker::new(&expressions, &levels, &environment);
        checker.strict_origin_probe = true;
        let domain = TypeValue::Term(Closure::new(ExprId(1), EnvFrame::empty()));
        let frame = EnvFrame::empty().extend_free(FreeId(0));
        checker.retain_checked_binding(&frame, domain.clone(), &[domain.clone()]);
        let mut cache = HashMap::new();
        let mut fuel = 1024;
        assert!(checker.infer_in(ExprId(42), &[domain.clone()], &frame, &mut fuel, &mut cache).is_proven());
        let mut fuel = 1024;
        let first = checker.infer_literal_beta_spine(ExprId(43), &[domain.clone()], &frame,
            &mut fuel, &mut cache).expect("literal source spine");
        assert!(first.is_proven(), "first body must be independently typed: {first:?}");
        let mut fuel = 8;
        let second = checker.infer_literal_beta_spine(ExprId(43), &[domain.clone()], &frame,
            &mut fuel, &mut cache).expect("same literal source spine");
        assert!(second.is_proven(), "bounded repeated checked body: {second:?}");
        assert_eq!(first.proven_value(), second.proven_value());
        let mut fuel = 1024;
        assert!(!checker.infer_literal_beta_spine(ExprId(44), &[domain.clone()], &frame,
            &mut fuel, &mut cache).unwrap().is_proven(), "wrong actual argument cannot reuse a typed frame");
        let mut fuel = 0;
        assert!(checker.infer_literal_beta_spine(ExprId(43), &[domain], &frame,
            &mut fuel, &mut cache).is_none());
    }

    #[test]
    fn checked_frame_tuple_separates_source_role_context_domain_actual_and_authority() {
        let (mut expressions, levels, environment, _) = fixture();
        expressions.insert(ExprId(99), Expr::Const { name: NameId(5), levels: vec![] }).unwrap();
        let environment = environment.extend(NameId(5),
            crate::environment::ConstantDecl::axiom(vec![], ExprId(1))).unwrap();
        let mut checker = TypeChecker::new(&expressions, &levels, &environment);
        assert!(checker.is_type(ExprId(1), 128).is_proven());
        assert!(checker.is_type(ExprId(6), 128).is_proven());
        let parent = EnvFrame::empty();
        let a = TypeValue::Term(Closure::new(ExprId(1), parent.clone()));
        let b = TypeValue::Term(Closure::new(ExprId(6), parent.clone()));
        let binding = CheckedFrameBinding::Free(FreeId(0));
        let first = checker.checked_source_frame(ExprId(25), CheckedFrameRole::InferLambda,
            &parent, a.clone(), &[a.clone()], binding.clone());
        checker.strict_origin_probe = true;
        let exact = checker.checked_source_frame(ExprId(25), CheckedFrameRole::InferLambda,
            &parent, a.clone(), &[a.clone()], binding.clone());
        assert_ne!(first.id(), exact.id(), "different authority mode must get a fresh source frame");
        assert_eq!(checker.checked_source_frame(ExprId(25), CheckedFrameRole::InferLambda,
            &parent, a.clone(), &[a.clone()], binding.clone()).id(), exact.id());
        for other in [
            checker.checked_source_frame(ExprId(26), CheckedFrameRole::InferLambda,
                &parent, a.clone(), &[a.clone()], binding.clone()),
            checker.checked_source_frame(ExprId(25), CheckedFrameRole::ExpectedLambda,
                &parent, a.clone(), &[a.clone()], binding.clone()),
            checker.checked_source_frame(ExprId(25), CheckedFrameRole::InferLambda,
                &parent, b.clone(), &[b.clone()], binding.clone()),
            checker.checked_source_frame(ExprId(25), CheckedFrameRole::InferLambda,
                &parent, a.clone(), &[b.clone(), a.clone()], binding.clone()),
            checker.checked_source_frame(ExprId(25), CheckedFrameRole::InferLambda,
                &parent, a.clone(), &[a.clone()], CheckedFrameBinding::Free(FreeId(1))),
        ] { assert_ne!(other.id(), exact.id(), "a changed checked source tuple must remain distinct"); }
        let actual_a = Closure::new(ExprId(4), parent.clone());
        assert!(checker.infer(ExprId(99), 128).is_proven());
        let actual_b = Closure::new(ExprId(99), parent.clone());
        let applied = checker.checked_source_frame(ExprId(25), CheckedFrameRole::LiteralBeta,
            &parent, a.clone(), &[a.clone()], CheckedFrameBinding::Actual(actual_a.clone()));
        assert_eq!(checker.checked_source_frame(ExprId(25), CheckedFrameRole::LiteralBeta,
            &parent, a.clone(), &[a.clone()], CheckedFrameBinding::Actual(actual_a)).id(), applied.id());
        assert_ne!(checker.checked_source_frame(ExprId(25), CheckedFrameRole::LiteralBeta,
            &parent, a.clone(), &[a.clone()], CheckedFrameBinding::Actual(actual_b)).id(), applied.id());
        checker.retain_checked_binding(&exact, b, &[a.clone()]);
        assert!(checker.checked_binding_lineage.borrow().get(&exact.id()).unwrap().is_none());
        let fresh = checker.checked_source_frame(ExprId(25), CheckedFrameRole::InferLambda,
            &parent, a.clone(), &[a], binding);
        assert_ne!(fresh.id(), exact.id(), "a quarantined frame cannot lend its cached judgments");
        assert!(checker.checked_binding_lineage.borrow().get(&exact.id()).unwrap().is_none());
    }

    #[test]
    fn failed_binder_formation_and_argument_typing_do_not_create_checked_frames() {
        let (mut expressions, levels, environment, _) = fixture();
        expressions.insert(ExprId(25), Expr::Lam { domain: ExprId(4), body: ExprId(5) }).unwrap();
        expressions.insert(ExprId(26), Expr::Lam { domain: ExprId(1), body: ExprId(5) }).unwrap();
        expressions.insert(ExprId(27), Expr::App { fun: ExprId(26), arg: ExprId(1) }).unwrap();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        assert!(!checker.infer(ExprId(25), 1024).is_proven());
        assert!(checker.checked_frames.borrow().is_empty(), "formation failed before source-frame registration");
        assert!(checker.infer(ExprId(26), 1024).is_proven());
        let prior = checker.checked_frames.borrow().len();
        let mut budget = 1024;
        assert!(!checker.infer_literal_beta_spine(ExprId(27), &[], &EnvFrame::empty(),
            &mut budget, &mut HashMap::new()).unwrap().is_proven());
        assert_eq!(checker.checked_frames.borrow().len(), prior, "wrong argument cannot obtain a substitution frame");
    }

    #[test]
    fn checked_frame_saturation_preserves_old_scopes_and_uses_fresh_fallback() {
        let (expressions, levels, environment, _) = fixture();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        assert!(checker.is_type(ExprId(1), 128).is_proven());
        let domain = TypeValue::Term(Closure::new(ExprId(1), EnvFrame::empty()));
        let mut first = None;
        let mut last_parent = EnvFrame::empty();
        for _ in 0..8193 {
            let parent = EnvFrame::empty().extend_free(FreeId(0));
            let frame = checker.checked_source_frame(ExprId(25), CheckedFrameRole::InferLambda,
                &parent, domain.clone(), &[domain.clone(), domain.clone()], CheckedFrameBinding::Free(FreeId(1)));
            if first.is_none() { first = Some((parent.clone(), frame)); }
            last_parent = parent;
        }
        assert_eq!(checker.checked_frames.borrow().len(), 8192);
        let (parent, frame) = first.unwrap();
        assert_eq!(checker.checked_source_frame(ExprId(25), CheckedFrameRole::InferLambda,
            &parent, domain.clone(), &[domain.clone(), domain.clone()], CheckedFrameBinding::Free(FreeId(1))).id(), frame.id());
        let one = checker.checked_source_frame(ExprId(25), CheckedFrameRole::InferLambda,
            &last_parent, domain.clone(), &[domain.clone(), domain.clone()], CheckedFrameBinding::Free(FreeId(1)));
        let two = checker.checked_source_frame(ExprId(25), CheckedFrameRole::InferLambda,
            &last_parent, domain.clone(), &[domain.clone(), domain], CheckedFrameBinding::Free(FreeId(1)));
        assert_ne!(one.id(), two.id(), "saturation declines sharing instead of merging unrelated source scopes");
    }

    #[test]
    fn formed_dependent_literal_lambda_checks_before_whole_function_inference_at_bounded_fuel() {
        let (mut expressions, levels, environment, _) = fixture();
        expressions.insert(ExprId(200), Expr::BVar(24)).unwrap();
        let mut value = ExprId(5);
        let mut expected = ExprId(200);
        let mut next = 201;
        for depth in (1..=24).rev() {
            let domain = ExprId(next); next += 1;
            expressions.insert(domain, Expr::BVar(depth - 1)).unwrap();
            let lambda = ExprId(next); next += 1;
            expressions.insert(lambda, Expr::Lam { domain, body: value }).unwrap();
            value = lambda;
            let pi = ExprId(next); next += 1;
            expressions.insert(pi, Expr::Pi { domain, body: expected }).unwrap();
            expected = pi;
        }
        let lambda = ExprId(next); next += 1;
        expressions.insert(lambda, Expr::Lam { domain: ExprId(0), body: value }).unwrap();
        let pi = ExprId(next);
        expressions.insert(pi, Expr::Pi { domain: ExprId(0), body: expected }).unwrap();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        let expected = TypeValue::Term(checker.closure(pi, EnvFrame::empty()));
        assert!(!checker.check_formed(lambda, &expected, 64).is_proven(), "a Pi shape is not formation authority");
        assert!(checker.is_type(pi, 4096).is_proven(), "expected dependent telescope must be formed first");
        assert!(!checker.check(lambda, &expected, 64).is_proven(), "unchecked public entry remains ordinary-first");
        let ordinary = TypeChecker::new(&expressions, &levels, &environment);
        let ordinary_expected = TypeValue::Term(ordinary.closure(pi, EnvFrame::empty()));
        assert!(!ordinary.check(lambda, &ordinary_expected, 768).is_proven(), "ordinary whole-function inference still exceeds the guarded bounded resource envelope");
        // Complete source support and actual capture freshness now consume
        // real work. Keep the guided rule bounded without raising kernel caps.
        let bounded = checker.check_formed(lambda, &expected, 768);
        if std::env::var_os("NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA").is_some() {
            assert!(bounded.is_proven(), "formed expected telescope should guide checked lambda: {bounded:?}");
        } else {
            assert!(!bounded.is_proven(), "formation cannot enable a disabled capability");
        }
        assert!(!checker.check_formed(lambda, &expected, 0).is_proven());
    }

    #[test]
    fn formed_lambda_entry_rejects_failed_expected_formation_bad_bodies_and_wrong_domains() {
        let (mut expressions, levels, environment, _) = fixture();
        for (id, expression) in [
            (60, Expr::Lam { domain: ExprId(0), body: ExprId(1) }),
            (61, Expr::Pi { domain: ExprId(0), body: ExprId(0) }),
            (62, Expr::Lam { domain: ExprId(4), body: ExprId(5) }),
            (63, Expr::Lam { domain: ExprId(0), body: ExprId(4) }),
            (64, Expr::Pi { domain: ExprId(4), body: ExprId(0) }),
            (65, Expr::Pi { domain: ExprId(0), body: ExprId(4) }),
            (66, Expr::Let { ty: ExprId(1), value: ExprId(1), body: ExprId(0) }),
            (67, Expr::Pi { domain: ExprId(0), body: ExprId(66) }),
            (68, Expr::Lam { domain: ExprId(2), body: ExprId(4) }),
            (69, Expr::App { fun: ExprId(68), arg: ExprId(60) }),
        ] { expressions.insert(ExprId(id), expression).unwrap(); }
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        for malformed in [64, 65, 67] {
            assert!(!checker.is_type(ExprId(malformed), 4096).is_proven(), "malformed Pi must actually fail formation");
            let expected = TypeValue::Term(checker.closure(ExprId(malformed), EnvFrame::empty()));
            assert!(!checker.check_formed(ExprId(60), &expected, 4096).is_proven(), "failed formation cannot register a checking warrant");
        }
        assert!(checker.is_type(ExprId(61), 4096).is_proven());
        let expected = TypeValue::Term(checker.closure(ExprId(61), EnvFrame::empty()));
        assert!(checker.check_formed(ExprId(60), &expected, 4096).is_proven());
        for invalid in [62, 63] {
            assert!(!checker.check_formed(ExprId(invalid), &expected, 4096).is_proven(), "bad annotation or body must still fail");
        }
        assert!(!checker.infer(ExprId(69), 4096).is_proven(), "lambda argument must check its actual expected function domain");
        let changed_scope = TypeValue::Term(checker.closure(ExprId(61), EnvFrame::empty().extend_free(FreeId(0))));
        assert!(!checker.check_formed(ExprId(60), &changed_scope, 4096).is_proven(), "closed formation does not certify a different captured scope");
        let non_pi = TypeValue::Term(checker.closure(ExprId(1), EnvFrame::empty()));
        assert!(checker.is_type(ExprId(1), 4096).is_proven());
        assert!(!checker.check_formed(ExprId(60), &non_pi, 4096).is_proven(), "lambda shape alone cannot replace a Pi premise");
    }

    #[test]
    fn formed_fixed_pi_checking_does_not_bypass_capture_safe_reopening() {
        let (mut expressions, levels, environment, _) = fixture();
        expressions.insert(ExprId(60), Expr::Lam { domain: ExprId(5), body: ExprId(5) }).unwrap();
        expressions.insert(ExprId(61), Expr::Lam { domain: ExprId(0), body: ExprId(60) }).unwrap();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        let inferred = checker.infer(ExprId(61), 4096);
        let expected = inferred.proven_value().expect("closed dependent lambda is independently typed");
        let a = TypeValue::Term(checker.closure(ExprId(1), EnvFrame::empty()));
        let frame = EnvFrame::empty().extend_free(FreeId(0));
        checker.retain_checked_binding(&frame, a.clone(), &[a.clone()]);
        let mut fuel = 4096;
        let result = checker.check_with_formation(ExprId(61), expected, &[a], &frame,
            &mut fuel, true, &mut HashMap::new(), true);
        assert!(!result.is_proven(), "reopening outer binder 0 as 1 collides with its retained inner binder 1");
    }

    #[test]
    fn repeated_checked_open_let_reuses_only_its_exact_source_scope() {
        let (mut expressions, levels, environment, _) = fixture();
        expressions.insert(ExprId(100), Expr::BVar(1)).unwrap();
        let mut body = ExprId(100);
        for id in 101..125 {
            expressions.insert(ExprId(id), Expr::App { fun: ExprId(3), arg: body }).unwrap();
            body = ExprId(id);
        }
        expressions.insert(ExprId(125), Expr::Let { ty: ExprId(1), value: ExprId(5), body }).unwrap();
        expressions.insert(ExprId(126), Expr::Let { ty: ExprId(1), value: ExprId(1), body }).unwrap();
        let mut checker = TypeChecker::new(&expressions, &levels, &environment);
        checker.strict_origin_probe = true;
        let a = TypeValue::Term(checker.closure(ExprId(1), EnvFrame::empty()));
        let frame = EnvFrame::empty().extend_free(FreeId(0));
        checker.retain_checked_binding(&frame, a.clone(), &[a.clone()]);
        let mut cache = HashMap::new();
        let mut fuel = 4096;
        let first = checker.infer_uncached(ExprId(125), &[a.clone()], &frame, &mut fuel, &mut cache);
        assert!(first.is_proven(), "first Let must independently check its premises: {first:?}");
        let mut fuel = 8;
        let second = checker.infer_uncached(ExprId(125), &[a.clone()], &frame, &mut fuel, &mut cache);
        assert!(second.is_proven(), "same checked Let body within budget: {second:?}");
        assert_eq!(first.proven_value(), second.proven_value());
        let retained = checker.checked_frames.borrow().len();
        let mut fuel = 4096;
        assert!(!checker.infer_uncached(ExprId(126), &[a.clone()], &frame, &mut fuel, &mut cache).is_proven());
        assert_eq!(retained, checker.checked_frames.borrow().len(), "failed value typing must not retain a frame");
        let mut fuel = 0;
        assert!(!checker.infer_uncached(ExprId(125), &[a], &frame, &mut fuel, &mut cache).is_proven());
    }

    #[test]
    fn nondependent_arrow_failure_remains_nonaccepting_under_finite_allowance() {
        if std::env::var_os("NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA").is_none(){return;}
        let(mut expressions,levels,environment,_)=fixture();
        let mut value=ExprId(4); // Original invalid p:A body against Prop.
        let mut expected=ExprId(0);let mut next=100;
        for _ in 0..12 {
            let lambda=ExprId(next);next+=1;
            expressions.insert(lambda,Expr::Lam{domain:ExprId(0),body:value}).unwrap();value=lambda;
            let pi=ExprId(next);next+=1;
            expressions.insert(pi,Expr::Pi{domain:ExprId(0),body:expected}).unwrap();expected=pi;
        }
        let checker=TypeChecker::new(&expressions,&levels,&environment);
        assert!(checker.is_type(expected,4096).is_proven());
        let expected=TypeValue::Term(checker.closure(expected,EnvFrame::empty()));
        let mut remaining=128;
        assert!(!checker.check_with_formation(value,&expected,&[],&EnvFrame::empty(),
            &mut remaining,true,&mut HashMap::new(),true).is_proven());
        assert!(remaining<128,"failed inference consumes actual work");
        let state=checker.lambda_trials.borrow();
        assert_eq!(state.active,0);assert!(state.spent<=128,"fallback stays within the finite original allowance");
        drop(state);
        assert!(!checker.check_with_formation(value,&expected,&[],&EnvFrame::empty(),
            &mut 0,true,&mut HashMap::new(),true).is_proven());
    }

    #[test]
    fn closed_arrow_goal_still_checks_unbound_original_lambda_body() {
        let(mut expressions,levels,environment,_)=fixture();
        expressions.insert(ExprId(80),Expr::BVar(1)).unwrap();
        expressions.insert(ExprId(81),Expr::Lam{domain:ExprId(1),body:ExprId(80)}).unwrap();
        let checker=TypeChecker::new(&expressions,&levels,&environment);
        assert!(checker.is_type(ExprId(2),4096).is_proven());
        let goal=TypeValue::Term(checker.closure(ExprId(2),EnvFrame::empty()));
        assert!(!checker.check_formed(ExprId(81),&goal,4096).is_proven());
        assert!(!checker.check_formed(ExprId(81),&goal,0).is_proven());
    }

    #[test]
    fn primary_formed_lambda_failure_uses_only_the_global_finite_allowance() {
        if std::env::var_os("NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA").is_none() { return; }
        let (mut expressions, levels, environment, _) = fixture();
        let mut value = ExprId(4); // p : A, never a proposition expression
        // A genuinely dependent source telescope: its final proposition is
        // the first introduced P, not a pure-arrow constant codomain.
        expressions.insert(ExprId(99),Expr::BVar(11)).unwrap();
        let mut expected = ExprId(99);
        let mut next = 100;
        for _ in 0..12 {
            let lambda = ExprId(next); next += 1;
            expressions.insert(lambda, Expr::Lam { domain: ExprId(0), body: value }).unwrap();
            value = lambda;
            let pi = ExprId(next); next += 1;
            expressions.insert(pi, Expr::Pi { domain: ExprId(0), body: expected }).unwrap();
            expected = pi;
        }
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        assert!(checker.is_type(expected, 4096).is_proven());
        let expected = TypeValue::Term(checker.closure(expected, EnvFrame::empty()));
        let mut remaining=128;
        assert!(!checker.check_with_formation(value,&expected,&[],&EnvFrame::empty(),
            &mut remaining,true,&mut HashMap::new(),true).is_proven());
        assert!(remaining<128,"failed primary derivation consumes its actual work");
        let state=checker.lambda_trials.borrow().clone();
        assert_eq!(state.active,0);
        assert_eq!(state.started,0,"a formed Pi goal uses primary checking rather than a speculative trial");
        assert_eq!(state.spent,0);
        assert!(!checker.check_with_formation(value,&expected,&[],&EnvFrame::empty(),
            &mut 0,true,&mut HashMap::new(),true).is_proven());
    }

    #[test]
    fn closed_spine_universe_instantiation_stays_with_its_checker() {
        let mut expressions = IdTable::default();
        let mut levels = IdTable::default();
        levels.insert(LevelId(0), Level::Param(NameId(9))).unwrap();
        expressions.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
        expressions.insert(ExprId(1), Expr::Const { name: NameId(1), levels: vec![LevelId(0)] }).unwrap();
        let environment = Environment::empty().extend(NameId(1),
            crate::environment::ConstantDecl::axiom(vec![NameId(9)], ExprId(0))).unwrap();
        let check = |level| TypeChecker::with_level_substitution(&expressions, &levels, &environment,
            HashMap::from([(NameId(9), level)]));
        let low_checker = check(LevelTerm::Zero);
        let high_checker = check(succ(LevelTerm::Zero));
        let low = low_checker.infer(ExprId(1), 128);
        let high = high_checker.infer(ExprId(1), 128);
        assert!(low.is_proven() && high.is_proven());
        assert_ne!(low.proven_value(), high.proven_value(), "universes do not inherit another checker cache");
        let parent = EnvFrame::empty();
        let low_domain = TypeValue::Term(low_checker.closure(ExprId(1), parent.clone()));
        let high_domain = TypeValue::Term(high_checker.closure(ExprId(1), parent.clone()));
        let low_frame = low_checker.checked_source_frame(ExprId(2), CheckedFrameRole::InferLambda,
            &parent, low_domain.clone(), &[low_domain], CheckedFrameBinding::Free(FreeId(0)));
        let high_frame = high_checker.checked_source_frame(ExprId(2), CheckedFrameRole::InferLambda,
            &parent, high_domain.clone(), &[high_domain], CheckedFrameBinding::Free(FreeId(0)));
        assert_ne!(low_frame.id(), high_frame.id(), "distinct checker universes have separate frame stores");
    }
}

#[cfg(test)]
mod exact_source_support_controls {
    use super::*;

    #[test]
    fn root_source_alias_uses_the_captured_lambda_and_its_own_level_map() {
        let mut expressions = IdTable::default();
        let mut levels = IdTable::default();
        levels.insert(LevelId(0), crate::syntax::Level::Zero).unwrap();
        for (id, node) in [
            (0, Expr::Sort(LevelId(0))), (1, Expr::BVar(0)), (2, Expr::BVar(1)),
            (3, Expr::Lam { domain: ExprId(0), body: ExprId(2) }),
        ] { expressions.insert(ExprId(id), node).unwrap(); }
        let environment = Environment::empty();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        let payload = |free| Closure::new(ExprId(3), EnvFrame::empty().extend_free(FreeId(free)));
        let alias = |captured: Closure| {
            let mut value = captured;
            for _ in 0..37 { value = Closure::new(ExprId(1), EnvFrame::empty().extend(value)); }
            Closure::with_levels(ExprId(1), EnvFrame::empty().extend(value),
                LevelSubstitution::new(vec![(NameId(7), LevelTerm::Succ(Box::new(LevelTerm::Zero)))]))
        };
        let original=payload(9);
        assert!(checker.exact_source_capture_identity(&alias(original.clone()), &original, &mut 128), "actual root alias discards outer BVar level map, preserving the stored lambda map");
        assert!(!checker.exact_source_capture_identity(&alias(payload(10)), &payload(9), &mut 128));
        assert!(!checker.exact_source_capture_identity(&alias(original.clone()), &original, &mut 0));
        let changed = Closure::with_levels(ExprId(3), original.env.clone(),
            LevelSubstitution::new(vec![(NameId(7), LevelTerm::Succ(Box::new(LevelTerm::Zero)))]));
        assert!(!checker.exact_source_capture_identity(&alias(changed), &original, &mut 128));
        let free0 = Closure::new(ExprId(1), EnvFrame::empty().extend_free(FreeId(0)));
        assert!(!checker.exact_source_capture_identity(&free0, &payload(0), &mut 128));
    }

    #[test]
    fn captured_source_inference_cannot_type_an_ambient_local_by_opening_a_binder() {
        let mut expressions = IdTable::default();
        let mut levels = IdTable::default();
        levels.insert(LevelId(0), crate::syntax::Level::Zero).unwrap();
        for (id, node) in [
            (0, Expr::Sort(LevelId(0))), (1, Expr::BVar(0)), (2, Expr::BVar(1)),
            (3, Expr::Lam { domain: ExprId(0), body: ExprId(1) }),
            (4, Expr::Lam { domain: ExprId(0), body: ExprId(2) }),
        ] { expressions.insert(ExprId(id), node).unwrap(); }
        let environment = Environment::empty();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        let source = |id| Closure::new(ExprId(id), EnvFrame::empty().extend_free(FreeId(0)));
        assert!(checker.infer_exact_closure_in_context(&source(3), &[], &mut 256, 0).is_some());
        assert!(checker.infer_exact_closure_in_context(&source(4), &[], &mut 256, 0).is_none(), "untyped ambient Free0 is not the newly introduced source binder");
    }

    #[test]
    fn paired_support_preserves_binder_capture_constructor_and_level_distinctions() {
        let mut expressions = IdTable::default();
        let mut levels = IdTable::default();
        levels.insert(LevelId(0), crate::syntax::Level::Zero).unwrap();
        levels.insert(LevelId(1), crate::syntax::Level::Succ(LevelId(0))).unwrap();
        for (id, node) in [
            (0, Expr::Sort(LevelId(0))), (1, Expr::BVar(0)), (2, Expr::BVar(1)),
            (3, Expr::Lam { domain: ExprId(0), body: ExprId(1) }),
            (4, Expr::Lam { domain: ExprId(0), body: ExprId(2) }),
            (5, Expr::Sort(LevelId(1))),
            (6, Expr::Const { name: NameId(1), levels: vec![LevelId(0)] }),
            (7, Expr::Const { name: NameId(1), levels: vec![LevelId(1)] }),
            (8, Expr::Const { name: NameId(2), levels: vec![LevelId(0)] }),
            (9, Expr::Pi { domain: ExprId(1), body: ExprId(1) }),
            (10, Expr::Pi { domain: ExprId(2), body: ExprId(1) }),
            (11, Expr::Let { ty: ExprId(0), value: ExprId(1), body: ExprId(1) }),
            (12, Expr::Let { ty: ExprId(0), value: ExprId(2), body: ExprId(1) }),
            (13, Expr::Proj { type_name: NameId(1), index: 0, structure: ExprId(1) }),
            (14, Expr::Proj { type_name: NameId(1), index: 0, structure: ExprId(2) }),
            (15, Expr::Proj { type_name: NameId(1), index: 1, structure: ExprId(2) }),
            (16, Expr::Lam { domain: ExprId(0), body: ExprId(16) }),
            (17, Expr::Lam { domain: ExprId(0), body: ExprId(17) }),
            (18, Expr::StrLit("left".into())), (19, Expr::StrLit("right".into())),
        ] { expressions.insert(ExprId(id), node).unwrap(); }
        let environment = Environment::empty();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        let original_owner=EnvFrame::empty().extend_free(FreeId(0));
        let left = |id| Closure::new(ExprId(id), original_owner.clone());
        let right = |id, used| Closure::new(ExprId(id), if used==0{original_owner.clone()}else{EnvFrame::empty().extend_free(FreeId(used))}.extend_free(FreeId(99)));
        assert!(!checker.exact_source_capture_identity(&left(3), &left(4), &mut 128), "bound variable must not identify ambient Free0");
        assert!(!checker.exact_source_capture_identity(&left(9), &right(10, 0), &mut 0));
        assert!(checker.exact_source_capture_identity(&left(9), &right(10, 0), &mut 128), "exhaustion must not cache an incomplete paired proof");
        for (a, b) in [(0, 5), (6, 7), (6, 8), (13, 15), (18, 19), (16, 17)] {
            assert!(!checker.exact_source_capture_identity(&left(a), &right(b, 0), &mut 128), "structural distinction or cycle {a}/{b}");
        }
        for (a, b) in [(9, 10), (11, 12), (13, 14)] {
            assert!(checker.exact_source_capture_identity(&left(a), &right(b, 0), &mut 128), "all used captures match at {a}/{b}");
            assert!(!checker.exact_source_capture_identity(&left(a), &right(b, 1), &mut 128), "used capture changed at {a}/{b}");
        }
        assert!(checker.complete_paired_source_support(ExprId(3), ExprId(4), &mut 0).is_none());
        assert!(checker.complete_paired_source_support(ExprId(3), ExprId(4), &mut 128).is_none());
    }

    #[test]
    fn every_annotation_value_projection_and_external_capture_is_accounted_for() {
        let mut expressions = IdTable::default();
        let mut levels = IdTable::default();
        levels.insert(LevelId(0), crate::syntax::Level::Zero).unwrap();
        for (id, node) in [
            (0, Expr::Sort(LevelId(0))), (1, Expr::BVar(0)), (2, Expr::BVar(1)),
            (3, Expr::Lam { domain: ExprId(0), body: ExprId(1) }),
            (4, Expr::Lam { domain: ExprId(1), body: ExprId(1) }),
            (5, Expr::Pi { domain: ExprId(0), body: ExprId(2) }),
            (6, Expr::Let { ty: ExprId(1), value: ExprId(0), body: ExprId(0) }),
            (7, Expr::Let { ty: ExprId(0), value: ExprId(1), body: ExprId(0) }),
            (8, Expr::Proj { type_name: NameId(1), index: 0, structure: ExprId(1) }),
            (9, Expr::Lam { domain: ExprId(0), body: ExprId(9) }),
        ] { expressions.insert(ExprId(id), node).unwrap(); }
        let environment = Environment::empty();
        let checker = TypeChecker::new(&expressions, &levels, &environment);
        let term = |id, free| Closure::new(ExprId(id), EnvFrame::empty().extend_free(FreeId(free)));
        assert!(checker.exact_source_capture_identity(&term(3, 1), &term(3, 2), &mut 128), "internally bound variables mask unused external frames");
        for id in [4, 5, 6, 7, 8] {
            assert!(!checker.exact_source_capture_identity(&term(id, 1), &term(id, 2), &mut 128), "used capture cannot be ignored at source{id}");
        }
        assert!(!checker.exact_source_capture_identity(&term(9, 1), &term(9, 1), &mut 128), "source cycles are not coinductive equality proofs");
        let original=term(4,1);
        assert!(!checker.exact_source_capture_identity(&original, &original, &mut 0));
        assert!(checker.exact_source_capture_identity(&original, &original, &mut 128), "exhaustion must not memoize incomplete support");
        assert!(!checker.exact_source_capture_identity(&original,&term(4,1),&mut 128),"same numerical capture at an independent owner remains distinct");
    }
}

#[cfg(test)]
mod opening_memo_tests {
    use super::*;
    fn fixture()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
        let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();
        for (id,node) in [(0,Expr::Sort(LevelId(0))),(1,Expr::BVar(0)),(2,Expr::BVar(1)),(3,Expr::BVar(2)),(4,Expr::Lam{domain:ExprId(4),body:ExprId(1)})] {e.insert(ExprId(id),node).unwrap();}(e,l,Environment::empty())
    }
    #[test]
    fn completed_exact_freshness_proof_reuses_at_paid_one_step() {
        let(e,l,env)=fixture();let checker=TypeChecker::new(&e,&l,&env);
        let mut captured=Closure::new(ExprId(1),EnvFrame::empty().extend_free(FreeId(9)));
        for _ in 0..12{captured=Closure::new(ExprId(1),EnvFrame::empty().extend(captured));}
        let body=Closure::new(ExprId(2),EnvFrame::empty().extend(captured));
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut 1));
        assert!(crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut 128));
        let mut fuel=1;assert!(crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut fuel),"completed exact capture proof should avoid repeating its transitive walk");assert_eq!(fuel,0);
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut 0));
    }
    #[test]
    fn freshness_memo_separates_source_frame_level_instance_and_actual_free() {
        let(e,l,env)=fixture();let checker=TypeChecker::new(&e,&l,&env);
        let parent=EnvFrame::empty().extend_free(FreeId(9));let body=Closure::new(ExprId(2),parent.clone());
        assert!(crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut 32));
        for changed in [
            Closure::new(ExprId(3),parent.clone()),
            Closure::new(ExprId(2),EnvFrame::empty().extend_free(FreeId(9))),
            Closure::with_levels(ExprId(2),parent.clone(),LevelSubstitution::new(vec![])),
            Closure::with_levels(ExprId(2),parent.clone(),LevelSubstitution::new(vec![(NameId(7),LevelTerm::Succ(Box::new(LevelTerm::Zero)))])),
        ] {
            assert!(!checker.has_source_opening_proof(&changed,FreeId(0)),"distinct immutable source/frame/level key has no borrowed proof");
            let valid=changed.expr==ExprId(2);
            assert_eq!(crate::convert::source_opening_avoids_capture(&checker,&changed,FreeId(0),&mut 1),valid,"a direct actual payload can independently complete in one paid fused node; the unbound BVar2 still declines");
        }
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(9),&mut 32));
        let collision=Closure::new(ExprId(2),EnvFrame::empty().extend_free(FreeId(0)));
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&collision,FreeId(0),&mut 32));
        for malformed in [Closure::new(ExprId(999),parent.clone()),Closure::new(ExprId(4),parent.clone()),Closure::new(ExprId(2),EnvFrame::empty())] {
            assert!(!crate::convert::source_opening_avoids_capture(&checker,&malformed,FreeId(0),&mut 32));
            assert!(!checker.has_source_opening_proof(&malformed,FreeId(0)));
        }
        let other=TypeChecker::new(&e,&l,&env);
        assert!(!other.has_source_opening_proof(&body,FreeId(0)),"completed proofs do not cross independent checker scope");
        assert!(!Rc::ptr_eq(&checker.source_capture_free_support,&other.source_capture_free_support));
        assert!(crate::convert::source_opening_avoids_capture(&other,&body,FreeId(0),&mut 1),"the independent checker validates this exact direct payload in its own paid node");
        assert!(crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut 1));
    }
    #[test]
    fn cold_freshness_cost_and_saturation_preserve_original_guard() {
        let(e,l,env)=fixture();let checker=TypeChecker::new(&e,&l,&env);let body=Closure::new(ExprId(1),EnvFrame::empty());
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut 0));
        assert!(!checker.has_source_opening_proof(&body,FreeId(0)));
        let mut cold=1;assert!(crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut cold));assert_eq!(cold,0,"the exact intrinsic BVar node requires one paid visit");
        for _ in 1..8192 {let distinct=Closure::new(ExprId(1),EnvFrame::empty().extend_free(FreeId(9)));assert!(crate::convert::source_opening_avoids_capture(&checker,&distinct,FreeId(0),&mut 8));}
        assert_eq!(checker.source_opening_proofs.borrow().len(),8192);
        assert!(crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut 1));
        let overflow=Closure::new(ExprId(1),EnvFrame::empty().extend_free(FreeId(9)));
        assert!(crate::convert::source_opening_avoids_capture(&checker,&overflow,FreeId(0),&mut 8));
        assert!(!checker.has_source_opening_proof(&overflow,FreeId(0)),"saturation does not publish the overflow source");
        assert!(crate::convert::source_opening_avoids_capture(&checker,&overflow,FreeId(0),&mut 1),"the intrinsic source is independently revalidated at its actual one-node cost");
        let dangling=Closure::new(ExprId(2),EnvFrame::empty());
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&dangling,FreeId(0),&mut 32));
        assert_eq!(checker.source_opening_proofs.borrow().len(),8192);
    }

}

#[cfg(test)]
mod lambda_role_sharing_tests {
    use super::*;
    fn fixture()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
        let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();
        for (id,node) in [(0,Expr::Sort(LevelId(0))),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::Const{name:NameId(2),levels:vec![]}),(3,Expr::BVar(0)),(4,Expr::Pi{domain:ExprId(1),body:ExprId(1)}),(5,Expr::Const{name:NameId(3),levels:vec![]}),(6,Expr::App{fun:ExprId(5),arg:ExprId(3)}),(7,Expr::App{fun:ExprId(5),arg:ExprId(6)}),(8,Expr::Lam{domain:ExprId(1),body:ExprId(7)}),(9,Expr::Pi{domain:ExprId(1),body:ExprId(2)}),(10,Expr::Lam{domain:ExprId(1),body:ExprId(7)})] {e.insert(ExprId(id),node).unwrap();}
        let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(3),crate::environment::ConstantDecl::axiom(vec![],ExprId(4))).unwrap();(e,l,env)
    }
    #[test]
    fn declined_goal_keeps_proven_subject_types_in_the_identical_lambda_scope() {
        let (e,l,env)=fixture();let checker=TypeChecker::new(&e,&l,&env);let root=EnvFrame::empty();
        assert!(checker.is_type(ExprId(9),128).is_proven());
        let wrong=TypeValue::Term(checker.closure(ExprId(9),root.clone()));let mut memo=HashMap::new();
        let declined=checker.check_expected_lambda_in(ExprId(8),&wrong,&[],&root,&mut 256,true,&mut memo,true);assert!(!declined.is_proven(),"a valid subject type does not prove a different expected goal");
        let old=checker.checked_frames.borrow().iter().find(|(key,_)|key.source==ExprId(8)).unwrap().1.clone();assert!(memo.contains_key(&(ExprId(7),old.id())));
        let inferred=checker.infer_in(ExprId(8),&[],&root,&mut 4,&mut memo);
        assert!(inferred.is_proven(),"the ordinary route must reuse independently proved types under the identical introduced binder: {inferred:?}");
        assert_eq!(checker.checked_frames.borrow().keys().filter(|key|key.source==ExprId(8)).count(),1,"role-only differences cannot reopen the same certified lambda scope");
        let inferred_ample=checker.infer(ExprId(8),256);assert!(checker.convert(inferred.proven_value().unwrap(),inferred_ample.proven_value().unwrap(),256).is_proven());
        let wrong_again=checker.check_expected_lambda_in(ExprId(8),&wrong,&[],&root,&mut 256,true,&mut memo,true);assert!(!wrong_again.is_proven(),"inference memo must not cache acceptance of an unrelated expected goal");
    }
    #[test]
    fn lambda_role_sharing_preserves_every_scope_field_and_other_roles() {
        let (e,l,env)=fixture();let checker=TypeChecker::new(&e,&l,&env);let root=EnvFrame::empty();
        assert!(checker.is_type(ExprId(1),128).is_proven());
        let a=TypeValue::Term(checker.closure(ExprId(1),root.clone()));
        let b=TypeValue::Term(checker.closure(ExprId(2),root.clone()));
        let frame=|source,role,parent:&EnvFrame,domain:TypeValue,ctx:&[TypeValue],binding|checker.checked_source_frame(source,role,parent,domain,ctx,binding);
        let first=frame(ExprId(8),CheckedFrameRole::ExpectedLambda,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Free(FreeId(0)));
        assert_eq!(first.id(),frame(ExprId(8),CheckedFrameRole::InferLambda,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Free(FreeId(0))).id());
        let parent=root.extend_free(FreeId(9));
        let changed_levels=TypeValue::Term(Closure::with_levels(ExprId(1),root.clone(),LevelSubstitution::new(vec![(NameId(7),LevelTerm::Succ(Box::new(LevelTerm::Zero)))])));
        for other in [
            frame(ExprId(10),CheckedFrameRole::InferLambda,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Free(FreeId(0))),
            frame(ExprId(8),CheckedFrameRole::InferLambda,&root,b.clone(),&[b.clone()],CheckedFrameBinding::Free(FreeId(0))),
            frame(ExprId(8),CheckedFrameRole::InferLambda,&root,a.clone(),&[b.clone(),a.clone()],CheckedFrameBinding::Free(FreeId(1))),
            frame(ExprId(8),CheckedFrameRole::InferLambda,&parent,a.clone(),&[a.clone()],CheckedFrameBinding::Free(FreeId(0))),
            frame(ExprId(8),CheckedFrameRole::InferLambda,&root,changed_levels.clone(),&[changed_levels],CheckedFrameBinding::Free(FreeId(0))),
            frame(ExprId(8),CheckedFrameRole::InferLambda,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Free(FreeId(1))),
        ] {assert_ne!(first.id(),other.id());}
        for role in [CheckedFrameRole::InferPi,CheckedFrameRole::LiteralBeta,CheckedFrameRole::Let,CheckedFrameRole::ExactPiSubstitution] {
            assert_ne!(first.id(),frame(ExprId(8),role,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Free(FreeId(0))).id());
        }
        for source in [ExprId(4),ExprId(999)] {
            assert_ne!(frame(source,CheckedFrameRole::ExpectedLambda,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Free(FreeId(0))).id(),frame(source,CheckedFrameRole::InferLambda,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Free(FreeId(0))).id());
        }
        let actual=checker.closure(ExprId(1),root.clone());
        assert_ne!(frame(ExprId(8),CheckedFrameRole::ExpectedLambda,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Actual(actual.clone())).id(),frame(ExprId(8),CheckedFrameRole::InferLambda,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Actual(actual.clone())).id());
        assert_ne!(first.id(),checker.checked_source_frame_with_codomain(ExprId(8),CheckedFrameRole::InferLambda,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Free(FreeId(0)),Some(actual)).id());
    }

    #[test]
    fn lambda_shared_scope_obeys_quarantine_fixed_pi_and_configuration() {
        let (e,l,env)=fixture();let mut checker=TypeChecker::new(&e,&l,&env);checker.strict_origin_probe=true;
        let root=EnvFrame::empty();let a=TypeValue::Term(checker.closure(ExprId(1),root.clone()));let b=TypeValue::Term(checker.closure(ExprId(2),root.clone()));
        let first=checker.checked_source_frame(ExprId(8),CheckedFrameRole::ExpectedLambda,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Free(FreeId(0)));
        checker.retain_checked_binding(&first,b.clone(),&[a.clone()]);
        assert!(checker.checked_binding_lineage.borrow().get(&first.id()).unwrap().is_none());
        let fresh=checker.checked_source_frame(ExprId(8),CheckedFrameRole::InferLambda,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Free(FreeId(0)));
        assert_ne!(first.id(),fresh.id());
        checker.strict_origin_probe=false;
        let ordinary=checker.checked_source_frame(ExprId(8),CheckedFrameRole::ExpectedLambda,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Free(FreeId(0)));
        assert_ne!(ordinary.id(),fresh.id());
        let pi=TypeValue::Pi{domain:Box::new(a.clone()),body:Box::new(b),binder:FreeId(0),binder_owner:None};
        for (domain,ctx) in [(pi.clone(),vec![pi.clone()]),(a.clone(),vec![pi,a])] {
            let one=checker.checked_source_frame(ExprId(8),CheckedFrameRole::ExpectedLambda,&root,domain.clone(),&ctx,CheckedFrameBinding::Free(FreeId(0)));
            let two=checker.checked_source_frame(ExprId(8),CheckedFrameRole::InferLambda,&root,domain,&ctx,CheckedFrameBinding::Free(FreeId(0)));
            assert_ne!(one.id(),two.id(),"fixed Pi scopes remain fresh and capture protected");
        }
    }

    #[test]
    fn lambda_shared_scope_saturation_preserves_exact_old_proofs() {
        let (e,l,env)=fixture();let checker=TypeChecker::new(&e,&l,&env);let root=EnvFrame::empty();let a=TypeValue::Term(checker.closure(ExprId(1),root.clone()));
        let first=checker.checked_source_frame(ExprId(8),CheckedFrameRole::ExpectedLambda,&root,a.clone(),&[a.clone()],CheckedFrameBinding::Free(FreeId(0)));
        for _ in 1..8192 {let parent=root.extend_free(FreeId(9));let domain=TypeValue::Term(checker.closure(ExprId(1),parent.clone()));checker.checked_source_frame(ExprId(8),CheckedFrameRole::InferLambda,&parent,domain.clone(),&[domain],CheckedFrameBinding::Free(FreeId(0)));}
        assert_eq!(checker.checked_frames.borrow().len(),8192);
        assert_eq!(first.id(),checker.checked_source_frame(ExprId(8),CheckedFrameRole::InferLambda,&root,a.clone(),&[a],CheckedFrameBinding::Free(FreeId(0))).id());
        let parent=root.extend_free(FreeId(9));let domain=TypeValue::Term(checker.closure(ExprId(1),parent.clone()));
        let one=checker.checked_source_frame(ExprId(8),CheckedFrameRole::ExpectedLambda,&parent,domain.clone(),&[domain.clone()],CheckedFrameBinding::Free(FreeId(0)));
        let two=checker.checked_source_frame(ExprId(8),CheckedFrameRole::InferLambda,&parent,domain.clone(),&[domain],CheckedFrameBinding::Free(FreeId(0)));
        assert_ne!(one.id(),two.id());assert_eq!(checker.checked_frames.borrow().len(),8192);
    }

}

#[cfg(test)]
mod proof_transport_tests {
 use super::*;
 #[test]
 fn original_formed_proof_pi_certifies_actual_opening_and_separate_one_slot_transport(){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();
  for(id,node)in[(0,Expr::Sort(LevelId(0))),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::Const{name:NameId(2),levels:vec![]}),(3,Expr::BVar(0)),(4,Expr::Pi{domain:ExprId(2),body:ExprId(2)})]{e.insert(ExprId(id),node).unwrap();}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::definition(vec![],ExprId(0),ExprId(1),true)).unwrap();
  let mut checker=TypeChecker::new(&e,&l,&env);checker.strict_origin_probe=true;let root=EnvFrame::empty();let p=TypeValue::Term(checker.closure(ExprId(1),root.clone()));let q=TypeValue::Term(checker.closure(ExprId(2),root.clone()));
  assert!(checker.is_type(ExprId(1),128).is_proven());let old=root.extend_free(FreeId(0));checker.retain_checked_binding(&old,p.clone(),&[p.clone()]);let opened=Closure::new(ExprId(2),root.extend_free(FreeId(0)));let local=Closure::new(ExprId(3),opened.env.clone());let right=Closure::new(ExprId(3),old.clone());
  assert!(checker.infer_exact_closure_in_context(&local,&[q.clone()],&mut 128,0).is_none());
  assert!(checker.certify_conversion_pi_opening(&checker.closure(ExprId(4),root.clone()),match &q {TypeValue::Term(c)=>c,_=>unreachable!()},&opened,&[],&mut 512));
  assert!(checker.infer_exact_closure_in_context(&right,&[q.clone()],&mut 128,0).is_none());
  assert!(checker.transport_conversion_proof_binder(&TypeValue::Term(opened.clone()),&TypeValue::Term(right.clone()),&p,&q,&[],&mut 2048));
  assert_eq!(checker.infer_exact_closure_in_context(&right,&[q.clone()],&mut 128,0),Some(p.clone()));assert_eq!(checker.infer_exact_closure_in_context(&local,&[q.clone()],&mut 128,0),Some(q.clone()));
  assert_eq!(checker.checked_binding_lineage.borrow()[&old.id()].as_ref().unwrap().protected_prefix.as_slice(),&[p.clone()]);
  assert_eq!(checker.checked_binding_lineage.borrow()[&opened.env.id()].as_ref().unwrap().protected_prefix.as_slice(),&[q.clone()]);
  let no_budget=Closure::new(ExprId(2),root.extend_free(FreeId(0)));assert!(!checker.certify_conversion_pi_opening(&checker.closure(ExprId(4),root.clone()),match &q{TypeValue::Term(c)=>c,_=>unreachable!()},&no_budget,&[],&mut 0));assert!(checker.checked_binding_lineage.borrow().get(&no_budget.env.id()).is_none());
  let mismatched=Closure::new(ExprId(3),root.extend_free(FreeId(0)));assert!(!checker.certify_conversion_pi_opening(&checker.closure(ExprId(4),root.clone()),match &q{TypeValue::Term(c)=>c,_=>unreachable!()},&mismatched,&[],&mut 512));
  assert!(!checker.certify_conversion_pi_opening(&checker.closure(ExprId(1),root.clone()),match &q{TypeValue::Term(c)=>c,_=>unreachable!()},&no_budget,&[],&mut 512),"formed proposition is not sourcePi authority");
  checker.retain_checked_binding(&opened.env,p.clone(),&[q.clone()]);assert!(checker.checked_binding_lineage.borrow()[&opened.env.id()].is_none());
  assert!(checker.infer_exact_closure_in_context(&right,&[q.clone()],&mut 128,0).is_none(),"poisoned opening revokes transport despite unchanged old witness");
  assert!(checker.infer_exact_closure_in_context(&local,&[q],&mut 128,0).is_none());

 }
}

#[cfg(test)]
mod proof_domain_universe_tests {
 use super::*;
 #[test]
 fn proof_domain_transport_does_not_require_proof_valued_codomain() {
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(id,node)in[(0,Expr::Sort(LevelId(0))),(1,Expr::Sort(LevelId(1))),(2,Expr::Const{name:NameId(1),levels:vec![]}),(3,Expr::Const{name:NameId(2),levels:vec![]}),(4,Expr::Pi{domain:ExprId(5),body:ExprId(3)}),(5,Expr::Const{name:NameId(3),levels:vec![]}),(6,Expr::Pi{domain:ExprId(3),body:ExprId(2)}),(7,Expr::BVar(0)),(8,Expr::BVar(2)),(9,Expr::Pi{domain:ExprId(5),body:ExprId(8)}),(10,Expr::Const{name:NameId(4),levels:vec![]}),(11,Expr::Const{name:NameId(5),levels:vec![]})]{e.insert(ExprId(id),node).unwrap();}
  use crate::environment::ConstantDecl;
  let env=Environment::empty().extend(NameId(1),ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),ConstantDecl::axiom(vec![],ExprId(1))).unwrap().extend(NameId(3),ConstantDecl::definition(vec![],ExprId(0),ExprId(2),true)).unwrap().extend(NameId(4),ConstantDecl::axiom(vec![],ExprId(3))).unwrap().extend(NameId(5),ConstantDecl::axiom(vec![],ExprId(3))).unwrap();
  let mut checker=TypeChecker::new(&e,&l,&env);checker.strict_origin_probe=true;let root=EnvFrame::empty();let p=TypeValue::Term(checker.closure(ExprId(2),root.clone()));let q=TypeValue::Term(checker.closure(ExprId(5),root.clone()));let opened=Closure::new(ExprId(3),root.extend_free(FreeId(0)));
  assert!(checker.certify_conversion_pi_opening(&checker.closure(ExprId(4),root.clone()),match &q{TypeValue::Term(c)=>c,_=>unreachable!()},&opened,&[],&mut 4096),"formed Pi proof domain permits typing transport even when codomain is data");
  let old=root.extend_free(FreeId(0));checker.retain_checked_binding(&old,p.clone(),&[p.clone()]);let old_proof=Closure::new(ExprId(7),old.clone());
  assert!(checker.transport_conversion_proof_binder(&TypeValue::Term(opened.clone()),&TypeValue::Term(old_proof.clone()),&p,&q,&[],&mut 4096));
  assert_eq!(checker.infer_exact_closure_in_context(&old_proof,&[q.clone()],&mut 128,0),Some(p));
  let data_open=Closure::new(ExprId(2),root.extend_free(FreeId(0)));let nat=checker.closure(ExprId(3),root.clone());
  assert!(!checker.certify_conversion_pi_opening(&checker.closure(ExprId(6),root.clone()),&nat,&data_open,&[],&mut 4096),"whole Pi being Prop never makes its Nat domain proof-irrelevant");
  assert!(checker.checked_binding_lineage.borrow().get(&data_open.env.id()).is_none());
  let bad=Closure::new(ExprId(8),root.extend_free(FreeId(0)));
  assert!(!checker.certify_conversion_pi_opening(&checker.closure(ExprId(9),root.clone()),match &q{TypeValue::Term(c)=>c,_=>unreachable!()},&bad,&[],&mut 4096),"unformed codomain cannot provide a Pi introduction");
  let a=checker.closure(ExprId(10),root.clone());let b=checker.closure(ExprId(11),root);
  assert!(!checker.checked_transport_proof_pair(&a,&b,&[q],&mut 4096),"data subjects never become proof-irrelevant from a proof binder");
 }
}


#[cfg(test)]
mod owned_neutral_typing_tests {
 use super::*;
 #[test]
 fn owned_neutral_alias_reuses_only_original_unchanged_scope_and_wrapper() {
  let mut expressions=IdTable::default();expressions.insert(ExprId(0),Expr::BVar(0)).unwrap();
  let levels=IdTable::default();let environment=Environment::empty();
  let mut checker=TypeChecker::new(&expressions,&levels,&environment);checker.strict_origin_probe=true;
  let domain=TypeValue::Sort(LevelTerm::Zero);let gamma=vec![domain.clone()];
  let owner=EnvFrame::empty().extend_free(FreeId(0));checker.retain_checked_binding(&owner,domain.clone(),&gamma);
  let wrapper=EnvFrame::empty().extend_neutral(Neutral{head:NeutralHead::Free(FreeId(0),Some(owner.clone())),spine:vec![]});
  let source=checker.closure(ExprId(0),wrapper.clone());
  assert_eq!(checker.infer_exact_closure_in_context(&source,&gamma,&mut 64,0),Some(domain.clone()));
  let different=TypeValue::Sort(LevelTerm::Succ(Box::new(LevelTerm::Zero)));
  assert!(checker.infer_exact_closure_in_context(&source,&[different.clone()],&mut 64,0).is_none(),"same number in a different Gamma has no original typing authority");
  checker.retain_checked_binding(&wrapper,domain.clone(),&gamma);
  checker.retain_checked_binding(&wrapper,different.clone(),&gamma);
  assert!(checker.infer_exact_closure_in_context(&source,&gamma,&mut 64,0).is_none(),"current wrapper quarantine revokes reuse");
  let alias=EnvFrame::empty().extend_neutral(Neutral{head:NeutralHead::Free(FreeId(0),Some(owner.clone())),spine:vec![]});
  checker.retain_checked_binding(&owner,different,&gamma);
  assert!(checker.infer_exact_closure_in_context(&checker.closure(ExprId(0),alias),&gamma,&mut 64,0).is_none(),"original owner quarantine revokes every alias");
 }
}

#[cfg(test)]
mod atomic_joint_opening_tests {
 use super::*;
 #[test]
 fn atomic_joint_intro_preserves_sources_and_requires_complete_premises(){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();
  for(id,node)in[(0,Expr::Sort(LevelId(0))),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::BVar(0)),(3,Expr::Const{name:NameId(2),levels:vec![]}),(4,Expr::Const{name:NameId(1),levels:vec![LevelId(0)]}),(5,Expr::BVar(1)),(6,Expr::Const{name:NameId(3),levels:vec![]})]{e.insert(ExprId(id),node).unwrap();}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![],ExprId(1))).unwrap().extend(NameId(3),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap();
  let mut checker=TypeChecker::new(&e,&l,&env);checker.strict_origin_probe=true;
  let lp=EnvFrame::empty();let rp=EnvFrame::empty().extend_free(FreeId(9));let left=checker.closure(ExprId(2),lp.clone());let right=Closure::with_levels(ExprId(2),rp.clone(),LevelSubstitution::new(vec![(NameId(77),LevelTerm::Succ(Box::new(LevelTerm::Zero)))]));let domain=checker.closure(ExprId(1),lp.clone());
  assert!(checker.checked_atomic_joint_opening(&domain,&domain,&left,&right,&[],FreeId(0),&mut 128).is_none(),"missing completed freshness must decline");
  assert!(crate::convert::source_opening_avoids_capture(&checker,&left,FreeId(0),&mut 64));assert!(crate::convert::source_opening_avoids_capture(&checker,&right,FreeId(0),&mut 64));
  assert!(checker.checked_atomic_joint_opening(&domain,&domain,&left,&right,&[],FreeId(0),&mut 0).is_none());
  for expr in [3,4,6]{let invalid=checker.closure(ExprId(expr),lp.clone());assert!(checker.checked_atomic_joint_opening(&domain,&invalid,&left,&right,&[],FreeId(0),&mut 128).is_none());}
  let (opened_l,opened_r)=checker.checked_atomic_joint_opening(&domain,&domain,&left,&right,&[],FreeId(0),&mut 128).unwrap();
  assert_eq!(opened_l.env.parent_id(),Some(lp.id()));assert_eq!(opened_r.env.parent_id(),Some(rp.id()));assert_eq!(opened_l.levels,left.levels);assert_eq!(opened_r.levels,right.levels);
  assert!(matches!(opened_r.env.lookup_binding_ref(0),Some(EnvBinding::Neutral(Neutral{head:NeutralHead::Free(FreeId(0),Some(owner)),spine})) if owner.id()==opened_l.env.id() && spine.is_empty()));
  let gamma=vec![TypeValue::Term(domain.clone())];assert_eq!(checker.infer_exact_closure_in_context(&opened_r,&gamma,&mut 64,0),Some(gamma[0].clone()));
  let saved_wrapper=checker.checked_binding_lineage.borrow()[&opened_r.env.id()].clone();
  checker.checked_binding_lineage.borrow_mut().insert(opened_r.env.id(),None);assert!(checker.infer_exact_closure_in_context(&opened_r,&gamma,&mut 64,0).is_none());
  checker.checked_binding_lineage.borrow_mut().insert(opened_r.env.id(),saved_wrapper);
  checker.checked_binding_lineage.borrow_mut().insert(opened_l.env.id(),None);assert!(checker.infer_exact_closure_in_context(&opened_r,&gamma,&mut 64,0).is_none());
  let collision=checker.closure(ExprId(5),lp.extend_free(FreeId(0)));assert!(!crate::convert::source_opening_avoids_capture(&checker,&collision,FreeId(0),&mut 64));assert!(checker.checked_atomic_joint_opening(&domain,&domain,&collision,&right,&[],FreeId(0),&mut 128).is_none());
 }
}

#[cfg(test)]
mod sort_joint_domain_tests {
 use super::*;
 #[test]
 fn sorts_use_each_original_universe_and_one_paid_work_owner(){
  let mut e=IdTable::default();let mut l=IdTable::default();
  l.insert(LevelId(0),Level::Param(NameId(1))).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();l.insert(LevelId(2),Level::Succ(LevelId(2))).unwrap();
  for(id,node)in[(0,Expr::Sort(LevelId(1))),(1,Expr::Sort(LevelId(99))),(2,Expr::Sort(LevelId(2))),(3,Expr::BVar(0))]{e.insert(ExprId(id),node).unwrap();}
  let env=Environment::empty();let mut checker=TypeChecker::new(&e,&l,&env);checker.strict_origin_probe=true;
  let lp=EnvFrame::empty();let rp=EnvFrame::empty().extend_free(FreeId(9));
  let theta=LevelSubstitution::new(vec![(NameId(1),LevelTerm::Param("u".into()))]);
  let extra=LevelSubstitution::new(vec![(NameId(1),LevelTerm::Param("u".into())),(NameId(7),LevelTerm::Zero)]);
  let left=Closure::with_levels(ExprId(0),lp.clone(),theta.clone());let right=Closure::with_levels(ExprId(0),rp.clone(),extra.clone());
  assert!(checker.checked_closed_atomic_domain_pair(&left,&right,&mut 32));
  let changed=Closure::with_levels(ExprId(0),rp.clone(),LevelSubstitution::new(vec![(NameId(1),LevelTerm::Zero)]));assert!(!checker.checked_closed_atomic_domain_pair(&left,&changed,&mut 64));
  let dangling=Closure::new(ExprId(0),rp.clone());assert!(!checker.checked_closed_atomic_domain_pair(&left,&dangling,&mut 64));
  for expr in [1,2]{let bad=Closure::with_levels(ExprId(expr),rp.clone(),extra.clone());assert!(!checker.checked_closed_atomic_domain_pair(&left,&bad,&mut 64));}
  let mut short=3;assert!(!checker.checked_closed_atomic_domain_pair(&left,&right,&mut short));assert_eq!(short,0);
  let lb=Closure::with_levels(ExprId(3),lp.clone(),theta);let rb=Closure::with_levels(ExprId(3),rp.clone(),extra);
  assert!(crate::convert::source_opening_avoids_capture(&checker,&lb,FreeId(0),&mut 32));assert!(crate::convert::source_opening_avoids_capture(&checker,&rb,FreeId(0),&mut 32));
  let (ol,or)=checker.checked_atomic_joint_opening(&left,&right,&lb,&rb,&[],FreeId(0),&mut 128).unwrap();
  assert_eq!(ol.levels,lb.levels);assert_eq!(or.levels,rb.levels);assert_eq!(ol.env.parent_id(),Some(lp.id()));assert_eq!(or.env.parent_id(),Some(rp.id()));
  assert!(matches!(or.env.lookup_binding_ref(0),Some(EnvBinding::Neutral(Neutral{head:NeutralHead::Free(FreeId(0),Some(owner)),..})) if owner.id()==ol.env.id()));
 }
}

#[cfg(test)]
mod domain_source_alias_tests {
 use super::*;
 #[test]
 fn domain_aliases_follow_only_actual_closures_and_their_own_levels(){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Param(NameId(7))).unwrap();l.insert(LevelId(2),Level::Succ(LevelId(2))).unwrap();
  for(id,node)in[(0,Expr::Sort(LevelId(0))),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::Const{name:NameId(2),levels:vec![]}),(3,Expr::BVar(0)),(4,Expr::BVar(7)),(5,Expr::Sort(LevelId(1))),(6,Expr::Sort(LevelId(2))),(7,Expr::Pi{domain:ExprId(7),body:ExprId(7)})]{e.insert(ExprId(id),node).unwrap();}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap();let checker=TypeChecker::new(&e,&l,&env);let root=EnvFrame::empty();let nat=checker.closure(ExprId(1),root.clone());let int=checker.closure(ExprId(2),root.clone());
  let alias=Closure::new(ExprId(3),root.extend(nat.clone()));assert!(checker.checked_closed_atomic_domain_pair(&nat,&alias,&mut 64));
  let changed=Closure::new(ExprId(3),root.extend(int));assert!(!checker.checked_closed_atomic_domain_pair(&nat,&changed,&mut 64));
  let free=Closure::new(ExprId(3),root.extend_free(FreeId(0)));let missing=Closure::new(ExprId(4),root.clone());let neutral=Closure::new(ExprId(3),root.extend_neutral(Neutral{head:NeutralHead::Free(FreeId(0),None),spine:vec![]}));
  for bad in [&free,&missing,&neutral]{assert!(!checker.checked_closed_atomic_domain_pair(&nat,bad,&mut 64));}
  let dangling_child=Closure::new(ExprId(3),root.extend(missing));assert!(!checker.checked_closed_atomic_domain_pair(&nat,&dangling_child,&mut 64));
  let malformed=Closure::new(ExprId(3),root.extend(Closure::new(ExprId(7),root.clone())));assert!(!checker.checked_closed_atomic_domain_pair(&nat,&malformed,&mut 64));
  let theta=LevelSubstitution::new(vec![(NameId(7),LevelTerm::Param("u".into()))]);let sort=Closure::with_levels(ExprId(5),root.clone(),theta);
  let sort_alias=Closure::with_levels(ExprId(3),root.extend(sort.clone()),LevelSubstitution::new(vec![(NameId(7),LevelTerm::Zero)]));assert!(checker.checked_closed_atomic_domain_pair(&sort,&sort_alias,&mut 64),"stored closure own levels supersede BVar occurrence levels");
  let cyclic=Closure::new(ExprId(3),root.extend(Closure::new(ExprId(6),root.clone())));assert!(!checker.checked_closed_atomic_domain_pair(&sort,&cyclic,&mut 64));
  let mut short=2;assert!(!checker.checked_closed_atomic_domain_pair(&nat,&alias,&mut short));assert_eq!(short,0);assert!(!checker.checked_closed_atomic_domain_pair(&nat,&alias,&mut 0));
 }
}

#[cfg(test)]
mod paired_hint_completed_tests {
 use super::*;
 fn fixture()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment) {
  let mut expressions=IdTable::default();let mut levels=IdTable::default();levels.insert(LevelId(0),Level::Zero).unwrap();levels.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for (id,node) in [(0,Expr::Sort(LevelId(1))),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::BVar(0)),(3,Expr::BVar(1)),(4,Expr::Lam{domain:ExprId(1),body:ExprId(2)}),(5,Expr::Lam{domain:ExprId(1),body:ExprId(3)}),(6,Expr::Pi{domain:ExprId(1),body:ExprId(1)}),(7,Expr::Const{name:NameId(2),levels:vec![]})]{expressions.insert(ExprId(id),node).unwrap();}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap();(expressions,levels,env)
 }
 #[test]
 fn completed_paired_hint_is_lookup_only_for_the_exact_source_pair() {
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);assert!(c.paired_lambda_hint(ExprId(4),ExprId(5),&mut 128));assert!(c.paired_lambda_hint(ExprId(4),ExprId(5),&mut 1));assert!(!c.paired_lambda_hint(ExprId(4),ExprId(5),&mut 0));assert!(!c.paired_lambda_hint(ExprId(1),ExprId(7),&mut 128));let mut hot=8;assert!(!c.paired_lambda_hint(ExprId(1),ExprId(7),&mut hot));assert_eq!(hot,7);
 }
 #[test]
 fn coarse_bound_variable_hint_never_proves_capture_or_typing_transport() {
  let(e,l,env)=fixture();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;
  let expected=c.closure(ExprId(6),EnvFrame::empty());assert!(c.is_type(ExprId(6),256).is_proven());assert!(c.check_formed(ExprId(4),&TypeValue::Term(expected.clone()),256).is_proven());let previous=OwnedLambdaGoal{source:c.closure(ExprId(4),EnvFrame::empty()),expected:expected.clone(),dependencies:vec![]};
  let nat=TypeValue::Term(c.closure(ExprId(1),EnvFrame::empty()));let frame=EnvFrame::empty().extend_free(FreeId(0));c.retain_checked_binding(&frame,nat.clone(),&[nat.clone()]);let changed=c.closure(ExprId(5),frame);assert!(c.paired_lambda_hint(ExprId(4),ExprId(5),&mut 128));assert!(!c.exact_source_capture_identity(&previous.source,&changed,&mut 256));let current=c.owned_goal_dependencies(&changed,&expected,&[nat],&mut 256).unwrap();assert!(!c.joint_owned_goal_transport(&previous,&changed,&expected,&current,&mut 256));
 }
 #[test]
 fn unfinished_zero_and_saturated_hint_work_never_publish_authority() {
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);assert!(!c.paired_lambda_hint(ExprId(4),ExprId(5),&mut 0));assert!(c.paired_lambda_hint_facts.borrow().is_empty());assert!(!c.paired_lambda_hint(ExprId(4),ExprId(5),&mut 2));assert!(!c.paired_lambda_hint_facts.borrow().contains_key(&(ExprId(4),ExprId(5))));assert!(c.paired_lambda_hint(ExprId(4),ExprId(5),&mut 128));let original=*(c.paired_lambda_hint_facts.borrow().get(&(ExprId(4),ExprId(5))).unwrap());{let mut facts=c.paired_lambda_hint_facts.borrow_mut();for i in 0..4096u64{if facts.len()>=4096{break;}facts.insert((ExprId(10000+i),ExprId(20000+i)),false);}}assert_eq!(c.paired_lambda_hint_facts.borrow().len(),4096);assert!(c.paired_lambda_hint(ExprId(4),ExprId(5),&mut 1));assert_eq!(c.paired_lambda_hint_facts.borrow().get(&(ExprId(4),ExprId(5))),Some(&original));assert!(c.paired_lambda_hint(ExprId(5),ExprId(4),&mut 128));assert!(!c.paired_lambda_hint_facts.borrow().contains_key(&(ExprId(5),ExprId(4))));
 }
 #[test]
 fn complete_hint_facts_are_confined_to_their_actual_expression_table() {
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);assert!(c.paired_lambda_hint(ExprId(4),ExprId(5),&mut 128));let mut other=IdTable::default();for (id,node) in e.iter_raw(){other.insert(ExprId(id),node.clone()).unwrap();}other.insert(ExprId(8),Expr::Sort(LevelId(0))).unwrap();let second=TypeChecker::new(&other,&l,&env);assert!(second.paired_lambda_hint_facts.borrow().is_empty());assert!(!second.paired_lambda_hint(ExprId(4),ExprId(5),&mut 1));
 }
 #[test]
 fn completed_child_pair_reuses_under_a_distinct_root_only_after_postorder() {
  let(mut e,l,env)=fixture();e.insert(ExprId(8),Expr::App{fun:ExprId(4),arg:ExprId(1)}).unwrap();e.insert(ExprId(9),Expr::App{fun:ExprId(5),arg:ExprId(1)}).unwrap();e.insert(ExprId(10),Expr::Lam{domain:ExprId(1),body:ExprId(8)}).unwrap();e.insert(ExprId(11),Expr::Lam{domain:ExprId(1),body:ExprId(9)}).unwrap();let c=TypeChecker::new(&e,&l,&env);assert!(c.paired_lambda_hint(ExprId(10),ExprId(11),&mut 128));assert!(c.paired_lambda_hint(ExprId(8),ExprId(9),&mut 1));assert!(c.paired_lambda_hint(ExprId(4),ExprId(5),&mut 1));
 }
 #[test]
 fn incomplete_parent_never_publishes_and_child_mismatch_propagates() {
  let(mut e,l,env)=fixture();e.insert(ExprId(8),Expr::App{fun:ExprId(1),arg:ExprId(4)}).unwrap();e.insert(ExprId(9),Expr::App{fun:ExprId(7),arg:ExprId(5)}).unwrap();let c=TypeChecker::new(&e,&l,&env);assert!(!c.paired_lambda_hint(ExprId(8),ExprId(9),&mut 2));assert!(!c.paired_lambda_hint_facts.borrow().contains_key(&(ExprId(8),ExprId(9))));assert!(!c.paired_lambda_hint(ExprId(8),ExprId(9),&mut 128));assert_eq!(c.paired_lambda_hint_facts.borrow().get(&(ExprId(1),ExprId(7))),Some(&false));assert!(!c.paired_lambda_hint(ExprId(8),ExprId(9),&mut 1));
 }
 #[test]
 fn active_cycles_are_not_completed_syntax_facts_and_identity_uses_no_slot() {
  let(mut e,l,env)=fixture();e.insert(ExprId(8),Expr::App{fun:ExprId(8),arg:ExprId(1)}).unwrap();e.insert(ExprId(9),Expr::App{fun:ExprId(9),arg:ExprId(1)}).unwrap();let c=TypeChecker::new(&e,&l,&env);assert!(!c.paired_lambda_hint(ExprId(8),ExprId(9),&mut 128));assert!(!c.paired_lambda_hint_facts.borrow().contains_key(&(ExprId(8),ExprId(9))));assert!(c.paired_lambda_hint(ExprId(1),ExprId(1),&mut 2));assert!(!c.paired_lambda_hint_facts.borrow().contains_key(&(ExprId(1),ExprId(1))));
 }
}

#[cfg(test)]
mod active_fixed_atomic_recovery_tests {
 use super::*;
 fn fixture()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(id,node)in[(0,Expr::Sort(LevelId(0))),(1,Expr::Sort(LevelId(1))),(2,Expr::Const{name:NameId(1),levels:vec![]}),(3,Expr::BVar(0)),(4,Expr::BVar(99)),(5,Expr::Const{name:NameId(2),levels:vec![]}),(6,Expr::Pi{domain:ExprId(2),body:ExprId(2)}),(7,Expr::Lam{domain:ExprId(2),body:ExprId(3)})]{e.insert(ExprId(id),node).unwrap();}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(1))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![],ExprId(2))).unwrap();(e,l,env)
 }
 #[test]
 fn lambda_versus_neutral_is_not_a_rigid_inequality_when_source_eta_is_unavailable(){
  let(e,l,env)=fixture();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let owner=EnvFrame::empty().extend_free(FreeId(0));let ty=TypeValue::Term(c.closure(ExprId(6),EnvFrame::empty()));let gamma=vec![ty.clone()];c.retain_checked_binding(&owner,ty,&gamma);
  let left=TypeValue::Term(c.closure(ExprId(7),owner.clone()));let right=TypeValue::Term(c.closure(ExprId(3),owner));let result=crate::convert::convert_with_policy_in_context(&c,&left,&right,4096,crate::convert::DeltaPolicy::GuardedSemanticFallback,1,&gamma);assert!(result.is_unknown(),"failure to establish eta cannot certify inequality: {result:?}");
 }
 #[test]
 fn active_formation_can_use_the_actual_type_variable_sort_witness_without_reinference(){
  let(mut e,l,env)=fixture();e.insert(ExprId(8),Expr::BVar(1)).unwrap();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;
  let alpha=EnvFrame::empty().extend_free(FreeId(0));let sort=TypeValue::Term(c.closure(ExprId(1),EnvFrame::empty()));let gamma=vec![sort.clone()];c.retain_checked_binding(&alpha,sort,&gamma);
  let left_domain=c.closure(ExprId(3),alpha.clone());let parent=alpha.extend(c.closure(ExprId(5),EnvFrame::empty()));let right_domain=c.closure(ExprId(8),parent.clone());
  let a=alpha.extend_free(FreeId(1));let b=parent.extend_free(FreeId(1));let mut ga=gamma.clone();ga.push(TypeValue::Term(left_domain.clone()));c.retain_checked_binding(&a,ga[1].clone(),&ga);let mut gb=gamma.clone();gb.push(TypeValue::Term(right_domain.clone()));c.retain_checked_binding(&b,gb[1].clone(),&gb);
  let mk=|domain:Closure,owner:EnvFrame|TypeValue::Pi{domain:Box::new(TypeValue::Term(domain)),body:Box::new(TypeValue::Term(c.closure(ExprId(1),owner.clone()))),binder:FreeId(1),binder_owner:Some(owner)};
  let left=mk(left_domain,a);let right=mk(right_domain,b);let _outer=GeneralDomainFormationOwner::enter();let result=crate::convert::convert_with_policy_in_context(&c,&left,&right,4096,crate::convert::DeltaPolicy::GuardedSemanticFallback,1,&gamma);assert!(result.is_proven(),"same original alpha:Sort has a completed source witness: {result:?}");assert!(GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.get()));
 }
 #[test]
 fn bound_sort_classification_rejects_proof_data_wrong_gamma_missing_and_revoked_origins(){
  let(e,l,env)=fixture();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let alpha=EnvFrame::empty().extend_free(FreeId(0));let sort=TypeValue::Term(c.closure(ExprId(1),EnvFrame::empty()));let gamma=vec![sort.clone()];c.retain_checked_binding(&alpha,sort,&gamma);let source=c.closure(ExprId(3),alpha.clone());assert!(c.checked_bound_literal_sort(&source,&gamma,&mut 4096).is_some());
  assert!(c.checked_bound_literal_sort(&source,&[TypeValue::Term(c.closure(ExprId(0),EnvFrame::empty()))],&mut 4096).is_none());assert!(c.checked_bound_literal_sort(&source,&gamma,&mut 0).is_none());
  let missing=c.closure(ExprId(3),EnvFrame::empty().extend_free(FreeId(0)));assert!(c.checked_bound_literal_sort(&missing,&gamma,&mut 4096).is_none());
  let wrapper=EnvFrame::empty().extend(source.clone());let alias=c.closure(ExprId(3),wrapper.clone());assert!(c.checked_bound_literal_sort(&alias,&gamma,&mut 4096).is_some());c.checked_binding_lineage.borrow_mut().insert(wrapper.id(),None);assert!(c.checked_bound_literal_sort(&alias,&gamma,&mut 4096).is_none());
  c.checked_binding_lineage.borrow_mut().insert(alpha.id(),None);assert!(c.checked_bound_literal_sort(&source,&gamma,&mut 4096).is_none());
  let p=EnvFrame::empty().extend_free(FreeId(0));let prop=TypeValue::Term(c.closure(ExprId(0),EnvFrame::empty()));let gp=vec![prop.clone()];c.retain_checked_binding(&p,prop,&gp);let h=p.extend_free(FreeId(1));let h_type=TypeValue::Term(c.closure(ExprId(3),p));let mut gh=gp;gh.push(h_type.clone());c.retain_checked_binding(&h,h_type,&gh);assert!(c.checked_bound_literal_sort(&c.closure(ExprId(3),h),&gh,&mut 4096).is_none(),"h:p is a proof although p:Prop");
  let n=EnvFrame::empty().extend_free(FreeId(0));let data=TypeValue::Term(c.closure(ExprId(2),EnvFrame::empty()));let gn=vec![data.clone()];c.retain_checked_binding(&n,data,&gn);assert!(c.checked_bound_literal_sort(&c.closure(ExprId(3),n),&gn,&mut 4096).is_none());
 }
 #[test]
 fn bound_type_sort_uses_the_actual_recorded_types_own_universes(){
  let(mut e,mut l,env)=fixture();l.insert(LevelId(42),Level::Param(NameId(42))).unwrap();e.insert(ExprId(42),Expr::Sort(LevelId(42))).unwrap();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;
  let owner=EnvFrame::empty().extend_free(FreeId(0));let actual=TypeValue::Term(Closure::with_levels(ExprId(42),EnvFrame::empty(),LevelSubstitution::new(vec![(NameId(42),LevelTerm::Zero)])));let gamma=vec![actual.clone()];c.retain_checked_binding(&owner,actual,&gamma);
  let occurrence=Closure::with_levels(ExprId(3),owner,LevelSubstitution::new(vec![(NameId(42),LevelTerm::Succ(Box::new(LevelTerm::Zero)))]));assert_eq!(c.checked_bound_literal_sort(&occurrence,&gamma,&mut 4096),Some(LevelTerm::Zero));
 }
 #[test]
 fn active_literal_pi_forms_its_original_dependent_source_independently(){
  let(mut e,l,env)=fixture();e.insert(ExprId(50),Expr::BVar(1)).unwrap();e.insert(ExprId(51),Expr::Pi{domain:ExprId(3),body:ExprId(50)}).unwrap();
  let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;
  let alpha=EnvFrame::empty().extend_free(FreeId(0));let sort=TypeValue::Term(c.closure(ExprId(1),EnvFrame::empty()));let gamma=vec![sort.clone()];c.retain_checked_binding(&alpha,sort,&gamma);
  let d=c.closure(ExprId(51),alpha.clone());let a=alpha.extend_free(FreeId(1));let b=alpha.extend_free(FreeId(1));let mut extended=gamma.clone();extended.push(TypeValue::Term(d.clone()));c.retain_checked_binding(&a,extended[1].clone(),&extended);c.retain_checked_binding(&b,extended[1].clone(),&extended);
  let mk=|owner:EnvFrame|TypeValue::Pi{domain:Box::new(TypeValue::Term(d.clone())),body:Box::new(TypeValue::Term(c.closure(ExprId(1),owner.clone()))),binder:FreeId(1),binder_owner:Some(owner)};
  let _outer=GeneralDomainFormationOwner::enter();let result=crate::convert::convert_with_policy_in_context(&c,&mk(a),&mk(b),4096,crate::convert::DeltaPolicy::GuardedSemanticFallback,1,&gamma);
  assert!(result.is_proven(),"literal Pi requires actual source formation even during outer formation: {result:?}");assert!(GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.get()));
 }
 #[test]
 fn structural_pi_trial_checks_dependent_body_scope_quarantine_and_same_allowance(){
  let(mut e,l,env)=fixture();
  for(id,node)in[(60,Expr::BVar(1)),(61,Expr::Pi{domain:ExprId(3),body:ExprId(1)}),(62,Expr::App{fun:ExprId(60),arg:ExprId(3)}),(63,Expr::Pi{domain:ExprId(60),body:ExprId(62)}),(64,Expr::App{fun:ExprId(60),arg:ExprId(5)}),(65,Expr::Pi{domain:ExprId(60),body:ExprId(64)}),(66,Expr::Pi{domain:ExprId(60),body:ExprId(4)})]{e.insert(ExprId(id),node).unwrap();}
  let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let alpha=EnvFrame::empty().extend_free(FreeId(0));let sort=TypeValue::Term(c.closure(ExprId(1),EnvFrame::empty()));let mut gamma=vec![sort.clone()];c.retain_checked_binding(&alpha,sort,&gamma);
  let beta_type=TypeValue::Term(c.closure(ExprId(61),alpha.clone()));let beta=alpha.extend_free(FreeId(1));gamma.push(beta_type.clone());c.retain_checked_binding(&beta,beta_type,&gamma);
  let good=c.closure(ExprId(63),beta.clone());let _outer=GeneralDomainFormationOwner::enter();assert!(c.checked_active_source_sort(&good,&gamma,&mut 4096).is_some());assert!(GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.get()));
  assert!(c.checked_active_source_sort(&c.closure(ExprId(65),beta.clone()),&gamma,&mut 4096).is_none(),"beta applied to Nat data cannot form beta(x:alpha)");assert!(c.checked_active_source_sort(&c.closure(ExprId(66),beta.clone()),&gamma,&mut 4096).is_none());assert!(c.checked_active_source_sort(&good,&[],&mut 4096).is_none());assert!(c.checked_active_source_sort(&good,&gamma,&mut 0).is_none());
  {let _nested=StructuralPiFormationOwner::enter().unwrap();assert!(c.checked_active_source_sort(&good,&gamma,&mut 4096).is_none());}assert!(GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.get()));
  c.checked_binding_lineage.borrow_mut().insert(beta.id(),None);assert!(c.checked_active_source_sort(&good,&gamma,&mut 4096).is_none());
 }
 #[test]
 fn actual_bound_type_sort_avoids_optional_proof_reservation_but_proofs_remain_eligible(){
  let(e,l,env)=fixture();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let alpha=EnvFrame::empty().extend_free(FreeId(0));let sort=TypeValue::Term(c.closure(ExprId(1),EnvFrame::empty()));let gamma=vec![sort.clone()];c.retain_checked_binding(&alpha,sort,&gamma);let source=c.closure(ExprId(3),alpha.clone());let mut remaining=512;
  assert!(!c.checked_owned_proof_source_pair(&source,&source,&gamma,&mut remaining));assert!(remaining>=450,"actual alpha:Sort cannot be a proof subject; paid witness should avoid unrelated256proof reservation, remaining={remaining}");
  let p=EnvFrame::empty().extend_free(FreeId(0));let prop=TypeValue::Term(c.closure(ExprId(0),EnvFrame::empty()));let gp=vec![prop.clone()];c.retain_checked_binding(&p,prop,&gp);let h_type=TypeValue::Term(c.closure(ExprId(3),p.clone()));let h=p.extend_free(FreeId(1));let mut gh=gp;gh.push(h_type.clone());c.retain_checked_binding(&h,h_type,&gh);let hs=c.closure(ExprId(3),h.clone());assert!(c.checked_owned_proof_source_pair(&hs,&hs,&gh,&mut 4096),"h:p remains eligible although p:Prop");
  assert!(!c.checked_owned_proof_source_pair(&source,&source,&[],&mut 4096));c.checked_binding_lineage.borrow_mut().insert(alpha.id(),None);assert!(!c.checked_owned_proof_source_pair(&source,&source,&gamma,&mut 4096));c.checked_binding_lineage.borrow_mut().insert(h.id(),None);assert!(!c.checked_owned_proof_source_pair(&hs,&hs,&gh,&mut 4096));assert!(!c.checked_owned_proof_source_pair(&source,&source,&gamma,&mut 0));
 }
 #[test]
 fn shape_support_compiler_publishes_no_occurrence_or_typing_facts(){
  let(mut e,l,env)=fixture();e.insert(ExprId(86),Expr::BVar(1)).unwrap();e.insert(ExprId(87),Expr::Lam{domain:ExprId(2),body:ExprId(86)}).unwrap();e.insert(ExprId(88),Expr::Pi{domain:ExprId(2),body:ExprId(3)}).unwrap();e.insert(ExprId(89),Expr::App{fun:ExprId(89),arg:ExprId(3)}).unwrap();let c=TypeChecker::new(&e,&l,&env);
  let a=c.complete_lambda_shape_only(ExprId(7),&mut 1024).unwrap();let b=c.complete_lambda_shape_only(ExprId(87),&mut 1024).unwrap();assert_eq!(a,b);assert!(c.source_syntax_patterns.borrow().is_empty(),"pure shape doesnotpublish occurrence maps");assert!(c.source_support.borrow().contains_key(&ExprId(7)),"complete shape traversal nowpublishes exactsupport");assert!(c.owned_lambda_goals.borrow().is_empty());assert_ne!(a,c.complete_lambda_shape_only(ExprId(88),&mut 1024).unwrap());assert!(c.complete_lambda_shape_only(ExprId(89),&mut 1024).is_none());assert!(!c.lambda_shape_ids.borrow().contains_key(&ExprId(89)));assert!(c.complete_lambda_shape_only(ExprId(7),&mut 0).is_none());assert_eq!(c.lambda_candidate_hint(ExprId(7),&mut 1024),Some(a));assert!(c.source_syntax_patterns.borrow().contains_key(&ExprId(7)));
  assert!(!c.check(ExprId(87),&TypeValue::Term(c.closure(ExprId(6),EnvFrame::empty())),4096).is_proven());
 }
 fn pi(c:&TypeChecker<'_>,owner:&EnvFrame,domain:u64,body:u64)->TypeValue{TypeValue::Pi{domain:Box::new(TypeValue::Term(c.closure(ExprId(domain),EnvFrame::empty()))),body:Box::new(TypeValue::Term(c.closure(ExprId(body),owner.clone()))),binder:FreeId(0),binder_owner:Some(owner.clone())}}
 #[test]
 fn completed_atomic_domains_can_open_fixed_bodies_inside_outer_formation_without_clearing_guard(){
  let(e,l,env)=fixture();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let a=EnvFrame::empty().extend_free(FreeId(0));let b=EnvFrame::empty().extend_free(FreeId(0));let gamma=vec![TypeValue::Term(c.closure(ExprId(2),EnvFrame::empty()))];c.retain_checked_binding(&a,gamma[0].clone(),&gamma);c.retain_checked_binding(&b,gamma[0].clone(),&gamma);
  let _outer=GeneralDomainFormationOwner::enter();let result=crate::convert::convert(&c,&pi(&c,&a,2,1),&pi(&c,&b,2,1),4096);assert!(result.is_proven(),"independently formed closed atomic domain has no recursive premise: {result:?}");assert!(GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.get()),"inner atomic rule must preserve the active outer owner");
  c.checked_binding_lineage.borrow_mut().insert(a.id(),None);assert!(!crate::convert::convert(&c,&pi(&c,&a,2,1),&pi(&c,&b,2,1),4096).is_proven());
 }
 #[test]
 fn active_atomic_rule_never_forms_data_or_dangling_domains_and_never_borrows_quota(){
  let(e,l,env)=fixture();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let a=EnvFrame::empty().extend_free(FreeId(0));let b=EnvFrame::empty().extend_free(FreeId(0));let _outer=GeneralDomainFormationOwner::enter();
  for domain in [4,5]{assert!(!crate::convert::convert(&c,&pi(&c,&a,domain,1),&pi(&c,&b,domain,1),4096).is_proven());}
  assert!(crate::convert::convert(&c,&pi(&c,&a,2,1),&pi(&c,&b,2,1),0).is_unknown());
  assert!(!crate::convert::convert(&c,&pi(&c,&a,2,4),&pi(&c,&b,2,4),4096).is_proven(),"unbound codomain cannot acquire the atomic binder witness");
 }
}
#[cfg(test)]
mod proof_pi_classification_review_tests {
 use super::*;
 fn setup()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(id,node)in [(0,Expr::Sort(LevelId(0))),(1,Expr::Sort(LevelId(1))),(2,Expr::Const{name:NameId(1),levels:vec![]}),(3,Expr::Const{name:NameId(2),levels:vec![]}),(4,Expr::Pi{domain:ExprId(2),body:ExprId(2)}),(5,Expr::BVar(0)),(6,Expr::Lam{domain:ExprId(2),body:ExprId(5)}),(7,Expr::Const{name:NameId(3),levels:vec![]}),(8,Expr::Const{name:NameId(4),levels:vec![]}),(9,Expr::Pi{domain:ExprId(4),body:ExprId(2)}),(10,Expr::App{fun:ExprId(8),arg:ExprId(6)}),(11,Expr::App{fun:ExprId(8),arg:ExprId(5)}),(12,Expr::Lam{domain:ExprId(3),body:ExprId(5)}),(13,Expr::Const{name:NameId(5),levels:vec![]}),(14,Expr::Lam{domain:ExprId(13),body:ExprId(5)}),(15,Expr::Lam{domain:ExprId(2),body:ExprId(3)}),(16,Expr::Pi{domain:ExprId(3),body:ExprId(3)}),(17,Expr::BVar(99)),(18,Expr::Lam{domain:ExprId(2),body:ExprId(17)}),(19,Expr::App{fun:ExprId(8),arg:ExprId(18)})]{e.insert(ExprId(id),node).unwrap();}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![],ExprId(1))).unwrap().extend(NameId(3),crate::environment::ConstantDecl::axiom(vec![],ExprId(4))).unwrap().extend(NameId(4),crate::environment::ConstantDecl::axiom(vec![],ExprId(9))).unwrap().extend(NameId(5),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap();(e,l,env)
 }
 #[test]
 fn actual_lambda_proof_type_pi_must_be_independently_formed_and_admitted(){
  let(e,l,env)=setup();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;
  let p=c.closure(ExprId(4),EnvFrame::empty());let p_kind=c.infer_exact_closure_in_context(&p,&[],&mut 4096,0).unwrap();assert_eq!(c.sort_level(Judgment::proven(p_kind,"source-P-formation"),4096).proven_value(),Some(&LevelTerm::Zero));
  let lambda=c.closure(ExprId(6),EnvFrame::empty());let q=c.closure(ExprId(7),EnvFrame::empty());let ty=c.infer_exact_closure_in_context(&lambda,&[],&mut 4096,0).unwrap();assert!(matches!(ty,TypeValue::Pi{binder_owner:Some(_),..}));
  assert!(c.checked_owned_proof_source_pair(&lambda,&q,&[],&mut 8192),"a checked lambda of P=(A→A):Prop must not be declined merely because its inferred type is TypeValue::Pi");
 }
 #[test]
 fn application_with_actual_lambda_proof_is_independently_typed(){
  let(e,l,env)=setup();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let p=TypeValue::Term(c.closure(ExprId(4),EnvFrame::empty()));let owner=EnvFrame::empty().extend_free(FreeId(0));let gamma=vec![p.clone()];c.retain_checked_binding(&owner,p,&gamma);
  let left=c.closure(ExprId(10),owner.clone());let right=c.closure(ExprId(11),owner);assert!(c.checked_owned_proof_source_pair(&left,&right,&gamma,&mut 16384));
 }
 #[test]
 fn data_illtyped_flipped_domain_and_quarantine_do_not_supply_proof_authority(){
  let(e,l,env)=setup();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let q=c.closure(ExprId(7),EnvFrame::empty());let lambda=c.closure(ExprId(6),EnvFrame::empty());
  for expr in [12,14,15,18]{assert!(!c.checked_owned_proof_source_pair(&c.closure(ExprId(expr),EnvFrame::empty()),&q,&[],&mut 8192),"bad lambda expr {expr}");}
  assert!(!c.checked_owned_proof_source_pair(&c.closure(ExprId(19),EnvFrame::empty()),&c.closure(ExprId(10),EnvFrame::empty()),&[],&mut 8192));
  assert!(!c.checked_owned_proof_source_pair(&lambda,&q,&[],&mut 0));
  let nat_lambda=c.closure(ExprId(12),EnvFrame::empty());assert!(!c.checked_owned_proof_source_pair(&nat_lambda,&nat_lambda,&[],&mut 8192));
  let p=TypeValue::Term(c.closure(ExprId(4),EnvFrame::empty()));let owner=EnvFrame::empty().extend_free(FreeId(0));let gamma=vec![p.clone()];c.retain_checked_binding(&owner,p,&gamma);let local_q=c.closure(ExprId(5),owner.clone());c.checked_binding_lineage.borrow_mut().insert(owner.id(),None);assert!(!c.checked_owned_proof_source_pair(&lambda,&local_q,&gamma,&mut 8192));
 }
 fn dependent_setup()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
  let(mut e,l,env)=setup();
  for(id,node)in [(20,Expr::BVar(1)),(21,Expr::Pi{domain:ExprId(5),body:ExprId(20)}),(22,Expr::Pi{domain:ExprId(0),body:ExprId(21)}),(23,Expr::Lam{domain:ExprId(5),body:ExprId(5)}),(24,Expr::Lam{domain:ExprId(0),body:ExprId(23)}),(25,Expr::Const{name:NameId(6),levels:vec![]}),(26,Expr::Lam{domain:ExprId(1),body:ExprId(23)}),(27,Expr::Pi{domain:ExprId(1),body:ExprId(21)}),(28,Expr::Const{name:NameId(7),levels:vec![]})]{e.insert(ExprId(id),node).unwrap();}
  let env=env.extend(NameId(6),crate::environment::ConstantDecl::axiom(vec![],ExprId(22))).unwrap().extend(NameId(7),crate::environment::ConstantDecl::axiom(vec![],ExprId(27))).unwrap();(e,l,env)
 }
 #[test]
 fn dependent_proposition_lambda_forms_both_domains_and_actual_owned_codomain(){
  let(e,l,env)=dependent_setup();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;
  let cold_lambda=c.closure(ExprId(24),EnvFrame::empty());let cold_q=c.closure(ExprId(25),EnvFrame::empty());assert!(c.checked_owned_proof_source_pair(&cold_lambda,&cold_q,&[],&mut 32768),"the dependent proof rule must succeed before any external formation or conversion probes");
  let source=c.closure(ExprId(22),EnvFrame::empty());let formed=c.infer_exact_closure_in_context(&source,&[],&mut 8192,0).unwrap();assert_eq!(c.sort_level(Judgment::proven(formed,"actual-dependent-P-formation"),8192).proven_value(),Some(&LevelTerm::Zero));
  let lambda=c.closure(ExprId(24),EnvFrame::empty());let q=c.closure(ExprId(25),EnvFrame::empty());let ty=c.infer_exact_closure_in_context(&lambda,&[],&mut 8192,0).unwrap();assert_eq!(c.owned_inferred_type_formation_sort(&ty,&[],&mut 8192,0),Some(LevelTerm::Zero));
  assert!(c.checked_owned_proof_source_pair(&lambda,&q,&[],&mut 32768),"∀P:Prop, P→P is Prop with actual two checked binder scopes");
  assert!(!c.checked_owned_proof_source_pair(&c.closure(ExprId(26),EnvFrame::empty()),&c.closure(ExprId(28),EnvFrame::empty()),&[],&mut 32768),"∀A:Type, A→A is a data type");
  assert_eq!(c.owned_inferred_type_formation_sort(&TypeValue::Sort(LevelTerm::Zero),&[],&mut 64,0),Some(succ(LevelTerm::Zero)));
  assert_eq!(c.owned_inferred_type_formation_sort(&TypeValue::Term(q),&[],&mut 8192,0),None,"a proof must not become a formed type");
 }
 #[test]
 fn actual_pi_formation_requires_matching_scope_owner_and_current_used_wrapper(){
  let(e,l,env)=dependent_setup();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let lambda=c.closure(ExprId(24),EnvFrame::empty());let ty=c.infer_exact_closure_in_context(&lambda,&[],&mut 8192,0).unwrap();
  let TypeValue::Pi{binder_owner:Some(original),domain,body,..}=&ty else{panic!()};
  assert_eq!(c.owned_inferred_type_formation_sort(&ty,&[],&mut 0,0),None);
  assert_eq!(c.owned_inferred_type_formation_sort(&ty,&[TypeValue::Term(c.closure(ExprId(3),EnvFrame::empty()))],&mut 8192,0),None);
  let mut no_owner=ty.clone();if let TypeValue::Pi{binder_owner,..}=&mut no_owner{*binder_owner=None;}assert_eq!(c.owned_inferred_type_formation_sort(&no_owner,&[],&mut 8192,0),None);
  let mut wrong_domain=ty.clone();if let TypeValue::Pi{domain,..}=&mut wrong_domain{*domain=Box::new(TypeValue::Term(c.closure(ExprId(3),EnvFrame::empty())));}assert_eq!(c.owned_inferred_type_formation_sort(&wrong_domain,&[],&mut 8192,0),None);
  let alias=EnvFrame::empty().extend_neutral(Neutral{head:NeutralHead::Free(FreeId(0),Some(original.clone())),spine:vec![]});c.retain_checked_binding(&alias,(**domain).clone(),&[(**domain).clone()]);
  let mut wrapped=ty.clone();let TypeValue::Pi{body:inner,..}=&mut wrapped else{panic!()};let TypeValue::Pi{body:inner_body,..}=inner.as_mut() else{panic!()};let TypeValue::Term(term)=inner_body.as_mut() else{panic!()};*term=term.sibling(term.expr,alias.clone());
  assert_eq!(c.owned_inferred_type_formation_sort(&wrapped,&[],&mut 8192,0),Some(LevelTerm::Zero));c.checked_binding_lineage.borrow_mut().insert(alias.id(),None);assert_eq!(c.owned_inferred_type_formation_sort(&wrapped,&[],&mut 8192,0),None);
  let _=body;c.checked_binding_lineage.borrow_mut().insert(original.id(),None);assert_eq!(c.owned_inferred_type_formation_sort(&ty,&[],&mut 8192,0),None);
 }
 #[test]
 fn actual_own_universe_substitutions_classify_pi_proofs_and_data_independently(){
  let(mut e,mut l,env)=setup();l.insert(LevelId(2),Level::Param(NameId(40))).unwrap();
  for(id,node)in [(29,Expr::Sort(LevelId(2))),(30,Expr::Const{name:NameId(10),levels:vec![LevelId(2)]}),(31,Expr::Lam{domain:ExprId(30),body:ExprId(5)}),(32,Expr::Pi{domain:ExprId(30),body:ExprId(30)}),(33,Expr::Const{name:NameId(11),levels:vec![LevelId(2)]})]{e.insert(ExprId(id),node).unwrap();}
  let env=env.extend(NameId(10),crate::environment::ConstantDecl::axiom(vec![NameId(40)],ExprId(29))).unwrap().extend(NameId(11),crate::environment::ConstantDecl::axiom(vec![NameId(40)],ExprId(32))).unwrap();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;
  let make=|expr,level,extra|{let mut levels=vec![(NameId(40),level)];if extra{levels.push((NameId(41),succ(LevelTerm::Zero)));}Closure::with_levels(ExprId(expr),EnvFrame::empty(),LevelSubstitution::new(levels))};
  let proof=make(31,LevelTerm::Zero,true);let q=make(33,LevelTerm::Zero,false);assert!(c.checked_owned_proof_source_pair(&proof,&q,&[],&mut 16384));
  let data=make(31,succ(LevelTerm::Zero),false);let data_q=make(33,succ(LevelTerm::Zero),false);assert!(!c.checked_owned_proof_source_pair(&data,&data_q,&[],&mut 16384));assert!(!c.checked_owned_proof_source_pair(&proof,&data_q,&[],&mut 16384));
  let missing=Closure::with_levels(ExprId(31),EnvFrame::empty(),LevelSubstitution::default());assert!(!c.checked_owned_proof_source_pair(&missing,&q,&[],&mut 16384));
 }
}

#[cfg(test)]
mod absent_zero_index_reclosure_tests {
 use super::*;
 #[test]
 fn unused_fixed_binder_needs_no_synthetic_bvar_expression(){
  let mut e=IdTable::default(); let mut l=IdTable::default();
  l.insert(LevelId(0),Level::Zero).unwrap();
  e.insert(ExprId(0),Expr::Sort(LevelId(0))).unwrap();
  e.insert(ExprId(1),Expr::BVar(1)).unwrap();
  let env=Environment::empty();let checker=TypeChecker::new(&e,&l,&env);
  let original=EnvFrame::empty().extend_free(FreeId(0));
  let target=EnvFrame::empty().extend_free(FreeId(1));
  let body=TypeValue::Sort(LevelTerm::Zero);
  assert_eq!(checker.reopen_fixed_pi_body_owned(&body,FreeId(0),&original,&target,&mut 64),Some(body));
  assert!(checker.reopen_fixed_pi_body_owned(&TypeValue::Sort(LevelTerm::Zero),FreeId(0),&original,&target,&mut 0).is_none());
  checker.checked_binding_lineage.borrow_mut().insert(original.id(),None);
  assert!(checker.reopen_fixed_pi_body_owned(&TypeValue::Sort(LevelTerm::Zero),FreeId(0),&original,&target,&mut 64).is_none());
 }
}

#[cfg(test)]
mod fused_shape_support_tests {
 use super::*;
 fn fixture()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();
  for(id,node)in [(0,Expr::Sort(LevelId(0))),(1,Expr::BVar(0)),(2,Expr::BVar(1)),(3,Expr::BVar(5)),(4,Expr::App{fun:ExprId(2),arg:ExprId(3)}),(5,Expr::Lam{domain:ExprId(3),body:ExprId(4)}),(6,Expr::Let{ty:ExprId(3),value:ExprId(2),body:ExprId(4)}),(7,Expr::Pi{domain:ExprId(0),body:ExprId(1)}),(8,Expr::Lam{domain:ExprId(0),body:ExprId(2)}),(9,Expr::Lam{domain:ExprId(0),body:ExprId(3)}),(10,Expr::App{fun:ExprId(100),arg:ExprId(1)}),(11,Expr::App{fun:ExprId(11),arg:ExprId(1)})]{e.insert(ExprId(id),node).unwrap();}
  (e,l,Environment::empty())
 }
 #[test]
 fn canonical_bvar_holes_do_not_erase_exact_lexical_support(){
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);
  assert_eq!(c.complete_lambda_shape_only(ExprId(1),&mut 512),c.complete_lambda_shape_only(ExprId(3),&mut 512));
  assert_eq!(c.source_support.borrow().get(&ExprId(1)),Some(&vec![0]));assert_eq!(c.source_support.borrow().get(&ExprId(3)),Some(&vec![5]));
  for(id,want)in [(4,vec![1,5]),(5,vec![0,4,5]),(6,vec![0,1,4,5]),(7,vec![]),(8,vec![0]),(9,vec![4])]{assert!(c.complete_lambda_shape_only(ExprId(id),&mut 512).is_some());assert_eq!(c.source_support.borrow().get(&ExprId(id)),Some(&want));}
  assert!(c.source_syntax_patterns.borrow().is_empty());assert!(c.source_syntax_pattern_nodes.borrow().is_empty());assert!(c.formed_lambda_goals.borrow().is_empty());assert!(c.owned_lambda_goals.borrow().is_empty());
 }
 #[test]
 fn cached_shape_alone_is_not_a_support_certificate_and_partial_roots_stay_unpublished(){
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);let shape=c.complete_lambda_shape_only(ExprId(3),&mut 32).unwrap();c.source_support.borrow_mut().remove(&ExprId(3));
  assert_eq!(c.complete_lambda_shape_only(ExprId(3),&mut 32),Some(shape));assert_eq!(c.source_support.borrow().get(&ExprId(3)),Some(&vec![5]));
  for id in [10,11]{assert!(c.complete_lambda_shape_only(ExprId(id),&mut 64).is_none());assert!(!c.source_support.borrow().contains_key(&ExprId(id)));assert!(!c.lambda_shape_ids.borrow().contains_key(&ExprId(id)));}
  let cold=TypeChecker::new(&e,&l,&env);assert!(cold.complete_lambda_shape_only(ExprId(5),&mut 1).is_none());assert!(!cold.source_support.borrow().contains_key(&ExprId(5)));assert!(!cold.lambda_shape_ids.borrow().contains_key(&ExprId(5)));
  let dangling=c.closure(ExprId(3),EnvFrame::empty());assert!(!crate::convert::source_opening_avoids_capture(&c,&dangling,FreeId(9),&mut 64),"exactsyntaxsupport doesnotform an absent actualcapture");
  let expected=TypeValue::Term(c.closure(ExprId(7),EnvFrame::empty()));assert!(!c.check(ExprId(9),&expected,512).is_proven());
 }
 #[test]
 fn fused_support_capacity_does_not_make_a_shape_only_hit_complete(){
  let(mut e,l,env)=fixture();for id in 1000..9192{e.insert(ExprId(id),Expr::Sort(LevelId(0))).unwrap();}
  let c=TypeChecker::new(&e,&l,&env);for id in 1000..9192{assert_eq!(c.complete_source_support(ExprId(id),&mut 4),Some(vec![]));}
  assert_eq!(c.source_support.borrow().len(),8192);let shape=c.complete_lambda_shape_only(ExprId(3),&mut 32).unwrap();assert_eq!(c.lambda_shape_ids.borrow().get(&ExprId(3)),Some(&shape));assert!(!c.source_support.borrow().contains_key(&ExprId(3)));
  assert!(c.complete_lambda_shape_only(ExprId(3),&mut 1).is_none(),"saturatedsupportcache cannotpromote barecachedshape tocomplete lexicalsupport");assert_eq!(c.source_support.borrow().len(),8192);
 }

}

#[cfg(test)]
mod active_original_application_formation_tests {
 use super::*;
 fn fixture()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
  let mut e=IdTable::default();let mut l=IdTable::default();for(id,level)in[(0,Level::Zero),(1,Level::Succ(LevelId(0))),(2,Level::Param(NameId(10)))]{l.insert(LevelId(id),level).unwrap();}
  for(id,node)in[(0,Expr::Sort(LevelId(0))),(1,Expr::Sort(LevelId(1))),(2,Expr::BVar(0)),(3,Expr::Const{name:NameId(1),levels:vec![]}),(4,Expr::App{fun:ExprId(3),arg:ExprId(2)}),(5,Expr::Pi{domain:ExprId(1),body:ExprId(1)}),(6,Expr::Const{name:NameId(2),levels:vec![]}),(7,Expr::Const{name:NameId(3),levels:vec![]}),(8,Expr::Pi{domain:ExprId(6),body:ExprId(6)}),(9,Expr::Const{name:NameId(6),levels:vec![]}),(10,Expr::App{fun:ExprId(9),arg:ExprId(7)}),(11,Expr::Const{name:NameId(4),levels:vec![]}),(12,Expr::Const{name:NameId(5),levels:vec![]}),(13,Expr::Pi{domain:ExprId(11),body:ExprId(11)}),(14,Expr::Const{name:NameId(7),levels:vec![]}),(15,Expr::App{fun:ExprId(14),arg:ExprId(12)}),(16,Expr::BVar(99)),(17,Expr::App{fun:ExprId(3),arg:ExprId(16)}),(18,Expr::App{fun:ExprId(3),arg:ExprId(7)}),(19,Expr::App{fun:ExprId(19),arg:ExprId(2)}),(20,Expr::Sort(LevelId(2))),(21,Expr::Pi{domain:ExprId(20),body:ExprId(20)}),(22,Expr::Const{name:NameId(8),levels:vec![LevelId(2)]}),(23,Expr::App{fun:ExprId(22),arg:ExprId(2)}),(25,Expr::App{fun:ExprId(3),arg:ExprId(12)}),(26,Expr::App{fun:ExprId(3),arg:ExprId(11)})]{e.insert(ExprId(id),node).unwrap();}
  let mut env=Environment::empty();for(name,ty)in[(1,5),(2,0),(3,6),(4,1),(5,11),(6,8),(7,13)]{env=env.extend(NameId(name),crate::environment::ConstantDecl::axiom(vec![],ExprId(ty))).unwrap();}env=env.extend(NameId(8),crate::environment::ConstantDecl::axiom(vec![NameId(10)],ExprId(21))).unwrap();(e,l,env)
 }
 #[test]
 fn cold_actual_application_forms_its_type_under_the_real_owned_gamma(){
  let(e,l,env)=fixture();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let owner=EnvFrame::empty().extend_free(FreeId(0));let ty=TypeValue::Term(c.closure(ExprId(1),EnvFrame::empty()));let gamma=vec![ty.clone()];c.retain_checked_binding(&owner,ty,&gamma);let source=c.closure(ExprId(4),owner.clone());let _outer=GeneralDomainFormationOwner::enter();let mut work=256;
  assert_eq!(c.checked_active_source_sort(&source,&gamma,&mut work),Some(succ(LevelTerm::Zero)),"F(A):Type must be formed from the original F declaration and actual typed A");assert!(work<256&&work>0);assert!(GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.get()));
  for id in[10,15,17,18,19,25]{assert!(c.checked_active_source_sort(&c.closure(ExprId(id),owner.clone()),&gamma,&mut 256).is_none(),"proof/data/malformed application {id} is not a formed TYPE");}
  assert!(c.checked_active_source_sort(&source,&[],&mut 256).is_none());assert!(c.checked_active_source_sort(&source,&gamma,&mut 0).is_none());assert!(GENERAL_DOMAIN_FORMATION_ACTIVE.with(|f|f.get()));
 }
 #[test]
 fn application_formation_uses_own_universes_and_preserves_original_and_wrapper_quarantine(){
  let(e,l,env)=fixture();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let theta=LevelSubstitution::new(vec![(NameId(10),succ(LevelTerm::Zero)),(NameId(11),LevelTerm::Param("unused".into()))]);let ty=TypeValue::Term(Closure::with_levels(ExprId(20),EnvFrame::empty(),theta.clone()));let gamma=vec![ty.clone()];let owner=EnvFrame::empty().extend_free(FreeId(0));c.retain_checked_binding(&owner,ty.clone(),&gamma);let source=Closure::with_levels(ExprId(23),owner.clone(),theta.clone());let _outer=GeneralDomainFormationOwner::enter();assert_eq!(c.checked_active_source_sort(&source,&gamma,&mut 256),Some(succ(LevelTerm::Zero)));
  let wrong=Closure::with_levels(ExprId(23),owner.clone(),LevelSubstitution::new(vec![(NameId(10),LevelTerm::Zero)]));assert!(c.checked_active_source_sort(&wrong,&gamma,&mut 256).is_none());let missing=Closure::with_levels(ExprId(23),owner.clone(),LevelSubstitution::default());assert!(c.checked_active_source_sort(&missing,&gamma,&mut 256).is_none());
  let wrapper=EnvFrame::empty().extend_neutral(Neutral{head:NeutralHead::Free(FreeId(0),Some(owner.clone())),spine:vec![]});c.retain_checked_binding(&wrapper,ty,&gamma);let wrapped=Closure::with_levels(ExprId(23),wrapper.clone(),theta);assert!(c.checked_active_source_sort(&wrapped,&gamma,&mut 256).is_some());c.checked_binding_lineage.borrow_mut().insert(wrapper.id(),None);assert!(c.checked_active_source_sort(&wrapped,&gamma,&mut 256).is_none());c.checked_binding_lineage.borrow_mut().insert(owner.id(),None);assert!(c.checked_active_source_sort(&source,&gamma,&mut 256).is_none());
 }
}

#[cfg(test)]
mod source_structure_relation_tests {
 use super::*;
 fn fixture(prop:bool,eta:bool)->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(id,node)in[(0,Expr::Sort(LevelId(if prop{0}else{1}))),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::Const{name:NameId(2),levels:vec![]}),(3,Expr::BVar(0)),(4,Expr::App{fun:ExprId(4),arg:ExprId(3)})]{e.insert(ExprId(id),node).unwrap();}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![],ExprId(1))).unwrap().install_projection_spec(NameId(1),crate::machine::ProjectionSpec{constructor:NameId(2),num_params:0,field_types:vec![],eta_expandable:eta}).unwrap();(e,l,env)
 }
 fn value(owner:&EnvFrame,free:FreeId)->Value{Value::Neutral(Neutral{head:NeutralHead::Free(free,Some(owner.clone())),spine:vec![]})}
 #[test]
 fn non_eta_requires_real_nominal_scope_and_refuses_same_number_siblings_and_proofs(){
  let(e,l,env)=fixture(false,false);let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let ty=TypeValue::Term(c.closure(ExprId(1),EnvFrame::empty()));
  let a=EnvFrame::empty().extend_free(FreeId(0));let ga=vec![ty.clone()];c.retain_checked_binding(&a,ty.clone(),&ga);
  let b=a.extend_free(FreeId(1));let gb=vec![ty.clone(),ty.clone()];c.retain_checked_binding(&b,ty.clone(),&gb);
  let left=c.closure(ExprId(3),a.clone());let right=c.closure(ExprId(3),b.clone());
  assert!(c.checked_source_structure_relation(&left,&right,&value(&a,FreeId(0)),&value(&b,FreeId(1)),&gb,&mut 4096).unwrap().is_refuted());
  let sibling=EnvFrame::empty().extend_free(FreeId(0));c.retain_checked_binding(&sibling,ty.clone(),&ga);assert!(c.checked_source_structure_relation(&left,&c.closure(ExprId(3),sibling.clone()),&value(&a,FreeId(0)),&value(&sibling,FreeId(0)),&ga,&mut 4096).is_none());
  assert!(c.checked_source_structure_relation(&left,&right,&value(&a,FreeId(0)),&value(&b,FreeId(1)),&[],&mut 4096).is_none());assert!(c.checked_source_structure_relation(&left,&right,&value(&a,FreeId(0)),&value(&b,FreeId(1)),&gb,&mut 0).is_none());
  let(pe,pl,penv)=fixture(true,false);let mut pc=TypeChecker::new(&pe,&pl,&penv);pc.strict_origin_probe=true;let p=TypeValue::Term(pc.closure(ExprId(1),EnvFrame::empty()));let pa=EnvFrame::empty().extend_free(FreeId(0));let pb=pa.extend_free(FreeId(1));let pg=vec![p.clone(),p.clone()];pc.retain_checked_binding(&pa,p.clone(),&pg[..1]);pc.retain_checked_binding(&pb,p,&pg);assert!(pc.checked_source_structure_relation(&pc.closure(ExprId(3),pa.clone()),&pc.closure(ExprId(3),pb.clone()),&value(&pa,FreeId(0)),&value(&pb,FreeId(1)),&pg,&mut 4096).is_none());
 }
 #[test]
 fn source_structure_domains_keep_own_universes_and_missing_or_prop_instantiation_declines(){
  let(mut e,mut l,_)=fixture(false,false);l.insert(LevelId(2),Level::Param(NameId(10))).unwrap();e.insert(ExprId(5),Expr::Sort(LevelId(2))).unwrap();e.insert(ExprId(6),Expr::Const{name:NameId(1),levels:vec![LevelId(2)]}).unwrap();
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![NameId(10)],ExprId(5))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![NameId(10)],ExprId(6))).unwrap().install_projection_spec(NameId(1),crate::machine::ProjectionSpec{constructor:NameId(2),num_params:0,field_types:vec![],eta_expandable:false}).unwrap();
  for level in [Some(succ(LevelTerm::Zero)),Some(LevelTerm::Zero),Some(LevelTerm::IMax(Box::new(succ(LevelTerm::Zero)),Box::new(LevelTerm::Zero))),Some(LevelTerm::Max(Box::new(LevelTerm::Zero),Box::new(LevelTerm::Zero))),None]{
   let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let theta=LevelSubstitution::new(level.clone().map(|x|vec![(NameId(10),x)]).unwrap_or_default());let ty=TypeValue::Term(Closure::with_levels(ExprId(6),EnvFrame::empty(),theta));let a=EnvFrame::empty().extend_free(FreeId(0));let b=a.extend_free(FreeId(1));let gamma=vec![ty.clone(),ty.clone()];c.retain_checked_binding(&a,ty.clone(),&gamma[..1]);c.retain_checked_binding(&b,ty,&gamma);let r=c.checked_source_structure_relation(&c.closure(ExprId(3),a.clone()),&c.closure(ExprId(3),b.clone()),&value(&a,FreeId(0)),&value(&b,FreeId(1)),&gamma,&mut 4096);
   if level==Some(succ(LevelTerm::Zero)){assert!(r.unwrap().is_refuted());}else{assert!(r.is_none());}
  }
 }
 #[test]
 fn projection_field_requires_exact_registered_body_index_major_arity_and_finite_source(){
  let(mut e,l,env)=fixture(false,true);
  for(id,node)in[(5,Expr::Proj{type_name:NameId(1),index:0,structure:ExprId(3)}),(6,Expr::Lam{domain:ExprId(1),body:ExprId(5)}),(7,Expr::Pi{domain:ExprId(1),body:ExprId(1)}),(8,Expr::Const{name:NameId(3),levels:vec![]}),(9,Expr::App{fun:ExprId(8),arg:ExprId(3)}),(10,Expr::App{fun:ExprId(9),arg:ExprId(3)}),(11,Expr::Proj{type_name:NameId(1),index:1,structure:ExprId(3)}),(12,Expr::App{fun:ExprId(12),arg:ExprId(3)}),(13,Expr::Lam{domain:ExprId(1),body:ExprId(11)}),(14,Expr::Const{name:NameId(4),levels:vec![]}),(15,Expr::App{fun:ExprId(14),arg:ExprId(3)})]{e.insert(ExprId(id),node).unwrap();}
  let env=env.extend(NameId(3),crate::environment::ConstantDecl::definition(vec![],ExprId(7),ExprId(6),true)).unwrap().extend(NameId(4),crate::environment::ConstantDecl::definition(vec![],ExprId(7),ExprId(13),true)).unwrap();let c=TypeChecker::new(&e,&l,&env);let owner=EnvFrame::empty().extend_free(FreeId(0));let target=Neutral{head:NeutralHead::Free(FreeId(0),Some(owner.clone())),spine:vec![]};
  assert!(c.certified_eta_projection_field(&c.closure(ExprId(9),owner.clone()),NameId(1),0,&target,0,128));
  for id in[8,10,12,15]{assert!(!c.certified_eta_projection_field(&c.closure(ExprId(id),owner.clone()),NameId(1),0,&target,0,128));}
  assert!(!c.certified_eta_projection_field(&c.closure(ExprId(9),owner.clone()),NameId(1),1,&target,0,128));assert!(!c.certified_eta_projection_field(&c.closure(ExprId(9),owner.clone()),NameId(5),0,&target,0,128));assert!(!c.certified_eta_projection_field(&c.closure(ExprId(9),owner.clone()),NameId(1),0,&target,0,0));
  let other=EnvFrame::empty().extend_free(FreeId(0));assert!(!c.certified_eta_projection_field(&c.closure(ExprId(9),other),NameId(1),0,&target,0,128));
 }
 #[test]
 fn eta_keeps_original_and_wrapper_quarantine_and_declines_bad_arity_cycles_and_low_work(){
  let(e,l,env)=fixture(false,true);let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let ty=TypeValue::Term(c.closure(ExprId(1),EnvFrame::empty()));let owner=EnvFrame::empty().extend_free(FreeId(0));let gamma=vec![ty.clone()];c.retain_checked_binding(&owner,ty.clone(),&gamma);let target=c.closure(ExprId(3),owner.clone());let ctor=c.closure(ExprId(2),EnvFrame::empty());let cv=Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(2),levels:vec![]},spine:vec![]});let tv=value(&owner,FreeId(0));
  assert!(c.checked_source_structure_relation(&target,&ctor,&tv,&cv,&gamma,&mut 4096).unwrap().is_proven());assert!(c.checked_source_structure_relation(&target,&ctor,&tv,&cv,&gamma,&mut 1).is_none());
  let bad=Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(2),levels:vec![]},spine:vec![ctor.clone()]});assert!(c.checked_source_structure_relation(&target,&ctor,&tv,&bad,&gamma,&mut 4096).is_none());
  assert!(c.checked_source_structure_relation(&target,&c.closure(ExprId(4),owner.clone()),&tv,&cv,&gamma,&mut 4096).is_none());
  let wrapper=EnvFrame::empty().extend_neutral(Neutral{head:NeutralHead::Free(FreeId(0),Some(owner.clone())),spine:vec![]});c.retain_checked_binding(&wrapper,ty,&gamma);let wrapped=c.closure(ExprId(3),wrapper.clone());assert!(c.checked_source_structure_relation(&wrapped,&ctor,&tv,&cv,&gamma,&mut 4096).unwrap().is_proven());c.checked_binding_lineage.borrow_mut().insert(wrapper.id(),None);assert!(c.checked_source_structure_relation(&wrapped,&ctor,&tv,&cv,&gamma,&mut 4096).is_none());c.checked_binding_lineage.borrow_mut().insert(owner.id(),None);assert!(c.checked_source_structure_relation(&target,&ctor,&tv,&cv,&gamma,&mut 4096).is_none());
 }
}

#[cfg(test)]
mod normalized_proof_sort_regression {
 use super::*;
 #[test]
 fn noncanonical_zero_substitution_certifies_actual_proofs_not_data() {
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Param(NameId(1))).unwrap();
  e.insert(ExprId(0),Expr::Sort(LevelId(0))).unwrap();e.insert(ExprId(1),Expr::Const{name:NameId(2),levels:vec![LevelId(0)]}).unwrap();e.insert(ExprId(2),Expr::BVar(0)).unwrap();e.insert(ExprId(3),Expr::Const{name:NameId(3),levels:vec![LevelId(0)]}).unwrap();
  let env=Environment::empty().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![NameId(1)],ExprId(0))).unwrap().extend(NameId(3),crate::environment::ConstantDecl::axiom(vec![NameId(1)],ExprId(0))).unwrap();
  for zero in [LevelTerm::IMax(Box::new(succ(LevelTerm::Zero)),Box::new(LevelTerm::Zero)),LevelTerm::Max(Box::new(LevelTerm::Zero),Box::new(LevelTerm::Zero))] {
   let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;
   let theta=LevelSubstitution::new(vec![(NameId(1),zero)]);let ty=TypeValue::Term(Closure::with_levels(ExprId(1),EnvFrame::empty(),theta));
   let a=EnvFrame::empty().extend_free(FreeId(0));let b=a.extend_free(FreeId(1));let gamma=vec![ty.clone(),ty.clone()];c.retain_checked_binding(&a,ty.clone(),&gamma[..1]);c.retain_checked_binding(&b,ty,&gamma);
   let p=c.closure(ExprId(2),a.clone());let q=c.closure(ExprId(2),b.clone());assert!(c.checked_owned_proof_source_pair(&p,&q,&gamma,&mut 4096),"both sources are independently proofs of the SAME proposition at a normalized-zero universe");
   c.checked_binding_lineage.borrow_mut().insert(a.id(),None);assert!(!c.checked_owned_proof_source_pair(&p,&q,&gamma,&mut 4096));
  }
  let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;
  let theta=LevelSubstitution::new(vec![(NameId(1),LevelTerm::IMax(Box::new(succ(LevelTerm::Zero)),Box::new(LevelTerm::Zero)))]);
  let pty=TypeValue::Term(Closure::with_levels(ExprId(1),EnvFrame::empty(),theta.clone()));let qty=TypeValue::Term(Closure::with_levels(ExprId(3),EnvFrame::empty(),theta));
  let a=EnvFrame::empty().extend_free(FreeId(0));let b=a.extend_free(FreeId(1));let gamma=vec![pty.clone(),qty.clone()];c.retain_checked_binding(&a,pty,&gamma[..1]);c.retain_checked_binding(&b,qty,&gamma);
  assert!(!c.checked_owned_proof_source_pair(&c.closure(ExprId(2),a),&c.closure(ExprId(2),b),&gamma,&mut 4096),"independently formed DIFFERENT propositions do not license proof irrelevance");
  let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;let ty=TypeValue::Term(Closure::with_levels(ExprId(1),EnvFrame::empty(),LevelSubstitution::new(vec![(NameId(1),succ(LevelTerm::Zero))])));let a=EnvFrame::empty().extend_free(FreeId(0));let b=a.extend_free(FreeId(1));let gamma=vec![ty.clone(),ty.clone()];c.retain_checked_binding(&a,ty.clone(),&gamma[..1]);c.retain_checked_binding(&b,ty,&gamma);assert!(!c.checked_owned_proof_source_pair(&c.closure(ExprId(2),a),&c.closure(ExprId(2),b),&gamma,&mut 4096),"Type data has no proof-irrelevance certificate");
 }
}

#[cfg(test)]
mod carried_context_scope_review_tests {
 use super::*;
 #[test]
 fn completed_context_opening_preserves_own_universes_and_both_revocations(){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(id,node)in[(0,Expr::Sort(LevelId(1))),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::BVar(0)),(3,Expr::BVar(1))]{e.insert(ExprId(id),node).unwrap();}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap();let mut c=TypeChecker::new(&e,&l,&env);c.strict_origin_probe=true;
  let d=c.closure(ExprId(1),EnvFrame::empty());let gamma=Rc::new(vec![TypeValue::Term(d.clone());3]);let fresh=FreeId(3);
  let lp=EnvFrame::empty();let rp=EnvFrame::empty().extend_free(FreeId(9));let lb=c.closure(ExprId(2),lp.clone());let rb=Closure::with_levels(ExprId(2),rp.clone(),LevelSubstitution::new(vec![(NameId(77),LevelTerm::Succ(Box::new(LevelTerm::Zero)))]));
  assert!(crate::convert::source_opening_avoids_capture(&c,&lb,fresh,&mut 64));assert!(crate::convert::source_opening_avoids_capture(&c,&rb,fresh,&mut 64));
  crate::convert::with_completed_domain_pair_for_test(&c,&d,&d,&gamma,|proof|{
   let mut zero=0;assert!(c.checked_proven_domain_joint_opening(proof,&d,&d,&lb,&rb,&gamma,fresh,&mut zero).is_none());
   let other=(*gamma).clone();assert!(c.checked_proven_domain_joint_opening(proof,&d,&d,&lb,&rb,&other,fresh,&mut 128).is_none());
   let changed=d.sibling(ExprId(0),d.env.clone());assert!(c.checked_proven_domain_joint_opening(proof,&changed,&d,&lb,&rb,&gamma,fresh,&mut 128).is_none());
   assert!(c.checked_proven_domain_joint_opening(proof,&d,&d,&lb,&rb,&gamma,FreeId(2),&mut 128).is_none());
   let (left,right)=c.checked_proven_domain_joint_opening(proof,&d,&d,&lb,&rb,&gamma,fresh,&mut 4096).expect("completed current domains and actual carried context permit one owned introduction");
   assert_eq!(left.env.parent_id(),Some(lp.id()));assert_eq!(right.env.parent_id(),Some(rp.id()));assert_eq!(right.levels,rb.levels);assert_eq!(left.levels,lb.levels);
   assert!(matches!(right.env.lookup_binding_ref(0),Some(EnvBinding::Neutral(Neutral{head:NeutralHead::Free(f,Some(owner)),spine})) if *f==fresh&&owner.id()==left.env.id()&&spine.is_empty()));
   let body_gamma=proof.completed_body_context();let witness=c.checked_binding_lineage.borrow()[&left.env.id()].clone().unwrap();assert!(Rc::ptr_eq(&witness.protected_prefix,body_gamma));
   assert_eq!(c.infer_exact_closure_in_context(&right,body_gamma,&mut 128,0),Some(TypeValue::Term(d.clone())));
   let saved=c.checked_binding_lineage.borrow()[&right.env.id()].clone();c.checked_binding_lineage.borrow_mut().insert(right.env.id(),None);assert!(c.infer_exact_closure_in_context(&right,body_gamma,&mut 128,0).is_none());
   c.checked_binding_lineage.borrow_mut().insert(right.env.id(),saved);c.checked_binding_lineage.borrow_mut().insert(left.env.id(),None);assert!(c.infer_exact_closure_in_context(&right,body_gamma,&mut 128,0).is_none());
  });
  let dangling=c.closure(ExprId(3),EnvFrame::empty());assert!(!crate::convert::source_opening_avoids_capture(&c,&dangling,fresh,&mut 64));
 }
}

#[cfg(test)]
mod source_abstract_data_local_controls {
 use super::*;use crate::syntax::Level;
 #[test] fn distinct_abstract_data_locals_require_the_actual_owned_gamma(){
  for proof in [false,true] {
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(i,v)in[(0,Expr::Sort(LevelId(if proof {0}else{1}))),(1,Expr::BVar(0)),(2,Expr::BVar(1))]{e.insert(ExprId(i),v).unwrap();}
  let env=Environment::empty();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();
  let sort=TypeValue::Term(Closure::new(ExprId(0),EnvFrame::empty()));let p=EnvFrame::empty().extend_free(FreeId(0));c.retain_shared_checked_binding(&p,sort.clone(),Rc::new(vec![sort.clone()]));
  let ty=TypeValue::Term(Closure::new(ExprId(1),p.clone()));let x=p.extend_free(FreeId(1));c.retain_shared_checked_binding(&x,ty.clone(),Rc::new(vec![sort.clone(),ty.clone()]));
  let y=x.extend_free(FreeId(2));let gamma=vec![sort,ty.clone(),ty.clone()];c.retain_shared_checked_binding(&y,ty,Rc::new(gamma.clone()));
  let left=Closure::new(ExprId(2),y.clone());let right=Closure::new(ExprId(1),y.clone());
  let lv=Value::Neutral(Neutral{head:NeutralHead::Free(FreeId(1),Some(x.clone())),spine:vec![]});let rv=Value::Neutral(Neutral{head:NeutralHead::Free(FreeId(2),Some(y.clone())),spine:vec![]});
  let compare=||c.checked_source_structure_relation(&left,&right,&lv,&rv,&gamma,&mut 4096);
  if proof {assert!(compare().is_none(),"proof locals cannot receive rigid data inequality");}
  else {assert!(compare().is_some_and(|r|r.is_refuted()),"distinct certified data locals of abstract p:Type are rigidly unequal");}
  assert!(c.checked_source_structure_relation(&left,&left,&lv,&lv,&gamma,&mut 4096).is_none(),"same owned local is never distinct");
  let forged=Value::Neutral(Neutral{head:NeutralHead::Free(FreeId(2),Some(EnvFrame::empty().extend_free(FreeId(2)))),spine:vec![]});
  assert!(c.checked_source_structure_relation(&left,&right,&lv,&forged,&gamma,&mut 4096).is_none(),"matching numeric local IDs in unrelated owners do not certify inequality");
  assert!(c.checked_source_structure_relation(&left,&right,&lv,&rv,&[],&mut 4096).is_none());
  assert!(c.checked_source_structure_relation(&left,&right,&lv,&rv,&gamma,&mut 0).is_none());
  c.checked_binding_lineage.borrow_mut().insert(x.id(),None);assert!(compare().is_none());
  }
 }
}
#[cfg(test)]
mod source_eta_argument_controls {
 use super::*;
 #[test]
 fn argument_inequality_requires_rigid_data_result_and_actual_owned_scope(){
  for mode in 0..4 {
   let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
   for(i,v)in[(0,Expr::Sort(LevelId(1))),(1,Expr::BVar(0)),(2,Expr::BVar(1)),(3,Expr::BVar(2)),(4,Expr::BVar(3)),(5,Expr::BVar(4)),(6,Expr::Const{name:NameId(1),levels:vec![]}),(7,Expr::Pi{domain:ExprId(2),body:ExprId(2)}),(8,Expr::Pi{domain:ExprId(3),body:ExprId(4)}),(9,Expr::App{fun:ExprId(2),arg:ExprId(1)}),(10,Expr::App{fun:ExprId(3),arg:ExprId(9)}),(11,Expr::Lam{domain:ExprId(4),body:ExprId(10)}),(12,Expr::Pi{domain:ExprId(2),body:ExprId(6)}),(13,Expr::App{fun:ExprId(3),arg:ExprId(1)}),(14,Expr::Sort(LevelId(0))),(15,Expr::Lam{domain:ExprId(4),body:ExprId(13)})]{e.insert(ExprId(i),v).unwrap();}
   let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();
   let sort=TypeValue::Term(c.closure(ExprId(if mode==3{14}else{0}),EnvFrame::empty()));let a=EnvFrame::empty().extend_free(FreeId(0));let mut gamma=vec![sort.clone()];c.retain_checked_binding(&a,sort,&gamma);
   let beta_sort=TypeValue::Term(c.closure(ExprId(if mode==1{14}else{0}),EnvFrame::empty()));let b=a.extend_free(FreeId(1));gamma.push(beta_sort.clone());c.retain_checked_binding(&b,beta_sort,&gamma);
   let ft=TypeValue::Term(c.closure(ExprId(if mode==2{12}else{7}),b.clone()));let f=b.extend_free(FreeId(2));gamma.push(ft.clone());c.retain_checked_binding(&f,ft,&gamma);
   let gt=TypeValue::Term(c.closure(ExprId(8),f.clone()));let g=f.extend_free(FreeId(3));gamma.push(gt.clone());c.retain_checked_binding(&g,gt.clone(),&gamma);
   let lambda=c.closure(ExprId(11),g.clone());let function=c.closure(ExprId(2),g.clone());
   let left=c.machine().expose(lambda.clone(),Transparency::Reducible,1024).proven_value().unwrap().clone();let right=c.machine().expose(function.clone(),Transparency::Reducible,1024).proven_value().unwrap().clone();
   let compare=||crate::convert::source_qualified_free_eta(&c,&lambda,&function,&left,&right,&gamma,4,&mut 16384);
   let result=compare();if mode==0 {assert!(result.is_some_and(|r|r.is_refuted()),"opaque f:data→abstractData preserves distinct checked neutral arguments");}else{assert!(!result.is_some_and(|r|r.is_refuted()),"proof arguments, proof-valued and Unit-like constant results cannot inherit argument inequality");}
   let identity=c.closure(ExprId(15),g.clone());let identity_value=c.machine().expose(identity.clone(),Transparency::Reducible,1024).proven_value().unwrap().clone();assert!(crate::convert::source_qualified_free_eta(&c,&identity,&function,&identity_value,&right,&gamma,4,&mut 16384).is_some_and(|r|r.is_proven()));
   assert!(crate::convert::source_qualified_free_eta(&c,&lambda,&function,&left,&right,&[],0,&mut 16384).is_none());
   let wrapper=f.extend_neutral(Neutral{head:NeutralHead::Free(FreeId(3),Some(g.clone())),spine:vec![]});c.retain_checked_binding(&wrapper,gt,&gamma);let wrapped=lambda.sibling(lambda.expr,wrapper.clone());c.checked_binding_lineage.borrow_mut().insert(wrapper.id(),None);assert!(crate::convert::source_qualified_free_eta(&c,&wrapped,&function,&left,&right,&gamma,4,&mut 16384).is_none());
   c.checked_binding_lineage.borrow_mut().insert(g.id(),None);assert!(compare().is_none());
  }
 }
}

#[cfg(test)]
mod bvar_proof_schedule_controls {
 use super::*;
 use crate::id::{IdTable,LevelId,NameId};
 use crate::syntax::Level;
 use crate::environment::ConstantDecl;
 #[test]
 fn deferred_bvars_keep_nominal_scope_and_original_proof_retry(){
  let mut e=IdTable::default();e.insert(ExprId(0),Expr::Sort(LevelId(0))).unwrap();e.insert(ExprId(1),Expr::Sort(LevelId(1))).unwrap();e.insert(ExprId(2),Expr::Const{name:NameId(1),levels:vec![]}).unwrap();e.insert(ExprId(3),Expr::BVar(0)).unwrap();e.insert(ExprId(4),Expr::BVar(1)).unwrap();e.insert(ExprId(5),Expr::Const{name:NameId(2),levels:vec![]}).unwrap();
  let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  let env=Environment::empty().extend(NameId(1),ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),ConstantDecl::axiom(vec![],ExprId(1))).unwrap();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let empty=EnvFrame::empty();let prop=TypeValue::Term(c.closure(ExprId(2),empty.clone()));let first=empty.extend_free(FreeId(0));let mut gamma=vec![prop.clone()];c.retain_checked_binding(&first,prop.clone(),&gamma);let second=first.extend_free(FreeId(1));gamma.push(prop.clone());c.retain_checked_binding(&second,prop,&gamma);
  let term=|id,frame|TypeValue::Term(c.closure(ExprId(id),frame));let compare=|a:&TypeValue,b:&TypeValue,g:&[TypeValue],budget|crate::convert::convert_with_policy_in_context(&c,a,b,budget,crate::convert::DeltaPolicy::GuardedSemanticFallback,g.len(),g);
  assert!(compare(&term(4,second.clone()),&term(3,first.clone()),&gamma,64).is_proven(),"ordinary exposure retains exact original owner");
  assert!(compare(&term(3,second.clone()),&term(3,first.clone()),&gamma,4096).is_proven(),"different proof locals still retry strict proof irrelevance on both originals");
  assert!(!compare(&term(3,second.clone()),&term(3,first.clone()),&[],4096).is_proven());
  let nat=TypeValue::Term(c.closure(ExprId(5),empty.clone()));let a=empty.extend_free(FreeId(0));let b=empty.extend_free(FreeId(0));let ng=vec![nat.clone()];c.retain_checked_binding(&a,nat.clone(),&ng);c.retain_checked_binding(&b,nat,&ng);assert!(!compare(&term(3,a),&term(3,b),&ng,4096).is_proven(),"same numeric Free in independent introductions cannot close");
  c.checked_binding_lineage.borrow_mut().insert(first.id(),None);assert!(!compare(&term(3,second),&term(3,first),&gamma,4096).is_proven(),"revoked originals cannot supply fallback proof typing");
 }
}

#[cfg(test)]
mod used_capture_binary_owner_cost_controls {
 use super::*;
 use crate::id::{IdTable,LevelId,NameId};
 use crate::syntax::Level;
 use crate::environment::ConstantDecl;
 #[test]
 fn actual_binary_hops_preserve_owned_used_capture_revocation(){
  let mut e=IdTable::default();e.insert(ExprId(0),Expr::Sort(LevelId(0))).unwrap();e.insert(ExprId(1),Expr::Const{name:NameId(1),levels:vec![]}).unwrap();e.insert(ExprId(2),Expr::BVar(8)).unwrap();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();let env=Environment::empty().extend(NameId(1),ConstantDecl::axiom(vec![],ExprId(0))).unwrap();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let empty=EnvFrame::empty();let domain=TypeValue::Term(c.closure(ExprId(1),empty.clone()));let owner=empty.extend_free(FreeId(0));c.retain_checked_binding(&owner,domain.clone(),&[domain]);let mut frame=owner.clone();for n in 1..=8{frame=frame.extend_free(FreeId(n));}
  let mut work=2;assert_eq!(c.source_capture_owner(&frame,8,&mut work),Some(owner.clone()));assert_eq!(work,0,"one lookup plus the single physical eight-ancestor hop");let mut warm=1;assert_eq!(c.source_capture_owner(&frame,8,&mut warm),Some(owner.clone()));assert_eq!(warm,0,"an exact completed owner lookup costs one");
  let source=c.closure(ExprId(2),frame.clone());let mut work=12;assert!(c.source_used_capture_authority_available(&source,&mut work),"paid owner lookup must preserve allowance for actual declared-domain validation");
  assert!(!c.source_used_capture_authority_available(&source,&mut 0));c.checked_binding_lineage.borrow_mut().insert(frame.id(),None);assert!(!c.source_used_capture_authority_available(&source,&mut 128));c.checked_binding_lineage.borrow_mut().remove(&frame.id());c.checked_binding_lineage.borrow_mut().insert(owner.id(),None);assert!(!c.source_used_capture_authority_available(&source,&mut 128),"cached lookup cannot retain a revoked original witness");
  let dangling=c.closure(ExprId(2),empty);assert!(!c.source_used_capture_authority_available(&dangling,&mut 128));
 }
}

#[cfg(test)]
mod checked_parameter_telescope_controls {
 use super::*;
 use crate::id::{IdTable,LevelId,NameId};
 use crate::syntax::Level;
 use crate::environment::ConstantDecl;
 #[test]
 fn complete_telescope_forms_original_domains_before_shared_introduction(){
  let mut e=IdTable::default();for(id,node)in[(0,Expr::Sort(LevelId(1))),(1,Expr::BVar(0)),(2,Expr::Pi{domain:ExprId(1),body:ExprId(3)}),(3,Expr::BVar(1)),(4,Expr::Lam{domain:ExprId(0),body:ExprId(1)}),(5,Expr::App{fun:ExprId(4),arg:ExprId(2)}),(6,Expr::Const{name:NameId(1),levels:vec![]}),(7,Expr::Lam{domain:ExprId(6),body:ExprId(0)}),(8,Expr::App{fun:ExprId(7),arg:ExprId(0)}),(9,Expr::BVar(99)),(10,Expr::Sort(LevelId(2)))]{e.insert(ExprId(id),node).unwrap();}
  let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();l.insert(LevelId(2),Level::Param(NameId(2))).unwrap();let env=Environment::empty().extend(NameId(1),ConstantDecl::axiom(vec![],ExprId(0))).unwrap();let c=TypeChecker::new(&e,&l,&env);
  let expected=[ExprId(0),ExprId(2)];let actual=[ExprId(0),ExprId(5)];assert!(c.checked_parameter_telescope_equivalence(&expected,&[&actual],&mut 65536),"dependent type domains retain the ONE actual preceding alpha owner");
  for actual in [ExprId(1),ExprId(8),ExprId(9),ExprId(10)] {assert!(!c.checked_parameter_telescope_equivalence(&[ExprId(0)],&[&[actual]],&mut 65536),"unbound/wrong-context, malformed beta-erased argument and missing own universe cannot form a parameter: {actual:?}");}
  assert!(!c.checked_parameter_telescope_equivalence(&expected,&[&actual[..1]],&mut 65536));assert!(!c.checked_parameter_telescope_equivalence(&expected,&[&actual],&mut 0));
  c.checked_binding_lineage.borrow_mut().insert(EnvFrame::empty().id(),None);assert!(!c.checked_parameter_telescope_equivalence(&expected,&[&actual],&mut 65536),"revoked original source/declared-domain scope cannot be retained as a new checked introduction");
 }
}

#[cfg(test)]
mod literal_sort_codomains {
 use super::*;
 #[test] fn checked_application_preserves_original_sort_codomain_own_universe_and_rejects_bad_argument(){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();l.insert(LevelId(2),Level::Param(NameId(13))).unwrap();l.insert(LevelId(3),Level::Succ(LevelId(2))).unwrap();
  for(i,n)in[(0,Expr::Sort(LevelId(1))),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::Sort(LevelId(3))),(3,Expr::Pi{domain:ExprId(2),body:ExprId(2)}),(4,Expr::Const{name:NameId(2),levels:vec![LevelId(0)]}),(5,Expr::App{fun:ExprId(4),arg:ExprId(1)}),(6,Expr::App{fun:ExprId(4),arg:ExprId(0)}),(7,Expr::Const{name:NameId(2),levels:vec![LevelId(1)]}),(8,Expr::App{fun:ExprId(7),arg:ExprId(0)}),(9,Expr::BVar(0)),(10,Expr::App{fun:ExprId(4),arg:ExprId(9)})]{e.insert(ExprId(i),n).unwrap();}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![NameId(13)],ExprId(3))).unwrap();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();
  for(id,level)in[(5,LevelTerm::Zero),(8,succ(LevelTerm::Zero))]{let ty=c.infer_exact_closure_in_context(&c.closure(ExprId(id),EnvFrame::empty()),&[],&mut 4096,0).unwrap();let TypeValue::Term(body)=ty else{panic!()};assert_eq!(body.expr,ExprId(2));assert_eq!(body.env,EnvFrame::empty(),"a literal Sort has no term-binder occurrence to substitute");assert_eq!(body.levels,LevelSubstitution::new(vec![(NameId(13),level)]));}
  for id in[6,10]{assert!(c.infer_exact_closure_in_context(&c.closure(ExprId(id),EnvFrame::empty()),&[],&mut 4096,0).is_none(),"argument must be independently checked before preserving a constant codomain");}
 }
}

#[cfg(test)]
mod active_bound_type_sort_controls {
 use super::*;
 use crate::environment::ConstantDecl;
 #[test]
 fn recorded_type_alias_exposes_sort_without_confusing_proofs_or_data(){
  let mut e=IdTable::default();for(i,n)in[(0,Expr::Sort(LevelId(0))),(1,Expr::Sort(LevelId(1))),(2,Expr::Sort(LevelId(2))),(3,Expr::Sort(LevelId(3))),(4,Expr::BVar(0)),(5,Expr::Pi{domain:ExprId(3),body:ExprId(3)}),(6,Expr::Lam{domain:ExprId(3),body:ExprId(4)}),(7,Expr::Const{name:NameId(1),levels:vec![LevelId(2)]}),(8,Expr::App{fun:ExprId(7),arg:ExprId(2)}),(9,Expr::Const{name:NameId(2),levels:vec![]}),(10,Expr::Lam{domain:ExprId(9),body:ExprId(1)}),(11,Expr::App{fun:ExprId(10),arg:ExprId(1)})]{e.insert(ExprId(i),n).unwrap();}
  let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();l.insert(LevelId(2),Level::Param(NameId(9))).unwrap();l.insert(LevelId(3),Level::Succ(LevelId(2))).unwrap();let env=Environment::empty().extend(NameId(1),ConstantDecl::definition(vec![NameId(9)],ExprId(5),ExprId(6),true)).unwrap().extend(NameId(2),ConstantDecl::axiom(vec![],ExprId(1))).unwrap();
  let c=TypeChecker::with_level_substitution(&e,&l,&env,HashMap::from([(NameId(9),succ(LevelTerm::Zero))])).strict_certificate_probe();let empty=EnvFrame::empty();
  for level in [LevelTerm::Zero,succ(LevelTerm::Zero)] {
   let domain=Closure::with_levels(ExprId(8),empty.clone(),LevelSubstitution::new(vec![(NameId(9),level.clone())]));assert!(c.shared_strict_source_sort(&domain,&[],&mut 4096).is_some());let ty=TypeValue::Term(domain);let gamma=vec![ty.clone()];let owner=empty.extend_free(FreeId(0));c.retain_checked_binding(&owner,ty.clone(),&gamma);let source=c.closure(ExprId(4),owner.clone());assert!(c.checked_bound_literal_sort(&source,&gamma,&mut 512).is_none(),"outside active formation retain the literal-only candidate policy");
   {let _active=GeneralDomainFormationOwner::enter();assert_eq!(c.checked_bound_literal_sort(&source,&gamma,&mut 512),Some(level));assert!(c.checked_bound_literal_sort(&source,&[],&mut 512).is_none());assert!(c.checked_bound_literal_sort(&source,&gamma,&mut 0).is_none());let wrapper=owner.extend_neutral(Neutral{head:NeutralHead::Free(FreeId(0),Some(owner.clone())),spine:vec![]});c.retain_checked_binding(&wrapper,ty,&gamma);let wrapped=c.closure(ExprId(4),wrapper.clone());c.checked_binding_lineage.borrow_mut().insert(wrapper.id(),None);assert!(c.checked_bound_literal_sort(&wrapped,&gamma,&mut 512).is_none());c.checked_binding_lineage.borrow_mut().insert(owner.id(),None);assert!(c.checked_bound_literal_sort(&source,&gamma,&mut 512).is_none());}
  }
  let p=empty.extend_free(FreeId(0));let prop=TypeValue::Term(c.closure(ExprId(0),empty.clone()));let mut gamma=vec![prop.clone()];c.retain_checked_binding(&p,prop,&gamma);let hty=TypeValue::Term(c.closure(ExprId(4),p.clone()));let h=p.extend_free(FreeId(1));gamma.push(hty.clone());c.retain_checked_binding(&h,hty,&gamma);let nat=TypeValue::Term(c.closure(ExprId(9),empty.clone()));let n=empty.extend_free(FreeId(0));c.retain_checked_binding(&n,nat.clone(),&[nat.clone()]);let _active=GeneralDomainFormationOwner::enter();assert!(c.checked_bound_literal_sort(&c.closure(ExprId(4),h),&gamma,&mut 512).is_none(),"h:p is a proof, although p:Prop; its actual TYPE p is not Sort");assert!(c.checked_bound_literal_sort(&c.closure(ExprId(4),n),&[nat],&mut 512).is_none());assert!(!c.checked_parameter_telescope_equivalence(&[ExprId(1)],&[&[ExprId(11)]],&mut 4096),"original malformed beta-erased domain cannot earn a binder witness");
 }
}

#[cfg(test)]
mod owned_prop_field_telescope_controls {
 use super::*;
 use crate::environment::ConstantDecl;
 #[test]
 fn only_independently_typed_proof_fields_receive_owned_introductions(){
  let mut e=IdTable::default();let mut l=IdTable::default();
  l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(i,node)in[(0,Expr::Sort(LevelId(0))),(1,Expr::Sort(LevelId(1))),(2,Expr::BVar(0)),(3,Expr::BVar(1)),(4,Expr::Const{name:NameId(1),levels:vec![]}),(5,Expr::Lam{domain:ExprId(4),body:ExprId(3)}),(6,Expr::App{fun:ExprId(5),arg:ExprId(0)}),(7,Expr::BVar(99))]{e.insert(ExprId(i),node).unwrap();}
  let env=Environment::empty().extend(NameId(1),ConstantDecl::axiom(vec![],ExprId(1))).unwrap();let c=TypeChecker::new(&e,&l,&env);
  let p=[ExprId(0)];
  assert!(c.checked_prop_field_telescope(&p,&p,&[ExprId(2),ExprId(3)],&mut 65536),"both proof fields refer to the actual preceding P:Prop under its original owned context");
  for field in [ExprId(0),ExprId(1),ExprId(4),ExprId(6),ExprId(7)] {assert!(!c.checked_prop_field_telescope(&p,&p,&[field],&mut 65536),"data, type, dangling, or beta-erased ill-typed field cannot qualify as a proof: {field:?}");}
  assert!(!c.checked_prop_field_telescope(&p,&[ExprId(1)],&[ExprId(2)],&mut 65536),"the actual constructor parameter must independently form and match the expected parameter");
  assert!(!c.checked_prop_field_telescope(&p,&p,&[ExprId(2)],&mut 0));
  c.checked_binding_lineage.borrow_mut().insert(EnvFrame::empty().id(),None);
  assert!(!c.checked_prop_field_telescope(&p,&p,&[ExprId(2)],&mut 65536),"revoked original source scopes cannot form a new checked telescope");
 }
}

#[cfg(test)]
mod completed_pi_lift_tests {
 use super::*;
 #[test] fn lift_conversion_checks_used_original_and_current_wrapper_authority(){
  let mut e=IdTable::default();let mut l=IdTable::default();let env=Environment::empty();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(i,n)in[(0,Expr::BVar(0)),(1,Expr::BVar(1)),(2,Expr::Pi{domain:ExprId(0),body:ExprId(1)}),(3,Expr::Pi{domain:ExprId(0),body:ExprId(1)}),(4,Expr::Sort(LevelId(1)))]{e.insert(ExprId(i),n).unwrap();}
  for original in[false,true]{
   let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let ty=TypeValue::Term(c.closure(ExprId(4),EnvFrame::empty()));let gamma=vec![ty.clone()];let owner=EnvFrame::empty().extend_free(FreeId(0));c.retain_checked_binding(&owner,ty.clone(),&gamma);
   let alias=EnvFrame::empty().extend_neutral(Neutral{head:NeutralHead::Free(FreeId(0),Some(owner.clone())),spine:vec![]});c.retain_checked_binding(&alias,ty,&gamma);
   assert!(c.complete_ast_lift(ExprId(0),ExprId(1),&mut 128));c.completed_pi_lifts.borrow_mut().insert((ExprId(0),ExprId(1)));
   let a=TypeValue::Term(c.closure(ExprId(2),owner.clone()));let b=TypeValue::Term(c.closure(ExprId(3),alias.clone()));
   let compare=|budget|crate::convert::convert_with_policy_in_context(&c,&a,&b,budget,crate::convert::DeltaPolicy::PreferredOnly,1,&gamma);
   assert!(compare(4096).is_proven());assert!(!compare(0).is_proven());
   c.checked_binding_lineage.borrow_mut().insert(if original{owner.id()}else{alias.id()},None);assert!(!c.source_used_capture_authority_available(&c.closure(ExprId(0),alias),&mut 4096),"the new lift continuation must decline its independent USED-authority premise after either revocation; existing value reflexivity has no typing premise");
  }
 }

 #[test] fn lift_tracks_nested_cutoffs_lets_and_projection_metadata(){
  let mut e=IdTable::default();let l=IdTable::default();let env=Environment::empty();
  for(i,n)in[(0,Expr::BVar(0)),(1,Expr::BVar(1)),(2,Expr::BVar(2)),(3,Expr::Const{name:NameId(1),levels:vec![]}),(4,Expr::Const{name:NameId(1),levels:vec![]}),(5,Expr::App{fun:ExprId(0),arg:ExprId(1)}),(6,Expr::App{fun:ExprId(0),arg:ExprId(2)}),(7,Expr::Lam{domain:ExprId(0),body:ExprId(5)}),(8,Expr::Lam{domain:ExprId(1),body:ExprId(6)}),(9,Expr::Pi{domain:ExprId(0),body:ExprId(5)}),(10,Expr::Pi{domain:ExprId(1),body:ExprId(6)}),(11,Expr::Let{ty:ExprId(0),value:ExprId(3),body:ExprId(5)}),(12,Expr::Let{ty:ExprId(1),value:ExprId(3),body:ExprId(6)}),(13,Expr::Proj{type_name:NameId(2),index:0,structure:ExprId(0)}),(14,Expr::Proj{type_name:NameId(2),index:0,structure:ExprId(1)}),(15,Expr::Proj{type_name:NameId(2),index:1,structure:ExprId(1)}),(16,Expr::Proj{type_name:NameId(3),index:0,structure:ExprId(1)}),(17,Expr::App{fun:ExprId(17),arg:ExprId(0)}),(18,Expr::App{fun:ExprId(18),arg:ExprId(1)})]{e.insert(ExprId(i),n).unwrap();}
  let c=TypeChecker::new(&e,&l,&env);
  for(a,b)in[(0,1),(7,8),(9,10),(11,12),(13,14),(3,3)]{assert!(c.complete_ast_lift(ExprId(a),ExprId(b),&mut 128),"{a}/{b}");}
  for(a,b)in[(0,0),(7,7),(13,15),(13,16),(3,4),(17,18),(0,99)]{assert!(!c.complete_ast_lift(ExprId(a),ExprId(b),&mut 128),"{a}/{b}");}
  assert!(!c.complete_ast_lift(ExprId(7),ExprId(8),&mut 1));
 }
 #[test] fn completed_publication_is_bounded_and_queries_preserve_exact_source_environment_and_theta(){
  let mut e=IdTable::default();let l=IdTable::default();let env=Environment::empty();e.insert(ExprId(0),Expr::BVar(0)).unwrap();e.insert(ExprId(1),Expr::BVar(1)).unwrap();e.insert(ExprId(2),Expr::App{fun:ExprId(0),arg:ExprId(0)}).unwrap();e.insert(ExprId(3),Expr::App{fun:ExprId(1),arg:ExprId(1)}).unwrap();let c=TypeChecker::new(&e,&l,&env);
  c.discover_completed_pi_lift(ExprId(2),ExprId(3),&[0],&[1],&mut 2);assert!(c.completed_pi_lifts.borrow().is_empty(),"partial work publishes nothing");
  c.discover_completed_pi_lift(ExprId(2),ExprId(3),&[0],&[2],&mut 32);assert!(c.completed_pi_lifts.borrow().is_empty(),"capture-gap mismatch has no certificate");
  c.discover_completed_pi_lift(ExprId(2),ExprId(3),&[0],&[1],&mut 32);
  let a=c.closure(ExprId(2),EnvFrame::empty());let b=a.sibling(ExprId(3),a.env.clone());assert!(c.completed_pi_lift_for_source(&a,&b,&mut 1));assert!(!c.completed_pi_lift_for_source(&a,&b,&mut 0));
  let different=b.sibling(b.expr,EnvFrame::empty().extend_free(FreeId(0)));assert!(!c.completed_pi_lift_for_source(&a,&different,&mut 8));
  let theta=Closure::with_levels(b.expr,b.env.clone(),LevelSubstitution::new(vec![(NameId(9),LevelTerm::Zero)]));assert!(!c.completed_pi_lift_for_source(&a,&theta,&mut 8));
  for i in 10..4105{c.completed_pi_lifts.borrow_mut().insert((ExprId(i),ExprId(i+1)));}assert_eq!(c.completed_pi_lifts.borrow().len(),4096);assert!(c.completed_pi_lift_for_source(&a,&b,&mut 1));
  c.discover_completed_pi_lift(ExprId(1),ExprId(0),&[1],&[2],&mut 32);assert_eq!(c.completed_pi_lifts.borrow().len(),4096);
 }
}

#[cfg(test)]
mod captured_cell_constant_tests {
 use super::*;
 fn setup()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(i,n)in[(0,Expr::BVar(0)),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::Const{name:NameId(2),levels:vec![]}),(3,Expr::Const{name:NameId(3),levels:vec![]}),(4,Expr::Const{name:NameId(1),levels:vec![LevelId(0)]}),(5,Expr::Lam{domain:ExprId(1),body:ExprId(0)}),(6,Expr::Const{name:NameId(4),levels:vec![]}),(7,Expr::Sort(LevelId(1))),(8,Expr::Const{name:NameId(1),levels:vec![]}),(9,Expr::BVar(1))]{e.insert(ExprId(i),n).unwrap();}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(7))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![],ExprId(7))).unwrap().extend(NameId(3),crate::environment::ConstantDecl::axiom(vec![NameId(9)],ExprId(7))).unwrap();(e,l,env)
 }
 #[test] fn monomorphic_actual_payload_keeps_own_theta_and_ignores_only_unused_constant_scope(){
  let(e,l,env)=setup();let c=TypeChecker::new(&e,&l,&env);let payload=c.closure(ExprId(1),EnvFrame::empty().extend_free(FreeId(8)));let wrapper=EnvFrame::empty().extend(payload.clone());let source=c.closure(ExprId(0),wrapper.clone());let (eligible,actual)=c.paid_source_substitution_payload(&source,0);assert!(eligible);assert_eq!(actual,Some(payload.clone()));
  let right=Closure::with_levels(ExprId(8),EnvFrame::empty(),LevelSubstitution::new(vec![(NameId(99),LevelTerm::Zero)]));assert!(c.same_monomorphic_source_constant(actual.as_ref().unwrap(),&right,&mut 1));assert!(!c.same_monomorphic_source_constant(&payload,&right,&mut 0));
  let result=crate::convert::convert(&c,&TypeValue::Term(source),&TypeValue::Term(right),3);assert!(result.is_proven(),"one compare step, already-paid actual cell lookup and literal global constant equality: {result:?}");
 }
 #[test] fn explicit_levels_missing_params_different_constants_and_nonclosure_cells_decline(){
  let(e,l,env)=setup();let c=TypeChecker::new(&e,&l,&env);let a=c.closure(ExprId(1),EnvFrame::empty());
  for id in[2,3,4,5,6]{assert!(!c.same_monomorphic_source_constant(&a,&c.closure(ExprId(id),EnvFrame::empty()),&mut 64));}
  let poly=c.closure(ExprId(3),EnvFrame::empty());assert!(!c.same_monomorphic_source_constant(&poly,&poly,&mut 64),"missing supplied parameters cannot be certified monomorphic");let missing=c.closure(ExprId(6),EnvFrame::empty());assert!(!c.same_monomorphic_source_constant(&missing,&missing,&mut 64));
  for frame in[EnvFrame::empty(),EnvFrame::empty().extend_free(FreeId(0)),EnvFrame::empty().extend_neutral(Neutral{head:NeutralHead::Free(FreeId(0),None),spine:vec![]})]{assert!(!c.paid_source_substitution_payload(&c.closure(ExprId(0),frame),0).0);}
  let lambda=c.closure(ExprId(5),EnvFrame::empty());let source=c.closure(ExprId(0),EnvFrame::empty().extend(lambda));let (_,actual)=c.paid_source_substitution_payload(&source,0);assert!(!c.same_monomorphic_source_constant(actual.as_ref().unwrap(),&a,&mut 64));
 }
 #[test] fn original_cell_current_wrapper_and_stored_payload_revocation_decline(){
  let(e,l,env)=setup();let c=TypeChecker::new(&e,&l,&env);let payload=c.closure(ExprId(1),EnvFrame::empty().extend_free(FreeId(7)));let original=EnvFrame::empty().extend(payload.clone());let wrapper=original.extend_free(FreeId(9));let source=c.closure(ExprId(0),original.clone());
  assert!(c.paid_source_substitution_payload(&source,0).1.is_some());
  c.checked_binding_lineage.borrow_mut().insert(original.id(),None);assert!(c.paid_source_substitution_payload(&source,0).0);assert!(c.paid_source_substitution_payload(&source,0).1.is_none());c.checked_binding_lineage.borrow_mut().remove(&original.id());
  let outer=c.closure(ExprId(9),wrapper.clone());c.checked_binding_lineage.borrow_mut().insert(wrapper.id(),None);assert!(c.paid_source_substitution_payload(&outer,1).1.is_none());c.checked_binding_lineage.borrow_mut().remove(&wrapper.id());
  c.checked_binding_lineage.borrow_mut().insert(payload.env.id(),None);assert!(c.paid_source_substitution_payload(&source,0).1.is_none());
 }
}

#[cfg(test)]
mod original_fixed_owner_tests {
 use super::*;
 #[test] fn completed_existing_binder_keeps_original_owned_body(){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();e.insert(ExprId(0),Expr::Sort(LevelId(1))).unwrap();e.insert(ExprId(1),Expr::Const{name:NameId(1),levels:vec![]}).unwrap();e.insert(ExprId(2),Expr::BVar(0)).unwrap();let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();
  for domain in[0,1]{let d=c.closure(ExprId(domain),EnvFrame::empty());let actual=EnvFrame::empty().extend_free(FreeId(0));let other=EnvFrame::empty().extend_free(FreeId(0));let gamma=Rc::new(vec![]);c.retain_checked_binding(&actual,TypeValue::Term(d.clone()),&[TypeValue::Term(d.clone())]);let lb=TypeValue::Term(c.closure(ExprId(2),actual.clone()));let rb=TypeValue::Term(c.closure(ExprId(2),other.clone()));
  let _active=GeneralDomainFormationOwner::enter();
  crate::convert::with_completed_domain_pair_for_test(&c,&d,&d,&gamma,|p|{let (left,right)=c.checked_fixed_pi_joint_bodies(p,&d,&d,&lb,&rb,FreeId(0),FreeId(0),&actual,&other,&gamma,FreeId(0),&mut 1024).unwrap();assert_eq!(left,lb,"a checked original binder must remain the same nominal owner");let TypeValue::Term(right)=right else{panic!()};let v=c.machine().expose(right,Transparency::Reducible,64);assert!(matches!(v.proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Free(FreeId(0),Some(owner)),spine})) if owner==&actual&&spine.is_empty()));});
 }}
 #[test] fn old_owner_is_not_reused_across_a_different_full_gamma(){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();for(i,n)in[(0,Expr::Sort(LevelId(1))),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::BVar(0)),(3,Expr::Const{name:NameId(2),levels:vec![]})]{e.insert(ExprId(i),n).unwrap();}let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let outer=c.closure(ExprId(1),EnvFrame::empty());let parent=EnvFrame::empty().extend_free(FreeId(0));let d=c.closure(ExprId(1),parent.clone());let owner=parent.extend_free(FreeId(1));let other=EnvFrame::empty().extend_free(FreeId(1));c.retain_checked_binding(&parent,TypeValue::Term(outer.clone()),&[TypeValue::Term(outer.clone())]);c.retain_checked_binding(&owner,TypeValue::Term(d.clone()),&[TypeValue::Term(outer),TypeValue::Term(d.clone())]);let lb=TypeValue::Term(c.closure(ExprId(2),owner.clone()));let rb=TypeValue::Term(c.closure(ExprId(2),other.clone()));let changed=Rc::new(vec![TypeValue::Term(c.closure(ExprId(3),EnvFrame::empty()))]);
  crate::convert::with_completed_domain_pair_for_test(&c,&d,&d,&changed,|p|{let out=c.checked_fixed_pi_joint_bodies(p,&d,&d,&lb,&rb,FreeId(1),FreeId(1),&owner,&other,&changed,FreeId(1),&mut 4096);assert!(out.is_none_or(|(left,_)|left!=lb),"matching last domain and numeric binder do not license original scope reuse");});
 }
 #[test] fn used_body_only_revocation_and_original_owner_revocation_decline(){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();for(i,n)in[(0,Expr::Sort(LevelId(1))),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::BVar(2))]{e.insert(ExprId(i),n).unwrap();}let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap();
  for original in[false,true]{let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let closed=TypeValue::Term(c.closure(ExprId(0),EnvFrame::empty()));let bad=EnvFrame::empty().extend_free(FreeId(0));let parent=bad.extend_free(FreeId(1));let owner=parent.extend_free(FreeId(2));let other=parent.extend_free(FreeId(2));let d=c.closure(ExprId(0),parent.clone());let gamma=Rc::new(vec![closed.clone(),closed.clone()]);c.retain_checked_binding(&bad,closed.clone(),&gamma[..1]);c.retain_checked_binding(&parent,closed,&gamma);let mut full=(*gamma).clone();full.push(TypeValue::Term(d.clone()));c.retain_checked_binding(&owner,TypeValue::Term(d.clone()),&full);let lb=TypeValue::Term(c.closure(ExprId(2),owner.clone()));let rb=TypeValue::Term(c.closure(ExprId(2),other.clone()));c.checked_binding_lineage.borrow_mut().insert(if original{owner.id()}else{bad.id()},None);
   crate::convert::with_completed_domain_pair_for_test(&c,&d,&d,&gamma,|p|{assert!(c.checked_fixed_pi_joint_bodies(p,&d,&d,&lb,&rb,FreeId(2),FreeId(2),&owner,&other,&gamma,FreeId(2),&mut 4096).is_none());});
  }
 }
 #[test] fn equal_beta_erasure_does_not_certify_ill_typed_right_domain(){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();for(i,n)in[(0,Expr::Sort(LevelId(1))),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::BVar(0)),(3,Expr::Lam{domain:ExprId(1),body:ExprId(0)}),(4,Expr::App{fun:ExprId(3),arg:ExprId(0)})]{e.insert(ExprId(i),n).unwrap();}let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let left=c.closure(ExprId(0),EnvFrame::empty());let right=c.closure(ExprId(4),EnvFrame::empty());let owner=EnvFrame::empty().extend_free(FreeId(0));let other=EnvFrame::empty().extend_free(FreeId(0));let gamma=Rc::new(vec![]);c.retain_checked_binding(&owner,TypeValue::Term(left.clone()),&[TypeValue::Term(left.clone())]);let lb=TypeValue::Term(c.closure(ExprId(2),owner.clone()));let rb=TypeValue::Term(c.closure(ExprId(2),other.clone()));
  crate::convert::with_completed_domain_pair_for_test(&c,&left,&right,&gamma,|p|{assert!(c.checked_fixed_pi_joint_bodies(p,&left,&right,&lb,&rb,FreeId(0),FreeId(0),&owner,&other,&gamma,FreeId(0),&mut 4096).is_none());assert!(c.checked_fixed_pi_joint_bodies(p,&left,&right,&lb,&rb,FreeId(0),FreeId(0),&owner,&other,&gamma,FreeId(0),&mut 0).is_none());});
 }

}

#[cfg(test)]
mod certified_nat_local_controls {
 use super::*;use crate::environment::{ConstantDecl,NatPrimitives};
 #[test] fn certified_nat_locals_keep_original_owners_and_context(){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(i,v)in[(0,Expr::Sort(LevelId(1))),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::BVar(1)),(3,Expr::BVar(0)),(4,Expr::Pi{domain:ExprId(1),body:ExprId(1)})]{e.insert(ExprId(i),v).unwrap();}
  let base=Environment::empty().extend(NameId(1),ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),ConstantDecl::axiom(vec![],ExprId(1))).unwrap().extend(NameId(3),ConstantDecl::axiom(vec![],ExprId(4))).unwrap().extend(NameId(4),ConstantDecl::axiom(vec![],ExprId(0))).unwrap();
  let env=base.install_nat_primitives(NatPrimitives{type_name:NameId(1),type_expr:ExprId(1),zero:NameId(2),succ:NameId(3),recursor:NameId(4),add:None,mul:None,pow:None,land:None,shift_right:None,div:None,modulo:None,sub:None,pred:None,virtual_bvar_zero:Some(ExprId(3)),ble:None,beq:None}).unwrap();
  for(qualified,env)in[(true,env),(false,base)]{
   let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let nat=TypeValue::Term(c.closure(ExprId(1),EnvFrame::empty()));let x=EnvFrame::empty().extend_free(FreeId(0));let y=x.extend_free(FreeId(1));let gamma=vec![nat.clone(),nat.clone()];c.retain_checked_binding(&x,nat.clone(),&gamma[..1]);c.retain_checked_binding(&y,nat,&gamma);
   let a=c.closure(ExprId(2),y.clone());let b=c.closure(ExprId(3),y.clone());let av=Value::Neutral(Neutral{head:NeutralHead::Free(FreeId(0),Some(x.clone())),spine:vec![]});let bv=Value::Neutral(Neutral{head:NeutralHead::Free(FreeId(1),Some(y.clone())),spine:vec![]});
   let relation=c.checked_source_structure_relation(&a,&b,&av,&bv,&gamma,&mut 4096);
   if qualified{assert!(relation.is_some_and(|r|r.is_refuted()),"distinct independently typed qualified Nat locals are rigid data");}else{assert!(relation.is_none(),"a matching name without the qualified Nat interface is insufficient");}
   assert!(c.checked_source_structure_relation(&a,&a,&av,&av,&gamma,&mut 4096).is_none());assert!(c.checked_source_structure_relation(&a,&b,&av,&bv,&[],&mut 4096).is_none());assert!(c.checked_source_structure_relation(&a,&b,&av,&bv,&gamma,&mut 0).is_none());
   let forged=Value::Neutral(Neutral{head:NeutralHead::Free(FreeId(1),Some(EnvFrame::empty().extend_free(FreeId(1)))),spine:vec![]});assert!(c.checked_source_structure_relation(&a,&b,&av,&forged,&gamma,&mut 4096).is_none());
   c.checked_binding_lineage.borrow_mut().insert(x.id(),None);assert!(c.checked_source_structure_relation(&a,&b,&av,&bv,&gamma,&mut 4096).is_none());
  }
 }
}

#[cfg(test)]
mod derived_pi_context_controls {
 use super::*;
 #[test] fn actual_checked_application_carries_pi_formation_and_declines_invalid_arguments_and_owners(){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(i,n)in[(0,Expr::Sort(LevelId(0))),(1,Expr::Sort(LevelId(1))),(2,Expr::BVar(0)),(3,Expr::Pi{domain:ExprId(1),body:ExprId(1)}),(4,Expr::Lam{domain:ExprId(1),body:ExprId(2)}),(5,Expr::Pi{domain:ExprId(3),body:ExprId(1)}),(6,Expr::Const{name:NameId(1),levels:vec![]}),(7,Expr::App{fun:ExprId(6),arg:ExprId(4)}),(8,Expr::Lam{domain:ExprId(1),body:ExprId(1)}),(9,Expr::App{fun:ExprId(6),arg:ExprId(8)}),(10,Expr::App{fun:ExprId(4),arg:ExprId(1)}),(11,Expr::App{fun:ExprId(6),arg:ExprId(10)})]{e.insert(ExprId(i),n).unwrap();}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(5))).unwrap();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let empty=EnvFrame::empty();
  assert!(c.infer_exact_closure_in_context(&c.closure(ExprId(7),empty.clone()),&[],&mut 8192,0).is_some());
  for bad in[9,11]{assert!(c.infer_exact_closure_in_context(&c.closure(ExprId(bad),empty.clone()),&[],&mut 8192,0).is_none(),"wrong codomain universe or beta-erased ill-typed source argument: {bad}");}
  let subject=c.closure(ExprId(4),empty.clone());let left=c.infer_exact_closure_in_context(&subject,&[],&mut 8192,0).unwrap();let right=TypeValue::Term(c.closure(ExprId(3),empty));assert!(c.owned_inferred_type_formation_sort(&right,&[],&mut 8192,0).is_some());
  assert!(c.compare_derived_fixed_pi_types(&left,&right,&[],&mut 8192,0).unwrap().is_proven());assert!(c.compare_derived_fixed_pi_types(&left,&right,&[],&mut 0,0).is_none());assert!(c.compare_derived_fixed_pi_types(&left,&right,&[TypeValue::Sort(LevelTerm::Zero)],&mut 8192,0).is_none());
  let TypeValue::Pi{binder_owner:Some(owner),..}=&left else{panic!()};c.checked_binding_lineage.borrow_mut().insert(owner.id(),None);assert!(c.compare_derived_fixed_pi_types(&left,&right,&[],&mut 8192,0).is_none());
  let ordinary=TypeChecker::new(&e,&l,&env);assert!(ordinary.compare_derived_fixed_pi_types(&left,&right,&[],&mut 8192,0).is_none(),"a legacy inference route cannot create this formation premise");
 }
}

#[cfg(test)]
mod substituted_pi_scope_controls {
 use super::*;
 #[test] fn applied_polymorphic_lambda_retains_a_formed_result_pi_in_actual_context(){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(i,n)in[(0,Expr::Sort(LevelId(1))),(1,Expr::BVar(0)),(2,Expr::Lam{domain:ExprId(1),body:ExprId(1)}),(3,Expr::Lam{domain:ExprId(0),body:ExprId(2)}),(4,Expr::Const{name:NameId(1),levels:vec![]}),(5,Expr::App{fun:ExprId(3),arg:ExprId(4)})]{e.insert(ExprId(i),n).unwrap();}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let result=c.infer(ExprId(5),65536);let ty=result.proven_value().expect("checked application of a polymorphic identity");
  assert!(c.owned_inferred_type_formation_sort(ty,&[],&mut 4096,0).is_some(),"the returned dependent Pi must retain its actual checked context after substituting A, rather than an introduction still requiring the eliminated A binder: {ty:?}");
 }
}

#[cfg(test)]
mod typed_substitution_dependency_controls {
 use super::*;
 fn fixture()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(i,n)in[(0,Expr::Sort(LevelId(1))),(1,Expr::BVar(0)),(2,Expr::Lam{domain:ExprId(1),body:ExprId(1)}),(3,Expr::Lam{domain:ExprId(0),body:ExprId(2)}),(4,Expr::Const{name:NameId(1),levels:vec![]}),(5,Expr::App{fun:ExprId(3),arg:ExprId(4)})]{e.insert(ExprId(i),n).unwrap();}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap();(e,l,env)
 }
 #[test] fn derived_pi_keeps_both_original_introduction_dependencies(){
  let(e,l,env)=fixture();
  for revoke_inner in [false,true]{
   let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let original=c.infer(ExprId(3),65536);let TypeValue::Pi{body,binder_owner:Some(outer),..}=original.proven_value().unwrap()else{panic!()};let TypeValue::Pi{binder_owner:Some(inner),..}=&**body else{panic!()};let revoked=if revoke_inner{inner}else{outer};
   let result=c.infer(ExprId(5),65536);let ty=result.proven_value().unwrap();let TypeValue::Pi{binder_owner:Some(new),..}=ty else{panic!()};assert!(c.owned_inferred_type_formation_sort(ty,&[],&mut 4096,0).is_some());assert!(c.checked_binding_lineage.borrow().get(&new.id()).is_some_and(Option::is_some));
   c.checked_binding_lineage.borrow_mut().insert(revoked.id(),None);
   assert!(c.checked_binding_lineage.borrow().get(&new.id()).is_some_and(Option::is_none),"a derived introduction cannot outlive the source proof it substitutes");assert!(c.owned_inferred_type_formation_sort(ty,&[],&mut 4096,0).is_none());
  }
 }
 #[test] fn revocation_is_immediate_even_if_a_mutation_guard_restores_the_original(){
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let original=c.infer(ExprId(3),65536);let TypeValue::Pi{binder_owner:Some(outer),..}=original.proven_value().unwrap()else{panic!()};let result=c.infer(ExprId(5),65536);let TypeValue::Pi{binder_owner:Some(new),..}=result.proven_value().unwrap()else{panic!()};let saved=c.checked_binding_lineage.borrow().get(&outer.id()).unwrap().clone();
  let mut ledger=c.checked_binding_lineage.borrow_mut();ledger.insert(outer.id(),None);assert!(ledger.get(&new.id()).is_some_and(Option::is_none));ledger.insert(outer.id(),saved);assert!(ledger.get(&new.id()).is_some_and(Option::is_none));
 }
 #[test] fn isolated_lineage_copies_preserve_substitution_dependencies(){
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let original=c.infer(ExprId(3),65536);let TypeValue::Pi{binder_owner:Some(outer),..}=original.proven_value().unwrap()else{panic!()};let result=c.infer(ExprId(5),65536);let TypeValue::Pi{binder_owner:Some(new),..}=result.proven_value().unwrap()else{panic!()};
  let isolated=c.checked_binding_lineage.cloned();isolated.borrow_mut().insert(outer.id(),None);assert!(isolated.borrow().get(&new.id()).is_some_and(Option::is_none));assert!(c.checked_binding_lineage.borrow().get(&new.id()).is_some_and(Option::is_some));
 }
 #[test] fn equal_context_types_do_not_replace_actual_caller_frame_identity(){
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let a=TypeValue::Term(c.closure(ExprId(0),EnvFrame::empty()));let gamma=vec![a.clone()];let first=EnvFrame::empty().extend_free(FreeId(0));let second=EnvFrame::empty().extend_free(FreeId(0));c.retain_checked_binding(&first,a.clone(),&gamma);c.retain_checked_binding(&second,a,&gamma);
  let original=c.infer_in(ExprId(3),&gamma,&first,&mut 65536,&mut HashMap::new());let TypeValue::Pi{domain,body,binder,binder_owner,..}=original.proven_value().unwrap()else{panic!()};let actual=c.closure(ExprId(4),second.clone());
  let changed=c.instantiate_checked_fixed_pi_body(body,*binder,binder_owner.as_ref(),domain,&actual,&gamma,&second,&mut 4096).unwrap();assert!(c.owned_inferred_type_formation_sort(&changed,&gamma,&mut 4096,0).is_none(),"the new checked transport must decline a different physical caller; the unchanged legacy result carries no new introduction certificate");
 }
}

#[cfg(test)]
mod evaluated_binding_typing_controls {
 use super::*;
 pub(super) fn fixture()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(i,n)in[(0,Expr::Sort(LevelId(1))),(1,Expr::BVar(0)),(2,Expr::Lam{domain:ExprId(1),body:ExprId(1)}),(3,Expr::Lam{domain:ExprId(0),body:ExprId(2)}),(4,Expr::Const{name:NameId(1),levels:vec![]}),(6,Expr::Const{name:NameId(2),levels:vec![]}),(7,Expr::Pi{domain:ExprId(0),body:ExprId(0)}),(201,Expr::App{fun:ExprId(3),arg:ExprId(0)})]{e.insert(ExprId(i),n).unwrap();}
  let mut last=ExprId(4);for i in 100..160{e.insert(ExprId(i),Expr::App{fun:ExprId(6),arg:last}).unwrap();last=ExprId(i);}e.insert(ExprId(200),Expr::App{fun:ExprId(3),arg:last}).unwrap();
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![],ExprId(7))).unwrap();(e,l,env)
 }
 #[test] fn evaluated_beta_binding_preserves_the_already_checked_argument_type(){
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();assert!(c.infer(ExprId(200),65536).is_proven());let value=c.machine().expose(c.closure(ExprId(200),EnvFrame::empty()),Transparency::Full,4096);let Value::Lam{body,..}=value.proven_value().unwrap()else{panic!()};let reduced=body.sibling(ExprId(2),body.env.clone());
  assert!(c.infer_exact_closure_in_context(&reduced,&[],&mut 8192,0).is_some(),"the original beta argument was source-checked; the evaluator's actual new binding must carry that derivation instead of rediscovering the sixty-application type argument");
 }
 #[test] fn an_erased_ill_typed_beta_argument_does_not_certify_its_reduced_lambda(){
  let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();assert!(!c.infer(ExprId(201),4096).is_proven());let value=c.machine().expose(c.closure(ExprId(201),EnvFrame::empty()),Transparency::Full,4096);let Value::Lam{body,..}=value.proven_value().unwrap()else{panic!()};let reduced=body.sibling(ExprId(2),body.env.clone());
  assert!(c.infer_exact_closure_in_context(&reduced,&[],&mut 4096,0).is_none(),"checking captured source requires the actual beta substitution's annotation and argument premises, even when the reduced lambda by itself looks typable");
 }
}

#[cfg(test)]
mod beta_provenance_lifetime_controls {
 use super::*;
 fn reduced(c:&TypeChecker<'_>,root:Closure)->Closure{let value=c.machine().expose(root,Transparency::Full,128);let Value::Lam{body,..}=value.proven_value().unwrap()else{panic!()};body.sibling(ExprId(2),body.env.clone())}
 #[test] fn a_fresh_strict_probe_cannot_forget_an_invalid_beta_origin(){
  let(e,l,env)=super::evaluated_binding_typing_controls::fixture();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let term=reduced(&c,c.closure(ExprId(201),EnvFrame::empty()));assert!(c.strict_certificate_probe().infer_exact_closure_in_context(&term,&[],&mut 4096,0).is_none());
 }
 #[test] fn evaluator_without_a_cache_keeps_the_actual_source_obligation(){
  let(e,l,env)=super::evaluated_binding_typing_controls::fixture();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let machine=Machine::new(env.authority(),&e,&l,env.definition_bodies());let value=machine.expose(c.closure(ExprId(201),EnvFrame::empty()),Transparency::Full,128);let Value::Lam{body,..}=value.proven_value().unwrap()else{panic!()};let term=body.sibling(ExprId(2),body.env.clone());assert!(c.infer_exact_closure_in_context(&term,&[],&mut 4096,0).is_none());
 }
 #[test] fn binding_interner_capacity_cannot_erase_a_new_source_obligation(){
  let(e,l,env)=super::evaluated_binding_typing_controls::fixture();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();for i in 0..8192{let _=reduced(&c,c.closure(ExprId(201),EnvFrame::empty().extend_free(FreeId(i))));}let term=reduced(&c,c.closure(ExprId(201),EnvFrame::empty()));assert!(c.infer_exact_closure_in_context(&term,&[],&mut 4096,0).is_none());
 }
 #[test] fn an_owned_substitution_preserves_the_actual_evaluator_source_obligation(){
  let(e,l,env)=super::evaluated_binding_typing_controls::fixture();let c=TypeChecker::new(&e,&l,&env).strict_certificate_probe();let original=EnvFrame::empty().extend_free(FreeId(9));let term=reduced(&c,c.closure(ExprId(201),original.clone()));let actual=c.closure(ExprId(4),EnvFrame::empty());let changed=term.substitute_local_free_from_owner(FreeId(9),&original,&actual,&mut 4096).unwrap();assert!(c.infer_exact_closure_in_context(&changed,&[],&mut 4096,0).is_none());
 }
}
