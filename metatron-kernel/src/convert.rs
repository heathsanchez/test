use std::collections::{HashMap, HashSet};

use crate::id::ExprId;
use crate::judgment::Judgment;
use crate::level::level_equal;
use crate::machine::Transparency;
use crate::syntax::Expr;
use crate::typecheck::{TypeChecker, TypeValue};
use crate::value::{Closure, EnvBinding, FreeId, Neutral, NeutralHead, Value};

type ConversionVisitKey = (crate::machine::AuthorityId, TypeValue, TypeValue);
const INLINE_CONVERSION_VISIT_CAPACITY: usize = 8;

struct ConversionVisitSet {
    inline: [Option<ConversionVisitKey>; INLINE_CONVERSION_VISIT_CAPACITY],
    len: usize,
    overflow: Option<HashSet<ConversionVisitKey>>,
}

impl ConversionVisitSet {
    #[inline]
    fn new() -> Self {
        Self {
            inline: std::array::from_fn(|_| None),
            len: 0,
            overflow: None,
        }
    }

    #[inline]
    fn insert(&mut self, key: ConversionVisitKey) -> bool {
        if let Some(overflow) = self.overflow.as_mut() {
            return overflow.insert(key);
        }
        if self.inline[..self.len]
            .iter()
            .flatten()
            .any(|existing| existing == &key)
        {
            return false;
        }
        if self.len < INLINE_CONVERSION_VISIT_CAPACITY {
            self.inline[self.len] = Some(key);
            self.len += 1;
            return true;
        }

        let mut overflow = HashSet::with_capacity(INLINE_CONVERSION_VISIT_CAPACITY * 2);
        for slot in &mut self.inline[..self.len] {
            overflow.insert(slot.take().expect("initialized conversion visit slot"));
        }
        let inserted = overflow.insert(key);
        self.overflow = Some(overflow);
        inserted
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DeltaPolicy {
    PreferredOnly,
    GuardedSemanticFallback,
}

#[cfg(test)]
use std::cell::Cell;

#[cfg(test)]
thread_local! {
    static TRUSTED_CONVERSION_CALLS: Cell<u64> = const { Cell::new(0) };
}

pub fn convert(
    checker: &TypeChecker<'_>,
    left: &TypeValue,
    right: &TypeValue,
    budget: usize,
) -> Judgment<()> {
    convert_with_policy(
        checker,
        left,
        right,
        budget,
        DeltaPolicy::GuardedSemanticFallback,
    )
}

pub fn convert_with_policy(
    checker: &TypeChecker<'_>,
    left: &TypeValue,
    right: &TypeValue,
    budget: usize,
    delta_policy: DeltaPolicy,
) -> Judgment<()> {
    convert_with_policy_at_depth(checker, left, right, budget, delta_policy, 0)
}

pub(crate) fn convert_with_policy_at_depth(
    checker: &TypeChecker<'_>,
    left: &TypeValue,
    right: &TypeValue,
    budget: usize,
    delta_policy: DeltaPolicy,
    initial_depth: usize,
) -> Judgment<()> {
    convert_with_policy_in_context(
        checker,
        left,
        right,
        budget,
        delta_policy,
        initial_depth,
        &[],
    )
}

pub(crate) fn convert_with_policy_in_context(
    checker: &TypeChecker<'_>,
    left: &TypeValue,
    right: &TypeValue,
    budget: usize,
    delta_policy: DeltaPolicy,
    initial_depth: usize,
    context: &[TypeValue],
) -> Judgment<()> {
    let mut congruence_attempts = 32;
    convert_in_context_with_congruence(
        checker,
        left,
        right,
        budget,
        delta_policy,
        initial_depth,
        context,
        0,
        &mut congruence_attempts,
        true,
    )
}

// The new proof-irrelevance premise gets one bounded conversion probe.
// Disable this extension throughout the nested comparison, including all
// application/projection congruence branches, so it cannot recursively reset
// its own quota. Existing structurally established proof equality is retained.
pub(crate) fn convert_proof_types_in_context(
    checker: &TypeChecker<'_>, left: &TypeValue, right: &TypeValue,
    budget: usize, delta_policy: DeltaPolicy, depth: usize, context: &[TypeValue],
) -> Judgment<()> {
    convert_in_context_with_congruence(checker, left, right, budget.min(256),
        delta_policy, depth, context, 0, &mut 32, false)
}

// Speculative congruence has shared attempt and depth bounds. Exhaustion merely
// declines this sufficient rule and leaves the established conversion path.
fn convert_in_context_with_congruence(
    checker: &TypeChecker<'_>,
    left: &TypeValue,
    right: &TypeValue,
    budget: usize,
    delta_policy: DeltaPolicy,
    initial_depth: usize,
    context: &[TypeValue],
    congruence_depth: usize,
    congruence_attempts: &mut usize,
    allow_proof_type_conversion: bool,
) -> Judgment<()> {
    #[cfg(test)]
    TRUSTED_CONVERSION_CALLS.with(|calls| calls.set(calls.get() + 1));
    #[cfg(feature = "diagnostics")]
    crate::diagnostics::conversion();

    let mut remaining = budget;
    let mut work = vec![(left.clone(), right.clone(), initial_depth, context.to_vec())];
    let mut visited = ConversionVisitSet::new();
    let mut unit_like_frees = HashMap::new();
    let mut proposition_frees = HashSet::new();
    let mut proof_frees = HashMap::new();
    let mut proof_function_frees = HashMap::new();

    while let Some((left, right, depth, local_context)) = work.pop() {
        let context = local_context.as_slice();
        if left == right {
            continue;
        }
        if remaining == 0 {
            return Judgment::unknown("conversion-budget-exhausted");
        }
        remaining -= 1;
        if !visited.insert((checker.authority(), left.clone(), right.clone())) {
            continue;
        }

        // Residual-generated function eta capability.  This is deliberately
        // syntactic and contraction-only: (fun x => f x) may contract to f
        // exactly when the bound variable does not occur in f.  No unfolding,
        // structure eta authority is introduced here; proof irrelevance, when
        // available, is a separately guarded typed-binder consequence below.
        if let (TypeValue::Term(left_term), TypeValue::Term(right_term)) = (&left, &right) {
            if let Some(contracted) = eta_contract(checker, left_term, depth) {
                work.push((
                    TypeValue::Term(contracted),
                    TypeValue::Term(right_term.clone()),
                    depth,
                    local_context.clone(),
                ));
                continue;
            }
            if let Some(contracted) = eta_contract(checker, right_term, depth) {
                work.push((
                    TypeValue::Term(left_term.clone()),
                    TypeValue::Term(contracted),
                    depth,
                    local_context.clone(),
                ));
                continue;
            }
        }

        if let (TypeValue::Term(left_term), TypeValue::Term(right_term)) = (&left, &right)
            && checker.proof_terms_same_proposition(left_term, right_term, context, remaining,
                delta_policy, depth, allow_proof_type_conversion)
        {
            continue;
        }

        if let (TypeValue::Term(left_term), TypeValue::Term(right_term)) = (&left, &right)
            && unit_like_free_pair(checker, left_term, right_term, &unit_like_frees, remaining)
        {
            continue;
        }

        if let (TypeValue::Term(left_term), TypeValue::Term(right_term)) = (&left, &right)
            && proof_free_pair(checker, left_term, right_term, &proof_frees, remaining)
        {
            continue;
        }

        if let (TypeValue::Term(left_term), TypeValue::Term(right_term)) = (&left, &right)
            && fixed_proof_function_application_pair(
                checker,
                left_term,
                right_term,
                &proof_function_frees,
                remaining,
            )
        {
            continue;
        }

        if depth == context.len()
            && distinct_rigid_local_terms(checker, &left, &right, context, remaining)
        {
            return Judgment::refuted("distinct-rigid-local-terms");
        }

        match (left, right) {
            (TypeValue::Sort(left), TypeValue::Sort(right)) => {
                match level_equal(left, right, remaining) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                }
            }
            (
                TypeValue::Pi {
                    domain: left_domain,
                    body: left_body,
                },
                TypeValue::Pi {
                    domain: right_domain,
                    body: right_body,
                },
            ) => {
                if let Some(free) = fresh_local(depth) {
                    if let (Some(left_key), Some(right_key)) = (
                        checker.unit_like_type_key(&left_domain, remaining),
                        checker.unit_like_type_key(&right_domain, remaining),
                    ) && left_key == right_key
                    {
                        unit_like_frees.insert(free, left_key);
                    }

                    if checker.type_value_is_prop_sort(&left_domain, remaining)
                        && checker.type_value_is_prop_sort(&right_domain, remaining)
                    {
                        proposition_frees.insert(free);
                    } else if let (Some(left_prop), Some(right_prop)) = (
                        bare_free_type(checker, &left_domain, remaining),
                        bare_free_type(checker, &right_domain, remaining),
                    ) && left_prop == right_prop
                        && proposition_frees.contains(&left_prop)
                    {
                        proof_frees.insert(free, left_prop);
                    }

                    if let (Some(left_key), Some(right_key)) = (
                        checker.fixed_proof_function_type_key(&left_domain, remaining),
                        checker.fixed_proof_function_type_key(&right_domain, remaining),
                    ) && left_key == right_key
                    {
                        proof_function_frees.insert(free, left_key);
                    }
                }
                let mut body_context = local_context.clone();
                if body_context.len() == depth {
                    body_context.push((*left_domain).clone());
                }
                work.push((
                    *left_body,
                    *right_body,
                    depth.saturating_add(1),
                    body_context,
                ));
                work.push((*left_domain, *right_domain, depth, local_context));
            }
            (TypeValue::Term(left), TypeValue::Term(right)) => {
                let machine = checker.machine();
                // Compare equal constant heads and their arguments before
                // delta reduction can erase a shared application. In particular,
                // this preserves a projection function's original structure
                // argument while proving id c = c inside that argument.
                // This is a positive-only rule: failure of a premise says
                // nothing about the applications (the function can ignore it).
                if congruence_depth < 16 && *congruence_attempts > 0 {
                    *congruence_attempts -= 1;
                    let probe_budget = remaining.min(256);
                    let opaque_left =
                        machine.expose(left.clone(), Transparency::Opaque, probe_budget);
                    let opaque_right =
                        machine.expose(right.clone(), Transparency::Opaque, probe_budget);
                    if let (Some(Value::Neutral(lhs)), Some(Value::Neutral(rhs))) =
                        (opaque_left.proven_value(), opaque_right.proven_value())
                        && let (
                            NeutralHead::Const {
                                name: left_name, ..
                            },
                            NeutralHead::Const {
                                name: right_name, ..
                            },
                        ) = (&lhs.head, &rhs.head)
                        && left_name == right_name
                        && !lhs.spine.is_empty()
                        && lhs.spine.len() == rhs.spine.len()
                        && compare_neutral_heads(checker, lhs, rhs, probe_budget).is_proven()
                        && lhs
                            .spine
                            .iter()
                            .zip(&rhs.spine)
                            .all(|(left_arg, right_arg)| {
                                convert_in_context_with_congruence(
                                    checker,
                                    &TypeValue::Term(left_arg.clone()),
                                    &TypeValue::Term(right_arg.clone()),
                                    probe_budget / lhs.spine.len(),
                                    delta_policy,
                                    depth,
                                    context,
                                    congruence_depth + 1,
                                    congruence_attempts,
                                    allow_proof_type_conversion,
                                )
                                .is_proven()
                            })
                    {
                        continue;
                    }
                }
                let cheap_left = machine.expose(left.clone(), Transparency::Reducible, remaining);
                let cheap_right = machine.expose(right.clone(), Transparency::Reducible, remaining);
                let (Some(cheap_left), Some(cheap_right)) =
                    (cheap_left.proven_value(), cheap_right.proven_value())
                else {
                    return Judgment::unknown("conversion-exposure");
                };
                if let (Value::Neutral(l), Value::Neutral(r)) = (cheap_left, cheap_right)
                    && matches!(
                        (&l.head, &r.head),
                        (
                            NeutralHead::Projection { .. },
                            NeutralHead::Projection { .. }
                        )
                    )
                    && positive_projection_congruence(
                        checker,
                        l,
                        r,
                        remaining,
                        depth,
                        context,
                        delta_policy,
                        congruence_depth,
                        &mut 32,
                        allow_proof_type_conversion,
                    )
                {
                    continue;
                }
                match compare_values(
                    checker,
                    cheap_left,
                    cheap_right,
                    remaining,
                    depth,
                    &mut work,
                    &mut proof_function_frees,
                    context,
                ) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { .. }
                        if delta_policy == DeltaPolicy::GuardedSemanticFallback =>
                    {
                        let full_left = machine.expose(left, Transparency::Full, remaining);
                        let full_right = machine.expose(right, Transparency::Full, remaining);
                        let (Some(full_left), Some(full_right)) =
                            (full_left.proven_value(), full_right.proven_value())
                        else {
                            return Judgment::unknown("full-conversion-exposure");
                        };
                        if let (Value::Neutral(l), Value::Neutral(r)) = (full_left, full_right)
                            && matches!(
                                (&l.head, &r.head),
                                (
                                    NeutralHead::Projection { .. },
                                    NeutralHead::Projection { .. }
                                )
                            )
                            && positive_projection_congruence(
                                checker,
                                l,
                                r,
                                remaining,
                                depth,
                                context,
                                delta_policy,
                                congruence_depth,
                                &mut 32,
                                allow_proof_type_conversion,
                            )
                        {
                            continue;
                        }
                        match compare_values(
                            checker,
                            full_left,
                            full_right,
                            remaining,
                            depth,
                            &mut work,
                            &mut proof_function_frees,
                            context,
                        ) {
                            Judgment::Proven { .. } => {}
                            Judgment::Refuted { obstruction } => {
                                return Judgment::Refuted { obstruction };
                            }
                            Judgment::Unknown { residual } => {
                                return Judgment::Unknown { residual };
                            }
                        }
                    }
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                }
            }
            (TypeValue::Term(term), other) | (other, TypeValue::Term(term)) => {
                let machine = checker.machine();
                let exposed = machine.expose(term.clone(), Transparency::Reducible, remaining);
                let Some(exposed) = exposed.proven_value() else {
                    return Judgment::unknown("conversion-exposure");
                };
                let exposed = if let Some(exposed) = value_as_type(exposed, depth) {
                    exposed
                } else if delta_policy == DeltaPolicy::GuardedSemanticFallback {
                    let full = machine.expose(term, Transparency::Full, remaining);
                    let Some(full) = full.proven_value() else {
                        return Judgment::unknown("full-conversion-exposure");
                    };
                    let Some(full) = value_as_type(full, depth) else {
                        return Judgment::refuted("rigid-type-constructor-mismatch");
                    };
                    full
                } else {
                    return Judgment::refuted("rigid-type-constructor-mismatch");
                };
                work.push((exposed, other, depth, local_context));
            }
            (TypeValue::Sort(_), TypeValue::Pi { .. })
            | (TypeValue::Pi { .. }, TypeValue::Sort(_)) => {
                return Judgment::refuted("rigid-type-constructor-mismatch");
            }
        }
    }

