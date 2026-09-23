use std::collections::HashMap;

use crate::convert::DeltaPolicy;
use crate::environment::{ConstantDecl, Environment};
use crate::id::NameId;
use crate::id::{ExprId, LevelId};
use crate::inductive::{ClosedNonrecursiveDerivation, DerivedSignature, OpaqueInductiveKind};
use crate::judgment::Judgment;
use crate::level::LevelTerm;
use crate::parser::ResolvedExport;
use crate::syntax::{Constructor, Declaration, Expr, InductiveBlock, Level, Name, Recursor};
use crate::typecheck::{TypeChecker, TypeValue};
use crate::value::{EnvFrame, FreeId};
use crate::verdict::Verdict;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Limits {
    pub judgment_steps: usize,
}

impl Default for Limits {
    fn default() -> Self {
        Self {
            judgment_steps: 16_384,
        }
    }
}

pub fn check_export(export: ResolvedExport, limits: Limits) -> Verdict {
    check_export_with_policy(export, limits, DeltaPolicy::GuardedSemanticFallback)
}

fn check_export_with_policy(
    mut export: ResolvedExport,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Verdict {
    let mut environment = Environment::empty();

    // Keep the resolved tables available while consuming declaration records.
    let declarations = std::mem::take(&mut export.declarations);
    for declaration in declarations {
        #[cfg(feature = "diagnostics")]
        crate::diagnostics::declaration();
        let level_parameters = match &declaration {
            Declaration::Axiom { level_params, .. }
            | Declaration::Definition { level_params, .. }
            | Declaration::Theorem { level_params, .. } => Some(level_params.as_slice()),
            Declaration::Inductive(_) | Declaration::Unsupported { .. } => None,
        };
        if level_parameters.is_some_and(has_duplicate_parameter) {
            return Verdict::Reject;
        }

        let (name, established) = match declaration {
            Declaration::Axiom {
                name,
                level_params,
                ty,
            } => {
                let checker = TypeChecker::with_level_substitution(
                    &export.exprs,
                    &export.levels,
                    &environment,
                    parameter_substitution(&level_params),
                )
                .with_delta_policy(delta_policy);
                if let Err(verdict) = verdict_boundary(checker.is_type(ty, limits.judgment_steps)) {
                    return verdict;
                }
                (name, ConstantDecl::axiom(level_params, ty))
            }
            Declaration::Definition {
                name,
                level_params,
                ty,
                value,
                preferred_for_reduction,
            } => {
                let checker = TypeChecker::with_level_substitution(
                    &export.exprs,
                    &export.levels,
                    &environment,
                    parameter_substitution(&level_params),
                )
                .with_delta_policy(delta_policy);
                if let Err(verdict) = verdict_boundary(checker.is_type(ty, limits.judgment_steps)) {
                    return verdict;
                }
                let expected = TypeValue::Term(checker.closure(ty, EnvFrame::empty()));
                if let Err(verdict) =
                    verdict_boundary(checker.check(value, &expected, limits.judgment_steps))
                {
                    return verdict;
                }
                (
                    name,
                    ConstantDecl::definition(level_params, ty, value, preferred_for_reduction),
                )
            }
            Declaration::Theorem {
                all: _,
                name,
                level_params,
                ty,
                value,
            } => {
                let checker = TypeChecker::with_level_substitution(
                    &export.exprs,
                    &export.levels,
                    &environment,
                    parameter_substitution(&level_params),
                )
                .with_delta_policy(delta_policy);
                if let Err(verdict) =
                    verdict_boundary(checker.is_proposition(ty, limits.judgment_steps))
                {
                    return verdict;
                }
                let expected = TypeValue::Term(checker.closure(ty, EnvFrame::empty()));
                if let Err(verdict) =
                    verdict_boundary(checker.check(value, &expected, limits.judgment_steps))
                {
                    return verdict;
                }
                (name, ConstantDecl::theorem(level_params, ty))
            }
            Declaration::Inductive(block) => {
                match check_inductive(&export, &environment, &block, limits, delta_policy) {
                    Ok(extended) => {
                        environment = extended;
                        continue;
                    }
                    Err(verdict) => return verdict,
                }
            }
            Declaration::Unsupported { .. } => return Verdict::Unknown,
        };

        let Ok(extended) = environment.extend(name, established) else {
            return Verdict::Reject;
        };
        environment = extended;
    }

    Verdict::Accept
}

fn inductive_arity_metadata_is_well_formed(
    export: &ResolvedExport,
    inductive: &crate::syntax::InductiveType,
) -> bool {
    if has_duplicate_parameter(&inductive.level_params) {
        return false;
    }
    let Some(binders) = inductive.num_params.checked_add(inductive.num_indices) else {
        return false;
    };
    let mut expression = inductive.ty;
    for _ in 0..binders {
        let Some(Expr::Pi { body, .. }) = export.exprs.get(expression) else {
            return false;
        };
        expression = *body;
    }
    matches!(export.exprs.get(expression), Some(Expr::Sort(_)))
}

fn check_inductive(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    // G16-001 is deliberately routed by its earned name before constructor
    // cardinality dispatch. This lets missing/extra constructors remain
    // malformed claims inside the PUnit envelope (REJECT), while broader
    // indexed/recursive/nested/unsafe neighbors remain unsupported (UNKNOWN).
    if let [inductive] = block.types.as_slice()
        && name_is_root_str(export, inductive.name, "PUnit")
    {
        if inductive.num_params != 0
            || inductive.num_indices != 0
            || inductive.num_nested != 0
            || inductive.is_recursive
            || inductive.is_reflexive
            || inductive.is_unsafe
        {
            return Err(Verdict::Unknown);
        }
        let [constructor] = block.constructors.as_slice() else {
            return Err(Verdict::Reject);
        };
        if constructor.is_unsafe {
            return Err(Verdict::Unknown);
        }
        let [recursor] = block.recursors.as_slice() else {
            return Err(Verdict::Reject);
        };
        if recursor.is_unsafe {
            return Err(Verdict::Unknown);
        }
        let [level] = inductive.level_params.as_slice() else {
            return Err(Verdict::Reject);
        };
        return ExactBinaryProductDerivation {
            inductive,
            constructor,
            recursor,
            constructor_suffix: "unit",
            law: BinaryProductSortLaw::PUnit { level: *level },
        }
        .validate_and_promote(export, environment, limits, delta_policy);
    }

    // G17-001 is the first indexed law. Keep the external envelope name-sealed
    // and distinguish malformed Eq claims (REJECT) from genuinely broader
    // recursive/reflexive/unsafe/nested semantics (UNKNOWN).
    if let [inductive] = block.types.as_slice()
        && name_is_root_str(export, inductive.name, "Eq")
    {
        if inductive.num_nested != 0
            || inductive.is_recursive
            || inductive.is_reflexive
            || inductive.is_unsafe
        {
            return Err(Verdict::Unknown);
        }
        if inductive.num_params != 2 || inductive.num_indices != 1 {
            return Err(Verdict::Reject);
        }
        let [constructor] = block.constructors.as_slice() else {
            return Err(Verdict::Reject);
        };
        if constructor.is_unsafe {
            return Err(Verdict::Unknown);
        }
        let [recursor] = block.recursors.as_slice() else {
            return Err(Verdict::Reject);
        };
        if recursor.is_unsafe {
            return Err(Verdict::Unknown);
        }
        let [level] = inductive.level_params.as_slice() else {
            return Err(Verdict::Reject);
        };
        return ExactBinaryProductDerivation {
            inductive,
            constructor,
            recursor,
            constructor_suffix: "refl",
            law: BinaryProductSortLaw::Eq { level: *level },
        }
        .validate_and_promote(export, environment, limits, delta_policy);
    }

    if let [inductive] = block.types.as_slice()
        && name_is_root_str(export, inductive.name, "N")
    {
        return check_exact_nat(export, environment, block, limits, delta_policy);
    }

    if let [inductive] = block.types.as_slice()
        && name_is_root_str(export, inductive.name, "RBTree")
    {
        return check_exact_rbtree(export, environment, block, limits, delta_policy);
    }

    match block.constructors.len() {
        0 => check_empty_inductive(export, environment, block, limits, delta_policy),
        1 => check_single_constructor_inductive(export, environment, block, limits, delta_policy),
        2 => check_binary_enum(export, environment, block, limits, delta_policy),
        _ => Err(Verdict::Unknown),
    }
}

fn check_single_constructor_inductive(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let [inductive] = block.types.as_slice() else {
        return Err(Verdict::Unknown);
    };
    if name_is_root_str(export, inductive.name, "And") {
        check_exact_binary_product_family(
            export,
            environment,
            block,
            limits,
            delta_policy,
            BinaryProductFamily::And,
        )
    } else if name_is_root_str(export, inductive.name, "Prod") {
        check_exact_binary_product_family(
            export,
            environment,
            block,
            limits,
            delta_policy,
            BinaryProductFamily::Prod,
        )
    } else if name_is_root_str(export, inductive.name, "PProd") {
        check_exact_binary_product_family(
            export,
            environment,
            block,
            limits,
            delta_policy,
            BinaryProductFamily::PProd,
        )
    } else if name_is_root_str(export, inductive.name, "TwoBool") {
        check_twobool_structure(export, environment, block, limits, delta_policy)
    } else if name_is_root_str(export, inductive.name, "reduceCtorParam") {
        check_conversion_lifted_unary_recursive(export, environment, block, limits, delta_policy)
    } else if unary_field_universe_candidate(export, block) {
        check_unary_field_universe_inductive(export, environment, block, limits, delta_policy)
    } else {
        check_unrecognized_single_constructor_coherence(export, block)
    }
}

/// G23-001: conversion-lifted one-parameter, one-field recursion.
///
/// The family remains name-sealed at dispatch. The reusable law is the
/// important part: after staging the inductive type, parameter and recursive
/// field domains are compared by the kernel's existing conversion relation
/// under shared free binders. Recursor/motive/minor/rule shapes are still
/// derived structurally before opaque promotion.
fn check_conversion_lifted_unary_recursive(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let [inductive] = block.types.as_slice() else {
        return Err(Verdict::Unknown);
    };
    if inductive.num_params != 1
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || !inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || !inductive.level_params.is_empty()
        || !inductive_arity_metadata_is_well_formed(export, inductive)
    {
        return Err(Verdict::Unknown);
    }

    let Some(Expr::Pi {
        domain: inductive_parameter,
        body: inductive_result,
    }) = export.exprs.get(inductive.ty)
    else {
        return Err(Verdict::Reject);
    };
    if !matches!(export.exprs.get(*inductive_result), Some(Expr::Sort(_))) {
        return Err(Verdict::Reject);
    }

    let [constructor] = block.constructors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if constructor.is_unsafe {
        return Err(Verdict::Unknown);
    }
    if inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || constructor.index != 0
        || constructor.inductive != inductive.name
        || !constructor.level_params.is_empty()
        || constructor.num_params != 1
        || constructor.num_fields != 1
        || !name_is_child_str(export, constructor.name, inductive.name, "mk")
        || constructor_result_is_definitely_malformed(export, inductive, constructor)
        || constructor_has_definite_negative_recursive_field(export, inductive, constructor)
    {
        return Err(Verdict::Reject);
    }

    let Some(Expr::Pi {
        domain: constructor_parameter,
        body,
    }) = export.exprs.get(constructor.ty)
    else {
        return Err(Verdict::Reject);
    };
    let Some(Expr::Pi {
        domain: constructor_field,
        body: constructor_result,
    }) = export.exprs.get(*body)
    else {
        return Err(Verdict::Reject);
    };

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if recursor.is_unsafe {
        return Err(Verdict::Unknown);
    }
    if !recursor_metadata_admissible(
        export,
        inductive,
        &block.constructors,
        recursor,
        false,
        recursor.level_params.len() == 1,
    ) {
        return Err(Verdict::Reject);
    }

    let Some((recursor_parameter, recursor_minor_field, rule_field)) =
        conversion_lifted_unary_shapes(export, inductive.name, constructor.name, recursor)
    else {
        return Err(Verdict::Reject);
    };

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote(
        export,
        derived_type(inductive.name, inductive.ty),
        limits.judgment_steps,
        delta_policy,
    )?;

    // Conversion is tested only after the inductive type itself has been
    // staged, so recursive applications have real kernel authority.
    {
        let checker = TypeChecker::new(&export.exprs, &export.levels, derivation.environment())
            .with_delta_policy(delta_policy);

        let empty = EnvFrame::empty();
        verdict_boundary(checker.convert(
            &TypeValue::Term(checker.closure(*inductive_parameter, empty.clone())),
            &TypeValue::Term(checker.closure(*constructor_parameter, empty.clone())),
            limits.judgment_steps,
        ))?;
        verdict_boundary(checker.convert(
            &TypeValue::Term(checker.closure(*inductive_parameter, empty.clone())),
            &TypeValue::Term(checker.closure(recursor_parameter, empty.clone())),
            limits.judgment_steps,
        ))?;

        let alpha = FreeId(10_001);
        let field = FreeId(10_002);
        let motive = FreeId(10_003);
        let minor = FreeId(10_004);
        let parameter_frame = EnvFrame::empty().extend_free(alpha);
        let constructor_result_frame = parameter_frame.clone().extend_free(field);
        verdict_boundary(checker.convert(
            &TypeValue::Term(checker.closure(*constructor_field, parameter_frame.clone())),
            &TypeValue::Term(checker.closure(*constructor_result, constructor_result_frame)),
            limits.judgment_steps,
        ))?;

        let recursor_minor_frame = parameter_frame.clone().extend_free(motive);
        verdict_boundary(checker.convert(
            &TypeValue::Term(checker.closure(*constructor_field, parameter_frame.clone())),
            &TypeValue::Term(checker.closure(recursor_minor_field, recursor_minor_frame)),
            limits.judgment_steps,
        ))?;

        let rule_field_frame = parameter_frame.extend_free(motive).extend_free(minor);
        verdict_boundary(checker.convert(
            &TypeValue::Term(
                checker.closure(*constructor_field, EnvFrame::empty().extend_free(alpha)),
            ),
            &TypeValue::Term(checker.closure(rule_field, rule_field_frame)),
            limits.judgment_steps,
        ))?;
    }

    derivation.promote_all(
        export,
        [derived_constructor(constructor), derived_recursor(recursor)],
        limits.judgment_steps,
        delta_policy,
    )?;
    Ok(derivation.finish())
}

fn is_empty_inductive_applied_to_bvar(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    parameter: u64,
) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::App { fun, arg })
            if is_empty_constant(export, *fun, inductive)
                && is_bvar(export, *arg, parameter)
    )
}

