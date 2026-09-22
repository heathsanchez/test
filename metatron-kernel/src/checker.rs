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

/// G15-001's closed internal quotient, extended by G16-001's independently
/// earned nullary law. External recognition remains name-sealed: adding this
/// variant cannot authorize any unrelated fourth product family.
#[derive(Clone, Copy)]
enum BinaryProductSortLaw {
    And,
    Prod { first: NameId, second: NameId },
    PProd { first: NameId, second: NameId },
    PUnit { level: NameId },
}

impl BinaryProductSortLaw {
    fn parameter_sort(self, export: &ResolvedExport, expression: ExprId, first: bool) -> bool {
        match self {
            Self::PUnit { .. } => false,
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
            Self::PUnit { level } => {
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
            Self::PUnit { level } => {
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
            Self::PUnit { .. } => {
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
            Self::And | Self::Prod { .. } | Self::PProd { .. } => 2,
        }
    }

    fn num_fields(self) -> u64 {
        self.num_params()
    }

    fn validates_type(self, export: &ResolvedExport, expression: ExprId) -> bool {
        match self {
            Self::PUnit { .. } => self.result_sort(export, expression),
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
            || !self.law.validates_constructor(
                export,
                self.constructor.ty,
                self.inductive.name,
            )
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
    let Some(Expr::Pi { domain: motive, body }) = export.exprs.get(recursor.ty) else {
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
    let Some(Expr::Lam { domain: motive, body }) = export.exprs.get(rule.rhs) else {
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
    law.constant(export, *argument, inductive)
        && is_sort_parameter(export, *result, motive_level)
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
