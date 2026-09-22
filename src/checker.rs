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
use crate::value::EnvFrame;
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
        check_exact_and(export, environment, block, limits, delta_policy)
    } else if name_is_root_str(export, inductive.name, "Prod") {
        check_exact_prod(export, environment, block, limits, delta_policy)
    } else if name_is_root_str(export, inductive.name, "PProd") {
        check_exact_pprod(export, environment, block, limits, delta_policy)
    } else {
        check_twobool_structure(export, environment, block, limits, delta_policy)
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
    if !valid_empty_recursor_metadata(export, inductive.name, recursor)
        || !is_derived_empty_recursor_type(export, inductive.name, recursor)
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

fn valid_empty_recursor_metadata(
    export: &ResolvedExport,
    inductive_name: NameId,
    recursor: &Recursor,
) -> bool {
    recursor.all == [inductive_name]
        && !recursor.is_unsafe
        && !recursor.k
        && recursor.level_params.len() == 1
        && !has_duplicate_parameter(&recursor.level_params)
        && recursor.num_params == 0
        && recursor.num_indices == 0
        && recursor.num_motives == 1
        && recursor.num_minors == 0
        && recursor.rules.is_empty()
        && matches!(
            export.names.get(recursor.name),
            Some(Name::Str { prefix, value }) if *prefix == inductive_name && value == "rec"
        )
}

fn is_derived_empty_recursor_type(
    export: &ResolvedExport,
    inductive_name: NameId,
    recursor: &Recursor,
) -> bool {
    let [universe_parameter] = recursor.level_params.as_slice() else {
        return false;
    };
    let Some(Expr::Pi {
        domain: motive_domain,
        body: recursor_body,
    }) = export.exprs.get(recursor.ty)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: motive_argument,
        body: motive_sort,
    }) = export.exprs.get(*motive_domain)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: target,
        body: motive_application,
    }) = export.exprs.get(*recursor_body)
    else {
        return false;
    };
    is_empty_constant(export, *motive_argument, inductive_name)
        && is_empty_constant(export, *target, inductive_name)
        && matches!(
            export.exprs.get(*motive_sort),
            Some(Expr::Sort(level))
                if matches!(export.levels.get(*level), Some(Level::Param(name)) if name == universe_parameter)
        )
        && matches!(
            export.exprs.get(*motive_application),
            Some(Expr::App { fun, arg })
                if matches!(export.exprs.get(*fun), Some(Expr::BVar(1)))
                    && matches!(export.exprs.get(*arg), Some(Expr::BVar(0)))
        )
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
        || !is_nat_succ_type(export, succ.ty, inductive.name)
    {
        return Err(Verdict::Reject);
    }

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if recursor.is_unsafe {
        return Err(Verdict::Unknown);
    }
    if !valid_nat_recursor_metadata(export, inductive.name, zero.name, succ.name, recursor)
        || !is_derived_nat_recursor_type(export, inductive.name, zero.name, succ.name, recursor)
        || !are_derived_nat_rules(export, inductive.name, zero.name, succ.name, recursor)
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
    derivation.promote(
        export,
        derived_constructor(zero),
        limits.judgment_steps,
        delta_policy,
    )?;
    derivation.promote(
        export,
        derived_constructor(succ),
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

fn is_nat_succ_type(export: &ResolvedExport, expression: ExprId, inductive: NameId) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::Pi { domain, body })
            if is_empty_constant(export, *domain, inductive)
                && is_empty_constant(export, *body, inductive)
    )
}

fn valid_nat_recursor_metadata(
    export: &ResolvedExport,
    inductive: NameId,
    zero: NameId,
    succ: NameId,
    recursor: &Recursor,
) -> bool {
    recursor.all == [inductive]
        && !recursor.k
        && recursor.level_params.len() == 1
        && !has_duplicate_parameter(&recursor.level_params)
        && recursor.num_params == 0
        && recursor.num_indices == 0
        && recursor.num_motives == 1
        && recursor.num_minors == 2
        && matches!(
            recursor.rules.as_slice(),
            [zero_rule, succ_rule]
                if zero_rule.constructor == zero
                    && zero_rule.num_fields == 0
                    && succ_rule.constructor == succ
                    && succ_rule.num_fields == 1
        )
        && name_is_child_str(export, recursor.name, inductive, "rec")
}

fn is_nat_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    motive_level: NameId,
) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::Pi { domain, body })
            if is_empty_constant(export, *domain, inductive)
                && is_sort_parameter(export, *body, motive_level)
    )
}

