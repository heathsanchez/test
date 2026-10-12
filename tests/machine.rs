use std::collections::HashMap;

use metatron_kernel::environment::{BoolPrimitives, NatPrimitives};
use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::level::LevelTerm;
use metatron_kernel::machine::{
    AuthorityId, DefinitionBody, Machine, ProjectionFieldType, ProjectionSpec,
    TransitionWitness, Transparency,
};
use metatron_kernel::syntax::{Expr, Level};
use metatron_kernel::value::{Closure, EnvFrame, FreeId, Neutral, NeutralHead, Value};

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
            add: None, mul:None, pow:None, sub: None, pred: None, virtual_bvar_zero: None, ble: Some(ble), beq: None,
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

#[test]
fn symbolic_nat_sub_successor_is_exact_predicate_computation() {
    let mut exprs = IdTable::default();
    let put_const = |exprs: &mut IdTable<ExprId, Expr>, id, name| {
        exprs.insert(ExprId(id), Expr::Const { name: NameId(name), levels: vec![] }).unwrap();
    };
    put_const(&mut exprs, 0, 65); // Nat
    exprs.insert(ExprId(1), Expr::BVar(0)).unwrap();
    put_const(&mut exprs, 2, 11); // Nat.succ
    exprs.insert(ExprId(3), Expr::App { fun: ExprId(2), arg: ExprId(1) }).unwrap();
    put_const(&mut exprs, 4, 12); // Nat.sub
    exprs.insert(ExprId(5), Expr::App { fun: ExprId(4), arg: ExprId(1) }).unwrap();
    exprs.insert(ExprId(6), Expr::App { fun: ExprId(5), arg: ExprId(3) }).unwrap();
    exprs.insert(ExprId(7), Expr::App { fun: ExprId(5), arg: ExprId(1) }).unwrap();
    put_const(&mut exprs, 8, 13); // Nat.pred
    exprs.insert(ExprId(9), Expr::App { fun: ExprId(8), arg: ExprId(3) }).unwrap();

    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(7), &exprs, &levels, HashMap::new())
        .with_nat_primitives(Some(NatPrimitives {
            type_name: NameId(65), type_expr: ExprId(0),
            zero: NameId(10), succ: NameId(11), recursor: NameId(66),
            add: None, mul:None, pow:None, sub: Some(NameId(12)), pred: Some(NameId(13)),
            virtual_bvar_zero: Some(ExprId(1)),
            ble: None, beq: None,
        }));
    let frame = EnvFrame::empty().extend_free(FreeId(7));
    let left = machine.expose(Closure::new(ExprId(6), frame.clone()), Transparency::Reducible, 128);
    let Some(Value::Neutral(outer)) = left.proven_value() else {
        panic!("symbolic sub-successor should normalize to Nat.pred");
    };
    assert_eq!(outer.head, NeutralHead::Const { name: NameId(13), levels: vec![] });
    assert_eq!(outer.spine.len(), 1);
    let inside = machine.expose(outer.spine[0].clone(), Transparency::Opaque, 64);
    let Some(Value::Neutral(inner)) = inside.proven_value() else {
        panic!("symbolic Nat.sub inner closure was not preserved");
    };
    assert_eq!(inner.head, NeutralHead::Const { name: NameId(12), levels: vec![] });
    assert_eq!(inner.spine.len(), 2);
    let variable = machine.expose(Closure::new(ExprId(7), frame.clone()), Transparency::Reducible, 64);
    assert!(matches!(variable.proven_value(),
        Some(Value::Neutral(neutral)) if neutral.head == NeutralHead::Const { name: NameId(12), levels: vec![] }
    ));
    let pred_succ = machine.expose(Closure::new(ExprId(9), frame), Transparency::Reducible, 64);
    assert!(matches!(pred_succ.proven_value(),
        Some(Value::Neutral(neutral)) if neutral.head == NeutralHead::Free(FreeId(7))
    ));
}

