use std::collections::HashMap;

use crate::convert::DeltaPolicy;
use crate::environment::{
    BoolPrimitives, ConstantDecl, Environment, NatOperation, NatPrimitives, QuotPrimitives,
};
use crate::id::NameId;
use crate::id::{ExprId, LevelId};
use crate::inductive::{ClosedNonrecursiveDerivation, DerivedSignature, OpaqueInductiveKind};
use crate::judgment::Judgment;
use crate::level::LevelTerm;
use crate::machine::{
    ProjectionFieldType, ProjectionSpec, RecursorReduction, RecursorRule, Transparency,
};
use crate::parser::ResolvedExport;
use crate::syntax::{
    Constructor, Declaration, Expr, InductiveBlock, Level, Name, QuotKind, Recursor,
};
use crate::typecheck::{TypeChecker, TypeValue};
use crate::value::{EnvFrame, FreeId, NeutralHead, Value};
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
    let has_unqualified_string_literal = export
        .exprs
        .values()
        .any(|expression| matches!(expression, Expr::StrLit(_)));
    let verdict = check_export_with_policy(export, limits, DeltaPolicy::GuardedSemanticFallback);
    if has_unqualified_string_literal && matches!(verdict, Verdict::Accept | Verdict::Reject) {
        Verdict::Unknown
    } else {
        verdict
    }
}

fn check_export_with_policy(
    mut export: ResolvedExport,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Verdict {
    if let Some(verdict) = crate::capability::execute(&export) {
        return verdict;
    }

    let mut environment = Environment::empty();

    // Keep the resolved tables available while consuming declaration records.
    let declarations = std::mem::take(&mut export.declarations);
    for declaration in declarations {
        #[cfg(feature = "diagnostics")]
        crate::diagnostics::declaration();
        let level_parameters = match &declaration {
            Declaration::Axiom { level_params, .. }
            | Declaration::Definition { level_params, .. }
            | Declaration::Theorem { level_params, .. }
            | Declaration::Quot { level_params, .. } => Some(level_params.as_slice()),
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
            Declaration::Quot {
                name,
                level_params,
                ty,
                kind,
            } => {
                match check_quot_declaration(
                    &export,
                    &environment,
                    name,
                    &level_params,
                    ty,
                    kind,
                    limits,
                    delta_policy,
                ) {
                    Ok(extended) => {
                        environment = extended;
                        continue;
                    }
                    Err(verdict) => return verdict,
                }
            }
            Declaration::Inductive(block) => {
                match check_inductive(&export, &environment, &block, limits, delta_policy) {
                    Ok(extended) => {
                        environment = extended;
                        continue;
                    }
                    Err(verdict) => {
                        if std::env::var_os("NUCLEUS_TRACE_RESIDUAL").is_some() {
                            eprintln!("NUCLEUS_INDUCTIVE_EXIT:{:?}", verdict);
                        }
                        return verdict;
                    }
                }
            }
            Declaration::Unsupported { .. } => {
                if std::env::var_os("NUCLEUS_TRACE_RESIDUAL").is_some() {
                    eprintln!("NUCLEUS_RESIDUAL:unsupported-declaration");
                }
                return Verdict::Unknown;
            }
        };

        let Ok(extended) = environment.extend(name, established) else {
            return Verdict::Reject;
        };
        environment = extended;

        // Lean's Nat-literal kernel extension gives exact native meaning to
        // these standard root definitions.  Authority is installed only after
        // the definition itself has passed ordinary Nucleus type checking and
        // exact Nat authority is already present.
        if let Some(nat) = environment.nat_primitives().cloned() {
            let operation = if name_is_child_str(&export, name, nat.type_name, "add") {
                Some(NatOperation::Add)
            } else if name_is_child_str(&export, name, nat.type_name, "sub") {
                Some(NatOperation::Sub)
            } else if name_is_child_str(&export, name, nat.type_name, "ble") {
                Some(NatOperation::Ble)
            } else {
                None
            };
            if let Some(operation) = operation {
                let Ok(extended) = environment.install_nat_operation(name, operation) else {
                    return Verdict::Reject;
                };
                environment = extended;
            }
        }
    }

    Verdict::Accept
}

fn quotient_parent(export: &ResolvedExport, name: NameId, suffix: &str) -> Option<NameId> {
    match export.names.get(name) {
        Some(Name::Str { prefix, value })
            if value == suffix && name_is_root_str(export, *prefix, "Quot") =>
        {
            Some(*prefix)
        }
        _ => None,
    }
}

fn quotient_child(export: &ResolvedExport, parent: NameId, suffix: &str) -> Option<NameId> {
    export.names.iter_raw().find_map(|(raw, name)| match name {
        Name::Str { prefix, value } if *prefix == parent && value == suffix => Some(NameId(raw)),
        _ => None,
    })
}

fn is_quot_relation_type(export: &ResolvedExport, expression: ExprId, carrier: u64) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [left, right] = domains.as_slice() else {
        return false;
    };
    is_bvar(export, *left, carrier)
        && is_bvar(export, *right, carrier + 1)
        && is_prop_sort(export, result)
}

fn is_quot_application(
    export: &ResolvedExport,
    expression: ExprId,
    quotient: NameId,
    level: NameId,
    carrier: u64,
    relation: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 2
        && is_unary_polymorphic_constant(export, head, quotient, level)
        && are_bvars(export, &arguments, &[carrier, relation])
}

fn is_quot_mk_application(
    export: &ResolvedExport,
    expression: ExprId,
    mk: NameId,
    level: NameId,
    carrier: u64,
    relation: u64,
    value: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 3
        && is_unary_polymorphic_constant(export, head, mk, level)
        && are_bvars(export, &arguments, &[carrier, relation, value])
}

fn is_quot_type(export: &ResolvedExport, expression: ExprId, level: NameId) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [carrier, relation] = domains.as_slice() else {
        return false;
    };
    is_sort_parameter(export, *carrier, level)
        && is_quot_relation_type(export, *relation, 0)
        && is_sort_parameter(export, result, level)
}

fn is_quot_mk_type(
    export: &ResolvedExport,
    expression: ExprId,
    quotient: NameId,
    level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [carrier, relation, value] = domains.as_slice() else {
        return false;
    };
    is_sort_parameter(export, *carrier, level)
        && is_quot_relation_type(export, *relation, 0)
        && is_bvar(export, *value, 1)
        && is_quot_application(export, result, quotient, level, 2, 1)
}

fn is_quot_function_type(export: &ResolvedExport, expression: ExprId) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 1) else {
        return false;
    };
    matches!(domains.as_slice(), [domain] if is_bvar(export, *domain, 2))
        && is_bvar(export, result, 1)
}

fn is_quot_lift_proof_type(
    export: &ResolvedExport,
    expression: ExprId,
    value_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [left, right, related] = domains.as_slice() else {
        return false;
    };
    if !is_bvar(export, *left, 3)
        || !is_bvar(export, *right, 4)
        || !is_binary_bvar_application(export, *related, 4, 1, 0)
    {
        return false;
    }
    let (head, arguments) = application_spine(export, result);
    let [carrier, lhs, rhs] = arguments.as_slice() else {
        return false;
    };
    let Some(Expr::Const { name, levels }) = export.exprs.get(head) else {
        return false;
    };
    levels.len() == 1
        && name_is_root_str(export, *name, "Eq")
        && matches!(
            export.levels.get(levels[0]),
            Some(Level::Param(parameter)) if *parameter == value_level
        )
        && is_bvar(export, *carrier, 4)
        && is_bvar_application(export, *lhs, 3, 2)
        && is_bvar_application(export, *rhs, 3, 1)
}

fn is_quot_lift_type(
    export: &ResolvedExport,
    expression: ExprId,
    quotient: NameId,
    quotient_level: NameId,
    value_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 6) else {
        return false;
    };
    let [carrier, relation, value_type, function, proof, target] = domains.as_slice() else {
        return false;
    };
    is_sort_parameter(export, *carrier, quotient_level)
        && is_quot_relation_type(export, *relation, 0)
        && is_sort_parameter(export, *value_type, value_level)
        && is_quot_function_type(export, *function)
        && is_quot_lift_proof_type(export, *proof, value_level)
        && is_quot_application(export, *target, quotient, quotient_level, 4, 3)
        && is_bvar(export, result, 3)
}

fn is_quot_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    quotient: NameId,
    level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 1) else {
        return false;
    };
    matches!(
        domains.as_slice(),
        [target] if is_quot_application(export, *target, quotient, level, 1, 0)
    ) && is_prop_sort(export, result)
}

fn is_quot_ind_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    mk: NameId,
    level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 1) else {
        return false;
    };
    let [value] = domains.as_slice() else {
        return false;
    };
    let Some(Expr::App { fun: motive, arg }) = export.exprs.get(result) else {
        return false;
    };
    is_bvar(export, *value, 2)
        && is_bvar(export, *motive, 1)
        && is_quot_mk_application(export, *arg, mk, level, 3, 2, 0)
}

fn is_quot_ind_type(
    export: &ResolvedExport,
    expression: ExprId,
    quotient: NameId,
    mk: NameId,
    level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 5) else {
        return false;
    };
    let [carrier, relation, motive, minor, target] = domains.as_slice() else {
        return false;
    };
    is_sort_parameter(export, *carrier, level)
        && is_quot_relation_type(export, *relation, 0)
        && is_quot_motive_type(export, *motive, quotient, level)
        && is_quot_ind_minor_type(export, *minor, mk, level)
        && is_quot_application(export, *target, quotient, level, 3, 2)
        && is_bvar_application(export, result, 2, 0)
}

#[allow(clippy::too_many_arguments)]
fn check_quot_declaration(
    export: &ResolvedExport,
    environment: &Environment,
    name: NameId,
    level_params: &[NameId],
    ty: ExprId,
    kind: QuotKind,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let exact = match kind {
        QuotKind::Type => {
            matches!(level_params, [level]
                if name_is_root_str(export, name, "Quot")
                    && is_quot_type(export, ty, *level))
        }
        QuotKind::Ctor => {
            let Some(quotient) = quotient_parent(export, name, "mk") else {
                return Err(Verdict::Reject);
            };
            matches!(level_params, [level]
                if environment.get(quotient).is_some()
                    && is_quot_mk_type(export, ty, quotient, *level))
        }
        QuotKind::Lift => {
            let Some(quotient) = quotient_parent(export, name, "lift") else {
                return Err(Verdict::Reject);
            };
            matches!(level_params, [quotient_level, value_level]
            if quotient_level != value_level
                && environment.get(quotient).is_some()
                && is_quot_lift_type(
                    export,
                    ty,
                    quotient,
                    *quotient_level,
                    *value_level,
                ))
        }
        QuotKind::Ind => {
            let Some(quotient) = quotient_parent(export, name, "ind") else {
                return Err(Verdict::Reject);
            };
            let Some(mk) = quotient_child(export, quotient, "mk") else {
                return Err(Verdict::Reject);
            };
            matches!(level_params, [level]
                if environment.get(quotient).is_some()
                    && environment.get(mk).is_some()
                    && is_quot_ind_type(export, ty, quotient, mk, *level))
        }
    };
    if !exact {
        return Err(Verdict::Reject);
    }

    let checker = TypeChecker::with_level_substitution(
        &export.exprs,
        &export.levels,
        environment,
        parameter_substitution(level_params),
    )
    .with_delta_policy(delta_policy);
    verdict_boundary(checker.is_type(ty, limits.judgment_steps))?;
    let extended = environment
        .extend(name, ConstantDecl::theorem(level_params.to_vec(), ty))
        .map_err(|_| Verdict::Reject)?;

    if kind == QuotKind::Ind {
        let quotient = quotient_parent(export, name, "ind").ok_or(Verdict::Reject)?;
        let mk = quotient_child(export, quotient, "mk").ok_or(Verdict::Reject)?;
        let lift = quotient_child(export, quotient, "lift").ok_or(Verdict::Reject)?;
        extended
            .install_quot_primitives(QuotPrimitives {
                type_name: quotient,
                mk,
                lift,
                ind: name,
            })
            .map_err(|_| Verdict::Reject)
    } else {
        Ok(extended)
    }
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

fn owned_single_type_recursor_metadata_is_definitely_malformed(
    export: &ResolvedExport,
    block: &InductiveBlock,
) -> bool {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return false;
    };

    // G26-001's earned negative envelope is intentionally narrower than
    // generic recursor validation. Broader indexed/parameterized/recursive
    // families remain UNKNOWN until separately earned.
    if inductive.num_params != 0
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || !inductive.level_params.is_empty()
        || constructor.num_params != 0
        || constructor.num_fields != 0
        || constructor.is_unsafe
        || !constructor.level_params.is_empty()
        || recursor.is_unsafe
        || recursor.all != [inductive.name]
        || !name_is_child_str(export, recursor.name, inductive.name, "rec")
    {
        return false;
    }

    !recursor_metadata_admissible(
        export,
        inductive,
        &block.constructors,
        recursor,
        recursor.k,
        true,
    )
}

