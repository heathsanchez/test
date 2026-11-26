use metatron_kernel::{
    environment::{ConstantDecl, Environment},
    id::{ExprId, IdTable, LevelId, NameId},
    syntax::{Expr, Level},
    typecheck::{TypeChecker, TypeValue},
    value::{Closure, EnvFrame},
};

fn fixture() -> (IdTable<ExprId, Expr>, IdTable<LevelId, Level>, Environment) {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    levels.insert(LevelId(1), Level::Succ(LevelId(0))).unwrap();
    let mut expressions = IdTable::default();
    let exprs = [
        (0, Expr::Sort(LevelId(0))), // Prop
        (1, Expr::Sort(LevelId(1))), // Type
        (2, Expr::Const { name: NameId(1), levels: vec![] }), // A : Prop
        (3, Expr::Pi { domain: ExprId(2), body: ExprId(2) }), // P = A -> A : Prop
        (4, Expr::BVar(0)),
        (5, Expr::Lam { domain: ExprId(2), body: ExprId(4) }), // id : P
        (6, Expr::Const { name: NameId(2), levels: vec![] }), // q : P
        (7, Expr::Const { name: NameId(3), levels: vec![] }), // Nat : Type
        (8, Expr::Pi { domain: ExprId(3), body: ExprId(7) }), // f : P -> Nat
        (9, Expr::Const { name: NameId(4), levels: vec![] }),
        (10, Expr::App { fun: ExprId(9), arg: ExprId(5) }), // f id
        (11, Expr::App { fun: ExprId(9), arg: ExprId(6) }), // f q
        (12, Expr::App { fun: ExprId(9), arg: ExprId(2) }), // f A (ill typed)
        (13, Expr::Const { name: NameId(5), levels: vec![] }), // n : Nat
        (14, Expr::Const { name: NameId(6), levels: vec![] }), // m : Nat
        (15, Expr::Pi { domain: ExprId(7), body: ExprId(7) }), // fd : Nat -> Nat
        (16, Expr::Const { name: NameId(7), levels: vec![] }),
        (17, Expr::App { fun: ExprId(16), arg: ExprId(13) }), // fd n
        (18, Expr::App { fun: ExprId(16), arg: ExprId(14) }), // fd m
    ];
    for (id, expr) in exprs {
        expressions.insert(ExprId(id), expr).unwrap();
    }
    let environment = Environment::empty()
        .extend(NameId(1), ConstantDecl::axiom(vec![], ExprId(0))).unwrap()
        .extend(NameId(2), ConstantDecl::axiom(vec![], ExprId(3))).unwrap()
        .extend(NameId(3), ConstantDecl::inductive_type(vec![], ExprId(1))).unwrap()
        .extend(NameId(4), ConstantDecl::axiom(vec![], ExprId(8))).unwrap()
        .extend(NameId(5), ConstantDecl::axiom(vec![], ExprId(7))).unwrap()
        .extend(NameId(6), ConstantDecl::axiom(vec![], ExprId(7))).unwrap()
        .extend(NameId(7), ConstantDecl::axiom(vec![], ExprId(15))).unwrap();
    (expressions, levels, environment)
}

fn compare(left: u64, right: u64) -> metatron_kernel::judgment::Judgment<()> {
    let (exprs, levels, env) = fixture();
    let checker = TypeChecker::new(&exprs, &levels, &env);
    checker.convert(
        &TypeValue::Term(Closure::new(ExprId(left), EnvFrame::empty())),
        &TypeValue::Term(Closure::new(ExprId(right), EnvFrame::empty())),
        8192,
    )
}

#[test]
fn distinct_proof_arguments_of_same_checked_proposition_are_convertible() {
    let result = compare(10, 11);
    assert!(result.is_proven(), "f (fun a : A => a) and f q must be defeq: {result:?}");
}

#[test]
fn mismatched_data_arguments_stay_distinct() {
    let result = compare(17, 18);
    assert!(!result.is_proven(), "Nat data cannot become equal through proof irrelevance: {result:?}");
}

#[test]
fn an_ill_typed_proposition_argument_does_not_count_as_a_proof() {
    let result = compare(12, 11);
    assert!(!result.is_proven(), "A : Prop is not a proof of A -> A: {result:?}");
}
