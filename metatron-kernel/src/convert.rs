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

        // Equal source syntax is sufficient only after every used capture
        // and universe is independently identical. Unused frame slots carry
        // no equality authority; incomplete support must decline this trial.
        if let (TypeValue::Term(lhs), TypeValue::Term(rhs)) = (&left, &right)
            && lhs.env != rhs.env
            && remaining > 8 && *congruence_attempts > 0
        {
            *congruence_attempts -= 1;
            let allowance = remaining.min(1024);
            let mut trial = allowance;
            let identical = checker.exact_source_capture_identity(lhs, rhs, &mut trial);
            remaining -= allowance.saturating_sub(trial);
            if identical { continue; }
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

        // Lean proof irrelevance after *independent* proposition formation
        // and exact type conversion. Unlike a FreeId shortcut this checks
        // the theorem application's argument before certifying a proof.
        if depth == context.len()
            && let (TypeValue::Term(lhs),TypeValue::Term(rhs))=(&left,&right)
            && checker.checked_proof_vs_local_in_context(lhs,rhs,context,remaining)
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
                    binder: left_binder,
                },
                TypeValue::Pi {
                    domain: right_domain,
                    body: right_body,
                    binder: right_binder,
                },
            ) => {
                let Some(free) = fresh_local(depth) else {
                    return Judgment::unknown("binder-depth-overflow");
                };
                let Some(left_body) = checker.reopen_fixed_pi_body(
                    &left_body, left_binder, free, &mut remaining,
                ) else {
                    return Judgment::unknown("fixed-pi-alpha-reopening");
                };
                let Some(right_body) = checker.reopen_fixed_pi_body(
                    &right_body, right_binder, free, &mut remaining,
                ) else {
                    return Judgment::unknown("fixed-pi-alpha-reopening");
                };
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
                    left_body,
                    right_body,
                    depth.saturating_add(1),
                    body_context,
                ));
                work.push((*left_domain, *right_domain, depth, local_context));
            }
            (TypeValue::Term(left), TypeValue::Term(right)) => {
                if delta_policy == DeltaPolicy::GuardedSemanticFallback
                    && let (Some(left_literal), Some(right_literal)) = (
                        checker.captured_string_literal(&left, remaining),
                        checker.captured_string_literal(&right, remaining),
                    )
                    && left_literal == right_literal
                {
                    continue;
                }
                let machine = checker.machine();
                let mut unfold_parent = false;
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
                        && compare_neutral_heads(checker, lhs, rhs, probe_budget, depth, context).is_proven()
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
                    // Unequal arguments are not an inequality proof for a
                    // reducible function. Compare its actual applications
                    // after delta instead of committing those argument goals.
                    unfold_parent = checker.definition_value(rigid_head).is_some();
                    if let Judgment::Refuted { obstruction } = &congruence
                        && checker.is_certified_constructor(rigid_head)
                    {
                        // Injectivity lets us transport a genuinely rigid
                        // argument inequivalence to the constructor result.
                        // A PreferredOnly mismatch alone is NOT such evidence:
                        // an argument may reduce under guarded/full delta or
                        // recursor iota. This previously misclassified two
                        // valid Nat.mod_lt exports as REJECT.
                        #[cfg(feature = "diagnostics")]
                        if std::env::var_os("NUCLEUS_TRACE_CONSTRUCTOR_MISMATCH").is_some() {
                            eprintln!(
                                "NUCLEUS_CONSTRUCTOR_MISMATCH:head={rigid_head:?}:depth={depth}:obstruction={obstruction:?}"
                            );
                        }
                        if matches!(
                            obstruction.0,
                            "distinct-canonical-universes"
                                | "distinct-Nat-literals"
                                | "rigid-value-constructor-mismatch"
                                | "distinct-opaque-proposition-types"
                        ) {
                            return Judgment::refuted("certified-constructor-argument-mismatch");
                        }
                        // This is not yet a mismatch, nor grounds for an
                        // early UNKNOWN. Continue to the ordinary guarded
                        // comparison below. In particular Full exposure may
                        // apply an already-certified Nat.rec iota rule when
                        // its captured major argument is canonical zero.
                        #[cfg(feature = "diagnostics")]
                        if std::env::var_os("NUCLEUS_TRACE_NATREC_MAJOR").is_some() {
                            eprintln!(
                                "NUCLEUS_CONSTRUCTOR_FALLTHROUGH:depth={depth}:head={rigid_head:?}:obstruction={obstruction:?}"
                            );
                        }
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
                        if let (Some(left_delta), Some(right_delta)) =
                            (left_delta.proven_value(), right_delta.proven_value())
                        {
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
                        } else {
                            // This optional bounded shortcut established no
                            // value comparison. Pay both attempted exposures
                            // and continue the ordinary guarded derivation.
                            let spent = remaining.min(64).saturating_mul(2);
                            remaining = remaining.saturating_sub(spent);
                        }
                    }
                }
                let cheap_left =
                    machine.expose_for_conversion(left.clone(), if unfold_parent { Transparency::Full } else { Transparency::Reducible }, remaining);
                let cheap_right = machine.expose_for_conversion(
                    right.clone(),
                    if unfold_parent { Transparency::Full } else { Transparency::Reducible },
                    remaining,
                );
                let (Some(cheap_left), Some(cheap_right)) =
                    (cheap_left.proven_value(), cheap_right.proven_value())
                else {
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_LITERAL_CONVERSION").is_some() {
                        eprintln!("NUCLEUS_LITERAL_CONVERSION:left={left:?}:syntax={:?}:result={cheap_left:?}:right={right:?}:syntax={:?}:result={cheap_right:?}",checker.expression(left.expr),checker.expression(right.expr));
                    }
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
                let exposed = if exposed.is_unknown() && depth == context.len()
                    && delta_policy == DeltaPolicy::GuardedSemanticFallback
                {
                    checked_source_type_value(checker, term.clone(), context, remaining)
                } else {
                    exposed
                };
                let Some(exposed) = exposed.proven_value() else {
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_RIGID_TYPE_MISMATCH").is_some() {
                        eprintln!("NUCLEUS_TYPE_EXPOSURE_UNKNOWN:term={term:?}:budget={remaining}:result={exposed:?}");
                    }
                    return Judgment::unknown("conversion-exposure");
                };
                let exposed = if let Some(exposed) = value_as_type(checker, exposed, depth, &mut remaining) {
                    exposed
                } else if delta_policy == DeltaPolicy::GuardedSemanticFallback {
                    let full = machine.expose(term.clone(), Transparency::Full, remaining);
                    let Some(full) = full.proven_value() else {
                        return Judgment::unknown("full-conversion-exposure");
                    };
                    let recovered = if depth == context.len() && value_as_type(checker, full, depth, &mut remaining).is_none() {
                        checked_source_type_value(checker, term.clone(), context, remaining)
                    } else {
                        Judgment::unknown("checked-source-type-recovery-not-needed")
                    };
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_SOURCE_TYPE_RECOVERY").is_some() {
                        eprintln!("NUCLEUS_SOURCE_TYPE_RECOVERY:term={:?}:result={recovered:?}",term.expr);
                    }
                    let full = recovered.proven_value().unwrap_or(full);
                    let Some(full) = value_as_type(checker, full, depth, &mut remaining) else {
                        #[cfg(feature="diagnostics")]
                        if std::env::var_os("NUCLEUS_TRACE_RIGID_TYPE_MISMATCH").is_some() {
                            eprintln!("NUCLEUS_RIGID_TYPE_MISMATCH:depth={depth}:context={}:exposed={full:?}:expected={other:?}:budget={remaining}",context.len());
                            if let Value::Neutral(n)=full {
                                eprintln!("NUCLEUS_RIGID_TYPE_MAJOR:{}",checker.diagnostic_captured_recursor_major_chain(n,remaining));
                            }
                        }
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

// Source-certified multi-binder η for the literal curried telescope.
// The final application must supply exactly the introduced binders in
// source order and its original head must be independent of all of them.
// All environments and universe substitutions come from the *original*
// closure; new locals are placeholders for bindings that the head does not
// use. Not a blanket lambda-versus-neutral equality.
fn eta_contract_telescope(
    checker: &TypeChecker<'_>,
    raw: &Closure,
    depth: usize,
) -> Option<Closure> {
    let source=resolve_local_closure(checker,raw)?;
    let mut body=source.expr;
    let mut n=0usize;
    while let Some(Expr::Lam {body:next,..})=checker.expression(body) {
        if n==4 {return None}
        n+=1;
        body=*next;
    }
    if n<2 {return None}
    let mut head=body;
    for index in 0..n {
        let Some(Expr::App {fun,arg})=checker.expression(head) else {return None};
        if !matches!(checker.expression(*arg),Some(Expr::BVar(j)) if *j==index as u64) {
            return None
        }
        head=*fun;
    }
    // The head may itself contain binders: expression_uses_bvar performs
    // de Bruijn-aware, conservative support checking across all constructors.
    if (0..n).any(|index|expression_uses_bvar(checker,head,index as u64,2048)) {
        return None
    }
    let mut captured=source.env.clone();
    for index in 0..n {
        captured=captured.extend_free(fresh_local(depth.checked_add(index)?)?);
    }
    let contracted=source.sibling(head,captured);
    #[cfg(feature="diagnostics")]
    if std::env::var_os("NUCLEUS_TRACE_MULTIBINDER_ETA").is_some() {
        eprintln!(
            "NUCLEUS_MULTIBINDER_ETA:original={:?}:body={body:?}:head={head:?}:arity={n}:depth={depth}:candidate={contracted:?}",
            source,
        );
    }
    Some(contracted)
}

fn eta_contract(checker: &TypeChecker<'_>, closure: &Closure, depth: usize) -> Option<Closure> {
    if let Some(contracted)=eta_contract_telescope(checker,closure,depth) {
        return Some(contracted);
    }
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
    let mut opening_budget = budget.min(1024);
    if !source_opening_avoids_capture(checker, lambda_body, argument_free, &mut opening_budget) {
        return false;
    }
    let budget = budget.saturating_sub(budget.min(1024) - opening_budget);
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
                EnvBinding::Free(_) | EnvBinding::Neutral(_) | EnvBinding::NatLit(_) => return Some(current),
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
    if depth!=context.len() || !target.spine.is_empty() {
        return false;
    }
    let NeutralHead::Free(free) = &target.head else {
        return false;
    };
    let NeutralHead::Const {
        name: constructor, levels:constructor_levels,
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
        name: actual_type, levels:type_levels,
    } = &target_type.head
    else {
        return false;
    };
    if *actual_type != type_name || target_type.spine.len() != num_params {
        return false;
    }
    if constructor_levels.len()!=type_levels.len() || !constructor_levels.iter().zip(type_levels).all(|(a,b)|
        level_equal(a.clone(),b.clone(),budget).is_proven()) {return false;}

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
                let allowance = current_budget.min(1024);
                let mut opening_budget = allowance;
                if !source_opening_avoids_capture(checker, left_body, free, &mut opening_budget)
                    || !source_opening_avoids_capture(checker, right_body, free, &mut opening_budget) {
                    return Judgment::unknown("source-binder-capture-or-support-unavailable");
                }
                current_budget -= allowance - opening_budget;
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
                // A checked projection of one fixed field is congruent only
                // after proving the receiver and all applied arguments equal.
                // The existing source-level Nat computation never licenses
                // identifying unrelated binder environments or Nat indices.
                let probe = (current_budget / 2).min(128);
                if probe >= 8
                    && left_spine.len() == right_spine.len()
                    && convert_with_policy_in_context(
                        checker,
                        &TypeValue::Term(left_structure.clone()),
                        &TypeValue::Term(right_structure.clone()),
                        probe,
                        DeltaPolicy::PreferredOnly,
                        depth,
                        context,
                    ).is_proven()
                    && left_spine.iter().zip(right_spine).all(|(lhs, rhs)| {
                        convert_with_policy_in_context(
                            checker,
                            &TypeValue::Term(lhs.clone()),
                            &TypeValue::Term(rhs.clone()),
                            probe,
                            DeltaPolicy::PreferredOnly,
                            depth,
                            context,
                        ).is_proven()
                    })
                {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_PROJECTION_CONGRUENCE").is_some() {
                        eprintln!("NUCLEUS_PROJECTION_CONGRUENCE:earned-certified-operands");
                    }
                    return Judgment::proven((), "certified-projection-congruence");
                }
                // Experimental: preserve the actual checked lexical context
                // for projection receiver/spine congruence. The context-free
                // fast path remains the production baseline. The new path is
                // permitted only when the local context matches its binder depth
                // and each argument conversion is independently PROVEN.
                let contextual = std::env::var_os(
                    "NUCLEUS_EXPERIMENTAL_PROJECTION_CONTEXT",
                ).is_some()
                    && depth == context.len()
                    && same_rigid_application_congruence_in_context(
                        checker, left_structure, right_structure,
                        current_budget, depth, context, CHEAP_PROJECTION_CONGRUENCE_BUDGET,
                    )
                    && same_closure_spine_congruence_in_context(
                        checker, left_spine, right_spine,
                        current_budget, depth, context, CHEAP_PROJECTION_CONGRUENCE_BUDGET,
                    );
                if contextual {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_PROJECTION_CONTEXT").is_some() {
                        eprintln!(
                            "NUCLEUS_CONTEXTUAL_PROJECTION:PROVEN:depth={depth}:receiver={left_structure:?}:opponent={right_structure:?}",
                        );
                    }
                    return Judgment::proven((), "checked-contextual-projection-congruence");
                }
                // Narrow second-stage budget: only paired projections with
                // the same original receiver syntax and universe instance,
                // under an explicit lexical context of at most two binders.
                // Unlike shape-based shortcuts, every recursor argument is
                // still independently proved definitionally equal by the
                // guarded converter with a bounded local budget.
                let deep_contextual =
                    std::env::var_os("NUCLEUS_EXPERIMENTAL_PROJECTION_CROSSFRAME_512")
                        .is_some()
                    && depth == context.len()
                    && depth <= 2
                    && *left_index == 0
                    && current_budget >= 256
                    && left_structure.expr == right_structure.expr
                    && left_structure.levels == right_structure.levels
                    && same_rigid_application_congruence_in_context(
                        checker,left_structure,right_structure,
                        512,depth,context,512,
                    )
                    && same_closure_spine_congruence_in_context(
                        checker,left_spine,right_spine,
                        512,depth,context,512,
                    );
                if deep_contextual {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_PROJECTION_CROSSFRAME_512").is_some() {
                        eprintln!(
                            "NUCLEUS_CROSSFRAME_512_PROVEN:depth={depth}:receiver_left={left_structure:?}:receiver_right={right_structure:?}",
                        );
                    }
                    return Judgment::proven((), "source-verified-bounded-projection-congruence");
                }
                // The source-scoped warrant is only used for the receiver
                // when both closures are independently typed in the SAME
                // existing lexical context. This is not a shape-based shortcut.
                let typed_receiver =
                    std::env::var_os("NUCLEUS_EXPERIMENTAL_TYPED_RECEIVER").is_some()
                    && depth == context.len()
                    && context.len() <= 12
                    && current_budget >= 512
                    && checker.checked_source_conversion(
                        left_structure,right_structure,context,
                        current_budget.min(2048),
                    ).is_proven()
                    && same_closure_spine_congruence_in_context(
                        checker,left_spine,right_spine,
                        current_budget,depth,context,512,
                    );
                if typed_receiver {
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_TYPED_RECEIVER").is_some(){
                        eprintln!(
                            "NUCLEUS_TYPED_RECEIVER:PROVEN:depth={depth}:left={left_structure:?}:right={right_structure:?}",
                        );
                    }
                    return Judgment::proven((),"checked-source-typed-projection-congruence");
                }
                // Reuse the *existing* typed receiver warrant at the
                // actual source binder depth. This experimental path is
                // independent of syntactic identity and requires separately
                // checked equality for every pending application argument.
                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_TEN_METHODS").is_some()
                    && depth==context.len() && (7..=8).contains(&depth)
                {
                    use std::sync::atomic::{AtomicUsize,Ordering};
                    static COUNT:AtomicUsize=AtomicUsize::new(0);
                    if COUNT.fetch_add(1,Ordering::Relaxed)<24 {
                        let left_typed=checker.checked_source_conversion(
                            left_structure,left_structure,context,512,
                        );
                        let right_typed=checker.checked_source_conversion(
                            right_structure,right_structure,context,512,
                        );
                        let receivers=checker.checked_source_conversion(
                            left_structure,right_structure,context,2048,
                        );
                        let args=same_closure_spine_congruence_in_context(
                            checker,left_spine,right_spine,512,depth,context,512,
                        );
                        eprintln!(
                            "NUCLEUS_TEN_METHODS:depth={depth}:budget={current_budget}:left_typed={left_typed:?}:right_typed={right_typed:?}:receiver_equality={receivers:?}:spine_equality={args}:left_expr={:?}:right_expr={:?}:left_arity={}:right_arity={}",
                            left_structure.expr,right_structure.expr,
                            left_spine.len(),right_spine.len(),
                        );
                    }
                }
                let source_typed_pair =
                    std::env::var_os("NUCLEUS_EXPERIMENTAL_SOURCE_PAIR_DEPTH8").is_some()
                    && depth == context.len()
                    && (7..=8).contains(&depth)
                    && current_budget >= 2
                    && checker.checked_source_conversion(
                        left_structure,right_structure,context,
                        2048,
                    ).is_proven()
                    && same_closure_spine_congruence_in_context(
                        checker,left_spine,right_spine,
                        512,depth,context,512,
                    );
                if source_typed_pair {
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_SOURCE_PAIR_DEPTH8").is_some(){
                        eprintln!(
                            "NUCLEUS_SOURCE_PAIR_DEPTH8:PROVEN:depth={depth}:left={left_structure:?}:right={right_structure:?}",
                        );
                    }
                    return Judgment::proven((),"checked-source-paired-projection");
                }
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
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_PROJECTION_LAST_FAILURE").is_some() {
                        eprintln!(
                            "NUCLEUS_POST_IOTA_PROJECTION_GAP:shape=pair:depth={depth}:budget={current_budget}:left_type={left_type:?}:left_index={left_index}:left_structure={left_structure:?}:left_exposed={left_value:?}:right_type={right_type:?}:right_index={right_index}:right_structure={right_structure:?}:right_exposed={right_value:?}"
                        );
                    }
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_TERMINAL_CAUSE").is_some()
                        && (6..=10).contains(&depth)
                    {
                        eprintln!(
                            "NUCLEUS_TERMINAL_CAUSE:shape=pair:depth={depth}:left_type={left_type:?}:left_index={left_index}:left_receiver={left_structure:?}:left_result={left_value:?}:right_type={right_type:?}:right_index={right_index}:right_receiver={right_structure:?}:right_result={right_value:?}"
                        );
                    }
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
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_FIRST_TYPED_CONTINUATION").is_some()
                    && let Value::Neutral(other) = &current_right
                    && current_budget >= 16
                    && other.spine.len() == 5
                {
                    use std::sync::atomic::{AtomicUsize, Ordering};
                    static PRINTED: AtomicUsize = AtomicUsize::new(0);
                    if PRINTED.fetch_add(1, Ordering::Relaxed) < 16 {
                        // The "separator" is a failed *typing premise* in a
                        // candidate proof derivation, not a claim that two
                        // valid convertible Lean terms are inequivalent.
                        let first = checker.diagnostic_neutral_source_telescope(
                            other, context, current_budget,
                        );
                        let first: String = first.chars().take(2500).collect();
                        eprintln!(
                            "NUCLEUS_FIRST_TYPED_CONTINUATION:depth={depth}:scope={}:projection={type_name:?}:{index}:receiver={:?}:opposing_head={:?}:opposing_arity={}:first_premise={first}",
                            context.len(), structure.expr, other.head, other.spine.len(),
                        );
                    }
                }
                let exposed = checker.machine().projection_value_for_conversion(
                    structure.clone(),
                    *type_name,
                    *index,
                    spine,
                    current_budget,
                );
                let Some(exposed) = exposed.proven_value() else {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_PROJECTION_LAST_FAILURE").is_some() {
                        eprintln!(
                            "NUCLEUS_POST_IOTA_PROJECTION_GAP:shape=single:depth={depth}:budget={current_budget}:projection_type={type_name:?}:index={index}:structure={structure:?}:pending={spine:?}"
                        );
                    }
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_TERMINAL_CAUSE").is_some()
                        && (6..=10).contains(&depth)
                    {
                        use std::sync::atomic::{AtomicUsize,Ordering};
                        static COUNT:AtomicUsize=AtomicUsize::new(0);
                        if COUNT.fetch_add(1,Ordering::Relaxed)<48 {
                            let receiver=checker.machine().expose_for_conversion(
                                structure.clone(),Transparency::Full,512,
                            );
                            let field=checker.machine().projection_field_for_conversion(
                                structure.clone(),*type_name,*index,512,
                            );
                            eprintln!(
                                "NUCLEUS_TERMINAL_CAUSE:depth={depth}:type={type_name:?}:index={index}:receiver_expr={:?}:receiver_env={}:receiver={}:field={}:pending={}",
                                structure.expr,structure.env.id(),
                                format!("{receiver:?}").chars().take(1300).collect::<String>(),
                                format!("{field:?}").chars().take(1300).collect::<String>(),
                                spine.len(),
                            );
                        }
                    }
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
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_PROJECTION_LAST_FAILURE").is_some() {
                        eprintln!(
                            "NUCLEUS_POST_IOTA_PROJECTION_GAP:shape=single:depth={depth}:budget={current_budget}:projection_type={type_name:?}:index={index}:structure={structure:?}:pending={spine:?}"
                        );
                    }
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_TERMINAL_CAUSE").is_some()
                        && (6..=10).contains(&depth)
                    {
                        use std::sync::atomic::{AtomicUsize,Ordering};
                        static COUNT:AtomicUsize=AtomicUsize::new(0);
                        if COUNT.fetch_add(1,Ordering::Relaxed)<48 {
                            let receiver=checker.machine().expose_for_conversion(
                                structure.clone(),Transparency::Full,512,
                            );
                            let field=checker.machine().projection_field_for_conversion(
                                structure.clone(),*type_name,*index,512,
                            );
                            eprintln!(
                                "NUCLEUS_TERMINAL_CAUSE:depth={depth}:type={type_name:?}:index={index}:receiver_expr={:?}:receiver_env={}:receiver={}:field={}:pending={}",
                                structure.expr,structure.env.id(),
                                format!("{receiver:?}").chars().take(1300).collect::<String>(),
                                format!("{field:?}").chars().take(1300).collect::<String>(),
                                spine.len(),
                            );
                        }
                    }
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
                // A registered recursor with an actual constructor major is
                // reducible even when both applications retain the same head.
                // Replay source iota before treating its arguments as rigid.
                if left.head == right.head
                    && let NeutralHead::Const { name, .. } = &left.head
                    && checker.has_qualified_recursor(*name)
                    && left.spine != right.spine
                {
                    let mut available = current_budget;
                    let mut reduced = None;
                    for (is_left, candidate) in [(false, right), (true, left)] {
                        if available < 128 { break; }
                        let probe = available / 2;
                        available -= probe;
                        if let Judgment::Proven { value, .. } = checker.machine()
                            .qualified_one_step_recursor_result(candidate, probe)
                            && !matches!(&value, Value::Neutral(n) if n == candidate)
                        {
                            reduced = Some((is_left, value));
                            break;
                        }
                    }
                    if let Some((is_left, value)) = reduced {
                        if is_left { current_left = value; } else { current_right = value; }
                        current_budget = available.saturating_sub(1);
                        continue;
                    }
                    current_budget = available;
                }
                // Proof-carrying relevance signature: a proposition-valued
                // argument may differ ONLY after both applications' exact
                // dependent argument typing and data-argument congruence
                // are independently established. The source metadata is
                // the same authority used for ordinary application checks.
                if checker.certified_relevance_spine_congruence(
                    left,right,context,current_budget,depth,
                ) {
                    return Judgment::proven((), "checked-prop-spine-congruence");
                }
                // Lean proof irrelevance: two checked proof terms of the same
                // *independently verified* proposition are convertible.
                // Do not quotient their FreeId values or closure frames.
                if certified_local_proof_irrelevance(
                    checker, left, right, context, current_budget, depth,
                ) {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_LOCAL_PROOF_IRREL").is_some() {
                        eprintln!("NUCLEUS_LOCAL_PROOF_IRREL:proved:depth={depth}:left={:?}:right={:?}",left.head,right.head);
                    }
                    return Judgment::proven((), "checked-local-proof-irrelevance");
                }
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
                // A Bool constructor cannot be equated with an unrelated
                // neutral. It may, however, match a registered recursor after
                // exact source-defined iota. The major can itself be a
                // Decidable/Bool recursor with a captured constructor major.
                // Never select the constructor from the expected Bool result.
                if current_budget >= 128 {
                    let candidate = |constructor: &Neutral, recursive: &Neutral| -> Option<Value> {
                        let NeutralHead::Const { name, levels } = &constructor.head else {
                            return None;
                        };
                        if !constructor.spine.is_empty()
                            || !levels.is_empty()
                            || !checker.is_certified_bool_constructor(*name)
                            || recursive.spine.len() != 5
                        {
                            return None;
                        }
                        checker.machine().qualified_nested_recursor_result(
                            recursive, current_budget,
                        ).proven_value().cloned()
                    };
                    if let Some(result) = candidate(left, right) {
                        if result != Value::Neutral(right.clone()) {
                            return compare_values(
                                checker, &Value::Neutral(left.clone()), &result,
                                current_budget.saturating_sub(1),
                                depth, context, work, proof_function_frees,
                            );
                        }
                    }
                    if let Some(result) = candidate(right, left) {
                        if result != Value::Neutral(left.clone()) {
                            return compare_values(
                                checker, &result, &Value::Neutral(right.clone()),
                                current_budget.saturating_sub(1),
                                depth, context, work, proof_function_frees,
                            );
                        }
                    }
                }
                match compare_neutral_heads(checker, left, right, current_budget, depth, context) {
                    Judgment::Proven { .. } => {}
                    other => {
                        // A retained registered recursor can still have an
                        // actual constructor major. Replay its checked rule,
                        // independently of the opposing head or desired value.
                        // Reserve both bounded probes from this comparison's
                        // allowance, and continue iteratively after real iota.
                        let mut available = current_budget;
                        let mut reduced = None;
                        if left.head != right.head {
                            // Source-authorized scheduling experiment: when
                            // EXACTLY ONE side is an application of a registered
                            // recursor and the other is rigid, do not reserve a
                            // second recursor probe for an ineligible side.
                            // Allocate 3/4 to the actual source iota witness
                            // and retain 1/4 for subsequent comparison.
                            // Neither branch, major, nor expected result is
                            // guessed, and all original rules still apply.
                            let eligible = |n:&Neutral| {
                                !n.spine.is_empty()
                                    && matches!(&n.head, NeutralHead::Const{name,..}
                                        if checker.has_qualified_recursor(*name))
                            };
                            let exactly_one = eligible(left) != eligible(right);
                            for (is_left, candidate) in [(false, right), (true, left)] {
                                if !matches!(candidate.head, NeutralHead::Const { .. })
                                    || candidate.spine.is_empty() || available < 128 {
                                    continue;
                                }
                                let use_larger_probe =
                                    std::env::var_os("NUCLEUS_EXPERIMENTAL_SINGLE_RECURSOR_BUDGET").is_some()
                                    && exactly_one && eligible(candidate);
                                let probe = if use_larger_probe {
                                    available.saturating_sub(available/4)
                                } else { available/2 };
                                available -= probe;
                                let attempt=checker.machine()
                                    .qualified_one_step_recursor_result(candidate, probe);
                                #[cfg(feature="diagnostics")]
                                if use_larger_probe
                                    && std::env::var_os("NUCLEUS_TRACE_SINGLE_RECURSOR_BUDGET").is_some() {
                                    use std::sync::atomic::{AtomicUsize,Ordering};
                                    static SEEN:AtomicUsize=AtomicUsize::new(0);
                                    if SEEN.fetch_add(1,Ordering::Relaxed)<64 {
                                        eprintln!(
                                            "NUCLEUS_SINGLE_RECURSOR_BUDGET:depth={depth}:source_head={:?}:source_arity={}:allowance={probe}:retained={available}:outcome={}",
                                            candidate.head,candidate.spine.len(),
                                            format!("{attempt:?}").chars().take(850).collect::<String>(),
                                        );
                                    }
                                }
                                if let Judgment::Proven { value, .. } = attempt
                                    && !matches!(&value, Value::Neutral(n) if n == candidate)
                                {
                                    reduced = Some((is_left, value));
                                    break;
                                }
                            }
                        }
                        if let Some((is_left, value)) = reduced {
                            if is_left { current_left = value; } else { current_right = value; }
                            current_budget = available.saturating_sub(1);
                            continue;
                        }
                        return other;
                    }
                }
                if left.spine.len() != right.spine.len() {
                    return Judgment::refuted("neutral-spine-length");
                }
                // Proof-irrelevant dependent application congruence. Source
                // traces have independently established the exact premise
                // in a 13-binder context: the predicate head is unchanged,
                // the first argument is convertible, and the second pair
                // consists of two checked proofs of the same proposition.
                //
                // Do NOT permute arguments or identify unrelated locals.
                if depth==context.len() && (4..=24).contains(&depth) && current_budget>=1024
                    && left.head==right.head
                    && matches!(&left.head,NeutralHead::Free(_))
                    && left.spine.len()==2
                    && convert_with_policy_in_context(
                        checker,
                        &TypeValue::Term(left.spine[0].clone()),
                        &TypeValue::Term(right.spine[0].clone()),
                        512,DeltaPolicy::PreferredOnly,depth,context,
                    ).is_proven()
                    && checker.checked_proof_pair_in_bounded_context(
                        &left.spine[1],&right.spine[1],context,current_budget,
                    )
                {
                    return Judgment::proven(
                        (),"certified-dependent-predicate-proof-irrelevance",
                    );
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

fn same_closure_spine_congruence_in_context(
    checker: &TypeChecker<'_>,
    left: &[Closure],
    right: &[Closure],
    budget: usize,
    depth: usize,
    context: &[TypeValue],
    max_budget: usize,
) -> bool {
    let budget = budget.min(max_budget);
    left.len() == right.len()
        && left.iter().zip(right).all(|(left,right)| {
            convert_with_policy_in_context(
                checker,
                &TypeValue::Term(left.clone()),
                &TypeValue::Term(right.clone()),
                budget.saturating_sub(1),
                DeltaPolicy::PreferredOnly, depth, context,
            ).is_proven()
        })
}

fn same_rigid_application_congruence_in_context(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    budget: usize,
    depth: usize,
    context: &[TypeValue],
    max_budget: usize,
) -> bool {
    rigid_application_head_congruence_in_context(
        checker, left, right, budget, depth, context, max_budget,
    ).is_some_and(|(_, judgment)| judgment.is_proven())
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
    rigid_application_head_congruence_in_context(
        checker, left, right, budget, 0, &[], CHEAP_PROJECTION_CONGRUENCE_BUDGET,
    )
}

fn rigid_application_head_congruence_in_context(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    budget: usize,
    depth: usize,
    context: &[TypeValue],
    max_budget: usize,
) -> Option<(crate::id::NameId, Judgment<()>)> {
    let budget = budget.min(max_budget);
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

    for (left, right) in left_args.iter().zip(&right_args) {
        match convert_with_policy_in_context(
            checker,
            &TypeValue::Term(left.clone()),
            &TypeValue::Term(right.clone()),
            budget.saturating_sub(1),
            DeltaPolicy::PreferredOnly, depth, context,
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
    if literal.is_zero() && *name == primitives.recursor && budget >= 32 {
        let result = checker.machine().qualified_nat_zero_recursor_result(
            neutral, budget,
        );
        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_NATREC_MAJOR").is_some() {
            eprintln!(
                "NUCLEUS_ZERO_IOTA_REPLAY:depth={depth}:budget={budget}:result={result:?}"
            );
        }
        return match result {
            Judgment::Proven { value, .. } => {
                if value == Value::Neutral(neutral.clone()) {
                    Judgment::unknown("natrec-zero-iota-nonprogress")
                } else {
                    compare_values(
                        checker, &Value::NatLit(literal.clone()), &value,
                        budget.saturating_sub(1), depth, context,
                        work, proof_function_frees,
                    )
                }
            }
            Judgment::Refuted { .. } | Judgment::Unknown { .. } => {
                // A polymorphic Nat.rec is not a Nat constructor. Failure
                // to reduce it cannot establish numeral inequality.
                Judgment::unknown("natrec-zero-iota-unresolved")
            }
        };
    }
    if !levels.is_empty() {
        // A polymorphic recursor is not the constructor for zero. A
        // source-certified iota step requires first identifying its exact
        // recursor table AND inspecting its major argument.
        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_NATREC_MAJOR").is_some()
            && neutral.spine.len() == 4
        {
            use std::sync::atomic::{AtomicUsize, Ordering};
            static MAJOR_PROBES: AtomicUsize = AtomicUsize::new(0);
            if MAJOR_PROBES.fetch_add(1, Ordering::Relaxed) < 12 {
                eprintln!(
                    "NUCLEUS_NATREC_MAJOR_AUTHORITY:depth={depth}:literal={literal:?}:{}",
                    checker.diagnostic_natrec_major_authority(neutral, budget)
                );
            }
        }
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

// A sufficient source equality proof for an entire neutral receiver. Every
// child uses the same remaining allowance; no normalization or typing
// witness is borrowed from another receiver or context.
fn exact_neutral_source_congruence(
    checker: &TypeChecker<'_>, left: &Neutral, right: &Neutral, remaining: &mut usize,
) -> bool {
    use crate::level::LevelTerm;
    let mut pending = vec![(left, right)];
    while let Some((left, right)) = pending.pop() {
        if *remaining == 0 { return false; }
        *remaining -= 1;
        match (&left.head, &right.head) {
            (NeutralHead::Free(a), NeutralHead::Free(b)) if a == b => {}
            (NeutralHead::Const { name: a, levels: x }, NeutralHead::Const { name: b, levels: y }) if a == b && x.len() == y.len() => {
                if *remaining < x.len() { return false; }
                *remaining -= x.len();
                let mut levels: Vec<_> = x.iter().zip(y).collect();
                while let Some((a, b)) = levels.pop() {
                    if *remaining == 0 { return false; }
                    *remaining -= 1;
                    match (a, b) {
                        (LevelTerm::Zero, LevelTerm::Zero) => {}
                        (LevelTerm::Param(x), LevelTerm::Param(y)) => {
                            let cost = x.len().max(y.len());
                            if *remaining < cost { return false; }
                            *remaining -= cost;
                            if x != y { return false; }
                        }
                        (LevelTerm::Succ(x), LevelTerm::Succ(y)) => {
                            if *remaining == 0 { return false; }
                            *remaining -= 1;
                            levels.push((x, y));
                        }
                        (LevelTerm::Max(x, u), LevelTerm::Max(y, v))
                        | (LevelTerm::IMax(x, u), LevelTerm::IMax(y, v)) => {
                            if *remaining < 2 { return false; }
                            *remaining -= 2;
                            levels.push((x, y)); levels.push((u, v));
                        }
                        _ => return false,
                    }
                }
            }
            (NeutralHead::Projection { type_name: a, index: i, structure: x },
             NeutralHead::Projection { type_name: b, index: j, structure: y }) if a == b && i == j => {
                if *remaining == 0 { return false; }
                *remaining -= 1;
                pending.push((x.as_ref(), y.as_ref()));
            }
            _ => return false,
        }
        if left.spine.len() != right.spine.len() { return false; }
        for (a, b) in left.spine.iter().zip(&right.spine) {
            if *remaining == 0 { return false; }
            *remaining -= 1;
            if a.expr == b.expr && a.env == b.env && a.levels.identity() == b.levels.identity() {
                continue;
            }
            if !checker.exact_source_capture_identity(a, b, remaining) { return false; }
        }
    }
    true
}

fn compare_neutral_heads(
    checker: &TypeChecker<'_>,
    left: &Neutral,
    right: &Neutral,
    budget: usize,
    depth: usize,
    context: &[TypeValue],
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
        ) if left_type == right_type && left_index == right_index
            && depth == context.len() =>
        {
            // Congruence requires equal receiver values, not identical
            // capture-frame allocations. This is only a sufficient equality
            // rule: failure does not prove unequal selected fields.
            if budget < 8 || left_structure.spine.len() != right_structure.spine.len() {
                return Judgment::unknown("neutral-projection-receiver-congruence");
            }
            let mut source_work = budget.saturating_sub(1);
            if exact_neutral_source_congruence(checker, left_structure, right_structure, &mut source_work) {
                return Judgment::proven((), "exact-source-neutral-receiver-congruence");
            }
            let budget = source_work;
            let probe = budget.saturating_sub(1) / 2;
            if !compare_neutral_heads(
                checker, left_structure, right_structure, probe, depth, context,
            ).is_proven() {
                return Judgment::unknown("neutral-projection-receiver-congruence");
            }
            let argument_budget = probe / left_structure.spine.len().max(1);
            for (lhs, rhs) in left_structure.spine.iter().zip(&right_structure.spine) {
                let argument_result = convert_with_policy_in_context(
                    checker, &TypeValue::Term(lhs.clone()), &TypeValue::Term(rhs.clone()),
                    argument_budget, DeltaPolicy::GuardedSemanticFallback, depth, context,
                );
                if !argument_result.is_proven() {
                    #[cfg(feature = "diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_FAILED_RECEIVER_CAPTURES").is_some()
                        && matches!(lhs.expr.0, 600 | 1214)
                        && lhs.expr == rhs.expr && argument_budget >= 2048
                    {
                        use std::sync::atomic::{AtomicUsize, Ordering};
                        static CAPTURES: AtomicUsize = AtomicUsize::new(0);
                        // Count before probing typed captures so recursive
                        // diagnostic conversion cannot start another trace.
                        if CAPTURES.fetch_add(1, Ordering::Relaxed) == 0 {
                            eprintln!("NUCLEUS_FAILED_RECEIVER_CAPTURES:owner={left_type:?}:field={left_index}:depth={depth}:budget={budget}:argument_budget={argument_budget}:result={argument_result:?}:{}",
                                checker.diagnostic_receiver_capture_pair(lhs, rhs, context, 128));
                        }
                    }
                    return Judgment::unknown("neutral-projection-receiver-congruence");
                }
            }
            Judgment::proven((), "neutral-projection-receiver-congruence")
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
                    "NUCLEUS_NEUTRAL_HEAD_MISMATCH:depth={depth}:context_len={}:left={:?}:left_spine={:?}:right={:?}:right_spine={:?}:budget={}",
                    context.len(),left.head,left.spine,right.head,right.spine,budget,
                );
                let l=format!("{:?}",left.head);
                let r=format!("{:?}",right.head);
                if ((l=="Free(FreeId(6))" && r=="Free(FreeId(5))") ||
                    (l=="Free(FreeId(5))" && r=="Free(FreeId(6))"))
                {
                    let a=context.get(6);
                    let b=context.get(5);
                    let prop=|ty:Option<&TypeValue>| {
                        if let Some(TypeValue::Term(c))=ty {
                            Some(checker.is_proposition_in_context(
                                c.expr,context,&c.env,budget.min(1024),
                            ))
                        }else{None}
                    };
                    let relation=match(a,b){
                        (Some(x),Some(y))=>Some(convert_with_policy_in_context(
                            checker,x,y,budget.min(256),
                            DeltaPolicy::GuardedSemanticFallback,depth,context,
                        )),
                        _=>None,
                    };
                    eprintln!(
                        "NUCLEUS_FIN_LOCAL_PAIR:depth={depth}:context_len={}:free6_type={a:?}:free5_type={b:?}:prop6={:?}:prop5={:?}:type_relation={relation:?}",
                        context.len(),prop(a),prop(b),
                    );
                }
            }
            if std::env::var_os("NUCLEUS_TRACE_RECURSOR_MAJOR").is_some() { eprintln!("NUCLEUS_RECURSOR_MAJOR:left={:?}:right={:?}", left.spine.last(), right.spine.last()); if let Some(c) = right.spine.last() { eprintln!("NUCLEUS_RECURSOR_MAJOR_VALUE:{:?}", checker.machine().expose(c.clone(), Transparency::Full, budget.min(64))); } }
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_CHECKED_MAJOR_CHAIN").is_some() && left.spine.len()>=4 && context.len()<=24 {
                eprintln!("NUCLEUS_CHECKED_MAJOR_CHAIN:{}",checker.diagnostic_captured_recursor_major_chain(left,budget));
            }
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_CHECKED_MAJOR_CHAIN").is_some() && context.len() <= 24 {
                for value in [left, right] {
                    if value.spine.len() >= 4 {
                        eprintln!("NUCLEUS_EITHER_MAJOR_CHAIN:{}",checker.diagnostic_captured_recursor_major_chain(value,budget));
                    }
                    if let NeutralHead::Projection { structure, .. } = &value.head {
                        eprintln!("NUCLEUS_PROJECTION_MAJOR_CHAIN:{}",checker.diagnostic_captured_recursor_major_chain(structure,budget));
                    }
                }
            }
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_LEFT_DECIDABLE_MAJOR_CHAIN").is_some()
                && left.spine.len()==5 && context.len()==3
            {
                eprintln!("NUCLEUS_LEFT_DECIDABLE_MAJOR_CHAIN:{}",checker.diagnostic_captured_recursor_major_chain(left,budget));
            }
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_DECIDABLE_MAJOR_CHAIN").is_some()
                && matches!(&right.head, NeutralHead::Const { .. })
                && right.spine.len() == 5
            {
                use std::sync::atomic::{AtomicUsize, Ordering};
                static PRINTED: AtomicUsize = AtomicUsize::new(0);
                if PRINTED.fetch_add(1, Ordering::Relaxed) < 8 {
                    eprintln!(
                        "NUCLEUS_DECIDABLE_MAJOR_CHAIN:{}",
                        checker.diagnostic_captured_recursor_major_chain(right, budget),
                    );
                }
            }
            Judgment::refuted("distinct-neutral-heads")
        }
    }
}