fn check_inductive(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    // G26-001: negative-only recursor coherence. A single safe inductive
    // that explicitly owns a .rec declaration cannot advertise impossible
    // motive/minor/rule cardinalities. This grants no positive family
    // authority; well-formed but unsupported recursors remain UNKNOWN.
    if owned_single_type_recursor_metadata_is_definitely_malformed(export, block) {
        return Err(Verdict::Reject);
    }

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
        && name_is_root_str(export, inductive.name, "Acc")
    {
        return check_exact_acc(export, environment, block, limits, delta_policy);
    }

    if let [inductive] = block.types.as_slice()
        && name_is_root_str(export, inductive.name, "List")
    {
        return check_exact_list(export, environment, block, limits, delta_policy);
    }

    if let [inductive] = block.types.as_slice()
        && environment
            .nat_primitives()
            .is_some_and(|nat| name_is_child_str(export, inductive.name, nat.type_name, "le"))
    {
        return check_exact_nat_le(export, environment, block, limits, delta_policy);
    }

    if let [inductive] = block.types.as_slice()
        && (name_is_root_str(export, inductive.name, "N")
            || name_is_root_str(export, inductive.name, "Nat"))
    {
        return check_exact_nat(export, environment, block, limits, delta_policy);
    }

    if let [inductive] = block.types.as_slice()
        && name_is_root_str(export, inductive.name, "RBTree")
    {
        return check_exact_rbtree(export, environment, block, limits, delta_policy);
    }

    if exact_closed_binary_tree_candidate(export, block) {
        return check_exact_closed_binary_tree(export, environment, block, limits, delta_policy);
    }

    if exact_closed_reflexive_tree_candidate(export, block) {
        return check_exact_closed_reflexive_tree(export, environment, block, limits, delta_policy);
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
    if name_is_root_str(export, inductive.name, "SortElimProp2") {
        check_exact_sort_elim_prop2(export, environment, block, limits, delta_policy)
    } else if name_is_root_str(export, inductive.name, "SortElimProp") {
        check_exact_sort_elim_prop(export, environment, block, limits, delta_policy)
    } else if name_is_root_str(export, inductive.name, "NewSingleton") {
        check_exact_new_singleton(export, environment, block, limits, delta_policy)
    } else if name_is_root_str(export, inductive.name, "Exists") {
        check_exact_exists_family(export, environment, block, limits, delta_policy)
    } else if name_is_root_str(export, inductive.name, "And") {
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
    } else if name_is_root_str(export, inductive.name, "OfNat") {
        check_exact_ofnat(export, environment, block, limits, delta_policy)
    } else if name_is_root_str(export, inductive.name, "TwoBool") {
        check_twobool_structure(export, environment, block, limits, delta_policy)
    } else if name_is_root_str(export, inductive.name, "reduceCtorParam") {
        check_conversion_lifted_unary_recursive(export, environment, block, limits, delta_policy)
    } else if generic_closed_prop_singleton_candidate(block) {
        check_generic_closed_prop_singleton(export, environment, block, limits, delta_policy)
    } else if generic_unary_structure_candidate(export, block) {
        check_generic_unary_structure(export, environment, block, limits, delta_policy)
    } else if generic_parameterized_nullary_candidate(export, block) {
        check_generic_parameterized_nullary(export, environment, block, limits, delta_policy)
    } else if inductive.num_params == 1
        && inductive.num_indices == 0
        && inductive.num_nested == 0
        && inductive.is_recursive
        && inductive.is_reflexive
        && !inductive.is_unsafe
    {
        check_conversion_lifted_reflexive_unary(export, environment, block, limits, delta_policy)
    } else if unary_field_universe_candidate(export, block) {
        check_unary_field_universe_inductive(export, environment, block, limits, delta_policy)
    } else if matches!(
        check_unrecognized_single_constructor_coherence(export, block),
        Err(Verdict::Reject)
    ) {
        Err(Verdict::Reject)
    } else if generic_field_structure_candidate(export, block) {
        check_generic_field_structure(export, environment, block, limits, delta_policy)
    } else {
        check_unrecognized_single_constructor_coherence(export, block)
    }
}

/// Exact built-in-shaped OfNat structure used by the Nat literal extension.
///
/// The exported recursor is reconstructed from the declaration; only after the
/// telescope, constructor, motive/minor and rule body agree do we install the
/// single field projection. No generic structure authority is granted here.
fn check_exact_ofnat(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };
    if inductive.num_params != 2
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || constructor.is_unsafe
        || recursor.is_unsafe
    {
        return Err(Verdict::Unknown);
    }
    let [carrier_level] = inductive.level_params.as_slice() else {
        return Err(Verdict::Reject);
    };
    if inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || constructor.index != 0
        || constructor.inductive != inductive.name
        || constructor.level_params != [*carrier_level]
        || constructor.num_params != 2
        || constructor.num_fields != 1
        || !name_is_child_str(export, constructor.name, inductive.name, "mk")
        || !ofnat_type(export, inductive.ty, *carrier_level)
        || !ofnat_constructor_type(
            export,
            constructor.ty,
            inductive.name,
            constructor.name,
            *carrier_level,
        )
    {
        return Err(Verdict::Reject);
    }
    let [motive_level, declared_carrier] = recursor.level_params.as_slice() else {
        return Err(Verdict::Reject);
    };
    if *declared_carrier != *carrier_level
        || *motive_level == *carrier_level
        || !recursor_metadata_admissible(
            export,
            inductive,
            &block.constructors,
            recursor,
            false,
            true,
        )
        || !ofnat_recursor_type(
            export,
            recursor.ty,
            inductive.name,
            constructor.name,
            *carrier_level,
            *motive_level,
        )
        || !ofnat_recursor_rule(
            export,
            recursor,
            inductive.name,
            constructor.name,
            *carrier_level,
            *motive_level,
        )
    {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_polymorphic_type(inductive.name, &inductive.level_params, inductive.ty),
            derived_constructor(constructor),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    derivation
        .finish()
        .install_projection_spec(
            inductive.name,
            ProjectionSpec {
                constructor: constructor.name,
                num_params: 2,
                field_types: vec![ProjectionFieldType::Parameter(0)],
            },
        )
        .map_err(|_| Verdict::Reject)
}

fn is_nat_constant(export: &ResolvedExport, expression: ExprId) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::Const { name, levels })
            if levels.is_empty() && name_is_root_str(export, *name, "Nat")
    )
}

fn ofnat_application(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    carrier_level: NameId,
    carrier: u64,
    numeral: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 2
        && is_unary_polymorphic_constant(export, head, inductive, carrier_level)
        && are_bvars(export, &arguments, &[carrier, numeral])
}

fn ofnat_constructor_application(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    carrier_level: NameId,
    carrier: u64,
    numeral: u64,
    field: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 3
        && is_unary_polymorphic_constant(export, head, constructor, carrier_level)
        && are_bvars(export, &arguments, &[carrier, numeral, field])
}

fn ofnat_type(export: &ResolvedExport, expression: ExprId, carrier_level: NameId) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [carrier, numeral] = domains.as_slice() else {
        return false;
    };
    is_sort_succ_parameter(export, *carrier, carrier_level)
        && is_nat_constant(export, *numeral)
        && is_sort_succ_parameter(export, result, carrier_level)
}

fn ofnat_constructor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    _constructor: NameId,
    carrier_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [carrier, numeral, field] = domains.as_slice() else {
        return false;
    };
    is_sort_succ_parameter(export, *carrier, carrier_level)
        && is_nat_constant(export, *numeral)
        && is_bvar(export, *field, 1)
        && ofnat_application(export, result, inductive, carrier_level, 2, 1)
}

fn ofnat_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    carrier_level: NameId,
    motive_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 1) else {
        return false;
    };
    let [target] = domains.as_slice() else {
        return false;
    };
    ofnat_application(export, *target, inductive, carrier_level, 1, 0)
        && is_sort_parameter(export, result, motive_level)
}

fn ofnat_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    carrier_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 1) else {
        return false;
    };
    let [field] = domains.as_slice() else {
        return false;
    };
    if !is_bvar(export, *field, 2) {
        return false;
    }
    let Some(Expr::App {
        fun: motive,
        arg: constructed,
    }) = export.exprs.get(result)
    else {
        return false;
    };
    is_bvar(export, *motive, 1)
        && ofnat_constructor_application(export, *constructed, constructor, carrier_level, 3, 2, 0)
}

fn ofnat_recursor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    constructor: NameId,
    carrier_level: NameId,
    motive_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 5) else {
        return false;
    };
    let [carrier, numeral, motive, minor, target] = domains.as_slice() else {
        return false;
    };
    is_sort_succ_parameter(export, *carrier, carrier_level)
        && is_nat_constant(export, *numeral)
        && ofnat_motive_type(export, *motive, inductive, carrier_level, motive_level)
        && ofnat_minor_type(export, *minor, constructor, carrier_level)
        && ofnat_application(export, *target, inductive, carrier_level, 3, 2)
        && is_bvar_application(export, result, 2, 0)
}

fn ofnat_recursor_rule(
    export: &ResolvedExport,
    recursor: &Recursor,
    inductive: NameId,
    constructor: NameId,
    carrier_level: NameId,
    motive_level: NameId,
) -> bool {
    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    if rule.constructor != constructor || rule.num_fields != 1 {
        return false;
    }
    let Some((domains, result)) = lam_spine(export, rule.rhs, 5) else {
        return false;
    };
    let [carrier, numeral, motive, minor, field] = domains.as_slice() else {
        return false;
    };
    is_sort_succ_parameter(export, *carrier, carrier_level)
        && is_nat_constant(export, *numeral)
        && ofnat_motive_type(export, *motive, inductive, carrier_level, motive_level)
        && ofnat_minor_type(export, *minor, constructor, carrier_level)
        && is_bvar(export, *field, 3)
        && is_bvar_application(export, result, 1, 0)
}

/// G30-001: exact indexed Prop family with one constructor field hidden
/// behind a reducible identity in an index.
///
/// This is deliberately *not* a relaxation of G29 large elimination.  The
/// recursor must be Prop-only (no motive universe parameter), so the checker
/// admits ordinary Prop elimination even though the first field is not
/// directly recoverable from the result indices without reduction.
fn check_exact_sort_elim_prop2(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };

    if inductive.num_nested != 0
        || inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || constructor.is_unsafe
        || recursor.is_unsafe
    {
        return Err(Verdict::Unknown);
    }

    if inductive.num_params != 1
        || inductive.num_indices != 2
        || !inductive.level_params.is_empty()
        || inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || !sort_elim_prop_inductive_type(export, inductive.ty)
        || constructor.index != 0
        || constructor.inductive != inductive.name
        || constructor.num_params != 1
        || constructor.num_fields != 2
        || !constructor.level_params.is_empty()
        || !name_is_child_str(export, constructor.name, inductive.name, "mk")
        || !sort_elim_prop2_constructor_type(export, constructor.ty, inductive.name)
    {
        return Err(Verdict::Reject);
    }

    if !recursor.level_params.is_empty()
        || !recursor_metadata_admissible(
            export,
            inductive,
            &block.constructors,
            recursor,
            false,
            true,
        )
        || !sort_elim_prop2_recursor_type(export, recursor.ty, inductive.name, constructor.name)
        || !sort_elim_prop2_recursor_rule(export, recursor, inductive.name, constructor.name)
    {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_type(inductive.name, inductive.ty),
            derived_constructor(constructor),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    Ok(derivation.finish())
}

fn is_bool_identity_application(export: &ResolvedExport, expression: ExprId, binder: u64) -> bool {
    let (head, arguments) = application_spine(export, expression);
    let [carrier, value] = arguments.as_slice() else {
        return false;
    };
    let Some(Expr::Const { name, levels }) = export.exprs.get(head) else {
        return false;
    };
    matches!(
        levels.as_slice(),
        [level]
            if matches!(
                export.levels.get(*level),
                Some(Level::Succ(inner))
                    if matches!(export.levels.get(*inner), Some(Level::Zero))
            )
    ) && name_is_root_str(export, *name, "id")
        && is_bool_constant(export, *carrier)
        && is_bvar(export, *value, binder)
}

fn sort_elim_prop2_constructor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [parameter, first_field, second_field] = domains.as_slice() else {
        return false;
    };
    if !is_bool_constant(export, *parameter)
        || !is_bool_constant(export, *first_field)
        || !is_bool_constant(export, *second_field)
    {
        return false;
    }
    let (head, arguments) = application_spine(export, result);
    let [family_parameter, first_index, second_index] = arguments.as_slice() else {
        return false;
    };
    is_empty_constant(export, head, inductive)
        && is_bvar(export, *family_parameter, 2)
        && is_bvar(export, *first_index, 0)
        && is_bool_identity_application(export, *second_index, 1)
}

fn sort_elim_prop2_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [first_index, second_index, target] = domains.as_slice() else {
        return false;
    };
    is_bool_constant(export, *first_index)
        && is_bool_constant(export, *second_index)
        && sort_elim_prop_application(export, *target, inductive, [2, 1, 0])
        && is_prop_sort(export, result)
}

fn sort_elim_prop2_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [first_field, second_field] = domains.as_slice() else {
        return false;
    };
    if !is_bool_constant(export, *first_field) || !is_bool_constant(export, *second_field) {
        return false;
    }
    let (motive, arguments) = application_spine(export, result);
    let [first_index, second_index, target] = arguments.as_slice() else {
        return false;
    };
    is_bvar(export, motive, 2)
        && is_bvar(export, *first_index, 0)
        && is_bool_identity_application(export, *second_index, 1)
        && sort_elim_prop_constructor_application(export, *target, constructor, [3, 1, 0])
}

fn sort_elim_prop2_recursor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    constructor: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 6) else {
        return false;
    };
    let [parameter, motive, minor, first_index, second_index, target] = domains.as_slice() else {
        return false;
    };
    if !is_bool_constant(export, *parameter)
        || !sort_elim_prop2_motive_type(export, *motive, inductive)
        || !sort_elim_prop2_minor_type(export, *minor, constructor)
        || !is_bool_constant(export, *first_index)
        || !is_bool_constant(export, *second_index)
        || !sort_elim_prop_application(export, *target, inductive, [4, 1, 0])
    {
        return false;
    }
    let (head, arguments) = application_spine(export, result);
    arguments.len() == 3 && is_bvar(export, head, 4) && are_bvars(export, &arguments, &[2, 1, 0])
}

fn sort_elim_prop2_recursor_rule(
    export: &ResolvedExport,
    recursor: &Recursor,
    inductive: NameId,
    constructor: NameId,
) -> bool {
    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    let Some((domains, result)) = lam_spine(export, rule.rhs, 5) else {
        return false;
    };
    let [parameter, motive, minor, first_field, second_field] = domains.as_slice() else {
        return false;
    };
    if !is_bool_constant(export, *parameter)
        || !sort_elim_prop2_motive_type(export, *motive, inductive)
        || !sort_elim_prop2_minor_type(export, *minor, constructor)
        || !is_bool_constant(export, *first_field)
        || !is_bool_constant(export, *second_field)
    {
        return false;
    }
    let (head, arguments) = application_spine(export, result);
    arguments.len() == 2 && is_bvar(export, head, 2) && are_bvars(export, &arguments, &[1, 0])
}

/// G29-001: exact indexed Prop family whose constructor data are
/// recoverable directly from the result indices.
///
/// This is the first qualified large-elimination rule for an indexed Prop.
/// The external envelope remains name-sealed to `SortElimProp`.  The two
/// constructor fields must occur as bare result indices (here in swapped
/// order); no conversion is used to recover them and no generic indexed-Prop
/// elimination authority is installed.
fn check_exact_sort_elim_prop(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };

    if inductive.num_nested != 0
        || inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || constructor.is_unsafe
        || recursor.is_unsafe
    {
        return Err(Verdict::Unknown);
    }

    if inductive.num_params != 1
        || inductive.num_indices != 2
        || !inductive.level_params.is_empty()
        || inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || !sort_elim_prop_inductive_type(export, inductive.ty)
        || constructor.index != 0
        || constructor.inductive != inductive.name
        || constructor.num_params != 1
        || constructor.num_fields != 2
        || !constructor.level_params.is_empty()
        || !name_is_child_str(export, constructor.name, inductive.name, "mk")
        || !sort_elim_prop_constructor_type(export, constructor.ty, inductive.name)
    {
        return Err(Verdict::Reject);
    }

    let [motive_level] = recursor.level_params.as_slice() else {
        return Err(Verdict::Reject);
    };
    if !recursor_metadata_admissible(
        export,
        inductive,
        &block.constructors,
        recursor,
        false,
        true,
    ) || !sort_elim_prop_recursor_type(
        export,
        recursor.ty,
        inductive.name,
        constructor.name,
        *motive_level,
    ) || !sort_elim_prop_recursor_rule(
        export,
        recursor,
        inductive.name,
        constructor.name,
        *motive_level,
    ) {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_type(inductive.name, inductive.ty),
            derived_constructor(constructor),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    Ok(derivation.finish())
}

