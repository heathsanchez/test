use std::collections::HashMap;
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
        }
    }

    pub fn with_delta_policy(mut self, policy: crate::convert::DeltaPolicy) -> Self {
        self.delta_policy = policy;
        self
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
                context
                    .iter()
                    .rev()
                    .nth(offset)
                    .cloned()
                    .map(|value| Judgment::proven(value, "context-lookup"))
                    .unwrap_or_else(|| Judgment::refuted("unbound-bvar"))
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
                            PiBody::Closure(body) => TypeValue::Term(Closure::with_levels(
                                body.expr,
                                body.env.extend(self.closure(*arg, frame.clone())),
                                body.levels,
                            )),
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
                extended.push(established);
                let extended_frame = frame.extend(self.closure(*value, frame.clone()));
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
                // Exact diagnostic only: separate the domain and dependent body
                // obligations when an inferred Pi is compared with a term that
                // must expose to a Pi. Never change an ACCEPT/REJECT/UNKNOWN.
                #[cfg(feature = "diagnostics")]
                if conversion.is_unknown()
                    && std::env::var_os("NUCLEUS_TRACE_MIXED_PI").is_some()
                    && let (
                        TypeValue::Pi {
                            domain: inferred_domain,
                            body: inferred_body,
                            binder: opened_free,
                        },
                        TypeValue::Term(_),
                    ) = (&value, expected)
                {
                    use std::sync::atomic::{AtomicUsize, Ordering};
                    static MIXED_PROBES: AtomicUsize = AtomicUsize::new(0);
                    if MIXED_PROBES.fetch_add(1, Ordering::Relaxed) < 12 {
                        let budget = (*remaining).min(512);
                        let exposed = self.pi_view(
                            Judgment::proven(expected.clone(), "mixed-pi-expected"),
                            budget,
                        );
                        if let Some((expected_domain, expected_body)) = exposed {
                        let domain_result = crate::convert::convert_with_policy_in_context(
                            self,
                            inferred_domain,
                            &expected_domain,
                            budget,
                            self.delta_policy,
                            context.len(),
                            context,
                        );
                        let normalized_expected_body = match expected_body {
                            PiBody::Fixed(_other_binder, value) => value,
                            PiBody::Closure(closure) => TypeValue::Term(
                                closure.under_free(*opened_free),
                            ),
                        };
                        let mut extended = context.to_vec();
                        extended.push((**inferred_domain).clone());
                        let body_result = crate::convert::convert_with_policy_in_context(
                            self,
                            inferred_body,
                            &normalized_expected_body,
                            budget,
                            self.delta_policy,
                            context.len() + 1,
                            &extended,
                        );
                        eprintln!(
                            "NUCLEUS_MIXED_PI:expr={expression:?}:context={}:binder={:?}:expected_pi=present:domain={domain_result:?}:body={body_result:?}:original={conversion:?}",
                            context.len(), opened_free,
                        );
                        } else {
                            eprintln!(
                                "NUCLEUS_MIXED_PI:expr={expression:?}:context={}:binder={:?}:expected_pi=not-exposed",
                                context.len(), opened_free,
                            );
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
            lexical_context.push(domain);
            lexical_frame = lexical_frame.extend(self.closure(arg, frame.clone()));
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
