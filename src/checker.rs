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

fn check_inductive(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    match block.constructors.len() {
        0 => check_empty_inductive(export, environment, block, limits, delta_policy),
        1 => check_twobool_structure(export, environment, block, limits, delta_policy),
        2 => check_binary_enum(export, environment, block, limits, delta_policy),
        _ => Err(Verdict::Unknown),
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

    use super::{Limits, check_export, check_export_with_policy, check_inductive};
    use crate::convert::DeltaPolicy;
    use crate::convert::{reset_test_conversion_calls, test_conversion_calls};
    use crate::environment::Environment;
    use crate::id::NameId;
    use crate::parser::parse;
    use crate::syntax::Declaration;
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
}