fn is_unary_recursive_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    motive_level: NameId,
) -> bool {
    let Some(Expr::Pi {
        domain: target,
        body: result,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    is_empty_inductive_applied_to_bvar(export, *target, inductive, 0)
        && is_sort_parameter(export, *result, motive_level)
}

fn unary_recursive_minor_field(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
) -> Option<ExprId> {
    let Expr::Pi {
        domain: field,
        body,
    } = export.exprs.get(expression)?
    else {
        return None;
    };
    let Expr::Pi {
        domain: induction_hypothesis,
        body: result,
    } = export.exprs.get(*body)?
    else {
        return None;
    };
    if !is_bvar_application(export, *induction_hypothesis, 1, 0) {
        return None;
    }
    let Expr::App {
        fun: motive,
        arg: constructed,
    } = export.exprs.get(*result)?
    else {
        return None;
    };
    (is_bvar(export, *motive, 2)
        && is_constructor_applied_to_two_bvars(export, *constructed, constructor, 3, 1))
    .then_some(*field)
}

fn conversion_lifted_unary_shapes(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    recursor: &Recursor,
) -> Option<(ExprId, ExprId, ExprId)> {
    let (recursor_domains, recursor_result) = pi_spine(export, recursor.ty, 4)?;
    let [parameter, motive, minor, target] = recursor_domains.as_slice() else {
        return None;
    };
    if !is_unary_recursive_motive_type(export, *motive, inductive, recursor.level_params[0])
        || !is_empty_inductive_applied_to_bvar(export, *target, inductive, 2)
        || !is_bvar_application(export, recursor_result, 2, 0)
    {
        return None;
    }
    let recursor_minor_field = unary_recursive_minor_field(export, *minor, constructor)?;

    let [rule] = recursor.rules.as_slice() else {
        return None;
    };
    let (rule_domains, rule_result) = lam_spine(export, rule.rhs, 4)?;
    let [_parameter, rule_motive, rule_minor, rule_field] = rule_domains.as_slice() else {
        return None;
    };
    if !is_unary_recursive_motive_type(export, *rule_motive, inductive, recursor.level_params[0])
        || unary_recursive_minor_field(export, *rule_minor, constructor).is_none()
    {
        return None;
    }

    let Expr::App {
        fun: minor_at_field,
        arg: recursive_call,
    } = export.exprs.get(rule_result)?
    else {
        return None;
    };
    if !is_bvar_application(export, *minor_at_field, 1, 0) {
        return None;
    }
    let (head, arguments) = application_spine(export, *recursive_call);
    if !is_unary_polymorphic_constant(export, head, recursor.name, recursor.level_params[0])
        || !are_bvars(export, &arguments, &[3, 2, 1, 0])
    {
        return None;
    }

    Some((*parameter, recursor_minor_field, *rule_field))
}

/// G24-001 candidate frontier: one manifest field, no parameters or indices.
///
/// This is deliberately structural and narrow. It recognizes the first
/// untouched universe corridor without granting a general inductive engine:
/// one safe, nonrecursive, nonreflexive, nonnested inductive; one `.mk`
/// constructor with exactly one manifest Sort field; and one recursor.
fn unary_field_universe_candidate(export: &ResolvedExport, block: &InductiveBlock) -> bool {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return false;
    };
    inductive.num_params == 0
        && inductive.num_indices == 0
        && inductive.num_nested == 0
        && !inductive.is_recursive
        && !inductive.is_reflexive
        && !inductive.is_unsafe
        && constructor.num_params == 0
        && constructor.num_fields == 1
        && !constructor.is_unsafe
        && !recursor.is_unsafe
        && name_is_child_str(export, constructor.name, inductive.name, "mk")
        && matches!(export.exprs.get(inductive.ty), Some(Expr::Sort(_)))
        && matches!(
            export.exprs.get(constructor.ty),
            Some(Expr::Pi { domain, .. })
                if matches!(export.exprs.get(*domain), Some(Expr::Sort(_)))
        )
}

fn unary_field_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: &crate::syntax::InductiveType,
    motive_level: Option<NameId>,
) -> bool {
    let Some(Expr::Pi {
        domain: target,
        body: result,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    inductive_constant_uses_declared_levels(
        export,
        *target,
        inductive.name,
        &inductive.level_params,
    ) && match motive_level {
        None => is_prop_sort(export, *result),
        Some(level) => is_sort_parameter(export, *result, level),
    }
}

fn unary_field_constructor_application(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: &Constructor,
    field: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 1
        && inductive_constant_uses_declared_levels(
            export,
            head,
            constructor.name,
            &constructor.level_params,
        )
        && is_bvar(export, arguments[0], field)
}

fn unary_field_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    field_domain: ExprId,
    constructor: &Constructor,
) -> bool {
    let Some(Expr::Pi {
        domain: field,
        body: result,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    if *field != field_domain {
        return false;
    }
    let Some(Expr::App {
        fun: motive,
        arg: constructed,
    }) = export.exprs.get(*result)
    else {
        return false;
    };
    is_bvar(export, *motive, 1)
        && unary_field_constructor_application(export, *constructed, constructor, 0)
}

fn unary_field_recursor_shape(
    export: &ResolvedExport,
    inductive: &crate::syntax::InductiveType,
    constructor: &Constructor,
    recursor: &Recursor,
    field_domain: ExprId,
    motive_level: Option<NameId>,
) -> bool {
    let Some((domains, result)) = pi_spine(export, recursor.ty, 3) else {
        return false;
    };
    let [motive, minor, target] = domains.as_slice() else {
        return false;
    };
    if !unary_field_motive_type(export, *motive, inductive, motive_level)
        || !unary_field_minor_type(export, *minor, field_domain, constructor)
        || !inductive_constant_uses_declared_levels(
            export,
            *target,
            inductive.name,
            &inductive.level_params,
        )
        || !is_bvar_application(export, result, 2, 0)
    {
        return false;
    }

    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    let Some((rule_domains, rule_result)) = lam_spine(export, rule.rhs, 3) else {
        return false;
    };
    let [rule_motive, rule_minor, rule_field] = rule_domains.as_slice() else {
        return false;
    };
    unary_field_motive_type(export, *rule_motive, inductive, motive_level)
        && unary_field_minor_type(export, *rule_minor, field_domain, constructor)
        && *rule_field == field_domain
        && is_bvar_application(export, rule_result, 1, 0)
}

fn check_unary_field_universe_inductive(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let [inductive] = block.types.as_slice() else {
        return Err(Verdict::Unknown);
    };
    let [constructor] = block.constructors.as_slice() else {
        return Err(Verdict::Unknown);
    };
    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Unknown);
    };

    if inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || constructor.index != 0
        || constructor.inductive != inductive.name
        || constructor.level_params != inductive.level_params
        || has_duplicate_parameter(&inductive.level_params)
        || constructor_result_is_definitely_malformed(export, inductive, constructor)
        || constructor_has_definite_negative_recursive_field(export, inductive, constructor)
    {
        return Err(Verdict::Reject);
    }

    let Some(Expr::Sort(inductive_level_id)) = export.exprs.get(inductive.ty) else {
        return Err(Verdict::Unknown);
    };
    let Some(Expr::Pi {
        domain: field_domain,
        ..
    }) = export.exprs.get(constructor.ty)
    else {
        return Err(Verdict::Reject);
    };
    let Some(Expr::Sort(field_level_id)) = export.exprs.get(*field_domain) else {
        return Err(Verdict::Unknown);
    };

    let substitution = parameter_substitution(&inductive.level_params);
    let inductive_level = crate::level::instantiate_level(
        &export.levels,
        *inductive_level_id,
        &substitution,
        limits.judgment_steps,
    )
    .map_err(|_| Verdict::Unknown)?;
    let field_level = crate::level::instantiate_level(
        &export.levels,
        *field_level_id,
        &substitution,
        limits.judgment_steps,
    )
    .map_err(|_| Verdict::Unknown)?;

    let is_prop = matches!(inductive_level, crate::level::LevelTerm::Zero);
    if !is_prop {
        let field_type_level = crate::level::succ(field_level);
        let upper = crate::level::max(field_type_level, inductive_level.clone());
        verdict_boundary(crate::level::level_equal(
            upper,
            inductive_level.clone(),
            limits.judgment_steps,
        ))?;
    }

    let motive_level = if is_prop {
        if !recursor.level_params.is_empty() {
            return Err(Verdict::Reject);
        }
        None
    } else {
        let Some((first, rest)) = recursor.level_params.split_first() else {
            return Err(Verdict::Reject);
        };
        if rest != inductive.level_params.as_slice() {
            return Err(Verdict::Reject);
        }
        Some(*first)
    };
    if !recursor_metadata_admissible(
        export,
        inductive,
        &block.constructors,
        recursor,
        false,
        true,
    ) || !unary_field_recursor_shape(
        export,
        inductive,
        constructor,
        recursor,
        *field_domain,
        motive_level,
    ) {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    let derived_inductive = if inductive.level_params.is_empty() {
        derived_type(inductive.name, inductive.ty)
    } else {
        derived_polymorphic_type(inductive.name, &inductive.level_params, inductive.ty)
    };
    derivation.promote_all(
        export,
        [derived_inductive, derived_constructor(constructor)],
        limits.judgment_steps,
        delta_policy,
    )?;
    derivation.promote(
        export,
        derived_recursor(recursor),
        limits.judgment_steps,
        delta_policy,
    )?;
    Ok(derivation.finish())
}

/// G21-001 is a rejection-only constructor-result law for the otherwise
/// unrecognized single-constructor frontier. It does not compare constructor
/// parameter domains, because those may require conversion (tutorial 055).
/// Instead it checks only hard structural invariants of the constructor result:
/// owner/index metadata, declared universe order, parameter reuse/order, and
/// absence of the inductive itself inside an index.
fn check_unrecognized_single_constructor_coherence(
    export: &ResolvedExport,
    block: &InductiveBlock,
) -> Result<Environment, Verdict> {
    let [inductive] = block.types.as_slice() else {
        return Err(Verdict::Unknown);
    };
    let [constructor] = block.constructors.as_slice() else {
        return Err(Verdict::Unknown);
    };

    // Preserve unsupported semantic envelopes rather than strengthening them
    // merely because they are unfamiliar.
    if inductive.is_unsafe
        || inductive.is_reflexive
        || inductive.num_nested != 0
        || constructor.is_unsafe
        || block.recursors.iter().any(|recursor| recursor.is_unsafe)
    {
        return Err(Verdict::Unknown);
    }

    if constructor_result_is_definitely_malformed(export, inductive, constructor)
        || constructor_has_definite_negative_recursive_field(export, inductive, constructor)
        || recursor_metadata_is_definitely_malformed(export, block)
    {
        Err(Verdict::Reject)
    } else {
        Err(Verdict::Unknown)
    }
}

/// G26-001 is rejection-only. It checks structural recursor metadata that is
/// fixed by a single-inductive declaration without claiming the unsupported
/// inductive itself is derivable. Universe/elimination details remain outside
/// this law and therefore cannot turn a coherent unsupported block into ACCEPT.
fn recursor_metadata_is_definitely_malformed(
    export: &ResolvedExport,
    block: &InductiveBlock,
) -> bool {
    let [inductive] = block.types.as_slice() else {
        return false;
    };
    let [recursor] = block.recursors.as_slice() else {
        return false;
    };

    recursor.all != inductive.all
        || recursor.num_params != inductive.num_params
        || recursor.num_indices != inductive.num_indices
        || recursor.num_motives != 1
        || recursor.num_minors != block.constructors.len() as u64
        || recursor.rules.len() != block.constructors.len()
        || !name_is_child_str(export, recursor.name, inductive.name, "rec")
        || recursor
            .rules
            .iter()
            .zip(&block.constructors)
            .any(|(rule, constructor)| {
                rule.constructor != constructor.name || rule.num_fields != constructor.num_fields
            })
}

fn expression_has_definite_negative_occurrence(
    export: &ResolvedExport,
    expression: ExprId,
    target: NameId,
    positive: bool,
) -> bool {
    match export.exprs.get(expression) {
        Some(Expr::Const { name, .. }) => *name == target && !positive,
        Some(Expr::App { fun, arg }) => {
            expression_has_definite_negative_occurrence(export, *fun, target, positive)
                || expression_has_definite_negative_occurrence(export, *arg, target, positive)
        }
        Some(Expr::Pi { domain, body }) => {
            expression_has_definite_negative_occurrence(export, *domain, target, !positive)
                || expression_has_definite_negative_occurrence(export, *body, target, positive)
        }
        Some(Expr::Lam { domain, body }) => {
            expression_has_definite_negative_occurrence(export, *domain, target, positive)
                || expression_has_definite_negative_occurrence(export, *body, target, positive)
        }
        Some(Expr::Let { ty, value, body }) => {
            expression_has_definite_negative_occurrence(export, *ty, target, positive)
                || expression_has_definite_negative_occurrence(export, *value, target, positive)
                || expression_has_definite_negative_occurrence(export, *body, target, positive)
        }
        Some(Expr::BVar(_) | Expr::Sort(_)) | None => false,
    }
}

fn constructor_has_definite_negative_recursive_field(
    export: &ResolvedExport,
    inductive: &crate::syntax::InductiveType,
    constructor: &Constructor,
) -> bool {
    let Some(total_binders) = constructor.num_params.checked_add(constructor.num_fields) else {
        return false;
    };
    let mut expression = constructor.ty;
    for binder in 0..total_binders {
        let Some(Expr::Pi { domain, body }) = export.exprs.get(expression) else {
            return false;
        };
        if binder >= constructor.num_params
            && expression_has_definite_negative_occurrence(export, *domain, inductive.name, true)
        {
            return true;
        }
        expression = *body;
    }
    false
}

/// G21-001 result-spine coherence; G22-001 adds only a definite-negative
/// field rejection above. Neither law grants positive inductive authority.
fn constructor_result_is_definitely_malformed(
    export: &ResolvedExport,
    inductive: &crate::syntax::InductiveType,
    constructor: &Constructor,
) -> bool {
    if constructor.inductive != inductive.name
        || constructor.index != 0
        || constructor.num_params != inductive.num_params
        || constructor.level_params != inductive.level_params
    {
        return true;
    }

    let Some(num_binders) = constructor.num_params.checked_add(constructor.num_fields) else {
        return true;
    };
    let mut result = constructor.ty;
    for _ in 0..num_binders {
        let Some(Expr::Pi { body, .. }) = export.exprs.get(result) else {
            return true;
        };
        result = *body;
    }

    let (head, arguments) = application_spine(export, result);
    if !inductive_constant_uses_declared_levels(
        export,
        head,
        inductive.name,
        &inductive.level_params,
    ) {
        return true;
    }

    let Some(expected_arguments) = inductive.num_params.checked_add(inductive.num_indices) else {
        return true;
    };
    let Ok(expected_arguments) = usize::try_from(expected_arguments) else {
        return true;
    };
    if arguments.len() != expected_arguments {
        return true;
    }

    let Ok(num_params) = usize::try_from(inductive.num_params) else {
        return true;
    };
    for parameter in 0..num_params {
        let parameter = parameter as u64;
        let expected_bvar = constructor.num_fields + inductive.num_params - 1 - parameter;
        if !is_bvar(export, arguments[parameter as usize], expected_bvar) {
            return true;
        }
    }

    arguments[num_params..]
        .iter()
        .any(|argument| expression_contains_constant(export, *argument, inductive.name))
}

fn inductive_constant_uses_declared_levels(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level_params: &[NameId],
) -> bool {
    let Some(Expr::Const { name, levels }) = export.exprs.get(expression) else {
        return false;
    };
    *name == inductive
        && levels.len() == level_params.len()
        && levels.iter().zip(level_params).all(|(level, expected)| {
            matches!(export.levels.get(*level), Some(Level::Param(name)) if name == expected)
        })
}

fn expression_contains_constant(
    export: &ResolvedExport,
    expression: ExprId,
    target: NameId,
) -> bool {
    match export.exprs.get(expression) {
        Some(Expr::Const { name, .. }) => *name == target,
        Some(Expr::App { fun, arg }) => {
            expression_contains_constant(export, *fun, target)
                || expression_contains_constant(export, *arg, target)
        }
        Some(Expr::Lam { domain, body }) | Some(Expr::Pi { domain, body }) => {
            expression_contains_constant(export, *domain, target)
                || expression_contains_constant(export, *body, target)
        }
        Some(Expr::Let { ty, value, body }) => {
            expression_contains_constant(export, *ty, target)
                || expression_contains_constant(export, *value, target)
                || expression_contains_constant(export, *body, target)
        }
        Some(Expr::BVar(_) | Expr::Sort(_)) | None => false,
    }
}

/// G9-001's deliberately narrow promotion boundary. Parsing preserves the
/// complete block, but authority is granted only to the exact safe empty-type
/// schema whose recursor signature is independently derived below.
fn check_empty_inductive(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let [inductive] = block.types.as_slice() else {
        return Err(Verdict::Unknown);
    };
    if !block.constructors.is_empty() {
        return Err(Verdict::Unknown);
    }

    // G20-001 is deliberately scoped to the zero-constructor frontier. It is
    // rejection-only and therefore cannot grant new inductive authority.
    // Within this frontier, malformed arity metadata is decidable: declared
    // parameters/indices must correspond to the exact Pi telescope ending in
    // Sort, and universe parameters must be unique.
    if !inductive_arity_metadata_is_well_formed(export, inductive) {
        return Err(Verdict::Reject);
    }

    // This is the G9 family discriminator, not a general empty inductive
    // rule: a nullary type living structurally in either Prop or Type.  Prop
    // is included because the extra/orphan-rec falsifiers target `False`.
    if inductive.num_params != 0
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || !matches!(
            export.exprs.get(inductive.ty),
            Some(Expr::Sort(level)) if matches!(
                export.levels.get(*level),
                Some(Level::Zero | Level::Succ(LevelId(0)))
            )
        )
    {
        return Err(Verdict::Unknown);
    }

    let exact_type_metadata = inductive.all == [inductive.name]
        && inductive.constructors.is_empty()
        && !inductive.is_recursive
        && !inductive.is_reflexive
        && !inductive.is_unsafe
        && inductive.level_params.is_empty();
    if !exact_type_metadata {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote(
        export,
        derived_type(inductive.name, inductive.ty),
        limits.judgment_steps,
        delta_policy,
    )?;

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if !recursor_metadata_admissible(
        export,
        inductive,
        &block.constructors,
        recursor,
        false,
        !recursor.is_unsafe && recursor.level_params.len() == 1,
    ) || !empty_recursor_obligation(export, inductive.name, recursor)
    {
        return Err(Verdict::Reject);
    }

    derivation.promote(
        export,
        derived_recursor(recursor),
        limits.judgment_steps,
        delta_policy,
    )?;
    Ok(derivation.finish())
}

fn empty_recursor_obligation(
    export: &ResolvedExport,
    inductive: NameId,
    recursor: &Recursor,
) -> bool {
    let Some((domains, result)) = pi_spine(export, recursor.ty, 2) else {
        return false;
    };
    let [motive, target] = domains.as_slice() else {
        return false;
    };
    let Some(Expr::Pi {
        domain: motive_argument,
        body: motive_sort,
    }) = export.exprs.get(*motive)
    else {
        return false;
    };
    is_empty_constant(export, *motive_argument, inductive)
        && is_empty_constant(export, *target, inductive)
        && matches!(
            export.exprs.get(*motive_sort),
            Some(Expr::Sort(level)) if matches!(
                export.levels.get(*level),
                Some(Level::Param(name)) if name == &recursor.level_params[0]
            )
        )
        && is_bvar_application(export, result, 1, 0)
}

fn is_empty_constant(export: &ResolvedExport, expression: ExprId, name: NameId) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::Const { name: actual, levels }) if *actual == name && levels.is_empty()
    )
}

