use metatron_kernel::{
    environment::Environment,
    id::{ExprId, IdTable, LevelId},
    judgment::Judgment,
    syntax::{Expr, Level},
    typecheck::{TypeChecker, TypeValue},
    value::{Closure, EnvFrame, FreeId},
};

/// Same source syntax, with separately constructed captured environments.
fn compare(expr: ExprId, left: FreeId, right: FreeId, unused: bool) -> Judgment<()> {
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    expressions.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    expressions.insert(ExprId(1), Expr::BVar(0)).unwrap();
    expressions.insert(ExprId(2), Expr::BVar(1)).unwrap();
    expressions.insert(ExprId(3), Expr::App {
        fun: ExprId(1), arg: ExprId(0),
    }).unwrap();
    expressions.insert(ExprId(4), Expr::Lam {
        domain: ExprId(0), body: ExprId(1),
    }).unwrap();
    expressions.insert(ExprId(5), Expr::Lam {
        domain: ExprId(0), body: ExprId(2),
    }).unwrap();
    expressions.insert(ExprId(6), Expr::Let {
        ty: ExprId(0), value: ExprId(0), body: ExprId(1),
    }).unwrap();
    expressions.insert(ExprId(7), Expr::Let {
        ty: ExprId(0), value: ExprId(0), body: ExprId(2),
    }).unwrap();

    let env = Environment::empty();
    let ck = TypeChecker::new(&expressions, &levels, &env);
    // If unused is requested, the second captured argument has no syntactic
    // occurrence in expressions 1, 3, 4 or 6; support must omit that slot.
    let lhs = EnvFrame::empty()
        .extend_free(if unused { FreeId(47) } else { FreeId(49) })
        .extend_free(left);
    let rhs = EnvFrame::empty()
        .extend_free(if unused { FreeId(48) } else { FreeId(49) })
        .extend_free(right);
    assert_ne!(lhs.id(), rhs.id());
    ck.convert(
        &TypeValue::Term(Closure::new(expr, lhs)),
        &TypeValue::Term(Closure::new(expr, rhs)),
        512,
    )
}

#[test]
fn same_source_with_equal_referenced_binders_ignores_unused_frame_slots() {
    assert!(compare(ExprId(3), FreeId(17), FreeId(17), true).is_proven());
}

#[test]
fn source_support_cannot_merge_distinct_data_frees() {
    assert!(!compare(ExprId(3), FreeId(17), FreeId(18), true).is_proven());
}

#[test]
fn binder_zero_under_lambda_shadows_captured_environment() {
    // Body BVar(0) is introduced by this lambda; the captured frame
    // differences have zero support in the source term.
    assert!(compare(ExprId(4), FreeId(17), FreeId(18), true).is_proven());
}

#[test]
fn binder_one_under_lambda_uses_captured_outer_environment() {
    // Body BVar(1) refers to the outside variable. It cannot be treated
    // as a locally bound BVar(0) or dropped as irrelevant.
    assert!(!compare(ExprId(5), FreeId(17), FreeId(18), true).is_proven());
}

#[test]
fn let_bound_zero_is_not_confused_with_captured_outer_variable() {
    assert!(compare(ExprId(6), FreeId(17), FreeId(18), true).is_proven());
    assert!(!compare(ExprId(7), FreeId(17), FreeId(18), true).is_proven());
}
