use std::cell::RefCell;
use std::collections::{HashMap, HashSet};
use std::rc::Rc;

use crate::environment::{BoolPrimitives, NatPrimitives, QuotPrimitives};
use crate::id::{ExprId, IdTable, LevelId, NameId};
use crate::judgment::Judgment;
use crate::level::instantiate_level;
use crate::syntax::{Expr, Level};
use crate::value::{
    Closure, EnvBinding, EnvFrame, FreeId, LevelSubstitution, Neutral, NeutralHead, Value,
};

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct AuthorityId(pub u64);

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
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
    Quotient,
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
    pub constructor_level_params: Vec<NameId>,
    pub num_params: usize,
    pub num_fields: usize,
    pub rhs: ExprId,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RecursorReduction {
    pub k: bool,
    pub num_params: usize,
    pub num_indices: usize,
    pub level_params: Vec<NameId>,
    pub rules: Vec<RecursorRule>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ProjectionFieldType {
    Parameter(usize),
    Derived(ExprId),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProjectionSpec {
    pub constructor: NameId,
    pub num_params: usize,
    pub field_types: Vec<ProjectionFieldType>,
    pub eta_expandable: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Exposure {
    pub value: Value,
    pub transitions: Vec<TransitionWitness>,
}

/// Only certified exposure results may be retained. Closure frames and the
/// declared authority are part of the key; budget is an exploration limit,
/// not a semantic hypothesis about the normalized value.
pub(crate) type ExposureCacheKey = (AuthorityId, Closure, Transparency, bool, Vec<Closure>);
pub(crate) type ExposureCache = Rc<RefCell<HashMap<ExposureCacheKey, Value>>>;

pub(crate) fn new_exposure_cache() -> ExposureCache {
    Rc::new(RefCell::new(HashMap::new()))
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
    exposure_cache: Option<ExposureCache>,
    expressions: &'a IdTable<ExprId, Expr>,
    levels: &'a IdTable<LevelId, Level>,
    definitions: Rc<HashMap<NameId, DefinitionBody>>,
    singleton_recursor_reductions: HashSet<NameId>,
    recursor_reductions: HashMap<NameId, RecursorReduction>,
    projection_specs: HashMap<NameId, ProjectionSpec>,
    nat_primitives: Option<NatPrimitives>,
    bool_primitives: Option<BoolPrimitives>,
    quot_primitives: Option<QuotPrimitives>,
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
            exposure_cache: None,
            expressions,
            levels,
            definitions: definitions.into(),
            singleton_recursor_reductions: HashSet::new(),
            recursor_reductions: HashMap::new(),
            projection_specs: HashMap::new(),
            nat_primitives: None,
            bool_primitives: None,
            quot_primitives: None,
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

    /// Share positive exposure evidence over one type-checker judgment.
    /// Unresolved / cyclic evaluations are intentionally never cached.
    pub(crate) fn with_exposure_cache(mut self, cache: ExposureCache) -> Self {
        self.exposure_cache = Some(cache);
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

    pub fn with_quot_primitives(mut self, primitives: Option<QuotPrimitives>) -> Self {
        self.quot_primitives = primitives;
        self
    }

    pub fn expose(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
    ) -> Judgment<Value> {
        self.expose_internal(closure, transparency, budget, false, false)
            .map(|exposure| exposure.value)
    }

    pub fn expose_for_conversion(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
    ) -> Judgment<Value> {
        self.expose_internal(closure, transparency, budget, false, true)
            .map(|exposure| exposure.value)
    }

    /// Unfold exactly the definition at an application's head, then resume
    /// cheap conversion exposure with the original application spine.
    pub(crate) fn expose_head_delta_for_conversion(
        &self,
        mut closure: Closure,
        mut budget: usize,
    ) -> Option<Judgment<Value>> {
        let mut pending = Vec::new();
        let mut visited = VisitSet::new();
        loop {
            if budget == 0 || !visited.insert((self.authority, closure.expr, closure.env.id())) {
                return Some(Judgment::unknown("head-delta-exposure"));
            }
            budget -= 1;
            match self.expressions.get(closure.expr)? {
                Expr::BVar(index) => match closure.env.lookup(*index)? {
                    EnvBinding::Closure(bound) => closure = bound,
                    EnvBinding::Free(_) | EnvBinding::Neutral(_) => return None,
                },
                Expr::Let { value, body, .. } => {
                    let value = closure.sibling(*value, closure.env.clone());
                    closure = closure.sibling(*body, closure.env.extend(value));
                }
                Expr::App { fun, arg } => {
                    pending.push(closure.sibling(*arg, closure.env.clone()));
                    closure = closure.sibling(*fun, closure.env.clone());
                }
                Expr::Const { name, levels } => {
                    let definition = self.definitions.get(name)?;
                    if definition.level_params.len() != levels.len() {
                        return Some(Judgment::unknown("head-delta-level-arity"));
                    }
                    let mut substitution = Vec::with_capacity(levels.len());
                    for (parameter, level) in definition.level_params.iter().zip(levels) {
                        let Some(level) = self.resolve_level(*level, &closure, budget) else {
                            return Some(Judgment::unknown("head-delta-level-instantiation"));
                        };
                        substitution.push((*parameter, level));
                    }
                    let body = Closure::with_levels(
                        definition.value,
                        EnvFrame::empty(),
                        LevelSubstitution::new(substitution),
                    );
                    return Some(
                        self.expose_internal_with_pending(
                            body,
                            Transparency::Reducible,
                            budget,
                            false,
                            true,
                            pending,
                        )
                        .map(|exposure| exposure.value),
                    );
                }
                _ => return None,
            }
        }
    }

    pub fn expose_with_witnesses(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
    ) -> Judgment<Exposure> {
        self.expose_internal(closure, transparency, budget, true, false)
    }

    pub(crate) fn projection_field_for_conversion(
        &self,
        structure: Closure,
        type_name: NameId,
        index: usize,
        budget: usize,
    ) -> Judgment<Closure> {
        let Some(spec) = self.projection_specs.get(&type_name) else {
            return Judgment::unknown("unsupported-projection");
        };
        if index >= spec.field_types.len() {
            return Judgment::unknown("projection-index-out-of-range");
        }
        let exposed = self.expose_internal(
            structure.clone(),
            Transparency::Full,
            budget,
            false,
            false,
        );
        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_PROJECTION_FIELD_FAILURE").is_some() {
            static COUNT: std::sync::atomic::AtomicUsize =
                std::sync::atomic::AtomicUsize::new(0);
            if COUNT.fetch_add(1, std::sync::atomic::Ordering::Relaxed) < 96 {
                eprintln!(
                    "NUCLEUS_PROJECTION_FIELD_PROBE:type={type_name:?}:index={index}:constructor={:?}:structure={structure:?}:full_exposure={exposed:?}",
                    spec.constructor,
                );
            }
        }
        let Some(Value::Neutral(neutral)) = exposed.proven_value().map(|value| &value.value) else {
            return Judgment::unknown("projection-structure-stuck");
        };
        let NeutralHead::Const { name, .. } = neutral.head else {
            return Judgment::unknown("projection-structure-neutral");
        };
        if name != spec.constructor {
            return Judgment::unknown("projection-constructor-mismatch");
        }
        let field_offset = spec.num_params + index;
        let Some(field) = neutral.spine.get(field_offset).cloned() else {
            return Judgment::unknown("projection-constructor-arity");
        };
        Judgment::proven(field, "projection-selected-field")
    }

    pub(crate) fn projection_value_for_conversion(
        &self,
        structure: Closure,
        type_name: NameId,
        index: usize,
        spine: &[Closure],
        budget: usize,
    ) -> Judgment<Value> {
        let field = self.projection_field_for_conversion(structure, type_name, index, budget);
        let Some(field) = field.proven_value() else {
            return Judgment::unknown("lazy-projection-field-exposure");
        };
        // Do not eagerly normalize a fully applied projection field through
        // every recursive definition. A proven preferred reduction is enough
        // to establish a legitimate rigid comparison; Full is the fallback
        // only if this bounded first stage cannot produce any certified value.
        let pending: Vec<Closure> = spine.iter().rev().cloned().collect();
        let cheap = self.expose_internal_with_pending(
            field.clone(), Transparency::Reducible,
            budget.saturating_sub(1), false, true, pending.clone(),
        ).map(|exposure| exposure.value);
        if cheap.is_proven() {
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_PROJECTION_CHEAP").is_some() {
                eprintln!("NUCLEUS_PROJECTION_CHEAP:field={:?}:type={type_name:?}:index={index}", field.expr);
            }
            return cheap;
        }
        self.expose_internal_with_pending(
            field.clone(), Transparency::Full,
            budget.saturating_sub(1), false, true, pending,
        ).map(|exposure| exposure.value)
    }

    fn expose_internal(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
        record_witnesses: bool,
        preserve_stuck_projection: bool,
    ) -> Judgment<Exposure> {
        self.expose_internal_with_pending(
            closure,
            transparency,
            budget,
            record_witnesses,
            preserve_stuck_projection,
            Vec::new(),
        )
    }

    /// Memoize exact successful normal forms across exposure calls that
    /// share an environment/authority. Never treat a cached UNKNOWN as proof.
    fn expose_internal_with_pending(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
        record_witnesses: bool,
        preserve_stuck_projection: bool,
        pending: Vec<Closure>,
    ) -> Judgment<Exposure> {
        if budget == 0 {
            return Judgment::unknown("reduction-budget-exhausted");
        }
        let Some(cache) = self.exposure_cache.as_ref().filter(|_| !record_witnesses) else {
            return self.expose_uncached_internal_with_pending(
                closure, transparency, budget, record_witnesses,
                preserve_stuck_projection, pending,
            );
        };
        let key = (
            self.authority,
            closure.clone(),
            transparency,
            preserve_stuck_projection,
            pending.clone(),
        );
        let cached = cache.borrow().get(&key).cloned();
        if let Some(value) = cached {
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_EXPOSURE_CACHE").is_some() {
                eprintln!("NUCLEUS_EXPOSURE_CACHE:hit:expression={:?}", closure.expr);
            }
            return Judgment::proven(
                Exposure { value, transitions: Vec::new() },
                "certified-cached-closure-exposure",
            );
        }
        let result = self.expose_uncached_internal_with_pending(
            closure, transparency, budget, false,
            preserve_stuck_projection, pending,
        );
        if let Some(established) = result.proven_value() {
            let mut entries = cache.borrow_mut();
            // Bound memory across large Arena exports. Eviction affects only
            // performance and never creates a judgment.
            if entries.len() >= 8192 {
                entries.clear();
            }
            entries.insert(key, established.value.clone());
        }
        result
    }

    fn expose_uncached_internal_with_pending(
        &self,
        mut closure: Closure,
        transparency: Transparency,
        mut budget: usize,
        record_witnesses: bool,
        preserve_stuck_projection: bool,
        mut pending: Vec<Closure>,
    ) -> Judgment<Exposure> {
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
                            EnvBinding::Neutral(mut neutral) => {
                                append_pending(&mut neutral.spine, &mut pending);
                                record_transition(
                                    &mut transitions,
                                    record_witnesses,
                                    TransitionWitness::Rigid,
                                );
                                return exposed(Value::Neutral(neutral), transitions);
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

                    if let Some(next) = self.try_quot_reduction(*name, levels, &mut pending) {
                        record_transition(
                            &mut transitions,
                            record_witnesses,
                            TransitionWitness::Quotient,
                        );
                        visited.clear();
                        closure = next;
                        continue;
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
                        if std::env::var_os("NUCLEUS_TRACE_NAT_IOTA").is_some() && self.nat_primitives.as_ref().is_some_and(|nat| nat.recursor == *name) { eprintln!("NUCLEUS_NAT_REC:pending={}:transparency={transparency:?}:rules={}", pending.len(), reduction.rules.len()); }
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
                            let prefix_len = reduction.num_params + 1 + reduction.rules.len();
                            if let Some((constructor, constructor_arguments)) =
                                self.rule_constructor_application(
                                    target,
                                    reduction,
                                    transparency,
                                    budget,
                                )
                                && let Some(rule) = reduction
                                    .rules
                                    .iter()
                                    .find(|rule| rule.constructor == constructor)
                                && constructor_arguments.len() == rule.num_params + rule.num_fields
                            {
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
                    let Some(spec) = self.projection_specs.get(type_name) else {
                        return Judgment::unknown("unsupported-projection");
                    };
                    let Ok(index) = usize::try_from(*index) else {
                        return Judgment::unknown("projection-index-overflow");
                    };
                    if index >= spec.field_types.len() {
                        return Judgment::unknown("projection-index-out-of-range");
                    }
                    let structure = closure.sibling(*structure, closure.env.clone());
                    let structure_transparency = if preserve_stuck_projection {
                        Transparency::Opaque
                    } else {
                        transparency
                    };
                    let exposed_structure = self.expose_internal(
                        structure.clone(),
                        structure_transparency,
                        budget,
                        false,
                        preserve_stuck_projection,
                    );
                    let Some(exposure) = exposed_structure.proven_value() else {
                        if preserve_stuck_projection {
                            let mut spine = Vec::new();
                            append_pending(&mut spine, &mut pending);
                            return exposed(
                                Value::StuckProjection {
                                    type_name: *type_name,
                                    index,
                                    structure,
                                    spine,
                                },
                                transitions,
                            );
                        }
                        return Judgment::unknown("projection-structure-stuck");
                    };
                    let Value::Neutral(neutral) = &exposure.value else {
                        if preserve_stuck_projection {
                            let mut spine = Vec::new();
                            append_pending(&mut spine, &mut pending);
                            return exposed(
                                Value::StuckProjection {
                                    type_name: *type_name,
                                    index,
                                    structure,
                                    spine,
                                },
                                transitions,
                            );
                        }
                        return Judgment::unknown("projection-structure-stuck");
                    };
                    match &neutral.head {
                        NeutralHead::Const { name, .. } if *name == spec.constructor => {
                            let field_offset = spec.num_params + index;
                            let Some(field) = neutral.spine.get(field_offset).cloned() else {
                                return Judgment::unknown("projection-constructor-arity");
                            };
                            visited.clear();
                            closure = field;
                            continue;
                        }
                        NeutralHead::Const { .. } => {
                            if preserve_stuck_projection {
                                let mut spine = Vec::new();
                                append_pending(&mut spine, &mut pending);
                                return exposed(
                                    Value::StuckProjection {
                                        type_name: *type_name,
                                        index,
                                        structure,
                                        spine,
                                    },
                                    transitions,
                                );
                            }
                            return Judgment::unknown("projection-constructor-mismatch");
                        }
                        NeutralHead::Free(_) | NeutralHead::Projection { .. } => {
                            let mut spine = Vec::new();
                            append_pending(&mut spine, &mut pending);
                            record_transition(
                                &mut transitions,
                                record_witnesses,
                                TransitionWitness::Rigid,
                            );
                            return exposed(
                                Value::Neutral(Neutral {
                                    head: NeutralHead::Projection {
                                        type_name: *type_name,
                                        index,
                                        structure: Box::new(neutral.clone()),
                                    },
                                    spine,
                                }),
                                transitions,
                            );
                        }
                    }
                }
                Expr::Sort(_) | Expr::Pi { .. } => {
                    return Judgment::unknown("rigid-head-applied-as-function");
                }
            }
        }
    }

    fn try_quot_reduction(
        &self,
        name: NameId,
        levels: &[LevelId],
        pending: &mut Vec<Closure>,
    ) -> Option<Closure> {
        let primitives = self.quot_primitives.as_ref()?;

        let (required, target_index, function_index, level_arity) = if name == primitives.lift {
            (6usize, 5usize, 3usize, 2usize)
        } else if name == primitives.ind {
            (5usize, 4usize, 3usize, 1usize)
        } else {
            return None;
        };
        if levels.len() != level_arity || pending.len() < required {
            return None;
        }

        let offset = pending.len() - required;
        let arguments = pending[offset..].iter().rev().cloned().collect::<Vec<_>>();
        let target = arguments.get(target_index)?;
        let (constructor, constructor_arguments) = self.constructor_application(target)?;
        if constructor != primitives.mk || constructor_arguments.len() != 3 {
            return None;
        }

        let function = arguments.get(function_index)?.clone();
        let value = constructor_arguments[2].clone();
        pending.truncate(offset);
        pending.push(value);
        Some(function)
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
            Pred,
            Ble,
            Beq,
        }
        let operation = if primitives.add == Some(name) {
            Operation::Add
        } else if primitives.sub == Some(name) {
            Operation::Sub
        } else if primitives.pred == Some(name) {
            Operation::Pred
        } else if primitives.ble == Some(name) {
            Operation::Ble
        } else if primitives.beq == Some(name) {
            Operation::Beq
        } else {
            return None;
        };
        // Nat.pred (Nat.succ n) reduces to n; on neutral n, preserve the
        // typed source application rather than forcing a recursively stuck
        // matcher. Full transparency may still inspect its definition.
        if matches!(operation, Operation::Pred) {
            if !levels.is_empty() || pending.len() != 1 {
                return None;
            }
            let argument = pending[0].clone();
            let exposed = self.expose_internal(
                argument.clone(), transparency, budget.saturating_sub(1), false, false,
            );
            if let Some(exposed) = exposed.proven_value() {
                match &exposed.value {
                    Value::NatLit(n) => {
                        pending.clear();
                        return Some(Value::NatLit(n.pred().unwrap_or_else(|| n.clone())));
                    }
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: ctor, levels },
                        spine,
                    }) if levels.is_empty() && *ctor == primitives.succ && spine.len() == 1 => {
                        let result = self.expose_internal(
                            spine[0].clone(), transparency, budget.saturating_sub(1),
                            false, false,
                        );
                        if let Some(value) = result.proven_value() {
                            pending.clear();
                            return Some(value.value.clone());
                        }
                    }
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: ctor, levels },
                        spine,
                    }) if levels.is_empty() && *ctor == primitives.zero && spine.is_empty() => {
                        pending.clear();
                        return Some(Value::Neutral(Neutral {
                            head: NeutralHead::Const { name: *ctor, levels: vec![] },
                            spine: vec![],
                        }));
                    }
                    _ => {}
                }
            }
            if transparency != Transparency::Full {
                pending.clear();
                return Some(Value::Neutral(Neutral {
                    head: NeutralHead::Const { name, levels: vec![] },
                    spine: vec![argument],
                }));
            }
            return None;
        }
        if !levels.is_empty() || pending.len() != 2 {
            return None;
        }

        // Applications are accumulated outside-in, so the last pending item
        // is the first source argument.
        let first = pending[pending.len() - 1].clone();
        let second = pending[pending.len() - 2].clone();

        if matches!(operation, Operation::Beq) {
            let bools = self.bool_primitives.as_ref()?;
            let first_value = self
                .expose_internal(
                    first.clone(),
                    transparency,
                    budget.saturating_sub(1),
                    false,
                    false,
                )
                .proven_value()?
                .value
                .clone();
            let second_value = self
                .expose_internal(
                    second.clone(),
                    transparency,
                    budget.saturating_sub(1),
                    false,
                    false,
                )
                .proven_value()?
                .value
                .clone();

            let bool_value = |truth: bool| {
                Value::Neutral(Neutral {
                    head: NeutralHead::Const {
                        name: if truth { bools.true_ctor } else { bools.false_ctor },
                        levels: Vec::new(),
                    },
                    spine: Vec::new(),
                })
            };

            // Nat literals already have exact native meaning.  Comparing two
            // literals is therefore the same definitional consequence as
            // recursively peeling their constructors.
            if let (Value::NatLit(left), Value::NatLit(right)) = (&first_value, &second_value) {
                pending.clear();
                return Some(bool_value(left.compare(right) == std::cmp::Ordering::Equal));
            }

            let constructor_view = |value: &Value| -> Option<(bool, Option<Closure>)> {
                match value {
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name, levels },
                        spine,
                    }) if levels.is_empty()
                        && *name == primitives.zero
                        && spine.is_empty() =>
                    {
                        Some((false, None))
                    }
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name, levels },
                        spine,
                    }) if levels.is_empty()
                        && *name == primitives.succ
                        && spine.len() == 1 =>
                    {
                        Some((true, Some(spine[0].clone())))
                    }
                    Value::NatLit(value) if value.is_zero() => Some((false, None)),
                    _ => None,
                }
            };

            let (first_succ, first_pred) = constructor_view(&first_value)?;
            let (second_succ, second_pred) = constructor_view(&second_value)?;
            pending.clear();
            return match (first_succ, second_succ) {
                (false, false) => Some(bool_value(true)),
                (false, true) | (true, false) => Some(bool_value(false)),
                (true, true) => Some(Value::Neutral(Neutral {
                    head: NeutralHead::Const {
                        name,
                        levels: Vec::new(),
                    },
                    spine: vec![first_pred?, second_pred?],
                })),
            };
        }

        // Nat.add n 0 = n and Nat.add n (succ 0) = succ n.
        // These are the exact constructor equations of the checked Prelude
        // definition, and work for any already well-typed symbolic n.
        // This contraction does not infer any recursor major or proof index.
        if matches!(operation, Operation::Add) {
            let right = self.expose_internal(
                second.clone(), transparency, budget.saturating_sub(1), false, false,
            );
            if let Some(v) = right.proven_value().map(|x| &x.value) {
                let zero = |v: &Value| matches!(v,
                    Value::NatLit(n) if n.is_zero())
                    || matches!(v,
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: ctor, levels },
                        spine,
                    }) if *ctor==primitives.zero && levels.is_empty() && spine.is_empty());
                let one = matches!(v,
                    Value::NatLit(n) if n.pred().is_some_and(|pre| pre.is_zero()))
                    || matches!(v,
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: ctor, levels },
                        spine,
                    }) if *ctor == primitives.succ && levels.is_empty() && spine.len()==1
                        && self.expose_internal(
                            spine[0].clone(), transparency, budget.saturating_sub(1),
                            false, false,
                        ).proven_value().is_some_and(|x| zero(&x.value)));
                if zero(v) {
                    let first_value = self.expose_internal(
                        first.clone(), transparency, budget.saturating_sub(1),
                        false, false,
                    );
                    if let Some(value)=first_value.proven_value() {
                        pending.clear();
                        #[cfg(feature="diagnostics")]
                        if std::env::var_os("NUCLEUS_TRACE_NAT_ADDONE").is_some() {
                            eprintln!("NUCLEUS_NAT_ADDONE:checked-zero");
                        }
                        return Some(value.value.clone());
                    }
                }
                if one {
                    pending.clear();
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_NAT_ADDONE").is_some() {
                        eprintln!("NUCLEUS_NAT_ADDONE:checked-one");
                    }
                    return Some(Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: primitives.succ, levels: vec![] },
                        spine: vec![first],
                    }));
                }
            }
        }

        // Pinned Lean v4.34.1 Init.Prelude defines:
        //   Nat.ble zero _ = true
        //   Nat.ble (succ _) zero = false
        //   Nat.ble (succ n) (succ m) = Nat.ble n m
        // The existing native extension only handled two numerals. Preserve
        // this exact source-defined one-step symbolic computation without
        // claiming the predecessor variables or proof indices are equal.
        if matches!(operation, Operation::Ble) {
            let bools = self.bool_primitives.as_ref()?;
            let as_constructor = |v: &Value| -> Option<(bool, Option<Closure>)> {
                match v {
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name, levels },
                        spine,
                    }) if levels.is_empty()
                        && *name == primitives.zero
                        && spine.is_empty() => Some((false, None)),
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name, levels },
                        spine,
                    }) if levels.is_empty()
                        && *name == primitives.succ
                        && spine.len() == 1 => Some((true, Some(spine[0].clone()))),
                    Value::NatLit(n) if n.is_zero() => Some((false, None)),
                    _ => None,
                }
            };
            let boolean = |truth: bool| Value::Neutral(Neutral {
                head: NeutralHead::Const {
                    name: if truth { bools.true_ctor } else { bools.false_ctor },
                    levels: Vec::new(),
                },
                spine: Vec::new(),
            });
            let left = self.expose_internal(
                first.clone(), transparency, budget.saturating_sub(1), false, false,
            ).proven_value()?.value.clone();
            if let Some((false, None)) = as_constructor(&left) {
                pending.clear();
                return Some(boolean(true));
            }
            let right = self.expose_internal(
                second.clone(), transparency, budget.saturating_sub(1), false, false,
            ).proven_value()?.value.clone();
            if let (Value::NatLit(n), Value::NatLit(m)) = (&left, &right) {
                pending.clear();
                return Some(boolean(n.compare(m) != std::cmp::Ordering::Greater));
            }
            match (as_constructor(&left), as_constructor(&right)) {
                (Some((true, Some(_))), Some((false, None))) => {
                    pending.clear();
                    return Some(boolean(false));
                }
                (Some((true, Some(n))), Some((true, Some(m)))) => {
                    pending.clear();
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_BLE_SYMBOLIC").is_some() {
                        eprintln!("NUCLEUS_BLE_SYMBOLIC:succ-succ:head={name:?}");
                    }
                    return Some(Value::Neutral(Neutral {
                        head: NeutralHead::Const { name, levels: Vec::new() },
                        spine: vec![n, m],
                    }));
                }
                _ => {}
            }
            return None;
        }

        // Verified source equation (Lean v4.34.1 Init.Prelude):
        // Nat.sub a 0 = a, including an arbitrary symbolic a.
        // No predecessor is synthesized and no unsupported succ rule is
        // inferred. The receiver's established WHNF is reused directly.
        if matches!(operation, Operation::Sub) {
            let second_value = self.expose_internal(
                second.clone(), transparency, budget.saturating_sub(1), false, false,
            );
            let zero_major = matches!(second_value.proven_value().map(|e| &e.value), Some(Value::NatLit(n)) if n.is_zero())
                || matches!(second_value.proven_value().map(|e| &e.value),
                    Some(Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: ctor, levels },
                        spine,
                    })) if *ctor == primitives.zero && levels.is_empty() && spine.is_empty());
            if zero_major {
                if let Some(first_value) = self.expose_internal(
                    first.clone(), transparency, budget.saturating_sub(1), false, false,
                ).proven_value().map(|e| e.value.clone()) {
                    pending.clear();
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_NAT_SUBZERO").is_some() {
                        eprintln!("NUCLEUS_NAT_SUBZERO:certified-zero-right");
                    }
                    return Some(first_value);
                }
            }
            // Nat.sub (succ a) (succ zero) = a, obtained by two
            // checked Nat.sub clauses and Nat.pred (succ a) = a.
            // Both constructor witnesses are required. A symbolic second
            // predecessor is deliberately NOT eliminated.
            if primitives.pred.is_some()
                && let Some(Value::Neutral(Neutral {
                    head: NeutralHead::Const { name: second_ctor, levels: second_levels },
                    spine: second_spine,
                })) = second_value.proven_value().map(|e| &e.value)
                && *second_ctor == primitives.succ
                && second_levels.is_empty()
                && second_spine.len() == 1
            {
                let predecessor = self.expose_internal(
                    second_spine[0].clone(), transparency,
                    budget.saturating_sub(1), false, false,
                );
                let is_zero = matches!(predecessor.proven_value().map(|e| &e.value),
                    Some(Value::NatLit(n)) if n.is_zero())
                    || matches!(predecessor.proven_value().map(|e| &e.value),
                        Some(Value::Neutral(Neutral {
                            head: NeutralHead::Const { name: zero, levels },
                            spine,
                        })) if *zero == primitives.zero && levels.is_empty() && spine.is_empty());
                if is_zero {
                    let first_value = self.expose_internal(
                        first.clone(), transparency, budget.saturating_sub(1), false, false,
                    );
                    if let Some(Value::Neutral(Neutral {
                        head: NeutralHead::Const { name: first_ctor, levels: first_levels },
                        spine: first_spine,
                    })) = first_value.proven_value().map(|e| &e.value)
                        && *first_ctor == primitives.succ
                        && first_levels.is_empty()
                        && first_spine.len() == 1
                    {
                        let result = self.expose_internal(
                            first_spine[0].clone(), transparency,
                            budget.saturating_sub(1), false, false,
                        );
                        if let Some(established) = result.proven_value() {
                            pending.clear();
                            #[cfg(feature = "diagnostics")]
                            if std::env::var_os("NUCLEUS_TRACE_NAT_SUBSUCC_ZERO").is_some() {
                                eprintln!("NUCLEUS_NAT_SUBSUCC_ZERO:certified-double-constructor");
                            }
                            return Some(established.value.clone());
                        }
                    }
                }
            }

            // Exact Lean v4.34.1 Nat.sub definition:
            //   Nat.sub a (Nat.succ b) = Nat.pred (Nat.sub a b).
            // Retain both source argument closures; a new opaque binder
            // holds the already-evaluated, typed inner native application.
            // It never equates two different b values or indexes.
            if let Some(Value::Neutral(Neutral {
                head: NeutralHead::Const { name: ctor, levels },
                spine,
            })) = second_value.proven_value().map(|e| &e.value)
                && *ctor == primitives.succ && levels.is_empty() && spine.len() == 1
                && let (Some(pred), Some(bvar0)) =
                    (primitives.pred, primitives.virtual_bvar_zero)
            {
                let sub_thunk = Closure::new(
                    bvar0,
                    EnvFrame::empty().extend_neutral(Neutral {
                        head: NeutralHead::Const { name, levels: vec![] },
                        spine: vec![first.clone(), spine[0].clone()],
                    }),
                );
                pending.clear();
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_NAT_SUBSUCC").is_some() {
                    eprintln!("NUCLEUS_NAT_SUBSUCC:checked-source-successor:pred={:?}", pred);
                }
                return Some(Value::Neutral(Neutral {
                    head: NeutralHead::Const { name: pred, levels: vec![] },
                    spine: vec![sub_thunk],
                }));
            }
            // No constructor evidence for the major: keep the expression
            // neutral on the cheap path; Full transparency retains the
            // definitional fallback. No equality is asserted here.
            if transparency != Transparency::Full
                && !matches!(second_value.proven_value().map(|e| &e.value), Some(Value::NatLit(_)))
            {
                pending.clear();
                return Some(Value::Neutral(Neutral {
                    head: NeutralHead::Const { name, levels: vec![] },
                    spine: vec![first, second],
                }));
            }
        }

        let first_value = self
            .expose_internal(first, transparency, budget.saturating_sub(1), false, false)
            .proven_value()?
            .value
            .clone();
        let second_value = self
            .expose_internal(second, transparency, budget.saturating_sub(1), false, false)
            .proven_value()?
            .value
            .clone();
        let (Value::NatLit(first), Value::NatLit(second)) = (first_value, second_value) else {
            return None;
        };
        pending.clear();
        Some(match operation {
            Operation::Pred => unreachable!("unary Nat.pred handled above"),
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
            Operation::Beq => unreachable!("Nat.beq handled before literal-only operations"),
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
                    EnvBinding::Free(_) | EnvBinding::Neutral(_) => return None,
                },
                Expr::Const { name, .. } => {
                    arguments.reverse();
                    return Some((*name, arguments));
                }
                _ => return None,
            }
        }
    }

    /// Reproduce one *existing* certified Nat.rec iota rule on an already
    /// evaluated neutral application. The expression evaluator normally
    /// performs this earlier, but type conversion can retain a rigid
    /// neutral because its cheap exposure precedes Full unfolding.
    ///
    /// No equality is guessed: only the installed recursor metadata,
    /// literal zero major, original minor arguments, RHS syntax and
    /// universe substitution are allowed to produce the reduct.
    pub(crate) fn qualified_nat_zero_recursor_result(
        &self,
        neutral: &Neutral,
        budget: usize,
    ) -> Judgment<Value> {
        if budget < 32 {
            return Judgment::unknown("natrec-zero-iota-small-budget");
        }
        let NeutralHead::Const { name, levels } = &neutral.head else {
            return Judgment::unknown("natrec-zero-iota-nonconst");
        };
        let (Some(nat), Some(reduction)) = (
            self.nat_primitives.as_ref(),
            self.recursor_reductions.get(name),
        ) else {
            return Judgment::unknown("natrec-zero-iota-missing-authority");
        };
        if *name != nat.recursor
            || reduction.num_params != 0
            || reduction.num_indices != 0
            || reduction.rules.len() != 2
            || reduction.level_params.len() != levels.len()
            || !reduction.rules.iter().any(|r| {
                r.constructor == nat.succ && r.num_fields == 1 && r.num_params == 0
            })
        {
            return Judgment::unknown("natrec-zero-iota-interface");
        }
        let required = reduction.num_params + 1
            + reduction.rules.len() + reduction.num_indices + 1;
        if neutral.spine.len() != required {
            return Judgment::unknown("natrec-zero-iota-arity");
        }
        let Some(rule) = reduction.rules.iter().find(|r| {
            r.constructor == nat.zero && r.num_fields == 0 && r.num_params == 0
        }) else {
            return Judgment::unknown("natrec-zero-iota-zero-rule");
        };
        let Some(major) = neutral.spine.last() else {
            return Judgment::unknown("natrec-zero-iota-major-missing");
        };
        let major_exposed = self.expose(
            major.clone(), Transparency::Full, budget.saturating_sub(1).min(256),
        );
        if !matches!(
            major_exposed.proven_value(),
            Some(Value::NatLit(n)) if n.is_zero()
        ) {
            return Judgment::unknown("natrec-zero-iota-major-not-canonical");
        }

        let substitution = reduction.level_params.iter().copied()
            .zip(levels.iter().cloned()).collect::<Vec<_>>();
        let mut result = Closure::with_levels(
            rule.rhs, EnvFrame::empty(), LevelSubstitution::new(substitution),
        );
        let prefix_len = reduction.num_params + 1 + reduction.rules.len();
        for arg in neutral.spine.iter().take(prefix_len) {
            let mut lets = 0usize;
            loop {
                match self.expressions.get(result.expr) {
                    Some(Expr::Lam { body, .. }) => {
                        result = result.sibling(*body, result.env.extend(arg.clone()));
                        break;
                    }
                    Some(Expr::Let { value, body, .. }) if lets < 32 => {
                        let value = result.sibling(*value, result.env.clone());
                        result = result.sibling(*body, result.env.extend(value));
                        lets += 1;
                    }
                    _ => return Judgment::unknown("natrec-zero-iota-rhs-telescope"),
                }
            }
        }
        self.expose(
            result, Transparency::Full, budget.saturating_sub(1).min(512),
        )
    }

    /// Re-evaluate a nested, *independently registered* two-case recursor
    /// whose major is itself a suspended recursor. The only successful path
    /// observes a constructor with the correct universe/arity, then replays
    /// the checked original iota RHS; neither constructor nor result is
    /// predicted by the desired conversion.
    pub(crate) fn certified_nested_two_case_recursor_result(
        &self, neutral: &Neutral, budget: usize, depth: usize,
    ) -> Judgment<Value> {
        if depth >= 4 || budget < 64 {
            return Judgment::unknown("nested-recursor-depth-or-budget");
        }
        let NeutralHead::Const { name, levels } = &neutral.head else {
            return Judgment::unknown("nested-recursor-not-constant");
        };
        let Some(reduction) = self.recursor_reductions.get(name) else {
            return Judgment::unknown("nested-recursor-missing-source-rule");
        };
        if reduction.rules.len() != 2 || reduction.level_params.len() != levels.len() {
            return Judgment::unknown("nested-recursor-unqualified-interface");
        }
        let required = reduction.num_params.saturating_add(1)
            .saturating_add(reduction.rules.len())
            .saturating_add(reduction.num_indices).saturating_add(1);
        if neutral.spine.len() != required {
            return Judgment::unknown("nested-recursor-argument-count");
        }
        let Some(major) = neutral.spine.last() else {
            return Judgment::unknown("nested-recursor-major-missing");
        };
        let initial = self.expose(
            major.clone(), Transparency::Full, budget.saturating_sub(1).min(384),
        );
        let Some(mut observed) = initial.proven_value().cloned() else {
            return Judgment::unknown("nested-recursor-major-unknown");
        };
        for step in depth..4 {
            let Value::Neutral(inner) = &observed else {
                return Judgment::unknown("nested-recursor-major-not-constructor");
            };
            let NeutralHead::Const { name: inner_name, levels: inner_levels } = &inner.head else {
                return Judgment::unknown("nested-recursor-major-not-constant");
            };
            if let Some(rule) = reduction.rules.iter().find(|rule| {
                rule.constructor == *inner_name
                    && inner.spine.len() == rule.num_params + rule.num_fields
            }) {
                let expected_ctor_levels = rule.constructor_level_params.iter()
                    .map(|param| {
                        reduction.level_params.iter().position(|p| p == param)
                            .and_then(|i| levels.get(i))
                            .cloned()
                    }).collect::<Option<Vec<_>>>();
                if expected_ctor_levels.as_ref() != Some(inner_levels) {
                    return Judgment::unknown("nested-recursor-constructor-universe");
                }
                let substitutions = reduction.level_params.iter().copied()
                    .zip(levels.iter().cloned()).collect::<Vec<_>>();
                let mut rhs = Closure::with_levels(
                    rule.rhs, EnvFrame::empty(), LevelSubstitution::new(substitutions),
                );
                let prefix_len = reduction.num_params + 1 + reduction.rules.len();
                for arg in neutral.spine[..prefix_len].iter()
                    .chain(inner.spine[rule.num_params..].iter())
                {
                    let mut lets = 0usize;
                    loop {
                        match self.expressions.get(rhs.expr) {
                            Some(Expr::Lam { body, .. }) => {
                                rhs = rhs.sibling(*body, rhs.env.extend(arg.clone()));
                                break;
                            }
                            Some(Expr::Let { value, body, .. }) if lets < 24 => {
                                let bound = rhs.sibling(*value, rhs.env.clone());
                                rhs = rhs.sibling(*body, rhs.env.extend(bound));
                                lets += 1;
                            }
                            _ => return Judgment::unknown("nested-recursor-rhs-telescope"),
                        }
                    }
                }
                return self.expose(
                    rhs, Transparency::Full, budget.saturating_sub(1).min(512),
                );
            }
            if *inner_name == *name || self.recursor_reductions.contains_key(inner_name) {
                let child = self.certified_nested_two_case_recursor_result(
                    inner, budget / 2, step + 1,
                );
                let Some(child) = child.proven_value() else {
                    return Judgment::unknown("nested-recursor-child-not-reduced");
                };
                if *child == observed {
                    return Judgment::unknown("nested-recursor-child-nonprogress");
                }
                observed = child.clone();
                continue;
            }
            return Judgment::unknown("nested-recursor-major-head-not-rule");
        }
        Judgment::unknown("nested-recursor-chain-exhausted")
    }

    fn rule_constructor_application(
        &self,
        target: &Closure,
        reduction: &RecursorReduction,
        transparency: Transparency,
        budget: usize,
    ) -> Option<(NameId, Vec<Closure>)> {
        let matches_rule = |constructor: NameId, arity: usize| {
            reduction.rules.iter().any(|rule| {
                rule.constructor == constructor
                    && arity == rule.num_params + rule.num_fields
            })
        };
        if let Some((constructor, arguments)) = self.constructor_application(target)
            && matches_rule(constructor, arguments.len())
        {
            return Some((constructor, arguments));
        }
        if transparency != Transparency::Full {
            return None;
        }
        // Allocate extra constructor exposure only for the certified
        // Bool.rec over a checked, fully applied Nat.beq.  This does not
        // infer the major constructor: exposure must produce the registered
        // Bool.false/Bool.true constructor and exact arity below.
        let bool_rules = self.bool_primitives.as_ref().is_some_and(|bools| {
            reduction.rules.len() == 2
                && reduction.rules.iter().any(|r| r.constructor == bools.false_ctor)
                && reduction.rules.iter().any(|r| r.constructor == bools.true_ctor)
        });
        let mut head = target.expr;
        let mut arity = 0usize;
        while let Some(Expr::App { fun, .. }) = self.expressions.get(head) {
            arity += 1;
            if arity > 2 { break; }
            head = *fun;
        }
        let nat_beq_major = arity == 2 && self.nat_primitives.as_ref().is_some_and(|nat| {
            matches!(self.expressions.get(head),
                Some(Expr::Const { name, levels })
                    if Some(*name) == nat.beq && levels.is_empty())
        });
        let certified_nat_rec = self.nat_primitives.as_ref().is_some_and(|nat| {
            reduction.rules.len() == 2
                && matches_rule(nat.zero, 0)
                && matches_rule(nat.succ, 1)
        });
        // Qualified Bool.rec may receive its major through a checked
        // lexical substitution rather than as a literal Nat.beq call.
        // Extra exposure searches for the registered constructor; it NEVER
        // assumes that a bound major is true or false.
        let captured_bool_major = match self.expressions.get(target.expr) {
            Some(Expr::BVar(index)) =>
                matches!(target.env.lookup(*index), Some(EnvBinding::Closure(_))),
            _ => false,
        };
        // A second certified two-case, unary-field recursor can be
        // nested outside the Bool.rec. Evaluate the *actual* captured
        // major until it exposes a registered constructor; no outcome
        // is guessed from a result-type shape or desired Bool value.
        let qualified_two_case_major = captured_bool_major
            && reduction.rules.len() == 2
            && reduction.rules.iter().all(|r| {
                r.num_params == 1 && r.num_fields == 1
            });
        let major_cap = if bool_rules && nat_beq_major {
            256
        } else if qualified_two_case_major {
            256
        } else if bool_rules && captured_bool_major {
            128
        } else if certified_nat_rec {
            128
        } else {
            16
        };
        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_CAPTURED_REC_CHAIN").is_some()
            && qualified_two_case_major
        {
            use std::sync::atomic::{AtomicUsize, Ordering};
            static TRACES: AtomicUsize = AtomicUsize::new(0);
            if TRACES.fetch_add(1, Ordering::Relaxed) < 32 {
                eprintln!(
                    "NUCLEUS_CAPTURED_REC_CHAIN:major={target:?}:cap={major_cap}:rules={}:budget={budget}",
                    reduction.rules.len()
                );
            }
        }
        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_CAPTURED_BOOL_REC").is_some()
            && bool_rules && captured_bool_major
        {
            use std::sync::atomic::{AtomicUsize,Ordering};
            static COUNT: AtomicUsize = AtomicUsize::new(0);
            if COUNT.fetch_add(1, Ordering::Relaxed) < 32 {
                eprintln!(
                    "NUCLEUS_CAPTURED_BOOL_REC:major={target:?}:major_cap={major_cap}:source_certified_rules={bool_rules}:budget={budget}"
                );
            }
        }
        let exposed = self
            .expose_internal(
                target.clone(),
                Transparency::Full,
                budget.saturating_sub(1).min(major_cap),
                false,
                false,
            )
            .proven_value()?
            .value
            .clone();
        match exposed {
            Value::Neutral(Neutral {
                head: NeutralHead::Const { name, .. },
                spine,
            }) if matches_rule(name, spine.len()) => Some((name, spine)),
            // Lean's trusted Nat numeral representation is definitionally
            // constructor-shaped. A recursor with independently installed
            // Nat.zero/Nat.succ iota rules may inspect that exact numeral.
            // Only reuse a predecessor that exists in the checked export;
            // no synthetic expression or rule is fabricated.
            Value::NatLit(number) => {
                let nat = self.nat_primitives.as_ref()?;
                if std::env::var_os("NUCLEUS_TRACE_NAT_IOTA").is_some() { eprintln!("NUCLEUS_NAT_LITERAL_IOTA:major={number:?}:zero_rule={}:succ_rule={}", matches_rule(nat.zero,0), matches_rule(nat.succ,1)); }
                if number.is_zero() && matches_rule(nat.zero, 0) {
                    return Some((nat.zero, Vec::new()));
                }
                if !matches_rule(nat.succ, 1) {
                    return None;
                }
                let predecessor = number.pred()?;
                // Reuse the earliest indexed numeral first. This preserves
                // the exhaustive fallback for exports that store it later,
                // but avoids a full expression-table walk in the common case.
                let pred_id = (0u64..4096).find_map(|id| {
                    matches!(
                        self.expressions.get(ExprId(id)),
                        Some(Expr::NatLit(candidate)) if candidate == &predecessor
                    ).then_some(ExprId(id))
                }).or_else(|| self.expressions.iter_raw().find_map(|(id, expr)| {
                    match expr {
                        Expr::NatLit(candidate) if candidate == &predecessor => Some(ExprId(id)),
                        _ => None,
                    }
                }))?;
                if std::env::var_os("NUCLEUS_TRACE_NAT_IOTA").is_some() { eprintln!("NUCLEUS_NAT_LITERAL_IOTA:constructor_succ:pred_id={pred_id:?}"); }
                Some((nat.succ, vec![Closure::new(pred_id, EnvFrame::empty())]))
            }
            _ => None,
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
