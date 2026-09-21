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
    mut export: ResolvedExport,
    limits: Limits,
    delta_policy: DeltaPolicy,
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
                match check_empty_inductive(&export, &environment, &block, limits, delta_policy) {
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

    let checker = TypeChecker::with_level_substitution(
        &export.exprs,
        &export.levels,
        environment,
        HashMap::new(),
    )
    .with_delta_policy(delta_policy);
    verdict_boundary(checker.is_type(inductive.ty, limits.judgment_steps))?;

    // Stage the type locally. Failure below never returns this environment,
    // so no recursor claim can partially extend caller authority.
    let staged = environment
        .extend(
            inductive.name,
            ConstantDecl::inductive_type(Vec::new(), inductive.ty),
        )
        .map_err(|_| Verdict::Reject)?;

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if !valid_empty_recursor_metadata(export, inductive.name, recursor)
        || !is_derived_empty_recursor_type(export, inductive.name, recursor)
    {
        return Err(Verdict::Reject);
    }

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
}
