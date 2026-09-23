//! Shared execution boundary for the closed, nonrecursive inductive families
//! that have independently earned Arena authority.
//!
//! Family-specific code must first derive and validate every exported claim.
//! This module only checks the resulting signatures in dependency order and
//! compiles them to opaque runtime authority.  It deliberately knows nothing
//! about parameters, indices, recursion, iota, projections, or eta.

use std::collections::HashMap;

use crate::convert::DeltaPolicy;
use crate::environment::{ConstantDecl, Environment};
use crate::id::{ExprId, NameId};
use crate::judgment::Judgment;
use crate::level::LevelTerm;
use crate::parser::ResolvedExport;
use crate::typecheck::TypeChecker;
use crate::verdict::Verdict;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum OpaqueInductiveKind {
    Type,
    Constructor,
    Recursor,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct DerivedSignature {
    pub(crate) kind: OpaqueInductiveKind,
    pub(crate) name: NameId,
    pub(crate) level_params: Vec<NameId>,
    pub(crate) ty: ExprId,
}

#[derive(Clone, Debug)]
pub(crate) struct ClosedNonrecursiveDerivation {
    staged: Environment,
}

impl ClosedNonrecursiveDerivation {
    pub(crate) fn begin(prior: &Environment) -> Self {
        Self {
            staged: prior.clone(),
        }
    }

    /// Validate one already-derived signature against exactly the authority
    /// preceding it and stage its opaque executable representative.
    pub(crate) fn promote(
        &mut self,
        export: &ResolvedExport,
        signature: DerivedSignature,
        judgment_steps: usize,
        delta_policy: DeltaPolicy,
    ) -> Result<(), Verdict> {
        #[cfg(feature = "diagnostics")]
        crate::diagnostics::inductive_signature();
        let checker = TypeChecker::with_level_substitution(
            &export.exprs,
            &export.levels,
            &self.staged,
            parameter_substitution(&signature.level_params),
        )
        .with_delta_policy(delta_policy);
        verdict_boundary(checker.is_type(signature.ty, judgment_steps))?;

        let declaration = match signature.kind {
            OpaqueInductiveKind::Type => {
                ConstantDecl::inductive_type(signature.level_params.clone(), signature.ty)
            }
            OpaqueInductiveKind::Constructor => {
                ConstantDecl::constructor(signature.level_params.clone(), signature.ty)
            }
            OpaqueInductiveKind::Recursor => {
                ConstantDecl::recursor(signature.level_params.clone(), signature.ty)
            }
        };
        self.staged = self
            .staged
            .extend(signature.name, declaration)
            .map_err(|_| Verdict::Reject)?;
        Ok(())
    }

    pub(crate) fn promote_all<I>(
        &mut self,
        export: &ResolvedExport,
        signatures: I,
        judgment_steps: usize,
        delta_policy: DeltaPolicy,
    ) -> Result<(), Verdict>
    where
        I: IntoIterator<Item = DerivedSignature>,
    {
        for signature in signatures {
            self.promote(export, signature, judgment_steps, delta_policy)?;
        }
        Ok(())
    }

    /// Commit the derivation. Until this value is returned, all stages remain
    /// local and the caller's persistent environment is unchanged.
    /// Read-only access to the staged authority for conversion-sensitive
    /// signature derivation. This exposes no commit path and does not enlarge
    /// the trusted boundary.
    pub(crate) fn environment(&self) -> &Environment {
        &self.staged
    }

    pub(crate) fn finish(self) -> Environment {
        self.staged
    }
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
