use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::machine::{
    AuthorityId, DefinitionBody, Machine, RecursorReduction, RecursorRule, Transparency,
};
use metatron_kernel::syntax::{Expr, Level};
use metatron_kernel::value::{Closure, EnvFrame, NeutralHead, Value};
use std::collections::HashMap;

fn run(major: Expr, extra_argument: bool) -> Value {
    let mut es = IdTable::default();
    let mut ls = IdTable::default();
    ls.insert(LevelId(0), Level::Zero).unwrap();
    let expressions = [
        Expr::Sort(LevelId(0)),
        Expr::Const {
            name: NameId(10),
            levels: vec![],
        },
        major,
        Expr::BVar(0),
        Expr::Lam {
            domain: ExprId(0),
            body: ExprId(3),
        },
        Expr::Lam {
            domain: ExprId(0),
            body: ExprId(4),
        },
        Expr::Const {
            name: NameId(30),
            levels: vec![],
        },
        Expr::App {
            fun: ExprId(6),
            arg: ExprId(0),
        },
        Expr::App {
            fun: ExprId(7),
            arg: ExprId(4),
        },
        Expr::App {
            fun: ExprId(8),
            arg: ExprId(2),
        },
        Expr::App {
            fun: ExprId(9),
            arg: ExprId(0),
        },
    ];
    for (i, e) in expressions.into_iter().enumerate() {
        es.insert(ExprId(i as u64), e).unwrap();
    }
    let machine = Machine::new(
        AuthorityId(0),
        &es,
        &ls,
        HashMap::from([(
            NameId(20),
            DefinitionBody {
                value: ExprId(1),
                preferred_for_reduction: true,
                level_params: vec![],
            },
        )]),
    )
    .with_recursor_reductions(HashMap::from([(
        NameId(30),
        RecursorReduction {
            eq_k: false,
            num_params: 0,
            num_indices: 0,
            level_params: vec![],
            rules: vec![RecursorRule {
                constructor: NameId(10),
                num_params: 0,
                num_fields: 0,
                rhs: ExprId(5),
            }],
        },
    )]));
    machine
        .expose(
            Closure::new(
                ExprId(if extra_argument { 10 } else { 9 }),
                EnvFrame::empty(),
            ),
            Transparency::Full,
            256,
        )
        .proven_value()
        .unwrap()
        .clone()
}

#[test]
fn recursor_reduces_computed_major_and_preserves_pending_application() {
    let major = Expr::Const {
        name: NameId(20),
        levels: vec![],
    };
    assert!(matches!(run(major.clone(), false), Value::Lam { .. }));
    assert!(matches!(run(major, true), Value::Sort(_)));
}

#[test]
fn recursor_does_not_reduce_free_or_wrong_constructor_major() {
    for major in [
        Expr::BVar(0),
        Expr::Const {
            name: NameId(11),
            levels: vec![],
        },
    ] {
        assert!(matches!(run(major, false), Value::Neutral(n)
            if matches!(n.head, NeutralHead::Const {name:NameId(30),..}) && n.spine.len()==3));
    }
}