fn is_bool_constant(export: &ResolvedExport, expression: ExprId) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::Const { name, levels })
            if levels.is_empty() && name_is_root_str(export, *name, "Bool")
    )
}

fn sort_elim_prop_application(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    binders: [u64; 3],
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 3
        && is_empty_constant(export, head, inductive)
        && are_bvars(export, &arguments, &binders)
}

fn sort_elim_prop_constructor_application(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    binders: [u64; 3],
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 3
        && is_empty_constant(export, head, constructor)
        && are_bvars(export, &arguments, &binders)
}

fn sort_elim_prop_inductive_type(export: &ResolvedExport, expression: ExprId) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [parameter, first_index, second_index] = domains.as_slice() else {
        return false;
    };
    is_bool_constant(export, *parameter)
        && is_bool_constant(export, *first_index)
        && is_bool_constant(export, *second_index)
        && is_prop_sort(export, result)
}

fn sort_elim_prop_constructor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [parameter, first_field, second_field] = domains.as_slice() else {
        return false;
    };
    is_bool_constant(export, *parameter)
        && is_bool_constant(export, *first_field)
        && is_bool_constant(export, *second_field)
        && sort_elim_prop_application(export, result, inductive, [2, 0, 1])
}

fn sort_elim_prop_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    motive_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [first_index, second_index, target] = domains.as_slice() else {
        return false;
    };
    is_bool_constant(export, *first_index)
        && is_bool_constant(export, *second_index)
        && sort_elim_prop_application(export, *target, inductive, [2, 1, 0])
        && is_sort_parameter(export, result, motive_level)
}

fn sort_elim_prop_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [first_field, second_field] = domains.as_slice() else {
        return false;
    };
    if !is_bool_constant(export, *first_field) || !is_bool_constant(export, *second_field) {
        return false;
    }
    let (motive, arguments) = application_spine(export, result);
    arguments.len() == 3
        && is_bvar(export, motive, 2)
        && are_bvars(export, &arguments[..2], &[0, 1])
        && sort_elim_prop_constructor_application(export, arguments[2], constructor, [3, 1, 0])
}

fn sort_elim_prop_recursor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    constructor: NameId,
    motive_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 6) else {
        return false;
    };
    let [parameter, motive, minor, first_index, second_index, target] = domains.as_slice() else {
        return false;
    };
    if !is_bool_constant(export, *parameter)
        || !sort_elim_prop_motive_type(export, *motive, inductive, motive_level)
        || !sort_elim_prop_minor_type(export, *minor, constructor)
        || !is_bool_constant(export, *first_index)
        || !is_bool_constant(export, *second_index)
        || !sort_elim_prop_application(export, *target, inductive, [4, 1, 0])
    {
        return false;
    }
    let (head, arguments) = application_spine(export, result);
    arguments.len() == 3 && is_bvar(export, head, 4) && are_bvars(export, &arguments, &[2, 1, 0])
}

fn sort_elim_prop_recursor_rule(
    export: &ResolvedExport,
    recursor: &Recursor,
    inductive: NameId,
    constructor: NameId,
    motive_level: NameId,
) -> bool {
    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    let Some((domains, result)) = lam_spine(export, rule.rhs, 5) else {
        return false;
    };
    let [parameter, motive, minor, first_field, second_field] = domains.as_slice() else {
        return false;
    };
    if !is_bool_constant(export, *parameter)
        || !sort_elim_prop_motive_type(export, *motive, inductive, motive_level)
        || !sort_elim_prop_minor_type(export, *minor, constructor)
        || !is_bool_constant(export, *first_field)
        || !is_bool_constant(export, *second_field)
    {
        return false;
    }
    let (head, arguments) = application_spine(export, result);
    arguments.len() == 2 && is_bvar(export, head, 2) && are_bvars(export, &arguments, &[1, 0])
}

/// G28-001: exact nullary singleton Type plus its first qualified
/// computation rule.  Recognition is name-sealed to `NewSingleton`; the
/// executable rule is installed only after type, constructor, recursor, and
/// exported rule shape have all been independently checked.
fn expression_matches_lift(
    export: &ResolvedExport,
    original: ExprId,
    lifted: ExprId,
    cutoff: u64,
    amount: u64,
) -> bool {
    let (Some(left), Some(right)) = (export.exprs.get(original), export.exprs.get(lifted)) else {
        return false;
    };
    match (left, right) {
        (Expr::BVar(left), Expr::BVar(right)) => {
            *right
                == if *left >= cutoff {
                    left.saturating_add(amount)
                } else {
                    *left
                }
        }
        (Expr::NatLit(left), Expr::NatLit(right)) => left == right,
        (Expr::StrLit(left), Expr::StrLit(right)) => left == right,
        (Expr::Sort(left), Expr::Sort(right)) => left == right,
        (
            Expr::Const {
                name: left_name,
                levels: left_levels,
            },
            Expr::Const {
                name: right_name,
                levels: right_levels,
            },
        ) => left_name == right_name && left_levels == right_levels,
        (
            Expr::App {
                fun: left_fun,
                arg: left_arg,
            },
            Expr::App {
                fun: right_fun,
                arg: right_arg,
            },
        ) => {
            expression_matches_lift(export, *left_fun, *right_fun, cutoff, amount)
                && expression_matches_lift(export, *left_arg, *right_arg, cutoff, amount)
        }
        (
            Expr::Lam {
                domain: left_domain,
                body: left_body,
            },
            Expr::Lam {
                domain: right_domain,
                body: right_body,
            },
        )
        | (
            Expr::Pi {
                domain: left_domain,
                body: left_body,
            },
            Expr::Pi {
                domain: right_domain,
                body: right_body,
            },
        ) => {
            expression_matches_lift(export, *left_domain, *right_domain, cutoff, amount)
                && expression_matches_lift(
                    export,
                    *left_body,
                    *right_body,
                    cutoff.saturating_add(1),
                    amount,
                )
        }
        (
            Expr::Let {
                ty: left_ty,
                value: left_value,
                body: left_body,
            },
            Expr::Let {
                ty: right_ty,
                value: right_value,
                body: right_body,
            },
        ) => {
            expression_matches_lift(export, *left_ty, *right_ty, cutoff, amount)
                && expression_matches_lift(export, *left_value, *right_value, cutoff, amount)
                && expression_matches_lift(
                    export,
                    *left_body,
                    *right_body,
                    cutoff.saturating_add(1),
                    amount,
                )
        }
        (
            Expr::Proj {
                type_name: left_type,
                index: left_index,
                structure: left_structure,
            },
            Expr::Proj {
                type_name: right_type,
                index: right_index,
                structure: right_structure,
            },
        ) => {
            left_type == right_type
                && left_index == right_index
                && expression_matches_lift(
                    export,
                    *left_structure,
                    *right_structure,
                    cutoff,
                    amount,
                )
        }
        _ => false,
    }
}

fn generic_unary_structure_recursor_shape(
    export: &ResolvedExport,
    inductive: &crate::syntax::InductiveType,
    constructor: &Constructor,
    recursor: &Recursor,
) -> bool {
    let (Ok(p), Ok(fields)) = (
        usize::try_from(inductive.num_params),
        usize::try_from(constructor.num_fields),
    ) else {
        return false;
    };
    let Some((ctor_domains, _)) = pi_spine(export, constructor.ty, p + fields) else {
        return false;
    };
    let ctor_fields = &ctor_domains[p..];

    let Some((domains, result)) = pi_spine(export, recursor.ty, p + 3) else {
        return false;
    };
    let params = &domains[..p];
    let motive = domains[p];
    let minor = domains[p + 1];
    let target = domains[p + 2];

    let Some((ind_params, _)) = pi_spine(export, inductive.ty, p) else {
        return false;
    };
    if params != ind_params.as_slice() {
        return false;
    }

    let Some((motive_domains, motive_result)) = pi_spine(export, motive, 1) else {
        return false;
    };
    let [motive_target] = motive_domains.as_slice() else {
        return false;
    };
    let (motive_head, motive_args) = application_spine(export, *motive_target);
    if motive_args.len() != p
        || !is_declared_level_constant(export, motive_head, inductive.name, &inductive.level_params)
        || !motive_args
            .iter()
            .enumerate()
            .all(|(i, arg)| is_bvar(export, *arg, (p - 1 - i) as u64))
    {
        return false;
    }

    let motive_level = match export.exprs.get(motive_result) {
        Some(Expr::Sort(level)) => match export.levels.get(*level) {
            Some(Level::Param(name)) => *name,
            _ => return false,
        },
        _ => return false,
    };
    if recursor.level_params.first().copied() != Some(motive_level)
        || recursor.level_params.get(1..) != Some(inductive.level_params.as_slice())
    {
        return false;
    }

    let Some((minor_domains, minor_result)) = pi_spine(export, minor, fields) else {
        return false;
    };
    if !ctor_fields.iter().zip(&minor_domains).enumerate().all(
        |(field, (ctor_domain, minor_domain))| {
            expression_matches_lift(export, *ctor_domain, *minor_domain, field as u64, 1)
        },
    ) {
        return false;
    }

    let Some(Expr::App {
        fun: minor_motive,
        arg: constructed,
    }) = export.exprs.get(minor_result)
    else {
        return false;
    };
    if !is_bvar(export, *minor_motive, fields as u64) {
        return false;
    }
    let (ctor_head, ctor_args) = application_spine(export, *constructed);
    if ctor_args.len() != p + fields
        || !is_declared_level_constant(
            export,
            ctor_head,
            constructor.name,
            &constructor.level_params,
        )
    {
        return false;
    }
    for (i, arg) in ctor_args.iter().take(p).enumerate() {
        if !is_bvar(export, *arg, (p + fields - i) as u64) {
            return false;
        }
    }
    for field in 0..fields {
        if !is_bvar(export, ctor_args[p + field], (fields - 1 - field) as u64) {
            return false;
        }
    }

    let (target_head, target_args) = application_spine(export, target);
    if target_args.len() != p
        || !is_declared_level_constant(export, target_head, inductive.name, &inductive.level_params)
        || !target_args
            .iter()
            .enumerate()
            .all(|(i, arg)| is_bvar(export, *arg, (p + 1 - i) as u64))
        || !is_bvar_application(export, result, 2, 0)
    {
        return false;
    }

    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    if rule.constructor != constructor.name || rule.num_fields != constructor.num_fields {
        return false;
    }
    let Some((rule_domains, rule_result)) = lam_spine(export, rule.rhs, p + 2 + fields) else {
        return false;
    };
    if rule_domains[..p] != ind_params[..]
        || rule_domains[p] != motive
        || rule_domains[p + 1] != minor
    {
        return false;
    }
    for field in 0..fields {
        if !expression_matches_lift(
            export,
            minor_domains[field],
            rule_domains[p + 2 + field],
            field as u64,
            1,
        ) {
            return false;
        }
    }
    let (rule_head, rule_args) = application_spine(export, rule_result);
    is_bvar(export, rule_head, fields as u64)
        && rule_args.len() == fields
        && rule_args
            .iter()
            .enumerate()
            .all(|(field, arg)| is_bvar(export, *arg, (fields - 1 - field) as u64))
}

fn generic_unary_structure_candidate(export: &ResolvedExport, block: &InductiveBlock) -> bool {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return false;
    };

    if inductive.num_params != 1
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || inductive.level_params.len() != 1
        || constructor.num_params != 1
        || constructor.num_fields != 1
        || constructor.is_unsafe
        || recursor.k
        || recursor.is_unsafe
        || recursor.level_params.len() != 2
    {
        return false;
    }

    let Some((inductive_domains, inductive_result)) = pi_spine(export, inductive.ty, 1) else {
        return false;
    };
    let [parameter_type] = inductive_domains.as_slice() else {
        return false;
    };
    if !matches!(export.exprs.get(*parameter_type), Some(Expr::Sort(_)))
        || !matches!(
            export.exprs.get(inductive_result),
            Some(Expr::Sort(level))
                if !matches!(export.levels.get(*level), Some(Level::Zero))
        )
    {
        return false;
    }

    let Some((constructor_domains, _)) = pi_spine(export, constructor.ty, 2) else {
        return false;
    };
    matches!(
        constructor_domains.as_slice(),
        [constructor_parameter, field]
            if *constructor_parameter == *parameter_type
                && !expression_contains_constant(export, *field, inductive.name)
    )
}

fn check_generic_unary_structure(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };
    if !generic_unary_structure_candidate(export, block) {
        return Err(Verdict::Unknown);
    }

    if inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || constructor.index != 0
        || constructor.inductive != inductive.name
        || constructor.level_params != inductive.level_params
        || has_duplicate_parameter(&inductive.level_params)
        || constructor_result_is_definitely_malformed(export, inductive, constructor)
        || !recursor_metadata_admissible(
            export,
            inductive,
            &block.constructors,
            recursor,
            false,
            true,
        )
        || !generic_unary_structure_recursor_shape(export, inductive, constructor, recursor)
    {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_polymorphic_type(inductive.name, &inductive.level_params, inductive.ty),
            derived_constructor(constructor),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;

    let Some((constructor_domains, _)) = pi_spine(export, constructor.ty, 2) else {
        return Err(Verdict::Reject);
    };
    let [_, field_type] = constructor_domains.as_slice() else {
        return Err(Verdict::Reject);
    };

    let environment = derivation
        .finish()
        .install_projection_spec(
            inductive.name,
            ProjectionSpec {
                constructor: constructor.name,
                num_params: 1,
                field_types: vec![ProjectionFieldType::Derived(*field_type)],
            },
        )
        .map_err(|_| Verdict::Reject)?;

    install_certified_recursor_reduction(environment, &block.constructors, recursor)
}

fn generic_field_structure_is_parameter_product(
    export: &ResolvedExport,
    inductive: &crate::syntax::InductiveType,
    constructor: &Constructor,
) -> bool {
    let (Ok(p), Ok(fields)) = (
        usize::try_from(inductive.num_params),
        usize::try_from(constructor.num_fields),
    ) else {
        return false;
    };
    if p == 0 || fields != p {
        return false;
    }
    let Some((domains, _)) = pi_spine(export, constructor.ty, p + fields) else {
        return false;
    };
    domains[p..]
        .iter()
        .all(|domain| is_bvar(export, *domain, (p - 1) as u64))
}

