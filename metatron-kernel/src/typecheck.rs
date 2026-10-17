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

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub enum TypeValue {
    Sort(LevelTerm),
    Term(Closure),
    Pi {
        domain: Box<TypeValue>,
        body: Box<TypeValue>,
        /// The lexical local opened when checking the lambda body.
        binder: FreeId,
    },
}

/// A binder admitted after the source-domain type and substituted value
/// were checked. Both the immutable node and the protected source scope
/// must match before the certified type can be reused.
#[derive(Clone, Debug, Eq, PartialEq)]
struct CheckedBinderWitness {
    domain: TypeValue,
    protected_prefix: Vec<TypeValue>,
}

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
enum CheckedFrameRole { InferPi, InferLambda, ExpectedLambda, LambdaIntro, LiteralBeta, Let, ExactPiSubstitution }

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
enum CheckedFrameBinding { Free(FreeId), Actual(Closure) }

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
struct CheckedFrameKey {
    source: ExprId,
    role: CheckedFrameRole,
    parent: u64,
    domain: TypeValue,
    protected_context: Vec<TypeValue>,
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
    source_support: RefCell<HashMap<ExprId, Vec<u64>>>,
    paired_source_support: RefCell<HashMap<(ExprId, ExprId), Vec<(u64, u64)>>>,
    checked_frames: RefCell<HashMap<CheckedFrameKey, EnvFrame>>,
    // Completed pure source-freshness proofs, local to these borrowed immutable
    // source tables. Retained closures pin frame and level allocation identity.
    source_opening_proofs: RefCell<HashMap<(ExprId,u64,usize,FreeId),Closure>>,
    // Closed source types admitted by this checker's actual formation judgment.
    formed_expected: RefCell<std::collections::HashSet<Closure>>,
    lambda_trials: RefCell<LambdaTrialState>,
    checked_binding_lineage: Rc<RefCell<HashMap<u64,Option<CheckedBinderWitness>>>>,
    // Diagnostic-only strictness: a FreeId is typed solely by its checked
    // immutable binder node under the identical protected source scope.
    strict_origin_probe: bool,
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
            source_support: RefCell::new(HashMap::new()),
            paired_source_support: RefCell::new(HashMap::new()),
            checked_frames: RefCell::new(HashMap::new()),
            source_opening_proofs:RefCell::new(HashMap::new()),
            formed_expected: RefCell::new(std::collections::HashSet::new()),
            lambda_trials: RefCell::new(LambdaTrialState::default()),
            checked_binding_lineage: Rc::new(RefCell::new(HashMap::new())),
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
            source_support: RefCell::new(HashMap::new()),
            paired_source_support: RefCell::new(HashMap::new()),
            checked_frames: RefCell::new(HashMap::new()),
            source_opening_proofs:RefCell::new(HashMap::new()),
            formed_expected: RefCell::new(std::collections::HashSet::new()),
            lambda_trials: RefCell::new(LambdaTrialState::default()),
            checked_binding_lineage: Rc::new(RefCell::new(HashMap::new())),
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
        let node=frame.id();
        let witness=CheckedBinderWitness {
            domain,
            protected_prefix:protected_context.to_vec(),
        };
        match self.checked_binding_lineage.borrow_mut().entry(node) {
            Entry::Vacant(v)=>{v.insert(Some(witness));}
            Entry::Occupied(mut o)=>{
                if o.get().as_ref()!=Some(&witness) {
                    // Conflicting records cannot establish a reusable
                    // typing judgment. Do not arbitrarily choose one.
                    o.insert(None);
                }
            }
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
        let retain = |frame: &EnvFrame, domain| {
            if role == CheckedFrameRole::ExactPiSubstitution {
                self.retain_checked_elimination(frame, domain, protected_context);
            } else {
                self.retain_checked_binding(frame, domain, protected_context);
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
        let key = eligible.then(|| CheckedFrameKey {
            source, role:cache_role, parent: parent.id(), domain: domain.clone(),
            protected_context: protected_context.to_vec(), binding: binding.clone(),
            captured_codomain, substitution_lineage_enabled,
            lineage_enabled, strict_origin: self.strict_origin_probe,
        });
        if let Some(key) = &key {
            let existing = self.checked_frames.borrow().get(key).cloned();
            if let Some(frame) = existing {
                let reusable = match self.checked_binding_lineage.borrow().get(&frame.id()) {
                    Some(Some(witness)) => witness.domain == domain
                        && witness.protected_prefix == protected_context,
                    Some(None) => false,
                    None => !lineage_enabled || (role == CheckedFrameRole::ExactPiSubstitution
                        && !substitution_lineage_enabled),
                };
                if reusable {
                    retain(&frame, domain);
                    return frame;
                }
            }
        }
        let frame = match binding {
            CheckedFrameBinding::Free(free) => parent.extend_free(free),
            CheckedFrameBinding::Actual(actual) => parent.extend(actual),
        };
        retain(&frame, domain);
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
        let (node_id,_)=frame.lookup_with_node_id(index)?;
        let proof=self.checked_binding_lineage.borrow()
            .get(&node_id)?.as_ref()?.clone();
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
        match self.expressions.get(term.expr)? {
            Expr::BVar(index) => {
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
                            head: NeutralHead::Free(_), spine,
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
                        head: NeutralHead::Free(free), spine,
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
                let domain_check = crate::convert::convert_with_policy_in_context(
                    self, &argument_ty, &domain, (*remaining).min(512),
                    crate::convert::DeltaPolicy::PreferredOnly,
                    context.len(), context,
                );
                if !domain_check.is_proven() {
                    #[cfg(feature = "diagnostics")]
                    self.record_capture_source_failure(term, context, *remaining, depth, &format!("argument-domain-relation:{domain_check:?}"));
                    return None;
                }
                if !take_step(remaining) {
                    #[cfg(feature = "diagnostics")]
                    self.record_capture_source_failure(term, context, *remaining, depth, "argument-substitution-fuel-exhausted");
                    return None;
                }
                match body {
                    PiBody::Fixed(binder, inferred_body) => {
                        self.instantiate_fixed_pi_body(
                            &inferred_body, binder, &argument, remaining,
                        )
                    }
                    PiBody::Closure(body) => {
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
                    &extended,TypeValue::Term(declared),context,
                );
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
                let allowance = (*remaining).min(1024);
                let mut opening_budget = allowance;
                let safe = crate::convert::source_opening_avoids_capture(
                    self, &source_body, binder, &mut opening_budget,
                );
                *remaining -= allowance - opening_budget;
                if !safe { return None; }
                let mut extended = context.to_vec();
                extended.push(TypeValue::Term(domain.clone()));
                let body_frame=term.env.extend_free(binder);
                self.retain_checked_elimination(
                    &body_frame,TypeValue::Term(domain.clone()),&extended,
                );
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
                    })
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
                                    NeutralHead::Free(_) | NeutralHead::Projection { .. } => {
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
        enum Capture { Free(FreeId), Closure(Closure), Nat(crate::nat::BigNat) }
        fn resolve(checker: &TypeChecker<'_>, term: &Closure, index: u64, remaining: &mut usize) -> Option<Capture> {
            let mut frame = term.env.clone();
            let mut index = index;
            let mut seen = std::collections::HashSet::new();
            loop {
                let cost = usize::try_from(index).ok()?.checked_add(1)?;
                if *remaining < cost { return None }
                *remaining -= cost;
                if !seen.insert((frame.id(), index)) { return None }
                match frame.lookup_binding_ref(index)? {
                    EnvBinding::Free(free) => return Some(Capture::Free(*free)),
                    EnvBinding::Neutral(Neutral { head: NeutralHead::Free(free), spine }) if spine.is_empty() =>
                        return Some(Capture::Free(*free)),
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
                    EnvBinding::Neutral(Neutral { head: NeutralHead::Free(_), spine }) if spine.is_empty() => break,
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
                    (Capture::Free(x), Capture::Free(y)) if x == y => {}
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
            Expr::Lam { domain, body } => {
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
                self.infer_in(*body, &extended, &body_frame, remaining, cache)
                    .map(|body_type| TypeValue::Pi {
                        domain: Box::new(domain_type),
                        body: Box::new(body_type),
                        binder: free,
                    })
            }
            Expr::App { fun, arg } => {
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
                        // The function was checked under a fresh local above, and
                        // the argument was checked against its domain. Re-infer a
                        // literal lambda body in the substituted environment:
                        // its inferred Pi body is open, not a constant codomain.
                        if let PiBody::Fixed(binder, inferred_body) = &body
                            && (!matches!(self.expressions.get(*fun), Some(Expr::Lam { .. }))
                                || self.type_depends_on_free(
                                    inferred_body,
                                    *binder,
                                    (*remaining).min(4096),
                                ) != Some(false))
                            && let Some(instantiated) = self.infer_literal_beta_spine(
                                expression, context, frame, remaining, cache,
                            )
                        {
                            return instantiated;
                        }
                        let result = match body {
                            PiBody::Fixed(binder, inferred_body) => {
                                let actual = self.closure(*arg, frame.clone());
                                let Some(type_value) = self.instantiate_fixed_pi_body(
                                    &inferred_body, binder, &actual, remaining,
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
                                NeutralHead::Const { .. } | NeutralHead::Free(_) | NeutralHead::Projection { .. } => {
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
                TypeValue::Term(expected_body.under_free(free))
            },
            PiBody::Fixed(binder,value) => {
                let Some(reopened) = self.reopen_fixed_pi_body(&value, binder, free, remaining) else {
                    return Judgment::unknown("bidir-lambda-fixed-binder-not-aligned");
                };
                reopened
            },
        };
        let mut extended=context.to_vec();
        extended.push(annotated.clone());
        let body_frame=self.checked_source_frame(
            expression, CheckedFrameRole::ExpectedLambda, frame, annotated,
            &extended, CheckedFrameBinding::Free(free),
        );
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
        // This rule is tried first only with a real formation premise.
        // Successful checking consumes its actual fuel; a declined bounded
        // trial leaves the ordinary inference path its original budget.
        if expected_formed
            && std::env::var_os("NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA").is_some()
            && matches!(self.expressions.get(expression), Some(Expr::Lam { .. }))
        {
            if self.lambda_trials.borrow().active != 0 {
                // Nested formed lambdas are part of this one bounded trial.
                // A declined child exits the trial rather than starting a
                // fresh speculative branch with a restored budget.
                self.lambda_trials.borrow_mut().nested_direct += 1;
                return self.check_expected_lambda_in(expression, expected, context, frame,
                    remaining, conversion_refutation_is_unknown, cache, true);
            }
            if let Some(budget) = self.begin_lambda_trial(*remaining) {
                let mut trial_budget = budget;
                let candidate = self.check_expected_lambda_in(expression, expected, context, frame,
                    &mut trial_budget, conversion_refutation_is_unknown, cache, true);
                self.finish_lambda_trial(budget, trial_budget, candidate.is_proven());
                if candidate.is_proven() {
                    *remaining = remaining.saturating_sub(budget - trial_budget);
                    return Judgment::proven((), "formed-expected-lambda-checking");
                }
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
                        TypeValue::Pi { domain: actual_domain, body: actual_body, binder },
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
                                    },
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
                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_RIGID_PROOF_REJECT").is_some()
                    && matches!(&conversion,Judgment::Refuted{obstruction}
                       if obstruction.0=="rigid-value-constructor-mismatch")
                {
                    use std::sync::atomic::{AtomicUsize,Ordering};
                    static FOUND:AtomicUsize=AtomicUsize::new(0);
                    if FOUND.fetch_add(1,Ordering::Relaxed)<12 {
                        eprintln!(
                          "NUCLEUS_RIGID_PROOF_REJECT:expr={expression:?}:expression_node={:?}:context_len={}:frame={}:remaining={}:actual_type={value:?}:expected_type={expected:?}:rejection={conversion:?}",
                          self.expressions.get(expression),context.len(),frame.id(),*remaining
                        );
                        if let (TypeValue::Term(actual),TypeValue::Term(wanted))=(&value,expected) {
                            let capture = |source:&Closure| {
                                (0..10u64).filter_map(|offset| {
                                    source.env.lookup_with_node_id(offset).map(|(id,element)| {
                                        (offset,id,format!("{element:?}").chars().take(650).collect::<String>())
                                    })
                                }).collect::<Vec<_>>()
                            };
                            eprintln!("NUCLEUS_RIGID_CAPTURE:expr={expression:?}:actual_expr={:?}:expected_expr={:?}:actual_frame={}:expected_frame={}:actual_capture={:?}:expected_capture={:?}",
                                self.expressions.get(actual.expr),self.expressions.get(wanted.expr),
                                actual.env.id(),wanted.env.id(),capture(actual),capture(wanted));
                        }
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
                TypeValue::Pi { domain, body, binder } => Some(
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
            TypeValue::Term(term) => Some(TypeValue::Term(
                term.substitute_local_free(binder, actual, remaining)?
            )),
            TypeValue::Pi { domain, body, binder: inner } => {
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
                })
            }
        }
    }

    // Syntactic support of an inferred type, through its actual closures.
    // Only a proved absence skips substitution. Exhaustion remains conservative.
    fn type_depends_on_free(&self, ty: &TypeValue, free: FreeId, budget: usize) -> Option<bool> {
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
                    NeutralHead::Free(f) => *f == self.free,
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
        Support {
            checker: self,
            free,
            remaining: budget,
            cache: HashMap::new(),
        }
        .ty(ty)
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
            TypeValue::Pi { domain, body, binder } => Some((*domain, PiBody::Fixed(binder, *body))),
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
                && matches!(&local.head,NeutralHead::Free(_))
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
                    PiBody::Fixed(binder,ty) => {
                        let mut f=probe;
                        self.instantiate_fixed_pi_body(&ty,binder,arg,&mut f)
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

    /// Candidate: use kernel proof irrelevance only after *both* neutral
    /// constructor/theorem applications have been independently typed in the
    /// same checked source Γ and their full result propositions converted.
    /// The pilot targets the exact List.Perm nil/refl arity/depth witness.
    /// A name or syntactic head comparison alone never grants equality.
    pub(crate) fn certified_distinct_source_proofs(
        &self,
        left: &Neutral,
        right: &Neutral,
        context: &[TypeValue],
        budget: usize,
        depth: usize,
    ) -> bool {
        if std::env::var_os("NUCLEUS_EXPERIMENTAL_EXACT_PROOF_NEUTRALS").is_none()
            || depth != context.len() || !matches!(depth, 10 | 13) || budget < 1024
            || !matches!((&left.head, &right.head),
                (NeutralHead::Const { .. }, NeutralHead::Const { .. }))
            || left.head == right.head
            || left.spine.is_empty() || right.spine.is_empty()
            || left.spine.len() > 6 || right.spine.len() > 6
        {
            return false;
        }
        let limit = budget.min(2048);
        let prove_type = |proof: &Neutral| -> Option<TypeValue> {
            let NeutralHead::Const { name, levels } = &proof.head else { return None };
            let declaration = self.environment.get(*name)?;
            if levels.len() != declaration.level_params.len() {
                return None;
            }
            let mut ty = TypeValue::Term(Closure::with_levels(
                declaration.ty,
                EnvFrame::empty(),
                LevelSubstitution::new(
                    declaration.level_params.iter().copied()
                        .zip(levels.iter().cloned()).collect(),
                ),
            ));
            for argument in &proof.spine {
                let (domain, codomain) = self.pi_view(
                    Judgment::proven(ty, "exact-source-proof-head"), limit,
                )?;
                let mut remaining = limit;
                let actual = self.infer_exact_closure_in_context(
                    argument, context, &mut remaining, 0,
                )?;
                if !crate::convert::convert_with_policy_in_context(
                    self, &actual, &domain, limit.min(512),
                    crate::convert::DeltaPolicy::PreferredOnly,
                    depth, context,
                ).is_proven() {
                    return None;
                }
                ty = match codomain {
                    PiBody::Fixed(binder, body) => {
                        self.instantiate_fixed_pi_body(
                            &body, binder, argument, &mut remaining,
                        )?
                    }
                    PiBody::Closure(body) => TypeValue::Term(
                        Closure::with_levels(
                            body.expr, body.env.extend(argument.clone()), body.levels,
                        ),
                    ),
                };
            }
            Some(ty)
        };
        let (Some(left_type), Some(right_type)) =
            (prove_type(left), prove_type(right))
        else { return false };
        let formed_proposition = |ty: &TypeValue| match ty {
            TypeValue::Term(closure) => {
                self.checked_captured_prop_type_in_context(
                    closure, context, limit,
                ).is_proven()
            }
            _ => false,
        };
        if !formed_proposition(&left_type) || !formed_proposition(&right_type) {
            return false;
        }
        let equality = crate::convert::convert_with_policy_in_context(
            self, &left_type, &right_type, limit.min(1024),
            crate::convert::DeltaPolicy::PreferredOnly,
            depth, context,
        );
        #[cfg(feature="diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_EXACT_PROOF_NEUTRALS").is_some() {
            eprintln!(
                "NUCLEUS_EXACT_PROOFS:depth={depth}:left={:?}:right={:?}:lhs_type={left_type:?}:rhs_type={right_type:?}:proposition_conversion={equality:?}",
                left.head, right.head,
            );
        }
        equality.is_proven()
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
            NeutralHead::Free(free) => {
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
                PiBody::Fixed(binder, body) => {
                    let mut fuel = budget;
                    self.instantiate_fixed_pi_body(&body, binder, argument, &mut fuel)?
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
                recovered_context=record.protected_prefix;
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
                                source_context=record.protected_prefix;
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
                origin=Some(prefix);
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
            source_support: RefCell::new(HashMap::new()),
            paired_source_support: RefCell::new(HashMap::new()),
            checked_frames: RefCell::new(HashMap::new()),
            source_opening_proofs:RefCell::new(HashMap::new()),
            formed_expected: RefCell::new(std::collections::HashSet::new()),
            lambda_trials: RefCell::new(LambdaTrialState::default()),
            checked_binding_lineage:Rc::new(RefCell::new(
                self.checked_binding_lineage.borrow().clone(),
            )),
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
                                joined=prefix;
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
                candidate = Some(record.protected_prefix);
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
            source_support: RefCell::new(HashMap::new()),
            paired_source_support: RefCell::new(HashMap::new()),
            checked_frames: RefCell::new(HashMap::new()),
            source_opening_proofs:RefCell::new(HashMap::new()),
            formed_expected: RefCell::new(std::collections::HashSet::new()),
            lambda_trials: RefCell::new(LambdaTrialState::default()),
            checked_binding_lineage: Rc::new(RefCell::new(
                self.checked_binding_lineage.borrow().clone(),
            )),
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
            source_support: RefCell::new(HashMap::new()),
            paired_source_support: RefCell::new(HashMap::new()),
            checked_frames: RefCell::new(HashMap::new()),
            source_opening_proofs:RefCell::new(HashMap::new()),
            formed_expected: RefCell::new(std::collections::HashSet::new()),
            lambda_trials: RefCell::new(LambdaTrialState::default()),
            checked_binding_lineage: Rc::new(RefCell::new(
                self.checked_binding_lineage.borrow().clone(),
            )),
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
            NeutralHead::Free(free) => {
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
                PiBody::Fixed(free, body_type) => {
                    let Some(instantiated) = probe.instantiate_fixed_pi_body(
                        &body_type, free, actual_arg, &mut remaining,
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
                PiBody::Fixed(binder, body) => {
                    let mut fuel = budget;
                    let Some(instantiated) = self.instantiate_fixed_pi_body(
                        &body, binder, argument, &mut fuel,
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
                        head: NeutralHead::Free(_),
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
        let mut closure = field.clone();
        let mut arguments = Vec::new();
        let (projection, levels) = loop {
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
            .expose(target_argument, Transparency::Reducible, budget);
        matches!(exposed.proven_value(), Some(Value::Neutral(actual)) if actual == target)
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
    Fixed(FreeId, TypeValue),
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
        };
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
            body: Box::new(source.clone()), binder: FreeId(0) };
        let mut fuel = 128;
        let Some(TypeValue::Pi { domain, body, binder }) = checker.instantiate_fixed_pi_body(
            &shadowed, FreeId(0), &actual, &mut fuel) else { panic!("shadowing must remain supported") };
        assert_eq!(binder, FreeId(0));
        assert_eq!(*body, source, "inner body shadows the source binder");
        assert_eq!(checker.type_depends_on_free(&domain, FreeId(1), 128), Some(true));
        let mut fuel = 0;
        assert!(checker.instantiate_fixed_pi_body(&source, FreeId(0), &actual, &mut fuel).is_none());
        let unsupported = TypeValue::Term(Closure::new(ExprId(0),
            EnvFrame::empty().extend_neutral(Neutral {
                head: NeutralHead::Free(FreeId(0)), spine: vec![actual.clone()],
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
        let fixed = TypeValue::Pi { domain: Box::new(domain.clone()), body: Box::new(domain.clone()), binder: FreeId(0) };
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
    fn failed_nested_lambda_trials_have_shared_bounded_work_and_preserve_ordinary_budget() {
        if std::env::var_os("NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA").is_none() { return; }
        let (mut expressions, levels, environment, _) = fixture();
        let mut value = ExprId(4); // p : A, never a proposition expression
        let mut expected = ExprId(0); // codomain Prop
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
        assert!(!checker.check_formed(value, &expected, 128).is_proven());
        let state = checker.lambda_trials.borrow().clone();
        assert!(state.declined > 0, "the negative must really exercise speculative failure");
        assert!(state.nested_direct > 0, "nested formed lambdas must use their active root trial");
        assert_eq!(state.active, 0);
        assert_eq!(state.spent + state.quota, 128, "reservation must refund only unused trial fuel");
        assert!(state.spent <= 128, "aggregate speculative inference work exceeded quota: started={}, declined={}, spent={}",
            state.started, state.declined, state.spent);
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
        assert!(checker.exact_source_capture_identity(&alias(payload(9)), &payload(9), &mut 128), "actual root alias discards outer BVar level map, preserving the stored lambda map");
        assert!(!checker.exact_source_capture_identity(&alias(payload(10)), &payload(9), &mut 128));
        assert!(!checker.exact_source_capture_identity(&alias(payload(9)), &payload(9), &mut 0));
        let changed = Closure::with_levels(ExprId(3), EnvFrame::empty().extend_free(FreeId(9)),
            LevelSubstitution::new(vec![(NameId(7), LevelTerm::Succ(Box::new(LevelTerm::Zero)))]));
        assert!(!checker.exact_source_capture_identity(&alias(changed), &payload(9), &mut 128));
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
        let left = |id| Closure::new(ExprId(id), EnvFrame::empty().extend_free(FreeId(0)));
        let right = |id, used| Closure::new(ExprId(id), EnvFrame::empty().extend_free(FreeId(used)).extend_free(FreeId(99)));
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
        assert!(!checker.exact_source_capture_identity(&term(4, 1), &term(4, 1), &mut 0));
        assert!(checker.exact_source_capture_identity(&term(4, 1), &term(4, 1), &mut 128), "exhaustion must not memoize incomplete support");
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
        ] {assert!(!crate::convert::source_opening_avoids_capture(&checker,&changed,FreeId(0),&mut 1));}
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(9),&mut 32));
        let collision=Closure::new(ExprId(2),EnvFrame::empty().extend_free(FreeId(0)));
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&collision,FreeId(0),&mut 32));
        for malformed in [Closure::new(ExprId(999),parent.clone()),Closure::new(ExprId(4),parent.clone()),Closure::new(ExprId(2),EnvFrame::empty())] {
            assert!(!crate::convert::source_opening_avoids_capture(&checker,&malformed,FreeId(0),&mut 32));
            assert!(!checker.has_source_opening_proof(&malformed,FreeId(0)));
        }
        let other=TypeChecker::new(&e,&l,&env);assert!(!crate::convert::source_opening_avoids_capture(&other,&body,FreeId(0),&mut 1),"proofs do not cross checker/source scope");
        assert!(crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut 1));
    }
    #[test]
    fn cold_freshness_cost_and_saturation_preserve_original_guard() {
        let(e,l,env)=fixture();let checker=TypeChecker::new(&e,&l,&env);let body=Closure::new(ExprId(1),EnvFrame::empty());
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut 0));
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut 1));
        let mut cold=3;assert!(crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut cold));assert_eq!(cold,0,"cold lookup replaces root step, not additional work");
        for _ in 1..8192 {let distinct=Closure::new(ExprId(1),EnvFrame::empty().extend_free(FreeId(9)));assert!(crate::convert::source_opening_avoids_capture(&checker,&distinct,FreeId(0),&mut 8));}
        assert_eq!(checker.source_opening_proofs.borrow().len(),8192);
        assert!(crate::convert::source_opening_avoids_capture(&checker,&body,FreeId(0),&mut 1));
        let overflow=Closure::new(ExprId(1),EnvFrame::empty().extend_free(FreeId(9)));
        assert!(crate::convert::source_opening_avoids_capture(&checker,&overflow,FreeId(0),&mut 8));
        assert!(!crate::convert::source_opening_avoids_capture(&checker,&overflow,FreeId(0),&mut 1));
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
        let pi=TypeValue::Pi{domain:Box::new(a.clone()),body:Box::new(b),binder:FreeId(0)};
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
