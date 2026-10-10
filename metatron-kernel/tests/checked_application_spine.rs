use metatron_kernel::{
    environment::{ConstantDecl,Environment},
    id::{ExprId,IdTable,LevelId,NameId},
    judgment::Judgment,
    syntax::{Expr,Level},
    typecheck::{TypeChecker,TypeValue},
};

fn infer(last_arg:ExprId) -> Judgment<TypeValue> {
    let mut lvls=IdTable::default();
    lvls.insert(LevelId(0),Level::Zero).unwrap();
    let mut ex=IdTable::default();
    let nodes=[
        (0,Expr::Sort(LevelId(0))), // Prop
        (1,Expr::Const{name:NameId(1),levels:vec![]}), // A : Prop
        (2,Expr::Const{name:NameId(2),levels:vec![]}), // p : A
        (3,Expr::Pi{domain:ExprId(1),body:ExprId(0)}), // A -> Prop
        (4,Expr::Pi{domain:ExprId(1),body:ExprId(3)}), // A -> A -> Prop
        (5,Expr::Pi{domain:ExprId(1),body:ExprId(4)}), // A -> A -> A -> Prop
        (6,Expr::Const{name:NameId(3),levels:vec![]}), // R
        (7,Expr::App{fun:ExprId(6),arg:ExprId(2)}), // R p
        (8,Expr::App{fun:ExprId(7),arg:ExprId(2)}), // R p p
        (9,Expr::App{fun:ExprId(8),arg:last_arg}), // R p p ?
    ];
    for (i,node) in nodes {ex.insert(ExprId(i),node).unwrap();}
    let env=Environment::empty()
       .extend(NameId(1),ConstantDecl::axiom(vec![],ExprId(0))).unwrap()
       .extend(NameId(2),ConstantDecl::axiom(vec![],ExprId(1))).unwrap()
       .extend(NameId(3),ConstantDecl::axiom(vec![],ExprId(5))).unwrap();
    TypeChecker::new(&ex,&lvls,&env).infer(ExprId(9),4096)
}

#[test]
fn entire_three_argument_telescope_instantiates_without_shortcuts(){
    let result=infer(ExprId(2));
    assert!(result.is_proven(),"valid fully checked 3-argument dependent application: {result:?}");
}

#[test]
fn wrong_type_in_final_application_cannot_be_laundered(){
    let result=infer(ExprId(1));
    assert!(!result.is_proven(),"A : Prop is not a proof of A: {result:?}");
}

#[test]
fn missing_binder_type_source_is_not_a_valid_argument(){
    let result=infer(ExprId(0));
    assert!(!result.is_proven(),"Prop : Sort1 is not a proof of A: {result:?}");
}
