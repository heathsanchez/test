use metatron_kernel::{
    environment::{ConstantDecl, Environment},
    id::{ExprId, IdTable, LevelId, NameId},
    machine::{ProjectionFieldType, ProjectionSpec},
    syntax::{Expr, Level},
    typecheck::TypeChecker,
    value::{Closure, EnvFrame},
};

fn projection_warrant_fixture() -> (
    IdTable<ExprId, Expr>, IdTable<LevelId, Level>, Environment,
) {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    levels.insert(LevelId(1), Level::Succ(LevelId(0))).unwrap();

    let mut expressions = IdTable::default();
    let exprs = [
        (0, Expr::Sort(LevelId(0))), // Prop
        (1, Expr::Sort(LevelId(1))), // Type
        (2, Expr::Const { name: NameId(1), levels: vec![] }), // A : Prop
        (3, Expr::Const { name: NameId(2), levels: vec![] }), // p : A
        (4, Expr::Const { name: NameId(3), levels: vec![] }), // Box : Type
        (5, Expr::Const { name: NameId(4), levels: vec![] }), // box : Box
        (6, Expr::Proj { type_name: NameId(3), index: 0, structure: ExprId(5) }),
        (7, Expr::Pi { domain: ExprId(2), body: ExprId(0) }),
        (8, Expr::Pi { domain: ExprId(2), body: ExprId(7) }),
        (9, Expr::Const { name: NameId(5), levels: vec![] }), // R : A → A → Prop
        (10, Expr::App { fun: ExprId(9), arg: ExprId(6) }),
        (11, Expr::App { fun: ExprId(10), arg: ExprId(6) }), // R box.1 box.1
        (12, Expr::Proj { type_name: NameId(3), index: 1, structure: ExprId(5) }),
        (13, Expr::App { fun: ExprId(9), arg: ExprId(12) }),
        (14, Expr::App { fun: ExprId(13), arg: ExprId(6) }), // bad field index
        (15, Expr::Pi { domain: ExprId(2), body: ExprId(4) }), // Box.mk : A → Box
        (16, Expr::Const { name: NameId(7), levels: vec![] }), // OtherBox : Type
        (17, Expr::Const { name: NameId(8), levels: vec![] }), // other : OtherBox
        (18, Expr::Proj { type_name: NameId(3), index: 0, structure: ExprId(17) }),
        (19, Expr::App { fun: ExprId(9), arg: ExprId(18) }),
        (20, Expr::App { fun: ExprId(19), arg: ExprId(6) }), // wrong inductive receiver
    ];
    for (id, expr) in exprs {
        expressions.insert(ExprId(id), expr).unwrap();
    }

    let env = Environment::empty()
        .extend(NameId(1), ConstantDecl::axiom(vec![], ExprId(0))).unwrap()
        .extend(NameId(2), ConstantDecl::axiom(vec![], ExprId(2))).unwrap()
        .extend(NameId(3), ConstantDecl::inductive_type(vec![], ExprId(1))).unwrap()
        .extend(NameId(4), ConstantDecl::axiom(vec![], ExprId(4))).unwrap()
        .extend(NameId(5), ConstantDecl::axiom(vec![], ExprId(8))).unwrap()
        .extend(NameId(6), ConstantDecl::constructor(vec![], ExprId(15))).unwrap()
        .extend(NameId(7), ConstantDecl::inductive_type(vec![], ExprId(1))).unwrap()
        .extend(NameId(8), ConstantDecl::axiom(vec![], ExprId(16))).unwrap()
        .install_projection_spec(
            NameId(3),
            ProjectionSpec {
                constructor: NameId(6),
                num_params: 0,
                field_types: vec![ProjectionFieldType::Derived(ExprId(2))],
                eta_expandable: false,
            },
        ).unwrap();
    (expressions, levels, env)
}

#[test]
fn captured_projection_field_is_typed_from_checked_constructor_telescope() {
    let (expressions, levels, env) = projection_warrant_fixture();
    let checker = TypeChecker::new(&expressions, &levels, &env);
    let result = checker.certify_applied_proposition_in_context(
        &Closure::new(ExprId(11), EnvFrame::empty()), &[], 4096,
    );
    assert!(result.is_proven(), "complete typed projection relation should be Prop: {result:?}");
}

#[test]
fn captured_projection_out_of_range_must_never_certify() {
    let (expressions, levels, env) = projection_warrant_fixture();
    let checker = TypeChecker::new(&expressions, &levels, &env);
    let result = checker.certify_applied_proposition_in_context(
        &Closure::new(ExprId(14), EnvFrame::empty()), &[], 4096,
    );
    assert!(!result.is_proven(), "invalid projection index must not certify: {result:?}");
}

#[test]
fn captured_projection_wrong_inductive_receiver_must_never_certify() {
    let (expressions, levels, env) = projection_warrant_fixture();
    let checker = TypeChecker::new(&expressions, &levels, &env);
    let result = checker.certify_applied_proposition_in_context(
        &Closure::new(ExprId(20), EnvFrame::empty()), &[], 4096,
    );
    assert!(!result.is_proven(), "wrong receiver inductive must not certify: {result:?}");
}
