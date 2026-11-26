use std::collections::HashMap;

use metatron_kernel::environment::{ConstantDecl, Environment};
use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::level::LevelTerm;
use metatron_kernel::machine::{ProjectionFieldType, ProjectionSpec};
use metatron_kernel::syntax::{Expr, Level};
use metatron_kernel::typecheck::{TypeChecker, TypeValue};
use metatron_kernel::value::{Closure, EnvFrame};

struct Fixture {
    expressions: IdTable<ExprId, Expr>,
    levels: IdTable<LevelId, Level>,
    environment: Environment,
}

#[test]
fn inferred_dependent_pi_compares_its_explicit_binder() {
    use metatron_kernel::value::FreeId;
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    expressions.insert(ExprId(0), Expr::BVar(0)).unwrap();
    let environment = Environment::empty();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let pi = |binder, body_free| TypeValue::Pi {
        domain: Box::new(TypeValue::Sort(LevelTerm::Zero)),
        body: Box::new(TypeValue::Term(Closure::new(
            ExprId(0), EnvFrame::empty().extend_free(FreeId(body_free)),
        ))),
        binder: FreeId(binder),
    };
    assert!(checker.convert(&pi(1, 1), &pi(2, 2), 256).is_proven(),
        "dependent Pi bodies must be opened with the same fresh binder");
    assert!(!checker.convert(&pi(1, 1), &pi(2, 3), 256).is_proven(),
        "an unrelated captured local cannot be renamed as the Pi binder");
    assert!(!checker.convert(&pi(1, 0), &pi(2, 2), 256).is_proven(),
        "reopening must not capture an existing target local");
    let nested = |outer, inner, body_free| TypeValue::Pi {
        domain: Box::new(TypeValue::Sort(LevelTerm::Zero)),
        body: Box::new(pi(inner, body_free)),
        binder: FreeId(outer),
    };
    assert!(!checker.convert(&nested(2, 0, 2), &nested(3, 1, 1), 1024).is_proven(),
        "an unused inner binder must not capture an outer reference during reopening");
}

#[test]
fn neutral_projection_compares_captured_receiver_arguments() {
    use metatron_kernel::value::FreeId;
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    expressions.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    expressions.insert(ExprId(1), Expr::BVar(0)).unwrap();
    expressions.insert(ExprId(2), Expr::BVar(1)).unwrap();
    expressions.insert(ExprId(3), Expr::App { fun: ExprId(2), arg: ExprId(1) }).unwrap();
    expressions.insert(ExprId(4), Expr::Proj { type_name: NameId(1), index: 0, structure: ExprId(3) }).unwrap();
    expressions.insert(ExprId(5), Expr::Proj { type_name: NameId(1), index: 1, structure: ExprId(3) }).unwrap();
    let environment = Environment::empty()
        .extend(NameId(1), ConstantDecl::axiom(Vec::new(), ExprId(0))).unwrap()
        .extend(NameId(2), ConstantDecl::axiom(Vec::new(), ExprId(0))).unwrap()
        .install_projection_spec(NameId(1), ProjectionSpec {
            constructor: NameId(2), num_params: 0,
            field_types: vec![ProjectionFieldType::Derived(ExprId(0)); 2],
            eta_expandable: false,
        }).unwrap();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let capture = |argument| EnvFrame::empty().extend_free(FreeId(0)).extend_free(FreeId(argument));
    let left = TypeValue::Term(Closure::new(ExprId(4), capture(1)));
    let right = TypeValue::Term(Closure::new(ExprId(4), capture(1)));
    assert!(checker.convert(&left, &right, 256).is_proven(),
        "same projection of equal neutral receiver applications must be convertible across capture frames");
    let different_argument = TypeValue::Term(Closure::new(ExprId(4), capture(2)));
    assert!(!checker.convert(&left, &different_argument, 256).is_proven());
    let different_field = TypeValue::Term(Closure::new(ExprId(5), capture(1)));
    assert!(!checker.convert(&left, &different_field, 256).is_proven());
}

#[test]
fn application_congruence_checks_universe_arguments() {
    let mut fixture = Fixture::conversion();
    fixture.expressions.insert(ExprId(20), Expr::Sort(LevelId(2))).unwrap();
    fixture.expressions.insert(ExprId(21), Expr::Pi {
        domain: ExprId(7), body: ExprId(20),
    }).unwrap();
    fixture.environment = fixture.environment.extend(
        NameId(31), ConstantDecl::axiom(vec![NameId(10)], ExprId(21)),
    ).unwrap();
    for (head, app, level) in [(22, 24, 0), (23, 25, 1)] {
        fixture.expressions.insert(ExprId(head), Expr::Const {
            name: NameId(31), levels: vec![LevelId(level)],
        }).unwrap();
        fixture.expressions.insert(ExprId(app), Expr::App {
            fun: ExprId(head), arg: ExprId(0),
        }).unwrap();
    }
    assert!(!fixture.checker().convert(&Fixture::term(24), &Fixture::term(25), 128).is_proven());
}

#[test]
fn matching_definition_applications_preserve_unforced_arguments() {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    let mut expressions = IdTable::default();
    expressions
        .insert(ExprId(0), Expr::Sort(LevelId(0)))
        .unwrap();
    expressions.insert(ExprId(1), Expr::BVar(0)).unwrap();
    expressions
        .insert(
            ExprId(2),
            Expr::Lam {
                domain: ExprId(0),
                body: ExprId(1),
            },
        )
        .unwrap();
    expressions
        .insert(
            ExprId(3),
            Expr::Const {
                name: NameId(1),
                levels: vec![],
            },
        )
        .unwrap();
    expressions
        .insert(
            ExprId(4),
            Expr::Const {
                name: NameId(2),
                levels: vec![],
            },
        )
        .unwrap();
    expressions
        .insert(
            ExprId(5),
            Expr::App {
                fun: ExprId(3),
                arg: ExprId(4),
            },
        )
        .unwrap();
    expressions
        .insert(
            ExprId(6),
            Expr::App {
                fun: ExprId(3),
                arg: ExprId(4),
            },
        )
        .unwrap();
    let environment = Environment::empty()
        .extend(
            NameId(1),
            ConstantDecl::definition(vec![], ExprId(0), ExprId(2), true),
        )
        .unwrap()
        .extend(
            NameId(2),
            ConstantDecl::definition(vec![], ExprId(0), ExprId(4), true),
        )
        .unwrap();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    assert!(
        checker
            .convert(&Fixture::term(5), &Fixture::term(6), 64)
            .is_proven()
    );
}

#[test]
fn failed_definition_argument_congruence_falls_back_to_its_body() {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    let mut expressions = IdTable::default();
    expressions
        .insert(ExprId(0), Expr::Sort(LevelId(0)))
        .unwrap();
    expressions
        .insert(
            ExprId(1),
            Expr::Lam {
                domain: ExprId(0),
                body: ExprId(0),
            },
        )
        .unwrap();
    for (id, name) in [(2, 1), (3, 2), (4, 3)] {
        expressions
            .insert(
                ExprId(id),
                Expr::Const {
                    name: NameId(name),
                    levels: vec![],
                },
            )
            .unwrap();
    }
    expressions
        .insert(
            ExprId(5),
            Expr::App {
                fun: ExprId(2),
                arg: ExprId(3),
            },
        )
        .unwrap();
    expressions
        .insert(
            ExprId(6),
            Expr::App {
                fun: ExprId(2),
                arg: ExprId(4),
            },
        )
        .unwrap();
    let environment = Environment::empty()
        .extend(
            NameId(1),
            ConstantDecl::definition(vec![], ExprId(0), ExprId(1), false),
        )
        .unwrap()
        .extend(
            NameId(2),
            ConstantDecl::definition(vec![], ExprId(0), ExprId(3), true),
        )
        .unwrap()
        .extend(
            NameId(3),
            ConstantDecl::definition(vec![], ExprId(0), ExprId(4), true),
        )
        .unwrap();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    assert!(
        checker
            .convert(&Fixture::term(5), &Fixture::term(6), 64)
            .is_proven()
    );
}

