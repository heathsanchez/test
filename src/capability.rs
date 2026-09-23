//! Residual-generated capability bank.
//!
//! The checker core stays generic: each promoted capability is a guarded,
//! independently-qualified consequence that may decide only the exports inside
//! its earned envelope.  Capabilities are evaluated before ordinary checking;
//! no capability may turn a previously decided opposite verdict into success.

use std::collections::HashSet;

use crate::id::NameId;
use crate::parser::ResolvedExport;
use crate::syntax::Declaration;
use crate::verdict::Verdict;

#[derive(Clone, Copy)]
struct VerifiedCapability {
    id: &'static str,
    apply: fn(&ResolvedExport) -> Option<Verdict>,
}

const CAPABILITIES: &[VerifiedCapability] = &[VerifiedCapability {
    id: "environment.declared-name-uniqueness.v0",
    apply: declared_name_uniqueness,
}];

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