#[test]
fn nat_add_symbolic_right_successor_zero_is_succ_without_index_assumption() {
    let mut exprs=IdTable::default();
    exprs.insert(ExprId(0),Expr::BVar(0)).unwrap();
    exprs.insert(ExprId(1),Expr::Const { name: NameId(10), levels: vec![] }).unwrap();
    exprs.insert(ExprId(2),Expr::Const { name: NameId(11), levels: vec![] }).unwrap();
    exprs.insert(ExprId(3),Expr::App { fun: ExprId(2), arg: ExprId(1) }).unwrap();
    exprs.insert(ExprId(4),Expr::Const { name: NameId(20), levels: vec![] }).unwrap();
    exprs.insert(ExprId(5),Expr::App { fun: ExprId(4), arg: ExprId(0) }).unwrap();
    exprs.insert(ExprId(6),Expr::App { fun: ExprId(5), arg: ExprId(3) }).unwrap();
    let levels=zero_levels();
    let machine=Machine::new(AuthorityId(8), &exprs, &levels, HashMap::new())
      .with_nat_primitives(Some(NatPrimitives {
        type_name:NameId(65),type_expr:ExprId(0),zero:NameId(10),
        succ:NameId(11),recursor:NameId(66),add:Some(NameId(20)),mul:None,pow:None,
        sub:None,pred:None,virtual_bvar_zero:Some(ExprId(0)),ble:None,beq:None,
      }));
    let frame=EnvFrame::empty().extend_free(FreeId(17));
    let got=machine.expose(Closure::new(ExprId(6),frame),Transparency::Reducible,64);
    let Some(Value::Neutral(s))=got.proven_value() else { panic!("Nat.add arbitrary (succ zero) must reduce"); };
    assert_eq!(s.head,NeutralHead::Const{name:NameId(11),levels:vec![]});
    assert_eq!(s.spine.len(),1);
    let arg=machine.expose(s.spine[0].clone(),Transparency::Opaque,16);
    assert!(matches!(arg.proven_value(),Some(Value::Neutral(n)) if n.head==NeutralHead::Free(FreeId(17))));
}


#[test]
fn symbolic_nat_sub_succ_zero_is_exact_source_equation() {
    // The checked Nat.sub and Nat.pred equations imply
    //   Nat.sub (Nat.succ x) (Nat.succ Nat.zero) = x.
    // A general symbolic second predecessor y is NOT interchangeable with zero.
    let mut exprs = IdTable::default();
    exprs.insert(ExprId(0), Expr::BVar(0)).unwrap(); // arbitrary x
    exprs.insert(ExprId(1), Expr::Const { name: NameId(10), levels: vec![] }).unwrap();
    exprs.insert(ExprId(2), Expr::Const { name: NameId(11), levels: vec![] }).unwrap();
    exprs.insert(ExprId(3), Expr::App { fun: ExprId(2), arg: ExprId(0) }).unwrap(); // succ x
    exprs.insert(ExprId(4), Expr::App { fun: ExprId(2), arg: ExprId(1) }).unwrap(); // succ zero
    exprs.insert(ExprId(5), Expr::Const { name: NameId(12), levels: vec![] }).unwrap();
    exprs.insert(ExprId(6), Expr::App { fun: ExprId(5), arg: ExprId(3) }).unwrap();
    exprs.insert(ExprId(7), Expr::App { fun: ExprId(6), arg: ExprId(4) }).unwrap();
    exprs.insert(ExprId(8), Expr::BVar(1)).unwrap(); // arbitrary y
    exprs.insert(ExprId(9), Expr::App { fun: ExprId(2), arg: ExprId(8) }).unwrap();
    exprs.insert(ExprId(10), Expr::App { fun: ExprId(6), arg: ExprId(9) }).unwrap();
    let levels = zero_levels();
    let machine = Machine::new(AuthorityId(4242), &exprs, &levels, HashMap::new())
        .with_nat_primitives(Some(NatPrimitives {
            type_name: NameId(65), type_expr: ExprId(1),
            zero: NameId(10), succ: NameId(11), recursor: NameId(66),
            add: None, mul:None, pow:None, sub: Some(NameId(12)), pred: Some(NameId(13)),
            virtual_bvar_zero: Some(ExprId(0)), ble: None, beq: None,
        }));
    let env = EnvFrame::empty().extend_free(FreeId(18)).extend_free(FreeId(17));
    let positive = machine.expose(Closure::new(ExprId(7), env.clone()), Transparency::Reducible, 128);
    assert!(matches!(positive.proven_value(),
        Some(Value::Neutral(v)) if v.head == NeutralHead::Free(FreeId(17)) && v.spine.is_empty()
    ), "sub (succ x) (succ zero) must reduce to x without assuming x is concrete: {positive:?}");
    let negative = machine.expose(Closure::new(ExprId(10), env), Transparency::Reducible, 128);
    assert!(matches!(negative.proven_value(),
        Some(Value::Neutral(v)) if v.head == NeutralHead::Const { name: NameId(13), levels: vec![] }
    ), "sub (succ x) (succ y) must not be rewritten to x for unknown y: {negative:?}");
}

