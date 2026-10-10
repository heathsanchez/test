use metatron_kernel::{
    environment::Environment,
    id::{ExprId,IdTable,LevelId},
    syntax::{Expr,Level},
    typecheck::{TypeChecker,TypeValue},
    value::{Closure,EnvFrame,FreeId},
};

fn fixture(different_outer: bool, mismatch: bool) -> bool {
    let mut expressions=IdTable::default();
    let mut levels=IdTable::default();
    levels.insert(LevelId(0),Level::Zero).unwrap();
    expressions.insert(ExprId(0),Expr::Sort(LevelId(0))).unwrap();
    expressions.insert(ExprId(1),Expr::BVar(0)).unwrap();
    expressions.insert(ExprId(2),Expr::BVar(1)).unwrap();
    expressions.insert(ExprId(3),Expr::Lam{domain:ExprId(0),body:ExprId(1)}).unwrap();
    expressions.insert(ExprId(4),Expr::Lam{domain:ExprId(0),body:ExprId(1)}).unwrap();
    expressions.insert(ExprId(5),Expr::Lam{domain:ExprId(0),body:ExprId(2)}).unwrap();
    expressions.insert(ExprId(6),Expr::BVar(0)).unwrap();
    let env=Environment::empty();
    let ck=TypeChecker::new(&expressions,&levels,&env);
    let left_outer=EnvFrame::empty().extend_free(FreeId(17));
    let right_outer=EnvFrame::empty().extend_free(if different_outer {FreeId(18)} else {FreeId(17)});
    let lhs=Closure::new(ExprId(6),EnvFrame::empty().extend(
        Closure::new(if mismatch {ExprId(5)} else {ExprId(3)},left_outer)
    ));
    let rhs=Closure::new(ExprId(6),EnvFrame::empty().extend(
        Closure::new(if mismatch {ExprId(5)} else {ExprId(4)},right_outer)
    ));
    assert_ne!(lhs.env.id(),rhs.env.id());
    ck.convert(&TypeValue::Term(lhs),&TypeValue::Term(rhs),2048).is_proven()
}

#[test]
fn alpha_renamed_lambdas_with_same_used_captures_are_convertible() {
    assert!(fixture(false,false));
}
#[test]
fn different_unused_capture_is_safe_when_lambda_body_is_bound_local() {
    assert!(fixture(true,false));
}
#[test]
fn different_used_outer_capture_never_becomes_equal_by_source_identity() {
    assert!(!fixture(true,true));
}
#[test]
fn same_used_outer_capture_stays_convertible() {
    assert!(fixture(false,true));
}