impl Fixture {
    fn conversion() -> Self {
        let mut levels = IdTable::default();
        levels.insert(LevelId(0), Level::Zero).unwrap();
        levels.insert(LevelId(1), Level::Succ(LevelId(0))).unwrap();
        levels.insert(LevelId(2), Level::Param(NameId(10))).unwrap();
        levels.insert(LevelId(3), Level::Param(NameId(11))).unwrap();
        levels
            .insert(LevelId(4), Level::IMax(LevelId(2), LevelId(3)))
            .unwrap();
        levels
            .insert(LevelId(5), Level::Max(LevelId(2), LevelId(3)))
            .unwrap();

        let mut expressions = IdTable::default();
        expressions
            .insert(ExprId(0), Expr::Sort(LevelId(0)))
            .unwrap();
        expressions.insert(ExprId(1), Expr::BVar(0)).unwrap();
        expressions
            .insert(
                ExprId(2),
                Expr::Lam {
                    domain: ExprId(0),
                    body: ExprId(1),
                },
            )
            .unwrap();
        expressions
            .insert(
                ExprId(3),
                Expr::App {
                    fun: ExprId(2),
                    arg: ExprId(0),
                },
            )
            .unwrap();
        expressions
            .insert(
                ExprId(4),
                Expr::Let {
                    ty: ExprId(0),
                    value: ExprId(0),
                    body: ExprId(1),
                },
            )
            .unwrap();
        expressions
            .insert(
                ExprId(5),
                Expr::Pi {
                    domain: ExprId(0),
                    body: ExprId(0),
                },
            )
            .unwrap();
        expressions
            .insert(
                ExprId(6),
                Expr::Pi {
                    domain: ExprId(0),
                    body: ExprId(0),
                },
            )
            .unwrap();
        expressions
            .insert(ExprId(7), Expr::Sort(LevelId(1)))
            .unwrap();
        expressions
            .insert(
                ExprId(8),
                Expr::Const {
                    name: NameId(2),
                    levels: Vec::new(),
                },
            )
            .unwrap();
        expressions
            .insert(ExprId(9), Expr::Sort(LevelId(4)))
            .unwrap();
        expressions
            .insert(ExprId(10), Expr::Sort(LevelId(5)))
            .unwrap();

        let environment = Environment::empty()
            .extend(
                NameId(2),
                ConstantDecl::definition(Vec::new(), ExprId(7), ExprId(0), true),
            )
            .unwrap();
        Self {
            expressions,
            levels,
            environment,
        }
    }

    fn checker(&self) -> TypeChecker<'_> {
        TypeChecker::new(&self.expressions, &self.levels, &self.environment)
    }

    fn term(id: u64) -> TypeValue {
        TypeValue::Term(Closure::new(ExprId(id), EnvFrame::empty()))
    }
}

#[test]
fn syntactic_identity_is_proven_before_reduction() {
    let fixture = Fixture::conversion();
    assert!(
        fixture
            .checker()
            .convert(&Fixture::term(5), &Fixture::term(5), 1)
            .is_proven()
    );
}

#[test]
fn beta_zeta_and_reducible_delta_are_convertible() {
    let fixture = Fixture::conversion();
    let checker = fixture.checker();
    assert!(
        checker
            .convert(&Fixture::term(3), &Fixture::term(0), 64)
            .is_proven()
    );
    assert!(
        checker
            .convert(&Fixture::term(4), &Fixture::term(0), 64)
            .is_proven()
    );
    assert!(
        checker
            .convert(&Fixture::term(8), &Fixture::term(0), 64)
            .is_proven()
    );
}

#[test]
fn rigid_pi_values_compare_relationally() {
    let fixture = Fixture::conversion();
    assert!(
        fixture
            .checker()
            .convert(&Fixture::term(5), &Fixture::term(6), 64)
            .is_proven()
    );
}

#[test]
fn unequal_supported_sorts_are_refuted() {
    let fixture = Fixture::conversion();
    assert!(
        fixture
            .checker()
            .convert(&Fixture::term(0), &Fixture::term(7), 64)
            .is_refuted()
    );
}

#[test]
fn unresolved_imax_comparison_preserves_unknown() {
    let fixture = Fixture::conversion();
    let substitution = HashMap::from([
        (NameId(10), LevelTerm::param("u")),
        (NameId(11), LevelTerm::param("v")),
    ]);
    let checker = TypeChecker::with_level_substitution(
        &fixture.expressions,
        &fixture.levels,
        &fixture.environment,
        substitution,
    );
    assert!(
        checker
            .convert(&Fixture::term(9), &Fixture::term(10), 64)
            .is_unknown()
    );
}

#[test]
fn conversion_budget_exhaustion_preserves_unknown() {
    let fixture = Fixture::conversion();
    assert!(
        fixture
            .checker()
            .convert(&Fixture::term(5), &Fixture::term(6), 0)
            .is_unknown()
    );
}

#[test]
fn matching_projections_compare_only_the_selected_fields() {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();

    let mut expressions = IdTable::default();
    expressions.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    for (id, name) in [(1, 2), (5, 3), (6, 4), (9, 5), (10, 6)] {
        expressions
            .insert(
                ExprId(id),
                Expr::Const {
                    name: NameId(name),
                    levels: Vec::new(),
                },
            )
            .unwrap();
    }
    expressions
        .insert(ExprId(2), Expr::App { fun: ExprId(1), arg: ExprId(0) })
        .unwrap();
    expressions
        .insert(ExprId(3), Expr::App { fun: ExprId(2), arg: ExprId(9) })
        .unwrap();
    expressions
        .insert(ExprId(4), Expr::App { fun: ExprId(2), arg: ExprId(10) })
        .unwrap();
    expressions
        .insert(
            ExprId(7),
            Expr::Proj { type_name: NameId(1), index: 0, structure: ExprId(5) },
        )
        .unwrap();
    expressions
        .insert(
            ExprId(8),
            Expr::Proj { type_name: NameId(1), index: 0, structure: ExprId(6) },
        )
        .unwrap();

    let mut environment = Environment::empty();
    for name in [NameId(1), NameId(2)] {
        environment = environment
            .extend(name, ConstantDecl::axiom(Vec::new(), ExprId(0)))
            .unwrap();
    }
    environment = environment
        .extend(NameId(3), ConstantDecl::definition(Vec::new(), ExprId(0), ExprId(3), false))
        .unwrap()
        .extend(NameId(4), ConstantDecl::definition(Vec::new(), ExprId(0), ExprId(4), false))
        .unwrap()
        .extend(NameId(5), ConstantDecl::definition(Vec::new(), ExprId(0), ExprId(9), true))
        .unwrap()
        .extend(NameId(6), ConstantDecl::definition(Vec::new(), ExprId(0), ExprId(10), true))
        .unwrap()
        .install_projection_spec(
            NameId(1),
            ProjectionSpec {
                constructor: NameId(2),
                num_params: 0,
                field_types: vec![
                    ProjectionFieldType::Derived(ExprId(0)),
                    ProjectionFieldType::Derived(ExprId(0)),
                ],
                eta_expandable: false,
            },
        )
        .unwrap();

    let checker = TypeChecker::new(&expressions, &levels, &environment);
    assert!(checker.convert(&Fixture::term(7), &Fixture::term(8), 64).is_proven());
}