/// G18-001: exact local recursive N. Recursion is admitted only inside this
/// name-sealed envelope; the existing staged signature transaction is reused
/// and no general positivity or recursive-inductive search is introduced.
fn check_exact_nat(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let [inductive] = block.types.as_slice() else {
        return Err(Verdict::Unknown);
    };
    if inductive.num_params != 0
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || inductive.is_reflexive
        || inductive.is_unsafe
    {
        return Err(Verdict::Unknown);
    }
    if !inductive.is_recursive {
        return Err(Verdict::Reject);
    }
    if !inductive.level_params.is_empty()
        || !matches!(
            export.exprs.get(inductive.ty),
            Some(Expr::Sort(level))
                if matches!(export.levels.get(*level), Some(Level::Succ(LevelId(0))))
        )
    {
        return Err(Verdict::Reject);
    }

    let [zero, succ] = block.constructors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if zero.is_unsafe || succ.is_unsafe {
        return Err(Verdict::Unknown);
    }
    if inductive.all != [inductive.name]
        || inductive.constructors != [zero.name, succ.name]
        || zero.index != 0
        || zero.inductive != inductive.name
        || !zero.level_params.is_empty()
        || zero.num_fields != 0
        || zero.num_params != 0
        || !name_is_child_str(export, zero.name, inductive.name, "zero")
        || !is_empty_constant(export, zero.ty, inductive.name)
        || succ.index != 1
        || succ.inductive != inductive.name
        || !succ.level_params.is_empty()
        || succ.num_fields != 1
        || succ.num_params != 0
        || !name_is_child_str(export, succ.name, inductive.name, "succ")
        || !matches!(
            export.exprs.get(succ.ty),
            Some(Expr::Pi { domain, body })
                if is_empty_constant(export, *domain, inductive.name)
                    && is_empty_constant(export, *body, inductive.name)
        )
    {
        return Err(Verdict::Reject);
    }

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if recursor.is_unsafe {
        return Err(Verdict::Unknown);
    }
    if !recursor_metadata_admissible(
        export,
        inductive,
        &block.constructors,
        recursor,
        false,
        recursor.level_params.len() == 1,
    ) || !nat_recursor_obligations(export, inductive.name, zero.name, succ.name, recursor)
    {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_type(inductive.name, inductive.ty),
            derived_constructor(zero),
            derived_constructor(succ),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    Ok(derivation.finish())
}

fn nat_recursor_obligations(
    export: &ResolvedExport,
    inductive: NameId,
    zero: NameId,
    succ: NameId,
    recursor: &Recursor,
) -> bool {
    let motive_level = recursor.level_params[0];

    let motive_ok = |expression: ExprId| {
        matches!(
            export.exprs.get(expression),
            Some(Expr::Pi { domain, body })
                if is_empty_constant(export, *domain, inductive)
                    && is_sort_parameter(export, *body, motive_level)
        )
    };

    let succ_minor_ok = |expression: ExprId| {
        let Some((domains, result)) = pi_spine(export, expression, 2) else {
            return false;
        };
        let [value, induction_hypothesis] = domains.as_slice() else {
            return false;
        };
        let Some(Expr::App {
            fun: motive,
            arg: succ_value,
        }) = export.exprs.get(result)
        else {
            return false;
        };
        let Some(Expr::App {
            fun: succ_head,
            arg: succ_arg,
        }) = export.exprs.get(*succ_value)
        else {
            return false;
        };
        is_empty_constant(export, *value, inductive)
            && is_bvar_application(export, *induction_hypothesis, 2, 0)
            && is_bvar(export, *motive, 3)
            && is_empty_constant(export, *succ_head, succ)
            && is_bvar(export, *succ_arg, 1)
    };

    let Some((type_domains, type_result)) = pi_spine(export, recursor.ty, 4) else {
        return false;
    };
    let [motive, zero_minor, succ_minor, target] = type_domains.as_slice() else {
        return false;
    };
    let type_ok = motive_ok(*motive)
        && is_bvar_applied_to_constant(export, *zero_minor, 0, zero)
        && succ_minor_ok(*succ_minor)
        && is_empty_constant(export, *target, inductive)
        && is_bvar_application(export, type_result, 3, 0);

    let [zero_rule, succ_rule] = recursor.rules.as_slice() else {
        return false;
    };
    let zero_ok = lam_spine(export, zero_rule.rhs, 3).is_some_and(|(domains, result)| {
        matches!(domains.as_slice(), [motive, zero_minor, succ_minor]
            if motive_ok(*motive)
                && is_bvar_applied_to_constant(export, *zero_minor, 0, zero)
                && succ_minor_ok(*succ_minor)
                && is_bvar(export, result, 1))
    });

    let succ_ok = lam_spine(export, succ_rule.rhs, 4).is_some_and(|(domains, result)| {
        let [motive, zero_minor, succ_minor, value] = domains.as_slice() else {
            return false;
        };
        if !motive_ok(*motive)
            || !is_bvar_applied_to_constant(export, *zero_minor, 0, zero)
            || !succ_minor_ok(*succ_minor)
            || !is_empty_constant(export, *value, inductive)
        {
            return false;
        }
        let Some(Expr::App {
            fun: succ_step,
            arg: recursive_call,
        }) = export.exprs.get(result)
        else {
            return false;
        };
        if !is_bvar_application(export, *succ_step, 1, 0) {
            return false;
        }
        let (head, arguments) = application_spine(export, *recursive_call);
        arguments.len() == 4
            && is_unary_polymorphic_constant(export, head, recursor.name, motive_level)
            && are_bvars(export, &arguments, &[3, 2, 1, 0])
    });

    type_ok && zero_ok && succ_ok
}

fn check_exact_rbtree(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let [inductive] = block.types.as_slice() else {
        return Err(Verdict::Unknown);
    };
    if inductive.num_nested != 0 || inductive.is_reflexive || inductive.is_unsafe {
        return Err(Verdict::Unknown);
    }
    if inductive.num_params != 1 || inductive.num_indices != 2 || !inductive.is_recursive {
        return Err(Verdict::Reject);
    }
    let [level] = inductive.level_params.as_slice() else {
        return Err(Verdict::Reject);
    };
    let Some((type_domains, type_result)) = pi_spine(export, inductive.ty, 3) else {
        return Err(Verdict::Reject);
    };
    let [carrier, color, height] = type_domains.as_slice() else {
        return Err(Verdict::Reject);
    };
    if !is_sort_succ_parameter(export, *carrier, *level)
        || !is_root_empty_constant_named(export, *color, "Color")
        || !is_root_empty_constant_named(export, *height, "N")
        || !is_sort_succ_parameter(export, type_result, *level)
    {
        return Err(Verdict::Reject);
    }

    let [leaf, red, black] = block.constructors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if leaf.is_unsafe || red.is_unsafe || black.is_unsafe {
        return Err(Verdict::Unknown);
    }
    let leaf_type_valid = pi_spine(export, leaf.ty, 1).is_some_and(|(domains, result)| {
        let [leaf_carrier] = domains.as_slice() else {
            return false;
        };
        rbtree_application_parts(export, result, inductive.name, *level).is_some_and(
            |(result_carrier, result_color, result_height)| {
                is_sort_succ_parameter(export, *leaf_carrier, *level)
                    && is_bvar(export, result_carrier, 0)
                    && is_child_empty_constant_named(export, result_color, "Color", "b")
                    && is_child_empty_constant_named(export, result_height, "N", "zero")
            },
        )
    });
    if inductive.all != [inductive.name]
        || inductive.constructors != [leaf.name, red.name, black.name]
        || !valid_rbtree_constructor_metadata(export, inductive.name, *level, leaf, 0, 0, "leaf")
        || !valid_rbtree_constructor_metadata(export, inductive.name, *level, red, 1, 4, "red")
        || !valid_rbtree_constructor_metadata(export, inductive.name, *level, black, 2, 6, "black")
        || !leaf_type_valid
        || !is_derived_rbtree_branch_type(export, red.ty, inductive.name, *level, RbBranch::Red)
        || !is_derived_rbtree_branch_type(export, black.ty, inductive.name, *level, RbBranch::Black)
    {
        return Err(Verdict::Reject);
    }

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if recursor.is_unsafe {
        return Err(Verdict::Unknown);
    }
    if !recursor_metadata_admissible(
        export,
        inductive,
        &block.constructors,
        recursor,
        false,
        recursor.level_params.len() == 2
            && recursor.level_params[1] == *level
            && recursor.level_params[0] != *level,
    ) || !is_derived_rbtree_recursor_type(
        export,
        inductive.name,
        *level,
        [leaf.name, red.name, black.name],
        recursor,
    ) || !are_derived_rbtree_rules(
        export,
        inductive.name,
        *level,
        [leaf.name, red.name, black.name],
        recursor,
    ) {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_polymorphic_type(inductive.name, &inductive.level_params, inductive.ty),
            derived_constructor(leaf),
            derived_constructor(red),
            derived_constructor(black),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    Ok(derivation.finish())
}

fn valid_rbtree_constructor_metadata(
    export: &ResolvedExport,
    inductive: NameId,
    level: NameId,
    constructor: &Constructor,
    index: u64,
    fields: u64,
    suffix: &str,
) -> bool {
    constructor.index == index
        && constructor.inductive == inductive
        && constructor.level_params == [level]
        && constructor.num_fields == fields
        && constructor.num_params == 1
        && name_is_child_str(export, constructor.name, inductive, suffix)
}

fn rbtree_application_parts(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
) -> Option<(ExprId, ExprId, ExprId)> {
    let (head, arguments) = application_spine(export, expression);
    let [carrier, color, height] = arguments.as_slice() else {
        return None;
    };
    is_unary_polymorphic_constant(export, head, inductive, level)
        .then_some((*carrier, *color, *height))
}

fn is_root_empty_constant_named(export: &ResolvedExport, expression: ExprId, root: &str) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::Const { name, levels })
            if levels.is_empty() && name_is_root_str(export, *name, root)
    )
}

