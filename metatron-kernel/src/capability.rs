//! Residual-generated capability bank.
//!
//! The checker core stays generic: each promoted capability is a guarded,
//! independently-qualified consequence that may decide only the exports inside
//! its earned envelope.  Capabilities are evaluated before ordinary checking;
//! no capability may turn a previously decided opposite verdict into success.

use std::collections::{HashMap, HashSet};

use crate::id::{ExprId, NameId};
use crate::level::{LevelTerm, instantiate_level};
use crate::parser::ResolvedExport;
use crate::syntax::{Declaration, Expr, Name};
use crate::verdict::Verdict;

#[derive(Clone, Copy)]
struct VerifiedCapability {
    id: &'static str,
    apply: fn(&ResolvedExport) -> Option<Verdict>,
}

const CAPABILITIES: &[VerifiedCapability] = &[
    VerifiedCapability {
        id: "environment.declared-name-uniqueness.v0",
        apply: declared_name_uniqueness,
    },
    VerifiedCapability {
        id: "environment.recursor-name-coherence.v0",
        apply: recursor_name_coherence,
    },
    VerifiedCapability {
        id: "projection.prop-dependent-safety.v0",
        apply: prop_projection_safety,
    },
];

pub(crate) fn execute(export: &ResolvedExport) -> Option<Verdict> {
    for capability in CAPABILITIES {
        if let Some(verdict) = (capability.apply)(export) {
            if std::env::var_os("NUCLEUS_TRACE_CAPABILITY").is_some() {
                eprintln!("NUCLEUS_CAPABILITY_HIT:{}:{verdict:?}", capability.id);
            }
            return Some(verdict);
        }
    }
    None
}

/// Lean environments cannot contain two declarations with the same name.
///
/// Earlier Nucleus generations already reject duplicates that arrive as
/// sequential ordinary declarations via Environment::extend.  The residual
/// occurs when a duplicate is hidden inside an inductive block and semantic
/// support for that block is otherwise UNKNOWN.  This capability extracts the
/// smaller consequential law: declaration-name uniqueness is independent of
/// the inductive family's semantics.
fn declared_name_uniqueness(export: &ResolvedExport) -> Option<Verdict> {
    let mut seen = HashSet::<NameId>::new();
    for declaration in &export.declarations {
        let mut insert = |name: NameId| {
            if seen.insert(name) {
                None
            } else {
                Some(Verdict::Reject)
            }
        };

        match declaration {
            Declaration::Axiom { name, .. }
            | Declaration::Definition { name, .. }
            | Declaration::Theorem { name, .. }
            | Declaration::Quot { name, .. } => {
                if let Some(verdict) = insert(*name) {
                    return Some(verdict);
                }
            }
            Declaration::Inductive(block) => {
                for inductive in &block.types {
                    if let Some(verdict) = insert(inductive.name) {
                        return Some(verdict);
                    }
                }
                for constructor in &block.constructors {
                    if let Some(verdict) = insert(constructor.name) {
                        return Some(verdict);
                    }
                }
                for recursor in &block.recursors {
                    if let Some(verdict) = insert(recursor.name) {
                        return Some(verdict);
                    }
                }
            }
            Declaration::Unsupported { .. } => {}
        }
    }
    None
}

/// Every recursor owned by an exported inductive block has the reserved
/// `<inductive>.rec` name.  This environment-level invariant is independent
/// of whether Nucleus already supports the inductive family's semantics.
fn recursor_name_coherence(export: &ResolvedExport) -> Option<Verdict> {
    for declaration in &export.declarations {
        let Declaration::Inductive(block) = declaration else {
            continue;
        };
        for recursor in &block.recursors {
            let canonical = matches!(
                export.names.get(recursor.name),
                Some(Name::Str { prefix, value })
                    if value == "rec"
                        && block.types.iter().any(|inductive| inductive.name == *prefix)
            );
            if !canonical {
                return Some(Verdict::Reject);
            }
        }
    }
    None
}