#[test]
fn constructor_demand_follows_computed_lexical_major_and_respects_fuel() {
    use metatron_kernel::machine::{RecursorReduction, RecursorRule};
    let mut exprs=IdTable::default();
    exprs.insert(ExprId(0),Expr::BVar(0)).unwrap();
    exprs.insert(ExprId(1),Expr::BVar(1)).unwrap();
    exprs.insert(ExprId(2),Expr::Sort(LevelId(0))).unwrap();
    exprs.insert(ExprId(3),Expr::Const{name:NameId(10),levels:vec![]}).unwrap();
    exprs.insert(ExprId(4),Expr::Const{name:NameId(11),levels:vec![]}).unwrap();
    exprs.insert(ExprId(5),Expr::Const{name:NameId(12),levels:vec![]}).unwrap();
    exprs.insert(ExprId(6),Expr::Const{name:NameId(20),levels:vec![]}).unwrap();
    exprs.insert(ExprId(7),Expr::Const{name:NameId(21),levels:vec![]}).unwrap();
    for (i,body) in [(8,1),(9,0)] {
        let mut b=ExprId(body);
        for k in 0..3 { let id=ExprId(20+i*3+k);exprs.insert(id,Expr::Lam{domain:ExprId(2),body:b}).unwrap();b=id; }
        exprs.insert(ExprId(i),Expr::Lam{domain:ExprId(2),body:b}).unwrap();
    }
    // Rules bind motive and two minors (three lambdas).
    let rules=vec![RecursorRule{constructor:NameId(10),constructor_level_params:vec![],num_params:0,num_fields:0,rhs:ExprId(46)},RecursorRule{constructor:NameId(11),constructor_level_params:vec![],num_params:0,num_fields:0,rhs:ExprId(49)}];
    let mut term=ExprId(5);
    for (i,arg) in [2,6,7,0].into_iter().enumerate() {let id=ExprId(60+i as u64);exprs.insert(id,Expr::App{fun:term,arg:ExprId(arg)}).unwrap();term=id;}
    let mut definitions=HashMap::new();
    for i in 0..40 {exprs.insert(ExprId(100+i),Expr::Const{name:NameId(100+i),levels:vec![]}).unwrap();definitions.insert(NameId(100+i),DefinitionBody{value:ExprId(if i==39 {3}else{101+i}),level_params:vec![],preferred_for_reduction:true});}
    let levels=zero_levels();
    let build=|defs|Machine::new(AuthorityId(1),&exprs,&levels,defs).with_recursor_reductions(HashMap::from([(NameId(12),RecursorReduction{k:false,num_params:0,num_indices:0,level_params:vec![],rules:rules.clone()})]));
    let major=Closure::new(ExprId(100),EnvFrame::empty());
    let source=Closure::new(term,EnvFrame::empty().extend(major));
    let bool_machine=build(definitions.clone()).with_bool_primitives(Some(BoolPrimitives{false_ctor:NameId(10),true_ctor:NameId(11)}));
    assert!(matches!(bool_machine.expose(source.clone(),Transparency::Full,256).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(20),..},..}))),"certified Bool iota must follow the exact captured computed major");
    assert!(!matches!(bool_machine.expose(source.clone(),Transparency::Full,12).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(20),..},..}))));
    assert!(matches!(bool_machine.expose(Closure::new(term,EnvFrame::empty().extend_free(FreeId(0))),Transparency::Full,256).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(12),..},..}))));
    let machine=build(definitions.clone());
    let true_value=machine.expose(source.clone(),Transparency::Full,256);
    assert!(matches!(true_value.proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(20),..},..}))),"{true_value:?}");
    assert!(!matches!(machine.expose(source.clone(),Transparency::Full,12).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(20),..},..}))));
    let neutral=Closure::new(term,EnvFrame::empty().extend_free(FreeId(0)));
    assert!(matches!(machine.expose(neutral,Transparency::Full,256).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(12),..},..}))));
    definitions.get_mut(&NameId(139)).unwrap().value=ExprId(4);
    assert!(matches!(build(definitions).expose(source,Transparency::Full,256).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(21),..},..}))));
}

