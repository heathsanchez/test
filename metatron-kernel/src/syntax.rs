use crate::id::{ExprId, LevelId, NameId};

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
        reducible: bool,
    },
    Unsupported {
        tag: String,
    },
}