    Judgment::proven((), "guarded-relational-conversion")
}

#[cfg(test)]
pub(crate) fn reset_test_conversion_calls() {
    TRUSTED_CONVERSION_CALLS.with(|calls| calls.set(0));
}

#[cfg(test)]
pub(crate) fn test_conversion_calls() -> u64 {
    TRUSTED_CONVERSION_CALLS.with(Cell::get)
}

fn distinct_rigid_local_terms(
    checker: &TypeChecker<'_>,
    left: &TypeValue,
    right: &TypeValue,
    context: &[TypeValue],
    budget: usize,
) -> bool {
    let (Some(l), Some(r)) = (
        opaque_free(checker, left, budget),
        opaque_free(checker, right, budget),
    ) else {
        return false;
    };
    if l == r {
        return false;
    }
    let (Some(lt), Some(rt)) = (context.get(l.0 as usize), context.get(r.0 as usize)) else {
        return false;
    };
    let (Some(la), Some(ra)) = (
        opaque_free(checker, lt, budget),
        opaque_free(checker, rt, budget),
    ) else {
        return false;
    };
    if la != ra {
        return false;
    }
    match context.get(la.0 as usize) {
        Some(TypeValue::Sort(crate::level::LevelTerm::Succ(_))) => true,
        Some(TypeValue::Term(t)) => matches!(
            checker
                .machine()
                .expose(t.clone(), Transparency::Opaque, budget.min(32))
                .proven_value(),
            Some(Value::Sort(crate::level::LevelTerm::Succ(_)))
        ),
        _ => false,
    }
}

