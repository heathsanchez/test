use std::collections::HashMap;

use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::machine::{
    AuthorityId, DefinitionBody, Machine, TransitionWitness, Transparency,
};
use metatron_kernel::syntax::Expr;
use metatron_kernel::value::{Closure, EnvFrame, Value};

#[test]
fn beta_uses_explicit_environment_extension() {
    let mut exprs = IdTable::default();
    exprs.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    exprs.insert(ExprId(1), Expr::BVar(0)).unwrap();
    exprs
        .insert(
            ExprId(2),
            Expr::Lam {
                domain: ExprId(0),
                body: ExprId(1),
            },
        )
        .unwrap();
    exprs.insert(ExprId(3), Expr::Sort(LevelId(0))).unwrap();
    exprs
        .insert(
            ExprId(4),
            Expr::App {
                fun: ExprId(2),
                arg: ExprId(3),
            },
        )
        .unwrap();
    let machine = Machine::new(AuthorityId(0), &exprs, HashMap::new());
    let root = Closure::new(ExprId(4), EnvFrame::empty());

    let result = machine.expose(root.clone(), Transparency::Reducible, 64);
    assert_eq!(result.proven_value(), Some(&Value::Sort(LevelId(0))));

    let traced = machine
        .expose_with_witnesses(root, Transparency::Reducible, 64)
        .proven_value()
        .unwrap()
        .transitions
        .clone();
    assert!(traced.contains(&TransitionWitness::Beta));
    assert!(traced.contains(&TransitionWitness::Rigid));
}

#[test]
fn zeta_uses_let_value_without_substitution_copy() {
    let mut exprs = IdTable::default();
    exprs.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    exprs.insert(ExprId(1), Expr::BVar(0)).unwrap();
    exprs
        .insert(
            ExprId(2),
            Expr::Let {
                ty: ExprId(0),
                value: ExprId(0),
                body: ExprId(1),
            },
        )
        .unwrap();
    let machine = Machine::new(AuthorityId(0), &exprs, HashMap::new());

    let result = machine.expose_with_witnesses(
        Closure::new(ExprId(2), EnvFrame::empty()),
        Transparency::Reducible,
        64,
    );
    let exposure = result.proven_value().unwrap();
    assert_eq!(exposure.value, Value::Sort(LevelId(0)));
    assert!(exposure.transitions.contains(&TransitionWitness::Zeta));
}

#[test]
fn cyclic_delta_returns_unknown() {
    let mut exprs = IdTable::default();
    exprs
        .insert(
            ExprId(0),
            Expr::Const {
                name: NameId(1),
                levels: Vec::new(),
            },
        )
        .unwrap();
    let definitions = HashMap::from([(
        NameId(1),
        DefinitionBody {
            value: ExprId(0),
            preferred_for_reduction: true,
            level_param_count: 0,
        },
    )]);
    let machine = Machine::new(AuthorityId(1), &exprs, definitions);

    assert!(
        machine
            .expose(
                Closure::new(ExprId(0), EnvFrame::empty()),
                Transparency::Reducible,
                16,
            )
            .is_unknown()
    );
}

#[test]
fn full_transparency_keeps_a_nonpreferred_delta_cycle_unknown() {
    let mut exprs = IdTable::default();
    exprs
        .insert(
            ExprId(0),
            Expr::Const {
                name: NameId(1),
                levels: Vec::new(),
            },
        )
        .unwrap();
    let definitions = HashMap::from([(
        NameId(1),
        DefinitionBody {
            value: ExprId(0),
            preferred_for_reduction: false,
            level_param_count: 0,
        },
    )]);
    let machine = Machine::new(AuthorityId(1), &exprs, definitions);

    assert!(
        machine
            .expose(
                Closure::new(ExprId(0), EnvFrame::empty()),
                Transparency::Full,
                16,
            )
            .is_unknown()
    );
}