#[derive(Clone, Debug)]
struct PropProjectionTarget {
    level_params: Vec<NameId>,
    constructor_level_params: Vec<NameId>,
    constructor_ty: ExprId,
    num_fields: usize,
}

/// Negative-only fragment of Lean's kernel projection admissibility rule.
///
/// For a Prop-valued, zero-parameter, zero-index, safe, nonrecursive,
/// one-constructor inductive, Lean permits a projection only when the projected
/// field is itself a proposition and no preceding non-Prop field must be
/// projected to instantiate a dependent later field.  This capability fires
/// only when those facts are definite from the export.  It never grants
/// projection authority; every uncertain case remains on the ordinary UNKNOWN
/// path.
fn prop_projection_safety(export: &ResolvedExport) -> Option<Verdict> {
    let projection_types: HashSet<NameId> = export
        .exprs
        .values()
        .filter_map(|expression| match expression {
            Expr::Proj { type_name, .. } => Some(*type_name),
            _ => None,
        })
        .collect();
    if projection_types.is_empty() {
        return None;
    }

    let target_names: HashSet<NameId> = projection_types
        .into_iter()
        .filter(|type_name| prop_projection_target(export, *type_name).is_some())
        .collect();
    if target_names.is_empty() {
        return None;
    }

    let mut relevance = HashMap::<ExprId, bool>::new();
    for declaration in &export.declarations {
        let mut roots = Vec::new();
        match declaration {
            Declaration::Axiom { ty, .. } | Declaration::Quot { ty, .. } => roots.push(*ty),
            Declaration::Definition { ty, value, .. } | Declaration::Theorem { ty, value, .. } => {
                roots.push(*ty);
                roots.push(*value);
            }
            Declaration::Inductive(block) => {
                for inductive in &block.types {
                    roots.push(inductive.ty);
                }
                for constructor in &block.constructors {
                    roots.push(constructor.ty);
                }
                for recursor in &block.recursors {
                    roots.push(recursor.ty);
                    for rule in &recursor.rules {
                        roots.push(rule.rhs);
                    }
                }
            }
            Declaration::Unsupported { .. } => {}
        }

        for root in roots {
            if expression_contains_invalid_prop_projection(
                export,
                root,
                &target_names,
                &mut relevance,
                &mut Vec::new(),
                0,
            ) {
                return Some(Verdict::Reject);
            }
        }
    }
    None
}

fn expression_may_contain_target_projection(
    export: &ResolvedExport,
    expression: ExprId,
    target_names: &HashSet<NameId>,
    memo: &mut HashMap<ExprId, bool>,
    depth: usize,
) -> bool {
    if let Some(cached) = memo.get(&expression) {
        return *cached;
    }
    if depth > 4096 {
        return true;
    }
    let Some(node) = export.exprs.get(expression) else {
        return true;
    };
    let result = match node {
        Expr::Proj {
            type_name,
            structure,
            ..
        } => {
            target_names.contains(type_name)
                || expression_may_contain_target_projection(
                    export,
                    *structure,
                    target_names,
                    memo,
                    depth + 1,
                )
        }
        Expr::App { fun, arg } => {
            expression_may_contain_target_projection(export, *fun, target_names, memo, depth + 1)
                || expression_may_contain_target_projection(
                    export,
                    *arg,
                    target_names,
                    memo,
                    depth + 1,
                )
        }
        Expr::Lam { domain, body } | Expr::Pi { domain, body } => {
            expression_may_contain_target_projection(
                export,
                *domain,
                target_names,
                memo,
                depth + 1,
            ) || expression_may_contain_target_projection(
                export,
                *body,
                target_names,
                memo,
                depth + 1,
            )
        }
        Expr::Let { ty, value, body } => {
            expression_may_contain_target_projection(export, *ty, target_names, memo, depth + 1)
                || expression_may_contain_target_projection(
                    export,
                    *value,
                    target_names,
                    memo,
                    depth + 1,
                )
                || expression_may_contain_target_projection(
                    export,
                    *body,
                    target_names,
                    memo,
                    depth + 1,
                )
        }
        Expr::BVar(_) | Expr::NatLit(_) | Expr::Sort(_) | Expr::Const { .. } => false,
    };
    memo.insert(expression, result);
    result
}