fn opaque_free(checker: &TypeChecker<'_>, ty: &TypeValue, budget: usize) -> Option<FreeId> {
    let TypeValue::Term(c) = ty else {
        return None;
    };
    let exposed = checker
        .machine()
        .expose(c.clone(), Transparency::Opaque, budget.min(32));
    let Value::Neutral(n) = exposed.proven_value()? else {
        return None;
    };
    if !n.spine.is_empty() {
        return None;
    }
    if let NeutralHead::Free(f) = n.head {
        Some(f)
    } else {
        None
    }
}

fn bare_free_type(checker: &TypeChecker<'_>, ty: &TypeValue, budget: usize) -> Option<FreeId> {
    let TypeValue::Term(closure) = ty else {
        return None;
    };
    let exposed = checker
        .machine()
        .expose(closure.clone(), Transparency::Reducible, budget);
    let Value::Neutral(neutral) = exposed.proven_value()? else {
        return None;
    };
    if !neutral.spine.is_empty() {
        return None;
    }
    let NeutralHead::Free(free) = neutral.head else {
        return None;
    };
    Some(free)
}

fn fixed_proof_function_application_pair(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    proof_functions: &HashMap<FreeId, (crate::id::NameId, Vec<crate::level::LevelTerm>)>,
    budget: usize,
) -> bool {
    let machine = checker.machine();
    let left = machine.expose(left.clone(), Transparency::Reducible, budget);
    let right = machine.expose(right.clone(), Transparency::Reducible, budget);
    let (Some(Value::Neutral(left)), Some(Value::Neutral(right))) =
        (left.proven_value(), right.proven_value())
    else {
        return false;
    };
    if left.spine.is_empty() || right.spine.is_empty() || left.spine.len() != right.spine.len() {
        return false;
    }
    let (NeutralHead::Free(left_head), NeutralHead::Free(right_head)) = (&left.head, &right.head)
    else {
        return false;
    };
    left_head == right_head && proof_functions.contains_key(left_head)
}

