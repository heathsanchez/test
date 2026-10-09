use metatron_kernel::environment::{ConstantDecl, Environment};
use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::level::{LevelTerm, succ};
use metatron_kernel::syntax::{Expr, Level};
use metatron_kernel::typecheck::{TypeChecker, TypeValue};
use metatron_kernel::value::{Closure, EnvFrame, FreeId};

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
            binder: FreeId(0),
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


/// Regression: an inferred Pi from a lambda wrapped in a legal let must
/// instantiate its captured binder even though the App head is not a literal
/// lambda expression. The binder is introduced inside the let context and
/// therefore does not have the caller's local depth.
#[test]
fn dependent_let_wrapped_lambda_substitutes_proposition_binder() {
    let mut fixture = Fixture::dependent_core();
    // The inner term is (fun proof : P => proof), with P = BVar(0).
    fixture.expressions.insert(ExprId(11), Expr::Lam {
        domain: ExprId(1), body: ExprId(1),
    }).unwrap();
    // (fun P : Prop => fun proof : P => proof)
    fixture.expressions.insert(ExprId(12), Expr::Lam {
        domain: ExprId(0), body: ExprId(11),
    }).unwrap();
    // (let ignored : Prop := A; fun P : Prop => fun proof : P => proof).
    fixture.expressions.insert(ExprId(13), Expr::Let {
        ty: ExprId(0), value: ExprId(4), body: ExprId(12),
    }).unwrap();
    // The result of applying the let-wrapped lambda to A is a function A -> A.
    fixture.expressions.insert(ExprId(14), Expr::App {
        fun: ExprId(13), arg: ExprId(4),
    }).unwrap();
    // Existing f : (P : Prop) -> P supplies a well-typed proof of A.
    fixture.expressions.insert(ExprId(15), Expr::App {
        fun: ExprId(14), arg: ExprId(10),
    }).unwrap();
    // Deliberately wrong second argument: A is a proposition, not a proof of A.
    fixture.expressions.insert(ExprId(16), Expr::App {
        fun: ExprId(14), arg: ExprId(4),
    }).unwrap();

    let checker = fixture.checker();
    let accepted = checker.infer(ExprId(15), 4096);
    assert!(
        accepted.is_proven(),
        "let-wrapped dependent lambda must accept checked proof: {accepted:?}"
    );
    assert!(
        checker.convert(
            accepted.proven_value().unwrap(),
            &TypeValue::Term(Closure::new(ExprId(4), EnvFrame::empty())),
            4096,
        ).is_proven(),
        "instantiated result must still inhabit the original proposition A"
    );
    assert!(
        !checker.infer(ExprId(16), 4096).is_proven(),
        "a proposition expression must not be accepted as a proof of itself"
    );
}


/// Verify the new local-proof proposition warrant from the declaration
/// telescope AND its exact typed application arguments, not just Sort 1.
#[test]
fn captured_two_argument_relation_requires_checked_domains() {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    let mut exprs = IdTable::default();
    let nodes = [
        (0, Expr::Sort(LevelId(0))),                    // Prop
        (1, Expr::Const { name: NameId(1), levels: vec![] }), // A : Prop
        (2, Expr::Pi { domain: ExprId(1), body: ExprId(0) }),
        (3, Expr::Pi { domain: ExprId(1), body: ExprId(2) }),
        (4, Expr::Const { name: NameId(3), levels: vec![] }), // R : A -> A -> Prop
        (5, Expr::Const { name: NameId(2), levels: vec![] }), // p : A
        (6, Expr::App { fun: ExprId(4), arg: ExprId(5) }),
        (7, Expr::App { fun: ExprId(6), arg: ExprId(5) }), // R p p
        (8, Expr::App { fun: ExprId(4), arg: ExprId(1) }),
        (9, Expr::App { fun: ExprId(8), arg: ExprId(5) }), // R A p, invalid
        (10, Expr::Lam { domain: ExprId(1), body: ExprId(4) }),
        (11, Expr::App { fun: ExprId(10), arg: ExprId(1) }),
        (12, Expr::App { fun: ExprId(11), arg: ExprId(5) }),
        (13, Expr::App { fun: ExprId(12), arg: ExprId(5) }), // beta normalizes to R p p,
                                                               // but the discarded argument A : Prop
                                                               // is not a proof of A
    ];
    for (id, expr) in nodes {
        exprs.insert(ExprId(id), expr).unwrap();
    }
    let environment = Environment::empty()
        .extend(NameId(1), ConstantDecl::axiom(vec![], ExprId(0))).unwrap()
        .extend(NameId(2), ConstantDecl::axiom(vec![], ExprId(1))).unwrap()
        .extend(NameId(3), ConstantDecl::axiom(vec![], ExprId(3))).unwrap();
    let checker = TypeChecker::new(&exprs, &levels, &environment);
    let certify = |id| checker.certify_applied_proposition_in_context(
        &Closure::new(ExprId(id), EnvFrame::empty()), &[], 4096,
    );
    assert!(
        certify(7).is_proven(),
        "a well-typed R p p must give a checked proposition certificate: {:?}",
        certify(7),
    );
    assert!(
        !certify(9).is_proven(),
        "an ill-typed first argument must never certify a proposition",
    );
    assert!(
        !certify(13).is_proven(),
        "an ill-typed beta-redex discarded during normalization is not a typed application",
    );
}