fn is_nat_succ_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    succ: NameId,
) -> bool {
    let Some(Expr::Pi {
        domain: value,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: induction_hypothesis,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::App {
        fun: motive,
        arg: succ_value,
    }) = export.exprs.get(*result)
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
}

fn is_derived_nat_recursor_type(
    export: &ResolvedExport,
    inductive: NameId,
    zero: NameId,
    succ: NameId,
    recursor: &Recursor,
) -> bool {
    let Some(Expr::Pi {
        domain: motive,
        body,
    }) = export.exprs.get(recursor.ty)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: zero_minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: succ_minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: target,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    is_nat_motive_type(export, *motive, inductive, recursor.level_params[0])
        && is_bvar_applied_to_constant(export, *zero_minor, 0, zero)
        && is_nat_succ_minor_type(export, *succ_minor, inductive, succ)
        && is_empty_constant(export, *target, inductive)
        && is_bvar_applied_to_bvar(export, *result, 3, 0)
}

fn are_derived_nat_rules(
    export: &ResolvedExport,
    inductive: NameId,
    zero: NameId,
    succ: NameId,
    recursor: &Recursor,
) -> bool {
    let [zero_rule, succ_rule] = recursor.rules.as_slice() else {
        return false;
    };
    is_derived_nat_zero_rule(
        export,
        zero_rule.rhs,
        inductive,
        zero,
        succ,
        recursor.level_params[0],
    ) && is_derived_nat_succ_rule(
        export,
        succ_rule.rhs,
        inductive,
        zero,
        succ,
        recursor.name,
        recursor.level_params[0],
    )
}

fn is_derived_nat_zero_rule(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    zero: NameId,
    succ: NameId,
    motive_level: NameId,
) -> bool {
    let Some(Expr::Lam {
        domain: motive,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: zero_minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: succ_minor,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    is_nat_motive_type(export, *motive, inductive, motive_level)
        && is_bvar_applied_to_constant(export, *zero_minor, 0, zero)
        && is_nat_succ_minor_type(export, *succ_minor, inductive, succ)
        && is_bvar(export, *result, 1)
}

fn is_derived_nat_succ_rule(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    zero: NameId,
    succ: NameId,
    recursor_name: NameId,
    motive_level: NameId,
) -> bool {
    let Some(Expr::Lam {
        domain: motive,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: zero_minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: succ_minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: value,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    if !is_nat_motive_type(export, *motive, inductive, motive_level)
        || !is_bvar_applied_to_constant(export, *zero_minor, 0, zero)
        || !is_nat_succ_minor_type(export, *succ_minor, inductive, succ)
        || !is_empty_constant(export, *value, inductive)
    {
        return false;
    }

    let Some(Expr::App {
        fun: succ_step,
        arg: recursive_call,
    }) = export.exprs.get(*result)
    else {
        return false;
    };
    if !is_bvar_application(export, *succ_step, 1, 0) {
        return false;
    }
    let Some(Expr::App {
        fun,
        arg: value_arg,
    }) = export.exprs.get(*recursive_call)
    else {
        return false;
    };
    let Some(Expr::App {
        fun,
        arg: succ_minor_arg,
    }) = export.exprs.get(*fun)
    else {
        return false;
    };
    let Some(Expr::App {
        fun,
        arg: zero_minor_arg,
    }) = export.exprs.get(*fun)
    else {
        return false;
    };
    let Some(Expr::App {
        fun: head,
        arg: motive_arg,
    }) = export.exprs.get(*fun)
    else {
        return false;
    };
    is_unary_polymorphic_constant(export, *head, recursor_name, motive_level)
        && is_bvar(export, *motive_arg, 3)
        && is_bvar(export, *zero_minor_arg, 2)
        && is_bvar(export, *succ_minor_arg, 1)
        && is_bvar(export, *value_arg, 0)
}

/// G19-001: exact recursive indexed RBTree. This is a name-sealed composition
/// of already-earned parameter, index, recursion, and staged opaque-signature
/// laws. It is deliberately not a generic recursive-indexed inductive engine.
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
    if !is_exact_rbtree_type(export, inductive.ty, *level) {
        return Err(Verdict::Reject);
    }

    let [leaf, red, black] = block.constructors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if leaf.is_unsafe || red.is_unsafe || black.is_unsafe {
        return Err(Verdict::Unknown);
    }
    if inductive.all != [inductive.name]
        || inductive.constructors != [leaf.name, red.name, black.name]
        || !valid_rbtree_constructor_metadata(export, inductive.name, *level, leaf, 0, 0, "leaf")
        || !valid_rbtree_constructor_metadata(export, inductive.name, *level, red, 1, 4, "red")
        || !valid_rbtree_constructor_metadata(export, inductive.name, *level, black, 2, 6, "black")
        || !is_derived_rbtree_leaf_type(export, leaf.ty, inductive.name, *level)
        || !is_derived_rbtree_red_type(export, red.ty, inductive.name, *level)
        || !is_derived_rbtree_black_type(export, black.ty, inductive.name, *level)
    {
        return Err(Verdict::Reject);
    }

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if recursor.is_unsafe {
        return Err(Verdict::Unknown);
    }
    if !valid_rbtree_recursor_metadata(
        export,
        inductive.name,
        *level,
        [leaf.name, red.name, black.name],
        recursor,
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
    derivation.promote(
        export,
        derived_polymorphic_type(inductive.name, &inductive.level_params, inductive.ty),
        limits.judgment_steps,
        delta_policy,
    )?;
    for constructor in [leaf, red, black] {
        derivation.promote(
            export,
            derived_constructor(constructor),
            limits.judgment_steps,
            delta_policy,
        )?;
    }
    derivation.promote(
        export,
        derived_recursor(recursor),
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

fn is_exact_rbtree_type(export: &ResolvedExport, expression: ExprId, level: NameId) -> bool {
    let Some(Expr::Pi {
        domain: carrier,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: color,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: height,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    is_sort_succ_parameter(export, *carrier, level)
        && is_root_empty_constant_named(export, *color, "Color")
        && is_root_empty_constant_named(export, *height, "N")
        && is_sort_succ_parameter(export, *result, level)
}

fn rbtree_application_parts(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
) -> Option<(ExprId, ExprId, ExprId)> {
    let Expr::App { fun, arg: height } = export.exprs.get(expression)? else {
        return None;
    };
    let Expr::App { fun, arg: color } = export.exprs.get(*fun)? else {
        return None;
    };
    let Expr::App {
        fun: head,
        arg: carrier,
    } = export.exprs.get(*fun)?
    else {
        return None;
    };
    is_unary_polymorphic_constant(export, *head, inductive, level)
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

fn is_derived_rbtree_leaf_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
) -> bool {
    let Some(Expr::Pi {
        domain: carrier,
        body: result,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some((result_carrier, result_color, result_height)) =
        rbtree_application_parts(export, *result, inductive, level)
    else {
        return false;
    };
    is_sort_succ_parameter(export, *carrier, level)
        && is_bvar(export, result_carrier, 0)
        && is_child_empty_constant_named(export, result_color, "Color", "b")
        && is_child_empty_constant_named(export, result_height, "N", "zero")
}

fn is_derived_rbtree_red_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
) -> bool {
    let Some(Expr::Pi {
        domain: carrier,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: height,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi { domain: left, body }) = export.exprs.get(*body) else {
        return false;
    };
    let Some(Expr::Pi {
        domain: value,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: right,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let (
        Some((left_carrier, left_color, left_height)),
        Some((right_carrier, right_color, right_height)),
        Some((result_carrier, result_color, result_height)),
    ) = (
        rbtree_application_parts(export, *left, inductive, level),
        rbtree_application_parts(export, *right, inductive, level),
        rbtree_application_parts(export, *result, inductive, level),
    )
    else {
        return false;
    };
    is_sort_succ_parameter(export, *carrier, level)
        && is_root_empty_constant_named(export, *height, "N")
        && is_bvar(export, left_carrier, 1)
        && is_child_empty_constant_named(export, left_color, "Color", "b")
        && is_bvar(export, left_height, 0)
        && is_bvar(export, *value, 2)
        && is_bvar(export, right_carrier, 3)
        && is_child_empty_constant_named(export, right_color, "Color", "b")
        && is_bvar(export, right_height, 2)
        && is_bvar(export, result_carrier, 4)
        && is_child_empty_constant_named(export, result_color, "Color", "r")
        && is_bvar(export, result_height, 3)
}

fn is_derived_rbtree_black_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
) -> bool {
    let Some(Expr::Pi {
        domain: carrier,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: first_color,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: second_color,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: height,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi { domain: left, body }) = export.exprs.get(*body) else {
        return false;
    };
    let Some(Expr::Pi {
        domain: value,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: right,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let (
        Some((left_carrier, left_color, left_height)),
        Some((right_carrier, right_color, right_height)),
        Some((result_carrier, result_color, result_height)),
    ) = (
        rbtree_application_parts(export, *left, inductive, level),
        rbtree_application_parts(export, *right, inductive, level),
        rbtree_application_parts(export, *result, inductive, level),
    )
    else {
        return false;
    };
    is_sort_succ_parameter(export, *carrier, level)
        && is_root_empty_constant_named(export, *first_color, "Color")
        && is_root_empty_constant_named(export, *second_color, "Color")
        && is_root_empty_constant_named(export, *height, "N")
        && is_bvar(export, left_carrier, 3)
        && is_bvar(export, left_color, 2)
        && is_bvar(export, left_height, 0)
        && is_bvar(export, *value, 4)
        && is_bvar(export, right_carrier, 5)
        && is_bvar(export, right_color, 3)
        && is_bvar(export, right_height, 2)
        && is_bvar(export, result_carrier, 6)
        && is_child_empty_constant_named(export, result_color, "Color", "b")
        && is_named_succ_bvar(export, result_height, "N", "succ", 3)
}

fn valid_rbtree_recursor_metadata(
    export: &ResolvedExport,
    inductive: NameId,
    level: NameId,
    constructors: [NameId; 3],
    recursor: &Recursor,
) -> bool {
    recursor.all == [inductive]
        && !recursor.k
        && recursor.level_params.len() == 2
        && recursor.level_params[1] == level
        && recursor.level_params[0] != level
        && !has_duplicate_parameter(&recursor.level_params)
        && recursor.num_params == 1
        && recursor.num_indices == 2
        && recursor.num_motives == 1
        && recursor.num_minors == 3
        && matches!(
            recursor.rules.as_slice(),
            [leaf_rule, red_rule, black_rule]
                if leaf_rule.constructor == constructors[0]
                    && leaf_rule.num_fields == 0
                    && red_rule.constructor == constructors[1]
                    && red_rule.num_fields == 4
                    && black_rule.constructor == constructors[2]
                    && black_rule.num_fields == 6
        )
        && name_is_child_str(export, recursor.name, inductive, "rec")
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
    let Some(Expr::Pi {
        domain: color,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: height,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: tree,
        body: result,
    }) = export.exprs.get(*body)
    else {
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
        && is_sort_parameter(export, *result, motive_level)
}

fn is_rbtree_leaf_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    leaf: NameId,
    level: NameId,
) -> bool {
    let Some((color, height, tree)) = motive_application_parts(export, expression, 0) else {
        return false;
    };
    let Some(arguments) = rbtree_constructor_application_args(export, tree, leaf, level) else {
        return false;
    };
    is_child_empty_constant_named(export, color, "Color", "b")
        && is_child_empty_constant_named(export, height, "N", "zero")
        && arguments.len() == 1
        && is_bvar(export, arguments[0], 1)
}

fn is_rbtree_red_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    red: NameId,
    level: NameId,
) -> bool {
    let Some(Expr::Pi {
        domain: height,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi { domain: left, body }) = export.exprs.get(*body) else {
        return false;
    };
    let Some(Expr::Pi {
        domain: value,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: right,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: left_ih,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: right_ih,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };

    let (
        Some((left_carrier, left_color, left_height)),
        Some((right_carrier, right_color, right_height)),
    ) = (
        rbtree_application_parts(export, *left, inductive, level),
        rbtree_application_parts(export, *right, inductive, level),
    )
    else {
        return false;
    };
    let (
        Some((left_ih_color, left_ih_height, left_ih_tree)),
        Some((right_ih_color, right_ih_height, right_ih_tree)),
        Some((result_color, result_height, result_tree)),
    ) = (
        motive_application_parts(export, *left_ih, 5),
        motive_application_parts(export, *right_ih, 6),
        motive_application_parts(export, *result, 7),
    )
    else {
        return false;
    };
    let Some(result_args) = rbtree_constructor_application_args(export, result_tree, red, level)
    else {
        return false;
    };

    is_root_empty_constant_named(export, *height, "N")
        && is_bvar(export, left_carrier, 3)
        && is_child_empty_constant_named(export, left_color, "Color", "b")
        && is_bvar(export, left_height, 0)
        && is_bvar(export, *value, 4)
        && is_bvar(export, right_carrier, 5)
        && is_child_empty_constant_named(export, right_color, "Color", "b")
        && is_bvar(export, right_height, 2)
        && is_child_empty_constant_named(export, left_ih_color, "Color", "b")
        && is_bvar(export, left_ih_height, 3)
        && is_bvar(export, left_ih_tree, 2)
        && is_child_empty_constant_named(export, right_ih_color, "Color", "b")
        && is_bvar(export, right_ih_height, 4)
        && is_bvar(export, right_ih_tree, 1)
        && is_child_empty_constant_named(export, result_color, "Color", "r")
        && is_bvar(export, result_height, 5)
        && result_args.len() == 5
        && [8, 5, 4, 3, 2]
            .into_iter()
            .zip(result_args.iter())
            .all(|(expected, actual)| is_bvar(export, *actual, expected))
}

fn is_rbtree_black_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    black: NameId,
    level: NameId,
) -> bool {
    let Some(Expr::Pi {
        domain: first_color,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: second_color,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: height,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi { domain: left, body }) = export.exprs.get(*body) else {
        return false;
    };
    let Some(Expr::Pi {
        domain: value,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: right,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: left_ih,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: right_ih,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };

    let (
        Some((left_carrier, left_color, left_height)),
        Some((right_carrier, right_color, right_height)),
    ) = (
        rbtree_application_parts(export, *left, inductive, level),
        rbtree_application_parts(export, *right, inductive, level),
    )
    else {
        return false;
    };
    let (
        Some((left_ih_color, left_ih_height, left_ih_tree)),
        Some((right_ih_color, right_ih_height, right_ih_tree)),
        Some((result_color, result_height, result_tree)),
    ) = (
        motive_application_parts(export, *left_ih, 8),
        motive_application_parts(export, *right_ih, 9),
        motive_application_parts(export, *result, 10),
    )
    else {
        return false;
    };
    let Some(result_args) = rbtree_constructor_application_args(export, result_tree, black, level)
    else {
        return false;
    };

    is_root_empty_constant_named(export, *first_color, "Color")
        && is_root_empty_constant_named(export, *second_color, "Color")
        && is_root_empty_constant_named(export, *height, "N")
        && is_bvar(export, left_carrier, 6)
        && is_bvar(export, left_color, 2)
        && is_bvar(export, left_height, 0)
        && is_bvar(export, *value, 7)
        && is_bvar(export, right_carrier, 8)
        && is_bvar(export, right_color, 3)
        && is_bvar(export, right_height, 2)
        && is_bvar(export, left_ih_color, 5)
        && is_bvar(export, left_ih_height, 3)
        && is_bvar(export, left_ih_tree, 2)
        && is_bvar(export, right_ih_color, 5)
        && is_bvar(export, right_ih_height, 4)
        && is_bvar(export, right_ih_tree, 1)
        && is_child_empty_constant_named(export, result_color, "Color", "b")
        && is_named_succ_bvar(export, result_height, "N", "succ", 5)
        && result_args.len() == 7
        && [11, 7, 6, 5, 4, 3, 2]
            .into_iter()
            .zip(result_args.iter())
            .all(|(expected, actual)| is_bvar(export, *actual, expected))
}

fn is_derived_rbtree_recursor_type(
    export: &ResolvedExport,
    inductive: NameId,
    level: NameId,
    constructors: [NameId; 3],
    recursor: &Recursor,
) -> bool {
    let Some(Expr::Pi {
        domain: carrier,
        body,
    }) = export.exprs.get(recursor.ty)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: motive,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: leaf_minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: red_minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: black_minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: color,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: height,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: target,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some((target_carrier, target_color, target_height)) =
        rbtree_application_parts(export, *target, inductive, level)
    else {
        return false;
    };
    let Some((result_color, result_height, result_tree)) =
        motive_application_parts(export, *result, 6)
    else {
        return false;
    };

    is_sort_succ_parameter(export, *carrier, level)
        && is_rbtree_motive_type(export, *motive, inductive, level, recursor.level_params[0])
        && is_rbtree_leaf_minor_type(export, *leaf_minor, constructors[0], level)
        && is_rbtree_red_minor_type(export, *red_minor, inductive, constructors[1], level)
        && is_rbtree_black_minor_type(export, *black_minor, inductive, constructors[2], level)
        && is_root_empty_constant_named(export, *color, "Color")
        && is_root_empty_constant_named(export, *height, "N")
        && is_bvar(export, target_carrier, 6)
        && is_bvar(export, target_color, 1)
        && is_bvar(export, target_height, 0)
        && is_bvar(export, result_color, 2)
        && is_bvar(export, result_height, 1)
        && is_bvar(export, result_tree, 0)
}

fn rbtree_recursor_prefix_domains(
    export: &ResolvedExport,
    expression: ExprId,
) -> Option<(ExprId, ExprId, ExprId, ExprId, ExprId)> {
    let Expr::Pi {
        domain: carrier,
        body,
    } = export.exprs.get(expression)?
    else {
        return None;
    };
    let Expr::Pi {
        domain: motive,
        body,
    } = export.exprs.get(*body)?
    else {
        return None;
    };
    let Expr::Pi { domain: leaf, body } = export.exprs.get(*body)? else {
        return None;
    };
    let Expr::Pi { domain: red, body } = export.exprs.get(*body)? else {
        return None;
    };
    let Expr::Pi { domain: black, .. } = export.exprs.get(*body)? else {
        return None;
    };
    Some((*carrier, *motive, *leaf, *red, *black))
}

fn peel_rbtree_rule_prefix(
    export: &ResolvedExport,
    expression: ExprId,
    expected: (ExprId, ExprId, ExprId, ExprId, ExprId),
) -> Option<ExprId> {
    let (carrier_ty, motive_ty, leaf_ty, red_ty, black_ty) = expected;
    let Expr::Lam {
        domain: carrier,
        body,
    } = export.exprs.get(expression)?
    else {
        return None;
    };
    let Expr::Lam {
        domain: motive,
        body,
    } = export.exprs.get(*body)?
    else {
        return None;
    };
    let Expr::Lam { domain: leaf, body } = export.exprs.get(*body)? else {
        return None;
    };
    let Expr::Lam { domain: red, body } = export.exprs.get(*body)? else {
        return None;
    };
    let Expr::Lam {
        domain: black,
        body,
    } = export.exprs.get(*body)?
    else {
        return None;
    };
    (*carrier == carrier_ty
        && *motive == motive_ty
        && *leaf == leaf_ty
        && *red == red_ty
        && *black == black_ty)
        .then_some(*body)
}

fn is_derived_rbtree_leaf_rule(
    export: &ResolvedExport,
    expression: ExprId,
    prefix: (ExprId, ExprId, ExprId, ExprId, ExprId),
) -> bool {
    let Some(result) = peel_rbtree_rule_prefix(export, expression, prefix) else {
        return false;
    };
    is_bvar(export, result, 2)
}

fn is_derived_rbtree_red_rule(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
    recursor: &Recursor,
    prefix: (ExprId, ExprId, ExprId, ExprId, ExprId),
) -> bool {
    let Some(body) = peel_rbtree_rule_prefix(export, expression, prefix) else {
        return false;
    };
    let Some(Expr::Lam {
        domain: height,
        body,
    }) = export.exprs.get(body)
    else {
        return false;
    };
    let Some(Expr::Lam { domain: left, body }) = export.exprs.get(*body) else {
        return false;
    };
    let Some(Expr::Lam {
        domain: value,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: right,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let (
        Some((left_carrier, left_color, left_height)),
        Some((right_carrier, right_color, right_height)),
    ) = (
        rbtree_application_parts(export, *left, inductive, level),
        rbtree_application_parts(export, *right, inductive, level),
    )
    else {
        return false;
    };
    let (head, arguments) = application_spine(export, *result);
    if !is_bvar(export, head, 5) || arguments.len() != 6 {
        return false;
    }
    let Some(left_call) = rbtree_recursor_application_args(
        export,
        arguments[4],
        recursor.name,
        recursor.level_params[0],
        level,
    ) else {
        return false;
    };
    let Some(right_call) = rbtree_recursor_application_args(
        export,
        arguments[5],
        recursor.name,
        recursor.level_params[0],
        level,
    ) else {
        return false;
    };
    is_root_empty_constant_named(export, *height, "N")
        && is_bvar(export, left_carrier, 5)
        && is_child_empty_constant_named(export, left_color, "Color", "b")
        && is_bvar(export, left_height, 0)
        && is_bvar(export, *value, 6)
        && is_bvar(export, right_carrier, 7)
        && is_child_empty_constant_named(export, right_color, "Color", "b")
        && is_bvar(export, right_height, 2)
        && [3, 2, 1, 0]
            .into_iter()
            .zip(arguments[..4].iter())
            .all(|(expected, actual)| is_bvar(export, *actual, expected))
        && left_call.len() == 8
        && [8, 7, 6, 5, 4]
            .into_iter()
            .zip(left_call[..5].iter())
            .all(|(expected, actual)| is_bvar(export, *actual, expected))
        && is_child_empty_constant_named(export, left_call[5], "Color", "b")
        && is_bvar(export, left_call[6], 3)
        && is_bvar(export, left_call[7], 2)
        && right_call.len() == 8
        && [8, 7, 6, 5, 4]
            .into_iter()
            .zip(right_call[..5].iter())
            .all(|(expected, actual)| is_bvar(export, *actual, expected))
        && is_child_empty_constant_named(export, right_call[5], "Color", "b")
        && is_bvar(export, right_call[6], 3)
        && is_bvar(export, right_call[7], 0)
}

fn is_derived_rbtree_black_rule(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
    recursor: &Recursor,
    prefix: (ExprId, ExprId, ExprId, ExprId, ExprId),
) -> bool {
    let Some(body) = peel_rbtree_rule_prefix(export, expression, prefix) else {
        return false;
    };
    let Some(Expr::Lam {
        domain: first_color,
        body,
    }) = export.exprs.get(body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: second_color,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: height,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam { domain: left, body }) = export.exprs.get(*body) else {
        return false;
    };
    let Some(Expr::Lam {
        domain: value,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: right,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let (
        Some((left_carrier, left_color, left_height)),
        Some((right_carrier, right_color, right_height)),
    ) = (
        rbtree_application_parts(export, *left, inductive, level),
        rbtree_application_parts(export, *right, inductive, level),
    )
    else {
        return false;
    };
    let (head, arguments) = application_spine(export, *result);
    if !is_bvar(export, head, 6) || arguments.len() != 8 {
        return false;
    }
    let Some(left_call) = rbtree_recursor_application_args(
        export,
        arguments[6],
        recursor.name,
        recursor.level_params[0],
        level,
    ) else {
        return false;
    };
    let Some(right_call) = rbtree_recursor_application_args(
        export,
        arguments[7],
        recursor.name,
        recursor.level_params[0],
        level,
    ) else {
        return false;
    };
    is_root_empty_constant_named(export, *first_color, "Color")
        && is_root_empty_constant_named(export, *second_color, "Color")
        && is_root_empty_constant_named(export, *height, "N")
        && is_bvar(export, left_carrier, 7)
        && is_bvar(export, left_color, 2)
        && is_bvar(export, left_height, 0)
        && is_bvar(export, *value, 8)
        && is_bvar(export, right_carrier, 9)
        && is_bvar(export, right_color, 3)
        && is_bvar(export, right_height, 2)
        && [5, 4, 3, 2, 1, 0]
            .into_iter()
            .zip(arguments[..6].iter())
            .all(|(expected, actual)| is_bvar(export, *actual, expected))
        && left_call.len() == 8
        && [10, 9, 8, 7, 6]
            .into_iter()
            .zip(left_call[..5].iter())
            .all(|(expected, actual)| is_bvar(export, *actual, expected))
        && is_bvar(export, left_call[5], 5)
        && is_bvar(export, left_call[6], 3)
        && is_bvar(export, left_call[7], 2)
        && right_call.len() == 8
        && [10, 9, 8, 7, 6]
            .into_iter()
            .zip(right_call[..5].iter())
            .all(|(expected, actual)| is_bvar(export, *actual, expected))
        && is_bvar(export, right_call[5], 4)
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
    let Some(prefix) = rbtree_recursor_prefix_domains(export, recursor.ty) else {
        return false;
    };
    leaf_rule.constructor == constructors[0]
        && leaf_rule.num_fields == 0
        && red_rule.constructor == constructors[1]
        && red_rule.num_fields == 4
        && black_rule.constructor == constructors[2]
        && black_rule.num_fields == 6
        && is_derived_rbtree_leaf_rule(export, leaf_rule.rhs, prefix)
        && is_derived_rbtree_red_rule(export, red_rule.rhs, inductive, level, recursor, prefix)
        && is_derived_rbtree_black_rule(export, black_rule.rhs, inductive, level, recursor, prefix)
}

/// G10-001: a closed, safe, two-constructor enum. This admits no constructor
/// fields and therefore needs neither positivity search nor recursive
/// occurrences. Exported recursor equations are checked against a derived
/// de Bruijn shape but are not installed as runtime iota rules.
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
    if !name_is_root_str(export, inductive.name, "Bool")
        && !name_is_root_str(export, inductive.name, "Color")
    {
        return Err(Verdict::Unknown);
    }
    if inductive.num_params != 0
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || !matches!(
            export.exprs.get(inductive.ty),
            Some(Expr::Sort(level))
                if matches!(export.levels.get(*level), Some(Level::Succ(LevelId(0))))
        )
    {
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
    if !valid_binary_recursor_metadata(export, inductive.name, recursor)
        || !is_derived_binary_recursor_type(export, inductive.name, &constructor_names, recursor)
        || !are_derived_binary_rules(export, inductive.name, &constructor_names, recursor)
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

fn valid_binary_recursor_metadata(
    export: &ResolvedExport,
    inductive_name: NameId,
    recursor: &Recursor,
) -> bool {
    recursor.all == [inductive_name]
        && !recursor.is_unsafe
        && !recursor.k
        && recursor.level_params.len() == 1
        && recursor.num_params == 0
        && recursor.num_indices == 0
        && recursor.num_motives == 1
        && recursor.num_minors == 2
        && recursor.rules.len() == 2
        && matches!(
            export.names.get(recursor.name),
            Some(Name::Str { prefix, value }) if *prefix == inductive_name && value == "rec"
        )
}

fn is_derived_binary_recursor_type(
    export: &ResolvedExport,
    inductive: NameId,
    constructors: &[NameId],
    recursor: &Recursor,
) -> bool {
    let [first, second] = constructors else {
        return false;
    };
    let Some(Expr::Pi {
        domain: motive,
        body,
    }) = export.exprs.get(recursor.ty)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: motive_arg,
        body: motive_sort,
    }) = export.exprs.get(*motive)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: first_minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: second_minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: target,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    is_empty_constant(export, *motive_arg, inductive)
        && matches!(
            export.exprs.get(*motive_sort),
            Some(Expr::Sort(level)) if matches!(
                export.levels.get(*level),
                Some(Level::Param(name)) if name == &recursor.level_params[0]
            )
        )
        && is_bvar_applied_to_constant(export, *first_minor, 0, *first)
        && is_bvar_applied_to_constant(export, *second_minor, 1, *second)
        && is_empty_constant(export, *target, inductive)
        && is_bvar_applied_to_bvar(export, *result, 3, 0)
}

fn are_derived_binary_rules(
    export: &ResolvedExport,
    inductive: NameId,
    constructors: &[NameId],
    recursor: &Recursor,
) -> bool {
    let [first, second] = constructors else {
        return false;
    };
    recursor.rules.iter().enumerate().all(|(index, rule)| {
        rule.constructor == constructors[index]
            && rule.num_fields == 0
            && is_binary_rule_rhs(
                export,
                rule.rhs,
                inductive,
                *first,
                *second,
                1 - index as u64,
            )
    })
}

fn is_binary_rule_rhs(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    first: NameId,
    second: NameId,
    selected_minor: u64,
) -> bool {
    let Some(Expr::Lam {
        domain: motive,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: motive_arg, ..
    }) = export.exprs.get(*motive)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: first_minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: second_minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    matches!(export.exprs.get(*body), Some(Expr::BVar(index)) if *index == selected_minor)
        && is_empty_constant(export, *motive_arg, inductive)
        && is_bvar_applied_to_constant(export, *first_minor, 0, first)
        && is_bvar_applied_to_constant(export, *second_minor, 1, second)
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

fn is_bvar_applied_to_bvar(
    export: &ResolvedExport,
    expression: ExprId,
    function: u64,
    argument: u64,
) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::App { fun, arg })
            if matches!(export.exprs.get(*fun), Some(Expr::BVar(index)) if *index == function)
                && matches!(export.exprs.get(*arg), Some(Expr::BVar(index)) if *index == argument)
    )
}

/// G15-001's closed internal quotient, extended by G16-001's independently
/// earned nullary law. External recognition remains name-sealed: adding this
/// variant cannot authorize any unrelated fourth product family.
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
            Self::Eq { .. } => is_prop_sort(export, expression),
            Self::And => is_prop_sort(export, expression),
            Self::Prod { first, second } => {
                is_sort_max_succ_parameters(export, expression, first, second)
            }
            Self::PProd { first, second } => {
                is_sort_max_one_parameters(export, expression, first, second)
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

    fn validates_type(self, export: &ResolvedExport, expression: ExprId) -> bool {
        match self {
            Self::PUnit { .. } => self.result_sort(export, expression),
            Self::Eq { level } => is_exact_eq_type(export, expression, level),
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
            Self::Eq { .. } => is_derived_eq_constructor_type(export, expression, inductive, self),
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
        derivation.promote(export, derived_type, limits.judgment_steps, delta_policy)?;
        derivation.promote(
            export,
            derived_constructor(self.constructor),
            limits.judgment_steps,
            delta_policy,
        )?;

        let valid_recursor = match self.law {
            BinaryProductSortLaw::PUnit { .. } => {
                valid_punit_recursor_metadata(
                    export,
                    self.inductive.name,
                    &self.inductive.level_params,
                    self.constructor.name,
                    self.recursor,
                    self.law,
                ) && is_derived_punit_recursor_type(
                    export,
                    self.inductive.name,
                    self.constructor.name,
                    self.recursor,
                    self.law,
                ) && is_derived_punit_rule(
                    export,
                    self.inductive.name,
                    self.constructor.name,
                    self.recursor,
                    self.law,
                )
            }
            BinaryProductSortLaw::Eq { .. } => {
                valid_eq_recursor_metadata(
                    export,
                    self.inductive.name,
                    &self.inductive.level_params,
                    self.constructor.name,
                    self.recursor,
                    self.law,
                ) && is_derived_eq_recursor_type(
                    export,
                    self.inductive.name,
                    self.constructor.name,
                    self.recursor,
                    self.law,
                ) && is_derived_eq_rule(
                    export,
                    self.inductive.name,
                    self.constructor.name,
                    self.recursor,
                    self.law,
                )
            }
            BinaryProductSortLaw::And
            | BinaryProductSortLaw::Prod { .. }
            | BinaryProductSortLaw::PProd { .. } => {
                valid_binary_product_recursor_metadata(
                    export,
                    self.inductive.name,
                    &self.inductive.level_params,
                    self.constructor.name,
                    self.recursor,
                    self.law,
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
fn check_exact_and(
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

    // These dimensions leave the exact And envelope. Their semantics remain
    // unsupported rather than being guessed from this one declaration.
    if inductive.num_params != 2
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || !inductive.level_params.is_empty()
        || constructor.is_unsafe
        || !constructor.level_params.is_empty()
    {
        return Err(Verdict::Unknown);
    }
    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if recursor.is_unsafe {
        return Err(Verdict::Unknown);
    }

    ExactBinaryProductDerivation {
        inductive,
        constructor,
        recursor,
        constructor_suffix: "intro",
        law: BinaryProductSortLaw::And,
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
    let Some(Expr::App { fun, arg }) = export.exprs.get(expression) else {
        return false;
    };
    let Some(Expr::App {
        fun: head,
        arg: first_arg,
    }) = export.exprs.get(*fun)
    else {
        return false;
    };
    is_bvar(export, *head, function)
        && is_bvar(export, *first_arg, first)
        && is_bvar(export, *arg, second)
}

fn is_exact_binary_product_parameter_telescope(
    export: &ResolvedExport,
    expression: ExprId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some(Expr::Pi {
        domain: first,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: second,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    law.parameter_sort(export, *first, true)
        && law.parameter_sort(export, *second, false)
        && law.result_sort(export, *result)
}

fn is_derived_binary_product_constructor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some(Expr::Pi {
        domain: first,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: second,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi { domain: left, body }) = export.exprs.get(*body) else {
        return false;
    };
    let Some(Expr::Pi {
        domain: right,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    law.parameter_sort(export, *first, true)
        && law.parameter_sort(export, *second, false)
        && is_bvar(export, *left, 1)
        && is_bvar(export, *right, 1)
        && is_binary_product_constant_application(export, *result, inductive, 3, 2, law)
}

fn valid_binary_product_recursor_metadata(
    export: &ResolvedExport,
    inductive: NameId,
    inductive_level_params: &[NameId],
    constructor: NameId,
    recursor: &Recursor,
    law: BinaryProductSortLaw,
) -> bool {
    recursor.all == [inductive]
        && !recursor.k
        && law.recursor_levels(inductive_level_params, recursor)
        && !has_duplicate_parameter(&recursor.level_params)
        && recursor.num_params == 2
        && recursor.num_indices == 0
        && recursor.num_motives == 1
        && recursor.num_minors == 1
        && matches!(recursor.rules.as_slice(), [rule] if rule.constructor == constructor && rule.num_fields == 2)
        && name_is_child_str(export, recursor.name, inductive, "rec")
}

fn is_derived_binary_product_recursor_type(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    recursor: &Recursor,
    law: BinaryProductSortLaw,
) -> bool {
    let Some(Expr::Pi {
        domain: first,
        body,
    }) = export.exprs.get(recursor.ty)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: second,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: motive,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: target,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    law.parameter_sort(export, *first, true)
        && law.parameter_sort(export, *second, false)
        && is_binary_product_motive_type(export, *motive, inductive, recursor.level_params[0], law)
        && is_binary_product_minor_type(export, *minor, constructor, law)
        && is_binary_product_constant_application(export, *target, inductive, 3, 2, law)
        && is_bvar_application(export, *result, 2, 0)
}

fn is_binary_product_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    motive_level: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some(Expr::Pi {
        domain: argument,
        body: result,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    is_binary_product_constant_application(export, *argument, inductive, 1, 0, law)
        && is_sort_parameter(export, *result, motive_level)
}

fn is_binary_product_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some(Expr::Pi { domain: left, body }) = export.exprs.get(expression) else {
        return false;
    };
    let Some(Expr::Pi {
        domain: right,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::App {
        fun: motive,
        arg: constructed,
    }) = export.exprs.get(*result)
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
    let Some(Expr::Lam {
        domain: first,
        body,
    }) = export.exprs.get(rule.rhs)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: second,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: motive,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam { domain: left, body }) = export.exprs.get(*body) else {
        return false;
    };
    let Some(Expr::Lam {
        domain: right,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    law.parameter_sort(export, *first, true)
        && law.parameter_sort(export, *second, false)
        && is_binary_product_motive_type(export, *motive, inductive, recursor.level_params[0], law)
        && is_binary_product_minor_type(export, *minor, constructor, law)
        && is_bvar(export, *left, 3)
        && is_bvar(export, *right, 3)
        && is_binary_bvar_application(export, *result, 2, 1, 0)
}

fn is_binary_product_constant_application(
    export: &ResolvedExport,
    expression: ExprId,
    constant: NameId,
    first: u64,
    second: u64,
    law: BinaryProductSortLaw,
) -> bool {
    let Some(Expr::App { fun, arg }) = export.exprs.get(expression) else {
        return false;
    };
    let Some(Expr::App {
        fun: head,
        arg: first_arg,
    }) = export.exprs.get(*fun)
    else {
        return false;
    };
    law.constant(export, *head, constant)
        && is_bvar(export, *first_arg, first)
        && is_bvar(export, *arg, second)
}

fn is_binary_product_constructor_application(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some(Expr::App { fun, arg: right }) = export.exprs.get(expression) else {
        return false;
    };
    let Some(Expr::App { fun, arg: left }) = export.exprs.get(*fun) else {
        return false;
    };
    let Some(Expr::App {
        fun,
        arg: second_parameter,
    }) = export.exprs.get(*fun)
    else {
        return false;
    };
    let Some(Expr::App {
        fun: head,
        arg: first_parameter,
    }) = export.exprs.get(*fun)
    else {
        return false;
    };
    law.constant(export, *head, constructor)
        && is_bvar(export, *first_parameter, 4)
        && is_bvar(export, *second_parameter, 3)
        && is_bvar(export, *left, 1)
        && is_bvar(export, *right, 0)
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

fn valid_punit_recursor_metadata(
    export: &ResolvedExport,
    inductive: NameId,
    inductive_level_params: &[NameId],
    constructor: NameId,
    recursor: &Recursor,
    law: BinaryProductSortLaw,
) -> bool {
    recursor.all == [inductive]
        && !recursor.k
        && law.recursor_levels(inductive_level_params, recursor)
        && !has_duplicate_parameter(&recursor.level_params)
        && recursor.num_params == 0
        && recursor.num_indices == 0
        && recursor.num_motives == 1
        && recursor.num_minors == 1
        && matches!(recursor.rules.as_slice(), [rule]
            if rule.constructor == constructor && rule.num_fields == 0)
        && name_is_child_str(export, recursor.name, inductive, "rec")
}

fn is_derived_punit_recursor_type(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    recursor: &Recursor,
    law: BinaryProductSortLaw,
) -> bool {
    let Some(Expr::Pi {
        domain: motive,
        body,
    }) = export.exprs.get(recursor.ty)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: target,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    is_punit_motive_type(export, *motive, inductive, recursor.level_params[0], law)
        && is_punit_minor_type(export, *minor, constructor, law)
        && law.constant(export, *target, inductive)
        && is_bvar_application(export, *result, 2, 0)
}

fn is_derived_punit_rule(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    recursor: &Recursor,
    law: BinaryProductSortLaw,
) -> bool {
    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    let Some(Expr::Lam {
        domain: motive,
        body,
    }) = export.exprs.get(rule.rhs)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: minor,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    is_punit_motive_type(export, *motive, inductive, recursor.level_params[0], law)
        && is_punit_minor_type(export, *minor, constructor, law)
        && is_bvar(export, *result, 0)
}

fn is_punit_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    motive_level: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some(Expr::Pi {
        domain: argument,
        body: result,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    law.constant(export, *argument, inductive) && is_sort_parameter(export, *result, motive_level)
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

fn is_exact_eq_type(export: &ResolvedExport, expression: ExprId, level: NameId) -> bool {
    let Some(Expr::Pi {
        domain: carrier,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: parameter,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: index,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    is_sort_parameter(export, *carrier, level)
        && is_bvar(export, *parameter, 0)
        && is_bvar(export, *index, 1)
        && is_prop_sort(export, *result)
}

fn is_derived_eq_constructor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some(Expr::Pi {
        domain: carrier,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: parameter,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let BinaryProductSortLaw::Eq { level } = law else {
        return false;
    };
    is_sort_parameter(export, *carrier, level)
        && is_bvar(export, *parameter, 0)
        && is_eq_application(export, *result, inductive, law, 1, 0, 0)
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
    let Some(Expr::App {
        fun,
        arg: index_arg,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::App {
        fun,
        arg: parameter_arg,
    }) = export.exprs.get(*fun)
    else {
        return false;
    };
    let Some(Expr::App {
        fun: head,
        arg: carrier_arg,
    }) = export.exprs.get(*fun)
    else {
        return false;
    };
    law.constant(export, *head, inductive)
        && is_bvar(export, *carrier_arg, carrier)
        && is_bvar(export, *parameter_arg, parameter)
        && is_bvar(export, *index_arg, index)
}

fn is_eq_constructor_application(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    law: BinaryProductSortLaw,
    carrier: u64,
    parameter: u64,
) -> bool {
    let Some(Expr::App {
        fun,
        arg: parameter_arg,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::App {
        fun: head,
        arg: carrier_arg,
    }) = export.exprs.get(*fun)
    else {
        return false;
    };
    law.constant(export, *head, constructor)
        && is_bvar(export, *carrier_arg, carrier)
        && is_bvar(export, *parameter_arg, parameter)
}

fn valid_eq_recursor_metadata(
    export: &ResolvedExport,
    inductive: NameId,
    inductive_level_params: &[NameId],
    constructor: NameId,
    recursor: &Recursor,
    law: BinaryProductSortLaw,
) -> bool {
    recursor.all == [inductive]
        && recursor.k
        && law.recursor_levels(inductive_level_params, recursor)
        && !has_duplicate_parameter(&recursor.level_params)
        && recursor.num_params == 2
        && recursor.num_indices == 1
        && recursor.num_motives == 1
        && recursor.num_minors == 1
        && matches!(recursor.rules.as_slice(), [rule]
            if rule.constructor == constructor && rule.num_fields == 0)
        && name_is_child_str(export, recursor.name, inductive, "rec")
}

fn is_eq_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    motive_level: NameId,
    law: BinaryProductSortLaw,
) -> bool {
    let Some(Expr::Pi {
        domain: index,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: proof,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    is_bvar(export, *index, 1)
        && is_eq_application(export, *proof, inductive, law, 2, 1, 0)
        && is_sort_parameter(export, *result, motive_level)
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

fn is_derived_eq_recursor_type(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    recursor: &Recursor,
    law: BinaryProductSortLaw,
) -> bool {
    let Some(Expr::Pi {
        domain: carrier,
        body,
    }) = export.exprs.get(recursor.ty)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: parameter,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: motive,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: index,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: proof,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let BinaryProductSortLaw::Eq { level } = law else {
        return false;
    };
    is_sort_parameter(export, *carrier, level)
        && is_bvar(export, *parameter, 0)
        && is_eq_motive_type(export, *motive, inductive, recursor.level_params[0], law)
        && is_eq_minor_type(export, *minor, constructor, law)
        && is_bvar(export, *index, 3)
        && is_eq_application(export, *proof, inductive, law, 4, 3, 0)
        && is_binary_bvar_application(export, *result, 3, 1, 0)
}

fn is_derived_eq_rule(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    recursor: &Recursor,
    law: BinaryProductSortLaw,
) -> bool {
    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    let Some(Expr::Lam {
        domain: carrier,
        body,
    }) = export.exprs.get(rule.rhs)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: parameter,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: motive,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: minor,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let BinaryProductSortLaw::Eq { level } = law else {
        return false;
    };
    is_sort_parameter(export, *carrier, level)
        && is_bvar(export, *parameter, 0)
        && is_eq_motive_type(export, *motive, inductive, recursor.level_params[0], law)
        && is_eq_minor_type(export, *minor, constructor, law)
        && is_bvar(export, *result, 0)
}

/// G13-001's name-specific frontier. G15 shares only its already-qualified
/// derivation skeleton; this envelope and its Type-level law remain separate.
fn check_exact_prod(
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
    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if recursor.is_unsafe {
        return Err(Verdict::Unknown);
    }
    if prod_has_dependent_parameter_neighbor(export, inductive.ty) {
        return Err(Verdict::Unknown);
    }
    let [first_level, second_level] = inductive.level_params.as_slice() else {
        return Err(Verdict::Reject);
    };
    ExactBinaryProductDerivation {
        inductive,
        constructor,
        recursor,
        constructor_suffix: "mk",
        law: BinaryProductSortLaw::Prod {
            first: *first_level,
            second: *second_level,
        },
    }
    .validate_and_promote(export, environment, limits, delta_policy)
}

fn prod_has_dependent_parameter_neighbor(export: &ResolvedExport, expression: ExprId) -> bool {
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

fn is_sort_max_succ_parameters(
    export: &ResolvedExport,
    expression: ExprId,
    first: NameId,
    second: NameId,
) -> bool {
    let Some(Expr::Sort(level)) = export.exprs.get(expression) else {
        return false;
    };
    let Some(Level::Max(left, right)) = export.levels.get(*level) else {
        return false;
    };
    level_is_succ_parameter(export, *left, first) && level_is_succ_parameter(export, *right, second)
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
fn check_exact_pprod(
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
    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if recursor.is_unsafe {
        return Err(Verdict::Unknown);
    }
    if pprod_has_dependent_parameter_neighbor(export, inductive.ty)
        || pprod_has_dependent_field_neighbor(export, constructor.ty)
    {
        return Err(Verdict::Unknown);
    }
    let [first_level, second_level] = inductive.level_params.as_slice() else {
        return Err(Verdict::Reject);
    };
    ExactBinaryProductDerivation {
        inductive,
        constructor,
        recursor,
        constructor_suffix: "mk",
        law: BinaryProductSortLaw::PProd {
            first: *first_level,
            second: *second_level,
        },
    }
    .validate_and_promote(export, environment, limits, delta_policy)
}

fn pprod_has_dependent_parameter_neighbor(export: &ResolvedExport, expression: ExprId) -> bool {
    let Some(Expr::Pi { body, .. }) = export.exprs.get(expression) else {
        return false;
    };
    matches!(
        export.exprs.get(*body),
        Some(Expr::Pi { domain, .. }) if matches!(export.exprs.get(*domain), Some(Expr::Pi { .. }))
    )
}

fn pprod_has_dependent_field_neighbor(export: &ResolvedExport, expression: ExprId) -> bool {
    let Some(Expr::Pi { body, .. }) = export.exprs.get(expression) else {
        return false;
    };
    let Some(Expr::Pi { body, .. }) = export.exprs.get(*body) else {
        return false;
    };
    let Some(Expr::Pi {
        domain: first_field,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: second_field,
        ..
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    [first_field, second_field].into_iter().any(|domain| {
        matches!(
            export.exprs.get(*domain),
            Some(Expr::Pi { .. } | Expr::App { .. })
        )
    })
}

fn is_sort_max_one_parameters(
    export: &ResolvedExport,
    expression: ExprId,
    first: NameId,
    second: NameId,
) -> bool {
    let Some(Expr::Sort(level)) = export.exprs.get(expression) else {
        return false;
    };
    let Some(Level::Max(left, right)) = export.levels.get(*level) else {
        return false;
    };
    let Some(Level::Max(one, first_level)) = export.levels.get(*left) else {
        return false;
    };
    level_is_one(export, *one)
        && matches!(export.levels.get(*first_level), Some(Level::Param(name)) if *name == first)
        && matches!(export.levels.get(*right), Some(Level::Param(name)) if *name == second)
}

fn level_is_one(export: &ResolvedExport, level: LevelId) -> bool {
    matches!(
        export.levels.get(level),
        Some(Level::Succ(inner)) if matches!(export.levels.get(*inner), Some(Level::Zero))
    )
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
    derivation.promote(
        export,
        derived_type(inductive.name, inductive.ty),
        limits.judgment_steps,
        delta_policy,
    )?;
    derivation.promote(
        export,
        derived_constructor(constructor),
        limits.judgment_steps,
        delta_policy,
    )?;

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if !valid_twobool_recursor_metadata(export, inductive.name, constructor.name, recursor)
        || !is_derived_twobool_recursor_type(
            export,
            inductive.name,
            constructor.name,
            bool_name,
            recursor,
        )
        || !is_derived_twobool_rule(
            export,
            inductive.name,
            constructor.name,
            bool_name,
            recursor,
        )
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

fn valid_twobool_recursor_metadata(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    recursor: &Recursor,
) -> bool {
    recursor.all == [inductive]
        && !recursor.is_unsafe
        && !recursor.k
        && recursor.level_params.len() == 1
        && !has_duplicate_parameter(&recursor.level_params)
        && recursor.num_params == 0
        && recursor.num_indices == 0
        && recursor.num_motives == 1
        && recursor.num_minors == 1
        && matches!(recursor.rules.as_slice(), [rule] if rule.constructor == constructor && rule.num_fields == 2)
        && name_is_child_str(export, recursor.name, inductive, "rec")
}

fn is_twobool_constructor_type(
    export: &ResolvedExport,
    expression: ExprId,
    field_type: NameId,
    inductive: NameId,
) -> bool {
    let Some(Expr::Pi {
        domain: first,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: second,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    is_empty_constant(export, *first, field_type)
        && is_empty_constant(export, *second, field_type)
        && is_empty_constant(export, *body, inductive)
}

fn is_derived_twobool_recursor_type(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    field_type: NameId,
    recursor: &Recursor,
) -> bool {
    let Some(Expr::Pi {
        domain: motive,
        body,
    }) = export.exprs.get(recursor.ty)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: motive_arg,
        body: motive_sort,
    }) = export.exprs.get(*motive)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: target,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    is_empty_constant(export, *motive_arg, inductive)
        && matches!(
            export.exprs.get(*motive_sort),
            Some(Expr::Sort(level)) if matches!(
                export.levels.get(*level),
                Some(Level::Param(name)) if name == &recursor.level_params[0]
            )
        )
        && is_twobool_minor_type(export, *minor, constructor, field_type)
        && is_empty_constant(export, *target, inductive)
        && is_bvar_applied_to_bvar(export, *result, 2, 0)
}

fn is_twobool_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    field_type: NameId,
) -> bool {
    let Some(Expr::Pi {
        domain: first,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: second,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::App {
        fun: motive,
        arg: constructed,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    is_empty_constant(export, *first, field_type)
        && is_empty_constant(export, *second, field_type)
        && matches!(export.exprs.get(*motive), Some(Expr::BVar(2)))
        && is_constructor_applied_to_two_bvars(export, *constructed, constructor, 1, 0)
}

fn is_derived_twobool_rule(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    field_type: NameId,
    recursor: &Recursor,
) -> bool {
    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    let Some(Expr::Lam {
        domain: motive,
        body,
    }) = export.exprs.get(rule.rhs)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: motive_arg, ..
    }) = export.exprs.get(*motive)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: minor,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: first,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: second,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    is_empty_constant(export, *motive_arg, inductive)
        && is_twobool_minor_type(export, *minor, constructor, field_type)
        && is_empty_constant(export, *first, field_type)
        && is_empty_constant(export, *second, field_type)
        && is_bvar_applied_to_two_bvars(export, *result, 2, 1, 0)
}

fn is_constructor_applied_to_two_bvars(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    first: u64,
    second: u64,
) -> bool {
    let Some(Expr::App { fun, arg }) = export.exprs.get(expression) else {
        return false;
    };
    let Some(Expr::App {
        fun: head,
        arg: first_arg,
    }) = export.exprs.get(*fun)
    else {
        return false;
    };
    is_empty_constant(export, *head, constructor)
        && matches!(export.exprs.get(*first_arg), Some(Expr::BVar(index)) if *index == first)
        && matches!(export.exprs.get(*arg), Some(Expr::BVar(index)) if *index == second)
}

fn is_bvar_applied_to_two_bvars(
    export: &ResolvedExport,
    expression: ExprId,
    function: u64,
    first: u64,
    second: u64,
) -> bool {
    let Some(Expr::App { fun, arg }) = export.exprs.get(expression) else {
        return false;
    };
    let Some(Expr::App {
        fun: head,
        arg: first_arg,
    }) = export.exprs.get(*fun)
    else {
        return false;
    };
    matches!(export.exprs.get(*head), Some(Expr::BVar(index)) if *index == function)
        && matches!(export.exprs.get(*first_arg), Some(Expr::BVar(index)) if *index == first)
        && matches!(export.exprs.get(*arg), Some(Expr::BVar(index)) if *index == second)
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
    let Expr::Pi { domain, .. } = export.exprs.get(expression)? else {
        return None;
    };
    let Expr::Const { name, levels } = export.exprs.get(*domain)? else {
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
        valid_binary_product_recursor_metadata,
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
        assert!(valid_binary_product_recursor_metadata(
            &export,
            inductive.name,
            &inductive.level_params,
            constructor.name,
            recursor,
            BinaryProductSortLaw::And,
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
