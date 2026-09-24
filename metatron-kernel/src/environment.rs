use std::cell::RefCell;
use std::collections::{HashMap, HashSet};
use std::error::Error;
use std::fmt;
use std::rc::Rc;

use crate::id::{ExprId, NameId};
use crate::machine::{AuthorityId, DefinitionBody, ExposureCache, ProjectionSpec, RecursorReduction};

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
pub struct NatPrimitives {
    pub type_name: NameId,
    pub type_expr: ExprId,
    pub zero: NameId,
    pub succ: NameId,
    pub recursor: NameId,
    pub add: Option<NameId>,
    pub sub: Option<NameId>,
    pub ble: Option<NameId>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BoolPrimitives {
    pub false_ctor: NameId,
    pub true_ctor: NameId,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct QuotPrimitives {
    pub type_name: NameId,
    pub mk: NameId,
    pub lift: NameId,
    pub ind: NameId,
}

#[derive(Clone, Debug)]
pub struct Environment {
    authority: AuthorityId,
    constants: Rc<HashMap<NameId, ConstantDecl>>,
    definitions: Rc<HashMap<NameId, DefinitionBody>>,
    singleton_recursor_reductions: Rc<HashSet<NameId>>,
    recursor_reductions: Rc<HashMap<NameId, RecursorReduction>>,
    projection_specs: Rc<HashMap<NameId, ProjectionSpec>>,
    nat_primitives: Option<NatPrimitives>,
    bool_primitives: Option<BoolPrimitives>,
    quot_primitives: Option<QuotPrimitives>,
    unit_like_types: Rc<HashSet<NameId>>,
    /// Proven reduction observations shared across this persistent environment
    /// lineage. Keys carry the exact authority, so no result crosses a
    /// semantic-authority boundary accidentally.
    exposure_cache: ExposureCache,
}

impl Environment {
    pub fn empty() -> Self {
        Self {
            authority: AuthorityId(0),
            constants: Rc::new(HashMap::new()),
            definitions: Rc::new(HashMap::new()),
            singleton_recursor_reductions: Rc::new(HashSet::new()),
            recursor_reductions: Rc::new(HashMap::new()),
            projection_specs: Rc::new(HashMap::new()),
            nat_primitives: None,
            bool_primitives: None,
            quot_primitives: None,
            unit_like_types: Rc::new(HashSet::new()),
            exposure_cache: Rc::new(RefCell::new(HashMap::new())),
        }
    }

    pub fn authority(&self) -> AuthorityId {
        self.authority
    }

    pub(crate) fn exposure_cache(&self) -> ExposureCache {
        self.exposure_cache.clone()
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
            projection_specs: self.projection_specs.clone(),
            nat_primitives: self.nat_primitives.clone(),
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: self.unit_like_types.clone(),
            exposure_cache: self.exposure_cache.clone(),
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
            projection_specs: self.projection_specs.clone(),
            nat_primitives: self.nat_primitives.clone(),
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: self.unit_like_types.clone(),
            exposure_cache: self.exposure_cache.clone(),
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
            projection_specs: self.projection_specs.clone(),
            nat_primitives: self.nat_primitives.clone(),
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: self.unit_like_types.clone(),
            exposure_cache: self.exposure_cache.clone(),
        })
    }

    pub fn singleton_recursor_reductions(&self) -> HashSet<NameId> {
        self.singleton_recursor_reductions.as_ref().clone()
    }

    pub fn recursor_reductions(&self) -> HashMap<NameId, RecursorReduction> {
        self.recursor_reductions.as_ref().clone()
    }