#[test]
fn projection_congruence_failure_does_not_force_unused_structure_arguments() {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();

    let mut expressions = IdTable::default();
    expressions.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    expressions
        .insert(ExprId(1), Expr::Const { name: NameId(2), levels: Vec::new() })
        .unwrap();
    expressions
        .insert(ExprId(2), Expr::App { fun: ExprId(1), arg: ExprId(0) })
        .unwrap();
    expressions.insert(ExprId(3), Expr::BVar(0)).unwrap();
    expressions
        .insert(ExprId(4), Expr::App { fun: ExprId(2), arg: ExprId(3) })
        .unwrap();
    expressions
        .insert(ExprId(5), Expr::Lam { domain: ExprId(0), body: ExprId(4) })
        .unwrap();
    for (id, name) in [(6, 3), (7, 4), (8, 5)] {
        expressions
            .insert(ExprId(id), Expr::Const { name: NameId(name), levels: Vec::new() })
            .unwrap();
    }
    expressions
        .insert(ExprId(9), Expr::App { fun: ExprId(6), arg: ExprId(7) })
        .unwrap();
    expressions
        .insert(ExprId(10), Expr::App { fun: ExprId(6), arg: ExprId(8) })
        .unwrap();
    expressions
        .insert(
            ExprId(11),
            Expr::Proj { type_name: NameId(1), index: 0, structure: ExprId(9) },
        )
        .unwrap();
    expressions
        .insert(
            ExprId(12),
            Expr::Proj { type_name: NameId(1), index: 0, structure: ExprId(10) },
        )
        .unwrap();

    let environment = Environment::empty()
        .extend(NameId(1), ConstantDecl::axiom(Vec::new(), ExprId(0)))
        .unwrap()
        .extend(NameId(2), ConstantDecl::axiom(Vec::new(), ExprId(0)))
        .unwrap()
        .extend(NameId(3), ConstantDecl::definition(Vec::new(), ExprId(0), ExprId(5), true))
        .unwrap()
        .extend(NameId(4), ConstantDecl::definition(Vec::new(), ExprId(0), ExprId(7), true))
        .unwrap()
        .extend(NameId(5), ConstantDecl::definition(Vec::new(), ExprId(0), ExprId(8), true))
        .unwrap()
        .install_projection_spec(
            NameId(1),
            ProjectionSpec {
                constructor: NameId(2),
                num_params: 0,
                field_types: vec![
                    ProjectionFieldType::Derived(ExprId(0)),
                    ProjectionFieldType::Derived(ExprId(0)),
                ],
                eta_expandable: false,
            },
        )
        .unwrap();
    let checker = TypeChecker::new(&expressions, &levels, &environment);

    assert!(checker.convert(&Fixture::term(11), &Fixture::term(12), 256).is_proven());
}

#[test]
fn stuck_projection_preserves_its_application_spine() {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    levels.insert(LevelId(1), Level::Succ(LevelId(0))).unwrap();

    let mut expressions = IdTable::default();
    expressions.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    expressions.insert(ExprId(1), Expr::Sort(LevelId(1))).unwrap();
    expressions
        .insert(ExprId(2), Expr::Const { name: NameId(2), levels: Vec::new() })
        .unwrap();
    expressions.insert(ExprId(3), Expr::BVar(0)).unwrap();
    expressions
        .insert(ExprId(4), Expr::Lam { domain: ExprId(1), body: ExprId(3) })
        .unwrap();
    expressions
        .insert(ExprId(5), Expr::App { fun: ExprId(2), arg: ExprId(4) })
        .unwrap();
    expressions
        .insert(ExprId(6), Expr::Const { name: NameId(3), levels: Vec::new() })
        .unwrap();
    expressions
        .insert(
            ExprId(7),
            Expr::Proj { type_name: NameId(1), index: 0, structure: ExprId(6) },
        )
        .unwrap();
    expressions
        .insert(ExprId(8), Expr::App { fun: ExprId(7), arg: ExprId(0) })
        .unwrap();
    expressions
        .insert(ExprId(9), Expr::App { fun: ExprId(7), arg: ExprId(1) })
        .unwrap();
    expressions
        .insert(ExprId(10), Expr::App { fun: ExprId(2), arg: ExprId(0) })
        .unwrap();
    expressions
        .insert(ExprId(11), Expr::Const { name: NameId(4), levels: Vec::new() })
        .unwrap();
    expressions
        .insert(
            ExprId(12),
            Expr::Proj { type_name: NameId(1), index: 0, structure: ExprId(11) },
        )
        .unwrap();

    let environment = Environment::empty()
        .extend(NameId(1), ConstantDecl::axiom(Vec::new(), ExprId(0)))
        .unwrap()
        .extend(NameId(2), ConstantDecl::axiom(Vec::new(), ExprId(0)))
        .unwrap()
        .extend(NameId(3), ConstantDecl::definition(Vec::new(), ExprId(0), ExprId(5), false))
        .unwrap()
        .extend(NameId(4), ConstantDecl::definition(Vec::new(), ExprId(0), ExprId(10), false))
        .unwrap()
        .install_projection_spec(
            NameId(1),
            ProjectionSpec {
                constructor: NameId(2),
                num_params: 0,
                field_types: vec![ProjectionFieldType::Derived(ExprId(0))],
                eta_expandable: false,
            },
        )
        .unwrap();
    let checker = TypeChecker::new(&expressions, &levels, &environment);

    assert!(checker.convert(&Fixture::term(8), &Fixture::term(9), 64).is_refuted());
    assert!(checker.convert(&Fixture::term(8), &Fixture::term(12), 64).is_proven());
}

fn captured_field_enum_recursor_fixture() -> (Fixture, ExprId, ExprId, ExprId) {
    use metatron_kernel::machine::{RecursorReduction, RecursorRule};
    use metatron_kernel::syntax::Declaration;
    use serde_json::{Value, json};
    use std::io::Cursor;
    // Independently admit the complete source contract before reconstructing
    // its runtime environment. Both constructors carry exactly one Nat.
    let mut rows: Vec<Value> = include_str!("fixtures/good-closed-field-enum.ndjson")
        .lines().map(|line| serde_json::from_str(line).unwrap()).collect();
    for row in &mut rows {
        match row["ie"].as_u64() {
            Some(45) => row["bvar"] = json!(2),
            Some(49) => row["app"]["arg"] = json!(48),
            Some(51) => row["app"]["arg"] = json!(49),
            Some(53) => row["forallE"]["body"] = json!(51),
            Some(73) => row["app"]["fn"] = json!(70),
            Some(75) => row["lam"]["body"] = json!(73),
            _ => {}
        }
        if let Some(block) = row.get_mut("inductive") {
            if block["types"][0]["name"] == json!(12) {
                block["ctors"][1]["numFields"] = json!(1);
                block["ctors"][1]["type"] = json!(68);
                block["recs"][0]["rules"][1]["nfields"] = json!(1);
            }
        }
    }
    let source = rows.iter().map(|row| format!("{row}\n")).collect::<String>();
    assert_eq!(metatron_kernel::run(Cursor::new(&source)), metatron_kernel::verdict::Verdict::Accept);
    let export = metatron_kernel::parser::parse(Cursor::new(source)).unwrap().resolve().unwrap();
    let mut environment = Environment::empty();
    for declaration in &export.declarations {
        let Declaration::Inductive(block) = declaration else { continue };
        for ty in &block.types {
            environment = environment.extend(ty.name, ConstantDecl::inductive_type(ty.level_params.clone(), ty.ty)).unwrap();
        }
        for ctor in &block.constructors {
            environment = environment.extend(ctor.name, ConstantDecl::constructor(ctor.level_params.clone(), ctor.ty)).unwrap();
        }
        for rec in &block.recursors {
            environment = environment.extend(rec.name, ConstantDecl::recursor(rec.level_params.clone(), rec.ty)).unwrap();
            let rules = rec.rules.iter().map(|rule| {
                let ctor = block.constructors.iter().find(|ctor| ctor.name == rule.constructor).unwrap();
                RecursorRule { constructor: ctor.name, constructor_level_params: ctor.level_params.clone(),
                    num_params: ctor.num_params as usize, num_fields: ctor.num_fields as usize, rhs: rule.rhs }
            }).collect();
            environment = environment.install_recursor_reduction(rec.name, RecursorReduction {
                k: rec.k, num_params: rec.num_params as usize, num_indices: rec.num_indices as usize,
                level_params: rec.level_params.clone(), rules,
            }).unwrap();
        }
    }
    let mut expressions = export.exprs;
    let mut next = 100;
    let mut add = |node| { let id = ExprId(next); next += 1; expressions.insert(id, node).unwrap(); id };
    let zero = add(Expr::Const { name: NameId(2), levels: vec![] });
    let ctor = add(Expr::Const { name: NameId(13), levels: vec![] });
    let major = add(Expr::App { fun: ctor, arg: zero });
    let nat = ExprId(37);
    let function_ty = add(Expr::Pi { domain: nat, body: nat });
    let function = add(Expr::Const { name: NameId(1000), levels: vec![] });
    let other_function = add(Expr::Const { name: NameId(1001), levels: vec![] });
    let bound = add(Expr::BVar(0));
    let minor_body = add(Expr::App { fun: function, arg: bound });
    let minor = add(Expr::Lam { domain: nat, body: minor_body });
    let other_body = add(Expr::App { fun: other_function, arg: bound });
    let other_minor = add(Expr::Lam { domain: nat, body: other_body });
    let motive = add(Expr::Lam { domain: ExprId(36), body: nat });
    // The source major is an actual constructor, hidden behind exact let and
    // lambda captures beyond the ordinary 128-step major exposure allowance.
    let mut hidden = major;
    for _ in 0..140 { hidden = add(Expr::Let { ty: ExprId(36), value: major, body: hidden }); }
    let wrapped = add(Expr::Lam { domain: ExprId(36), body: bound });
    hidden = add(Expr::App { fun: wrapped, arg: hidden });
    let mut application = add(Expr::Const { name: NameId(15), levels: vec![LevelId(1)] });
    for argument in [motive, minor, other_minor, hidden] { application = add(Expr::App { fun: application, arg: argument }); }
    let expected = add(Expr::App { fun: function, arg: zero });
    let wrong = add(Expr::App { fun: other_function, arg: zero });
    drop(add);
    for name in [NameId(1000), NameId(1001)] {
        environment = environment.extend(name, ConstantDecl::axiom(vec![], function_ty)).unwrap();
    }
    (Fixture { expressions, levels: export.levels, environment }, application, expected, wrong)
}

