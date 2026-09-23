use std::collections::{HashMap, HashSet};
use std::rc::Rc;

use crate::environment::{BoolPrimitives, NatPrimitives};
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
    NatExtension,
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
pub struct ProjectionSpec {
    pub constructor: NameId,
    pub num_params: usize,
    pub field_param_indices: Vec<usize>,
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

pub struct Machine<'a> {
    authority: AuthorityId,
    expressions: &'a IdTable<ExprId, Expr>,
    levels: &'a IdTable<LevelId, Level>,
    definitions: Rc<HashMap<NameId, DefinitionBody>>,
    singleton_recursor_reductions: HashSet<NameId>,
    recursor_reductions: HashMap<NameId, RecursorReduction>,
    projection_specs: HashMap<NameId, ProjectionSpec>,
    nat_primitives: Option<NatPrimitives>,
    bool_primitives: Option<BoolPrimitives>,
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
            singleton_recursor_reductions: HashSet::new(),
            recursor_reductions: HashMap::new(),
            projection_specs: HashMap::new(),
            nat_primitives: None,
            bool_primitives: None,
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

    pub fn with_projection_specs(mut self, specs: HashMap<NameId, ProjectionSpec>) -> Self {
        self.projection_specs = specs;
        self
    }

    pub fn with_nat_primitives(mut self, primitives: Option<NatPrimitives>) -> Self {
        self.nat_primitives = primitives;
        self
    }

    pub fn with_bool_primitives(mut self, primitives: Option<BoolPrimitives>) -> Self {
        self.bool_primitives = primitives;
        self
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
        let mut pending = Vec::new();
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
                Expr::NatLit(value) if pending.is_empty() => {
                    record_transition(&mut transitions, record_witnesses, TransitionWitness::Rigid);
                    return exposed(Value::NatLit(value.clone()), transitions);
                }
                Expr::NatLit(_) => {
                    return Judgment::unknown("nat-literal-applied-as-function");
                }
                Expr::StrLit(_) => {
                    return Judgment::unknown("string-literal-reduction-not-qualified");
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
                    if let Some(native) = self.try_native_nat_reduction(
                        *name,
                        levels,
                        &mut pending,
                        transparency,
                        budget,
                    ) {
                        record_transition(
                            &mut transitions,
                            record_witnesses,
                            TransitionWitness::NatExtension,
                        );
                        return exposed(native, transitions);
                    }

                    // G28: a separately qualified nullary-singleton recursor
                    // ignores its target and returns its sole minor.  This is
                    // kernel computation authority, not delta unfolding.
                    if self.singleton_recursor_reductions.contains(name) && pending.len() >= 3 {
                        let _motive = pending.pop().expect("length checked");
                        let minor = pending.pop().expect("length checked");
                        let _target = pending.pop().expect("length checked");
                        record_transition(
                            &mut transitions,
                            record_witnesses,
                            TransitionWitness::SingletonRecursor,
                        );
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
                                    record_transition(
                                        &mut transitions,
                                        record_witnesses,
                                        TransitionWitness::ConstructorRecursor,
                                    );
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
                Expr::Proj {
                    type_name,
                    index,
                    structure,
                } => {
                    if !pending.is_empty() {
                        return Judgment::unknown("projection-applied-as-function");
                    }
                    let Some(spec) = self.projection_specs.get(type_name) else {
                        return Judgment::unknown("unsupported-projection");
                    };
                    let Ok(index) = usize::try_from(*index) else {
                        return Judgment::unknown("projection-index-overflow");
                    };
                    if index >= spec.field_param_indices.len() {
                        return Judgment::unknown("projection-index-out-of-range");
                    }
                    let structure = closure.sibling(*structure, closure.env.clone());
                    let exposed_structure =
                        self.expose_internal(structure, transparency, budget, false);
                    let Some(exposure) = exposed_structure.proven_value() else {
                        return Judgment::unknown("projection-structure-stuck");
                    };
                    let Value::Neutral(neutral) = &exposure.value else {
                        return Judgment::unknown("projection-structure-stuck");
                    };
                    let NeutralHead::Const { name, .. } = &neutral.head else {
                        return Judgment::unknown("projection-structure-neutral");
                    };
                    if *name != spec.constructor {
                        return Judgment::unknown("projection-constructor-mismatch");
                    }
                    let field_offset = spec.num_params + index;
                    let Some(field) = neutral.spine.get(field_offset).cloned() else {
                        return Judgment::unknown("projection-constructor-arity");
                    };
                    visited.clear();
                    closure = field;
                    continue;
                }
                Expr::Sort(_) | Expr::Pi { .. } => {
                    return Judgment::unknown("rigid-head-applied-as-function");
                }
            }
        }
    }

    fn try_native_nat_reduction(
        &self,
        name: NameId,
        levels: &[LevelId],
        pending: &mut Vec<Closure>,
        transparency: Transparency,
        budget: usize,
    ) -> Option<Value> {
        let primitives = self.nat_primitives.as_ref()?;
        enum Operation {
            Add,
            Sub,
            Ble,
        }
        let operation = if primitives.add == Some(name) {
            Operation::Add
        } else if primitives.sub == Some(name) {
            Operation::Sub
        } else if primitives.ble == Some(name) {
            Operation::Ble
        } else {
            return None;
        };
        if !levels.is_empty() || pending.len() < 2 {
            return None;
        }

        // Applications are accumulated outside-in, so the last pending item
        // is the first source argument.
        let first = pending[pending.len() - 1].clone();
        let second = pending[pending.len() - 2].clone();
        let first_value = self
            .expose_internal(first, transparency, budget.saturating_sub(1), false)
            .proven_value()?
            .value
            .clone();
        let second_value = self
            .expose_internal(second, transparency, budget.saturating_sub(1), false)
            .proven_value()?
            .value
            .clone();
        let (Value::NatLit(first), Value::NatLit(second)) = (first_value, second_value) else {
            return None;
        };
        if pending.len() != 2 {
            return None;
        }
        pending.clear();
        Some(match operation {
            Operation::Add => Value::NatLit(first.add(&second)),
            Operation::Sub => Value::NatLit(first.sub_trunc(&second)),
            Operation::Ble => {
                let bools = self.bool_primitives.as_ref()?;
                let ctor = if first.compare(&second) != std::cmp::Ordering::Greater {
                    bools.true_ctor
                } else {
                    bools.false_ctor
                };
                Value::Neutral(Neutral {
                    head: NeutralHead::Const {
                        name: ctor,
                        levels: Vec::new(),
                    },
                    spine: Vec::new(),
                })
            }
        })
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
        instantiate_level(self.levels, level, &closure.levels, budget).ok()
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