fn proof_free_pair(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    proof_frees: &HashMap<FreeId, FreeId>,
    budget: usize,
) -> bool {
    let machine = checker.machine();
    let left = machine.expose(left.clone(), Transparency::Reducible, budget);
    let right = machine.expose(right.clone(), Transparency::Reducible, budget);
    let (Some(Value::Neutral(left)), Some(Value::Neutral(right))) =
        (left.proven_value(), right.proven_value())
    else {
        return false;
    };
    if !left.spine.is_empty() || !right.spine.is_empty() {
        return false;
    }
    let (NeutralHead::Free(left), NeutralHead::Free(right)) = (&left.head, &right.head) else {
        return false;
    };
    if left == right {
        return false;
    }
    proof_frees
        .get(left)
        .zip(proof_frees.get(right))
        .is_some_and(|(left_prop, right_prop)| left_prop == right_prop)
}

fn unit_like_free_pair(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    unit_like_frees: &HashMap<FreeId, (crate::id::NameId, Vec<crate::level::LevelTerm>)>,
    budget: usize,
) -> bool {
    let machine = checker.machine();
    let left = machine.expose(left.clone(), Transparency::Reducible, budget);
    let right = machine.expose(right.clone(), Transparency::Reducible, budget);
    let (Some(Value::Neutral(left)), Some(Value::Neutral(right))) =
        (left.proven_value(), right.proven_value())
    else {
        return false;
    };
    if !left.spine.is_empty() || !right.spine.is_empty() {
        return false;
    }
    let (NeutralHead::Free(left), NeutralHead::Free(right)) = (&left.head, &right.head) else {
        return false;
    };
    if left == right {
        return false;
    }
    let _ = (checker, budget);
    unit_like_frees
        .get(left)
        .zip(unit_like_frees.get(right))
        .is_some_and(|(left, right)| left == right)
}