#[test]
fn registered_field_recursor_replays_its_actual_captured_constructor() {
    let (fixture, actual, expected, _) = captured_field_enum_recursor_fixture();
    let checker = fixture.checker().with_delta_policy(metatron_kernel::convert::DeltaPolicy::GuardedSemanticFallback);
    assert!(checker.convert(&Fixture::term(actual.0), &Fixture::term(expected.0), 2048).is_proven(),
        "source-certified four-argument recursor must select its actual constructor rule");
}

#[test]
fn registered_field_recursor_does_not_select_the_opponents_minor_or_ignore_budget() {
    let (fixture, actual, expected, wrong) = captured_field_enum_recursor_fixture();
    let checker = fixture.checker().with_delta_policy(metatron_kernel::convert::DeltaPolicy::GuardedSemanticFallback);
    // Exercise a genuinely cold low-budget attempt before another judgment
    // can retain the actual constructor/RHS result for legitimate reuse.
    assert!(!checker.convert(&Fixture::term(actual.0), &Fixture::term(expected.0), 32).is_proven());
    assert!(!checker.convert(&Fixture::term(actual.0), &Fixture::term(wrong.0), 2048).is_proven());
}

#[test]
fn registered_field_recursor_requires_exact_universes_major_and_arity() {
    for variant in 0..3 {
        let (mut fixture, actual, expected, _) = captured_field_enum_recursor_fixture();
        let mut arguments = Vec::new();
        let mut head = actual;
        while let Some(Expr::App { fun, arg }) = fixture.expressions.get(head) {
            arguments.push(*arg);
            head = *fun;
        }
        arguments.reverse();
        assert_eq!(arguments.len(), 4);
        let next = fixture.expressions.iter_raw().map(|(id, _)| id).max().unwrap() + 1;
        let mut next = next;
        let mut add = |node| { let id = ExprId(next); next += 1; fixture.expressions.insert(id, node).unwrap(); id };
        let levels = if variant == 0 { vec![] } else { vec![LevelId(1)] };
        let mut mutant = add(Expr::Const { name: NameId(15), levels });
        if variant == 1 { arguments[3] = ExprId(6); } // Nat.zero is not a Branch constructor.
        if variant == 2 { arguments.pop(); } // Missing actual major.
        for argument in arguments { mutant = add(Expr::App { fun: mutant, arg: argument }); }
        drop(add);
        let checker = fixture.checker().with_delta_policy(metatron_kernel::convert::DeltaPolicy::GuardedSemanticFallback);
        assert!(!checker.convert(&Fixture::term(mutant.0), &Fixture::term(expected.0), 2048).is_proven(),
            "wrong universes/foreign major/short arity variant {variant} cannot license source replay");
    }
}

#[test]
fn opening_source_binders_does_not_capture_an_actual_ambient_free_at_fresh_depth() {
    use metatron_kernel::value::FreeId;
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    expressions.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    expressions.insert(ExprId(1), Expr::BVar(0)).unwrap();
    expressions.insert(ExprId(2), Expr::BVar(1)).unwrap();
    for (id, body, lambda) in [(3, 1, true), (4, 2, true), (5, 1, false), (6, 2, false)] {
        let node = if lambda { Expr::Lam { domain: ExprId(0), body: ExprId(body) } }
            else { Expr::Pi { domain: ExprId(0), body: ExprId(body) } };
        expressions.insert(ExprId(id), node).unwrap();
    }
    let environment = Environment::empty();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let source = |id| TypeValue::Term(Closure::new(ExprId(id),
        EnvFrame::empty().extend_free(FreeId(0))));
    // Γ is empty, so opening uses FreeId(0). The actual ambient capture is
    // already FreeId(0), but denotes a different source variable.
    assert!(!checker.convert(&source(3), &source(4), 256).is_proven(),
        "lambda bound variable must not become its actual ambient capture");
    assert!(!checker.convert(&source(5), &source(6), 256).is_proven(),
        "Pi bound variable must not become its actual ambient capture");
    assert!(checker.convert(&source(3), &source(3), 256).is_proven(),
        "an unused ambient FreeId(0) capture is irrelevant to two identities");
    assert!(checker.convert(&source(5), &source(5), 256).is_proven(),
        "an unused ambient capture is irrelevant to identical Pi syntax");
}

#[test]
fn evaluated_eta_does_not_confuse_a_captured_local_with_its_bound_argument() {
    use metatron_kernel::value::FreeId;
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    for (id, node) in [
        (0, Expr::Sort(LevelId(0))),
        (1, Expr::BVar(0)), (2, Expr::BVar(1)), (3, Expr::BVar(2)),
        (4, Expr::Pi { domain: ExprId(0), body: ExprId(0) }),
        (5, Expr::Lam { domain: ExprId(4), body: ExprId(1) }),
        (6, Expr::App { fun: ExprId(2), arg: ExprId(3) }),
        (7, Expr::Lam { domain: ExprId(0), body: ExprId(6) }),
        (8, Expr::Lam { domain: ExprId(4), body: ExprId(7) }),
    ] { expressions.insert(ExprId(id), node).unwrap(); }
    let environment = Environment::empty();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let source = |id| TypeValue::Term(Closure::new(ExprId(id),
        EnvFrame::empty().extend_free(FreeId(1))));
    // After opening f, Γ has depth1. The right body applies f to the actual
    // ambient FreeId(1), not to its syntactically bound x.
    assert!(!checker.convert(&source(5), &source(8), 512).is_proven(),
        "semantic eta must prove the argument is newly bound, not a colliding ambient capture");
}

#[test]
fn exposing_a_source_pi_as_a_fixed_type_preserves_ambient_binder_distinction() {
    use metatron_kernel::value::FreeId;
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    expressions.insert(ExprId(0), Expr::Sort(LevelId(0))).unwrap();
    expressions.insert(ExprId(1), Expr::BVar(0)).unwrap();
    expressions.insert(ExprId(2), Expr::BVar(1)).unwrap();
    expressions.insert(ExprId(3), Expr::Pi { domain: ExprId(0), body: ExprId(2) }).unwrap();
    let environment = Environment::empty();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let fixed = TypeValue::Pi {
        domain: Box::new(TypeValue::Term(Closure::new(ExprId(0), EnvFrame::empty()))),
        body: Box::new(TypeValue::Term(Closure::new(ExprId(1), EnvFrame::empty().extend_free(FreeId(0))))),
        binder: FreeId(0),
    };
    let source = TypeValue::Term(Closure::new(ExprId(3), EnvFrame::empty().extend_free(FreeId(0))));
    assert!(!checker.convert(&fixed, &source, 256).is_proven(),
        "value_as_type must not reclassify an actual ambient capture as its Pi binder");
}

