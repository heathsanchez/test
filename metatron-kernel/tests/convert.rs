use std::collections::HashMap;

use metatron_kernel::environment::{ConstantDecl, Environment};
use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::level::LevelTerm;
use metatron_kernel::syntax::{Expr, Level};
use metatron_kernel::typecheck::{TypeChecker, TypeValue};
use metatron_kernel::value::{Closure, EnvFrame};

struct Fixture {
    expressions: IdTable<ExprId, Expr>,
    levels: IdTable<LevelId, Level>,
    environment: Environment,
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
