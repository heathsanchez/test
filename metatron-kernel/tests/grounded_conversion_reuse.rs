use metatron_kernel::{
    convert::{convert_with_policy, DeltaPolicy},
    environment::Environment,
    id::{ExprId, IdTable, LevelId},
    syntax::{Expr, Level},
    typecheck::{TypeChecker, TypeValue},
    value::{Closure, EnvFrame},
};

/// The two syntactically distinct sort expressions represent the same
/// kernel type, but need an actual conversion the first time.
#[test]
fn only_completed_positive_proof_can_be_reused_without_new_search_budget() {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    let mut expressions = IdTable::default();
    expressions.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    expressions.insert(ExprId(1), Expr::Sort(LevelId(0))).unwrap();
    let env = Environment::empty();
    let ck = TypeChecker::new(&expressions, &levels, &env);
    let a = TypeValue::Term(Closure::new(ExprId(0), EnvFrame::empty()));
    let b = TypeValue::Term(Closure::new(ExprId(1), EnvFrame::empty()));
    assert!(ck.convert(&a, &b, 0).is_unknown(), "cold zero-budget lookup");
    assert!(ck.convert(&a, &b, 128).is_proven(), "source checked once");
    assert!(ck.convert(&a, &b, 0).is_proven(), "exact complete proof retained");

    // Policy is part of the certificate scope. A proof under guarded
    // unfolding must never become a PreferredOnly proof by cache accident.
    assert!(convert_with_policy(&ck, &a, &b, 0, DeltaPolicy::PreferredOnly).is_unknown());

    // Another checker instance has no authority to inherit that record.
    let fresh = TypeChecker::new(&expressions, &levels, &env);
    assert!(fresh.convert(&a, &b, 0).is_unknown());
}

#[test]
fn neither_unknown_nor_definite_refutation_is_cached_as_equality() {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    levels.insert(LevelId(1), Level::Succ(LevelId(0))).unwrap();
    let mut expressions = IdTable::default();
    expressions.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    expressions.insert(ExprId(1), Expr::Sort(LevelId(1))).unwrap();
    let env = Environment::empty();
    let ck = TypeChecker::new(&expressions, &levels, &env);
    let a = TypeValue::Term(Closure::new(ExprId(0), EnvFrame::empty()));
    let b = TypeValue::Term(Closure::new(ExprId(1), EnvFrame::empty()));
    assert!(ck.convert(&a, &b, 0).is_unknown());
    assert!(!ck.convert(&a, &b, 128).is_proven());
    assert!(ck.convert(&a, &b, 0).is_unknown());
}