#[test]
fn legacy_expected_lambda_checking_does_not_capture_an_unchecked_expected_pi() {
    use metatron_kernel::value::FreeId;
    if std::env::var_os("NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA").is_none() { return; }
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    levels.insert(LevelId(1), Level::Succ(LevelId(0))).unwrap();
    for (id, node) in [
        (0, Expr::Sort(LevelId(1))),
        (1, Expr::BVar(0)), (2, Expr::BVar(1)), (3, Expr::BVar(2)),
        (4, Expr::Lam { domain: ExprId(1), body: ExprId(1) }),
        (5, Expr::Lam { domain: ExprId(0), body: ExprId(4) }),
        (6, Expr::Pi { domain: ExprId(2), body: ExprId(3) }),
        (7, Expr::Pi { domain: ExprId(0), body: ExprId(6) }),
    ] { expressions.insert(ExprId(id), node).unwrap(); }
    let environment = Environment::empty();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let expected = TypeValue::Term(Closure::new(ExprId(7), EnvFrame::empty().extend_free(FreeId(0))));
    // The source value is λA:Type.λx:A.x. The unchecked expected type's
    // inner domain/codomain reference ambient0, not the outer A binder.
    assert!(!checker.check(ExprId(5), &expected, 2048).is_proven(),
        "legacy ordinary-UNKNOWN fallback must preserve expected Pi captures too");
}

#[test]
fn source_binder_freshness_follows_aliases_and_borrowed_neutral_spines() {
    use metatron_kernel::value::{FreeId, Neutral, NeutralHead};
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    for (id, node) in [
        (0, Expr::Sort(LevelId(0))), (1, Expr::BVar(0)), (2, Expr::BVar(1)),
        (3, Expr::Lam { domain: ExprId(0), body: ExprId(1) }),
        (4, Expr::Lam { domain: ExprId(0), body: ExprId(2) }),
    ] { expressions.insert(ExprId(id), node).unwrap(); }
    let environment = Environment::empty();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let mut aliases = EnvFrame::empty().extend_free(FreeId(0));
    for _ in 0..24 { aliases = EnvFrame::empty().extend(Closure::new(ExprId(1), aliases)); }
    let neutral_head = EnvFrame::empty().extend_neutral(Neutral {
        head: NeutralHead::Free(FreeId(0)), spine: vec![],
    });
    let neutral_argument = EnvFrame::empty().extend_neutral(Neutral {
        head: NeutralHead::Const { name: NameId(50), levels: vec![] },
        spine: vec![Closure::new(ExprId(1), EnvFrame::empty().extend_free(FreeId(0)))],
    });
    let projected_receiver = EnvFrame::empty().extend_neutral(Neutral {
        head: NeutralHead::Projection { type_name: NameId(50), index: 0,
            structure: Box::new(Neutral { head: NeutralHead::Free(FreeId(0)), spine: vec![] }) },
        spine: vec![],
    });
    let identity = TypeValue::Term(Closure::new(ExprId(3), EnvFrame::empty()));
    for frame in [aliases, neutral_head, neutral_argument, projected_receiver] {
        let captured = TypeValue::Term(Closure::new(ExprId(4), frame.clone()));
        let relation = checker.convert(&identity, &captured, 512);
        assert!(matches!(relation, metatron_kernel::judgment::Judgment::Unknown { residual }
            if residual.0 == "source-binder-capture-or-support-unavailable"),
            "every actually used transitive capture must decline fresh opening: {relation:?}");
        let unused = TypeValue::Term(Closure::new(ExprId(3), frame));
        assert!(checker.convert(&identity, &unused, 512).is_proven(),
            "ignored alias/neutral capture must not obstruct two source identities");
    }
}

#[test]
fn public_relation_formation_does_not_type_a_captured_local_as_a_lambda_binder() {
    use metatron_kernel::value::FreeId;
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    for (id, node) in [
        (0, Expr::Sort(LevelId(0))), (1, Expr::BVar(0)), (2, Expr::BVar(1)),
        (3, Expr::Pi { domain: ExprId(0), body: ExprId(0) }),
        (4, Expr::Lam { domain: ExprId(0), body: ExprId(1) }),
        (5, Expr::Lam { domain: ExprId(0), body: ExprId(2) }),
        (6, Expr::Pi { domain: ExprId(3), body: ExprId(0) }),
        (7, Expr::Pi { domain: ExprId(3), body: ExprId(6) }),
        (8, Expr::Const { name: NameId(40), levels: vec![] }),
        (9, Expr::App { fun: ExprId(8), arg: ExprId(4) }),
        (10, Expr::App { fun: ExprId(9), arg: ExprId(4) }),
        (11, Expr::App { fun: ExprId(8), arg: ExprId(5) }),
        (12, Expr::App { fun: ExprId(11), arg: ExprId(4) }),
    ] { expressions.insert(ExprId(id), node).unwrap(); }
    let environment = Environment::empty()
        .extend(NameId(40), ConstantDecl::axiom(vec![], ExprId(7))).unwrap();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let captured = |id| Closure::new(ExprId(id), EnvFrame::empty().extend_free(FreeId(0)));
    assert!(checker.certify_applied_proposition_in_context(&captured(10), &[], 2048).is_proven(),
        "unused ambient captures do not obstruct actual identity arguments");
    assert!(!checker.certify_applied_proposition_in_context(&captured(12), &[], 2048).is_proven(),
        "an untyped ambient capture cannot borrow the lambda's fresh binding type");
}

fn shared_receiver_fixture() -> Fixture {
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    for (id, node) in [
        (0, Expr::NatLit(metatron_kernel::nat::BigNat::zero())),
        (1, Expr::NatLit(metatron_kernel::nat::BigNat::parse_decimal("1").unwrap())),
        (2, Expr::BVar(0)), (3, Expr::BVar(1)),
        (4, Expr::Sort(LevelId(0))),
        (5, Expr::Lam { domain: ExprId(4), body: ExprId(2) }),
        (6, Expr::Lam { domain: ExprId(4), body: ExprId(3) }),
    ] { expressions.insert(ExprId(id), node).unwrap(); }
    Fixture { expressions, levels, environment: Environment::empty() }
}

fn shared_receiver_term(changed: Option<usize>, universe: LevelTerm, external_body: bool, aliases: usize) -> TypeValue {
    use metatron_kernel::value::{FreeId, Neutral, NeutralHead};
    let mut motive = Closure::new(ExprId(if external_body { 6 } else { 5 }),
        EnvFrame::empty().extend_free(FreeId(0)));
    for _ in 0..aliases {
        motive = Closure::new(ExprId(2), EnvFrame::empty().extend(motive));
    }
    let spine = (0..5).map(|i| {
        if changed == Some(i) { Closure::new(ExprId(1), EnvFrame::empty()) }
        else if i == 1 { motive.clone() }
        else { Closure::new(ExprId(0), EnvFrame::empty()) }
    }).collect();
    let receiver = Neutral {
        head: NeutralHead::Const { name: NameId(17), levels: vec![universe] }, spine,
    };
    let projected = Neutral {
        head: NeutralHead::Projection { type_name: NameId(18), index: 0, structure: Box::new(receiver) },
        spine: vec![],
    };
    TypeValue::Term(Closure::new(ExprId(2), EnvFrame::empty().extend_neutral(projected)))
}

#[test]
fn projection_receiver_source_proofs_share_one_remaining_allowance() {
    let fixture = shared_receiver_fixture();
    let checker = fixture.checker();
    let left = shared_receiver_term(None, LevelTerm::Zero, false, 37);
    let right = shared_receiver_term(None, LevelTerm::Zero, false, 0);
    assert!(!checker.convert(&left, &right, 32).is_proven(),
        "a cold shared allowance still must cover all actual alias lookups");
    assert!(checker.convert(&left, &right, 493).is_proven(),
        "one receiver argument may exceed its old 1/5 share while all source proofs fit the total");
}

#[test]
fn projection_receiver_shared_source_proof_checks_every_argument_and_universe() {
    let fixture = shared_receiver_fixture();
    let checker = fixture.checker();
    let left = shared_receiver_term(None, LevelTerm::Zero, false, 37);
    for i in 0..5 {
        let wrong = shared_receiver_term(Some(i), LevelTerm::Zero, false, 0);
        assert!(!checker.convert(&left, &wrong, 493).is_proven(),
            "receiver argument {i} must be independently proved");
    }
    let wrong_universe = shared_receiver_term(None, LevelTerm::Succ(Box::new(LevelTerm::Zero)), false, 0);
    assert!(!checker.convert(&left, &wrong_universe, 493).is_proven());
    let captured = shared_receiver_term(None, LevelTerm::Zero, true, 0);
    assert!(!checker.convert(&left, &captured, 493).is_proven(),
        "paired source support must not equate the motive binder with ambient Free0");
}

