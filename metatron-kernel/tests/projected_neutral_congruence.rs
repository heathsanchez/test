use metatron_kernel::{
    environment::{ConstantDecl, Environment},
    id::{ExprId, IdTable, LevelId, NameId},
    judgment::Judgment,
    machine::{ProjectionFieldType, ProjectionSpec},
    syntax::{Expr, Level},
    typecheck::{TypeChecker, TypeValue},
    value::{Closure, EnvFrame, FreeId},
};

/// A projection of a symbolic application of a free function.  Its receiver
/// is a neutral with a nonempty argument spine, and each independently
/// constructed environment has a different frame identity.
///
/// Congruence must depend on semantic argument comparison, not frame IDs.
fn compare_projected_receivers(
    left_receiver: FreeId,
    right_receiver: FreeId,
    left_arg: FreeId,
    right_arg: FreeId,
    left_index: u64,
    right_index: u64,
) -> Judgment<()> {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();

    let mut expressions = IdTable::default();
    expressions.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    expressions.insert(ExprId(1), Expr::BVar(0)).unwrap();
    expressions.insert(ExprId(2), Expr::BVar(1)).unwrap();
    expressions.insert(
        ExprId(3), Expr::App { fun: ExprId(1), arg: ExprId(2) },
    ).unwrap();
    expressions.insert(
        ExprId(4), Expr::Proj {
            type_name: NameId(1), index: left_index, structure: ExprId(3),
        },
    ).unwrap();
    expressions.insert(
        ExprId(5), Expr::Proj {
            type_name: NameId(1), index: right_index, structure: ExprId(3),
        },
    ).unwrap();
    expressions.insert(
        ExprId(6), Expr::App { fun: ExprId(4), arg: ExprId(0) },
    ).unwrap();
    expressions.insert(
        ExprId(7), Expr::App { fun: ExprId(5), arg: ExprId(0) },
    ).unwrap();

    let environment = Environment::empty()
        .extend(NameId(1), ConstantDecl::axiom(vec![], ExprId(0)))
        .unwrap()
        .extend(NameId(2), ConstantDecl::axiom(vec![], ExprId(0)))
        .unwrap()
        .install_projection_spec(NameId(1), ProjectionSpec {
            constructor: NameId(2),
            num_params: 0,
            field_types: vec![
                ProjectionFieldType::Derived(ExprId(0)),
                ProjectionFieldType::Derived(ExprId(0)),
            ],
            eta_expandable: false,
        }).unwrap();
    let checker = TypeChecker::new(&expressions, &levels, &environment);

    let left_env = EnvFrame::empty()
        .extend_free(left_arg)
        .extend_free(left_receiver);
    let right_env = EnvFrame::empty()
        .extend_free(right_arg)
        .extend_free(right_receiver);
    assert_ne!(left_env.id(), right_env.id());

    checker.convert(
        &TypeValue::Term(Closure::new(ExprId(6), left_env)),
        &TypeValue::Term(Closure::new(ExprId(7), right_env)),
        1024,
    )
}

#[test]
fn alpha_equivalent_projection_receivers_with_distinct_frames_are_convertible() {
    assert!(compare_projected_receivers(
        FreeId(17), FreeId(17), FreeId(19), FreeId(19), 0, 0
    ).is_proven());
}

#[test]
fn distinct_data_receiver_arguments_are_not_identified() {
    // Equal source AST, function and field index are insufficient: Free19
    // and Free20 are unrelated data variables and have no equality proof.
    assert!(!compare_projected_receivers(
        FreeId(17), FreeId(17), FreeId(19), FreeId(20), 0, 0
    ).is_proven());
}

#[test]
fn distinct_projected_receiver_heads_are_not_identified() {
    assert!(!compare_projected_receivers(
        FreeId(17), FreeId(18), FreeId(19), FreeId(19), 0, 0
    ).is_proven());
}

#[test]
fn different_projection_fields_are_not_identified() {
    assert!(!compare_projected_receivers(
        FreeId(17), FreeId(17), FreeId(19), FreeId(19), 0, 1
    ).is_proven());
}
