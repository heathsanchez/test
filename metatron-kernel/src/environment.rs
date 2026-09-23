use std::collections::{HashMap, HashSet};
use std::error::Error;
use std::fmt;
use std::rc::Rc;

use crate::id::{ExprId, NameId};
use crate::machine::{AuthorityId, DefinitionBody, RecursorReduction};

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

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProjectionInfo {
    pub constructor: NameId,
    pub num_params: usize,
    pub field_parameter_indices: Vec<usize>,
}

#[derive(Clone, Debug)]
pub struct Environment {
    authority: AuthorityId,
    constants: Rc<HashMap<NameId, ConstantDecl>>,
    definitions: Rc<HashMap<NameId, DefinitionBody>>,
    singleton_recursor_reductions: Rc<HashSet<NameId>>,
    recursor_reductions: Rc<HashMap<NameId, RecursorReduction>>,
    projections: Rc<HashMap<NameId, ProjectionInfo>>,
}

impl Environment {
    pub fn empty() -> Self {
        Self {
            authority: AuthorityId(0),
            constants: Rc::new(HashMap::new()),
            definitions: Rc::new(HashMap::new()),
            singleton_recursor_reductions: Rc::new(HashSet::new()),
            recursor_reductions: Rc::new(HashMap::new()),
            projections: Rc::new(HashMap::new()),
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
        let mut definitions = self.definitions.as_ref().clone();
        if let Some(value) = declaration.value {
            definitions.insert(
                name,
                DefinitionBody {
                    value,
                    preferred_for_reduction: declaration.preferred_for_reduction,
                    level_params: declaration.level_params.clone(),
                },
            );
        }
        constants.insert(name, declaration);
        let authority = self
            .authority
            .0
            .checked_add(1)
            .ok_or(EnvironmentError::AuthorityOverflow)?;
        Ok(Self {
            authority: AuthorityId(authority),
            constants: Rc::new(constants),
            definitions: Rc::new(definitions),
            singleton_recursor_reductions: self.singleton_recursor_reductions.clone(),
            recursor_reductions: self.recursor_reductions.clone(),
            projections: self.projections.clone(),
        })
    }

    /// Install the independently qualified nullary-singleton recursor
    /// computation rule for an already admitted recursor constant.
    pub fn install_singleton_recursor_reduction(
        &self,
        name: NameId,
    ) -> Result<Self, EnvironmentError> {
        if !self.constants.contains_key(&name) {
            return Err(EnvironmentError::MissingConstant(name));
        }
        if self.singleton_recursor_reductions.contains(&name) {
            return Err(EnvironmentError::DuplicateReduction(name));
        }
        let mut reductions = self.singleton_recursor_reductions.as_ref().clone();
        reductions.insert(name);
        let authority = self
            .authority
            .0
            .checked_add(1)
            .ok_or(EnvironmentError::AuthorityOverflow)?;
        Ok(Self {
            authority: AuthorityId(authority),
            constants: self.constants.clone(),
            definitions: self.definitions.clone(),
            singleton_recursor_reductions: Rc::new(reductions),
            recursor_reductions: self.recursor_reductions.clone(),
            projections: self.projections.clone(),
        })
    }

    /// Install an independently qualified constructor-specific iota table for
    /// an already admitted recursor constant.
    pub fn install_recursor_reduction(
        &self,
        name: NameId,
        reduction: RecursorReduction,
    ) -> Result<Self, EnvironmentError> {
        if !self.constants.contains_key(&name) {
            return Err(EnvironmentError::MissingConstant(name));
        }
        if self.recursor_reductions.contains_key(&name) {
            return Err(EnvironmentError::DuplicateReduction(name));
        }
        let mut reductions = self.recursor_reductions.as_ref().clone();
        reductions.insert(name, reduction);
        let authority = self
            .authority
            .0
            .checked_add(1)
            .ok_or(EnvironmentError::AuthorityOverflow)?;
        Ok(Self {
            authority: AuthorityId(authority),
            constants: self.constants.clone(),
            definitions: self.definitions.clone(),
            singleton_recursor_reductions: self.singleton_recursor_reductions.clone(),
            recursor_reductions: Rc::new(reductions),
            projections: self.projections.clone(),
        })
    }

    pub fn install_projection(
        &self,
        type_name: NameId,
        info: ProjectionInfo,
    ) -> Result<Self, EnvironmentError> {
        if !self.constants.contains_key(&type_name)
            || !self.constants.contains_key(&info.constructor)
        {
            return Err(EnvironmentError::MissingConstant(type_name));
        }
        if self.projections.contains_key(&type_name) {
            return Err(EnvironmentError::DuplicateProjection(type_name));
        }
        let mut projections = self.projections.as_ref().clone();
        projections.insert(type_name, info);
        let authority = self
            .authority
            .0
            .checked_add(1)
            .ok_or(EnvironmentError::AuthorityOverflow)?;
        Ok(Self {
            authority: AuthorityId(authority),
            constants: self.constants.clone(),
            definitions: self.definitions.clone(),
            singleton_recursor_reductions: self.singleton_recursor_reductions.clone(),
            recursor_reductions: self.recursor_reductions.clone(),
            projections: Rc::new(projections),
        })
    }

    pub fn projection(&self, type_name: NameId) -> Option<&ProjectionInfo> {
        self.projections.get(&type_name)
    }

    pub fn projections(&self) -> HashMap<NameId, ProjectionInfo> {
        self.projections.as_ref().clone()
    }

    pub fn singleton_recursor_reductions(&self) -> HashSet<NameId> {
        self.singleton_recursor_reductions.as_ref().clone()
    }

    pub fn recursor_reductions(&self) -> HashMap<NameId, RecursorReduction> {
        self.recursor_reductions.as_ref().clone()
    }

    pub fn definition_bodies(&self) -> Rc<HashMap<NameId, DefinitionBody>> {
        self.definitions.clone()
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
    MissingConstant(NameId),
    DuplicateReduction(NameId),
    DuplicateProjection(NameId),
    AuthorityOverflow,
}

impl fmt::Display for EnvironmentError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::DuplicateConstant(name) => {
                write!(formatter, "duplicate constant name {}", name.0)
            }
            Self::MissingConstant(name) => {
                write!(formatter, "missing constant name {}", name.0)
            }
            Self::DuplicateReduction(name) => {
                write!(
                    formatter,
                    "duplicate singleton recursor reduction {}",
                    name.0
                )
            }
            Self::DuplicateProjection(name) => {
                write!(formatter, "duplicate projection authority {}", name.0)
            }
            Self::AuthorityOverflow => write!(formatter, "environment authority overflow"),
        }
    }
}

impl Error for EnvironmentError {}