fn expression_contains_invalid_prop_projection(
    export: &ResolvedExport,
    expression: ExprId,
    target_names: &HashSet<NameId>,
    relevance: &mut HashMap<ExprId, bool>,
    context: &mut Vec<ExprId>,
    depth: usize,
) -> bool {
    if depth > 4096 {
        return false;
    }
    if !expression_may_contain_target_projection(
        export,
        expression,
        target_names,
        relevance,
        depth,
    ) {
        return false;
    }
    let Some(node) = export.exprs.get(expression) else {
        return false;
    };
    match node {
        Expr::Proj {
            type_name,
            index,
            structure,
        } => {
            if target_names.contains(type_name)
                && let Some(Expr::BVar(bvar)) = export.exprs.get(*structure)
                && let Ok(bvar) = usize::try_from(*bvar)
                && let Some(structure_ty) = context.get(bvar).copied()
                && projection_is_definitely_invalid(export, *type_name, *index, structure_ty)
            {
                return true;
            }
            expression_contains_invalid_prop_projection(
                export,
                *structure,
                target_names,
                relevance,
                context,
                depth + 1,
            )
        }
        Expr::App { fun, arg } => {
            expression_contains_invalid_prop_projection(
                export,
                *fun,
                target_names,
                relevance,
                context,
                depth + 1,
            ) || expression_contains_invalid_prop_projection(
                export,
                *arg,
                target_names,
                relevance,
                context,
                depth + 1,
            )
        }
        Expr::Lam { domain, body } | Expr::Pi { domain, body } => {
            if expression_contains_invalid_prop_projection(
                export,
                *domain,
                target_names,
                relevance,
                context,
                depth + 1,
            ) {
                return true;
            }
            context.insert(0, *domain);
            let result = expression_contains_invalid_prop_projection(
                export,
                *body,
                target_names,
                relevance,
                context,
                depth + 1,
            );
            context.remove(0);
            result
        }
        Expr::Let { ty, value, body } => {
            if expression_contains_invalid_prop_projection(
                export,
                *ty,
                target_names,
                relevance,
                context,
                depth + 1,
            ) || expression_contains_invalid_prop_projection(
                export,
                *value,
                target_names,
                relevance,
                context,
                depth + 1,
            ) {
                return true;
            }
            context.insert(0, *ty);
            let result = expression_contains_invalid_prop_projection(
                export,
                *body,
                target_names,
                relevance,
                context,
                depth + 1,
            );
            context.remove(0);
            result
        }
        Expr::BVar(_) | Expr::NatLit(_) | Expr::Sort(_) | Expr::Const { .. } => false,
    }
}

fn projection_is_definitely_invalid(
    export: &ResolvedExport,
    type_name: NameId,
    index: u64,
    structure_ty: ExprId,
) -> bool {
    let Some(target) = prop_projection_target(export, type_name) else {
        return false;
    };
    let Ok(index) = usize::try_from(index) else {
        return false;
    };
    if index >= target.num_fields {
        return false;
    }

    let (head, arguments) = application_spine(export, structure_ty);
    if !arguments.is_empty() {
        return false;
    }
    let Some(Expr::Const {
        name,
        levels: actual_levels,
    }) = export.exprs.get(head)
    else {
        return false;
    };
    if *name != type_name || actual_levels.len() != target.level_params.len() {
        return false;
    }

    let empty = HashMap::<NameId, LevelTerm>::new();
    let mut outer_substitution = HashMap::<NameId, LevelTerm>::new();
    for (parameter, level) in target.level_params.iter().zip(actual_levels) {
        let Ok(level) = instantiate_level(&export.levels, *level, &empty, 256) else {
            return false;
        };
        outer_substitution.insert(*parameter, level);
    }

    if target.constructor_level_params != target.level_params {
        return false;
    }

    let mut current = target.constructor_ty;
    for _ in 0..index {
        let Some(Expr::Pi { domain, body }) = export.exprs.get(current) else {
            return false;
        };
        if expression_has_loose_bvars(export, *body, 0, 0) {
            match proposition_status(export, *domain, &outer_substitution) {
                Some(false) => return true,
                Some(true) | None => return false,
            }
        }
        current = *body;
    }

    let Some(Expr::Pi { domain, .. }) = export.exprs.get(current) else {
        return false;
    };
    matches!(
        proposition_status(export, *domain, &outer_substitution),
        Some(false)
    )
}