fn is_child_empty_constant_named(
    export: &ResolvedExport,
    expression: ExprId,
    root: &str,
    child: &str,
) -> bool {
    let Some(Expr::Const { name, levels }) = export.exprs.get(expression) else {
        return false;
    };
    if !levels.is_empty() {
        return false;
    }
    matches!(
        export.names.get(*name),
        Some(Name::Str { prefix, value })
            if value == child && name_is_root_str(export, *prefix, root)
    )
}

fn is_named_succ_bvar(
    export: &ResolvedExport,
    expression: ExprId,
    root: &str,
    child: &str,
    argument: u64,
) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::App { fun, arg })
            if is_child_empty_constant_named(export, *fun, root, child)
                && is_bvar(export, *arg, argument)
    )
}

fn is_derived_rbtree_branch_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
    branch: RbBranch,
) -> bool {
    let branch_index = match branch {
        RbBranch::Red => 0,
        RbBranch::Black => 1,
    };
    let extra_colors = 2 * branch_index;
    let arity = 5 + extra_colors;
    let Some((domains, result)) = pi_spine(export, expression, arity) else {
        return false;
    };

    let carrier = domains[0];
    let height = domains[1 + extra_colors];
    let left = domains[2 + extra_colors];
    let value = domains[3 + extra_colors];
    let right = domains[4 + extra_colors];

    let (
        Some((left_carrier, left_color, left_height)),
        Some((right_carrier, right_color, right_height)),
        Some((result_carrier, result_color, result_height)),
    ) = (
        rbtree_application_parts(export, left, inductive, level),
        rbtree_application_parts(export, right, inductive, level),
        rbtree_application_parts(export, result, inductive, level),
    )
    else {
        return false;
    };

    let prefix_colors_ok = match branch {
        RbBranch::Red => true,
        RbBranch::Black => {
            is_root_empty_constant_named(export, domains[1], "Color")
                && is_root_empty_constant_named(export, domains[2], "Color")
        }
    };
    let child_colors_ok = match branch {
        RbBranch::Red => {
            is_child_empty_constant_named(export, left_color, "Color", "b")
                && is_child_empty_constant_named(export, right_color, "Color", "b")
        }
        RbBranch::Black => is_bvar(export, left_color, 2) && is_bvar(export, right_color, 3),
    };
    let result_index_ok = match branch {
        RbBranch::Red => {
            is_child_empty_constant_named(export, result_color, "Color", "r")
                && is_bvar(export, result_height, 3)
        }
        RbBranch::Black => {
            is_child_empty_constant_named(export, result_color, "Color", "b")
                && is_named_succ_bvar(export, result_height, "N", "succ", 3)
        }
    };

    is_sort_succ_parameter(export, carrier, level)
        && prefix_colors_ok
        && is_root_empty_constant_named(export, height, "N")
        && is_bvar(export, left_carrier, 1 + 2 * branch_index as u64)
        && child_colors_ok
        && is_bvar(export, left_height, 0)
        && is_bvar(export, value, 2 + 2 * branch_index as u64)
        && is_bvar(export, right_carrier, 3 + 2 * branch_index as u64)
        && is_bvar(export, right_height, 2)
        && is_bvar(export, result_carrier, 4 + 2 * branch_index as u64)
        && result_index_ok
}

fn application_spine(export: &ResolvedExport, expression: ExprId) -> (ExprId, Vec<ExprId>) {
    let mut head = expression;
    let mut arguments = Vec::new();
    while let Some(Expr::App { fun, arg }) = export.exprs.get(head) {
        arguments.push(*arg);
        head = *fun;
    }
    arguments.reverse();
    (head, arguments)
}

fn pi_spine(
    export: &ResolvedExport,
    expression: ExprId,
    count: usize,
) -> Option<(Vec<ExprId>, ExprId)> {
    let mut current = expression;
    let mut domains = Vec::with_capacity(count);
    for _ in 0..count {
        let Expr::Pi { domain, body } = export.exprs.get(current)? else {
            return None;
        };
        domains.push(*domain);
        current = *body;
    }
    Some((domains, current))
}

fn lam_spine(
    export: &ResolvedExport,
    expression: ExprId,
    count: usize,
) -> Option<(Vec<ExprId>, ExprId)> {
    let mut current = expression;
    let mut domains = Vec::with_capacity(count);
    for _ in 0..count {
        let Expr::Lam { domain, body } = export.exprs.get(current)? else {
            return None;
        };
        domains.push(*domain);
        current = *body;
    }
    Some((domains, current))
}

fn motive_application_parts(
    export: &ResolvedExport,
    expression: ExprId,
    motive: u64,
) -> Option<(ExprId, ExprId, ExprId)> {
    let (head, arguments) = application_spine(export, expression);
    if !is_bvar(export, head, motive) || arguments.len() != 3 {
        return None;
    }
    Some((arguments[0], arguments[1], arguments[2]))
}

fn rbtree_constructor_application_args(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    level: NameId,
) -> Option<Vec<ExprId>> {
    let (head, arguments) = application_spine(export, expression);
    is_unary_polymorphic_constant(export, head, constructor, level).then_some(arguments)
}

fn rbtree_recursor_application_args(
    export: &ResolvedExport,
    expression: ExprId,
    recursor: NameId,
    motive_level: NameId,
    level: NameId,
) -> Option<Vec<ExprId>> {
    let (head, arguments) = application_spine(export, expression);
    is_polymorphic_constant(export, head, recursor, motive_level, level).then_some(arguments)
}

fn is_rbtree_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
    motive_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [color, height, tree] = domains.as_slice() else {
        return false;
    };
    let Some((carrier, tree_color, tree_height)) =
        rbtree_application_parts(export, *tree, inductive, level)
    else {
        return false;
    };
    is_root_empty_constant_named(export, *color, "Color")
        && is_root_empty_constant_named(export, *height, "N")
        && is_bvar(export, carrier, 2)
        && is_bvar(export, tree_color, 1)
        && is_bvar(export, tree_height, 0)
        && is_sort_parameter(export, result, motive_level)
}

#[derive(Clone, Copy)]
enum RbBranch {
    Red,
    Black,
}

fn is_rbtree_branch_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    constructor: NameId,
    level: NameId,
    branch: RbBranch,
) -> bool {
    let color_prefix = match branch {
        RbBranch::Red => 0,
        RbBranch::Black => 2,
    };
    let arity = 6 + color_prefix;
    let Some((domains, result)) = pi_spine(export, expression, arity) else {
        return false;
    };

    let height = domains[color_prefix];
    let left = domains[color_prefix + 1];
    let value = domains[color_prefix + 2];
    let right = domains[color_prefix + 3];
    let left_ih = domains[color_prefix + 4];
    let right_ih = domains[color_prefix + 5];

    let (
        Some((left_carrier, left_color, left_height)),
        Some((right_carrier, right_color, right_height)),
    ) = (
        rbtree_application_parts(export, left, inductive, level),
        rbtree_application_parts(export, right, inductive, level),
    )
    else {
        return false;
    };

    let (left_motive, right_motive, result_motive) = match branch {
        RbBranch::Red => (5, 6, 7),
        RbBranch::Black => (8, 9, 10),
    };
    let (
        Some((left_ih_color, left_ih_height, left_ih_tree)),
        Some((right_ih_color, right_ih_height, right_ih_tree)),
        Some((result_color, result_height, result_tree)),
    ) = (
        motive_application_parts(export, left_ih, left_motive),
        motive_application_parts(export, right_ih, right_motive),
        motive_application_parts(export, result, result_motive),
    )
    else {
        return false;
    };

    let Some(result_args) =
        rbtree_constructor_application_args(export, result_tree, constructor, level)
    else {
        return false;
    };

    let branch_index = match branch {
        RbBranch::Red => 0,
        RbBranch::Black => 1,
    };
    let prefix_colors_ok = match branch {
        RbBranch::Red => true,
        RbBranch::Black => {
            is_root_empty_constant_named(export, domains[0], "Color")
                && is_root_empty_constant_named(export, domains[1], "Color")
        }
    };
    let child_colors_ok = match branch {
        RbBranch::Red => {
            is_child_empty_constant_named(export, left_color, "Color", "b")
                && is_child_empty_constant_named(export, right_color, "Color", "b")
        }
        RbBranch::Black => is_bvar(export, left_color, 2) && is_bvar(export, right_color, 3),
    };
    let ih_colors_ok = match branch {
        RbBranch::Red => {
            is_child_empty_constant_named(export, left_ih_color, "Color", "b")
                && is_child_empty_constant_named(export, right_ih_color, "Color", "b")
        }
        RbBranch::Black => is_bvar(export, left_ih_color, 5) && is_bvar(export, right_ih_color, 5),
    };
    let result_index_ok = match branch {
        RbBranch::Red => {
            is_child_empty_constant_named(export, result_color, "Color", "r")
                && is_bvar(export, result_height, 5)
        }
        RbBranch::Black => {
            is_child_empty_constant_named(export, result_color, "Color", "b")
                && is_named_succ_bvar(export, result_height, "N", "succ", 5)
        }
    };

    let mut result_bvars = vec![8 + 3 * branch_index];
    result_bvars.extend((2..=5 + color_prefix as u64).rev());

    prefix_colors_ok
        && is_root_empty_constant_named(export, height, "N")
        && is_bvar(export, left_carrier, 3 + 3 * branch_index)
        && child_colors_ok
        && is_bvar(export, left_height, 0)
        && is_bvar(export, value, 4 + 3 * branch_index)
        && is_bvar(export, right_carrier, 5 + 3 * branch_index)
        && is_bvar(export, right_height, 2)
        && ih_colors_ok
        && is_bvar(export, left_ih_height, 3)
        && is_bvar(export, left_ih_tree, 2)
        && is_bvar(export, right_ih_height, 4)
        && is_bvar(export, right_ih_tree, 1)
        && result_index_ok
        && result_args.len() == 5 + color_prefix
        && are_bvars(export, &result_args, &result_bvars)
}

