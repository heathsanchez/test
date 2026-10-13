use std::collections::{HashMap, HashSet};
use std::error::Error;
use std::fmt;
use std::rc::Rc;

use crate::id::{ExprId, NameId};
use crate::machine::{AuthorityId, DefinitionBody, ClosedNestedMinorReduction, NullaryMinorReduction, ProjectionSpec, RecursorReduction};

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

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub struct NatPrimitives {
    pub type_name: NameId,
    pub type_expr: ExprId,
    pub zero: NameId,
    pub succ: NameId,
    pub recursor: NameId,
    pub add: Option<NameId>,
    pub mul: Option<NameId>,
    pub pow: Option<NameId>,
    pub land: Option<NameId>,
    pub shift_right: Option<NameId>,
    pub div: Option<NameId>,
    pub modulo: Option<NameId>,
    pub sub: Option<NameId>,
    pub pred: Option<NameId>,
    /// A checked export binder variable used solely to represent a
    /// closure over an already-evaluated native Nat expression.
    pub virtual_bvar_zero: Option<ExprId>,
    pub ble: Option<NameId>,
    pub beq: Option<NameId>,
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
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
    nullary_minor_reductions: Rc<HashMap<NameId,Vec<NullaryMinorReduction>>>,
    closed_nested_minor_reductions: Rc<HashMap<NameId,Vec<ClosedNestedMinorReduction>>>,
    recursor_reductions: Rc<HashMap<NameId, RecursorReduction>>,
    projection_specs: Rc<HashMap<NameId, ProjectionSpec>>,
    nat_primitives: Option<NatPrimitives>,
    string_literal_type:Option<ExprId>,
    bool_primitives: Option<BoolPrimitives>,
    quot_primitives: Option<QuotPrimitives>,
    unit_like_types: Rc<HashSet<NameId>>,
}

impl Environment {
    pub fn empty() -> Self {
        Self {
            authority: AuthorityId(0),
            constants: Rc::new(HashMap::new()),
            definitions: Rc::new(HashMap::new()),
            singleton_recursor_reductions: Rc::new(HashSet::new()),
            nullary_minor_reductions: Rc::new(HashMap::new()),
            closed_nested_minor_reductions: Rc::new(HashMap::new()),
            recursor_reductions: Rc::new(HashMap::new()),
            projection_specs: Rc::new(HashMap::new()),
            nat_primitives: None,
            string_literal_type:None,
            bool_primitives: None,
            quot_primitives: None,
            unit_like_types: Rc::new(HashSet::new()),
        }
    }

    pub(crate) fn string_literal_type(&self)->Option<ExprId> {self.string_literal_type}

    pub(crate) fn install_string_literal_type(&self,ty:ExprId)->Result<Self,EnvironmentError> {
        let mut result=self.clone();
        result.authority=AuthorityId(self.authority.0.checked_add(1).ok_or(EnvironmentError::AuthorityOverflow)?);
        result.string_literal_type=Some(ty);Ok(result)
    }

    pub fn authority(&self) -> AuthorityId {
        self.authority
    }

    pub fn get(&self, name: NameId) -> Option<&ConstantDecl> {
        self.constants.get(&name)
    }

    pub fn extend(
        &self,name:NameId,declaration:ConstantDecl,
    )->Result<Self,EnvironmentError>{
        self.clone().extend_owned(name,declaration)
    }

    /// Append to a consumed environment. Strong snapshot and machine-map
    /// owners force copy-on-write; unique maps avoid copying prior entries.
    pub fn extend_owned(
        mut self,name:NameId,declaration:ConstantDecl,
    )->Result<Self,EnvironmentError>{
        if self.constants.contains_key(&name){
            return Err(EnvironmentError::DuplicateConstant(name));
        }
        let authority=AuthorityId(self.authority.0.checked_add(1)
            .ok_or(EnvironmentError::AuthorityOverflow)?);
        if let Some(value)=declaration.value {
            Rc::make_mut(&mut self.definitions).insert(name,DefinitionBody {
                value,preferred_for_reduction:declaration.preferred_for_reduction,
                level_params:declaration.level_params.clone(),
            });
        }
        Rc::make_mut(&mut self.constants).insert(name,declaration);
        self.authority=authority;
        Ok(self)
    }