fn eta_contract(checker: &TypeChecker<'_>, closure: &Closure, depth: usize) -> Option<Closure> {
    let closure = resolve_local_closure(checker, closure)?;
    let Expr::Lam { body, .. } = checker.expression(closure.expression()?)? else {
        return None;
    };
    if std::env::var_os("NUCLEUS_TRACE_ETA").is_some() {
        eprintln!(
            "NUCLEUS_ETA_BODY:closure={:?}:body={:?}:body_expr={:?}",
            closure, body, checker.expression(*body)
        );
    }
    let Expr::App { fun, arg } = checker.expression(*body)? else {
        return None;
    };
    if !matches!(checker.expression(*arg), Some(Expr::BVar(0))) {
        return None;
    }
    if expression_uses_bvar(checker, *fun, 0, 512) {
        return None;
    }
    let free = fresh_local(depth)?;
    Some(closure.sibling(*fun, closure.env.extend_free(free)))
}

// Evaluated function eta for a bare local function versus an explicit lambda.
// This is the semantic counterpart of eta_contract above: it is admitted only
// when evaluating the lambda body under a fresh local yields exactly f x, where
// f is the same bare local function and x is that fresh local.  The local's
// declared Pi domain is still compared through the ordinary conversion worklist.
fn evaluated_free_eta(
    checker: &TypeChecker<'_>,
    neutral: &Neutral,
    lambda_domain: &Closure,
    lambda_body: &Closure,
    budget: usize,
    depth: usize,
    work: &mut Vec<(TypeValue, TypeValue, usize, Vec<TypeValue>)>,
    context: &[TypeValue],
) -> bool {
    if !neutral.spine.is_empty() {
        return false;
    }
    let NeutralHead::Free(function_free) = neutral.head else {
        return false;
    };
    let Some(function_type) = context.get(function_free.0 as usize) else {
        return false;
    };
    let function_domain = match function_type {
        TypeValue::Pi { domain, .. } => (**domain).clone(),
        TypeValue::Term(_) => return false,
        TypeValue::Sort(_) => return false,
    };
    let Some(argument_free) = fresh_local(depth) else {
        return false;
    };
    let exposed_body = checker
        .machine()
        .expose(lambda_body.under_free(argument_free), Transparency::Reducible, budget);
    let Some(Value::Neutral(body_neutral)) = exposed_body.proven_value() else {
        return false;
    };
    if body_neutral.head != NeutralHead::Free(function_free) || body_neutral.spine.len() != 1 {
        return false;
    }
    let exposed_argument = checker
        .machine()
        .expose(body_neutral.spine[0].clone(), Transparency::Reducible, budget);
    let Some(Value::Neutral(argument_neutral)) = exposed_argument.proven_value() else {
        return false;
    };
    if argument_neutral.head != NeutralHead::Free(argument_free)
        || !argument_neutral.spine.is_empty()
    {
        return false;
    }
    work.push((
        function_domain,
        TypeValue::Term(lambda_domain.clone()),
        depth,
        context.to_vec(),
    ));
    true
}