fn is_derived_rbtree_recursor_type(
    export: &ResolvedExport,
    inductive: NameId,
    level: NameId,
    constructors: [NameId; 3],
    recursor: &Recursor,
) -> bool {
    let Some((domains, result)) = pi_spine(export, recursor.ty, 8) else {
        return false;
    };
    let [
        carrier,
        motive,
        leaf_minor,
        red_minor,
        black_minor,
        color,
        height,
        target,
    ] = domains.as_slice()
    else {
        return false;
    };
    let Some((target_carrier, target_color, target_height)) =
        rbtree_application_parts(export, *target, inductive, level)
    else {
        return false;
    };
    let Some((result_color, result_height, result_tree)) =
        motive_application_parts(export, result, 6)
    else {
        return false;
    };
    let leaf_minor_valid =
        motive_application_parts(export, *leaf_minor, 0).is_some_and(|(color, height, tree)| {
            rbtree_constructor_application_args(export, tree, constructors[0], level).is_some_and(
                |arguments| {
                    is_child_empty_constant_named(export, color, "Color", "b")
                        && is_child_empty_constant_named(export, height, "N", "zero")
                        && matches!(arguments.as_slice(), [argument] if is_bvar(export, *argument, 1))
                },
            )
        });

    is_sort_succ_parameter(export, *carrier, level)
        && is_rbtree_motive_type(export, *motive, inductive, level, recursor.level_params[0])
        && leaf_minor_valid
        && is_rbtree_branch_minor_type(
            export,
            *red_minor,
            inductive,
            constructors[1],
            level,
            RbBranch::Red,
        )
        && is_rbtree_branch_minor_type(
            export,
            *black_minor,
            inductive,
            constructors[2],
            level,
            RbBranch::Black,
        )
        && is_root_empty_constant_named(export, *color, "Color")
        && is_root_empty_constant_named(export, *height, "N")
        && is_bvar(export, target_carrier, 6)
        && is_bvar(export, target_color, 1)
        && is_bvar(export, target_height, 0)
        && is_bvar(export, result_color, 2)
        && is_bvar(export, result_height, 1)
        && is_bvar(export, result_tree, 0)
}

fn peel_rbtree_rule_prefix(
    export: &ResolvedExport,
    expression: ExprId,
    expected: (ExprId, ExprId, ExprId, ExprId, ExprId),
) -> Option<ExprId> {
    let (domains, body) = lam_spine(export, expression, 5)?;
    let [carrier, motive, leaf, red, black] = domains.as_slice() else {
        return None;
    };
    let (carrier_ty, motive_ty, leaf_ty, red_ty, black_ty) = expected;
    (*carrier == carrier_ty
        && *motive == motive_ty
        && *leaf == leaf_ty
        && *red == red_ty
        && *black == black_ty)
        .then_some(body)
}

fn is_derived_rbtree_branch_rule(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
    recursor: &Recursor,
    prefix: (ExprId, ExprId, ExprId, ExprId, ExprId),
    branch: RbBranch,
) -> bool {
    let Some(body) = peel_rbtree_rule_prefix(export, expression, prefix) else {
        return false;
    };
    let color_prefix = match branch {
        RbBranch::Red => 0,
        RbBranch::Black => 2,
    };
    let arity = 4 + color_prefix;
    let Some((domains, result)) = lam_spine(export, body, arity) else {
        return false;
    };
    let height = domains[color_prefix];
    let left = domains[color_prefix + 1];
    let value = domains[color_prefix + 2];
    let right = domains[color_prefix + 3];

    let (
        Some((left_carrier, left_color, left_height)),
        Some((right_carrier, right_color, right_height)),
    ) = (
        rbtree_application_parts(export, left, inductive, level),
        rbtree_application_parts(export, right, inductive, level),
    )
    else {
        return false;
    };

    let (head, arguments) = application_spine(export, result);
    if !is_bvar(export, head, 5 + (color_prefix / 2) as u64) || arguments.len() != arity + 2 {
        return false;
    }
    let Some(left_call) = rbtree_recursor_application_args(
        export,
        arguments[arity],
        recursor.name,
        recursor.level_params[0],
        level,
    ) else {
        return false;
    };
    let Some(right_call) = rbtree_recursor_application_args(
        export,
        arguments[arity + 1],
        recursor.name,
        recursor.level_params[0],
        level,
    ) else {
        return false;
    };

    let prefix_bvars = (0..arity as u64).rev().collect::<Vec<_>>();
    let recursive_prefix = (0..5)
        .map(|offset| 8 + color_prefix as u64 - offset)
        .collect::<Vec<_>>();

    let colors_ok = match branch {
        RbBranch::Red => true,
        RbBranch::Black => {
            is_root_empty_constant_named(export, domains[0], "Color")
                && is_root_empty_constant_named(export, domains[1], "Color")
        }
    };
    let child_colors_ok = match branch {
        RbBranch::Red => {
            is_child_empty_constant_named(export, left_color, "Color", "b")
                && is_child_empty_constant_named(export, right_color, "Color", "b")
        }
        RbBranch::Black => is_bvar(export, left_color, 2) && is_bvar(export, right_color, 3),
    };
    let call_colors_ok = match branch {
        RbBranch::Red => {
            is_child_empty_constant_named(export, left_call[5], "Color", "b")
                && is_child_empty_constant_named(export, right_call[5], "Color", "b")
        }
        RbBranch::Black => is_bvar(export, left_call[5], 5) && is_bvar(export, right_call[5], 4),
    };

    colors_ok
        && is_root_empty_constant_named(export, height, "N")
        && is_bvar(export, left_carrier, 5 + color_prefix as u64)
        && child_colors_ok
        && is_bvar(export, left_height, 0)
        && is_bvar(export, value, 6 + color_prefix as u64)
        && is_bvar(export, right_carrier, 7 + color_prefix as u64)
        && is_bvar(export, right_height, 2)
        && are_bvars(export, &arguments[..arity], &prefix_bvars)
        && left_call.len() == 8
        && are_bvars(export, &left_call[..5], &recursive_prefix)
        && call_colors_ok
        && is_bvar(export, left_call[6], 3)
        && is_bvar(export, left_call[7], 2)
        && right_call.len() == 8
        && are_bvars(export, &right_call[..5], &recursive_prefix)
        && is_bvar(export, right_call[6], 3)
        && is_bvar(export, right_call[7], 0)
}

fn are_derived_rbtree_rules(
    export: &ResolvedExport,
    inductive: NameId,
    level: NameId,
    constructors: [NameId; 3],
    recursor: &Recursor,
) -> bool {
    let [leaf_rule, red_rule, black_rule] = recursor.rules.as_slice() else {
        return false;
    };
    let Some((prefix_domains, _)) = pi_spine(export, recursor.ty, 5) else {
        return false;
    };
    let [carrier, motive, leaf, red, black] = prefix_domains.as_slice() else {
        return false;
    };
    let prefix = (*carrier, *motive, *leaf, *red, *black);
    leaf_rule.constructor == constructors[0]
        && leaf_rule.num_fields == 0
        && red_rule.constructor == constructors[1]
        && red_rule.num_fields == 4
        && black_rule.constructor == constructors[2]
        && black_rule.num_fields == 6
        && peel_rbtree_rule_prefix(export, leaf_rule.rhs, prefix)
            .is_some_and(|result| is_bvar(export, result, 2))
        && is_derived_rbtree_branch_rule(
            export,
            red_rule.rhs,
            inductive,
            level,
            recursor,
            prefix,
            RbBranch::Red,
        )
        && is_derived_rbtree_branch_rule(
            export,
            black_rule.rhs,
            inductive,
            level,
            recursor,
            prefix,
            RbBranch::Black,
        )
}

/// G10-001: a closed, safe, two-constructor enum. This admits no constructor
/// fields and therefore needs neither positivity search nor recursive
/// occurrences. Exported recursor equations are checked against a derived
/// de Bruijn shape but are not installed as runtime iota rules.
#[derive(Clone, Copy)]
enum BinaryEnumSortLaw {
    Type,
    Prop,
}

fn check_binary_enum(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let [inductive] = block.types.as_slice() else {
        return Err(Verdict::Unknown);
    };

    // Existing Type-level authority remains name-sealed to Bool/Color. G25
    // adds one independently earned Prop-level family, BoolProp, while sharing
    // the internal binary-enum derivation below.
    let sort_law = if name_is_root_str(export, inductive.name, "BoolProp") {
        if !is_prop_sort(export, inductive.ty) {
            return Err(Verdict::Reject);
        }
        BinaryEnumSortLaw::Prop
    } else if name_is_root_str(export, inductive.name, "Bool")
        || name_is_root_str(export, inductive.name, "Color")
    {
        if !matches!(
            export.exprs.get(inductive.ty),
            Some(Expr::Sort(level))
                if matches!(export.levels.get(*level), Some(Level::Succ(LevelId(0))))
        ) {
            return Err(Verdict::Unknown);
        }
        BinaryEnumSortLaw::Type
    } else {
        return Err(Verdict::Unknown);
    };

    if inductive.num_params != 0 || inductive.num_indices != 0 || inductive.num_nested != 0 {
        return Err(Verdict::Unknown);
    }
    let constructor_names = block
        .constructors
        .iter()
        .map(|constructor| constructor.name)
        .collect::<Vec<_>>();
    if inductive.all != [inductive.name]
        || inductive.constructors != constructor_names
        || inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || !inductive.level_params.is_empty()
    {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote(
        export,
        derived_type(inductive.name, inductive.ty),
        limits.judgment_steps,
        delta_policy,
    )?;

    for (index, constructor) in block.constructors.iter().enumerate() {
        if constructor.index != index as u64
            || constructor.inductive != inductive.name
            || constructor.is_unsafe
            || !constructor.level_params.is_empty()
            || constructor.num_fields != 0
            || constructor.num_params != 0
            || !is_empty_constant(export, constructor.ty, inductive.name)
        {
            return Err(Verdict::Reject);
        }
        derivation.promote(
            export,
            derived_constructor(constructor),
            limits.judgment_steps,
            delta_policy,
        )?;
    }

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    let levels_ok = match sort_law {
        BinaryEnumSortLaw::Type => recursor.level_params.len() == 1,
        BinaryEnumSortLaw::Prop => recursor.level_params.is_empty(),
    };
    if !recursor_metadata_admissible(
        export,
        inductive,
        &block.constructors,
        recursor,
        false,
        !recursor.is_unsafe && levels_ok,
    ) || !binary_enum_recursor_obligations(
        export,
        inductive.name,
        &constructor_names,
        recursor,
        sort_law,
    ) {
        return Err(Verdict::Reject);
    }
    derivation.promote(
        export,
        derived_recursor(recursor),
        limits.judgment_steps,
        delta_policy,
    )?;
    Ok(derivation.finish())
}

fn binary_enum_motive_sort_ok(
    export: &ResolvedExport,
    expression: ExprId,
    recursor: &Recursor,
    sort_law: BinaryEnumSortLaw,
) -> bool {
    match sort_law {
        BinaryEnumSortLaw::Prop => is_prop_sort(export, expression),
        BinaryEnumSortLaw::Type => recursor
            .level_params
            .first()
            .is_some_and(|motive_level| is_sort_parameter(export, expression, *motive_level)),
    }
}

fn binary_enum_recursor_obligations(
    export: &ResolvedExport,
    inductive: NameId,
    constructors: &[NameId],
    recursor: &Recursor,
    sort_law: BinaryEnumSortLaw,
) -> bool {
    let [first, second] = constructors else {
        return false;
    };

    let type_ok = pi_spine(export, recursor.ty, 4).is_some_and(|(domains, result)| {
        let [motive, first_minor, second_minor, target] = domains.as_slice() else {
            return false;
        };
        matches!(
            export.exprs.get(*motive),
            Some(Expr::Pi {
                domain: motive_arg,
                body: motive_sort,
            }) if is_empty_constant(export, *motive_arg, inductive)
                && binary_enum_motive_sort_ok(export, *motive_sort, recursor, sort_law)
        ) && is_bvar_applied_to_constant(export, *first_minor, 0, *first)
            && is_bvar_applied_to_constant(export, *second_minor, 1, *second)
            && is_empty_constant(export, *target, inductive)
            && is_bvar_application(export, result, 3, 0)
    });

    let rules_ok = recursor.rules.iter().enumerate().all(|(index, rule)| {
        lam_spine(export, rule.rhs, 3).is_some_and(|(domains, result)| {
            let [motive, first_minor, second_minor] = domains.as_slice() else {
                return false;
            };
            let motive_ok = matches!(
                export.exprs.get(*motive),
                Some(Expr::Pi {
                    domain: motive_arg,
                    body: motive_sort,
                }) if is_empty_constant(export, *motive_arg, inductive)
                    && match sort_law {
                        BinaryEnumSortLaw::Prop => is_prop_sort(export, *motive_sort),
                        // Preserve the previously qualified Type-enum rule
                        // boundary: the recursor type fixes its universe.
                        BinaryEnumSortLaw::Type => true,
                    }
            );
            motive_ok
                && is_bvar_applied_to_constant(export, *first_minor, 0, *first)
                && is_bvar_applied_to_constant(export, *second_minor, 1, *second)
                && is_bvar(export, result, 1 - index as u64)
        })
    });

    type_ok && rules_ok
}

fn is_bvar_applied_to_constant(
    export: &ResolvedExport,
    expression: ExprId,
    variable: u64,
    constant: NameId,
) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::App { fun, arg })
            if matches!(export.exprs.get(*fun), Some(Expr::BVar(index)) if *index == variable)
                && is_empty_constant(export, *arg, constant)
    )
}

