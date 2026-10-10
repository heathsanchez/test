use metatron_kernel::{
    environment::{ConstantDecl,Environment},
    id::{ExprId,IdTable,LevelId,NameId},
    syntax::{Expr,Level},
    typecheck::{TypeChecker,TypeValue},
    value::{Closure,EnvFrame,FreeId},
};

fn compare(negative:bool)->bool {
    let mut es=IdTable::default();
    let mut ls=IdTable::default();
    ls.insert(LevelId(0),Level::Zero).unwrap();
    es.insert(ExprId(0),Expr::Sort(LevelId(0))).unwrap();
    es.insert(ExprId(1),Expr::BVar(0)).unwrap();
    es.insert(ExprId(2),Expr::BVar(1)).unwrap();
    es.insert(ExprId(3),Expr::Lam{domain:ExprId(0),body:ExprId(1)}).unwrap();
    es.insert(ExprId(4),Expr::Lam{domain:ExprId(0),body:ExprId(2)}).unwrap();
    es.insert(ExprId(5),Expr::Const{name:NameId(7),levels:vec![]}).unwrap();
    es.insert(ExprId(6),Expr::BVar(0)).unwrap();
    let env=Environment::empty()
        .extend(NameId(7),ConstantDecl::definition(vec![],ExprId(0),ExprId(3),true)).unwrap();
    let ck=TypeChecker::new(&es,&ls,&env);
    let lhs=Closure::new(ExprId(6),EnvFrame::empty().extend(
        Closure::new(ExprId(3),EnvFrame::empty().extend_free(FreeId(17)))
    ));
    let rhs=Closure::new(ExprId(6),EnvFrame::empty().extend(
        Closure::new(if negative {ExprId(4)}else{ExprId(5)},
            EnvFrame::empty().extend_free(if negative {FreeId(18)}else{FreeId(17)}))
    ));
    ck.convert(&TypeValue::Term(lhs),&TypeValue::Term(rhs),2048).is_proven()
}

#[test]
fn definitionally_reduced_lambda_compares_under_shared_lexical_binder(){
    assert!(compare(false));
}
#[test]
fn different_data_binders_are_not_identified_by_weak_head_reduction(){
    assert!(!compare(true));
}
