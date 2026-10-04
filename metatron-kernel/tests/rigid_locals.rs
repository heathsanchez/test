use metatron_kernel::{
    environment::Environment,
    id::{ExprId, IdTable, LevelId},
    syntax::{Expr, Level},
    typecheck::{TypeChecker, TypeValue},
    value::{Closure, EnvFrame},
};

fn compare(sort: LevelId, right_index: u64) -> metatron_kernel::judgment::Judgment<()> {
    let mut es = IdTable::default();
    let mut ls = IdTable::default();
    ls.insert(LevelId(0), Level::Zero).unwrap();
    ls.insert(LevelId(1), Level::Succ(LevelId(0))).unwrap();
    let xs = [
        Expr::Sort(sort),
        Expr::BVar(0),
        Expr::BVar(1),
        Expr::BVar(right_index),
        Expr::Lam {
            domain: ExprId(2),
            body: ExprId(2),
        },
        Expr::Lam {
            domain: ExprId(1),
            body: ExprId(4),
        },
        Expr::Lam {
            domain: ExprId(0),
            body: ExprId(5),
        },
        Expr::Lam {
            domain: ExprId(2),
            body: ExprId(3),
        },
        Expr::Lam {
            domain: ExprId(1),
            body: ExprId(7),
        },
        Expr::Lam {
            domain: ExprId(0),
            body: ExprId(8),
        },
    ];
    for (i, e) in xs.into_iter().enumerate() {
        es.insert(ExprId(i as u64), e).unwrap();
    }
    let env = Environment::empty();
    let ck = TypeChecker::new(&es, &ls, &env);
    let term = |i| TypeValue::Term(Closure::new(ExprId(i), EnvFrame::empty()));
    ck.convert(&term(6), &term(9), 1024)
}

#[test]
fn distinct_locals_of_a_rigid_type_variable_are_definitely_unequal() {
    let result = compare(LevelId(1), 0);
    assert!(
        matches!(result,metatron_kernel::judgment::Judgment::Refuted{obstruction} if obstruction.0=="distinct-rigid-local-terms")
    );
}

#[test]
fn proof_locals_remain_irrelevant_and_same_data_local_remains_equal() {
    assert!(compare(LevelId(0), 0).is_proven());
    assert!(compare(LevelId(1), 1).is_proven());
}
