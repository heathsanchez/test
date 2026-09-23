use std::collections::{HashMap, HashSet};

use crate::id::{ExprId, IdTable, LevelId, NameId};
use crate::judgment::Judgment;
use crate::level::instantiate_level;
use crate::syntax::{Expr, Level};
use crate::value::{
    Closure, EnvBinding, EnvFrame, FreeId, LevelSubstitution, Neutral, NeutralHead, Value,
};

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct AuthorityId(pub u64);

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
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
    Rigid,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DefinitionBody {
    pub value: ExprId,
    pub preferred_for_reduction: bool,
    pub level_params: Vec<NameId>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RecursorRule {
    pub constructor: NameId,
    pub num_params: usize,
    pub num_fields: usize,
    pub rhs: ExprId,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RecursorReduction {
    pub num_params: usize,
    pub num_indices: usize,
    pub level_params: Vec<NameId>,
    pub rules: Vec<RecursorRule>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Exposure {
    pub value: Value,
    pub transitions: Vec<TransitionWitness>,
}

pub struct Machine<'a> {
    authority: AuthorityId,
    expressions: &'a IdTable<ExprId, Expr>,
    levels: &'a IdTable<LevelId, Level>,
    definitions: HashMap<NameId, DefinitionBody>,
    singleton_recursor_reductions: HashSet<NameId>,
    recursor_reductions: HashMap<NameId, RecursorReduction>,
}

impl<'a> Machine<'a> {
    pub fn new(
        authority: AuthorityId,
        expressions: &'a IdTable<ExprId, Expr>,
        levels: &'a IdTable<LevelId, Level>,
        definitions: HashMap<NameId, DefinitionBody>,
    ) -> Self {
        Self {
            authority,
            expressions,
            levels,
            definitions,
            singleton_recursor_reductions: HashSet::new(),
            recursor_reductions: HashMap::new(),
        }
    }

    pub fn with_singleton_recursor_reductions(mut self, reductions: HashSet<NameId>) -> Self {
        self.singleton_recursor_reductions = reductions;
        self
    }

    pub fn with_recursor_reductions(
        mut self,
        reductions: HashMap<NameId, RecursorReduction>,
    ) -> Self {
        self.recursor_reductions = reductions;
        self
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
                        match bound {
                            EnvBinding::Closure(bound) => {
                                visited.clear();
                                closure = bound;
                                continue;
                            }
                            EnvBinding::Free(free) => {
                                let mut spine = Vec::new();
                                append_pending(&mut spine, &mut pending);
                                transitions.push(TransitionWitness::Rigid);
                                return exposed(
                                    Value::Neutral(Neutral {
                                        head: NeutralHead::Free(free),
                                        spine,
                                    }),
                                    transitions,
                                );
                            }
                        }
                    }
                    let mut spine = Vec::new();
                    append_pending(&mut spine, &mut pending);
                    transitions.push(TransitionWitness::Rigid);
                    return exposed(
                        Value::Neutral(Neutral {
                            head: NeutralHead::Free(FreeId(*index)),
                            spine,
                        }),
                        transitions,
                    );
                }
                Expr::Sort(level) if pending.is_empty() => {
                    let Some(level) = self.resolve_level(*level, &closure, budget) else {
                        return Judgment::unknown("unresolved-sort-level-during-reduction");
                    };
                    transitions.push(TransitionWitness::Rigid);
                    return exposed(Value::Sort(level), transitions);
                }
                Expr::Pi { domain, body } if pending.is_empty() => {
                    transitions.push(TransitionWitness::Rigid);
                    return exposed(
                        Value::Pi {
                            domain: closure.sibling(*domain, closure.env.clone()),
                            body: closure.sibling(*body, closure.env.clone()),
                        },
                        transitions,
                    );
                }
                Expr::Lam { domain, body } => {
                    if let Some(argument) = pending.pop() {
                        transitions.push(TransitionWitness::Beta);
                        visited.clear();
                        closure = closure.sibling(*body, closure.env.extend(argument));
                        continue;
                    }
                    transitions.push(TransitionWitness::Rigid);
                    return exposed(
                        Value::Lam {
                            domain: closure.sibling(*domain, closure.env.clone()),
                            body: closure.sibling(*body, closure.env.clone()),
                        },
                        transitions,
                    );
                }
                Expr::Let { value, body, .. } => {
                    transitions.push(TransitionWitness::Zeta);
                    visited.clear();
                    let value = closure.sibling(*value, closure.env.clone());
                    closure = closure.sibling(*body, closure.env.extend(value));
                }
                Expr::App { fun, arg } => {
                    pending.push(closure.sibling(*arg, closure.env.clone()));
                    closure = closure.sibling(*fun, closure.env.clone());
                }
                Expr::Const { name, levels } => {
                    // G28: a separately qualified nullary-singleton recursor
                    // ignores its target and returns its sole minor.  This is
                    // kernel computation authority, not delta unfolding.
                    if self.singleton_recursor_reductions.contains(name) && pending.len() >= 3 {
                        let _motive = pending.pop().expect("length checked");
                        let minor = pending.pop().expect("length checked");
                        let _target = pending.pop().expect("length checked");
                        transitions.push(TransitionWitness::SingletonRecursor);
                        visited.clear();
                        closure = minor;
                        continue;
                    }
                    if let Some(reduction) = self.recursor_reductions.get(name) {
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
                            if let Some((constructor, constructor_arguments)) =
                                self.constructor_application(target)
                                && let Some(rule) = reduction
                                    .rules
                                    .iter()
                                    .find(|rule| rule.constructor == constructor)
                                && constructor_arguments.len() == rule.num_params + rule.num_fields
                            {
                                let prefix_len = reduction.num_params + 1 + reduction.rules.len();
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
                                    transitions.push(TransitionWitness::ConstructorRecursor);
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
                        transitions.push(TransitionWitness::Delta);
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
                    transitions.push(TransitionWitness::Rigid);
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
                Expr::Sort(_) | Expr::Pi { .. } => {
                    return Judgment::unknown("rigid-head-applied-as-function");
                }
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
                    EnvBinding::Free(_) => return None,
                },
                Expr::Const { name, .. } => {
                    arguments.reverse();
                    return Some((*name, arguments));
                }
                _ => return None,
            }
        }
    }

    fn resolve_level(
        &self,
        level: LevelId,
        closure: &Closure,
        budget: usize,
    ) -> Option<crate::level::LevelTerm> {
        instantiate_level(self.levels, level, &closure.levels.to_map(), budget).ok()
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

fn exposed(value: Value, transitions: Vec<TransitionWitness>) -> Judgment<Exposure> {
    Judgment::proven(Exposure { value, transitions }, "explicit-closure-machine")
}