fn resolve_local_closure(checker: &TypeChecker<'_>, closure: &Closure) -> Option<Closure> {
    let mut current = closure.clone();
    for _ in 0..64 {
        match checker.expression(current.expression()?)? {
            Expr::BVar(index) => match current.env.lookup(*index)? {
                EnvBinding::Closure(bound) => current = bound,
                EnvBinding::Free(_) | EnvBinding::Neutral(_) => return Some(current),
            },
            Expr::Let { value, body, .. } => {
                let value = current.sibling(*value, current.env.clone());
                current = current.sibling(*body, current.env.extend(value));
            }
            _ => return Some(current),
        }
    }
    None
}

fn expression_uses_bvar(
    checker: &TypeChecker<'_>,
    expression: ExprId,
    target: u64,
    budget: usize,
) -> bool {
    if budget == 0 {
        return true;
    }
    let Some(expression) = checker.expression(expression) else {
        return true;
    };
    let next = budget - 1;
    match expression {
        Expr::BVar(index) => *index == target,
        Expr::NatLit(_) | Expr::StrLit(_) | Expr::Sort(_) | Expr::Const { .. } => false,
        Expr::App { fun, arg } => {
            expression_uses_bvar(checker, *fun, target, next)
                || expression_uses_bvar(checker, *arg, target, next)
        }
        Expr::Lam { domain, body } | Expr::Pi { domain, body } => {
            expression_uses_bvar(checker, *domain, target, next)
                || expression_uses_bvar(checker, *body, target.saturating_add(1), next)
        }
        Expr::Let { ty, value, body } => {
            expression_uses_bvar(checker, *ty, target, next)
                || expression_uses_bvar(checker, *value, target, next)
                || expression_uses_bvar(checker, *body, target.saturating_add(1), next)
        }
        Expr::Proj { structure, .. } => expression_uses_bvar(checker, *structure, target, next),
    }
}

