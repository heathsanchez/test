use metatron_kernel::{convert,environment::Environment,id::{ExprId,IdTable,LevelId},level::LevelTerm,syntax::{Expr,Level},typecheck::{TypeChecker,TypeValue},value::{Closure,EnvFrame,FreeId}};

fn tower(height:u64)->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>){
 let mut e=IdTable::default(); let mut l=IdTable::default();
 l.insert(LevelId(0),Level::Zero).unwrap();e.insert(ExprId(0),Expr::Sort(LevelId(0))).unwrap();
 for n in 1..=height {e.insert(ExprId(n),Expr::Pi{domain:ExprId(0),body:ExprId(n-1)}).unwrap();}
 (e,l)
}
fn sides(height:u64)->(TypeValue,TypeValue){
 let c=|id|Closure::new(ExprId(id),EnvFrame::empty());
 (TypeValue::Term(c(height)),TypeValue::Pi{domain:Box::new(TypeValue::Term(c(0))),body:Box::new(TypeValue::Term(c(height-1).under_free(FreeId(0)))),binder:FreeId(0)})
}
#[test]
fn a_source_pi_converts_to_its_semantic_pi_with_sufficient_owner_work(){
 let(e,l)=tower(600);let env=Environment::empty();let checker=TypeChecker::new(&e,&l,&env);let(a,b)=sides(600);
 let r=convert::convert(&checker,&a,&b,20000);assert!(r.is_proven(),"source and its own semantic Pi agree: {r:?}");
}
#[test]
fn insufficient_capture_work_is_unknown_rather_than_a_rigid_refutation(){
 let(e,l)=tower(600);let env=Environment::empty();let checker=TypeChecker::new(&e,&l,&env);let(a,b)=sides(600);
 let r=convert::convert(&checker,&a,&b,128);assert!(r.is_unknown(),"an incomplete capture premise is not a refutation: {r:?}");
}
#[test]
fn a_real_capture_collision_cannot_establish_semantic_pi_equality(){
 let(mut e,l)=tower(1);e.insert(ExprId(2),Expr::BVar(1)).unwrap();e.insert(ExprId(3),Expr::Pi{domain:ExprId(0),body:ExprId(2)}).unwrap();e.insert(ExprId(4),Expr::BVar(0)).unwrap();
 let env=Environment::empty();let checker=TypeChecker::new(&e,&l,&env);
 let frame=EnvFrame::empty().extend_free(FreeId(0));
 let a=TypeValue::Term(Closure::new(ExprId(3),frame));
 // A bound local and an ambient local with the same numeric ID must
 // not become equal through opening. Removing the guard makes this pass.
 let b=TypeValue::Pi{domain:Box::new(TypeValue::Term(Closure::new(ExprId(0),EnvFrame::empty()))),body:Box::new(TypeValue::Term(Closure::new(ExprId(4),EnvFrame::empty().extend_free(FreeId(0))))),binder:FreeId(0)};
 let r=convert::convert(&checker,&a,&b,20000);assert!(!r.is_proven(),"capture guard must remain mandatory: {r:?}");
}
#[test]
fn genuinely_different_type_constructors_remain_refuted(){
 let(e,l)=tower(1);let env=Environment::empty();let checker=TypeChecker::new(&e,&l,&env);let(a,_)=sides(1);
 assert!(convert::convert(&checker,&a,&TypeValue::Sort(LevelTerm::Zero),20000).is_refuted());
}