/// Proof irrelevance is permitted only after checking BOTH proposition
/// judgments and checking conversion of their exact dependent types in
/// the current binder context. The local identifiers themselves are
/// explicitly *not* assumed interchangeable.
fn certified_local_proof_irrelevance(
    checker: &TypeChecker<'_>,
    left: &Neutral,
    right: &Neutral,
    context: &[TypeValue],
    budget: usize,
    depth: usize,
) -> bool {
    if budget < 32 || depth != context.len()
        || !left.spine.is_empty() || !right.spine.is_empty()
    {
        return false;
    }
    let (NeutralHead::Free(left_free), NeutralHead::Free(right_free)) =
        (&left.head, &right.head)
    else {
        return false;
    };
    if left_free == right_free {
        return false;
    }
    let (Some(TypeValue::Term(left_type)), Some(TypeValue::Term(right_type))) = (
        usize::try_from(left_free.0).ok().and_then(|i| context.get(i)),
        usize::try_from(right_free.0).ok().and_then(|i| context.get(i)),
    ) else {
        return false;
    };
    // Preserve the established default-substitution path unchanged.
    // A nontrivial universe substitution is not itself a sound reason to
    // reject proof irrelevance: the exact instantiated proposition may be
    // checked against Sort 0 through its closure, with its *real* levels.
    // Until independently qualified, this generalized rule is restricted
    // to the observed seven-binder locus and experimental flag.
    let polymorphic = left_type.levels != crate::value::LevelSubstitution::default()
        || right_type.levels != crate::value::LevelSubstitution::default();
    let polymorphic_enabled = polymorphic
        && depth == 7
        && std::env::var_os("NUCLEUS_EXPERIMENTAL_POLYMORPHIC_PROP_IRREL").is_some();
    if polymorphic && !polymorphic_enabled { return false; }
    let probe = budget.min(1024);
    let mut left_proposition = if polymorphic_enabled {
        checker.checked_captured_prop_type_in_context(
            left_type, context, probe,
        )
    } else {
        checker.is_proposition_in_context(
            left_type.expr, context, &left_type.env, probe,
        )
    };
    let mut right_proposition = if polymorphic_enabled {
        checker.checked_captured_prop_type_in_context(
            right_type, context, probe,
        )
    } else {
        checker.is_proposition_in_context(
            right_type.expr, context, &right_type.env, probe,
        )
    };
    // Replay exactly the captured dependent application when the ordinary
    // proposition checker cannot resolve either side. The replay checks
    // BOTH arguments against the instantiated Pi domains. A codomain
    // inspection alone must never authorize proof irrelevance.
    //
    // Keep this confined to the independently observed depth-5 residual:
    // widening it without a full-corpus qualification adds no warrant.
    if depth == 5 && left_proposition.is_unknown() && right_proposition.is_unknown() {
        let left_certificate = checker.certify_applied_proposition_in_context(
            left_type, context, probe,
        );
        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_LOCAL_PROOF_IRREL").is_some() {
            eprintln!("NUCLEUS_TYPED_TELESCOPE:depth={depth}:side=left:judgment={left_certificate:?}");
        }
        if left_certificate.is_proven() {
            left_proposition = left_certificate;
        } else {
            let right_certificate = checker.certify_applied_proposition_in_context(
                right_type, context, probe,
            );
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_LOCAL_PROOF_IRREL").is_some() {
                eprintln!("NUCLEUS_TYPED_TELESCOPE:depth={depth}:side=right:judgment={right_certificate:?}");
            }
            if right_certificate.is_proven() {
                right_proposition = right_certificate;
            }
        }
    }
    #[cfg(feature = "diagnostics")]
    if std::env::var_os("NUCLEUS_TRACE_LOCAL_PROOF_IRREL").is_some() {
        use std::sync::atomic::{AtomicUsize, Ordering};
        static PRINTED: AtomicUsize = AtomicUsize::new(0);
        if PRINTED.fetch_add(1, Ordering::Relaxed) < 48 {
            let relation = convert_with_policy_in_context(
                checker,
                &TypeValue::Term(left_type.clone()),
                &TypeValue::Term(right_type.clone()),
                probe,
                DeltaPolicy::PreferredOnly,
                depth,
                context,
            );
            if depth == 5 {
                let lhs = checker.machine().expose(left_type.clone(), Transparency::Reducible, probe);
                if let Some(Value::Neutral(neutral)) = lhs.proven_value() {
                    if let NeutralHead::Const { name, .. } = neutral.head {
                        let declaration = checker.diagnostic_applied_telescope(
                            name, &neutral.spine, probe,
                        );
                        eprintln!("NUCLEUS_DEPTH5_APPLIED_TELESCOPE:{declaration}");
                    }
                }
            }
            eprintln!("NUCLEUS_LOCAL_PROOF_PREMISES:depth={depth}:left={left_free:?}:right={right_free:?}:left_type={left_type:?}:right_type={right_type:?}:left_proposition={left_proposition:?}:right_proposition={right_proposition:?}:type_relation={relation:?}");
        }
    }
    // Sort preservation under definitional equality: if P : Prop and
    // P is demonstrably convertible to Q under the checked telescope,
    // Q is also a proposition. A second incomplete Q : Prop check is
    // not an obstruction. A definite failure on either side remains
    // an obstruction and NEVER licenses proof irrelevance.
    if left_proposition.is_refuted()
        || right_proposition.is_refuted()
        || (!left_proposition.is_proven() && !right_proposition.is_proven())
    {
        return false;
    }
    let type_relation=convert_with_policy_in_context(
        checker,
        &TypeValue::Term(left_type.clone()),
        &TypeValue::Term(right_type.clone()),
        probe,
        DeltaPolicy::PreferredOnly,
        depth,
        context,
    );
    let warranted=type_relation.is_proven();
    #[cfg(feature="diagnostics")]
    if polymorphic_enabled &&
       std::env::var_os("NUCLEUS_TRACE_POLYMORPHIC_PROP_IRREL").is_some()
    {
        use std::sync::atomic::{AtomicUsize, Ordering};
        static REPORT:AtomicUsize=AtomicUsize::new(0);
        if REPORT.fetch_add(1,Ordering::Relaxed)<16 {
            eprintln!(
                "NUCLEUS_POLYMORPHIC_PROP_IRREL:depth={depth}:left_free={left_free:?}:right_free={right_free:?}:left_formation={left_proposition:?}:right_formation={right_proposition:?}:type_relation={type_relation:?}:warranted={warranted}",
            );
        }
    }
    warranted
}