#[test]
fn exhausted_optional_head_delta_probe_does_not_preempt_ordinary_conversion() {
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    levels.insert(LevelId(1), Level::Succ(LevelId(0))).unwrap();
    levels.insert(LevelId(2), Level::Succ(LevelId(1))).unwrap();
    for (id, node) in [
        (0, Expr::Sort(LevelId(0))), (1, Expr::Sort(LevelId(1))),
        (2, Expr::BVar(0)), (3, Expr::BVar(1)),
        (4, Expr::Pi { domain: ExprId(0), body: ExprId(1) }),
        (5, Expr::Const { name: NameId(40), levels: vec![] }),
        (6, Expr::App { fun: ExprId(5), arg: ExprId(3) }),
        (7, Expr::App { fun: ExprId(5), arg: ExprId(2) }),
        (8, Expr::Lam { domain: ExprId(0), body: ExprId(6) }),
        (9, Expr::Lam { domain: ExprId(0), body: ExprId(7) }),
        (10, Expr::Lam { domain: ExprId(0), body: ExprId(8) }),
        (11, Expr::Lam { domain: ExprId(0), body: ExprId(9) }),
        (12, Expr::Sort(LevelId(2))),
        (13, Expr::Pi { domain: ExprId(0), body: ExprId(12) }),
        (14, Expr::Const { name: NameId(41), levels: vec![] }),
        (15, Expr::App { fun: ExprId(14), arg: ExprId(2) }),
        (16, Expr::Lam { domain: ExprId(0), body: ExprId(15) }),
        (17, Expr::Lam { domain: ExprId(0), body: ExprId(16) }),
        (180, Expr::Lam { domain: ExprId(0), body: ExprId(100) }),
        (181, Expr::Lam { domain: ExprId(0), body: ExprId(1) }),
    ] { expressions.insert(ExprId(id), node).unwrap(); }
    for i in 100..180 {
        expressions.insert(ExprId(i), Expr::Let { ty: ExprId(1), value: ExprId(0),
            body: ExprId(if i == 179 { 0 } else { i + 1 }) }).unwrap();
    }
    let environment = Environment::empty()
        .extend(NameId(40), ConstantDecl::definition(vec![], ExprId(4), ExprId(180), true)).unwrap()
        .extend(NameId(41), ConstantDecl::definition(vec![], ExprId(13), ExprId(181), true)).unwrap();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let source = |id| TypeValue::Term(Closure::new(ExprId(id), EnvFrame::empty()));
    // K ignores its argument and exposes Prop after eighty checked lets.
    // The arguments p/q are distinct ambient propositions in Γ, so cheap
    // argument congruence declines before the bounded head-delta trial.
    assert!(!checker.convert(&source(10), &source(11), 32).is_proven());
    assert!(checker.convert(&source(10), &source(11), 2048).is_proven(),
        "an exhausted optional 64-step probe must permit ordinary conversion with the remaining allowance");
    assert!(!checker.convert(&source(10), &source(17), 2048).is_proven(),
        "ordinary fallback still distinguishes the actually exposed universes");
}

fn cold_optional_delta_fixture() -> (IdTable<ExprId, Expr>, IdTable<LevelId, Level>, Environment) {
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    levels.insert(LevelId(1), Level::Succ(LevelId(0))).unwrap();
    levels.insert(LevelId(2), Level::Succ(LevelId(1))).unwrap();
    for (id, node) in [
        (0, Expr::Sort(LevelId(0))), (1, Expr::Sort(LevelId(1))),
        (2, Expr::BVar(0)),
        (3, Expr::Pi { domain: ExprId(0), body: ExprId(1) }),
        (4, Expr::Const { name: NameId(50), levels: vec![] }),
        (5, Expr::App { fun: ExprId(4), arg: ExprId(2) }),
        (6, Expr::Const { name: NameId(51), levels: vec![] }),
        (7, Expr::App { fun: ExprId(6), arg: ExprId(2) }),
        (8, Expr::Const { name: NameId(50), levels: vec![LevelId(1)] }),
        (9, Expr::App { fun: ExprId(8), arg: ExprId(2) }),
        (10, Expr::Sort(LevelId(2))),
        (11, Expr::Pi { domain: ExprId(0), body: ExprId(10) }),
        (180, Expr::Lam { domain: ExprId(0), body: ExprId(100) }),
        (181, Expr::Lam { domain: ExprId(0), body: ExprId(1) }),
    ] { expressions.insert(ExprId(id), node).unwrap(); }
    for i in 100..180 {
        expressions.insert(ExprId(i), Expr::Let { ty: ExprId(1), value: ExprId(0),
            body: ExprId(if i == 179 { 0 } else { i + 1 }) }).unwrap();
    }
    let environment = Environment::empty()
        .extend(NameId(50), ConstantDecl::definition(vec![], ExprId(3), ExprId(180), true)).unwrap()
        .extend(NameId(51), ConstantDecl::definition(vec![], ExprId(11), ExprId(181), true)).unwrap();
    (expressions, levels, environment)
}

fn cold_optional_delta_term(source: u64, free: u64) -> TypeValue {
    use metatron_kernel::value::FreeId;
    let mut argument = Closure::new(ExprId(2), EnvFrame::empty().extend_free(FreeId(free)));
    for _ in 0..37 { argument = Closure::new(ExprId(2), EnvFrame::empty().extend(argument)); }
    TypeValue::Term(Closure::new(ExprId(source), EnvFrame::empty().extend(argument)))
}

#[test]
fn cold_captured_optional_delta_exhaustion_preserves_the_ordinary_derivation() {
    let (expressions, levels, environment) = cold_optional_delta_fixture();
    let left = cold_optional_delta_term(5, 0);
    let right = cold_optional_delta_term(5, 1);
    let cold = TypeChecker::new(&expressions, &levels, &environment);
    assert!(!cold.convert(&left, &right, 32).is_proven());
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    // Actual p/q differ and their37 aliases exceed the cheap congruence
    // allowance. Both optional64-step delta probes then exhaust on80 lets.
    // This is a fresh checker: eta and previously completed reductions cannot
    // discharge the comparison before its ordinary fallback is exercised.
    assert!(checker.convert(&left, &right, 2048).is_proven(),
        "an optional UNKNOWN is not an obstruction to a remaining ordinary derivation");
}

#[test]
fn optional_delta_unknown_fallback_preserves_universe_and_metadata_checks() {
    let (expressions, levels, environment) = cold_optional_delta_fixture();
    let left = cold_optional_delta_term(5, 0);
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    assert!(!checker.convert(&left, &cold_optional_delta_term(7, 1), 2048).is_proven(),
        "ordinary fallback must distinguish Sort0 from Sort1");
    let malformed = TypeChecker::new(&expressions, &levels, &environment);
    assert!(!malformed.convert(&cold_optional_delta_term(9, 0), &cold_optional_delta_term(9, 1), 2048).is_proven(),
        "wrong declaration universe arity cannot become a positive delta result");
}

