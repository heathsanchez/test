use metatron_kernel::{
    id::{ExprId, IdTable, LevelId, NameId},
    machine::{AuthorityId, Machine, RecursorReduction, RecursorRule, Transparency},
    syntax::{Expr, Level},
    value::{Closure, EnvFrame, NeutralHead, Value},
};
use std::collections::HashMap;

fn expose(same: bool, extra: bool, qualified: bool) -> Value {
    let mut es = IdTable::default();
    let mut ls = IdTable::default();
    ls.insert(LevelId(0), Level::Zero).unwrap();
    let mut put = |i, e| {
        es.insert(ExprId(i), e).unwrap();
    };
    put(0, Expr::Sort(LevelId(0)));
    put(1, Expr::BVar(0));
    put(
        2,
        Expr::Const {
            name: NameId(10),
            levels: vec![],
        },
    );
    put(
        3,
        Expr::Const {
            name: NameId(11),
            levels: vec![],
        },
    );
    put(
        4,
        Expr::Lam {
            domain: ExprId(0),
            body: ExprId(1),
        },
    );
    put(
        5,
        Expr::Const {
            name: NameId(30),
            levels: vec![],
        },
    );
    let args = [0, 2, 0, 4, if same { 2 } else { 3 }, 1, 0];
    let mut root = 5;
    for (j, a) in args[..if extra { 7 } else { 6 }].iter().enumerate() {
        let i = 6 + j as u64;
        put(
            i,
            Expr::App {
                fun: ExprId(root),
                arg: ExprId(*a),
            },
        );
        root = i;
    }
    let m = Machine::new(AuthorityId(0), &es, &ls, HashMap::new()).with_recursor_reductions(
        HashMap::from([(
            NameId(30),
            RecursorReduction {
                eq_k: qualified,
                num_params: 2,
                num_indices: 1,
                level_params: vec![],
                rules: vec![RecursorRule {
                    constructor: NameId(12),
                    num_params: 2,
                    num_fields: 0,
                    rhs: ExprId(4),
                }],
            },
        )]),
    );
    m.expose(
        Closure::new(ExprId(root), EnvFrame::empty()),
        Transparency::Reducible,
        128,
    )
    .proven_value()
    .unwrap()
    .clone()
}
#[test]
fn equality_k_reduces_equal_endpoints_and_preserves_extra_arguments() {
    assert!(matches!(expose(true, false, true), Value::Lam { .. }));
    assert!(matches!(expose(true, true, true), Value::Sort(_)));
}
#[test]
fn equality_k_does_not_reduce_distinct_endpoints() {
    assert!(
        matches!(expose(false,false,true),Value::Neutral(n) if matches!(n.head,NeutralHead::Const{name:NameId(30),..}) && n.spine.len()==6)
    );
}

#[test]
fn ordinary_recursor_cannot_use_equality_k() {
    assert!(matches!(expose(true, false, false), Value::Neutral(_)));
}
