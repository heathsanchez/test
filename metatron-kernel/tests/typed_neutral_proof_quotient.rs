use metatron_kernel::{
    environment::{ConstantDecl,Environment},
    id::{ExprId,IdTable,LevelId,NameId},
    judgment::Judgment,
    syntax::{Expr,Level},
    typecheck::{TypeChecker,TypeValue},
    value::{Closure,EnvFrame},
};

fn fixture()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
    let mut levels=IdTable::default();
    levels.insert(LevelId(0),Level::Zero).unwrap();
    levels.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
    let mut expressions=IdTable::default();
    let nodes=[
        (0,Expr::Sort(LevelId(0))), // Prop
        (1,Expr::Sort(LevelId(1))), // Type 0
        (2,Expr::Const{name:NameId(1),levels:vec![]}), // A : Prop
        (3,Expr::Const{name:NameId(2),levels:vec![]}), // B : Prop
        (4,Expr::Pi{domain:ExprId(2),body:ExprId(2)}), // A -> A : Prop
        (5,Expr::Pi{domain:ExprId(2),body:ExprId(3)}), // A -> B : Prop
        (6,Expr::Const{name:NameId(3),levels:vec![]}), // proof p : A->A
        (7,Expr::Const{name:NameId(4),levels:vec![]}), // proof q : A->A
        (8,Expr::Const{name:NameId(5),levels:vec![]}), // proof r : A->B
        (9,Expr::Const{name:NameId(6),levels:vec![]}), // Nat : Type 0
        (10,Expr::Const{name:NameId(7),levels:vec![]}), // n: Nat
        (11,Expr::Const{name:NameId(8),levels:vec![]}), // m: Nat
        (12,Expr::Const{name:NameId(9),levels:vec![]}), // proof a : A
        (13,Expr::Pi{domain:ExprId(2),body:ExprId(4)}), // A -> (A -> A)
        (14,Expr::Const{name:NameId(10),levels:vec![]}), // f : A -> (A->A)
        (15,Expr::Const{name:NameId(11),levels:vec![]}), // g : A -> (A->A)
        (16,Expr::App{fun:ExprId(14),arg:ExprId(12)}), // f a
        (17,Expr::App{fun:ExprId(15),arg:ExprId(12)}), // g a
        (18,Expr::App{fun:ExprId(14),arg:ExprId(2)}), // f A ill-typed
    ];
    for (i,node) in nodes{expressions.insert(ExprId(i),node).unwrap();}
    let env=Environment::empty()
        .extend(NameId(1),ConstantDecl::axiom(vec![],ExprId(0))).unwrap()
        .extend(NameId(2),ConstantDecl::axiom(vec![],ExprId(0))).unwrap()
        .extend(NameId(3),ConstantDecl::axiom(vec![],ExprId(4))).unwrap()
        .extend(NameId(4),ConstantDecl::axiom(vec![],ExprId(4))).unwrap()
        .extend(NameId(5),ConstantDecl::axiom(vec![],ExprId(5))).unwrap()
        .extend(NameId(6),ConstantDecl::inductive_type(vec![],ExprId(1))).unwrap()
        .extend(NameId(7),ConstantDecl::axiom(vec![],ExprId(9))).unwrap()
        .extend(NameId(8),ConstantDecl::axiom(vec![],ExprId(9))).unwrap()
        .extend(NameId(9),ConstantDecl::axiom(vec![],ExprId(2))).unwrap()
        .extend(NameId(10),ConstantDecl::axiom(vec![],ExprId(13))).unwrap()
        .extend(NameId(11),ConstantDecl::axiom(vec![],ExprId(13))).unwrap();
    (expressions,levels,env)
}
fn compare(a:u64,b:u64)->Judgment<()> {
    let (expr,levels,environment)=fixture();
    let checker=TypeChecker::new(&expr,&levels,&environment);
    checker.convert(
        &TypeValue::Term(Closure::new(ExprId(a),EnvFrame::empty())),
        &TypeValue::Term(Closure::new(ExprId(b),EnvFrame::empty())),
        8192,
    )
}

#[test]
fn distinct_rigid_proof_terms_of_the_same_function_proposition_are_equal(){
    let result=compare(6,7);
    assert!(result.is_proven(),
        "opaque proofs of the same checked Pi proposition are definitionally equal: {result:?}");
}
#[test]
fn distinct_data_terms_with_equal_types_remain_distinct(){
    let result=compare(10,11);
    assert!(!result.is_proven(),
        "two Nat data constants are not equal merely because they have the same type: {result:?}");
}
#[test]
fn two_proofs_of_different_propositions_are_not_equal(){
    let result=compare(6,8);
    assert!(!result.is_proven(),
        "A->A and A->B are not known convertible propositions: {result:?}");
}
#[test]
fn two_opaque_proof_functions_with_checked_arguments_are_irrelevant(){
    let result=compare(16,17);
    assert!(result.is_proven(),
        "two applied proof functions returning the same checked proposition: {result:?}");
}
#[test]
fn ill_typed_proof_argument_cannot_be_accepted_by_new_neutral_rule(){
    let result=compare(18,17);
    assert!(!result.is_proven(),
        "A : Prop is not proof of A, so the applied neutral has no checked type: {result:?}");
}
