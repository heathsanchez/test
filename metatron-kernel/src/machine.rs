use std::collections::{HashMap, HashSet};

use crate::id::{ExprId, IdTable, NameId};
use crate::judgment::Judgment;
use crate::syntax::Expr;
use crate::value::{Closure, EnvFrame, Neutral, NeutralHead, Value};

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct AuthorityId(pub u64);

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Transparency {
    Opaque,
    Reducible,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TransitionWitness {
    Beta,
    Zeta,
    Delta,
    Rigid,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DefinitionBody {
    pub value: ExprId,
    pub reducible: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Exposure {
    pub value: Value,
    pub transitions: Vec<TransitionWitness>,
}

pub struct Machine<'a> {
    authority: AuthorityId,
    expressions: &'a IdTable<ExprId, Expr>,
    definitions: HashMap<NameId, DefinitionBody>,
}

impl<'a> Machine<'a> {
    pub fn new(
        authority: AuthorityId,
        expressions: &'a IdTable<ExprId, Expr>,
        definitions: HashMap<NameId, DefinitionBody>,
    ) -> Self {
        Self {
            authority,
            expressions,
            definitions,
        }
    }

    pub fn expose(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
    ) -> Judgment<Value> {
        self.expose_with_witnesses(closure, transparency, budget)
            .map(|exposure| exposure.value)
    }

    pub fn expose_with_witnesses(
        &self,
        mut closure: Closure,
        transparency: Transparency,
        mut budget: usize,
    ) -> Judgment<Exposure> {
        let mut pending = Vec::new();
        let mut visited = HashSet::new();
        let mut transitions = Vec::new();

        loop {
            if budget == 0 {
                return Judgment::unknown("reduction-budget-exhausted");
            }
            budget -= 1;
            if !visited.insert((self.authority, closure.expr, closure.env.id())) {
                return Judgment::unknown("reduction-cycle");
            }

            let Some(expression) = self.expressions.get(closure.expr) else {
                return Judgment::unknown("missing-expression-during-reduction");
            };
            match expression {
                Expr::BVar(index) => {
                    if let Some(bound) = closure.env.lookup(*index) {
                        visited.clear();
                        closure = bound;
                        continue;
                    }
                    let mut spine = Vec::new();
                    append_pending(&mut spine, &mut pending);
                    transitions.push(TransitionWitness::Rigid);
                    return exposed(
                        Value::Neutral(Neutral {
                            head: NeutralHead::Free(*index),
                            spine,
                        }),
                        transitions,
                    );
                }
                Expr::Sort(level) if pending.is_empty() => {
                    transitions.push(TransitionWitness::Rigid);
                    return exposed(Value::Sort(*level), transitions);
                }
                Expr::Pi { domain, body } if pending.is_empty() => {
                    transitions.push(TransitionWitness::Rigid);
                    return exposed(
                        Value::Pi {
                            domain: Closure::new(*domain, closure.env.clone()),
                            body: Closure::new(*body, closure.env),
                        },
                        transitions,
                    );
                }
                Expr::Lam { domain, body } => {
                    if let Some(argument) = pending.pop() {
                        transitions.push(TransitionWitness::Beta);
                        visited.clear();
                        closure = Closure::new(*body, closure.env.extend(argument));
                        continue;
                    }
                    transitions.push(TransitionWitness::Rigid);
                    return exposed(
                        Value::Lam {
                            domain: Closure::new(*domain, closure.env.clone()),
                            body: Closure::new(*body, closure.env),
                        },
                        transitions,
                    );
                }
                Expr::Let { value, body, .. } => {
                    transitions.push(TransitionWitness::Zeta);
                    visited.clear();
                    let value = Closure::new(*value, closure.env.clone());
                    closure = Closure::new(*body, closure.env.extend(value));
                }
                Expr::App { fun, arg } => {
                    pending.push(Closure::new(*arg, closure.env.clone()));
                    closure = Closure::new(*fun, closure.env);
                }
                Expr::Const { name, levels } => {
                    if let Some(definition) = self.definitions.get(name)
                        && transparency == Transparency::Reducible
                        && definition.reducible
                    {
                        transitions.push(TransitionWitness::Delta);
                        closure = Closure::new(definition.value, EnvFrame::empty());
                        continue;
                    }
                    let mut spine = Vec::new();
                    append_pending(&mut spine, &mut pending);
                    transitions.push(TransitionWitness::Rigid);
                    return exposed(
                        Value::Neutral(Neutral {
                            head: NeutralHead::Const {
                                name: *name,
                                levels: levels.clone(),
                            },
                            spine,
                        }),
                        transitions,
                    );
                }
                Expr::Sort(_) | Expr::Pi { .. } => {
                    return Judgment::unknown("rigid-head-applied-as-function");
                }
            }
        }
    }
}

fn append_pending(spine: &mut Vec<Closure>, pending: &mut Vec<Closure>) {
    while let Some(argument) = pending.pop() {
        spine.push(argument);
    }
}

fn exposed(value: Value, transitions: Vec<TransitionWitness>) -> Judgment<Exposure> {
    Judgment::proven(Exposure { value, transitions }, "explicit-closure-machine")
}