fn one_neutral_head_is_free(left: &Neutral, right: &Neutral) -> bool {
    matches!(left.head, NeutralHead::Free(_)) ^ matches!(right.head, NeutralHead::Free(_))
}

pub(crate) fn checked_source_type_value(
    checker: &TypeChecker<'_>,
    term: Closure,
    context: &[TypeValue],
    budget: usize,
) -> Judgment<Value> {
    if budget < 128 {
        return Judgment::unknown("checked-transport-projection-budget");
    }
    let machine = checker.machine();
    let preserved = machine.expose_for_conversion(term, Transparency::Full, budget);
    #[cfg(feature="diagnostics")]
    if std::env::var_os("NUCLEUS_TRACE_SOURCE_TYPE_RECOVERY").is_some() {
        eprintln!("NUCLEUS_SOURCE_TYPE_PRESERVED:{preserved:?}");
    }
    let preserved = if let Some(Value::Neutral(neutral)) = preserved.proven_value() {
        machine.qualified_nested_recursor_result(neutral, budget)
    } else {
        preserved
    };
    let Some(Value::StuckProjection { type_name, index, structure, spine }) = preserved.proven_value() else {
        return preserved;
    };
    let receiver = machine.expose(structure.clone(), Transparency::Full, budget / 2);
    let Some(Value::Neutral(neutral)) = receiver.proven_value() else {
        return Judgment::unknown("checked-transport-projection-receiver");
    };
    let RuleKAttempt::Reduced(reduced) = checker.rule_k_reduce_neutral(neutral, context, budget / 2) else {
        return Judgment::unknown("checked-transport-projection-premise");
    };
    // Select only a field of the actual source-registered constructor after
    // the existing typed K premise succeeds; retain all projection arguments.
    machine.projection_value_for_conversion(reduced, *type_name, *index, spine, budget / 2)
}

