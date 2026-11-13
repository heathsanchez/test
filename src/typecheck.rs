Warning: truncated output (original token count: 88091)
Total output lines: 6633

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
                let mut domain_check = crate::convert::convert_with_policy_in_context(
                    self, &argument_ty, &domain, (*remaining).min(512),
                    crate::convert::DeltaPolicy::PreferredOnly,
                    context.len(), context,
                );
                // A captured proof argument may require source iota inside
                // its proposition type. Retry only after BOTH proposition
                // formations are independently checked in this exact Gamma.
                // The converter still must prove actual type equality; no
                // value equality or proof irrelevance follows from formation.
                if domain_check.is_unknown() && *remaining > 512
                    && std::env::var_os("NUCLEUS_EXPERIMENTAL_FORMED_PROP_DOMAIN_RETRY").is_some()
                    && let (TypeValue::Term(actual), TypeValue::Term(required)) = (&argument_ty, &domain)
                    && self.checked_captured_prop_type_in_context(actual,context,512).is_proven()
                    && self.checked_captured_prop_type_in_context(required,context,512).is_proven()
                {
                    domain_check = crate::convert::convert_with_policy_in_context(
                        self,&argument_ty,&domain,(*remaining).min(2048),
                        crate::convert::DeltaPolicy::PreferredOnly,context.len(),context,
                    );
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_FORMED_PROP_DOMAIN_RETRY").is_some() {
                        use std::sync::atomic::{AtomicUsize,Ordering};
                        static REPORTED:AtomicUsize=AtomicUsize::new(0);
                        if REPORTED.fetch_add(1,Ordering::Relaxed)<24 {
                            eprintln!("NUCLEUS_FORMED_PROP_DOMAIN_RETRY:source={term:?}:context={}:remaining={remaining}:actual={argument_ty:?}:required={domain:?}:result={domain_check:?}",context.len());
                        }
                    }
                }
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
                    let Some(nat) = self.en…48091 tokens truncated…ments = Vec::new();
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