/// G15-001's closed internal quotient, extended by G16-001's independently
/// earned nullary law. External recognition remains name-sealed: adding this
/// variant cannot authorize any unrelated fourth product family.
fn recursor_metadata_admissible(
    export: &ResolvedExport,
    inductive: &crate::syntax::InductiveType,
    constructors: &[Constructor],
    recursor: &Recursor,
    expected_k: bool,
    levels_ok: bool,
) -> bool {
    recursor.all == [inductive.name]
        && recursor.k == expected_k
        && levels_ok
        && !has_duplicate_parameter(&recursor.level_params)
        && recursor.num_params == inductive.num_params
        && recursor.num_indices == inductive.num_indices
        && recursor.num_motives == 1
        && recursor.num_minors == constructors.len() as u64
        && recursor.rules.len() == constructors.len()
        && recursor
            .rules
            .iter()
            .zip(constructors)
            .all(|(rule, constructor)| {
                rule.constructor == constructor.name && rule.num_fields == constructor.num_fields
            })
        && name_is_child_str(export, recursor.name, inductive.name, "rec")
}

#[derive(Clone, Copy)]
enum BinaryProductSortLaw {
    And,
    Prod { first: NameId, second: NameId },
    PProd { first: NameId, second: NameId },
    PUnit { level: NameId },
    Eq { level: NameId },
}

impl BinaryProductSortLaw {
    fn parameter_sort(self, export: &ResolvedExport, expression: ExprId, first: bool) -> bool {
        match self {
            Self::PUnit { .. } | Self::Eq { .. } => false,
            Self::And => is_prop_sort(export, expression),
            Self::Prod {
                first: first_level,
                second: second_level,
            } => is_sort_succ_parameter(
                export,
                expression,
                if first { first_level } else { second_level },
            ),
            Self::PProd {
                first: first_level,
                second: second_level,
            } => is_sort_parameter(
                export,
                expression,
                if first { first_level } else { second_level },
            ),
        }
    }

    fn result_sort(self, export: &ResolvedExport, expression: ExprId) -> bool {
        match self {
            Self::PUnit { level } => is_sort_parameter(export, expression, level),
            Self::Eq { .. } | Self::And => is_prop_sort(export, expression),
            Self::Prod { first, second } => {
                let Some(Expr::Sort(level)) = export.exprs.get(expression) else {
                    return false;
                };
                let Some(Level::Max(left, right)) = export.levels.get(*level) else {
                    return false;
                };
                level_is_succ_parameter(export, *left, first)
                    && level_is_succ_parameter(export, *right, second)
            }
            Self::PProd { first, second } => {
                let Some(Expr::Sort(level)) = export.exprs.get(expression) else {
                    return false;
                };
                let Some(Level::Max(left, right)) = export.levels.get(*level) else {
                    return false;
                };
                let Some(Level::Max(one, first_level)) = export.levels.get(*left) else {
                    return false;
                };
                matches!(
                    export.levels.get(*one),
                    Some(Level::Succ(inner))
                        if matches!(export.levels.get(*inner), Some(Level::Zero))
                ) && matches!(
                    export.levels.get(*first_level),
                    Some(Level::Param(name)) if *name == first
                ) && matches!(
                    export.levels.get(*right),
                    Some(Level::Param(name)) if *name == second
                )
            }
        }
    }

    fn constant(self, export: &ResolvedExport, expression: ExprId, name: NameId) -> bool {
        match self {
            Self::PUnit { level } | Self::Eq { level } => {
                is_unary_polymorphic_constant(export, expression, name, level)
            }
            Self::And => is_empty_constant(export, expression, name),
            Self::Prod { first, second } | Self::PProd { first, second } => {
                is_polymorphic_constant(export, expression, name, first, second)
            }
        }
    }

    fn declaration_levels(
        self,
        inductive: &crate::syntax::InductiveType,
        constructor: &Constructor,
    ) -> bool {
        match self {
            Self::PUnit { level } | Self::Eq { level } => {
                inductive.level_params == [level] && constructor.level_params == [level]
            }
            Self::And => inductive.level_params.is_empty() && constructor.level_params.is_empty(),
            Self::Prod { first, second } | Self::PProd { first, second } => {
                first != second
                    && inductive.level_params == [first, second]
                    && constructor.level_params == inductive.level_params
            }
        }
    }

    fn recursor_levels(self, inductive_level_params: &[NameId], recursor: &Recursor) -> bool {
        match self {
            Self::PUnit { .. } | Self::Eq { .. } => {
                recursor.level_params.len() == 2
                    && recursor.level_params[1] == inductive_level_params[0]
            }
            Self::And => recursor.level_params.len() == 1,
            Self::Prod { .. } | Self::PProd { .. } => {
                recursor.level_params.len() == 3
                    && &recursor.level_params[1..] == inductive_level_params
            }
        }
    }

    fn num_params(self) -> u64 {
        match self {
            Self::PUnit { .. } => 0,
            Self::Eq { .. } | Self::And | Self::Prod { .. } | Self::PProd { .. } => 2,
        }
    }

    fn num_fields(self) -> u64 {
        match self {
            Self::PUnit { .. } | Self::Eq { .. } => 0,
            Self::And | Self::Prod { .. } | Self::PProd { .. } => 2,
        }
    }

    fn recursor_uses_rule_k(self) -> bool {
        matches!(self, Self::Eq { .. })
    }

    fn validates_recursor_metadata(
        self,
        export: &ResolvedExport,
        inductive: &crate::syntax::InductiveType,
        constructor: &Constructor,
        recursor: &Recursor,
    ) -> bool {
        recursor_metadata_admissible(
            export,
            inductive,
            std::slice::from_ref(constructor),
            recursor,
            self.recursor_uses_rule_k(),
            self.recursor_levels(&inductive.level_params, recursor),
        )
    }

    fn validates_type(self, export: &ResolvedExport, expression: ExprId) -> bool {
        match self {
            Self::PUnit { .. } => self.result_sort(export, expression),
            Self::Eq { level } => {
                let Some((domains, result)) = pi_spine(export, expression, 3) else {
                    return false;
                };
                let [carrier, parameter, index] = domains.as_slice() else {
                    return false;
                };
                is_sort_parameter(export, *carrier, level)
                    && is_bvar(export, *parameter, 0)
                    && is_bvar(export, *index, 1)
                    && is_prop_sort(export, result)
            }
            Self::And | Self::Prod { .. } | Self::PProd { .. } => {
                is_exact_binary_product_parameter_telescope(export, expression, self)
            }
        }
    }

    fn validates_constructor(
        self,
        export: &ResolvedExport,
        expression: ExprId,
        inductive: NameId,
    ) -> bool {
        match self {
            Self::PUnit { .. } => self.constant(export, expression, inductive),
            Self::Eq { level } => {
                let Some((domains, result)) = pi_spine(export, expression, 2) else {
                    return false;
                };
                let [carrier, parameter] = domains.as_slice() else {
                    return false;
                };
                is_sort_parameter(export, *carrier, level)
                    && is_bvar(export, *parameter, 0)
                    && is_eq_application(export, result, inductive, self, 1, 0, 0)
            }
            Self::And | Self::Prod { .. } | Self::PProd { .. } => {
                is_derived_binary_product_constructor_type(export, expression, inductive, self)
            }
        }
    }
}

struct ExactBinaryProductDerivation<'a> {
    inductive: &'a crate::syntax::InductiveType,
    constructor: &'a Constructor,
    recursor: &'a Recursor,
    constructor_suffix: &'static str,
    law: BinaryProductSortLaw,
}

impl ExactBinaryProductDerivation<'_> {
    fn validate_and_promote(
        &self,
        export: &ResolvedExport,
        environment: &Environment,
        limits: Limits,
        delta_policy: DeltaPolicy,
    ) -> Result<Environment, Verdict> {
        if !self
            .law
            .declaration_levels(self.inductive, self.constructor)
            || !self.law.validates_type(export, self.inductive.ty)
            || self.inductive.all != [self.inductive.name]
            || self.inductive.constructors != [self.constructor.name]
            || self.constructor.index != 0
            || self.constructor.inductive != self.inductive.name
            || self.constructor.num_fields != self.law.num_fields()
            || self.constructor.num_params != self.law.num_params()
            || !name_is_child_str(
                export,
                self.constructor.name,
                self.inductive.name,
                self.constructor_suffix,
            )
            || !self
                .law
                .validates_constructor(export, self.constructor.ty, self.inductive.name)
        {
            return Err(Verdict::Reject);
        }

        let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
        let derived_type = if self.inductive.level_params.is_empty() {
            derived_type(self.inductive.name, self.inductive.ty)
        } else {
            derived_polymorphic_type(
                self.inductive.name,
                &self.inductive.level_params,
                self.inductive.ty,
            )
        };
        derivation.promote_all(
            export,
            [derived_type, derived_constructor(self.constructor)],
            limits.judgment_steps,
            delta_policy,
        )?;

        let valid_recursor = match self.law {
            BinaryProductSortLaw::PUnit { .. } => {
                let type_valid =
                    pi_spine(export, self.recursor.ty, 3).is_some_and(|(domains, result)| {
                        matches!(domains.as_slice(), [motive, minor, target]
                            if is_punit_motive_type(
                                export,
                                *motive,
                                self.inductive.name,
                                self.recursor.level_params[0],
                                self.law,
                            )
                                && is_punit_minor_type(
                                    export,
                                    *minor,
                                    self.constructor.name,
                                    self.law,
                                )
                                && self.law.constant(export, *target, self.inductive.name)
                                && is_bvar_application(export, result, 2, 0))
                    });
                let rule_valid = matches!(self.recursor.rules.as_slice(), [rule]
                if lam_spine(export, rule.rhs, 2).is_some_and(|(domains, result)| {
                    matches!(domains.as_slice(), [motive, minor]
                        if is_punit_motive_type(
                            export,
                            *motive,
                            self.inductive.name,
                            self.recursor.level_params[0],
                            self.law,
                        )
                            && is_punit_minor_type(
                                export,
                                *minor,
                                self.constructor.name,
                                self.law,
                            )
                            && is_bvar(export, result, 0))
                }));
                self.law.validates_recursor_metadata(
                    export,
                    self.inductive,
                    self.constructor,
                    self.recursor,
                ) && type_valid
                    && rule_valid
            }
            BinaryProductSortLaw::Eq { level } => {
                let type_valid =
                    pi_spine(export, self.recursor.ty, 6).is_some_and(|(domains, result)| {
                        matches!(domains.as_slice(), [carrier, parameter, motive, minor, index, proof]
                            if is_sort_parameter(export, *carrier, level)
                                && is_bvar(export, *parameter, 0)
                                && is_eq_motive_type(
                                    export,
                                    *motive,
                                    self.inductive.name,
                                    self.recursor.level_params[0],
                                    self.law,
                                )
                                && is_eq_minor_type(
                                    export,
                                    *minor,
                                    self.constructor.name,
                                    self.law,
                                )
                                && is_bvar(export, *index, 3)
                                && is_eq_application(
                                    export,
                                    *proof,
                                    self.inductive.name,
                                    self.law,
                                    4,
                                    3,
                                    0,
                                )
                                && is_binary_bvar_application(export, result, 3, 1, 0))
                    });
                let rule_valid = matches!(self.recursor.rules.as_slice(), [rule]
                if lam_spine(export, rule.rhs, 4).is_some_and(|(domains, result)| {
                    matches!(domains.as_slice(), [carrier, parameter, motive, minor]
                        if is_sort_parameter(export, *carrier, level)
                            && is_bvar(export, *parameter, 0)
                            && is_eq_motive_type(
                                export,
                                *motive,
                                self.inductive.name,
                                self.recursor.level_params[0],
                                self.law,
                            )
                            && is_eq_minor_type(
                                export,
                                *minor,
                                self.constructor.name,
                                self.law,
                            )
                            && is_bvar(export, result, 0))
                }));
                self.law.validates_recursor_metadata(
                    export,
                    self.inductive,
                    self.constructor,
                    self.recursor,
                ) && type_valid
                    && rule_valid
            }
            BinaryProductSortLaw::And
            | BinaryProductSortLaw::Prod { .. }
            | BinaryProductSortLaw::PProd { .. } => {
                self.law.validates_recursor_metadata(
                    export,
                    self.inductive,
                    self.constructor,
                    self.recursor,
                ) && is_derived_binary_product_recursor_type(
                    export,
                    self.inductive.name,
                    self.constructor.name,
                    self.recursor,
                    self.law,
                ) && is_derived_binary_product_rule(
                    export,
                    self.inductive.name,
                    self.constructor.name,
                    self.recursor,
                    self.law,
                )
            }
        };
        if !valid_recursor {
            return Err(Verdict::Reject);
        }
        derivation.promote(
            export,
            derived_recursor(self.recursor),
            limits.judgment_steps,
            delta_policy,
        )?;
        Ok(derivation.finish())
    }
}