fn value_as_type(checker: &TypeChecker<'_>, value: &Value, depth: usize, remaining: &mut usize) -> Option<TypeValue> {
    match value {
        Value::Sort(level) => Some(TypeValue::Sort(level.clone())),
        Value::Pi { domain, body } => {
            let free = fresh_local(depth)?;
            let allowance = (*remaining).min(1024);
            let mut opening_budget = allowance;
            let safe = source_opening_avoids_capture(checker, body, free, &mut opening_budget);
            *remaining -= allowance - opening_budget;
            if !safe { return None; }
            Some(TypeValue::Pi {
                domain: Box::new(TypeValue::Term(domain.clone())),
                body: Box::new(TypeValue::Term(body.under_free(free))),
                binder: free,
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

// A source body still has its leading de Bruijn binder, so drop that
// virtual slot before inspecting actual captures. Only complete source
// support can justify opening it with an ID used by the checked context.
pub(crate) fn source_opening_avoids_capture(
    checker: &TypeChecker<'_>, body: &Closure, free: FreeId, budget: &mut usize,
) -> bool {
    // The exact lookup consumes the existing initial source-node step.
    // A miss carries that prepaid node into the original traversal once.
    if *budget==0{return false;}
    *budget-=1;
    if checker.has_source_opening_proof(body,free){return true;}
    let safe=source_opening_avoids_capture_uncached(checker,body,free,budget);
    if safe{checker.retain_source_opening_proof(body,free);}
    safe
}

fn source_opening_avoids_capture_uncached(
    checker:&TypeChecker<'_>,body:&Closure,free:FreeId,budget:&mut usize,
)->bool {
    let mut pending = vec![(body.clone(), 1u64)];
    let mut visited = HashSet::new();
    let mut prepaid_root=true;
    while let Some((source, virtual_slots)) = pending.pop() {
        if prepaid_root {prepaid_root=false;}
        else {
            if *budget == 0 { return false; }
            *budget -= 1;
        }
        if !visited.insert((source.expr, source.env.id(), virtual_slots)) { continue; }
        let Some(support) = checker.complete_source_support(source.expr, budget) else { return false; };
        for index in support {
            if index < virtual_slots { continue; }
            let index = index - virtual_slots;
            let Some(cost) = index.checked_add(1).and_then(|n| usize::try_from(n).ok()) else { return false; };
            if *budget < cost { return false; }
            *budget -= cost;
            let Some(binding) = source.env.lookup_binding_ref(index) else { return false; };
            match binding {
                EnvBinding::Free(actual) => { if *actual == free { return false; } }
                EnvBinding::Closure(captured) => pending.push((captured.clone(), 0)),
                EnvBinding::NatLit(_) => {}
                EnvBinding::Neutral(neutral) => {
                    let mut neutrals = vec![neutral];
                    while let Some(value) = neutrals.pop() {
                        if *budget == 0 { return false; }
                        *budget -= 1;
                        match &value.head {
                            NeutralHead::Free(actual) => { if *actual == free { return false; } }
                            NeutralHead::Projection { structure, .. } => neutrals.push(structure.as_ref()),
                            NeutralHead::Const { .. } => {}
                        }
                        if *budget < value.spine.len() { return false; }
                        *budget -= value.spine.len();
                        pending.extend(value.spine.iter().map(|c| (c.clone(), 0)));
                    }
                }
            }
        }
    }
    true
}
