use crate::id::{ExprId, LevelId, NameId};

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Name {
    Str { prefix: NameId, value: String },
    Num { prefix: NameId, value: u64 },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Level {
    Zero,
    Succ(LevelId),
    Max(LevelId, LevelId),
    IMax(LevelId, LevelId),
    Param(NameId),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Expr {
    BVar(u64),
    Sort(LevelId),
    Const {
        name: NameId,
        levels: Vec<LevelId>,
    },
    App {
        fun: ExprId,
        arg: ExprId,
    },
    Lam {
        domain: ExprId,
        body: ExprId,
    },
    Pi {
        domain: ExprId,
        body: ExprId,
    },
    Let {
        ty: ExprId,
        value: ExprId,
        body: ExprId,
    },
    Proj {
        type_name: NameId,
        index: u64,
        structure: ExprId,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Declaration {
    Axiom {
        name: NameId,
        level_params: Vec<NameId>,
        ty: ExprId,
    },
    Definition {
        name: NameId,
        level_params: Vec<NameId>,
        ty: ExprId,
        value: ExprId,
        preferred_for_reduction: bool,
    },
    Theorem {
        all: Vec<NameId>,
        name: NameId,
        level_params: Vec<NameId>,
        ty: ExprId,
        value: ExprId,
    },
    Inductive(InductiveBlock),
    Unsupported {
        tag: String,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct InductiveBlock {
    pub types: Vec<InductiveType>,
    pub constructors: Vec<Constructor>,
    pub recursors: Vec<Recursor>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct InductiveType {
    pub all: Vec<NameId>,
    pub constructors: Vec<NameId>,
    pub is_recursive: bool,
    pub is_reflexive: bool,
    pub is_unsafe: bool,
    pub level_params: Vec<NameId>,
    pub name: NameId,
    pub num_indices: u64,
    pub num_nested: u64,
    pub num_params: u64,
    pub ty: ExprId,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Constructor {
    pub index: u64,
    pub inductive: NameId,
    pub is_unsafe: bool,
    pub level_params: Vec<NameId>,
    pub name: NameId,
    pub num_fields: u64,
    pub num_params: u64,
    pub ty: ExprId,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Recursor {
    pub all: Vec<NameId>,
    pub is_unsafe: bool,
    pub k: bool,
    pub level_params: Vec<NameId>,
    pub name: NameId,
    pub num_indices: u64,
    pub num_minors: u64,
    pub num_motives: u64,
    pub num_params: u64,
    pub rules: Vec<RecursorRule>,
    pub ty: ExprId,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RecursorRule {
    pub constructor: NameId,
    pub num_fields: u64,
    pub rhs: ExprId,
}
