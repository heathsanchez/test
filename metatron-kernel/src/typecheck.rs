use std::collections::HashMap;

use crate::environment::Environment;
use crate::id::{ExprId, IdTable, LevelId, NameId};
use crate::judgment::Judgment;
use crate::level::{LevelTerm, imax, instantiate_level, succ};
use crate::machine::{Machine, Transparency};
use crate::syntax::{Expr, Level};
use crate::value::{Closure, EnvFrame, FreeId, LevelSubstitution, Value};

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub enum TypeValue {
    Sort(LevelTerm),
    Term(Closure),
    Pi {
        domain: Box<TypeValue>,
        body: Box<TypeValue>,
    },
}

pub struct TypeChecker<'a> {
    expressions: &'a IdTable<ExprId, Expr>,
    levels: &'a IdTable<LevelId, Level>,
    environment: &'a Environment,
    level_substitution: HashMap<NameId, LevelTerm>,
    delta_policy: crate::convert::DeltaPolicy,
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
        }
    }

    pub fn with_delta_policy(mut self, policy: crate::convert::DeltaPolicy) -> Self {
        self.delta_policy = policy;
        self
    }

    pub fn infer(&self, expression: ExprId, budget: usize) -> Judgment<TypeValue> {
        let mut remaining = budget;
        self.infer_in(expression, &[], &EnvFrame::empty(), &mut remaining)
    }

    pub fn check(&self, expression: ExprId, expected: &TypeValue, budget: usize) -> Judgment<()> {
        let mut remaining = budget;
        self.check_in(
            expression,
            expected,
            &[],
            &EnvFrame::empty(),
            &mut remaining,
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
        self.check(expression, &TypeValue::Sort(LevelTerm::Zero), budget)
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
    ) -> Judgment<TypeValue> {
        if !take_step(remaining) {
            return Judgment::unknown("type-inference-budget");
        }
        let Some(expression_node) = self.expressions.get(expression) else {
            return Judgment::unknown("missing-expression-during-inference");
        };
        match expression_node {
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
                let domain_type = self.infer_in(*domain, context, frame, remaining);
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
                let body_type = self.infer_in(*body, &extended, &body_frame, remaining);
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
                let domain_type = self.infer_in(*domain, context, frame, remaining);
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
                self.infer_in(*body, &extended, &body_frame, remaining)
                    .map(|body_type| TypeValue::Pi {
                        domain: Box::new(domain_type),
                        body: Box::new(body_type),
                    })
            }
            Expr::App { fun, arg } => {
                let function_type = self.infer_in(*fun, context, frame, remaining);
                let Some((domain, body)) = self.pi_view(function_type, *remaining) else {
                    return Judgment::unknown("application-function-type");
                };
                match self.check_in(*arg, &domain, context, frame, remaining) {
                    Judgment::Proven { .. } => Judgment::proven(
                        match body {
                            PiBody::Fixed(body) => body,
                            PiBody::Closure(body) => TypeValue::Term(Closure::with_levels(
                                body.expr,
                                body.env.extend(self.closure(*arg, frame.clone())),
                                body.levels,
                            )),
                        },
                        "application-type-instantiation",
                    ),
                    Judgment::Refuted { obstruction } => Judgment::Refuted { obstruction },
                    Judgment::Unknown { residual } => Judgment::Unknown { residual },
                }
            }
            Expr::Let { ty, value, body } => {
                let annotation_type = self.infer_in(*ty, context, frame, remaining);
                match self.sort_level(annotation_type, *remaining) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                }
                let established = TypeValue::Term(self.closure(*ty, frame.clone()));
                match self.check_in(*value, &established, context, frame, remaining) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                }
                let mut extended = context.to_vec();
                extended.push(established);
                let extended_frame = frame.extend(self.closure(*value, frame.clone()));
                self.infer_in(*body, &extended, &extended_frame, remaining)
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
    ) -> Judgment<()> {
        let inferred = self.infer_in(expression, context, frame, remaining);
        match inferred {
            Judgment::Proven { value, .. } => crate::convert::convert_with_policy_at_depth(
                self,
                &value,
                expected,
                *remaining,
                self.delta_policy,
                context.len(),
            ),
            Judgment::Refuted { obstruction } => Judgment::Refuted { obstruction },
            Judgment::Unknown { residual } => Judgment::Unknown { residual },
        }
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
            TypeValue::Pi { domain, body } => Some((*domain, PiBody::Fixed(*body))),
            TypeValue::Term(closure) => {
                let machine = self.machine();
                let exposed = machine.expose(closure, Transparency::Reducible, budget);
                match exposed.proven_value()? {
                    Value::Pi { domain, body } => Some((
                        TypeValue::Term(domain.clone()),
                        PiBody::Closure(body.clone()),
                    )),
                    Value::Sort(_) | Value::Lam { .. } | Value::Neutral(_) => None,
                }
            }
            TypeValue::Sort(_) => None,
        }
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
    }

    pub(crate) fn instantiate(&self, level: LevelId, budget: usize) -> Result<LevelTerm, ()> {
        instantiate_level(self.levels, level, &self.level_substitution, budget).map_err(|_| ())
    }

    pub(crate) fn authority(&self) -> crate::machine::AuthorityId {
        self.environment.authority()
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

enum PiBody {
    Fixed(TypeValue),
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