fn generic_field_structure_candidate(export: &ResolvedExport, block: &InductiveBlock) -> bool {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return false;
    };
    let (Ok(p), Ok(fields)) = (
        usize::try_from(inductive.num_params),
        usize::try_from(constructor.num_fields),
    ) else {
        return false;
    };
    if fields == 0
        || generic_field_structure_is_parameter_product(export, inductive, constructor)
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || constructor.num_params != inductive.num_params
        || constructor.is_unsafe
        || recursor.k
        || recursor.is_unsafe
    {
        return false;
    }
    let Some((_, result)) = pi_spine(export, inductive.ty, p) else {
        return false;
    };
    if !matches!(
        export.exprs.get(result),
        Some(Expr::Sort(level)) if !matches!(export.levels.get(*level), Some(Level::Zero))
    ) {
        return false;
    }
    let Some((ctor_domains, _)) = pi_spine(export, constructor.ty, p + fields) else {
        return false;
    };
    ctor_domains[p..]
        .iter()
        .all(|field| !expression_contains_constant(export, *field, inductive.name))
}

fn check_generic_field_structure(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };
    if !generic_field_structure_candidate(export, block) {
        return Err(Verdict::Unknown);
    }
    if inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || constructor.index != 0
        || constructor.inductive != inductive.name
        || constructor.level_params != inductive.level_params
        || has_duplicate_parameter(&inductive.level_params)
        || constructor_result_is_definitely_malformed(export, inductive, constructor)
        || !recursor_metadata_admissible(
            export,
            inductive,
            &block.constructors,
            recursor,
            false,
            true,
        )
        || !generic_unary_structure_recursor_shape(export, inductive, constructor, recursor)
    {
        return Err(Verdict::Unknown);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    let derived_inductive = if inductive.level_params.is_empty() {
        derived_type(inductive.name, inductive.ty)
    } else {
        derived_polymorphic_type(inductive.name, &inductive.level_params, inductive.ty)
    };
    derivation.promote_all(
        export,
        [
            derived_inductive,
            derived_constructor(constructor),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    Ok(derivation.finish())
}

fn generic_parameterized_nullary_candidate(
    export: &ResolvedExport,
    block: &InductiveBlock,
) -> bool {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return false;
    };
    inductive.num_params > 0
        && inductive.num_indices == 0
        && inductive.num_nested == 0
        && !inductive.is_recursive
        && !inductive.is_reflexive
        && !inductive.is_unsafe
        && constructor.num_params == inductive.num_params
        && constructor.num_fields == 0
        && !constructor.is_unsafe
        && !recursor.k
        && !recursor.is_unsafe
        && matches!(pi_spine(export, inductive.ty, inductive.num_params as usize),
            Some((_, result)) if matches!(export.exprs.get(result), Some(Expr::Sort(level))
                if !matches!(export.levels.get(*level), Some(Level::Zero))))
}

fn generic_parameterized_nullary_recursor_shape(
    export: &ResolvedExport,
    inductive: &crate::syntax::InductiveType,
    constructor: &Constructor,
    recursor: &Recursor,
) -> bool {
    let p = inductive.num_params as usize;
    let Some((domains, result)) = pi_spine(export, recursor.ty, p + 3) else {
        return false;
    };
    let params = &domains[..p];
    let motive = domains[p];
    let minor = domains[p + 1];
    let target = domains[p + 2];

    // Parameters in the recursor telescope must match the inductive's own
    // parameter telescope exactly. This first generic corridor is deliberately
    // syntactic; conversion-lifted parameters remain a later extension.
    let Some((ind_params, _)) = pi_spine(export, inductive.ty, p) else {
        return false;
    };
    if params != ind_params.as_slice() {
        return false;
    }

    let (motive_domains, motive_result) = match pi_spine(export, motive, 1) {
        Some(pair) => pair,
        None => return false,
    };
    let [motive_target] = motive_domains.as_slice() else {
        return false;
    };
    let (head, args) = application_spine(export, *motive_target);
    if args.len() != p
        || !is_declared_level_constant(export, head, inductive.name, &inductive.level_params)
        || !args
            .iter()
            .enumerate()
            .all(|(i, arg)| is_bvar(export, *arg, (p - 1 - i) as u64))
    {
        return false;
    }

    let motive_level = match export.exprs.get(motive_result) {
        Some(Expr::Sort(level)) => match export.levels.get(*level) {
            Some(Level::Param(name)) => *name,
            _ => return false,
        },
        _ => return false,
    };
    if recursor.level_params.first().copied() != Some(motive_level)
        || recursor.level_params.get(1..) != Some(inductive.level_params.as_slice())
    {
        return false;
    }

    // minor : motive (ctor params)
    let Some(Expr::App {
        fun: minor_motive,
        arg: constructed,
    }) = export.exprs.get(minor)
    else {
        return false;
    };
    if !is_bvar(export, *minor_motive, 0) {
        return false;
    }
    let (ctor_head, ctor_args) = application_spine(export, *constructed);
    if ctor_args.len() != p
        || !is_declared_level_constant(
            export,
            ctor_head,
            constructor.name,
            &constructor.level_params,
        )
        || !ctor_args
            .iter()
            .enumerate()
            .all(|(i, arg)| is_bvar(export, *arg, (p - i) as u64))
    {
        return false;
    }

    let (target_head, target_args) = application_spine(export, target);
    if target_args.len() != p
        || !is_declared_level_constant(export, target_head, inductive.name, &inductive.level_params)
        || !target_args
            .iter()
            .enumerate()
            .all(|(i, arg)| is_bvar(export, *arg, (p + 1 - i) as u64))
        || !is_bvar_application(export, result, 2, 0)
    {
        return false;
    }

    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    let Some((rule_domains, rule_result)) = lam_spine(export, rule.rhs, p + 2) else {
        return false;
    };
    if rule_domains.len() != p + 2 || !is_bvar(export, rule_result, 0) {
        return false;
    }
    true
}

fn is_declared_level_constant(
    export: &ResolvedExport,
    expression: ExprId,
    name: NameId,
    level_params: &[NameId],
) -> bool {
    let Some(Expr::Const {
        name: actual,
        levels,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    *actual == name
        && levels.len() == level_params.len()
        && levels.iter().zip(level_params).all(|(level, parameter)| {
            matches!(export.levels.get(*level), Some(Level::Param(actual)) if actual == parameter)
        })
}

fn check_generic_parameterized_nullary(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };
    if !generic_parameterized_nullary_candidate(export, block) {
        return Err(Verdict::Unknown);
    }
    if inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || constructor.index != 0
        || constructor.inductive != inductive.name
        || constructor.level_params != inductive.level_params
        || has_duplicate_parameter(&inductive.level_params)
        || constructor_result_is_definitely_malformed(export, inductive, constructor)
        || !recursor_metadata_admissible(
            export,
            inductive,
            &block.constructors,
            recursor,
            false,
            true,
        )
        || !generic_parameterized_nullary_recursor_shape(export, inductive, constructor, recursor)
    {
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
        [
            derived_inductive,
            derived_constructor(constructor),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    Ok(derivation.finish())
}

fn generic_closed_prop_singleton_candidate(block: &InductiveBlock) -> bool {
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
        && inductive.level_params.is_empty()
        && constructor.num_params == 0
        && constructor.num_fields == 0
        && !constructor.is_unsafe
        && recursor.k
        && !recursor.is_unsafe
}

fn check_generic_closed_prop_singleton(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };

    if !generic_closed_prop_singleton_candidate(block) {
        return Err(Verdict::Unknown);
    }

    // Lean's K target for this structural envelope is a closed inductive Prop
    // with one constructor whose telescope contains only the parameters
    // (there are none here).  Derive every remaining exported claim rather
    // than trusting the metadata.
    if inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || !matches!(
            export.exprs.get(inductive.ty),
            Some(Expr::Sort(level)) if matches!(export.levels.get(*level), Some(Level::Zero))
        )
        || constructor.index != 0
        || constructor.inductive != inductive.name
        || !constructor.level_params.is_empty()
        || !is_empty_constant(export, constructor.ty, inductive.name)
    {
        return Err(Verdict::Reject);
    }

    let [motive_level] = recursor.level_params.as_slice() else {
        return Err(Verdict::Reject);
    };
    if !recursor_metadata_admissible(export, inductive, &block.constructors, recursor, true, true)
        || !new_singleton_recursor_type(
            export,
            recursor.ty,
            inductive.name,
            constructor.name,
            *motive_level,
        )
        || !new_singleton_recursor_rule(
            export,
            recursor,
            inductive.name,
            constructor.name,
            *motive_level,
        )
    {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_type(inductive.name, inductive.ty),
            derived_constructor(constructor),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    derivation
        .finish()
        .install_singleton_recursor_reduction(recursor.name)
        .map_err(|_| Verdict::Reject)
}

fn check_exact_new_singleton(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };

    if inductive.num_nested != 0
        || inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || constructor.is_unsafe
        || recursor.is_unsafe
    {
        return Err(Verdict::Unknown);
    }

    if inductive.num_params != 0
        || inductive.num_indices != 0
        || !inductive.level_params.is_empty()
        || inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || !matches!(
            export.exprs.get(inductive.ty),
            Some(Expr::Sort(level))
                if matches!(export.levels.get(*level), Some(Level::Succ(LevelId(0))))
        )
        || constructor.index != 0
        || constructor.inductive != inductive.name
        || constructor.num_fields != 0
        || constructor.num_params != 0
        || !constructor.level_params.is_empty()
        || !name_is_child_str(export, constructor.name, inductive.name, "mk")
        || !is_empty_constant(export, constructor.ty, inductive.name)
    {
        return Err(Verdict::Reject);
    }

    let [motive_level] = recursor.level_params.as_slice() else {
        return Err(Verdict::Reject);
    };
    if !recursor_metadata_admissible(
        export,
        inductive,
        &block.constructors,
        recursor,
        false,
        true,
    ) || !new_singleton_recursor_type(
        export,
        recursor.ty,
        inductive.name,
        constructor.name,
        *motive_level,
    ) || !new_singleton_recursor_rule(
        export,
        recursor,
        inductive.name,
        constructor.name,
        *motive_level,
    ) {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_type(inductive.name, inductive.ty),
            derived_constructor(constructor),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    derivation
        .finish()
        .install_singleton_recursor_reduction(recursor.name)
        .map_err(|_| Verdict::Reject)
}

fn new_singleton_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    motive_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 1) else {
        return false;
    };
    let [target] = domains.as_slice() else {
        return false;
    };
    is_empty_constant(export, *target, inductive) && is_sort_parameter(export, result, motive_level)
}

fn new_singleton_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
) -> bool {
    is_bvar_applied_to_constant(export, expression, 0, constructor)
}

fn new_singleton_recursor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    constructor: NameId,
    motive_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [motive, minor, target] = domains.as_slice() else {
        return false;
    };
    new_singleton_motive_type(export, *motive, inductive, motive_level)
        && new_singleton_minor_type(export, *minor, constructor)
        && is_empty_constant(export, *target, inductive)
        && is_bvar_application(export, result, 2, 0)
}