/// G12-001's complete external frontier: the built-in-shaped `And` declaration
/// with two Prop parameters and one field for each parameter. This is a named
/// classifier, not a general parameterized-inductive rule. The shared
/// promotion transaction is reused unchanged and installs no computation.
#[derive(Clone, Copy)]
enum BinaryProductFamily {
    And,
    Prod,
    PProd,
}

fn check_exact_binary_product_family(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
    family: BinaryProductFamily,
) -> Result<Environment, Verdict> {
    let [inductive] = block.types.as_slice() else {
        return Err(Verdict::Unknown);
    };
    let [constructor] = block.constructors.as_slice() else {
        return Err(Verdict::Unknown);
    };

    if inductive.num_params != 2
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || constructor.is_unsafe
    {
        return Err(Verdict::Unknown);
    }

    // And's already-qualified envelope treats any universe-polymorphic
    // neighbor as unsupported before recursor validation.
    if matches!(family, BinaryProductFamily::And)
        && (!inductive.level_params.is_empty() || !constructor.level_params.is_empty())
    {
        return Err(Verdict::Unknown);
    }

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if recursor.is_unsafe {
        return Err(Verdict::Unknown);
    }

    let (constructor_suffix, law) = match family {
        BinaryProductFamily::And => ("intro", BinaryProductSortLaw::And),
        BinaryProductFamily::Prod => {
            if has_dependent_parameter_neighbor(export, inductive.ty) {
                return Err(Verdict::Unknown);
            }
            let [first, second] = inductive.level_params.as_slice() else {
                return Err(Verdict::Reject);
            };
            (
                "mk",
                BinaryProductSortLaw::Prod {
                    first: *first,
                    second: *second,
                },
            )
        }
        BinaryProductFamily::PProd => {
            if has_dependent_parameter_neighbor(export, inductive.ty)
                || pprod_has_dependent_field_neighbor(export, constructor.ty)
            {
                return Err(Verdict::Unknown);
            }
            let [first, second] = inductive.level_params.as_slice() else {
                return Err(Verdict::Reject);
            };
            (
                "mk",
                BinaryProductSortLaw::PProd {
                    first: *first,
                    second: *second,
                },
            )
        }
    };

    ExactBinaryProductDerivation {
        inductive,
        constructor,
        recursor,
        constructor_suffix,
        law,
    }
    .validate_and_promote(export, environment, limits, delta_policy)
}

fn is_prop_sort(export: &ResolvedExport, expression: ExprId) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::Sort(level)) if matches!(export.levels.get(*level), Some(Level::Zero))
    )
}

fn is_bvar(export: &ResolvedExport, expression: ExprId, expected: u64) -> bool {
    matches!(export.exprs.get(expression), Some(Expr::BVar(index)) if *index == expected)
}

fn are_bvars(export: &ResolvedExport, expressions: &[ExprId], expected: &[u64]) -> bool {
    expressions.len() == expected.len()
        && expressions
            .iter()
            .zip(expected)
            .all(|(expression, expected)| is_bvar(export, *expression, *expected))
}

fn is_bvar_application(
    export: &ResolvedExport,
    expression: ExprId,
    function: u64,
    argument: u64,
) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::App { fun, arg })
            if is_bvar(export, *fun, function) && is_bvar(export, *arg, argument)
    )
}

fn is_binary_bvar_application(
    export: &ResolvedExport,
    expression: ExprId,
    function: u64,
    first: u64,
    second: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 2
        && is_bvar(export, head, function)
        && are_bvars(export, &arguments, &[first, second])
}

fn is_exact_binary_product_parameter_telescope(
    export: &ResolvedExport,
    expression: ExprId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [first, second] = domains.as_slice() else {
        return false;
    };
    law.parameter_sort(export, *first, true)
        && law.parameter_sort(export, *second, false)
        && law.result_sort(export, result)
}

fn is_derived_binary_product_constructor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 4) else {
        return false;
    };
    let [first, second, left, right] = domains.as_slice() else {
        return false;
    };
    law.parameter_sort(export, *first, true)
        && law.parameter_sort(export, *second, false)
        && is_bvar(export, *left, 1)
        && is_bvar(export, *right, 1)
        && is_binary_product_constant_application(export, result, inductive, 3, 2, law)
}

fn is_derived_binary_product_recursor_type(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    recursor: &Recursor,
    law: BinaryProductSortLaw,
) -> bool {
    let Some((domains, result)) = pi_spine(export, recursor.ty, 5) else {
        return false;
    };
    let [first, second, motive, minor, target] = domains.as_slice() else {
        return false;
    };
    law.parameter_sort(export, *first, true)
        && law.parameter_sort(export, *second, false)
        && is_binary_product_motive_type(export, *motive, inductive, recursor.level_params[0], law)
        && is_binary_product_minor_type(export, *minor, constructor, law)
        && is_binary_product_constant_application(export, *target, inductive, 3, 2, law)
        && is_bvar_application(export, result, 2, 0)
}

fn is_binary_product_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    motive_level: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 1) else {
        return false;
    };
    let [argument] = domains.as_slice() else {
        return false;
    };
    is_binary_product_constant_application(export, *argument, inductive, 1, 0, law)
        && is_sort_parameter(export, result, motive_level)
}

fn is_binary_product_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [left, right] = domains.as_slice() else {
        return false;
    };
    let Some(Expr::App {
        fun: motive,
        arg: constructed,
    }) = export.exprs.get(result)
    else {
        return false;
    };
    is_bvar(export, *left, 2)
        && is_bvar(export, *right, 2)
        && is_bvar(export, *motive, 2)
        && is_binary_product_constructor_application(export, *constructed, constructor, law)
}

fn is_derived_binary_product_rule(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    recursor: &Recursor,
    law: BinaryProductSortLaw,
) -> bool {
    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    let Some((domains, result)) = lam_spine(export, rule.rhs, 6) else {
        return false;
    };
    let [first, second, motive, minor, left, right] = domains.as_slice() else {
        return false;
    };
    law.parameter_sort(export, *first, true)
        && law.parameter_sort(export, *second, false)
        && is_binary_product_motive_type(export, *motive, inductive, recursor.level_params[0], law)
        && is_binary_product_minor_type(export, *minor, constructor, law)
        && is_bvar(export, *left, 3)
        && is_bvar(export, *right, 3)
        && is_binary_bvar_application(export, result, 2, 1, 0)
}

fn is_binary_product_constant_application(
    export: &ResolvedExport,
    expression: ExprId,
    constant: NameId,
    first: u64,
    second: u64,
    law: BinaryProductSortLaw,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 2
        && law.constant(export, head, constant)
        && are_bvars(export, &arguments, &[first, second])
}

fn is_binary_product_constructor_application(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 4
        && law.constant(export, head, constructor)
        && are_bvars(export, &arguments, &[4, 3, 1, 0])
}

fn is_unary_polymorphic_constant(
    export: &ResolvedExport,
    expression: ExprId,
    constant: NameId,
    level_parameter: NameId,
) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::Const { name, levels })
            if *name == constant
                && matches!(levels.as_slice(), [level]
                    if matches!(export.levels.get(*level), Some(Level::Param(name)) if *name == level_parameter))
    )
}

fn is_punit_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    motive_level: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 1) else {
        return false;
    };
    let [argument] = domains.as_slice() else {
        return false;
    };
    law.constant(export, *argument, inductive) && is_sort_parameter(export, result, motive_level)
}

fn is_punit_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::App { fun, arg })
            if is_bvar(export, *fun, 0) && law.constant(export, *arg, constructor)
    )
}

fn is_eq_application(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    law: BinaryProductSortLaw,
    carrier: u64,
    parameter: u64,
    index: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 3
        && law.constant(export, head, inductive)
        && are_bvars(export, &arguments, &[carrier, parameter, index])
}

fn is_eq_constructor_application(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    law: BinaryProductSortLaw,
    carrier: u64,
    parameter: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 2
        && law.constant(export, head, constructor)
        && are_bvars(export, &arguments, &[carrier, parameter])
}

fn is_eq_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    motive_level: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [index, proof] = domains.as_slice() else {
        return false;
    };
    is_bvar(export, *index, 1)
        && is_eq_application(export, *proof, inductive, law, 2, 1, 0)
        && is_sort_parameter(export, result, motive_level)
}

fn is_eq_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some(Expr::App {
        fun: motive_at_parameter,
        arg: refl,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    is_bvar_application(export, *motive_at_parameter, 0, 1)
        && is_eq_constructor_application(export, *refl, constructor, law, 2, 1)
}

fn has_dependent_parameter_neighbor(export: &ResolvedExport, expression: ExprId) -> bool {
    let Some(Expr::Pi { body, .. }) = export.exprs.get(expression) else {
        return false;
    };
    matches!(
        export.exprs.get(*body),
        Some(Expr::Pi { domain, .. }) if matches!(export.exprs.get(*domain), Some(Expr::Pi { .. }))
    )
}

fn is_sort_parameter(export: &ResolvedExport, expression: ExprId, parameter: NameId) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::Sort(level)) if matches!(export.levels.get(*level), Some(Level::Param(name)) if *name == parameter)
    )
}

fn is_sort_succ_parameter(export: &ResolvedExport, expression: ExprId, parameter: NameId) -> bool {
    let Some(Expr::Sort(level)) = export.exprs.get(expression) else {
        return false;
    };
    level_is_succ_parameter(export, *level, parameter)
}

fn level_is_succ_parameter(export: &ResolvedExport, level: LevelId, parameter: NameId) -> bool {
    matches!(
        export.levels.get(level),
        Some(Level::Succ(inner)) if matches!(export.levels.get(*inner), Some(Level::Param(name)) if *name == parameter)
    )
}

fn is_polymorphic_constant(
    export: &ResolvedExport,
    expression: ExprId,
    constant: NameId,
    first_level: NameId,
    second_level: NameId,
) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::Const { name, levels })
            if *name == constant
                && matches!(levels.as_slice(), [first, second]
                    if matches!(export.levels.get(*first), Some(Level::Param(name)) if *name == first_level)
                        && matches!(export.levels.get(*second), Some(Level::Param(name)) if *name == second_level))
    )
}

/// G14-001's name-specific frontier. G15 shares only its already-qualified
/// derivation skeleton; this envelope and its Sort-level law remain separate.
fn pprod_has_dependent_field_neighbor(export: &ResolvedExport, expression: ExprId) -> bool {
    let Some((domains, _)) = pi_spine(export, expression, 4) else {
        return false;
    };
    domains[2..].iter().any(|domain| {
        matches!(
            export.exprs.get(*domain),
            Some(Expr::Pi { .. } | Expr::App { .. })
        )
    })
}