#[test]
fn multi_motive_nullary_selection_preserves_exact_major_and_surplus_arguments() {
    use metatron_kernel::machine::NullaryMinorReduction;
    let mut exprs=IdTable::default();
    for (i,e) in [
        (0,Expr::Sort(LevelId(0))),
        (1,Expr::Const{name:NameId(10),levels:vec![]}),
        (2,Expr::Const{name:NameId(11),levels:vec![]}),
        (3,Expr::Const{name:NameId(12),levels:vec![LevelId(0)]}),
        (4,Expr::Const{name:NameId(20),levels:vec![]}),
        (5,Expr::Const{name:NameId(21),levels:vec![]}),
        (6,Expr::Const{name:NameId(22),levels:vec![]}),
        (7,Expr::BVar(0)),
        (8,Expr::Const{name:NameId(12),levels:vec![]}),
    ] {exprs.insert(ExprId(i),e).unwrap();}
    let mut build=|head:u64,start:u64,args:&[u64]| {
        let mut term=ExprId(head);
        for (i,arg) in args.iter().enumerate() {let id=ExprId(start+i as u64);exprs.insert(id,Expr::App{fun:term,arg:ExprId(*arg)}).unwrap();term=id;}
        term
    };
    let term=build(3,20,&[0,0,4,5,6,7]);
    let short=build(3,30,&[0,0,4,5,6]);
    let extra=build(3,40,&[0,0,4,5,6,7,0]);
    let bad_levels=build(8,50,&[0,0,4,5,6,7]);
    let levels=zero_levels();
    let machine=Machine::new(AuthorityId(1),&exprs,&levels,HashMap::new()).with_nullary_minor_reductions(HashMap::from([(NameId(12),vec![NullaryMinorReduction{constructor:NameId(10),level_arity:1,prefix_len:5,minor_argument:3}])]));
    let correct=EnvFrame::empty().extend(Closure::new(ExprId(1),EnvFrame::empty()));
    let wrong=EnvFrame::empty().extend(Closure::new(ExprId(2),EnvFrame::empty()));
    for policy in [Transparency::Opaque,Transparency::Reducible,Transparency::Full] {
        assert!(matches!(machine.expose(Closure::new(term,correct.clone()),policy,128).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(21),..},spine})) if spine.is_empty()));
        assert!(matches!(machine.expose(Closure::new(extra,correct.clone()),policy,128).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(21),..},spine})) if spine.len()==1));
        for (expression,frame) in [(term,wrong.clone()),(short,correct.clone()),(bad_levels,correct.clone())] {
            assert!(matches!(machine.expose(Closure::new(expression,frame),policy,128).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(12),..},..}))));
        }
    }
}

