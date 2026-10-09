use std::collections::HashMap;

use metatron_kernel::environment::{BoolPrimitives, NatPrimitives};
use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::level::LevelTerm;
use metatron_kernel::machine::{
    AuthorityId, DefinitionBody, Machine, ProjectionFieldType, ProjectionSpec,
    TransitionWitness, Transparency,
};
use metatron_kernel::syntax::{Expr, Level};
use metatron_kernel::value::{Closure, EnvFrame, FreeId, NeutralHead, Value};

fn zero_levels() -> IdTable<LevelId, Level> {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    levels
}

#[test]
fn conversion_projection_probe_does_not_delta_reduce_its_structure() {
    let mut exprs = IdTable::default();
    exprs.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    exprs
        .insert(
            ExprId(1),
            Expr::Const {
                name: NameId(2),
                levels: Vec::new(),
            },
        )
        .unwrap();
    exprs
        .insert(
            ExprId(2),
            Expr::App {
                fun: ExprId(1),
                arg: ExprId(0),
            },
        )
        .unwrap();
    exprs
        .insert(
            ExprId(3),
            Expr::Const {
                name: NameId(3),
                levels: Vec::new(),
            },
        )
        .unwrap();
    exprs
        .insert(
            ExprId(4),
            Expr::Proj {
                type_name: NameId(1),
                index: 0,
                structure: ExprId(3),
            },
        )
        .unwrap();

    let definitions = HashMap::from([(
        NameId(3),
        DefinitionBody {
            value: ExprId(2),
            preferred_for_reduction: true,
            level_params: Vec::new(),
        },
    )]);
    let specs = HashMap::from([(
        NameId(1),
        ProjectionSpec {
            constructor: NameId(2),
            num_params: 0,
            field_types: vec![ProjectionFieldType::Derived(ExprId(0))],
            eta_expandable: false,
        },
    )]);
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(1), &exprs, &levels, definitions)
        .with_projection_specs(specs);
    let projection = Closure::new(ExprId(4), EnvFrame::empty());

    assert!(matches!(
        machine
            .expose_for_conversion(projection.clone(), Transparency::Reducible, 32)
            .proven_value(),
        Some(Value::StuckProjection { structure, .. }) if structure.expr == ExprId(3)
    ));
    assert_eq!(
        machine
            .expose(projection, Transparency::Reducible, 32)
            .proven_value(),
        Some(&Value::Sort(LevelTerm::Zero))
    );
}

#[test]
fn semantic_locals_use_explicit_identity_not_source_index_aliasing() {
    let mut exprs = IdTable::default();
    exprs.insert(ExprId(0), Expr::BVar(0)).unwrap();
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(0), &exprs, &levels, HashMap::new());

    let expose = |free| {
        machine
            .expose(
                Closure::new(ExprId(0), EnvFrame::empty().extend_free(free)),
                Transparency::Opaque,
                8,
            )
            .proven_value()
            .unwrap()
            .clone()
    };
    let left = expose(FreeId(7));
    let same = expose(FreeId(7));
    let distinct = expose(FreeId(8));

    assert_eq!(left, same);
    assert_ne!(left, distinct);
    assert!(matches!(
        left,
        Value::Neutral(ref neutral) if neutral.head == NeutralHead::Free(FreeId(7))
    ));
}

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
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(0), &exprs, &levels, HashMap::new());
    let root = Closure::new(ExprId(4), EnvFrame::empty());

    let result = machine.expose(root.clone(), Transparency::Reducible, 64);
    assert_eq!(result.proven_value(), Some(&Value::Sort(LevelTerm::Zero)));

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
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(0), &exprs, &levels, HashMap::new());

    let result = machine.expose_with_witnesses(
        Closure::new(ExprId(2), EnvFrame::empty()),
        Transparency::Reducible,
        64,
    );
    let exposure = result.proven_value().unwrap();
    assert_eq!(exposure.value, Value::Sort(LevelTerm::Zero));
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
            level_params: Vec::new(),
        },
    )]);
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(1), &exprs, &levels, definitions);

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
            level_params: Vec::new(),
        },
    )]);
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(1), &exprs, &levels, definitions);

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
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(0), &exprs, &levels, HashMap::new());

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
            level_params: Vec::new(),
        },
    )]);
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(1), &exprs, &levels, definitions);
    let root = Closure::new(ExprId(1), EnvFrame::empty());

    let reducible = machine
        .expose_with_witnesses(root.clone(), Transparency::Reducible, 8)
        .proven_value()
        .unwrap()
        .clone();
    assert_eq!(reducible.value, Value::Sort(LevelTerm::Zero));
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
            level_params: Vec::new(),
        },
    )]);
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(1), &exprs, &levels, definitions);
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
    assert_eq!(semantic.value, Value::Sort(LevelTerm::Zero));
    assert!(semantic.transitions.contains(&TransitionWitness::Delta));
}

#[test]
fn exhausted_reduction_budget_preserves_unknown() {
    let mut exprs = IdTable::default();
    exprs.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(0), &exprs, &levels, HashMap::new());

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
            level_params: vec![NameId(9)],
        },
    )]);
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(1), &exprs, &levels, definitions);

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