fn compare_values(
    checker: &TypeChecker<'_>,
    left: &Value,
    right: &Value,
    budget: usize,
    depth: usize,
    work: &mut Vec<(TypeValue, TypeValue, usize, Vec<TypeValue>)>,
    proof_function_frees: &mut HashMap<FreeId, (crate::id::NameId, Vec<crate::level::LevelTerm>)>,
    context: &[TypeValue],
) -> Judgment<()> {
    match (left, right) {
        (Value::NatLit(left), Value::NatLit(right)) => {
            if left != right {
                return Judgment::refuted("distinct-Nat-literals");
            }
        }
        (Value::NatLit(literal), Value::Neutral(neutral)) => {
            return compare_nat_literal_neutral(
                checker,
                literal,
                neutral,
                budget,
                depth,
                work,
                proof_function_frees,
                context,
            );
        }
        (Value::Neutral(neutral), Value::NatLit(literal)) => {
            return compare_nat_literal_neutral(
                checker,
                literal,
                neutral,
                budget,
                depth,
                work,
                proof_function_frees,
                context,
            );
        }
        (Value::Sort(left), Value::Sort(right)) => {
            work.push((
                TypeValue::Sort(left.clone()),
                TypeValue::Sort(right.clone()),
                depth,
                context.to_vec(),
            ));
        }
        (
            Value::Pi {
                domain: left_domain,
                body: left_body,
            },
            Value::Pi {
                domain: right_domain,
                body: right_body,
            },
        )
        | (
            Value::Lam {
                domain: left_domain,
                body: left_body,
            },
            Value::Lam {
                domain: right_domain,
                body: right_body,
            },
        ) => {
            let Some(free) = fresh_local(depth) else {
                return Judgment::unknown("binder-depth-overflow");
            };
            let left_domain_type = TypeValue::Term(left_domain.clone());
            let right_domain_type = TypeValue::Term(right_domain.clone());
            if let (Some(left_key), Some(right_key)) = (
                checker.fixed_proof_function_type_key(&left_domain_type, budget),
                checker.fixed_proof_function_type_key(&right_domain_type, budget),
            ) && left_key == right_key
            {
                proof_function_frees.insert(free, left_key);
            }
            let mut body_context = context.to_vec();
            if body_context.len() == depth {
                body_context.push(left_domain_type);
            }
            work.push((
                TypeValue::Term(left_body.under_free(free)),
                TypeValue::Term(right_body.under_free(free)),
                depth.saturating_add(1),
                body_context,
            ));
            work.push((
                TypeValue::Term(left_domain.clone()),
                TypeValue::Term(right_domain.clone()),
                depth,
                context.to_vec(),
            ));
        }
        (Value::Neutral(left), Value::Neutral(right)) => {
            match compare_neutral_heads(checker, left, right, budget) {
                Judgment::Proven { .. } => {}
                other => return other,
            }
            if left.spine.len() != right.spine.len() {
                return Judgment::refuted("neutral-spine-length");
            }
            work.extend(left.spine.iter().zip(&right.spine).map(|(left, right)| {
                (
                    TypeValue::Term(left.clone()),
                    TypeValue::Term(right.clone()),
                    depth,
                    context.to_vec(),
                )
            }));
        }
        (
            Value::Neutral(neutral),
            Value::Lam { domain, body },
        )
        | (
            Value::Lam { domain, body },
            Value::Neutral(neutral),
        ) if evaluated_free_eta(
            checker,
            neutral,
            domain,
            body,
            budget,
            depth,
            work,
            context,
        ) => {}
        _ => {
            if std::env::var_os("NUCLEUS_TRACE_VALUE_MISMATCH").is_some() {
                eprintln!(
                    "NUCLEUS_VALUE_MISMATCH:left={:?}:right={:?}:budget={}:depth={}",
                    left, right, budget, depth
                );
            }
            return Judgment::refuted("rigid-value-constructor-mismatch");
        }
    }
    Judgment::proven((), "rigid-value-comparison")
}

fn compare_nat_literal_neutral(
    checker: &TypeChecker<'_>,
    literal: &crate::nat::BigNat,
    neutral: &Neutral,
    budget: usize,
    depth: usize,
    work: &mut Vec<(TypeValue, TypeValue, usize, Vec<TypeValue>)>,
    proof_function_frees: &mut HashMap<FreeId, (crate::id::NameId, Vec<crate::level::LevelTerm>)>,
    context: &[TypeValue],
) -> Judgment<()> {
    let Some(primitives) = checker.nat_primitives() else {
        return Judgment::unknown("Nat-literal-conversion-without-authority");
    };
    let NeutralHead::Const { name, levels } = &neutral.head else {
        return Judgment::refuted("Nat-literal-neutral-head");
    };
    if !levels.is_empty() {
        return Judgment::refuted("Nat-literal-constructor-levels");
    }
    if *name == primitives.zero {
        return if neutral.spine.is_empty() && literal.is_zero() {
            Judgment::proven((), "Nat-literal-zero")
        } else {
            Judgment::refuted("Nat-literal-zero-mismatch")
        };
    }
    if *name == primitives.succ {
        if neutral.spine.len() != 1 {
            return Judgment::refuted("Nat-literal-succ-arity");
        }
        let Some(pred) = literal.pred() else {
            return Judgment::refuted("Nat-zero-is-not-succ");
        };
        let exposed =
            checker
                .machine()
                .expose(neutral.spine[0].clone(), Transparency::Reducible, budget);
        let Some(argument) = exposed.proven_value() else {
            return Judgment::unknown("Nat-literal-succ-argument");
        };
        return compare_values(
            checker,
            &Value::NatLit(pred),
            argument,
            budget.saturating_sub(1),
            depth,
            work,
            proof_function_frees,
            context,
        );
    }
    Judgment::refuted("Nat-literal-non-Nat-head")
}

