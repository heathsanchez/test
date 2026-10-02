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
    EqualityK,
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
    pub num_params: usize,
    pub num_fields: usize,
    pub rhs: ExprId,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RecursorReduction {
    /// Enabled only after the exact Eq declaration, recursor type and rule
    /// have been independently validated by the admission checker.
    pub eq_k: bool,
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
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Exposure {
    pub value: Value,
    pub transitions: Vec<TransitionWitness>,
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
enum SupportClosureRoot {
    Expression(ExprId),
    NatLiteral(crate::nat::BigNat),
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
struct SupportClosureKey {
    root: SupportClosureRoot,
    levels: LevelSubstitution,
    bindings: Vec<(usize, SupportBindingKey)>,
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
enum SupportBindingKey {
    Free(FreeId),
    Closure(Box<SupportClosureKey>),
    Neutral(Box<SupportNeutralKey>),
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
struct SupportNeutralKey {
    head: SupportNeutralHeadKey,
    spine: Vec<SupportClosureKey>,
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
enum SupportNeutralHeadKey {
    Free(FreeId),
    Const {
        name: NameId,
        levels: Vec<crate::level::LevelTerm>,
    },
    Projection {
        type_name: NameId,
        index: usize,
        structure: Box<SupportNeutralKey>,
    },
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
struct ExposureCacheKey {
    authority: AuthorityId,
    transparency: Transparency,
    closure: SupportClosureKey,
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct CachedExposure {
    value: Value,
}

#[derive(Debug, Default)]
pub(crate) struct ExposureCacheData {
    exposures: HashMap<ExposureCacheKey, CachedExposure>,
    hits: u64,
}

pub(crate) type ExposureCache = Rc<RefCell<ExposureCacheData>>;

pub(crate) fn new_exposure_cache() -> ExposureCache {
    Rc::new(RefCell::new(ExposureCacheData::default()))
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
    quot_primitives: Option<QuotPrimitives>,
    exposure_cache: ExposureCache,
}

impl<'a> Machine<'a> {
    fn collect_support_outer_bvars(
        &self,
        expression: ExprId,
        depth: usize,
        budget: usize,
        out: &mut Vec<usize>,
    ) -> Option<()> {
        if budget == 0 {
            return None;
        }
        let node = self.expressions.get(expression)?;
        let next = budget - 1;
        match node {
            Expr::BVar(index) => {
                let index = usize::try_from(*index).ok()?;
                if index >= depth {
                    out.push(index - depth);
                }
            }
            Expr::NatLit(_) | Expr::StrLit(_) | Expr::Sort(_) | Expr::Const { .. } => {}
            Expr::App { fun, arg } => {
                self.collect_support_outer_bvars(*fun, depth, next, out)?;
                self.collect_support_outer_bvars(*arg, depth, next, out)?;
            }
            Expr::Lam { domain, body } | Expr::Pi { domain, body } => {
                self.collect_support_outer_bvars(*domain, depth, next, out)?;
                self.collect_support_outer_bvars(
                    *body,
                    depth.checked_add(1)?,
                    next,
                    out,
                )?;
            }
            Expr::Let { ty, value, body } => {
                self.collect_support_outer_bvars(*ty, depth, next, out)?;
                self.collect_support_outer_bvars(*value, depth, next, out)?;
                self.collect_support_outer_bvars(
                    *body,
                    depth.checked_add(1)?,
                    next,
                    out,
                )?;
            }
            Expr::Proj { structure, .. } => {
                self.collect_support_outer_bvars(*structure, depth, next, out)?;
            }
        }
        Some(())
    }

    fn support_binding_key(
        &self,
        binding: EnvBinding,
        budget: &mut usize,
    ) -> Option<SupportBindingKey> {
        if *budget == 0 {
            return None;
        }
        *budget -= 1;
        match binding {
            EnvBinding::Free(free) => Some(SupportBindingKey::Free(free)),
            EnvBinding::Closure(closure) => Some(SupportBindingKey::Closure(Box::new(
                self.support_closure_key(&closure, budget)?,
            ))),
            EnvBinding::Neutral(neutral) => Some(SupportBindingKey::Neutral(Box::new(
                self.support_neutral_key(&neutral, budget)?,
            ))),
        }
    }

    fn support_neutral_key(
        &self,
        neutral: &Neutral,
        budget: &mut usize,
    ) -> Option<SupportNeutralKey> {
        if *budget == 0 {
            return None;
        }
        *budget -= 1;
        let head = match &neutral.head {
            NeutralHead::Free(free) => SupportNeutralHeadKey::Free(*free),
            NeutralHead::Const { name, levels } => SupportNeutralHeadKey::Const {
                name: *name,
                levels: levels.clone(),
            },
            NeutralHead::Projection {
                type_name,
                index,
                structure,
            } => SupportNeutralHeadKey::Projection {
                type_name: *type_name,
                index: *index,
                structure: Box::new(self.support_neutral_key(structure, budget)?),
            },
        };
        let mut spine = Vec::with_capacity(neutral.spine.len());
        for closure in &neutral.spine {
            spine.push(self.support_closure_key(closure, budget)?);
        }
        Some(SupportNeutralKey { head, spine })
    }

    fn support_closure_key(
        &self,
        closure: &Closure,
        budget: &mut usize,
    ) -> Option<SupportClosureKey> {
        if *budget == 0 {
            return None;
        }
        *budget -= 1;
        let root = if let Some(expression) = closure.expression() {
            SupportClosureRoot::Expression(expression)
        } else {
            SupportClosureRoot::NatLiteral(closure.literal()?.clone())
        };
        let mut bindings = Vec::new();
        if let SupportClosureRoot::Expression(expression) = root {
            let mut offsets = Vec::new();
            self.collect_support_outer_bvars(expression, 0, 4096, &mut offsets)?;
            offsets.sort_unstable();
            offsets.dedup();
            bindings.reserve(offsets.len());
            for offset in offsets {
                let index = u64::try_from(offset).ok()?;
                let binding = closure.env.lookup(index)?;
                bindings.push((offset, self.support_binding_key(binding, budget)?));
            }
        }
        Some(SupportClosureKey {
            root,
            levels: closure.levels.clone(),
            bindings,
        })
    }

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
            quot_primitives: None,
            exposure_cache: new_exposure_cache(),
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

    pub fn with_quot_primitives(mut self, primitives: Option<QuotPrimitives>) -> Self {
        self.quot_primitives = primitives;
        self
    }

    pub(crate) fn with_exposure_cache(mut self, cache: ExposureCache) -> Self {
        self.exposure_cache = cache;
        self
    }

    pub fn expose(
        &self,
        closure: Closure,
        transparency: Transparency,
        budget: usize,
    ) -> Judgment<Value> {
        let cache_enabled =
            std::env::var_os("NUCLEUS_DISABLE_SUPPORT_EXPOSURE_CACHE").is_none();
        let cache_key = if cache_enabled {
            let mut support_budget = 256usize;
            self.support_closure_key(&closure, &mut support_budget)
                .map(|closure| ExposureCacheKey {
                    authority: self.authority,
                    transparency,
                    closure,
                })
        } else {
            None
        };

        if let Some(key) = cache_key.as_ref() {
            let mut cache = self.exposure_cache.borrow_mut();
            if let Some(value) = cache.exposures.get(key).map(|entry| entry.value.clone()) {
                cache.hits += 1;
                if std::env::var_os("NUCLEUS_TRACE_SUPPORT_EXPOSURE_CACHE").is_some()
                    && cache.hits.is_power_of_two()
                {
                    eprintln!(
                        "NUCLEUS_SUPPORT_EXPOSURE_CACHE:hits={}:entries={}",
                        cache.hits,
                        cache.exposures.len()
                    );
                }
                return Judgment::proven(value, "cached-support-exposure");
            }
        }

        let result = self
            .expose_internal(closure, transparency, budget, false)
            .map(|exposure| exposure.value);

        if let (Some(key), Judgment::Proven { value, .. }) = (cache_key, &result) {
            self.exposure_cache.borrow_mut().exposures.entry(key).or_insert_with(|| {
                CachedExposure {
                    value: value.clone(),
                }
            });
        }
        result
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
            if let Some(value) = closure.literal() {
                if !pending.is_empty() {
                    return Judgment::unknown("nat-literal-applied-as-function");
                }
                record_transition(&mut transitions, record_witnesses, TransitionWitness::Rigid);
                return exposed(Value::NatLit(value.clone()), transitions);
            }
            let expr = closure
                .expression()
                .expect("nonliteral closure has an expression");
            if !visited.insert((self.authority, expr, closure.env.id())) {
                return Judgment::unknown("reduction-cycle");
            }

            let Some(expression) = self.expressions.get(expr) else {
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
                            if reduction.eq_k && arguments.len() == 6 {
                                let left = self.expose_internal(
                                    arguments[1].clone(),
                                    Transparency::Opaque,
                                    budget.min(64),
                                    false,
                                );
                                let right = self.expose_internal(
                                    arguments[4].clone(),
                                    Transparency::Opaque,
                                    budget.min(64),
                                    false,
                                );
                                if let (Some(l), Some(r)) =
                                    (left.proven_value(), right.proven_value())
                                    && l.value == r.value
                                {
                                    pending.truncate(offset);
                                    closure = arguments[3].clone();
                                    visited.clear();
                                    record_transition(
                                        &mut transitions,
                                        record_witnesses,
                                        TransitionWitness::EqualityK,
                                    );
                                    continue;
                                }
                            }
                            let target = arguments.last().expect("required includes target");
                            if let Some((constructor, constructor_arguments)) = self
                                .constructor_application(target)
                                .filter(|(constructor, _)| {
                                    reduction
                                        .rules
                                        .iter()
                                        .any(|r| r.constructor == *constructor)
                                })
                                .or_else(|| {
                                    if transparency != Transparency::Full {
                                        return None;
                                    }
                                    self.reduced_constructor_application(
                                        *name,
                                        target,
                                        budget.min(256),
                                    )
                                })
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
                    let exposed_structure =
                        self.expose_internal(structure, transparency, budget, false);
                    let Some(exposure) = exposed_structure.proven_value() else {
                        return Judgment::unknown("projection-structure-stuck");
                    };
                    let Value::Neutral(neutral) = &exposure.value else {
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
                        // A nonconstructor head is stuck, not a projection refutation.
                        // Preserve the field identity and every pending application.
                        NeutralHead::Const { .. }
                        | NeutralHead::Free(_)
                        | NeutralHead::Projection { .. } => {
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

    // Full conversion may expose a computed major. Cheap/opaque conversion
    // retains the original spine, preserving the qualified congruence shortcut.
    // Only a matching independently admitted constructor rule can consume it.
    fn reduced_constructor_application(
        &self,
        recursor: NameId,
        target: &Closure,
        budget: usize,
    ) -> Option<(NameId, Vec<Closure>)> {
        let result = self.expose_internal(
            target.clone(),
            Transparency::Full,
            budget.saturating_sub(1),
            false,
        );
        match &result.proven_value()?.value {
            Value::Neutral(neutral) => {
                let NeutralHead::Const { name, .. } = neutral.head else {
                    return None;
                };
                Some((name, neutral.spine.clone()))
            }
            Value::NatLit(value) => {
                let nat = self.nat_primitives.as_ref()?;
                if recursor != nat.recursor {
                    return None;
                }
                if value.is_zero() {
                    Some((nat.zero, Vec::new()))
                } else {
                    Some((nat.succ, vec![Closure::nat_literal(value.pred()?)]))
                }
            }
            _ => None,
        }
    }

    fn constructor_application(&self, target: &Closure) -> Option<(NameId, Vec<Closure>)> {
        let mut closure = target.clone();
        let mut arguments = Vec::new();
        loop {
            match self.expressions.get(closure.expression()?)? {
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
