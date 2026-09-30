use metatron_kernel::{
    environment::{ConstantDecl, Environment},
    id::{ExprId, IdTable, LevelId, NameId},
    syntax::{Expr, Level},
    typecheck::TypeChecker,
};

#[test]
fn shared_lambda_dag_is_checked_once_per_typing_frame() {
    let mut es = IdTable::default();
    let mut ls = IdTable::default();
    ls.insert(LevelId(0), Level::Zero).unwrap();
    let xs = [
        Expr::Sort(LevelId(0)),
        Expr::Const {
            name: NameId(1),
            levels: vec![],
        },
        Expr::Const {
            name: NameId(2),
            levels: vec![],
        },
        Expr::Pi {
            domain: ExprId(1),
            body: ExprId(1),
        },
        Expr::Pi {
            domain: ExprId(3),
            body: ExprId(1),
        },
        Expr::Pi {
            domain: ExprId(3),
            body: ExprId(4),
        },
        Expr::Const {
            name: NameId(3),
            levels: vec![],
        },
    ];
    for (i, e) in xs.into_iter().enumerate() {
        es.insert(ExprId(i as u64), e).unwrap();
    }
    let mut root = ExprId(2);
    for i in 0..16 {
        let n = 7 + 3 * i;
        es.insert(
            ExprId(n),
            Expr::Lam {
                domain: ExprId(1),
                body: root,
            },
        )
        .unwrap();
        es.insert(
            ExprId(n + 1),
            Expr::App {
                fun: ExprId(6),
                arg: ExprId(n),
            },
        )
        .unwrap();
        es.insert(
            ExprId(n + 2),
            Expr::App {
                fun: ExprId(n + 1),
                arg: ExprId(n),
            },
        )
        .unwrap();
        root = ExprId(n + 2);
    }
    let env = Environment::empty()
        .extend(NameId(1), ConstantDecl::axiom(vec![], ExprId(0)))
        .unwrap()
        .extend(NameId(2), ConstantDecl::axiom(vec![], ExprId(1)))
        .unwrap()
        .extend(NameId(3), ConstantDecl::axiom(vec![], ExprId(5)))
        .unwrap();
    assert!(
        TypeChecker::new(&es, &ls, &env)
            .infer(root, 512)
            .is_proven()
    );
}

#[test]
fn shared_bvar_syntax_retains_its_own_binder_type() {
    let mut es = IdTable::default();
    let mut ls = IdTable::default();
    ls.insert(LevelId(0), Level::Zero).unwrap();
    let xs = [
        Expr::Sort(LevelId(0)),
        Expr::Const {
            name: NameId(1),
            levels: vec![],
        },
        Expr::Const {
            name: NameId(2),
            levels: vec![],
        },
        Expr::BVar(0),
        Expr::Pi {
            domain: ExprId(1),
            body: ExprId(1),
        },
        Expr::Pi {
            domain: ExprId(2),
            body: ExprId(2),
        },
        Expr::Pi {
            domain: ExprId(5),
            body: ExprId(1),
        },
        Expr::Pi {
            domain: ExprId(4),
            body: ExprId(6),
        },
        Expr::Lam {
            domain: ExprId(1),
            body: ExprId(3),
        },
        Expr::Lam {
            domain: ExprId(2),
            body: ExprId(3),
        },
        Expr::Const {
            name: NameId(3),
            levels: vec![],
        },
        Expr::App {
            fun: ExprId(10),
            arg: ExprId(8),
        },
        Expr::App {
            fun: ExprId(11),
            arg: ExprId(9),
        },
        Expr::App {
            fun: ExprId(11),
            arg: ExprId(8),
        },
    ];
    for (i, e) in xs.into_iter().enumerate() {
        es.insert(ExprId(i as u64), e).unwrap();
    }
    let env = Environment::empty()
        .extend(NameId(1), ConstantDecl::axiom(vec![], ExprId(0)))
        .unwrap()
        .extend(NameId(2), ConstantDecl::axiom(vec![], ExprId(0)))
        .unwrap()
        .extend(NameId(3), ConstantDecl::axiom(vec![], ExprId(7)))
        .unwrap();
    let ck = TypeChecker::new(&es, &ls, &env);
    assert!(ck.infer(ExprId(12), 512).is_proven());
    assert!(!ck.infer(ExprId(13), 512).is_proven());
}
