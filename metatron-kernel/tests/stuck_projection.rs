use metatron_kernel::environment::{ConstantDecl, Environment};
use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::machine::{
    AuthorityId, Machine, ProjectionFieldType, ProjectionSpec, Transparency,
};
use metatron_kernel::syntax::{Expr, Level};
use metatron_kernel::typecheck::{TypeChecker, TypeValue};
use metatron_kernel::value::{Closure, EnvFrame, NeutralHead, Value};
use std::collections::HashMap;

#[test]
fn stuck_constant_projection_preserves_field_and_pending_arguments() {
    let mut es = IdTable::default();
    let mut ls = IdTable::default();
    ls.insert(LevelId(0), Level::Zero).unwrap();
    let expressions = [
        Expr::Const {
            name: NameId(20),
            levels: vec![],
        },
        Expr::Sort(LevelId(0)),
        Expr::Proj {
            type_name: NameId(10),
            index: 0,
            structure: ExprId(0),
        },
        Expr::App {
            fun: ExprId(2),
            arg: ExprId(1),
        },
    ];
    for (i, e) in expressions.into_iter().enumerate() {
        es.insert(ExprId(i as u64), e).unwrap();
    }
    let machine = Machine::new(AuthorityId(0), &es, &ls, HashMap::new()).with_projection_specs(
        HashMap::from([(
            NameId(10),
            ProjectionSpec {
                constructor: NameId(11),
                num_params: 0,
                field_types: vec![ProjectionFieldType::Derived(ExprId(1))],
            },
        )]),
    );
    let result = machine.expose(
        Closure::new(ExprId(3), EnvFrame::empty()),
        Transparency::Reducible,
        64,
    );
    let Value::Neutral(n) = result
        .proven_value()
        .expect("stuck projection is a neutral value")
    else {
        panic!("not a neutral")
    };
    let NeutralHead::Projection {
        type_name,
        index,
        structure,
    } = &n.head
    else {
        panic!("lost projection")
    };
    assert_eq!((*type_name, *index), (NameId(10), 0));
    assert!(matches!(
        structure.head,
        NeutralHead::Const {
            name: NameId(20),
            ..
        }
    ));
    assert_eq!(n.spine.len(), 1);
    assert_eq!(n.spine[0].expr, ExprId(1));
}

#[test]
fn projection_congruence_checks_structure_arguments_and_field_identity() {
    let mut es = IdTable::default();
    let mut ls = IdTable::default();
    ls.insert(LevelId(0), Level::Zero).unwrap();
    let xs = [
        Expr::Sort(LevelId(0)),
        Expr::BVar(0),
        Expr::Lam {
            domain: ExprId(0),
            body: ExprId(1),
        },
        Expr::Const {
            name: NameId(20),
            levels: vec![],
        },
        Expr::Const {
            name: NameId(21),
            levels: vec![],
        },
        Expr::App {
            fun: ExprId(2),
            arg: ExprId(4),
        },
        Expr::App {
            fun: ExprId(3),
            arg: ExprId(4),
        },
        Expr::App {
            fun: ExprId(3),
            arg: ExprId(5),
        },
        Expr::Proj {
            type_name: NameId(10),
            index: 0,
            structure: ExprId(6),
        },
        Expr::Proj {
            type_name: NameId(10),
            index: 0,
            structure: ExprId(7),
        },
        Expr::Proj {
            type_name: NameId(10),
            index: 1,
            structure: ExprId(7),
        },
        Expr::Const {
            name: NameId(22),
            levels: vec![],
        },
        Expr::App {
            fun: ExprId(3),
            arg: ExprId(11),
        },
        Expr::Proj {
            type_name: NameId(10),
            index: 0,
            structure: ExprId(12),
        },
        Expr::Const {
            name: NameId(23),
            levels: vec![],
        },
        Expr::App {
            fun: ExprId(3),
            arg: ExprId(14),
        },
        Expr::Proj {
            type_name: NameId(10),
            index: 0,
            structure: ExprId(15),
        },
    ];
    for (i, e) in xs.into_iter().enumerate() {
        es.insert(ExprId(i as u64), e).unwrap();
    }
    let mut env = Environment::empty();
    for n in [10, 11, 20, 21, 22] {
        env = env
            .extend(NameId(n), ConstantDecl::axiom(vec![], ExprId(0)))
            .unwrap();
    }
    env = env
        .extend(
            NameId(23),
            ConstantDecl::definition(vec![], ExprId(0), ExprId(4), false),
        )
        .unwrap();
    env = env
        .install_projection_spec(
            NameId(10),
            ProjectionSpec {
                constructor: NameId(11),
                num_params: 0,
                field_types: vec![ProjectionFieldType::Derived(ExprId(0)); 2],
            },
        )
        .unwrap();
    let ck = TypeChecker::new(&es, &ls, &env);
    let ty = |i| TypeValue::Term(Closure::new(ExprId(i), EnvFrame::empty()));
    assert!(ck.convert(&ty(8), &ty(9), 1024).is_proven());
    assert!(!ck.convert(&ty(8), &ty(10), 1024).is_proven());
    assert!(!ck.convert(&ty(8), &ty(13), 1024).is_proven());
    assert!(ck.convert(&ty(8), &ty(16), 1024).is_proven());
    assert!(
        !metatron_kernel::convert::convert_with_policy(
            &ck,
            &ty(8),
            &ty(16),
            1024,
            metatron_kernel::convert::DeltaPolicy::PreferredOnly
        )
        .is_proven()
    );
}

#[test]
fn projection_congruence_keeps_local_binding_identity() {
    use metatron_kernel::value::FreeId;
    let mut es = IdTable::default();
    let mut ls = IdTable::default();
    ls.insert(LevelId(0), Level::Zero).unwrap();
    for (i, e) in [
        Expr::Sort(LevelId(0)),
        Expr::BVar(0),
        Expr::Const {
            name: NameId(20),
            levels: vec![],
        },
        Expr::App {
            fun: ExprId(2),
            arg: ExprId(1),
        },
        Expr::Proj {
            type_name: NameId(10),
            index: 0,
            structure: ExprId(3),
        },
    ]
    .into_iter()
    .enumerate()
    {
        es.insert(ExprId(i as u64), e).unwrap();
    }
    let mut env = Environment::empty();
    for n in [10, 11, 20] {
        env = env
            .extend(NameId(n), ConstantDecl::axiom(vec![], ExprId(0)))
            .unwrap();
    }
    env = env
        .install_projection_spec(
            NameId(10),
            ProjectionSpec {
                constructor: NameId(11),
                num_params: 0,
                field_types: vec![ProjectionFieldType::Derived(ExprId(0))],
            },
        )
        .unwrap();
    let ck = TypeChecker::new(&es, &ls, &env);
    let ty = |free| {
        TypeValue::Term(Closure::new(
            ExprId(4),
            EnvFrame::empty().extend_free(FreeId(free)),
        ))
    };
    assert!(ck.convert(&ty(0), &ty(0), 1024).is_proven());
    assert!(!ck.convert(&ty(0), &ty(1), 1024).is_proven());
}

#[test]
fn dependency_closed_nat_no_confusion_prefix_is_accepted() {
    use metatron_kernel::verdict::Verdict;
    assert_eq!(
        metatron_kernel::run(std::io::Cursor::new(include_bytes!(
            "fixtures/nat_no_confusion_prefix.ndjson"
        ))),
        Verdict::Accept
    );
}