fn compare_neutral_heads(
    checker: &TypeChecker<'_>,
    left: &Neutral,
    right: &Neutral,
    budget: usize,
) -> Judgment<()> {
    match (&left.head, &right.head) {
        (NeutralHead::Free(left), NeutralHead::Free(right)) if left == right => {
            Judgment::proven((), "same-free-variable")
        }
        (
            NeutralHead::Projection {
                type_name: left_type,
                index: left_index,
                structure: left_structure,
            },
            NeutralHead::Projection {
                type_name: right_type,
                index: right_index,
                structure: right_structure,
            },
        ) if left_type == right_type
            && left_index == right_index
            && left_structure == right_structure =>
        {
            Judgment::proven((), "same-neutral-projection")
        }
        (
            NeutralHead::Const {
                name: left_name,
                levels: left_levels,
            },
            NeutralHead::Const {
                name: right_name,
                levels: right_levels,
            },
        ) if left_levels.is_empty()
            && right_levels.is_empty()
            && checker.distinct_bool_constructors(*left_name, *right_name) =>
        {
            Judgment::refuted("rigid-value-constructor-mismatch")
        }
        (
            NeutralHead::Const {
                name: left_name,
                levels: left_levels,
            },
            NeutralHead::Const {
                name: right_name,
                levels: right_levels,
            },
        ) if left.spine.is_empty()
            && right.spine.is_empty()
            && checker.distinct_opaque_closed_proposition_types(
                *left_name,
                left_levels,
                *right_name,
                right_levels,
                budget,
            ) =>
        {
            Judgment::refuted("distinct-opaque-proposition-types")
        }
        (
            NeutralHead::Const {
                name: left_name,
                levels: left_levels,
            },
            NeutralHead::Const {
                name: right_name,
                levels: right_levels,
            },
        ) if left_name == right_name && left_levels.len() == right_levels.len() => {
            for (left, right) in left_levels.iter().zip(right_levels) {
                match level_equal(left.clone(), right.clone(), budget) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                }
            }
            Judgment::proven((), "same-rigid-constant")
        }
        _ => {
            if std::env::var_os("NUCLEUS_TRACE_NEUTRAL_HEADS").is_some() {
                eprintln!(
                    "NUCLEUS_NEUTRAL_HEAD_MISMATCH:left={:?}:left_spine={:?}:right={:?}:right_spine={:?}:budget={}",
                    left.head, left.spine, right.head, right.spine, budget
                );
            }
            Judgment::refuted("distinct-neutral-heads")
        }
    }
}

fn value_as_type(value: &Value, depth: usize) -> Option<TypeValue> {
    match value {
        Value::Sort(level) => Some(TypeValue::Sort(level.clone())),
        Value::Pi { domain, body } => {
            let free = fresh_local(depth)?;
            Some(TypeValue::Pi {
                domain: Box::new(TypeValue::Term(domain.clone())),
                body: Box::new(TypeValue::Term(body.under_free(free))),
            })
        }
        Value::NatLit(_) | Value::Lam { .. } | Value::Neutral(_) => None,
    }
}

fn fresh_local(depth: usize) -> Option<FreeId> {
    u64::try_from(depth).ok().map(FreeId)
}

// Positive-only congruence for exposed stuck projections. Unequal structures
// never imply unequal fields. Scoped typing context and conversion depth are
// retained. A separate probe quota cannot directly spend the existing shortcut's
// shared application-attempt quota; failure falls back to ordinary conversion.
fn positive_projection_congruence(
    checker: &TypeChecker<'_>,
    left: &Neutral,
    right: &Neutral,
    budget: usize,
    depth: usize,
    context: &[TypeValue],
    delta_policy: DeltaPolicy,
    congruence_depth: usize,
    attempts: &mut usize,
    allow_proof_type_conversion: bool,
) -> bool {
    if *attempts == 0 || congruence_depth >= 16 || left.spine.len() != right.spine.len() {
        return false;
    }
    *attempts -= 1;
    let heads = match (&left.head, &right.head) {
        (
            NeutralHead::Projection {
                type_name: lt,
                index: li,
                structure: ls,
            },
            NeutralHead::Projection {
                type_name: rt,
                index: ri,
                structure: rs,
            },
        ) => {
            lt == rt
                && li == ri
                && positive_projection_congruence(
                    checker,
                    ls,
                    rs,
                    budget,
                    depth,
                    context,
                    delta_policy,
                    congruence_depth + 1,
                    attempts,
                    allow_proof_type_conversion,
                )
        }
        _ => compare_neutral_heads(checker, left, right, budget).is_proven(),
    };
    heads
        && left.spine.iter().zip(&right.spine).all(|(l, r)| {
            convert_in_context_with_congruence(
                checker,
                &TypeValue::Term(l.clone()),
                &TypeValue::Term(r.clone()),
                budget.min(1024),
                delta_policy,
                depth,
                context,
                congruence_depth + 1,
                attempts,
                allow_proof_type_conversion,
            )
            .is_proven()
        })
}