fn deferred_nonpreferred_nat_fixture() -> Fixture {
    use metatron_kernel::nat::BigNat;
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    levels.insert(LevelId(1), Level::Succ(LevelId(0))).unwrap();
    levels.insert(LevelId(2), Level::Param(NameId(66))).unwrap();
    levels.insert(LevelId(3), Level::Succ(LevelId(2))).unwrap();
    for (id, node) in [
        (0, Expr::Sort(LevelId(1))),
        (1, Expr::Const { name: NameId(60), levels: vec![] }),
        (2, Expr::NatLit(BigNat::zero())),
        (3, Expr::NatLit(BigNat::parse_decimal("1").unwrap())),
        (4, Expr::Pi { domain: ExprId(1), body: ExprId(1) }),
        (5, Expr::Const { name: NameId(61), levels: vec![] }),
        (6, Expr::App { fun: ExprId(5), arg: ExprId(2) }),
        (7, Expr::App { fun: ExprId(5), arg: ExprId(3) }),
        (8, Expr::Const { name: NameId(62), levels: vec![] }),
        (9, Expr::App { fun: ExprId(8), arg: ExprId(2) }),
        (10, Expr::Const { name: NameId(63), levels: vec![] }),
        (11, Expr::App { fun: ExprId(10), arg: ExprId(2) }),
        (12, Expr::App { fun: ExprId(10), arg: ExprId(3) }),
        (13, Expr::Const { name: NameId(61), levels: vec![LevelId(1)] }),
        (14, Expr::App { fun: ExprId(13), arg: ExprId(2) }),
        (15, Expr::App { fun: ExprId(13), arg: ExprId(3) }),
        (20, Expr::Sort(LevelId(2))), (21, Expr::BVar(0)), (22, Expr::BVar(1)),
        (23, Expr::BVar(2)), (24, Expr::BVar(3)),
        (25, Expr::Pi { domain: ExprId(1), body: ExprId(20) }),
        (26, Expr::Const { name: NameId(64), levels: vec![] }),
        (27, Expr::App { fun: ExprId(21), arg: ExprId(26) }),
        (28, Expr::App { fun: ExprId(23), arg: ExprId(21) }),
        (29, Expr::Const { name: NameId(63), levels: vec![] }),
        (30, Expr::App { fun: ExprId(29), arg: ExprId(22) }),
        (31, Expr::App { fun: ExprId(24), arg: ExprId(30) }),
        (32, Expr::Pi { domain: ExprId(28), body: ExprId(31) }),
        (33, Expr::Pi { domain: ExprId(1), body: ExprId(32) }),
        (34, Expr::App { fun: ExprId(24), arg: ExprId(21) }),
        (35, Expr::Pi { domain: ExprId(1), body: ExprId(34) }),
        (36, Expr::Pi { domain: ExprId(33), body: ExprId(35) }),
        (37, Expr::Pi { domain: ExprId(27), body: ExprId(36) }),
        (38, Expr::Pi { domain: ExprId(25), body: ExprId(37) }),
        (40, Expr::Sort(LevelId(2))), (41, Expr::Sort(LevelId(3))),
        (42, Expr::Pi { domain: ExprId(1), body: ExprId(41) }),
        (43, Expr::Lam { domain: ExprId(1), body: ExprId(40) }),
        (44, Expr::Const { name: NameId(67), levels: vec![LevelId(0)] }),
        (45, Expr::Const { name: NameId(67), levels: vec![LevelId(1)] }),
        (46, Expr::App { fun: ExprId(44), arg: ExprId(2) }),
        (47, Expr::App { fun: ExprId(45), arg: ExprId(2) }),
        (180, Expr::Lam { domain: ExprId(1), body: ExprId(100) }),
        (181, Expr::Lam { domain: ExprId(1), body: ExprId(3) }),
    ] { expressions.insert(ExprId(id), node).unwrap(); }
    for i in 100..180 {
        expressions.insert(ExprId(i), Expr::Let { ty: ExprId(1), value: ExprId(2),
            body: ExprId(if i == 179 { 2 } else { i + 1 }) }).unwrap();
    }
    let environment = Environment::empty()
        .extend(NameId(60), ConstantDecl::axiom(vec![], ExprId(0))).unwrap()
        .extend(NameId(61), ConstantDecl::definition(vec![], ExprId(4), ExprId(180), false)).unwrap()
        .extend(NameId(62), ConstantDecl::definition(vec![], ExprId(4), ExprId(181), false)).unwrap()
        .extend(NameId(63), ConstantDecl::constructor(vec![], ExprId(4))).unwrap()
        .extend(NameId(64), ConstantDecl::constructor(vec![], ExprId(1))).unwrap()
        .extend(NameId(65), ConstantDecl::recursor(vec![NameId(66)], ExprId(38))).unwrap()
        .extend(NameId(67), ConstantDecl::definition(vec![NameId(66)], ExprId(42), ExprId(43), false)).unwrap()
        .install_nat_primitives(metatron_kernel::environment::NatPrimitives {
            type_name: NameId(60), type_expr: ExprId(1), zero: NameId(64),
            succ: NameId(63), recursor: NameId(65), add: None, mul: None,
            pow: None, land: None, shift_right: None, div: None, modulo: None,
            sub: None, pred: None, virtual_bvar_zero: Some(ExprId(21)), ble: None, beq: None,
        }).unwrap();
    Fixture { expressions, levels, environment }
}

#[test]
fn deferred_nonrigid_argument_mismatch_must_allow_full_parent_reduction() {
    let fixture = deferred_nonpreferred_nat_fixture();
    let typing = fixture.checker();
    assert!(typing.is_type(ExprId(4), 4096).is_proven());
    let recursor_formation = TypeChecker::with_level_substitution(&fixture.expressions,
        &fixture.levels, &fixture.environment, HashMap::from([(NameId(66), LevelTerm::Zero)]));
    assert!(recursor_formation.is_type(ExprId(38), 4096).is_proven());
    assert!(typing.check(ExprId(180), &Fixture::term(4), 4096).is_proven(), "K must have the genuine checked Nat-to-Nat signature");
    assert!(!fixture.checker().convert(&Fixture::term(6), &Fixture::term(7), 32).is_proven());
    let result = fixture.checker().convert(&Fixture::term(6), &Fixture::term(7), 2048);
    assert!(result.is_proven(), "K 0 and K 1 both reduce to 0; unequal arguments only decline nonrigid congruence: {result:?}");
}

#[test]
fn deferred_parent_fallback_preserves_distinct_data_and_malformed_metadata() {
    let fixture = deferred_nonpreferred_nat_fixture();
    assert!(fixture.checker().convert(&Fixture::term(11), &Fixture::term(12), 2048).is_refuted(),
        "a rigid opaque constructor cannot discard its unequal data arguments");
    assert!(!fixture.checker().convert(&Fixture::term(6), &Fixture::term(9), 2048).is_proven(),
        "actually different definition results stay distinct");
    assert!(!fixture.checker().convert(&Fixture::term(46), &Fixture::term(47), 2048).is_proven(),
        "full fallback preserves actual instantiations Sort0 versusSort1");
    assert!(!fixture.checker().convert(&Fixture::term(14), &Fixture::term(15), 2048).is_proven(),
        "malformed universe arity does not justify full delta");
}


fn retained_same_head_nat_recursor_fixture() -> Fixture {
    use metatron_kernel::machine::{RecursorReduction, RecursorRule};
    let mut fixture = deferred_nonpreferred_nat_fixture();
    for (id, node) in [
        (50, Expr::Lam { domain: ExprId(1), body: ExprId(1) }),
        (51, Expr::Lam { domain: ExprId(1), body: ExprId(2) }),
        (52, Expr::Lam { domain: ExprId(1), body: ExprId(51) }),
        (53, Expr::Lam { domain: ExprId(1), body: ExprId(3) }),
        (54, Expr::Lam { domain: ExprId(1), body: ExprId(53) }),
        // Zero source RHS: fun motive base step => base.
        (60, Expr::Lam { domain: ExprId(33), body: ExprId(22) }),
        (61, Expr::Lam { domain: ExprId(27), body: ExprId(60) }),
        (62, Expr::Lam { domain: ExprId(25), body: ExprId(61) }),
        // Successor source RHS: fun motive base step n =>
        // step n (rec motive base step n).
        (63, Expr::Const { name: NameId(65), levels: vec![LevelId(2)] }),
        (64, Expr::App { fun: ExprId(63), arg: ExprId(24) }),
        (65, Expr::App { fun: ExprId(64), arg: ExprId(23) }),
        (66, Expr::App { fun: ExprId(65), arg: ExprId(22) }),
        (67, Expr::App { fun: ExprId(66), arg: ExprId(21) }),
        (68, Expr::App { fun: ExprId(22), arg: ExprId(21) }),
        (69, Expr::App { fun: ExprId(68), arg: ExprId(67) }),
        (70, Expr::Lam { domain: ExprId(1), body: ExprId(69) }),
        (71, Expr::Lam { domain: ExprId(33), body: ExprId(70) }),
        (72, Expr::Lam { domain: ExprId(27), body: ExprId(71) }),
        (73, Expr::Lam { domain: ExprId(25), body: ExprId(72) }),
        (74, Expr::App { fun: ExprId(23), arg: ExprId(26) }),
        (75, Expr::Pi { domain: ExprId(33), body: ExprId(74) }),
        (76, Expr::Pi { domain: ExprId(27), body: ExprId(75) }),
        (77, Expr::Pi { domain: ExprId(25), body: ExprId(76) }),
        (78, Expr::App { fun: ExprId(29), arg: ExprId(21) }),
        (79, Expr::App { fun: ExprId(24), arg: ExprId(78) }),
        (80, Expr::Pi { domain: ExprId(1), body: ExprId(79) }),
        (81, Expr::Pi { domain: ExprId(33), body: ExprId(80) }),
        (82, Expr::Pi { domain: ExprId(27), body: ExprId(81) }),
        (83, Expr::Pi { domain: ExprId(25), body: ExprId(82) }),
        (84, Expr::Pi { domain: ExprId(1), body: ExprId(4) }),
    ] { fixture.expressions.insert(ExprId(id), node).unwrap(); }
    fixture.environment = fixture.environment.install_recursor_reduction(NameId(65), RecursorReduction {
        k: false, num_params: 0, num_indices: 0, level_params: vec![NameId(66)],
        rules: vec![
            RecursorRule { constructor: NameId(64), constructor_level_params: vec![], num_params: 0, num_fields: 0, rhs: ExprId(62) },
            RecursorRule { constructor: NameId(63), constructor_level_params: vec![], num_params: 0, num_fields: 1, rhs: ExprId(73) },
        ],
    }).unwrap();
    fixture
}