fn prop_projection_target(
    export: &ResolvedExport,
    type_name: NameId,
) -> Option<PropProjectionTarget> {
    for declaration in &export.declarations {
        let Declaration::Inductive(block) = declaration else {
            continue;
        };
        if block.types.len() != 1 || block.constructors.len() != 1 {
            continue;
        }
        let inductive = &block.types[0];
        let constructor = &block.constructors[0];
        if inductive.name != type_name
            || constructor.inductive != type_name
            || inductive.num_params != 0
            || inductive.num_indices != 0
            || inductive.num_nested != 0
            || inductive.is_recursive
            || inductive.is_reflexive
            || inductive.is_unsafe
            || constructor.is_unsafe
            || constructor.num_params != 0
        {
            continue;
        }

        let Some(Expr::Sort(level)) = export.exprs.get(inductive.ty) else {
            continue;
        };
        let empty = HashMap::<NameId, LevelTerm>::new();
        let Ok(level) = instantiate_level(&export.levels, *level, &empty, 256) else {
            continue;
        };
        if proposition_level_status(&level) != Some(true) {
            continue;
        }

        let Ok(num_fields) = usize::try_from(constructor.num_fields) else {
            continue;
        };
        return Some(PropProjectionTarget {
            level_params: inductive.level_params.clone(),
            constructor_level_params: constructor.level_params.clone(),
            constructor_ty: constructor.ty,
            num_fields,
        });
    }
    None
}

fn proposition_status(
    export: &ResolvedExport,
    expression: ExprId,
    outer_substitution: &HashMap<NameId, LevelTerm>,
) -> Option<bool> {
    let (head, arguments) = application_spine(export, expression);
    let Expr::Const { name, levels } = export.exprs.get(head)? else {
        return None;
    };
    let (level_params, declaration_ty) = declaration_type(export, *name)?;
    if level_params.len() != levels.len() {
        return None;
    }

    let (arity, result) = pi_arity_and_result(export, declaration_ty)?;
    if arguments.len() < arity {
        return None;
    }
    let Expr::Sort(result_level) = export.exprs.get(result)? else {
        return None;
    };

    let mut substitution = HashMap::<NameId, LevelTerm>::new();
    for (parameter, level) in level_params.iter().zip(levels) {
        let level = instantiate_level(&export.levels, *level, outer_substitution, 256).ok()?;
        substitution.insert(*parameter, level);
    }
    let level = instantiate_level(&export.levels, *result_level, &substitution, 256).ok()?;
    proposition_level_status(&level)
}

fn proposition_level_status(level: &LevelTerm) -> Option<bool> {
    match level {
        LevelTerm::Zero => Some(true),
        LevelTerm::Succ(_) => Some(false),
        LevelTerm::Max(left, right) => {
            let left = proposition_level_status(left);
            let right = proposition_level_status(right);
            match (left, right) {
                (Some(true), Some(true)) => Some(true),
                (Some(false), _) | (_, Some(false)) => Some(false),
                _ => None,
            }
        }
        LevelTerm::IMax(_, right) => match proposition_level_status(right) {
            Some(true) => Some(true),
            Some(false) => Some(false),
            None => None,
        },
        LevelTerm::Param(_) => None,
    }
}