fn new_singleton_recursor_rule(
    export: &ResolvedExport,
    recursor: &Recursor,
    inductive: NameId,
    constructor: NameId,
    motive_level: NameId,
) -> bool {
    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    lam_spine(export, rule.rhs, 2).is_some_and(|(domains, result)| {
        let [motive, minor] = domains.as_slice() else {
            return false;
        };
        new_singleton_motive_type(export, *motive, inductive, motive_level)
            && new_singleton_minor_type(export, *minor, constructor)
            && is_bvar(export, result, 0)
    })
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

/// Residual-generated extension of G23: one-parameter reflexive recursion
/// whose sole recursive field is a function. The field's parameter and
/// codomain are admitted only after reducible conversion proves them equal
/// to the inductive parameter and recursive target. The recursor must carry
/// the corresponding pointwise induction hypothesis.
fn check_conversion_lifted_reflexive_unary(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };

    if inductive.num_params != 1
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || !inductive.is_recursive
        || !inductive.is_reflexive
        || inductive.is_unsafe
        || !inductive.level_params.is_empty()
        || !inductive_arity_metadata_is_well_formed(export, inductive)
        || constructor.is_unsafe
        || recursor.is_unsafe
    {
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
        || !recursor_metadata_admissible(
            export,
            inductive,
            &block.constructors,
            recursor,
            false,
            recursor.level_params.len() == 1,
        )
    {
        return Err(Verdict::Reject);
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

    let Some(Expr::Pi {
        domain: constructor_parameter,
        body: constructor_body,
    }) = export.exprs.get(constructor.ty)
    else {
        return Err(Verdict::Reject);
    };
    let Some(Expr::Pi {
        domain: constructor_field,
        body: constructor_result,
    }) = export.exprs.get(*constructor_body)
    else {
        return Err(Verdict::Reject);
    };
    if !matches!(export.exprs.get(*constructor_field), Some(Expr::Pi { .. })) {
        return Err(Verdict::Reject);
    }

    let Some((recursor_parameter, recursor_minor_field, rule_field)) =
        conversion_lifted_reflexive_shapes(export, inductive.name, constructor.name, recursor)
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
            &TypeValue::Term(checker.closure(recursor_parameter, empty)),
            limits.judgment_steps,
        ))?;

        let alpha = FreeId(20_001);
        let field = FreeId(20_002);
        let point = FreeId(20_003);
        let motive = FreeId(20_004);
        let minor = FreeId(20_005);
        let parameter_frame = EnvFrame::empty().extend_free(alpha);

        // The constructor field itself may be presented through reducible
        // wrappers. Its WHNF must be a function α → I α.
        let exposed_field = checker.machine().expose(
            checker.closure(*constructor_field, parameter_frame.clone()),
            Transparency::Reducible,
            limits.judgment_steps,
        );
        let Some(Value::Pi {
            domain: field_domain,
            body: field_body,
        }) = exposed_field.proven_value()
        else {
            return Err(Verdict::Reject);
        };
        let reduced_field_domain = checker.machine().expose(
            field_domain.clone(),
            Transparency::Reducible,
            limits.judgment_steps,
        );
        let Some(Value::Neutral(neutral_domain)) = reduced_field_domain.proven_value() else {
            return Err(Verdict::Reject);
        };
        if !matches!(neutral_domain.head, NeutralHead::Free(free) if free == alpha)
            || !neutral_domain.spine.is_empty()
        {
            return Err(Verdict::Reject);
        }

        let recursive_body = field_body.under_free(point);
        let constructor_target = checker.closure(
            *constructor_result,
            parameter_frame.clone().extend_free(field),
        );
        verdict_boundary(checker.convert(
            &TypeValue::Term(recursive_body),
            &TypeValue::Term(constructor_target),
            limits.judgment_steps,
        ))?;

        // The exported recursor and rule must expose the same field type under
        // their shifted binders. Pointwise IH shape is checked structurally.
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

fn reflexive_unary_minor_field(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    constructor: NameId,
) -> Option<ExprId> {
    let (domains, result) = pi_spine(export, expression, 2)?;
    let [field, induction_hypothesis] = domains.as_slice() else {
        return None;
    };
    if !matches!(export.exprs.get(*field), Some(Expr::Pi { .. })) {
        return None;
    }

    let Expr::Pi {
        domain: ih_argument,
        body: ih_result,
    } = export.exprs.get(*induction_hypothesis)?
    else {
        return None;
    };
    if !is_bvar(export, *ih_argument, 2) {
        return None;
    }
    let Expr::App {
        fun: ih_motive,
        arg: field_at_argument,
    } = export.exprs.get(*ih_result)?
    else {
        return None;
    };
    if !is_bvar(export, *ih_motive, 2) || !is_bvar_application(export, *field_at_argument, 1, 0) {
        return None;
    }

    let Expr::App {
        fun: result_motive,
        arg: constructed,
    } = export.exprs.get(result)?
    else {
        return None;
    };
    if !is_bvar(export, *result_motive, 2)
        || !is_constructor_applied_to_two_bvars(export, *constructed, constructor, 3, 1)
    {
        return None;
    }

    // The recursive target itself is validated by conversion after the
    // inductive signature has been staged.
    let _ = inductive;
    Some(*field)
}

fn conversion_lifted_reflexive_shapes(
    export: &ResolvedExport,
    inductive: NameId,
    constructor: NameId,
    recursor: &Recursor,
) -> Option<(ExprId, ExprId, ExprId)> {
    let (domains, result) = pi_spine(export, recursor.ty, 4)?;
    let [parameter, motive, minor, target] = domains.as_slice() else {
        return None;
    };
    if !is_unary_recursive_motive_type(export, *motive, inductive, recursor.level_params[0])
        || !is_empty_inductive_applied_to_bvar(export, *target, inductive, 2)
        || !is_bvar_application(export, result, 2, 0)
    {
        return None;
    }
    let minor_field = reflexive_unary_minor_field(export, *minor, inductive, constructor)?;

    let [rule] = recursor.rules.as_slice() else {
        return None;
    };
    let (rule_domains, rule_result) = lam_spine(export, rule.rhs, 4)?;
    let [_parameter, rule_motive, rule_minor, rule_field] = rule_domains.as_slice() else {
        return None;
    };
    if !is_unary_recursive_motive_type(export, *rule_motive, inductive, recursor.level_params[0])
        || reflexive_unary_minor_field(export, *rule_minor, inductive, constructor).is_none()
        || !matches!(export.exprs.get(*rule_field), Some(Expr::Pi { .. }))
    {
        return None;
    }

    let Expr::App {
        fun: minor_at_field,
        arg: pointwise_ih,
    } = export.exprs.get(rule_result)?
    else {
        return None;
    };
    if !is_bvar_application(export, *minor_at_field, 1, 0) {
        return None;
    }
    let Expr::Lam {
        domain: ih_domain,
        body: recursive_call,
        ..
    } = export.exprs.get(*pointwise_ih)?
    else {
        return None;
    };
    if !is_bvar(export, *ih_domain, 3) {
        return None;
    }

    let (head, arguments) = application_spine(export, *recursive_call);
    let [parameter_arg, motive_arg, minor_arg, target_arg] = arguments.as_slice() else {
        return None;
    };
    if !is_unary_polymorphic_constant(export, head, recursor.name, recursor.level_params[0])
        || !is_bvar(export, *parameter_arg, 4)
        || !is_bvar(export, *motive_arg, 3)
        || !is_bvar(export, *minor_arg, 2)
        || !is_bvar_application(export, *target_arg, 1, 0)
    {
        return None;
    }

    Some((*parameter, minor_field, *rule_field))
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

/// G27-001: the exact dependent existential Prop family.
///
/// This is deliberately name-sealed to `Exists`.  The newly earned law is
/// narrower than general singleton-Prop elimination: one universe-polymorphic
/// carrier, one dependent predicate parameter, one witness field and one proof
/// field, with a recursor whose motive itself lands in Prop.  No iota rule,
/// indexed elimination, or general structure authority is installed.
fn check_exact_exists_family(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };

    // Preserve broader envelopes as UNKNOWN.  Inside this exact named
    // envelope, structural disagreement is a malformed Exists claim.
    if inductive.num_params != 2
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || constructor.is_unsafe
        || recursor.is_unsafe
    {
        return Err(Verdict::Unknown);
    }

    let [level] = inductive.level_params.as_slice() else {
        return Err(Verdict::Reject);
    };
    if inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || constructor.index != 0
        || constructor.inductive != inductive.name
        || constructor.num_params != 2
        || constructor.num_fields != 2
        || constructor.level_params != [*level]
        || !name_is_child_str(export, constructor.name, inductive.name, "intro")
        || !is_exists_inductive_type(export, inductive.ty, *level)
        || !is_exists_constructor_type(
            export,
            constructor.ty,
            inductive.name,
            constructor.name,
            *level,
        )
    {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_polymorphic_type(inductive.name, &inductive.level_params, inductive.ty),
            derived_constructor(constructor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;

    if !recursor_metadata_admissible(
        export,
        inductive,
        &block.constructors,
        recursor,
        false,
        recursor.level_params == [*level],
    ) || !is_exists_recursor_type(
        export,
        recursor.ty,
        inductive.name,
        constructor.name,
        *level,
    ) || !is_exists_recursor_rule(export, recursor, inductive.name, constructor.name, *level)
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

fn is_exists_predicate_type(export: &ResolvedExport, expression: ExprId, carrier: u64) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::Pi { domain, body })
            if is_bvar(export, *domain, carrier) && is_prop_sort(export, *body)
    )
}

fn is_exists_application(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
    carrier: u64,
    predicate: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 2
        && is_unary_polymorphic_constant(export, head, inductive, level)
        && are_bvars(export, &arguments, &[carrier, predicate])
}

fn is_exists_constructor_application(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    level: NameId,
    binders: [u64; 4],
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 4
        && is_unary_polymorphic_constant(export, head, constructor, level)
        && are_bvars(export, &arguments, &binders)
}

fn is_exists_inductive_type(export: &ResolvedExport, expression: ExprId, level: NameId) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [carrier, predicate] = domains.as_slice() else {
        return false;
    };
    is_sort_parameter(export, *carrier, level)
        && is_exists_predicate_type(export, *predicate, 0)
        && is_prop_sort(export, result)
}

fn is_exists_constructor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    _constructor: NameId,
    level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 4) else {
        return false;
    };
    let [carrier, predicate, witness, proof] = domains.as_slice() else {
        return false;
    };
    is_sort_parameter(export, *carrier, level)
        && is_exists_predicate_type(export, *predicate, 0)
        && is_bvar(export, *witness, 1)
        && is_bvar_application(export, *proof, 1, 0)
        && is_exists_application(export, result, inductive, level, 3, 2)
}

fn is_exists_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 1) else {
        return false;
    };
    let [target] = domains.as_slice() else {
        return false;
    };
    is_exists_application(export, *target, inductive, level, 1, 0) && is_prop_sort(export, result)
}

fn is_exists_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [witness, proof] = domains.as_slice() else {
        return false;
    };
    let Some(Expr::App {
        fun: motive,
        arg: constructed,
    }) = export.exprs.get(result)
    else {
        return false;
    };
    is_bvar(export, *witness, 2)
        && is_bvar_application(export, *proof, 2, 0)
        && is_bvar(export, *motive, 2)
        && is_exists_constructor_application(export, *constructed, constructor, level, [4, 3, 1, 0])
}

fn is_exists_recursor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    constructor: NameId,
    level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 5) else {
        return false;
    };
    let [carrier, predicate, motive, minor, target] = domains.as_slice() else {
        return false;
    };
    is_sort_parameter(export, *carrier, level)
        && is_exists_predicate_type(export, *predicate, 0)
        && is_exists_motive_type(export, *motive, inductive, level)
        && is_exists_minor_type(export, *minor, constructor, level)
        && is_exists_application(export, *target, inductive, level, 3, 2)
        && is_bvar_application(export, result, 2, 0)
}

fn is_exists_recursor_rule(
    export: &ResolvedExport,
    recursor: &Recursor,
    inductive: NameId,
    constructor: NameId,
    level: NameId,
) -> bool {
    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    let Some((domains, result)) = lam_spine(export, rule.rhs, 6) else {
        return false;
    };
    let [carrier, predicate, motive, minor, witness, proof] = domains.as_slice() else {
        return false;
    };
    is_sort_parameter(export, *carrier, level)
        && is_exists_predicate_type(export, *predicate, 0)
        && is_exists_motive_type(export, *motive, inductive, level)
        && is_exists_minor_type(export, *minor, constructor, level)
        && is_bvar(export, *witness, 3)
        && is_bvar_application(export, *proof, 3, 0)
        && is_binary_bvar_application(export, result, 2, 1, 0)
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
    {
        return Err(Verdict::Unknown);
    }

    if constructor_result_is_definitely_malformed(export, inductive, constructor)
        || constructor_has_definite_negative_recursive_field(export, inductive, constructor)
    {
        Err(Verdict::Reject)
    } else {
        Err(Verdict::Unknown)
    }
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
        Some(Expr::Proj { structure, .. }) => {
            expression_has_definite_negative_occurrence(export, *structure, target, positive)
        }
        Some(Expr::BVar(_) | Expr::NatLit(_) | Expr::StrLit(_) | Expr::Sort(_)) | None => false,
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
        Some(Expr::Proj {
            type_name,
            structure,
            ..
        }) => *type_name == target || expression_contains_constant(export, *structure, target),
        Some(Expr::BVar(_) | Expr::NatLit(_) | Expr::StrLit(_) | Expr::Sort(_)) | None => false,
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

/// G34: exact unary-polymorphic List family.
///
/// This does not introduce a second recursive evaluator.  It validates the
/// standard List telescope, constructors, recursor and certified rule bodies,
/// then reuses the G33 rule-body reduction capability.
fn check_exact_list(
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
    {
        return Err(Verdict::Unknown);
    }
    let [level] = inductive.level_params.as_slice() else {
        return Err(Verdict::Reject);
    };
    let Some((type_domains, type_result)) = pi_spine(export, inductive.ty, 1) else {
        return Err(Verdict::Reject);
    };
    let [carrier] = type_domains.as_slice() else {
        return Err(Verdict::Reject);
    };
    if !is_sort_succ_parameter(export, *carrier, *level)
        || !is_sort_succ_parameter(export, type_result, *level)
    {
        return Err(Verdict::Reject);
    }

    let [nil, cons] = block.constructors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if nil.is_unsafe || cons.is_unsafe {
        return Err(Verdict::Unknown);
    }
    if inductive.all != [inductive.name]
        || inductive.constructors != [nil.name, cons.name]
        || nil.index != 0
        || nil.inductive != inductive.name
        || nil.level_params != [*level]
        || nil.num_params != 1
        || nil.num_fields != 0
        || !name_is_child_str(export, nil.name, inductive.name, "nil")
        || !list_nil_constructor_type(export, nil.ty, inductive.name, *level)
        || cons.index != 1
        || cons.inductive != inductive.name
        || cons.level_params != [*level]
        || cons.num_params != 1
        || cons.num_fields != 2
        || !name_is_child_str(export, cons.name, inductive.name, "cons")
        || !list_cons_constructor_type(export, cons.ty, inductive.name, *level)
    {
        return Err(Verdict::Reject);
    }

    let [recursor] = block.recursors.as_slice() else {
        return Err(Verdict::Reject);
    };
    if recursor.is_unsafe {
        return Err(Verdict::Unknown);
    }
    let levels_ok = matches!(
        recursor.level_params.as_slice(),
        [motive_level, carrier_level]
            if *carrier_level == *level && *motive_level != *carrier_level
    );
    if !recursor_metadata_admissible(
        export,
        inductive,
        &block.constructors,
        recursor,
        false,
        levels_ok,
    ) || !list_recursor_type(
        export,
        inductive.name,
        nil.name,
        cons.name,
        *level,
        recursor,
    ) || !list_recursor_rules(
        export,
        inductive.name,
        nil.name,
        cons.name,
        *level,
        recursor,
    ) {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_polymorphic_type(inductive.name, &inductive.level_params, inductive.ty),
            derived_constructor(nil),
            derived_constructor(cons),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    install_certified_recursor_reduction(derivation.finish(), &block.constructors, recursor)
}

fn list_application(
    export: &ResolvedExport,
    expression: ExprId,
    constant: NameId,
    level: NameId,
    argument: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    matches!(arguments.as_slice(), [arg]
        if is_unary_polymorphic_constant(export, head, constant, level)
            && is_bvar(export, *arg, argument))
}

fn list_nil_application(
    export: &ResolvedExport,
    expression: ExprId,
    nil: NameId,
    level: NameId,
    carrier: u64,
) -> bool {
    list_application(export, expression, nil, level, carrier)
}

fn list_cons_application(
    export: &ResolvedExport,
    expression: ExprId,
    cons: NameId,
    level: NameId,
    carrier: u64,
    head: u64,
    tail: u64,
) -> bool {
    let (constant, arguments) = application_spine(export, expression);
    arguments.len() == 3
        && is_unary_polymorphic_constant(export, constant, cons, level)
        && are_bvars(export, &arguments, &[carrier, head, tail])
}

fn list_nil_constructor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 1) else {
        return false;
    };
    let [carrier] = domains.as_slice() else {
        return false;
    };
    is_sort_succ_parameter(export, *carrier, level)
        && list_application(export, result, inductive, level, 0)
}

fn list_cons_constructor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [carrier, head, tail] = domains.as_slice() else {
        return false;
    };
    is_sort_succ_parameter(export, *carrier, level)
        && is_bvar(export, *head, 0)
        && list_application(export, *tail, inductive, level, 1)
        && list_application(export, result, inductive, level, 2)
}

fn list_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    carrier_level: NameId,
    motive_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 1) else {
        return false;
    };
    let [target] = domains.as_slice() else {
        return false;
    };
    list_application(export, *target, inductive, carrier_level, 0)
        && is_sort_parameter(export, result, motive_level)
}

fn list_nil_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    nil: NameId,
    carrier_level: NameId,
) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::App { fun, arg })
            if is_bvar(export, *fun, 0)
                && list_nil_application(export, *arg, nil, carrier_level, 1)
    )
}

fn list_cons_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    cons: NameId,
    carrier_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [head, tail, tail_ih] = domains.as_slice() else {
        return false;
    };
    if !is_bvar(export, *head, 2)
        || !list_application(export, *tail, inductive, carrier_level, 3)
        || !is_bvar_application(export, *tail_ih, 3, 0)
    {
        return false;
    }
    let Some(Expr::App {
        fun: motive,
        arg: constructed,
    }) = export.exprs.get(result)
    else {
        return false;
    };
    is_bvar(export, *motive, 4)
        && list_cons_application(export, *constructed, cons, carrier_level, 5, 2, 1)
}