#[test]
fn closed_nested_iota_checks_constructor_specialization_and_preserves_field_closures() {
    use metatron_kernel::machine::ClosedNestedMinorReduction;
    let mut expressions=IdTable::default();let mut levels=zero_levels();
    levels.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
    for (id,e) in [
        (0,Expr::Sort(LevelId(0))), (1,Expr::BVar(0)), (2,Expr::BVar(2)),
        (3,Expr::Const{name:NameId(12),levels:vec![LevelId(0)]}),
        (4,Expr::Const{name:NameId(10),levels:vec![LevelId(0)]}),
        (5,Expr::Const{name:NameId(10),levels:vec![LevelId(1)]}),
        (6,Expr::Const{name:NameId(30),levels:vec![]}),
        (7,Expr::Const{name:NameId(31),levels:vec![]}),
        (8,Expr::Const{name:NameId(20),levels:vec![]}),
        (9,Expr::Const{name:NameId(21),levels:vec![]}),
        (10,Expr::App{fun:ExprId(2),arg:ExprId(1)}),
    ] {expressions.insert(ExprId(id),e).unwrap();}
    let mut body=ExprId(10);
    for id in 20..26 {expressions.insert(ExprId(id),Expr::Lam{domain:ExprId(0),body}).unwrap();body=ExprId(id);}
    let rhs=body;
    let mut build=|head:u64,start:u64,args:&[u64]|{
        let mut term=ExprId(head);
        for (i,arg) in args.iter().enumerate() {let id=ExprId(start+i as u64);expressions.insert(id,Expr::App{fun:term,arg:ExprId(*arg)}).unwrap();term=id;}
        term
    };
    let correct=build(4,30,&[6,1]);let wrong_parameter=build(4,40,&[7,1]);let wrong_universe=build(5,50,&[6,1]);
    let call=build(3,60,&[0,0,8,9,8,correct.0]);
    let parameter_call=build(3,70,&[0,0,8,9,8,wrong_parameter.0]);
    let universe_call=build(3,80,&[0,0,8,9,8,wrong_universe.0]);
    let machine=Machine::new(AuthorityId(1),&expressions,&levels,HashMap::new()).with_closed_nested_minor_reductions(HashMap::from([(NameId(12),vec![ClosedNestedMinorReduction{constructor:NameId(10),constructor_levels:vec![LevelTerm::Zero],constructor_parameters:vec![(NameId(30),vec![])],num_fields:1,rhs,level_params:vec![NameId(40)],prefix_len:5,minor_argument:3}])]));
    let frame=EnvFrame::empty().extend(Closure::new(ExprId(8),EnvFrame::empty()));
    for policy in [Transparency::Opaque,Transparency::Reducible,Transparency::Full] {
        let result=machine.expose(Closure::new(call,frame.clone()),policy,256);
        let Some(Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(21),..},spine}))=result.proven_value() else{panic!("{result:?}");};
        assert_eq!(spine.len(),1);
        assert!(matches!(machine.expose(spine[0].clone(),policy,64).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(20),..},spine})) if spine.is_empty()));
        for expression in [parameter_call,universe_call] {
            assert!(matches!(machine.expose(Closure::new(expression,frame.clone()),policy,256).proven_value(),Some(Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(12),..},..}))));
        }
    }
}