    /// Install the independently qualified nullary-singleton recursor
    /// computation rule for an already admitted recursor constant.
    pub(crate) fn install_closed_nested_minor_reductions(&self,name:NameId,rules:Vec<ClosedNestedMinorReduction>)->Result<Self,EnvironmentError> {
        if !self.constants.contains_key(&name) {return Err(EnvironmentError::MissingConstant(name));}
        if self.closed_nested_minor_reductions.contains_key(&name) {return Err(EnvironmentError::DuplicateReduction(name));}
        let mut result=self.clone();
        result.authority=AuthorityId(self.authority.0.checked_add(1).ok_or(EnvironmentError::AuthorityOverflow)?);
        let mut reductions=self.closed_nested_minor_reductions.as_ref().clone();reductions.insert(name,rules);
        result.closed_nested_minor_reductions=Rc::new(reductions);Ok(result)
    }

    pub(crate) fn closed_nested_minor_reductions(&self)->Rc<HashMap<NameId,Vec<ClosedNestedMinorReduction>>> {
        self.closed_nested_minor_reductions.clone()
    }

    pub(crate) fn install_nullary_minor_reductions(&self,name:NameId,rules:Vec<NullaryMinorReduction>)->Result<Self,EnvironmentError> {
        if !self.constants.contains_key(&name) {return Err(EnvironmentError::MissingConstant(name));}
        if self.nullary_minor_reductions.contains_key(&name) {return Err(EnvironmentError::DuplicateReduction(name));}
        let mut result=self.clone();
        result.authority=AuthorityId(self.authority.0.checked_add(1).ok_or(EnvironmentError::AuthorityOverflow)?);
        let mut reductions=self.nullary_minor_reductions.as_ref().clone();reductions.insert(name,rules);
        result.nullary_minor_reductions=Rc::new(reductions);
        Ok(result)
    }