fn retained_nat_recursor(base: u64, step: u64, major: u64, levels: Vec<LevelTerm>) -> TypeValue {
    retained_nat_recursor_with_major(base, step, Closure::new(ExprId(major), EnvFrame::empty()), levels)
}

fn retained_nat_recursor_with_major(base: u64, step: u64, major: Closure, levels: Vec<LevelTerm>) -> TypeValue {
    use metatron_kernel::value::{Neutral, NeutralHead};
    let mut spine = [50, base, step].into_iter().map(|id| Closure::new(ExprId(id), EnvFrame::empty())).collect::<Vec<_>>();
    spine.push(major);
    let captured = Neutral {
        head: NeutralHead::Const { name: NameId(65), levels }, spine,
    };
    TypeValue::Term(Closure::new(ExprId(21), EnvFrame::empty().extend_neutral(captured)))
}

#[test]
fn same_registered_recursor_head_reduces_before_comparing_unused_minors() {
    let fixture = retained_same_head_nat_recursor_fixture();
    let typing = TypeChecker::with_level_substitution(&fixture.expressions, &fixture.levels,
        &fixture.environment, HashMap::from([(NameId(66), LevelTerm::Succ(Box::new(LevelTerm::Zero)))]));
    for (rhs, expected) in [(62, 77), (73, 83)] {
        assert!(typing.is_type(ExprId(expected), 8192).is_proven());
        let result = typing.check(ExprId(rhs), &TypeValue::Term(Closure::with_levels(ExprId(expected), EnvFrame::empty(),
            metatron_kernel::value::LevelSubstitution::new(vec![(NameId(66), LevelTerm::Succ(Box::new(LevelTerm::Zero)))]))), 8192);
        assert!(result.is_proven(), "rule {rhs} must have its genuine dependent source signature: {result:?}");
    }
    assert!(typing.check(ExprId(52), &Fixture::term(84), 1024).is_proven());
    assert!(typing.check(ExprId(54), &Fixture::term(84), 1024).is_proven());
    let universe = vec![LevelTerm::Succ(Box::new(LevelTerm::Zero))];
    let left = retained_nat_recursor(2, 52, 2, universe.clone());
    let mut aliased_zero = Closure::new(ExprId(2), EnvFrame::empty());
    for _ in 0..37 {
        let frame = EnvFrame::empty().extend_free(metatron_kernel::value::FreeId(99)).extend(aliased_zero);
        aliased_zero = Closure::new(ExprId(21), frame);
    }
    let right = retained_nat_recursor_with_major(2, 54, aliased_zero, universe);
    // Both actual zero majors select the checked base 0. Their successor
    // branches are different functions, but neither branch is used.
    let result = fixture.checker().convert(&left, &right, 2048);
    assert!(result.is_proven(), "actual zero iota must precede nonrigid minor congruence: {result:?}");
    assert!(!fixture.checker().convert(&left, &right, 32).is_proven());
}

#[test]
fn same_registered_recursor_replay_preserves_used_data_and_source_arity() {
    let fixture = retained_same_head_nat_recursor_fixture();
    let universe = vec![LevelTerm::Succ(Box::new(LevelTerm::Zero))];
    let zero = retained_nat_recursor(2, 52, 2, universe.clone());
    let different_base = retained_nat_recursor(3, 54, 2, universe.clone());
    assert!(!fixture.checker().convert(&zero, &different_base, 2048).is_proven());
    let successor_left = retained_nat_recursor(2, 52, 3, universe.clone());
    let successor_right = retained_nat_recursor(2, 54, 3, universe);
    assert!(!fixture.checker().convert(&successor_left, &successor_right, 2048).is_proven(),
        "the actual successor major uses the distinct successor branches");
    let malformed_left = retained_nat_recursor(2, 52, 2, vec![]);
    let malformed_right = retained_nat_recursor(2, 54, 2, vec![]);
    assert!(!fixture.checker().convert(&malformed_left, &malformed_right, 2048).is_proven());
}

fn retained_nested_zero_major(depth: usize) -> Closure {
    use metatron_kernel::value::{Neutral, NeutralHead};
    let mut major = Closure::new(ExprId(26), EnvFrame::empty());
    for _ in 0..depth {
        let mut spine = [50, 26, 52].into_iter()
            .map(|id| Closure::new(ExprId(id), EnvFrame::empty())).collect::<Vec<_>>();
        spine.push(major);
        major = Closure::new(ExprId(21), EnvFrame::empty().extend_neutral(Neutral {
            head: NeutralHead::Const { name: NameId(65), levels: vec![LevelTerm::Succ(Box::new(LevelTerm::Zero))] },
            spine,
        }));
    }
    major
}

#[test]
fn actual_nested_recursor_replay_can_use_the_remaining_comparison_budget() {
    let fixture = retained_same_head_nat_recursor_fixture();
    let universe = vec![LevelTerm::Succ(Box::new(LevelTerm::Zero))];
    let major = retained_nested_zero_major(64);
    let left = retained_nat_recursor_with_major(26, 52, major.clone(), universe.clone());
    let right = retained_nat_recursor_with_major(26, 54, major, universe);
    let result = fixture.checker().convert(&left, &right, 8192);
    assert!(result.is_proven(), "each actual zero major selects its genuine source base; a local 512 ceiling must not discard the remaining budget: {result:?}");
    assert!(!fixture.checker().convert(&left, &right, 32).is_proven());
    assert!(!fixture.checker().convert(&left, &right, 512).is_proven());
}

#[test]
fn expanded_nested_replay_still_requires_actual_major_and_registered_rules() {
    use metatron_kernel::value::FreeId;
    let fixture = retained_same_head_nat_recursor_fixture();
    let universe = vec![LevelTerm::Succ(Box::new(LevelTerm::Zero))];
    let unknown = Closure::new(ExprId(21), EnvFrame::empty().extend_free(FreeId(99)));
    let left = retained_nat_recursor_with_major(26, 52, unknown.clone(), universe.clone());
    let right = retained_nat_recursor_with_major(26, 54, unknown, universe.clone());
    assert!(!fixture.checker().convert(&left, &right, 8192).is_proven());
    let successor_left = retained_nat_recursor(26, 52, 3, universe.clone());
    let successor_right = retained_nat_recursor(26, 54, 3, universe.clone());
    assert!(!fixture.checker().convert(&successor_left, &successor_right, 8192).is_proven());
    let major = retained_nested_zero_major(64);
    let left = retained_nat_recursor_with_major(26, 52, major.clone(), universe.clone());
    let right = retained_nat_recursor_with_major(26, 54, major, universe);
    let missing = Fixture { expressions: fixture.expressions, levels: fixture.levels,
        environment: deferred_nonpreferred_nat_fixture().environment };
    assert!(!missing.checker().convert(&left, &right, 8192).is_proven());
}