#[test]
fn recursor_output_constructor_does_not_identify_its_symbolic_major() {
    use metatron_kernel::machine::{RecursorReduction, RecursorRule};
    let mut exprs = IdTable::default();
    let nodes = [
        Expr::Sort(LevelId(0)),
        Expr::BVar(0),
        Expr::Const { name: NameId(1), levels: vec![] }, // zero
        Expr::Const { name: NameId(2), levels: vec![] }, // successor
        Expr::App { fun: ExprId(3), arg: ExprId(2) },
        Expr::Const { name: NameId(3), levels: vec![] }, // recursor
        Expr::App { fun: ExprId(5), arg: ExprId(0) },
        Expr::App { fun: ExprId(6), arg: ExprId(4) },
        Expr::App { fun: ExprId(7), arg: ExprId(4) },
        Expr::App { fun: ExprId(8), arg: ExprId(1) },
        Expr::Lam { domain: ExprId(0), body: ExprId(4) },
        Expr::Lam { domain: ExprId(0), body: ExprId(10) },
        Expr::Lam { domain: ExprId(0), body: ExprId(11) },
        Expr::Lam { domain: ExprId(0), body: ExprId(12) },
    ];
    for (index, node) in nodes.into_iter().enumerate() {
        exprs.insert(ExprId(index as u64), node).unwrap();
    }
    // Both branch programs expose successor, but the actual major is free.
    // The machine consumes already certified programs; this isolates dispatch.
    let reduction = RecursorReduction {
        k: false, num_params: 0, num_indices: 0, level_params: vec![],
        rules: vec![
            RecursorRule { constructor: NameId(1), constructor_level_params: vec![],
                num_params: 0, num_fields: 0, rhs: ExprId(12) },
            RecursorRule { constructor: NameId(2), constructor_level_params: vec![],
                num_params: 0, num_fields: 1, rhs: ExprId(13) },
        ],
    };
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(0), &exprs, &levels, HashMap::new())
        .with_recursor_reductions(HashMap::from([(NameId(3), reduction)]));
    let closure = Closure::new(ExprId(9), EnvFrame::empty().extend_free(FreeId(100)));
    let exposed = machine.expose(closure, Transparency::Full, 100);
    assert!(matches!(exposed.proven_value(), Some(Value::Neutral(neutral))
        if matches!(neutral.head, NeutralHead::Const { name: NameId(3), .. })
            && neutral.spine.len() == 4));
}

#[test]
fn symbolic_nat_ble_respects_pinned_constructor_equations() {
    let mut exprs = IdTable::default();
    let zero = NameId(60);
    let succ = NameId(61);
    let ble = NameId(62);
    let true_ctor = NameId(63);
    let false_ctor = NameId(64);
    for (id, name) in [(0, zero), (1, succ), (2, ble)] {
        exprs.insert(ExprId(id), Expr::Const { name, levels: vec![] }).unwrap();
    }
    exprs.insert(ExprId(5), Expr::BVar(0)).unwrap();
    exprs.insert(ExprId(6), Expr::BVar(1)).unwrap();
    for (id, fun, arg) in [
        (7,1,5), (8,1,6),
        (9,2,7), (10,9,8),
        (11,2,5), (12,11,6),
        (13,2,0), (14,13,6),
        (15,2,7), (16,15,0),
    ] {
        exprs.insert(ExprId(id), Expr::App { fun: ExprId(fun), arg: ExprId(arg) }).unwrap();
    }
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(42), &exprs, &levels, HashMap::new())
        .with_nat_primitives(Some(NatPrimitives {
            type_name: NameId(65), type_expr: ExprId(0),
            zero, succ, recursor: NameId(66),
            add: None, sub: None, pred: None, ble: Some(ble), beq: None,
        }))
        .with_bool_primitives(Some(BoolPrimitives { true_ctor, false_ctor }));
    let env = EnvFrame::empty().extend_free(FreeId(73)).extend_free(FreeId(74));
    let exposed = |id| machine.expose(
        Closure::new(ExprId(id), env.clone()), Transparency::Reducible, 64
    ).proven_value().cloned().expect("certified Nat.ble equation");
    // Succ/succ cancels exactly once without equating its free predecessors.
    let result = exposed(10);
    let Value::Neutral(term) = result else { panic!("expected symbolic Nat.ble"); };
    assert_eq!(term.head, NeutralHead::Const { name: ble, levels: vec![] });
    assert_eq!(term.spine.len(), 2);
    assert_eq!(term.spine[0].expr, ExprId(5));
    assert_eq!(term.spine[1].expr, ExprId(6));
    // The zero cases are definitionally computed independently of symbolic n.
    let Value::Neutral(term) = exposed(14) else { panic!("ble zero must return true"); };
    assert_eq!(term.head, NeutralHead::Const { name: true_ctor, levels: vec![] });
    let Value::Neutral(term) = exposed(16) else { panic!("ble succ zero must return false"); };
    assert_eq!(term.head, NeutralHead::Const { name: false_ctor, levels: vec![] });
    // No constructor evidence: ordinary neutral comparison remains pending.
    let Value::Neutral(term) = exposed(12) else { panic!("symbolic ble must remain neutral"); };
    assert_eq!(term.head, NeutralHead::Const { name: ble, levels: vec![] });
}
