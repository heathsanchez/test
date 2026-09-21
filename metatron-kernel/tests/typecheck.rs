use metatron_kernel::environment::{ConstantDecl, Environment};
use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::level::{LevelTerm, succ};
use metatron_kernel::syntax::{Expr, Level};
use metatron_kernel::typecheck::{TypeChecker, TypeValue};
use metatron_kernel::value::{Closure, EnvFrame};

struct Fixture {
    expressions: IdTable<ExprId, Expr>,
    levels: IdTable<LevelId, Level>,
    environment: Environment,
}

impl Fixture {
    fn dependent_core() -> Self {
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
                Expr::Pi {
                    domain: ExprId(0),
                    body: ExprId(0),
                },
            )
            .unwrap();
        expressions
            .insert(
                ExprId(3),
                Expr::Lam {
                    domain: ExprId(0),
                    body: ExprId(1),
                },
            )
            .unwrap();
        expressions
            .insert(
                ExprId(4),
                Expr::Const {
                    name: NameId(1),
                    levels: Vec::new(),
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
                Expr::Let {
                    ty: ExprId(0),
                    value: ExprId(4),
                    body: ExprId(1),
                },
            )
            .unwrap();
        expressions.insert(ExprId(7), Expr::BVar(0)).unwrap();
        expressions
            .insert(
                ExprId(8),
                Expr::Pi {
                    domain: ExprId(0),
                    body: ExprId(1),
                },
            )
            .unwrap();
        expressions
            .insert(
                ExprId(9),
                Expr::Const {
                    name: NameId(2),
                    levels: Vec::new(),
                },
            )
            .unwrap();
        expressions
            .insert(
                ExprId(10),
                Expr::App {
                    fun: ExprId(9),
                    arg: ExprId(4),
                },
            )
            .unwrap();

        let environment = Environment::empty()
            .extend(NameId(1), ConstantDecl::axiom(Vec::new(), ExprId(0)))
            .unwrap()
            .extend(NameId(2), ConstantDecl::axiom(Vec::new(), ExprId(8)))
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
}

#[test]
fn sort_u_has_type_sort_successor_u() {
    let fixture = Fixture::dependent_core();
    let inferred = fixture.checker().infer(ExprId(0), 64);
    assert_eq!(
        inferred.proven_value(),
        Some(&TypeValue::Sort(succ(LevelTerm::Zero)))
    );
}

#[test]
fn pi_sort_uses_imax_of_domain_and_body_sorts() {
    let fixture = Fixture::dependent_core();
    let inferred = fixture.checker().infer(ExprId(2), 64);
    assert_eq!(
        inferred.proven_value(),
        Some(&TypeValue::Sort(succ(LevelTerm::Zero)))
    );
}

#[test]
fn annotated_identity_lambda_infers_a_pi_type() {
    let fixture = Fixture::dependent_core();
    let inferred = fixture.checker().infer(ExprId(3), 64);
    let domain = TypeValue::Term(Closure::new(ExprId(0), EnvFrame::empty()));
    assert_eq!(
        inferred.proven_value(),
        Some(&TypeValue::Pi {
            domain: Box::new(domain.clone()),
            body: Box::new(domain),
        })
    );
}

#[test]
fn identity_application_checks_its_argument() {
    let fixture = Fixture::dependent_core();
    let inferred = fixture.checker().infer(ExprId(5), 128);
    assert_eq!(
        inferred.proven_value(),
        Some(&TypeValue::Term(Closure::new(ExprId(0), EnvFrame::empty())))
    );
}

#[test]
fn let_inference_uses_the_established_annotation() {
    let fixture = Fixture::dependent_core();
    let inferred = fixture.checker().infer(ExprId(6), 128);
    assert_eq!(
        inferred.proven_value(),
        Some(&TypeValue::Term(Closure::new(ExprId(0), EnvFrame::empty())))
    );
}

#[test]
fn unbound_bvar_is_refuted() {
    let fixture = Fixture::dependent_core();
    assert!(fixture.checker().infer(ExprId(7), 64).is_refuted());
}

#[test]
fn dependent_application_instantiates_the_pi_body_with_the_argument_closure() {
    let fixture = Fixture::dependent_core();
    let checker = fixture.checker();
    let inferred = checker.infer(ExprId(10), 128);
    let expected = TypeValue::Term(Closure::new(ExprId(4), EnvFrame::empty()));

    assert!(
        checker
            .convert(inferred.proven_value().unwrap(), &expected, 64)
            .is_proven()
    );
}
