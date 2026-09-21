use std::collections::HashMap;
use std::error::Error;
use std::fmt;
use std::rc::Rc;

use crate::id::{ExprId, NameId};
use crate::machine::{AuthorityId, DefinitionBody};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ConstantDecl {
    pub level_params: Vec<NameId>,
    pub ty: ExprId,
    pub value: Option<ExprId>,
    pub preferred_for_reduction: bool,
}

impl ConstantDecl {
    pub fn axiom(level_params: Vec<NameId>, ty: ExprId) -> Self {
        Self {
            level_params,
            ty,
            value: None,
            preferred_for_reduction: false,
        }
    }

    pub fn definition(
        level_params: Vec<NameId>,
        ty: ExprId,
        value: ExprId,
        preferred_for_reduction: bool,
    ) -> Self {
        Self {
            level_params,
            ty,
            value: Some(value),
            preferred_for_reduction,
        }
    }

    /// Compile a checked theorem to its shallow executable representative.
    /// The proof body is deliberately absent, so it cannot become delta fuel.
    pub fn theorem(level_params: Vec<NameId>, ty: ExprId) -> Self {
        Self {
            level_params,
            ty,
            value: None,
            preferred_for_reduction: false,
        }
    }

    /// A checked inductive type contributes only its signature at runtime.
    pub fn inductive_type(level_params: Vec<NameId>, ty: ExprId) -> Self {
        Self::theorem(level_params, ty)
    }

    /// A validated constructor is executable only as a rigid constant until
    /// a separately qualified iota rule is installed.
    pub fn constructor(level_params: Vec<NameId>, ty: ExprId) -> Self {
        Self::theorem(level_params, ty)
    }

    /// A checked recursor is opaque: its reduction rules require a separately
    /// qualified iota mechanism and are not definition bodies.
    pub fn recursor(level_params: Vec<NameId>, ty: ExprId) -> Self {
        Self::theorem(level_params, ty)
    }
}

#[derive(Clone, Debug)]
pub struct Environment {
    authority: AuthorityId,
    constants: Rc<HashMap<NameId, ConstantDecl>>,
}

impl Environment {
    pub fn empty() -> Self {
        Self {
            authority: AuthorityId(0),
            constants: Rc::new(HashMap::new()),
        }
    }

    pub fn authority(&self) -> AuthorityId {
        self.authority
    }

    pub fn get(&self, name: NameId) -> Option<&ConstantDecl> {
        self.constants.get(&name)
    }

    pub fn extend(
        &self,
        name: NameId,
        declaration: ConstantDecl,
    ) -> Result<Self, EnvironmentError> {
        if self.constants.contains_key(&name) {
            return Err(EnvironmentError::DuplicateConstant(name));
        }
        let mut constants = self.constants.as_ref().clone();
        constants.insert(name, declaration);
        let authority = self
            .authority
            .0
            .checked_add(1)
            .ok_or(EnvironmentError::AuthorityOverflow)?;
        Ok(Self {
            authority: AuthorityId(authority),
            constants: Rc::new(constants),
        })
    }

    pub fn definition_bodies(&self) -> HashMap<NameId, DefinitionBody> {
        self.constants
            .iter()
            .filter_map(|(name, declaration)| {
                declaration.value.map(|value| {
                    (
                        *name,
                        DefinitionBody {
                            value,
                            preferred_for_reduction: declaration.preferred_for_reduction,
                            level_params: declaration.level_params.clone(),
                        },
                    )
                })
            })
            .collect()
    }
}

impl Default for Environment {
    fn default() -> Self {
        Self::empty()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum EnvironmentError {
    DuplicateConstant(NameId),
    AuthorityOverflow,
}

impl fmt::Display for EnvironmentError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::DuplicateConstant(name) => {
                write!(formatter, "duplicate constant name {}", name.0)
            }
            Self::AuthorityOverflow => write!(formatter, "environment authority overflow"),
        }
    }
}

impl Error for EnvironmentError {}
