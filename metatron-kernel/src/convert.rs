use std::collections::{HashMap, HashSet};

use crate::id::ExprId;
use crate::judgment::Judgment;
use crate::level::level_equal;
use crate::machine::Transparency;
use crate::syntax::Expr;
use crate::typecheck::{RuleKAttempt, TypeChecker, TypeValue};
use crate::value::{Closure, EnvBinding, FreeId, Neutral, NeutralHead, Value};

type ConversionVisitKey = (crate::machine::AuthorityId, TypeValue, TypeValue);
const INLINE_CONVERSION_VISIT_CAPACITY: usize = 8;
const CHEAP_PROJECTION_CONGRUENCE_BUDGET: usize = 64;

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
        checker, left, right, budget, delta_policy, initial_depth, context, 0,
        &mut congruence_attempts,
    )
}

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
    let mut lazy_head_delta_used = false;

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
            && checker.proof_terms_same_proposition(left_term, right_term, context, remaining)
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
                // Positive congruence before unfolding. Failed premises only
                // decline this rule; all nested probes share an attempt limit.
                if congruence_depth < 16 && *congruence_attempts > 0 {
                    *congruence_attempts -= 1;
                    let probe_budget = remaining;
                    let opaque_left = machine.expose(left.clone(), Transparency::Opaque, probe_budget);
                    let opaque_right = machine.expose(right.clone(), Transparency::Opaque, probe_budget);
                    if let (Some(Value::Neutral(lhs)), Some(Value::Neutral(rhs))) =
                        (opaque_left.proven_value(), opaque_right.proven_value())
                        && let (
                            NeutralHead::Const { name: left_name, .. },
                            NeutralHead::Const { name: right_name, .. },
                        ) = (&lhs.head, &rhs.head)
                        && left_name == right_name
                        && definition_arguments_used(checker, *left_name, lhs.spine.len())
                        && !lhs.spine.is_empty()
                        && lhs.spine.len() == rhs.spine.len()
                        && compare_neutral_heads(checker, lhs, rhs, probe_budget).is_proven()
                        && lhs.spine.iter().zip(&rhs.spine).rev().all(|(left_arg, right_arg)| {
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
                            ).is_proven()
                        })
                    {
                        continue;
                    }
                }
                if delta_policy == DeltaPolicy::GuardedSemanticFallback
                    && let Some((rigid_head, congruence)) =
                        rigid_application_head_congruence(checker, &left, &right, remaining)
                {
                    if congruence.is_proven() {
                        continue;
                    }
                    if congruence.is_refuted() && checker.is_certified_constructor(rigid_head) {
                        return Judgment::refuted("certified-constructor-argument-mismatch");
                    }
                    if !congruence.is_refuted()
                        && !lazy_head_delta_used
                        && remaining > INLINE_CONVERSION_VISIT_CAPACITY
                        && let (Some(left_delta), Some(right_delta)) = (
                            machine
                                .expose_head_delta_for_conversion(left.clone(), remaining.min(64)),
                            machine
                                .expose_head_delta_for_conversion(right.clone(), remaining.min(64)),
                        )
                    {
                        lazy_head_delta_used = true;
                        if std::env::var_os("NUCLEUS_TRACE_LAZY_DELTA").is_some() {
                            eprintln!(
                                "NUCLEUS_LAZY_HEAD_DELTA:left={:?}:right={:?}:budget={remaining}",
                                left.expr, right.expr
                            );
                        }
                        let (Some(left_delta), Some(right_delta)) =
                            (left_delta.proven_value(), right_delta.proven_value())
                        else {
                            return Judgment::unknown("lazy-head-delta-exposure");
                        };
                        match compare_values(
                            checker,
                            left_delta,
                            right_delta,
                            remaining.saturating_sub(1),
                            depth,
                            context,
                            &mut work,
                            &mut proof_function_frees,
                        ) {
                            Judgment::Proven { .. } => continue,
                            Judgment::Refuted { obstruction } => {
                                return Judgment::Refuted { obstruction };
                            }
                            Judgment::Unknown { residual } => {
                                return Judgment::Unknown { residual };
                            }
                        }
                    }
                }
                let cheap_left =
                    machine.expose_for_conversion(left.clone(), Transparency::Reducible, remaining);
                let cheap_right = machine.expose_for_conversion(
                    right.clone(),
                    Transparency::Reducible,
                    remaining,
                );
                let (Some(cheap_left), Some(cheap_right)) =
                    (cheap_left.proven_value(), cheap_right.proven_value())
                else {
                    return Judgment::unknown("conversion-exposure");
                };
                match compare_values(
                    checker,
                    cheap_left,
                    cheap_right,
                    remaining,
                    depth,
                    context,
                    &mut work,
                    &mut proof_function_frees,
                ) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { .. }
                        if delta_policy == DeltaPolicy::GuardedSemanticFallback =>
                    {
                        let full_left =
                            machine.expose_for_conversion(left, Transparency::Full, remaining);
                        let full_right =
                            machine.expose_for_conversion(right, Transparency::Full, remaining);
                        let (Some(full_left), Some(full_right)) =
                            (full_left.proven_value(), full_right.proven_value())
                        else {
                            return Judgment::unknown("full-conversion-exposure");
                        };
                        match compare_values(
                            checker,
                            full_left,
                            full_right,
                            remaining,
                            depth,
                            context,
                            &mut work,
                            &mut proof_function_frees,
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
    let (Some(left_free), Some(right_free)) = (
        opaque_free(checker, left, budget),
        opaque_free(checker, right, budget),
    ) else {
        return false;
    };
    if left_free == right_free {
        return false;
    }
    let (Some(left_type), Some(right_type)) = (
        context.get(left_free.0 as usize),
        context.get(right_free.0 as usize),
    ) else {
        return false;
    };
    let (Some(left_type_free), Some(right_type_free)) = (
        opaque_free(checker, left_type, budget),
        opaque_free(checker, right_type, budget),
    ) else {
        return false;
    };
    if left_type_free != right_type_free {
        return false;
    }
    match context.get(left_type_free.0 as usize) {
        Some(TypeValue::Sort(crate::level::LevelTerm::Succ(_))) => true,
        Some(TypeValue::Term(term)) => matches!(
            checker
                .machine()
                .expose(term.clone(), Transparency::Opaque, budget.min(32))
                .proven_value(),
            Some(Value::Sort(crate::level::LevelTerm::Succ(_)))
        ),
        _ => false,
    }
}

fn opaque_free(checker: &TypeChecker<'_>, ty: &TypeValue, budget: usize) -> Option<FreeId> {
    let TypeValue::Term(closure) = ty else {
        return None;
    };
    let exposed = checker
        .machine()
        .expose(closure.clone(), Transparency::Opaque, budget.min(32));
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
    if proof_functions.is_empty() {
        return false;
    }
    let machine = checker.machine();
    let left = machine.expose_for_conversion(left.clone(), Transparency::Reducible, budget);
    let right = machine.expose_for_conversion(right.clone(), Transparency::Reducible, budget);
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
    if proof_frees.is_empty() {
        return false;
    }
    let machine = checker.machine();
    let left = machine.expose_for_conversion(left.clone(), Transparency::Reducible, budget);
    let right = machine.expose_for_conversion(right.clone(), Transparency::Reducible, budget);
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
    if unit_like_frees.is_empty() {
        return false;
    }
    let machine = checker.machine();
    let left = machine.expose_for_conversion(left.clone(), Transparency::Reducible, budget);
    let right = machine.expose_for_conversion(right.clone(), Transparency::Reducible, budget);
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
    let Expr::Lam { body, .. } = checker.expression(closure.expr)? else {
        return None;
    };
    if std::env::var_os("NUCLEUS_TRACE_ETA").is_some() {
        eprintln!(
            "NUCLEUS_ETA_BODY:closure={:?}:body={:?}:body_expr={:?}",
            closure,
            body,
            checker.expression(*body)
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
    let Some(argument_free) = fresh_local(depth) else {
        return false;
    };
    let exposed_body = checker.machine().expose(
        lambda_body.under_free(argument_free),
        Transparency::Reducible,
        budget,
    );
    let Some(Value::Neutral(body_neutral)) = exposed_body.proven_value() else {
        return false;
    };
    if body_neutral.head != NeutralHead::Free(function_free) || body_neutral.spine.len() != 1 {
        return false;
    }
    let exposed_argument = checker.machine().expose(
        body_neutral.spine[0].clone(),
        Transparency::Reducible,
        budget,
    );
    let Some(Value::Neutral(argument_neutral)) = exposed_argument.proven_value() else {
        return false;
    };
    if argument_neutral.head != NeutralHead::Free(argument_free)
        || !argument_neutral.spine.is_empty()
    {
        return false;
    }

    // Pay for function-domain exposure only after the eta shape is established.
    // This preserves the exact semantic condition while rejecting non-eta
    // Neutral/Lam pairs before the expensive type exposure.
    let Some(function_type) = context.get(function_free.0 as usize) else {
        return false;
    };
    let function_domain = match function_type {
        TypeValue::Pi { domain, .. } => (**domain).clone(),
        TypeValue::Term(closure) => {
            let exposed = checker
                .machine()
                .expose(closure.clone(), Transparency::Reducible, budget);
            let Some(Value::Pi { domain, .. }) = exposed.proven_value() else {
                return false;
            };
            TypeValue::Term(domain.clone())
        }
        TypeValue::Sort(_) => return false,
    };
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
        match checker.expression(current.expr)? {
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

// Skip speculative argument equality when direct beta reduction can erase an
// argument. This is only a cost gate; ordinary conversion remains authoritative.
fn definition_arguments_used(
    checker: &TypeChecker<'_>,
    name: crate::id::NameId,
    arity: usize,
) -> bool {
    let Some(mut expression) = checker.definition_value(name) else {
        return false;
    };
    for _ in 0..arity {
        let Some(Expr::Lam { body, .. }) = checker.expression(expression) else {
            return false;
        };
        if !expression_uses_bvar(checker, *body, 0, 64) {
            return false;
        }
        expression = *body;
    }
    true
}

// Reference-derived, source-certified beta erasure: for a checked definition
// with k leading lambdas, an argument is erasable only if its binder is
// syntactically absent from the body after those k beta substitutions.
// This is not a proof-irrelevance shortcut and is conservative if the
// syntax support scan exceeds its bound.
fn provably_absent_definition_arguments(
    checker: &TypeChecker<'_>,
    name: crate::id::NameId,
    arity: usize,
) -> Option<Vec<bool>> {
    if arity == 0 || arity > 12 {
        return None;
    }
    let mut body = checker.definition_value(name)?;
    for _ in 0..arity {
        let Expr::Lam { body: next, .. } = checker.expression(body)? else {
            return None;
        };
        body = *next;
    }
    Some((0..arity)
        .map(|i| !expression_uses_bvar(checker, body, (arity - 1 - i) as u64, 128))
        .collect())
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

#[allow(clippy::too_many_arguments)]
fn certified_structure_eta(
    checker: &TypeChecker<'_>,
    target: &Neutral,
    constructed: &Neutral,
    budget: usize,
    depth: usize,
    work: &mut Vec<(TypeValue, TypeValue, usize, Vec<TypeValue>)>,
    context: &[TypeValue],
) -> bool {
    if !target.spine.is_empty() {
        return false;
    }
    let NeutralHead::Free(free) = &target.head else {
        return false;
    };
    let NeutralHead::Const {
        name: constructor, ..
    } = &constructed.head
    else {
        return false;
    };
    let Some((type_name, num_params, num_fields)) =
        checker.eta_projection_spec_for_constructor(*constructor)
    else {
        return false;
    };
    if constructed.spine.len() != num_params + num_fields {
        return false;
    }

    let Ok(free_index) = usize::try_from(free.0) else {
        return false;
    };
    let Some(TypeValue::Term(target_type)) = context.get(free_index) else {
        return false;
    };
    let target_type =
        checker
            .machine()
            .expose(target_type.clone(), Transparency::Reducible, budget);
    let Some(Value::Neutral(target_type)) = target_type.proven_value() else {
        return false;
    };
    let NeutralHead::Const {
        name: actual_type, ..
    } = &target_type.head
    else {
        return false;
    };
    if *actual_type != type_name || target_type.spine.len() != num_params {
        return false;
    }

    for (index, field) in constructed.spine[num_params..].iter().enumerate() {
        if !checker
            .certified_eta_projection_field(field, type_name, index, target, num_params, budget)
        {
            return false;
        }
    }

    for (actual, rebuilt) in target_type
        .spine
        .iter()
        .zip(constructed.spine.iter().take(num_params))
    {
        work.push((
            TypeValue::Term(actual.clone()),
            TypeValue::Term(rebuilt.clone()),
            depth,
            context.to_vec(),
        ));
    }
    true
}

fn rigid_local_non_eta_constructor_mismatch(
    checker: &TypeChecker<'_>,
    target: &Neutral,
    constructed: &Neutral,
    context: &[TypeValue],
    budget: usize,
) -> bool {
    if !target.spine.is_empty() {
        return false;
    }
    let NeutralHead::Free(free) = target.head else {
        return false;
    };
    let NeutralHead::Const {
        name: constructor, ..
    } = constructed.head
    else {
        return false;
    };
    let Some((type_name, constructor_arity)) =
        checker.non_eta_structure_for_constructor(constructor)
    else {
        return false;
    };
    if constructed.spine.len() != constructor_arity {
        return false;
    }
    let Ok(index) = usize::try_from(free.0) else {
        return false;
    };
    let Some(TypeValue::Term(target_type)) = context.get(index) else {
        return false;
    };
    let exposed =
        checker
            .machine()
            .expose(target_type.clone(), Transparency::Reducible, budget.min(64));
    matches!(
        exposed.proven_value(),
        Some(Value::Neutral(Neutral {
            head: NeutralHead::Const { name, .. },
            ..
        })) if *name == type_name
    )
}

fn distinct_non_eta_structure_locals(
    checker: &TypeChecker<'_>,
    left: &Neutral,
    right: &Neutral,
    context: &[TypeValue],
    budget: usize,
) -> bool {
    if !left.spine.is_empty() || !right.spine.is_empty() {
        return false;
    }
    let (NeutralHead::Free(left), NeutralHead::Free(right)) = (&left.head, &right.head) else {
        return false;
    };
    if left == right {
        return false;
    }
    let (Ok(left_index), Ok(right_index)) = (usize::try_from(left.0), usize::try_from(right.0))
    else {
        return false;
    };
    let (Some(TypeValue::Term(left_type)), Some(TypeValue::Term(right_type))) =
        (context.get(left_index), context.get(right_index))
    else {
        return false;
    };
    let expose_type = |ty: &Closure| {
        let exposed = checker
            .machine()
            .expose(ty.clone(), Transparency::Reducible, budget.min(64));
        let Value::Neutral(neutral) = exposed.proven_value()? else {
            return None;
        };
        let NeutralHead::Const { name, .. } = neutral.head else {
            return None;
        };
        Some(name)
    };
    expose_type(left_type)
        .zip(expose_type(right_type))
        .is_some_and(|(left, right)| left == right && checker.is_non_eta_structure_type(left))
}

fn compare_values(
    checker: &TypeChecker<'_>,
    left: &Value,
    right: &Value,
    budget: usize,
    depth: usize,
    context: &[TypeValue],
    work: &mut Vec<(TypeValue, TypeValue, usize, Vec<TypeValue>)>,
    proof_function_frees: &mut HashMap<FreeId, (crate::id::NameId, Vec<crate::level::LevelTerm>)>,
) -> Judgment<()> {
    let mut current_left = left.clone();
    let mut current_right = right.clone();
    let mut current_budget = budget;
    loop {
        match (&current_left, &current_right) {
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
                    current_budget,
                    depth,
                    context,
                    work,
                    proof_function_frees,
                );
            }
            (Value::Neutral(neutral), Value::NatLit(literal)) => {
                return compare_nat_literal_neutral(
                    checker,
                    literal,
                    neutral,
                    current_budget,
                    depth,
                    context,
                    work,
                    proof_function_frees,
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
                    checker.fixed_proof_function_type_key(&left_domain_type, current_budget),
                    checker.fixed_proof_function_type_key(&right_domain_type, current_budget),
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
            (
                Value::StuckProjection {
                    type_name: left_type,
                    index: left_index,
                    structure: left_structure,
                    spine: left_spine,
                },
                Value::StuckProjection {
                    type_name: right_type,
                    index: right_index,
                    structure: right_structure,
                    spine: right_spine,
                },
            ) if left_type == right_type && left_index == right_index => {
                if same_rigid_application_congruence(
                    checker,
                    left_structure,
                    right_structure,
                    current_budget,
                ) && same_closure_spine_congruence(
                    checker,
                    left_spine,
                    right_spine,
                    current_budget,
                ) {
                    return Judgment::proven((), "stuck-projection-rigid-application-congruence");
                }
                let machine = checker.machine();
                let left_value = machine.projection_value_for_conversion(
                    left_structure.clone(),
                    *left_type,
                    *left_index,
                    left_spine,
                    current_budget,
                );
                let right_value = machine.projection_value_for_conversion(
                    right_structure.clone(),
                    *right_type,
                    *right_index,
                    right_spine,
                    current_budget,
                );
                let (Some(left_value), Some(right_value)) =
                    (left_value.proven_value(), right_value.proven_value())
                else {
                    return Judgment::unknown("lazy-projection-value-exposure");
                };
                if current_budget == 0 {
                    return Judgment::unknown("lazy-projection-budget-exhausted");
                }
                current_left = left_value.clone();
                current_right = right_value.clone();
                current_budget -= 1;
                continue;
            }
            (
                Value::StuckProjection {
                    type_name,
                    index,
                    structure,
                    spine,
                },
                _,
            ) => {
                let exposed = checker.machine().projection_value_for_conversion(
                    structure.clone(),
                    *type_name,
                    *index,
                    spine,
                    current_budget,
                );
                let Some(exposed) = exposed.proven_value() else {
                    return Judgment::unknown("lazy-projection-value-exposure");
                };
                if current_budget == 0 {
                    return Judgment::unknown("lazy-projection-budget-exhausted");
                }
                current_left = exposed.clone();
                current_budget -= 1;
                continue;
            }
            (
                _,
                Value::StuckProjection {
                    type_name,
                    index,
                    structure,
                    spine,
                },
            ) => {
                let exposed = checker.machine().projection_value_for_conversion(
                    structure.clone(),
                    *type_name,
                    *index,
                    spine,
                    current_budget,
                );
                let Some(exposed) = exposed.proven_value() else {
                    return Judgment::unknown("lazy-projection-value-exposure");
                };
                if current_budget == 0 {
                    return Judgment::unknown("lazy-projection-budget-exhausted");
                }
                current_right = exposed.clone();
                current_budget -= 1;
                continue;
            }
            (Value::Neutral(left), Value::Neutral(right)) => {
                if certified_structure_eta(
                    checker,
                    left,
                    right,
                    current_budget,
                    depth,
                    work,
                    context,
                ) || certified_structure_eta(
                    checker,
                    right,
                    left,
                    current_budget,
                    depth,
                    work,
                    context,
                ) {
                    return Judgment::proven((), "certified-structure-eta");
                }
                if rigid_local_non_eta_constructor_mismatch(
                    checker,
                    left,
                    right,
                    context,
                    current_budget,
                ) || rigid_local_non_eta_constructor_mismatch(
                    checker,
                    right,
                    left,
                    context,
                    current_budget,
                ) {
                    return Judgment::refuted("non-eta-structure-mismatch");
                }
                if distinct_non_eta_structure_locals(checker, left, right, context, current_budget)
                {
                    return Judgment::refuted("non-eta-structure-mismatch");
                }
                match checker.rule_k_reduce_neutral(left, context, current_budget) {
                    RuleKAttempt::Reduced(closure) => {
                        let exposed = checker.machine().expose(
                            closure,
                            Transparency::Reducible,
                            current_budget.saturating_sub(1),
                        );
                        let Some(reduced) = exposed.proven_value() else {
                            return Judgment::unknown("rule-k-reduction-exposure");
                        };
                        let other = Value::Neutral(right.clone());
                        return compare_values(
                            checker,
                            reduced,
                            &other,
                            current_budget.saturating_sub(1),
                            depth,
                            context,
                            work,
                            proof_function_frees,
                        );
                    }
                    RuleKAttempt::DefiniteMismatch => {
                        return Judgment::refuted("rule-k-target-mismatch");
                    }
                    RuleKAttempt::NotApplicable => {}
                }
                match checker.rule_k_reduce_neutral(right, context, current_budget) {
                    RuleKAttempt::Reduced(closure) => {
                        let exposed = checker.machine().expose(
                            closure,
                            Transparency::Reducible,
                            current_budget.saturating_sub(1),
                        );
                        let Some(reduced) = exposed.proven_value() else {
                            return Judgment::unknown("rule-k-reduction-exposure");
                        };
                        let other = Value::Neutral(left.clone());
                        return compare_values(
                            checker,
                            &other,
                            reduced,
                            current_budget.saturating_sub(1),
                            depth,
                            context,
                            work,
                            proof_function_frees,
                        );
                    }
                    RuleKAttempt::DefiniteMismatch => {
                        return Judgment::refuted("rule-k-target-mismatch");
                    }
                    RuleKAttempt::NotApplicable => {}
                }
                if one_neutral_head_is_free(left, right)
                    && (checker.certified_stuck_nonproof_recursor_on_local(
                        left,
                        context,
                        current_budget,
                    ) || checker.certified_stuck_nonproof_recursor_on_local(
                        right,
                        context,
                        current_budget,
                    ))
                {
                    return Judgment::refuted("certified-stuck-recursor-mismatch");
                }
                match compare_neutral_heads(checker, left, right, current_budget) {
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
            (Value::Neutral(neutral), Value::Lam { domain, body })
            | (Value::Lam { domain, body }, Value::Neutral(neutral))
                if evaluated_free_eta(
                    checker,
                    neutral,
                    domain,
                    body,
                    current_budget,
                    depth,
                    work,
                    context,
                ) => {}
            _ => {
                if std::env::var_os("NUCLEUS_TRACE_VALUE_MISMATCH").is_some() {
                    eprintln!(
                        "NUCLEUS_VALUE_MISMATCH:left={:?}:right={:?}:budget={}:depth={}",
                        current_left, current_right, current_budget, depth
                    );
                }
                return Judgment::refuted("rigid-value-constructor-mismatch");
            }
        }
        break;
    }
    Judgment::proven((), "rigid-value-comparison")
}

fn same_closure_spine_congruence(
    checker: &TypeChecker<'_>,
    left: &[Closure],
    right: &[Closure],
    budget: usize,
) -> bool {
    let budget = budget.min(CHEAP_PROJECTION_CONGRUENCE_BUDGET);
    left.len() == right.len()
        && left.iter().zip(right).all(|(left, right)| {
            matches!(
                convert_with_policy(
                    checker,
                    &TypeValue::Term(left.clone()),
                    &TypeValue::Term(right.clone()),
                    budget.saturating_sub(1),
                    DeltaPolicy::PreferredOnly,
                ),
                Judgment::Proven { .. }
            )
        })
}

fn same_rigid_application_congruence(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    budget: usize,
) -> bool {
    rigid_application_head_congruence(checker, left, right, budget)
        .is_some_and(|(_, judgment)| judgment.is_proven())
}

fn rigid_application_head_congruence(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    budget: usize,
) -> Option<(crate::id::NameId, Judgment<()>)> {
    let budget = budget.min(CHEAP_PROJECTION_CONGRUENCE_BUDGET);
    if budget == 0 {
        return None;
    }

    fn rigid_application_spine(
        checker: &TypeChecker<'_>,
        closure: &Closure,
    ) -> Option<(Closure, Vec<Closure>)> {
        let mut current = resolve_local_closure(checker, closure)?;
        let mut arguments = Vec::new();
        loop {
            match checker.expression(current.expr)? {
                Expr::App { fun, arg } => {
                    arguments.push(current.sibling(*arg, current.env.clone()));
                    current = current.sibling(*fun, current.env.clone());
                    current = resolve_local_closure(checker, &current)?;
                }
                Expr::Const { .. } => {
                    arguments.reverse();
                    return Some((current, arguments));
                }
                _ => return None,
            }
        }
    }

    let Some((left_head, left_args)) = rigid_application_spine(checker, left) else {
        return None;
    };
    let Some((right_head, right_args)) = rigid_application_spine(checker, right) else {
        return None;
    };
    if left_args.is_empty()
        || left_args.len() != right_args.len()
        || left_head.expr != right_head.expr
        || left_head.levels != right_head.levels
    {
        return None;
    }
    let Expr::Const {
        name: rigid_head, ..
    } = checker.expression(left_head.expr)?
    else {
        return None;
    };

    let erased = provably_absent_definition_arguments(checker, *rigid_head, left_args.len());
    for (i, (left, right)) in left_args.iter().zip(&right_args).enumerate() {
        if erased.as_ref().is_some_and(|bits| bits[i]) {
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_ABSENT_ARG").is_some() {
                eprintln!(
                    "NUCLEUS_CERTIFIED_ABSENT_ARG:constant={rigid_head:?}:arity={}:index={i}",
                    left_args.len()
                );
            }
            continue;
        }
        match convert_with_policy(
            checker,
            &TypeValue::Term(left.clone()),
            &TypeValue::Term(right.clone()),
            budget.saturating_sub(1),
            DeltaPolicy::PreferredOnly,
        ) {
            Judgment::Proven { .. } => {}
            Judgment::Refuted { obstruction } => {
                return Some((*rigid_head, Judgment::Refuted { obstruction }));
            }
            Judgment::Unknown { residual } => {
                return Some((*rigid_head, Judgment::Unknown { residual }));
            }
        }
    }
    Some((
        *rigid_head,
        Judgment::proven((), "same-rigid-application-congruence"),
    ))
}

fn compare_nat_literal_neutral(
    checker: &TypeChecker<'_>,
    literal: &crate::nat::BigNat,
    neutral: &Neutral,
    budget: usize,
    depth: usize,
    context: &[TypeValue],
    work: &mut Vec<(TypeValue, TypeValue, usize, Vec<TypeValue>)>,
    proof_function_frees: &mut HashMap<FreeId, (crate::id::NameId, Vec<crate::level::LevelTerm>)>,
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
            context,
            work,
            proof_function_frees,
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
            if std::env::var_os("NUCLEUS_TRACE_RECURSOR_MAJOR").is_some() { eprintln!("NUCLEUS_RECURSOR_MAJOR:left={:?}:right={:?}", left.spine.last(), right.spine.last()); if let Some(c) = right.spine.last() { eprintln!("NUCLEUS_RECURSOR_MAJOR_VALUE:{:?}", checker.machine().expose(c.clone(), Transparency::Full, budget.min(64))); } }
            Judgment::refuted("distinct-neutral-heads")
        }
    }
}

fn one_neutral_head_is_free(left: &Neutral, right: &Neutral) -> bool {
    matches!(left.head, NeutralHead::Free(_)) ^ matches!(right.head, NeutralHead::Free(_))
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
        Value::NatLit(_)
        | Value::Lam { .. }
        | Value::Neutral(_)
        | Value::StuckProjection { .. } => None,
    }
}

fn fresh_local(depth: usize) -> Option<FreeId> {
    u64::try_from(depth).ok().map(FreeId)
}
