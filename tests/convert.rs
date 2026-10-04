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
