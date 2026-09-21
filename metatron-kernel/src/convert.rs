use std::collections::HashSet;

use crate::judgment::Judgment;
use crate::level::level_equal;
use crate::machine::Transparency;
use crate::typecheck::{TypeChecker, TypeValue};
use crate::value::{Neutral, NeutralHead, Value};

pub fn convert(
    checker: &TypeChecker<'_>,
    left: &TypeValue,
    right: &TypeValue,
    budget: usize,
) -> Judgment<()> {
    let mut remaining = budget;
    let mut work = vec![(left.clone(), right.clone())];
    let mut visited = HashSet::new();

    while let Some((left, right)) = work.pop() {
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
                work.push((*left_body, *right_body));
                work.push((*left_domain, *right_domain));
            }
            (TypeValue::Term(left), TypeValue::Term(right)) => {
                let machine = checker.machine();
                let left = machine.expose(left, Transparency::Reducible, remaining);
                let right = machine.expose(right, Transparency::Reducible, remaining);
                let (Some(left), Some(right)) = (left.proven_value(), right.proven_value()) else {
                    return Judgment::unknown("conversion-exposure");
                };
                match compare_values(checker, left, right, remaining, &mut work) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                }
            }
            (TypeValue::Term(term), other) | (other, TypeValue::Term(term)) => {
                let machine = checker.machine();
                let exposed = machine.expose(term, Transparency::Reducible, remaining);
                let Some(exposed) = exposed.proven_value() else {
                    return Judgment::unknown("conversion-exposure");
                };
                let Some(exposed) = value_as_type(checker, exposed, remaining) else {
                    return Judgment::refuted("rigid-type-constructor-mismatch");
                };
                work.push((exposed, other));
            }
            (TypeValue::Sort(_), TypeValue::Pi { .. })
            | (TypeValue::Pi { .. }, TypeValue::Sort(_)) => {
                return Judgment::refuted("rigid-type-constructor-mismatch");
            }
        }
    }

    Judgment::proven((), "guarded-relational-conversion")
}

fn compare_values(
    checker: &TypeChecker<'_>,
    left: &Value,
    right: &Value,
    budget: usize,
    work: &mut Vec<(TypeValue, TypeValue)>,
) -> Judgment<()> {
    match (left, right) {
        (Value::Sort(left), Value::Sort(right)) => {
            let (Ok(left), Ok(right)) = (
                checker.instantiate(*left, budget),
                checker.instantiate(*right, budget),
            ) else {
                return Judgment::unknown("unresolved-conversion-level");
            };
            work.push((TypeValue::Sort(left), TypeValue::Sort(right)));
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
            work.push((
                TypeValue::Term(left_body.clone()),
                TypeValue::Term(right_body.clone()),
            ));
            work.push((
                TypeValue::Term(left_domain.clone()),
                TypeValue::Term(right_domain.clone()),
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
                )
            }));
        }
        _ => return Judgment::refuted("rigid-value-constructor-mismatch"),
    }
    Judgment::proven((), "rigid-value-comparison")
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
                let (Ok(left), Ok(right)) = (
                    checker.instantiate(*left, budget),
                    checker.instantiate(*right, budget),
                ) else {
                    return Judgment::unknown("unresolved-neutral-level");
                };
                match level_equal(left, right, budget) {
                    Judgment::Proven { .. } => {}
                    Judgment::Refuted { obstruction } => {
                        return Judgment::Refuted { obstruction };
                    }
                    Judgment::Unknown { residual } => return Judgment::Unknown { residual },
                }
            }
            Judgment::proven((), "same-rigid-constant")
        }
        _ => Judgment::refuted("distinct-neutral-heads"),
    }
}

fn value_as_type(checker: &TypeChecker<'_>, value: &Value, budget: usize) -> Option<TypeValue> {
    match value {
        Value::Sort(level) => checker
            .instantiate(*level, budget)
            .ok()
            .map(TypeValue::Sort),
        Value::Pi { domain, body } => Some(TypeValue::Pi {
            domain: Box::new(TypeValue::Term(domain.clone())),
            body: Box::new(TypeValue::Term(body.clone())),
        }),
        Value::Lam { .. } | Value::Neutral(_) => None,
    }
}
