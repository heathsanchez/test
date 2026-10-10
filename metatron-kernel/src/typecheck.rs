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
    checked_binding_lineage: Rc<RefCell<HashMap<u64,Option<CheckedBinderWitness>>>>,
}

impl<'a> TypeChecker<'a> {
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
            checked_binding_lineage: Rc::new(RefCell::new(HashMap::new())),
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
            checked_binding_lineage: Rc::new(RefCell::new(HashMap::new())),
        }
    }

    pub fn with_delta_policy(mut self, policy: crate::convert::DeltaPolicy) -> Self {
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
        if std::env::var_os("NUCLEUS_EXPERIMENTAL_TYPED_LINEAGE").is_none() {
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
        if std::env::var_os("NUCLEUS_EXPERIMENTAL_TYPED_LINEAGE").is_none(){
            return None;
        }
        let observed=frame.lookup_with_node_id(index);
        let stored=observed.as_ref().and_then(|(id,_)|
            self.checked_binding_lineage.borrow().get(id).cloned()
        );
        #[cfg(feature="diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_FIRST_UNWARRANTED_BINDING").is_some()
            && context.len()==5 && index==2
        {
            use std::sync::atomic::{AtomicUsize,Ordering};
            static FIRST:AtomicUsize=AtomicUsize::new(0);
            if FIRST.fetch_add(1,Ordering::Relaxed)<36 {
                let typed=stored.as_ref().and_then(|r|r.as_ref());
                let separator=typed.and_then(|w|
                    w.protected_prefix.iter().zip(context)
                        .position(|(a,b)|a!=b)
                );
                eprintln!(
                    "NUCLEUS_FIRST_UNWARRANTED_BINDING:frame={}:index={index}:context={}:actual_binding={observed:?}:witness_status={}:prefix_length={:?}:matches_protected_scope={}:first_separator={separator:?}",
                    frame.id(),context.len(),
                    if stored.is_none() {"unregistered"} else if stored.as_ref().is_some_and(|w|w.is_none()) {"conflicted"} else {"checked"},
                    typed.map(|w|w.protected_prefix.len()),
                    typed.is_some_and(|w|context.starts_with(&w.protected_prefix)),
                );
            }
        }
        let (node_id,_)=observed?;
        let proof=stored?.as_ref()?.clone();
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

    pub fn is_type(&self, expression: ExprId, budget: usize) -> Judgment<()> {
        #[cfg(feature = "diagnostics")]
        crate::diagnostics::type_judgment();
        match self.infer(expression, budget) {
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
        }
    }

    /// Establish that `expression` itself inhabits `Prop` (`Sort 0`).
    ///
    /// This remains three-valued: unresolved universe equality or reduction
    /// is not a refutation.
    pub fn is_proposition(&self, expression: ExprId, budget: usize) -> Judgment<()> {
        let mut remaining = budget;
        self.check_in(
            expression,
            &TypeValue::Sort(LevelTerm::Zero),
            &[],
            &EnvFrame::empty(),
            &mut remaining,
            false,
            &mut HashMap::new(),
        )
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
        if depth >= 48 || !take_step(remaining) {
            return None;
        }
        match self.expressions.get(term.expr)? {
            Expr::BVar(index) => match term.env.lookup(*index)? {
                EnvBinding::Free(free) => {
                    context.get(usize::try_from(free.0).ok()?).cloned()
                }
                EnvBinding::Neutral(Neutral {
                    head: NeutralHead::Free(free),
                    spine,
                }) if spine.is_empty() => {
                    context.get(usize::try_from(free.0).ok()?).cloned()
                }
                EnvBinding::Closure(value) => {
                    self.infer_exact_closure_in_context(
                        &value, context, remaining, depth + 1,
                    )
                }
                EnvBinding::Neutral(_) => None,
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
                let (domain, body) = self.pi_view(
                    Judgment::proven(function_ty, "exact-captured-function-type"),
                    (*remaining).min(512),
                )?;
                let argument_ty = self.infer_exact_closure_in_context(
                    &argument, context, remaining, depth + 1,
                )?;
                let domain_check = crate::convert::convert_with_policy_in_context(
                    self, &argument_ty, &domain, (*remaining).min(512),
                    crate::convert::DeltaPolicy::PreferredOnly,
                    context.len(), context,
                );
                if !domain_check.is_proven() || !take_step(remaining) {
                    return None;
                }
                match body {
                    PiBody::Fixed(binder, inferred_body) => {
                        self.instantiate_fixed_pi_body(
                            &inferred_body, binder, &argument, remaining,
                        )
                    }
                    PiBody::Closure(body) => {
                        let extended=body.env.extend(argument);
                        // The argument type and dependent Pi domain were
                        // independently established above. Retain that exact
                        // substitution as a typed environment-node warrant.
                        self.retain_checked_elimination(&extended,domain,context);
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
                let domain_sort = self.sort_level(
                    Judgment::proven(domain_ty, "captured-binder-domain"),
                    (*remaining).min(512),
                ).proven_value()?.clone();
                let binder = FreeId(u64::try_from(context.len()).ok()?);
                let mut extended = context.to_vec();
                extended.push(TypeValue::Term(domain.clone()));
                let body_frame=term.env.extend_free(binder);
                self.retain_checked_elimination(
                    &body_frame,TypeValue::Term(domain.clone()),&extended,
                );
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
            Expr::StrLit(_) => None,
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
        let mut current = neutral.spine.last().cloned();
        let machine = self.machine();
        for step in 0..5 {
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
                Some(Value::Neutral(Neutral {
                    head: NeutralHead::Const { name: inner, .. }, spine,
                })) if self.environment.recursor_reduction(*inner).is_some()
                        && !spine.is_empty() => spine.last().cloned(),
                _ => None,
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

    fn infer_in(
        &self,
        expression: ExprId,
        context: &[TypeValue],
        frame: &EnvFrame,
        remaining: &mut usize,
        cache: &mut HashMap<(ExprId, u64), TypeValue>,
    ) -> Judgment<TypeValue> {
        // Share only certified results inside one public judgment. Frame
        // identity keeps equal syntax under distinct binders separate.
        let key = (expression, frame.id());
        if let Some(value) = cache.get(&key) {
            return if take_step(remaining) {
                Judgment::proven(value.clone(), "shared-expression-inference")
            } else {
                Judgment::unknown("type-inference-budget")
            };
        }
        let result = self.infer_uncached(expression, context, frame, remaining, cache);
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
            Expr::StrLit(_) => Judgment::unknown("string-literal-type-not-qualified"),
            Expr::BVar(index) => {
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
                let body_frame = frame.extend_free(free);
                self.retain_checked_binding(
                    &body_frame,TypeValue::Term(self.closure(*domain,frame.clone())),&extended,
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
                let body_frame = frame.extend_free(free);
                self.retain_checked_binding(&body_frame,domain_type.clone(),&extended);
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
                let Some((domain, body)) = self.pi_view(function_type.clone(), *remaining) else {
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
                match self.check_in(*arg, &domain, context, frame, remaining, true, cache) {
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
                                NeutralHead::Const { .. } => {
                                    return Judgment::unknown(
                                        "projection-dependent-constructor-mismatch",
                                    );
                                }
                                NeutralHead::Free(_) | NeutralHead::Projection { .. } => {
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
                match self.check_in(*value, &established, context, frame, remaining, true, cache) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                }
                let mut extended = context.to_vec();
                extended.push(established.clone());
                let extended_frame = frame.extend(self.closure(*value, frame.clone()));
                self.retain_checked_binding(&extended_frame,established,&extended);
                self.infer_in(*body, &extended, &extended_frame, remaining, cache)
            }
        }
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
        let inferred = self.infer_in(expression, context, frame, remaining, cache);
        match inferred {
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
                            if check.is_proven()
                                && *binder == FreeId(context.len() as u64)
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
                                    if inner_domain_relation.is_proven()
                                        && *inner_binder == FreeId(ext.len() as u64)
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
        }
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
            match self.check_in(arg, &domain, context, frame, remaining, true, cache) {
                Judgment::Proven { .. } => {}
                Judgment::Refuted { obstruction } => {
                    return Some(Judgment::Refuted { obstruction });
                }
                Judgment::Unknown { residual } => return Some(Judgment::Unknown { residual }),
            }
            lexical_context.push(domain.clone());
            lexical_frame = lexical_frame.extend(self.closure(arg, frame.clone()));
            self.retain_checked_binding(&lexical_frame,domain,&lexical_context);
            head = *body;
        }
        Some(self.infer_in(head, &lexical_context, &lexical_frame, remaining, cache))
    }

    /// Unlike a fixed codomain, the body of an inferred lambda Pi may refer
    /// to its opened lexical local even when an outer Let hides the lambda
    /// syntactically. Instantiate only that local, within immutable closures.
    /// Unknown substitution shapes or exhausted fuel never justify acceptance.
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
                    Some(EnvBinding::Neutral(_)) | None => return false,
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
                        | crate::value::EnvBinding::Neutral(_) => return false,
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

    pub(crate) fn machine(&self) -> Machine<'_> {
        Machine::new(
            self.environment.authority(),
            self.expressions,
            self.levels,
            self.environment.definition_bodies(),
        )
        .with_singleton_recursor_reductions(self.environment.singleton_recursor_reductions())
        .with_recursor_reductions(self.environment.recursor_reductions())
        .with_projection_specs(self.environment.projection_specs())
        .with_nat_primitives(self.environment.nat_primitives().cloned())
        .with_bool_primitives(self.environment.bool_primitives().cloned())
        .with_quot_primitives(self.environment.quot_primitives().cloned())
        .with_exposure_cache(self.exposure_cache.clone())
    }

    pub(crate) fn instantiate(&self, level: LevelId, budget: usize) -> Result<LevelTerm, ()> {
        instantiate_level(self.levels, level, &self.level_substitution, budget).map_err(|_| ())
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