fn list_recursor_type(
    export: &ResolvedExport,
    inductive: NameId,
    nil: NameId,
    cons: NameId,
    carrier_level: NameId,
    recursor: &Recursor,
) -> bool {
    let [motive_level, declared_carrier] = recursor.level_params.as_slice() else {
        return false;
    };
    if *declared_carrier != carrier_level {
        return false;
    }
    let Some((domains, result)) = pi_spine(export, recursor.ty, 5) else {
        return false;
    };
    let [carrier, motive, nil_minor, cons_minor, target] = domains.as_slice() else {
        return false;
    };
    is_sort_succ_parameter(export, *carrier, carrier_level)
        && list_motive_type(export, *motive, inductive, carrier_level, *motive_level)
        && list_nil_minor_type(export, *nil_minor, nil, carrier_level)
        && list_cons_minor_type(export, *cons_minor, inductive, cons, carrier_level)
        && list_application(export, *target, inductive, carrier_level, 3)
        && is_bvar_application(export, result, 3, 0)
}

fn list_recursor_rules(
    export: &ResolvedExport,
    inductive: NameId,
    nil: NameId,
    cons: NameId,
    carrier_level: NameId,
    recursor: &Recursor,
) -> bool {
    let [motive_level, declared_carrier] = recursor.level_params.as_slice() else {
        return false;
    };
    if *declared_carrier != carrier_level {
        return false;
    }
    let [nil_rule, cons_rule] = recursor.rules.as_slice() else {
        return false;
    };

    let nil_ok = lam_spine(export, nil_rule.rhs, 4).is_some_and(|(domains, result)| {
        let [carrier, motive, nil_minor, cons_minor] = domains.as_slice() else {
            return false;
        };
        is_sort_succ_parameter(export, *carrier, carrier_level)
            && list_motive_type(export, *motive, inductive, carrier_level, *motive_level)
            && list_nil_minor_type(export, *nil_minor, nil, carrier_level)
            && list_cons_minor_type(export, *cons_minor, inductive, cons, carrier_level)
            && is_bvar(export, result, 1)
    });

    let cons_ok = lam_spine(export, cons_rule.rhs, 6).is_some_and(|(domains, result)| {
        let [carrier, motive, nil_minor, cons_minor, head, tail] = domains.as_slice() else {
            return false;
        };
        if !is_sort_succ_parameter(export, *carrier, carrier_level)
            || !list_motive_type(export, *motive, inductive, carrier_level, *motive_level)
            || !list_nil_minor_type(export, *nil_minor, nil, carrier_level)
            || !list_cons_minor_type(export, *cons_minor, inductive, cons, carrier_level)
            || !is_bvar(export, *head, 3)
            || !list_application(export, *tail, inductive, carrier_level, 4)
        {
            return false;
        }
        let (minor, arguments) = application_spine(export, result);
        let [head_arg, tail_arg, recursive_call] = arguments.as_slice() else {
            return false;
        };
        if !is_bvar(export, minor, 2)
            || !is_bvar(export, *head_arg, 1)
            || !is_bvar(export, *tail_arg, 0)
        {
            return false;
        }
        let (recursive, recursive_arguments) = application_spine(export, *recursive_call);
        recursive_arguments.len() == 5
            && is_polymorphic_constant(
                export,
                recursive,
                recursor.name,
                *motive_level,
                carrier_level,
            )
            && are_bvars(export, &recursive_arguments, &[5, 4, 3, 2, 0])
    });

    nil_ok && cons_ok
}

fn acc_relation_type(export: &ResolvedExport, expression: ExprId) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    matches!(domains.as_slice(), [left, right]
        if is_bvar(export, *left, 0)
            && is_bvar(export, *right, 1)
            && is_prop_sort(export, result))
}

fn acc_application(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
    carrier: u64,
    relation: u64,
    index: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 3
        && is_unary_polymorphic_constant(export, head, inductive, level)
        && are_bvars(export, &arguments, &[carrier, relation, index])
}

#[allow(clippy::too_many_arguments)]
fn acc_constructor_application(
    export: &ResolvedExport,
    expression: ExprId,
    constructor: NameId,
    level: NameId,
    carrier: u64,
    relation: u64,
    index: u64,
    recursive_field: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 4
        && is_unary_polymorphic_constant(export, head, constructor, level)
        && are_bvars(
            export,
            &arguments,
            &[carrier, relation, index, recursive_field],
        )
}

fn acc_recursive_field_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
    carrier: u64,
    relation: u64,
    index: u64,
) -> bool {
    let Some(Expr::Pi {
        domain: point,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    if !is_bvar(export, *point, carrier) {
        return false;
    }
    let Some(Expr::Pi {
        domain: edge,
        body: recursive,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    if !is_binary_bvar_application(
        export,
        *edge,
        relation.saturating_add(1),
        0,
        index.saturating_add(1),
    ) {
        return false;
    }
    acc_application(
        export,
        *recursive,
        inductive,
        level,
        carrier.saturating_add(2),
        relation.saturating_add(2),
        1,
    )
}

fn acc_inductive_type(export: &ResolvedExport, expression: ExprId, level: NameId) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [carrier, relation, index] = domains.as_slice() else {
        return false;
    };
    is_sort_parameter(export, *carrier, level)
        && acc_relation_type(export, *relation)
        && is_bvar(export, *index, 1)
        && is_prop_sort(export, result)
}

fn acc_constructor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 4) else {
        return false;
    };
    let [carrier, relation, index, recursive_field] = domains.as_slice() else {
        return false;
    };
    is_sort_parameter(export, *carrier, level)
        && acc_relation_type(export, *relation)
        && is_bvar(export, *index, 1)
        && acc_recursive_field_type(export, *recursive_field, inductive, level, 2, 1, 0)
        && acc_application(export, result, inductive, level, 3, 2, 1)
}

fn acc_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    level: NameId,
    motive_level: NameId,
    carrier: u64,
    relation: u64,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [index, target] = domains.as_slice() else {
        return false;
    };
    is_bvar(export, *index, carrier)
        && acc_application(
            export,
            *target,
            inductive,
            level,
            carrier.saturating_add(1),
            relation.saturating_add(1),
            0,
        )
        && is_sort_parameter(export, result, motive_level)
}

fn acc_induction_hypothesis_type(
    export: &ResolvedExport,
    expression: ExprId,
    carrier: u64,
    relation: u64,
    index: u64,
    motive: u64,
    recursive_field: u64,
) -> bool {
    let Some(Expr::Pi {
        domain: point,
        body,
    }) = export.exprs.get(expression)
    else {
        return false;
    };
    if !is_bvar(export, *point, carrier) {
        return false;
    }
    let Some(Expr::Pi {
        domain: edge,
        body: result,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    if !is_binary_bvar_application(
        export,
        *edge,
        relation.saturating_add(1),
        0,
        index.saturating_add(1),
    ) {
        return false;
    }
    let (head, arguments) = application_spine(export, *result);
    if !is_bvar(export, head, motive.saturating_add(2)) || arguments.len() != 2 {
        return false;
    }
    let [point_arg, recursive_target] = arguments.as_slice() else {
        return false;
    };
    is_bvar(export, *point_arg, 1)
        && is_binary_bvar_application(
            export,
            *recursive_target,
            recursive_field.saturating_add(2),
            1,
            0,
        )
}

fn acc_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    constructor: NameId,
    level: NameId,
    motive_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [index, recursive_field, induction_hypothesis] = domains.as_slice() else {
        return false;
    };
    if !is_bvar(export, *index, 2)
        || !acc_recursive_field_type(export, *recursive_field, inductive, level, 3, 2, 0)
        || !acc_induction_hypothesis_type(export, *induction_hypothesis, 4, 3, 1, 2, 0)
    {
        return false;
    }

    let (motive, arguments) = application_spine(export, result);
    if !is_bvar(export, motive, 3) || arguments.len() != 2 {
        return false;
    }
    let [index_arg, constructed] = arguments.as_slice() else {
        return false;
    };
    is_bvar(export, *index_arg, 2)
        && acc_constructor_application(export, *constructed, constructor, level, 5, 4, 2, 1)
        && motive_level != level
}

fn acc_recursor_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    constructor: NameId,
    level: NameId,
    motive_level: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 6) else {
        return false;
    };
    let [carrier, relation, motive, minor, index, target] = domains.as_slice() else {
        return false;
    };
    if !is_sort_parameter(export, *carrier, level)
        || !acc_relation_type(export, *relation)
        || !acc_motive_type(export, *motive, inductive, level, motive_level, 1, 0)
        || !acc_minor_type(export, *minor, inductive, constructor, level, motive_level)
        || !is_bvar(export, *index, 3)
        || !acc_application(export, *target, inductive, level, 4, 3, 0)
    {
        return false;
    }
    let (result_motive, result_arguments) = application_spine(export, result);
    result_arguments.len() == 2
        && is_bvar(export, result_motive, 3)
        && are_bvars(export, &result_arguments, &[1, 0])
}

fn acc_recursor_rule(
    export: &ResolvedExport,
    recursor: &Recursor,
    inductive: NameId,
    constructor: NameId,
    level: NameId,
    motive_level: NameId,
) -> bool {
    let [rule] = recursor.rules.as_slice() else {
        return false;
    };
    if rule.constructor != constructor || rule.num_fields != 2 {
        return false;
    }
    let Some((domains, result)) = lam_spine(export, rule.rhs, 6) else {
        return false;
    };
    let [carrier, relation, motive, minor, index, recursive_field] = domains.as_slice() else {
        return false;
    };
    if !is_sort_parameter(export, *carrier, level)
        || !acc_relation_type(export, *relation)
        || !acc_motive_type(export, *motive, inductive, level, motive_level, 1, 0)
        || !acc_minor_type(export, *minor, inductive, constructor, level, motive_level)
        || !is_bvar(export, *index, 3)
        || !acc_recursive_field_type(export, *recursive_field, inductive, level, 4, 3, 0)
    {
        return false;
    }

    let (minor_head, minor_arguments) = application_spine(export, result);
    let [index_arg, field_arg, pointwise_ih] = minor_arguments.as_slice() else {
        return false;
    };
    if !is_bvar(export, minor_head, 2)
        || !is_bvar(export, *index_arg, 1)
        || !is_bvar(export, *field_arg, 0)
    {
        return false;
    }

    let Some(Expr::Lam {
        domain: point,
        body,
    }) = export.exprs.get(*pointwise_ih)
    else {
        return false;
    };
    if !is_bvar(export, *point, 5) {
        return false;
    }
    let Some(Expr::Lam {
        domain: edge,
        body: recursive_call,
    }) = export.exprs.get(*body)
    else {
        return false;
    };
    if !is_binary_bvar_application(export, *edge, 5, 0, 2) {
        return false;
    }

    let (recursive_head, recursive_arguments) = application_spine(export, *recursive_call);
    let [
        carrier_arg,
        relation_arg,
        motive_arg,
        minor_arg,
        point_arg,
        target_arg,
    ] = recursive_arguments.as_slice()
    else {
        return false;
    };
    is_polymorphic_constant(export, recursive_head, recursor.name, motive_level, level)
        && are_bvars(
            export,
            &[
                *carrier_arg,
                *relation_arg,
                *motive_arg,
                *minor_arg,
                *point_arg,
            ],
            &[7, 6, 5, 4, 1],
        )
        && is_binary_bvar_application(export, *target_arg, 2, 1, 0)
}

fn check_exact_acc(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };

    if inductive.num_params != 2
        || inductive.num_indices != 1
        || inductive.num_nested != 0
        || !inductive.is_recursive
        || !inductive.is_reflexive
        || inductive.is_unsafe
        || constructor.is_unsafe
        || recursor.is_unsafe
    {
        return Err(Verdict::Unknown);
    }

    let [level] = inductive.level_params.as_slice() else {
        return Err(Verdict::Reject);
    };
    let [motive_level, recursor_level] = recursor.level_params.as_slice() else {
        return Err(Verdict::Reject);
    };
    if *recursor_level != *level || *motive_level == *level {
        return Err(Verdict::Reject);
    }

    if inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || !name_is_root_str(export, inductive.name, "Acc")
        || constructor.index != 0
        || constructor.inductive != inductive.name
        || constructor.level_params != [*level]
        || constructor.num_params != 2
        || constructor.num_fields != 2
        || !name_is_child_str(export, constructor.name, inductive.name, "intro")
        || !name_is_child_str(export, recursor.name, inductive.name, "rec")
        || !acc_inductive_type(export, inductive.ty, *level)
        || !acc_constructor_type(export, constructor.ty, inductive.name, *level)
        || !recursor_metadata_admissible(
            export,
            inductive,
            &block.constructors,
            recursor,
            false,
            true,
        )
        || !acc_recursor_type(
            export,
            recursor.ty,
            inductive.name,
            constructor.name,
            *level,
            *motive_level,
        )
        || !acc_recursor_rule(
            export,
            recursor,
            inductive.name,
            constructor.name,
            *level,
            *motive_level,
        )
    {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_polymorphic_type(inductive.name, &inductive.level_params, inductive.ty),
            derived_constructor(constructor),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    install_certified_recursor_reduction(derivation.finish(), &block.constructors, recursor)
}

fn nat_le_application(
    export: &ResolvedExport,
    expression: ExprId,
    le: NameId,
    lower: u64,
    upper: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 2
        && is_empty_constant(export, head, le)
        && are_bvars(export, &arguments, &[lower, upper])
}

fn nat_le_refl_application(
    export: &ResolvedExport,
    expression: ExprId,
    refl: NameId,
    value: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    matches!(arguments.as_slice(), [argument]
        if is_empty_constant(export, head, refl)
            && is_bvar(export, *argument, value))
}

fn nat_le_step_application(
    export: &ResolvedExport,
    expression: ExprId,
    step: NameId,
    lower: u64,
    upper: u64,
    proof: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 3
        && is_empty_constant(export, head, step)
        && are_bvars(export, &arguments, &[lower, upper, proof])
}

fn nat_succ_bvar(export: &ResolvedExport, expression: ExprId, succ: NameId, value: u64) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::App { fun, arg })
            if is_empty_constant(export, *fun, succ)
                && is_bvar(export, *arg, value)
    )
}

fn nat_le_type(export: &ResolvedExport, expression: ExprId, nat: NameId) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    matches!(domains.as_slice(), [lower, upper]
        if is_empty_constant(export, *lower, nat)
            && is_empty_constant(export, *upper, nat)
            && is_prop_sort(export, result))
}

fn nat_le_refl_type(export: &ResolvedExport, expression: ExprId, nat: NameId, le: NameId) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 1) else {
        return false;
    };
    matches!(domains.as_slice(), [value]
        if is_empty_constant(export, *value, nat)
            && nat_le_application(export, result, le, 0, 0))
}