#[test]
fn certified_successor_of_native_numeral_keeps_numeric_comparisons_exact() {
    use metatron_kernel::nat::BigNat;
    let mut exprs=IdTable::default();
    for (i,n) in [(0,10),(1,11),(2,12)] {exprs.insert(ExprId(i),Expr::Const{name:NameId(n),levels:vec![]}).unwrap();}
    for (i,n) in [(3,"55296"),(4,"4294967296"),(5,"4294967296")] {exprs.insert(ExprId(i),Expr::NatLit(BigNat::parse_decimal(n).unwrap())).unwrap();}
    exprs.insert(ExprId(6),Expr::BVar(0)).unwrap();
    for (i,f,a) in [(7,1,3),(8,1,5),(9,1,6),(10,2,7),(11,10,4),(12,2,8),(13,12,4)] {exprs.insert(ExprId(i),Expr::App{fun:ExprId(f),arg:ExprId(a)}).unwrap();}
    let levels=zero_levels();
    let nat=NatPrimitives{type_name:NameId(20),type_expr:ExprId(0),zero:NameId(10),succ:NameId(11),recursor:NameId(21),add:None,mul:None,pow:None,sub:None,pred:None,virtual_bvar_zero:Some(ExprId(6)),ble:Some(NameId(12)),beq:None};
    let machine=Machine::new(AuthorityId(51),&exprs,&levels,HashMap::new()).with_nat_primitives(Some(nat)).with_bool_primitives(Some(BoolPrimitives{true_ctor:NameId(30),false_ctor:NameId(31)}));
    for transparency in [Transparency::Opaque,Transparency::Reducible,Transparency::Full] {
        let success=machine.expose(Closure::new(ExprId(11),EnvFrame::empty()),transparency,128);
        assert!(matches!(success.proven_value(),Some(Value::Neutral(n)) if n.head==NeutralHead::Const{name:NameId(30),levels:vec![]}));
        let failure=machine.expose(Closure::new(ExprId(13),EnvFrame::empty()),transparency,128);
        assert!(matches!(failure.proven_value(),Some(Value::Neutral(n)) if n.head==NeutralHead::Const{name:NameId(31),levels:vec![]}));
        let neutral=machine.expose(Closure::new(ExprId(9),EnvFrame::empty().extend_free(FreeId(99))),transparency,128);
        assert!(matches!(neutral.proven_value(),Some(Value::Neutral(n)) if n.head==NeutralHead::Const{name:NameId(11),levels:vec![]} && n.spine.len()==1));
    }
    let uncertified=Machine::new(AuthorityId(52),&exprs,&levels,HashMap::new()).expose(Closure::new(ExprId(7),EnvFrame::empty()),Transparency::Full,128);
    assert!(matches!(uncertified.proven_value(),Some(Value::Neutral(_))));
}

#[test]
fn native_power_computes_the_exact_uint32_carrier_bound() {
    use metatron_kernel::nat::BigNat;
    let mut exprs=IdTable::default();
    exprs.insert(ExprId(0),Expr::Const{name:NameId(40),levels:vec![]}).unwrap();
    for (i,n) in [(1,"2"),(2,"32")] {exprs.insert(ExprId(i),Expr::NatLit(BigNat::parse_decimal(n).unwrap())).unwrap();}
    exprs.insert(ExprId(3),Expr::App{fun:ExprId(0),arg:ExprId(1)}).unwrap();
    exprs.insert(ExprId(4),Expr::App{fun:ExprId(3),arg:ExprId(2)}).unwrap();
    let levels=zero_levels();
    let nat=NatPrimitives{type_name:NameId(20),type_expr:ExprId(0),zero:NameId(10),succ:NameId(11),recursor:NameId(21),add:None,mul:None,pow:Some(NameId(40)),sub:None,pred:None,virtual_bvar_zero:None,ble:None,beq:None};
    let machine=Machine::new(AuthorityId(53),&exprs,&levels,HashMap::new()).with_nat_primitives(Some(nat));
    let result=machine.expose(Closure::new(ExprId(4),EnvFrame::empty()),Transparency::Opaque,128);
    assert_eq!(result.proven_value(),Some(&Value::NatLit(BigNat::parse_decimal("4294967296").unwrap())));
}
