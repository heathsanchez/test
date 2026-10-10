use metatron_kernel::{
    convert::DeltaPolicy,
    environment::{ConstantDecl, Environment},
    id::{ExprId,IdTable,LevelId,NameId},
    syntax::{Expr,Level},
    typecheck::{TypeChecker,TypeValue},
    value::{Closure,EnvFrame},
};

fn test_equal(left:u64,right:u64) -> metatron_kernel::judgment::Judgment<()> {
    let mut levels=IdTable::default();
    levels.insert(LevelId(0),Level::Zero).unwrap();
    levels.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
    let mut expr=IdTable::default();
    let nodes=[
        (0,Expr::Sort(LevelId(1))), // Type
        (1,Expr::Const{name:NameId(1),levels:vec![]}), // Nat
        (2,Expr::Const{name:NameId(2),levels:vec![]}), // n : Nat
        (3,Expr::Const{name:NameId(3),levels:vec![]}), // m : Nat
        (4,Expr::Pi{domain:ExprId(1),body:ExprId(1)}), // Nat -> Nat
        (5,Expr::Lam{domain:ExprId(1),body:ExprId(2)}), // ignore Nat arg
        (6,Expr::Const{name:NameId(4),levels:vec![]}), // f : Nat -> Nat
        (7,Expr::App{fun:ExprId(6),arg:ExprId(2)}), // f n
        (8,Expr::App{fun:ExprId(6),arg:ExprId(3)}), // f m
        (9,Expr::BVar(0)),
        (10,Expr::Lam{domain:ExprId(1),body:ExprId(9)}), // identity
        (11,Expr::Const{name:NameId(5),levels:vec![]}),
        (12,Expr::App{fun:ExprId(11),arg:ExprId(2)}), // id n
        (13,Expr::App{fun:ExprId(11),arg:ExprId(3)}), // id m
        (14,Expr::Sort(LevelId(0))), // Prop itself is not Nat
        (15,Expr::App{fun:ExprId(6),arg:ExprId(14)}), // invalid argument
        (16,Expr::Pi{domain:ExprId(1),body:ExprId(9)}), // dependent type, must not erase
        (17,Expr::Const{name:NameId(6),levels:vec![]}),
        (18,Expr::App{fun:ExprId(17),arg:ExprId(2)}),
        (19,Expr::App{fun:ExprId(17),arg:ExprId(3)}),
    ];
    for (i,node) in nodes {
        expr.insert(ExprId(i),node).unwrap();
    }
    let env=Environment::empty()
       .extend(NameId(1),ConstantDecl::axiom(vec![],ExprId(0))).unwrap()
       .extend(NameId(2),ConstantDecl::axiom(vec![],ExprId(1))).unwrap()
       .extend(NameId(3),ConstantDecl::axiom(vec![],ExprId(1))).unwrap()
       .extend(NameId(4),ConstantDecl::definition(vec![],ExprId(4),ExprId(5),false)).unwrap()
       .extend(NameId(5),ConstantDecl::definition(vec![],ExprId(4),ExprId(10),false)).unwrap()
       // Malformed-dependent signature is intentionally an adversarial case.
       .extend(NameId(6),ConstantDecl::definition(vec![],ExprId(16),ExprId(5),false)).unwrap();
    let ck=TypeChecker::new(&expr,&levels,&env);
    ck.convert_with_policy(
        &TypeValue::Term(Closure::new(ExprId(left),EnvFrame::empty())),
        &TypeValue::Term(Closure::new(ExprId(right),EnvFrame::empty())),
        8192,DeltaPolicy::PreferredOnly,
    )
}

#[test]
fn checked_absent_data_argument_has_same_result() {
    let result=test_equal(7,8);
    assert!(result.is_proven(),
        "a certified value-and-type-absent argument must be ignorable: {result:?}");
}

#[test]
fn source_value_using_argument_cannot_be_ignored() {
    let result=test_equal(12,13);
    assert!(!result.is_proven(),
        "a source value using BVar0 is observably different: {result:?}");
}

#[test]
fn source_ignored_argument_still_requires_well_typed_inputs() {
    let result=test_equal(15,7);
    assert!(!result.is_proven(),
        "discarded ill-typed argument cannot be admitted: {result:?}");
}

#[test]
fn dependent_result_type_blocks_absence_elimination() {
    let result=test_equal(18,19);
    assert!(!result.is_proven(),
        "a dependent codomain makes the input type-relevant: {result:?}");
}