#[test]
fn revisiting_shared_syntax_after_beta_is_not_a_cycle() {
    let mut exprs = IdTable::default();
    exprs.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    exprs.insert(ExprId(1), Expr::BVar(0)).unwrap();
    exprs
        .insert(
            ExprId(2),
            Expr::Lam {
                domain: ExprId(0),
                body: ExprId(1),
            },
        )
        .unwrap();
    exprs
        .insert(
            ExprId(3),
            Expr::App {
                fun: ExprId(2),
                arg: ExprId(2),
            },
        )
        .unwrap();
    let machine = Machine::new(AuthorityId(0), &exprs, HashMap::new());

    assert!(
        machine
            .expose(
                Closure::new(ExprId(3), EnvFrame::empty()),
                Transparency::Reducible,
                64,
            )
            .is_proven()
    );
}

#[test]
fn delta_requires_reducible_transparency_and_records_its_witness() {
    let mut exprs = IdTable::default();
    exprs.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    exprs
        .insert(
            ExprId(1),
            Expr::Const {
                name: NameId(4),
                levels: Vec::new(),
            },
        )
        .unwrap();
    let definitions = HashMap::from([(
        NameId(4),
        DefinitionBody {
            value: ExprId(0),
            preferred_for_reduction: true,
            level_param_count: 0,
        },
    )]);
    let machine = Machine::new(AuthorityId(1), &exprs, definitions);
    let root = Closure::new(ExprId(1), EnvFrame::empty());

    let reducible = machine
        .expose_with_witnesses(root.clone(), Transparency::Reducible, 8)
        .proven_value()
        .unwrap()
        .clone();
    assert_eq!(reducible.value, Value::Sort(LevelId(0)));
    assert!(reducible.transitions.contains(&TransitionWitness::Delta));

    let opaque = machine
        .expose_with_witnesses(root, Transparency::Opaque, 8)
        .proven_value()
        .unwrap()
        .clone();
    assert!(matches!(opaque.value, Value::Neutral(_)));
    assert!(!opaque.transitions.contains(&TransitionWitness::Delta));
}

#[test]
fn full_transparency_can_request_a_nonpreferred_definition_body() {
    let mut exprs = IdTable::default();
    exprs.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    exprs
        .insert(
            ExprId(1),
            Expr::Const {
                name: NameId(4),
                levels: Vec::new(),
            },
        )
        .unwrap();
    let definitions = HashMap::from([(
        NameId(4),
        DefinitionBody {
            value: ExprId(0),
            preferred_for_reduction: false,
            level_param_count: 0,
        },
    )]);
    let machine = Machine::new(AuthorityId(1), &exprs, definitions);
    let root = Closure::new(ExprId(1), EnvFrame::empty());

    let cheap = machine
        .expose_with_witnesses(root.clone(), Transparency::Reducible, 8)
        .proven_value()
        .unwrap()
        .clone();
    assert!(matches!(cheap.value, Value::Neutral(_)));
    assert!(!cheap.transitions.contains(&TransitionWitness::Delta));

    let semantic = machine
        .expose_with_witnesses(root, Transparency::Full, 8)
        .proven_value()
        .unwrap()
        .clone();
    assert_eq!(semantic.value, Value::Sort(LevelId(0)));
    assert!(semantic.transitions.contains(&TransitionWitness::Delta));
}

#[test]
fn exhausted_reduction_budget_preserves_unknown() {
    let mut exprs = IdTable::default();
    exprs.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    let machine = Machine::new(AuthorityId(0), &exprs, HashMap::new());

    assert!(
        machine
            .expose(
                Closure::new(ExprId(0), EnvFrame::empty()),
                Transparency::Reducible,
                0,
            )
            .is_unknown()
    );
}

#[test]
fn polymorphic_delta_preserves_unknown_until_level_instantiation_is_explicit() {
    let mut exprs = IdTable::default();
    exprs
        .insert(
            ExprId(0),
            Expr::Const {
                name: NameId(5),
                levels: vec![LevelId(0)],
            },
        )
        .unwrap();
    let definitions = HashMap::from([(
        NameId(5),
        DefinitionBody {
            value: ExprId(0),
            preferred_for_reduction: true,
            level_param_count: 1,
        },
    )]);
    let machine = Machine::new(AuthorityId(1), &exprs, definitions);

    assert!(
        machine
            .expose(
                Closure::new(ExprId(0), EnvFrame::empty()),
                Transparency::Reducible,
                8,
            )
            .is_unknown()
    );
}
