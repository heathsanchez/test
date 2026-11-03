#![allow(dead_code)]
struct ExprId(u64);struct NameId(u64);struct LevelId(u64);struct BigNat(Vec<u32>);
pub enum OldExpr {
    BVar(u64),
    NatLit(BigNat),
    StrLit(String),
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
pub enum BoolExpr {
    BVar(u64),
    NatLit(BigNat),
    StrLit(String),
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
        nondep: bool,
    },
    Proj {
        type_name: NameId,
        index: u64,
        structure: ExprId,
    },
}
pub enum TaggedExpr {
    BVar(u64),
    NatLit(BigNat),
    StrLit(String),
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
    LetNondep { ty: ExprId, value: ExprId, body: ExprId },
    Proj {
        type_name: NameId,
        index: u64,
        structure: ExprId,
    },
}
fn main(){println!("old={} old_option={} bool={} bool_option={} tagged={} tagged_option={}",std::mem::size_of::<OldExpr>(),std::mem::size_of::<Option<OldExpr>>(),std::mem::size_of::<BoolExpr>(),std::mem::size_of::<Option<BoolExpr>>(),std::mem::size_of::<TaggedExpr>(),std::mem::size_of::<Option<TaggedExpr>>());}
