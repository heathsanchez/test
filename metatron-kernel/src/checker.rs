use std::collections::HashMap;

use crate::convert::DeltaPolicy;
use crate::environment::{ConstantDecl, Environment};
use crate::id::NameId;
use crate::id::{ExprId, LevelId};
use crate::judgment::Judgment;
use crate::level::LevelTerm;
use crate::parser::ResolvedExport;
use crate::syntax::{Declaration, Expr, InductiveBlock, Level, Name, Recursor};
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
    export: ResolvedExport,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Verdict {
    check_export_with_policy_and_installer(
        export,
        limits,
        delta_policy,
        install_closed_nonrecursive_inductive,
    )
}

fn check_export_with_policy_and_installer(
    mut export: ResolvedExport,
    limits: Limits,
    delta_policy: DeltaPolicy,
    installer: ClosedInstaller,
) -> Verdict {
    let mut environment = Environment::empty();

    // Keep the resolved tables available while consuming declaration records.
    let declarations = std::mem::take(&mut export.declarations);
    for declaration in declarations {
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
                match check_inductive_with_installer(
                    &export,
                    &environment,
                    &block,
                    limits,
                    delta_policy,
                    installer,
                ) {
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

fn check_inductive_with_installer(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
    installer: ClosedInstaller,
) -> Result<Environment, Verdict> {
    match block.constructors.len() {
        0 => check_empty_inductive(export, environment, block, limits, delta_policy, installer),
        1 => check_two_bool_structure(export, environment, block, limits, delta_policy, installer),
        2 => check_binary_enum(export, environment, block, limits, delta_policy, installer),
        _ => Err(Verdict::Unknown),
    }
}

#[derive(Clone, Debug)]
struct DerivedConstructorSignature {
    name: NameId,
    level_params: Vec<NameId>,
    ty: ExprId,
}

#[derive(Clone, Debug)]
struct DerivedRecursorSignature {
    name: NameId,
    level_params: Vec<NameId>,
    ty: ExprId,
}

#[derive(Clone, Debug)]
struct DerivedClosedInductive {
    name: NameId,
    level_params: Vec<NameId>,
    ty: ExprId,
    constructors: Vec<DerivedConstructorSignature>,
    recursor: DerivedRecursorSignature,
}

type ClosedInstaller = fn(
    &ResolvedExport,
    &Environment,
    &DerivedClosedInductive,
    Limits,
    DeltaPolicy,
) -> Result<Environment, Verdict>;

fn install_closed_nonrecursive_inductive(
    export: &ResolvedExport,
    environment: &Environment,
    derived: &DerivedClosedInductive,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let checker = TypeChecker::with_level_substitution(
        &export.exprs,
        &export.levels,
        environment,
        parameter_substitution(&derived.level_params),
    )
    .with_delta_policy(delta_policy);
    verdict_boundary(checker.is_type(derived.ty, limits.judgment_steps))?;

    let mut staged = environment
        .extend(
            derived.name,
            ConstantDecl::inductive_type(derived.level_params.clone(), derived.ty),
        )
        .map_err(|_| Verdict::Reject)?;

    for constructor in &derived.constructors {
        let checker = TypeChecker::with_level_substitution(
            &export.exprs,
            &export.levels,
            &staged,
            parameter_substitution(&constructor.level_params),
        )
        .with_delta_policy(delta_policy);
        verdict_boundary(checker.is_type(constructor.ty, limits.judgment_steps))?;
        staged = staged
            .extend(
                constructor.name,
                ConstantDecl::constructor(constructor.level_params.clone(), constructor.ty),
            )
            .map_err(|_| Verdict::Reject)?;
    }

    let recursor = &derived.recursor;
    let checker = TypeChecker::with_level_substitution(
        &export.exprs,
        &export.levels,
        &staged,
        parameter_substitution(&recursor.level_params),
    )
    .with_delta_policy(delta_policy);
    verdict_boundary(checker.is_type(recursor.ty, limits.judgment_steps))?;

    staged
        .extend(
            recursor.name,
            ConstantDecl::recursor(recursor.level_params.clone(), recursor.ty),
        )
        .map_err(|_| Verdict::Reject)
}

#[cfg(test)]
fn install_closed_nonrecursive_inductive_legacy(
    export: &ResolvedExport,
    environment: &Environment,
    derived: &DerivedClosedInductive,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let type_checker = TypeChecker::with_level_substitution(
        &export.exprs,
        &export.levels,
        environment,
        parameter_substitution(&derived.level_params),
    )
    .with_delta_policy(delta_policy);
    verdict_boundary(type_checker.is_type(derived.ty, limits.judgment_steps))?;

    let mut staged = environment
        .extend(
            derived.name,
            ConstantDecl::inductive_type(derived.level_params.clone(), derived.ty),
        )
        .map_err(|_| Verdict::Reject)?;

    for constructor in &derived.constructors {
        let constructor_checker = TypeChecker::with_level_substitution(
            &export.exprs,
            &export.levels,
            &staged,
            parameter_substitution(&constructor.level_params),
        )
        .with_delta_policy(delta_policy);
        verdict_boundary(constructor_checker.is_type(constructor.ty, limits.judgment_steps))?;
        staged = staged
            .extend(
                constructor.name,
                ConstantDecl::constructor(constructor.level_params.clone(), constructor.ty),
            )
            .map_err(|_| Verdict::Reject)?;
    }

    let recursor = &derived.recursor;
    let recursor_checker = TypeChecker::with_level_substitution(
        &export.exprs,
        &export.levels,
        &staged,
        parameter_substitution(&recursor.level_params),
    )
    .with_delta_policy(delta_policy);
    verdict_boundary(recursor_checker.is_type(recursor.ty, limits.judgment_steps))?;
    staged
        .extend(
            recursor.name,
            ConstantDecl::recursor(recursor.level_params.clone(), recursor.ty),
        )
        .map_err(|_| Verdict::Reject)
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
    installer: ClosedInstaller,
) -> Result<Environment, Verdict> {
    let [inductive] = block.types.as_slice() else {
        return Err(Verdict::Unknown);
    };
    if !block.constructors.is_empty() {
        return Err(Verdict::Unknown);
    }

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

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if !valid_empty_recursor_metadata(export, inductive.name, recursor)
        || !is_derived_empty_recursor_type(export, inductive.name, recursor)
    {
        return Err(Verdict::Reject);
    }

    let derived = DerivedClosedInductive {
        name: inductive.name,
        level_params: inductive.level_params.clone(),
        ty: inductive.ty,
        constructors: Vec::new(),
        recursor: DerivedRecursorSignature {
            name: recursor.name,
            level_params: recursor.level_params.clone(),
            ty: recursor.ty,
        },
    };
    installer(export, environment, &derived, limits, delta_policy)
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

/// G11-001: the exact closed TwoBool structure.  This is deliberately
/// name-scoped so unrelated one-constructor inductives retain UNKNOWN.
/// Constructor and recursor authority are installed as opaque signatures only;
/// the exported rule is validated structurally but does not become an iota rule.
fn check_two_bool_structure(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
    installer: ClosedInstaller,
) -> Result<Environment, Verdict> {
    let [inductive] = block.types.as_slice() else {
        return Err(Verdict::Unknown);
    };
    let [constructor] = block.constructors.as_slice() else {
        return Err(Verdict::Unknown);
    };

    if !is_root_name(export, inductive.name, "TwoBool")
        || !is_child_name(export, constructor.name, inductive.name, "mk")
    {
        return Err(Verdict::Unknown);
    }

    let exact_type_metadata = inductive.all == [inductive.name]
        && inductive.constructors == [constructor.name]
        && !inductive.is_recursive
        && !inductive.is_reflexive
        && !inductive.is_unsafe
        && inductive.level_params.is_empty()
        && inductive.num_params == 0
        && inductive.num_indices == 0
        && inductive.num_nested == 0
        && matches!(
            export.exprs.get(inductive.ty),
            Some(Expr::Sort(level))
                if matches!(export.levels.get(*level), Some(Level::Succ(LevelId(0))))
        );
    if !exact_type_metadata {
        return Err(Verdict::Reject);
    }

    let exact_constructor_metadata = constructor.index == 0
        && constructor.inductive == inductive.name
        && !constructor.is_unsafe
        && constructor.level_params.is_empty()
        && constructor.num_fields == 2
        && constructor.num_params == 0
        && is_derived_two_bool_constructor_type(export, inductive.name, constructor.ty);
    if !exact_constructor_metadata {
        return Err(Verdict::Reject);
    }

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if !valid_two_bool_recursor_metadata(export, inductive.name, recursor)
        || !is_derived_two_bool_recursor_type(export, inductive.name, constructor.name, recursor)
        || !is_derived_two_bool_rule(export, inductive.name, constructor.name, recursor)
    {
        return Err(Verdict::Reject);
    }

    let derived = DerivedClosedInductive {
        name: inductive.name,
        level_params: inductive.level_params.clone(),
        ty: inductive.ty,
        constructors: vec![DerivedConstructorSignature {
            name: constructor.name,
            level_params: constructor.level_params.clone(),
            ty: constructor.ty,
        }],
        recursor: DerivedRecursorSignature {
            name: recursor.name,
            level_params: recursor.level_params.clone(),
            ty: recursor.ty,
        },
    };
    installer(export, environment, &derived, limits, delta_policy)
}

fn is_root_name(export: &ResolvedExport, name: NameId, expected: &str) -> bool {
    matches!(
        export.names.get(name),
        Some(Name::Str { prefix, value })
            if *prefix == NameId(0) && value == expected
    )
}

fn is_child_name(export: &ResolvedExport, name: NameId, parent: NameId, expected: &str) -> bool {
    matches!(
        export.names.get(name),
        Some(Name::Str { prefix, value })
            if *prefix == parent && value == expected
    )
}

fn is_root_named_constant(export: &ResolvedExport, expression: ExprId, expected: &str) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::Const { name, levels })
            if levels.is_empty() && is_root_name(export, *name, expected)
    )
}

fn is_derived_two_bool_constructor_type(
    export: &ResolvedExport,
    inductive: NameId,
    expression: ExprId,
) -> bool {
    let Some(Expr::Pi {
        domain: first_field,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: second_field,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };

    is_root_named_constant(export, *first_field, "Bool")
        && is_root_named_constant(export, *second_field, "Bool")
        && is_empty_constant(export, *result, inductive)
}

fn valid_two_bool_recursor_metadata(
    export: &ResolvedExport,
    inductive: NameId,
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
        && recursor.rules.len() == 1
        && is_child_name(export, recursor.name, inductive, "rec")
}

fn is_two_bool_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    universe_parameter: NameId,
) -> bool {
    let Some(Expr::Pi { domain, body }) = export.exprs.get(expression) else {
        return false;
    };
    is_empty_constant(export, *domain, inductive)
        && matches!(
            export.exprs.get(*body),
            Some(Expr::Sort(level))
                if matches!(
                    export.levels.get(*level),
                    Some(Level::Param(name)) if *name == universe_parameter
                )
        )
}

fn is_constructor_applied_to_two_fields(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
) -> bool {
    let Some(Expr::App {
        fun: partial,
        arg: second,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::App { fun, arg: first }) = export.exprs.get(*partial) else {
        return false;
    };
    is_empty_constant(export, *fun, constructor)
        && matches!(export.exprs.get(*first), Some(Expr::BVar(1)))
        && matches!(export.exprs.get(*second), Some(Expr::BVar(0)))
}

fn is_two_bool_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
) -> bool {
    let Some(Expr::Pi {
        domain: first_field,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::Pi {
        domain: second_field,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::App { fun, arg }) = export.exprs.get(*result) else {
        return false;
    };

    is_root_named_constant(export, *first_field, "Bool")
        && is_root_named_constant(export, *second_field, "Bool")
        && matches!(export.exprs.get(*fun), Some(Expr::BVar(2)))
        && is_constructor_applied_to_two_fields(export, *arg, constructor)
}

fn is_derived_two_bool_recursor_type(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    recursor: &Recursor,
) -> bool {
    let [universe_parameter] = recursor.level_params.as_slice() else {
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

    is_two_bool_motive_type(export, *motive, inductive, *universe_parameter)
        && is_two_bool_minor_type(export, *minor, constructor)
        && is_empty_constant(export, *target, inductive)
        && is_bvar_applied_to_bvar(export, *result, 2, 0)
}

fn is_bvar_applied_to_two_bvars(
    export: &ResolvedExport,
    expression: ExprId,
    function: u64,
    first: u64,
    second: u64,
) -> bool {
    let Some(Expr::App {
        fun: partial,
        arg: second_arg,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    let Some(Expr::App {
        fun,
        arg: first_arg,
    }) = export.exprs.get(*partial)
    else {
        return false;
    };
    matches!(export.exprs.get(*fun), Some(Expr::BVar(index)) if *index == function)
        && matches!(export.exprs.get(*first_arg), Some(Expr::BVar(index)) if *index == first)
        && matches!(export.exprs.get(*second_arg), Some(Expr::BVar(index)) if *index == second)
}

fn is_derived_two_bool_rule(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    recursor: &Recursor,
) -> bool {
    let [universe_parameter] = recursor.level_params.as_slice() else {
        return false;
    };
    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    if rule.constructor != constructor || rule.num_fields != 2 {
        return false;
    }

    let Some(Expr::Lam {
        domain: motive,
        body,
    }) = export.exprs.get(rule.rhs)
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
        domain: first_field,
        body,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    let Some(Expr::Lam {
        domain: second_field,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };

    is_two_bool_motive_type(export, *motive, inductive, *universe_parameter)
        && is_two_bool_minor_type(export, *minor, constructor)
        && is_root_named_constant(export, *first_field, "Bool")
        && is_root_named_constant(export, *second_field, "Bool")
        && is_bvar_applied_to_two_bvars(export, *result, 2, 1, 0)
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
    installer: ClosedInstaller,
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

    let derived = DerivedClosedInductive {
        name: inductive.name,
        level_params: inductive.level_params.clone(),
        ty: inductive.ty,
        constructors: block
            .constructors
            .iter()
            .map(|constructor| DerivedConstructorSignature {
                name: constructor.name,
                level_params: constructor.level_params.clone(),
                ty: constructor.ty,
            })
            .collect(),
        recursor: DerivedRecursorSignature {
            name: recursor.name,
            level_params: recursor.level_params.clone(),
            ty: recursor.ty,
        },
    };
    installer(export, environment, &derived, limits, delta_policy)
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

    use super::{Limits, check_export, check_export_with_policy};
    use crate::convert::DeltaPolicy;
    use crate::convert::{reset_test_conversion_calls, test_conversion_calls};
    use crate::id::NameId;
    use crate::parser::parse;
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
    fn closed_inductive_refactor_is_causally_equivalent_on_frozen_family_bank() {
        let mut bank = vec![
            include_bytes!("../evidence/residuals/G9-001/fixture.ndjson").to_vec(),
            include_bytes!("../evidence/residuals/G10-001/fixture.ndjson").to_vec(),
            include_bytes!("../evidence/residuals/G11-001/fixture.ndjson").to_vec(),
            include_bytes!("../tests/fixtures/unsupported-inductive.ndjson").to_vec(),
        ];
        bank.push(
            include_str!("../evidence/residuals/G10-001/fixture.ndjson")
                .replacen("\"cidx\":0", "\"cidx\":1", 1)
                .into_bytes(),
        );
        bank.push(
            include_str!("../evidence/residuals/G11-001/fixture.ndjson")
                .replacen(
                    "\"numFields\":2,\"numParams\":0,\"type\":24",
                    "\"numFields\":1,\"numParams\":0,\"type\":24",
                    1,
                )
                .into_bytes(),
        );

        for bytes in bank {
            let export = parse(Cursor::new(bytes)).unwrap().resolve().unwrap();
            let legacy = check_export_with_policy_and_installer(
                export.clone(),
                Limits::default(),
                DeltaPolicy::GuardedSemanticFallback,
                install_closed_nonrecursive_inductive_legacy,
            );
            let generic = check_export_with_policy_and_installer(
                export,
                Limits::default(),
                DeltaPolicy::GuardedSemanticFallback,
                install_closed_nonrecursive_inductive,
            );
            assert_eq!(generic, legacy);
        }
    }
}