fn nat_le_step_type(
    export: &ResolvedExport,
    expression: ExprId,
    nat: NameId,
    succ: NameId,
    le: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [lower, upper, proof] = domains.as_slice() else {
        return false;
    };
    if !is_empty_constant(export, *lower, nat)
        || !is_empty_constant(export, *upper, nat)
        || !nat_le_application(export, *proof, le, 1, 0)
    {
        return false;
    }
    let (head, arguments) = application_spine(export, result);
    let [lower_arg, upper_arg] = arguments.as_slice() else {
        return false;
    };
    is_empty_constant(export, head, le)
        && is_bvar(export, *lower_arg, 2)
        && nat_succ_bvar(export, *upper_arg, succ, 1)
}

fn nat_le_motive_type(
    export: &ResolvedExport,
    expression: ExprId,
    nat: NameId,
    le: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [upper, proof] = domains.as_slice() else {
        return false;
    };
    is_empty_constant(export, *upper, nat)
        && nat_le_application(export, *proof, le, 1, 0)
        && is_prop_sort(export, result)
}

fn nat_le_refl_minor_type(export: &ResolvedExport, expression: ExprId, refl: NameId) -> bool {
    let (head, arguments) = application_spine(export, expression);
    let [upper, proof] = arguments.as_slice() else {
        return false;
    };
    is_bvar(export, head, 0)
        && is_bvar(export, *upper, 1)
        && nat_le_refl_application(export, *proof, refl, 1)
}

fn nat_le_step_minor_type(
    export: &ResolvedExport,
    expression: ExprId,
    nat: NameId,
    succ: NameId,
    le: NameId,
    step: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 3) else {
        return false;
    };
    let [upper, proof, induction_hypothesis] = domains.as_slice() else {
        return false;
    };
    if !is_empty_constant(export, *upper, nat)
        || !nat_le_application(export, *proof, le, 3, 0)
        || !is_binary_bvar_application(export, *induction_hypothesis, 3, 1, 0)
    {
        return false;
    }
    let (motive, arguments) = application_spine(export, result);
    let [next_upper, stepped] = arguments.as_slice() else {
        return false;
    };
    is_bvar(export, motive, 4)
        && nat_succ_bvar(export, *next_upper, succ, 2)
        && nat_le_step_application(export, *stepped, step, 5, 2, 1)
}

fn nat_le_recursor_type(
    export: &ResolvedExport,
    recursor: &Recursor,
    nat: NameId,
    succ: NameId,
    le: NameId,
    refl: NameId,
    step: NameId,
) -> bool {
    if !recursor.level_params.is_empty() {
        return false;
    }
    let Some((domains, result)) = pi_spine(export, recursor.ty, 6) else {
        return false;
    };
    let [lower, motive, refl_minor, step_minor, upper, proof] = domains.as_slice() else {
        return false;
    };
    if !is_empty_constant(export, *lower, nat)
        || !nat_le_motive_type(export, *motive, nat, le)
        || !nat_le_refl_minor_type(export, *refl_minor, refl)
        || !nat_le_step_minor_type(export, *step_minor, nat, succ, le, step)
        || !is_empty_constant(export, *upper, nat)
        || !nat_le_application(export, *proof, le, 4, 0)
    {
        return false;
    }
    is_binary_bvar_application(export, result, 4, 1, 0)
}

fn nat_le_recursor_rules(
    export: &ResolvedExport,
    recursor: &Recursor,
    nat: NameId,
    succ: NameId,
    le: NameId,
    refl: NameId,
    step: NameId,
) -> bool {
    let [refl_rule, step_rule] = recursor.rules.as_slice() else {
        return false;
    };

    let refl_ok = lam_spine(export, refl_rule.rhs, 4).is_some_and(|(domains, result)| {
        let [lower, motive, refl_minor, step_minor] = domains.as_slice() else {
            return false;
        };
        is_empty_constant(export, *lower, nat)
            && nat_le_motive_type(export, *motive, nat, le)
            && nat_le_refl_minor_type(export, *refl_minor, refl)
            && nat_le_step_minor_type(export, *step_minor, nat, succ, le, step)
            && is_bvar(export, result, 1)
    });

    let step_ok = lam_spine(export, step_rule.rhs, 6).is_some_and(|(domains, result)| {
        let [lower, motive, refl_minor, step_minor, upper, proof] = domains.as_slice() else {
            return false;
        };
        if !is_empty_constant(export, *lower, nat)
            || !nat_le_motive_type(export, *motive, nat, le)
            || !nat_le_refl_minor_type(export, *refl_minor, refl)
            || !nat_le_step_minor_type(export, *step_minor, nat, succ, le, step)
            || !is_empty_constant(export, *upper, nat)
            || !nat_le_application(export, *proof, le, 4, 0)
        {
            return false;
        }
        let Some(Expr::App {
            fun: step_at_proof,
            arg: recursive_call,
        }) = export.exprs.get(result)
        else {
            return false;
        };
        if !is_binary_bvar_application(export, *step_at_proof, 2, 1, 0) {
            return false;
        }
        let (head, arguments) = application_spine(export, *recursive_call);
        arguments.len() == 6
            && is_empty_constant(export, head, recursor.name)
            && are_bvars(export, &arguments, &[5, 4, 3, 2, 1, 0])
    });

    refl_ok && step_ok
}

fn check_exact_nat_le(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [refl, step], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };
    let Some(nat) = environment.nat_primitives() else {
        return Err(Verdict::Unknown);
    };

    if inductive.num_params != 1
        || inductive.num_indices != 1
        || inductive.num_nested != 0
        || !inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || !inductive.level_params.is_empty()
        || refl.is_unsafe
        || step.is_unsafe
        || recursor.is_unsafe
    {
        return Err(Verdict::Unknown);
    }

    if inductive.all != [inductive.name]
        || inductive.constructors != [refl.name, step.name]
        || !name_is_child_str(export, inductive.name, nat.type_name, "le")
        || !nat_le_type(export, inductive.ty, nat.type_name)
        || refl.index != 0
        || refl.inductive != inductive.name
        || !refl.level_params.is_empty()
        || refl.num_params != 1
        || refl.num_fields != 0
        || !name_is_child_str(export, refl.name, inductive.name, "refl")
        || !nat_le_refl_type(export, refl.ty, nat.type_name, inductive.name)
        || step.index != 1
        || step.inductive != inductive.name
        || !step.level_params.is_empty()
        || step.num_params != 1
        || step.num_fields != 2
        || !name_is_child_str(export, step.name, inductive.name, "step")
        || !nat_le_step_type(export, step.ty, nat.type_name, nat.succ, inductive.name)
        || !recursor_metadata_admissible(
            export,
            inductive,
            &block.constructors,
            recursor,
            false,
            recursor.level_params.is_empty(),
        )
        || !nat_le_recursor_type(
            export,
            recursor,
            nat.type_name,
            nat.succ,
            inductive.name,
            refl.name,
            step.name,
        )
        || !nat_le_recursor_rules(
            export,
            recursor,
            nat.type_name,
            nat.succ,
            inductive.name,
            refl.name,
            step.name,
        )
    {
        return Err(Verdict::Reject);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_type(inductive.name, inductive.ty),
            derived_constructor(refl),
            derived_constructor(step),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    install_certified_recursor_reduction(derivation.finish(), &block.constructors, recursor)
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
    let constructor_names_ok = if name_is_root_str(export, inductive.name, "N") {
        (name_is_child_str(export, zero.name, inductive.name, "zero")
            && name_is_child_str(export, succ.name, inductive.name, "succ"))
            || (name_is_child_str(export, zero.name, inductive.name, "O")
                && name_is_child_str(export, succ.name, inductive.name, "S"))
    } else {
        name_is_child_str(export, zero.name, inductive.name, "zero")
            && name_is_child_str(export, succ.name, inductive.name, "succ")
    };

    if inductive.all != [inductive.name]
        || inductive.constructors != [zero.name, succ.name]
        || zero.index != 0
        || zero.inductive != inductive.name
        || !zero.level_params.is_empty()
        || zero.num_fields != 0
        || zero.num_params != 0
        || !constructor_names_ok
        || !is_empty_constant(export, zero.ty, inductive.name)
        || succ.index != 1
        || succ.inductive != inductive.name
        || !succ.level_params.is_empty()
        || succ.num_fields != 1
        || succ.num_params != 0
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
    let environment =
        install_certified_recursor_reduction(derivation.finish(), &block.constructors, recursor)?;
    let Some(type_expr) = export.exprs.iter_raw().find_map(|(raw, expression)| {
        matches!(
            expression,
            Expr::Const { name, levels }
                if *name == inductive.name && levels.is_empty()
        )
        .then_some(ExprId(raw))
    }) else {
        return Err(Verdict::Unknown);
    };
    environment
        .install_nat_primitives(NatPrimitives {
            type_name: inductive.name,
            type_expr,
            zero: zero.name,
            succ: succ.name,
            recursor: recursor.name,
            add: None,
            sub: None,
            ble: None,
        })
        .map_err(|_| Verdict::Reject)
}

fn install_certified_recursor_reduction(
    environment: Environment,
    constructors: &[Constructor],
    recursor: &Recursor,
) -> Result<Environment, Verdict> {
    if constructors.len() != recursor.rules.len() {
        return Err(Verdict::Reject);
    }
    let rules = constructors
        .iter()
        .zip(&recursor.rules)
        .map(|(constructor, rule)| {
            Ok(RecursorRule {
                constructor: constructor.name,
                num_params: usize::try_from(constructor.num_params).map_err(|_| Verdict::Reject)?,
                num_fields: usize::try_from(constructor.num_fields).map_err(|_| Verdict::Reject)?,
                rhs: rule.rhs,
            })
        })
        .collect::<Result<Vec<_>, Verdict>>()?;
    let reduction = RecursorReduction {
        num_params: usize::try_from(recursor.num_params).map_err(|_| Verdict::Reject)?,
        num_indices: usize::try_from(recursor.num_indices).map_err(|_| Verdict::Reject)?,
        level_params: recursor.level_params.clone(),
        rules,
    };
    environment
        .install_recursor_reduction(recursor.name, reduction)
        .map_err(|_| Verdict::Reject)
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

/// Residual-generated closed reflexive function-tree law.
///
/// One safe closed Type-valued recursive+reflexive inductive has a nullary
/// leaf and one node field D -> I for an already-declared closed domain D.
/// The recursor must expose the exact pointwise induction hypothesis and rule
/// equation.  This is structural and grants no authority to parameterized,
/// indexed, nested, unsafe, multi-field, or differently reflexive families.
fn exact_closed_reflexive_tree_candidate(export: &ResolvedExport, block: &InductiveBlock) -> bool {
    let ([inductive], [leaf, node], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return false;
    };

    if inductive.num_params != 0
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || !inductive.is_recursive
        || !inductive.is_reflexive
        || inductive.is_unsafe
        || !inductive.level_params.is_empty()
        || inductive.all != [inductive.name]
        || inductive.constructors != [leaf.name, node.name]
    {
        return false;
    }

    let type_level_ok = matches!(
        export.exprs.get(inductive.ty),
        Some(Expr::Sort(level))
            if matches!(
                export.levels.get(*level),
                Some(Level::Succ(inner))
                    if matches!(export.levels.get(*inner), Some(Level::Zero))
            )
    );
    if !type_level_ok
        || leaf.index != 0
        || leaf.inductive != inductive.name
        || leaf.is_unsafe
        || !leaf.level_params.is_empty()
        || leaf.num_params != 0
        || leaf.num_fields != 0
        || !is_empty_constant(export, leaf.ty, inductive.name)
        || node.index != 1
        || node.inductive != inductive.name
        || node.is_unsafe
        || !node.level_params.is_empty()
        || node.num_params != 0
        || node.num_fields != 1
        || recursor.is_unsafe
        || !recursor_metadata_admissible(
            export,
            inductive,
            &block.constructors,
            recursor,
            false,
            recursor.level_params.len() == 1,
        )
    {
        return false;
    }

    let Some(domain) = reflexive_tree_constructor_domain(export, node.ty, inductive.name) else {
        return false;
    };
    reflexive_tree_recursor_obligations(
        export,
        inductive.name,
        leaf.name,
        node.name,
        domain,
        recursor,
    )
}

fn check_exact_closed_reflexive_tree(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [leaf, node], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };
    if !exact_closed_reflexive_tree_candidate(export, block) {
        return Err(Verdict::Unknown);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_type(inductive.name, inductive.ty),
            derived_constructor(leaf),
            derived_constructor(node),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    install_certified_recursor_reduction(derivation.finish(), &block.constructors, recursor)
}

fn reflexive_tree_constructor_domain(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
) -> Option<NameId> {
    let Expr::Pi {
        domain: field,
        body: result,
    } = export.exprs.get(expression)?
    else {
        return None;
    };
    if !is_empty_constant(export, *result, inductive) {
        return None;
    }
    let Expr::Pi {
        domain,
        body: recursive_result,
    } = export.exprs.get(*field)?
    else {
        return None;
    };
    if !is_empty_constant(export, *recursive_result, inductive) {
        return None;
    }
    let Expr::Const { name, levels } = export.exprs.get(*domain)? else {
        return None;
    };
    levels.is_empty().then_some(*name)
}

fn reflexive_tree_field_type(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    domain: NameId,
) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::Pi {
            domain: field_domain,
            body,
        }) if is_empty_constant(export, *field_domain, domain)
            && is_empty_constant(export, *body, inductive)
    )
}

fn reflexive_tree_node_application(
    export: &ResolvedExport,
    expression: ExprId,
    node: NameId,
    field: u64,
) -> bool {
    matches!(
        export.exprs.get(expression),
        Some(Expr::App { fun, arg })
            if is_empty_constant(export, *fun, node)
                && is_bvar(export, *arg, field)
    )
}

fn reflexive_tree_node_minor(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    node: NameId,
    domain: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    let [field, induction_hypothesis] = domains.as_slice() else {
        return false;
    };
    if !reflexive_tree_field_type(export, *field, inductive, domain) {
        return false;
    }

    let Some(Expr::Pi {
        domain: ih_domain,
        body: ih_body,
    }) = export.exprs.get(*induction_hypothesis)
    else {
        return false;
    };
    let Some(Expr::App {
        fun: ih_motive,
        arg: field_at_point,
    }) = export.exprs.get(*ih_body)
    else {
        return false;
    };
    if !is_empty_constant(export, *ih_domain, domain)
        || !is_bvar(export, *ih_motive, 3)
        || !is_bvar_application(export, *field_at_point, 1, 0)
    {
        return false;
    }

    matches!(
        export.exprs.get(result),
        Some(Expr::App {
            fun: result_motive,
            arg: constructed,
        }) if is_bvar(export, *result_motive, 3)
            && reflexive_tree_node_application(export, *constructed, node, 1)
    )
}