    pub(crate) fn nullary_minor_reductions(&self)->Rc<HashMap<NameId,Vec<NullaryMinorReduction>>> {
        self.nullary_minor_reductions.clone()
    }

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
            nullary_minor_reductions: self.nullary_minor_reductions.clone(),
            closed_nested_minor_reductions: self.closed_nested_minor_reductions.clone(),
            recursor_reductions: self.recursor_reductions.clone(),
            projection_specs: self.projection_specs.clone(),
            nat_primitives: self.nat_primitives.clone(),
            string_literal_type:self.string_literal_type,
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: self.unit_like_types.clone(),
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
            nullary_minor_reductions: self.nullary_minor_reductions.clone(),
            closed_nested_minor_reductions: self.closed_nested_minor_reductions.clone(),
            recursor_reductions: Rc::new(reductions),
            projection_specs: self.projection_specs.clone(),
            nat_primitives: self.nat_primitives.clone(),
            string_literal_type:self.string_literal_type,
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: self.unit_like_types.clone(),
        })
    }

    pub(crate) fn shared_singleton_recursor_reductions(&self) -> Rc<HashSet<NameId>> {
        self.singleton_recursor_reductions.clone()
    }

    pub(crate) fn shared_recursor_reductions(&self) -> Rc<HashMap<NameId, RecursorReduction>> {
        self.recursor_reductions.clone()
    }

    pub(crate) fn shared_projection_specs(&self) -> Rc<HashMap<NameId, ProjectionSpec>> {
        self.projection_specs.clone()
    }

    pub fn singleton_recursor_reductions(&self) -> HashSet<NameId> {
        self.singleton_recursor_reductions.as_ref().clone()
    }

    pub fn recursor_reductions(&self) -> HashMap<NameId, RecursorReduction> {
        self.recursor_reductions.as_ref().clone()
    }

    pub fn recursor_reduction(&self, name: NameId) -> Option<&RecursorReduction> {
        self.recursor_reductions.get(&name)
    }

    pub(crate) fn is_certified_constructor(&self, name: NameId) -> bool {
        self.recursor_reductions
            .values()
            .any(|reduction| reduction.rules.iter().any(|rule| rule.constructor == name))
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
            nullary_minor_reductions: self.nullary_minor_reductions.clone(),
            closed_nested_minor_reductions: self.closed_nested_minor_reductions.clone(),
            recursor_reductions: self.recursor_reductions.clone(),
            projection_specs: Rc::new(specs),
            nat_primitives: self.nat_primitives.clone(),
            string_literal_type:self.string_literal_type,
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: self.unit_like_types.clone(),
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
            nullary_minor_reductions: self.nullary_minor_reductions.clone(),
            closed_nested_minor_reductions: self.closed_nested_minor_reductions.clone(),
            recursor_reductions: self.recursor_reductions.clone(),
            projection_specs: self.projection_specs.clone(),
            nat_primitives: Some(primitives),
            string_literal_type:self.string_literal_type,
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: self.unit_like_types.clone(),
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
            NatOperation::Mul => &mut primitives.mul,
            NatOperation::Pow => &mut primitives.pow,
            NatOperation::Land => &mut primitives.land,
            NatOperation::ShiftRight => &mut primitives.shift_right,
            NatOperation::Div => &mut primitives.div,
            NatOperation::Mod => &mut primitives.modulo,
            NatOperation::Sub => &mut primitives.sub,
            NatOperation::Pred => &mut primitives.pred,
            NatOperation::Ble => &mut primitives.ble,
            NatOperation::Beq => &mut primitives.beq,
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
            nullary_minor_reductions: self.nullary_minor_reductions.clone(),
            closed_nested_minor_reductions: self.closed_nested_minor_reductions.clone(),
            recursor_reductions: self.recursor_reductions.clone(),
            projection_specs: self.projection_specs.clone(),
            nat_primitives: Some(primitives),
            string_literal_type:self.string_literal_type,
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: self.unit_like_types.clone(),
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
            nullary_minor_reductions: self.nullary_minor_reductions.clone(),
            closed_nested_minor_reductions: self.closed_nested_minor_reductions.clone(),
            recursor_reductions: self.recursor_reductions.clone(),
            projection_specs: self.projection_specs.clone(),
            nat_primitives: self.nat_primitives.clone(),
            string_literal_type:self.string_literal_type,
            bool_primitives: Some(primitives),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: self.unit_like_types.clone(),
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
            nullary_minor_reductions: self.nullary_minor_reductions.clone(),
            closed_nested_minor_reductions: self.closed_nested_minor_reductions.clone(),
            recursor_reductions: self.recursor_reductions.clone(),
            projection_specs: self.projection_specs.clone(),
            nat_primitives: self.nat_primitives.clone(),
            string_literal_type:self.string_literal_type,
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: Some(primitives),
            unit_like_types: self.unit_like_types.clone(),
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
            nullary_minor_reductions: self.nullary_minor_reductions.clone(),
            closed_nested_minor_reductions: self.closed_nested_minor_reductions.clone(),
            recursor_reductions: self.recursor_reductions.clone(),
            projection_specs: self.projection_specs.clone(),
            nat_primitives: self.nat_primitives.clone(),
            string_literal_type:self.string_literal_type,
            bool_primitives: self.bool_primitives.clone(),
            quot_primitives: self.quot_primitives.clone(),
            unit_like_types: Rc::new(unit_like_types),
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
    Mul,
    Pow,
    Land,
    ShiftRight,
    Div,
    Mod,
    Sub,
    Pred,
    Ble,
    Beq,
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

#[cfg(test)]
mod owned_append_tests {
    use super::*;
    #[test]
    fn unique_owned_append_preserves_both_map_allocations_across_many_definitions() {
        let mut env=Environment::empty();let constants=Rc::as_ptr(&env.constants);let definitions=Rc::as_ptr(&env.definitions);
        for i in 0..2048 {env=env.extend_owned(NameId(i),ConstantDecl::definition(vec![],ExprId(0),ExprId(i),true)).unwrap();assert_eq!(Rc::as_ptr(&env.constants),constants,"unique owned publication must avoid cloning all prior signatures");assert_eq!(Rc::as_ptr(&env.definitions),definitions,"unique owned publication must avoid cloning all prior bodies");}
        assert_eq!(env.authority(),AuthorityId(2048));assert_eq!(env.constants.len(),2048);assert_eq!(env.definitions.len(),2048);
    }
    #[test]
    fn borrowed_and_pinned_snapshots_keep_their_maps_and_authority() {
        let env=Environment::empty().extend_owned(NameId(1),ConstantDecl::definition(vec![NameId(8)],ExprId(10),ExprId(11),true)).unwrap();
        let old=env.clone();let pinned=env.definition_bodies();let authority=env.authority();
        let next=env.extend_owned(NameId(2),ConstantDecl::definition(vec![],ExprId(12),ExprId(13),false)).unwrap();
        assert_eq!(old.authority(),authority);assert_eq!(next.authority(),AuthorityId(authority.0+1));
        assert!(old.get(NameId(2)).is_none());assert!(pinned.get(&NameId(2)).is_none());
        assert_eq!(pinned[&NameId(1)].value,ExprId(11));assert!(!Rc::ptr_eq(&pinned,&next.definition_bodies()));
        let borrowed=old.extend(NameId(3),ConstantDecl::axiom(vec![],ExprId(14))).unwrap();
        assert!(old.get(NameId(3)).is_none());assert!(borrowed.get(NameId(3)).is_some());
        assert!(Rc::ptr_eq(&pinned,&borrowed.definition_bodies()),"no-body append can share unchanged bodies under incremented authority");
    }
    #[test]
    fn validation_errors_do_not_modify_shared_snapshots_and_siblings_remain_distinct() {
        let env=Environment::empty().extend_owned(NameId(1),ConstantDecl::axiom(vec![],ExprId(1))).unwrap();let snapshot=env.clone();let constants=env.constants.clone();
        assert_eq!(env.extend_owned(NameId(1),ConstantDecl::definition(vec![],ExprId(2),ExprId(3),true)).unwrap_err(),EnvironmentError::DuplicateConstant(NameId(1)));
        assert_eq!(snapshot.get(NameId(1)).unwrap().ty,ExprId(1));assert!(snapshot.definition_bodies().is_empty());assert!(Rc::ptr_eq(&constants,&snapshot.constants));
        let mut exhausted=snapshot.clone();exhausted.authority=AuthorityId(u64::MAX);let exhausted_snapshot=exhausted.clone();
        assert_eq!(exhausted.extend_owned(NameId(2),ConstantDecl::definition(vec![],ExprId(2),ExprId(3),true)).unwrap_err(),EnvironmentError::AuthorityOverflow);
        assert!(exhausted_snapshot.get(NameId(2)).is_none());assert!(exhausted_snapshot.definition_bodies().is_empty());
        let left=snapshot.clone().extend_owned(NameId(2),ConstantDecl::definition(vec![],ExprId(2),ExprId(3),true)).unwrap();
        let right=snapshot.extend_owned(NameId(2),ConstantDecl::definition(vec![],ExprId(2),ExprId(4),true)).unwrap();
        assert_eq!(left.authority(),right.authority());assert_ne!(left.definition_bodies()[&NameId(2)].value,right.definition_bodies()[&NameId(2)].value);assert!(!Rc::ptr_eq(&left.definition_bodies(),&right.definition_bodies()));
    }
    #[test]
    fn retained_machine_delta_witness_cannot_observe_future_owned_appends() {
        use crate::id::{IdTable,LevelId};use crate::syntax::{Expr,Level};use crate::value::{Closure,EnvFrame,Value};use crate::machine::{Machine,Transparency};
        let mut expressions=IdTable::default();let mut levels=IdTable::default();levels.insert(LevelId(0),Level::Zero).unwrap();
        expressions.insert(ExprId(0),Expr::Const{name:NameId(2),levels:vec![]}).unwrap();expressions.insert(ExprId(1),Expr::Sort(LevelId(0))).unwrap();
        let env=Environment::empty();let old=Machine::new(env.authority(),&expressions,&levels,env.definition_bodies());
        let extended=env.extend_owned(NameId(2),ConstantDecl::definition(vec![],ExprId(1),ExprId(1),true)).unwrap();
        let new=Machine::new(extended.authority(),&expressions,&levels,extended.definition_bodies());let term=Closure::new(ExprId(0),EnvFrame::empty());
        assert!(matches!(old.expose(term.clone(),Transparency::Full,32).proven_value(),Some(Value::Neutral(_))));
        assert!(matches!(new.expose(term.clone(),Transparency::Full,32).proven_value(),Some(Value::Sort(_))));
        assert!(matches!(old.expose(term.clone(),Transparency::Full,32).proven_value(),Some(Value::Neutral(_))));
    }

}
