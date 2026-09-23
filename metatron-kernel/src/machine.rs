use std::collections::{HashMap, HashSet};
use std::rc::Rc;

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
    Rigid,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DefinitionBody {
    pub value: ExprId,
    pub preferred_for_reduction: bool,
    pub level_params: Vec<NameId>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Exposure {
    pub value: Value,
    pub transitions: Vec<TransitionWitness>,
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
}

const INLINE_PENDING_CAPACITY: usize = 8;

struct PendingStack {
    inline: [Option<Closure>; INLINE_PENDING_CAPACITY],
    len: usize,
    overflow: Option<Vec<Closure>>,
}

impl PendingStack {
    #[inline]
    fn new() -> Self {
        Self {
            inline: std::array::from_fn(|_| None),
            len: 0,
            overflow: None,
        }
    }

    #[inline]
    fn is_empty(&self) -> bool {
        self.len == 0 && self.overflow.as_ref().is_none_or(Vec::is_empty)
    }

    #[inline]
    fn push(&mut self, value: Closure) {
        if let Some(overflow) = self.overflow.as_mut() {
            overflow.push(value);
            return;
        }
        if self.len < INLINE_PENDING_CAPACITY {
            self.inline[self.len] = Some(value);
            self.len += 1;
            return;
        }
        let mut overflow = Vec::with_capacity(INLINE_PENDING_CAPACITY * 2);
        for slot in &mut self.inline[..self.len] {
            overflow.push(slot.take().expect("initialized pending slot"));
        }
        self.len = 0;
        overflow.push(value);
        self.overflow = Some(overflow);
    }

    #[inline]
    fn pop(&mut self) -> Option<Closure> {
        if let Some(overflow) = self.overflow.as_mut() {
            return overflow.pop();
        }
        if self.len == 0 {
            return None;
        }
        self.len -= 1;
        self.inline[self.len].take()
    }
}

pub struct Machine<'a> {
    authority: AuthorityId,
    expressions: &'a IdTable<ExprId, Expr>,
    levels: &'a IdTable<LevelId, Level>,
    definitions: Rc<HashMap<NameId, DefinitionBody>>,
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
            expressions,
            levels,
            definitions: definitions.into(),
        }
    }

    pub fn expose(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
    ) -> Judgment<Value> {
        self.expose_internal(closure, transparency, budget, false)
            .map(|exposure| exposure.value)
    }

    pub fn expose_with_witnesses(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
    ) -> Judgment<Exposure> {
        self.expose_internal(closure, transparency, budget, true)
    }

    fn expose_internal(
        &self,
        mut closure: Closure,
        transparency: Transparency,
        mut budget: usize,
        record_witnesses: bool,
    ) -> Judgment<Exposure> {
        let mut pending = PendingStack::new();
        let mut visited = VisitSet::new();
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
                    if let Some(argument) = pending.pop() {
                        record_transition(
                            &mut transitions,
                            record_witnesses,
                            TransitionWitness::Beta,
                        );
                        visited.clear();
                        closure = closure.sibling(*body, closure.env.extend(argument));
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
                    closure = closure.sibling(*body, closure.env.extend(value));
                }
                Expr::App { fun, arg } => {
                    pending.push(closure.sibling(*arg, closure.env.clone()));
                    closure = closure.sibling(*fun, closure.env.clone());
                }
                Expr::Const { name, levels } => {
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
                Expr::Sort(_) | Expr::Pi { .. } => {
                    return Judgment::unknown("rigid-head-applied-as-function");
                }
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

fn append_pending(spine: &mut Vec<Closure>, pending: &mut PendingStack) {
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