fn declaration_type(export: &ResolvedExport, name: NameId) -> Option<(Vec<NameId>, ExprId)> {
    for declaration in &export.declarations {
        match declaration {
            Declaration::Axiom {
                name: candidate,
                level_params,
                ty,
            }
            | Declaration::Definition {
                name: candidate,
                level_params,
                ty,
                ..
            }
            | Declaration::Theorem {
                name: candidate,
                level_params,
                ty,
                ..
            }
            | Declaration::Quot {
                name: candidate,
                level_params,
                ty,
                ..
            } if *candidate == name => return Some((level_params.clone(), *ty)),
            Declaration::Inductive(block) => {
                for inductive in &block.types {
                    if inductive.name == name {
                        return Some((inductive.level_params.clone(), inductive.ty));
                    }
                }
                for constructor in &block.constructors {
                    if constructor.name == name {
                        return Some((constructor.level_params.clone(), constructor.ty));
                    }
                }
                for recursor in &block.recursors {
                    if recursor.name == name {
                        return Some((recursor.level_params.clone(), recursor.ty));
                    }
                }
            }
            _ => {}
        }
    }
    None
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

fn pi_arity_and_result(export: &ResolvedExport, expression: ExprId) -> Option<(usize, ExprId)> {
    let mut arity = 0usize;
    let mut current = expression;
    for _ in 0..4096 {
        match export.exprs.get(current)? {
            Expr::Pi { body, .. } => {
                arity = arity.checked_add(1)?;
                current = *body;
            }
            _ => return Some((arity, current)),
        }
    }
    None
}

fn expression_has_loose_bvars(
    export: &ResolvedExport,
    expression: ExprId,
    binder_depth: u64,
    depth: usize,
) -> bool {
    if depth > 4096 {
        return true;
    }
    let Some(node) = export.exprs.get(expression) else {
        return true;
    };
    match node {
        Expr::BVar(index) => *index >= binder_depth,
        Expr::App { fun, arg } => {
            expression_has_loose_bvars(export, *fun, binder_depth, depth + 1)
                || expression_has_loose_bvars(export, *arg, binder_depth, depth + 1)
        }
        Expr::Lam { domain, body } | Expr::Pi { domain, body } => {
            expression_has_loose_bvars(export, *domain, binder_depth, depth + 1)
                || expression_has_loose_bvars(
                    export,
                    *body,
                    binder_depth.saturating_add(1),
                    depth + 1,
                )
        }
        Expr::Let { ty, value, body } => {
            expression_has_loose_bvars(export, *ty, binder_depth, depth + 1)
                || expression_has_loose_bvars(export, *value, binder_depth, depth + 1)
                || expression_has_loose_bvars(
                    export,
                    *body,
                    binder_depth.saturating_add(1),
                    depth + 1,
                )
        }
        Expr::Proj { structure, .. } => {
            expression_has_loose_bvars(export, *structure, binder_depth, depth + 1)
        }
        Expr::NatLit(_) | Expr::Sort(_) | Expr::Const { .. } => false,
    }
}


#[cfg(test)]
mod tests {
    use super::declared_name_uniqueness;
    use crate::id::{ExprId, IdTable, NameId};
    use crate::parser::{Meta, ResolvedExport};
    use crate::syntax::{Declaration, Name};

    fn export_with(declarations: Vec<Declaration>) -> ResolvedExport {
        ResolvedExport {
            meta: Meta {
                format_version: "3.1.0".to_owned(),
                raw: serde_json::json!({"meta":{"format":{"version":"3.1.0"}}}),
            },
            names: IdTable::<NameId, Name>::default(),
            levels: Default::default(),
            exprs: Default::default(),
            declarations,
        }
    }

    fn definition(name: u64) -> Declaration {
        Declaration::Definition {
            name: NameId(name),
            level_params: vec![],
            ty: ExprId(0),
            value: ExprId(0),
            preferred_for_reduction: false,
        }
    }

    #[test]
    fn distinct_declared_names_do_not_fire() {
        let export = export_with(vec![definition(1), definition(2)]);
        assert_eq!(declared_name_uniqueness(&export), None);
    }

    #[test]
    fn duplicate_declared_names_reject() {
        let export = export_with(vec![definition(1), definition(1)]);
        assert_eq!(
            declared_name_uniqueness(&export),
            Some(crate::verdict::Verdict::Reject)
        );
    }
}