/// G11-001's exact `TwoBool` promotion boundary. This deliberately names the
/// fixture family: a generic structure/positivity rule has not yet been
/// earned. The exported rule is validated but no iota, projection, or eta
/// operation is installed.
fn check_twobool_structure(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let [inductive] = block.types.as_slice() else {
        return Err(Verdict::Unknown);
    };
    if inductive.num_params != 0
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || !inductive.level_params.is_empty()
        || !name_is_root_str(export, inductive.name, "TwoBool")
        || !matches!(
            export.exprs.get(inductive.ty),
            Some(Expr::Sort(level))
                if matches!(export.levels.get(*level), Some(Level::Succ(LevelId(0))))
        )
    {
        return Err(Verdict::Unknown);
    }
    let [constructor] = block.constructors.as_slice() else {
        unreachable!("dispatched by constructor count");
    };
    if constructor.is_unsafe || !constructor.level_params.is_empty() {
        return Err(Verdict::Unknown);
    }
    if inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || constructor.index != 0
        || constructor.inductive != inductive.name
        || constructor.num_fields != 2
        || constructor.num_params != 0
        || !name_is_child_str(export, constructor.name, inductive.name, "mk")
    {
        return Err(Verdict::Reject);
    }
    let Some(bool_name) = first_constructor_domain_constant(export, constructor.ty) else {
        return Err(Verdict::Reject);
    };
    if !name_is_root_str(export, bool_name, "Bool")
        || !is_twobool_constructor_type(export, constructor.ty, bool_name, inductive.name)
    {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_type(inductive.name, inductive.ty),
            derived_constructor(constructor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if !recursor_metadata_admissible(
        export,
        inductive,
        &block.constructors,
        recursor,
        false,
        !recursor.is_unsafe && recursor.level_params.len() == 1,
    ) || !twobool_recursor_obligations(
        export,
        inductive.name,
        constructor.name,
        bool_name,
        recursor,
    ) {
        return Err(Verdict::Reject);
    }
    derivation.promote(
        export,
        derived_recursor(recursor),
        limits.judgment_steps,
        delta_policy,
    )?;
    Ok(derivation.finish())
}

fn is_twobool_constructor_type(
    export: &ResolvedExport,
    expression: ExprId,
    field_type: NameId,
    inductive: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [first, second] = domains.as_slice() else {
        return false;
    };
    is_empty_constant(export, *first, field_type)
        && is_empty_constant(export, *second, field_type)
        && is_empty_constant(export, result, inductive)
}

fn twobool_recursor_obligations(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    field_type: NameId,
    recursor: &Recursor,
) -> bool {
    let type_ok = pi_spine(export, recursor.ty, 3).is_some_and(|(domains, result)| {
        matches!(domains.as_slice(), [motive, minor, target]
            if matches!(
                export.exprs.get(*motive),
                Some(Expr::Pi {
                    domain: motive_arg,
                    body: motive_sort,
                }) if is_empty_constant(export, *motive_arg, inductive)
                    && matches!(
                        export.exprs.get(*motive_sort),
                        Some(Expr::Sort(level)) if matches!(
                            export.levels.get(*level),
                            Some(Level::Param(name)) if name == &recursor.level_params[0]
                        )
                    )
            )
                && is_twobool_minor_type(export, *minor, constructor, field_type)
                && is_empty_constant(export, *target, inductive)
                && is_bvar_application(export, result, 2, 0))
    });

    let rule_ok = matches!(recursor.rules.as_slice(), [rule]
    if lam_spine(export, rule.rhs, 4).is_some_and(|(domains, result)| {
        matches!(domains.as_slice(), [motive, minor, first, second]
            if matches!(
                export.exprs.get(*motive),
                Some(Expr::Pi { domain: motive_arg, .. })
                    if is_empty_constant(export, *motive_arg, inductive)
            )
                && is_twobool_minor_type(export, *minor, constructor, field_type)
                && is_empty_constant(export, *first, field_type)
                && is_empty_constant(export, *second, field_type)
                && is_binary_bvar_application(export, result, 2, 1, 0))
    }));

    type_ok && rule_ok
}

fn is_twobool_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    field_type: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [first, second] = domains.as_slice() else {
        return false;
    };
    let Some(Expr::App {
        fun: motive,
        arg: constructed,
    }) = export.exprs.get(result)
    else {
        return false;
    };
    is_empty_constant(export, *first, field_type)
        && is_empty_constant(export, *second, field_type)
        && is_bvar(export, *motive, 2)
        && is_constructor_applied_to_two_bvars(export, *constructed, constructor, 1, 0)
}

fn is_constructor_applied_to_two_bvars(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    first: u64,
    second: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 2
        && is_empty_constant(export, head, constructor)
        && are_bvars(export, &arguments, &[first, second])
}

fn name_is_root_str(export: &ResolvedExport, name: NameId, value: &str) -> bool {
    matches!(export.names.get(name), Some(Name::Str { prefix: NameId(0), value: actual }) if actual == value)
}

fn name_is_child_str(export: &ResolvedExport, name: NameId, prefix: NameId, value: &str) -> bool {
    matches!(export.names.get(name), Some(Name::Str { prefix: actual_prefix, value: actual }) if *actual_prefix == prefix && actual == value)
}

fn first_constructor_domain_constant(
    export: &ResolvedExport,
    expression: ExprId,
) -> Option<NameId> {
    let (domains, _) = pi_spine(export, expression, 1)?;
    let Expr::Const { name, levels } = export.exprs.get(domains[0])? else {
        return None;
    };
    levels.is_empty().then_some(*name)
}

fn derived_type(name: NameId, ty: ExprId) -> DerivedSignature {
    DerivedSignature {
        kind: OpaqueInductiveKind::Type,
        name,
        level_params: Vec::new(),
        ty,
    }
}

fn derived_polymorphic_type(name: NameId, level_params: &[NameId], ty: ExprId) -> DerivedSignature {
    DerivedSignature {
        kind: OpaqueInductiveKind::Type,
        name,
        level_params: level_params.to_vec(),
        ty,
    }
}

fn derived_constructor(constructor: &Constructor) -> DerivedSignature {
    DerivedSignature {
        kind: OpaqueInductiveKind::Constructor,
        name: constructor.name,
        level_params: constructor.level_params.clone(),
        ty: constructor.ty,
    }
}

fn derived_recursor(recursor: &Recursor) -> DerivedSignature {
    DerivedSignature {
        kind: OpaqueInductiveKind::Recursor,
        name: recursor.name,
        level_params: recursor.level_params.clone(),
        ty: recursor.ty,
    }
}

fn has_duplicate_parameter(parameters: &[NameId]) -> bool {
    parameters
        .iter()
        .enumerate()
        .any(|(index, parameter)| parameters[..index].contains(parameter))
}

fn parameter_substitution(parameters: &[NameId]) -> HashMap<NameId, LevelTerm> {
    parameters
        .iter()
        .map(|parameter| (*parameter, LevelTerm::param(format!("u#{}", parameter.0))))
        .collect()
}

fn verdict_boundary(judgment: Judgment<()>) -> Result<(), Verdict> {
    match judgment {
        Judgment::Proven { .. } => Ok(()),
        Judgment::Refuted { .. } => Err(Verdict::Reject),
        Judgment::Unknown { .. } => Err(Verdict::Unknown),
    }
}

#[cfg(test)]
mod tests {
    use std::io::Cursor;

    use super::{
        BinaryProductSortLaw, Limits, check_export, check_export_with_policy, check_inductive,
        is_binary_product_constant_application, is_binary_product_minor_type,
        is_binary_product_motive_type, is_bvar_application,
        is_derived_binary_product_constructor_type, is_derived_binary_product_recursor_type,
        is_derived_binary_product_rule, is_exact_binary_product_parameter_telescope, is_prop_sort,
        name_is_root_str,
    };
    use crate::convert::DeltaPolicy;
    use crate::convert::{reset_test_conversion_calls, test_conversion_calls};
    use crate::environment::Environment;
    use crate::id::NameId;
    use crate::parser::parse;
    use crate::syntax::{Declaration, Expr};
    use crate::verdict::Verdict;

    #[test]
    fn good_beta_definition_has_one_trusted_conversion_call() {
        let bytes = include_bytes!("../tests/fixtures/good-beta-definition.ndjson");
        let export = parse(Cursor::new(bytes)).unwrap().resolve().unwrap();
        reset_test_conversion_calls();

        assert_eq!(check_export(export, Limits::default()), Verdict::Accept);
        assert_eq!(test_conversion_calls(), 1);
    }

    #[test]
    fn g3_001_ablation_requires_guarded_semantic_delta() {
        let bytes = include_bytes!("../evidence/residuals/G3-001/fixture.ndjson");
        let export = parse(Cursor::new(bytes)).unwrap().resolve().unwrap();

        assert_eq!(
            check_export_with_policy(
                export.clone(),
                Limits::default(),
                DeltaPolicy::PreferredOnly,
            ),
            Verdict::Reject,
        );
        assert_eq!(
            check_export_with_policy(
                export,
                Limits::default(),
                DeltaPolicy::GuardedSemanticFallback,
            ),
            Verdict::Accept,
        );
    }

    #[test]
    fn universe_parameter_uniqueness_keeps_distinct_binders() {
        assert!(!super::has_duplicate_parameter(&[]));
        assert!(!super::has_duplicate_parameter(&[NameId(1), NameId(2)]));
        assert!(super::has_duplicate_parameter(&[NameId(1), NameId(1)]));
        assert!(super::has_duplicate_parameter(&[
            NameId(1),
            NameId(2),
            NameId(1),
        ]));
    }

    #[test]
    fn rejected_twobool_block_cannot_partially_extend_authority() {
        let bytes = include_bytes!("../evidence/residuals/G11-001/fixture.ndjson");
        let export = parse(Cursor::new(bytes)).unwrap().resolve().unwrap();
        let blocks: Vec<_> = export
            .declarations
            .iter()
            .filter_map(|declaration| match declaration {
                Declaration::Inductive(block) => Some(block.clone()),
                _ => None,
            })
            .collect();
        let [bool_block, twobool_block] = blocks.as_slice() else {
            panic!("fixture must contain Bool followed by TwoBool");
        };
        let environment = check_inductive(
            &export,
            &Environment::empty(),
            bool_block,
            Limits::default(),
            DeltaPolicy::GuardedSemanticFallback,
        )
        .unwrap();
        let authority_before = environment.authority();
        let mut malformed = twobool_block.clone();
        malformed.recursors[0].rules[0].num_fields = 1;

        assert!(matches!(
            check_inductive(
                &export,
                &environment,
                &malformed,
                Limits::default(),
                DeltaPolicy::GuardedSemanticFallback,
            ),
            Err(Verdict::Reject)
        ));
        assert_eq!(environment.authority(), authority_before);
        for name in [
            twobool_block.types[0].name,
            twobool_block.constructors[0].name,
            twobool_block.recursors[0].name,
        ] {
            assert!(environment.get(name).is_none());
        }
    }

    #[test]
    fn g25_boolprop_reconstructs_prop_only_binary_recursor() {
        let bytes = include_bytes!("../evidence/residuals/G25-001/072_boolPropRec.ndjson");
        let export = parse(Cursor::new(bytes)).unwrap().resolve().unwrap();

        assert_eq!(
            check_export(export.clone(), Limits::default()),
            Verdict::Accept
        );

        let block = export
            .declarations
            .iter()
            .find_map(|declaration| match declaration {
                Declaration::Inductive(block)
                    if name_is_root_str(&export, block.types[0].name, "BoolProp") =>
                {
                    Some(block.clone())
                }
                _ => None,
            })
            .unwrap();

        let mut wrong_metadata = block.clone();
        wrong_metadata.recursors[0].num_motives = 0;
        assert!(matches!(
            check_inductive(
                &export,
                &Environment::empty(),
                &wrong_metadata,
                Limits::default(),
                DeltaPolicy::GuardedSemanticFallback,
            ),
            Err(Verdict::Reject)
        ));

        let mut illicit_large_elim_metadata = block;
        illicit_large_elim_metadata.recursors[0]
            .level_params
            .push(NameId(5));
        assert!(matches!(
            check_inductive(
                &export,
                &Environment::empty(),
                &illicit_large_elim_metadata,
                Limits::default(),
                DeltaPolicy::GuardedSemanticFallback,
            ),
            Err(Verdict::Reject)
        ));
    }

    #[test]
    fn g26_rejects_definitely_incoherent_recursor_metadata() {
        let bytes = include_bytes!("../evidence/residuals/G25-001/073_BogusRecursor.ndjson");
        let export = parse(Cursor::new(bytes)).unwrap().resolve().unwrap();
        assert_eq!(check_export(export, Limits::default()), Verdict::Reject);
    }

    #[test]
    fn exact_and_fixture_satisfies_each_independently_derived_claim() {
        let bytes = include_bytes!("../evidence/residuals/G12-001/fixture.ndjson");
        let export = parse(Cursor::new(bytes)).unwrap().resolve().unwrap();
        let block = export
            .declarations
            .iter()
            .find_map(|declaration| match declaration {
                Declaration::Inductive(block) => Some(block),
                _ => None,
            })
            .unwrap();
        let inductive = &block.types[0];
        let constructor = &block.constructors[0];
        let recursor = &block.recursors[0];

        assert!(is_exact_binary_product_parameter_telescope(
            &export,
            inductive.ty,
            BinaryProductSortLaw::And,
        ));
        assert!(is_derived_binary_product_constructor_type(
            &export,
            constructor.ty,
            inductive.name,
            BinaryProductSortLaw::And,
        ));
        assert!(BinaryProductSortLaw::And.validates_recursor_metadata(
            &export,
            inductive,
            constructor,
            recursor,
        ));
        let Expr::Pi {
            domain: first,
            body,
        } = export.exprs.get(recursor.ty).unwrap()
        else {
            panic!("recursor parameter one");
        };
        let Expr::Pi {
            domain: second,
            body,
        } = export.exprs.get(*body).unwrap()
        else {
            panic!("recursor parameter two");
        };
        let Expr::Pi {
            domain: motive,
            body,
        } = export.exprs.get(*body).unwrap()
        else {
            panic!("recursor motive");
        };
        let Expr::Pi {
            domain: minor,
            body,
        } = export.exprs.get(*body).unwrap()
        else {
            panic!("recursor minor");
        };
        let Expr::Pi {
            domain: target,
            body: result,
        } = export.exprs.get(*body).unwrap()
        else {
            panic!("recursor target");
        };
        assert!(is_prop_sort(&export, *first));
        assert!(is_prop_sort(&export, *second));
        assert!(is_binary_product_motive_type(
            &export,
            *motive,
            inductive.name,
            recursor.level_params[0],
            BinaryProductSortLaw::And,
        ));
        assert!(is_binary_product_minor_type(
            &export,
            *minor,
            constructor.name,
            BinaryProductSortLaw::And,
        ));
        assert!(is_binary_product_constant_application(
            &export,
            *target,
            inductive.name,
            3,
            2,
            BinaryProductSortLaw::And,
        ));
        assert!(is_bvar_application(&export, *result, 2, 0));
        assert!(is_derived_binary_product_recursor_type(
            &export,
            inductive.name,
            constructor.name,
            recursor,
            BinaryProductSortLaw::And,
        ));
        assert!(is_derived_binary_product_rule(
            &export,
            inductive.name,
            constructor.name,
            recursor,
            BinaryProductSortLaw::And,
        ));
    }
}