    pub fn install_projection_spec(
        &self,
        name: NameId,
        spec: ProjectionSpec,
    ) -> Result<Self, EnvironmentError> {
        if !self.constants.contains_key(&name) || !self.constants.contains_key(&spec.constructor) {
            return Err(EnvironmentError::MissingConstant(name));
        }
        if self.projection_specs.contains_key(&name) {
            return Err(EnvironmentError::DuplicateReduction(name));
        }
        let mut specs = self.projection_specs.as_ref().clone();
        specs.insert(name, spec);
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
            projection_specs: Rc::new(specs),
            nat_primitives: self.nat_primitives.clone(),
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: self.unit_like_types.clone(),
            exposure_cache: self.exposure_cache.clone(),
        })
    }

    pub fn projection_specs(&self) -> HashMap<NameId, ProjectionSpec> {
        self.projection_specs.as_ref().clone()
    }

    pub fn install_nat_primitives(
        &self,
        primitives: NatPrimitives,
    ) -> Result<Self, EnvironmentError> {
        if self.nat_primitives.is_some() {
            return Err(EnvironmentError::DuplicateNatPrimitives);
        }
        for name in [
            primitives.type_name,
            primitives.zero,
            primitives.succ,
            primitives.recursor,
        ] {
            if !self.constants.contains_key(&name) {
                return Err(EnvironmentError::MissingConstant(name));
            }
        }
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
            projection_specs: self.projection_specs.clone(),
            nat_primitives: Some(primitives),
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: self.unit_like_types.clone(),
            exposure_cache: self.exposure_cache.clone(),
        })
    }

    pub fn nat_primitives(&self) -> Option<&NatPrimitives> {
        self.nat_primitives.as_ref()
    }

    pub fn install_nat_operation(
        &self,
        name: NameId,
        operation: NatOperation,
    ) -> Result<Self, EnvironmentError> {
        if !self.constants.contains_key(&name) {
            return Err(EnvironmentError::MissingConstant(name));
        }
        let Some(mut primitives) = self.nat_primitives.clone() else {
            return Err(EnvironmentError::MissingNatPrimitives);
        };
        let slot = match operation {
            NatOperation::Add => &mut primitives.add,
            NatOperation::Sub => &mut primitives.sub,
            NatOperation::Ble => &mut primitives.ble,
        };
        if slot.is_some() {
            return Err(EnvironmentError::DuplicateNatOperation(name));
        }
        *slot = Some(name);
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
            projection_specs: self.projection_specs.clone(),
            nat_primitives: Some(primitives),
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: self.unit_like_types.clone(),
            exposure_cache: self.exposure_cache.clone(),
        })
    }

    pub fn install_bool_primitives(
        &self,
        primitives: BoolPrimitives,
    ) -> Result<Self, EnvironmentError> {
        if self.bool_primitives.is_some() {
            return Err(EnvironmentError::DuplicateBoolPrimitives);
        }
        for name in [primitives.false_ctor, primitives.true_ctor] {
            if !self.constants.contains_key(&name) {
                return Err(EnvironmentError::MissingConstant(name));
            }
        }
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
            projection_specs: self.projection_specs.clone(),
            nat_primitives: self.nat_primitives.clone(),
            bool_primitives: Some(primitives),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: self.unit_like_types.clone(),
            exposure_cache: self.exposure_cache.clone(),
        })
    }

    pub fn bool_primitives(&self) -> Option<&BoolPrimitives> {
        self.bool_primitives.as_ref()
    }

    pub fn install_quot_primitives(
        &self,
        primitives: QuotPrimitives,
    ) -> Result<Self, EnvironmentError> {
        if self.quot_primitives.is_some() {
            return Err(EnvironmentError::DuplicateQuotPrimitives);
        }
        for name in [
            primitives.type_name,
            primitives.mk,
            primitives.lift,
            primitives.ind,
        ] {
            if !self.constants.contains_key(&name) {
                return Err(EnvironmentError::MissingConstant(name));
            }
        }
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
            projection_specs: self.projection_specs.clone(),
            nat_primitives: self.nat_primitives.clone(),
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: Some(primitives),
            unit_like_types: self.unit_like_types.clone(),
            exposure_cache: self.exposure_cache.clone(),
        })
    }

    pub fn quot_primitives(&self) -> Option<&QuotPrimitives> {
        self.quot_primitives.as_ref()
    }

    pub fn install_unit_like_type(&self, name: NameId) -> Result<Self, EnvironmentError> {
        if !self.constants.contains_key(&name) {
            return Err(EnvironmentError::MissingConstant(name));
        }
        if self.unit_like_types.contains(&name) {
            return Err(EnvironmentError::DuplicateUnitLikeType(name));
        }
        let mut unit_like_types = self.unit_like_types.as_ref().clone();
        unit_like_types.insert(name);
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
            projection_specs: self.projection_specs.clone(),
            nat_primitives: self.nat_primitives.clone(),
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: Rc::new(unit_like_types),
            exposure_cache: self.exposure_cache.clone(),
        })
    }

    pub fn is_unit_like_type(&self, name: NameId) -> bool {
        self.unit_like_types.contains(&name)
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

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum NatOperation {
    Add,
    Sub,
    Ble,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum EnvironmentError {
    DuplicateConstant(NameId),
    MissingConstant(NameId),
    DuplicateReduction(NameId),
    DuplicateNatPrimitives,
    MissingNatPrimitives,
    DuplicateNatOperation(NameId),
    DuplicateBoolPrimitives,
    DuplicateQuotPrimitives,
    DuplicateUnitLikeType(NameId),
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
            Self::DuplicateNatPrimitives => write!(formatter, "duplicate Nat primitive authority"),
            Self::MissingNatPrimitives => write!(formatter, "missing Nat primitive authority"),
            Self::DuplicateNatOperation(name) => {
                write!(formatter, "duplicate Nat operation {}", name.0)
            }
            Self::DuplicateBoolPrimitives => {
                write!(formatter, "duplicate Bool primitive authority")
            }
            Self::DuplicateQuotPrimitives => {
                write!(formatter, "duplicate Quot primitive authority")
            }
            Self::DuplicateUnitLikeType(name) => {
                write!(formatter, "duplicate unit-like type {}", name.0)
            }
            Self::AuthorityOverflow => write!(formatter, "environment authority overflow"),
        }
    }
}

impl Error for EnvironmentError {}