fn reflexive_tree_recursor_call(
    export: &ResolvedExport,
    expression: ExprId,
    recursor: NameId,
    motive_level: NameId,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    let [motive, leaf_minor, node_minor, target] = arguments.as_slice() else {
        return false;
    };
    is_unary_polymorphic_constant(export, head, recursor, motive_level)
        && is_bvar(export, *motive, 4)
        && is_bvar(export, *leaf_minor, 3)
        && is_bvar(export, *node_minor, 2)
        && is_bvar_application(export, *target, 1, 0)
}

fn reflexive_tree_recursor_obligations(
    export: &ResolvedExport,
    inductive: NameId,
    leaf: NameId,
    node: NameId,
    domain: NameId,
    recursor: &Recursor,
) -> bool {
    let [motive_level] = recursor.level_params.as_slice() else {
        return false;
    };

    let motive_ok = |expression: ExprId| {
        matches!(
            export.exprs.get(expression),
            Some(Expr::Pi {
                domain: target,
                body: result,
            }) if is_empty_constant(export, *target, inductive)
                && is_sort_parameter(export, *result, *motive_level)
        )
    };

    let Some((type_domains, type_result)) = pi_spine(export, recursor.ty, 4) else {
        return false;
    };
    let [motive, leaf_minor, node_minor, target] = type_domains.as_slice() else {
        return false;
    };
    if !motive_ok(*motive)
        || !is_bvar_applied_to_constant(export, *leaf_minor, 0, leaf)
        || !reflexive_tree_node_minor(export, *node_minor, inductive, node, domain)
        || !is_empty_constant(export, *target, inductive)
        || !is_bvar_application(export, type_result, 3, 0)
    {
        return false;
    }

    let [leaf_rule, node_rule] = recursor.rules.as_slice() else {
        return false;
    };
    let leaf_ok = lam_spine(export, leaf_rule.rhs, 3).is_some_and(|(domains, result)| {
        let [motive, leaf_minor, node_minor] = domains.as_slice() else {
            return false;
        };
        motive_ok(*motive)
            && is_bvar_applied_to_constant(export, *leaf_minor, 0, leaf)
            && reflexive_tree_node_minor(export, *node_minor, inductive, node, domain)
            && is_bvar(export, result, 1)
    });

    let node_ok = lam_spine(export, node_rule.rhs, 4).is_some_and(|(domains, result)| {
        let [motive, leaf_minor, node_minor, field] = domains.as_slice() else {
            return false;
        };
        if !motive_ok(*motive)
            || !is_bvar_applied_to_constant(export, *leaf_minor, 0, leaf)
            || !reflexive_tree_node_minor(export, *node_minor, inductive, node, domain)
            || !reflexive_tree_field_type(export, *field, inductive, domain)
        {
            return false;
        }

        let (minor_head, arguments) = application_spine(export, result);
        let [field_arg, pointwise_ih] = arguments.as_slice() else {
            return false;
        };
        if !is_bvar(export, minor_head, 1) || !is_bvar(export, *field_arg, 0) {
            return false;
        }
        let Some(Expr::Lam {
            domain: ih_domain,
            body: recursive_call,
        }) = export.exprs.get(*pointwise_ih)
        else {
            return false;
        };
        is_empty_constant(export, *ih_domain, domain)
            && reflexive_tree_recursor_call(export, *recursive_call, recursor.name, *motive_level)
    });

    leaf_ok && node_ok
}

/// Residual-generated closed binary-tree law.
///
/// This is deliberately structural rather than name-sealed: one safe closed
/// Type-valued recursive inductive, a nullary leaf, a binary node whose two
/// fields are direct recursive occurrences, and one canonical recursor with
/// the exact derived motive/minor/rule equations.  It grants no authority to
/// parameterized, indexed, reflexive, nested, unsafe, or differently-shaped
/// recursive families.
fn exact_closed_binary_tree_candidate(export: &ResolvedExport, block: &InductiveBlock) -> bool {
    let ([inductive], [leaf, node], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return false;
    };

    if inductive.num_params != 0
        || inductive.num_indices != 0
        || inductive.num_nested != 0
        || !inductive.is_recursive
        || inductive.is_reflexive
        || inductive.is_unsafe
        || !inductive.level_params.is_empty()
        || inductive.all != [inductive.name]
        || inductive.constructors != [leaf.name, node.name]
    {
        return false;
    }

    let type_level_ok = matches!(
        export.exprs.get(inductive.ty),
        Some(Expr::Sort(level))
            if matches!(
                export.levels.get(*level),
                Some(Level::Succ(inner))
                    if matches!(export.levels.get(*inner), Some(Level::Zero))
            )
    );
    if !type_level_ok
        || leaf.index != 0
        || leaf.inductive != inductive.name
        || leaf.is_unsafe
        || !leaf.level_params.is_empty()
        || leaf.num_params != 0
        || leaf.num_fields != 0
        || !is_empty_constant(export, leaf.ty, inductive.name)
        || node.index != 1
        || node.inductive != inductive.name
        || node.is_unsafe
        || !node.level_params.is_empty()
        || node.num_params != 0
        || node.num_fields != 2
        || !binary_tree_node_type(export, node.ty, inductive.name)
        || recursor.is_unsafe
        || !recursor_metadata_admissible(
            export,
            inductive,
            &block.constructors,
            recursor,
            false,
            recursor.level_params.len() == 1,
        )
    {
        return false;
    }

    binary_tree_recursor_obligations(export, inductive.name, leaf.name, node.name, recursor)
}

fn check_exact_closed_binary_tree(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [leaf, node], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };
    if !exact_closed_binary_tree_candidate(export, block) {
        return Err(Verdict::Unknown);
    }

    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_type(inductive.name, inductive.ty),
            derived_constructor(leaf),
            derived_constructor(node),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    install_certified_recursor_reduction(derivation.finish(), &block.constructors, recursor)
}

fn binary_tree_node_type(export: &ResolvedExport, expression: ExprId, inductive: NameId) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 2) else {
        return false;
    };
    matches!(
        domains.as_slice(),
        [left, right]
            if is_empty_constant(export, *left, inductive)
                && is_empty_constant(export, *right, inductive)
                && is_empty_constant(export, result, inductive)
    )
}

fn binary_tree_node_application(
    export: &ResolvedExport,
    expression: ExprId,
    node: NameId,
    left: u64,
    right: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    matches!(
        arguments.as_slice(),
        [left_arg, right_arg]
            if is_empty_constant(export, head, node)
                && is_bvar(export, *left_arg, left)
                && is_bvar(export, *right_arg, right)
    )
}

fn binary_tree_node_minor(
    export: &ResolvedExport,
    expression: ExprId,
    inductive: NameId,
    node: NameId,
) -> bool {
    let Some((domains, result)) = pi_spine(export, expression, 4) else {
        return false;
    };
    let [left, right, left_ih, right_ih] = domains.as_slice() else {
        return false;
    };
    is_empty_constant(export, *left, inductive)
        && is_empty_constant(export, *right, inductive)
        && is_bvar_application(export, *left_ih, 3, 1)
        && is_bvar_application(export, *right_ih, 4, 1)
        && matches!(
            export.exprs.get(result),
            Some(Expr::App { fun: motive, arg })
                if is_bvar(export, *motive, 5)
                    && binary_tree_node_application(export, *arg, node, 3, 2)
        )
}

fn binary_tree_recursor_call(
    export: &ResolvedExport,
    expression: ExprId,
    recursor: NameId,
    motive_level: NameId,
    target: u64,
) -> bool {
    let (head, arguments) = application_spine(export, expression);
    arguments.len() == 4
        && is_unary_polymorphic_constant(export, head, recursor, motive_level)
        && are_bvars(export, &arguments, &[4, 3, 2, target])
}

fn binary_tree_recursor_obligations(
    export: &ResolvedExport,
    inductive: NameId,
    leaf: NameId,
    node: NameId,
    recursor: &Recursor,
) -> bool {
    let [motive_level] = recursor.level_params.as_slice() else {
        return false;
    };

    let motive_ok = |expression: ExprId| {
        matches!(
            export.exprs.get(expression),
            Some(Expr::Pi { domain, body })
                if is_empty_constant(export, *domain, inductive)
                    && is_sort_parameter(export, *body, *motive_level)
        )
    };

    let Some((type_domains, type_result)) = pi_spine(export, recursor.ty, 4) else {
        return false;
    };
    let [motive, leaf_minor, node_minor, target] = type_domains.as_slice() else {
        return false;
    };
    let type_ok = motive_ok(*motive)
        && is_bvar_applied_to_constant(export, *leaf_minor, 0, leaf)
        && binary_tree_node_minor(export, *node_minor, inductive, node)
        && is_empty_constant(export, *target, inductive)
        && is_bvar_application(export, type_result, 3, 0);
    if !type_ok {
        return false;
    }

    let [leaf_rule, node_rule] = recursor.rules.as_slice() else {
        return false;
    };
    let leaf_ok = lam_spine(export, leaf_rule.rhs, 3).is_some_and(|(domains, result)| {
        let [motive, leaf_minor, node_minor] = domains.as_slice() else {
            return false;
        };
        motive_ok(*motive)
            && is_bvar_applied_to_constant(export, *leaf_minor, 0, leaf)
            && binary_tree_node_minor(export, *node_minor, inductive, node)
            && is_bvar(export, result, 1)
    });

    let node_ok = lam_spine(export, node_rule.rhs, 5).is_some_and(|(domains, result)| {
        let [motive, leaf_minor, node_minor, left, right] = domains.as_slice() else {
            return false;
        };
        if !motive_ok(*motive)
            || !is_bvar_applied_to_constant(export, *leaf_minor, 0, leaf)
            || !binary_tree_node_minor(export, *node_minor, inductive, node)
            || !is_empty_constant(export, *left, inductive)
            || !is_empty_constant(export, *right, inductive)
        {
            return false;
        }

        let (minor_head, arguments) = application_spine(export, result);
        let [left_arg, right_arg, left_call, right_call] = arguments.as_slice() else {
            return false;
        };
        is_bvar(export, minor_head, 2)
            && is_bvar(export, *left_arg, 1)
            && is_bvar(export, *right_arg, 0)
            && binary_tree_recursor_call(export, *left_call, recursor.name, *motive_level, 1)
            && binary_tree_recursor_call(export, *right_call, recursor.name, *motive_level, 0)
    });

    leaf_ok && node_ok
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
    let environment = derivation.finish();

    // G31 installs executable iota authority only for the exact Bool family.
    // Color and BoolProp retain declaration authority without computation.
    if name_is_root_str(export, inductive.name, "Bool") {
        let rules = block
            .constructors
            .iter()
            .zip(&recursor.rules)
            .map(|(constructor, rule)| {
                Ok(RecursorRule {
                    constructor: constructor.name,
                    num_params: usize::try_from(constructor.num_params)
                        .map_err(|_| Verdict::Reject)?,
                    num_fields: usize::try_from(constructor.num_fields)
                        .map_err(|_| Verdict::Reject)?,
                    rhs: rule.rhs,
                })
            })
            .collect::<Result<Vec<_>, Verdict>>()?;
        let reduction = RecursorReduction {
            num_params: usize::try_from(recursor.num_params).map_err(|_| Verdict::Reject)?,
            num_indices: usize::try_from(recursor.num_indices).map_err(|_| Verdict::Reject)?,
            level_params: recursor.level_params.clone(),
            rules,
        };
        let environment = environment
            .install_recursor_reduction(recursor.name, reduction)
            .map_err(|_| Verdict::Reject)?;
        let [false_ctor, true_ctor] = constructor_names.as_slice() else {
            return Err(Verdict::Reject);
        };
        if !name_is_child_str(export, *false_ctor, inductive.name, "false")
            || !name_is_child_str(export, *true_ctor, inductive.name, "true")
        {
            return Err(Verdict::Unknown);
        }
        environment
            .install_bool_primitives(BoolPrimitives {
                false_ctor: *false_ctor,
                true_ctor: *true_ctor,
            })
            .map_err(|_| Verdict::Reject)
    } else {
        Ok(environment)
    }
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
        let environment = derivation.finish();
        let environment = if matches!(
            self.law,
            BinaryProductSortLaw::And
                | BinaryProductSortLaw::Prod { .. }
                | BinaryProductSortLaw::PProd { .. }
        ) {
            environment
                .install_projection_spec(
                    self.inductive.name,
                    ProjectionSpec {
                        constructor: self.constructor.name,
                        num_params: 2,
                        field_types: vec![
                            ProjectionFieldType::Parameter(0),
                            ProjectionFieldType::Parameter(1),
                        ],
                    },
                )
                .map_err(|_| Verdict::Reject)?
        } else {
            environment
        };

        let environment = if matches!(self.law, BinaryProductSortLaw::PUnit { .. }) {
            environment
                .install_unit_like_type(self.inductive.name)
                .map_err(|_| Verdict::Reject)?
        } else {
            environment
        };

        // G32 reuses G31's already-qualified constructor-iota machine. Only
        // exact Prod opts in here; And/PProd/PUnit/Eq remain opaque.
        if matches!(self.law, BinaryProductSortLaw::Prod { .. }) {
            let [rule] = self.recursor.rules.as_slice() else {
                return Err(Verdict::Reject);
            };
            let reduction = RecursorReduction {
                num_params: usize::try_from(self.recursor.num_params)
                    .map_err(|_| Verdict::Reject)?,
                num_indices: usize::try_from(self.recursor.num_indices)
                    .map_err(|_| Verdict::Reject)?,
                level_params: self.recursor.level_params.clone(),
                rules: vec![RecursorRule {
                    constructor: self.constructor.name,
                    num_params: usize::try_from(self.constructor.num_params)
                        .map_err(|_| Verdict::Reject)?,
                    num_fields: usize::try_from(self.constructor.num_fields)
                        .map_err(|_| Verdict::Reject)?,
                    rhs: rule.rhs,
                }],
            };
            environment
                .install_recursor_reduction(self.recursor.name, reduction)
                .map_err(|_| Verdict::Reject)
        } else {
            Ok(environment)
        }
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
        Judgment::Refuted { obstruction } => {
            if std::env::var_os("NUCLEUS_TRACE_RESIDUAL").is_some() {
                eprintln!("NUCLEUS_REFUTED:{}", obstruction.0);
            }
            Err(Verdict::Reject)
        }
        Judgment::Unknown { residual } => {
            if std::env::var_os("NUCLEUS_TRACE_RESIDUAL").is_some() {
                eprintln!("NUCLEUS_RESIDUAL:{}", residual.0);
            }
            Err(Verdict::Unknown)
        }
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
    fn g26_rejects_impossible_owned_recursor_metadata() {
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
